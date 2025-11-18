"""コンポーネント使用例

このファイルは、各コンポーネントの使用方法を示すサンプルです。
実際のページ実装の参考にしてください。
"""

import streamlit as st

from ui.components import (
    apply_common_styles,
    render_paper_card,
    render_rag_form,
    render_search_form,
)
from ui.components.rag_form import (
    execute_rag_query,
    render_answer,
    render_question_input,
    render_sources,
)
from ui.components.search_form import execute_search


def example_search_page():
    """検索ページの使用例"""

    # 共通スタイルを適用
    apply_common_styles()

    st.title("📖 論文検索（コンポーネント使用例）")

    # サイドバーで検索フォームを表示
    with st.sidebar:
        query, max_results, search_button = render_search_form()

    # 検索実行
    if search_button:
        result = execute_search(query, max_results)

        if result:
            papers = result.get("papers", [])

            # セッションステートに保存
            st.session_state["search_results"] = papers
            st.session_state["search_query"] = query

    # 検索結果を表示
    if "search_results" in st.session_state and st.session_state["search_results"]:
        st.subheader(f"検索結果: {st.session_state.get('search_query', '')}")

        papers = st.session_state["search_results"]

        # 論文カードを表示
        for i, paper in enumerate(papers):
            render_paper_card(paper, i, show_download=True)
    else:
        st.info("👆 左のサイドバーから検索を開始してください")


def example_rag_page():
    """RAG質問応答ページの使用例"""

    # 共通スタイルを適用
    apply_common_styles()

    st.title("💬 RAG質問応答（コンポーネント使用例）")

    # サイドバーで設定フォームを表示
    with st.sidebar:
        selected_arxiv_ids, top_k, _, _, _ = render_rag_form()

    # メインエリアで質問入力
    question, query_button, clear_button = render_question_input()

    # クリアボタン処理
    if clear_button:
        st.session_state.pop("rag_result", None)
        st.rerun()

    # 質問実行
    if query_button:
        result = execute_rag_query(question, selected_arxiv_ids, top_k)

        if result:
            # セッションステートに保存
            st.session_state["rag_result"] = result
            st.session_state["rag_question"] = question

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
    else:
        st.info("👆 質問を入力して「質問する」ボタンをクリックしてください")


if __name__ == "__main__":
    # どちらかのページを表示（実際のアプリでは別々のページファイルになります）
    page = st.sidebar.radio("ページ選択", ["検索", "RAG"])

    if page == "検索":
        example_search_page()
    else:
        example_rag_page()
