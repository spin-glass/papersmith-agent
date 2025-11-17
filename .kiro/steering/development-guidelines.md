# Development Guidelines for Papersmith Agent

## Core Principles

1. **Test-Driven Development (TDD)**: Write tests before implementation
2. **Execute and Verify**: Always run code after writing it
3. **Fix Immediately**: Don't defer problems - fix them on the spot
4. **Coverage Target**: Maintain 85%+ test coverage
5. **No Documentation Escape**: Don't create docs to avoid fixing issues

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

## Success Criteria

Code is ready when:
- ✅ **ALL existing tests pass** (no regressions)
- ✅ **No new warnings introduced**
- ✅ **At least one real API connectivity test** (if working with external APIs)
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
