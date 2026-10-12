# TASK-010 模型调用与结构化结果校验

日期：2026-10-07｜执行者：Codex｜状态：已完成，实际产物已获用户认可（2026-10-07）

## 范围与依据

前置TASK-007整体报告第17章及TASK-009实际模块均已获用户认可。输入文件及执行前SHA256见[输入记录](../.codex/task010-inputs.json)。本模块依据已确认003模型契约第3～6章及007补充、006 C02/C03和F12/D03、U03/U04/U12。业务Prompt正文、评分语义决策及QA业务交接分别由011、013、016承接；本模块不生成这些业务内容。

```text
011/013/016冻结来源、完整Prompt和配置
              ↓
009预检 → 先提交attempt与次数 → 010 start_once
                                  ↓
                          官方SDK只发送一次
                                  ↓
                    外壳 → 严格JSON → 完整协议
                       ↙                    ↘
                成功含追溯信息           结构化失败
                       ↘                    ↙
                       009同事务保存
                  重试2/5秒或Retry-After，最多3次
                       ↓
             成功/最终异常互斥，取消后不提供结果
```

## 路径及接入接口

| 路径 | 职责 |
|---|---|
| app/model_client/deepseek.py | 固定配置、离线输入预检、AsyncOpenAI单次请求及等待/清理 |
| app/domain/model_contract.py | Draft202012及条件完整性、严格JSON、码点和证据定位 |
| app/services/model_results.py | 从已有009表读取普通批次互斥成功/最终异常集合，不计算指标 |
| app/services/execution.py | 仅在已有009预检快照补stage、Prompt接口版本及文档型号 |
| app/main.py | 从运行环境创建010客户端，停机后清理；缺密钥保持无客户端 |
| app/model_client/assets/ | 官方V4 tokenizer与模板的原文件、来源及SHA256 |
| tests/test_model_*.py | 契约、SDK替身、SQLite调度集成和真实本地HTTP冒烟 |

`validate(preview)`在009计次前检查固定配置、两条system/user消息、完整Prompt、原history与target_reply及输入能力。未发送的本地阻塞交009记录零次；不截断资料。输入消息及Prompt由业务模块提供，本轮测试内容仅用于确定性协议验证。`start_once(prepared)`同步创建一次HTTP执行任务，返回可等待任务；不额外计次或自行重试。`Outcome`携成功合同/定位/追溯警告，或CALL_ERROR、PARSE_ERROR、INCOMPLETE_RESULT及安全原因、响应依据、Retry-After。009保存请求、每次尝试及终态；模型密钥不进入这些字段。

`case_outcomes(database, task_id)`只读取普通任务的原回复E单元。尚未齐备返回eligible=false；取消返回空集合；全部E终态返回successes与final_errors，携case身份、真实次数、最后attempt依据，核对两集合覆盖输入数。有效Badcase仍是模型成功结果，后续业务分类不在本轮实现。效果完整链结果留016。

009独占发送前持久计次、最多3次、全局3并发、共享窗口、取消竞争、恢复和退避。SDK `max_retries=0`。截止点为300秒，先清理连接再释放名额；截止后的成功不接收。取消由009丢弃迟到回复，不声称供应商撤回计算或免计费。成功已保存则恢复不重调；已发送未保存按009保守计次恢复。

## 冻结配置和校验

请求统一为`deepseek-flash`，文档依据`DeepSeek-V4.1-Flash`。E启用thinking/high，max_tokens=32768；G关闭thinking/temperature=0/max_tokens=8192；Q关闭thinking/temperature=0/max_tokens=2048。均json_object、stream=false，不新增调参入口。完整配置及Prompt按009已有快照保存；供应商model、指纹、id、created和usage保留，缺失字段记追溯警告而不凭空填零或重试有效评分。

仅接受单个严格JSON对象。拒绝Markdown围栏、解释、重复键、NaN/Infinity、额外字段、4.0或布尔评分；分数1～5。校验三维reason及知识证据reason的CRLF/CR归一和≤50 Unicode码点。主次因枚举及知识缺失、资料冲突、合规主因条件按003执行。snippet必须在单条原history消息或target_reply中连续定位；不跨消息拼接。不判断证据语义是否充分或模型评分是否正确。

## 本机运行与验证

沿用[README](README.md)的单worker Uvicorn启动命令。运行环境若有`DEEPSEEK_API_KEY`则创建官方SDK客户端；本轮无密钥，未发真实API请求。不要把密钥写进配置快照、CSV、日志或代码。008导入及009任务查询仍可运行。普通评测业务启动尚需TASK-011提供builder和hooks；不能把本模块看作完整评测产品。

在项目根PowerShell执行：

```powershell
./backend/run-task010-tests.ps1
./backend/.venv/Scripts/python.exe .codex/task010-review.py
```

真实命令、逐项预期/实际、JUnit、日志、diff及未验证项见[验证记录](../.codex/task010-verification.md)。所有输入为临时合成测试内容，不是调试集或正式验收集。SDK MockTransport证明本地接口和故障处理；localhost HTTP服务器证明SDK真实socket收发；均不证明真实DeepSeek评分/费用/效果。

## 技术核对与限制

复用OpenAI SDK 2.54.0、jsonschema和tokenizers/Jinja。SDK 2主版本兼容既有HTTPX 0.28；没有借本任务迁移SDK 3与HTTPX 2。新依赖及哈希锁在requirements.lock，已有008/009依赖保持原版本。未新增表或迁移、第二调度器、手动重试、额外AI审核。离线tokenizer直接使用官方数据与模板，不执行下载包中的Python；配套示例配置中的model_max_length=16384未作为当前V4 API上下文上限。当前输入预检使用1M上下文的本地计数边界；与真实API计数/能力的一致性仍需最小真实调用核对，超限不静默截断。

官方依据：[DeepSeek型号/能力](https://api-docs.deepseek.com/quick_start/pricing/)、[thinking](https://api-docs.deepseek.com/guides/thinking_mode/)、[token用量及离线分词器](https://api-docs.deepseek.com/quick_start/token_usage/)、[OpenAI SDK 2.54.0](https://github.com/openai/openai-python/tree/v2.54.0)。具体API参考页本轮读取超时，既有003已确认协议与本地SDK请求测试仍有效；不能称真实API已核对通过。官方发布名称/指纹不构成供应商冻结承诺。

U10耗时阈值留TASK-023；U12正式50条及逐条预期留TASK-021。本轮不关闭两项，不进入TASK-011～024。后续020/022独立及正式验证按006保持。当前只有模块实现及本地验证完成，用户产物认可和产品最终验收尚未记录通过。


### 2026-10-07 TASK-010产物认可（最新状态，Codex）

用户针对TASK-010实际代码与本地验证交付明确回复“确认”。TASK-010已完成，实际产物已获用户认可。认可范围为已交付的DeepSeek单次调用、完整结构校验、009统一调度接入、异常与终态追溯，以及188项本地验证证据；不是真实模型语义通过或整产品最终验收。

真实DeepSeek调用因密钥缺失未验证；API兼容性及token计数差异仍待真实核对，既有依赖弃用提示保留。U10耗时阈值留TASK-023，U12正式样本留TASK-021且开放。TASK-011～024未执行、未获本次授权。此前“待用户确认”为交付时历史检查点，本条为最新认可记录。本次仅同步认可状态，不修改实现或原测试运行快照。
