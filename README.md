# AI 评测自迭代工作台

2026-10-12｜Codex｜本仓库展示单人本机使用的模拟客服评测与知识补充验证工作台。业务对象为会员、额度积分、API 与 Skill/Agent 交易。输入为模拟 CSV，不连接真实客户系统。

## 功能链路

三类 CSV（对话、业务规则、知识库）导入并保留版本 → DeepSeek 三维评测与缺失证据 → 批次指标和预警 → 每个合格缺失点生成标准问 → 人工补答审核 → 选择导出并保存不可变快照 → 本人在外部补充模拟知识库并确认关联 → 旧新分别生成回答和评测 → 随机抽检及人工效果结论。

评测、标准问与新回答分别使用已保存的 Prompt 版本和模型配置。自动任务共用一个运行窗口；单任务最多三个同时请求，每个请求单元最多三次尝试。取消、失败和重启恢复有持久状态。页面从后端读取结果，不在浏览器中重算分数或效果。

## 技术与目录

- `backend/`：Python 3.13、FastAPI、SQLAlchemy、Alembic、SQLite、DeepSeek 官方 API。`backend/app/` 为运行代码，`backend/tests/` 为本地自动化测试。
- `frontend/`：React、TypeScript、Vite。构建后由 FastAPI 同源提供。
- `RDD/`：需求地图、业务决定、验收清单与未知项。
- `docs/02_prd/`、`docs/02_design/`、`docs/03_tasks/`：范围、设计及任务记录。
- `docs/04_validation/`：正式验收、版本选择和适用限制。原始运行数据与临时日志留在本机。

## 在 Windows 本机运行

准备 Python 3.13、Node.js 与 `uv`。在仓库根目录的 PowerShell 中执行：

```powershell
uv venv --python 3.13 backend/.venv
uv pip sync --python backend/.venv/Scripts/python.exe backend/requirements.lock
Set-Location frontend
npm ci
npm run build
Set-Location ..
$env:DEEPSEEK_API_KEY = '自己的密钥'
& backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

用 Chrome 打开 `http://127.0.0.1:8000/#/batches`。密钥只通过服务进程环境变量提供。未配置密钥时，仍可导入和查看历史、编辑及审核已有 QA；不能启动新的模型任务。一个数据库目录只运行一个服务实例。默认数据库位于 `backend/data/`，该目录不会提交到仓库。

可使用 `docs/04_validation/use50-20261012-v2/` 中的模拟 CSV 理解输入格式。首次使用时，按页面顺序导入规则、知识库及对话，再选择两份资料版本启动批次。自动任务会调用真实模型并产生费用。QA 答案、资料有效性和效果结论由使用者本人判断。

## 本地验证与演示

```powershell
& backend/.venv/Scripts/python.exe -m pytest backend/tests -q
Set-Location frontend
npm run test
npm run build
```

浏览器验证采用 Playwright 与独立测试数据库，入口及覆盖范围见 `frontend/README.md` 和 `backend/run-task018-tests.ps1`。[工作台验证视频](docs/demo/workbench-verification.webm) 展示已保存的真实本地评测结果、QA、导出、补充和效果页面；[录制核对记录](docs/demo/verification.json)列出八段页面及对应数据量。录制本身没有发送模型请求。录屏不能代替重新运行正式语义验收。

最终交付选择为 E-v2、Q-v2、G-v4。见 [TASK-024 交付记录](docs/04_validation/task024-e2-delivery-confirmation.md)。正式 50 条按用户确认的新规则通过；038 误冲突、漏缺失点、漏 QA 和同区间分差仍为已接受的实际限制，不能称作原缺陷已修复。E-v3 资产保留，但未作为本次交付版本验证。性能记录仅适用原机器、短对话、小资料及约 20 个 QA 的三批实验，见 [性能报告](docs/04_validation/performance-report.md)。
