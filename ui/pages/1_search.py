# -*- coding: utf-8 -*-
"""論文検索ページ

Requirements: 3.2, 3.3
"""

import asyncio
from typing import List, Optional

import httpx
import streamlit as st

from ui.config import api_config
from ui.utils.error_handler import ErrorHandler, LoadingState, validate_input


# ページ設定
st.set_page_config(
    page_title="論文検索 - Papersmith Agent",
    page_icon="📖",
    layout="wide"
)


# カスタムCSS
st.markdown("""
<style>
    .paper-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .paper-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .paper-authors {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .paper-meta {
        color: #888;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .paper-summary {
        color: #333;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        line-height: 1.5;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


async def search_papers(query: str, max_results: int) -> Optional[dict]:
    """論文を検索
    
    Args:
        query: 検索クエリ
        max_results: 最大取得件数
        
    Returns:
        検索結果（papers, count）またはNone
    """
    try:
        async with api_config.get_client() as client:
            response = await client.post(
                "/papers/search",
                json={"query": query, "max_results": max_results}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        ErrorHandler.handle_api_error(e, "論文検索")
        return None


async def download_paper(arxiv_id: str) -> Optional[dict]:
    """論文をダウンロードしてインデックス化
    
    Args:
        arxiv_id: arXiv論文ID
        
    Returns:
        ダウンロード結果またはNone
    """
    try:
        async with api_config.get_client() as client:
            response = await client.post(
                "/papers/download",
                json={"arxiv_id": arxiv_id}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        ErrorHandler.handle_api_error(e, f"論文ダウンロード (ID: {arxiv_id})")
        return None


def render_paper_card(paper: dict, index: int):
    """論文カードを表示
    
    Args:
        paper: 論文メタデータ
        index: カードのインデックス
    """
    arxiv_id = paper.get("arxiv_id", "")
    title = paper.get("title", "タイトル不明")
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    summary = paper.get("summary", "")
    pdf_url = paper.get("pdf_url", "")
    
    # 著者リストを整形
    authors_str = ", ".join(authors[:3])
    if len(authors) > 3:
        authors_str += f" 他{len(authors) - 3}名"
    
    # カードを表示
    st.markdown(f"""
    <div class="paper-card">
        <div class="paper-title">{title}</div>
        <div class="paper-authors">👤 {authors_str}</div>
        <div class="paper-meta">📅 {year} | 🆔 {arxiv_id}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 要約を表示（折りたたみ可能）
    with st.expander("📄 要約を表示"):
        st.markdown(f'<div class="paper-summary">{summary}</div>', unsafe_allow_html=True)
    
    # アクションボタン
    col1, col2, col3 = st.columns([2, 2, 6])
    
    with col1:
        if st.button("📥 ダウンロード", key=f"download_{index}_{arxiv_id}"):
            with LoadingState.spinner(f"📥 {arxiv_id} をダウンロード中..."):
                result = asyncio.run(download_paper(arxiv_id))
                
                if result and result.get("status") == "success":
                    st.success(
                        f"✅ {result.get('message', 'ダウンロード完了')} "
                        f"({result.get('indexed_chunks', 0)} チャンク)"
                    )
                    
                    # ダウンロードした論文をセッションステートに追加
                    if "downloaded_papers" not in st.session_state:
                        st.session_state["downloaded_papers"] = []
                    
                    # 重複チェック
                    if not any(p.get("arxiv_id") == arxiv_id for p in st.session_state["downloaded_papers"]):
                        st.session_state["downloaded_papers"].append(paper)
                    
                    st.balloons()
    
    with col2:
        if pdf_url:
            st.link_button("🔗 PDF", pdf_url, use_container_width=True)
    
    st.markdown("---")


def main():
    """メインアプリケーション"""
    
    st.title("📖 論文検索")
    st.markdown("arXiv APIを使用してキーワードで論文を検索し、ダウンロードしてインデックス化します。")
    
    # サイドバー: 検索フォーム
    with st.sidebar:
        st.header("検索設定")
        
        # キーワード入力
        query = st.text_input(
            "🔍 検索キーワード",
            placeholder="例: transformer attention mechanism",
            help="論文のタイトル、要約、著者名などで検索できます"
        )
        
        # 最大取得件数
        max_results = st.slider(
            "📊 最大取得件数",
            min_value=1,
            max_value=50,
            value=10,
            help="取得する論文の最大件数を指定します"
        )
        
        # 検索ボタン
        search_button = st.button("🔍 検索", type="primary", use_container_width=True)
        
        st.markdown("---")
        
        # ヘルプ
        with st.expander("💡 検索のヒント"):
            st.markdown("""
            **効果的な検索方法:**
            - 具体的なキーワードを使用
            - 複数のキーワードを組み合わせる
            - 英語で検索すると精度が向上
            
            **例:**
            - `transformer attention`
            - `deep learning computer vision`
            - `reinforcement learning robotics`
            """)
    
    # メインエリア
    if search_button:
        if not validate_input(query, "検索キーワード"):
            return
        
        # 検索実行
        with LoadingState.spinner(f"🔍 '{query}' を検索中..."):
            result = asyncio.run(search_papers(query, max_results))
        
        if result:
            papers = result.get("papers", [])
            count = result.get("count", 0)
            
            if count == 0:
                st.info("📭 検索結果が見つかりませんでした。別のキーワードで試してください。")
            else:
                st.success(f"✅ {count}件の論文が見つかりました")
                
                # セッションステートに保存
                st.session_state["search_results"] = papers
                st.session_state["search_query"] = query
    
    # 検索結果を表示
    if "search_results" in st.session_state and st.session_state["search_results"]:
        st.markdown("---")
        st.subheader(f"検索結果: {st.session_state.get('search_query', '')}")
        
        papers = st.session_state["search_results"]
        
        # 論文カードを表示
        for i, paper in enumerate(papers):
            render_paper_card(paper, i)
    
    else:
        # 初期表示
        st.info("👆 左のサイドバーから検索キーワードを入力して検索を開始してください")
        
        # 使い方ガイド
        st.markdown("---")
        st.subheader("📚 使い方")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 1️⃣ 論文を検索
            - 左のサイドバーでキーワードを入力
            - 取得件数を調整
            - 「検索」ボタンをクリック
            """)
        
        with col2:
            st.markdown("""
            ### 2️⃣ 論文をダウンロード
            - 検索結果から興味のある論文を選択
            - 「ダウンロード」ボタンをクリック
            - 自動的にインデックス化されます
            """)
        
        st.markdown("""
        ### 3️⃣ 質問応答
        ダウンロードした論文は自動的にインデックス化され、
        「💬 RAG質問応答」ページで質問できるようになります。
        """)


if __name__ == "__main__":
    main()
