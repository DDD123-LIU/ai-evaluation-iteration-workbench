# TASK-014 QA人工审核与导出快照模块
2026-10-07｜Codex｜S2｜已完成，实际产物已获用户认可（原运行证据不变）

## 运行与实际代码

Windows项目根运行 `./backend/run-task014-tests.ps1`，执行本模块及008～013本地回归。沿用008工程和现有运行入口，启动迁移至0006；未替换用户已有预览进程，旧服务须重新启动才加载新路由。没有新增依赖、模型调用或页面。QA内容正确性须本人判断。

| 路径 | 职责 |
|---|---|
| app/services/qa_review.py | 人工问答修改、明确审核、选择导出、操作重传及历史读取 |
| app/api/qa_review.py；app/main.py | 请求类型/额外键/版本约束、真实路由接入 |
| app/models/exports.py；migrations/versions/0006_qa_exports.py | 导出事件、不可变条目及原写入回执；新增三表，不改旧表/旧迁移 |
| tests/test_qa_review.py、test_qa_review_integration.py、test_qa_review_api.py、test_qa_review_process.py | CSV、状态、SQLite事务故障、并发、实际API与HTTP强杀重启 |

## 接口契约

共同约束：所有写入operation_id为UUID；修改/审核expected_revision为非负严格整数；未知字段拒绝。更新200，导出创建201、同操作重传200。过期版本409；必填/类型422；不存在404；明确写失败503/not_committed；提交确认未知503/unknown。原GET /operations/{id}可查本模块提交，不需要第二提交索引。

| 方法/路径 | 请求或输出 |
|---|---|
| PATCH /api/v1/qa/{id} | question、answer、operation_id、expected_revision；返回当前写入的问答、来源编号、固定分类、审核态、revision |
| POST /api/v1/qa/{id}/approve | operation_id、expected_revision、confirm=true；仅明确人工确认及四字段完整才approved |
| POST /api/v1/exports | selected_qa_ids非空集合、与选择集合完全一致的expected_qa_revisions映射、operation_id；返回事件id、时间、item_ids、文件名、原字节长度/hash、download_url |
| GET /api/v1/exports | 事件摘要；可筛source_batch_id及offset/limit；不读取当前QA代替历史 |
| GET /api/v1/exports/{id} | 当时条目：item id、QA/revision、case/原批次引用及四字段副本；提供015实际历史输入 |
| GET /api/v1/exports/{id}/file | 数据库内保存的UTF-8 BOM CSV字节，固定四列及原样内容；反复下载不建新事件 |

问题分类固定“知识库缺少对应信息”，来源编号从不可变导入case取值，二者不能由编辑API改写。只有pending_review/approved两审核态，生成失败继续013单列，不生成可审核qa。标准问/答案实际变动保存后pending_review且revision+1；原样保存维持审核态/revision。查看或取消本地编辑不提交写入。明确审核改变状态也推进revision，用于防止过期导出。再次导出必须使用当前已通过且完整的真实版本。

## 事务与历史

```text
本人修改/确认 → 核对revision → QA更新＋operation＋原回执 → 同一次COMMIT
本人选择导出 → 核对全部资格/版本 → 生成四列CSV
                                      ↓
                         event＋items＋精确bytes＋operation＋回执
                                      ↓ 同一次COMMIT
                           下载旧event/file（只读）
```

写入采用008/009同一database.write_lock及SQLite事务。操作编号重传返回原提交回执，即使QA后来又被修改，不误报当前内容为旧动作结果；同编号异动作/内容409。qa_write_receipt仅保存人工提交的原返回结果，承接007 TX09，并不增加审核状态或新业务功能。

导出按已认可007来源批次身份、case原输入顺序、gap顺序排序；去重选择集合但不自动追加QA。CSV使用Python标准库csv，列序“标准问、参考答案、来源案例编号、问题分类”，UTF-8 BOM，CSV逗号/引号/换行正确转义。文件名沿007 `qa-{UTC时间到毫秒}-{事件UUID}.csv`。允许跨原批次导出，不新增仅一批限制；015补充记录的单原批次约束由015负责，本次不实现。

每次新业务导出新event/items，允许内容相同的重复导出。历史条目含导出时qa_revision、来源全局case/原批次引用，四字段完全复制；当前QA后续编辑、回待审核或再导出B均不改变A及A的历史资格。015可使用detail中的具体item_id及原内容；不得用当前问答代替。没有历史修改API，没有exported/pushed/驳回状态。

浏览器下载不在数据库事务内。下载失败不撤销已提交事件，重新下载同URL返回原字节。后端不保证浏览器最终保存到磁盘；实际页面/下载反馈留018。未知提交应先查operation，健康数据库确认未提交才同ID原请求重传；不可读时继续未知。

## 验证及边界

440常规＋7独立HTTP/进程测试，共447通过，无跳过。其中014新增40常规及1进程，008～013回归406。逐F22/F23/F24/D06、输入哈希、命令和证据见项目.codex/task014-verification.md。QA内容语义不是自动测试判断，未执行用户正式答案正确性验收、真实模型API或性能。U10留023、U12实际样本留021保持开放。

本模块等待用户产物确认。无015补充关联、自动补库、额外AI审核、效果验证或018页面；TASK-015～024未启动，产品最终验收未执行。


### 2026-10-07 TASK-014产物认可（最新状态，Codex）

用户针对TASK-014实际代码、接口及本地验证交付明确回复“认可”。TASK-014已完成，实际产物已获用户认可。范围为人工补答与明确审核、两审核状态、修改及版本冲突、选择导出、四列CSV、同事务原字节和不可变历史快照、原操作读回及447项本地验证证据。

本次仅更新认可记录，不修改代码、需求/设计或原运行证据，不重跑产品测试。页面整合留018，答案内容正确性仍由本人判断；历史快照供015读取，实际补充关联尚未执行。U10留023、U12实际样本留021保持开放。真实模型语义仍沿013未验证，产品最终验收未执行。TASK-015～024未获本次执行授权，不自动启动。此前“待用户确认”为交付时历史状态，本条为最新认可记录。
