# CK3 native checkpoint contract

更新时间：2026-08-23；目标版本：CK3 `1.19.0.6`。

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

## Minimized 实机结果

2026-08-23，精确匹配的 CK3 `1.19.0.6` 在窗口最小化时完成了两次闭环：

- 首次 native submission 生成 `xar_checkpoint.ck3`，大小 `63,367,813` 字节，
  SHA-256 为 `a50e61b839cd80c08661d402a9bc0d3ea42fdfd418ee21c294a089657d69bfa2`；
  command result 和下一份 snapshot 的 sequence/name/date 一致。
- 停止该 CK3 进程后，新的纯 native 会话用 `-continuelastsave` 恢复到 checkpoint 的
  `date_raw=53167488`。恢复后的 typed `ck3_save_checkpoint` 又在最小化状态覆写同一
  文件，返回 `status=saved`、完整路径、同样的大小与新文件 SHA-256
  `e767471a9d0f2984f4dba5baeaa9dcb43cb72b055f585a650c2ff1501ffcc914`。

这两次过程都没有调用 OCR、截图、聚焦、键盘或鼠标后端。当前恢复路径是进程级
`continuelastsave`；同进程指定文件热加载尚未实现。
