# CK3 native checkpoint contract

更新时间：2026-08-24；目标版本：CK3 `1.19.0.6`。

`game.command.save-checkpoint` 只证明 DLL 已把固定名称 `xar_checkpoint` 的
`CAutoSaveCommand` 提交到 CK3 command queue。planner 需要的是可恢复的存档文件，因此 Python
native driver 将 submission 补全为和视觉 `save-checkpoint` 相同的 `checkpoint` 结果：

```json
{
  "step": "save-checkpoint",
  "accepted": true,
  "status": "submitted",
  "submission": {
    "sequence": 2,
    "requested_save_name": "xar_checkpoint",
    "date_raw": 53171424
  },
  "checkpoint": {
    "status": "saved",
    "path": "<isolated-profile>/save games/xar_checkpoint.ck3",
    "name": "xar_checkpoint.ck3",
    "size": 123456,
    "sha256": "...",
    "date_raw": 53171424,
    "overwrite_confirmed": true,
    "strategy": "native-autosave-command-v1"
  }
}
```

`xar-ck3-mcp --driver native-headless --state-dir <root>` 和 `hybrid-fallback` 都把
`<root>/profile/save games` 传给 native driver。执行前记录目标文件的 size/mtime；submission 后等待
文件新建或 size/mtime 改变，并连续两次观察到相同签名后计算 SHA-256。配置目录下未落盘会让该
step 失败，不能把 queue submission 记成成功 checkpoint。

直接构造 driver 而未提供 `save_dir` 时仍可提交原生命令，但结果明确返回
`checkpoint.status=materialization_unavailable`、空 path/size/hash，以及
`materialization.reason=save_dir_not_configured`；不会隐式调用视觉保存。

MCP 同时保留 generic `ck3_execute_step("save-checkpoint")`，并提供 typed
`ck3_save_checkpoint(expected_revision?)`。两者走同一个 semantic step；typed 工具要求结果含明确
`checkpoint` 对象。

## 进程级 restore-checkpoint

`ck3_restore_checkpoint(expected_revision?)` 与 generic
`ck3_execute_step("restore-checkpoint")` 走同一条纯 native 生命周期路径：

1. MCP native driver 向 `<state>/native-session/bridge/inbox` 原子发布请求，并记录当前
   `connection_generation`；
2. 请求同时携带 `xar_checkpoint.ck3` 的 size、SHA-256 与已知保存日期；持有 CK3
   `SessionHandle` 的 `native-session` 主线程在停止前和停止后各核对一次文件，再使用完全相同的
   pipe、DLL 和 injector 执行 `launch(..., load_save_name="xar_checkpoint")`；
3. 会话进程在 outbox 返回旧/新 PID；driver 仍不会立即宣称成功，而是等待 named pipe 出现更大的
   `connection_generation`，等待该代 DLL 发布 `map_ready=true` snapshot，并要求语义 revision 至少稳定
   0.5 秒；
4. driver 核对恢复日期（有保存日期元数据时）、本局 played CharacterID 和 checkpoint hash，随后返回
   `restored_date`、checkpoint 路径/大小/hash、新连接代次和新 PID。

这条路径不导入 OCR、截图或输入模块，也不激活窗口。`native-headless` 缺少受管
`native-session` 或 checkpoint 文件时直接失败；`hybrid-fallback` 对这一特定步骤也不会改走视觉
`restore-checkpoint`。当前实现是固定 checkpoint 的进程级 `-loadsave=xar_checkpoint`，不是同进程热读档。
CK3 1.19.0.6 的启动分支在 RVA `0x34806E5`/`0x3480878` 分别处理
`continuelastsave`/`loadsave`；后者把 basename 交给 save manager，由 `save games` 目录和 `.ck3`
扩展拼出实际文件。因此参数必须是不带扩展名和路径的 `xar_checkpoint`。这避免了
`-continuelastsave` 随 profile 根目录 `last_save.ck3` 漂移到更新 autosave 的实际功能错误。
`native-session` 在入口已经验证一次 committed profile，并在整个会话期间独占同一 state/launch 锁；受管重启因此复用
该验证结果，不再重复执行完整 Git/runtime 指纹。这样恢复时间由 CK3 重载决定，不会被第二次 `git ls-files` 卡住；普通冷启动
仍执行完整验证，Git 子进程本身也有 15 秒上限。

## 完整 agent + CK3 冷重启连续性

显式冷恢复入口为：

```text
xar-autoplayer ... --bridge-mode native-headless native-session --cold-start-checkpoint
```

该入口先读取 `<state>/native-session/driver-state.json` v2，核对当前 pipe、checkpoint
size/SHA-256 和历史锚点，再明确调用 `launch(..., load_save_name="xar_checkpoint")`；不会使用
`-continuelastsave`。如果 v2 元数据或 checkpoint 字节不匹配，进程不会启动。

driver-state v2 在 `last_checkpoint` 中额外保存：

- `history_index`：成功 `save-checkpoint` 在 command history 中的 1-based 位置；
- `episode_character_id` 与 `episode_run_id`：该存档所属的一代 rogue episode。

新 daemon 收到与持久状态相同 PID 的 hello 时仍走原有 hot 路径，立即恢复 episode/history。收到不同
PID 时只建立 `pending_cold_candidate`，此时不会把旧角色误判成死亡或继承，也不会覆盖磁盘上的旧状态。
首个同时满足 `map_ready=true` 且含有效 played CharacterID 的 snapshot 才完成绑定：

1. CharacterID、snapshot `date_raw`、checkpoint size/SHA-256 全部与锚点一致：恢复原
   episode/run id，把 history 截到 `history_index`，丢弃存档之后发生但已被回滚的命令，再追加一条
   `source=native-session-cold-start` 的 synthetic `restore-checkpoint`；
2. 任一项不一致：把当前角色作为新局创建新的 run id，清空旧 history/checkpoint；该首帧不是
   one-life terminal。

旧 v1 状态只允许同 PID hot 恢复。hot 恢复或下一次持久化时，driver 从最后一条 SHA/size/date
都匹配的成功 `save-checkpoint` row 推导 `history_index`，补入 episode ids 并写成 v2；随后才能安全执行
跨 PID 冷恢复。2026-08-24 的确定性 Python 验收覆盖了实机迁移形状：checkpoint 位于 index 8，
index 9/10 的 `life-advance` 与 index 11 的 army move 在冷恢复时被截断，最终追加新的 index 9
synthetic restore。CK3 冷启动实机验收尚未执行。

## Minimized 实机结果

2026-08-23，精确匹配的 CK3 `1.19.0.6` 在窗口最小化时完成了两次闭环：

- 首次 native submission 生成 `xar_checkpoint.ck3`，大小 `63,367,813` 字节，
  SHA-256 为 `a50e61b839cd80c08661d402a9bc0d3ea42fdfd418ee21c294a089657d69bfa2`；
  command result 和下一份 snapshot 的 sequence/name/date 一致。
- 停止该 CK3 进程后，新的纯 native 会话用 `-continuelastsave` 恢复到 checkpoint 的
  `date_raw=53167488`。恢复后的 typed `ck3_save_checkpoint` 又在最小化状态覆写同一
  文件，返回 `status=saved`、完整路径、同样的大小与新文件 SHA-256
  `e767471a9d0f2984f4dba5baeaa9dcb43cb72b055f585a650c2ff1501ffcc914`。

这两次过程都没有调用 OCR、截图、聚焦、键盘或鼠标后端。上述自动生命周期队列将同样的实测手工
重启路径封装成 MCP semantic step；其 Python 双进程闭环已有确定性测试。上述两次历史实测使用的是
旧 `-continuelastsave` 路径。

2026-08-24 又完成了当前 exact restore 的最小化实测：

- PID `25336` 的窗口在恢复前为 `SDL_app / IsIconic=true`；进程重启为 PID `126204` 后仍为
  `SDL_app / IsIconic=true`，lifecycle 返回 `previous_window_minimized=true`、
  `minimized_state_preserved=true`。
- 固定文件 `xar_checkpoint.ck3` 的 SHA-256 为
  `4e546e64d125838b846e0d67e4cd00554f4a2ec1b5b55ba12139ea4d7a11fd45`，大小
  `63,955,822` 字节。游戏先由 `date_raw=53168664` 推进到 `53168688`，再由
  `-loadsave=xar_checkpoint` 精确回到 `53168664`。
- connection generation 从 `1` 变为 `2`；episode CharacterID `29829`、run ID 与
  `save-checkpoint → life-advance → restore-checkpoint` history 保持连续，返回 revision 已稳定为 `12`。

同进程指定文件热加载尚未实现；当前闭环使用受管进程重启。
