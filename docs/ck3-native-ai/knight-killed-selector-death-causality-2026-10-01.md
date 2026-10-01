# event11 骑士死亡：精确原版路径与本案证据边界

研究仅使用本机已冻结的 1.19.0.6 输入和独立分支 `codex/war-e2-mechanism-closure-20261001`。基线 commit 为 `1901473429deb1297be7d5d4451169082629858b`；没有接收 master、启动游戏或执行桌面输入。原版 `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` 为 95,206,008 字节，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。下述 ABI 只适用于此精确 EXE。

## 实际 R0139 已证明的范围

原始 live 根为 `C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02`。它使用190源码和 ED537…DLL，与旧 R0127 的 EB643…DLL 是不同 run。真实日历为 **1066.12.29 → 1066.12.30**，原生日数 `53146848 → 53146872`，恰好推进一次。d26/d27 是案例检查点标签，不能改写为12月30日→31日。

7条原生阶段记录均 flags0，实际 nested dispatcher call indices0–40 共41项完整保留；当前 source 的一般序列化仍有只保留 RNG 改变行的限制，本次完整覆盖必须以实际计数和索引验证。人物33437在前态存活且关联regiment65，后态 `dead_data` 记录死亡日1066.12.30、`death_battle`、killer34120，并失去 `court_data`。两人物的完整traits/base skills/traitXP净值没有变化。34120的prestige currency与saved accumulated各增加150，kills新增33437，signature_weapon新为flag:axe。

实际selector返回typed scope kind4、人物34120，候选14、index8，原生counter1117324859→1117324860；独立31位draw1400813912模14为8。旧190仅有最终index、数量、选中raw scope，没有完整原候选向量及每次筛选返回。实际call38为 `CCharacterDeathEffect`；这不能替代原生死亡request→queue→commit取证，也不能仅凭saved reason宣称本案唯一死因已完成。

严格回执为 `C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-R0139-readonly-verification-attempt-01/continuation-a02/R0139-readonly-facts-a01.json`（56,389B，SHA `68C10AC7E866026DD387427CE132F4C1FE86AD45292D991ABD35DE4E0994DB1C`）。完整sourcebound存档和native投影为同根 `full-block-projection-a01/R0139-full-block-sourcebound-projection-a01.json`（1,017,595B，SHA `7F141E8D028187CF579B5B7D2A71DE2A0025549A5B74E31F270EFD74CBB5703C`）。这两份不充当新run的字段来源，也不证明真实角色UI或完整战斗窗。

## selector 的原始执行口径

`19DD670` 接收RDX vector header、R8 list context。list context+0指向typed combat-side scope；`2011090`要求kind word+0为0x0B，payload dword+8为combat fullID，aux word+2为0取combat+20，否则取combat+368。原store570C758以完整ID校验combat+8，再检验原对象有效性，fallback不得当有效本案。源侧不能由phase.side猜测。解析后读取side+40/+4C，stride60的row+08是regiment fullID。严格按全代ID解析regiment后读取+148角色ID，只有-1被跳过，依原始row顺序追加16B kind4 scope。

`19F4760`的参数为RCX=this，RDX专用predicate，R8共用predicate，R9 list context，entryRSP+28为vector header。它记住旧count，只筛选新增range。共用与专用predicate的+5C均0时直接保留。kind0直接淘汰。共用predicate先执行，false短路专用predicate；两次实际`334C600`原返回地址分别为19F480B、19F481F，返回有效位AL。失败后19F482D读取末项、19F4832覆盖当前位置、19F483F减count，并再次检查当前位置。因此筛选后的顺序可能变化。

完整筛选取证必须保存materializer入/出完整vector与prefix count、两个predicate count、实际原调用返回及candidate/index/role、最终vector；不得重复求值或制造零predicate时的通过记录。新只读合同为外置 `knight-selector-causality-research-attempt-01/selector-filter-and-house-readonly-contract-a02.json`（6,002B，SHA `70635A186446EA9C990807DE11D4A72E61BE61B7D28E70DB631F24B6FF76E700`）。a01有regiment-store文本笔误，已在a02指明实际57BF4C8，旧bytes保留。

## 原生死亡链

`CCharacterDeathEffect` primary vtable4468B28、execute2EE8E30，在2EE9046调用request264BC00。参数依次是deathmanager*、victim*、reason*、date-object*、killer*、artifact*，后两项位于entryRSP+28/+30。管理器条件决定直接commit264BCB0或enqueue2654960；queued command stride30，记录victim/reason/date/killer/artifact，flush264C070随后调用commit。enqueue实际返回新row指针RAX，不能伪造void返回。

commit在264BF76安装char+1C8 death pointer，264BF85复制日期到death data+04；setter2609210写reason+10、killer fullID+18、artifactID+1C。death reason稳定key位于reason+18的有界MSVC字符串。日期、reason、killer、artifact缺失必须保持UNKNOWN，人物saved alive_data XOR dead_data缺失/冲突必须拒绝。

本案因果判定应限定为：同run、同thread/date/combat/token内，被event11实际选中执行的death节点发出唯一关联tuple；该request/queue/commit原调用与返回完整，marker在commit前false、返回后true，后续名册、伤亡与下一paused字段吻合；保存态独立确认同tuple。所有其他本案写域仍须各自说明时间分辨率。“本案这次死亡来自此路径”与“游戏只有一种死亡机制”是不同命题；本研究不主张后者。

## 武器与家族分支

原版 `00_personal_details_effects.txt:350` 的 `set_signature_weapon_effect` 优先取装备主武器；没有signature_weapon与temporary_signature_weapon时进入random_list。其中axe权重10，瓦兰吉文化等可修正权重。原版customizable localization仅读取变量并有剑fallback。

直接下游producer位于 `events/death_events/death_management_events.txt:2303` 的inline `death_in_battle_scope_effect`：dead_character存在alive killer时在killer执行setter。该effect由战场死亡通知1200/1201/1202/1204/1205/1206/1207的 **immediate** 调用，recipient分派从death_management.0001进入，而该event列于原版on_death。它同时有 `show_as_tooltip` death块；tooltip不是新的实际死亡提交。R0139全部41个event11 dispatcher节点里没有武器setter，因此axe净差不能直接归为event11。

新的passive变量monitor应先覆盖推进日、commit与死亡管理，随后另保留UI打开前后的独立checkpoint/RNG。若UI前已有axe且UI窗口0次赋值，只能说明本轮UI没有产生该写。按两个实际人物原`3329A40` getter返回owner关联setter3346BE0，可避免额外调用可能懒初始化/迁移的getter；keyID应从已初始化名字表只读扫描并双向验证，不能猜hash。仅setter通用caller还不足以指认哪个脚本producer，需保留实际node和ancestor/event来源。

实际原版flag显示/有效性函数33C6230与33C63A0均要求typed16 word+0为3，读取dword+8的identifier index，与已初始化585F240表的byte0 epoch组合，再经3B97090按低24位索引到names+30/count+3C、stride20的MSVC字符串。新监控须保存实际raw words、表epoch/count与原字符串，独立解码为axe后再与同run save比较，不能由save填入写值；3B971A0可能懒初始化、3B97020/3B96D40可能插入key，不能额外调用作只读查询。原版commit在264BE24调用33F8350的派生分发，早于264BF76安装死亡marker，监控必须在推进前启动，不能仅从marker后开始。

家族对象是1105与1053；R0139完整house_relations DB前后都没有这对关系，也没有任何关系涉及其中任一家族。实际call36执行了CImpactHouseRelationEffect，但没有持久pair写；数据库24条变化属于无关婚姻关系。原生2F03EF6调用start guard2DF7030（RCX relationType、RDX house1、R8 house2，AL bool），false时不创建关系。typed char house ID是char+150，house+10 fullID；relationType+18 stable key已由ctor→345E690原复制key证明。必须记录原bool返回，不能额外再次求值。若要指认具体未满足的子条件，还需要实际predicate子返回，而非根据净差推断。

## 列表与特质经验的原生入口

实际slain_side_knights节点22调用CJominiAddListVariableEffect execute33914A0，3391622把原variable owner、node+118 keyID、typed16B value与derived duration交给33463D0。owner+30/+3C是stride48列表行；行+8为key、+10/+1C为typed16B值数组、+28/+34为并行int32 expiry数组。33DD720按expiry顺序插入，重复typed value不再插入；expiry存为行+40 elapsed offset加请求duration，-1保持永久。不能把duration1的存档字段直接填作未采到的请求参数。

2609210在更换死亡killer时，从真实killer的alive extension+E0（或已死亡killer的death data+40）取int32 fullID vector，在26092D4调用209F7F0排序插入victim fullID。该helper返回EAX位置，并不自行去重。新采样可在commit前后读完整vector，并把actual killer/victim tuple和静态原调用锚对账。

260F640特质经验getter在260F70F写输出span+8 count；character本体+138指向完整int64 raw XP数组，+144为count。它与prestige extension+138是不同地址层级；不能用getter输出+0C作count，也不能把raw数组序号猜作track ID。完整raw数组与原版trait定义、同run保存态独立映射后才给语义名称。

## 可复用验证入口与预验

`ck3_autonomous_player/native_bridge/research/verify_knight_causal_run.py --help` 已实际执行。它读取before/after pair、raw saves、trace、固定Rakaly及source/DLL/actor/两人物identity，输出新目录，保存exact输入与成功/失败素材；不会运行CK3。显式新binding形状还需 `--day-finished`。新格式已用明确标为offline repack的R0139原件验证58条件、exit0；这是格式验证，未制造新原生run。纯schema1 journal另有12个正反offline样本。

原版精确ABI69项bytes校验只证明静态锚。open_kaishek本机依赖commit `890b32de49081b7b5510e40c5518dfb59d5c8a6d` 未更新；CLI0.1.0-cli/profileck3-1.19.0.6实际执行。6份stock脚本parse都exit0且roundTrip=true；validate syntax0但semantic均RED，主要UNKNOWN_OPCODE和有限profile的domain覆盖。3个已有acclaimed/cultural pillar/cultural parameter finite fixtures通过，它们没有执行本案IR或原生selector/death。现有公开CLI不提供任意knight_killed effect的compile/run入口；精确EXE ABI属于not-applicable。全部argv/Java/JAR/fixtures/profile/commit及stdout/stderr保存于外置open-kaishek-precheck-a02。

最终交付需要逐项证明13个required write domains。新的native publisher仍将global/full mutable collector flags保持false；外部验证不能把机器校验数量、净差或真实UI中的某一项自动升级为完整本案链。视频修订在用户要求的这些前置完成后再开始。
