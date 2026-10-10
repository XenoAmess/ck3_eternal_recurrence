# 《礼与道》当前 1.20.0.4 resolve 与继承缓存研究

2026-10-10，本机已从当前 CK3 1.20.0.4 的 typed effect 入口连接到角色与 LandState 处理链。**尚未证明继承缓存的实际 writer，也没有可据此采用的生产修复。** 这是 R49 后的有界静态研究，不是新的实机场次；正式 B4/B5/C3/I4 仍未通过，一期工作量估计仍为75%。

[R49 实机](../li-yu-dao/acceptance/2026-10-10-r0049-holder-diagnostic/REPORT.md)记录单次 holder 诊断后继承缓存45→40，保存名单与后置原生名单一致。四段日志中，各 Title 观察名单在 BEFORE_CREATE、AFTER_CREATE、AFTER_HOLDER 相同，首次差异在 AFTER_RESOLVE；五政治头衔各有尾部4项替换。日志观察面不能区分 resolve 内部写入与紧随其后的 getter lazy refresh，39527也未出现在这些20人列表中。静态研究针对这个尚未解决的因果边界，没有重复无变化的 B4、去flag或无getter对照。

全部地址为 RVA，仅绑定本机已资格化的 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本轮入口研究核对了当前大小、版本与既有213B小pin，继承此前的全文件身份记录，**没有重新计算 EXE 全文件 SHA**。旧1.19入口与偏移不能用于当前版本。

| 已证静态范围 | 实际依据与限制 |
| --- | --- |
| 当前 typed resolve | `CResolveTitleAndVassalChangeEffect` RTTI：TypeDescriptor `5A7BCC8` → COL `4ECF198` → vtable `4860A38`，`+B0=2D1CC00`。邻近脚本名在 `4859268`；注册表行尚未映射。 |
| 两个直接分支 | `change+260==17` 时 `2D1CCB7→2AA5AA0`；普通路径 `2D1CD77→2AA58E0`。两处 receiver 为 game-state `+A0+D310`，RDX为解析后的change。 |
| 预处理与移交 | 普通 wrapper 按 change 字段及 context 计数调用 `2773150`，随后与type17分支同到 `2AA5AA0`；后者移交8B change指针集合。它不是已证明的 actor缓存写入。 |
| 角色到 LandState | `277445E→29171B0` 的输入经过Char magic、fullID与`+1C0`检查；条件分支 `291720C→2954C00` 传 `RCX=[Char+1C0]`、RDX原Char、R8D=0。 |
| 原 Land 参数保存 | `2954C00` 的home-slot保存/恢复独立证明 `2954E2F→2955000` 仍传原Land与原Char。是否进入该分支属于静态条件，actor31254本场命中情况尚无运行时证据。 |
| Land 批次处理 | `2955000` 遍历Land`+230/+23C`的DWORD ID批次。它另有`+3A0/+3AC`访问，但基址来自`A92A50`返回值，记录步长72B；原生actor继承缓存步长为4B，不能因同偏移而认定为同一对象。 |

每个逻辑函数的范围依据当前 `.pdata` 与 `UNW_FLAG_CHAININFO`，没有凭地址相邻拼接。`2773150` 初次线性反汇编将尾部内嵌字节当成指令，原件保留；同字节SHA的可达CFG重读纠正了这一点。两个间接跳转和异常路径未穷举，因此“本体没有直接目标偏移”也不能外推为整个调用没有缓存写入。

`open_kaishek`预验判断为not-applicable：本工作包读取当前PE/RTTI/异常展开边界并追踪CPU寄存器参数，没有mod脚本fixture、finite runtime或replay语义可供其预验，也没有进入任何CK3验收步骤。不为此形式重跑parser，后继真实脚本变更与实机仍各自执行适用预验。

006的后继读取预算含必要重复累计代码17,436/65,536B；独立入口包另读7,347,162B EXE元数据及小窗（其中入口代码313B，含重复窗口），各后继的读段会计分别保存在事实文件。未扫描完整`.text`、复制EXE、重编native、读取存档正文或调用游戏/SDK。Source09/O8及其原manifest没有变更，已关闭的4GiB预约没有重新使用。

006的最窄下一直接门为 `2955486/295555C→29555D0`：RCX原Char的Land、EDX原Char完整ID、R8当前候选、R9当前Land批次对象；这些对象的业务角色没有按偏移猜名。ROOT随后只授权该逻辑函数及必要边界元数据，不授权递归展开其它callee。缓存writer、五政治头衔的刷新链、实际批次成员及lazy refresh仍需独立证明，87/88保护合同保持。

007随后读取`29555D0–2955A64`的1,172B逻辑体及必要条件/参数重读，累计代码18,885B。该本体没有直接目标vector偏移或原Land写入；它在条件分支`2955734→2955DE0`仍传原Land，但EDX改为候选完整ID、R8B=1、R9D=0，栈参数为0/R10/-1。R10的magic必须为`0x4163436C`且另一解析角色的ID等于原actor；magic对应类名未证明。不能把原R8/R9指针语义误转到新调用，也不能称该条件门为通用继承刷新。ROOT只对这个新直接门授权008有界读取。

008确认`2955DE0–2955FC3`为483B逻辑体，实际处理原Land的`+230/+23C` DWORD集合，仍没有目标vector直接访问或原Land直接写入。随后有两条串联调用`2956EA0`与`2956530`，第二条还受前返回值及context+40与候选ID相等条件约束；两者本体没有读取，不能擅称存在一个唯一writer。008新增539B代码（含必要重复），后继预算累计19,424/65,536B，至此封存该支。另一处003已保存的`2773EAF→2957510`直接门可单独核查，但其批次对象类名未证明，不能凭`+1C0`先称Char/Land。

009已单独核查该直接门：当前逻辑体1,150B，没有目标vector的直接访问，批次对象与其`+1C0`成员类型仍UNKNOWN。开头栈探测helper未读，不能把其后当前RCX无条件认作入口RCX；后段home-slot重载独立证明的调用为原输入`+F0→B02D10`，callee未读。临时指针序列及各项成员`+1D9`写不能混同原输入或4B继承缓存。累计后继代码20,574/65,536B，到此停止；[009紧凑补记](acceptance/2026-10-10-lyd-resolve-cache-source-only/009-INDEX.actual.json)只保3项记录，ZIP6,453B，原事实pins与解压字节核验通过。

精确事实、原INDEX、报告与可用性边界收于[紧凑来源包](acceptance/2026-10-10-lyd-resolve-cache-source-only/INDEX.actual.json)。001–008与交接/原R49 CI状态的31个选定记录共172,752B，压缩为59,895B，SHA-256 `c2fc65918779a9010ef42200f43196bed112ce08d340a2b652d8607267b4408f`；选定原pins及逐成员解压字节均实际核验。只保选定小事实与报告，不复制003的完整派生指令表、EXE、存档、运行时或旧build。原派生文件48小时、活跃compact事实7日的复核期限不因入库续期；本次交付记录按通用策略180日复核和归并。来源INDEX中未选定成员仅在外置来源，不能声称已全部归档。没有新增业务PASS或完整mod PASS。

同轮核对了交接第155项：完整 challenger/sponsor provider与显式第24个profile工具已实现，不重复底层施工。公共host的G4显式路由是另一个有限源码缺口；固定Source09尚未声明该能力。正式新Title、同Faith NPC真实资格、nonempty完整集合与saved ownerFaith独立join、挑战生命周期及冷载仍待合法正式B4/B5之后实测。来源状态报告也收于上述紧凑包；源码完成不授予实机信用。
