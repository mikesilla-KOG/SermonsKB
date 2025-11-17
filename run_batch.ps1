#!/usr/bin/env pwsh
# Batch runner with automatic venv activation
param(
    [int]$StartIndex = 0,
    [int]$MaxVideos = 100
)

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. "$PSScriptRoot\.venv\Scripts\Activate.ps1"
python "$PSScriptRoot\scripts\fetch_batch.py" --start-index $StartIndex --max-videos $MaxVideos
