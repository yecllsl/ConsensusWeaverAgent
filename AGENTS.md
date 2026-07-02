# ConsensusWeaverAgent — AGENTS.md

## Project

MCP Server that uses Playwright browser automation to ask questions to 5 Chinese AI web platforms (豆包, 智谱清言, DeepSeek, 千问, 元宝) in parallel and collect answers.

**Entrypoint:** `mcp_server.py` — exposes 4 tools via FastMCP: `ask_ai`, `list_platforms`, `check_login`, `capture_screenshot`.

## Setup

```sh
pip install -r requirements.txt
python -m playwright install chromium  # downloads Chromium binary
```

`config.yaml` must exist at project root at runtime.

## Run

```sh
python mcp_server.py
```

## Test

```sh
python -m pytest                                          # all tests
python -m pytest -m "not slow and not integration and not e2e"  # unit only (fast, no browser)
python -m pytest tests/unit/test_config.py -v             # single file
python -m pytest -m e2e -v                                # E2E only
```

- `asyncio_mode = auto` in `pytest.ini` — no need for `@pytest.mark.asyncio` on per-test basis (though existing tests use it).
- Unit tests mock Playwright entirely. Integration/E2E tests require Playwright Chromium installed.
- `tests/conftest.py` provides `test_config` and `test_config_partial` fixtures with isolated temp directories.
- Root `conftest.py` adds project root to `sys.path` so imports work directly.

## Architecture

```
mcp_server.py  →  PlatformManager  →  BrowserPool  (Playwright lifecycle)
                                    →  DoubaoAdapter, ChatGLMAdapter, ...  (one per platform)
```

- **`adapters/base_adapter.py`**: Abstract base with `AdapterResult` dataclass. Defines 6 abstract methods: `navigate_to_chat`, `check_login_status`, `send_question`, `wait_for_answer`, `capture_screenshot`, `new_chat`. The `ask()` method runs the full lifecycle.
- **`core/browser_pool.py`**: Uses `launch_persistent_context` per platform with isolated user data dirs (`./data/user_data/{platform_id}`) for login persistence. Each platform gets exactly one context/page, reused across calls.
- **`core/platform_manager.py`**: Hardcoded registry of 5 adapters. Uses `asyncio.gather` for parallel execution. `min_success` gates overall success.
- **`mcp_server.py`**: Each `@mcp.tool()` function gets a `.fn` attribute (e.g. `ask_ai.fn = ask_ai`) so E2E tests can call them directly without MCP transport.

## Key conventions

- **Login check**: URL + textarea DOM (2 checks, both must pass).
- **Answer wait**: Poll every 1s — check textarea disabled attribute (doubao/chatglm/qianwen) or stop-button presence (deepseek). Extra 2s cooldown after completion detected.
- **Answer extraction**: Try 5–6 CSS selectors, fall back to JS `querySelectorAll('[class*="message"]')`.
- **New chat**: Try clicking "新对话" button first, fall back to page reload.
- **Adapters** accept `page: Page` in constructor (from BrowserPool) and store it as `self.page`.
- **Agent output** follows `{"success": bool, "total_count": ..., "success_count": ..., "question": ..., "results": [...]}`.
- **Comments and strings** are in Chinese.

## Limitations / Gotchas

- No `ruff`, `mypy`, or `bandit` in project config (the `.trae/rules/` files are aspirational Trae IDE rules, not actual project tooling).
- No `pyproject.toml` — only `requirements.txt`.
- `.trae/` directory is Trae IDE-specific config, not relevant to OpenCode.
- Adapters may break when target web platforms change their DOM.
