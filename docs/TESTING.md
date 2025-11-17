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

```yaml
- name: Run tests with coverage
  run: |
    uv run pytest --cov=src --cov-report=xml --cov-fail-under=85

- name: Upload to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
```

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
```bash
# タイムアウトを延長
uv run pytest --timeout=600

# 特定のテストをスキップ
uv run pytest -m "not slow"
```

**2. Import errors**
```bash
# PYTHONPATHを設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run pytest
```

**3. Coverage not accurate**
```bash
# キャッシュをクリア
rm -rf .pytest_cache .coverage htmlcov/
uv run pytest --cov=src --cov-report=html
```

**4. Parallel execution issues**
```bash
# 並列実行を無効化
uv run pytest -n 0
```

## Best Practices

### DO ✅

- テストを書いてから実装（TDD）
- 各テストは1つの概念をテスト
- モックを適切に使用（外部依存を排除）
- 実際のAPI接続テストを少なくとも1つ含める
- テスト名は明確で説明的に
- フィクスチャを再利用
- カバレッジ目標を維持（85%+）

### DON'T ❌

- テストをスキップしない
- 実装の詳細をテストしない
- テスト間で状態を共有しない
- すべてをモックしない（実際のテストも必要）
- カバレッジのためだけにテストを書かない
- 失敗するテストをコミットしない

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
