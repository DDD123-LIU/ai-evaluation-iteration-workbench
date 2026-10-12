# TASK-011 评分分类与知识缺失证据模块

日期：2026-10-07｜执行者：Codex｜S2｜状态：已完成，实际产物已获用户认可

## 已实现的组件

- `app/prompts/evaluation-v1.md`：首份实际完整评测Prompt。`manifest.json`绑定版本、正文哈希和验收来源；配置加载器冻结DeepSeek型号、参数及全文。
- `app/services/evaluation.py`：按008的指定对话、规则、知识库版本组装原上下文及待评回复；以009的Plan/ItemSpec传递，不查“最新版本”替换来源。
- `app/domain/evaluation.py`：单条三维均值、两位小数及Badcase判定。125种合法分数组合有确定性验证。
- `app/models/evaluation.py`及`migrations/versions/0003_evaluation.py`：评分、原因、逐点知识缺失证据及最终异常。增量迁移保留008/009表。
- `EvaluationHooks`：在009的结果事务内保存E07/E08；每点保留稳定ID、原文片段、reason及010返回的消息/偏移定位。保存失败整体回滚。取消后级联清除结果，迟到回复由009拒绝。
- `results(database, task_id)`：只读单条结论、证据和完整追溯。最终异常单独返回，不当作Badcase。

## 职责与接入

```text
008 指定资料版本 → EvaluationBuilder + evaluation-v1
                           ↓ 冻结Plan/请求
009 窗口/并发/计次/取消/恢复 → 010 SDK/结构/证据校验
                           ↓ 已校验Outcome
EvaluationHooks → 同一SQLite事务：attempt + result + gap
                           ↓
后续012批次指标 / 013 QA阶段（本次未实现）
```

普通任务启动时须冻结真实Q配置。因此Builder要求调用方提供`qa_config`；Hooks要求提供`next_hooks`。后续模块负责普通任务阶段衔接和终态，本模块不伪造QA完成或提前释放窗口。生产`main`未自动装配缺失的012/013，当前产品不能直接完成整条普通批次链路。该模块完整实现其组装、持久保存和读取职责；端到端页面及批次汇总仍属后续任务。

测试入口`tests/evaluation_test_server.py`显式注入SDK及后续阶段替身，仅用于本地验证，不进入生产main。测试使用合格case完成阶段，因此不冒充QA生成模块。

接口用法：`EvaluationBuilder(db, approved_q_config)(body)`；`TaskService(db, hooks=EvaluationHooks(next_hooks))`采用既有009构造契约；010的`DeepSeekTransport`与009的`Executor`沿用。实际构造签名以services/execution.py为准。

011不调用第二套SDK，不重复校验补造缺失证据，不增加重试。009发送前计次、累计最多3次；010禁用SDK隐式重试。保存重试不增加模型请求。恢复使用持久快照，不重新加载当前Prompt。只有规则及知识库联合仍缺信息才允许知识缺失标签；真实语义判断由模型按Prompt执行，代码不以关键词猜测或重写分类。

单纯冲突和冲突伴违规承诺均禁止QA。违规承诺伴真实知识缺失但无资料冲突，仍可保留缺失次因并供后续QA使用，依据004 RULE-01及U02。只是派生资格，不生成标准问。

## 本地运行与验证

在项目根运行：

```powershell
./backend/run-task011-tests.ps1
backend/.venv/Scripts/python.exe .codex/task011-review.py
```

第一条运行4组独立本地HTTP/进程冒烟，再运行单元、契约、SQLite故障及008～010必要回归。第二条核对输入哈希、Prompt哈希、原迁移/依赖不变、Python语法和真实测试证据。逐项结果见`../.codex/task011-verification.md`。本地运行依赖沿用008～010，无新增包。

## 版本及未验证项

输入版本和SHA256：`../.codex/task011-inputs.json`，16个基线/认可/证据文件。Prompt为evaluation-v1；模型契约model-contract-v1；deepseek-flash（已确认发布DeepSeek-V4.1-Flash），thinking=enabled/reasoning_effort=high/max_tokens=32768，其余配置完整保存在快照。实际参数以003及010的settings为准。

缺DEEPSEEK_API_KEY，未调用真实API。替身不证明评分、主次因、知识缺失判断或F32抗评分暗示能力。正式F06/F08阈值保留：每维≥45/50，Badcase≥45/50，主因和完整次因集合各≥23/25；失败计错，不剔除分母。021固定样本后022验收。本次不准备正式50条或019调试集。U10留023，U12实际样本仍开放。

Windows进程测试独立运行；新增测试终止整棵自建进程树，避免虚拟环境启动器残留。已有Starlette/httpx弃用提示未改变功能，保留记录。具体测试结果及限制见验证说明。


### 2026-10-07 TASK-011产物认可（最新状态，Codex）

用户对TASK-011实际模块、evaluation-v1版本化Prompt及本地验证交付明确回复“确认”。TASK-011已完成，实际产物已获用户认可。认可范围为已交付的评分分类与知识缺失证据模块、原文/资料/Prompt/模型配置追溯及343项本地证据；不是真实模型语义通过或整产品最终验收。

真实DeepSeek API因密钥缺失未验证，评分、归因、知识缺失与F32抗评分暗示效果仍未验证。完整普通批次链路待012/013真实配置和阶段接口接入。U10耗时阈值留023，U12正式样本留021且开放；既有Windows验证隔离及依赖弃用提示保留。TASK-012～024未启动、未获本次授权。此前“待用户确认”是交付时历史检查点，本条为最新认可记录。本次仅同步认可状态，不修改代码、需求/设计基线或原测试证据，不重跑产品测试。
