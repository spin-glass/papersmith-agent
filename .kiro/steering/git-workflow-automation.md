# Git Workflow Automation

## MANDATORY: Automated Branch Creation Before Starting Work

**CRITICAL RULE**: Before starting ANY new feature, fix, or refactor work, you MUST automatically create a new branch following the GitHub Flow branching strategy.

### Pre-Work Branch Creation Workflow

When the user asks you to start work on a feature, fix, or refactor, you MUST:

1. **Check current branch** using MCP tools
2. **Ensure you're on develop branch** (switch if needed)
3. **Pull latest changes** from develop
4. **Create a new feature branch** with appropriate naming
5. **Confirm branch creation** to the user
6. **Then begin the work**

### Branch Naming Convention

Follow these naming patterns based on work type:

- **Features**: `feature/<descriptive-name>`
  - Example: `feature/add-steering-automation`
  - Example: `feature/improve-test-coverage`
  
- **Bug Fixes**: `fix/<descriptive-name>`
  - Example: `fix/resolve-encoding-error`
  - Example: `fix/correct-test-failure`
  
- **Refactoring**: `refactor/<descriptive-name>`
  - Example: `refactor/simplify-git-workflow`
  - Example: `refactor/improve-error-handling`

- **Documentation**: `docs/<descriptive-name>`
  - Example: `docs/update-testing-guide`
  - Example: `docs/add-api-examples`

- **Tests**: `test/<descriptive-name>`
  - Example: `test/add-e2e-coverage`
  - Example: `test/improve-unit-tests`

### Automated Branch Creation Script

**Use MCP tools for ALL Git operations:**

```python
# 1. Check current status
status = mcp_git_git_status(repo_path=".")
print(f"Current status: {status}")

# 2. Switch to develop branch
mcp_git_git_checkout(repo_path=".", branch_name="develop")
print("✅ Switched to develop branch")

# 3. Pull latest changes (use bash - no MCP alternative)
execute_bash("git pull origin develop")
print("✅ Pulled latest changes from develop")

# 4. Create new feature branch
branch_name = "feature/descriptive-name"  # Customize based on work
mcp_git_git_create_branch(
    repo_path=".",
    branch_name=branch_name,
    base_branch="develop"
)
print(f"✅ Created new branch: {branch_name}")

# 5. Confirm to user
print(f"""
🎯 Ready to start work!

Branch: {branch_name}
Base: develop
Status: Ready for commits

You can now begin implementing the feature.
""")
```

### Complete Automated Workflow

When user requests work, follow this complete flow:

#### Step 1: Create Branch (MANDATORY - Do this FIRST)

```python
# Determine branch type and name
work_type = "feature"  # or "fix", "refactor", "docs", "test"
work_description = "add-steering-automation"  # descriptive kebab-case
branch_name = f"{work_type}/{work_description}"

# Check current branch
status = mcp_git_git_status(repo_path=".")

# Switch to develop
mcp_git_git_checkout(repo_path=".", branch_name="develop")

# Pull latest
execute_bash("git pull origin develop")

# Create new branch
mcp_git_git_create_branch(
    repo_path=".",
    branch_name=branch_name,
    base_branch="develop"
)

print(f"✅ Created branch: {branch_name}")
```

#### Step 2: Do the Work

- Implement features
- Write tests
- Fix bugs
- Update documentation

#### Step 3: Commit Changes (Use MCP)

```python
# Stage all changes
mcp_git_git_add(repo_path=".", files=["."])

# Commit with conventional commit message
mcp_git_git_commit(
    repo_path=".",
    message="""feat(steering): add automated branch creation workflow

- Add git-workflow-automation.md steering file
- Include pre-work branch creation rules
- Add complete Git flow automation examples
- Document MCP tool usage for Git operations

This ensures all work starts on a proper feature branch
following GitHub Flow branching strategy.
"""
)

print("✅ Changes committed")
```

#### Step 4: Push Branch (Use Bash or MCP)

```python
# Option 1: Simple bash push (acceptable)
execute_bash(f"git push -u origin {branch_name}")

# Option 2: MCP push files (more reliable)
# Get changed files and push using mcp_github_push_files
# (See development-guidelines.md for details)

print(f"✅ Pushed branch: {branch_name}")
```

#### Step 5: Create Pull Request (MANDATORY - Use MCP)

```python
# Get commit information
commit_count = execute_bash(f"git rev-list --count develop..{branch_name}")
commit_summary = execute_bash(f"git log develop..{branch_name} --oneline --no-decorate")

# Create PR using MCP (NEVER use gh pr create)
result = mcp_github_create_pull_request(
    owner="spin-glass",
    repo="papersmith-agent",
    title=f"feat: {work_description.replace('-', ' ')}",
    head=branch_name,
    base="develop",
    body=f"""## Summary

This PR implements {work_description.replace('-', ' ')}.

## Changes Included ({commit_count} commits)

```
{commit_summary}
```

## Testing Status

- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ E2E tests passing
- ✅ Code coverage: 85%+

## Checklist

- [x] Tests written and passing
- [x] Documentation updated
- [x] Code follows style guidelines
- [x] No breaking changes
- [x] Ready for review
"""
)

print(f"✅ Pull request created: {result['html_url']}")
```

#### Step 6: Review and Merge (Use MCP)

```python
# After review and approval, merge the PR
pr_number = result['number']

mcp_github_merge_pull_request(
    owner="spin-glass",
    repo="papersmith-agent",
    pullNumber=pr_number,
    merge_method="merge",  # or "squash" or "rebase"
    commit_title=f"feat: {work_description.replace('-', ' ')}",
    commit_message="Merged after successful review and testing"
)

print(f"✅ PR #{pr_number} merged successfully")
```

#### Step 7: Update Local Branches

```python
# Switch back to develop
mcp_git_git_checkout(repo_path=".", branch_name="develop")

# Pull latest changes (includes the merged PR)
execute_bash("git pull origin develop")

# Optional: Delete local feature branch
execute_bash(f"git branch -d {branch_name}")

print("✅ Local branches updated")
```

## Quick Reference: Complete Workflow

```python
# 1. CREATE BRANCH (MANDATORY FIRST STEP)
mcp_git_git_checkout(repo_path=".", branch_name="develop")
execute_bash("git pull origin develop")
mcp_git_git_create_branch(repo_path=".", branch_name="feature/my-feature", base_branch="develop")

# 2. DO THE WORK
# ... implement features, write tests, etc ...

# 3. COMMIT (Use MCP)
mcp_git_git_add(repo_path=".", files=["."])
mcp_git_git_commit(repo_path=".", message="feat: implement feature")

# 4. PUSH (Use bash or MCP)
execute_bash("git push -u origin feature/my-feature")

# 5. CREATE PR (Use MCP - MANDATORY)
mcp_github_create_pull_request(
    owner="spin-glass",
    repo="papersmith-agent",
    title="feat: my feature",
    head="feature/my-feature",
    base="develop",
    body="PR description..."
)

# 6. MERGE PR (Use MCP)
mcp_github_merge_pull_request(
    owner="spin-glass",
    repo="papersmith-agent",
    pullNumber=pr_number,
    merge_method="merge"
)

# 7. UPDATE LOCAL
mcp_git_git_checkout(repo_path=".", branch_name="develop")
execute_bash("git pull origin develop")
```

## Error Handling

### Branch Already Exists

```python
try:
    mcp_git_git_create_branch(
        repo_path=".",
        branch_name=branch_name,
        base_branch="develop"
    )
except Exception as e:
    if "already exists" in str(e):
        print(f"⚠️ Branch {branch_name} already exists")
        print("Switching to existing branch...")
        mcp_git_git_checkout(repo_path=".", branch_name=branch_name)
    else:
        raise
```

### PR Already Exists

```python
try:
    result = mcp_github_create_pull_request(...)
except Exception as e:
    if "already exists" in str(e):
        print("⚠️ PR already exists for this branch")
        # Get existing PR details
        prs = mcp_github_list_issues(
            owner="spin-glass",
            repo="papersmith-agent",
            state="OPEN"
        )
        # Find matching PR and display URL
    else:
        raise
```

## Integration with Kiro Workflow

When Kiro receives a request to start work:

1. **FIRST**: Automatically create branch (no user prompt needed)
2. **THEN**: Begin the actual work
3. **DURING**: Make commits using MCP tools
4. **AFTER**: Push branch and create PR using MCP
5. **FINALLY**: Report PR URL and status to user

## Success Criteria

Before marking work complete, verify:

- ✅ Work done on a feature branch (not develop or main)
- ✅ Branch follows naming convention
- ✅ All commits use conventional commit format
- ✅ All tests pass
- ✅ PR created using MCP tools
- ✅ PR includes comprehensive description
- ✅ PR merged successfully (if approved)
- ✅ Local develop branch updated

## CRITICAL REMINDERS

1. **ALWAYS create a branch BEFORE starting work**
2. **NEVER work directly on develop or main**
3. **ALWAYS use MCP tools for Git/GitHub operations**
4. **NEVER use `gh pr create` or `gh pr merge`**
5. **ALWAYS follow conventional commit format**
6. **ALWAYS create PR to develop (not main)**
7. **ALWAYS update local develop after merge**
