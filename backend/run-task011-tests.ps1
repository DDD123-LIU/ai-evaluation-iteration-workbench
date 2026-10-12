# 011本地验证。各进程冒烟在独立pytest进程运行，保留Windows隔离证据。
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location $PSScriptRoot
try {
    $smokeExit = 0
    $groups = @('evaluation_process','model_http_smoke','task_process','http_smoke')
    foreach ($group in $groups) {
        & $taskPython -m pytest "tests/test_$group.py" -q --tb=short "--basetemp=../.codex/task011-process-evidence/$group" "--junitxml=../.codex/task011-smoke-$group.xml" *> (Join-Path $taskRoot ".codex/task011-smoke-$group.log")
        if ($LASTEXITCODE -ne 0) { $smokeExit = 1 }
        Get-Content (Join-Path $taskRoot ".codex/task011-smoke-$group.log")
    }
    & $taskPython -m pytest tests/test_evaluation.py tests/test_evaluation_integration.py tests/test_model_contract.py tests/test_model_client.py tests/test_model_execution.py tests/test_task_execution.py tests/test_task_faults.py tests/test_csv_import.py tests/test_import_api.py tests/test_failures_and_history.py -q --tb=short --junitxml=../.codex/task011-tests.xml --cov=app --cov-branch --cov-report=term-missing --cov-report=json:../.codex/task011-coverage.json *> (Join-Path $taskRoot '.codex/task011-tests.log')
    $testsExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task011-tests.log')
    @{date='2026-10-07';executor='Codex';smoke_exit=$smokeExit;tests_exit=$testsExit;real_model_semantics='not_verified_missing_key';F32_real_model='not_verified_missing_key';user_acceptance='pending'} | ConvertTo-Json | Set-Content (Join-Path $taskRoot '.codex/task011-test-results.json') -Encoding utf8
    if ($smokeExit -ne 0 -or $testsExit -ne 0) { exit 1 }
} finally { Pop-Location }
