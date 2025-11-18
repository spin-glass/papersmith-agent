"""RAG質問フォームコンポーネント

Requirements: 3.4
"""

import asyncio
from typing import Optional

import httpx
import streamlit as st

from ui.config import api_config


async def get_indexed_papers() -> Optional[list[dict]]:
    """インデックス済み論文の一覧を取得

    Returns:
        論文リストまたはNone
    """
    try:
        async with api_config.get_client() as client:
            # ヘルスチェックでインデックスサイズを確認
            response = await client.get("/health")
            response.raise_for_status()
            health_data = response.json()

            # インデックスが空の場合
            if health_data.get("index_size", 0) == 0:
                return []

            # 実際の論文リストを取得する方法がないため、
            # セッションステートから取得した論文を使用
            if "downloaded_papers" in st.session_state:
                return st.session_state["downloaded_papers"]

            return []

    except httpx.HTTPError as e:
        st.error(f"❌ API接続エラー: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        return None


async def rag_query(question: str, arxiv_ids: Optional[list[str]], top_k: int) -> Optional[dict]:
    """RAGクエリを実行

    Args:
        question: 質問
        arxiv_ids: フィルタリングする論文IDリスト
        top_k: 取得する検索結果数

    Returns:
        RAG回答またはNone
    """
    try:
        async with api_config.get_client() as client:
            response = await client.post(
                "/rag/query",
                json={
                    "question": question,
                    "arxiv_ids": arxiv_ids,
                    "top_k": top_k
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        error_detail = "不明なエラー"
        try:
            error_json = e.response.json()
            error_detail = error_json.get("detail", str(e))
        except:
            error_detail = str(e)
        st.error(f"❌ RAGクエリエラー: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        return None


def render_rag_form() -> tuple[Optional[list[str]], int, Optional[str], bool, bool]:
    """RAG質問フォームを表示

    Returns:
        (selected_arxiv_ids, top_k, question, query_button, clear_button):
        選択された論文ID、top_k、質問、質問ボタンがクリックされたか、クリアボタンがクリックされたか
    """
    st.header("質問設定")

    # インデックス状態を確認
    with st.spinner("インデックス状態を確認中..."):
        papers = asyncio.run(get_indexed_papers())

    if papers is None:
        st.error("❌ インデックス情報の取得に失敗しました")
        return None, 5, None, False, False

    if len(papers) == 0:
        st.warning("⚠️ インデックス化された論文がありません")
        st.info("まず「📖 論文検索」ページで論文をダウンロードしてください")
        return None, 5, None, False, False
    else:
        st.success(f"✅ {len(papers)}件の論文がインデックス化されています")

    st.markdown("---")

    # 論文フィルタ
    st.subheader("論文フィルタ")

    # 論文選択（マルチセレクト）
    paper_options = {
        f"{p.get('title', 'タイトル不明')[:40]}... ({p.get('arxiv_id', '')})": p.get('arxiv_id', '')
        for p in papers
    }

    selected_papers = st.multiselect(
        "検索対象の論文を選択",
        options=list(paper_options.keys()),
        help="特定の論文に絞り込む場合は選択してください。未選択の場合は全論文が対象になります。"
    )

    # 選択された論文のarxiv_idリストを取得
    selected_arxiv_ids = [paper_options[p] for p in selected_papers] if selected_papers else None

    if selected_arxiv_ids:
        st.info(f"📌 {len(selected_arxiv_ids)}件の論文に絞り込み")

    st.markdown("---")

    # 検索パラメータ
    st.subheader("検索パラメータ")

    top_k = st.slider(
        "取得チャンク数 (top_k)",
        min_value=1,
        max_value=20,
        value=5,
        help="検索結果として取得するチャンク数を指定します"
    )

    st.markdown("---")

    # ヘルプ
    with st.expander("💡 使い方のヒント"):
        st.markdown("""
        **効果的な質問方法:**
        - 具体的な質問をする
        - 論文の内容に関連する質問をする
        - 日本語でも英語でも質問可能

        **例:**
        - この論文の主な貢献は何ですか？
        - どのような手法を使用していますか？
        - 実験結果はどうでしたか？
        - この研究の限界は何ですか？
        """)

    # 質問入力（メインエリアで使用するため、ここでは返すだけ）
    return selected_arxiv_ids, top_k, None, False, False


def render_question_input() -> tuple[Optional[str], bool, bool]:
    """質問入力フォームを表示

    Returns:
        (question, query_button, clear_button): 質問、質問ボタンがクリックされたか、クリアボタンがクリックされたか
    """
    st.subheader("❓ 質問を入力")

    question = st.text_area(
        "質問",
        placeholder="例: この論文の主な貢献は何ですか？",
        height=100,
        help="論文の内容に関する質問を入力してください"
    )

    # 質問ボタン
    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        query_button = st.button("🚀 質問する", type="primary", use_container_width=True)

    with col2:
        clear_button = st.button("🗑️ クリア", use_container_width=True)

    return question, query_button, clear_button


def execute_rag_query(question: str, selected_arxiv_ids: Optional[list[str]], top_k: int) -> Optional[dict]:
    """RAGクエリを実行

    Args:
        question: 質問
        selected_arxiv_ids: 選択された論文IDリスト
        top_k: 取得チャンク数

    Returns:
        RAG結果またはNone
    """
    if not question.strip():
        st.warning("⚠️ 質問を入力してください")
        return None

    # 質問を表示
    st.markdown(f"""
    <div class="question-box">
        <strong>❓ 質問:</strong> {question}
    </div>
    """, unsafe_allow_html=True)

    # RAGクエリを実行
    with st.spinner("🤔 回答を生成中... (LLM推論には時間がかかる場合があります)"):
        result = asyncio.run(rag_query(question, selected_arxiv_ids, top_k))

    if result:
        st.success("✅ 回答を生成しました")
        return result

    return None


def render_answer(answer: str):
    """回答を表示

    Args:
        answer: 生成された回答
    """
    st.markdown(f"""
    <div class="answer-box">
        <div class="answer-title">💡 回答</div>
        <div class="answer-text">{answer}</div>
    </div>
    """, unsafe_allow_html=True)


def render_sources(sources: list[dict]):
    """参照元チャンクを表示

    Args:
        sources: 検索結果リスト
    """
    st.subheader("📚 参照元チャンク")

    for i, source in enumerate(sources, 1):
        chunk_id = source.get("chunk_id", "")
        text = source.get("text", "")
        score = source.get("score", 0.0)
        metadata = source.get("metadata", {})

        arxiv_id = metadata.get("arxiv_id", "")
        title = metadata.get("title", "タイトル不明")
        section = metadata.get("section", "unknown")

        # エクスパンダーで表示
        with st.expander(f"📄 チャンク {i}: {title[:50]}... (スコア: {score:.3f})"):
            st.markdown(f"""
            <div class="source-box">
                <div class="source-text">{text}</div>
                <div class="source-meta">
                    📌 論文ID: {arxiv_id} | 📑 セクション: {section} | 🆔 チャンクID: {chunk_id}
                </div>
            </div>
            """, unsafe_allow_html=True)
