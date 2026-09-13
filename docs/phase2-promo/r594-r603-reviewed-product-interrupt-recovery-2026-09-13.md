# R594–R603 reviewed product interruption recovery（2026-09-13）

## 验收边界

- T0 P1 保持 `9/9 GREEN`，没有重跑或改写 P1。
- T0 P2 保持 `0/8`。两次连续 take 都只有前四段形成成对 clean marks；失败 take 不拆分计数。
- 最终宣传片硬锁继续生效。本轮只采集源录像，没有制作、更新、发布或预热最终成片。
- 两次失败都保留 RED；修复只接入现场已经出现且已有严格合同的产品事件，通用单按钮自动清理继续关闭。

## R594–R598：Central GREEN，`zg361.40` RED

artifact 根：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r594-plus-c48b1a6-20260913`

| 轮次 | PID | 用途与处置 |
|---|---:|---|
| R594 | `207788` | frontend warmup；Frontend 后终止 |
| R595 | `11524` | gameplay 段 1–2；clean end 后终止 |
| R596 | `106520` | manager governance 段 3；clean end 后终止 |
| R597 | `145836` | promotion compensation 段 4；clean end 后终止 |
| R598 | `82688` | HC/Workforce source；遇到 `zg361.40` RED 后终止 |

连续 FFmpeg PID `129464` 在清理时停止。原始 MKV 为 `297,910,383` bytes，SHA-256
`79AC0AF08179904F9D1D58757DDE4183E742A08720B35293586D66056DA0DE14`；报告 SHA-256
`0D27F81DCD473CFD5625EDFFF5FA19599617BE55E58EADD0BF171ABCBB377440`，时间线 SHA-256
`75D6BCE5ADDB17D60D539CF5C466B9D799D84CDB5D0346A84FA9741591CCD6E9`。报告耗时
`677.605 s`。所有 CK3、FFmpeg 和 injector 最终为零实例。

R598 先再次证明原版 `ep3_story_cycle_admin_eunuch.8030` authored 4/native 3 GREEN，随后首次证明
Central `zg361p2c.2` authored 1/native 0 GREEN。两者的 identity、scope、option、selection 与
postcondition 检查全部为 true。之后产品事件 `zg361.40` 以 instance `623`、root `32904`、两个选项出现，
被窄 Central 白名单保留为 RED。

`zg361.40` 的源码表明选项 1 只打开免费京察规划器并安排 300 天履约点；选项 2 会立即写入拒绝、经理治理事实和
下一次 review KPI 后果。R598 的 paused frame 含 110 个继承作用域；用已有经理恢复合同回放后所有严格检查均为 true，
固定选择 authored 1/native 0。提交
`a44ca20f33f48e85456f8ab24eda85c651f5545a` 只把该键加入 P2 reviewed-product 白名单。

## R599–R603：`zg361.40` GREEN，`zg361.1` RED

artifact 根：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r599-plus-a44ca20-20260913`

| 轮次 | PID | 用途与处置 |
|---|---:|---|
| R599 | `98400` | frontend warmup；Frontend 后终止 |
| R600 | `13080` | gameplay 段 1–2；clean end 后终止 |
| R601 | `195868` | manager governance 段 3；clean end 后终止 |
| R602 | `66328` | promotion compensation 段 4；clean end 后终止 |
| R603 | `127900` | HC/Workforce source；遇到 `zg361.1` RED 后终止 |

cleanup 报告将 gameplay lineage 固定为 `[13080, 195868, 66328, 127900]`，每个旧 PID 的 process tree、job、
watchdog、control file 与全局 CK3 inventory 清理检查均为 true。连续 FFmpeg PID `102576` 最终停止。

| 文件 | SHA-256 |
|---|---|
| `capture-plan.json` | `D718C75D81349C3C3638086C6B1314C89BA0F155E99538969348BB13DAF06F20` |
| `capture/report.json` | `8990E275658F87417C11206D3C5490DB067D1785B0322C5038A165597D12D7FA` |
| HC native event wait gate | `8C9B0FE86EF61712F177F0F4F2ECB9F47D2988BC1B74C4EB7850AE61B3CC27CF` |
| `capture-timeline.json` | `7183C557E7289E61463518399114FBF045AB14A9293704D04570A7D1DA19F472` |
| raw MKV | `31D66FAE8FB1FDA0C9FB21937A54F3FF6697579EA2127F3A1F8E082839ACB7A6` |

原始 MKV 为 `350,673,985` bytes。时间线包含前四段八个 clean marks，缺少 HC、Projects、Incidents 与 Endgame
四段，因此 `clean_capture_complete=false`。

R603 的 reviewed event 顺序和结果为：

1. `.8030` authored 4/native 3 GREEN；
2. `zg361p2c.2` authored 1/native 0 GREEN；
3. `zg361.40` authored 1/native 0 GREEN，identity 与 selection 检查全部为 true；
4. 原版 `debate_event.5110` authored 2/native 1 GREEN；
5. 原版 `ep3_decisions_event.2001` authored 2/native 1 GREEN；
6. `zg361.1` 被白名单保留为 RED。

这证明 `zg361.40` 接入已经 production-live。其 300 天履约检查后来按产品规则处理未举办京察，随后年度 review、
promotion track 与 scoreboard 继续推进；该产品结果不被伪装成警告。

`zg361.1` 是玩家领主年度考核总览。immediate 只复制四个已经发布的档位人数，唯一按钮“知道了。”没有 effect。
R603 的 frame 为 instance `626`、date `53375616`、root `32904`、106 个继承作用域、唯一 native 0。
既有 manager annual summary 合同经经理恢复投影后对该 frame 的严格检查全部为 true，固定 authored 1/native 0。
提交 `5e8d77365a1fdda0510c32adba7d3b8750f9219f` 只再加入这一事件键。

聚焦测试为 reviewed wait 普通/optimized 各 `6/6` GREEN，`py_compile` 与 `git diff --check` GREEN。
两个提交都只修改 Python runner 和聚焦测试，没有改 mod、DLL、游戏文件、启动配置、MCP schema/version 或公共接口，
因此不触发 open_kaishek 兼容层变化，也不新建 MCP 资产。

## 下一步

下一次 CK3 从 R604 warmup 开始，只运行一轮新的连续八段 source capture。若再遇到新事件，继续保留现场 RED，
只审查该真实事件，不扩大为全注册表放行或单 bug 永久长跑。
