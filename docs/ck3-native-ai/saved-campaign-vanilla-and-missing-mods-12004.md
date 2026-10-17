# 纯原版存档恢复与缺失模组弹窗边界（1.20.0.4）

机器来源：`machine_id: 4-8e1c2f1861`；观察时间 `2026-10-17T09:01:31.722157+00:00`。本次只读研究安装目录中的原版 GUI 与仓库源码，并运行离线 Python 测试；没有启动、恢复或操作游戏。这里没有 R2 冷载成功、弹窗出现或弹窗消失的实机事实。

## 规划器如何选择恢复输入

共享 host 的 `prepare_saved_campaign` 现在接受两种显式清单，字段均恰为 `schema/profile_path/enabled_mods/product_files`。`ck3-saved-campaign-product-only-profile-v1` 仍要求两个列表非空，逐个校验实际完整启用投影及描述符的字节数/SHA，并拒绝含 `on_game_start_after_lobby` 的文本。`ck3-saved-campaign-vanilla-profile-v1` 要求清单两个列表都严格为 `[]`，且实际 `dlc_load.json` 也为空；没有用空模组占位。

两条路径继续要求新的未启动 profile/state、外部普通 `.ck3` 文件、明确字节数/SHA/实际玩家 ID/日期，复制后再次读回。清单资格与复制成功只证明恢复输入就绪，不证明游戏已经加载，也不证明历史角色编号就是运行时角色 ID。

一次 managed launch 使用 `-loadsave=restored_campaign`，排除 `-continuelastsave` 并禁止第二次启动。初始 tail plan 仍只读。是否发生缺失模组确认，必须看该次实际加载结果，不能从 CLI 参数推断跳过或一定出现弹窗。

## 缺失模组的实际原生接点

本机原版来源位于 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`：

| 来源 | 字节数 | SHA-256 | 绑定 |
| --- | ---: | --- | --- |
| `gui/frontend_load.gui` | 17493 | `5c8947e6aac9353ac19e124392cbced85a3c49b28a6fcdb4a20ec1ff8fe3eb41` | 260 行加载按钮 `FrontEndLoadView.OnLoadSavedGameButton`；567–572 行显示 `SaveGameItem.HasMissingMods/GetMissingMods` |
| `gui/shared/dialogs.gui` | 5232 | `b83ca05ff9aab1eab38d079512c4e1a2c0154b9a8f12c0082c652ca7eef6fa16` | 通用确认窗 `basic_confirmation_popup` 的 `accept_button` 调用 `GameDialog.Accept` |

GUI 脚本只证明上述公开绑定；没有证明加载缺失模组时 C++ 实际创建哪种弹窗或 Accept 对该场景的含义。原始小型来源回执：`C:/workspace/ck3-faith-and-power-20261017/episode01/runtime-audit/saved-load-gui-source-pins.json`。

现有 typed MCP 没有 load-view/missing-mod 的 continue 或 ignore 工具。`DispatchConfirmCustomRuler` 虽复用通用确认窗，但只批准 ruler designer 的覆盖确认，不能用于存档加载。`ck3_inspect_frontend_gui_tree_v1` 在已知前端 route 上仅检查其子树；route unavailable 时才读全局 `_root_`，因此也不能保证已覆盖另一个 modal。现有 ingame window census 的固定名单没有 load view 或通用确认窗。

若实机出现阻断，应先保存该 modal 的原生 owner/root、实际缺失模组与目标存档绑定，再增加该场景专用的 typed 只读上下文及一次 Accept 动作，复用当前 build 的 named-widget dispatch。动作后必须独立证明原 modal 消失、同一 PID/代次恢复到存档的实际玩家和日期；ACK 不作加载后验。不能借 ruler-designer 接口确认，也不能用 OCR/鼠标。

`--saved-campaign-inject-after-load` 会等实际 `Setup completion` 和 `In Game` 标记才注入。若弹窗出现在这些标记之前，这条路径尚未提供处理它的 MCP 通道；不能把等待超时冒充已经拒绝或确认。

## 离线验证

`test_saved_campaign_vanilla_profile` 七项通过（`2026-10-17`，本机，Python venv：`C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`）。覆盖显式纯原版、旧 product-only 正向路径、非空/未知/跨 profile 清单拒绝、原投影 SHA 与冷启动 registrar 拒绝，以及存档 SHA 和 fresh-profile 守卫。结果仅为输入合同测试；没有实机加载验收。
