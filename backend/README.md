# TASK-008 本地导入与资料版本模块

2026-10-07新增：TASK-009调度模块的接入与运行边界见[TASK009.md](TASK009.md)，本轮产物待用户确认。以下TASK-008认可记录保留，不代表新增模块获认可。启动现在执行0001～0002增量迁移，保留原导入及历史资料。

日期：2026-10-07｜执行者：Codex｜状态：TASK-008产物已获用户认可（用户回复“确认”）；不表示产品最终验收。

本模块只实现三类CSV导入、整份校验、原文保存、不可覆盖的规则/知识版本及历史查询。技术依据为已认可的[TASK-007第12章](../docs/03_tasks/design-gate-review.md)，业务依据为[TASK-008](../docs/03_tasks/task-cards/TASK-008.md)、U01和已认可Spec。

## 本机运行

在项目根目录PowerShell执行。已准备项目局部Python 3.13环境；无需改系统Python。

```powershell
& ./backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

打开 `http://127.0.0.1:8000/docs` 使用接口调试页。它用于本模块核对；业务页面由TASK-018承接。停止服务用Ctrl+C。

默认数据库为`backend/data/workbench.sqlite3`，原CSV字节与记录保存在同一数据库事务内。需要独立目录时，在启动前设置`$env:WORKBENCH_DATA_DIR='本机绝对目录'`。只用本机磁盘。不可同时运行两个实例使用同一目录；不要使用多worker。目录被占用时启动失败，释放后可重启。启动自动执行Alembic初始迁移，未建立后续业务表。

重建依赖环境时，先安装Python 3.13及uv，再执行：

```powershell
uv venv --python 3.13 backend/.venv
uv pip sync --python backend/.venv/Scripts/python.exe backend/requirements.lock
```

`requirements.lock`锁定本模块运行和测试依赖及下载哈希。当前环境和实际版本见[验证记录](../.codex/task008-verification.md)。不需要前端、模型SDK或API密钥。

## 核对流程

1. 在`GET /api/v1/templates/{kind}`下载对应模板。kind为`dialogues`、`rules`、`knowledge`。
2. 填写符合U01的模拟内容。模板只有表头；没有数据的文件不能导入。
3. 在`POST /api/v1/uploads`点击Try it out，选kind及文件。operation_id填写新的UUID，例如在PowerShell执行`[guid]::NewGuid().ToString()`。
4. 成功返回201和资源`id`、文件名、UTC时间、行数。资料响应另含`kind=rule/kb`。对话id对应upload_id，资料id对应material_version_id。
5. 在uploads或materials列表/详情读取保存结果。资料详情包含所有行及原顺序；对话详情含四字段、内部case身份及解析后的有序history。`/{id}/file`返回原始上传字节，可逐字节对照。
6. 新的明确上传动作使用新operation_id，即使内容相同也产生独立上传/版本。网络重传使用原operation_id，返回200及原结果，不重复保存。同ID不同kind或内容返回409；原文件名作为首次操作元数据保留。

规则、知识标题和内容原样保存。系统不判断知识语义是否正确，不关联实际补库或发起效果任务。列表按uploaded_at和id倒序稳定分页；默认limit=20，范围1～100，offset≥0。materials可按`kind=rules/knowledge`筛选。历史没有更新/删除接口，不自动选最新资料。

## 失败与恢复

CSV错误返回422。错误格式固定为`code,message,resource_id,field_errors,commit_state`。字段错误含物理CSV起始行、字段、案例编号（适用时）及原因；错误文件整份拒绝。任一保存前错误或数据库写入失败不留下部分记录、不生成新版本；已有版本继续可读。

保存失败返回503。`not_committed`表示未提交，修复后可用原operation_id重传。`unknown`表示提交确认有异常，不能直接断言没有保存。先通过`GET /api/v1/operations/{operation_id}`核对：200返回已保存资源；数据库可读时404表示无提交索引，可同ID重传；503表示仍不可核实，先修复再查。成功内容、原字节及提交索引同时保存，避免重复版本。CSV与请求校验失败也必须修正文件/字段后重传；本模块不自动重试。

## 本地测试

在项目根目录执行：

```powershell
& ./backend/run-tests.ps1
```

脚本分别运行真实HTTP进程冒烟，以及解析/接口/SQLite事务测试。两组都执行；任一失败返回非零。输入在测试中临时构造，数据库位于临时目录，不是TASK-019调试集或正式验收集。HTTP测试启动、拒绝第二实例、强制中断、重启读回后停止所有测试进程。

本机发现TestClient验证后同一pytest进程启动子进程出现WinError 5；独立进程运行正常。隔离运行保留所有测试，不将该混跑失败记为通过。系统原因尚未核实。当前TestClient还发出httpx弃用提示；已锁定依赖，实际测试可运行，未来升级需复核该适配器。

D01本模块验证原四字段与H；模型请求只追加目标回复的真实组装留TASK-011。D02本模块验证不可覆盖版本和按固定id读历史；原任务版本绑定留TASK-009/011集成。不宣称整产品、真实模型、UI或性能已验收。

## 代码与官方依据

- `app/domain/csv_import.py`：标准CSV解析与U01校验。
- `app/models/imports.py`、`app/db/database.py`、`migrations/`：本模块结构、外键、WAL/FULL、目录锁及迁移。
- `app/services/imports.py`：TX01事务、重传提交索引、固定版本查询。
- `app/api/imports.py`、`app/main.py`：本模块接口与生命周期。
- `tests/`：单元、功能、实错故障和真实HTTP冒烟。

实现核对资料：[Python 3.13 CSV](https://docs.python.org/3.13/library/csv.html)、[SQLAlchemy SQLite事务及外键](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)、[FastAPI文件上传](https://fastapi.tiangolo.com/tutorial/request-files/)、[Alembic迁移](https://alembic.sqlalchemy.org/en/latest/tutorial.html)、[uv Python环境](https://docs.astral.sh/uv/concepts/python-versions/)。官方资料支持组件用法；具体模块正确性以本地测试证据为准。


### 2026-10-07 TASK-008产物认可（最新状态，Codex）

用户针对TASK-008交付明确回复“确认”。本模块实际产物已获用户认可，TASK-008已完成。认可范围为已展示的三类CSV导入、整份校验、原文保存、资料版本及本地证据；不是整产品最终验收或后续开发授权。既有Windows混跑限制、依赖弃用提示及D01/D02后续集成边界继续保留。U10阈值与U12正式样本事项仍开放。TASK-009～024未执行，未获本次授权。此前“待确认”为交付当时历史状态，不覆盖本条。


### 2026-10-07 TASK-008已披露影响接受记录（Codex）

用户明确表示：“继续认可目前的task-008。所列举的‘对task-008’的影响可以接受。”TASK-008继续保持已完成、实际产物获用户认可。

本次接受的现状：产品不持久保存可查询的失败导入错误详情历史；当次接口返回错误，关闭提示后无法通过产品重新查询详细错误。规则/知识库未设产品级条数上限，三类CSV未设产品级文件字节上限；完整读取文件可能占用较多内存。对话每批最多100条的已确认限制保持。

这是接受当前模块及上述影响，本次不要求补做失败历史或容量限制。没有确认无限处理能力、具体容量阈值、永久保留期限或未来永不调整；如需改变现状，另行明确要求和授权。原有整份拒绝、零部分数据、旧版本保留及成功历史追溯规则不变。测试证据日志不等于产品失败导入历史。

本次只补认可记录，不改产品代码、需求/设计基线，不启动TASK-009～024。既有Windows混跑限制、依赖弃用提示、D01/D02后续集成及U10/U12实际事项继续保留；不表示全产品最终验收。
