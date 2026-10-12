# TASK-015 知识库补充关联模块
2026-10-07｜Codex｜S2｜已完成，实际产物已获用户认可（原运行证据不变）

## 运行和路径

沿用008的安装与单worker运行入口。启动时Alembic升级至0007_supplements。没有新增依赖。项目根运行 `./backend/run-task015-tests.ps1`。已有预览进程须重新启动才能载入新路由；本次不替换用户进程、不部署。

实际代码：`app/models/supplements.py`、`services/supplements.py`、`api/supplements.py`、`migrations/versions/0007_supplements.py`；`app/main.py`只接入路由。测试：`tests/test_supplements.py`、`test_supplements_api.py`、`test_supplements_process.py`。

## 调用契约

`POST /api/v1/supplements`：new_kb_id、source_batch_id、export_item_ids、confirm、operation_id。所有标识使用实际UUID，confirm必须为布尔true。export_item_ids选择014导出详情中的具体item.id，不能传QA.id或event.id。新记录201；同operation相同请求重传200，返回原记录；不同内容409。确认失败422，未创建记录或任务。空选择返回NO_VALIDATION_CASES及“无可验证案例”。上传或导出本身不产生补充确认。

`GET /api/v1/supplements`：可按new_kb_id/source_batch_id筛选；offset/limit分页。`GET /api/v1/supplements/{id}`：确认时间、原批次和固定版本、所选历史四字段、导出事件、QA身份、case原问/回复/H、去重case集合和资料/原任务读取链接。只读，无再次确认/修改/自动补库动作。

`SupplementService.validation_input(id)`是016的真实只读消费接口。提供详情及008读取的new_kb_id/old_kb_id/rule_version_id完整资料。016须先检查confirmed、can_validate及source_case_ids非空，再按009窗口规则创建任务。本次没有实现effect-tasks路由；请求仍404，不能把接口准备当成效果验证完成。018负责入口和展示，本次没有页面。

## 事务与不可变来源

```text
本人外部编辑CSV → 008导入新库 → 本人选择014具体历史条目并确认
                                            ↓
                       Supplement＋SupplementItem集合＋OperationCommit
                                            ↓ 同一次COMMIT
       新库 → 历史事件/条目四字段 → QA → case → 原批次 → 原规则/旧库
                                            ↓
                            仅选中来源按case去重 → 016将来消费
```

沿用SQLAlchemy/SQLite/Alembic、database.write_lock和008的OperationCommit。同操作内容按来源集合规范化，重复勾选及顺序变化不新建记录。不同operation表示新的人工业务记录；同新库、同原批次均可多个独立记录，不增加次数上限。每条补充只接受一个有效普通原批次，不接受取消批次、未导出的QA或混批条目。

历史问答直接读取ExportItem，不用当前QA内容、状态或“最新导出”替换。可同时选择同一QA的A/B历史内容；保留每个item，只对验证case去重。原规则和旧库从OrdinaryTask固定依据读取，不用最新上传替换。新库只校验已导入且kind=kb；本模块不会判定知识内容是否有效或确实补齐。该事实由本人明确确认，不增加时间或语义匹配规则。

任何flush失败，记录、关联与operation全回滚。COMMIT异常返回unknown，客户端先用既有 `GET /api/v1/operations/{operation_id}` 查回；存在则读取原记录，不存在再用原编号原请求重传。历史记录只新增，不提供修改接口。迁移仅新增两张表，旧QA、证据、导出字节和快照不改。

## 验证边界

本地规则、事务故障、API、并发幂等及独立HTTP强杀重启证据见项目 `.codex/task015-verification.md`。这些证据不证明本人实际采用了哪些知识内容，也不替代答案正确性、真实模型语义、产品验收或性能。无CI、真实模型API、真实知识库连接。U10留023、U12实际正式样本留021，保持开放。016～024未启动。


### 2026-10-07 TASK-015产物认可（最新状态，Codex）

用户对TASK-015实际代码、接口及本地验证交付明确回复“确认”。TASK-015已完成，实际产物已获用户认可。范围为本人实际补充确认、具体不可变历史快照关联、完整来源追溯、所选来源case去重、同事务保存与原操作重放，以及480项本地验证证据。

本次仅同步认可记录，不修改产品代码、需求/设计或原测试运行证据，不重跑产品测试。本人实际采用知识内容仍由本人确认；页面整合留018，效果任务及旧新生成留016。U10留023、U12实际正式样本留021且开放，产品最终验收未执行。TASK-016～024未启动且未获本次授权，不自动推进。此前“待用户确认”为交付时历史检查点，本条为最新认可状态。
