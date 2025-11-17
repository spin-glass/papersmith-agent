# UI ユーティリティ

このディレクトリには、Streamlit UIで使用する共通ユーティリティが含まれています。

## error_handler.py

エラーハンドリングとローディング状態管理のためのユーティリティモジュール。

### ErrorHandler クラス

API呼び出しエラーを統一的に処理するクラス。

#### 主な機能

- **503エラー**: インデックス未準備時の適切なメッセージ表示
- **404エラー**: リソースが見つからない場合の処理
- **400エラー**: 不正なリクエストの処理
- **500エラー**: サーバーエラーの処理
- **接続エラー**: API接続失敗時の詳細な説明
- **タイムアウト**: 処理時間超過時の対応方法の提示

#### 使用例

```python
from ui.utils.error_handler import ErrorHandler

try:
    # API呼び出し
    response = await client.get("/health")
    response.raise_for_status()
except Exception as e:
    ErrorHandler.handle_api_error(e, "ヘルスチェック")
```

### LoadingState クラス

ローディング状態を管理するクラス。

#### 主な機能

- **spinner**: スピナー表示
- **progress_bar**: プログレスバー表示
- **status_message**: ステータスメッセージ表示

#### 使用例

```python
from ui.utils.error_handler import LoadingState

# スピナー表示
with LoadingState.spinner("⏳ データを読み込み中..."):
    data = load_data()

# プログレスバー表示
LoadingState.progress_bar(total=100, current=50, message="処理中")
```

### validate_input 関数

入力値を検証する関数。

#### 使用例

```python
from ui.utils.error_handler import validate_input

if not validate_input(query, "検索キーワード", min_length=2):
    return  # 検証失敗時は処理を中断
```

## Requirements

- Requirements: 3.5
- エラーメッセージは日本語で表示
- ユーザーフレンドリーな説明を提供
- 503エラー時の適切な対応
