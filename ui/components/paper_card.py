"""論文カードコンポーネント

Requirements: 3.2, 3.3
"""

import asyncio
from typing import Optional

import httpx
import streamlit as st

from ui.config import api_config


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
    except httpx.HTTPError as e:
        error_detail = "不明なエラー"
        try:
            error_json = e.response.json()
            error_detail = error_json.get("detail", str(e))
        except:
            error_detail = str(e)
        st.error(f"❌ ダウンロードエラー: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        return None


def render_paper_card(paper: dict, index: int, show_download: bool = True):
    """論文カードを表示

    Args:
        paper: 論文メタデータ
        index: カードのインデックス
        show_download: ダウンロードボタンを表示するか
    """
    arxiv_id = paper.get("arxiv_id", "")
    title = paper.get("title", "タイトル不明")
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    summary = paper.get("summary", "")
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
    <div class="paper-card">
        <div class="paper-title">{title}</div>
        <div class="paper-authors">👤 {authors_str}</div>
        <div class="paper-meta">📅 {year} | 🆔 {arxiv_id}</div>
    </div>
    """, unsafe_allow_html=True)

    # 要約を表示（折りたたみ可能）
    if summary:
        with st.expander("📄 要約を表示"):
            st.markdown(f'<div class="paper-summary">{summary}</div>', unsafe_allow_html=True)

    # アクションボタン
    if show_download:
        col1, col2, col3 = st.columns([2, 2, 6])

        with col1:
            if st.button("📥 ダウンロード", key=f"download_{index}_{arxiv_id}"):
                with st.spinner(f"📥 {arxiv_id} をダウンロード中..."):
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
                    else:
                        st.error("❌ ダウンロードに失敗しました")

        with col2:
            if pdf_url:
                st.link_button("🔗 PDF", pdf_url, use_container_width=True)
    else:
        # ダウンロードボタンなしの場合はPDFリンクのみ
        if pdf_url:
            st.link_button("🔗 PDF", pdf_url)

    st.markdown("---")


def render_paper_list_card(paper: dict, index: int, chunk_count: Optional[int] = None):
    """論文一覧用のカードを表示

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
    summary = paper.get("summary", "")

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
            if summary:
                st.markdown("**要約:**")
                st.markdown(summary)

    st.markdown("---")
