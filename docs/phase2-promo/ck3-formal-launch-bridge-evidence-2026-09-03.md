# CK3 正式启动与 Release bridge 证据摘要（2026-09-03）

## 结论

CK3 本体、正式 Steam 路径和当前 Release bridge 均已在受控条件下成功启动。当前 279-file broad Phase2 投影仍会在原版 on_action 加载后长时间停留，问题应继续按内容分组定位，不能归因于 CK3 本体或 bridge 不可用。

## 可复核证据

| 项目 | 结果 |
|---|---|
| 游戏 | CK3 1.19.0.6 / Steam buildid 23530548 |
| EXE | `Z:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe` |
| EXE SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| 旧核心 + 当前 Release bridge | `_runtime/formal-phase2-legacy51-currentbridge-20260903` |
| Frontend | 03:50:04 UTC；`Setting idler 'Frontend'`、`End loading of history`、窗口标题 `Crusader Kings III` |
| Bridge | 收到 hello；未发送 gameplay 命令 |
| 收尾 | WM_CLOSE、退出码 `0`、`cleanup_proven=true`；CK3/injector/watchdog 树清空 |
| 禁止动作 | 未载入存档、未游玩、未点击商店、未购买/付款 |

## 对照结论

- 当前 broad product+fixture（279 files）和去掉 scoreboard 的版本，都在 `Total on_action: 880/881` 后长加载，未在限定窗口内完成正式 Frontend。
- 隔离旧版精确 51-file product 在无 bridge 时约 51.7 秒到 Frontend；接入当前 Release bridge 后仍可到 Frontend 并正常退出。
- 因此下一项是离线分组缩小 broad 投影的负载/脚本来源；旧核心 GREEN 不代表 Phase2 seed、native readiness 或最终视频素材已完成。
