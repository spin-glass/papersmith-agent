# エラーハンドリングとローディング状態

## 概要

Streamlit UIの統一的なエラーハンドリングとローディング状態管理を提供します。

## コンポーネント

### 1. エラーハンドリングユーティリティ (`ui/utils/error_handler.py`)

#### ErrorHandler クラス

統一的なエラー処理を提供するクラス。

**主な機能:**

- **503エラー**: インデックス未準備時の適切なメッセージ表示
  - ユーザーに待機を促す
  - システムが準備中であることを明確に伝える

- **404エラー**: リソースが見つからない場合の処理
  - どのリソースが見つからないかを明示

- **400エラー**: 不正なリクエストの処理
  - APIからの詳細なエラーメッセージを表示

- **500エラー**: サーバーエラーの処理
  - 再試行を促すメッセージを表示

- **接続エラー**: API接続失敗時の詳細な説明
  - Dockerコンテナの起動確認を促す
  - API URLの確認を促す

- **タイムアウト**: 処理時間超過時の対応方法の提示
  - LLM推論に時間がかかることを説明
  - 考えられる原因を列挙

**使用例:**

```python
try:
    response = await client.get("/health")
    response.raise_for_status()
except Exception as e:
    ErrorHandler.handle_api_error(e, "ヘルスチェック")
```

#### LoadingState クラス

ローディング状態を管理するクラス。

**主な機能:**

- **spinner**: スピナー表示（`st.spinner`のラッパー）
- **progress_bar**: プログレスバー表示
- **status_message**: ステータスメッセージ表示

**使用例:**

```python
# スピナー表示
with LoadingState.spinner("⏳ データを読み込み中..."):
    data = load_data()

# プログレスバー表示
LoadingState.progress_bar(total=100, current=50, message="処理中")
```

#### validate_input 関数

入力値を検証する関数。

**機能:**

- 空文字列のチェック
- 空白のみの入力のチェック
- 最小文字数のチェック
- 日本語のエラーメッセージ表示

**使用例:**

```python
if not validate_input(query, "検索キーワード", min_length=2):
    return  # 検証失敗時は処理を中断
```

### 2. UI統合

全UIページ（`ui/app.py`, `ui/pages/*.py`）で使用されています。詳細は [UI_GUIDE.md](UI_GUIDE.md) を参照してください。

### 3. テスト

`tests/unit/test_error_handler.py` で11個のテストケースをカバー（全テスト成功）。

## エラーメッセージの例

### 503エラー（インデックス未準備）

```
⚠️ システムが準備中です

インデックスの構築が完了していません。
しばらく待ってから再度お試しください。
```

### 接続エラー

```
❌ API接続エラー

FastAPI サーバーに接続できません。
サーバーが起動しているか確認してください。

**確認事項:**
- Docker コンテナが起動しているか
- API URL が正しいか (デフォルト: http://localhost:8000)
```

### タイムアウトエラー

```
❌ タイムアウトエラー

RAG質問応答の処理に時間がかかりすぎています。

**考えられる原因:**
- LLM推論に時間がかかっている
- 大量のデータを処理している
- ネットワークが不安定

しばらく待ってから再度お試しください。
```

## Requirements

**Requirement 3.5**: エラーハンドリングとローディング状態の改善
- ✅ API呼び出しのエラーハンドリング
- ✅ ローディング状態の表示（st.spinner、st.progress）
- ✅ エラーメッセージの改善（日本語、わかりやすい説明）
- ✅ 503エラー時の適切な表示

## 使用方法

### 新しいページでエラーハンドリングを使用する場合

```python
from ui.utils.error_handler import ErrorHandler, LoadingState, validate_input

# エラーハンドリング
try:
    response = await client.post("/api/endpoint", json=data)
    response.raise_for_status()
except Exception as e:
    ErrorHandler.handle_api_error(e, "処理名")
    return None

# ローディング表示
with LoadingState.spinner("⏳ 処理中..."):
    result = process_data()

# 入力検証
if not validate_input(user_input, "フィールド名", min_length=3):
    return
```

## 関連ドキュメント

- [UI使用ガイド](UI_GUIDE.md) - エラーハンドリングの実際の動作
- [ユーティリティREADME](../ui/utils/README.md) - 詳細な使用方法
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - 実装状況
