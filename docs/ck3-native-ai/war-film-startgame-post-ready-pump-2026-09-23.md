# R0003 StartGame 后 pump 等待：Python 修复与现场证据边界

日期：2026-09-23。原始 attempt：`desktop-3fevhd2-1c74096080--vanilla--R0003`。
本包只读已有磁盘记录并修改 Python 等待逻辑及单测；没有启动、注入、附加或查询 CK3，未改 native 源码或重建 DLL。

## 实际故障与不能推导的结论

`D:/workspace/ck3_war_film_research_20260923/capture-live-live-r3/mcp-calls.jsonl`
第 359 行记录 `ck3_activate_frontend_start_1066_bookmark_character_v1` 失败：

```text
ApplicationMain pump did not advance on the stable paused StartGame binding; baseline=11361, last=11361
```

该行 `seconds=448.47564990003593`、`at=2026-09-22T20:35:06.347179+00:00`
属于工具调用记录的开始时刻，不能当作异常发生时刻或 StartGame 独立耗时。
`capture-report.json` 是 RED、marks/clean_spans 为空，不能认定完成地图取景。

协调者从原始录像 `raw-desktop.mkv` 的 `512.566s` 抽帧，保存在：

- `D:/workspace/ck3_war_film_research_20260923/capture-r3-postready-inspection/end-minus-8.png`
- 同目录 `receipt.json`：实际 FFmpeg 命令、返回码 0 与原始时间点。

本包查看该图，画面仍显示“载入：100%”，没有地图 HUD。
这与“语义 player/map snapshot 已发布，但加载回调尚未完全退出”相容；
**既不能宣布地图可操作，也不能断言下述 Python 缺陷是 R0003 唯一原因**。
旧日志未保存等待循环每次的 snapshot key/epoch，因此无法回放裁定本次 pump 是否实际连续推进。
`session-result.json` 的 `ok=true` 只对应 session 清理成功；其 `cleanup_proven=true` 与取景 RED 不矛盾。

## 代码机制

[等待函数](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:4902)
原逻辑维护 `key=(snapshot_id,native_revision)`：每逢 key 改变，就把 `baseline_epoch`
覆盖为本次 `last_epoch`；只有 key 不变的 `elif` 分支才检查 `last_epoch > baseline_epoch`。

因此，对于相同 paused/date/player/PID/connection binding 下的输入：

| 观测 | snapshot key | pump epoch | 旧行为 |
|---|---|---:|---|
| 首次 ready | native:1 / 1 | 100 | baseline=100 |
| 后续 | native:2 / 2 | 101 | baseline 被改成 101，不通过 |
| 后续 | native:3 / 3 | 102 | baseline 又改成 102，不通过 |

只要轮询持续遇到新 publication，这个算法就会丢弃全部真实推进。
最后 `baseline=last` 是重置分支也能产生的结果，不足以证明游戏线程停滞。

发布链的实际条件如下；本包没有把“定期尝试发布”误称为“每次都增加 revision”：

- `native_bridge/src/bridge.cpp:147` 的 heartbeat 间隔为 250ms；`8927–8935` 先发 heartbeat，再尝试 `PublishSnapshot`。
- 同文件 `8526–8532`：完整 Snapshot 与 checkpoint sequence 均不变时 deduplicate；否则 `++revision`。
- 同文件 `4292–4295`：把该 revision 同时编码成 `snapshot_id="native:N"` 与 wire revision。
- `native_driver.py:965–992`：读取当前缓存语义帧，`native_revision` 来自 wire revision，diagnostics 另取当前已接收的 heartbeat。
- `native_driver.py:2242–2249/2280–2294`：`take_snapshot()` 读取上述缓存并补本地历史；它不会发新的 native 查询，也不会主动推动 pump。

所以 paused/date/player 稳定不等于整个 Snapshot 内容稳定，publication identity 也不是本等待所需的角色绑定身份。

## 最小修复

1. 将首次 ready 的 pump 保留为固定 baseline，后续只在相同日期、角色、PID、connection generation、
   map-ready 且 paused 的前提下要求 `last_epoch > baseline_epoch`。publication key 仅用于诊断统计。
2. 使用已配置的 `frontend_transition_timeout_seconds`，取消额外的 30 秒上限。
   等待时间变长不等于放行：没有真实后续 pump 仍然超时，不跳过等待提交游戏查询。
3. 超时消息保留固定 baseline、last、observations、snapshot_changes、starting_key 与 last_key，
   便于区分“出版号在变但 pump 不变”与“缺少有效样本”，不再用被覆盖的 baseline 隐藏历史。

角色/日期/进程/连接/暂停条件变化仍立即拒绝；pump 缺失或无效仍拒绝。
通过这里只证明观测到同一绑定下较晚的 pump，不直接证明 HUD 已显示、后续查询已执行或影片机制已经实机闭合。
原有 campaign-root 独立后置检查仍需成功。

## 聚焦验证与下一步

`tests/unit/test_feudal_1066_frontend_start.py` 新增直接调用等待函数的用例：
新 publication 与 pump 同时推进、只有 heartbeat 推进、key 变化但 pump 停滞、
模拟第 31 秒才推进并尊重 45 秒配置预算、六类绑定变化、缺失/无效 epoch。
历史 StartGame 组合测试用 lambda 绕过该等待函数，本轮补齐实际等待路径的离线覆盖。

实际命令：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe ck3_autonomous_player/tests/unit/test_feudal_1066_frontend_start.py
```

测试使用模拟时钟和缓存快照，不等待真实加载，不连接游戏。
结果收据：`D:/workspace/ck3_war_film_research_20260923/post-ready-pump-python-r1/test-result.json`。

下一次已有现场若可保留，应由唯一 owner 使用同一 driver 记录等待前后 pump、绑定及独立查询结果。
如依然停在加载画面且 pump 不推进，应保留 RED 并诊断加载完成条件；不能靠忽略 pump 或把地图快照等同 HUD 来绕过。
