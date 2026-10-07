# R26 闭合后的下一冷轮源码

本说明记录 R26 原进程和辅助进程全部正常退出、CAS 3788 释放、最终新鲜离线审阅与 v3 闭合实际核验后才应用的源码。R26 实机仍绑定 1982837ee；不得用这里的新源码追认其 B4 82/88 失败通过。[本轮最终报告](REPORT-FINAL.md)及所有旧 cutoff 原样保留。

- phase2 的 pending 判断由多条件 NOT 改为 NOT{AND{原四条件}}，修正 R3 只有一票、未签署却显示实施的真实反例。对应生产 AST 检查实际退出 0；新游戏行为待冷启动。
- M3 在跨 faith 分合入口及最终授权重新检查既有军会与圣人登记，明确拒绝尚不支持的资产迁移。只修改七个 authored 文件，由正式生成器投影；14 个政策案例与两个删除门禁反例得到 PASS_SOURCE_ONLY。ROOT 回执包装器因 Windows 文件名大小写碰撞退出 1，原子报告、stdio 与错误保留，独立子进程退出码为 NULL；没有重复测试来覆盖该记录。军会、圣物及冷重载实机结果仍为 NULL。
- 宗主工厂只移动完整 SetHead 条目，采用当前 1.20.0.4 原版的 holder→resolve→SetHead 顺序。原 capture 与条件 cleanup 保留，cleanup 仍在 SetHead 后、Title law95 前；四项保护属性、owner、授权与所有 87/88 存档保护不变。原版顺序是源码依据，尚未证明该顺序解决引擎继承副作用。未采用零显式 realm-effect 候选。

实际 ROOT 工厂集成回执位于 `BASE/r26-root-stock-factory-order-integration-20261008-001/RESULT.actual.json`，7154 bytes，SHA-256 `8c934d10412d9d5dbbb3e8be39191814f71215e13a753eed68a0a8daa451337f`。canonical generate、check、static、diff check 均为 0；生成 factory 3022 bytes，SHA-256 `bf1b40de272467afd9b1e0eb2e3c59c4f62285d0daef314cb066446467efccc7`，与已做两项聚焦测试的外置候选完全一致，未重跑旧测试。实际 .4 原版来源和 AST inverse 保留于 `BASE/r26-factory-head-after-resolve-sourceonly-20261008-001/INDEX.json`，SHA-256 `c2b540255a1a0faf8cdb73645ece6ca787a08a8c6d3bf8baebee18886e890872`。

`BASE` 为 `C:/workspace/ck3_lyd_runtime_20261004`。下一轮必须使用新的 clean HEAD/export、正式构建、官方 metadata、profile/session、实机编号和当次离线证据，从原 R10 0240 无 HoF 分立存档开始；新增 M3 helper 单独列入正式产品，原 69 个业务文件的比较宇宙及 87 项保护不得被覆盖或删减。实际构建库存以新 manifest 为准，不沿旧 69/70 数量强行接受。R26 坏工厂世界仅作失败证据。新 B4/B5、宗主冷重载、C3 和 I4 均未运行；整体 NOT_GREEN。
