# CI/CD Optimization Strategy

## Overview

Papersmith AgentのCI/CDパイプラインは、開発速度と品質保証のバランスを取るために最適化されています。

## Problem Statement

### Before Optimization

```
Feature Branch Push → Run ALL Tests (10+ minutes)
├── Unit Tests (~1 min)
├── Integration Tests (~3 min)
└── E2E Tests (~3 min)
```

**課題:**
- featureブランチでの開発サイクルが遅い
- 全テストが毎回実行されるため、フィードバックが遅延
- CI実行時間が長く、開発者の待ち時間が増加

### After Optimization

```
Feature Branch Push → Run Unit Tests ONLY (~1 min)

Develop/Main Push → Run ALL Tests (~7 min)
├── Unit Tests (~1 min)
├── Integration Tests (~3 min)
└── E2E Tests (~3 min)
```

**改善:**
- featureブランチでの高速フィードバック（1分）
- 重要なブランチでは包括的なテスト
- CI実行時間を90%削減（feature開発時）

## Test Execution Strategy

### Tier 1: Unit Tests (Always Run)

**実行タイミング:**
- すべてのpush
- すべてのPR
- すべてのブランチ

**実行時間:** ~1分

**目的:**
- 高速フィードバック
- 基本的なコード品質保証
- 構文エラー・型エラーの早期発見

**カバレッジ:**
- Services: 90%+
- API Endpoints: 85%+
- Models: 95%+
- Clients: 80%+

### Tier 2: Integration Tests (Conditional)

**実行タイミング:**
- `main`ブランチへのpush
- `develop`ブランチへのpush
- `main`または`develop`へのPR
- 手動トリガー（workflow_dispatch）

**実行時間:** ~3分

**目的:**
- コンポーネント間の統合確認
- 外部API接続テスト
- データフロー検証

**カバレッジ:**
- API統合
- サービス間連携
- データベース操作

### Tier 3: E2E Tests (Conditional)

**実行タイミング:**
- `main`ブランチへのpush
- `develop`ブランチへのpush
- `main`または`develop`へのPR
- 手動トリガー（workflow_dispatch）

**実行時間:** ~3分

**目的:**
- エンドツーエンドのワークフロー検証
- ユーザーシナリオのテスト
- システム全体の動作確認

**カバレッジ:**
- 論文検索→ダウンロード→インデックス化
- RAGクエリ→回答生成
- UI操作フロー

## GitHub Actions Configuration

### Workflow File: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:
    inputs:
      run_full_tests:
        description: 'Run full test suite (including integration and E2E)'
        required: false
        default: 'false'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      # ... setup steps ...

      # Tier 1: Always run unit tests
      - name: Run unit tests
        run: uv run pytest tests/unit --cov=src --cov-report=xml -v

      # Tier 2 & 3: Conditional execution
      - name: Run integration tests
        if: |
          github.ref == 'refs/heads/main' ||
          github.ref == 'refs/heads/develop' ||
          github.base_ref == 'develop' ||
          github.base_ref == 'main' ||
          github.event.inputs.run_full_tests == 'true'
        run: uv run pytest tests/integration -v

      - name: Run E2E tests
        if: |
          github.ref == 'refs/heads/main' ||
          github.ref == 'refs/heads/develop' ||
          github.base_ref == 'develop' ||
          github.base_ref == 'main' ||
          github.event.inputs.run_full_tests == 'true'
        run: uv run pytest tests/e2e -v
```

## Conditional Logic Explanation

### Condition Breakdown

```yaml
if: |
  github.ref == 'refs/heads/main' ||           # mainブランチへのpush
  github.ref == 'refs/heads/develop' ||        # developブランチへのpush
  github.base_ref == 'develop' ||              # developへのPR
  github.base_ref == 'main' ||                 # mainへのPR
  github.event.inputs.run_full_tests == 'true' # 手動トリガー
```

### Scenarios

| Scenario | Unit | Integration | E2E |
|----------|------|-------------|-----|
| Feature branch push | ✅ | ❌ | ❌ |
| Feature → develop PR | ✅ | ✅ | ✅ |
| Develop branch push | ✅ | ✅ | ✅ |
| Develop → main PR | ✅ | ✅ | ✅ |
| Main branch push | ✅ | ✅ | ✅ |
| Manual trigger (full) | ✅ | ✅ | ✅ |

## Benefits

### 1. Faster Development Cycle

**Before:**
```
Write code → Push → Wait 10 minutes → Get feedback
```

**After:**
```
Write code → Push → Wait 1 minute → Get feedback
```

**Impact:** 90% reduction in CI wait time for feature development

### 2. Cost Optimization

**Before:**
- Every push: 10 minutes × N developers × M pushes/day
- Example: 5 developers × 10 pushes/day = 500 minutes/day

**After:**
- Feature pushes: 1 minute × 5 developers × 8 pushes/day = 40 minutes/day
- Important pushes: 7 minutes × 5 developers × 2 pushes/day = 70 minutes/day
- Total: 110 minutes/day

**Impact:** 78% reduction in CI execution time

### 3. Maintained Quality

- 重要なブランチ（main/develop）では全テスト実行
- PRマージ前に包括的なテスト
- 本番環境への影響なし

## Best Practices

### 1. Local Testing Before Push

```bash
# 開発中は頻繁にunit testを実行
uv run pytest tests/unit -v

# PRを作成する前に全テストを実行
uv run pytest tests/ -v
```

### 2. Use Manual Trigger When Needed

```bash
# GitHub UI から workflow_dispatch を使用
# "Run full test suite" を true に設定
```

### 3. Monitor Test Execution Time

```bash
# テスト実行時間を確認
uv run pytest tests/unit --durations=10

# 遅いテストを最適化
```

### 4. Keep Tests Fast

**Unit Tests:**
- モックを使用して外部依存を排除
- 1テスト < 1秒を目標

**Integration Tests:**
- 必要最小限の統合テスト
- 重複を避ける

**E2E Tests:**
- クリティカルパスのみ
- 並列実行を検討

## Monitoring and Metrics

### Key Metrics

1. **CI Execution Time**
   - Target: Feature branches < 2 minutes
   - Target: Main/develop < 10 minutes

2. **Test Success Rate**
   - Target: > 95% pass rate
   - Monitor flaky tests

3. **Coverage**
   - Target: Overall 85%+
   - Target: Services 90%+

4. **Feedback Time**
   - Target: < 5 minutes for feature branches
   - Target: < 15 minutes for main/develop

### GitHub Actions Insights

```
Settings → Actions → General → Workflow permissions
- Enable "Read and write permissions"
- Enable "Allow GitHub Actions to create and approve pull requests"
```

## Troubleshooting

### Issue: Tests Fail Only in CI

**Possible Causes:**
- Environment differences
- Missing dependencies
- Timing issues

**Solutions:**
```bash
# 1. Check Python version
python --version  # Should match CI (3.12)

# 2. Check dependencies
uv sync --frozen

# 3. Run tests with same flags as CI
uv run pytest tests/unit --cov=src --cov-report=xml -v
```

### Issue: Slow Test Execution

**Diagnosis:**
```bash
# Find slow tests
uv run pytest tests/ --durations=20
```

**Solutions:**
- Add `@pytest.mark.slow` to slow tests
- Use mocks for external dependencies
- Parallelize tests: `uv run pytest -n auto`

### Issue: Flaky Tests

**Diagnosis:**
```bash
# Run tests multiple times
uv run pytest tests/unit --count=10
```

**Solutions:**
- Fix timing dependencies
- Use proper fixtures
- Avoid shared state

## Future Improvements

### 1. Parallel Test Execution

```yaml
strategy:
  matrix:
    test-group: [unit, integration, e2e]
```

### 2. Test Result Caching

```yaml
- uses: actions/cache@v3
  with:
    path: .pytest_cache
    key: pytest-${{ hashFiles('tests/**') }}
```

### 3. Incremental Testing

- Only run tests affected by changes
- Use `pytest-testmon` or similar tools

### 4. Performance Benchmarking

- Add performance regression tests
- Monitor test execution trends

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Test Optimization Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)
