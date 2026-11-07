# P113：完整 Construction 原件与公开软件生产链

本地日期2026-11-08，实际编测UTC日期为11月7日。持续优化目标保持active；本单元闭合大输入的功能与原件路径，不授实机装载、游戏推进、SAVE或10秒／新增保存日提速。

原Construction链把含完整快照的query放进262144B SDK输入、1MiB命令和4MiB材料输入；只给SDK临时角色仍无法保全后继原件。本次新增显式full-material入口与版本化引用，完整query、starting／ending snapshot、native envelope、旧ledger和source原件继续保存，原小输入构造器、parser、encode、hash和旧cap保持。

NativeQuote.fromFullMaterial与ObservedRequest.fromFullMaterial各只接收一个完整raw input，内部确定性推导SDK临时角色，保留完整original()及防御clone；不公开任意raw／typed二元组。query仅投影两个snapshot的已核SDK角色，保父容器缺失／null／错误shape、hello四build键presence、业务数组和完整native envelope；消费内容本身超262144B仍拒绝。该纯DATA入口不产生Guard或原件权限。

ConstructionOriginalSource在同一实际held Session通过现有64MiB FullMaterial CAS保存并真正读回，核长度、SHA和每byte。未来新命令保持原外层五字段，ordinary_cash_request可为闭合manifest {schema,input_ref,financing_request}；融资副本逐侧使用与ActionCodec相同的PublicDataJson fixed typed encoder后逐byte绑定到全文。新规划的ActionId／bodySHA自然反映新表示，不改已发行命令或其hash。原small inline保持原OpportunityJson／SDK路线。

fresh revalidation、INTENT准备与冷核验、restore、所有OUTCOME分支及Native archived binding均显式重新打开同writer完整原件；Loaded只能由私有构造器的实际loader产生，类型本身不授许可。restore先由Root originals在原Session加载，再把bodySHA索引的完整DATA传给纯reducer，不在reducer内开writer，也不重建ActionCommand。Applied继续委托原Native效果核验；Rejected／Unknown消费manifest前同样必须有完整sidecar，缺件时不改owning body。

材料独立采用xar.construction-material-source/v2和java_construction_material_source_v2，输入为显式reducer v3／FULL_V3。旧v1 source、旧v1／v2 decoder及4MiB限制不扩宽；混合活动v1／v2 source拒绝，完整previous ledger保留在新full input。owning current／saved／restore／finance reader均实际打开新source；v3进入与旧refresh相同的kind核对。完整SEM重建相等、唯一原native envelope逐byte核验、query receipts及全部source／frame顺序保持。RawCash使用已有P107 hello四键角色，未误用P110 diag三键角色。

新版本最终DOMAIN BODY走已有canonical body codec，使publisher与owning verifier的逐byte合同一致；完整6.8MB input、query、CAS原件与canonical command均不因此排序。ordinary source closure加入真实implementation carrier；legacy配置必须明确选择新Java source且原closure包含它们。requireLoadedClass兼容hook并非source资格，离线classpath成功也不授Runtime安装。

16个独立生产源分最小3 SDK、2 Material、11 App TU验收；后续实际变更只增编受影响叶子，未重编已绿全图。三个新Test TU覆盖SDK、真实CAS与owning DATA、公开生产链。现有public fixture仅新增显式有限软件预算和fresh responder选项：旧默认总归档预算16MiB保持，新P113软件case明确64MiB，单artifact／生产cap不改；新fresh选项保留原native:revision名称，仍有新read_request_id、完整两包／ACK绑定和真实chronology，旧configure默认行为保持。

最终通过按真实执行分开记录：

| 范围 | 实际通过 |
| --- | --- |
| SDK full／old控制、完整nested original、clone、schema／null／消费内容cap | 修正现金夹具后的Test02同JVM5P；原Test01为3P／2E保留 |
| 完整CAS、canonical command融资绑定、INTENT／restore、owning材料 | 最新manifest Test06为1P；受最终body producer变化影响的intent／material Test05为2P；各负例保留 |
| public Applied | Public15独立1P，child112.223149s，outer112.9836304s；XML suite110.116s／case110.084s，console110371ms；23:20:10.857671Z关闭 |
| public Unknown | Public15-fresh独立1P，child65.4859073s，outer66.2828238s；23:24:32.985993Z关闭 |
| public RejectedBeforeDispatch | Public16独立1P，child58.3810997s，outer59.3011581s；XML suite56.005s／case55.965s；23:29:47.867285Z关闭 |

三个public方法并非同JVM3P。它们通过公开ActionWriterIntegrationFixture、实际collector、四个Finance Read contracts、七领域同writer导入、真实准备／Guard／coordinator／归档及owning reducer运行；数据为明确的软件Game42／actor73临时原件，不是Runtime授权。Applied实际经过完整quote→future manifest→fresh revalidate→INTENT→software Native动作→真实NativeConstructionEffects／cold verifier→OUTCOME→历史发布→full MATERIAL。历史行由正式DriverActionHistoryPublisher从真实NativeEffectEvidence compatible result、前后Native／Driver帧、全部independent reads与supporting material产生并正式提交，未手造coverage；版本+1、重复ALREADY_COVERED及零新增Native读写均断言。

Unknown原件与pending保持，缺sidecar先拒绝。最初Rejected软件case只有generic负ACK，实际系统正确保留Unknown，原0P／1F／0E留存，未强行解释成不执行证明。最终独立case在既有public observer中确认真实IntentDurable后触发写前故障；原coordinator自行归档BEFORE_WRITE／0字节proof并重抛，测试从canonical journal读真实RejectedBeforeDispatch，核原proof和Native动作写入0，再验完整sidecar缺件拒绝／恢复后clear。未更改生产Guard或制造receipt。

Applied15阳性目录为D:/ck3-state/resume91-native-integration/p113-public-production-test15/tmp-junit/junit-17257718389505711248/APPLIED，NEVER保留CAS。实际full plan6828384B／SHA256 6949269be1a5652bca1e6e0d68df6d35462d0d66f13bcf94f4ed52c85c07cc7f；完整材料input6850180B／SHA256 0040bd31f5d9ca998f1e1e47a90f39d9c649eb314bd69e1daf6718e57fef4785；owning Construction body39332B。具名四原件读回记录public-test15/APPLIED15-RETAINED-CAS-OBSERVATION.json为4785B／SHA256 61888fa56851a47acd715cb47375d04048602836919b75a56d48979e02938be6；该有限核验不冒称全store图独审。

真实模型三次调用均完整结束：SDK01 total23142.843ms／TTFT5413.791ms／prompt40632／output3051；SDK02 total24170.797ms／TTFT953.076ms／41072／3916；Material01 total23598.794ms／TTFT4230.598ms／31974／3321，cached均未报告。首SDK候选拒收，第二轮full factory／typed decoder核心部分采用，owner修正parent类型／顺序／imports；EmergencyFinancingAssessmentCodec.Request本来就是合法API。Material候选部分采用，owner修实际FullMaterial lane、readback、活动source替换和imports。后继11App consumer、版本兼容、最终body canonical及header绑定为owner接线，不能记作模型完整实现。

全部失败原件保留：SDK现金软件夹具缺当前monthly source合同；Native SDK JUnit已5P后wrapper误进probe导致actor错误，离线原XML／ARGV／pin／close补正且0重跑；CAS测试初始raw-vs-canonical目标oracle；公开夹具的FRESH／producerInput canonical、ROOT exact nullable field、动态held Session、CASH wire profile、16MiB软件总预算、fresh responder和缺严格历史publisher等逐项修正。Public12真实命中生产新header成员顺序绑定错误，修为同ActionCodec fixed typed canonical比较；不把该生产修正或owner夹具错误归咎模型。旧negative ACK保Unknown的结果不改写。原business120秒／readiness30秒生成规则保持，未刷新在途命令；150秒只是有限新软件actor外层资源窗。

主要证据根为D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-full-original113；Native包括p113-construction-full-sdk01、p113-construction-full-material02、p113-construction-full-app01及后继变叶、p113-sdk-data-test02、p113-app-custody-test05／06、p113-public-production-test15、p113-public-production-test15-fresh、p113-public-production-test16。公开失败09之后及最终阳性CAS保留；早期08失败READ原路径已由旧TempDir cleanup移除，只保源码／日志／XML／运行原件，不声称那些bin仍可读。

交付仅清SDK Codec四个新增空行尾空格49／55／65／69，13927B／77fd0c…已编原件仍留，正式13879B／e2493209…的全部非空行逐byte相同，sdk-whitespace01/WHITESPACE-PROOF01.json记录差异；不为纯空白重编／重跑。当前新增类型与source graph尚未Runtime采用，无body-only热替资格，无新增游戏日或SAVE收益。发表后立即继续P114：只复用同一不可变full NativeQuote首次fixed finalizer的exact bytes，先有意义回归再同输入whole-consumer测量，不用经济codec重编码结果冒充原byte，不以本次发表结束持续性能任务。
