# 受控20种债务危机的引擎验收

本case为 `crisis-scenes20-engine-fixture`，与自然 `news-crisis` 独立。它使用明确声明的API债务、成熟期和成年AI压力种子检验分支和后态，不证明自然亏损、随机发生概率或20次自然离世。源码及NoGame测试不能授予实机信用；本候选尚无EMIT或引擎结果。

输入是schema3、exact caseId、literal `controlledFixtureOnly=true`、玩家与独立AI债权账户、顺序1..20的实际账户ID，以及child/inherited/asset/aid/restructure五个控制账户。共27个不同永久账户ID；不接受“isAI”“adult”“trait”“context”等断言，也不收未来角色/新闻/债权ID。角色、年龄、AI身份、PRIMARY、资产和原场景条件都在引擎内从实际引用重审。前进来源、所有FilePin和路径须由实际 `Path.resolve()` 或Java实际绝对规范路径产生，不手写不同斜杠的别名。

公共入口仍为同一builder/prepare/allocate/preflight/run/verify、同一CaseClient和既有后台控件/事件/保存/只读toast工具。新分支通过原6个Java producer源，并额外验证新2个Java组件和原selector/terminal两份生产脚本，组成该新manifest的10份来源。旧schema、旧6producer、旧23case和已完成的EMIT原件不重标。App17的只读审计/SaveCore来源不因新fixture被改称新资格。渲染只增加一个独立测试fixture；正式产品只提取原终局完整参数模板，原入口继续选择原weighted selector。没有新Native ABI、runner、钟或每日fixture callback。

仅新fixture在原有限被动目录外追加已真实存在的E6/E7/E8三个observer声明，均只有visible=no、无callback，保存已有历史且不再ARM；不修改旧profile的五epoch目录或接受任意未知XFMA。

`xfmc20_setup`只可执行一次，先消费尝试，再遍历一次既有账户registry。要求原最大账户ID≤65536、金融日≥30；不存在或重复索引不能算绑定成功。只绑定明确27ID，不扫全人口。20个正例及两名受援控制必须是实际成年、存活、无外部金币的AI PRIMARY，已知零资产、非继承、无旧债/终局；20个实际context分别采用生产AST的原条件。生产债权账户须与正例受益人独立。角色不合格时不补造特质、战争、羁押、头衔、地点或新人物，也不替换角色。

全部绑定通过后，26个目标通过原 `xfm_debt_cover_shortfall_effect` 各登记1,000,000分、kind1、fund_eligible0的受控义务。请求源日为当前金融日−30；没有转账、注资、减资产或伪称市场穿仓。明确种子设置逾期30、成熟14日和两次review；成年AI才增加400压力。原 `xfm_crisis_begin_effect` 仍实际尝试援助/展期，产生的真实援助和保护期不移除。控制种子不冒充实际30天历史。分配中途失败保留已创建对象/义务并禁止重播，不清理旧权利来“修复”场景。

| 阶段 | 原操作与独立证据 |
| --- | --- |
| S1，D0 | 一次setup；第一物理SAVE；Audit、完整Raw和Whole绑定实际27账户、26债权及源、20真实context、资产与原继承关系。`xfmc20_select_aid`只选择新受援债权；随后用正常市场`.106`付真实1000分。`xfmc20_select_restructure`只选玩家真实债权，正常`.107`由实际债权人同意减记/展期。玩家资金不足时仅正常自愿入金，不从fixture造钱。 |
| S2，仍D0 | 真实援助和同意的保护仍有效后，一次execute依次调用20个source-derived分支；每个调用都再次检查完整原终局guard及原context，死亡、on_death、custody、债务state4及新闻只走共用生产体。六个负对照只在原guard实际false时调用原入口；意外true直接记录负例失败，不冒险杀死控制角色。一次retry只调用被原guard拒绝的旧目标，不能第二次死亡。第二SAVE逐项核对本金分拆、原actor、继承/冻结、权利ID与唯一kind5事实。 |
| S3，最多14个新自然日 | 每次原单日后保留原两次只读toast查询，再用同一CaseClient公共队列作最多45秒、15对、提交间隔至少3秒的被动观察。只发两条readonly query，不推进日期或清理head。两次实际empty可提前结束；失败、未完成或UNKNOWN立即停止后续提交，保留全部原结果。第三SAVE、实际源join和现有Raw/Whole分别核对原义务、新闻簿与显示。不得清队列、移动cursor、直接送toast或补日。 |

三份SAVE均须独立归档，单档≤256MiB；新case显式7200秒hold以及正常退出180秒须在启动前准入，不延长运行中期限。每次被动提交都重新检查原hold、已完成S1/S2且S3尚未提交、原Root阶段已接受以及无其他在途/新增控制写者。阶段review携带 `crisis20` 的baseline/terminal/retained三种有限JSON及原证据FilePin，Root手读原件后明确判断；它们不是新金融parser或自动现金认证。kind5新闻入账、20种终局/继承、六个保护对照、20条实际local visible join分别计数。后端20项齐备但显示不齐仍保留后端事实，整case为PARTIAL。未发生和Unknown不填0或OBSERVED。全产品、所有人类、自然概率及逐日金融覆盖始终不由此case授予。

每个OBSERVED终局必须保留实际account/claim/source身份、原死者和实际scene。成人继承者按原custody接手并留继承索引；未成年继承者冻结；无实际继承者保留state2/frozen及原债务。不推断或设置继承人，不给死亡奖励、免债或价格变更。原actor不能随账户holder迁移而改成继承者。正例、负例和重入后的变化通过实际保存读回，GUI callback或marker不替代后态。

新闻限每人每金融日3条，当前HUD只一个active toast。20条入账在无旧urgent积压时至少需7个送达日，但这不保证采齐20条；积压保留。本机原版 `hud_notification_templates.gui` 使用单个 `ToastMessageHandler.GetMessage`，并有悬停延迟与dismiss方法；所核当前Native及Java DTO没有寿命或剩余秒字段。因此45/15/3仅是有界被动观察政策，不是引擎TTL证明或轮转保证。Root旧R77采样器只有源码、从未实机执行，新case不导入该TASK工具或其队列wrapper。local OBSERVED必须用同一对原Native DTO的不同completed frame、相同head/源entry/revision/actor/recipient与完整EOF的现有NewsToastDelivery报告，匹配生产本地化和真实文本，不接受ERROR或literal accessor；重复head不新增场景信用。原 `delivery_confirmed=false` 保持false，独立join另记。单人最多授该实际接收者；多human必须另有实际连接玩家与逐人join，不伪造人类或借单人结果。

读回复用当前受资格的Audit/Whole/exact Raw/NewsToastDelivery入口，不新parser，不扩大帽。原custom-source INCOMPLETE、layout UNQUALIFIED和未知字段完整保留；需要多批时按显式选取union稳定拆分。实际角色/来源、request/EMIT/product/runtime/grant和后继读回均由Root绑定，此文不预测运行ID、PID、存储余量或通过。

修改了公共CaseClient的精确case组合接线，未修改C++/ABI。是否影响Q54或后继Python来源资格必须按真实compiled-input闭包和现成same-root Host delta路径判断，不能由“只是Python”外推复用资格。新case采用stop_at_boundary，当前Host针对observe_unanswered_inbox的三案白名单保持不变；不为此增加收件箱或多日Native特权。
