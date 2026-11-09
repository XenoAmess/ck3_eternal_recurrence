# P184：提交后 readback 长度复用，正常DATA源码采用与既有3B功能证据

Root已正式接受本单元有限正常DATA源码等价与一次冗余副本消除，依据单行源码及实际Code等价、既有合法3B软件回归与独立三阶段费用／预算核验。性能、自然频率、实际allocation／CPU／wall收益均 **UNPROVEN**，不拿小功能测试冒性能样本。当前离线软件actual359尚未采用本候选；正式源码、后继软件基线与Runtime各自另验，不预填装载、SAVE或10秒目标。D稿原件保留，最终exact4发表已获授权，无新增文档ACK或编测门。

[LedgerFiles.java](../../java/ck3-control/adapters-storage/src/main/java/org/xar/ck3/control/continuity/writer/LedgerFiles.java)基底15173B／`f231189a583013abfb8aac2ba0fbd3a05c338c3d7099206bf31177d583263748`，候选15163B／`e2e8088dd7218e58e0cac07e37be7ce4d60167288143dda3f816fa39c074a0e5`。仅195行 `read(write.target(),write.bytes().length)` 改 `read(write.target(),raw.length)`；整叶inverse精确恢复基底。原180行 `byte[] raw=write.bytes()` 已在同次调用取得副本，196还要使用它作完整Arrays.equals，因此没有新局部、字段、API、类型、cache或额外数组延寿。AtomicWrite151构造器own clone、152防御getter、154私有长度读取全保；164的raw是canonical加末尾换行，必须保其完整长度，不能用canonical.length。数组长度恒定，不依赖hash／provider只读前提。

StorageWriteGuard原计划／嵌套calls、实际write及force、Win32同卷rename、fresh identity、195 fresh read、196 fullEq、199–200原pending／UNKNOWN文字与其它全部source字节保持。去掉的是**commit之后**一处长度用getter分配／OOME机会，不能宣称所有异常或UNKNOWN时序等价，也不借本单元改变历史账本、原Guard、parser、hash、oldencode或deadline。

必要生产首次1TU6实际0accepted／CLOSE。Top19306B／`4eeaf0c64836a8d73f95f657735ba61f7cfef90ad4bce772ddcddd8ef7d6a713`，五nested SHA旧同；raw constant pool、fields／class attrs含bootstrap、方法flags及non-Code attrs exact，其余24个完整Code属性相同。唯一lambda$atomic$3 Code126→123，old91–94 getter四字节换new91 aload3，原arraylength仍在，机械Code inverse精确恢复原体；必要debug offset调整单列，不声称全部25个Code字节相同。旧actual C0完整编源／原compiler flags不从源文或SourceFile推定。

选用现有 `ContinuityWriterTransactionTest#immutableEventConflictNeverOverwritesAndPendingRemovalIsRejected`，原三Test TU逐字编译，实际6类：原Test、两个匿名类、WriterFixture及其匿名类、WindowsWriterInteropTest。未改任何Test源码，没有新镜像Test、Support重编或Python interop selector／额外Python进程。实际复用p111 Support2（Top49fd5c54…／Frame12523c1d…），与早先只读adapters Support源不能混认；Native独立闭合实际ABI／首origin。原default TempDir源不改，以既有NEVER配置保全；Windows／JNA显式临时目录与原64MiB软件guard保留。

原selector唯一JUnit实际1P、0F、0E、0skip，case **2.820s**、Jupiter engine **2.846s**。所有操作在全新独立软件TempDir：WriterFixture创建新software card／lock／source，公开TestSupport.atomic经真实WindowsLedgerLock.acquire／requireHeld与原StorageWriteGuard进入atomic。首写canonical `{}` 为2B，正常返回结构必过195 fresh read与196 fullEq；实际保留target为 **`{}\n`三字节**（LF），SHA `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`。再次同target no-replace原IOException拒绝，原件未覆写；独立clean根的既有pending-removal preview预期ContractViolationException且无event。负例不是合法许可或真实运行账本；没有Game、Runtime、P100、历史UNKNOWN、重放或期限刷新。

3.4MB测量方案在源码审查即否决：所选公开TestSupport.atomic默认prepareAtomic入口上限 **65536B，含LF**；LedgerFiles的显式maximum重载生产可到 **262144B**。大原件超过原cap，在写入前按原 `original writer output cap` 拒绝；两side固定target replace=true虽可避免累积32份文件，也无法消除硬cap。因此没有另造小输入benchmark、ABBA、抬预算或改Guard来凑收益。静态省一次长度副本的尺寸上界只按各原入口说明，默认64KiB不能外推全部生产caller；真实尺寸、频率、耗时与allocation收益未测。

已知三资源子窗为生产actor4.8984025／operator6.7910609s，原Test编译4.6823157／6.4388102s，soleJUnit5.2609916／7.0499216s；合计actor14.8417098／operator20.2797927s仍只是子窗。**完整准备／等待／资格／Git费用全部保留，不以子窗冒全费用；更早完整研究起点UNKNOWN，不记0。** Root已独核全部三次0accepted／CLOSE／资源释放及静态预算：metadata1295128B／87文件在4MiB内，原guarded fixture3352B／11文件在64MiB内，JNA273408B及所有其它operator／tmp计metadata；不排除all tmp，不宣称连续硬峰值或Java heap peak。Native后到final-cost／budget append按当时原件另记，Root已核证据足以作本次有限source决定，不因重复大资格延后发表。 原0VM工具错误保留：Root第一次class cursor解析假设失败后纠正、XML把合法system-out误作不应有子节点后纠正；owner曾误假设actual位于test输出根而读到不存在目录，随即改读实际prod控制根。均非Java RED，不重跑Test、不改源，不抹准备成本。本最终稿由D稿另存，原D稿及全部错误原件不改，也不提前填性能通过。

可核原件：`J/construction-ledger-readback-length184/candidate01-owner/SOURCE-READY01.json`（2132B／7e1dbc8e…）与wholeinverse3284B／11832c2f…；`R/P184-STAGE1-ALL25CODE-RAWCP-OPERAND-INVERSE-INDEPENDENT01.json`（1700B／`029a77b074759ef92b30187697ce1722c81c5851a2425f129720c9a4f84ae988`）；`R/P184-ACTUAL-SOLECASE-1P-3B-ORIGINAL-INDEPENDENT01.json`（1897B／`81ff2e964f7e9b008aa6ae988df28e8a6434a04cf3fd24d0189a875df7638d02`）。N／R／J为隔离证据根；本次仅交付一个生产leaf与unit／daily／weekly，全部Test正式字节不动；Root已按exact4授权正常commit／push，后到离线软件采用仍需独立实际回执。


最终source接受：`R/P184-FINAL-LIMITED-REDUNDANT-LENGTH-COPY-SOURCE-ACCEPTANCE01.json`，4812B／`5dc34d2fe9ecb07b58e6bd1f27b3315b24794b2af1d7ed7ff9f984924f79c7d8`。三阶段费用及静态快照：`R/P184-ALL3CLOSE-COST-AND-STATIC-BUDGET-INDEPENDENT01.json`，2419B／`a0e9ebf1de065e1a635430377d8316c93c32da046464cdfee64d722b1bbdf73e`。生产资格：`N/p184-ledger-readback-prod01/QUALIFIED-P184-PRODUCTION6-CODE-AND-METADATA01.json`，31159B／ba41d6e5…；后到final大图不重写这些历史切点。无P100／Runtime／Game／GET／保存信用，零新增SAVE不报有限秒／日；P185独立工具与实际caller研究继续，不以本单元完成结束主线。


后到Native最终资格已实际封：`N/p184-ledger-readback-prod01/QUALIFIED-P184-PRODUCTION6-EXISTING3B-ALL3COST01.json`，26392B／`0e6164615b7d3a2e5d60492edc7a03579a4cce1ce5f533fded0be7c3362f8993`。最早已持Native切点 **11:58:40.429467Z → lastCLOSE 1432.558427s → qualification 2022.52318s**，更早真实开始UNKNOWN而非0；三actor14.8417098／operator20.2797927s仍仅子窗，不代替完整准备、等待、0VM错误、资格与Git费用。final metadata **1335060B／91文件**，guarded fixture **3352B／11文件**，JNA273408B保计metadata；比Root先前1295128B／87文件快照追加39932B／4文件，两个切点均真实保留，不覆盖旧数，不宣称连续瞬时硬峰值。该薄final补齐本次费用／预算，不新增性能、频率或全异常等价信用。
