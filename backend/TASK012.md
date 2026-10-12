# TASK-012模块与接口
2026-10-07｜Codex｜S2｜已完成，实际产物已获用户认可（原运行证据不变）

## 实现及职责

- app/domain/batch_metrics.py：Q/S、T/(S×3)、E/N；原始量按整数分子分母输出。阈值用整数交叉乘法，不用浮点或显示值；展示用Decimal ROUND_HALF_UP两位。
- app/services/batch_metrics.py：读取009固定TaskCase及原始E终态、011不可变结果/最终异常。全E终态才汇总；不统计Q失败、不按attempt计case、不重调模型。
- app/models/batch_metrics.py及0004_batch_metrics：每普通task一行终态派生JSON，含原始量、显示值、独立批次结论、两预警及问题集合。只新增表，原迁移/评分/证据/依赖不改。
- app/api/tasks.py：已有列表及详情增加summary；新增已约定cases集合与case详情接口，列表摘要/详情完整依据。

```text
009 固定case / E终态 → 011评分 / 最终异常
                              ↓
          012 原始量 → 精确阈值 → 汇总快照
                       ├ 批次通过结论
                       ├ 质量预警 → 本批次Badcase集合
                       └ 异常预警 → 本批次最终异常集合
                              ↓
                    018工作台查询/跳转（未实现）
```

## 接入契约

生产组装方式：`TaskService(db, EvaluationHooks(MetricsHooks(real_qa_hooks)))`，Builder仍须真实冻结Q配置；models/SDK/Executor沿009～011。012没有Q Prompt、标准问或QA业务处理。`real_qa_hooks`沿009 BusinessHooks，负责创建真实Q单元及Q阶段终态；在全E终态事务前就绪。没有应生成Q（包括全异常）时，`MetricsHooks()`可按现有规则真实完成；若有应生成Q却缺后续hook，明确DEPENDENCY_NOT_READY，事务回滚，保留窗口，绝不假完成。生产main仍未自动配置尚未实现的013。

全E终态时011先落成功/最终异常，012同事务保存summary，再交接Q。Q运行时已完成E指标可读，Q失败不改变其分母或异常率。取消由009调用011→012清理钩子，同事务删除汇总及单条结果。未终态summary pending/data=null；取消cancelled/data=null；不生成有效结论或预警。旧011终态历史首次查询可幂等补建同一汇总，不重调模型、不改旧单条结果。保存失败明确503，不能伪造空数据或成功。

## HTTP输出

- GET /api/v1/tasks：普通批次摘要增加summary。
- GET /api/v1/tasks/{task_id}：进度与summary。
- GET /api/v1/tasks/{task_id}/cases?filter=all|badcase|errors：案例身份、问题、三维整数/综合分/合格/主因摘要或最终异常类别/次数。
- GET /api/v1/tasks/{task_id}/cases/{case_id}：原H/R、完整三分理由、主次因、gap位置、原资料/Prompt/模型配置及请求结果追溯；跨批case/取消case不能返回有效详情。

summary={status,data}。status available时data含task_id/source/counts/raw/display/batch_passed/quality_warning/error_warning/alerts。raw每指标为{numerator,denominator}，零成功的通过率及均分为null；display同样为null，018显示“无数据”，不能把null转0。pending显示“统计待完成”。异常率全失败100.00%。其他任务类型not_applicable不混用普通批次结论；调度记录缺真实结果时unavailable并明确RESULT_INCONSISTENT，仍允许看真实进度，不算有效汇总。

每alert含kind=quality|error、task_id、problem_case_ids，以及target={path:'/api/v1/tasks/{id}/cases',filter:'badcase'|'errors'}。集合按固定输入顺序，无跨批case/重试重复；质量只成功Badcase，异常只最终异常。批次通过独立于alerts：存在Badcase而通过率恰95%，无质量预警仍不通过。无邮件/飞书/外部通知或预警处理流程。

## 验证及限制

项目根执行`./backend/run-task012-tests.ps1`；输入版本及SHA256见../.codex/task012-inputs.json，逐F13～15证据见../.codex/task012-verification.md。核心固定值/边界、事务保存失败、取消/恢复、真实本地HTTP及008～011回归。确定性测试使用固定数值/替身，未调用真实API，不涉及真实模型语义或性能实测；不编正式50条。超过100的大分母只出现在纯数学舍入测试，服务仍限制1～100固定case。U10留023，U12实际样本留021且开放。完整QA/页面/效果链路待013/016/018，不启动后续任务。


### 2026-10-07 TASK-012产物认可（最新状态，Codex）

用户针对TASK-012实际代码、接口和本地验证交付明确回复“确认”。TASK-012已完成，实际产物已获用户认可。范围为批次指标、独立批次结论、两类预警及对应问题集合、原始值阈值与显示、终态/取消/恢复持久处理和381项本地证据；不是整产品最终验收或后续开发授权。

完整普通QA链路仍待013真实Q配置/hooks接入；不以替身表示QA已实现。真实模型语义沿011未验证记录；U10耗时阈值留023，U12实际正式样本留021且开放。Windows同pytest进程重开SQLite的差异及原依赖弃用提示保留，独立新进程恢复和完整性已有本地证据。TASK-013～024未启动、未获本次授权。此前“待用户确认”为交付时历史记录，本条为最新认可状态。本次仅同步认可记录，不改代码、需求/设计基线或原测试快照，不重跑产品测试。
