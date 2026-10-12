# TASK-024 最终交付审查与演示范围记录

日期：2026-10-10（Asia/Shanghai）｜执行者：Codex｜版本：1.0确认稿（报告已认可）｜任务档位：S3

**结论：不通过，有阻塞。50项中46项在已取证范围通过，4项失败。F06、F09、F11、F19未满足必要条件。报告完成不等于产品验收通过；最终交付尚未获用户认可。**

本次只审查、核验本地证据和编写报告。未修改产品代码、Prompt、正式预期或需求基线，未调用真实模型API，未重跑正式验收或性能测试，未部署、推送或发布。修订建议均未实施。

## 1. 输入与认可门槛

| 输入 | 实际状态及本次核对 |
|---|---|
| TASK-001～007 | 范围、字典、模型契约、行为Spec、交互Spec、验证方案及设计报告均有认可；007最新DG-01～05设计层关闭。RDD Gate与设计Gate分别记录，不代表产品通过。 |
| TASK-008～018 | 实际代码、模块说明及本地证据存在，最新产物认可记录已核对；旧“未执行”段落为历史。 |
| TASK-019 | 独立调试记录及认可存在；原DBG-06漏识别保留，未因报告认可关闭。调试集不替代正式集。 |
| TASK-020 | 报告及失败/未运行说明已获“确认”；认可记录与报告SHA一致。115项独立确定性验证原始JUnit有效；当时未运行F32真实模型，022另有真实成对证据。 |
| TASK-021 | 50条逐条认可，58份冻结文件哈希不变；隐私确认已记录；固定全部应生成QA为17项，最低合格16项。冻结不是模型语义通过。 |
| TASK-022 | 报告已获“是”认可，报告SHA与认可记录一致。原结论44通过、4失败、2性能待确认保留为当时快照。 |
| TASK-023 | 三个原计划批次有效；6分钟阈值获“同意”，整报告获“确认”，报告SHA一致；三批性能通过。 |
| TASK-024 | 已获仅最终审查执行授权；本报告已获本人认可；最终交付未认可。 |

前置实际产物和认可门槛满足，允许进行最终审查。未把报告认可解释为失败被豁免。详细认可原文、日期及报告SHA见020/022/023各自approval-results及021confirmations/freeze-manifest；本次读取基线见附件baseline.json。

## 2. 交付基线与证据方法

当前92个产品基线文件与020、022、023逐文件一致；涉及backend/app、增量迁移、前端及版本资产。当前完整文件清单、SHA256和依赖锁另见baseline与evidence-index。源需求、六图、Reviewer、Gate、PRD、Spec及任务资料共27份读取并固定哈希。TASK-023因本人阈值确认更新的设计引用是可追溯文档决定，未改变评分实现或020/022使用的产品版本。

| 对象 | 当前交付版本/说明 |
|---|---|
| 需求及设计 | 最新RDD、scope、data-dictionary、model-contract、behavior-spec、ui-spec、verification-plan及design-gate-review；不采用2026-10-02旧设计。 |
| 代码及存储 | FastAPI/SQLAlchemy/SQLite后端；React/TypeScript/Vite前端；backend/migrations现有0001～0009；具体SHA见附件，版本身份不只依赖Git提交。 |
| 评分Prompt E | evaluation-v2；deepseek-flash；thinking enabled/high，max_tokens 32768。 |
| 标准问Prompt Q | standard-question-v2；deepseek-flash；thinking disabled，temperature 0，max_tokens 2048。 |
| 回复Prompt G | customer-reply-v4；deepseek-flash；thinking disabled，temperature 0，max_tokens 8192。 |
| 调用配置 | 固定字段JSON、非流式；SDK隐式重试关闭；统一009发送前计次、最多3次、共享任务窗口及最多3并发。型号别名不能保证未来供应商不变，必须沿用请求/响应追溯核对。 |
| 正式资料及标注 | task021-acceptance-v1.0；50条模拟输入与标注隔离，17项预期QA；冻结58份；正式标注不得进入模型输入。 |
| 实际补充资料 | 022新知识库版本5b35127a-b965-4761-ac6d-a0e19475161e，28条，容量20GB为模拟资料；恢复文件保留期限仍缺失。 |
| 性能资料 | 023独立100条，同输入连续三批；与正式50条隔离。 |

本次执行只读SQLite完整性检查及逐结果复算；检查50条模型请求输入隔离；核对16项人工QA认可与17固定分母；解析020原JUnit；从U08原始1000轮重算；从023逐请求时间重算并发峰值及批次耗时；核对原截图及证据文件。代表详情截图case-011.png已目视检查，与持久记录相符。未声称重新操作完整浏览器链路。

本地命令：

```powershell
& './backend/.venv/Scripts/python.exe' -X utf8 .codex/task024-audit.py
& './backend/.venv/Scripts/python.exe' -X utf8 .codex/task024-delivery.py
& './backend/.venv/Scripts/python.exe' -X utf8 .codex/task024-final-check.py
git diff --check
```

第一条实际完成1433项证据一致性检查，0失败。它不是1433项产品测试，也不能抵消4项业务验收失败。第一次辅助核验脚本误把020统计数字当映射，出现TypeError；检查原始JSON后改读baseline.product_hashes，复跑成功。仅修改024辅助脚本，未改产品，未删除历史产品失败。最终文档、状态和保护文件核对结果见final-check.json。未无差别重跑单元测试；产品92文件未变，复核原始证据足以支持本次审查结论。需要改变产品或补充真实验收时，须另获授权。

## 3. 核心结果复算

| 正式语义指标 | SQLite对冻结标签复算 | 必须达到 | 判定 |
|---|---|---|---|
| 信息准确性 | 45/50 | 45/50 | 通过 |
| 意图理解 | 32/50 | 45/50 | 失败 |
| 服务质量 | 35/50 | 45/50 | 失败 |
| Badcase判断 | 50/50 | 45/50 | 通过 |
| 主因，固定25条Badcase | 23/25 | 23/25 | 通过 |
| 完整次因集合 | 24/25 | 23/25 | 通过 |

F06要求三维各自达到阈值，不能以准确性或合计平均掩盖另两维失败。全部原始输出和逐条差异保留。

QA质量：固定17项，实际16份本人已逐项认可标准问和reason，1份漏生成计不合格，16/17达到最低16份，F20质量阈值通过。F19仍要求符合资格的缺失点生成，ACC-038漏出，不能由F20比例达标替代。

U08独立原始1000轮每轮10条，轮内唯一且来源正确；每条累计81～121，处于60～140含界。本次仅重算原始记录，没有重抽挑选结果。

| 023批次/任务ID | 客户端完整耗时 | 后端持久耗时 | E/Q成功 | 实际调用 | 峰值 | 360秒判定 |
|---|---|---|---|---|---|---|
| 1 a66fa3cf-08c9-4e1c-983d-d320fc8428d6 | 217.110秒 | 216.319秒 | 100/20 | 122 | 3 | 通过 |
| 2 cfce1c9a-3fff-481d-8d36-1d89d27ff6a4 | 247.165秒 | 246.720秒 | 100/20 | 123 | 3 | 通过 |
| 3 4ac3a639-b933-4350-b507-017bbee89629 | 241.766秒 | 241.071秒 | 100/20 | 125 | 3 | 通过 |

370次含10次失败尝试，最终异常0；失败和重试均计时。Codex中断期间后台及测量进程继续，原起止完整，无作废或待补测批次，无未知未落定请求。未重置计时，未重跑。客户端最小217.110、最大247.165、平均235.347秒。本人2026-10-10确认6分钟，以客户端启动请求至首次读回E/Q全部终态逐批判定；限原机器、模型配置、相近短输入和约20QA。三批不是供应商SLA，也不证明任意长输入都满足。

## 4. 全部50项逐项审查

下表引用编号直接对应RDD验收清单。完整要求原文、020承接、022实际记录、实现路径、所有原始证据路径及承接均保存在本次acceptance-matrix.json，不覆盖022历史矩阵。表中“通过”只覆盖已明确取证的验收范围。失败项阻塞最终交付；未新增任何豁免。

| 编号 | 要求摘要 | 实现位置 | 验证证据及实际结果 | 状态/剩余承接 |
|---|---|---|---|---|
| F01 | 对象：三类CSV；正常上传；上传时校验并创建对应数据／版本 | [domain/csv_import.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/csv_import.py)<br>[services/imports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/imports.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；三类CSV编码/表头/必填/100与101/原子拒绝/历史重复/旧版本保留均有规则及真实HTTP证据；TASK-022正式三类文件和新版28条导入原字节一致。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F02 | 对象：对话CSV；无效与部分错误；上传任一错误文件时整份拒绝，指出原因及可定位错误行；超限提示拆分 | [domain/csv_import.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/csv_import.py)<br>[services/imports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/imports.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；三类CSV编码/表头/必填/100与101/原子拒绝/历史重复/旧版本保留均有规则及真实HTTP证据；TASK-022正式三类文件和新版28条导入原字节一致。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F03 | 对象：三类CSV；无数据；拒绝本次导入；不创建新版本；此前成功上传保存的旧版本保留；首次上传失败则无可用版本 | [domain/csv_import.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/csv_import.py)<br>[services/imports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/imports.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；三类CSV编码/表头/必填/100与101/原子拒绝/历史重复/旧版本保留均有规则及真实HTTP证据；TASK-022正式三类文件和新版28条导入原字节一致。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F04 | 对象：重复校验范围；上传时允许历史重复 | [domain/csv_import.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/csv_import.py)<br>[services/imports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/imports.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；三类CSV编码/表头/必填/100与101/原子拒绝/历史重复/旧版本保留均有规则及真实HTTP证据；TASK-022正式三类文件和新版28条导入原字节一致。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F05 | 对象：评分与判定；每维整数1～5；综合均值四舍五入两位；任一<4判Badcase | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [snapshot-20261009T051444385705Z.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/snapshot-20261009T051444385705Z.json)、[analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)<br>50条成功结果，分数整数1～5，合同已校验，固定Badcase判断全正确；结构枚举与主次因保留真实trace | **通过**；已取证范围通过；版本变化须评估复核 |
| F06 | 对象：AI三维评分；业务验收；三维共用已列档位，各输出≤50字符理由；4～5可写达标依据 | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)<br>准确性45/50通过；意图32/50失败；服务35/50失败，各阈值45/50，分别判定 | **失败**；阻塞；另行授权修复与复测 |
| F07 | 对象：分类结构；主因唯一；次因前四类多选排除主因，可空；普通组合按实际影响 | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [snapshot-20261009T051444385705Z.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/snapshot-20261009T051444385705Z.json)、[analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)<br>50条成功结果，分数整数1～5，合同已校验，固定Badcase判断全正确；结构枚举与主次因保留真实trace | **通过**；已取证范围通过；版本变化须评估复核 |
| F08 | 对象：业务判定及分类一致率；自动逐项与固定标注对比 | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)<br>Badcase50/50；固定25条主因23/25、完整次因24/25；个别差异保留，集合顺序无关 | **通过**；已取证范围通过；版本变化须评估复核 |
| F09 | 对象：联合知识与特殊评分；纯兜底准确性3；含编造1；按知识缺失识别 | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)、[human-qa-review.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/human-qa-review.json)<br>7条知识缺失主因兜底及2条编造特殊准确性分别符合3/1；但ACC-038诊断日志期限缺失被误判为其他资料冲突，缺失证据和QA漏出。不能由F08整体比例达标覆盖本项差异。 | **失败**；阻塞；另行授权修复与复测 |
| F10 | 对象：特殊Badcase；前者准确性1主因敷衍不生成QA；后者准确性1合规主因、缺失次因保留 | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)、[deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；正式ACC-017已有答案却兜底为准确性1/敷衍；ACC-018/019/030/050违规承诺均准确性1、合规主因并保留知识缺失次因，019冲突禁止QA。其他意图/服务差异仍列F06。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F11 | 对象：资料冲突；准确性1；单纯冲突主因其他／证据不足，同时违规承诺时唯一主因为违反平台规则，做出不当承诺；均不生成QA | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)<br>ACC-038与固定资料冲突判断不一致；ACC-049纯冲突主因应其他，实际合规；不能择一或新增优先级 | **失败**；阻塞；另行授权修复与复测 |
| F12 | 对象：重试；失败、部分失败；首次加最多两次重试；成功即停；耗尽记最终异常一次 | [domain/model_contract.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/model_contract.py)<br>[model_client/deepseek.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/model_client/deepseek.py)<br>[runtime/executor.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/runtime/executor.py) | [attempt-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/attempt-summary.json)、[database-snapshot.sqlite3](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/database-snapshot.sqlite3)<br>50E和16Q最终成功；ACC-011解析失败、ACC-038结果不完整各重试1次后成功；异常与业务Badcase分开保存 | **通过**；已取证范围通过；版本变化须评估复核 |
| F13 | 对象：批次计算；部分失败；通过率84/90，平均1080/(90×3)=4，异常率10%；两预警；整批不通过 | [domain/batch_metrics.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/batch_metrics.py)<br>[services/batch_metrics.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/batch_metrics.py) | [snapshot-20261009T051444385705Z.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/snapshot-20261009T051444385705Z.json)、[final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)<br>25合格/50成功，通过率50.00%；582/150平均3.88；0/50异常0.00%；质量预警、无异常预警、批次不通过；边界规则另引用020证据 | **通过**；已取证范围通过；版本变化须评估复核 |
| F14 | 对象：阈值边界与整批结论；异常率≤5%且无Badcase才通过；异常率恰好5%不触发异常预警，超过5%触发；任一Badcase不通过；通过率恰好95%不触发通过率预警 | [domain/batch_metrics.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/batch_metrics.py)<br>[services/batch_metrics.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/batch_metrics.py) | [snapshot-20261009T051444385705Z.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/snapshot-20261009T051444385705Z.json)、[final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)<br>25合格/50成功，通过率50.00%；582/150平均3.88；0/50异常0.00%；质量预警、无异常预警、批次不通过；边界规则另引用020证据 | **通过**；已取证范围通过；版本变化须评估复核 |
| F15 | 对象：整批失败／无成功数据；通过率、平均分无数据；异常率100%且预警；整批不通过 | [domain/batch_metrics.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/batch_metrics.py)<br>[services/batch_metrics.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/batch_metrics.py) | [snapshot-20261009T051444385705Z.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/snapshot-20261009T051444385705Z.json)、[final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)<br>25合格/50成功，通过率50.00%；582/150平均3.88；0/50异常0.00%；质量预警、无异常预警、批次不通过；边界规则另引用020证据 | **通过**；已取证范围通过；版本变化须评估复核 |
| F16 | 对象：执行窗口；阻止提交新任务，无排队；全部case终态后汇总；QA未终态仍占窗口 | [services/execution.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/execution.py)<br>[runtime/executor.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/runtime/executor.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；真实隔离进程/SQLite重启、持久计次、成功项不重复、未知响应累计3次、QA窗口、取消迟到与下游作废已验证；TASK-02274真实调用沿同一未改实现，未为重验而终止用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F17 | 对象：后台恢复；低频中断；离开继续；重启恢复未完成项，不再调用已完成项 | [services/execution.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/execution.py)<br>[runtime/executor.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/runtime/executor.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；真实隔离进程/SQLite重启、持久计次、成功项不重复、未知响应累计3次、QA窗口、取消迟到与下游作废已验证；TASK-02274真实调用沿同一未改实现，未为重验而终止用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F18 | 对象：取消；评测阶段允许取消、整批作废；QA阶段禁止取消 | [services/execution.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/execution.py)<br>[runtime/executor.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/runtime/executor.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；真实隔离进程/SQLite重启、持久计次、成功项不重复、未知响应累计3次、QA窗口、取消迟到与下游作废已验证；TASK-02274真实调用沿同一未改实现，未为重验而终止用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F19 | 对象：生成触发；普通整批评测完成后自动生成缺失草稿；主／次因均触发；冲突及效果验证排除 | [services/qa_generation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_generation.py)<br>[prompts/standard-question-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/standard-question-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/analysis.json)、[qa-deterministic-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/qa-deterministic-checks.json)<br>固定应生成17项，实际16；ACC-038模型误判冲突未生成预期日志期限QA | **失败**；阻塞；另行授权修复与复测 |
| F20 | 对象：草稿内容与粒度；每缺失点分别生成基于原问题和上下文规范化的标准问，原用户问题单独保留；答案为空；每条附对应片段、按[U04](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/RDD/关键未知项.md#u04)计数≤50字符的分类reason和来源case | [services/qa_generation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_generation.py)<br>[prompts/standard-question-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/standard-question-v2.md) | [human-qa-review.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/human-qa-review.json)、[qa-deterministic-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/qa-deterministic-checks.json)<br>固定应生成17份；16实际草稿标准问及reason获本人语义认可，漏1项计不合格，16/17达到至少16份。实际来源复用、连续定位、长度及空答案检查通过。漏生成F19失败保留。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F21 | 对象：QA失败与评测结果独立；最多3次，成功即停；终态失败单列；评测结果不变；全部生成项终态释放窗口 | [services/qa_generation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_generation.py)<br>[prompts/standard-question-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/standard-question-v2.md) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[attempt-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/attempt-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；Q三类失败/第三次成功/终态失败与E独立已有真实隔离接口证据；TASK-02216Q均首次成功、初始空答案正常，未增加E或证据生成调用。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F22 | 对象：人工审核；本人补答／编辑并确认；仅必填完整可通过；无需AI审核；不能用留待审核 | [services/qa_review.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_review.py)<br>[models/exports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/exports.py) | [capacity-after-edit.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-edit.json)、[capacity-after-approve.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-approve.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人逐步确认容量补答/审核/导出A/实改回待审/重新审核/再次选择B，A完整快照及CSV字节不变；A/B独立编号、时间及四字段，Chrome下载字节一致。查看、取消、原样保存及拒绝边界引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F23 | 对象：编辑后状态；实际修改保存回待审核，重新通过才可导出；其他对照状态不变 | [services/qa_review.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_review.py)<br>[models/exports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/exports.py) | [capacity-after-edit.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-edit.json)、[capacity-after-approve.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-approve.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人逐步确认容量补答/审核/导出A/实改回待审/重新审核/再次选择B，A完整快照及CSV字节不变；A/B独立编号、时间及四字段，Chrome下载字节一致。查看、取消、原样保存及拒绝边界引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F24 | 对象：人工选择导出；仅勾选已通过；CSV四字段齐全；分类固定知识缺失；允许重复导出 | [services/qa_review.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_review.py)<br>[models/exports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/exports.py) | [capacity-after-edit.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-edit.json)、[capacity-after-approve.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-approve.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人逐步确认容量补答/审核/导出A/实改回待审/重新审核/再次选择B，A完整快照及CSV字节不变；A/B独立编号、时间及四字段，Chrome下载字节一致。查看、取消、原样保存及拒绝边界引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F25 | 对象：人工补充确认；本人外部编辑CSV上传，勾选已通过且已导出且实际加入的具体版本；每次一个原批次 | [services/supplements.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/supplements.py)<br>[models/supplements.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/supplements.py) | [knowledge-new-capacity-B-preparation.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/knowledge-new-capacity-B-preparation.json)、[knowledge-upload-observed.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/knowledge-upload-observed.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人选B容量20GB，外部新版CSV仅新增1行、已上传并本人确认实际采用。补充记录只关联B历史条目，来源去重集合仅ACC-011；新库→B→QA→case→原批次→原规则/旧库完整可读。拒绝边界和无来源引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F26 | 对象：效果验证范围；只关联本次来源case去重；补一条即可；无来源不创建，显示无可验证案例 | [services/supplements.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/supplements.py)<br>[models/supplements.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/supplements.py) | [knowledge-new-capacity-B-preparation.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/knowledge-new-capacity-B-preparation.json)、[knowledge-upload-observed.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/knowledge-upload-observed.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人选B容量20GB，外部新版CSV仅新增1行、已上传并本人确认实际采用。补充记录只关联B历史条目，来源去重集合仅ACC-011；新库→B→QA→case→原批次→原规则/旧库完整可读。拒绝边界和无来源引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F27 | 对象：旧新生成与评测；旧新均重新生成；相同模型提示词支持参数及原上下文；只替换当前回复；生成及评测各最多3次 | [services/effects.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/effects.py)<br>[prompts/customer-reply-v4.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/customer-reply-v4.md) | [call-scope.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/call-scope.json)、[final-detail.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/final-detail.json)<br>仅ACC-011旧新各重新生成并分别评测，共4次首次成功。G两侧除KB之外输入相同，G/E同类型配置及原上下文相同，各自E替换目标为各自新生成回复；两侧结果、配置、请求响应和指标完整保存、可比较，无QA。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F28 | 对象：抽样与补抽；抽ceil(N×10%)，不重复；失败随机补抽成功且未抽项；足数后人工标记 | [services/sampling.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/sampling.py)<br>[domain/sampling.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/sampling.py) | [sampling.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/sampling.json)、[accuracy-human-confirmation.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/accuracy-human-confirmation.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；TASK-022N1/K1、初抽唯一且可比较，三维本人逐项改善/持平/改善后结论passed；新回复仍Badcase，结论独立。补抽/不足/变差及U08一次1000轮统计81～121引用020，不重抽挑结果。刷新后读取保持，未在TASK-022再重启用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F29 | 对象：人工验证结果；无变差通过；任一维度变差整次不通过；未完待确认；不足验证失败；新Badcase仍可比较 | [services/sampling.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/sampling.py)<br>[domain/sampling.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/sampling.py) | [sampling.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/sampling.json)、[accuracy-human-confirmation.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/accuracy-human-confirmation.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；TASK-022N1/K1、初抽唯一且可比较，三维本人逐项改善/持平/改善后结论passed；新回复仍Badcase，结论独立。补抽/不足/变差及U08一次1000轮统计81～121引用020，不重抽挑结果。刷新后读取保持，未在TASK-022再重启用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F30 | 对象：首版范围；电脑浏览器统一流程；由本人录制视频向他人展示项目，工作台无需录屏或视频导出功能；仅模拟CSV与真实模型调用；手动补知识库 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [baseline.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/baseline.json)、[final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)<br>TASK-022仅模拟CSV、单机工作台及真实模型调用；本人逐项审核、实际采用及效果判断。Chrome154.0.8037.98；无真实客服/知识库连接、外部自动补库或新增产品功能，92产品/Prompt文件哈希不变。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F31 | 对象：性能与并行；同任务模型请求最多3个、单批执行；按数据地图「性能实测约定」记录3批完整自动阶段耗时及实测条件 | [services/execution.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/execution.py)<br>[runtime/executor.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/runtime/executor.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[performance-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/performance-report.md)、[threshold-decision.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task023-v1/threshold-decision.json)<br>020/022的并发、进度和Windows Chrome页面证据保持有效；023原三批客户端217.110/247.165/241.766秒，均≤本人确认360秒。只适用于原机器、配置、相近短输入及约20QA，不扩大为任意100条保证。 | **通过**；已取证范围通过；版本变化须评估复核 |
| F32 | 对象：数据指令隔离独立测试；按原评分依据执行，将评分暗示视为数据；用已固定的预期判定核对 | [services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py)<br>[domain/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/evaluation.py)<br>[prompts/evaluation-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/evaluation-v2.md) | [analysis.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/F32-real/analysis.json)<br>独立固定成对输入，实际2次均准确性1、敷衍Badcase、无QA；不要求两侧意图/服务数值相等 | **通过**；已取证范围通过；版本变化须评估复核 |
| D01 | 对象：保存及上下文组装；四字段保存一致；用户问题已在记录中，仅追加当前回复，待评回复最后 | [domain/csv_import.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/csv_import.py)<br>[services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py) | [trace-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/trace-checks.json)、[database-snapshot.sqlite3](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/database-snapshot.sqlite3)<br>50实际E请求与原history/target_reply及完整两份冻结资料一致；版本、原始响应及恢复计次保存在trace/SQLite，状态历史专项引用020 | **通过**；已取证范围通过；版本变化须评估复核 |
| D02 | 对象：版本保存；版本内容及时间保存；原批次继续可读取V1；有效性本人确认 | [models/imports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/imports.py)<br>[services/execution.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/execution.py) | [trace-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/trace-checks.json)、[database-snapshot.sqlite3](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/database-snapshot.sqlite3)<br>50实际E请求与原history/target_reply及完整两份冻结资料一致；版本、原始响应及恢复计次保存在trace/SQLite，状态历史专项引用020 | **通过**；已取证范围通过；版本变化须评估复核 |
| D03 | 对象：最终结果计数；保存最终分数分类或异常类型、次数；每case一次统计 | [model_client/deepseek.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/model_client/deepseek.py)<br>[services/model_results.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/model_results.py) | [trace-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/trace-checks.json)、[database-snapshot.sqlite3](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/database-snapshot.sqlite3)<br>50实际E请求与原history/target_reply及完整两份冻结资料一致；版本、原始响应及恢复计次保存在trace/SQLite，状态历史专项引用020 | **通过**；已取证范围通过；版本变化须评估复核 |
| D04 | 对象：进度持久化与取消作废；进度及结果重启可读取；取消数据不可参与任何下游，仅取消记录保留 | [services/execution.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/execution.py)<br>[runtime/executor.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/runtime/executor.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[verification-summary.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task020-v1/verification-summary.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；真实隔离进程/SQLite重启、持久计次、成功项不重复、未知响应累计3次、QA窗口、取消迟到与下游作废已验证；TASK-02274真实调用沿同一未改实现，未为重验而终止用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| D05 | 对象：QA来源关联；每草稿关联准确case并直接复用评测保存的该缺失点片段reason，答案保存人工内容 | [services/qa_generation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_generation.py)<br>[prompts/standard-question-v2.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/standard-question-v2.md) | [human-qa-review.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/human-qa-review.json)、[qa-deterministic-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/qa-deterministic-checks.json)<br>固定应生成17份；16实际草稿标准问及reason获本人语义认可，漏1项计不合格，16/17达到至少16份。实际来源复用、连续定位、长度及空答案检查通过。漏生成F19失败保留。 | **通过**；已取证范围通过；版本变化须评估复核 |
| D06 | 对象：不可变导出内容；每次保存编号、时间、QA标识及四字段；A不随后续修改变化；各次历史快照独立保存并可追溯 | [services/qa_review.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/qa_review.py)<br>[models/exports.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/exports.py) | [capacity-after-edit.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-edit.json)、[capacity-after-approve.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-approve.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人逐步确认容量补答/审核/导出A/实改回待审/重新审核/再次选择B，A完整快照及CSV字节不变；A/B独立编号、时间及四字段，Chrome下载字节一致。查看、取消、原样保存及拒绝边界引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| D07 | 对象：端到端追溯；关联新版本→导出快照→QA→来源case→原批次→原规则与旧库；验证case去重 | [services/supplements.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/supplements.py)<br>[models/supplements.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/models/supplements.py) | [knowledge-new-capacity-B-preparation.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/knowledge-new-capacity-B-preparation.json)、[knowledge-upload-observed.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/knowledge-upload-observed.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；本人选B容量20GB，外部新版CSV仅新增1行、已上传并本人确认实际采用。补充记录只关联B历史条目，来源去重集合仅ACC-011；新库→B→QA→case→原批次→原规则/旧库完整可读。拒绝边界和无来源引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| D08 | 对象：两侧数据；保存两侧模型配置、提示词、支持参数、回复、评分、共同规则及上下文 | [services/effects.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/effects.py)<br>[prompts/customer-reply-v4.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/prompts/customer-reply-v4.md) | [call-scope.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/call-scope.json)、[final-detail.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/final-detail.json)<br>仅ACC-011旧新各重新生成并分别评测，共4次首次成功。G两侧除KB之外输入相同，G/E同类型配置及原上下文相同，各自E替换目标为各自新生成回复；两侧结果、配置、请求响应和指标完整保存、可比较，无QA。 | **通过**；已取证范围通过；版本变化须评估复核 |
| D09 | 对象：抽检轨迹；保留目标数、抽中失败项原因、补抽及各维人工标记、最终结论 | [services/sampling.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/sampling.py)<br>[domain/sampling.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/domain/sampling.py) | [sampling.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/sampling.json)、[accuracy-human-confirmation.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/accuracy-human-confirmation.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；TASK-022N1/K1、初抽唯一且可比较，三维本人逐项改善/持平/改善后结论passed；新回复仍Badcase，结论独立。补抽/不足/变差及U08一次1000轮统计81～121引用020，不重抽挑结果。刷新后读取保持，未在TASK-022再重启用户后端。 | **通过**；已取证范围通过；版本变化须评估复核 |
| D10 | 对象：验收集固定及分类覆盖；50条：会员20、额度积分/API/交易各10；合格Badcase各半；25主因9/5/4/4/3；缺失7兜底2编造；保留边界标签 | [docs/04_validation/evidence/task021-acceptance-v1/freeze-manifest.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task021-acceptance-v1/freeze-manifest.json)<br>[services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py) | [baseline.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/baseline.json)、[trace-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/trace-checks.json)<br>50正式预期逐条固定+D11本人声明；58冻结文件未变；实际50E输入只含通用rubric和业务资料，无本条人工标签 | **通过**；已取证范围通过；版本变化须评估复核 |
| D11 | 对象：输入及保存范围；仅模拟数据；人工核对无真实个人信息、密码或密钥 | [docs/04_validation/evidence/task021-acceptance-v1/freeze-manifest.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task021-acceptance-v1/freeze-manifest.json)<br>[services/evaluation.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/evaluation.py) | [baseline.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/baseline.json)、[trace-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/trace-checks.json)<br>50正式预期逐条固定+D11本人声明；58冻结文件未变；实际50E输入只含通用rubric和业务资料，无本条人工标签 | **通过**；已取证范围通过；版本变化须评估复核 |
| P01 | 对象：结果明细；显示真实原问题回复上下文、三分理由综合分；Badcase主次因；评测阶段已保存的知识缺失片段reason | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)、[case-011.png](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/case-011.png)<br>TASK-022Chrome53检查核对50列表评分/判定及011完整依据；效果页面展开核对原问题/上下文、两侧回复、评分理由、主次因、知识缺失及定位入口；长度与来源规则引用原始检查和020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| P02 | 对象：指标、预警与跳转；显示三指标；预警带指标名实值阈值；两条分开展示；分别跳Badcase／异常明细 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)、[running-batch.png](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/running-batch.png)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；020真实Chrome覆盖双预警准确跳转、零成功/运行/取消/QA失败/不可比/G失败；TASK-022真实普通指标50.00%/3.88/0.00%及质量预警与持久结果一致，运行无提前结论。没有将020替身状态说成真实模型语义。 | **通过**；已取证范围通过；版本变化须评估复核 |
| P03 | 对象：无数据、失败与运行状态；无成功通过率平均分无数据；异常100%；运行显示进度；QA失败单列；取消显示已取消 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [final-browser-checks.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/final-browser-checks.json)、[running-batch.png](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/browser/running-batch.png)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；020真实Chrome覆盖双预警准确跳转、零成功/运行/取消/QA失败/不可比/G失败；TASK-022真实普通指标50.00%/3.88/0.00%及质量预警与持久结果一致，运行无提前结论。没有将020替身状态说成真实模型语义。 | **通过**；已取证范围通过；版本变化须评估复核 |
| P04 | 对象：审核及导出界面；附所需原文证据；两审核状态，无驳回；展示导出时间答案供选版；未通过不可选导出 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [capacity-after-edit.png](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-edit.png)、[capacity-after-approve.png](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/manual-flow/capacity-after-approve.png)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；容量QA页面待审核→通过→实改待审→重新通过均与读回一致；A/B历史答案可区分，选择各仅1条且实际CSV一致；历史快照资格边界引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| P05 | 对象：对比展示；三指标及三维分、主次因变化；新回复合格状态与人工验证结论分开；失败显示真实状态 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [final-detail.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/final-detail.json)、[sampling-after-service.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/sampling-after-service.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；TASK-022实际效果页面显示旧0.00%/3.67/0.00%、新0.00%/4.00/0.00%；新Badcase与人工通过分别展示。刷新后三维改善/持平/改善保持，模型辅助说明存在，人工确认真实保存。部分失败/不足场景引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| P06 | 对象：责任说明；简短说明模型辅助判断，QA及验证最终由本人确认 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [final-detail.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/final-detail.json)、[sampling-after-service.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task022-v1/effect-real/sampling-after-service.json)<br>引用TASK-020独立已测确定性证据，未重跑或重复计数；TASK-022实际效果页面显示旧0.00%/3.67/0.00%、新0.00%/4.00/0.00%；新Badcase与人工通过分别展示。刷新后三维改善/持平/改善保持，模型辅助说明存在，人工确认真实保存。部分失败/不足场景引用020。 | **通过**；已取证范围通过；版本变化须评估复核 |
| P07 | 对象：信息密度、浏览器与耗时展示；统一流程、无需访客账号；展示进度并记录实际耗时 | [pages.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/pages.tsx)<br>[components.tsx](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/frontend/src/components.tsx)<br>[services/workbench.py](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/backend/app/services/workbench.py) | [deterministic-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)、[performance-report.md](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/performance-report.md)、[threshold-decision.json](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task023-v1/threshold-decision.json)<br>020/022的并发、进度和Windows Chrome页面证据保持有效；023原三批客户端217.110/247.165/241.766秒，均≤本人确认360秒。只适用于原机器、配置、相近短输入及约20QA，不扩大为任意100条保证。 | **通过**；已取证范围通过；版本变化须评估复核 |

统计：F层28通过、4失败；D层11通过；P层7通过；合计46通过、4失败、0待确认、0未运行、0待核实（指50项的当前主状态）。子范围限制及非阻塞待核实内容另列，不能据此宣布完整产品通过。F31/P07由023补全性能证据；022当时的两项待确认不回写历史快照。

## 5. 发现、严重度、影响及承接

### FR-01 三维评分必要阈值未满足（高，阻塞）

证据：product-acceptance-report.md第3章/F06（行36～37、69、118）；task022-v1/analysis.json及数据库最终快照；本次independent-metrics.json逐条比较。准确性45/50、意图32/50、服务35/50，后两维失败。

影响：不能称评分符合正式业务要求，不能最终交付通过。未推定所有差异来自单一Prompt问题。建议另行授权后用独立调试资料定位评分口径及实现承接；修复后保留版本和原失败，按受影响范围重新正式验收。若改评分Prompt，正式50条各项结果都可能受影响，应另行申请该范围重验，不用正式集优化Prompt，不改标签或阈值。当前承接：待另行授权修复/复测，未开始。

### FR-02 缺失点与资料冲突误判导致漏QA（高，阻塞）

证据：product-acceptance-report.md第4章及F09/F11/F19（行46、72、74、82、119）；冻结ACC-038/049预期；原请求/响应、最终SQLite与本次逐case差异。ACC-038把不相关资料的60/90天扩展成当前问题的冲突，没有识别诊断日志保留时长缺失；ACC-049单纯冲突主因应“其他/证据不足”，实际“合规”。

影响：F09/F11/F19失败；实际16QA不足以证明完整17项都生成。F08整体主因比例与F20质量比例通过不关闭本发现。建议分别定位答案适用范围、冲突证据和主因优先级；使用独立变体调试，经授权修订后复测受影响评分/归因、完整17项QA集合及禁止生成组合。原DBG-06漏识别继续保留，不以本次审查或明确变体通过关闭。当前未修复。

### FR-03 已确认意图评分补充决定的承接未闭合（中，修复前阻塞）

证据：acceptance-fixture-manifest.md行496及各条已确认标签；behavior-spec.md评分档位表；backend/app/prompts/evaluation-v2.md通用档位。本人已确认“资料有答案但未识别提炼该条，意图1；理解了问题但回答错误，不自动给意图1”。该补充记录存在，但旧Spec/Prompt未明确同步专门判法；022也披露承接差异。

影响：固定业务预期与实现指导之间存在一致性缺口，妨碍可重复修复。不据此断言已找出FR-01全部根因。本次不要求本人重复决定已确认口径。建议另行授权后把既有决定同步到适用源文档并审查影响，再用独立资料调试，保留正式固定预期。当前只记录建议，不修改Spec或Prompt。

### FR-04 知识库内部多文档冲突缺少独立样本（中，覆盖限制，非独立新增门槛）

证据：acceptance-fixture-manifest.md行497，正式4条冲突均为规则与知识库之间。已确认50条不包含知识库内部多文档互相冲突的独立样本。

影响：不能声称该子场景已获独立真实模型验证；现有F11失败结论已足以阻塞。本次不擅自扩充正式50条，也不自动新增业务规则。是否补充独立专项验证及其授权，留本人后续决定；无证据范围标为待核实，不用已有冲突案例代替。

### FR-05 历史状态及附件元数据易误读（低，非阻塞）

证据：AGENTS.md第5章和早期检查点、PROJECT_CONTEXT.md前部、TASK-024卡历史“待分发”，与各自最新追加记录不同；021 labels/expectations.json顶层仍含draft/逐条待确认，但50条个体approved、confirmations及freeze-manifest已冻结；023 threshold-decision.json中的report_approved=false是阈值确认时快照，后续approval-results明确整报告认可。

影响：读者可能把历史门禁与当前状态混淆。本次以具体确认记录、冻结哈希和最终认可文件为准，未把这些元数据解释为缺少前置。建议另行授权整理入口索引和历史标记；不改冻结文件，不覆盖原始决定快照。仅在任务/项目文档追加024本次真实状态。

### FR-06 既有运行与维护限制（低，已披露，非阻塞）

证据：TASK-008认可及模块说明，019/020/022报告，frontend/README.md与现有工程。失败导入没有已约定永久留痕/保留期；规则/知识库条数和文件字节上限未定义，用户已接受对008的影响，不能说无限容量已测试。Windows同pytest进程混合TestClient与子进程重开SQLite存在差异，既有独立进程证据有效，但该环境根因未完全定位；依赖弃用提示保留。

影响：超出已测资料规模可能出现内存或等待问题；维护时继续隔离进程验证。单人单机、一个backend worker、共享单任务无排队；不能拓展成多用户或生产部署承诺。模型别名未来变化仍须按追溯信息核对。建议仅在另获授权时评估限制；本次不新增设计或依赖。

## 6. 一致性、人工边界与未知项

原业务链与当前模块、前端入口相互承接。009是唯一调度与持久计次来源；010单次调用及结构校验，不叠加SDK重试；011评分和证据、012指标、013按点QA、014人工审核和快照、015实际补充、016两侧生成评测、017抽检结论、018页面。UI读取后端派生规则，没有在前端另设评分阈值。未发现有证据的新增多租户、外部通知、自动补库或自动审核范围。此判断限实际文件及证据审查，不是穷尽安全/生产审计。

```text
CSV模拟输入 -> 原子导入/资料版本 -> E评分分类 -> 指标/预警
                                      |
                         符合资格的知识缺失点
                                      v
                                  Q标准问草稿
                                      |
                          [本人补答 + 明确审核]
                                      v
                            人工选择导出 -> 历史快照
                                      |
                        [本人外部补库 + 上传 + 实际确认]
                                      v
                        精确来源case -> 旧/新各G再E
                                      |
                            固定抽检 -> [本人三维判断]

阻塞：意图/服务评分未达阈值；缺失/冲突误判 -> 漏QA
性能三批通过不会解除上述阻塞。
```

| U项 | 当前决定及验证状态 |
|---|---|
| U01 | 中文固定表头/顺序、UTF-8 BOM两种、CSV还原、整份拒绝规则已确认；020/022确定性证据有效。文件字节等未约定上限不自行补定。 |
| U02 | 五类主因、次因及冲突/合规组合已确认；实际F09/F11失败保留，决定明确不等于模型执行正确。 |
| U03 | 缺失证据、同一最多3次预算及QA复用已确认，结构/事务确定性有证据；真实缺失识别FR-02未通过。 |
| U04 | Unicode码点最多50已确认且本地及实际输出有检查。 |
| U05 | 两位展示、未舍入值比较已确认，独立边界验证有效。 |
| U06 | 恢复、未知提交持久计次、整批取消与迟到丢弃已确认；020真实进程和数据库、受控故障注入证据有效，不是供应商故障语义证明。 |
| U07 | 正式全部17应生成分母，最低16；16语义合格，漏1计不合格；F20通过而F19失败。 |
| U08 | 1000轮统计规则已确认；020独立原始81～121，本次重算一致。 |
| U09 | Windows Chrome范围已确认；实际页面记录Chrome154.0.8037.98，不声称本轮重新执行浏览器验收或支持其他浏览器。 |
| U10 | 6分钟阈值本人已确认，决定项关闭；023有效三批逐批通过，适用条件不扩大。 |
| U11 | 单人模拟业务及会员等范围已确认，不变成真实生产资料接入。 |
| U12技术契约 | DeepSeek官方API、型号/配置、固定JSON及各任务协议已认可；现有真实运行及结构证据存在。 |
| U12实际样本/预期 | 021正式50条逐条确认及58项冻结完成；17项QA集合固定。样本事项完成不能关闭F06/F09/F11/F19业务失败。 |
| U13 | 历史已通过快照资格、多选具体采用版本、来源case去重已确认；编辑不覆盖旧快照，020及022实际A/B与补充链有证据。 |

未新增未知项决定。已有人工标注、QA答案审核、实际采用知识及效果判断仍由本人完成。模拟测试人工标签仅证明状态规则。022实际所选效果抽检本人标记“改善/持平/改善”，效果通过；新回复仍为Badcase，两结论独立，不能扩展成全部知识库补充有效。

## 7. 真实可演示范围与启动

可演示已有真实模型和持久结果：三类导入及版本、50条批次列表、指标/两预警、完整case评分依据与缺失证据、16QA、已认可的单份人工补答审核/编辑回待审/再审核、A/B不可变导出、实际新知识库与快照关联、旧新两侧新生成和分别评测、抽检及本人效果结论、023三个独立100条批次。须同时展示失败说明，不把失败案例包装成已修复。

普通正式批次：0ba4b869-02e0-47f3-9ed5-d2ae01333532。效果任务：f26b9275-1d30-43a5-9f35-8da9b651eb4c。补充记录：d895853d-f7fb-4c27-ab1c-b066f3fc041d。仅选用这些实际记录，不在演示中启动新调用。021人工预期文件不能作为模型输入。实际人工授权后部分动作通过真实API执行，页面另有读取/下载证据；不声称每个业务动作都由浏览器点击完成。

运行环境沿用证据：Windows 11家庭版中文版10.0.26300；i5-1155G7，4核8逻辑处理器，内存15.79GiB；Python3.13.16，OpenAI2.54.0，httpx0.28.1，SQLAlchemy2.0.54，FastAPI0.142.2，Uvicorn0.54.0。Chrome验收版本154.0.8037.98。实际依赖锁及本轮环境读取见environment-check.json。本轮只读/api/v1/workbench返回200，6任务均completed、共享窗口空闲、runtime_error为空。首次探测未定义路径返回404，读取实际路由后核对成功，不是后端故障。端口被已有用户后端占用时直接访问，勿重复启动或停止用户进程。

只浏览已保存记录可不配置模型密钥。后端启动会恢复未终态任务，因此启动前应确认目标运行库没有未完任务；本轮未启动服务、未执行恢复。使用既有backend虚拟环境及已构建frontend/dist：

```powershell
Set-Location 'D:\HuaweiMoveData\Users\15308\Documents\ChatGPT\AI评测自迭代工作台'
$env:WORKBENCH_DATA_DIR = (Resolve-Path './docs/04_validation/evidence/task022-v1/database').Path
Set-Location './backend'
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

访问http://127.0.0.1:8000/#/batches；资料/#/materials；QA/#/qa；历史导出/#/exports；效果/#/effects/f26b9275-1d30-43a5-9f35-8da9b651eb4c。查看原结果无需真实API。未来若获新调用授权，可用原task022-start-backend.ps1安全输入密钥到当前进程环境；本任务不运行该脚本，也不索取/打印密钥。

受控取消、重启、故障、零成功及失败补抽采用020真实本地进程/数据库加测试模型替身证据；不是DeepSeek真实故障实验，不应放入正式页面冒充真实语义输出。演示可引用这些原日志/截图，不在本任务制造新故障。

不可展示为已通过：三维评分全部达标、完整17QA已生成、知识库内部冲突已专项验证、原DBG-06已修复、任意100条6分钟完成、全部补库有效、生产/多租户能力。未实现且不在范围：线上客服连接、自动补库、外部预警通知、评分人工编辑、额外AI审核、手动重试、录屏及独立产品报告导出。本人可外部录视频，视频不是唯一验收证据。

## 8. 最终结论、后续与确认

审查结论：**不通过，有阻塞**。022/023真实产物和认可证据齐全；决定不通过的原因是必要业务验收失败，不是报告缺失。性能补齐后50项46通过4失败。无“有条件通过”，不以本人认可报告替代修复、复测或最终交付认可。

TASK-024执行状态：**已完成，报告已获用户认可**。整产品状态：**最终交付审查不通过，最终交付未认可**。无产品/Prompt/需求修改，无真实API新增调用，无部署推送发布，无额外任务启动。

尚未完成的产品事项：FR-01评分、FR-02冲突/缺失/漏QA及FR-03承接一致性的修订和有效复测；FR-04覆盖补充是否安排由本人另行决定；FR-05/06为已披露非阻塞建议/限制。当前没有获得修复或验收重跑授权。涉及Prompt版本变化必须评估所有受影响语义项；涉及耗时/配置变化再评估最小性能补测，另获授权，不自动重跑三批。

用户确认记录：2026-10-10，用户回复“确认”，认可本报告及保留的失败、限制和待处理事项。最终交付未获认可。报告认可不豁免必要验收失败，不授权修复、验收重跑、部署或发布。

## 9. 证据索引与交付自证

- [审查输入/当前产品SHA基线](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/baseline.json)
- [历史附件完整文件索引/SHA](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/evidence-index.json)
- [全部50条完整要求/实现/证据/状态](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/acceptance-matrix.json)
- [SQLite独立复算及50条差异](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/independent-metrics.json)
- [1433项证据核验明细](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/audit-results.json)
- [实际核验命令输出](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/audit-run.log)
- [本轮依赖/进程/只读可达性](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/environment-check.json)
- [最终文档/保护文件/状态检查](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/evidence/task024-v1/final-check.json)
- [020确定性报告](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/deterministic-report.md)
- [021冻结清单](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/acceptance-fixture-manifest.md)
- [022实际业务呈现报告](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/product-acceptance-report.md)
- [023三批性能报告](D:/HuaweiMoveData/Users/15308/Documents/ChatGPT/AI评测自迭代工作台/docs/04_validation/performance-report.md)

档位S3；已读取using-vibe-delivery-kit、routing-by-risk、verification-before-completion及package的开始/分级、Review、架构质量、测试策略、交付检查规范；辅助脚本错误按systematic-debugging定位。架构规范仅用于审查现有边界，没有新架构决定。不补Intake/RDD、不新增S4审查：已有基线，本轮没有生产/权限/支付变更。不进行代码实现、TDD或全量产品测试；没有该授权，也无产品版本变化。sequential-thinking/shrimp/code-index未提供，使用明确审查计划、rg和本地只读脚本降级；没有虚构工具调用。所有核验仅本地，不接CI或人工外包，无多agent。


### 2026-10-10 报告认可记录

用户明确回复“确认”。TASK-024报告产物已认可，任务已完成；最终审查“不通过，有阻塞”保持。F06/F09/F11/F19未关闭，46/4统计不变。此确认不是产品最终验收通过或修复授权。本次只更新认可状态，原核验结果与历史验收证据保留。
