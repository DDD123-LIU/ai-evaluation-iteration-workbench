# 规划及设计门禁审查报告（TASK-007）

日期：2026-10-06（Asia/Shanghai）｜执行者：Codex｜审查角色：证据复核与架构审查｜档位：S3｜版本：1.0确认稿｜状态：第12章明确部分整体认可；DG-01～05已关闭（设计文档层）；整体报告已获用户认可

**最新设计审查结论：已无已知阻塞设计发现，具备进入实现的设计条件；整体报告已获用户认可，开发未授权。** 001～006实际产物及认可前置满足。全部50条验收有设计和验证承接；这证明可追溯，不证明产品通过。最新状态见第16章；DG-03已按两项决定同步复审关闭，DG-04旧状态已整理并复审关闭。本报告不是开发授权。未启动008或后续任务。

## 1. 审查范围、授权及方法

用户明确授权仅执行TASK-007，并要求先展示发现，涉及业务决定或源修订先确认，再落实和复审。主要交付按[TASK-007完整卡](task-cards/TASK-007.md)落本文件。审查使用与编写不同的视角：对照权威RDD逐项反查设计、任务及验证，不以旧自审的“通过”替代结论；由当前Codex执行，不声称另一个模型或外部独立审查者已参与，不自动启动多agent。

范围：当前六图、验收清单全部50项、未知项U01～U13、最新Reviewer/Gate记录、任务总表/依赖图、24张实际任务卡，以及001～006实际认可产物。业务语义逐项复核；24卡按输入、输出、负责/不负责、可判断验收、依赖和人工确认检查。008～024没有实际业务产物，未来输出路径不当作完成证据。

排除：2026-10-02旧设计、自审；产品代码、模型API、实际样本、调试、正式业务验收、浏览器测试、性能测量、部署、CI及外包。不恢复或改动既有删除文件。只新增本报告及项目`.codex/`审计材料；本轮未修改RDD、001～006、任务卡、总表、依赖或项目入口以关闭问题。

### 1.1 实际使用规范与限制

配套根：`D:/Codex/home/skills/using-vibe-delivery-kit/references/project-template/ai-delivery-kit/`。

| 规范 | 应用 |
|---|---|
| `06_ai_execution/task-start-protocol.md`、`00_overview/task-complexity-routing.md` | S3设计门禁，核对前置、范围和授权 |
| `03_task_dispatch/task-card-template.md` | 24个任务包契约及一个主要交付 |
| `02_rdd_requirement_discovery/rdd-gates.md` | 按真实Gate 0～3定义复核；不混同实现门禁 |
| `07_quality_gates/review-checklist.md` | 已定需求、范围、边界、人工确认与证据 |
| `07_quality_gates/architecture-code-quality.md` | 模块、依赖、公共接口、数据生命周期、选型和可测试性 |
| `07_quality_gates/testing-strategy.md`、`final-response-checklist.md` | 本地文档证据、未运行限制与交付自证 |

技能：using-vibe-delivery-kit、routing-by-risk、verification-before-completion、systematic-debugging。未重做RDD/Intake；无新功能设计，不重套Feature Spec；无产品代码Bug；本地检查器初次失败按`07_quality_gates/debugging-protocol.md`定位修正，见本轮验证记录。模拟业务的合规原因标签不是本轮真实生产合规操作，未触及真实支付、权限或生产数据，S4安全扫描及生产回滚不适用。Review清单默认`docs/05_review/`路径按本卡约定改为本文件；不新增第二份报告。项目禁止CI、自动multiagent和外包，优先遵守项目及本次明确边界。

sequential-thinking、shrimp-task-manager、code-index、exa工具未暴露；采用显式分析计划、rg/PowerShell读取和本地检查，官方能力核对使用web工具。没有虚构调用。记忆注册表无相关命中，不使用记忆事实。

### 1.2 审查执行顺序

前置及输入版本核实 → 50项源/设计/主责/验证反查 → 字段、状态、异常和人工边界交叉比对 → 24卡及57依赖复核 → 技术准备和延期影响判断 → 保存开放发现 → 本地文档检查。后续关闭须用户决定、实际修订及新鲜复审三者齐备。

## 2. 输入版本及产物认可前置

所有当前源的SHA-256和行数见[本次输入清单](../../.codex/task007-review-inputs.json)。本报告引用相对路径、章节/条目和行号；输入改变后行号可能变化，复审以哈希和条目共同定位。未核实历史聊天逐字记录时只陈述当前源记录，不把旧日志当新证据。

| 产物 | 文件实际版本/认可证据 | 前置结果 |
|---|---|---|
| TASK-001 | [scope.md](../02_prd/scope.md)首版确认稿，第3行及“基线与确认记录”；[001卡](task-cards/TASK-001.md)确认与完成记录，用户回复“是” | 实际文件存在，已完成且认可 |
| TASK-002 | [data-dictionary.md](../02_design/data-dictionary.md)首版确认稿，第3/7行；[002卡](task-cards/TASK-002.md)确认与完成记录 | 实际文件存在，已完成且认可 |
| TASK-003 | [model-contract.md](../02_design/model-contract.md)首版确认稿，第3/11行；[003卡](task-cards/TASK-003.md)记录协议及U12技术提案认可 | 实际文件存在，已完成且认可 |
| TASK-004 | [behavior-spec.md](../02_design/behavior-spec.md)1.0确认稿，第3行及12.3；[004卡](task-cards/TASK-004.md)记录整体认可；B01～03有单项决定 | 实际文件存在，已完成且认可 |
| TASK-005 | [ui-spec.md](../02_design/ui-spec.md)1.0确认稿，第3/28行及第12章；[005卡](task-cards/TASK-005.md)记录整体设计建议认可 | 实际文件存在，已完成且认可 |
| TASK-006 | [verification-plan.md](../02_design/verification-plan.md)1.0确认稿，第3/304行；[006卡](task-cards/TASK-006.md)已完成；本聊天用户在方案认可问题后回复“是” | 实际文件存在，已完成且认可 |

其余输入：[用户地图](../../RDD/user-map.md)、[场景地图](../../RDD/scenario-map.md)、[决策地图](../../RDD/decision-map.md)、[数据地图](../../RDD/data-map.md)、[输出地图](../../RDD/output-map.md)、[风险地图](../../RDD/risk-map.md)、[验收清单](../../RDD/验收清单.md)、[关键未知项](../../RDD/关键未知项.md)、[Reviewer记录](../../RDD/Reviewer记录.md)、[RDD Gate结论](../../RDD/Gate结论.md)、[总表](ai-task-master-list.md)、[依赖图](dependency-map.md)、[AGENTS](../../AGENTS.md)、[PROJECT_CONTEXT](../../PROJECT_CONTEXT.md)。六图主体更新于2026-10-05，003～005局部确认及状态更新于2026-10-06；以实际当前文件和最新决定为准。

本次直接用户请求已满足007审查授权。007卡中“未获得执行授权”“未来前置未满足”是编卡检查点，本报告记录新授权，不据该旧文案拒绝审查；源同步待用户确认。

## 3. 首次审查发现及最新状态

以下证据、影响和建议保留首次审查时点；行号对应原输入快照，不冒充同步后的现状。最新关闭/未决依据以第16章为准；第14/15章保留对应轮次检查点。

严重程度：P1阻止受影响工程路径启动；P2局部契约或业务决定缺口，阻止受影响操作；P3非阻塞整理建议。严重程度是本轮判断，不是新增产品验收标准。没有P0证据。建议不是决定；首次审查全部发现开放，当前状态须依据实际源同步及第14章复审。

### DG-01｜P1｜缺少可供工程实施的统一技术设计｜已关闭（设计文档层）

证据：[PROJECT_CONTEXT](../../PROJECT_CONTEXT.md)第5章第54～57行明确前端/后端/数据库未定、部署配置未定，第10章第123行交“后续技术设计”；[字典](../02_design/data-dictionary.md)第7章第371行明确数据库/ORM/schema/ID/保存方式未定；[008卡](task-cards/TASK-008.md)“输出物”要求代码/测试路径由**认可技术设计**确定，[018卡](task-cards/TASK-018.md)输入依赖008～017真实接口。001～006仅业务、逻辑数据、外部模型和交互/验证契约，没有实际产品接口、物理持久结构、工程运行配置或被认可技术栈文件。[006方案](../02_design/verification-plan.md)第2章第33行又将工具/命令交实现后登记、经007办理。

判断与影响：业务Spec已准备好，工程的共享基础仍未准备好。不能将“框架可选”解释成已认可选型，也不能把009逻辑次数字段直接当完整恢复实现。影响008～018整体工程准备；008最先需要资料版本/case持久层，009/010需要可测试接口，018需要实际服务契约。不是要求现在实现全部模块或冻结每个代码文件。

建议：先提交一份可审阅技术设计补充，复用现有生态，明确运行时/前后端/存储及依赖理由、模块边界、物理实体/唯一性/版本引用、产品操作输入输出及错误结构、单机启动/停止/恢复、测试生态/隔离和模块交接。长期依赖/跨模块选型按package架构规范留ADR权衡。具体版本/方案尚未提出，不自动选型、安装或生成产品代码。获用户授权后办理文档补充；不擅自新增任务编号或依赖边。

关闭证据：实际技术提案、用户认可、与002～006及008～018接口/数据/运行条件逐项复审。只认可本发现不能等同认可尚未提出的技术方案。

### DG-02｜P1｜关键持久提交和失败恢复边界未落实｜已关闭（设计文档层）

证据：[006方案](../02_design/verification-plan.md)第5章X04第126行仅明确计次保存失败“不发送”，X13第135行明确写未确认不翻状态、文件与快照不一致不报成功；第137行明确“精确事务及恢复实现未定”。[005 UI](../02_design/ui-spec.md)6.1第149行明确导出文件/快照的“具体恢复协议待工程设计”。[004行为](../02_design/behavior-spec.md)7.1规定E→Q竞争、取消、成功保存及释放窗口，但未规定物理提交边界。[003协议](../02_design/model-contract.md)第6章明确次数发送前持久及成功不重调。

判断与影响：已有正确不变量，尚不能在“写失败/提交已完成但客户端未收到/进程停在两步之间”时判定如何恢复。需要区分本地存储故障和模型三次预算；不能把计次未保存的失败伪记模型调用，也不能通过重新调成功模型修复本地写入。影响009/010调度提交、013草稿创建、014导出、015确认、017抽检标记和018读写反馈，关联F16～F18/F21/F23～F25、D03～D09、P03/P04。

建议：技术设计列出每个原子提交包含的记录、成功/取消竞争的最终裁决点、恢复扫描规则和持久身份去重；计次保存失败后的任务可恢复去向/窗口释放依据；评测成功与应生成Q建立的恢复交接；导出同一事件的文件/快照一致读回及未确认提交如何查询。保留已有三次调用、成功不重调和整体取消规则。使用存储生态事务/约束，不新增通用组件或未确认业务状态。当前仅建议需明确的边界，不指定新重试次数或自动重新发起产品任务。

关闭证据：认可的边界表，逐一承接006 X04/X05/X07/X08/X13，可构造预期/恢复后记录；随后真正产品测试留获授权实现及020。本次不要求先跑恢复实测才认可设计。

### DG-03｜P2｜全局补充/效果重复操作语义仍待决定｜已关闭（设计文档层）

证据：[002字典](../02_design/data-dictionary.md)E12第202行留新版本关联记录数未定，E13第210行留多次验证全局次数未定；[005 UI](../02_design/ui-spec.md)6.2及第12章UI-05明确“新库能关联多少补充记录、同一补充记录能发多少效果任务没有已定全局限制”，并禁止直接宣称无限次已确认；[006方案](../02_design/verification-plan.md)第19/300行保留同样问题。已确认多选**同QA多个历史快照**是另一问题，不解决重复补充记录或重复效果任务的关系。

判断与影响：不能仅凭“不新增次数限制”自定只允许一次，也不能自定无限次及只保留最新结果。影响015/016/018相关入口、关系基数、重复提交与历史任务选择；不阻断已明确CSV解析、计算或JSON结构规则的设计。全局技术不具备时仍不能实际启动这些独立模块。

建议：按用户既定方式逐个确认。先复述同一补充记录再次发起效果任务的含义，再问一次是否允许独立新任务，以及已有人工待确认记录如何定位；另一个新库对应多个补充记录的问题单独问。候选方案可比较单次与多次，但本轮不选规则、不关闭UI-05。既有“单原批次、单运行任务、历史不可覆盖、成功阶段不重复调用”保留；新任务与原任务重试不能混用。

关闭证据：逐问题明确用户决定、对应字典/行为/UI/验证及015/016接口同步后复审；不是只改待确认文字。

### DG-04｜P2（非阻塞）｜早期产物与卡保留旧就绪描述，缺少统一当前承接提示｜已关闭（设计文档层）

证据：[001范围](../02_prd/scope.md)第64行及8.1/8.2仍写型号协议未定、002～006未执行；[002字典](../02_design/data-dictionary.md)E06/E07/E11及第7章留003/004/005待确定字段/导出格式；与[003协议](../02_design/model-contract.md)第11行及第10章已认可、[005 UI](../02_design/ui-spec.md)第151行导出BOM/列顺序已认可不一致。[007卡](task-cards/TASK-007.md)第69行仍称FRESH-03开放，但[RDD Gate](../../RDD/Gate结论.md)顶部及最新“全部24卡确认及FRESH-03关闭复核”已关闭。[总表](ai-task-master-list.md)人工确认记录仍有004～006未执行的早期检查点，顶部及末尾最新状态已更新。

判断与影响：这些是设计递进/历史就绪描述，不证明001～006缺少认可，也不重新打开FRESH-03。005/006显式说明最新协议优先，实际G/E/Q字段、阈值和快照语义未见相反新决定。非阻塞，但开发若只读001/002/旧卡摘要，可能错误重开U12、漏B03或导出格式，需统一来源提示。

建议：用户确认后仅补当前承接索引/状态提示及必要明确勘误，将003完整字段、004 B01～03、005 UI-03/04的最新决定链接回001/002和相关卡；历史确认原文保留并标为当时检查点，不批量改历史为“已执行”，不重新制定枚举/阈值，不以报告直接关闭旧发现。精确导出文件名另属后续技术细节，当前方向及格式已定。

关闭证据：授权后的最小diff、最新引用/状态语义复核、50标准和57依赖保持一致。未授权，本轮零源修订。

### DG-05｜P2｜模型返回追溯元数据缺失时的成功/可比判法未明确｜已关闭（设计文档层）

证据：[003协议](../02_design/model-contract.md)第6章第138行规定“metadata缺失单独记录契约问题”，第8章第191行是“有返回则保留”，第195行只明确已检测returned_model/fingerprint变化时不可有效比较。[004行为](../02_design/behavior-spec.md)4.5要求满足003可比条件；[006方案](../02_design/verification-plan.md)X12第133行只列实际model/fingerprint不同或一侧失败。官方[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)将返回model和system_fingerprint列为required；本次官方域搜索可读取该内容，但无实调用证据。

判断与影响：没有发现官方能力与已确认型号/参数相冲突；缺口是本地遇到缺失/非法追溯元数据时，究竟仅记问题仍判阶段成功、作为外壳失败重试，或只使效果不可比，当前没有单一可判断条款。不能将无法观察指纹解释为没有漂移。影响010完整响应处理、016可比判定、018错误/对比呈现及020测试；关联F12/F27、D08/P05、U12。usage缺失已明确记未知，不能把它也改成强制失败。

建议：技术提案只对必要响应外壳和可比所需元数据列合法/缺失/非法的处理、错误类别、阶段预算和可比状态；保持usage“实际存在才保存”的原决定。新增判法先交用户确认，再同步003/004/006与010/016，不能本轮将建议当确认。官方字段required不替代项目必须明确自身异常处理。

关闭证据：用户认可处理表和对应测试设计，正常/缺失/非法/漂移各有预期。不通过重调成功项或静默换模型修复不可比。

## 4. 设计间一致性及人工/自动边界

本表表示本轮读取后的语义判断，分别说明足够与不足，不把每个“有章节”当设计正确。

| 核对主题 | 相互承接的条目 | 判断及限制 |
|---|---|---|
| 范围/角色 | 六图、001第1～3章、004第2章、005第2/9章、006第1章 | 单人模拟、会员优先、≤100、Chrome、观看者外部视频一致；无新增线上/访客/自动补库 |
| CSV/上下文 | U01/D01，002第3章，003第4章，004 RULE-01，005 A01～04/G01～02，006 C01 | 固定列及顺序、BOM、多行保原文、整份拒绝、历史重复允许；H含问题、仅末尾目标回复一致 |
| 模型结果 | 002 E06～09→003第3～6章→004第6章→005 G04～07→006 C02/C03 | G/E/Q完整字段与词法整数、码点、连续来源、条件必填明确；DG-05元数据异常未定 |
| 分数/归因 | 决策规则/U02，001 4.3，003第4/5章，004 RULE-02，006第6章 | 单维<4、合规优先、联合知识、冲突禁QA、各阈值一致；结构不代替语义 |
| 计算/无数据 | U05/F13～15，002 5.3，003第7章，004 RULE-03，005 G03/第8章，006 C04/I02 | S+E=N、成功分母、原值阈值、两位展示、零成功两项无数据、取消不统计一致 |
| 任务/计次/取消 | U06/B01～03，003第6章及补充，004第7/8章，005 T04～13，006 X01～11 | 单窗口/并发≤3/发送前计次/成功不重调/QA不取消/效果整体取消/自动终态释放明确；DG-02原子交接待补 |
| QA生成/人工审核 | U03/U07，002 E08/E10，003 Q，004 RULE-04，005 A08～11，006 C05/C06 | 每gap独立、仅标准问、空答正常、证据复用；人工补答完整并确认才通过，实际改保存回待审核 |
| 导出/快照/补充 | U13及005补充决定，002 E11/E12→004 4.4/4.5及尾部→005 6.1/6.2→006 C06/C07/I04 | BOM/四列/历史独立/当前待审历史仍有资格/同QA实际多个快照分别关联已定；来源case去重；DG-02提交、DG-03全局关系开放 |
| 旧新及抽检 | 003第8章，004 RULE-05/06，005 6.3，006 C07/C08/X12/第9章 | 原H/规则同，仅库不同；两侧重新G/E，各独立预算；K向上取整、失败补抽不缩N；足额再人工逐维；新Badcase与效果结论分开 |
| 版本/追溯 | 002第4～6章、003第8章、004第5章、005 G09～12、006 EV01～07 | 原输入、资料、Prompt全文/配置、历史快照、两侧结果及抽检可还原要求清楚；物理键/事务仍DG-01/02 |
| 验证/阈值 | 输出业务验收、U07/U08/U10/U12、004第11章、006第6/8～11章 | 45/50、23/25、ceil(M×90%)、确定性全通过、100/1000/10/60～140保留；调试/正式/性能数据分离；U10/U12未关闭 |

自动仅负责校验、调用/预算内重试、规则计算、状态/版本保存、符合条件QA、来源去重、抽补及已保存人工标记的汇总。本人仍负责资料有效、启动/取消、补答/修改/审核、导出选择、外部实际补库/快照确认、正式逐条标注、QA语义判断、效果逐维判断。没有把用户这些业务判断替换成本地AI测试或新增AI审核。

## 5. 全50条需求—设计—任务—验证反查

下表每行以[验收清单](../../RDD/验收清单.md)同ID为原判据；设计定位为实际章节/条目，不要求六份文档每份都承担全部50项。004第10章完整GWT、006第3章逐行方法/输入/预期/证据与源逐行核对。008～018主责及021的数据主责沿用总表，验证任务独立目的保留。标“承接存在”不表示实现就绪或产品通过；适用开放发现见第3章。

<!-- TRACE_START -->
| ID | 范围/字典定位 | 模型/交互定位 | 行为设计 | 验证设计 | 实施主责 | 后续验证承接 | 审查结果 |
|---|---|---|---|---|---|---|---|
| D01 | [5. 功能模块 L208](../02_prd/scope.md)；[8. 验收追溯 L416](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L314](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L78](../02_design/verification-plan.md) | [TASK-008](task-cards/TASK-008.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01设计层已补齐 |
| D02 | [5. 功能模块 L209](../02_prd/scope.md)；[8. 验收追溯 L417](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L315](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L79](../02_design/verification-plan.md) | [TASK-008](task-cards/TASK-008.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01设计层已补齐 |
| D03 | [5. 功能模块 L210](../02_prd/scope.md)；[8. 验收追溯 L418](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L287](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L316](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L80](../02_design/verification-plan.md) | [TASK-010](task-cards/TASK-010.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| D04 | [5. 功能模块 L211](../02_prd/scope.md)；[8. 验收追溯 L419](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L288](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L317](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L81](../02_design/verification-plan.md) | [TASK-009](task-cards/TASK-009.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| D05 | [5. 功能模块 L212](../02_prd/scope.md)；[8. 验收追溯 L420](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L289](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L318](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L82](../02_design/verification-plan.md) | [TASK-013](task-cards/TASK-013.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| D06 | [5. 功能模块 L213](../02_prd/scope.md)；[8. 验收追溯 L421](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L244](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L319](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L83](../02_design/verification-plan.md) | [TASK-014](task-cards/TASK-014.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| D07 | [5. 功能模块 L214](../02_prd/scope.md)；[8. 验收追溯 L422](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L245](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L320](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L84](../02_design/verification-plan.md) | [TASK-015](task-cards/TASK-015.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02/05设计层已补齐；DG-03设计层已补齐 |
| D08 | [5. 功能模块 L215](../02_prd/scope.md)；[8. 验收追溯 L423](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L290](../02_design/model-contract.md)；[10. 验收追溯矩阵 L246](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L321](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L85](../02_design/verification-plan.md) | [TASK-016](task-cards/TASK-016.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02/05设计层已补齐；DG-03设计层已补齐 |
| D09 | [5. 功能模块 L216](../02_prd/scope.md)；[8. 验收追溯 L424](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L247](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L322](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L86](../02_design/verification-plan.md) | [TASK-017](task-cards/TASK-017.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| D10 | [5. 功能模块 L217](../02_prd/scope.md)；[8. 验收追溯 L425](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L323](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L87](../02_design/verification-plan.md) | [TASK-021](task-cards/TASK-021.md) | 021准备/用户确认＋022实际核对 | 承接存在；产品未运行；U12正式资料/结果未运行 |
| D11 | [5. 功能模块 L218](../02_prd/scope.md)；[8. 验收追溯 L426](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L324](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L88](../02_design/verification-plan.md) | [TASK-021](task-cards/TASK-021.md) | 021准备/用户确认＋022实际核对 | 承接存在；产品未运行；U12正式资料/结果未运行 |
| F01 | [5. 功能模块 L176](../02_prd/scope.md)；[8. 验收追溯 L397](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L225](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L282](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L46](../02_design/verification-plan.md) | [TASK-008](task-cards/TASK-008.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01设计层已补齐 |
| F02 | [5. 功能模块 L177](../02_prd/scope.md)；[8. 验收追溯 L398](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L226](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L283](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L47](../02_design/verification-plan.md) | [TASK-008](task-cards/TASK-008.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01设计层已补齐 |
| F03 | [5. 功能模块 L178](../02_prd/scope.md)；[8. 验收追溯 L399](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L227](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L284](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L48](../02_design/verification-plan.md) | [TASK-008](task-cards/TASK-008.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01设计层已补齐 |
| F04 | [5. 功能模块 L179](../02_prd/scope.md)；[8. 验收追溯 L400](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L228](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L285](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L49](../02_design/verification-plan.md) | [TASK-008](task-cards/TASK-008.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01设计层已补齐 |
| F05 | [5. 功能模块 L180](../02_prd/scope.md)；[8. 验收追溯 L401](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L272](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L286](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L50](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F06 | [5. 功能模块 L181](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L273](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L287](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L51](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行；U12正式资料/结果未运行 |
| F07 | [5. 功能模块 L182](../02_prd/scope.md)；[8. 验收追溯 L402](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L274](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L288](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L52](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F08 | [5. 功能模块 L183](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L275](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L289](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L53](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行；U12正式资料/结果未运行 |
| F09 | [5. 功能模块 L184](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L276](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L290](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L54](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行 |
| F10 | [5. 功能模块 L185](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L277](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L291](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L55](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行 |
| F11 | [5. 功能模块 L186](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L278](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L292](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L56](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行 |
| F12 | [5. 功能模块 L187](../02_prd/scope.md)；[8. 验收追溯 L403](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L279](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L293](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L57](../02_design/verification-plan.md) | [TASK-010](task-cards/TASK-010.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F13 | [5. 功能模块 L188](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L229](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L294](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L58](../02_design/verification-plan.md) | [TASK-012](task-cards/TASK-012.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F14 | [5. 功能模块 L189](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L230](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L295](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L59](../02_design/verification-plan.md) | [TASK-012](task-cards/TASK-012.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F15 | [5. 功能模块 L190](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L231](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L296](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L60](../02_design/verification-plan.md) | [TASK-012](task-cards/TASK-012.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F16 | [5. 功能模块 L191](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L232](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L297](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L61](../02_design/verification-plan.md) | [TASK-009](task-cards/TASK-009.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F17 | [5. 功能模块 L192](../02_prd/scope.md)；[8. 验收追溯 L404](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L280](../02_design/model-contract.md)；[10. 验收追溯矩阵 L233](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L298](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L62](../02_design/verification-plan.md) | [TASK-009](task-cards/TASK-009.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F18 | [5. 功能模块 L193](../02_prd/scope.md)；[8. 验收追溯 L405](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L234](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L299](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L63](../02_design/verification-plan.md) | [TASK-009](task-cards/TASK-009.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F19 | [5. 功能模块 L194](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L281](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L300](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L64](../02_design/verification-plan.md) | [TASK-013](task-cards/TASK-013.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F20 | [5. 功能模块 L195](../02_prd/scope.md)；[8. 验收追溯 L406](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L282](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L301](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L65](../02_design/verification-plan.md) | [TASK-013](task-cards/TASK-013.md) | 020确定性＋021固定预期＋022语义验收 | 承接存在；产品未运行；U12正式资料/结果未运行 |
| F21 | [5. 功能模块 L196](../02_prd/scope.md)；[8. 验收追溯 L407](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L283](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L302](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L66](../02_design/verification-plan.md) | [TASK-013](task-cards/TASK-013.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F22 | [5. 功能模块 L197](../02_prd/scope.md)；[8. 验收追溯 L408](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L235](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L303](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L67](../02_design/verification-plan.md) | [TASK-014](task-cards/TASK-014.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F23 | [5. 功能模块 L198](../02_prd/scope.md)；[8. 验收追溯 L409](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L236](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L304](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L68](../02_design/verification-plan.md) | [TASK-014](task-cards/TASK-014.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F24 | [5. 功能模块 L199](../02_prd/scope.md)；[8. 验收追溯 L410](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L237](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L305](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L69](../02_design/verification-plan.md) | [TASK-014](task-cards/TASK-014.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| F25 | [5. 功能模块 L200](../02_prd/scope.md)；[8. 验收追溯 L411](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L238](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L306](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L70](../02_design/verification-plan.md) | [TASK-015](task-cards/TASK-015.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02/05设计层已补齐；DG-03设计层已补齐 |
| F26 | [5. 功能模块 L201](../02_prd/scope.md)；[8. 验收追溯 L412](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L239](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L307](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L71](../02_design/verification-plan.md) | [TASK-015](task-cards/TASK-015.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02/05设计层已补齐；DG-03设计层已补齐 |
| F27 | [5. 功能模块 L202](../02_prd/scope.md)；[8. 验收追溯 L413](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L284](../02_design/model-contract.md)；[10. 验收追溯矩阵 L240](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L308](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L72](../02_design/verification-plan.md) | [TASK-016](task-cards/TASK-016.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行；DG-01/02/05设计层已补齐；DG-03设计层已补齐 |
| F28 | [5. 功能模块 L203](../02_prd/scope.md)；[8. 验收追溯 L414](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L241](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L309](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L73](../02_design/verification-plan.md) | [TASK-017](task-cards/TASK-017.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F29 | [5. 功能模块 L204](../02_prd/scope.md)；[8. 验收追溯 L415](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L242](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L310](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L74](../02_design/verification-plan.md) | [TASK-017](task-cards/TASK-017.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| F30 | [5. 功能模块 L205](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L217](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L311](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L75](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行 |
| F31 | [5. 功能模块 L206](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L285](../02_design/model-contract.md)；[10. 验收追溯矩阵 L243](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L312](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L76](../02_design/verification-plan.md) | [TASK-009](task-cards/TASK-009.md) | 020并发规则＋023三批实测/用户定阈值 | 承接存在；产品未运行；U10性能开放 |
| F32 | [5. 功能模块 L207](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | [11. 验收追溯与本轮验证边界 L286](../02_design/model-contract.md)；非本稿独立行；由004完整GWT承接 | [10. 全50条验收追溯与 Given-When-Then L313](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L77](../02_design/verification-plan.md) | [TASK-011](task-cards/TASK-011.md) | 020本地独立验证；022链路验收 | 承接存在；产品未运行 |
| P01 | [5. 功能模块 L219](../02_prd/scope.md)；[8. 验收追溯 L427](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L291](../02_design/model-contract.md)；[10. 验收追溯矩阵 L218](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L325](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L89](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行 |
| P02 | [5. 功能模块 L220](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L219](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L326](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L90](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行 |
| P03 | [5. 功能模块 L221](../02_prd/scope.md)；[8. 验收追溯 L428](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L220](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L327](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L91](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| P04 | [5. 功能模块 L222](../02_prd/scope.md)；[8. 验收追溯 L429](../02_design/data-dictionary.md) | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L221](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L328](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L92](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行；DG-01/02设计层已补齐 |
| P05 | [5. 功能模块 L223](../02_prd/scope.md)；[8. 验收追溯 L430](../02_design/data-dictionary.md) | [11. 验收追溯与本轮验证边界 L292](../02_design/model-contract.md)；[10. 验收追溯矩阵 L222](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L329](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L93](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行；DG-01/02/05设计层已补齐；DG-03设计层已补齐 |
| P06 | [5. 功能模块 L224](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L223](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L330](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L94](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020交互规则＋022实际呈现 | 承接存在；产品未运行 |
| P07 | [5. 功能模块 L225](../02_prd/scope.md)；非本稿独立行；由004完整GWT承接 | 非本稿独立行；由004完整GWT承接；[10. 验收追溯矩阵 L224](../02_design/ui-spec.md) | [10. 全50条验收追溯与 Given-When-Then L331](../02_design/behavior-spec.md) | [3. 全50条验证追溯矩阵 L95](../02_design/verification-plan.md) | [TASK-018](task-cards/TASK-018.md) | 020/022呈现浏览器＋023性能 | 承接存在；产品未运行；U10性能开放 |
<!-- TRACE_END -->

计数目标：F32＋D11＋P7＝50。不新增第51条验收或迁移主责。正式业务的50个case与50条F/D/P要求不同；F32成对试验不占正式50case。原数值/禁止行为保留，缺结果计错、不从50/25/M剔除。本轮没有实际测试输入和产品输出。

## 6. 24个任务契约、依赖和实现准备

逐卡已核对输入、一个主要输出、负责/不负责、可判断验收、前后依赖及人工确认。以下列实际主输出、现阶段准备和缺口；卡内“本轮仅编卡/未来输入”按编卡日期解释，不能成为授权当前审查的阻碍。

<!-- TASKS_START -->
| 任务 | 当前主要交付 | 输入/输出/边界/验收/依赖/人工点 | 现阶段判断 |
|---|---|---|---|
| [TASK-001](task-cards/TASK-001.md) | docs/02_prd/scope.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 实际产物完成且认可；旧状态已按DG-04整理 |
| [TASK-002](task-cards/TASK-002.md) | docs/02_design/data-dictionary.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 实际产物完成且认可；旧状态已按DG-04整理 |
| [TASK-003](task-cards/TASK-003.md) | docs/02_design/model-contract.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 实际产物完成且认可；旧状态已按DG-04整理 |
| [TASK-004](task-cards/TASK-004.md) | docs/02_design/behavior-spec.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 实际产物完成且认可；旧状态已按DG-04整理 |
| [TASK-005](task-cards/TASK-005.md) | docs/02_design/ui-spec.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 实际产物完成且认可；旧状态已按DG-04整理 |
| [TASK-006](task-cards/TASK-006.md) | docs/02_design/verification-plan.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 实际产物完成且认可；旧状态已按DG-04整理 |
| [TASK-007](task-cards/TASK-007.md) | docs/03_tasks/design-gate-review.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 本轮已执行并复审；设计发现均关闭；整体报告待用户审阅，开发未授权 |
| [TASK-008](task-cards/TASK-008.md) | 导入及版本模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-009](task-cards/TASK-009.md) | 单任务执行模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-010](task-cards/TASK-010.md) | 模型适配及校验模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-011](task-cards/TASK-011.md) | 评测模块（含版本化Prompt）＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-012](task-cards/TASK-012.md) | 批次汇总模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-013](task-cards/TASK-013.md) | QA生成模块（含Prompt）＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-014](task-cards/TASK-014.md) | 审核导出模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-015](task-cards/TASK-015.md) | 补充及来源追溯模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-016](task-cards/TASK-016.md) | 效果对比模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-017](task-cards/TASK-017.md) | 抽检及结论模块＋本地测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-018](task-cards/TASK-018.md) | 工作台页面模块＋本地交互测试 | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 安排认可、未执行；DG-01/02/05设计层已补齐，DG-03设计层已补齐；仍需明确实现授权 |
| [TASK-019](task-cards/TASK-019.md) | docs/04_validation/debug-record.md（引用独立调试数据） | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 独立调试有契约，无数据或结果；等待011/013/016/018实际产物及授权 |
| [TASK-020](task-cards/TASK-020.md) | docs/04_validation/deterministic-report.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 确定性/恢复独立验证有契约，等待018/019及授权 |
| [TASK-021](task-cards/TASK-021.md) | docs/04_validation/acceptance-fixture-manifest.md（引用50条及标注） | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 正式样本配额/预期固定契约清楚，等待020及逐条用户固定；U12开放 |
| [TASK-022](task-cards/TASK-022.md) | docs/04_validation/product-acceptance-report.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 真实模型/QA语义/UI及人工效果有契约，等待020/021及授权 |
| [TASK-023](task-cards/TASK-023.md) | docs/04_validation/performance-report.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 三批实测/用户限值决定有契约，等待020；U10开放 |
| [TASK-024](task-cards/TASK-024.md) | docs/04_validation/final-review.md | 六项均具条目；按卡原契约核对，前后依赖与总表/图一致 | 等待022/023真实证据和用户确认；无产品交付通过证据 |
<!-- TASKS_END -->

57条依赖与总表/卡/图一致且无环，单人顺序拓扑方向合理：008导入/版本→009持久调度→010适配/校验→011评分证据→012指标→013标准问→014人工审核/快照→015补充→016旧新→017抽检→018完整UI；019独立调试→020规则/恢复→021正式固定→022业务/呈现，020→023性能，022/023→024。直接边以原图为准，这一串是可行顺序，不补边。

009在010前可实现通用阶段/计次接口并用本地替身验证；不应在009再实现模型解析重试、让010也调度造成双重预算。011/013/016的完整Prompt是各自主要交付的一部分，003已定义输入输出和固定正文/升版要求，当前没有Prompt全文并不要求本轮提前编写它们或正式样本。模块主责与019独立调试/020独立验证分开，后期验证不是取消模块本地测试。

018最后接入所有真实接口，符合后端数据先准备的顺序；不要求现在完成全部页面才写每个模块。但DG-01须先确定共享基础/交接，DG-02须先确定可靠性边界；原图缺少具体技术设计的承接位置，不通过添加新边掩盖，要由用户明确如何补充。未发现任务图循环或验收主责漏分；不是所有任务都能现在执行。

## 7. U项及其阻塞边界

| U | 本次核实的当前状态 | 承接/影响 |
|---|---|---|
| U01 | 已确认三CSV模板、解析、原文及问题一致 | 002/004设计→008/020，不重开 |
| U02 | 已确认纯冲突/合规组合与QA禁止 | 003/004→011/013/020/022 |
| U03 | 已确认E证据必填、Q只标准问及独立预算 | 003/004→010/011/013/020 |
| U04 | 已确认≤50 Unicode码点，换行统一 | 003/004→010/011/018/020 |
| U05 | 已确认两位展示，原值阈值，无数据 | 004/005/006→012/018/020/022 |
| U06 | 已确认发送前计次、恢复、整体取消及B01/B03 | 009/010/020；DG-02技术边界待补，不重开已定业务 |
| U07 | 已确认固定应生成集合、语义90%、确定性全通过 | 013/021/022；M随实际正式内容固定，本轮不准备 |
| U08 | 已确认目标/补抽/偏选规模及60～140 | 017/020；当前未运行 |
| U09 | 已确认Windows Chrome，实际版本后记 | 018/022，不预设实测通过 |
| U10 | 并发3、计时条件、连续3批已确认；耗时上限延期认可、最终未定 | 009已定规则可实现；023实测后提出限值/判法，用户确认；阻断性能通过声明，不单独阻断业务实现 |
| U11 | 已确认信息原则、本人角色/风险分工；005布局已认可 | 018/022，不加评分分类人工编辑 |
| U12 | 003型号/配置/完整G/E/Q/网络/漂移技术已认可；入口已定；实际50及标注仍开放 | 010/011/013/016按认可协议；DG-05待补局部异常判法；019独立调试，021用户逐条固定，022正式验收，不阻断已定契约实现，不提前准备样本 |
| U13 | 历史已通过导出资格已定；005同QA多历史快照实际采用可多选已定 | 014/015/018/020/022；DG-03全局重复不是重开U13 |

精确文件名、随机库/测试器版本、物理时间/ID/空值编码等工程细节在DG-01认可提案中承接，不各建业务U项。模型别名稳定也不能保证零波动，正式语义/性能/效果需未来真实证据。本次不关闭U10或U12实际样本。

## 8. 架构质量及官方模型能力复核

| 维度 | 本次判断 |
|---|---|
| 模块边界/复杂度 | 008～018职责及排除清楚；不把计算和人工判断交模型，不自研模型协议框架；实际工程结构未定DG-01 |
| 依赖方向/接口 | 57边无环；003外部接口完整G/E/Q；产品HTTP/模块输入输出和错误表示尚未具体化DG-01 |
| 数据/生命周期 | 15逻辑实体、历史不覆盖、来源去重、阶段次数和终态已定义；物理约束/提交/恢复DG-01/02；全局关系DG-03 |
| 技术选型/ADR | DeepSeek官方API及ADR-003已认可；其余跨模块选型/长期依赖未定，须实际提案及权衡记录，不直接判已通过 |
| 可测试性/失败证据 | 006五层/八规则组/十三故障/六页面组和证据字段明确；尚无实际工具/产品命令，不宣称任何产品测试通过 |
| 返回追溯 | 保存Prompt全文/请求依据/实际返回有明确要求；缺失必要元数据判法DG-05，不把未观察到变化当无漂移 |
| 本轮修改/回退 | 本轮只新增报告/审计文件；无需产品迁移或生产回滚；源修订待确认，保留审查输入哈希 |

官方核实（2026-10-06）：[Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)的直接读取超时，官方域检索核实Flash/Pro映射、JSON及上下文/输出能力与003当前记录一致。[Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)直接读取核实enabled/disabled、high及思考模式temperature不生效等，003显式参数方向符合。[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)直接读取失败后官方域检索核实max_tokens范围、输入/输出共同受上下文限制和响应model/fingerprint结构。未改配置、引用来源价目不作永久价格承诺，未调用API或证明SDK兼容/实际质量。证据与失败限制见`.codex/task007-review-verification.md`。

## 9. RDD Gate复核与本次设计门禁分别判断

RDD只回答想法/需求/任务化/能否写Spec，不回答全部工程设计已准备。最新FRESH-01～04关闭是旧RDD文档发现，不能直接关闭本次DG发现。

| 门禁条件（package原定义） | 当前证据 | 结论及影响 |
|---|---|---|
| Gate 0：一句话目标用户/核心场景/痛点之一 | 用户/场景地图及001定位明确 | 满足 |
| Gate 1：六维至少各一结论 | 六图3角色/9场景/11决策/15实体/13输出/21风险 | 满足 |
| Gate 1：关键未知列出 | U01～13具来源/影响/人/阶段/决定，最新子项可读 | 满足，不要求全部关闭 |
| Gate 2：每需求可拆任务包 | 50条唯一主责、24工作包 | 满足文档任务化条件 |
| Gate 2：包有输入/输出/边界/验收/依赖 | 24实际卡逐项核对，50主责、57依赖一致 | 满足；不是24产物已完成 |
| Gate 3：范围稳定 | 当前确认基线及001～006认可，无新增业务范围 | 满足既定范围条件 |
| Gate 3：不依赖大量开放问题 | U10/U12延期有承接；DG问题局部及工程准备，有明确影响 | 可继续分阶段补技术Spec；不能据此实现全部路径 |
| Gate 3：可进入产品/技术Spec | 001～006已形成，DG-01/02/05需要技术补充，DG-03单项业务确认 | 维持“限定明确范围按依赖写Spec”成熟度；不是设计门禁通过 |

**本次设计门禁：需补齐，暂不通过整体实现准备审查。** 原因是DG-01/02的共享工程基础和恢复契约未形成，DG-03/05的受影响操作仍未可判断；不是因为缺正式样本/未测性能，也不是重判RDD失败。已明确解析/评分/指标/QA资格/快照不变量可作为技术设计输入，但本轮不部分放行代码。

```text
001～006真实认可 + 50设计/验证承接 + RDD Gate成熟度
                           |
                           v
                  TASK-007发现已记录
                           |
          DG-01/02技术补充 + DG-03单项决定 + DG-05处理表
                           |
                           v
               用户确认 -> 实际修订 -> 本次复审
                           |
                           v
                  设计审查是否满足条件
                           |
                           v
                 用户另行明确开发授权
                           |
                           v
                 才按原依赖执行008～018
```

## 10. 验证证据、未审限制及复审条件

本轮本地命令：`& ./.codex/all-task-confirmation-base-check.ps1`；`& ./.codex/task007-review-check.ps1`；`git diff --check`。结果详见[本轮验证记录](../../.codex/task007-review-verification.md)和[审查检查JSON](../../.codex/task007-review-results.json)。报告完成前运行并读取结果；自动检查证明计数/链接/映射/源保护/无环，语义判断由本报告证据支持，不从布尔“全绿”推导门禁通过。

本次未核实API实响应、实际SDK/校验器、真实持久层、产品接口、Chrome页面、Prompt语义、正式50及QA全集、随机实测或性能。它们或尚无产物，或被本次明确排除；对应产品通过一律未运行/不可声明。模型官方页检索有可读内容，但直接超时限制保留；不伪造实调用。

每发现关闭需：具体用户授权/决定→实际源修订及版本→对应文件/条目和diff→逐项语义复审与新鲜结构/链接/源保护结果→更新发现及设计判断。未落实建议保持开放；部分修订只关闭有证据部分。影响其他设计/任务时指出F/D/P/U与承接，不通过修改阈值解决问题。

## 11. 待用户审阅的处理建议及当前结论

建议先审阅DG-01/02需要补齐的技术设计范围，获授权后形成具体方案，再交用户确认；DG-05可纳入该技术提案的响应处理表。DG-03每次只确认一个业务问题；DG-04只作授权后的最新承接勘误，不重写历史。以上是处理顺序建议，不是自动源修订授权，不新增工作包或依赖。

当前已完成审查范围读取、前置核实、50条及24契约追溯、依赖复核、一致性/架构/延期检查和发现记录。报告0.1待用户审查；DG-01～05全部开放，未进行源修订或复审关闭。TASK-007审查报告的交付认可与设计门禁判断分开；本报告可得出“需补齐”，不能提前写通过。设计通过后仍须用户明确授权进入开发。本轮不启动008～024，不写代码、不调用模型API、不执行产品验收。

## 12. DG-01／DG-02／DG-05技术设计补充提案（已认可，DG-03许可已由第15章补齐）

当前：第12章明确部分整体认可，DG-01/02/05已完成源同步及设计层复审关闭；DG-03/04未决。下段保留提案形成时授权记录，其待确认状态已由第14章更新。

日期：2026-10-06｜执行者：Codex。用户对“先按DG-01、DG-02、DG-05的范围补齐具体技术设计提案供确认”回复“是”。此回复授权形成本章，不是认可尚未展示的选型、接口或异常判法。第1～11章保留首次审查事实，第12章记录本轮补充。DG-01/02/05状态为**已有提案，待用户确认及源同步复审，仍开放**；DG-03/04未处理，设计结论仍需补齐。提案仅附在007唯一主要报告，不新建任务或实施代码。

### 12.1 ADR-T01：单机技术栈与模块边界（已认可）

背景：001单人首版，002版本/快照，003G/E/Q，004运行窗口及恢复，005Chrome交互，006本地验证；008～018需要同一工程基础。推荐下表方案。Python 3.13、Node 24 LTS、React 19、SQLAlchemy 2.0是建议兼容系列，不声称是所有组件最新版本。具体补丁版本须在方案认可后、008安装前核对兼容并记录到锁文件；尚无环境安装或构建证据。影响多个功能的长期依赖和数据模型权衡按ADR规范在本章留痕。

| 层 | 推荐及职责 | 依据／约束 |
|---|---|---|
| 前端 | React 19＋TypeScript＋Vite；原生fetch；详情/列表组件按005组织 | [React版本](https://react.dev/versions)、[Vite指南](https://vite.dev/guide/)；不用UI计算值替代后端权威规则 |
| 运行时 | Python 3.13系列；Node 24 LTS仅前端工具链 | [Python发行记录](https://blog.python.org/2026/08/python-3147-31315/)、[Node下载](https://nodejs.org/en/download)；Vite要求按官方兼容范围核对 |
| 后端 | FastAPI＋Uvicorn，单进程单worker；Pydantic v2处理产品API类型 | [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)、[Pydantic严格模式](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/)；后台工作归应用生命周期管理，不依赖一次HTTP请求存活 |
| 持久层 | SQLAlchemy 2.0＋Python sqlite3＋本地SQLite；Alembic记录schema版本 | [SQLite方言](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)、[Alembic迁移](https://alembic.sqlalchemy.org/en/latest/tutorial.html)；逐连接启用外键；显式事务，短写事务，HTTP等待时不持有数据库写锁 |
| 模型接入 | 官方OpenAI Python SDK的AsyncOpenAI调用已确认DeepSeek官方地址；只有010持有供应商细节 | [SDK](https://github.com/openai/openai-python)、[DeepSeek思考参数](https://api-docs.deepseek.com/guides/thinking_mode/)；max_retries=0，SDK不能隐式多发；009统一预算和退避 |
| 完整协议验证 | 标准json解析＋jsonschema Draft202012Validator＋003已有跨字段约束 | [官方验证器](https://github.com/python-jsonschema/jsonschema/blob/main/docs/validate.rst)；拒绝重复键/非标准数字；词法整数拒绝4.0、布尔和字符串，不能靠JSON Schema integer单独判定 |
| 本地验证 | pytest＋HTTPX/FastAPI测试客户端；Vitest/React Testing Library；Playwright使用实际本地Chrome | [pytest临时目录](https://pytest.org/en/stable/reference/reference.html)、[HTTPX异步](https://www.python-httpx.org/async/)、[Vitest](https://vitest.dev/guide/)、[React测试库](https://testing-library.com/docs/react-testing-library/intro/)、[Chrome channel](https://playwright.dev/docs/browsers)；单元/接口用模拟transport，无真实模型；页面工具的兼容及锁版本留008核对 |

依赖仅服务本次已定功能，不安装完整生态包。SQLite建议`journal_mode=WAL`、`synchronous=FULL`，数据目录必须本机磁盘；WAL读写约束见[SQLite WAL](https://www.sqlite.org/wal.html)。不支持同时启动多个后端对同库运行调度；启动时用既有OS文件锁库（建议filelock，版本后续核对）占用数据目录，第二实例直接报启动失败。这是防双调度的工程约束，不新增登录或业务角色。SQLite损坏/磁盘满不假装恢复成功；保持数据供诊断，不自动重建空库。

备选权衡：全TypeScript＋SQLite可少一种语言，但Python契约校验/指标及本地测试复用更直接；Django可复用ORM，却引入当前不需要的后台/认证默认面；PostgreSQL更适合多服务，但当前单机需要额外数据库服务；Redis/Celery的独立队列与本首版无排队方向不匹配。选择是推荐，非宣称备选不可行。SQLite单写者及数据库体积是限制，不承诺U10性能；遇实测瓶颈再提出实际证据，不提前切库。

```text
Chrome：005列表摘要 / 详情完整依据
                 |
              /api/v1
                 v
FastAPI路由 -> 应用服务 -> 纯规则/指标/契约验证
                 |                |
                 v                v
       SQLAlchemy + SQLite    010 DeepSeek adapter
                 ^                ^
                 |                |
       009应用生命周期调度（单任务；全任务最多3请求）
```

建议工程路径仅供后续卡使用：`backend/app/{api,services,models,db,domain,model_client}`、`backend/tests/`、`frontend/src/`、`frontend/tests/`、`tests/e2e/`；并非现在创建。依赖方向api→services→domain/db/model_client；domain不引用FastAPI、UI或SDK。009只管预算/恢复/窗口；010只做一次供应商发送及严格结果检查；011/013/016组装业务任务；012纯计算；014/015/017管各自领域。018组合页面与接口，不复制调度或规则。

### 12.2 ADR-T02：物理持久结构、类型与版本（已认可，DG-03基数已补齐）

不新增业务实体；以下是002 E01～E15的物理展开，内部执行/提交记录不对外新增业务能力。主键建议标准库UUID4字符串；原CSV案例编号仅批内唯一，不能作全库主键。文本原样保存，UTF-8 bytes保存上传原始文件；时间UTC带时区ISO 8601，UI按上海时间显示。布尔存INTEGER CHECK 0/1；计次CHECK 0～3，序号CHECK 1～3；金额不涉及本产品。引用用外键，业务标识用唯一约束。JSON字段以TEXT保存通过对应契约验证的结构；不依赖数据库JSON自动修正。

| 逻辑来源 | 建议表／必要字段及唯一键 | 生命周期、关联及条件 |
|---|---|---|
| E01/E02 | dialogue_upload(id, raw_csv BLOB, uploaded_at)；case_record(id, upload_id, csv_case_id, row_ordinal, question, original_reply, H_json)；UNIQUE(upload_id,csv_case_id) | 对话整份校验后提交；H保存按U01解释后的有序原文；重复上传形成独立身份，不合并跨上传case |
| E03/E04 | material_version(id, kind=rule/kb, raw_csv, uploaded_at)；rule_row(version_id, source_id,title,content)、kb_row同形；UNIQUE(version_id,source_id) | 上传成功一次一版本；规则/库引用分别检查kind；版本内容不可覆盖；校验失败零版本 |
| E05 | task(id, kind=ordinary/effect, phase, state, cancel_epoch, started_at, automatic_ended_at, elapsed_ms)；task_case(task_id,case_id,ordinal)；runtime_slot(id=1,task_id nullable) | task_case固定去重集合；普通≤100；无排队；slot唯一1行；人工抽检不占slot；state值见12.3 |
| E05版本绑定 | ordinary_task(task_id PK,upload_id,rule_version_id,kb_version_id)；effect_task(task_id PK,supplement_id,source_batch_id,old_kb_id,new_kb_id,rule_version_id) | 对应task类型且互斥；效果原H/规则从来源还原；新库从实际补充记录取，不能取最新资料 |
| E06 | config_snapshot(id,task_id,stage,contract_version,prompt_version,full_prompt,request_model,documented_release,parameters_json)；请求messages保存于attempt | 开始执行前固定，G/E/Q各自配置；Prompt正文由011/013/016后续任务提供，不在007编写；仅hash不足以还原输入 |
| E05/E13执行展开 | execution_item(id,task_id,case_id,stage,side,gap_key,state,attempt_count,result_id)；UNIQUE(task_id,case_id,stage,side,gap_key) | 无gap用固定空串，Q用对应gap身份；避免SQLite NULL唯一性漏洞；Q普通侧original；G仅old/new；E按类型分侧 |
| E05尝试展开 | attempt(id,item_id,ordinal,state,request_json,config_id,started_at,ended_at,response_envelope_json,raw_content,error_category,error_detail)；UNIQUE(item_id,ordinal) | 保存实际请求与响应，不保存凭据；发送不在事务内；成功/错误及counter一致更新；ordinal不可重置 |
| E07/E08/E09 | evaluation_result(item_id PK,contract_json,三分/理由,has_material_conflict,主因/次因)；gap(id,result_item_id,gap_ordinal,gap_text,snippet,reason)；UNIQUE(result_item_id,gap_ordinal)；final_error(item_id PK,category,last_attempt_id nullable仅B03本地次数0) | 同E item不能同时成功/最终异常，服务事务校验；gap归固定case及侧；派生分数/合格/指标由012计算，不重复维护可变第二份数值 |
| E13 G结果 | generation_result(item_id PK,reply) | G成功后原文固定；E输入引用对应G；G最终失败的E不创建假调用，展示“上游生成失败”派生状态，不冒充E final_failed |
| E10 | qa(id,q_item_id UNIQUE,gap_id UNIQUE,question,answer,category,review_state,revision) | Q成功才建可审核qa；answer初始空；只有pending_review/approved；人工答案绝不进入模型messages |
| E11 | export_event(id,operation_id UNIQUE,created_at,csv_bytes BLOB,byte_length,content_hash)；export_item(id,event_id,ordinal,qa_id,qa_revision,question,answer,source_case_number,category)；UNIQUE(event_id,ordinal) | 事件四字段固定列序及BOM，字节/条目同事务；历史条目不可修改；source_case_number展示CSV编号且仍保留全局case引用；原批次沿各条目来源还原，不增加跨批导出业务限制 |
| E12 | supplement(id,new_kb_id,source_batch_id,confirmed_at)；supplement_item(supplement_id,export_item_id)复合主键 | 同QA不同快照可多选；同一具体条目在同记录不重复；来源case沿快照去重；**DG-03已确认new_kb_id与effect_task.supplement_id均非全局唯一，同库多记录、同记录多独立任务** |
| E14 | sampling_run(effect_task_id PK,population_size,target_size,status)；draw(effect_task_id,draw_ordinal,case_id,kind,unusable_reason)；UNIQUE(effect_task_id,case_id)；human_mark(effect_task_id,case_id,accuracy,intent,service,revision) | 保留初抽/补抽顺序；目标ceil(N×10%)；标记nullable不等于持平；只有足额有效才人工标记；三维枚举沿004，结论按原规则派生 |
| E15 | 正式/调试资料与证据按006隔离目录及运行数据库 | 不把正式标注导入产品模型请求；019/021才准备实际文件，本轮不新增数据或标注 |
| 技术提交索引 | operation_commit(operation_id PK,kind,request_hash,result_type,result_id,committed_at) | 每次明确用户动作一个UUID；网络重传用同ID；同ID不同内容409；新用户动作用新ID，不能据此限制业务重复次数 |

每张可变业务表都有revision非负整数，更新时expected_revision必填；真实内容改变才+1，过期编辑409而非覆盖。历史材料、配置、结果、快照不提供更新API。cancel_epoch只用于丢弃跨取消回调，不是新业务状态。跨表来源一致性及成功/异常互斥由同服务事务检查，普通查询只读固定来源，禁止用当前版本替代引用。取消删除该task执行结果/尝试/messages及下游引用，仅保留任务取消记录的身份、类型、开始/取消时间；原上传资料及效果来源批次/补充记录保留。不存在合法普通已取消批次的下游QA，因为进入Q阶段后禁止取消。

SQLite外键开启与显式事务控制不能靠默认值假定，SQLAlchemy方言文档指出sqlite3事务模式差异；实现须记录实际Python/sqlite版本及配置。schema迁移由Alembic管理，后续变更先审查，不使用删库重建解决有历史数据的迁移。数据库原子提交依据[SQLite atomic commit](https://www.sqlite.org/atomiccommit.html)；这是生态机制依据，不是本产品掉电验证证据。

### 12.3 产品操作接口与状态（已认可，DG-03接口许可已补齐）

共同类型：id为UUID字符串，revision为整数≥0，time为带时区字符串；枚举采用下面机器值与004语义一一对应。JSON额外键拒绝、类型不隐式转换。所有写入请求带operation_id；更新已有内容还带expected_revision。正常返回资源id/revision/当前真实状态；创建201、相同操作重传200或原结果、任务运行202；条件冲突409、字段/CSV422、对象不存在404、本地存储不可用503。错误固定`code,message,resource_id,field_errors,commit_state`，commit_state为not_committed/unknown；模型三类错误在task detail里按003保存，不混作API重提交理由。读返回data，列表返回items；分页建议offset≥0、limit=20且1～100，按created_at及id稳定排序。列表摘要及详情字段具体内容引用005对应页面，不新增页面。

| 接口／承担任务 | 输入条件 | 输出／领域行为及验收 |
|---|---|---|
| GET /api/v1/templates/{kind}；008 | kind=dialogues/rules/knowledge | U01三模板固定列；F01/D01 |
| POST /api/v1/uploads；008 | multipart kind/file/operation_id；严格UTF-8可带BOM；kind必填 | 成功upload_id或material_version_id、行数；整份拒绝具体行列错误，无部分写入；F01～04/D01/D02 |
| GET /api/v1/uploads、/materials、/materials/{id}；008/018 | 指定kind及分页 | 列表版本摘要，详情完整原文；不自动选择最新；D02 |
| POST /api/v1/evaluation-tasks；009/011 | dialogue_upload_id、rule_version_id、kb_version_id、operation_id；非空≤100、slot空 | 原子建ordinary task及E items/配置绑定并占slot；task_id；F05/F16/D03/D04 |
| GET /api/v1/tasks、/tasks/{id}、/tasks/{id}/cases、/tasks/{id}/cases/{case_id}；012/018 | 固定task/case引用 | 列表摘要；详情H、完整三分/原因/gap/次数/最终异常/指标；未终态不报最终结论；F07～18/P01～03 |
| POST /api/v1/tasks/{id}/cancel；009 | operation_id、expected_revision；ordinary处于evaluating或effect自动阶段 | 已取消及取消时间；Q阶段409 CANCEL_NOT_ALLOWED，终态新取消409；同operation重传返回原结果；F18/D04 |
| GET /api/v1/tasks/{id}/qa、/qa/{id}；013/018 | 来源普通task及qa | 成功草稿/生成失败分开；详情证据完整；F19～21/P04 |
| PATCH /api/v1/qa/{id}；013 | question、answer、operation_id、expected_revision | 保存实际修改→pending_review；原样保存维持审核；不改分数/来源；F21/D05 |
| POST /api/v1/qa/{id}/approve；013 | operation_id、expected_revision、confirm=true；四字段完整 | approved；空答案422，无AI审核；F22/F23/P06 |
| POST /api/v1/exports；014 | selected_qa_ids非空去重、operation_id；均为005当前页面所选且当前approved/完整，expected_qa_revisions映射 | event_id及具体item_ids、download_url；历史快照新建；F23/F24/D06 |
| GET /api/v1/exports、/exports/{id}、/exports/{id}/file；014/018 | 事件id、筛选来源批次 | 时间/来源及当时内容；文件返回数据库保存的CSV字节；无新业务导出种类；P04/D06 |
| POST /api/v1/supplements；015 | new_kb_id、source_batch_id、export_item_ids、confirm=true、operation_id；全是实际采用历史快照 | supplement_id、来源case去重数；单记录关联校验明确；同库允许多补充记录，各自只引用一个原批次并独立保存来源；F25/D07/U13 |
| POST /api/v1/supplements/{id}/effect-tasks；016 | operation_id、实际补充已确认、来源非空、slot空 | 独立effect_task固定来源/旧新库/G/E配置；允许本人再次新建独立任务；同operation重传返回原任务，新的明确动作使用新operation_id；F26/F27/D08 |
| GET /api/v1/effect-tasks/{id}、/effect-tasks/{id}/sampling；016/017 | task id | 旧新结果、同范围指标、不可比原因、抽检轨迹及人工结论；F27～29/P05 |
| PATCH /api/v1/effect-tasks/{id}/sampling/{case_id}；017 | 三维改善/持平/变差、operation_id、expected_revision；已足额有效 | 保存本人标记，自动按004汇总人工结论；不以自动评分代标记；F28/F29/D09/P06 |

更精确响应DTO复用上述物理字段和005详情需求；普通case返回evaluation|null、final_error|null且互斥，质量字段仅成功有值；指标分子分母整数、原值按012计算，显示ROUND_HALF_UP两位，阈值比较原值；无数据用null加既定说明。effect case返回old/new各G/E状态及结果、comparable boolean、reasons数组；人工mark nullable。Model G/E/Q输出字段和枚举仍唯一以003为准，不在本章复制另一个schema。

任务机器状态建议running/completed/cancelled；phase建议evaluating/qa_generation/effect_automatic/done；completed只表示自动工作终态，不表示效果人工通过或无技术失败。执行项使用003 pending/running/succeeded/final_failed；G失败导致尚未创建E，以派生不可执行原因表示。QA审核仅pending_review/approved；效果结论pending/pass/fail/insufficient分别对应待确认/通过/不通过/验证失败，具体判据沿004。恢复正在执行项仍属running，不新增可手动重试状态。本地存储故障用执行反馈storage_unavailable呈现，不改模型失败类型。

### 12.4 ADR-T03：提交、取消和恢复协议（已认可）

基本规则：只有数据库COMMIT可确认产品写入成功。operation_id/result在同事务内保存；事务明确回滚返回not_committed，提交确认丢失返回unknown或网络断开。前端不能当成功、不能换operation_id自动重复动作；先GET /api/v1/operations/{operation_id}。找到提交索引返回原资源；未找到且数据库健康确认事务不存在，可使用同ID原请求重传；数据库不可读时继续未知，不伪造失败或成功。请求内容hash只辅助一致校验，完整业务原文仍按12.2保存。

| 提交点 | 同一事务包含什么 | 中断／失败恢复及终态裁决 |
|---|---|---|
| TX01 上传 | 整份已校验原文件/解析行/版本＋operation索引 | 任一失败全回滚，旧版本不变；未知提交按operation查，不能多建版本 |
| TX02 任务启动 | slot空条件更新、task、固定来源/版本/配置、初始E或G items、operation | 提交后生命周期调度扫描发现任务；通知worker失败不丢任务；忙碌409且零新任务，无排队 |
| TX03 发送准备 | item次数+1、ordinal、完整请求/配置、attempt预发送标识、item running | 计次提交失败不发送；未知提交先读ordinal/operation身份，禁止直接再增；外部发送只发生在确认提交后 |
| TX04 响应保存 | 原始有效响应记录、G/E/Q解析结果、必要gap、attempt终态、item成功或最后失败 | 本地写失败只重做同一次本地保存，不重调模型；进程内保留待保存响应，暂停此task新发送及退避重试；成功持久后恢复 |
| TX05 普通E→Q | 确认全E终态/未取消、汇总可读范围、固定eligible gaps、唯一Q items、phase切QA；无gap则完成并释放slot | 在一个写事务与取消竞争。取消先提交→不建Q；转QA先提交→取消409；重启扫描不会重评或漏gap。Q配置在转阶段前就绪，不能临时变更 |
| TX06 Q成功／普通完成 | TX04同时建立qa(gap唯一)、空答案、待审核；全部Q终态或无Q→task完成/计时结束/slot释放 | 已持久Q与qa不可二次建；最后项及释放在同事务；人工补答/审核不占运行窗口 |
| TX07 效果G→E／自动完成 | G保存成功与对应E item输入引用同事务；末项终态时固定自动结果、抽检候选/轨迹并释放slot | E重试不重调G；G失败不发E；自动完成即释放，不等人工抽检；抽检轨迹写失败不静默再抽新集合 |
| TX08 取消 | 条件核对phase/revision、cancelled/epoch+1、取消时间、清理该task工作数据、清空slot、operation结果 | worker发出/保存前查task epoch；取消提交后停止新请求/重试，迟到只丢弃；已发HTTP尽力取消但不能承诺供应商不计费；新task不复用旧item |
| TX09 人工修改/审核/补充/标记 | 校验expected_revision及已有来源、一次领域更新＋operation | 重传原ID读原提交；真实内容未变不改变QA状态；历史快照不改；不将网络错误变模型重试 |
| TX10 导出 | 核对所选QA当前approved/版本→固化4字段/排序→生成UTF-8 BOM CSV bytes→event/items/bytes及operation同事务 | 浏览器下载不在事务内。下载中断再GET同event/file返回相同bytes，不新建导出；数据库失败不出现半事件；磁盘外文件不是成功条件 |

CSV导出建议事件条目按来源批次身份、来源case原输入顺序、同case按gap序号排序，文件名`qa-{created_at_UTC_YYYYMMDDTHHmmssfffZ}-{export_event_id}.csv`，含005已认可的记录身份及时间，列顺序沿005已确认规则。这是待确认技术细节，不修改四字段或允许导出资格。数据库内保存精确字节消除工作台文件与快照双重提交；浏览器最终是否另存到用户磁盘无法由后端事务保证。界面“导出记录已生成”与下载传输状态分别如实显示，不把开始下载宣称落盘成功。完整CSV快照在数据库内不是独立报告导出功能。

发送边界特别说明：数据库与外部HTTP无法实现同一原子提交。TX03后若可证明尚未进入发送且有当前进程证据，撤销该未发送预留（attempt标为未发送技术记录、不计有效次数）；进程崩溃导致是否已发送未知时，保守保留已经持久的次数。不得以重启“推断未发”退还预算；可能少一次实际机会，不能多于三次潜在发送。已有已发送未保存仍计次规则保持。SDK/HTTP代理不能隐式重试或自动重放POST；一ordinal最多一次transport发送尝试。

启动恢复顺序：先独占数据目录→打开并核对schema/外键/事务配置→检查slot与唯一running任务→扫描items和已持久响应→先完成本地结果落表/阶段交接→对未成功且剩余额度项恢复原配置调用。succeeded绝不再调用；running且无持久响应的attempt按已发送未知处理，记CALL_ERROR恢复原因，在已有剩余额度内重试；恰3次则按最后错误最终失败。取消记录不恢复工作。离开页面不影响后端；关机启动才能扫描，非另建排队任务。

响应保存失败且数据库仍不可写时，保留running及slot，停止所有该任务新发送；仍可读时UI显示存储故障/状态未确认。建议本地写恢复每5秒尝试一次，仅检查存储并提交同一待保存动作，不发送模型、不计API次数；恢复后继续，重启按已持久数据扫描。不新增“手动重试”按钮。数据库始终故障不能承诺最终自动结束；修复运行环境后才恢复，此限制待用户认可。若内存中的有效响应在提交前随崩溃丢失，没有成功持久证据，不能声称成功不重调已被违反；按既定已发送未保存预算处理。磁盘持久成功是停止再调用的界限。

取消竞态还需实际发送门：单个应用内用同一任务锁协调“最终取消检查＋交给HTTP transport发送”与取消提交，网络等待在锁外。进入发送先于取消者属于已发请求；取消先者不得发送。slot可释放给新任务，但旧请求未真正结束仍占全局3个请求信号量；新任务可以显示运行/等待调用额度，不新增业务排队或额外取消阶段。数据库条件写/epoch复核用于丢迟到；锁只解决单进程极短竞态，不能替代持久约束。

### 12.5 DG-05：响应元数据及可比处理表（已认可并同步）

建议分开“业务内容成功”与“归因可比信息完整”。必要API响应外壳继承003 HTTP200/chat.completion/一有效choice/assistant/非空content/stop；外壳缺失或非法为CALL_ERROR，finish_reason不完整沿003 INCOMPLETE_RESULT。业务JSON失败仍按PARSE_ERROR/INCOMPLETE_RESULT处理，预算仍最多3次。模型元数据不进入G/E/Q业务JSON，不自动猜值。

| 字段/情况 | 建议阶段判定与记录 | 效果对比／重试 |
|---|---|---|
| model、system_fingerprint均为非空字符串 | 保存原返回值；model与请求别名不同不直接视作错误，要按003实际两侧/同类型配置比较 | 两侧同类型的G和E实际元数据按003比较；发现漂移仍不可比，不能靠重调成功项消除 |
| model缺失/null/空/非字符串 | 业务JSON完整仍保存阶段成功；记录METADATA_MISSING或METADATA_INVALID及具体字段，不造model | 对应effect case不可比、原因归因证据不足；不触发额外模型重试；普通E仍有有效评分 |
| system_fingerprint缺失/null/空/非字符串 | 同上；null表示未知，不能当共同null相等 | 任一相关G/E未知则effect case不可比；不以“未检测到漂移”解释充分归因；不重调成功项 |
| response id缺失/非法或created缺失/非整数 | 保存业务成功、警告及本地attempt时间；created要求正整数且排除bool | 不单独阻止可比，model/fingerprint完整仍沿003比较；不补假供应商ID或创建时间，不触发重试 |
| usage不存在或部分非法 | 缺失标未知；保留实际合法字段及原响应，非法字段记问题 | 不影响业务成功/可比，不伪造token或金额，不新增必填usage |
| 业务JSON合法且元数据警告 | 校验警告和内容成功同时保存，完整attempt追溯 | 不将警告混作Badcase或最终评测异常；模型内容成功数照原规则计；效果候选资格单独判 |

理由：返回元数据不足是不能归因，不一定是评分内容无效；不为了补指纹重复调用成功内容。2026-10-06用户对BR-06回复“接受”，确认完整评分保留、型号或运行标识缺失时不可比、不重调成功项的业务取舍。字段合法性、非法值及其他外壳细分处理仍由Codex负责技术审查，不把该答复视为全表技术认可。现有003“metadata缺失单独记录问题”方向继续；实际同步003第6/8章、0044.5、006 X12及010/016输入、复审关闭尚未进行。普通评分保留不降低正式语义标准，效果足额抽检条件不降低；无效候选仍沿004补抽，数量不足验证失败。检测model/fingerprint漂移的既有决定不重开；U12实际样本仍由019/021/022承接。

此前直接读取失败保留历史证据；2026-10-06本次重新直接读取官方Chat Completions成功，核对响应结构。仍无API实际调用证据；相关建议是本地处理策略而非供应商保证。支持协议以[DeepSeek官方接口](https://api-docs.deepseek.com/api/create-chat-completion/)及已认可003为准，具体型号/参数不更改。

### 12.6 工程命令、测试隔离及实现交接（均为设计建议）

建议运行配置：DEEPSEEK_API_KEY仅传010客户端，不写配置快照；APP_DATA_DIR为本地工作目录，APP_DB_PATH指向该目录SQLite，APP_ENV区分产品/独立调试/正式验收；不提供用户调温功能。配置检查在发送前完成，缺已确认Prompt/版本时不发请求、不计次。静态页面构建后由FastAPI同源提供；开发Vite代理/api到后端，页面轮询运行摘要建议每2秒、离页停止轮询但任务继续。建议监听127.0.0.1:8000，一台本机演示；未提出公开服务器运行方案，不声称已部署。

下列命令是拟建立的工程契约，现在未安装、未执行，不声明通过：backend内`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`；`python -m pytest`；`python -m alembic upgrade head`；frontend内`npm run dev`、`npm run build`、`npm run test`；项目本地页面验证`npx playwright test`。具体cwd及脚本内容在008建立并留证，启动产品模式不用热重载或多worker。停止按Ctrl+C，停止新发送、尝试保存已取得响应；超出退出等待则保留持久次数供下次扫描，不标取消。性能elapsed_ms建议累计各自动运行片段单调时钟时长，另存开始/自动结束UTC；中断批不冒充023固定完整自动性能样本，U10聚合判法仍延期。

所有确定性测试用临时SQLite、模拟transport、注入clock/随机源/提交失败点；不访问用户产品库。独立调试与正式验收使用不同APP_DATA_DIR/数据库及006目录，不跨复制标注或调试case。019及021才建立实际集合；任务内部提供依赖注入而非自研通用测试框架。测试结果与截图/API日志等证据落006约定，实际Chrome版本后续记录。Playwright仅替本人点击以验证页面规则，QA语义/人工标注/效果判断仍本人负责。

| 后续承接 | 本章提供的设计输入 | 后续才产生的验证证据 |
|---|---|---|
| 008 | 运行时/锁依赖/版本表/CSV事务TX01；F01～04/D01/D02 | 安装锁版本、迁移、启动、整份拒绝本地测试 |
| 009 | slot、执行项、attempt、TX02～08、发送门/恢复；F16～18/D04/P03 | 计次、未知发送、取消/崩溃竞争及全局并发≤3的本地故障注入 |
| 010 | SDK max_retries=0、一次发送、严格JSON、12.5处理表；F12/D03/D08/U12 | 三类技术错误及元数据合法/缺失/非法/漂移测试，无真实API必需 |
| 011～013 | 固定输入/配置、E→Q原子交接、gap/qa、012派生值；F05～23/P01～04 | 完整Prompt及模块实现、本地逻辑测试，语义效果留019/022 |
| 014 | bytes与export_item同事务、操作查询、重下载；F23/F24/D06 | 一致四字段/BOM/字节、编辑历史及下载中断测试 |
| 015～017 | 来源FK/多快照/对比结果/抽检事务；F25～29/D07～09/P05/P06 | DG-03两项已确认，接口许可及关系见第15章；状态/足额/人工标记验证 |
| 018 | API DTO、409/503/unknown呈现、同源页面；F30～32/P01～07 | 005各状态的页面实现及本地验证，不凭本章证明通过 |
| 019～024 | 延续006分层与隔离、U10/U12延期 | 调试/正式固定、真实模型/业务/Chrome证据、三批性能及最终Review |

计划复测设计覆盖（未执行产品测试）：TX03计次失败0发送；成功COMMIT但响应丢失按operation找回；E结果成功→Q创建中断原子恢复；Q成功不建重复草稿；取消先/QA阶段先两种竞态；3个迟到请求不突破全局并发；导出快照与bytes一致且重下载不新建；元数据缺失/非法不造值、不重调成功且效果不可比。各项具体断言承接006 X04/X05/X07/X08/X12/X13，不降低50项已有标准。

### 12.7 本轮提案复核与下一门槛

补充工程约束：进程独占建议复用[filelock官方机制](https://py-filelock.readthedocs.io/en/stable/)，不使用锁文件存在与否冒充活进程；对操作未知提交保留原operation_id及内容摘要，不保留凭据。取消后启动/取消动作的幂等定位归取消任务记录，不残留模型内容、结果或有效下游；旧启动操作重传返回已取消原任务，不重新建任务。明确未发送且尚未交给transport的预留撤销时，同一未发送ordinal允许重新预留更新，不新增已发送尝试；发送未知则ordinal不得复用。SDK等待配置之外用应用300秒请求等待截止点，连接取消清理可稍晚完成且未结束请求仍占全局并发名额，不把截止点当作供应商必定停止计算的保证；避免各HTTP阶段分别300秒扩大已认可等待边界；退避仍2/5秒及Retry-After优先，按003不变。

架构自审结论：推荐方案复用生态；模块职责和依赖单向；业务15实体由物理表承接；单slot/全局3信号量、成功与计次、不可变历史、人工边界有明确处理；SQLite单写者、未知发送及不可读存储限制已说明。未安装依赖、验证SDK适配/数据库事务/迁移/Chrome，因此不能宣称可运行。DG-03基数/重复任务业务问题不能被operation幂等性替代，相关接口认可仍阻断；DG-04源状态提示仍开放。

待确认提案分组：T01技术栈/依赖/工程与接口；T02物理模型及状态映射；T03原子提交、SQLite内保存CSV bytes、操作查询/取消/存储恢复边界；T05元数据处理及不可比门槛。用户认可这些具体方案后，才同步受影响003/004/005/006及项目技术索引，核对实际diff再复审DG-01/02/05；不能只凭本章文字关闭。所有更新维持50验收、57依赖和U10/U12正式事项。本次提供待审提案，不启动008～024，也不准备样本/调用模型/写产品代码。

## 13. 第12章业务负责人复核说明（先整体展示，再逐项讨论）

日期：2026-10-06｜执行者：Codex｜对应TASK-007，S3。用户要求先解释使用、费用、维护与证据，再逐项讨论业务取舍。**技术提案整体仍未认可，所有发现仍开放；BR-01/03/04/05/06的业务取舍已分别接受。** 阅读本章或回答一项，不构成其余项确认、源契约修订或开发授权。第12章是工程细节；本章说明它对本人实际使用意味着什么。技术正确性、依赖兼容、数据库/接口设计和实际验证由Codex负责。业务负责人决定接受哪些使用后果，不承担技术审核责任。

### 13.1 整体流程、费用和确认范围

```text
在本人电脑启动工作台 -> Chrome打开页面
    -> 上传模拟CSV -> 选择版本 -> 启动评测
    -> 查看结果 -> 人工补答/审核 -> 下载QA文件
    -> 在外部实际补库 -> 上传新版并选择历史快照
    -> 旧新效果验证 -> 本人足额抽检及确认

故障旁路：状态未确认 -> 查询原动作是否保存 -> 恢复原工作
                    不通过再次点击制造新的模型调用
```

推荐方案不增加登录、自动补库、AI审核、手动模型重试或正式样本准备。你仍负责资料有效、答案正确、QA通过、实际补充和人工效果判断。正常页面与操作沿005，技术核对与本地自动验证由Codex负责。

费用分三类：本机存储/运行消耗；实际DeepSeek调用；开发维护时间。首版本机方案不要求购买托管数据库或另租云服务器，但不意味着总费用为零；代码依赖并不自动带来付费托管服务，具体依赖许可证与版本在实现前由Codex核对。若以后选择服务器，机器/托管费用另行评估。DeepSeek按输入输出token及缓存等条件计费，不能只按case数算钱；价格和条件以[官方定价](https://api-docs.deepseek.com/quick_start/pricing/)及当时账单为准。本轮已读取价格页，不编造人民币批次报价，也不换已确认模型。

沿003已有预算：普通N条最多3N次评测，加每个应生成缺失点最多3次标准问调用；效果N条最多12N次潜在调用（每条旧/新各生成、各评测，每阶段最多3次），成功即停，生成失败不再调用对应评测。它们是次数上界，不是每次都收费或实际必用次数。100条效果任务的理论上界为1200次，不代表常态费用；输入超限未发送为0次。输入越长、回复/推理越长、失败重试越多，实际费用可能越高。取消不能撤回供应商已处理的请求；不得承诺取消退款。

| 说明项 | 对应第12章 | 业务负责人要看的取舍 | 当前确认安排 |
|---|---|---|---|
| BR-01 本机启动与运行 | 12.1、12.6 | 少服务维护，接受先启动程序且电脑关机时不运行 | 已接受运行取舍（用户回复“接受”）；技术方案整体未认可 |
| BR-02 保存历史和来源 | 12.2 | 历史可查，需要磁盘空间及维护 | 历史不覆盖已确认；不重复询问既定规则 |
| BR-03 真实状态与重复提交 | 12.3、12.4 TX01/02/09 | 不确定时先查记录；过期编辑重读后再保存 | 已接受交互取舍（用户回复“接受”）；技术方案整体未认可 |
| BR-04 导出与下载分开 | 12.4 TX10 | 工作台保留原文件，可重新下载；电脑下载完成另看浏览器 | 已接受流程取舍（用户回复“接受”）；技术方案整体未认可 |
| BR-05 故障暂停与恢复 | 12.4 TX03～08、12.7 | 写不进去时暂停并占运行位置，修复后继续 | 已接受故障取舍（用户回复“接受”）；技术方案整体未认可 |
| BR-06 追溯不足的效果结果 | 12.5 | 评分可保留，但证据不足不用于有效效果比较 | 已接受缺失信息的业务判法（用户回复“接受”）；技术细则及源同步仍待审 |
| BR-07 本地检查和实际验收 | 12.6 | 自动检查不替人工业务判断；真实模型验证仍有调用费用 | 原分工及延期已确认；不重问 |
| BR-08 逐项决定及门禁复审 | 12.7 | 单项答复只记录该项，不自动开发 | 按本次明确要求执行，不另求授权 |

### BR-01 本机启动与运行

1. **解决什么问题：**让首版在一台电脑上完整运行，避免为单人演示维护额外数据库服务器和任务队列。React负责页面，FastAPI负责业务处理，SQLite保存数据；这些名称由Codex负责选型和适配。
2. **对使用、费用和维护的影响：**你先启动工作台，再用本机Chrome打开页面。关网页不等于停程序；电脑关机或程序停止时任务不能继续，重启程序后按记录恢复。首版不必为了运行再购买云数据库/服务器；DeepSeek调用仍有费用。本机首次安装、依赖版本及运行说明由Codex完成；日常需启动程序、保持网络和本机可用。没有承诺已经有双击启动器。
3. **与已确认需求的关系：**符合001首版单人、本机/单台服务器模拟演示、F30/U09及004恢复边界。仅把允许范围中的“本机”作为本次推荐，不关闭未来单台服务器可能性，也不承诺本轮提供其部署方案。
4. **推荐理由、限制和替代：**服务少，便于本人演示和定位问题；SQLite适合本地应用，但一次仅一个写入者，实际性能仍需U10实测。[SQLite适用场景](https://www.sqlite.org/whentouse.html)。限制是电脑必须开机、网络必须可访问DeepSeek，不是离线模型。替代是先准备一台常开服务器，能脱离本人电脑持续运行，但多出部署、机器和维护成本；另一语言实现不必交你判断，Codex按适配证据负责技术选择。
5. **已有证据与实现后验证：**已有001/005范围、官方生态支持说明及第12章架构审查。未有安装/启动证据；后续008核对锁版本，009验证恢复，018/022验证Windows Chrome，023实测速度。官方支持不是整套已兼容证明。
6. **具体需要确认：**是否接受首版先以本人电脑本机运行，先启动程序再使用，关机期间不执行，重新启动后恢复？这仅确认运行取舍，不认可其余技术提案，也不授权开发。**单项决定已接受：2026-10-06用户明确回复“接受”。**该答复不确认具体框架、数据库或其余项，不关闭DG-01。

### BR-02 保存历史和来源

1. **解决什么问题：**避免新知识库、当前QA或后续编辑覆盖旧依据。每个任务都能沿版本、QA、具体导出快照回到原case，解释当时为何得到该结果。
2. **对使用、费用和维护的影响：**你继续选具体版本和历史内容，不需要认识数据库表。系统保存原CSV、请求依据、结果及历史导出内容，占用磁盘会随使用增长；仅保存本地记录不额外调用DeepSeek。升级程序要处理已有数据，不可随意删库重新开始。迁移/容量诊断由Codex负责；数据被手动删除或硬盘损坏不能保证仍可找回。当前没有新增自动备份、自动清理或保留天数功能。
3. **与已确认需求的关系：**承接002 E01～E14、D01～D09、004历史不可覆盖、005同QA多个具体快照可选、U13。QA答案仍由你填写，且不得放进模型输入；重复效果任务次数和新库关联记录数仍待DG-03，不会通过技术表结构代定。
4. **推荐理由、限制和替代：**用一个数据库保存明确关系，减少依赖页面缓存或文件名猜来源。限制是本机数据增长及数据迁移成本。分散保存CSV/JSON也是候选，但版本关系、恢复一致性和查错更复杂；只保留最新内容会违反已确认追溯要求，不作为当前可选替代。任何自动删历史方案需新的明确决定。
5. **已有证据与实现后验证：**业务证据来自002/004/005；官方支持关系约束及文本/原始字节保存，参见[SQLite数据类型](https://www.sqlite.org/datatype3.html)。真实外键、错版本阻断、旧快照不变及升级保留需008/014/015/020验证；现在没有历史恢复或硬盘故障验证。
6. **具体需要确认：**历史不覆盖和完整追溯已确认，不重新问你是否要这些能力。当前新增维护后果是保存原文件/请求依据/导出字节会持续占空间；本轮只说明，不推定你接受新增清理或备份功能。若磁盘成本成为实际顾虑，再基于真实体积提出单项方案。

### BR-03 真实状态与重复提交

1. **解决什么问题：**点了保存/启动却断网时，避免界面说成功但数据没保存，也避免再点一次创建重复任务。刷新后显示工作台已保存的真实状态。
2. **对使用、费用和维护的影响：**状态未知时页面先查询原动作，不直接报成功，也不提示再开一个任务。旧页面正在编辑的QA若已被另一页面更新，保存会要求重读内容再处理，不直接覆盖。网络重传同一次启动不应多花一批模型费用；重新主动发起另一合法任务仍是另一动作。需维护动作记录与错误呈现，但无需你操作接口编号。
3. **与已确认需求的关系：**符合005提交读回、004不丢人工内容、F16/D04；不增加业务排队、手动模型重试或自动审核。一次动作因网络重传而重复，与用户是否允许再次效果验证是两个问题；后者仍待DG-03。
4. **推荐理由、限制和替代：**先查实际保存结果，减少误成功和重复工作。限制是数据库不可读时无法立即给确定结论，需要等待故障恢复；过期编辑不能自动合并。替代为收到网络错误后盲目重建任务，会增加重复调用风险；假报成功或静默覆盖不符合既定保存要求。更复杂自动合并需额外设计，目前不推荐。
5. **已有证据与实现后验证：**保存一致性是已确认规则，数据库事务机制有[官方说明](https://www.sqlite.org/atomiccommit.html)。本产品的同动作重传、已保存但反馈丢失、过期编辑及恢复读回应由009/013/018/020注入故障验证，现在没有实际验证。
6. **具体需要确认：**是否接受“结果未知先查原记录；已有内容变化时先重读再保存”的使用反馈？这不是让你选择接口或错误码；也不改变本人可取消的阶段。**单项决定已接受：2026-10-06用户明确回复“接受”。**只确认上述使用反馈，技术实现及整套提案仍待审，不关闭DG或授权开发。

### BR-04 导出记录与电脑下载分开

1. **解决什么问题：**防止下载文件与历史快照不是同一版本。工作台同时保存当时四字段及完整CSV原文件，重下载同一导出记录得到同样内容。
2. **对使用、费用和维护的影响：**你仍勾选已通过QA并下载CSV。工作台可以确认“导出记录已保存”，浏览器负责显示文件下载是否完成。下载中断后可再次下载同记录；不会重新生成标准问或调用模型，通常只增加本地读取。原文件长期保存会占磁盘；文件名建议带导出时间及记录编号，主要用于辨认历史，精确格式由Codex处理。
3. **与已确认需求的关系：**保持F23/F24/D06、005四列顺序、UTF-8 BOM、重复导出与历史不可覆盖。仅改变保存位置及真实反馈，不增加独立报告导出，也不把下载等同实际补库。
4. **推荐理由、限制和替代：**文件与快照在同次保存中完成，少一个本地文件夹与数据库同步点。限制是数据库变大；后端不能确认你是否最终把文件存到指定磁盘位置。另存文件夹也可实现，但必须额外处理文件写成功/记录写失败的恢复。只重新拼装当前QA的文件会破坏历史，不作为替代。
5. **已有证据与实现后验证：**SQLite支持原始字节及事务，005已确认格式。需014/020验证实际CSV字节、BOM、四字段、历史修改和重复下载；018/022验证浏览器中断反馈。现在没有文件下载或数据库写入实测。
6. **具体需要确认：**是否接受“先保存固定导出记录，再下载该原文件；下载中断可从同一记录重新下载”的流程及两种状态反馈？不要求你判断文件如何进数据库。**单项决定已接受：2026-10-06用户明确回复“接受”。**仅确认该流程及反馈，技术实现仍待审和实际验证，不关闭DG或授权开发。

### BR-05 存储故障暂停与重启恢复

1. **解决什么问题：**磁盘满、保存失败或程序突然停止时，避免把丢失记录当成功，也避免重做已保存成功项。取消与进入QA生成相撞时，必须按先完成的真实动作处理。
2. **对使用、费用和维护的影响：**推荐写入故障时暂停当前自动任务，保留它的运行位置；故障解除后继续。这段时间不能新开自动任务，不能强行宣布完成。只重试本地保存不增加模型费用；已发出且尚未保存的请求若随崩溃丢失，仍占已有预算，恢复时可能在剩余额度内另发请求并产生费用。不能承诺零重复费用或断电零损失。磁盘满等环境问题需先修复；由Codex定位，必要时本人按明确操作腾出空间/重启，不新增手动模型重试按钮。
3. **与已确认需求的关系：**保留F16～18/D04/U06：先保存计次，成功持久后不重调，已发未保存仍计次，最多三次，QA阶段不可取消，效果自动阶段终态立即释放窗口。取消整体作废已确认；已发出的供应商请求可能仍处理和计费，不是取消后的新请求。输入超限未发送的B03零次失败例外继续成立。
4. **推荐理由、限制和替代：**暂停保护真实进度并阻止继续花调用费用，数据库恢复后接着走。限制是磁盘始终故障时任务可能持续暂停；若不清楚某请求是否发出，保守计一次可能少一次实际机会。另一方案是本地写失败立即结束任务并释放位置，但须重新定义无可信结果的终态和后续恢复，会改变当前可恢复使用行为，不能自动采用。丢弃故障并继续调用不推荐。关闭再开程序也不是保证故障消失。
5. **已有证据与实现后验证：**003/004预算及取消明确；[SDK官方说明](https://github.com/openai/openai-python)允许关闭默认自动重试；SQLite [WAL/FULL](https://www.sqlite.org/wal.html)支持持久提交机制。实际存储失败、恢复、取消竞态、迟到响应和三请求上限必须由009/020验证；官方机制不能证明本产品正确，也不能证明硬盘损坏可恢复。
6. **具体需要确认：**是否接受“写入故障期间保留当前任务、暂停新调用并占用运行位置，修复后恢复”的新增故障取舍？不重新确认已定三次预算或取消规则。本地检查间隔建议5秒属Codex技术细节，不另让你选择。**单项决定已接受：2026-10-06用户明确回复“接受”。**仅确认此故障处理后果，技术实现及整套提案仍待审，不关闭DG或授权开发。

### BR-06 追溯信息不足时的效果判断

1. **解决什么问题：**模型给出合法评分，却没给完整返回型号或后端指纹时，无法确认旧新比较的技术依据是否一致。后端指纹是供应商提供的运行标识，不是你的业务资料版本。
2. **对使用、费用和维护的影响：**建议保留完整合法评分，普通评测仍正常统计；效果对比标出“追溯信息不足，不可比”，不拿它证明改善。它可能导致随机抽检需补抽，仍不足时本次验证失败。为了补指纹不再重调成功项，不额外花该项模型费用。以后若另做合法新效果任务，需要独立授权/既定DG-03规则，且可能另计费，系统不自动替你重开。
3. **与已确认需求的关系：**沿003缺metadata记问题、004漂移不可比及成功不重调，保持F12/F27/D08/P05/U12。**型号或指纹缺失也不可比的业务取舍已接受；非法值与外壳细分技术处理仍待Codex审查及源同步。** 不把该警告冒充Badcase或最终评测异常，不降低足额抽检或模型语义验收标准；缺usage仍标未知，不假造费用。
4. **推荐理由、限制和替代：**评分是否完整与能否归因分开，既留住有效内容又不过度解释效果。限制是供应商若经常漏指纹，可比样本会减少，即使看起来回复不错仍不能判有效改善。替代为整个阶段按技术失败重试，会增加费用且混淆合法业务内容与追溯；另一替代是继续比较并只显示警告，但会削弱归因依据。两者都需业务取舍，不默认采用；同指纹也不能保证模型零波动。
5. **已有证据与实现后验证：**[DeepSeek接口文档](https://api-docs.deepseek.com/api/create-chat-completion/)官方域检索可见model/fingerprint字段，本轮直接页失败限制保留；SDK/JSON结构规则有资料。没有真实返回证据。010/020可先验证缺失/非法/漂移各分支，019/022才验证真实返回频率和业务表现，正式样本仍不关闭。
6. **具体需要确认：**是否接受“完整评分保留成功，但型号或指纹缺失的案例不算有效效果对比，且不重调成功项”的判法？费用与可比数量的取舍由你决定，字段合法性及检测正确性由Codex负责。**单项决定已接受：2026-10-06用户明确回复“接受”。**仅确认上述业务取舍，技术提案整体未认可、源契约未同步、DG-05未关闭，不授权开发。

### BR-07 本地检查、真实验收与费用

1. **解决什么问题：**防止代码结构检查通过却业务效果不达标，也避免把调试样本混入正式验收。程序自动通过与本人业务认可分开。
2. **对使用、费用和维护的影响：**本地规则测试大多用模拟模型，不应产生真实DeepSeek费用；后续真实调试、业务验收和性能批次会有实际调用费用。你仍须固定人工标注、判断QA语义及效果；Codex负责运行自动检查、记录问题、修复复测。无需你接CI或找外包。维护需要保留依赖版本、验证证据和相互隔离的数据目录。
3. **与已确认需求的关系：**完全沿006分工、D10/D11、019～024顺序，U10三批性能后定阈值、U12正式样本后续固定；本轮不重开已定分工或提前准备样本。
4. **推荐理由、限制和替代：**分层验证能区分程序错误与模型语义偏差。限制是模型具有波动且真实验证需时间及费用；本轮无法用文档检查证明效果。纯手点或只测代码均不足以替代已确认方案。接CI、外包和用正式集合调试不属于本项目可选替代。
5. **已有证据与实现后验证：**006方案已认可，本轮只有文档计数/来源/链接检查；pytest、Playwright等官方工具支持本地运行的证据在12.1。所有产品测试、真实模型一致率、QA语义、随机抽检与耗时仍待原验证任务，不声称通过。
6. **具体需要确认：**本项没有新增业务决定，不再询问你是否同意已认可的验证分工。实际真实调用规模/条件与测后性能阈值到对应任务按约定确认，本轮不给未测费用总额或性能承诺。

### BR-08 决定顺序与技术责任

1. **解决什么问题：**避免你一句“是”被扩展成整套工程方案认可、设计门禁通过或开发授权。
2. **对使用、费用和维护的影响：**本轮只读说明和讨论取舍，不产生模型费用，不需要你安装工具。Codex记录每一项原话、影响范围及待确认项；整体评审有额外文档维护，但减少以后误改业务边界。
3. **与已确认需求的关系：**遵守007“发现→本人确认→实际修订→复审”的流程，计划、产物、门禁、开发授权和产品验收分别记录。DG-03/04仍开放，U10/U12仍按约定延期。
4. **推荐理由、限制和替代：**逐项确认使用后果，技术正确性由Codex审核及验证，不要求本人猜技术名词。限制是需要多个明确的小决定。整章一次性确认虽然快，但你本次已要求逐项讨论，不再用打包认可问题。
5. **已有证据与实现后验证：**007卡、用户本轮请求和第12章现状可核实。BR-01/03/04/05/06均已有用户“接受”单项证据，技术方案整体仍草案。源同步与技术复审尚未进行，不能将业务取舍接受当成发现已关闭；实施后实际验证仍归原任务。
6. **具体需要确认：**本轮确认顺序为BR-01→BR-03→BR-04→BR-05→BR-06，每次只问一项；BR-02/07只说明已定要求及后果，不重复询问。BR-08遵循你的明确要求，无额外确认。每个答复只记对应业务取舍；是否达到设计审查条件由Codex依实际修订/检查判断，开发仍等你单独明确授权。

### 13.2 技术核对责任、证据及实施限制

本轮依据package架构质量规范核对模块、接口、生命周期、依赖和可测试性。技术结论：推荐方向有官方生态机制支持；整体安装兼容、接口实现、持久提交及恢复并无产品证据，保持待实现验证。业务负责人接受使用后果，不能替代这些技术证据。第12章草案所有版本及工具参数由Codex负责核对，不交本人凭技术背景判断。

| 本轮技术核对 | 已有资料／实际结论 | 仍须实现验证或澄清 |
|---|---|---|
| SQLite单机、本地文件/WAL、单写者 | 官方适用场景/WAL/数据类型及atomiccommit说明与单机方向相符 | 当前Windows实际版本、外键及事务配置、故障注入、实际容量/速度；不能直接复制运行中的数据库主文件宣称完整保存，WAL还可能有未合并内容，具体维护由Codex给正确步骤，不新增备份产品功能 |
| SDK调用及三次预算 | 官方SDK支持max_retries=0，默认自动重试必须关闭 | HTTP请求总等待、一次ordinal一次transport、实际DeepSeek适配与原始响应保留；不是选SDK就自动满足003 |
| 模型业务JSON与metadata分离 | 003严格JSON完整性已确认，metadata判法是本次待审部分 | 实际SDK不要先丢失原外壳；合法内容/警告/不可比三者正确保存和呈现 |
| B03零次失败例外 | 003末尾B03已确认输入超限本地阻断，次数0直接失败 | 第12章“恰3次最终失败”只适用已经发送的可重试技术失败；final_error.last_attempt_id须允许本地阻断时null并保留未发送原因，不能伪造attempt或等三次。此为已定规则澄清，不是新取舍 |
| 普通E→Q、G→E、取消及释放 | 004固定边界；第12章事务/发送门有方案 | 取消与最后E同时发生、迟到占真实HTTP名额、Q成功结果持久、防重复以及抽检轨迹恢复均需009/020实际验证 |
| CSV原文件与快照一致 | 数据库BLOB和事务机制支持该设计方向 | 实际导出四字段及字节一致、历史保存/再下载、浏览器最终落盘不可由后端证明 |

价格页本轮读取成功；DeepSeek接口直接页本轮仍失败，官方域检索可读字段内容，不假装做过调用。只用官方来源支持技术事实；选择适合本项目与费用后果属于审查推断，区别于供应商承诺。没有证据的真实表现一律留后续验证，不要求业务负责人代验。

此前单项确认检查点（整体认可前）：第12章五项业务取舍均已分别接受：BR-01运行取舍、BR-03交互取舍、BR-04导出流程取舍、BR-05故障取舍、BR-06缺失追溯信息的效果判法。不再发送第12章确认问题。44权威输入源不改，不关闭任何DG、不降低50验收、不变57依赖，不将技术提案整体记认可或启动任何开发/产品测试/模型调用。DG-03重复效果任务/补充记录基数及DG-04承接状态问题仍保持原未决记录，不在本次单项答复中自动解决。


## 14. 五项汇总认可、源同步与设计复审（最新记录）

日期：2026-10-06｜执行者：Codex｜档位：S3。用户明确表示“五项业务取舍已确认”，并授权核对没有遗漏后汇总整体提案认可、同步源设计及复审DG-01、DG-02、DG-05；要求DG-03、DG-04保持未决，并明确不授权开发。第1～13章中的待确认/未同步/仍开放文字是历史检查点；当前结论以本章和第3章最新状态为准。报告本身仍待用户审阅。

### 14.1 第12章是否存在额外业务决定

| 核对范围 | 判断及依据 | 决定归属 |
|---|---|---|
| 12.1/12.6本机运行 | 本机启动、关机停止、重启恢复均已在BR-01接受 | 已确认五项之一 |
| 12.3人工提交读回/冲突 | 同ID读回、过期内容不覆盖已在BR-03接受 | 已确认五项之一 |
| 12.2/12.4导出 | 先提交快照和原字节再下载，失败重新下载已在BR-04接受 | 已确认五项之一 |
| 12.4存储故障 | 暂停新调用和重试、保留窗口、修复后续行已在BR-05接受 | 已确认五项之一 |
| 12.5追溯缺失 | 合法业务结果保留成功，型号/指纹无法识别时不可比、不重调成功项已在BR-06接受 | 已确认五项之一；非法类型检测归Codex技术责任 |
| 技术栈/物理键/DTO/分页/文件名/轮询/本地保存间隔 | 为已定业务提供工程承接，不新增业务入口、次数许可或人工审核规则 | Codex核对技术正确性；并入本次整体认可 |
| 历史独立/人工补答审核/真实补库/抽检/数据集隔离 | BR-02/07说明既定规则，50条标准及U项未改变 | 已有确认，不重新询问 |
| 12.2/12.3全局补充和再次效果任务 | 已显式留给DG-03；接口基数及许可不能假定已定 | 本次认可明确排除，继续未决 |

结论：未发现五项之外新增且尚未告知的业务取舍。DG-03是已列明的独立未决事项，不以整体认可暗中确定。技术细节由Codex承担审查责任，不要求业务负责人判断库API类型。

### 14.2 技术依据复核及完整限制

本轮官方资料复核已完成设计层审查。核对[SQLite WAL](https://www.sqlite.org/wal.html)、[原子提交](https://www.sqlite.org/atomiccommit.html)、[SQLAlchemy SQLite](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)、[SDK重试和响应](https://github.com/openai/openai-python)、[FastAPI生命周期](https://fastapi.tiangolo.com/advanced/events/)、[Python取消与超时](https://docs.python.org/3.13/library/asyncio-task.html)和[DeepSeek响应结构](https://api-docs.deepseek.com/api/create-chat-completion/)。官方机制支持设计方向，不能证明本产品已实现或测试通过。

- SQLite一次一个写者；WAL只用本机磁盘。FULL原子性不保证损坏硬盘可恢复，也不提供本项目自动备份承诺。单worker与OS锁阻止第二实例调度，锁文件存在不是运行证据。
- Python sqlite3事务和外键不能依赖默认值。使用显式非legacy事务配置（Python3.13 autocommit=False）；开启外键按官方方言要求处理连接事务模式。每个事务独立Session、及时结束，HTTP等待不持有事务；安装时核对实际SQLite版本。SQLAlchemy 2.0是所选维护系列，不声称最新主系列，补丁及全依赖兼容在008安装前核对锁定。
- SDK默认自动重试必须关闭；读取原始响应后执行003完整校验，不能依赖SDK类型提示保证供应商字段合法。可使用官方with_streaming_response读取原始响应体，API参数仍stream=False，二者不是同一含义。
- **本轮新增澄清的技术限制：300秒是请求等待截止点，连接取消清理可能稍后完成。**未结束请求仍占全局3名额；不能靠提前释放掩盖超过并发限制。已发送外部请求可能继续计算并收费。该澄清不降低等待标准，不新增提醒或重试次数。
- 未知是否发送的尝试保守占预算；可能减少可成功的机会。仅内存响应在崩溃时可能丢失，不能保证零损失；已持久成功不重调。存储故障占窗口，本机修复前不能启动另一自动任务。
- 固化CSV原字节增加本机空间，下载事件提交不证明浏览器文件已保存。模型元数据不足可能减少可比候选，补抽不足仍失败；别名一致及temperature=0不保证无波动。
- 未安装或锁依赖、验证SDK适配、迁移/事务/文件锁、真实Chrome、响应频率和性能；这些必须实现后由本地验证完成。U10阈值及U12正式50条和逐条预期保持开放。没有实模型调用、实际数据集、产品测试或性能证据。

除上述已补充澄清，未发现应告知却遗漏的设计限制；这不是对未来实现行为的保证。适用架构Review核对模块单向、生态复用、15实体承接、原子提交、可测试边界及人工职责。无新需求，跳过RDD重做/Intake；无产品实现，跳过构建、产品测试、性能和真实模型验收；不启动子agent。

### 14.3 整体提案认可记录

| 取舍 | 用户已有决定 | 本次汇总承接 |
|---|---|---|
| BR-01 | 接受 | 本人电脑运行，先启动，关机停止，重启恢复 |
| BR-03 | 接受 | 提交未知按同动作读回，过期编辑先读最新内容 |
| BR-04 | 接受 | 先保存事件/快照/CSV字节再下载，失败可重新下载历史事件 |
| BR-05 | 接受 | 存储故障暂停新调用/重试、保留窗口，修复后恢复 |
| BR-06 | 接受 | 合法结果成功，型号/指纹不足使效果不可比，不重调成功项 |

上述五项与第12章明确技术承接汇总为**整体提案已认可**，依据是用户本次明确的条件授权及14.1/14.2无额外未告知取舍的核对结果。不是仅凭五个单项答复推定技术认可。DG-03两项业务规则及相关接口最终许可不在认可范围；DG-04历史整理未关闭。报告待审、门禁未通过、开发未授权、产品未验收分别保留。

### 14.4 实际源同步及检查

同步[data-dictionary](../02_design/data-dictionary.md)TASK-007认可技术承接、[model-contract](../02_design/model-contract.md)第6/8章及TASK-007补充、[behavior-spec](../02_design/behavior-spec.md)TASK-007补充、[ui-spec](../02_design/ui-spec.md)TASK-007补充、[verification-plan](../02_design/verification-plan.md)X04/X12/X13及TASK-007补充、[PROJECT_CONTEXT](../../PROJECT_CONTEXT.md)技术索引与最新阶段提示。原50条条目、阈值、57依赖及人工分工不变；没有批量改历史为已执行。

本轮变更白名单为上述6个源文件。首次44源哈希证据保留；另38个源保护检查、全50追溯、24卡、57依赖及本地链接适用检查已新鲜执行通过，结果记录于[同步复审验证](../../.codex/task007-sync-verification.md)。未来测试预期详见006补充表，当前不运行产品验证。

### 14.5 DG-01、DG-02、DG-05复审

| 发现 | 已形成并实际同步的关闭证据 | 设计层复审状态与边界 |
|---|---|---|
| DG-01 | 12.1 ADR-T01技术栈/路径、12.2 ADR-T02物理结构、12.3接口/状态；002技术承接及PROJECT第5章已同步；008～018输入有统一认可技术依据 | 已关闭（设计文档层）；本轮文档检查通过；DG-03影响的补充/重复效果许可继续排除，实际兼容性实现后验证 |
| DG-02 | 12.4 ADR-T03十个提交点；003持久/取消、004恢复/交接、005读回/导出、006故障矩阵已同步，失败/恢复预期可构造 | 已关闭（设计文档层）；本轮文档检查通过；没有声称真实事务或恢复测试已通过 |
| DG-05 | BR-06已接受；12.5合法/缺失/非法/漂移处理表、003成功/可比规定、004行为、005反馈、006 X12预期已同步 | 已关闭（设计文档层）；本轮文档检查通过；不靠成功项重调，实际供应商返回频率待验证 |

### 14.6 DG-03、DG-04继续未决，具体需要解决什么

**DG-03（P2，业务规则缺口）：**第一，决定同一补充记录是否允许再次建立独立效果任务，以及多份历史/人工待确认结果怎样定位；这是新任务许可，不是原任务重试。第二，决定同一新知识库版本可对应一个还是多个补充确认记录，以及来源合并或分别保留的规则。两个问题必须分开复述和询问；本轮不询问或代定。关闭需用户逐项决定，再同步002/004/005/006及015/016接口，复审历史追溯和重复操作预期。影响015/016及018相关入口，不能用operation幂等性替代次数规则；原同QA多个具体历史快照可选仍已定。

**DG-04（P2，非阻塞文档整理）：**001第64行及8.1/8.2、002旧字段阶段提示、007任务卡FRESH-03旧记录及总表早期确认记录仍需统一当前承接提示，区分历史检查点与最新状态。本轮必要技术索引同步不等于完成全部历史勘误，故继续开放。关闭需限定勘误范围、保留历史原文，补最新003/004/005/006/007的定位并执行一致性检查；不重新打开已认可U12或RDD FRESH-03，不改50标准或57依赖。它不要求新增业务功能或变更已有取舍。

### 14.7 最新整体结论

本次设计门禁：需补齐。DG-03未关闭，暂不具备整体进入TASK-008～018实现的条件；DG-04继续作为非阻塞整理项。DG-01/02/05已按认可提案、实际源同步和本轮新鲜文档检查关闭（设计文档层），不表示产品实现已验证。RDD Gate原结论不替代本次设计门禁；U10/U12延期及正式验收仍保留。即使以后设计审查通过，仍等待用户明确授权开发。本次不启动008或任何后续任务。

## 15. DG-03逐项业务确认记录

日期：2026-10-06｜执行者：Codex。用户授权开始DG-03逐项确认，本节更新第14章两项未决的进度，不构成开发授权。

### DG-03-A：同一补充记录再次发起独立效果任务（已确认）

用户对“允许手动再次发起，每次独立保存结果和人工结论”的方案回复“是”。决定：允许本人为同一补充记录手动创建新的独立效果任务；每次固定该记录的来源case、旧新知识库及已确认配置，重新生成旧新回复并评测，可能产生新的模型费用。每次结果、抽检轨迹及人工结论分别保存，不覆盖历史；前次人工抽检可继续待确认。新自动任务须运行窗口空闲，无排队；系统不自动重开，不借新任务重调旧任务的成功项目。操作重传仍返回同一任务，不当成新的业务发起。

关联：F16/F26～F29、D07～D09、P05/P06、U06/U12/U13；002 E12/E13、004效果行为、005补充/效果入口、006验证及015/016接口需在第二项决定后统一同步复审。DG-03-B“同一新知识库可对应多少补充记录及来源如何保存”仍待确认，DG-03整体保持开放；DG-04不变。


### DG-03-B：同一新知识库多条补充记录（已确认）

用户对“同一新知识库可关联多条补充记录，按原批次分别保存和验证”回复“是”。决定：同一new_kb_id可关联多条独立补充记录，每条仅一个source_batch_id，保存本人实际采用的历史快照及去重case；不自动合并来源。不要求不同记录必须来自不同批次，也不额外设置未提出的记录数限制。效果从具体记录发起，分别使用对应原批次旧库/规则/上下文与已选新库；保存关联不调用模型，各次效果任务按实际调用产生费用。结合DG-03-A，各记录可有多份独立效果任务、抽检和人工结论，历史不覆盖。

### 15.1 关系和接口定稿承接

关系为new_kb 1→N supplement，每个supplement属于一个原批次；supplement 1→N effect_task。允许多个关联不等于自动创建任务。supplement.new_kb_id及effect_task.supplement_id不设全局唯一；单条记录内export_item去重、case去重和来源一致校验保持。每个effect_task使用独立task_id、配置快照、执行项及三次阶段预算；原任务历史和预算不修改。

POST /api/v1/supplements允许给已有新库建立新的独立补充记录，各次operation_id对应明确动作；source_batch_id仅一个，export_item_ids均须归属该原批次且实际采用已确认。POST /api/v1/supplements/{id}/effect-tasks允许手动再次发起，前置为记录已确认、有来源、运行窗口空；真正新动作新operation_id，网络重传原ID原内容返回原task_id。旧人工待确认不阻塞新自动任务，保存和查询必须定位指定task_id，不默认覆盖旧结果。

### 15.2 实际同步、验证设计和复审

已同步002 E12/E13及物理关系、003任务预算/取消范围、004触发与独立状态、005历史定位与入口反馈、006多记录/多任务/重传/历史验证方案及PROJECT最新索引；未修改RDD阈值、任务卡、总表、依赖图或DG-04历史勘误范围。涉及F16/F25～F29、D07～D09、P04～P06及U06/U12/U13。故障、取消及恢复限本次task，不影响兄弟任务；不启动真实产品测试、模型调用或样本准备。

DG-03复审：两项用户决定均已明确，源和接口许可已实际同步，验证预期可构造；本轮新鲜文档检查通过，**DG-03已关闭（设计文档层）**。原第14章的DG-03未决及门禁需补齐结论保留为当时检查点，由本段更新。DG-04仍非阻塞开放，旧文字按历史语境保留，不重开已定事项。报告待审，开发未授权；U10及U12实际验收事项保持开放。


### 15.3 最新设计门禁及授权边界

DG-01、DG-02、DG-03、DG-05均已关闭（设计文档层），目前没有已知阻塞设计问题，具备进入实现的设计条件。DG-04继续非阻塞开放：只剩旧源状态/承接索引整理，不要求新增业务决定。报告0.5仍待用户审阅，本结论不替代开发授权或产品验收；**开发未授权**，本次不启动TASK-008或后续任务。U10阈值、U12实际正式样本及标注仍按约定开放，适用于后续验收，不假定已验证。

新鲜本地文档检查及实际diff见[DG-03复审验证](../../.codex/task007-dg03-verification.md)。检查覆盖两项确认、源一致性、50条验收、24卡、57依赖及38源保护；产品运行、模型、语义和性能验证未执行。DG-04须另获源整理授权后处理，本次不自动推进。


## 16. DG-04旧状态与当前承接整理（本轮记录）

日期：2026-10-06（Asia/Shanghai）｜执行者：Codex｜范围：TASK-007/S3文档审查。用户要求“现在开始解决DG004未解决问题，逐项说明”，明确不授权开发；按上下文解释为DG-04，授权本项状态提示及当前引用整理，不改变业务决定或执行后续任务。

### 16.1 五项问题、修订及证据

| 项目 | 旧证据和要解决的问题 | 实际修订与当前依据 | 边界 |
|---|---|---|---|
| 04-1 范围 | 001 3.1、8.1/8.2及确认段仍说型号/协议未定、002～006未执行 | 顶部DG-04当前承接，8.1/8.2标成稿检查点，链接003契约、004 B01～B03、005/006及007技术/复审 | 历史原文保留；U10阈值及U12实际样本未关闭，50条不改 |
| 04-2 字典 | 002 E06/E07/E11、第1/4/5/7章待定字段/技术格式与现决定混读 | 顶部6行承接表逐项链接003～007及本文件DG-03确认，明确编码/列序/状态/物理关系；第7章标历史 | 不另复制schema或创造枚举/阈值，原逻辑字段含义保留 |
| 04-3 007卡 | 卡头/状态/输入/输出仍未执行/无报告；确认记录FRESH-03开放 | 更新当前执行及报告存在状态；原编卡记录完整保留并标历史；追加现授权、前置、报告待审和RDD FRESH-03已关闭证据 | 不把卡安排当报告认可；不改目标/契约/依赖，产品未验收 |
| 04-4 总表 | 顶部、007行、人工记录及历次“最新”仍显示007未执行 | 更新顶部和007状态行，人工记录标时点，追加当前承接指向007第16章及RDD Gate | 其余任务状态不改；008～024未执行；24任务/50主责/57依赖不改 |
| 04-5 入口 | AGENTS/PROJECT路径和“007以后未执行”与现报告不一致 | AGENTS主产物索引、PROJECT当前阶段/007入口/授权表补准确状态；末尾旧授权标历史 | 只更新项目事实路由，不改通用操作规则，不授权实现 |

对应F01～F32/D01～D11/P01～P07的原设计追溯继续使用第5章；本轮只纠正就绪与来源提示，不重开已定U12技术、U13、多快照或DG-03。当前RDD FRESH-03已关闭的直接证据为[RDD Gate顶部及Gate 2](../../RDD/Gate结论.md)，不改RDD源、不用RDD通过替代设计结论。

### 16.2 复审证据与状态

实际修改范围：AGENTS、PROJECT_CONTEXT、001范围、002字典、007卡、总表和本报告。原文/源哈希快照与diff及本轮检查记录见[DG-04文档验证](../../.codex/task007-dg04-verification.md)。其他源和历史认可原句受保护；读取Review及交付检查规范，不重做RDD/Intake、不重套Feature Spec、不做安全扫描或产品测试：本轮无新功能/新技术/S4范围。没有子agent、外包或CI。

DG-04已修订并完成新鲜复审：当前提示可直达实际认可源；原历史确认记录保留并标时点；任务执行、报告认可和开发授权分别记录；50条验收及57依赖保持。专项和全局本地文档检查通过，**DG-04已关闭（设计文档层）**。第14/15章的开放表述保留为当时检查点，由本章更新。报告整体待用户审阅，不写已认可。

### 16.3 最新门禁与授权边界

DG-01～05均已在设计文档层关闭，当前没有已知开放设计审查发现；本轮DG-04不改变既有业务或技术设计，不推导新的开发授权。具备进入实现的设计条件，但报告整体仍待用户审阅，开发未授权。U10具体性能阈值及U12实际正式50条/逐条预期继续开放，产品、模型API、恢复能力与性能尚未验证。本次不启动TASK-008～024，不写产品代码、不调用模型API、不准备实样本。


## 17. 整体报告认可与任务完成记录

2026-10-06｜Codex｜用户对TASK-007整体报告明确回复“认可”。报告及设计审查结论已获认可，TASK-007已完成；DG-01～05设计文档层关闭。此次仅为报告认可，不授权开发，TASK-008～024未执行。U10具体阈值及U12实际正式样本/逐条预期继续开放，产品未验收。

第1～16章中的待审文字保留对应轮次历史语境，当前认可状态以本章及报告顶部为准。设计门禁通过不等于实现授权、产品验收或真实性能达标。
