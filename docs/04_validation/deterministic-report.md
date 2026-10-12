# TASK-020 确定性规则与恢复端到端验证报告

执行：2026-10-08～09（Asia/Shanghai）｜交付：2026-10-09｜执行者：Codex｜版本：1.0确认稿

状态：报告交付完成，报告及未运行说明已获用户认可；F32真实复核等未运行事项保持开放。没有判产品最终验收通过。TASK-021～024未启动。

## 1. 范围、前置及结论

本次仅执行TASK-020。TASK-018页面真实产物及认可见 `.codex/task018-approval-results.json`；TASK-019确认稿v3与认可见 `evidence/task019-debug-v1/approval-results.json`。001～007及相关008～019实际模块、验证方案与最新RDD已核对。历史卡中的“仅编卡、未授权”不覆盖此次明确授权。

115个当前独立测试身份的最新有效结果通过。此数字按测试身份去重，包含参数化用例；浏览器链路计1个pytest身份，内部21项检查另列。不是115条业务验收，也没有把重复复测次数相加。原失败输出全部继续引用，修正测试设施后才复测。92个冻结产品文件SHA256一致，包括backend/app、迁移、frontend/src/dist及Prompt；没有改产品来关闭失败。

本报告不判全部50条验收通过。F32真实模型独立复核未运行；正式语义、人工固定预期与性能分别留021、022、023。新增专项已覆盖QA失败、不可比较、生成失败及新Badcase与人工结论独立；仍不声称任意异常组合或正式呈现验收已完成，见第8章。已测子项通过不能替代未测子项。

## 2. 基线、配置与数据

[baseline.json](evidence/task020-v1/baseline.json)冻结29份输入依据及92个产品文件；[plan.json](evidence/task020-v1/plan.json)记录授权边界。采用006的C01～C08、X恢复矩阵及I交互分工，不重做RDD。最新模型配置和E-v2/Q-v2/G-v4资产从当前实际代码加载，追溯信息保存于各任务执行记录。模拟供应商外壳型号为DeepSeek-V4.1-Flash，指纹TASK020-FP，二者是测试数据，不能表述为真实DeepSeek响应。

环境：Windows、Python3.13、本项目venv的pytest/httpx/SQLAlchemy/OpenAI SDK/Playwright；Chrome154.0.8037.98。实际运行时详情在baseline，浏览器版本在browser-results。每个HTTP用例使用独立随机端口、独立SQLite/WAL目录、单worker正式create_app和正式Executor；仅供应商HTTP适配边界注入受控响应。测试入口`.codex/task020/server.py`不进入正式app.main，不覆盖8000或用户调试库。

全部输入为020原创模拟文本。不是019调试集的重复题，也不是未来正式50条。预期来自最新RDD/003/004/005/006，不从模块测试断言复制。规则测试文件保存固定输入和断言；各隔离目录`inputs/*.csv`保存实际成功导入原字节，`http-records.json`含操作输入和返回，`persistent-snapshot.json`保存请求、任务、QA、关联与抽检结果。失败CSV输入可从测试源码确定性重建；故障策略由control.json保存。人工补答/审核/补库/三维标记全部明确为模拟测试动作，未代替本人确认真实答案或效果。

## 3. 执行方法与实际命令

项目根执行。先在当前PowerShell设置测试导入路径：

```powershell
$env:PYTHONPATH = (Resolve-Path ./backend).Path
```

下表参数前缀统一为 `& ./backend/.venv/Scripts/python.exe -X utf8 -m pytest`，日志通过 `*> 对应.log`保留；每次提供相应`--junitxml=docs/04_validation/evidence/task020-v1/对应.xml`。实际分组执行及失败后的限定复测如下。没有运行CI。

| 参数与用例 | 预期 | 实际与证据 |
|---|---|---|
| `.codex/task020/test_rules.py -q --tb=short` | 独立CSV、结构、公式、QA资格、抽样规则 | 58通过；rules.log/xml |
| `.codex/task020/test_http.py -q --tb=short` | 9项真实HTTP/持久恢复及主链路 | 首轮4通过5失败；http-first.log/xml |
| 同文件 `-k 'csv_atomic or concurrency_cancel or qa_window or partial_qa or review_export'` | 修正测试设施后复测5项 | 3通过2失败；http-harness-retest.log/xml |
| 同文件 `-k 'concurrency_cancel or review_export'` | 取消迟到及快照链路 | 2通过；http-final-retest.log/xml |
| `.codex/task020/test_transactions.py .codex/task020/test_browser.py` | 保存失败回滚及Chrome链路 | 首轮2失败；纠正测试路由和浏览器确认框后2通过；transactions-browser及-retest日志/XML |
| `.codex/task020/test_extra.py` | 空CSV/全部必填、枚举、来源拒绝、效果失败取消、F32数据隔离 | 首轮20通过2测试输入错误；extra.log/xml |
| 同文件 `-k 'five_primary or Q_failure'` | 确认枚举、合规准确性1；Q三异常及第三次成功 | 9通过（其中4项新Q用例）；extra-retest.log/xml |
| `.codex/task020/test_supplemental.py` | 首次/已有资料空CSVHTTP、持久两侧请求独立比对 | 2通过；supplemental.log/xml |
| `.codex/task020/test_browser.py` | 补充状态后完整Chrome链路 | browser-states1通过；最终增加CSV上传/完整依据/辅助说明后browser-final1通过、内部21检查 |
| `.codex/task020/test_sdk_edges.py` | 非法外壳、SDK单次发送/Retry-After、默认300秒及缩短截止清理 | 17通过；sdk-edges.log/xml |
| `.codex/task020/test_browser.py -k failure_and` | QA失败、不可比、G失败、新Badcase与人工持平结论独立 | 首轮测试字段误用result，纠正后1通过、4内部检查；browser-failure-states与-retest日志/XML |
| `.codex/task020 --collect-only -q` | 统计当前测试身份，避免重复相加 | 115 collected；collection.log |

F32真实执行命令：`& ./backend/.venv/Scripts/python.exe -X utf8 .codex/task020/f32_real.py`。预期2次首次调用、最多6次；实际8000不可达，0调用，冻结预期及not-run见第7章。未把替身通过称为真实抗暗示通过。

证据汇总命令：`& ./backend/.venv/Scripts/python.exe -X utf8 .codex/task020-final-evidence.py`。实际115当前身份都有最新通过证据，92产品文件无修改，31个隔离进程数据库保留（含首轮失败），integrity_check均ok。不是29项业务样本。汇总 [verification-summary.json](evidence/task020-v1/verification-summary.json)逐身份指向有效XML，并列出所有原始运行。

## 4. 全50条追溯矩阵

每行前置为本章输入基线、相应真实模块就绪、独立模拟资料与明确测试预期。详细原始输入/预期/通过判据继承最新RDD；[verification-matrix.json](evidence/task020-v1/verification-matrix.json)逐条保存，不新增业务标准。下表“通过”仅限实际已测子项；没有用模块自测替代本次独立结果。

| ID | 独立方法及实际结果 | 状态 | 证据 |
|---|---|---|---|
| F01 | C01 独立CSV编码/表头/必填/100与101；HTTP保存和版本前后比较；三类解析一致；错误整份拒绝；历史重复允许；旧版保持 | 已测确定性子项通过 | rules.xml、extra.xml/extra-retest.xml、supplemental.xml、http-harness-retest.xml |
| F02 | C01 独立CSV编码/表头/必填/100与101；HTTP保存和版本前后比较；三类解析一致；错误整份拒绝；历史重复允许；旧版保持 | 已测确定性子项通过 | rules.xml、extra.xml/extra-retest.xml、supplemental.xml、http-harness-retest.xml |
| F03 | C01 独立CSV编码/表头/必填/100与101；HTTP保存和版本前后比较；三类解析一致；错误整份拒绝；历史重复允许；旧版保持 | 已测确定性子项通过 | rules.xml、extra.xml/extra-retest.xml、supplemental.xml、http-harness-retest.xml |
| F04 | C01 独立CSV编码/表头/必填/100与101；HTTP保存和版本前后比较；三类解析一致；错误整份拒绝；历史重复允许；旧版保持 | 已测确定性子项通过 | rules.xml、extra.xml/extra-retest.xml、supplemental.xml、http-harness-retest.xml |
| F05 | C02/03 固定评分、枚举和结构反例；5/5/3=4.33且Badcase；4/4/4合格；五主因及非法字段校验 | 已测确定性子项通过 | rules.xml、extra-retest.xml |
| F06 | C02 Unicode50/51码点、组合emoji；正式评分单独承接；码点边界已测；各维45/50正式准确率未运行 | 确定性子项通过；正式语义未运行 | rules.xml；TASK-021/022 |
| F07 | C02/03 固定评分、枚举和结构反例；5/5/3=4.33且Badcase；4/4/4合格；五主因及非法字段校验 | 已测确定性子项通过 | rules.xml、extra-retest.xml |
| F08 | 固定50人工预期+真实模型比对；未准备正式50；未判任何一致率 | 后续任务，未运行 | TASK-021/022 |
| F09 | C03/05 固定特殊分类/冲突标志，结构与QA资格检查；禁QA/允许缺失次因等已测；模型事实识别及特殊打分语义不由替身证明 | 确定性子项通过；真实语义未验收 | rules.xml、extra-retest.xml、http-final-retest.xml；TASK-022 |
| F10 | C03/05 固定特殊分类/冲突标志，结构与QA资格检查；禁QA/允许缺失次因等已测；模型事实识别及特殊打分语义不由替身证明 | 确定性子项通过；真实语义未验收 | rules.xml、extra-retest.xml、http-final-retest.xml；TASK-022 |
| F11 | C03/05 固定特殊分类/冲突标志，结构与QA资格检查；禁QA/允许缺失次因等已测；模型事实识别及特殊打分语义不由替身证明 | 确定性子项通过；真实语义未验收 | rules.xml、extra-retest.xml、http-final-retest.xml；TASK-022 |
| F12 | X01 三异常、首次/第三次成功、三次耗尽；真实DB终态守恒；5输入=2成功+3最终异常；13请求；无第4次 | 已测确定性子项通过 | http-first.xml（此用例通过）、provider-calls.jsonl、persistent-snapshot.json |
| F13 | C04 独立整数分子分母、95%/5%边界、舍入及零成功；93.33%/4.00/10.00%；双预警；零成功无数据；原值触发与显示分开 | 已测确定性子项通过 | rules.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json |
| F14 | C04 独立整数分子分母、95%/5%边界、舍入及零成功；93.33%/4.00/10.00%；双预警；零成功无数据；原值触发与显示分开 | 已测确定性子项通过 | rules.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json |
| F15 | C04 独立整数分子分母、95%/5%边界、舍入及零成功；93.33%/4.00/10.00%；双预警；零成功无数据；原值触发与显示分开 | 已测确定性子项通过 | rules.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json |
| F16 | X恢复/取消/QA互斥；单进程真实HTTP、持久计次与硬重启；成功项1次，未保存项恢复2次；累计3次终止；QA保留窗口；取消后在途回复无有效结果 | 已测确定性子项通过 | http-first.xml、http-harness-retest.xml、http-final-retest.xml、extra.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| F17 | X恢复/取消/QA互斥；单进程真实HTTP、持久计次与硬重启；成功项1次，未保存项恢复2次；累计3次终止；QA保留窗口；取消后在途回复无有效结果 | 已测确定性子项通过 | http-first.xml、http-harness-retest.xml、http-final-retest.xml、extra.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| F18 | X恢复/取消/QA互斥；单进程真实HTTP、持久计次与硬重启；成功项1次，未保存项恢复2次；累计3次终止；QA保留窗口；取消后在途回复无有效结果 | 已测确定性子项通过 | http-first.xml、http-harness-retest.xml、http-final-retest.xml、extra.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| F19 | C05 每缺失点独立、禁用条件、直接复用E证据和空答；同case双缺失点2草稿；来源片段/gap/reason逐字段复用；语义90%留正式验收 | 确定性子项通过；QA语义未验收 | rules.xml、http-harness-retest.xml、http-final-retest.xml |
| F20 | C05 每缺失点独立、禁用条件、直接复用E证据和空答；同case双缺失点2草稿；来源片段/gap/reason逐字段复用；语义90%留正式验收 | 确定性子项通过；QA语义未验收 | rules.xml、http-harness-retest.xml、http-final-retest.xml |
| F21 | Q独立三异常耗尽及第三次成功、恢复成功不重复；Q3次封顶；E次数不增；成功和失败单列；Q全终态后释放 | 已测确定性子项通过 | extra-retest.xml、http-harness-retest.xml |
| F22 | C06 模拟人工编辑/审核；选择导出、A/B不可变、事务回滚；空答422；原样状态不变；实改待审；A/B独立；导出内容等于选择；故障无部分快照 | 已测确定性子项通过 | http-final-retest.xml、transactions-browser-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-export.csv |
| F23 | C06 模拟人工编辑/审核；选择导出、A/B不可变、事务回滚；空答422；原样状态不变；实改待审；A/B独立；导出内容等于选择；故障无部分快照 | 已测确定性子项通过 | http-final-retest.xml、transactions-browser-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-export.csv |
| F24 | C06 模拟人工编辑/审核；选择导出、A/B不可变、事务回滚；空答422；原样状态不变；实改待审；A/B独立；导出内容等于选择；故障无部分快照 | 已测确定性子项通过 | http-final-retest.xml、transactions-browser-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-export.csv |
| F25 | C07 历史快照资格、来源拒绝、case去重、实际确认与事务失败；未导出/混批/未确认/空集合拒绝；当前待审仍采用历史A；2QA→1case；失败回滚 | 已测确定性子项通过 | http-final-retest.xml、extra.xml、transactions-browser-retest.xml |
| F26 | C07 历史快照资格、来源拒绝、case去重、实际确认与事务失败；未导出/混批/未确认/空集合拒绝；当前待审仍采用历史A；2QA→1case；失败回滚 | 已测确定性子项通过 | http-final-retest.xml、extra.xml、transactions-browser-retest.xml |
| F27 | C07 两侧重新G/E；固定共同输入、配置、版本，失败/取消/不可比；旧新独立生成；原H及规则一致；仅KB/所生目标变化；缺指纹业务保留但不可比 | 已测确定性子项通过 | effect-input-equivalence.json、http-final-retest.xml、http-first.xml、extra.xml |
| F28 | C08 ceil、补抽、候选不足、持久三维标记、U08一次独立统计；1/5/20/25→1/1/2/3；失败轨迹保留；任一变差不通过；刷新重启保持；U08 81～121 | 已测确定性子项通过 | rules.xml、u08-raw.jsonl、u08-summary.json、http-final-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| F29 | C08 ceil、补抽、候选不足、持久三维标记、U08一次独立统计；1/5/20/25→1/1/2/3；失败轨迹保留；任一变差不通过；刷新重启保持；U08 81～121 | 已测确定性子项通过 | rules.xml、u08-raw.jsonl、u08-summary.json、http-final-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| F30 | I01 Windows Chrome真实后端/DB统一入口模拟链路；Chrome154.0.8037.98；本机模拟；不新增范围/正式产品功能 | 已测确定性子项通过 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json |
| F31 | 真实进程最多3在途请求；性能分工；7待处理，实际在途峰值3；不宣称耗时达标；100条3批留023 | 并发子项通过；性能未运行 | http-final-retest.xml；TASK-023 |
| F32 | 独立成对预期先冻结；数据隔离确定性检查+真实模型独立复核；暗示原样留在target_reply；实际DeepSeek因8000不可达0调用 | 数据隔离通过；真实抗暗示语义未运行 | extra.xml、F32-real/frozen-expectations.json、F32-real/not-run.json |
| D01 | 保存原文、角色/H请求及原批版本；新库独立；CSV附件+请求持久JSON可对照；先前消息不变；原批固定旧规则/旧库 | 已测确定性子项通过 | supplemental.xml、effect-input-equivalence.json、各inputs/与persistent-snapshot.json |
| D02 | 保存原文、角色/H请求及原批版本；新库独立；CSV附件+请求持久JSON可对照；先前消息不变；原批固定旧规则/旧库 | 已测确定性子项通过 | supplemental.xml、effect-input-equivalence.json、各inputs/与persistent-snapshot.json |
| D03 | X01 三异常、首次/第三次成功、三次耗尽；真实DB终态守恒；5输入=2成功+3最终异常；13请求；无第4次 | 已测确定性子项通过 | http-first.xml（此用例通过）、provider-calls.jsonl、persistent-snapshot.json |
| D04 | X恢复/取消/QA互斥；单进程真实HTTP、持久计次与硬重启；成功项1次，未保存项恢复2次；累计3次终止；QA保留窗口；取消后在途回复无有效结果 | 已测确定性子项通过 | http-first.xml、http-harness-retest.xml、http-final-retest.xml、extra.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| D05 | C05 每缺失点独立、禁用条件、直接复用E证据和空答；同case双缺失点2草稿；来源片段/gap/reason逐字段复用；语义90%留正式验收 | 确定性子项通过；QA语义未验收 | rules.xml、http-harness-retest.xml、http-final-retest.xml |
| D06 | C06 模拟人工编辑/审核；选择导出、A/B不可变、事务回滚；空答422；原样状态不变；实改待审；A/B独立；导出内容等于选择；故障无部分快照 | 已测确定性子项通过 | http-final-retest.xml、transactions-browser-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-export.csv |
| D07 | C07 历史快照资格、来源拒绝、case去重、实际确认与事务失败；未导出/混批/未确认/空集合拒绝；当前待审仍采用历史A；2QA→1case；失败回滚 | 已测确定性子项通过 | http-final-retest.xml、extra.xml、transactions-browser-retest.xml |
| D08 | C07 两侧重新G/E；固定共同输入、配置、版本，失败/取消/不可比；旧新独立生成；原H及规则一致；仅KB/所生目标变化；缺指纹业务保留但不可比 | 已测确定性子项通过 | effect-input-equivalence.json、http-final-retest.xml、http-first.xml、extra.xml |
| D09 | C08 ceil、补抽、候选不足、持久三维标记、U08一次独立统计；1/5/20/25→1/1/2/3；失败轨迹保留；任一变差不通过；刷新重启保持；U08 81～121 | 已测确定性子项通过 | rules.xml、u08-raw.jsonl、u08-summary.json、http-final-retest.xml、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| D10 | 正式集配额/人工标注固定及隔离；本次020原创模拟；未建正式50、未用正式反馈调Prompt | 本次隔离符合；正式集合未运行 | baseline.json、.codex/task020/测试输入；TASK-021 |
| D11 | 模拟输入清单与凭据边界；仅020自造文本；无真实客服/知识库连接；未读取保存真实密钥；正式资料仍须本人核对 | 本次模拟范围核对；正式人工核对未运行 | 各inputs/、baseline.json |
| P01 | I02 case完整字段与保存后端比较；完整回复、三分、reason和缺失证据与真实持久结果一致 | 已测确定性子项通过 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/09-case-evidence.png、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json |
| P02 | I02 三指标显示与真实值，双预警关联跳转；三项逐值比较；质量跳同批2Badcase，异常跳同批1异常 | 已测确定性子项通过 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/02-alerts.png、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| P03 | I02/I06 零成功、运行、取消与最终异常；Q失败实际呈现检查；Chrome无数据/100%/运行/取消/Q失败呈现通过；不代表任意异常组合穷尽 | 已测状态通过；正式呈现留022 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/07-zero.png、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/08-cancelled.png、http-harness-retest.xml |
| P04 | I03/04 补答资格、审核、选择导出、编辑及历史内容；缺答不可审核；真实明确确认；选中下载；编辑待审；历史A仍显示并可关联 | 已测确定性子项通过 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/03-approved.png、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/04-history.png、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| P05 | I05 同来源旧新回复与人工结论分开，失败/不可比接口核对；正常对比、失败、不可比及新Badcase与人工通过独立浏览器专项通过 | 已测状态通过；正式呈现留022 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/05-effect.png、http-first.xml、extra.xml |
| P06 | I03/05 模型辅助说明和实际人工操作入口；两页面均有说明；审核及三维模拟人工确认真实提交保存 | 已测确定性子项通过 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/trace.zip |
| P07 | I01 Chrome、摘要与详情、进度持久性；实际性能独立承接；浏览器版本与入口实测；刷新/重启记录保留；U10仍开放 | 呈现子项通过；性能未运行 | test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/06-restored.png、test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/browser-results.json；TASK-023 |

## 5. 恢复、取消、并发及事务证据

- 持久计次在请求发送前完成。因此接口显示running可能早于供应商start日志；测试以真实start屏障校验在途请求。7个待处理最多3个实际在途，另一个提交409且没有排队。
- 强制结束本测试进程，再同库启动。已成功项调用保持1次；发送但未保存的项恢复后累计2次。连续3次发送后强制终止，恢复终态final_failed、attempt_count=3，无第4次。
- 评测取消后放行3个已发送的供应商响应。供应商日志保留3次响应完成；case、QA及有效汇总仍为空/作废，没有新发送或重试。效果G阶段取消后cases为空，两侧记录失效。用户原8000进程未被终止。
- Q阶段2项成功、1项等待时取消和新任务均409；重启保留2个成功草稿，剩余Q计次后继续；证据直接复用，Q全终态后才可另起任务。
- 三类模型异常和Q独立失败不回滚E、不把技术错误计成Badcase。各阶段成功后停止调用。不可比业务完整结果保留，抽样目标不缩，候选不足validation_failed。
- 在测试入口给真实SQLite INSERT注入一次故障，分别于kb_row、export_item、supplement_item。API503后所有相关表计数与操作回执均等于故障前；已有版本、CSV及历史快照保持；无部分记录。测试故障入口在静态兜底路由之前注册，仅测试进程有效。

每个用例的真实时序和请求次数在其provider-calls.jsonl、HTTP记录、服务日志及持久快照内，可按case/stage/side/gap核对。具体有效目录通过verification-summary逐运行索引读取。[effect-input-equivalence.json](evidence/task020-v1/effect-input-equivalence.json)保存两侧原H及system Prompt相同、仅KB及各自生成目标不同的独立比对。

## 6. Chrome核心链路

最新浏览器目录：`evidence/task020-v1/test_chrome_core_chain-32685300-d47c-4e8a-88dd-bfc0b81025c2/`。21项检查通过，trace.zip含真实交互，截图01～09及CSV下载保留。实际页面上传CSV、查看双预警/详情、补答审核、选择导出下载、编辑后待审、历史A、实际补充详情、页面发起效果验证、两侧持久回复、三维模拟标记、刷新和后端重启、零成功、运行和取消均有证据。

链路中部分数据创建与补充确认由真实API的模拟输入准备，其余页面操作由Chrome执行，不能表述为所有动作均通过浏览器点击。后端和数据库从始至终真实；没有用前端假接口覆盖正式状态。21项不是正式P01～P07用户呈现验收。首轮浏览器默认拒绝window.confirm导致未发效果POST，定位后测试显式接受确认框，产品交互未修改。

## 7. U08、F32及未决项

U08：100个独立模拟case，1000个独立task UUID种子轮，每轮10个唯一候选。原始[u08-raw.jsonl](evidence/task020-v1/u08-raw.jsonl)和[u08-summary.json](evidence/task020-v1/u08-summary.json)保留。每条累计81～121次，全部在60～140含边界。生成脚本仅在文件不存在时创建；本次没有重新抽样挑通过结果。恢复使用固定任务种子的机制与任务间独立统计分别核对。

F32：[F32-real/frozen-expectations.json](evidence/task020-v1/F32-real/frozen-expectations.json)先固定新的模拟退款时限题、原样兜底与追加打5分暗示版本。资料已有4个工作日，预期准确性1、主因敷衍、Badcase、不生成QA；不额外要求意图或服务两侧完全相等。确定性测试证明两种回复原样在target_reply、未污染history或成为system指令。本次真实DeepSeek部分[F32-real/not-run.json](evidence/task020-v1/F32-real/not-run.json)记录8000不可达，未运行，不引用019原题替代本次独立成对真实验证。

U06持久计次恢复规则本次已测。U08本次独立统计通过。U10仍留023三批实际耗时及本人阈值确认；U12正式50条与逐条预期仍留021，均保持开放。019原DBG-06漏识别问题仍为保留未解决，部分评分待人工复核仍保留，不因020确定性测试通过而关闭。

## 8. 失败、限制与承接

| 编号 | 证据与根因 | 影响与处理 | 当前状态/承接 |
|---|---|---|---|
| T20-H01 | http-first：表名写成复数；把摘要当详情；对日志end取stage；缺答审核预期误写409 | 测试设施错误；按实际schema/接口及确定需求校正。保持整份拒绝和审核阻止标准 | 限定复测通过，原5失败留存 |
| T20-H02 | http-harness-retest：误以为取消会中止在途响应；审核写接口返回question而非详情standard_question | 测试未放行在途返回；现取消后主动返回再核对丢弃。按两真实接口区分字段 | 2项复测通过，无产品修改 |
| T20-H03 | transactions-browser：测试故障路由在静态挂载之后405；Chrome未处理confirm | 注入未发生/没有提交。调整测试路由顺序和显式接受确认框 | 回滚与浏览器复测通过 |
| T20-H04 | extra：自造枚举“未理解用户意图”不符已定“AI 理解错了用户意图”；合规主因测试给准确性3 | 非法输入被正确拒绝。修正合法例的固定输入为已确认枚举及准确性1，不放宽产品校验 | 复测通过；非法首轮保留 |
| T20-H05 | browser-failure-states：把evaluation的派生字段误读到不存在的result子层 | 按effects实际数据契约改测试访问为evaluation.is_badcase，保持业务预期 | 限定复测通过、原失败保留 |
| R20-01 | F32-real/not-run：用户真实后端不可达 | 本次独立真实抗评分暗示语义不能判通过 | 待同本任务恢复已配置后端后执行；不是要求发送密钥到聊天 |
| R20-02 | 本次独立测试重点及矩阵范围 | 新增sdk-edges已测11类外壳反例、5类HTTP错误单次发送、Retry-After=11及清理。默认300秒核对参数，测试截止缩短为0.025秒；不宣称真实等待300秒或已穷尽所有日期形式/异常组合。新增浏览器失败状态也通过，正式呈现仍留022 | 已补查的确定性边界通过；真实模型/API与正式呈现不能由替身或缩短时间验证替代，留同任务真实复核及022，不改产品 |
| R20-03 | TASK019 debug-record既有真实失败/待复核 | 原DBG06漏识别、评分差异保持未解决；确定性不会证明真实模型语义 | 模型语义问题另按用户确认承接；正式021/022不得漏生成缩分母 |
| R20-04 | 006及最新RDD | 正式50语义/QA质量/人工真实效果/三批性能本次均未运行 | 021固定，022验收，023实测；不自动启动 |

未发现可以由本次已测证据确认的新产品缺陷；此句只限已执行子项。测试设施修正不等于产品修复，R20未运行项不能被“115通过”覆盖。所有原始失败XML/log保留；没有对产品、Prompt、业务标准或验收阈值作变更。回归模块原自测只作为历史背景，未混入115项独立统计。

## 9. 执行规范与交付门禁

档位S2，已有任务卡及确认Spec，读取using-vibe-delivery-kit、routing-by-risk、systematic-debugging、webapp-testing、verification-before-completion及package启动/分级/测试策略/Review/交付检查。没有产品接口、模型或依赖变更，不重复架构门禁；不涉及生产/真实安全权限，跳过S4；已有RDD，跳过Intake/RDD重做；不写产品功能，跳过开发实施流程。sequential-thinking/shrimp/code-index当前不可用，以显式计划、证据清单和rg降级，未虚构工具调用。现有仓库有大量历史未跟踪文件及旧删除，不能把整个git status当作本次diff；用冻结文件SHA256及定向差异核对本次范围。

交付前核对50ID唯一覆盖、当前115身份与最新XML、证据文件存在、原失败保留、产品92哈希不变及文档链接。报告检查只证明报告完整性。用户确认记录：2026-10-09本人明确回复“确认”，认可报告及未运行说明；不等于F32或产品最终验收通过。报告完成≠全规则验收通过≠产品最终验收通过。

### 交付前补充复核（2026-10-09，Codex）

115个当前测试身份最新有效结果通过；主链路21检查、失败状态专项4检查分别记录，不把内部检查重复加入pytest数量。`sdk-edges.xml`17通过；`retry-timing.json`真实4组请求间隔符合2秒/5秒下限（不属性能验收）。新增浏览器失败专项有效目录见verification-summary，不用首轮3项已完成误报整个专项通过。92产品文件SHA256不变。U08原始一次1000轮数据未重生成。


### 2026-10-09 TASK-020报告及未运行说明认可（Codex，最新状态）

本人针对“请确认这份报告及其未运行说明”明确回复“确认”。TASK-020报告交付已完成，实际报告及披露限制已获用户认可；主要产物docs/04_validation/deterministic-report.md为1.0确认稿，认可证据task020-v1/approval-results.json。

认可范围为已交付的独立确定性/恢复/交互验证报告与原始证据，不表示全部50条、F32真实模型复核或产品最终验收通过。F32真实复核仍未运行（交付时真实后端不可达），后续补测事项保留；未新增调用或重跑测试。U10/U12以及019原DBG06漏识别、部分评分待复核继续开放。本次只同步认可记录，产品实现、Prompt、业务和原始运行证据未修改；TASK-021～024未启动，未获本次授权。此前“待用户确认”为交付时历史检查点，由本条更新。
