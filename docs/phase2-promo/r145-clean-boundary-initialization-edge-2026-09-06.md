# R145 clean boundary 夹具初始化边界（2026-09-06）

## 实机结果

- frozen source：`e8064e9669a55f147627a1a2a133f8d94c246f7e`；源码 ZIP SHA-256：`AEF77B10C10E62B2AA8D3798AC5C41E4A3DB9764FC06886B7DD271BD4EB7A601`。
- no-launch preflight GREEN；R130 产品投影及关键 B2 effect 字节等价门保持 GREEN。
- CK3 PID `173172`、玩家 CharacterID `32904`、默认 5 速；存活保护应用一次，未发生 owner terminal。
- `tribute_mission.1002` 与 `.1005` exact drain GREEN；R144 新登记的 `.0015` 本轮没有在 clean boundary 前随机发生，未因此形成新结论。
- runner 在 `date_raw=53154120` 再次取得 `B1=false / Central=false / PP=false / review_now=true` 的暂停 clean boundary，manager-cycle recovery 本身为 GREEN。
- 等待 1 秒且没有恢复时间后，`zga_phase2_manager_seed.1` 仍未出现；因此最终 seed capture 保持 RED。
- `manager-cycle-recovery.json` SHA-256：`9020BC625D53197A198CAC99B1FA8F8740CEC20FC1AE1D7E7D19038CFC6C15E4`。
- `runner-report.json` SHA-256：`3155BFDA21BD6E241E076EA59309432E1AB960E0BCE9F7428A96B8CF6B2F0B4A`。

## 根因与最小修改

R140 已把“加载诊断”和“clean-entry”拆成两个 GUI animation state，但 R145 证明单纯拆 state 仍不足。窗口在存档局面完全恢复前已经存在；此时 clean-entry state 可能在产品 B1 flag 恢复前短暂满足并被消费，之后真实 B1 从 active 变为 inactive 时不会重入。证据边界是：同一地图会话中存活 modifier 的应用日志存在、clean business gate 由 MCP 同帧确认，但没有任何 seed-entry debug/event。

R146 的最小改动是在 clean-entry scripted GUI 增加 `has_character_modifier = zga_phase2_manager_seed_survivability_modifier`。该 modifier 只会由 loaded-map diagnostic 对已绑定真人管理者安装，因此它同时充当 acceptance fixture 已初始化的正向栅栏：部分恢复阶段不能提前消费 entry state，完整加载后又因 B1 active 保持 false，只有真实 clean boundary 才首次变为 true。

该修改只影响 acceptance-only fixture，不改 R130 产品、业务变量、receipt 或 release staging。effect 仍为单文件 4 个；没有新增大文件或超过用途分片上限。
