# Cross-cycle endgame：原生 Switch Character 生产接缝

基线：CK3 `1.19.0.6`，`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
当前状态是 `static-ready-live-pending`；本包没有启动 CK3，也没有生成 live checkpoint。

## 实现边界

正式 Phase2 runner 的 `capture_cross_cycle_endgame` handler 现在有两条显式、互斥的
subject-session 路径：

- 未提供 product title key 时，保留旧的 acceptance-only typed-event fixture 路径，只用于既有回归；
- 提供 `--phase2-endgame-product-switch-title-key` 时，runner 不安装 fixture、不重启 CK3、
  不调用 console 或 generic character rebind，而是在同一个 managed product PID / connection
  generation 中执行 CK3 单人模式的普通 `Switch Character` UI。

title key 不是要扮演的 CharacterID，也不是 rebind 参数。目标 CharacterID 只能来自当前真实
`zg361we.361` 的 saved subject scope。title key 只供已经验收的
`game.command.center-map-on-landed-title-v1` 把该 subject 的有地头衔中心放到地图选择点；若 key
指向了其他角色，最终 bridge 回读的 `played_character_id != #361 subject`，整个 cell typed RED。

生产顺序固定为：

1. 回读 paused owner-facing `zg361we.361`，复核 owner、subject、date 和三项可选 option；
2. 在任何后续 save 之前，把 owner-result checkpoint 原始 bytes 复制到证据目录并复算 SHA；
3. 用 exact-build native title navigation 落到调用方声明的 subject landed-title key，要求
   `title_bounds_center`、settled camera、相同 episode/date/generation；
4. 选择 `#361` authored option 1，只把 submitted ACK 记为输入，不记为业务结果；
5. 通过原版快捷键进入 `Escape -> menu_switch(3) -> any_ruler(Tab)`，每个界面都用连续两帧 OCR
   识别英文或简中原版文案；
6. 点击点只能由当前 CK3 client rectangle 的中心计算，并且必须位于 native title navigation
   已经稳定的 frame；runner 不接受任何调用方坐标；
7. 地图选择提示连续两帧消失后提交原版 `confirm(Return)`；
8. 只有 bridge 回读 exact subject、相同 date、相同 PID、相同 connection generation、paused、
   map-ready、无 active event 后，才保存 child checkpoint；
9. 对 child 文件复核 path/bytes/SHA，随后调用
   `bind_product_subject_checkpoint_session`；最终 GREEN 仍要求 Workforce received-self provider 和
   AI-owned owner provider 同 revision 观察到同一 terminal cycle，而不是 UI、save 或 option ACK。

换角前后的 `episode_run_id` 都写入 receipt；CK3 正常换角可能建立新的 played-character episode，
因此不把 episode id 相等当成事实。连续性硬门禁是同一 product process、同一 pipe generation、
同一游戏日期以及前后都 paused/map-ready；child receipt 同时回链 owner-result SHA 与 seed save lineage。

## exact-build UI 证据

2026-09-04 的只读 source preflight 对当前安装得到：

| 原版文件 | SHA-256 | 固定入口 |
|---|---|---|
| `game/gui/frontend_ingame_menu.gui` | `B593A4EA396A1E2EBAA996389C1795C0CD08DFD42BF88BCEC97A228F3E67F6B8` | `switch_character_button` → `PauseMenu.SwitchCharacter`，shortcut `menu_switch` |
| `game/gui/frontend_bookmarks.gui` | `C853B48F42A5A3B84208B2FC570C02F5FCB5DA217133553C6A5B70B7F8F0F267` | `pick_any_character_button` / `any_ruler`，以及 `start_button` → `GameSetup.StartGame` / `confirm` |
| `game/gui/shortcuts.shortcuts` | `A70755FCE82E7541108CEF926C09860643070FAC15B0EECFA7C6ED7BCFEDC25D` | `menu_switch="3"`、`any_ruler="tab"`、`confirm="RETURN"` |

pause menu 的原版 `Switch Character` button 只在非 Ironman、非多人局可见；这正是 runner
使用的 managed ordinary single-player 产品会话边界。title-navigation 合同仍只是 presentation
capability，不承担选角或业务证明。

## 不启动 CK3 的 preflight

```powershell
py tools/preflight_zg361_phase2_cross_cycle_endgame_switch_ui.py
```

它只读取上述三个原版文件，输出文件哈希、必需 widget/action/shortcut 片段及
`ck3_launched=false / live_executed=false`。任何文件或语义片段漂移都 typed RED。

## 唯一 live 命令

在真实第三周期 `#356` source registry 与 subject 的真实 primary-title key 已经确定后，只使用：

```powershell
py tools/run_zhongguo_acceptance.py --phase2-promo-capture --phase2-source-checkpoint-registry <schema-2-registry.json> --phase2-endgame-product-switch-title-key <subject-primary-title-key>
```

不得另写 click/rebind 命令。该命令仍需环境中既有 exact-build bridge 配置；缺少真实第三周期
checkpoint、title key 不匹配、UI surface 未连续识别、PID/generation/date 漂移、child bytes
未落盘或任一 provider 不可用，都会保持 RED / live-pending。

## 仍待实机闭合

- 当前真实第三周期 `zg361we.356` checkpoint 及其 `#361` result 尚未实跑；
- subject primary-title key 尚未由本次 no-launch 包产生，必须从该真实 case lineage 确认，不能把
  seed 的 `k_hedong` 无条件外推到未来第三周期 subject；
- 原生 UI 四段 surface、地图中心选中结果、bridge 对 ordinary switch 后 episode 的实际表现、
  child checkpoint bytes/SHA 与 Workforce + AI-owner 双 provider 仍需同一 live artifact 验收。

因此这个施工包只消除了 runner/contract/preflight 缺口，没有把 readiness 升成 production-live。
