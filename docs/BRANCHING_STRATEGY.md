# Branching Strategy - GitHub Flow

## Overview

Papersmith Agentは**GitHub Flow**を採用しています。これはシンプルで効果的なブランチ戦略で、継続的デリバリーに最適です。

## Branch Structure

```
main (production-ready)
  ↑
  └── develop (integration branch)
       ↑
       ├── feature/xxx (feature branches)
       ├── fix/xxx (bug fix branches)
       └── refactor/xxx (refactoring branches)
```

### Main Branches

#### `main`
- **目的**: 本番環境にデプロイ可能な安定版コード
- **保護**: 直接pushは禁止、PRのみ
- **テスト**: 全テスト（Unit + Integration + E2E）が必須
- **マージ元**: `develop`ブランチからのPRのみ

#### `develop`
- **目的**: 開発中の統合ブランチ
- **保護**: 直接pushは推奨されない、PRを推奨
- **テスト**: 全テスト（Unit + Integration + E2E）が実行される
- **マージ元**: feature/fix/refactorブランチからのPR

### Working Branches

#### Feature Branches (`feature/*`)
- **命名**: `feature/short-description`
- **例**: `feature/add-support-score`, `feature/streaming-response`
- **作成元**: `develop`
- **マージ先**: `develop`
- **テスト**: Unit testsのみ（高速フィードバック）

#### Bug Fix Branches (`fix/*`)
- **命名**: `fix/short-description`
- **例**: `fix/pdf-extraction-error`, `fix/memory-leak`
- **作成元**: `develop`（または緊急時は`main`）
- **マージ先**: `develop`（または緊急時は`main`）
- **テスト**: Unit testsのみ（高速フィードバック）

#### Refactoring Branches (`refactor/*`)
- **命名**: `refactor/short-description`
- **例**: `refactor/modernize-type-hints`, `refactor/extract-service`
- **作成元**: `develop`
- **マージ先**: `develop`
- **テスト**: Unit testsのみ（高速フィードバック）

## Workflow

### 1. Feature Development

```bash
# 1. developブランチから最新を取得
git checkout develop
git pull origin develop

# 2. featureブランチを作成
git checkout -b feature/my-new-feature

# 3. 開発とコミット
git add .
git commit -m "feat: add new feature"

# 4. pushしてPR作成
git push origin feature/my-new-feature
# GitHub上でdevelopへのPRを作成
```

### 2. Bug Fix

```bash
# 1. developブランチから最新を取得
git checkout develop
git pull origin develop

# 2. fixブランチを作成
git checkout -b fix/bug-description

# 3. 修正とコミット
git add .
git commit -m "fix: resolve bug description"

# 4. pushしてPR作成
git push origin fix/bug-description
# GitHub上でdevelopへのPRを作成
```

### 3. Release to Production

```bash
# 1. developが安定していることを確認
# - 全テストがパス
# - コードレビュー完了
# - 動作確認完了

# 2. GitHub上でdevelopからmainへのPRを作成
# - タイトル: "Release: v1.x.x"
# - 変更内容のサマリーを記載

# 3. PRマージ後、mainブランチにタグを付ける
git checkout main
git pull origin main
git tag -a v1.x.x -m "Release version 1.x.x"
git push origin v1.x.x
```

### 4. Hotfix (緊急修正)

```bash
# 1. mainブランチから直接fixブランチを作成
git checkout main
git pull origin main
git checkout -b fix/critical-bug

# 2. 修正とコミット
git add .
git commit -m "fix: resolve critical bug"

# 3. mainへのPRを作成
git push origin fix/critical-bug
# GitHub上でmainへのPRを作成

# 4. マージ後、developにもマージ
git checkout develop
git merge main
git push origin develop
```

## CI/CD Integration

### Test Execution Strategy

GitHub Actionsは以下のルールでテストを実行します：

#### Unit Tests (常に実行)
- **実行タイミング**: すべてのpushとPR
- **実行時間**: ~1分
- **目的**: 高速フィードバック

#### Integration + E2E Tests (条件付き実行)
- **実行タイミング**:
  - `main`ブランチへのpush
  - `develop`ブランチへのpush
  - `main`または`develop`へのPR
  - 手動トリガー（workflow_dispatch）
- **実行時間**: ~6分
- **目的**: 包括的な品質保証

### Branch Protection Rules

#### `main`ブランチ
- ✅ Require pull request reviews (1 approval)
- ✅ Require status checks to pass
  - Unit tests
  - Integration tests
  - E2E tests
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes

#### `develop`ブランチ
- ✅ Require status checks to pass
  - Unit tests
  - Integration tests
  - E2E tests
- ✅ Require branches to be up to date
- ⚠️ Require pull request reviews (推奨)
- ❌ Allow force pushes

## Commit Message Convention

Conventional Commitsを使用します：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードフォーマット（機能変更なし）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・補助ツール変更
- `ci`: CI設定変更

### Examples

```bash
# 新機能
git commit -m "feat(rag): add support score calculation"

# バグ修正
git commit -m "fix(pdf): resolve text extraction encoding issue"

# ドキュメント
git commit -m "docs: update API documentation"

# リファクタリング
git commit -m "refactor: modernize type hints to Python 3.9+ syntax"

# テスト
git commit -m "test: add unit tests for data models"

# CI
git commit -m "ci: optimize test execution strategy"
```

## Best Practices

### 1. Keep Branches Short-Lived
- featureブランチは1-3日以内にマージ
- 長期ブランチは避ける（マージコンフリクトのリスク）

### 2. Frequent Integration
- developへ頻繁にマージ
- 小さな変更を積み重ねる

### 3. Always Pull Before Creating Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/new-feature
```

### 4. Keep Commits Atomic
- 1コミット = 1つの論理的変更
- コミットメッセージは明確に

### 5. Test Before PR
```bash
# ローカルでテスト実行
uv run pytest tests/unit -v

# カバレッジ確認
uv run pytest --cov=src --cov-report=term
```

### 6. Write Descriptive PR Descriptions
- 何を変更したか
- なぜ変更したか
- どのようにテストしたか

## Troubleshooting

### Merge Conflicts

```bash
# 1. developの最新を取得
git checkout develop
git pull origin develop

# 2. featureブランチにマージ
git checkout feature/my-feature
git merge develop

# 3. コンフリクトを解決
# エディタでコンフリクトを修正

# 4. コミット
git add .
git commit -m "merge: resolve conflicts with develop"
```

### Accidentally Committed to Wrong Branch

```bash
# 1. コミットを取り消し（変更は保持）
git reset --soft HEAD~1

# 2. 正しいブランチに切り替え
git checkout correct-branch

# 3. 再度コミット
git add .
git commit -m "your commit message"
```

## References

- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project)
