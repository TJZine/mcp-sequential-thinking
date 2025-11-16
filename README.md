[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/arben-adm-mcp-sequential-thinking-badge.png)](https://mseep.ai/app/arben-adm-mcp-sequential-thinking)

# Sequential Thinking MCP Server

A Model Context Protocol (MCP) server that facilitates structured, progressive thinking through defined stages. This tool helps break down complex problems into sequential thoughts, track the progression of your thinking process, and generate summaries.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<a href="https://glama.ai/mcp/servers/m83dfy8feg"><img width="380" height="200" src="https://glama.ai/mcp/servers/m83dfy8feg/badge" alt="Sequential Thinking Server MCP server" /></a>

## Features

- **Structured Thinking Framework**: Organizes thoughts through coding-aware stages (Scoping, Research & Spike, Implementation, Testing, Review)
- **Thought Tracking**: Records and manages sequential thoughts with metadata
- **Related Thought Analysis**: Identifies connections between similar thoughts
- **Progress Monitoring**: Tracks your position in the overall thinking sequence
- **Summary Generation**: Creates concise overviews of the entire thought process
- **Persistent Storage**: Automatically saves your thinking sessions with thread-safety
- **Data Import/Export**: Share and reuse thinking sessions
- **Extensible Architecture**: Easily customize and extend functionality
- **Robust Error Handling**: Graceful handling of edge cases and corrupted data
- **Type Safety**: Comprehensive type annotations and validation
- **Stage-Specific Prompts**: Built-in FastMCP prompts for scoping, research, implementation, testing, and review guardrails
- **Project-Aware Sessions**: Scope histories per repository or initiative using `project_id`

## Prerequisites

- Python 3.10 or higher
- UV package manager ([Install Guide](https://github.com/astral-sh/uv))

## Key Technologies

- **Pydantic**: For data validation and serialization
- **Portalocker**: For thread-safe file access
- **FastMCP**: For Model Context Protocol integration
- **Rich**: For enhanced console output
- **PyYAML**: For configuration management

## Project Structure

```
mcp-sequential-thinking/
├── mcp_sequential_thinking/
│   ├── server.py       # Main server implementation and MCP tools
│   ├── models.py       # Data models with Pydantic validation
│   ├── storage.py      # Thread-safe persistence layer
│   ├── storage_utils.py # Shared utilities for storage operations
│   ├── analysis.py     # Thought analysis and pattern detection
│   ├── testing.py      # Test utilities and helper functions
│   ├── utils.py        # Common utilities and helper functions
│   ├── logging_conf.py # Centralized logging configuration
│   └── __init__.py     # Package initialization
├── tests/              
│   ├── test_analysis.py # Tests for analysis functionality
│   ├── test_models.py   # Tests for data models
│   ├── test_storage.py  # Tests for persistence layer
│   └── __init__.py
├── run_server.py       # Server entry point script
├── debug_mcp_connection.py # Utility for debugging connections
├── README.md           # Main documentation
├── CHANGELOG.md        # Version history and changes
├── example.md          # Customization examples
├── LICENSE             # MIT License
└── pyproject.toml      # Project configuration and dependencies
```

## Quick Start

1. **Set Up Project**
   ```bash
   # Create and activate virtual environment
   uv venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Unix

   # Install package and dependencies
   uv pip install -e .

   # For development with testing tools
   uv pip install -e ".[dev]"

   # For all optional dependencies
   uv pip install -e ".[all]"
   ```

2. **Run the Server**
   ```bash
   # Run directly
   uv run -m mcp_sequential_thinking.server

   # Or use the installed script
   mcp-sequential-thinking
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   pytest

   # Run with coverage report
   pytest --cov=mcp_sequential_thinking
   ```

## Claude Desktop Integration

Add to your Claude Desktop configuration (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\your\\mcp-sequential-thinking\\run_server.py",
        "run",
        "server.py"
        ]
      }
    }
  }
```

Alternatively, if you've installed the package with `pip install -e .`, you can use:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "mcp-sequential-thinking"
    }
  }
}
```

You can also run it directly using uvx and skipping the installation step:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/arben-adm/mcp-sequential-thinking",
        "--with",
        "portalocker",
        "mcp-sequential-thinking"
      ]
    }
  }
}
```

# How It Works

The server maintains a history of thoughts and processes them through a structured workflow. Each thought is validated using Pydantic models, categorized into thinking stages, and stored with relevant metadata in a thread-safe storage system. The server automatically handles data persistence, backup creation, and provides tools for analyzing relationships between thoughts.

## Usage Guide

The Sequential Thinking server exposes three main tools:

### 1. `process_thought`

Records and analyzes a new thought in your sequential thinking process.

**Parameters:**

- `thought` (string): The content of your thought
- `thought_number` (integer): Position in your sequence (e.g., 1 for first thought)
- `total_thoughts` (integer): Expected total thoughts in the sequence
- `next_thought_needed` (boolean): Whether more thoughts are needed after this one
- `stage` (string): The thinking stage - must be one of:
  - "Scoping"
  - "Research & Spike"
  - "Implementation"
  - "Testing"
  - "Review"
- `tags` (list of strings, optional): Keywords or categories for your thought
- `axioms_used` (list of strings, optional): Principles or axioms applied in your thought
- `assumptions_challenged` (list of strings, optional): Assumptions your thought questions or challenges
- `files_touched` (list of strings, optional): Repository paths referenced in this thought
- `tests_to_run` (list of strings, optional): Targeted tests Codex should run after this step
- `dependencies` (list of strings, optional): External systems, teams, or documents this thought relies on
- `risk_level` (string, optional): "low", "medium", or "high"; defaults to "medium"
- `confidence_score` (float, optional): Between 0.0 and 1.0, defaults to 0.5
- `project_id` (string, optional): Session scope identifier (e.g., repo name or ticket)

**Example:**

```python
# First thought in a 5-thought sequence
process_thought(
    thought="The problem of climate change requires analysis of multiple factors including emissions, policy, and technology adoption.",
    thought_number=1,
    total_thoughts=5,
    next_thought_needed=True,
    stage="Scoping",
    tags=["climate", "global policy", "systems thinking"],
    axioms_used=["Complex problems require multifaceted solutions"],
    assumptions_challenged=["Technology alone can solve climate change"],
    files_touched=["docs/climate.md"],
    tests_to_run=["pytest tests/test_climate.py"],
    dependencies=["epa-api"],
    risk_level="high",
    confidence_score=0.7,
    project_id="climate-mission"
)
```

## Serena/Codex Integration Notes

- Stage aliases: the `stage` parameter now accepts common synonyms used by Serena/Codex, e.g. `Planning` maps to `Implementation`; `Scope/Scoping`, `Research/Spike`, `Testing/Test`, and `Review/Code Review` are all supported. If `stage` is omitted, it defaults to `Implementation`.
- Stringified inputs: some tool bridges send everything as strings. The server now coerces types for:
  - `thought_number`, `total_thoughts`: numeric strings are parsed as integers
  - `next_thought_needed`: accepts `true/false/1/0/yes/no`
  - list fields (`tags`, `axioms_used`, `assumptions_challenged`, `files_touched`, `tests_to_run`, `dependencies`): accepts JSON-encoded lists or comma/semicolon-separated strings
  - `confidence_score`: parses numeric strings
- Legacy kwargs: if your bridge requires a `legacy_kwargs` parameter, you can pass a JSON object as a string (e.g., `{"nextThoughtNeeded": true}`) and the server will merge it with other args and camelCase aliases. Unknown extra keyword arguments are also treated as legacy/camelCase payload.
- Recommendation: if Serena “planning mode” is not yet compatible with your Codex context, drive plan updates from sequential-thinking outputs instead. For example, use `generate_summary` as the basis for `update_plan` calls, or map Implementation-stage thoughts to `plan` steps with `status` transitions managed by Codex.

### 2. `generate_summary`

Generates a summary of your entire thinking process.

**Example output:**

```json
{
  "summary": {
    "totalThoughts": 5,
    "stages": {
      "Scoping": 1,
      "Research & Spike": 1,
      "Implementation": 1,
      "Testing": 1,
      "Review": 1
    },
    "timeline": [
      {"number": 1, "stage": "Scoping"},
      {"number": 2, "stage": "Research & Spike"},
      {"number": 3, "stage": "Implementation"},
      {"number": 4, "stage": "Testing"},
      {"number": 5, "stage": "Review"}
    ]
  }
}
```

### 3. `clear_history`

Resets the thinking process by clearing all recorded thoughts.

## Practical Applications

- **Decision Making**: Work through important decisions methodically
- **Problem Solving**: Break complex problems into manageable components
- **Research Planning**: Structure your research approach with clear stages
- **Writing Organization**: Develop ideas progressively before writing
- **Project Analysis**: Evaluate projects through defined analytical stages

## Stage-Aware Prompts

The server now exposes FastMCP prompts for the five default stages:

- `scoping_prompt` – clarifies scope, non-goals, and success metrics.
- `research_prompt` – plans spikes and surfaces references before coding.
- `implementation_prompt` – sequences coding tasks, files touched, and risk mitigations.
- `testing_prompt` – enumerates targeted test suites and regression areas.
- `review_prompt` – gathers reviewer checklists, follow-ups, and release confidence.

Use these prompts directly from your MCP client to keep each stage of the thought flow structured and repeatable.

## Getting Started

With the proper MCP setup, simply use the `process_thought` tool to begin working through your thoughts in sequence. As you progress, you can get an overview with `generate_summary` and reset when needed with `clear_history`.



# Customizing the Sequential Thinking Server

For detailed examples of how to customize and extend the Sequential Thinking server, see [example.md](example.md). It includes code samples for:

- Modifying thinking stages
- Enhancing thought data structures with Pydantic
- Adding persistence with databases
- Implementing enhanced analysis with NLP
- Creating custom prompts
- Setting up advanced configurations
- Building web UI integrations
- Implementing visualization tools
- Connecting to external services
- Creating collaborative environments
- Separating test code
- Building reusable utilities




## License

MIT License
