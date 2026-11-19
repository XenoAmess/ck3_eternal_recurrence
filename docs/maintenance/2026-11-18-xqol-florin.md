# 体验优化 1.1.2 / CK3 1.21.0 迁移

2026-11-19T16:17Z，machine_id `desktop-3fevhd2-1c74096080`：独立富文本分隔修正已集成1.1.3候选，原金额表达式/九语/核心与UI断言不改，清单27→28；`xqol-v1.1.2`不移动。完整受影响builder+fixture模块33项回归零skip、实际28文件双构建、完整静态+release-localization、全producer及validator严格mypy(imports silent)均0。最初两处临时变量bytes/str类型冲突只改名修复，原失败保留；builder另9项既有严格诊断仍按外置原始对照记，不称整builder strict绿。新负数新闻/hover及全部未完成UI/Native/发布仍NOT_RUN，旧R4原1530B不追改。以上软件绑定旧1.21.0/build26622941；公开后续热修待本机更新/重核，不能当最新版本通过。[软件原件](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/xqol-aub-gui-integrated-software.json)。

执行机器 `desktop-3fevhd2-1c74096080`，实际Steam CK3 1.21.0 / Florin、build26622941、EXE SHA `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。本轮恢复完整迁移，10月测试关闭仅保留当时事实。上一公开版本1.1.0；1.1.1旧候选和历史失败不改写。当前1.1.2仅完成下述源码及软件资格，尚未取得新版业务或工坊发布资格。

19份旧精确来源中18份当前SHA改变，贤能继任文件相同。历史完整源文件未保存于本机默认源码目录，不宣称这18份均已有完整旧新语义diff；旧JSON与失败原件保留。三份继任覆盖从完整新版原版重新生成，只保留原5处玩家开关／独立性／扣分1000000插入，去掉插入即精确还原当前原版字节。行政、天朝覆盖字节变化，贤能原字节相同；不把纯字节变化一概称为行为变化。

实际阻点为旧黄金义务生成器要求在golden_obligation_value内移除max=gold，新版该限制已拆到golden_obligation_value_check_current_situation：当前钱包取整、以上限quote截断。足额模式继续使用完整quote，保留新原版puppet_or_actor优先、actor备用的强牵制1.5倍逻辑；有钱即收继续通过真实原版互动支付。生成器同时检查新支付路径，拒绝把带钱包上限的quote误用于足额筛选。原旧生成器的真实RED保留。其余4份二期生成产物未变；改信／释放原版条件投影和九语格式仍逐项静态检查，不因此声称真实异步答复通过。

原默认游戏源码目录在本机不存在，工具现在沿已有XAR_CK3_GAME_DIR约定显式选择实际Steam安装，继任生成器、公共原版合同和validator消费同一来源；不创建另一份游戏目录或改变全局环境。新合同tools/xqol_vanilla_1_21_0.json绑定本次19份实际来源，只授来源／投影身份。原1.20合同保持历史可读。

实际软件结果：继任及二期生成器check、27文件／9语格式静态检查GREEN；9项builder测试与27文件双构建通过；原actor-scope CI文件内新增Florin未封顶quote和支付路径变化回归，实际8项通过，原CI命令自动包含新用例。三个完整修改工具文件xqol_vanilla_contract、gen_xqol_appointments、validate_xenoamess_quality_of_life的strict mypy通过，follow-imports=skip，不外推依赖图。正式脚本／GUI及原完整天朝core fixture共22文件通用语法parse通过，4进程、各192MiB上限；不授1.21语义profile或JAR来源构建资格。

继续使用公共GUI-only runtime，旧Native不加载。原完整天朝core生产effect／断言与27条marker保留，单独case上限60自然日；继任、移除、死亡、转封门禁及索款／改信／赎囚／释放后果在真实引擎验证。防御战争、生产滑条及官职候选GUI仍须分别取得实际结果，core单场不能授完整产品发布。原始软件结果在D:/ck3-state/upgrade-20261118/xqol-1210-software、xqol-core-a01，源码来源检查与旧失败在xqol-1210-review。原件30日复核，不默认永久保留。

下一场前，已回收已发布Ox缓存及CHT业务／缓存的可重建shader：10624文件、438096209逻辑字节，零失败。实际D卷由22099402752增至22556413952B（包含并发系统变化，不全归因删除）；日志、GUI、产品／夹具、CHT物理保存及唯一MRM warm输入仍在。历史已删shader的prepared pins不可读取。新场仍独立核容量、活跃任务与预算。

2026-11-18T09:07:37.244267Z，R0001原Game正常退出0、无WM_CLOSE/STOP，keeper/CAS闭合，零SAVE。原生产继任／移除／死亡／转封、足额／有钱即收索款、改信筛选、两种赎囚及释放矩阵均达到原标记，但最终accepted-rite与DONE两条未完成；保持HARNESS_RED，不把25/27及零FAIL标记当业务通过。实际error.log91988B：核心驱动仍设committed threshold而dispatcher读draft，造成101路未设变量诊断；另有来源尚未确认的文本formatter回退诊断。最后可见1066-10-01，由普通事件暂停，16自然日。

修复仅改共享fixture producer中两处50门槛初始化为消费者实际读取的draft，不更改正式27文件、原生产effects、原断言、调度顺序和完整marker清单。真实生产generator→fixture入口字段回归加入原CI测试文件，含当前stock的9项实际通过、无跳过。新a03 fixture仅event文件两处字段变化，精确逆替换可还原旧输入；该文件重新parse通过，其余21份原精确输入资格复用。a02生成时误带一处空格的准备校验失败亦保留，没有启动Game。原R0001 common verify因失败review缺少direct_image_review字段返回BLOCKED，保留原回执，不追认任何业务信用；原退出及closure依各自原件独立记录。

本次最早prepare尚在运行时误调用allocate，被缺少prepared-case拒绝，未消费live ID或启动Game；原拒绝留xqol-core-allocate-early-blocked.json。后继分配消费实际prepare退出0。新场wrapper在run前明确拒绝没有run_dir的失败分配结果，不按外层调用成功启动下一步。

2026-11-18T09:42:03.374090Z，R0002原Popen正常退出0，keeper/CAS闭合、零SAVE；最后画面1066-09-29，14自然日。26/27必需marker各一次，唯独原conversion_threshold_50_filtered失败；其断言仍读取已保存门槛，前次仅初始化draft的修正遗漏该状态，error.log4775B含三条未设committed变量诊断及42条来源尚未确认的formatter提示。accepted faith/rite与DONE均已完成，但FAIL1必须保留，整场仍HARNESS_RED。

本次按实际生产xqol_events.txt确认选项完整消费链修正两处fixture入口：draft=50，提交committed=draft，dispatch，清理draft。原全部断言及生产运行27文件不变。回归同时读取真实生成dispatcher、生产Save提交和原矩阵断言，验证字段及顺序闭环，当前stock共9项无跳过通过。a04只重parse修改的event，另21份输入逐项SHA确认后复用；不以源码修正追认R0002通过。

已按策略提前回收R0001/R0002共8616个可重建shader、387047361逻辑字节，零失败；具体问题为fixture输入，shader与该故障无关。原日志、截图、fixture、formal及失败记录保留，已删除shader的历史prepared pins不可读；唯一MRM warm输入和CHT物理保存仍在。新场重新计预算，不重复扣旧unused。

R0003在实际1066-10-07／22自然日已达到完整27/27各一次、FAIL0，原fixture变量错误消失。Root随后为补充角色画面误从菜单恢复模拟，后见1066-11-21／67自然日，超出本case60日上限；记录OPERATOR_CALENDAR_RED，不以较早核心完成点追认整场PASS。10:17:05.727020Z正常退出0、keeper/CAS闭合、零SAVE，原件保留。error.log3150B仅35条weak/positive_value/negative_value格式提示，来源归因尚未闭合，不先称原版或错误日志为空。

后继临时GUI收束在完整原标记各一次／零FAIL且无Script system error时，从已暂停菜单直接正常Exit，不恢复模拟补图。退出前只接受三张已审XQOL同版截图中一致的unchecked-autosave16×16原像素SHA；不匹配则保持菜单，不点退出。该像素核对不是业务信用，仍须原Popen正常终止、keeper/CAS及实际图片审阅。正式27文件、原断言和自然日上限均未改变。

R0004在实际1066-10-09／24自然日完成原27项各一次、FAIL0、零SAVE，11:02:06.486827Z原Popen正常退出0，无WM_CLOSE，keeper/CAS闭合。直接审阅原场景日期、未勾选退出自动保存及原退出操作；公共verify为PASS，明确product_release_pass=false。途中原版ep3_emperor_yearly.8000暂停，核对定义及四选项后经本场GUI-only路径选第一项并实际消失；不授Native能力资格。error.log1530B仍有未完成归因的formatter提示，未出现Script system error或fixture未设变量错误；不宣称零错误。原件见[xqol-florin-core-R0004-pass.json](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/xqol-florin-core-R0004-pass.json)，复核期限2026-12-18。生产滑条、实际防御调用／反向合同、官职候选界面继续分别验收后才评估发布。

R0005在1066-09-15／零自然日正常退出，原Popen0于11:18:19.213446Z、keeper/CAS闭合、零SAVE。既有UI夹具先从原玩家切到宋帝，随后又在宋帝scope内重复set_player_character，真实引擎明确拒绝“Target character is also a player”；保留HARNESS_RED，不授UI25信用。共享producer仅移除第二次自切换，原宋帝资格、AI三域信仰种子、玩家信仰／头衔／政体及生产27文件不变；精确逆插入还原旧输入，新event通用parse通过。

原9项focused回归通过后，扩展followups实际出现5项错误：本轮较早迁移的xqol_vanilla_contract指纹未同步三个专项支持引用。已逐调用核对：这些旧专项仅调用未改变的block()，不调用新版索款／来源生成路径；三个合同只改该支持pin，完整工具逆变换、block AST不变、旧整份合同哈希及错误pin拒绝均验证。原扩展失败不覆盖；修正后原入口27项与focused9项全部通过，focused入口加入既有CI。以上仅授支持源码资格，不授旧1.20专项在1.21运行资格。证据见[xqol-florin-ui-fixture-and-support-regression.json](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/xqol-florin-ui-fixture-and-support-regression.json)及并列R0005失败记录。

R0006采用修正UI夹具，宋帝三条资格标记各一次，重复自切换错误消失，实际error.log为0。真实生产决议打开默认50%滑条；0、1、49、50各实际显示、取消并重开50通过，51只取得draft画面，没有合格重开读回。其余边界保存／恢复、官职候选／扣分／任命及防御矩阵均未执行，不以部分画面授UI25通过。部分点击ACK停留在决议详情、部分来源过期被拒，并因错误假定滑条已打开误开无关角色窗；均保留原件，不从ACK推断业务后态。12:27:46.592932Z原Popen正常退出0，无WM_CLOSE，keeper/CAS闭合、零SAVE，最终1066-09-15／零自然日；在原3600秒期限前正常退出，没有延期。公共verify因官职业务缺失返回BLOCKED；[实际部分结果](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/xqol-florin-ui-R0006-partial.json)保留明确缺口，1.1.2尚未发布。
