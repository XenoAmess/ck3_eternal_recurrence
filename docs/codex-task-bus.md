# Codex 跨任务状态与通知总线

独立 Codex 会话不能直接读取彼此的聊天，也不能由普通文件强制注入一条会话消息。本机制使用
`D:\workspace\.codex-task-bus` 作为同机共享、append-only 的协作面，让各任务主动登记状态并增量轮询通知。

## 数据模型

- `events.jsonl`：全局只追加事件流；每条事件有单调 `sequence`、UTC 时间、发送任务、接收者和事件类型。
- `tasks/<task-id>.json`：每个任务的最新快照，包括 `running/waiting/blocked/done`、摘要、下一步、资源、仓库、Git HEAD 与脏项数。
- `cursors/<task-id>.json`：该任务已经确认读取的全局序号。
- `.lock`：跨进程写锁；事件追加、序号分配、快照与游标更新不会互相覆盖。

状态和通知只是协作信息，不授予操作权限，也不替代 Git `fetch + rebase`、CK3 排他锁或发布门禁。

## 安装与命令

```text
py tools/codex_task_bus.py install
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py register --task ck3-xqol-release-20260909 --repo D:\workspace\ck3_xqol_publication --summary "发布 XenoAmess的体验优化" --next-step "fresh-cache L3" --resource origin/master --resource CK3
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py status --task ck3-xqol-release-20260909 --state waiting --summary "等待 CK3 进入主菜单" --next-step "L3 游戏内断言"
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py notify --task ck3-xqol-release-20260909 --to * --level warning --message "origin/master 已推进；推送前请 fetch + rebase"
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py poll --task ck3-xqol-release-20260909 --ack
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py list
py D:\workspace\.codex-task-bus\bin\codex_task_bus.py status --task ck3-xqol-release-20260909 --state done --summary "Workshop 发布闭环完成"
```

`poll --ack` 只返回游标后的广播或定向事件，并原子推进游标；不带 `--ack` 可只读预览。
`list` 默认把超过 15 分钟没有心跳且未完成的任务标为 `stale=true`，但不删除历史。
`status --state done` 在未显式传入对应参数时会自动清空旧的 `next_step` 与 `resources`，表示该任务已经释放共享资源。
此普通命令只适用于非 `ck3-screen:acquired` 任务。屏幕资源只能由新任务在锁内独占登记，
以精确序号续租，再以 `release-screen-cas` 释放；旧 `status` 不再能移除或完成屏幕 owner。

## CK3 屏幕租约的 CAS 命令

本节只适用于源码和 `D:\workspace\.codex-task-bus\bin\codex_task_bus.py` 已经在受管静默期
安装并逐字节核对为同一经审版本的环境。当前旧安装版、未退休的历史屏幕记录或旧调用方在场时，
停止新的屏幕领取；不能用旧 `status` 清理历史记录。

```text
<verified-python> tools/codex_task_bus.py --bus-dir D:\workspace\.codex-task-bus --expected-cli-sha256 <审定的源/安装共同 SHA-256> register --task <全新任务ID> --repo <本工作树> --summary <本次屏幕工作> --resource ck3-screen:acquired
<verified-python> tools/codex_task_bus.py --bus-dir D:\workspace\.codex-task-bus --expected-cli-sha256 <同一 SHA-256> heartbeat --task <本任务ID> --expected-sequence <上次权威快照的 last_sequence> --repo <本工作树>
<verified-python> tools/codex_task_bus.py --bus-dir D:\workspace\.codex-task-bus --expected-cli-sha256 <同一 SHA-256> release-screen-cas --task <本任务ID> --expected-sequence <最新权威快照的 last_sequence> --summary <实际清场结论>
```

每次写入须保存完整 argv、返回码和 JSON，并回读 `event.sequence == task.last_sequence`、
任务状态/资源及全局 owner。心跳后用新序号续租；冲突、写后异常或回读未知均为 RED，
不能按旧序号盲重试。`list` 的 `stale=true` 只是诊断标记，**不自动释放**屏幕；
超时的 `running+screen` 和异常的 `done+screen` 都阻止新任务占屏，需单独审计恢复。
租约与新鲜 Steam 离线原图、目标进程清零和 CK3 受管清理是不同的门，不能互相代替。

## 任务协作约定

1. 会话开始时使用唯一、稳定的 task ID 注册，并立即 `poll --ack`、`list`。
2. 开始或结束一个工作包、进入等待/阻塞、占用或释放普通共享资源时更新 `status`；CK3 屏幕使用上面的 CAS 命令。
3. Git push、Workshop 上传、CK3 启动等共享状态变更前再轮询一次；发现冲突时定向 `notify`。
4. 长任务至少每 15 分钟发一次 `heartbeat`。任务完成后写 `done`，不要删除事件或旧快照。
5. 已在运行的旧会话不会自动获得新约定；它们必须在下一次交互时读取本文件或由用户明确告知。
