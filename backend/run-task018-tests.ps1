# TASK-018构建、组件、接口及前置回归、独立HTTP与Windows Chrome；不运行019～024。
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Push-Location (Join-Path $taskRoot 'frontend')
try {
 foreach ($taskCommand in @('build','typecheck','test')) {
  & npm run $taskCommand *> (Join-Path $taskRoot ".codex/task018-$taskCommand.log")
  $taskExit=$LASTEXITCODE
  Get-Content (Join-Path $taskRoot ".codex/task018-$taskCommand.log")
  if ($taskExit -ne 0) {exit $taskExit}
 }
 & npx prettier --check src vite.config.ts tsconfig.json package.json index.html *> (Join-Path $taskRoot '.codex/task018-format-check.log')
 if ($LASTEXITCODE -ne 0) {exit $LASTEXITCODE}
} finally {Pop-Location}
Push-Location $taskRoot
try {
 $env:PYTHONPATH=(Join-Path $taskRoot 'backend')+[IO.Path]::PathSeparator+(Join-Path $taskRoot 'backend/tests')
 $taskTests=Get-ChildItem backend/tests/test_*.py | Where-Object {$_.BaseName -notmatch '_process$|^test_http_smoke$|^test_model_http_smoke$'} | ForEach-Object {$_.FullName}
 & $taskPython -m pytest @taskTests -q --tb=short --junitxml=.codex/task018-regression.xml *> .codex/task018-regression.log
 if ($LASTEXITCODE -ne 0) {exit $LASTEXITCODE}
 # 必须新pytest进程；保持008已披露的Windows隔离方式。
 & $taskPython -m pytest backend/tests/test_http_smoke.py -q --tb=short --junitxml=.codex/task018-smoke.xml *> .codex/task018-smoke.log
 if ($LASTEXITCODE -ne 0) {exit $LASTEXITCODE}
 & $taskPython .codex/task018-browser.py *> .codex/task018-browser.log
 if ($LASTEXITCODE -ne 0) {exit $LASTEXITCODE}
 & $taskPython .codex/task018-read-recovery.py *> .codex/task018-read-recovery.log
 if ($LASTEXITCODE -ne 0) {exit $LASTEXITCODE}
 Get-Content .codex/task018-browser.log
} finally {Pop-Location}
