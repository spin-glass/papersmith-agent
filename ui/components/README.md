# UI Components

このディレクトリには、Papersmith Agent UIの再利用可能なコンポーネントが含まれています。

## コンポーネント一覧

### 1. `styles.py` - 共通スタイル

全ページで使用する共通CSSスタイルを定義します。

```python
from ui.components import apply_common_styles

# ページの最初で呼び出す
apply_common_styles()
```

### 2. `paper_card.py` - 論文カード

論文のメタデータを表示するカードコンポーネント。

```python
from ui.components import render_paper_card, render_paper_list_card

# 検索結果用のカード（ダウンロードボタン付き）
render_paper_card(paper, index=0, show_download=True)

# 論文一覧用のカード（統計情報付き）
render_paper_list_card(paper, index=0, chunk_count=42)
```

### 3. `search_form.py` - 検索フォーム

論文検索用のフォームコンポーネント。

```python
from ui.components.search_form import render_search_form, execute_search

# サイドバーでフォームを表示
with st.sidebar:
    query, max_results, search_button = render_search_form()

# 検索実行
if search_button:
    result = execute_search(query, max_results)
    if result:
        papers = result.get("papers", [])
        # 検索結果を処理
```

### 4. `rag_form.py` - RAG質問フォーム

RAG質問応答用のフォームコンポーネント。

```python
from ui.components.rag_form import (
    render_rag_form,
    render_question_input,
    execute_rag_query,
    render_answer,
    render_sources
)

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
        st.session_state["rag_result"] = result
        st.session_state["rag_question"] = question

# 結果表示
if "rag_result" in st.session_state:
    result = st.session_state["rag_result"]

    # 回答を表示
    answer = result.get("answer", "")
    render_answer(answer)

    # 参照元チャンクを表示
    sources = result.get("sources", [])
    if sources:
        render_sources(sources)
```

## 使用例

完全な使用例は、各ページファイル（`ui/pages/*.py`）を参照してください。

## スタイルのカスタマイズ

`styles.py`を編集することで、全ページのスタイルを一括で変更できます。

主要なCSSクラス:
- `.paper-card` - 論文カード
- `.answer-box` - RAG回答ボックス
- `.source-box` - 参照元チャンクボックス
- `.question-box` - 質問ボックス
- `.success-message`, `.error-message`, `.info-message` - メッセージスタイル
