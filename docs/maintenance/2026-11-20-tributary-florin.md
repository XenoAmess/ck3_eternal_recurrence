# 驱策朝贡国 Florin 源码迁移

machine_id: `desktop-3fevhd2-1c74096080`；实际本机1.21.0.3/build26785313/EXE859f0d…，canonical Workshop `3801490405`。

1.0.2候选已接入共享精确引擎制备。现有指令/补贴/开战/结果政策保持：prestige150、12个月收入按5进位50–500补贴、五年冷却、玩家发起/AI朝贡接收；执行时先context及原生can_declare_war，再原转账/开战，失效退款/清冷却保持。产品仍动态调用原版，未覆盖stock VFS。

实际七完整原版定义（宣战、三种truce结果、POW、county CB参照及夹具start_tributary）正文与之前Florin审阅一致。既有validator新增typed literal pin及显式--game-root，拒绝每项正文漂移/缺失/重复/坏UTF8，不提供该参数时明确NOT_CHECKED。新增common core case保留原12标记加engineStartup共13，**原GAP保留**，不将core效应验收替代真实selector Send、实际AI响应、战争结果/停战方向及期限/tribute、同局物理SaveLoad。

完整受影响builder/display两个模块16测试零skip、明确当前原版的完整静态、16文件双构建、完整validator strict mypy(imports silent/noincremental/NUL cache)均0；两个原制备入口实际生成新engine core/context-only输入0，收据保持NOT_RUN。原1.0.1 tag与历史实机不动，本候选无正式tag、无新版实机或发表。[证据](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/tributary-121003-integrated-software.json)。
