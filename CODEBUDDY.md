# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

ConsensusWeaverAgent is an intelligent Q&A coordination terminal application that coordinates multiple AI tools and generates comprehensive reports. The system features:

- **Local-first architecture**: Core processing (LLM, analysis, orchestration) runs locally; only external tools require network access
- **Four-layer architecture**: UI → Service → Core → Infrastructure
- **Privacy-focused**: User questions and clarifications stay local; only refined questions are sent to external tools
- **Async concurrent execution**: Multiple external tools run concurrently via asyncio

## Common Commands

### Environment Setup
```powershell
# Install uv package manager
pip install uv

# Create virtual environment and install dependencies
uv venv && uv sync --all-extras

# Activate virtual environment
.venv\Scripts\activate

# Download NLTK resources (required for text analysis)
python -c "import nltk; nltk.data.path.append('https://gitee.com/gislite/nltk_data/raw/'); nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Download GGUF model file
python scripts/download_qwen3-8b-gguf.py
# Or manually download Qwen3-8B-Q5_K_M.gguf to .models/qwen/
```

### Development Workflow
```powershell
# Code formatting and linting
uv run ruff check .
uv run ruff format .

# Type checking (strict mode)
uv run mypy --strict .

# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests only
uv run pytest tests/integration/

# Run a specific test
uv run pytest tests/unit/test_config_manager.py::test_config_load

# Run application
python -m src.main

# Run with custom config
python -m src.main --config my_config.yaml

# Run with verbose logging
python -m src.main --verbose
```

### Dependency Management
```powershell
# Add a dependency
uv add <package>

# Add dev dependency
uv add --group dev <package>

# Update all dependencies
uv update

# Sync environment after changes
uv sync
```

## Architecture Overview

### Layer Structure

```
src/
├── main.py                   # Application entry point with Click CLI
├── core/                     # Core business logic layer
│   ├── analyzer/             # Consensus analysis engine (TF-IDF, cosine similarity)
│   ├── executor/             # Concurrent query executor (asyncio)
│   └── reporter/             # Report generator
├── infrastructure/           # Infrastructure services layer
│   ├── config/               # YAML configuration management
│   ├── data/                 # SQLite database persistence
│   ├── llm/                  # Local LLM integration (LangChain + llama-cpp-python)
│   ├── logging/              # Centralized logging with rotation
│   └── tools/                # External tool management (async subprocess)
├── service/                  # Application service layer
│   ├── interaction/          # User interaction workflow (clarification loop)
│   └── strategy/             # Execution strategy (simple vs complex)
├── models/                   # Data models (inline dataclasses)
├── utils/                    # Utility functions (currently empty)
└── ui/                       # User interface layer (currently empty, CLI in main.py)
```

### Component Initialization Order

Components are initialized in `src/main.py` in this order:

```
ConfigManager → DataManager → LLMService → ToolManager
→ InteractionEngine → ExecutionStrategyManager
→ QueryExecutor → ConsensusAnalyzer → ReportGenerator
```

All components use dependency injection pattern.

### Application Flow

1. **User input** → `InteractionEngine.start_interaction()` creates session
2. **Question analysis** → LLM analyzes completeness, clarity, ambiguities, complexity
3. **Clarification loop** → Max 3 rounds, user can skip
4. **Question refinement** → LLM rewrites question based on clarifications
5. **Strategy selection** → `ExecutionStrategyManager` classifies as simple/complex
6. **Execution**:
   - Simple: LLM answers directly (no network)
   - Complex: `QueryExecutor` runs tools concurrently via `asyncio`
7. **Consensus analysis** → `ConsensusAnalyzer` computes similarity matrix, consensus scores
8. **Report generation** → `ReportGenerator` outputs structured report

## Key Architectural Patterns

1. **Four-Layer Architecture**: UI → Service → Core → Infrastructure (low coupling, high cohesion)
2. **Dependency Injection**: All components receive dependencies via constructors
3. **Async/Await Pattern**: asyncio for concurrent tool execution
4. **Repository Pattern**: DataManager abstracts data access
5. **Dataclass Pattern**: All data structures use `@dataclass`
6. **Strategy Pattern**: ExecutionStrategyManager selects execution path
7. **Fallback Pattern**: Multiple fallbacks (NLTK resources, LLM JSON parsing)
8. **Singleton Pattern**: Global logger instance
9. **Context Manager Pattern**: DataManager supports `with` statement

## Data Models

All data models are defined inline as `@dataclass`:

- `InteractionState`: Tracks user interaction session
- `ExecutionPlan`: Contains strategy ("direct_answer" or "parallel_query") and tools
- `QueryExecutionResult`: Contains success/failure counts, timing, and results
- Config models: `Config`, `LocalLLMConfig`, `ExternalToolConfig`, `NetworkConfig`, `AppConfig`

## Database Schema (SQLite)

Three tables managed by `DataManager`:

1. **sessions**: Stores question sessions (id, original_question, refined_question, timestamp)
2. **tool_results**: Stores tool execution results (session_id, tool_name, answer, error_message, execution_time, timestamp)
3. **analysis_results**: Stores consensus analysis results (session_id, similarity_matrix, consensus_scores, key_points, differences, summary, conclusion)

## Configuration

Configuration is YAML-based (`config.yaml`). Auto-created on first run with defaults. Key sections:

- **local_llm**: Model path, context size, threads, temperature
- **external_tools**: Tool definitions (name, command, args, needs_internet, priority, enabled)
- **network**: check_before_run, timeout
- **app**: max_clarification_rounds, max_parallel_tools, log_level, log_file, history_enabled, history_limit

External tools can be added/modified in config without code changes.

## External Tool Integration

Tools are configured in `config.yaml` and executed via `ToolManager`:

- Uses `asyncio.subprocess` for concurrent execution
- Supports PowerShell scripts on Windows
- Network connection checking before execution
- Timeout handling (default 60s)
- **Security**: Never use `shell=True` in subprocess

Example tool configuration:
```yaml
- name: "iflow"
  command: "iflow"
  args: "ask --streaming=false"
  needs_internet: true
  priority: 1
  enabled: true
```

## LLM Integration

Local LLM integration via `LLMService`:

- Uses LangChain with `llama-cpp-python`
- Loads GGUF format models (default: Qwen3-8B-Q5_K_M.gguf)
- Methods: `generate_response()`, `chat()`, `analyze_question()`, `refine_question()`, `classify_question_complexity()`, `answer_simple_question()`
- Robust JSON parsing with fallbacks for LLM responses
- Models can be swapped by changing config without code modification

## Consensus Analysis

`ConsensusAnalyzer` implements multi-source answer analysis:

- **Similarity calculation**: TF-IDF vectorization + cosine similarity (scikit-learn)
- **Consensus scoring**: Per-tool scores (0-100 scale)
- **Key points extraction**: LLM-based with fallback to simple extraction
- **Differences identification**: LLM-based
- **Summary and conclusion**: LLM-generated
- **Fallback mechanisms**: Graceful degradation when NLTK resources fail

## Testing

- **Framework**: pytest with pytest-asyncio
- **Structure**: `tests/unit/` for unit tests, `tests/integration/` for integration tests
- **Mocking**: pytest-mock for external dependency isolation
- **Coverage**: Tests should cover normal paths, error paths, and edge cases
- **Test naming**: `test_*.py` files, `Test*` classes, `test_*` functions

## Coding Standards

- **Formatting**: ruff (line length 88)
- **Type checking**: mypy strict mode (all functions must have type annotations)
- **Docstrings**: Google style for public modules/classes/functions
- **Imports**: Explicit relative imports within project
- **Language**: Documentation and comments in Chinese (user-facing), code comments explain "why" not "what"

## Security Requirements

- **SQL**: Always use parameterized queries (never string concatenation)
- **Subprocess**: Never use `shell=True`
- **Deserialization**: Avoid unsafe deserialization
- **Privacy**: User data stays local; only refined questions sent to external tools

## File Locations

- **Entry point**: `src/main.py`
- **Configuration**: `config.yaml` (auto-generated)
- **Database**: `consensusweaver.db` (auto-generated)
- **Logs**: `consensusweaver.log` (auto-generated)
- **Models**: `.models/qwen/` directory
- **Rules/standards**: `.trae/rules/project_rules.md`
- **Architecture docs**: `docs/design/架构设计.md`
- **Requirements**: `docs/requirements/requirements.md`

## NLTK Resources

Required NLTK data (punkt, stopwords, wordnet). Download via:

```python
python -c "import nltk; nltk.data.path.append('https://gitee.com/gislite/nltk_data/raw/'); nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

The application includes fallback mechanisms when NLTK resources are unavailable.

## Extension Points

1. **New external tools**: Add to `config.yaml` under `external_tools`
2. **Different LLM models**: Update `config.yaml` `local_llm.model` and `local_llm.model_path`
3. **GUI implementation**: Create in `src/ui/`, reuse Service/Core layers
4. **New analysis algorithms**: Extend `ConsensusAnalyzer` in `src/core/analyzer/`

## Important Implementation Details

- **Async main loop**: Application uses `asyncio.run()` in `src/main.py:69`
- **Session management**: All operations tied to `session_id` for database tracking
- **Error handling**: Layered error handling with logging; user-friendly error messages
- **Clarification workflow**: Max 3 rounds, user can skip with 'skip' command
- **Complexity classification**: LLM determines if question needs external tools or can be answered locally
- **Network independence**: Core functionality (LLM, analysis, orchestration) works offline; only external tools require internet
