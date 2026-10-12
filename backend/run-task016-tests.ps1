# 016常规及008～013回归；各真实进程测试独立执行，无CI或真实API。
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force -Path (Join-Path $taskRoot '.codex/task016-process-evidence') | Out-Null
 $smokeExit=0
 foreach ($group in @('effects_process','supplements_process','qa_review_process','qa_generation_process','batch_metrics_process','evaluation_process','model_http_smoke','task_process','http_smoke')) {
  & $taskPython -m pytest "tests/test_$group.py" -q --tb=short "--basetemp=../.codex/task016-process-evidence/$group" "--junitxml=../.codex/task016-smoke-$group.xml" *> (Join-Path $taskRoot ".codex/task016-smoke-$group.log")
  if ($LASTEXITCODE -ne 0) {$smokeExit=1}
  Get-Content (Join-Path $taskRoot ".codex/task016-smoke-$group.log")
 }
 & $taskPython -m pytest tests/test_effects.py tests/test_effects_integration.py tests/test_effects_api.py tests/test_supplements.py tests/test_supplements_api.py tests/test_qa_review.py tests/test_qa_review_integration.py tests/test_qa_review_api.py tests/test_qa_generation.py tests/test_qa_generation_integration.py tests/test_batch_metrics.py tests/test_batch_metrics_integration.py tests/test_evaluation.py tests/test_evaluation_integration.py tests/test_model_contract.py tests/test_model_client.py tests/test_model_execution.py tests/test_task_execution.py tests/test_task_faults.py tests/test_csv_import.py tests/test_import_api.py tests/test_failures_and_history.py -q --tb=short --junitxml=../.codex/task016-tests.xml --cov=app --cov-branch --cov-report=term-missing --cov-report=json:../.codex/task016-coverage.json *> (Join-Path $taskRoot '.codex/task016-tests.log')
 $testsExit=$LASTEXITCODE
 Get-Content (Join-Path $taskRoot '.codex/task016-tests.log')
 @{date='2026-10-07';executor='Codex';smoke_exit=$smokeExit;tests_exit=$testsExit;real_model_api='not_called_task016';semantic_acceptance='not_performed';user_acceptance='pending'} | ConvertTo-Json | Set-Content (Join-Path $taskRoot '.codex/task016-test-results.json') -Encoding utf8
 if ($smokeExit -ne 0 -or $testsExit -ne 0) {exit 1}
} finally {Pop-Location}




