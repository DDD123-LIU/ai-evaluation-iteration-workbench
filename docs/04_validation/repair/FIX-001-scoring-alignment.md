# FIX-001 评分口径承接核对记录

**2026-10-10｜Codex｜最新关闭记录：**用户针对FIX-001文档任务卡关闭请求回复“确认”。本卡文档范围已获认可并关闭；FR-03整体产品问题及真实模型复验仍开放。FIX-002/003未关闭。以下待确认文字保留为历史检查点，本次无产品变更或模型调用。

**2026-10-10本轮补充（Codex）：本卡文档范围已完成并核对关闭标准，待本人确认关闭，未自动关闭。** 详见[本轮记录](FIX-repair-round-progress.md)第1章及`.codex/fix-repair-round-audit.json`。下文“002/003未确认”“Prompt未改”为001执行时历史状态；当前002/003卡已确认，002已产生E-v3候选，但真实语义未验证。FR-03整体产品问题保持开放。原文档/检查证据保留。

日期：2026-10-10（Asia/Shanghai）｜执行者：Codex｜版本：1.0｜档位：S2

## 1. 授权及结论

用户在逐卡提交FIX-001后回复“确认任务卡”。按上下文仅确认FIX-001，执行范围为已有决定的文档同步和实现指导；FIX-002/003未确认、未执行。

本次已同步文档，产品代码及Prompt未改。文档一致性核验结果见`.codex/fix001-check.json`。FR-03文档承接缺口已处理；产品实际承接仍待FIX-002，不将FR-03整体产品阻塞记为关闭。FR-01及F06失败保持，FR-02和F09/F11/F19保持。未运行真实语义或正式复验。

## 2. 决定来源及边界

1. `docs/04_validation/evidence/task021-acceptance-v1/checks/intent-score-decision-20261009.json`：本人原话“知识库有的，但是没有识别提炼出来那一条的，都是1分。”澄清“仅仅指意图识别 1分”。仅意图受约束，不将准确性/服务一起固定1。
2. 同目录`ACC-018-intent-decision.json`：本人原话“给4分 他理解了 但是回复错了”。这是具体案例分数，用于说明理解与回答正确性不同，不推出所有理解问题的回复统一4分。
3. `docs/04_validation/acceptance-fixture-manifest.md`第13章记录已有统一口径及未同步限制；50条最终认可在`evidence/task021-acceptance-v1/confirmations.json`，58冻结哈希在freeze-manifest.json。早期单维决定的pending不覆盖最终认可。本次不修改这些文件。
4. `docs/04_validation/final-review.md`第5章FR-03确认承接缺口，但没有证明全部FR-01失败由此造成。

规则正文统一维护在`RDD/decision-map.md`“意图评分补充决定”。Spec/协议引用该处。适用：已有答案但未识别提炼正确条目；不适用自动推断：所有事实错误、所有违规承诺、所有低服务分。不能新增逐维度档位。主次因仍依原证据和特殊规则，不从意图1直接推出意图错误主因或知识缺失；已有答案却兜底的准确性1/敷衍主因规则保持。

## 3. 承接矩阵与实际变更

| 文件/位置 | 本次处理 | 状态 |
|---|---|---|
| RDD/decision-map.md 已确认判定规则 | 增补已有决定、边界和原话来源，作为规则正文 | 已同步 |
| docs/02_design/behavior-spec.md RULE-02 | 增补指向规则正文的适用说明及独立维度边界 | 已同步 |
| docs/02_design/model-contract.md 第4章承接说明（第5章前） | 引用规则，明确E/rubric一致与JSON协议不变 | 已同步 |
| RDD/验收清单.md F06 | 原共用档位及45/50标准仍有效；已有决策来源引用可用，不改冻结验收标准 | 无需修改 |
| backend/app/prompts/evaluation-v2.md及manifest | 正文未明确补充口径 | 未改，留FIX-002 |
| backend/app/services/evaluation.py::request_for | system与user.rubric均用config.full_prompt | 无需在本卡改动；新版本须检查两处一致 |
| backend/app/prompts/evaluation.py::prompt_config | manifest加载正文及SHA绑定，返回ConfigSpec | 未改；后续沿用版本机制 |
| backend/app/domain/evaluation.py::derived | 仅派生均分/Badcase/QA资格，不负责语义评分 | 未改，不在这里按案例纠分 |

## 4. 实现指导与验证交接

FIX-002应先用独立模拟资料定位口径缺口的实际贡献，不能直接宣称全部根因。候选E新正文须明确区分“漏识别已有条目”与“理解问题但答错”；保持原准确性/服务、主次因、冲突、知识缺失及QA规则。新正文独立存版并更新manifest，历史任务ConfigSnapshot不得覆写。request_for已把同一full_prompt用于system及rubric；验证新任务绑定及请求实际内容，避免只改一侧。不得将正式标签或ACC编号送模型，不在保存后覆盖分数。

独立验证至少有：已有条目未提炼、理解问题而事实错误、理解问题而违规承诺、资料确实缺失、服务无有效下一步与正常合格对照。无确切分数来源的条件不猜填；需本人判断时逐项提出。本文未编制调试样本，不调用模型。

E变化会影响F05～11、F19～21、F32及D01～05/D08/D10与效果链，不能继承旧语义通过。最终正式50条及必要性能补测均先交方案确认。原45/32/35及漏QA保持为历史结果，三批旧性能仅覆盖旧版本。

## 5. 验证、风险与状态

本次仅运行本地文档和哈希检查，不运行产品测试、模型或性能：无产品变更，且本卡排除该范围。检查原92产品、58冻结文件及规划基线中的历史证据不变；检查三处承接、引用文件、边界文字及允许变更范围，保存实际前后SHA和diff。

实际命令：`backend/.venv/Scripts/python.exe -X utf8 .codex/fix001-check.py`；163项检查，0失败。`git diff --check`通过。当前相关文档原本未跟踪，空Git diff不能证明内容；本地检查另固定前后SHA、逐处新增承接及范围。运行库不作为历史不可变证据检查，原快照、冻结文件和其他历史附件保持。变更清单及前后SHA见fix001-check.json；本文第3章列实际修改位置，未生成Git可追踪补丁。

状态：已修改=文档是/产品否；本地验证=文档检查结果单列；正式复验=未运行；FR-03文档缺口=已处理/产品承接=待FIX-002；FR-01/02=未关闭；产品仍“不通过，有阻塞”。用户产物认可尚未记录。本次没有证明评分效果改善。

规范：沿用using-vibe-delivery-kit、routing-by-risk、systematic-debugging及verification-before-completion和package任务卡/调试/验证/交付检查。S2文档承接；不重做RDD，不新增架构/S4审查，不接CI、不启多agent。指定MCP不可用，继续本地检索与审计降级。
