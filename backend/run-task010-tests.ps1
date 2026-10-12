# 本地两组验证，不接CI，不覆盖008/009历史证据。
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location $PSScriptRoot
try {
    & $taskPython -m pytest tests/test_model_http_smoke.py tests/test_task_process.py tests/test_http_smoke.py -q --tb=short --basetemp=../.codex/task010-process-evidence --junitxml=../.codex/task010-smoke.xml *> (Join-Path $taskRoot '.codex/task010-smoke.log')
    $smokeExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task010-smoke.log')
    & $taskPython -m pytest tests/test_model_contract.py tests/test_model_client.py tests/test_model_execution.py tests/test_task_execution.py tests/test_task_faults.py tests/test_csv_import.py tests/test_import_api.py tests/test_failures_and_history.py -q --tb=short --junitxml=../.codex/task010-tests.xml --cov=app --cov-branch --cov-report=term-missing --cov-report=json:../.codex/task010-coverage.json *> (Join-Path $taskRoot '.codex/task010-tests.log')
    $testsExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task010-tests.log')
    @{date='2026-10-07';executor='Codex';smoke_exit=$smokeExit;tests_exit=$testsExit;real_deepseek_api='not_verified_missing_key';user_acceptance='pending'} | ConvertTo-Json | Set-Content (Join-Path $taskRoot '.codex/task010-test-results.json') -Encoding utf8
    if ($smokeExit -ne 0 -or $testsExit -ne 0) { exit 1 }
} finally { Pop-Location }
