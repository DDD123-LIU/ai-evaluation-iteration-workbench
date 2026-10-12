# TASK-016 旧新回复生成与效果评测模块
2026-10-07｜Codex｜S2｜已完成，实际产物已获用户认可（原运行证据不变）

## 运行、代码及配置

沿用008单worker本地启动方式，启动迁移至0008_effects。没有新增依赖。项目根运行 `./backend/run-task016-tests.ps1`。当前已有预览进程不由本任务替换；重启原入口才载入新路由。

实际路径：`app/{models,domain,services,api}/effects.py`、`migrations/versions/0008_effects.py`；`app/prompts/customer-reply-v1.md`、`customer-reply-manifest.json`、`customer_reply.py`；`app/main.py`接入路由和按kind分发hooks，`services/execution.py`仅增加原启动事务内started钩子。测试为`test_effects.py`、`test_effects_integration.py`、`test_effects_api.py`、`test_effects_process.py`与测试专用`effects_test_server.py`。

G-v1按003认可配置：deepseek-flash／文档发布DeepSeek-V4.1-Flash，thinking disabled、temperature=0、max_tokens=8192、json_object、非流式。E-v1完整复用011已认可Prompt和010设置，thinking enabled/high、max_tokens=32768。三次预算、300秒截止、退避和SDK无隐式重试沿009/010，本模块不新增重试逻辑。资产manifest保存版本/正文哈希/F27/D08/U12；任务启动冻结全文和支持参数，历史不读取“最新Prompt”替换。

## 真实接口和职责

`POST /api/v1/supplements/{id}/effect-tasks`只接`operation_id` UUID。来源只取015已确认的实际历史快照去重case集合、原问题/H、原规则、原库及选中新库。无来源/未确认拒绝，不创建任务；共享slot忙碌409，无排队。模型未接入时409，不创建任务；缺密钥仍可查询已有记录。相同operation原请求返回原task，不同明确动作可对同一记录新建独立task，旧记录不覆盖。

`GET /api/v1/effect-tasks/{id}`返回固定来源、原问题/H、两侧G和E状态/实际次数、生成回复、三分/理由/主次因/逐点证据、所有尝试与请求/响应、完整冻结配置、两侧同范围三指标及不可比原因。取消返回无有效来源/结果/指标，仅任务取消状态。运行期metrics.pending，自动全终态后available。人工作用字段human_effect_conclusion始终为null；本模块不生成改善/持平/变差或人工结论。

已有009 `/tasks/{id}`保留执行进度及revision，`/tasks/{id}/cancel`仍是唯一取消入口。原012普通summary/cases接口继续仅用于ordinary；效果完整结果从上述effect接口读取，不冒充普通汇总。017 sampling路由仍不存在。018负责页面整合。

## 事务、保存及来源

```text
015已确认补充 → 精确去重case、原H/规则、旧库/新库
                         ↓ 009同一启动事务
          slot＋task＋EffectTask＋TaskCase＋G/E配置＋两侧G＋operation
                         ↓
             旧G / 新G（全局最多3请求，每单元≤3次）
                         ↓ 各侧G保存与对应E创建同事务
             旧E / 新E（各自复用已保存G，不再调用G）
                         ↓
           全自动终态 → 释放slot → 只读指标/可比证据供017/018
```

EffectPlan继承009 Plan，补充身份/新库只进入effect序列化，普通Plan及其历史operation哈希结构不变。started钩子在已有TX02保存effect_task；不另起事务、调度器或运行窗口。只增加effect_task/generation_result两张表，旧迁移和数据保留。配置每stage共用一个冻结快照，两侧同模型/Prompt/支持参数。

G输入只有原H与完整原规则、该侧完整库。两侧都重新生成，不把上传回复作为旧侧基线。G成功保存原文并创建同侧E，E复用011 request_for，以本侧G.reply作为target_reply，不改此前H。两侧结果按item/side独立保存。G最终失败不建E或假计E次数；E重试不重G。011保存E三分、分类及gap，derived(kind=effect)永不QA；效果hooks没有Q阶段交接。

009先保存次数再发送、恢复保留成功、未知发送占预算、取消门/epoch丢迟到、存储故障只重做本地保存并保留窗口都不变。取消effect自动阶段清除effect_task和G/E有效结果，不动来源普通批次、补充或导出。已发调用仍可能计费；重启未知处理不保证外部恰好一次。

## 指标与可比

全终态才按012 calculate公式输出各侧counts/raw/display。成功分母为该侧G及E均完整成功的case；任一阶段最终失败按case计一次异常，固定输入N不缩。零成功通过率和均分null、异常率100%；显示两位。缺失/非法型号或指纹不改变成功业务结果和指标分母，不重调成功项，只使case不可比。

可比要求两侧G/E完整且具持久配置/请求/响应。分别比old G与new G、old E与new E的非空字符串model/fingerprint；同类型缺失、非法或不同均不可比，不要求G与E跨类型相同。另核对同stage配置和去除允许差异后的输入。两側E的target_reply自然来自各侧G；knowledge_base是唯一资料差异。可比不等于知识改善，也不能排除模型随机波动。

## 016与后续边界

017需消费固定case集合、comparison.comparable及各侧状态，持久抽样/补抽和人工结论；本模块只准备真实结果，不实施抽检、不创建占位抽样或结论记录。018据详情展示原文/追溯/不可比信息。019语义调试、021正式集合、022业务与人工效果验收、023性能均未执行。U10及U12实际样本保持开放。

当前没有密钥，真实DeepSeek调用、回复/评测语义和知识补充效果未验证；本地MockTransport、SQLite、真实HTTP进程和回归只证明模块规则与接口。无CI、正式样本、真实知识库连接或自动补库。本地证据见项目`.codex/task016-verification.md`。


### 2026-10-07 TASK-016产物认可（最新状态，Codex）

用户对TASK-016实际代码、必要版本化Prompt、接口及本地验证交付明确回复“确认”。TASK-016已完成，实际产物已获用户认可。范围为所选补充来源case集合、旧新两侧重新生成及分别评测、版本追溯和独立结果保存、指标复用、不可比较标记，以及统一调度计次/恢复/取消接入与526项本地验证证据。

本次仅同步认可记录，不修改产品代码、Prompt、需求/设计或原测试运行证据，不重跑产品测试。真实DeepSeek API及模型语义因缺密钥仍未验证，补库改善未验证；本次认可不表示知识补充效果通过或产品最终验收通过。U10耗时阈值留023、U12实际正式样本留021且开放。TASK-017～024未启动且未获本次授权，不自动推进。此前“待用户确认”为交付时历史检查点，本条为最新认可状态。
