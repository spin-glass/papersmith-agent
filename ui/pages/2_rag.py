# -*- coding: utf-8 -*-
"""RAG質問応答ページ

Requirements: 3.4
"""

import asyncio
from typing import List, Optional

import httpx
import streamlit as st

from ui.config import api_config
from ui.utils.error_handler import ErrorHandler, LoadingState, validate_input


# ページ設定（Streamlitの制約により、ファイル先頭で実行が必要）
st.set_page_config(
    page_title="RAG質問応答 - Papersmith Agent",
    page_icon="💬",
    layout="wide"
)


# CSSスタイル定義（文字列として保持、実行時に適用）
CUSTOM_CSS = """
<style>
    .answer-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1.5rem;
    }
    .answer-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .answer-text {
        color: #333;
        font-size: 1rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }
    .source-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border-left: 3px solid #6c757d;
        margin-bottom: 0.8rem;
    }
    .source-text {
        color: #555;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }
    .source-meta {
        color: #888;
        font-size: 0.8rem;
    }
    .score-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        background-color: #28a745;
        color: white;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .question-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin-bottom: 1rem;
    }
</style>
"""


async def get_indexed_papers() -> Optional[List[dict]]:
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
            
    except Exception as e:
        ErrorHandler.handle_api_error(e, "インデックス情報取得")
        return None


async def rag_query(question: str, arxiv_ids: Optional[List[str]], top_k: int) -> Optional[dict]:
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
    except Exception as e:
        ErrorHandler.handle_api_error(e, "RAG質問応答")
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


def render_sources(sources: List[dict]):
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


def main():
    """メインアプリケーション"""
    
    # カスタムCSSを適用
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    st.title("💬 RAG質問応答")
    st.markdown("インデックス化された論文に対して質問を投げかけ、LLMが関連情報を基に回答を生成します。")
    
    # サイドバー: 設定
    with st.sidebar:
        st.header("質問設定")
        
        # インデックス状態を確認
        with LoadingState.spinner("⏳ インデックス状態を確認中..."):
            papers = asyncio.run(get_indexed_papers())
        
        if papers is None:
            return
        
        if len(papers) == 0:
            st.warning("⚠️ インデックス化された論文がありません")
            st.info("まず「📖 論文検索」ページで論文をダウンロードしてください")
        else:
            st.success(f"✅ {len(papers)}件の論文がインデックス化されています")
        
        st.markdown("---")
        
        # 論文フィルタ
        st.subheader("論文フィルタ")
        
        if len(papers) > 0:
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
        else:
            selected_arxiv_ids = None
        
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
    
    # メインエリア
    if len(papers) == 0:
        st.info("👆 まず「📖 論文検索」ページで論文をダウンロードしてインデックス化してください")
        
        # 使い方ガイド
        st.markdown("---")
        st.subheader("📚 RAG質問応答とは？")
        
        st.markdown("""
        RAG (Retrieval-Augmented Generation) は、検索拡張生成と呼ばれる技術です。
        
        ### 仕組み
        1. **検索**: 質問に関連する論文のチャンクをベクター検索で取得
        2. **拡張**: 検索結果をコンテキストとしてLLMに提供
        3. **生成**: LLMが検索結果を基に回答を生成
        
        ### 利点
        - 論文の内容に基づいた正確な回答
        - 参照元のチャンクを確認可能
        - 複数の論文を横断して検索可能
        """)
        
        return
    
    # 質問入力フォーム
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
        if st.button("🗑️ クリア", use_container_width=True):
            st.session_state.pop("rag_result", None)
            st.rerun()
    
    # 質問実行
    if query_button:
        if not validate_input(question, "質問"):
            pass
        else:
            # 質問を表示
            st.markdown(f"""
            <div class="question-box">
                <strong>❓ 質問:</strong> {question}
            </div>
            """, unsafe_allow_html=True)
            
            # RAGクエリを実行
            with LoadingState.spinner("🤔 回答を生成中... (LLM推論には時間がかかる場合があります)"):
                result = asyncio.run(rag_query(question, selected_arxiv_ids, top_k))
            
            if result:
                # セッションステートに保存
                st.session_state["rag_result"] = result
                st.session_state["rag_question"] = question
                st.success("✅ 回答を生成しました")
    
    # 結果を表示
    if "rag_result" in st.session_state and st.session_state["rag_result"]:
        st.markdown("---")
        
        result = st.session_state["rag_result"]
        question_text = st.session_state.get("rag_question", "")
        
        # 質問を表示
        if question_text:
            st.markdown(f"""
            <div class="question-box">
                <strong>❓ 質問:</strong> {question_text}
            </div>
            """, unsafe_allow_html=True)
        
        # 回答を表示
        answer = result.get("answer", "")
        render_answer(answer)
        
        # メタデータを表示
        metadata = result.get("metadata", {})
        if metadata:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if "support_score" in metadata:
                    st.metric("サポートスコア", f"{metadata['support_score']:.2f}")
            
            with col2:
                if "attempts" in metadata:
                    st.metric("試行回数", metadata["attempts"])
            
            with col3:
                sources_count = len(result.get("sources", []))
                st.metric("参照チャンク数", sources_count)
        
        st.markdown("---")
        
        # 参照元チャンクを表示
        sources = result.get("sources", [])
        if sources:
            render_sources(sources)
        else:
            st.info("参照元チャンクがありません")


if __name__ == "__main__":
    main()
