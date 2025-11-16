Param(
    [string]$RepoRoot = "C:\software\video\mcp-seuqnetial-thinking"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    $RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$slug = Split-Path -Leaf $RepoRoot
$hashInput = [System.Text.Encoding]::UTF8.GetBytes($RepoRoot)
$digest = (Get-FileHash -InputStream ([System.IO.MemoryStream]::new($hashInput)) -Algorithm SHA1).Hash.Substring(0,8).ToLower()
$sessionId = (New-Guid).Guid.Substring(0,6)
$projectId = "$slug-$digest-$sessionId"
$storageDir = Join-Path $env:USERPROFILE ".mcp_sequential_thinking"

$env:MCP_PROJECT_ID = $projectId
$env:MCP_STORAGE_DIR = $storageDir

Write-Host "Starting Sequential Thinking MCP server for project $projectId using $RepoRoot"

& uv --directory $RepoRoot run -m mcp_sequential_thinking.server
