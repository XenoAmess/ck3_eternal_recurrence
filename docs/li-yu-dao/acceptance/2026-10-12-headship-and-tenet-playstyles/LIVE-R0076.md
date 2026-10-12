# R0076：两项实践与本派签署通过，代表门槛暴露实机缺陷

2026-10-13（Asia/Shanghai）。冻结源码 `115a5f0815ab890cf0b02d375cfa4678c02e1ae7`，CK3 1.20.0.4，正式构建83文件。**PARTIAL / 宗主制度门槛存在实际缺陷；没有创建宗主，不能作为0.1.2发布通过。** 公开版本仍为0.1.1 Alpha内部测试，Workshop item 3817934804；0.1.2未上传。

外置根 `A38` 为 `C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-cadence-storage-admission-20261013-038`；`RUN76` 为 `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0076`。CASE027、keeper `20261013-a39`，实际CK3 PID12372、创建时间1791838072.4719222。原件遵守统一时效策略，未把SAVE、截图、全量报告或第三方转换器复制入库。

## 实际游戏结果

正式83文件与隔离profile一致，启动marker1、fixture failure0、LYD错误列表为空。角色31254，原版Faith31 `confucian_faith`、本人rite32、main rite33。入儒门及正常择师三次翻页后转白沙rite174；Faith31及main33保留。实际入门前学识5、入门后6。

白沙T35静中自得通过正式决议及 `lyd.1034 native0` 支付一次：威望2200→2050，实际学识6→12。T08圣贤传承通过正式决议及 `lyd.1007 native0` 支付一次：金币248→148、虔诚150→350、实际学识12→16。ROOT随后分别打开两个决议，实际四年冷却要求未满足、确认按钮禁用；没有再次付费。没有用源码经验奖励或随机廷臣结果补成未读取的实机事实。

最终完整G2观察为4678名在世成员：主礼仪33有4677名成员、25县、258名合格学者；白沙174有本人一名成员、一名合格学者。准备阶段资格实际通过。主礼仪建议候选30667，实际学识30、AI；没有沿用旧场候选ID。

ROOT通过正式GUI发起一次宗主筹议；初次 `lyd.430 instance8` 的serial1/nonce1/phase1真实匹配。自荐一次后，`lyd.410 instance9 native0` 接受本派代表提名。普通交互查询30667返回 `shown=false`、`can_send=false`、`ready_to_initiate=false`，没有发起该交互，没有把查询失败记为AI拒绝。

封案GUI显示前置条件满足并允许确认，确认一次后真实进入phase2/nonce2：`lyd.430 instance12`，随后 `lyd.412 instance11 native0` 玩家同意、`lyd.411 instance10 native0` 本人赞成、`lyd.413 instance13 native0` 本派代表签署。这里每项只证明对应本人的实际操作，不证明其他礼仪授权。

一次正式复核产生 `lyd.430 instance14`。ROOT直接审阅选项tooltip：**道学（原版）赞成130/合格学者258，需要172票；尚无已接受提名的代表，尚未签署。** 该行也证明主礼仪确实出现在实际捕获的制度条款中，不能再把当前问题解释为已经证实的main遗漏。实施选项native0未显示，native1/2/3显示；没有实施工厂、没有改宗或新建共宗、没有注入AI票数或职位。ROOT在institution0012返回partial。

## 已定位问题与后继修复边界

缺主礼仪代表仍能封案并触发表决，已经是产品门槛缺陷，不能归为单纯GUI误显示：决议和effect均重验同一个 `can_seal` 条件。生成器的代表检查使用复合 `NOT = { exists = var:lyd_i3b_delegate var:lyd_i3b_total > 0 }`，旧离线oracle却按 `not all(...)` 模拟。游戏随附Jomini逻辑本地化把NOT对应“All of these”、NAND对应“At least one of these”，并有原版NAND用例。二者混同会漏掉仅一项不满足的情况；宗主生成器共发现九处意图为否定合取的直接复合NOT。后继需显式NAND及正确的NOT/NOR/NAND回归，不能仅刷新旧期望值。

另一个独立源码缺口是提名交互未声明外交距离政策；本机原版交互说明规定默认 `use_diplomatic_range = yes`，全信仰代表提名应显式使用 `no`，仍保留角色、名册、阶段及接受门槛。**本场查询未暴露逐项失败原因，不能断言外交距离就是本次shown=false的唯一原因。** 原位源码审阅及最小候选在A38/i3b-not-nand-source-review-001；本场冻结树没有热改。

## 二进制SAVE读取与容量

制度发起前真实保存为SAV0101二进制，69,439,625 B，SHA-256 `cc91e58cf1a94a75c0cfc04e6952c6956bf0e28673dd05d459e1d0f83c73d8e8`。原明文入口先后暴露编码和固定缩进不兼容，失败原件保留。ROOT从Rakaly官方v0.8.21取得转换器并核发布digest/版本；严格未知token策略，通过stdin/stdout仅在RAM转换101,124,427 B，没有落盘转换全文。v2只适配实际缩进与唯一title容器，继续使用原政治AST解析和比较函数。

初始政治摘要20,721 B，包含完整七个自有政治头衔AST、holder/heir/法律、45个有序继承候选及四项领国法律。初始摘要不是前后不变证明。原生保存同时留下last_save、autosave和固定checkpoint三份；固定名称覆盖不能证明下一次保存的临时峰值。22:05:54Z保守占用912,574,476 B，额外保存上界未闭合，故未请求precommit/post SAVE。完整前后政治保护、宗主结果与冷重载B5/C3仍未验收，36项完整矩阵也未完成。

## 正常退出、清理与闭账

ROOT取消退出自动存档，正常“退出到桌面”仅点击一次。点击后即时回执仍为原CK3窗口；原reviewer因此拒绝，未重放点击。后续新截图和进程读回确认为Steam PID8880、CK3为空；v2 reviewer绑定原唯一点击及新鲜延迟截图，宿主随后独立完成正常关闭。public run0、verify2、原allocator等待0分别保留；verify完成比run外层最终回执早约一秒，不能把调用完成顺序改写。最终资源收集使用两份均已终结的实际回执。

22:25:10Z新窗口位移图经ROOT亲审为Steam离线；恢复原1024×768并审阅恢复图。SCREEN于22:31:41Z按实际5322序列CAS释放成功。AD038于22:31:58.877106Z、原到期22:42:42.006399Z前关闭：预留1,073,741,824 B，保守计费1,012,106,102 B，归还未用61,635,722 B；carry从140,236,512,171到141,248,618,273 B，hard cap141,327,031,211 B，GC信用0。未续期、未准入新场，闭账后A38停止写入。

并行清理只删除精确复核过的 `C:/lr27b1/CMakeFiles` 546个过期、已被替代的派生编译文件，逻辑162,424,095 B，跳过0；**物理回收量未知，未抵扣存储账本**。原源码、构建配方、DLL/EXE/PDB/LIB及日志保留。Steam文件、着色器、当前native、基线SAVE和本场原件均未触碰。

| 小原件 | bytes | SHA-256 |
| --- | ---: | --- |
| A38/political-initial-ram-002.json | 20721 | `98b3708ac1ac4a7bbf372b8800abd395ad3eff6f0e3656b24a3f25654777c2da` |
| A38/scene-helpers-001/desktop/institution-terms-visible-001.png | 2292787 | `464a6ce80a1f4ef3cf89d2e9a9339fff6b4217494f2c5bfa884a05ddd027cd1c` |
| RUN76/case-output/release012-institution-0012-root-result.json | 1512 | `c0074386ba9147e88bc58d5a4d5b2e505adb3df60774a3a38284f8585d73c3f2` |
| A38/RESOURCE-CLOSE.actual.json | 23275 | `4decfd0c6422149a7164c9f57d7d8286b497e5d588cd13b175dddd541f0abfdb` |
| A38/retirement-review-001/BATCH.actual.json | 1785 | `b70a741778f682d95f1556ce50ba9b154985a6d5b25552f81ab3543656fc5174` |

## 冻结源码CI

115a5f08的[全仓CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38305944634)、[LYD CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38305941555)及[线性历史](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38305941660)均实际SUCCESS。这些旧测试没有捕获本场NOT/NAND缺陷；不能用CI绿替代宗主业务通过，也不能外推为后继修复的CI结果。
