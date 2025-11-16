#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
slug=$(basename "$repo_root")
digest=$(printf "%s" "$repo_root" | shasum | cut -c1-8)
session_id=$(uuidgen | cut -c1-6)
project_id="${slug}-${digest}-${session_id}"
storage_dir="${HOME}/.mcp_sequential_thinking"

export MCP_PROJECT_ID="$project_id"
uv --directory /Users/tristan/Software/mcp-sequential-thinking run -m mcp_sequential_thinking.server
