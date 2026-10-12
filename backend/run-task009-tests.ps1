# TASK-009本地验证；保留008原证据，进程冒烟与TestClient隔离。
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location $PSScriptRoot
try {
    & $taskPython -m pytest tests/test_task_process.py tests/test_http_smoke.py -q --tb=short --basetemp=../.codex/task009-process-evidence --junitxml=../.codex/task009-smoke.xml *> (Join-Path $taskRoot '.codex/task009-smoke.log')
    $smokeExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task009-smoke.log')
    & $taskPython -m pytest tests/test_task_execution.py tests/test_task_faults.py tests/test_csv_import.py tests/test_import_api.py tests/test_failures_and_history.py -q --tb=short --junitxml=../.codex/task009-tests.xml --cov=app --cov-branch --cov-report=term-missing --cov-report=json:../.codex/task009-coverage.json *> (Join-Path $taskRoot '.codex/task009-tests.log')
    $rulesExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task009-tests.log')
    @{date='2026-10-07';executor='Codex';smoke_exit=$smokeExit;rules_exit=$rulesExit;user_acceptance='pending';scope='TASK-009 + necessary TASK-008 regression'} | ConvertTo-Json | Set-Content (Join-Path $taskRoot '.codex/task009-test-results.json') -Encoding utf8
    if ($smokeExit -ne 0 -or $rulesExit -ne 0) { exit 1 }
} finally { Pop-Location }
