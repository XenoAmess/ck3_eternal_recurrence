# 第四集：R0241有限结算证据、R0243就绪修复与47段正文来源

machine_id: `desktop-3fevhd2-1c74096080`。本轮来源整理于2026-10-22 UTC晚间（北京时间2026-10-23）；状态观察以各回执内UTC时间为准。其他机器只能复用知识和源码，不能继承本机安装、容量、离线或实机资格。[10月23日交接](../handover/2026-10-23-war-episode04-vacation-handover.md)保留原字节；本页补充之后的准备闭场和最小来源归档。

## 实际证据与未完成边界

正式动态机制主题维持 **10/11**，剩余R05自然低补给实体减员因果证据；这是主题计数，不是整片完成率。[R0241有限接受回执](evidence/episode04-closed-source-integration-20261023/R0241-R08-SHOT-ACCEPTANCE.actual-a01.json)证明角色31254在1066-12-30→12-31的同次净结算中，父实例分量`a=384653,b=0,c=273262,d=0,scale=100000`，净额111391完整入账，钱包25455910→25567301。因此军费分量2.73262金币参与抵扣，最终净加1.11391金币。没有独立军费钱包扣款，也没有取得付款人或完整周期；`full_R08_qualified`、`business_pass`和`opportunity_complete`仍为false。不能从净额中再次扣军费。

R0241连续原片的编辑选区为`[180,1051)`、871帧；精确原生事件到编码PTS仍未知。原片、配音和图卡留在机器外置资产中，本次不复制或重新验收媒体。

R0242在MCP注册/SDK返回类型处失败；[修复冻结](evidence/episode04-closed-source-integration-20261023/R0242-REGISTRATION-SOURCE-FREEZE.actual-a01.json)保留官方stdio初始化、工具注册及原消费者往返的历史检查。SDK必须能解析实际注册函数的返回类型；普通结果统一构造具体`CallToolResult`，已有SDK结果原样保留，不能丢弃错误标志或元数据。R0243实际进入暂停地图并完成MCP初始化，已越过该次初始化问题，不能据此取得R05业务信用。

R0243普通推进前，Selection和适配器重复调用会唯一创建`readiness-window.json`的等待，触发`FileExistsError`。本场普通新增日、AUTO、Film、新业务Save均为0；它不是低补给阴性实验。后继[就绪合同冻结](evidence/episode04-closed-source-integration-20261023/R0243-READY-ONCE-SOURCE-FREEZE.actual-a01.json)改为消费原Selection已完成的唯一readiness：核对同run、runtime、冻结argv、原时限和保留进程身份，不新开等待、不延长时钟。[源码差分](evidence/episode04-closed-source-integration-20261023/R0243-READY-ONCE-SOURCE-DIFF.actual-a01.json)记录仅替换等待交接和来源绑定；未知Save不重试，原Selection的finally关闭路径保留。旧release CLI和supervisor未知原wait仍未知，不补写为0。

2026-10-22T20:41:52.858150Z的[新准备闭场](evidence/episode04-closed-source-integration-20261023/R05-PREPARATION-FINAL-FREEZE-AND-CLOSED.actual-a01.json)绑定新`r05-source/SOURCE-FREEZE.actual-a02.json`（3724B，SHA `d62f7f76889f04153b6e52d74f590b6d79739240aeba42dd1941c2c7a0c95135`）：16文件strict、1738个来源Pin、53公共调用方、实际prepare/plan/preflight，以及首claim和首Savecopy的变更前拒绝均已完成。最后counter仍为R0243；**本轮新RunID、Game、SDK、Film、Savecopy均0**，作者及owned Popen为0，准备包已停写。[Root当次关闭观察](evidence/episode04-closed-source-integration-20261023/ROOT-GAME-CLOSED.actual-a01.json)同样未发现Game或屏幕owner。它是`static-ready`准备结果，不是R05实机通过或未来Game财务卡。

## 精选源码参考包

[来源清单](evidence/episode04-closed-source-integration-20261023/SOURCE-MANIFEST.json)绑定[参考归档](evidence/episode04-closed-source-integration-20261023/curated-source-reference.tar.xz)：19件、282581B原始源码/说明，归档66344B，SHA `4b433c01430c7b6b9144b270774775518c4be5b2ae6bc3d97794a2c53965ec73`。各成员保留原字节、原路径和SHA；没有接入planner、runtime或CI执行入口。

| 保留内容 | 后继用途 |
| --- | --- |
| `ready_contract.py`及原路线检查 | 单次readiness的来源、时限与保留进程校验参考 |
| `registration_result.py`及原注册检查 | 具体SDK信封、JSON域与错误身份保留参考 |
| `final47_base/products/recipe`及检查 | 严格R05接受合同、47段正文配方和新产物消费合同 |
| `executor_contract.py`、`produce_final47.py`及检查 | 独立媒体准入、实际原Popen/Job闭场、逐段编码与整片验证参考 |
| 新R08编辑依赖、中文安全分页及QA合同 | 保留原配方关系，避免旧字幕边界和旧派生片被误用 |

这是精选历史来源参考包，**不是可独立部署的执行树**。检查文件仍依赖其原冻结图；[本次实际检查](evidence/episode04-closed-source-integration-20261023/VALIDATION.actual-a01.json)只重新核对成员字节、归档往返和17份Python的AST，没有重新执行其业务或历史strict矩阵。[原47段来源包](evidence/episode04-mechanism-final-source-20261022/SOURCE-MANIFEST.json)中的`r/mechanics_contract.py`按原SHA引用，不重复封包。319346B的host、281004B的scoped server、完整展开配方、第三方依赖、EXE/DLL、字体、存档及媒体均未纳入。后继如需修公共生产路径，应按当前Java迁移边界和实际新HEAD单独实施、校验真实消费者，不能把这些参考脚本自动装回生产。

## 47段正文与完整工作片

[a04正文配方冻结](evidence/episode04-closed-source-integration-20261023/CORE47-SOURCE-FREEZE.actual-a04.json)与[a02执行器冻结](evidence/episode04-closed-source-integration-20261023/CORE47-EXECUTOR-SOURCE-FREEZE.actual-a02.json)均为源码结果。旧黄色47段审核片只有机制正文，漏了片头，不能称为完整第四集。用户本轮要求制作包含片头的完整`FullWorkingReview`；本次来源入库时该工作并行进行，尚不在本包内声称新片生成、整片验收或交付。

新47段正文尚缺实际R05接受回执；R05须有自然stock<10的writer入场值、同次callback到正向物理扣兵的可核链、连续raw和正常闭场。`null`不是0，净兵差或ACK不能补证。后续正文须实际重编码全部47段；完整片头、最终PTS/音轨/字幕/画面检查、人工1×及用户签收继续分别记录。旧源码卡和用途已过期，不能据此启动新的Game或媒体任务。

本包只交付小型事实和不可变来源；不改旧冻结根，不追认新的实机能力，不重复全仓或业务矩阵。后续完整工作片的实际产物与报告更新另作小包。

2026-10-22T22:30:49.939851Z后继实际补注（machine_id同上）：包含品牌片头、罗贝尔动态开场、六章及结尾的62cue完整工作审阅片现已生成，50138帧/27:51.266667，最终本地文件与OneDrive客户端同步有实际回执。[交付与两阶段来源](episode04-full-working-review-20261023.md)保留a04全部62cue生产及a05整数采样时钟收尾、前代失败、整片QA与原始闭场。human1x=false、user_signoff=false，R05仍规则说明/实机未验、正式10/11保持；本页上文为首包当时截点，不据媒体完成追认R05资格。
