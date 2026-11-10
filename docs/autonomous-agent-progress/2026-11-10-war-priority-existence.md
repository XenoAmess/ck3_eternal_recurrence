# P211：复用已算 protectedWars 的存在性，只有源码与实际 Code 资格

仅将 `OrdinaryWarPriority.observe` 第187行 `wars.stream().anyMatch(...)` 改为 `!protectedWars.isEmpty()`，290物理行中其它所有字节保持。180–185原filter/sort/toList已用同一protect_cash_reasons非空谓词完整算出集合，186只创建无关out；中间未改wars、理由或protectedWars。排序不改变存在性，空集合false、非空true；191仍需该集合，不新增cache或延长其必要生命期。

双decode、全部Guard、理由分类、角色/count scope、比较器/排序/tie与其它输出原样；rowsOrValues原纯shape/list抽取不改，也不把独立证据验证删作重复。只去第二次存在性遍历及其临时物化；W、自然频率、实际allocation/CPU/wall贡献未知，不迁移[P210](2026-11-10-confirmed-start-measurement.md)或其它组件测量。正常自身生成DATA等价不授OOME/分配/恶意反射私态或全部资源异常等价。

本轮只有唯一 **1TU→4类生产编译**，实际exit0 accepted、fencedreleased。**0Tests、0JUnit/1P、0benchmark/完整case/新fixture/采样**。原Chooser selector在observe之后还构造AckReceived/GuardEvidence/PlanningReadGuard并replay，已在首JVM前整体排除：不执行、裁剪、包装或伪造fixture赚绿。早SourceReady原缓存/selectedpass NOT_HELD保留，后到TestEXCLUDED/Code-only选择另件，不把早有限source引用写成无Guard测试闭包。

实际Top30221→30149B，new SHA `0f6ca7ecd5bfaa2b34768a6c86813b4198db261a9bf25b0147734e277d7fbfea`；nested3原字节/SHA、public API/fields/decoded params/Nests保持。旧原compiler CFG及完整编源谱系仍NOT_HELD；本次初始debug/parameters选择来自已持LVT/参数形状推导，不冒原CFG。资格依据实际old binary→new的完整程序比较，不授整个source307/C0动态定义来源。

方法47→46，synthetic30→29：只删除旧187专用private synthetic `lambda$observe$15`（24B，和180 filter `$9`原Code同）。14个后续方法按**实际descriptor+flags+source-role LNT**逐一对应，再核完整Code/异常/CP/BSM；observe16→15至ids29→28的序号变化是后验记录，不是global名字mask。45个其它程序8raw同/37resolved同；没有dummy/dead helper保数量。私有结构变化可见，不是body-only或热重定义资格。

BootstrapMethods42→41，只移除旧17；全部41项factory/handle/args逐项匹配。CP1093→1088（不含0槽）是选定一项InvokeDynamic移除及四项明确private-name intern碰撞，字符串/数字常量与其它符号不放宽。observe1972→1970B，整行region[1643,1669)→[1643,1667)：实际toList1615/store local15于1620，187读取同local15、isEmpty1650，非空push true1658、空走false1662，再同out16/key/put1663。

整行外737指令加四个原样receiver/key/put/pop边界操作，共741保留指令、80分支完整对应；所有decode/filter/sort/Guard/理由/输出与局部操作保持。owner checker初把Native的741口径误作整行外数量，原件保留；02明确737+四个逐项相同边界=741，没有放宽语义标准。未设global slot/ordinal/BSM mask，也不以源码block或槽位推GC。

唯一JVM最后CLOSE **2026-11-10T01:26:19.291425Z**。actor **4.594041300006211s**、operator **5.814117999980226s**仅嵌套子窗，不相加代替整轮。Planning **2026-11-10T01:10:55.301567Z→CLOSE923.989858s→Native final1339.576558s**；SourceReady→683.832177/1099.418877s是内窗，更早begin UNKNOWN、不记0。Native final以peer[]早切点封存；后到owner proof及Root接受（01:45:22.574360Z）另件，不回填早稿。后续审阅/等待/Git在发表回执继续计入，不能把Native较早final当整轮已完成。

所有准备/来源预检、Guard-Test排除、Code映射、授权、等待和错误保原；Native静态checker/路径与Root BSM顺序checker纠正不是Java失败重跑。owner只读语法错误tool wall0.1646451s、计数口径错误0.2000975s另记，缺精确进程耗时仍NOT_HELD。预算旧pre-final601541B/43files、after-final/pre-budget615900B/44files，以及随后budget1222B/summary1005B保留；预算/summary写后计算为618127B/46files；后到selfreview实际快照627880B/48files（另增9753B/2文件）仍在4MiB内，早预算不重写，tmp/owned DLL/磁盘fixture0不授process-wide JNI未载、heap或hard瞬时峰值。

源24454B / `d6155a3808ae8b62a382a0e0a940c21da85ad5d6a54f50638dc5255fdacff678`；`J/construction-war-priority-existence211/candidate01-owner/SOURCE-READY01.json`2754B / `a0c80fc928f7f3e5594f7800cf5dfde09305ecd2386b445d10fdfe1c4ba4fd9e`，后到排除append2813B / `e50b1d2dbf6e2bcdb2388f22199f430dd26d4dff8cd6ae8eafe5cf31edd04684`。owner `owner-review01/ACTUAL4-45PROGRAMS-EXACT14SYNTHETIC-BSM41-EXISTENCE-OWNER-REVIEW01.json`44552B / `b387727f10afcd9187a49efac2e27d417a232cadd951bd612bc366f21e46eae9`，在同J unit下。

`N/p211-war-priority-existence-prod01/QUALIFIED-P211-CODEONLY4-SINGLEPHASE-ALLCOST-FINAL01.json`14359B / `07dec0b52793c191df8f7c63b7925bd0e9a2d3e6d9c7142f2dfce1058b8758cb`，Root后到接受 `R/P211-FINAL-SINGLECOST-AND-NORMAL-DELIVERY-INDEPENDENT-ACCEPT01.json`2560B / `908485accabd062305199ec02e88e819e99e92762f6666d04dc24fbb5eb69332`。J/N/R沿用隔离证据根。

正常exact4只该生产叶+unit/daily11-10/W46；无Test、Guard/parser/hash/oldencode/桥或策略改动。当前软件372；未来373候选及Root后到实际离线采用另账，不预填新装载、动态分支命中或热更新。无Runtime/Game/GET/P100/账本/UNKNOWN操作、SAVE/10秒达标，新增确认保存日0、秒/日null；主性能目标持续。
