# Development Guidelines for Papersmith Agent

## Core Principles

1. **Test-Driven Development (TDD) - MANDATORY**: Write tests before implementation
   - Red: Write failing test first
   - Green: Implement minimal solution
   - Refactor: Improve code quality
   - Coverage: Verify 85%+ coverage
2. **Execute and Verify**: Always run code after writing it
3. **Fix Immediately**: Don't defer problems - fix them on the spot
4. **Coverage Target - MANDATORY**: Maintain 85%+ test coverage
   - Overall: 85%+
   - Services: 90%+
   - API Endpoints: 85%+
   - Models: 95%+
   - Clients: 80%+
5. **No Documentation Escape**: Don't create docs to avoid fixing issues
6. **Test Review - MANDATORY**: Complete test review checklist before marking tasks complete

## Task Completion Definition

A task is complete ONLY when ALL of these are met:

1. ✅ **Code Implemented**: All required code is written
2. ✅ **No Syntax Errors**: `getDiagnostics` shows no errors
3. ✅ **Executable**: Code actually runs without errors
4. ✅ **Verified**: Tested with actual execution (API calls, imports, pytest)
5. ✅ **Working**: Produces expected results

## File Operations: Use Kiro Tools, Not Bash Commands

**CRITICAL RULE**: Always use Kiro file tools, never bash commands for file operations.

### Why This Matters

**Use Kiro Tools** (`fsWrite`, `strReplace`, `fsAppend`):
- ✅ Atomic operations (no partial writes)
- ✅ Proper error handling
- ✅ Encoding handled correctly (UTF-8)
- ✅ Trackable in execution logs
- ✅ Can be reviewed before application
- ✅ Works consistently across all platforms

**Don't Use Bash Commands** (`cat`, `echo >`, `>>`, `echo`):
- ❌ Shell escaping issues (quotes, special characters)
- ❌ Encoding problems (especially with Japanese text)
- ❌ Platform-specific behavior (macOS vs Linux)
- ❌ No error recovery
- ❌ Harder to review changes
- ❌ Can create corrupted files
- ❌ **Large output causes hangs** (especially with heredoc `<<EOF`)

### Examples

**WRONG**:
```bash
# ❌ Don't do this - causes hangs with large content
cat > file.py << 'EOF'
def hello():
    print("こんにちは")
EOF

# ❌ Don't do this - shell escaping issues
echo "content" > file.txt
echo "more" >> file.txt

# ❌ Don't do this - large output hangs terminal
cat large_file.txt

# ❌ Don't do this - heredoc with large content hangs
cat > docs/guide.md << 'EOF'
[... 1000 lines of documentation ...]
EOF
```

**CORRECT**:
```python
# ✅ Do this - always use Kiro tools
fsWrite(path="file.py", text='def hello():\n    print("こんにちは")')

# ✅ Do this - for appending
fsWrite(path="file.txt", text="content\n")
fsAppend(path="file.txt", text="more\n")

# ✅ Do this - for reading (if needed)
readFile(path="large_file.txt", explanation="...")

# ✅ Do this - for large documentation
fsWrite(path="docs/guide.md", text="""
[... all content as Python string ...]
""")
```

### Critical: Avoid Large Stdout Operations

**NEVER use commands that produce large stdout output:**
- ❌ `cat > file << 'EOF' ... EOF` (heredoc with large content)
- ❌ `echo "$(cat large_file)"` (command substitution with large output)
- ❌ `cat large_file.txt` (displaying large files)
- ❌ Any bash command that outputs >1000 lines

**These operations cause terminal hangs and execution timeouts.**

**ALWAYS use Kiro file tools instead:**
- ✅ `fsWrite()` - for creating files
- ✅ `fsAppend()` - for appending to files
- ✅ `strReplace()` - for modifying files
- ✅ `readFile()` - for reading files

## Mandatory Verification Steps

### For ALL Python Files

```bash
# 1. Syntax check
python3 -m py_compile src/api/main.py

# 2. Import test
python3 -c "import sys; sys.path.insert(0, 'src'); from api.main import app; print('✓ Import successful')"

# 3. If encoding error: Add to file top
# -*- coding: utf-8 -*-

# 4. If ModuleNotFoundError: Install package
pip3 install <missing-package>
```

### For API Endpoints

```bash
# Test with curl (if server running)
curl -X POST http://localhost:8000/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

### For Streamlit UI Pages

```bash
# Safe import test (doesn't hang)
timeout 5 python3 -c "
import sys
sys.path.insert(0, 'ui')
import importlib.util
spec = importlib.util.spec_from_file_location('page', 'ui/pages/2_rag.py')
module = importlib.util.module_from_spec(spec)
sys.modules['page'] = module
spec.loader.exec_module(module)
print('✓ Import successful')
"
```

### For Tests

```bash
# Run the actual tests
pytest tests/unit/test_file.py -v
pytest tests/integration/ -v
```

## Streamlit UI Safety Rules

**CRITICAL**: Streamlit files execute on import. Follow this pattern:

```python
import streamlit as st

# Page config MUST be first (top-level OK)
st.set_page_config(title="...", icon="...", layout="wide")

# CSS as string constant
CUSTOM_CSS = """<style>...</style>"""

# ALL UI code in main()
def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.title("...")
    # ... rest of UI code

if __name__ == "__main__":
    main()
```

**Never** put `st.title()`, `st.markdown()`, etc. at top level!

## Testing Strategy

### Unit Tests
- Test individual functions/classes with mocks
- Focus on core logic
- Keep tests simple and fast
- **Mock by default** for external dependencies (APIs, heavy models)
- Use `unittest.mock.patch` or `unittest.mock.Mock`

### Integration Tests
- Test component interactions
- **Use real APIs for connectivity tests** (mark with `@pytest.mark.slow`)
- Use actual Embedding models (lightweight)
- Mock heavy components (LLM inference)
- Verify end-to-end flows work correctly

### API Connectivity Tests
- **ALWAYS include at least one real API test** per external service
- Use `.env` file for API keys (GOOGLE_API_KEY, OPENAI_API_KEY)
- Mark as `@pytest.mark.slow` and `@pytest.mark.integration`
- Test basic connectivity and response format
- Example: Test Gemini API with a simple prompt
- Example: Test OpenAI API with a simple embedding request
- **Purpose**: Verify our code works with actual APIs, not just mocks

### Property-Based Tests
- Test universal properties across many inputs
- Use PBT library specified in design doc
- Run minimum 100 iterations
- Tag with: `**Feature: {name}, Property {N}: {text}**`

### E2E Tests
- Mock heavy components (LLM, external APIs)
- Verify pipeline flow, not full functionality
- Keep lightweight

### Test Organization
```
tests/
├── unit/              # Fast, mocked tests
├── integration/       # Component interaction tests (some mocked)
├── e2e/              # End-to-end workflow tests
└── connectivity/     # Real API connectivity tests (slow)
```

## Error Handling

### CRITICAL: Never Ignore Existing Errors or Warnings

**MANDATORY RULE**: Before starting any new task, you MUST:

1. **Run full test suite**: `uv run pytest tests/ -v`
2. **Check for failures**: If ANY tests fail, fix them FIRST
3. **Check for warnings**: Address deprecation warnings and other warnings
4. **Verify diagnostics**: Run `getDiagnostics` on modified files
5. **Only proceed** when all existing tests pass and warnings are addressed

**Why This Matters**:
- Ignoring existing errors creates technical debt
- Broken tests indicate broken functionality
- Warnings often become errors in future versions
- Clean baseline ensures new changes don't break existing code

### When Errors Occur

1. **Read the error message** - understand what failed
2. **Identify the cause** - import, syntax, logic, dependency
3. **Fix immediately** - don't defer or document
4. **Re-run** - verify the fix works
5. **Repeat** - until it works

### Common Issues

**Encoding Errors**:
```python
# Add to top of file
# -*- coding: utf-8 -*-
```

**Import Errors**:
```bash
# Install missing package
pip3 install <package>
# Verify in requirements.txt
```

**Streamlit Hangs**:
- Use `timeout` command
- Use `importlib` for safe imports
- Never run `streamlit run` in tests

## What NOT to Do

### Critical Violations (Will Break Things)

❌ **Use bash commands for file operations** (`cat`, `echo >`, `>>`)
  - Causes encoding issues, shell escaping problems, platform inconsistencies
  - **ALWAYS use fsWrite, strReplace, fsAppend instead**

❌ **Ignore existing test failures or errors**
  - Creates technical debt, breaks functionality
  - **MUST fix before starting new work**

❌ **Ignore warnings** (deprecation, import, etc.)
  - Warnings become errors in future versions
  - **MUST address all warnings**

❌ **Start new work when existing tests are broken**
  - Compounds problems, makes debugging harder
  - **MUST have clean baseline**

### Common Mistakes

❌ Mark task complete without running code
❌ Assume code works without testing
❌ Skip verification steps
❌ Create documentation instead of fixing issues
❌ Ignore encoding errors
❌ Ignore dependency errors
❌ Use `python` instead of `python3` (may be Python 2.7)
❌ Put Streamlit UI code at top level
❌ Use `rm -rf` without `-f` flag (causes interactive prompts)
❌ Use commands that require user input (yes/no prompts)
❌ **Only use mocks without any real API connectivity tests**

## What TO Do

✅ **Check and fix ALL existing test failures before starting new work**
✅ **Address ALL warnings (deprecation, import, etc.)**
✅ **Include at least one real API connectivity test per service**
✅ Run code immediately after writing
✅ Use `getDiagnostics` for syntax check
✅ Test imports with `python3 -c "import ..."`
✅ Fix errors on the spot
✅ Install missing dependencies
✅ Add encoding declarations for Japanese comments
✅ Use `timeout` for potentially hanging commands
✅ Verify with actual execution (curl, pytest, etc.)
✅ **ALWAYS use Kiro file tools for file operations**:
  - `fsWrite` for creating new files
  - `strReplace` for modifying existing files
  - `fsAppend` for appending to files
  - **NEVER use bash commands** (`cat`, `echo >`, `>>`) for file creation/modification
✅ Always use `rm -rf` with `-f` flag to avoid prompts
✅ Use non-interactive commands only (no yes/no prompts)
✅ **Use .env file for API keys in tests**
✅ **Balance mocks (fast) with real API tests (confidence)**

## Standard Task Flow (TDD)

1. **Start**: Mark task `in_progress`
2. **Red**: Write failing test first
   - Define expected behavior in test
   - Run test to confirm it fails
   - Verify test fails for the right reason
3. **Green**: Write minimal implementation
   - Make the test pass
   - Don't over-engineer
   - Run test to confirm it passes
4. **Refactor**: Improve code quality
   - Remove duplication
   - Improve readability
   - Ensure tests still pass
5. **Check Coverage**: Run `uv run pytest --cov=src`
   - Verify coverage meets target (85%+)
   - Add tests for uncovered code
6. **Complete**: Mark task `completed`

## TDD Workflow

```
Requirements → Test Design → Red → Green → Refactor → Coverage Check → Done
                                ↑                    ↓
                                └────────────────────┘
```

## Documentation Maintenance

### Update on Task Completion

- `docs/PROJECT_STATUS.md` - Update task checkbox and progress (MANDATORY)
- `.kiro/specs/papersmith-agent/tasks.md` - Update task checkbox
- `README.md` - If user-facing features changed
- `ui/README.md` - If UI implementation changed

### Never Create

- Task completion summaries with full details
- Verification reports
- Temporary implementation notes
- Phase-specific testing documents

### Link, Don't Duplicate

- Write detailed content ONCE
- Reference with links elsewhere
- Keep summaries brief

## Phase-Specific Notes

### Phase 1 (Complete)
- All core RAG functionality implemented
- 29/29 tests passing
- Docker environment ready

### Phase 2 (Current)
- Focus on Streamlit UI
- Verify imports safely (use `timeout`)
- Test API integration with curl
- Keep UI code in `main()` function

### Phase 3 (Future)
- RAG enhancements (Support Score, HyDE, etc.)
- Streaming responses
- Graceful degradation

### Phase 4 (Future)
- Multi-agent system with LangGraph
- Advanced features (comparison, digest, etc.)

## Branching Strategy

Papersmith Agent uses **GitHub Flow** with a develop branch:

```
main (production-ready)
  ↑
  └── develop (integration branch)
       ↑
       ├── feature/* (new features)
       ├── fix/* (bug fixes)
       └── refactor/* (code improvements)
```

### Branch Types

- **main**: Production-ready code, protected, requires PR + all tests
- **develop**: Integration branch, requires PR + all tests (recommended)
- **feature/**: New features, branch from develop, merge to develop
- **fix/**: Bug fixes, branch from develop (or main for hotfixes)
- **refactor/**: Code improvements, branch from develop

### Workflow

```bash
# Start new feature
git checkout develop && git pull origin develop
git checkout -b feature/my-feature

# Commit with conventional commits
git commit -m "feat(scope): description"

# Push and create PR to develop
git push origin feature/my-feature
```

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `ci`: CI/CD changes

See [docs/BRANCHING_STRATEGY.md](../docs/BRANCHING_STRATEGY.md) for detailed workflows.

## Quick Reference

```bash
# BEFORE STARTING ANY TASK: Check existing tests
uv run pytest tests/ -v  # Must pass before starting new work

# TDD: Write test first
# 1. Create test file: tests/unit/test_feature.py
# 2. Write failing test
# 3. Run: uv run pytest tests/unit/test_feature.py
# 4. Implement feature
# 5. Run test again (should pass)

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test type
uv run pytest tests/unit -m unit
uv run pytest tests/integration -m integration
uv run pytest tests/e2e -m e2e

# Run slow/connectivity tests (real APIs)
uv run pytest -m slow
uv run pytest tests/connectivity/ -v

# Skip slow tests (for fast iteration)
uv run pytest -m "not slow"

# Run specific test file
uv run pytest tests/unit/services/test_llm_service.py

# Run specific test function
uv run pytest tests/unit/services/test_llm_service.py::test_build_prompt

# Run in parallel (faster)
uv run pytest -n auto

# Re-run failed tests only
uv run pytest --lf

# Show warnings
uv run pytest -v -W default

# Syntax check
python3 -m py_compile file.py

# Import test
python3 -c "import module; print('OK')"

# API test
curl http://localhost:8000/health

# Check diagnostics
# Use getDiagnostics tool in Kiro

# File operations (ALWAYS use Kiro tools)
# ✅ Create file: fsWrite(path="file.py", text="content")
# ✅ Modify file: strReplace(path="file.py", oldStr="old", newStr="new")
# ✅ Append file: fsAppend(path="file.py", text="more content")
# ❌ NEVER: cat > file.py, echo "text" > file.py
```

## Test Review Checklist

Before marking any task complete or submitting a pull request, verify ALL items in this checklist:

### Pre-Implementation Checklist

- [ ] **Existing tests pass**: Run `uv run pytest tests/ -v` - all tests must pass
- [ ] **No warnings**: Address all deprecation and import warnings
- [ ] **Clean baseline**: No broken tests or pending fixes

### Test Implementation Checklist

- [ ] **TDD followed**: Tests written before implementation (Red → Green → Refactor)
- [ ] **Test coverage**: New code has 85%+ coverage
- [ ] **Test types**:
  - [ ] Unit tests for core logic (mocked dependencies)
  - [ ] Integration tests for component interactions
  - [ ] At least 1 real API connectivity test (if applicable)
  - [ ] Property-based tests for universal properties (if applicable)
- [ ] **Test quality**:
  - [ ] Tests are independent (no shared state)
  - [ ] Tests are deterministic (no random failures)
  - [ ] Tests are fast (unit tests < 1s, integration < 10s)
  - [ ] Tests have clear, descriptive names
  - [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] **Test markers**: Appropriate markers applied (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`)
- [ ] **Fixtures**: Reusable fixtures in `conftest.py` where appropriate
- [ ] **Mocking**: External dependencies properly mocked in unit tests
- [ ] **Assertions**: Clear, specific assertions (not just `assert result`)

### Code Quality Checklist

- [ ] **No syntax errors**: `getDiagnostics` shows no errors
- [ ] **Imports work**: `python3 -c "import module"` succeeds
- [ ] **Code runs**: Actual execution produces expected results
- [ ] **Encoding**: UTF-8 encoding declaration for files with Japanese text
- [ ] **Dependencies**: All required packages in `pyproject.toml`
- [ ] **Type hints**: Functions have type annotations
- [ ] **Docstrings**: Public functions have docstrings
- [ ] **Error handling**: Appropriate error handling and logging

### Coverage Checklist

- [ ] **Overall coverage**: 85%+ (run `uv run pytest --cov=src --cov-report=term`)
- [ ] **Component coverage**:
  - [ ] Services: 90%+
  - [ ] API Endpoints: 85%+
  - [ ] Models: 95%+
  - [ ] Clients: 80%+
- [ ] **Coverage report**: HTML report generated and reviewed
- [ ] **Uncovered lines**: Justified (e.g., error handling, defensive code)

### Integration Checklist

- [ ] **All tests pass**: `uv run pytest` - 100% pass rate
- [ ] **No test skips**: No `@pytest.mark.skip` without justification
- [ ] **Parallel execution**: Tests pass with `uv run pytest -n auto`
- [ ] **CI/CD ready**: Tests pass in CI environment
- [ ] **Documentation updated**: README.md, docs/TESTING.md if needed

### Final Verification

- [ ] **Clean run**: `uv run pytest --cov=src --cov-fail-under=85` passes
- [ ] **No regressions**: Existing functionality still works
- [ ] **Performance**: No significant performance degradation
- [ ] **Logs clean**: No unexpected errors or warnings in logs

### Before Commit

```bash
# Run this command sequence before committing:
uv run pytest --cov=src --cov-report=term --cov-fail-under=85
uv run pytest -n auto  # Verify parallel execution
uv run pytest -m slow -v  # Verify connectivity tests (if applicable)
```

### Review Questions

Ask yourself these questions before marking complete:

1. **Would I trust this code in production?**
2. **Can another developer understand these tests?**
3. **Do the tests actually verify the requirements?**
4. **Are there any edge cases I haven't tested?**
5. **Would these tests catch regressions?**
6. **Is the test coverage meaningful or just for numbers?**
7. **Have I tested error conditions and edge cases?**
8. **Do the tests run fast enough for TDD workflow?**

## Success Criteria

Code is ready when:
- ✅ **ALL existing tests pass** (no regressions)
- ✅ **No new warnings introduced**
- ✅ **At least one real API connectivity test** (if working with external APIs)
- ✅ **Test Review Checklist completed** (all items checked)
- ✅ No syntax errors
- ✅ Imports successfully
- ✅ Runs without errors
- ✅ Produces expected output
- ✅ New tests pass (if applicable)
- ✅ Coverage target met (85%+)

Only then mark the task complete.

## API Testing Best Practices

### When to Use Mocks vs Real APIs

**Use Mocks (Unit Tests)**:
- Testing error handling
- Testing edge cases
- Testing internal logic
- Fast iteration during development
- CI/CD pipelines (fast feedback)

**Use Real APIs (Connectivity Tests)**:
- Verifying API integration works
- Testing request/response format
- Catching API changes
- Building confidence in production readiness
- At least 1 test per external service

### Example: Gemini API Test

```python
@pytest.mark.slow
@pytest.mark.integration
async def test_gemini_api_connectivity():
    """Real Gemini API connectivity test"""
    import os
    from src.services.llm_service import LLMService
    from src.models.config import LLMConfig

    # Skip if no API key
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")

    config = LLMConfig(backend="gemini")
    service = LLMService(config)
    await service.load_model()

    # Simple test prompt
    answer = await service.generate(
        question="What is 2+2?",
        context="Basic math question"
    )

    assert len(answer) > 0
    assert isinstance(answer, str)
```

### Running Tests Strategically

```bash
# Fast iteration (skip slow tests)
uv run pytest -m "not slow"

# Before commit (run all tests)
uv run pytest

# Check connectivity (run slow tests only)
uv run pytest -m slow -v
```


## GitHub Flow Automation

### Branch Management and PR Creation

When working with the GitHub Flow branching strategy, follow these automated steps:

#### 1. Develop Branch Push

After completing work on the develop branch:

```bash
# Push develop branch to remote
git push -u origin develop
```

#### 2. Create Pull Request to Main

Use GitHub CLI to create a PR from develop to main:

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Login: gh auth login

# Create PR from develop to main
gh pr create \
  --base main \
  --head develop \
  --title "Release: Merge develop to main" \
  --body "$(cat <<EOF
## Summary
Merge latest development changes from develop branch to main.

## Changes Included
$(git log main..develop --oneline --no-decorate)

## Testing
- ✅ All unit tests passing
- ✅ Integration tests passing (on develop)
- ✅ E2E tests passing (on develop)
- ✅ Code coverage maintained at 85%+

## Checklist
- [x] All tests pass
- [x] Documentation updated
- [x] No breaking changes
- [x] Ready for production deployment
EOF
)"
```

#### 3. Automated PR Creation Script

For convenience, create a script to automate the entire process:

```bash
#!/bin/bash
# scripts/create_release_pr.sh

set -e

echo "🚀 Creating release PR from develop to main..."

# Ensure we're on develop branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "develop" ]; then
    echo "❌ Error: Must be on develop branch"
    exit 1
fi

# Ensure develop is up to date
echo "📥 Pulling latest changes..."
git pull origin develop

# Push develop to remote
echo "📤 Pushing develop to remote..."
git push -u origin develop

# Get commit summary
commit_summary=$(git log main..develop --oneline --no-decorate | head -20)
commit_count=$(git rev-list --count main..develop)

# Create PR
echo "📝 Creating pull request..."
gh pr create \
  --base main \
  --head develop \
  --title "Release: Merge develop to main ($commit_count commits)" \
  --body "## Summary

This PR merges the latest development changes from \`develop\` to \`main\`.

## Changes Included ($commit_count commits)

\`\`\`
$commit_summary
\`\`\`

## Testing Status

- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ E2E tests passing
- ✅ Code coverage: 85%+

## Pre-merge Checklist

- [x] All tests pass on develop branch
- [x] Documentation updated
- [x] No breaking changes identified
- [x] CI/CD pipeline successful
- [x] Ready for production deployment

## Deployment Notes

After merging:
1. Tag the release: \`git tag -a v1.x.x -m 'Release version 1.x.x'\`
2. Push tags: \`git push origin v1.x.x\`
3. Monitor production deployment
4. Update changelog if needed
"

echo "✅ Pull request created successfully!"
echo "🔗 View PR: $(gh pr view --web)"
```

#### 4. Usage in Development Workflow

**Automated Workflow:**

```bash
# 1. Complete work on develop branch
git checkout develop
git add .
git commit -m "feat: complete feature implementation"

# 2. Run automated PR creation
./scripts/create_release_pr.sh

# 3. Review and merge PR on GitHub
# - Check CI/CD status
# - Review changes
# - Approve and merge
```

#### 5. Kiro Agent Automation

When Kiro completes work on develop branch, it should automatically:

1. **Push develop branch**
   ```bash
   git push -u origin develop
   ```

2. **Create PR using GitHub CLI**
   ```bash
   gh pr create --base main --head develop --title "Release: ..." --body "..."
   ```

3. **Report status to user**
   - PR URL
   - Commit count
   - Test status
   - Next steps

#### 6. Error Handling

**If GitHub CLI is not installed:**
```bash
echo "⚠️ GitHub CLI not found. Please install:"
echo "  macOS: brew install gh"
echo "  Linux: See https://github.com/cli/cli#installation"
exit 1
```

**If not authenticated:**
```bash
if ! gh auth status &>/dev/null; then
    echo "⚠️ Not authenticated with GitHub. Please run:"
    echo "  gh auth login"
    exit 1
fi
```

**If PR already exists:**
```bash
if gh pr list --head develop --base main | grep -q .; then
    echo "⚠️ PR already exists from develop to main"
    echo "🔗 View existing PR: $(gh pr view develop --web)"
    exit 0
fi
```

### Quick Reference Commands

```bash
# Check if GitHub CLI is installed
gh --version

# Login to GitHub
gh auth login

# Check current PRs
gh pr list

# View PR status
gh pr status

# Create PR (interactive)
gh pr create

# Create PR (automated)
gh pr create --base main --head develop --title "Title" --body "Body"

# View PR in browser
gh pr view --web

# Merge PR (after approval)
gh pr merge --merge --delete-branch
```

### Integration with Kiro Workflow

When Kiro completes a series of commits on develop:

1. ✅ All tests pass
2. ✅ Documentation updated
3. ✅ Code coverage maintained
4. 🤖 **Automatically push develop**
5. 🤖 **Automatically create PR to main**
6. 📢 **Notify user with PR link**
7. ⏳ **Wait for user approval and merge**

This automation ensures:
- Consistent PR format
- Complete change documentation
- Proper testing verification
- Streamlined release process
