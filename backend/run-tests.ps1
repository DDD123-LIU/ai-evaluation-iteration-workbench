# TASK-008：两组均运行，任一失败返回非零；不用CI或正式验收数据。
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location $PSScriptRoot
try {
    # 真实服务进程与TestClient使用独立的验证进程，避免本机Windows混跑影响。
    & $taskPython -m pytest tests/test_http_smoke.py -q --tb=short *> (Join-Path $taskRoot '.codex/task008-smoke.log')
    $smokeExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task008-smoke.log')
    & $taskPython -m pytest tests/test_csv_import.py tests/test_import_api.py tests/test_failures_and_history.py -q --tb=short --cov=app --cov-branch --cov-report=term-missing --cov-report=json:../.codex/task008-coverage.json *> (Join-Path $taskRoot '.codex/task008-tests.log')
    $rulesExit = $LASTEXITCODE
    Get-Content (Join-Path $taskRoot '.codex/task008-tests.log')
    @{date='2026-10-07';executor='Codex';smoke_exit=$smokeExit;rules_exit=$rulesExit;isolation='separate pytest processes';user_acceptance='pending'} | ConvertTo-Json | Set-Content (Join-Path $taskRoot '.codex/task008-test-results.json') -Encoding utf8
    if ($smokeExit -ne 0 -or $rulesExit -ne 0) { exit 1 }
} finally {
    Pop-Location
}
