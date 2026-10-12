# TASK-024 E-v2最终验收、交付选择及默认版本切换

2026-10-10（Asia/Shanghai）｜Codex｜S2版本切换（承接S3验收）｜状态：本人明确选择E-v2验收与交付，并确认TASK-024按新标准通过。

## 1. 本人明确决定

本人原话：“E-v2作为验收和交付版本，TASK-024按新标准通过，并将默认评分版本切回E-v2”。确认人：本聊天项目用户本人；日期2026-10-10。

此前[rule-review-v3报告](final-review-rules-v3.md)以原E-v2及本人已确认的新标准，复审50项在原取证范围满足。该报告中的“最终认可待定/版本选择待定”属于本次决定之前状态，本记录为最新明确交付选择，不覆盖原报告内容或原失败证据。

**TASK-024按已确认新标准通过。验收与交付版本固定为evaluation-v2、standard-question-v2、customer-reply-v4，沿原deepseek-flash及参数、单机模拟业务和原性能条件。** 不把E-v3未验证作为这个已选版本的交付阻塞，也不宣称E-v3通过。

## 2. 实际切换

| 文件 | 实际变化 |
|---|---|
| backend/app/model_client/deepseek.py | 默认evaluation-v3→evaluation-v2；历史许可继续包含E-v1/v2/v3，Q/G及参数不变 |
| backend/app/prompts/manifest.json | 指向原evaluation-v2.md及实际SHA256；记本人交付决定，加载器不改 |
| backend/tests/test_task019_prompt_versions.py | 当前默认断言切回v2；增加默认注册/加载器版本一致与全文原字节解码一致检查；历史v3恢复验证保持 |
| backend/tests/test_evaluation.py | 3处当前版本预期切回v2，业务判断断言不改 |
| backend/tests/test_effects.py | 效果评测当前E配置追溯预期切回v2，G-v4保持 |

原E-v2 SHA256：`4a51fc8a1a265095612fdee3457be10105b0223f48e39ff028ebf8bd0a1dfbb6`。E-v2正文未改，E-v3正文和原候选历史材料保留。没有按ACC编号改分、修改保存结果、数据库迁移、业务调度或模型参数。

新任务EvaluationBuilder在构造时使用manifest加载E；普通与效果配置绑定由本地集成覆盖。历史任务按已持久化Prompt全文和版本恢复，不把旧任务快照重写为v2。新进程的默认注册和加载器均v2；本轮没有探测、启动或重启已运行服务，不宣称在内存中的任意旧进程已重载全部模块。当前源码的PROMPTS历史集合继续包含三个E版本，避免因切默认拒绝旧v3快照。

## 3. 验收范围与已接受限制

F06三维区间一致50/47/47，各≥45；F09固定18缺失点识别17，≥ceil(18×90%)；F11真实冲突4/4、无冲突45/46，两组各≥90%，049禁止/允许直接冲突归违规符合；F19固定17应生成点覆盖16，≥ceil(17×90%)，16正确保存有资格点都交接且没有非预期草稿。其余项目沿原已取证范围，完整矩阵和来源见rule-review-v3附件。

038误冲突、漏缺失点/漏QA仍是实际错误，按已确认比例计错并接受；同区间精确分差保留；没有将规则容差记录为原缺陷已修复。F11只有4条真冲突样本，不外推广泛泛化。QA仍本人补答审核；模型容差不等于系统可漏调度或违背保存冲突禁QA。

原023的6分钟逐批判法与三批证据仍只覆盖原机器、E-v2、相近短输入、小资料及约20QA。E-v2/参数/正文未变，本轮只是切回选择入口，不新增真实模型或性能运行。原DBG-06、知识库内部冲突专项等原披露及非阻塞覆盖限制保持，未新增必要验收分母。

## 4. FIX/FR处置

FIX-001文档子项原已关闭。原FR-01/FR-02在E-v2新标准下已满足，不再作为本次交付必要阻塞；原因是本人规则调整及限制接受，不是候选修复验证通过。

FIX-002/003的E-v3候选及其未完成真实验证不纳入本次交付，不再为本次TASK-024继续执行候选调试。记录为“本轮交付采用E-v2，候选保留/不交付”，不标候选本地语义/正式复验通过，不删除原受拒动作与失败。FR-03精确意图1指导仍是原指导，E-v2未因此被证明符合每个精确值；按新F06容错和本人交付选择接受其当前能力，不额外要求v3作为交付前置。

后续若再选择E-v3、修复DBG-06或扩展业务，另说明范围和取证计划。本次没有授权部署推送、删除候选、重试受拒启动动作或新增模型补验，不自动启动这些操作。

## 5. 验证与规范

使用using-vibe-delivery-kit、routing-by-risk、verification-before-completion及既有测试/Review/最终交付规范。S2小范围默认配置变更；本决定和本记录构成等效任务范围，沿原Spec及已确认规则，无新行为档位。跳过新RDD/架构/S4实施、CI、真实模型与服务启动：无新接口、依赖、数据结构或生产资金操作，且本地现有集成足以验证版本选择；不启多agent。

命令（项目根PowerShell设置PYTHONPATH=backend）：

```powershell
& ./backend/.venv/Scripts/python.exe -X utf8 -m pytest backend/tests/test_task019_prompt_versions.py backend/tests/test_evaluation.py backend/tests/test_evaluation_integration.py backend/tests/test_effects.py backend/tests/test_model_client.py -q --junitxml=.codex/e2-delivery-tests.xml
```

最终代码225项通过，0失败/错误/跳过，19.55秒。覆盖默认版本/原全文、E-v1/v2/v3历史SDK许可、普通任务组装/保存/派生/集成、效果绑定及单次模型客户端边界；使用本地替身和SQLite，不发送真实API。首轮225通过后补强原全文断言，再完整重跑同一225项，统计不重复相加。XML和日志保存在项目`.codex/e2-delivery-tests.xml`及`.codex/e2-delivery-tests.log`。

1266份非允许改动的原产品/前端/迁移/冻结/历史证据SHA不变；允许产品改动仅默认注册和manifest两份，3份测试仅版本断言及绑定核对。真实文本diff：`.codex/e2-delivery-code.diff`；前置基线`.codex/e2-delivery-before.json`；最终核验`.codex/e2-delivery-verification.json`。没有用未跟踪文件的空Git diff作为唯一依据。

已同步AGENTS/PROJECT_CONTEXT、TASK-024卡、任务总表/依赖图、修复总表及002/003卡和分项状态。最终选择与通过由本人明确决定，不再重复请求同一认可。
