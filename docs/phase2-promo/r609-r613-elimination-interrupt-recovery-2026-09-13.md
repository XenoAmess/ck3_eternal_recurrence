# R609–R613 `zg361.5` 淘汰事件恢复（2026-09-13）

## 验收状态

- T0 P1 保持 `9/9 GREEN`。
- T0 P2 保持 `0/8`。本 take 完成前四个连续 clean spans，在 HC/Workforce span 5 遇到新的产品事件 RED；失败 take 不拆分计数。
- 最终宣传片硬锁继续生效；没有制作、更新、发布或预热最终成片。
- R613 证明原版 `epidemic_events.1060` 的既有三作用域形态可实机 GREEN；R608 的 `faith_to_blame` 四作用域变体仍只拥有实见 RED 与 exact-frame 静态回放证据，未冒充 live selection。

## 连续 take 与清理

artifact 根：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r609-plus-e658753-20260913`

| 轮次 | PID | 用途与处置 |
|---|---:|---|
| R609 | `177744` | frontend warmup；frontend 后终止 |
| R610 | `56132` | gameplay spans 1–2；clean end 后终止 |
| R611 | `28888` | manager governance span 3；clean end 后终止 |
| R612 | `61560` | promotion compensation span 4；clean end 后终止 |
| R613 | `215080` | HC/Workforce source；`zg361.5` RED 后终止 |

连续 FFmpeg PID `147728` 已停止。cleanup 为 GREEN，PID lineage 精确为 `[56132, 28888, 61560, 215080]`；CK3、FFmpeg 与 injector 最终均为零实例。source/runtime/product trees 未变化，protected storage 为 `UNCHANGED`。

| 文件 | SHA-256 |
|---|---|
| `capture-plan.json` | `FFFBC1A4F445CE259874E05A528DA5A6C2A672E274F2FFFB25866AC3C24DBEE2` |
| `capture/report.json` | `4B487FEEF97FC9789F64E245108C00446F418DC5ADB52D30DD28A0F2719F8736` |
| HC native event wait gate | `7C4DD599138D0E3666A0A16337AA301DF52B43F3BB47836B721797501211BFB7` |
| `capture-timeline.json` | `41751B7007CC30BEADA0F875B38C7002146F8DC212FFBFE4AD113F4237AE812C` |
| raw MKV | `13BA6A1AD633A7A2DAC466116546F699DB7D6F988FC57F1C095ED93A76350885` |

原始 MKV 为 `360,285,151` bytes；报告耗时 `753.308 s`。前四段拥有八个 clean marks，span 5–8 未完成。

## R613 reviewed 路径

native identity 顺序为：

1. `ep3_story_cycle_admin_eunuch.8030` authored 4/native 3 GREEN；
2. `zg361p2c.2` authored 1/native 0 GREEN；
3. `zg361.40` authored 1/native 0 GREEN；
4. `epidemic_events.1060` authored 3/native 2 GREEN；
5. `debate_event.5110` authored 2/native 1 GREEN；
6. `ep3_emperor_yearly.2240` authored 3/native 2 GREEN；
7. `zg361.1` authored 1/native 0 GREEN；
8. `zg361.5` 因不在 P2 reviewed-product 路由而保留 RED。

`.1060` 本次 frame 为 instance `624`、date `53368272`、snapshot revision `111`，保存作用域只有 `epidemic`、`epidemic_scope` 与 `story_scope`。所有严格检查为 true；选择将 snapshot `native:33` 推进至 `native:34`，gold 与 stress 不漂移。提交 `1b4f30312f1ce6467a0cbaf1db4082ec574cf733` 已把这条 base projection production-live 证据写入共享 MCP vanilla-event 资产，并明确未给 R608 四作用域变体追加 live 声明。

## `zg361.5` 根因与最小修复

事件定义位于 `mod_zhongguo_style/events/zg361_events.txt`。这是玩家领主年度 review 之后的批量末位淘汰卡，三个选项分别是：

- authored 1/native 0：逐人调用含随机与强处置分支的 AI 裁决；
- authored 2/native 1：全部降岗留用，玩家损失 100 威望；
- authored 3/native 2：streak<3 者延长 PIP，其余降岗，玩家损失 50 威望。

专用 `MANAGER_ELIMINATION_TIMELINE_CONTRACTS` 与 manager-recovery 投影早已存在，并固定选择 authored 3/native 2。R613 frame 为 instance `628`、date `53375640`、root `32904`、103 个继承作用域、native tuple `(0, 1, 2)`；对现有投影回放时所有严格 root/date/option 检查为 true。失败原因仅是 P2 reviewed-product exact-key 集合遗漏该键。

提交 `3330f4c4202d62b5e0bbe043253578d203b0481a` 只把 `zg361.5` 加入 `PHASE2_CHOREOGRAPHY_PRODUCT_EVENT_KEYS`，没有改变事件、合同、选择语义或通用自动清理规则。未知事件与投影漂移仍保持 RED。reviewed wait 普通/optimized 各 `7/7` GREEN，R613 artifact 回放为 `103 scopes / authored 3 / native 2 GREEN`，`py_compile` 与 `git diff --check` GREEN。

## open_kaishek 与通用资产边界

本 take 的 `open_kaishek-preflight.json` 继续保留已知非必需语义覆盖 RED：`required=false`、`outcome=not-applicable`，parser `828 files / 0 diagnostics` GREEN，full-root validator 对尚未建模的 CK3 opcode 报 `175,310 UNKNOWN_OPCODE`。该结果不替代、也不推翻本轮 exact-build CK3 live evidence；它仍是 open_kaishek 的已记录覆盖债务，未被伪装为 GREEN。

本轮没有 MCP schema/version、DLL、游戏文件、启动配置、加载顺序或公共接口变化，因此不需要修改 open_kaishek 兼容层。共享 vanilla-event 数据资产新增了 R613 live observation；`zg361.5` 修复仅改变根仓库 P2 runner 的 exact-key 路由。

## 下一步

下一次启动从新轮次 R614 warmup 开始，再运行一轮连续八段 source capture。若 `zg361.5` 以相同投影出现，应由已有合同选择 authored 3/native 2；若出现任何其他新 RED，继续按单事件最小审查处理。
