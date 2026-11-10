# P218：finance 内部 Input 读取去副本，仅 Code-only

本单元只改 OrdinaryWarPriority.finance 第90、91行：通过原两次 request.observations() 取得 Input 后，读取其已拥有的 snapshot、nullableCampaignRoot 私有字段，交给原只读解析器。公开 Input 构造与 getter 的防御复制、FinanceRequest 构造、P216 observe、Optional/BigInteger、两个解析角色、编码及全部 Guard 保持原样；没有把 Input 构造或数据复用外提到公司循环。

源码24463B/02c49259…→24459B/c2b35591…，290行仅两表达式变化，整叶逆变换完全恢复正式基底。正常构造域中 FinanceRequest 保证 observations 非空，Input 的两个数组由原构造器复制持有；既有有限实际解析程序证明消费者只读。finance(null) 仍首先调用原 FinanceRequest.observations()；实际指令、参数 request/slot0/flags0 和 source90 不变，但没有执行动态 null 用例，不授实际 NPE 文本或去掉 clone 后的 OOME 全异常等价。

唯一生产1TU4编译实际 exit0、契约接受、CLOSE fenced/released。Top30189B/a07b1dfd…→30179B/70f8d567…；另外3类二进制完全相同。finance 仍96B、41条指令、maxstack7/maxlocals5，仅PC4、18从 getter invoke 改成对应字段读取；PC1、15两次 observations()、PC7/10/23解析及 record、全部 Optional 回调/BigInteger 传递/finance/encode 其余39条指令完整保留。其余72个程序中28个 raw 相同、44个完整 resolved CP 程序相同，API/fields/Nests/全部参数、LNT/LVT/LVTT/StackMap 保留，无 LDC 宽度例外。CP只删未再使用的外层 nullableCampaignRoot getter Methodref 和 NAT，未删公开 getter 定义；snapshot getter 仍由 observe 的原 null 分支PC5使用，41项完整 BSM 不变。

这是 Code-only：零 Tests、JUnit、1P、benchmark 或新 fixture。直接 public finance 的完整原 FinanceRequest oracle 未持；原 Chooser 的 ACK/Guard/ledger helper 整体排除，不裁剪。源码上去掉每次正常 finance 调用的两个中间 clone；实际数组大小、公司数、频率、JIT 消除、堆分配、CPU/wall 收益未知，P217 observe 的测量结果不能转授 finance。

单编译 actor8.810721300076693秒、operator10.04140730004292秒仅嵌套子窗。具名规划→CLOSE544.279640秒→final904.789759秒，SourceReady→CLOSE347.918197秒→final708.428316秒，AUTH→BEGIN24.943513秒；更早真实开始 UNKNOWN，准备、源码/Code审阅、错误与等待全部保留。Native final 写后两 metadata 根389029B/40files，tmp和ownedDLL文件为0，不代表全进程 JNI、Java堆或机器峰值。Owner 只读脚本把41条误写40触发断言，0VM工具窗0.2031272秒；原01/trace保留，02仅纠正计数和剩余39条标签后0.2172721秒通过，无源码、实际类、比较标准或Java重跑。

主要原件：

- J/construction-finance-input218/candidate01-owner/SOURCE-READY01.json，3135B/5caffd84…；整叶 inverse2095B/1286b662…。
- N/p218-finance-input-prod01/ACTUAL4-FINANCE96-TWOFIELDS-OTHER72-CPMINUS2-CODE01.json，57592B/6f457c7a…；owner实际独审32272B/4cb438aa…。
- R/P218-ACTUAL4-OTHER72-FINANCE-TWOFIELDS-INDEPENDENT-ACCEPT01.json，20613B/5f3693bc…；singlecost接受1777B/331cb7de…。
- N/p218-finance-input-prod01/QUALIFIED-P218-CODEONLY-FINANCEINPUT-SINGLECOST-FINAL01.json，14252B/acefbdef…；owner后到成本一致性2286B/0de0cb49…另件保留原final peer pending切点。

J为D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108，N为D:/ck3-state/resume91-native-integration，R为D:/ck3-state/resume91-root/post-vacation-20261107。本次正常发表仅生产单叶加本记录、日记、周记；当前 actual OFFLINE376，候选与后继实际选择另账。没有新装载、Runtime、SAVE或新增确认保存日，秒/新增保存日为null，10秒目标未由此通过，主目标继续。
