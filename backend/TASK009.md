# TASK-009 持久任务执行与恢复取消

日期：2026-10-07｜执行者：Codex｜状态：已完成，实际产物已获用户认可

沿用TASK-008的Python3.13、FastAPI、SQLAlchemy、Alembic、SQLite WAL/FULL和单进程目录锁。没有新增依赖。正常启动仍为README的单worker Uvicorn命令。页面关闭不会结束lifespan后台扫描；进程关闭或关机期间不执行，重启后读取同一数据目录恢复。

```text
011/013/016固定输入与配置
          ↓ 同一事务创建task、case、配置、窗口
009扫描待执行单元 → 全局3名额 → 取消/发送共用门
                                      ↓
                             先提交次数与attempt
                                      ↓
                          010 start_once（只调用一次）
                                      ↓ 等待响应及清理，门外等待
                          本地原子保存结果与阶段交接
                            ↙                 ↘
                    E→Q，保留窗口       全部终态，释放窗口

取消 → 同一门、检查revision/阶段 → 整批删除工作与结果 → 释放窗口
旧请求尚未结束 → 仍占全局名额 → 回复到达后丢弃
```

## 接入接口与职责

- `TaskService.start(Plan, operation_id)`：固定来源case、版本、全部阶段配置及初始单元；重传相同操作返回原身份，冲突409，忙碌409，无排队。普通任务冻结规则/知识版本在`ordinary_task`。效果的补充记录、旧新库业务绑定由016在其事务中补齐，本轮没有补充业务表。
- `ConfigSpec`保存完整Prompt、协议/Prompt版本、型号、官方发布依据及参数；`ItemSpec`保存完整单次输入。业务模块负责组装和判断，009不生成Prompt正文、评分、QA内容或抽检。
- `BusinessHooks.item_saved(session,task,item,outcome)`和`phase_finished(session,task)`在结果事务内运行。前者保存业务结果，016在G成功后创建同侧E；后者由011/013给应生成Q列表，或由016冻结自动结果并返回done。钩子不得发网络调用或自行提交事务。取消钩子`cancelled(session,task)`须删除后续业务表的本任务数据，保留外部来源；它必须与取消同事务。
- 010实现`Transport.start_once(prepared)`：**同步交给HTTP transport，再返回等待对象**。不要只返回尚未启动的异步函数。每次仅一次发送，SDK `max_retries=0`，010不得再次增加计次或重试；300秒单请求截止与连接清理由010负责，等待对象必须在请求真正结束/清理完成后结束。009此时才归还并发名额。
- 可选`validate(preview)`做010本地能力预检；`LocalBlocked`表示未发送，本地最终CALL_ERROR，初次次数0。`NoSend`只能在010能证明未交给transport时抛出，撤销预留；重启未知发送绝不退款。普通传输异常计CALL_ERROR并耗一次。
- `Outcome`由010返回已校验内容`payload`、原始content、供应商外壳`envelope`、原错误及可选Retry-After。分类只能CALL_ERROR/PARSE_ERROR/INCOMPLETE_RESULT。009保存真实内容，不解释JSON或修补schema，不因Badcase重试。
- 009唯一拥有首次加两次重试预算，默认2/5秒，合法Retry-After优先。每次尝试留请求/配置/响应/错误，成功即停。不同case、阶段、侧及gap各自计次，不能改身份重置耗尽预算。
- TX03提交结果未知时，原attempt UUID读回，再决定发送，不能生成新UUID计第二次。TX04失败时保留内存响应、冻结任务新调用、本地每5秒重新保存；这不是模型重试。进程此时被杀会失去未保存响应，该次仍耗预算。
- 业务和编程钩子错误保留持久任务及窗口，暴露runtime_error，不伪装模型结果。恢复检测窗口或计次不一致时拒绝启动，须修复真实存储，不能自动清空。

## HTTP与运行边界

`GET /api/v1/tasks`、`GET /api/v1/tasks/{UUID}`返回持久状态、阶段、revision、进度及计次。`POST /api/v1/tasks/{UUID}/cancel`接收`operation_id`与`expected_revision`；变化409后须重新读取，QA或终态不能取消。

`POST /api/v1/evaluation-tasks`预留已认可的入口及固定版本字段。仅当后续真实transport、业务builder及hooks均注册后才能启动；当前返回409 DEPENDENCY_NOT_READY，零任务、零模型调用。测试替身只在`backend/tests/`注入，不在产品接口提供模拟运行按钮。效果启动及人工抽检由015～018接入，不在本轮实现。

`downstream_items`屏蔽取消任务；后续指标/QA/效果业务仍须检查task资格。本轮只证明取消工作记录删除、来源保留和事务钩子不被迟到响应调用；尚未建立的业务表要在020/022做完整集成验证。

## 本地验证

从项目根运行`./backend/run-task009-tests.ps1`。它将真实进程测试与TestClient测试隔离，沿用008已经披露的Windows混跑限制；不覆盖008原测试证据。命令、逐验收预期/实际与证据见`.codex/task009-verification.md`。

U10仅验证并发规则及持久计时，不代表三批耗时达标；阈值留TASK-023。U12正式样本事项开放。用户尚未确认本轮产物，TASK-010～024没有本次执行授权。


### 2026-10-07 TASK-009产物认可（最新状态，Codex）

用户针对TASK-009代码及本地验证交付明确回复“确认”。TASK-009已完成，实际产物已获用户认可。范围为已展示的共享任务窗口、持久计次、恢复取消、事务交接接口与103项本地证据；不是全产品最终验收或后续执行授权。之前“待用户确认”是交付时历史检查点，本条为最新认可记录。

010单次模型调用与截止/清理、后续业务接入和020/022全链路验证仍留原任务；U10耗时阈值留023，U12正式样本事项开放。已披露的Windows隔离验证、依赖弃用提示、008接受的限制及未保存响应可能重复处理/费用边界继续保留。TASK-010～024未启动，未获本次执行授权。本次只更新认可状态，不修改产品代码、业务设计或原测试运行快照。
