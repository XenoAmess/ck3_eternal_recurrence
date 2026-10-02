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

## 任务协作约定

1. 会话开始时使用唯一、稳定的 task ID 注册，并立即 `poll --ack`、`list`。
2. 开始或结束一个工作包、进入等待/阻塞、占用或释放共享资源时更新 `status`。
3. Git push、Workshop 上传、CK3 启动等共享状态变更前再轮询一次；发现冲突时定向 `notify`。
4. 普通长任务至少每 15 分钟发一次 `heartbeat`；屏幕 owner 必须遵守下文 600 秒有效期及 fresh CAS。普通任务完成后写 `done`，不要删除事件或旧快照。
5. 已在运行的旧会话不会自动获得新约定；它们必须在下一次交互时读取本文件或由用户明确告知。

## 屏幕租约与 CAS 续租

普通任务的 15 分钟心跳建议与屏幕租约是两个合同。[当前 CLI](../tools/codex_task_bus.py) 的
`SCREEN_LEASE_MAX_AGE_SECONDS=600`；`ck3-screen:acquired` owner 只在更新时间距当前不超过 600 秒时有效。
默认 `list` 仍按 15 分钟标记 stale，因此 `stale=false` 不能证明屏幕 owner 新鲜。
屏幕任务必须是唯一、`running` 且 resources 恰为 `["ck3-screen:acquired"]` 的 owner，不能混入 Git 等资源。
续租必须调用 `heartbeat --expected-sequence <latest-sequence>`，绑定已核对 source/installed CLI 的同一 SHA；
缺少精确序号、租约过期或 owner 变化都会拒绝，普通 heartbeat/status 不能复活过期声明。

长准备或受管会话直接复用 [ScreenLeaseKeeper](../promo/ck3_native_war_ai/integration/screen_bus_lease.py)：
默认 `interval_seconds=180`（允许 30–240 秒），在新鲜 owner 准入后启动，按既有 `renew_once` 完成
前后 locked list、heartbeat CAS 和新序号读回，保留 append-only journal。它不领取或释放屏幕。
keeper 活跃期间，同一 task 的 sequence 只能由 keeper 推进；其他线程不得再对该 task heartbeat/status
或另起续租器。续租失败会设 abort 并保留 RED，不能继续把该租约当作有效。
交接或释放前先 `stop()`、确认 keeper 线程退出，再读取其 `report()["last_sequence"]` 与当前任务快照。

实际长时间离线准备已发生超过有效期、fresh heartbeat CAS 被拒绝的情形。此时保留原事件、失败回执和
精确最后序号，使用既有 `release-screen-cas` 释放未变化的自有声明；不要删资源 flag、编辑 task 文件
或普通 status/done 绕过。CLI 对过期 owner 写 `waiting`、清空 resources、保留 next_step，并追加
`retirement.business_status="unresolved_red"`；这只是释放占用，业务仍待处理，不是完成或恢复授权。
若 owner/序号已变化，释放也会拒绝，应先闭合当前 owner；释放成功后以新 task 注册屏幕资源，再启动既有 keeper。

```text
<verified-python> <cli-source> --bus-dir <bus-dir> --expected-cli-sha256 <reviewed-cli-sha256> heartbeat --task <screen-task> --expected-sequence <latest-sequence> --repo <owner-checkout>
<verified-python> <cli-source> --bus-dir <bus-dir> --expected-cli-sha256 <reviewed-cli-sha256> release-screen-cas --task <screen-task> --expected-sequence <latest-sequence> --summary "释放过期的自有屏幕声明；业务仍待处理"
<verified-python> <cli-source> --bus-dir <bus-dir> --expected-cli-sha256 <reviewed-cli-sha256> register --task <new-screen-task> --repo <owner-checkout> --resource ck3-screen:acquired --summary "领取新的屏幕任务" --next-step "新鲜准入后启动既有 keeper"
```

本段核对 CLI SHA `b3c44b42f7bdf401b593d863e3210106a46412dcd7d89f8596c74f4c27392dee` 与
keeper SHA `d000883192b63d0aa7f5df7769a7eff0c1ed90450075e88c3d21d10943b46924`；只补文档，
未执行上述屏幕命令、启动 keeper 或操作游戏。后续部署仍须绑定当次实际 source/installed bytes。
