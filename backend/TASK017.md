# TASK-017随机抽检与人工效果结论模块
2026-10-07｜Codex｜S2｜已完成，实际产物已获用户认可（原运行证据不变）

## 运行与实际路径

沿用既有单worker本地启动及资料目录锁，启动自动迁移至0009_sampling。无需新依赖。项目根执行 `./backend/run-task017-tests.ps1`。当前已运行进程不会自动载入变更，原入口重启后使用新路由；不部署。

代码为`app/{domain,models,services,api}/sampling.py`、`migrations/versions/0009_sampling.py`；`services/effects.py`抽出同session读函数并接入终态抽样，`main.py`只接路由。测试`tests/test_sampling.py`、`test_sampling_integration.py`、`test_sampling_api.py`、`test_sampling_process.py`。不新增Prompt、模型请求或人工修改模型结果。

## 抽样及持久化

F28/U08：N为016全部来源case，K=(N+9)//10。初抽标准库Random.sample完整参与集合；抽中失败/不可比保存comparison理由，再从成功可比且未抽集合随机补足。不缩N/K，不去掉失败轨迹，不允许本人挑样。目标不足时validation_failed且禁止人工标记。

任务UUID固定Random种子用于未提交事务的重放，避免保存失败后更换抽样；不同任务身份独立。已保存后只读draw，刷新或重启不重抽。此为技术实现，不新增业务配置。U08单次频数测试使用同一Python Random.sample实现的默认实例；任务身份重放另有确定性测试。不追加挑选统计结果。统计不能证明绝对随机，020独立复核保留。

E14新增sampling_run保存参与身份/资格理由/目标/时间/结论，draw保存唯一case/初补顺序/失败原因，human_mark保存nullable三维与revision，sampling_receipt保存原operation回执。0009仅增表，旧资料/快照/G/E保持。

016最后自动结果、E14和009slot释放同事务。轨迹写失败不发布完成/新抽样，009当前进程保留原响应重存；提交前重放同任务抽样。历史已完成016缺E14首次GET原子补建；失败503明确未确认保存，重新读该task，不发模型或创建新效果任务。

## 真实接口及职责

`GET /api/v1/effect-tasks/{task_id}/sampling`返回完整population/target/initial及replacement draws/unusable_reasons/mark/revision/status。运行中automatic_pending，取消cancelled，无有效抽检。不存在/普通task为404。没有POST重新抽样接口。

`PATCH /api/v1/effect-tasks/{task_id}/sampling/{case_id}`输入operation_id(UUID)、expected_revision(非负整数)、accuracy/intent/service（三项必须出现，可为null或改善/持平/变差）。只允许足额有效抽中项。null为未标记，保存部分进度合法。不存在有效选择422，不足/未完成409，版本冲突409，extra或非法字段422。

三维标记/独立结论/operation_commit/sampling_receipt同事务。原值保存revision不变，实际改变+1；同operation同请求读原回执，内容不同409。flush失败503/STORAGE_UNAVAILABLE全回滚；COMMIT_UNKNOWN附原operation，通过既有`GET /api/v1/operations/{id}`查提交并原请求重传。没有手动模型重试。

F29：足额未标完pending_confirmation；任一维变差not_passed，即使其他维尚空；足额全标无变差passed；不足validation_failed。新Badcase仍可比较，012普通结论、新侧指标与human_effect_conclusion分开。016详情读已保存人工结论。模拟标签不代表本人确认真实效果。

016供来源及可比门槛；017不改G/E评分/分类/追溯，人工阶段不占slot；018只需消费这些真实接口，页面整合未做。019语义/020独立复核/021正式样本/022真实业务与本人效果验收/023性能保持原分工；U10/U12开放。

逐项命令、预期、结果、诊断与完整证据见`.codex/task017-verification.md`。状态仅实现与本地验证待用户确认，产品未最终验收。


### 2026-10-07 TASK-017产物认可（最新状态，Codex）

用户对TASK-017实际代码、接口及本地验证交付明确回复“确认”。TASK-017已完成，实际产物已获用户认可。范围为随机初抽和失败补抽、参与分母及抽检目标保持、本人三维标记与独立效果结论、持久轨迹/事务故障/版本与操作重传/重启恢复，以及566项去重本地测试和U08一次1000轮原始统计证据（每case77～122次，满足60～140含界）。

本次仅同步认可记录，不修改产品代码、需求/设计或原测试证据，不重跑产品测试或U08统计。模拟人工标签不表示本人已完成真实效果判断；真实API、模型语义及补库改善仍未验证。U08模块统计不替代TASK-020独立复核；U10留023、U12实际正式样本留021且开放，产品最终验收未执行。TASK-018～024未启动且未获本次授权，不自动推进。此前“待用户确认”为交付时历史检查点，本条为最新认可状态。
