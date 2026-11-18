# 体验优化 1.1.2 / CK3 1.21.0 迁移

执行机器 `desktop-3fevhd2-1c74096080`，实际Steam CK3 1.21.0 / Florin、build26622941、EXE SHA `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。本轮恢复完整迁移，10月测试关闭仅保留当时事实。上一公开版本1.1.0；1.1.1旧候选和历史失败不改写。当前1.1.2仅完成下述源码及软件资格，尚未取得新版业务或工坊发布资格。

19份旧精确来源中18份当前SHA改变，贤能继任文件相同。历史完整源文件未保存于本机默认源码目录，不宣称这18份均已有完整旧新语义diff；旧JSON与失败原件保留。三份继任覆盖从完整新版原版重新生成，只保留原5处玩家开关／独立性／扣分1000000插入，去掉插入即精确还原当前原版字节。行政、天朝覆盖字节变化，贤能原字节相同；不把纯字节变化一概称为行为变化。

实际阻点为旧黄金义务生成器要求在golden_obligation_value内移除max=gold，新版该限制已拆到golden_obligation_value_check_current_situation：当前钱包取整、以上限quote截断。足额模式继续使用完整quote，保留新原版puppet_or_actor优先、actor备用的强牵制1.5倍逻辑；有钱即收继续通过真实原版互动支付。生成器同时检查新支付路径，拒绝把带钱包上限的quote误用于足额筛选。原旧生成器的真实RED保留。其余4份二期生成产物未变；改信／释放原版条件投影和九语格式仍逐项静态检查，不因此声称真实异步答复通过。

原默认游戏源码目录在本机不存在，工具现在沿已有XAR_CK3_GAME_DIR约定显式选择实际Steam安装，继任生成器、公共原版合同和validator消费同一来源；不创建另一份游戏目录或改变全局环境。新合同tools/xqol_vanilla_1_21_0.json绑定本次19份实际来源，只授来源／投影身份。原1.20合同保持历史可读。

实际软件结果：继任及二期生成器check、27文件／9语格式静态检查GREEN；9项builder测试与27文件双构建通过；原actor-scope CI文件内新增Florin未封顶quote和支付路径变化回归，实际8项通过，原CI命令自动包含新用例。三个完整修改工具文件xqol_vanilla_contract、gen_xqol_appointments、validate_xenoamess_quality_of_life的strict mypy通过，follow-imports=skip，不外推依赖图。正式脚本／GUI及原完整天朝core fixture共22文件通用语法parse通过，4进程、各192MiB上限；不授1.21语义profile或JAR来源构建资格。

继续使用公共GUI-only runtime，旧Native不加载。原完整天朝core生产effect／断言与27条marker保留，单独case上限60自然日；继任、移除、死亡、转封门禁及索款／改信／赎囚／释放后果在真实引擎验证。防御战争、生产滑条及官职候选GUI仍须分别取得实际结果，core单场不能授完整产品发布。原始软件结果在D:/ck3-state/upgrade-20261118/xqol-1210-software、xqol-core-a01，源码来源检查与旧失败在xqol-1210-review。原件30日复核，不默认永久保留。

下一场前，已回收已发布Ox缓存及CHT业务／缓存的可重建shader：10624文件、438096209逻辑字节，零失败。实际D卷由22099402752增至22556413952B（包含并发系统变化，不全归因删除）；日志、GUI、产品／夹具、CHT物理保存及唯一MRM warm输入仍在。历史已删shader的prepared pins不可读取。新场仍独立核容量、活跃任务与预算。
