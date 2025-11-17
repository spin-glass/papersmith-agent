# -*- coding: utf-8 -*-
"""論文一覧ページ

Requirements: 3.1
"""

import asyncio
from typing import List, Optional

import httpx
import streamlit as st

from ui.config import api_config
from ui.utils.error_handler import ErrorHandler, LoadingState


# ページ設定
st.set_page_config(
    page_title="論文一覧 - Papersmith Agent",
    page_icon="📚",
    layout="wide"
)


# カスタムCSS
st.markdown("""
<style>
    .paper-list-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .paper-list-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #28a745;
        margin-bottom: 0.5rem;
    }
    .paper-list-authors {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .paper-list-meta {
        color: #888;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .paper-list-stats {
        color: #555;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        padding: 0.5rem;
        background-color: #e9ecef;
        border-radius: 0.3rem;
    }
    .stat-badge {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        background-color: #17a2b8;
        color: white;
        font-size: 0.85rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #6c757d;
    }
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)



async def get_health_status() -> Optional[dict]:
    """ヘルスチェックを実行してインデックス情報を取得
    
    Returns:
        ヘルスチェック結果またはNone
    """
    try:
        async with api_config.get_client() as client:
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        ErrorHandler.handle_api_error(e, "ヘルスチェック")
        return None


def get_indexed_papers_from_session() -> List[dict]:
    """セッションステートからインデックス済み論文を取得
    
    Returns:
        論文リスト
    """
    papers = []
    
    # ダウンロードした論文を取得
    if "downloaded_papers" in st.session_state:
        papers.extend(st.session_state["downloaded_papers"])
    
    # 重複を除去（arxiv_idベース）
    seen_ids = set()
    unique_papers = []
    for paper in papers:
        arxiv_id = paper.get("arxiv_id")
        if arxiv_id and arxiv_id not in seen_ids:
            seen_ids.add(arxiv_id)
            unique_papers.append(paper)
    
    return unique_papers



def render_paper_list_card(paper: dict, index: int, chunk_count: Optional[int] = None):
    """論文リストカードを表示
    
    Args:
        paper: 論文メタデータ
        index: カードのインデックス
        chunk_count: チャンク数（オプション）
    """
    arxiv_id = paper.get("arxiv_id", "")
    title = paper.get("title", "タイトル不明")
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    pdf_url = paper.get("pdf_url", "")
    
    # 著者リストを整形
    if isinstance(authors, list):
        authors_str = ", ".join(authors[:3])
        if len(authors) > 3:
            authors_str += f" 他{len(authors) - 3}名"
    else:
        authors_str = str(authors)
    
    # カードを表示
    st.markdown(f"""
    <div class="paper-list-card">
        <div class="paper-list-title">{title}</div>
        <div class="paper-list-authors">👤 {authors_str}</div>
        <div class="paper-list-meta">📅 {year} | 🆔 {arxiv_id}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 統計情報を表示
    col1, col2, col3 = st.columns([3, 3, 4])
    
    with col1:
        if chunk_count is not None:
            st.metric("インデックス済みチャンク", f"{chunk_count}")
        else:
            st.metric("インデックス済みチャンク", "不明")
    
    with col2:
        if pdf_url:
            st.link_button("🔗 PDF", pdf_url, use_container_width=True)
    
    with col3:
        # 詳細表示ボタン（エクスパンダー）
        with st.expander("📄 詳細情報"):
            st.markdown(f"""
            **arXiv ID:** {arxiv_id}
            
            **タイトル:** {title}
            
            **著者:** {authors_str}
            
            **年:** {year}
            
            **PDF URL:** {pdf_url if pdf_url else "なし"}
            """)
            
            # 要約があれば表示
            summary = paper.get("summary", "")
            if summary:
                st.markdown("**要約:**")
                st.markdown(summary)
    
    st.markdown("---")


def render_empty_state():
    """空の状態を表示"""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <h3>インデックス化された論文がありません</h3>
        <p>まず「📖 論文検索」ページで論文をダウンロードしてインデックス化してください。</p>
    </div>
    """, unsafe_allow_html=True)



def main():
    """メインアプリケーション"""
    
    st.title("📚 論文一覧")
    st.markdown("インデックス化された論文の一覧を表示します。")
    
    # サイドバー: 統計情報
    with st.sidebar:
        st.header("インデックス統計")
        
        # ヘルスチェックを実行
        with LoadingState.spinner("⏳ インデックス情報を取得中..."):
            health_status = asyncio.run(get_health_status())
        
        if health_status:
            index_size = health_status.get("index_size", 0)
            index_ready = health_status.get("index_ready", False)
            
            st.metric("総ドキュメント数", f"{index_size}")
            
            if index_ready:
                st.success("✅ インデックス準備完了")
            else:
                st.warning("⚠️ インデックス構築中...")
        
        st.markdown("---")
        
        # リフレッシュボタン
        if st.button("🔄 リフレッシュ", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # ヘルプ
        with st.expander("💡 ヒント"):
            st.markdown("""
            **論文一覧について:**
            - ダウンロードした論文の一覧を表示
            - 各論文の詳細情報を確認可能
            - インデックス済みチャンク数を表示
            
            **注意:**
            - チャンク数は推定値です
            - 実際のインデックスサイズは左の統計情報を参照
            """)
    
    # メインエリア
    # セッションステートから論文を取得
    papers = get_indexed_papers_from_session()
    
    if len(papers) == 0:
        render_empty_state()
        
        # 使い方ガイド
        st.markdown("---")
        st.subheader("📚 論文をインデックス化する方法")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 1️⃣ 論文を検索
            - 「📖 論文検索」ページに移動
            - キーワードで論文を検索
            """)
        
        with col2:
            st.markdown("""
            ### 2️⃣ ダウンロード
            - 興味のある論文を選択
            - 「ダウンロード」ボタンをクリック
            """)
        
        st.markdown("""
        ### 3️⃣ 自動インデックス化
        ダウンロードした論文は自動的にインデックス化され、
        このページに表示されます。
        """)
        
        return
    
    # 論文一覧を表示
    st.success(f"✅ {len(papers)}件の論文がインデックス化されています")
    
    # ソートオプション
    col1, col2 = st.columns([3, 7])
    
    with col1:
        sort_option = st.selectbox(
            "並び替え",
            options=["新しい順", "古い順", "タイトル順"],
            index=0
        )
    
    # ソート処理
    if sort_option == "新しい順":
        papers_sorted = sorted(
            papers,
            key=lambda p: p.get("year", ""),
            reverse=True
        )
    elif sort_option == "古い順":
        papers_sorted = sorted(
            papers,
            key=lambda p: p.get("year", ""),
            reverse=False
        )
    else:  # タイトル順
        papers_sorted = sorted(
            papers,
            key=lambda p: p.get("title", "").lower()
        )
    
    st.markdown("---")
    
    # 論文カードを表示
    for i, paper in enumerate(papers_sorted):
        # チャンク数は推定（実際のAPIがないため）
        # 実際の実装では、各論文のチャンク数を取得するAPIが必要
        estimated_chunks = None  # 不明として表示
        
        render_paper_list_card(paper, i, chunk_count=estimated_chunks)
    
    # フッター
    st.markdown("---")
    st.caption(f"合計 {len(papers)} 件の論文")


if __name__ == "__main__":
    main()
