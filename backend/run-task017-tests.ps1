# 017模块及008～016回归；各HTTP/重启进程独立，无CI或真实模型。
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force -Path (Join-Path $taskRoot '.codex/task017-process-evidence') | Out-Null
 $smokeExit=0
 foreach ($group in @('sampling_process','effects_process','supplements_process','qa_review_process','qa_generation_process','batch_metrics_process','evaluation_process','model_http_smoke','task_process','http_smoke')) {
  & $taskPython -m pytest "tests/test_$group.py" -q --tb=short "--basetemp=../.codex/task017-process-evidence/$group" "--junitxml=../.codex/task017-smoke-$group.xml" *> (Join-Path $taskRoot ".codex/task017-smoke-$group.log")
  if ($LASTEXITCODE -ne 0) {$smokeExit=1}
  Get-Content (Join-Path $taskRoot ".codex/task017-smoke-$group.log")
 }
 $tests=Get-ChildItem tests/test_*.py | Where-Object {$_.BaseName -notmatch '_process$|^test_http_smoke$|^test_model_http_smoke$'} | ForEach-Object {$_.FullName}
 & $taskPython -m pytest @tests -q --tb=short --junitxml=../.codex/task017-tests.xml --cov=app --cov-branch --cov-report=term-missing --cov-report=json:../.codex/task017-coverage.json *> (Join-Path $taskRoot '.codex/task017-tests.log')
 $testsExit=$LASTEXITCODE
 Get-Content (Join-Path $taskRoot '.codex/task017-tests.log')
 @{date='2026-10-07';executor='Codex';smoke_exit=$smokeExit;tests_exit=$testsExit;real_model_api='not_called';semantic_acceptance='not_performed';user_acceptance='pending'} | ConvertTo-Json | Set-Content (Join-Path $taskRoot '.codex/task017-test-results.json') -Encoding utf8
 if ($smokeExit -ne 0 -or $testsExit -ne 0) {exit 1}
} finally {Pop-Location}
