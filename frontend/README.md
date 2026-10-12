# 完整工作台页面（TASK-018）

2026-10-07｜Codex｜S2｜已完成，实际产物已获用户认可（原运行证据保持不变）。

这是React、TypeScript、Vite页面。页面只读写008～017实际接口。没有模拟模型结果入口，没有第二套评分、预警或调度算法。正式启动不导入`backend/tests/ui_test_server.py`。

## 启动与访问

在项目根目录打开PowerShell。已有本项目后端虚拟环境时执行：

```powershell
Set-Location ./frontend
npm ci
npm run build
Set-Location ../backend
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

使用Windows Chrome访问`http://127.0.0.1:8000/#/batches`。FastAPI同源提供`frontend/dist`及`/api/v1`。只运行一个后端进程。停止服务用当前终端Ctrl+C。后端安装和数据目录沿用`backend/README.md`。未配置DeepSeek密钥时可以导入资料、浏览历史、补答审核；自动任务入口显示未配置并禁用。密钥只沿用后端配置，不进入前端。

开发调试可在后端8000已启动时，另一个终端在`frontend`运行`npm run dev`。访问Vite打印的地址，`/api`代理到8000。正式浏览使用前述构建入口。

## 页面、路由与真实接口

| 页面 | 路由 | 既有数据与动作 |
|---|---|---|
| 资料与版本 | `#/materials`、`#/materials/id` | 008 templates/uploads/materials及原文件 |
| 批次入口、列表 | `#/batches` | 008导入及历史选择、009 evaluation-tasks、012 summary |
| 批次详情、预警 | `#/batches/id?filter=all/badcase/errors` | 009 tasks/cancel、012 cases、013 qa失败 |
| 完整case依据 | `#/batches/task/cases/case` | 011原文、评分理由、归因、缺失点及完整追溯 |
| QA草稿、审核 | `#/qa?batch=id`、`#/qa/id` | 013草稿，014 PATCH/approve，明确本人确认 |
| 导出历史 | `#/exports`、`#/exports/id` | 014 exports/file、不可变四字段快照 |
| 实际补充 | `#/supplements`、`#/supplements/id` | 008新版本、015快照选择确认、完整来源及去重case |
| 效果及抽检 | `#/effects`、`#/effects/id` | 016旧新G/E和指标、017 sampling及本人三维PATCH |

新增必要只读适配：`GET /api/v1/workbench`提供真实任务窗口、模型就绪、来源、分阶段进度及预警展示说明；`GET /api/v1/workbench/qa/id/capabilities`复用014四字段校验和审核状态，提供审核/导出资格及来源案例编号。最终写入仍由原接口重新校验版本和当前状态。没有数据库迁移或新的业务状态。

## 状态与事务分界

普通E、Q及效果旧新G/E分别显示真实数量。效果E未产生时明示等待G或上游失败，分母不缩小。前端不以重试次数扩大case数量。预警读取后台有效快照，并显示指标实值、已确认阈值和同批集合入口。显示舍入值不参与判定。

轮询间隔2秒；请求未完成时不重叠轮询。离开页面不停止后台任务。刷新从持久状态还原。QA输入与人工标记不因轮询被覆盖。QA未保存编辑不能审核，取消编辑保持原状态，离开未保存编辑有提示。

写入包含一个operation_id及原请求，后端事务仍由008～017负责。提交响应未知时保留请求，先查`operations/id`；200跳到原结果，数据库可读的404后允许同编号原请求重发，503继续待核查。正常发送中不开放未知操作恢复按钮。上传文件正文不存会话存储；保留原类型、文件名和SHA256，健康404后需重选相同内容，仍用原编号。浏览器关闭会清理本标签页会话信息；服务端持久结果和历史记录不因此丢失。模型单元重试只归009/010，页面没有手动模型重试。

## 本地验证

前端依赖由`package-lock.json`固定。Node实测24.19.0。组件及提交契约使用Vitest/Testing Library。Python Chrome测试依赖独立放在`requirements-ui-test.txt`，不修改原后端依赖锁：

```powershell
./.codex/runtime-tools/bin/uv.exe pip install --python backend/.venv/Scripts/python.exe -r frontend/requirements-ui-test.txt
./backend/run-task018-tests.ps1
```

测试运行真实本地HTTP服务和SQLite。Chrome通过`channel='chrome'`使用本机安装版本。测试替身仅在后端测试入口，并使用独立数据目录、空真实密钥及MockTransport；从不发外网。测试中的人工标签是模拟输入，不表示本人已完成真实审核或效果判断。完整证据见`.codex/task018-verification.md`。

## 限制与后续边界

未调用真实DeepSeek API，未证明模型评分、标准问质量或补库改善。019语义调试、020独立复核、021正式样本、022正式验收、023性能及024交付均未执行。U10/U12开放。本模块没有新增产品报告导出、访客、多租户、自动补库、录屏或外部通知。

008已接受的规则/知识文件条数与字节上限缺口继续保留，大文件受内存影响。既有TestClient弃用提示仍存在；Windows同pytest进程先TestClient再创建子进程会出现WinError5，独立进程验证通过，未把混跑失败记为通过。真实数据请沿用项目已确认的模拟输入范围。

架构依据：已认可007第12/14/17章、005第13章；组件用法核对[React版本文档](https://react.dev/versions)、[Vite官方指南](https://vite.dev/guide/)、[Vitest官方指南](https://vitest.dev/guide/)、[Playwright Chrome通道](https://playwright.dev/python/docs/browsers)。本地测试负责证明本模块行为，官方资料不替代测试。


### 2026-10-07 TASK-018产物认可（最新状态，Codex）

用户针对TASK-018页面开发和本地验证交付明确回复“确认”。TASK-018已完成，实际产物已获用户认可。认可范围为完整React/TypeScript/Vite工作台页面、必要只读接口接入、九场景及13输出入口、人工审核/导出/历史快照/补充来源/效果抽检操作与状态展示，以及已交付的561项去重后端验证、15项前端测试、Windows Chrome154.0.8037.98共35项交互检查和构建/类型/格式/diff/文档证据。

页面代码和接口已在上一轮实际开发完成。本次仅同步认可状态；不修改产品代码、Prompt、已认可需求/设计或原运行证据，不重跑测试。模拟模型及人工标签不代表真实模型语义、答案正确性或本人真实效果判断通过。真实API/语义及产品最终验收未执行；U10性能留023、U12实际正式样本留021开放；020独立复核未执行。既有Windows混跑限制、TestClient弃用提示及008已接受的容量限制继续保留。

TASK-019～024未启动，未获本次执行授权，不自动推进。此前“待用户确认”为交付时历史记录，本条为当前认可状态。
