---
name: ci-auto-fix
description: Automates CI execution, error recording, and fixing issues until CI passes. Invoke when user wants to run CI and automatically fix any errors encountered.
---

# CI Auto-Fix

This skill automates the process of running the local CI/CD pipeline, recording errors, and fixing issues until the CI passes successfully.

## When to Invoke

- User asks to run CI and fix any errors automatically
- User wants to execute the local CI process including code static analysis, unit tests, integration tests, and build verification
- User encounters CI failures and wants them fixed automatically

## Process Overview

1. **Run CI Script**: Execute `python Scripts/cicd.py` to run the full CI pipeline
2. **Analyze Results**: Check for any failures in code formatting, type checking, unit tests, or integration tests
3. **Record Errors**: Document all errors encountered during the CI run
4. **Fix Errors**: Automatically fix common errors:
   - Ruff formatting issues: Use `ruff check --fix .`
   - Type checking errors: Fix type annotations and imports
   - Test failures: Fix test cases, mocks, and assertions
5. **Re-run CI**: Execute the CI script again to verify fixes
6. **Repeat**: Continue the fix-and-verify cycle until all tests pass

## Common Error Patterns and Fixes

### 1. Ruff Formatting Errors

**Symptoms**: 
- `F401` - unused imports
- `E501` - line too long
- `F841` - unused variables

**Fix**:
```bash
uv run ruff check --fix .
```

### 2. Type Checking Errors

**Symptoms**:
- Missing type annotations
- Incorrect import paths
- `NoneType` attribute access

**Fix**:
- Add proper type hints to functions and variables
- Fix import statements
- Add proper null checks

### 3. Unit Test Errors

**Symptoms**:
- AssertionError in test assertions
- AttributeError on mocked objects
- Failed: DID NOT RAISE <exception>

**Fix**:
- Update test assertions to match expected behavior
- Fix mock configurations
- Update exception expectations

### 4. Integration Test Errors

**Symptoms**:
- Timeout errors
- Resource exhaustion
- Async/await issues

**Fix**:
- Add proper async/await handling
- Increase timeout values
- Fix resource cleanup

## Implementation Steps

### Step 1: Run Initial CI

```bash
python Scripts/cicd.py
```

### Step 2: Analyze Output

Look for error patterns in the output:
- `FAILED` for test failures
- `error:` for code errors
- `Error:` for runtime errors

### Step 3: Fix Identified Issues

Based on the error type, apply appropriate fixes:

**For Ruff errors**:
```bash
uv run ruff check --fix .
```

**For test failures**:
1. Read the failing test file
2. Identify the specific test case
3. Analyze the error message
4. Fix the test code or the source code
5. Re-run the specific test to verify

**For import/type errors**:
1. Check the source file
2. Add missing imports
3. Add type annotations
4. Verify with mypy or ruff

### Step 4: Re-run CI

```bash
python Scripts/cicd.py
```

### Step 5: Verify Success

Ensure all checks pass:
- Code formatting: ✓
- Type checking: ✓
- Unit tests: ✓
- Integration tests: ✓

## Example Workflow

1. User: "运行CI并自动修复所有错误"
2. Agent: Runs `python Scripts/cicd.py`
3. CI Output: Shows 2 failed tests
4. Agent: Analyzes failures:
   - `test_main_with_invalid_agent_flags` - Click Context issue
   - `test_answer_simple_question_success` - Mock configuration issue
5. Agent: Fixes both tests by updating test code
6. Agent: Re-runs CI
7. CI Output: All tests pass ✓
8. Agent: Reports success to user

## Notes

- Always use `uv run` for running Python tools
- Keep track of all changes made
- Verify fixes don't break other tests
- Document any manual fixes required
- Use TodoWrite tool to track progress