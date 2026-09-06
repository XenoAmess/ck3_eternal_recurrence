# R143 管理者终止与验收存活保护（2026-09-06）

## 实机结论

- frozen source：`ef1a7926cf8e8f6833e1d33b8d8854b3f77bf12b`；源码 ZIP SHA-256：`9E9701FCC34A5B1B7376D1EBD143AC1D9594C9F5542A98D586E66FD738D81772`。
- no-launch preflight GREEN：3182 个源文件与归档等价，R130 的 1031-file 产品投影及四个关键 B2 effect 均逐字节一致。
- CK3 PID `158092`、connection generation `1`、玩家 CharacterID `32904`、默认 5 速。
- 从 `date_raw=53147040` 推进到 `53148048`（42 个游戏日），13 个暂停观测点均为 B1 active、Central/PP inactive、review-now false，期间没有待处理事件。
- 下一帧玩家变为 CharacterID `36354`；runner 的 one-life 驱动器将其精确分类为 `death-terminal / played_character_changed`。PID 与 connection generation 未变化，因此不是重启、重连或 revision 漂移。
- `manager-cycle-recovery.json` SHA-256：`C40309BA0BEA8E3A53A7E87781DDC9806CA2330CE982F684DFA32C3D6CEF08DD`。
- `runner-report.json` SHA-256：`70BC285D6526A2D543A6CA09A4B49D078DE95DB7FEE3C93C9994AD3C832E25BB`。

现有 native 接口仍不发布死亡原因字段，所以不能把具体死因冒充为已观测；能确定的是 R133、R137、R143 已三次捕获同一 `death-terminal / played_character_changed` 形状，而且都发生在同一 R131 管理者、同一 active-B1 清理等待阶段。R143 不构成产品功能 RED，也不提升逐号 readiness。

## 授权后的 acceptance-only 缓解

按照项目所有者此前对三次角色死亡后的明确授权，R144 起只在 `zg361_phase2_manager_seed_bootstrap` 验收夹具对已由 runner 绑定的当前真人管理者添加：

- modifier：`zga_phase2_manager_seed_survivability_modifier`；
- health：`+10`；
- epidemic resistance：`+100`；
- duration：`1100 days`，与 runner 的最大 manager-cycle recovery horizon 完全相同；
- 幂等条件：角色存活、非 AI 且尚无该 modifier；
- 应用日志：`ZGAP2MANAGERSEED: acceptance survivability health=10 epidemic_resistance=100 days=1100`。

该文件仅由专用 seed-capture runner 挂载；release builder 与常规天朝验收 runner 都不包含该 fixture。R130 产品投影、二期业务变量、receipt 与业务 effect 均不修改。用途分片仍符合约束：同一个 manager-seed effect 文件现在含 4 个 effect，处于每文件 1–10 的目标内。

## 下一实机门禁

R144 必须首先在 loader 日志中确认上述 modifier 被一次性应用，并继续验证 CharacterID `32904` 不再于既有 42 日终止点交接。随后仍按 5 速在同一进程内推进、精确 drain 已登记事件，直至获得 `B1=false / Central=false / PP=false / review_now=true` 的 clean boundary 和最终 `zga_phase2_manager_seed.1`；健康保护本身不得冒充 seed 或产品验收 GREEN。
