# a04 骑士章逐句证据审计（2026-10-01）

38 句机制断言均有对应证据或明确边界；未发现把当前 a02 次日人物状态冒称已证的句子。k035 的‘放大通告’是实际成片未兑现的画面承诺，需修剪辑。完整原件路径、大小、SHA、逐句 claims 与实际 timeline 见同目录 `sentence-audit.json`。

历史039→040、020、070、036→038均单列，原UI未留存；当前a08/a02不替它们证明因果。当前a02 final trace失败，33437次日生命状态及选择器仍UNKNOWN。旧历史证据不关闭这个缺口。

a04骑士章为470.900–886.467秒。project story、最终sources/story及timeline的38句中文逐句完全一致。固定原件重投影039→040、036→038和020 selector均与冻结输出相同。155件本地文件独立哈希；旧a03 fact pack里无关contact original_case的pin与fixeda04文件不同，已保留差异，不参与本章结论。

| key | 中文原句 | 原版证据与画面关系 | 结论与缺口 |
| --- | --- | --- | --- |
| knights-k001 | 第二本账看骑士。要分别看人物是否留在名单，以及他此刻的勇武；人数和属性会有不同的变化。 | 骑士人物事件与兵团current/soft/hard伤亡是不同路径；039→040名单不变而属性变化。 当前a08画面可示名单和勇武列；不证明历史人物。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：无超出本句的断言；不把所有人物风险当作已证。 |
| knights-k002 | 先看这份独立冷载的界面。防御方有十一名骑士，第五行骑士的勇武是七，上面一行同名人物的勇武是十二。 | 直接审阅a08原尺寸静帧：11名骑士，第4行同名人物12勇武，第5行7勇武。 原图可直接匹配；两个同名人物不能唯一绑定CharacterID。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：精确PTS未保存，10s只为requested seek；无历史34333身份。 |
| knights-k003 | 右侧的七是勇武，名单标题的十一才是骑士人数。这张画面只有当前状态，没有展示这名骑士此前的属性。 | 单帧同时显示人数11、勇武7；并无同人前态。 匹配当前静帧。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：本句诚实指出无时间差；无须为11→7补假画面。 |
| knights-k004 | 同版原版规则里，每点勇武提供五十基础伤害与十基础坚韧，再受骑士战斗力影响；人数相同，属性也可能不同。 | 同版defines中每勇武damage50/toughness10；039→040有效勇武×1.75×50/10等于原生属性。 a08是规则示意背景；未实采a08同帧效能，不能计算该人的有效属性。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：原版50/10静态定义可用；不构成每日杀人数。 |
| knights-k005 | 现在切到历史回放零三九与零四零。这是同版原生记录，原始界面未留存，下面展示绑定原件的记录投影。 | 039 d5源档D978…→d6后档9ACA…；040逐字节加载9ACA…，历史capture raw_video=null。 历史039/040原UI未留存；实际board左a08明确标示另次示例，不能当历史。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：历史原UI缺失已口播并上屏，属于已声明画面边界。 |
| knights-k006 | 零三九从第五日检查点另起回放。新增战报是骑士三四三三三被四七零三二致残，受害者仍然存活。 | 039新增side1 knight_maimed_by_enemy：34333被47032致残；d6存档34333 alive_data=true/dead_data=false。 无039事件实录；右栏原生记录可核，a08左栏另次。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：没有当前a08对应34333的前后实拍。 |
| knights-k007 | 源档已有另一条受伤战报，最终列表同时保留两条。所以本日新增事件要看前后差集，不能把累计列表整份算进今天。 | 039源列表已有47029/33435 wounded；最终2条，新增差集仅34333/47032 maimed一条。 历史UI无；前后trace列表差集支持本句。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不能把累计战报整份当日增量。 |
| knights-k008 | 同源前后存档显示，他新增独腿与受伤两个特质，基础勇武仍是三；这里把伤势和基础技能分别列出，避免混读。 | 039同源d5→d6，34333新增one_legged+wounded_1，基础勇武3→3；中文名为独腿/受伤。 历史前后人物卡未留存；a08不显示该trait组合。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不能把静态trait修正-4与-2直接相加解释有效净差。 |
| knights-k009 | 他的对手四七零三二得到一百五十威望；这次成长列表选中第零项，没有增加对手的基础勇武，两笔变化也要分开。 | 039同源47032威望300→450，基础勇武10→10；成长实际entry选中第0项。 历史人物威望/成长前后UI未留存。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：039调整后运行时权重未直接捕获；本句仅说实际选项与存档差。 |
| knights-k010 | 零四零逐字节载入零三九保存的第六日状态，没有再推进日期；我们读取这份伤后存档的下一暂停帧。 | 039保存9ACACDE3…，040 checkpoint_source同SHA；date_raw53146368、paused=true、snapshot/control/v3同revision。 历史冷载UI无；原始native回件与capture支持。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：040为同保存状态冷载下一暂停帧，不证事件当日即时刷新时点。 |
| knights-k011 | 骑士总名单仍是二十四人，五十一条兵团记录也没减少；他的六十一号兵团当前仍为一人，变化落在属性列里。 | 039→040 knights24→24/regiments51→51，Reg61 current_soldiers1→1。 历史名单UI无；a08人数11不同源，不参与此对拍。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：补画面需原档同源前后名单，不能用a08代替。 |
| knights-k012 | 原生读到的有效勇武从十一变成七，骑士战斗力仍为一点七五；有效勇武与刚才存档里的基础勇武是不同口径。 | 34333有效勇武11→7；效能raw175000→175000/scale100000；存档基础勇武3→3。 历史有效属性UI无；当前a08勇武7不是同人净差。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不指定同日实际伤亡已在哪一步重算。 |
| knights-k013 | 伤前这一帧，十一乘一点七五，再乘每点五十的基础伤害，得到九百六十二点五；卡上同时保留原生属性读数。 | 11×1.75×50=962.5；原生effective_damage_raw96250000/100000=962.5。 右栏历史记录/复算；a08左栏只示人数。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：数值是属性，不是当天杀人数。 |
| knights-k014 | 伤后用七点有效勇武重算，同样的一点七五和五十，得到六百一十二点五，与零四零这帧的原生伤害属性一致。 | 7×1.75×50=612.5；040原生effective_damage_raw61250000/100000=612.5。 历史UI无，数据与计算同源匹配。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：当前a08没有该角色效能实采，不借图宣称其伤害612.5。 |
| knights-k015 | 坚韧按每点十来算，同一链里从一百九十二点五降到一百二十二点五；于是名单人数不变，战斗输入已经变弱。 | 11×1.75×10=192.5→7×1.75×10=122.5；24人名册保持。 历史右栏数据可核，当前左图另次。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：只证明本次保存态的下一暂停输入变弱。 |
| knights-k016 | 伤害是战斗属性，不能念成每天杀死同样人数。其他兵团也有正常伤亡，所有人数差不能都归给这次致残。 | 12个其他兵团current_soldiers有正常伤亡变化；damage为属性，不能等同每日杀人数。 原生兵团差异无真实历史UI。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：归因范围诚实；不扩成整场人数差都由致残造成。 |
| knights-k017 | 再切到第26日的独立历史回放零二零。原版选中的事件是骑士被杀，我们先追谁被选为对手，再看死亡怎样写回。 | 020 day26/native_event_load_index11、root33437/Reg65，对应stock knight_killed。 020原UI缺失；a02击杀通告独立。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不得称当前a02也直接读取了选择器。 |
| knights-k018 | 原生来源有十九名敌方骑士，按这条事件的勇武门槛过滤后，只有十四人参加抽取；这里的候选数是十四。 | 020源骑士ID序列19人；勇武门槛后compact14人，原生selector count14。 候选列表/门槛为内部值，不存在可用原版UI清单。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：只针对这次事件分支，不能外推所有骑士事件。 |
| knights-k019 | 过滤顺序也会改变结果。原生容器删掉不合格项时，用尾项填进空位，再检查这个位置，而不是让后面各行依次前移。 | RVA0x19F4760以尾项填洞重查；fixed projector对同次v3谓词重建顺序并命中原生结果。 内部容器顺序只能用图示，不以UI排序替代。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：无通用分布声明。 |
| knights-k020 | 索引从零开始，八是第九个位置。原生顺序这里是三四一二零，稳定删除却会变成五四一四零，随机数相同也会选错人。 | native compacted[8]=34120；稳定删除的相同index8为54140；0-based8是第9项。 原生记录与图示匹配；a08人物行无关。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不把UI行顺序或姓名当原生候选顺序。 |
| knights-k021 | 这个分支没有候选权重。按选择器记录的局部随机状态复算，得到十四亿零八十一万三千九百一十二；除以十四余八。 | counter1117324859→1117324860/salt0；复算draw31=1400813912，%14=8；无候选weight分支。 随机数非UI/钩子直接draw字段；旁白明确复算。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不把020 root draw26436929或070 list draw51510340混入。 |
| knights-k022 | 原生选择器直接记录的返回项就是三四一二零，新增击杀战报的对手也是他；抽签计算与实际执行在这一步对上。 | 020 selector word1=0x8548=34120；新增BattleEvent右侧34120，两者一致。 无020原实录；原生trace为证。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：仅此一次选择执行对拍，currenta02 selector UNKNOWN仍保留。 |
| knights-k023 | 被杀目标是三三四三七，对应六十五号兵团。在一个执行边界，他仍然存活、有效勇武为四，并且仍链接这个兵团。 | 020 fire边界5：33437 death_marker=false、effective prowess4、current_regiment65且反链匹配。 无原人物界面；左a08与右历史边界均有独立标签。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：边界5不是最终死亡状态；currenta02前边界false不能推出d27存活。 |
| knights-k024 | 后一个捕获边界已有死亡标记，人物与兵团的连接被清空，有效勇武读成二；前后存档里的基础勇武却始终是二。 | 020 final边界6 death_marker=true、prowess2、regiment0；同run存档基础2→2。 020原UI无；a08不构成死者画面。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不把effective4→2称基础技能-2；不填currenta02空final行。 |
| knights-k025 | 四变二不是基础技能被扣两点。后存档记下战死与击杀者编号；击杀者的威望货币和累计威望各增加一百五十。 | 020 d27后档dead_data=true/alive_data=false、death_date1066.12.30/reasondeath_battle/killer34120；34120两种威望各+150。 原版人物死因和威望UI缺失；已绑定原始与Rakaly melted bytes。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：死亡发生日12/30可存入12/31后档；不能替当前a02生命状态。 |
| knights-k026 | 击杀者还会进入另一张成长列表。这里必须换成零七零来源卡：它从相同第26日源档另起，是独立的权重实采。 | 070自C127…第26日源档冷载，独立raw begin/finish/v3与020分开。 070原UI无；来源卡明确切换。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：相同源档不等于020续帧。 |
| knights-k027 | 零七零直接读取的三个运行时权重是四十、三十、十五，总和八十五；这是本次列表的权重，不能念成每天的概率。 | 070 listcall14权重int32[40,30,15]、bytes280000001E0000000F000000、positive total85。 内部权重无原版UI；右记录卡正确。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不是每日死亡/成长概率或所有角色永久比例。 |
| knights-k028 | 按列表自己的局部状态复算，抽签值为五千一百五十一万零三百四十；比例阈值为二，落在不作成长的第零项。 | 070 listcounter1462316485；draw51510340，floor(draw×85/2^31)=2；选entry0/no_op。 旁白明确复算；原生记录实际entry身份另核。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不使用mod85，不把根节点draw当成长抽签。 |
| knights-k029 | 这不是只看勇武没有变化再倒猜分支：采集还把实际执行的条目与原生列表绑定，证明这一次确实选中了第零项。 | selected_entry_identity_token等于entry_node_identity_tokens[0]；selected_growth_branch_matches_original=true。 实际原生指针身份可核，无人物UI。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不是仅因基础勇武未变而倒猜分支。 |
| knights-k030 | 要看下一暂停帧的名册，我们再换来源。零三六保存自己的事件后状态，零三八逐字节复载这份存档，读取第27日。 | 036保存CD0648…第27日后档；038 checkpoint_source同SHA，paused/date53146872、query revision一致。 036/038原始名单UI无；左a08另次示例。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：不能串成020/070连续录像。 |
| knights-k031 | 这条链的兵团名册从六十九条变成六十八条，骑士从三十人变成二十九人；缺的正是三三四三七和六十五号兵团。 | 03669团/30骑士→03868团/29骑士；ID差集仅65与33437，保留基础行逐对象一致。 只有原生读取证明此名册；currenta02界面11→10不能替换。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：需要同源真实名单画面才可补该历史可视化。 |
| knights-k032 | 击杀者三四一二零仍在下一帧名单，勇武仍为七；这里只核对保留名册与基础输入，没有证明全部伤亡状态相同。 | 038仍含34120，prowess7；full_casualty_state_identical_proven=false。 历史名册/属性UI无；输入行可核。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：相同base_inputs不证明所有soft/hard/隐藏状态相同。 |
| knights-k033 | 零二零解释选择和死亡写回，零七零解释成长权重，零三六到零三八解释后档名册；这些记录不能剪成同一次连续录像。 | 020 traceD5F044…；070 finish35ADD1…；036 trace713DB2…及后档CD0648…/038v3独立。 三组原UI未留存；来源切换标签避免连续错觉。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：本句为必要来源边界；各attempt不能互填。 |
| knights-k034 | 回到另一段独立实录。十二月三十日，同一录像的相邻两帧里，防御方骑士从十一变成十；这次变化能直接从界面读到。 | a02相邻4918/4919帧PTS232.533/232.567、同UI日期1066.12.30，骑士11→10。 两原尺寸图直接审阅；raw clip原速，当前数据事实匹配。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：总人数11→2是另一字段；净少1不能唯一绑定33437死亡；无d27状态。 |
| knights-k035 | 随后战报清楚写着，一名我方骑士被敌方骑士击杀；我们放大这条中文通告，同时保留十名骑士与当天日期。 | a02 PTS233.0与233.5/235.5清晰通告，骑士10、日期12/30；243.5通知已消失但count/date保持。 原图可读；actual a04用原速raw233.0..243.867，只有scale/pad，final842.5s未放大通告。 | FACT_SUPPORTED_VISUAL_PROMISE_UNRESOLVED：机制事实受支持；旁白“我们放大”未交付。需同帧inset或标注冻结放大，不改为d27。 |
| knights-k036 | 这份实录没有证明历史抽签发生在本次画面里，也没有逐编号证明名单净少一人的完整原因；我们只读它真正显示的内容。 | a02无selector字段、final读取失败；实录只示当前人数/通知，不能证明020/070/036/038路径。 独立a02实录与历史卡分离正确。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：此句诚实保留UNKNOWN，不能因为没证明历史路径而把事实UI判RED。 |
| knights-k037 | 现在两种风险更清楚了：致残者可以仍在阵中，却带着更弱的有效属性；阵亡者会在已核对的后档链里退出骑士名单。 | 039→040致残者24人名册保留/有效属性下降；独立036→038移除33437。 历史UI缺失明示，当前a08/a02只为各自示例。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：结论限定已核后档链；不声明currenta02d27死亡已读到。 |
| knights-k038 | 这些还不是完整人物风险分布。其他分支、条件权重与未来每日刷新仍需验证；本期也不提前宣布治疗结果。 | full mutable write set/未来daily transitions/whole-battle probability均未证明；本片不讲041治疗已结束。 来源卡准确，未配虚构治疗画面。 | SUPPORTED_WITH_DECLARED_BOUNDARIES：其他分支、条件权重和治疗结果不是本章现有断言；不用扩为新blocker。 |

补证顺序：新独立run的33437次日状态优先；保存态人物卡/名单可视化随后。k035同帧inset可离线修复。当前a02 PTS233.0–243.867片段属案例第26日/1066-12-30，不是第27日/12-31；检查233.5与235.5帧有通告，243.5帧已消失，不能宣称全段通告持续存在。

本次未启动CK3、Steam、录制器或桌面操作，未修改旧素材，未提交、推送或接收master内容。人工1×完整审片和clean span认证仍未完成。
