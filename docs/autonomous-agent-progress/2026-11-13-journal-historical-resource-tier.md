# Journal 历史恢复 scope 的有限资源档位（Source79）

同局历史恢复的 `readSameGameHistory` 现在可选择既有的 8192 publications／16384 handles 档位，字节上限仍为 256MiB。生产变化只有 Journal 内的两个数值；其它 scope、DPP 的 `MAX_CHAIN=4096`、所有 source／Guard／parser／hash／immutable encode 校验、opaque 分支、失败 poison、完整回退及关闭顺序均保留。

实际源码在 `ContinuityBatchJournal.java:3471`，正式变体的同一锚点在3326。正式 BASE 为422914B／`57f9bb8754a94d004429ac4c901b08b09fa904e0944be067456aaf1942eaf549`，候选为422915B／`78fff9e22695b88340cf6ef9dac1581bd9bdef8ae0251fc7895bbb785e201ee7`。将两个数值逆回后，与正式 BASE 全字节一致；没有用实际438606B版本覆盖正式文件。实际候选438607B／`c79ea030e434e28baa830c8344e0d9d0ed3e56b7703a2a1e3f8d3e0ff5293bd9`另行冻结。

源码机会来自真实恢复链：Journal 的 capability replay 位于这个 scope 内，资源不足时的未持有读取会使当前 dependency trace 失格。Source70 的 INITIAL／VIEW 可走纯 CAS；已冻结的最早 INITIAL 是空 baseline、original／saved 均为空，相邻 DECLARATION 的6033B输入中 adoption为空、before／after为 GAMEPLAY。该具体分支没有必经的 adopted／operator／physical opaque 回调，但仍须实际依赖全部持有并通过 fresh 校验。此处是 declaration opportunity cooldown；同日 lifestyle 无 points 或 council 无动作不会因此自动发布新 VIEW。

原 R75 单次 BOOT 栈已具名经过 Journal3470／4049→DPP 的 owned replay243→rebuild445→Reader131→Archive.loadMaterial1741→Store599。这只证明该采样点的实际调用路径与一次未持有读取，不能确定是 entry、handle、byte 或 opaque 导致，也不证明整窗 CPU、prefix 命中或提速。没有为本候选新增采样、读取 Driver／SEM 大体或扫描 CAS。

`JournalHistoricalProfile79DataTest` 是无外部文件、资源、属性、Helper 或 JNA 的单 TU／3类／3方法测试。它通过真实 public `readSettledSameGame` 进入 wrapper，在首个 canonical `loadRecord` 回调处按设计抛出同一个 Runtime 异常；另外验证 owner／header 在 scope 前拒绝，以及 scope 声明的 IOException 原对象透出、退出后可再次进入原 reader authority scope。它没有成功重建完整历史，也不构造 physical writer、Native custody 或执行许可。

实际 Journal 首次单 TU／21类编译通过，全部类结构与旧版相同、只有顶层 class 字节变化。Test 首次单 TU／3类编译通过，唯一 whole3 首次3P／0FES，2026-11-13T05:04:59.843299Z释放；全部原 XML、输入不变的 POST 和 Close 已独立复核。正式 Journal 单 TU／21类独立首编通过；复用逐字相同的 portable Test3而不重编，独立 whole3 首次3P／0FES，2026-11-13T05:17:41.952776Z释放。正式全部原 XML、输入不变的 POST 和 Close 也已独立复核；两变体资格分账。测试不依赖绝对路径或工作目录，但本单元没有运行 Maven 整模块或 CI。

一次完整源码审阅 HTTP 为241107 input／1750 output、42.1776秒，完整 stop／无重试。其七项 finding 没有可采用问题；首条 withLocked 猜测已自行纠正，关于 checked `loadRecord` IOException 的建议不符合接口声明，其余完整 history／Store 内部覆盖超出本 wrapper 测试边界。没有采用模型 finding、生产 hunk 或 Test 变动，也没有追加 HTTP。

Source79 当前未实际装载，未授 prefix hit、I/O／wall 收益或10秒目标。8k档位只是有限资源选择：handle公式仍使实际最多8191个 retained entries，byte上限和全部 fresh／opaque 条件仍可能先阻止资格；扩大档位不会修改 proof-chain 语义界。现有35分钟批次的 C77 成功属于此前运行源码与配置，不能归因于本候选。

原件入口：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/journal-historical-profile-source79/SOURCE-READY79-02.json`、同根 `formal01/SOURCE-READY79-FORMAL01.json`、`OWNER-SOURCE-REVIEW79-01.json`；测试源与 Ready 位于 `journal-historical-profile-tests-owner30`。实际 whole3 原件位于 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/j79j1`。正式独立 whole3 位于同根 `j79fj1`，Jupiter46594B／`7e226a4759a9b0b215b10839e81cef4548685334bf8555ceb6d18224f2ca1cd4`，POST1261B／`e26d9f84f98286c2e9097ec19203d94b0e22614777df43118ade8d851501562c`。运行 owner 独占后继实际采用；本次正式发表不要求现场停止、GET、重放或重启。
