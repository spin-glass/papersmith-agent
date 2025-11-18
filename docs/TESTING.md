# Testing Guide

## Overview

Papersmith Agentは包括的なテスト戦略を採用しており、高いコードカバレッジ（91%+）を維持しています。

## Test Structure

```
tests/
├── unit/              # ユニットテスト（高速、モック使用）
│   ├── api/           # APIエンドポイント
│   ├── clients/       # 外部APIクライアント
│   ├── models/        # データモデル
│   └── services/      # サービスレイヤー
├── integration/       # 統合テスト（実際のコンポーネント使用）
├── e2e/              # E2Eテスト（フルワークフロー）
└── connectivity/     # 実際のAPI接続テスト（スロー）
```

## Running Tests

### Quick Start

```bash
# 全テスト実行（推奨）
uv run pytest

# カバレッジ付き
uv run pytest --cov=src --cov-report=html --cov-report=term

# 高速イテレーション（スローテストをスキップ）
uv run pytest -m "not slow"
```

### Test Categories

```bash
# ユニットテストのみ（最速）
uv run pytest tests/unit -m unit

# 統合テスト
uv run pytest tests/integration -m integration

# E2Eテスト
uv run pytest tests/e2e -m e2e

# 実際のAPI接続テスト（要APIキー）
uv run pytest tests/connectivity -m slow -v
```

### Parallel Execution

```bash
# 並列実行（高速化）
uv run pytest -n auto

# 4プロセスで並列実行
uv run pytest -n 4
```

### Specific Tests

```bash
# 特定のファイル
uv run pytest tests/unit/services/test_llm_service.py

# 特定のテスト関数
uv run pytest tests/unit/services/test_llm_service.py::test_build_prompt

# 特定のクラス
uv run pytest tests/unit/services/test_llm_service.py::TestLLMServiceInitialization

# パターンマッチ
uv run pytest -k "test_llm"
```

### Failed Tests

```bash
# 失敗したテストのみ再実行
uv run pytest --lf

# 最後に失敗したテストから再開
uv run pytest --ff
```

## Coverage Reporting

### Generate Reports

```bash
# HTMLレポート生成
uv run pytest --cov=src --cov-report=html

# ターミナルレポート
uv run pytest --cov=src --cov-report=term

# JSONレポート（CI/CD用）
uv run pytest --cov=src --cov-report=json

# 複数形式同時生成
uv run pytest --cov=src --cov-report=html --cov-report=term --cov-report=json
```

### View Reports

```bash
# HTMLレポートを開く
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# または便利スクリプトを使用
./scripts/coverage_report.sh
```

### Coverage Targets

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| Overall | 85%+ | 91.20% | ✅ |
| Services | 90%+ | 95%+ | ✅ |
| API Endpoints | 85%+ | 92% | ✅ |
| Models | 95%+ | 100% | ✅ |
| Clients | 80%+ | 90%+ | ✅ |

### Coverage Threshold

```bash
# カバレッジが85%未満の場合、テスト失敗
uv run pytest --cov=src --cov-fail-under=85
```

## Test Configuration

### pytest.ini (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests (fast, mocked)",
    "integration: Integration tests (real components)",
    "e2e: End-to-end tests (full workflows)",
    "slow: Slow tests (real API calls)",
]
asyncio_mode = "auto"
timeout = 300
addopts = "-v --strict-markers"

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Test Markers

### Using Markers

```bash
# ユニットテストのみ
uv run pytest -m unit

# 統合テストのみ
uv run pytest -m integration

# スローテストをスキップ
uv run pytest -m "not slow"

# ユニットと統合テスト
uv run pytest -m "unit or integration"
```

### Available Markers

- `unit`: 高速なユニットテスト（モック使用）
- `integration`: 統合テスト（実際のコンポーネント使用）
- `e2e`: E2Eテスト（フルワークフロー）
- `slow`: スローテスト（実際のAPI呼び出し）

## Writing Tests

### Test Structure

```python
# -*- coding: utf-8 -*-
"""モジュールのテスト

Requirements: X.Y
Testing Strategy: Unit Tests - Component Name
"""

import pytest
from unittest.mock import Mock, patch

from src.module import Component


class TestComponentInitialization:
    """初期化テスト"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化"""
        component = Component()
        assert component.config is not None

    def test_init_with_custom_config(self):
        """カスタム設定での初期化"""
        config = Config(param="value")
        component = Component(config)
        assert component.config.param == "value"


class TestComponentMethods:
    """メソッドテスト"""

    @pytest.mark.asyncio
    async def test_async_method(self):
        """非同期メソッドのテスト"""
        component = Component()
        result = await component.async_method()
        assert result is not None

    def test_method_with_mock(self):
        """モックを使用したテスト"""
        component = Component()

        with patch('src.module.external_call') as mock_call:
            mock_call.return_value = "mocked"
            result = component.method()
            assert result == "mocked"
            mock_call.assert_called_once()
```

### Fixtures

```python
@pytest.fixture
def sample_data():
    """テストデータのフィクスチャ"""
    return {
        "key": "value",
        "items": [1, 2, 3]
    }

@pytest.fixture
async def async_client():
    """非同期クライアントのフィクスチャ"""
    client = AsyncClient()
    await client.connect()
    yield client
    await client.disconnect()
```

### Mocking

```python
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# 同期関数のモック
mock_func = Mock(return_value="result")

# 非同期関数のモック
mock_async = AsyncMock(return_value="result")

# クラスのモック
mock_obj = MagicMock()
mock_obj.method.return_value = "result"

# パッチ
with patch('module.function') as mock_func:
    mock_func.return_value = "mocked"
    result = function()
```

## API Testing

### Real API Tests

実際のAPI接続をテストする場合（`tests/connectivity/`）：

```python
@pytest.mark.slow
@pytest.mark.integration
async def test_gemini_api_connectivity():
    """実際のGemini API接続テスト"""
    import os

    # APIキーがない場合はスキップ
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")

    # 実際のAPI呼び出し
    service = LLMService(LLMConfig(backend="gemini"))
    await service.load_model()
    answer = await service.generate("Test question", "Test context")

    assert len(answer) > 0
```

### Environment Variables

```bash
# .envファイルにAPIキーを設定
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# テスト実行時に環境変数を渡す
GOOGLE_API_KEY=xxx uv run pytest tests/connectivity/
```

## CI/CD Integration

### GitHub Actions

`.github/workflows/test.yml`でCI/CDを設定：

#### テスト実行戦略

GitHub Actionsでは、実行時間を最適化するため、以下の戦略を採用しています：

**デフォルト動作（高速フィードバック）**:
- ✅ Unit tests（常に実行）
- ❌ Integration tests（スキップ）
- ❌ E2E tests（スキップ）

**フルテスト実行のトリガー**:
1. **mainブランチへのpush**: すべてのテストを実行
2. **PRに`run-full-tests`ラベル**: すべてのテストを実行
3. **手動トリガー**: GitHub Actionsの"Run workflow"から実行

#### 使い方

**1. 通常のPR開発時（高速）**
```bash
# 自動的にUnit testsのみ実行（~1分）
git push origin feature-branch
```

**2. フルテストが必要な場合**

方法A: PRにラベルを追加
```
1. GitHubのPRページを開く
2. 右側の"Labels"をクリック
3. "run-full-tests"ラベルを追加
4. 次回のpushで全テストが実行される
```

方法B: 手動トリガー
```
1. GitHub Actionsタブを開く
2. "Tests"ワークフローを選択
3. "Run workflow"をクリック
4. "Run full test suite"にチェック
5. "Run workflow"を実行
```

**3. mainブランチへのマージ時（自動）**
```bash
# mainブランチへのマージ時は自動的に全テストを実行
git checkout main
git merge feature-branch
git push origin main
```

#### ワークフロー設定例

```yaml
# Unit tests: 常に実行
- name: Run unit tests
  run: uv run pytest tests/unit --cov=src

# Integration/E2E tests: 条件付き実行
- name: Run integration tests
  if: |
    github.ref == 'refs/heads/main' ||
    github.event.inputs.run_full_tests == 'true' ||
    contains(github.event.pull_request.labels.*.name, 'run-full-tests')
  run: uv run pytest tests/integration --cov=src --cov-append

- name: Upload to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
```

#### Pythonバージョン

- **使用バージョン**: Python 3.12のみ
- **理由**: 開発環境と一致、CI実行時間の短縮

### Pre-commit Hooks

```bash
# pre-commit hooksのインストール
pip install pre-commit
pre-commit install

# 手動実行
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

**1. Tests hang or timeout**

症状: テストが無限に実行される、またはタイムアウトする

```bash
# 解決策1: タイムアウトを延長
uv run pytest --timeout=600

# 解決策2: 特定のテストをスキップ
uv run pytest -m "not slow"

# 解決策3: 並列実行を無効化
uv run pytest -n 0

# 解決策4: 詳細ログで原因特定
uv run pytest -vv -s
```

原因:
- Streamlit UIコードがトップレベルで実行されている
- 外部APIが応答しない
- 無限ループやデッドロック

**2. Import errors**

症状: `ModuleNotFoundError` または `ImportError`

```bash
# 解決策1: PYTHONPATHを設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run pytest

# 解決策2: 依存関係を再インストール
uv sync

# 解決策3: パッケージを明示的にインストール
uv pip install -e .

# 解決策4: Pythonパスを確認
python3 -c "import sys; print('\n'.join(sys.path))"
```

原因:
- PYTHONPATHが設定されていない
- 依存関係がインストールされていない
- 仮想環境が有効化されていない

**3. Coverage not accurate**

症状: カバレッジレポートが不正確、または古いデータを表示

```bash
# 解決策1: キャッシュをクリア
rm -rf .pytest_cache .coverage htmlcov/ .ruff_cache/
uv run pytest --cov=src --cov-report=html

# 解決策2: カバレッジデータをリセット
coverage erase
uv run pytest --cov=src

# 解決策3: 特定のディレクトリのみカバレッジ測定
uv run pytest --cov=src/services --cov-report=term
```

原因:
- 古いカバレッジデータが残っている
- 複数回の実行でデータが混在
- .coveragercの設定が不適切

**4. Parallel execution issues**

症状: 並列実行時にテストが失敗する、またはランダムに失敗する

```bash
# 解決策1: 並列実行を無効化
uv run pytest -n 0

# 解決策2: プロセス数を減らす
uv run pytest -n 2

# 解決策3: 特定のテストのみシリアル実行
uv run pytest tests/integration/ -n 0
uv run pytest tests/unit/ -n auto
```

原因:
- テスト間で状態を共有している
- ファイルシステムやデータベースの競合
- グローバル変数の使用

**5. API key errors**

症状: `GOOGLE_API_KEY not set` または API認証エラー

```bash
# 解決策1: .envファイルを作成
cp .env.template .env
# .envファイルにAPIキーを設定

# 解決策2: 環境変数を直接設定
export GOOGLE_API_KEY="your_key_here"
uv run pytest tests/connectivity/

# 解決策3: スローテストをスキップ
uv run pytest -m "not slow"
```

原因:
- APIキーが設定されていない
- .envファイルが読み込まれていない
- APIキーの形式が不正

**6. Encoding errors**

症状: `UnicodeDecodeError` または日本語文字が文字化け

```bash
# 解決策1: ファイルの先頭にエンコーディング宣言を追加
# -*- coding: utf-8 -*-

# 解決策2: 環境変数を設定
export PYTHONIOENCODING=utf-8
uv run pytest

# 解決策3: ファイルをUTF-8で保存し直す
```

原因:
- ファイルのエンコーディングが不適切
- システムのデフォルトエンコーディングがUTF-8でない

**7. Fixture errors**

症状: `fixture 'xxx' not found` または フィクスチャが正しく動作しない

```bash
# 解決策1: conftest.pyの場所を確認
# tests/conftest.py が存在することを確認

# 解決策2: フィクスチャのスコープを確認
@pytest.fixture(scope="function")  # または "module", "session"

# 解決策3: フィクスチャの依存関係を確認
def test_example(fixture1, fixture2):  # 順序が重要な場合がある
    pass
```

原因:
- conftest.pyが適切な場所にない
- フィクスチャ名のタイポ
- スコープの設定が不適切

**8. Async test errors**

症状: `RuntimeError: Event loop is closed` または非同期テストが失敗

```bash
# 解決策1: pytest-asyncioを使用
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# 解決策2: asyncio_modeを設定
# pyproject.tomlに追加:
# asyncio_mode = "auto"

# 解決策3: イベントループを明示的に管理
import asyncio

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

原因:
- pytest-asyncioが正しく設定されていない
- イベントループの管理が不適切
- 非同期コンテキストの問題

**9. Mock not working**

症状: モックが期待通りに動作しない、または実際の関数が呼ばれる

```bash
# 解決策1: パッチのパスを確認
# 間違い: @patch('module.function')
# 正しい: @patch('src.services.module.function')

# 解決策2: モックの戻り値を設定
mock_func.return_value = "expected"
# または
mock_func.side_effect = Exception("error")

# 解決策3: モックの呼び出しを確認
mock_func.assert_called_once()
mock_func.assert_called_with(expected_arg)
```

原因:
- パッチのパスが不正確
- モックの設定が不完全
- インポートのタイミング問題

**10. Test discovery issues**

症状: pytestがテストを見つけられない

```bash
# 解決策1: テストファイル名を確認
# test_*.py または *_test.py

# 解決策2: テスト関数名を確認
# test_* で始まる必要がある

# 解決策3: __init__.pyを確認
# tests/ディレクトリに__init__.pyが必要な場合がある

# 解決策4: 明示的にパスを指定
uv run pytest tests/unit/services/
```

原因:
- ファイル名や関数名の命名規則違反
- ディレクトリ構造の問題
- pytest設定の問題

### Debug Tips

**詳細ログを有効化**
```bash
# 最も詳細なログ
uv run pytest -vv -s --log-cli-level=DEBUG

# 標準出力を表示
uv run pytest -s

# 失敗時のみ詳細表示
uv run pytest --tb=short
```

**特定のテストをデバッグ**
```bash
# pdbデバッガーを使用
uv run pytest --pdb

# 最初の失敗で停止
uv run pytest -x

# 失敗時にpdbを起動
uv run pytest --pdb -x
```

**テスト実行時間を測定**
```bash
# 最も遅いテストを表示
uv run pytest --durations=10

# すべてのテストの実行時間を表示
uv run pytest --durations=0
```

## TDD Workflow

### Test-Driven Development Process

Papersmith Agentでは、TDD（Test-Driven Development）を推奨しています。

```
Requirements → Test Design → Red → Green → Refactor → Coverage Check → Done
                                ↑                    ↓
                                └────────────────────┘
```

### Step-by-Step TDD Flow

**1. Red Phase（失敗するテストを書く）**
```bash
# 1. テストファイルを作成
# tests/unit/services/test_new_feature.py

# 2. 期待される動作を定義
def test_new_feature():
    service = NewService()
    result = service.process("input")
    assert result == "expected_output"

# 3. テストを実行（失敗することを確認）
uv run pytest tests/unit/services/test_new_feature.py
# FAILED - NewService not found
```

**2. Green Phase（最小限の実装）**
```bash
# 1. 実装を追加
# src/services/new_service.py
class NewService:
    def process(self, input):
        return "expected_output"

# 2. テストを実行（成功することを確認）
uv run pytest tests/unit/services/test_new_feature.py
# PASSED
```

**3. Refactor Phase（コード改善）**
```bash
# 1. コードをリファクタリング
# - 重複を削除
# - 可読性を向上
# - パフォーマンスを最適化

# 2. テストが引き続き成功することを確認
uv run pytest tests/unit/services/test_new_feature.py
# PASSED
```

**4. Coverage Check（カバレッジ確認）**
```bash
# カバレッジを確認
uv run pytest --cov=src/services/new_service.py --cov-report=term

# 目標: 85%以上
# 不足している場合は追加テストを書く
```

### TDD Benefits

- ✅ **バグの早期発見**: 実装前にテストを書くことで、要件を明確化
- ✅ **リファクタリングの安全性**: テストがあるため、安心してコード改善可能
- ✅ **ドキュメント**: テストが実装の使用例として機能
- ✅ **設計の改善**: テスト可能なコードは、疎結合で保守しやすい

### Example: TDD in Practice

```python
# Step 1: Write failing test
def test_calculate_support_score():
    """Support Score計算のテスト"""
    service = RAGService()
    score = service.calculate_support_score(
        question="What is RAG?",
        results=[SearchResult(text="RAG is...", score=0.9)]
    )
    assert 0.0 <= score <= 1.0
    assert isinstance(score, float)

# Step 2: Run test (fails)
# $ uv run pytest tests/unit/services/test_rag_service.py::test_calculate_support_score
# FAILED - AttributeError: 'RAGService' object has no attribute 'calculate_support_score'

# Step 3: Implement minimal solution
class RAGService:
    def calculate_support_score(self, question: str, results: list) -> float:
        # Minimal implementation
        return 0.5

# Step 4: Run test (passes)
# $ uv run pytest tests/unit/services/test_rag_service.py::test_calculate_support_score
# PASSED

# Step 5: Refactor and add more tests
def test_calculate_support_score_high_relevance():
    """高関連性の場合のSupport Score"""
    service = RAGService()
    score = service.calculate_support_score(
        question="What is RAG?",
        results=[
            SearchResult(text="RAG is Retrieval-Augmented Generation...", score=0.95),
            SearchResult(text="RAG combines retrieval and generation...", score=0.90)
        ]
    )
    assert score > 0.7  # High relevance should give high score

def test_calculate_support_score_low_relevance():
    """低関連性の場合のSupport Score"""
    service = RAGService()
    score = service.calculate_support_score(
        question="What is RAG?",
        results=[
            SearchResult(text="Unrelated content...", score=0.3)
        ]
    )
    assert score < 0.5  # Low relevance should give low score
```

## Best Practices

### DO ✅

- **テストを書いてから実装（TDD）**: Red → Green → Refactor
- **各テストは1つの概念をテスト**: 単一責任原則
- **モックを適切に使用**: 外部依存を排除、テストを高速化
- **実際のAPI接続テストを少なくとも1つ含める**: 統合の信頼性確保
- **テスト名は明確で説明的に**: `test_calculate_support_score_with_empty_results`
- **フィクスチャを再利用**: `conftest.py`で共通フィクスチャを定義
- **カバレッジ目標を維持（85%+）**: 定期的にカバレッジをチェック
- **失敗したテストは即座に修正**: 技術的負債を蓄積しない

### DON'T ❌

- **テストをスキップしない**: `@pytest.mark.skip`は一時的な使用のみ
- **実装の詳細をテストしない**: 公開APIのみテスト
- **テスト間で状態を共有しない**: 各テストは独立して実行可能に
- **すべてをモックしない**: 実際のテストも必要（バランスが重要）
- **カバレッジのためだけにテストを書かない**: 意味のあるテストを書く
- **失敗するテストをコミットしない**: CI/CDが常にグリーンに
- **既存のテスト失敗を無視しない**: 新しい作業前に全テストをパス

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Summary

```bash
# 開発時の基本フロー
uv run pytest -m "not slow"  # 高速イテレーション
uv run pytest --cov=src      # カバレッジ確認
./scripts/coverage_report.sh # レポート生成

# コミット前
uv run pytest                # 全テスト実行
uv run pytest --cov=src --cov-fail-under=85  # カバレッジチェック
```

現在のテスト統計:
- **総テスト数**: 372 passed, 5 skipped
- **カバレッジ**: 91.20%
- **実行時間**: ~4分22秒
