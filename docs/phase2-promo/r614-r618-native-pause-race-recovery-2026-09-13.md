# R614–R618 native 暂停竞态恢复（2026-09-13）

## 验收状态

- T0 P1 保持 `9/9 GREEN`。
- T0 P2 保持 `0/8`。本 take 连续完成前四个 clean spans，进入 HC/Workforce span 5 后发生 harness RED；失败 take 不拆分计数。
- 最终宣传片硬锁继续生效；本轮没有制作、更新、发布或预热最终成片。
- RED 没有被降级或吞掉。R618 报告、暂停门、wait gate、时间线与原始 MKV 均保留。

## 连续 take 与清理

artifact 根：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r614-plus-4bfecea-20260913`

| 轮次 | PID | 用途与处置 |
|---|---:|---|
| R614 | `70424` | frontend warmup；frontend ready 后终止 |
| R615 | `69312` | gameplay spans 1–2；clean end 后终止 |
| R616 | `35276` | manager governance span 3；clean end 后终止 |
| R617 | `161572` | promotion compensation span 4；clean end 后终止 |
| R618 | `130820` | HC/Workforce source；暂停门 RED 后终止 |

连续 FFmpeg PID `125024` 已停止。cleanup 为 GREEN，PID lineage 为
`[69312, 35276, 161572, 130820]`；CK3 与 FFmpeg 最终库存均为零，protected storage 为
`UNCHANGED`。报告耗时 `768.616 s`，原始 MKV 为 `359,929,308` bytes。

| 文件 | SHA-256 |
|---|---|
| `capture-plan.json` | `9901B98B7B19B74AF47A9344B930B320FC1B77F1C234A4FCE7C151E189448F54` |
| `capture/report.json` | `C9948ED306D12009849615F8300F8DF91A90F0C20FDC9FA2279091E5B5D5C0AA` |
| HC native event wait gate | `3C49747E5DE56EC812CB9E3D366F55E637863D9B53660E21B64CA575BBE56E01` |
| failing identity pause gate | `011060D11EEA5CD326B56CFCA7B9B349E217104EC214E2D8614FFDAAD49DE03C` |
| `capture-timeline.json` | `8AE3FF4E044E932C3EF9D45FCE206731EB37168782CE55E82717F2A544DDCBAA` |
| raw MKV | `28490BA00C96F186059D0FEECABD2394E8EB1E6D5C1198F4520CA6A204B9C05D` |

## RED 根因

R618 的第七次 HC 事件身份查询开始于 revision `198`、native revision `117`、date
`53375616`、event instance `627`、玩家 `32904`。起始快照显示 `paused=false`，所以 runner 以
`expected_revision=198` 提交 `pause-map`。

命令到达 native bridge 时 CK3 已因事件自动暂停。bridge 返回：

```text
accepted=true
status=already_paused
ending_revision=199
ending_native_revision=118
ending_date_raw=53375616
ending_paused=true
state_frame_rejections=0
```

这是已接受且带真实暂停后置观测的幂等成功。旧 runner 只接受字面状态 `submitted`，在读取上述后置条件前即报
`native pause-map was not accepted before event-definition query`。因此本次是 runner 对 native ACK 语义覆盖不全造成的
harness RED，不是 mod 业务事件、MCP DLL、事件定义或 CK3 崩溃。

## 最小修复与验证

提交 `e642e39fae3dc84d5aee7fccedda49e4d04e65c3` 只修改事件身份查询前的暂停门：当命令本身
`accepted=true` 时，允许 `submitted` 或 `already_paused` 进入原有后续稳定性检查。它没有把
`not_needed_already_paused` 混入命令提交分支，也没有接受 rejected/unknown ACK。

后续检查没有放宽：快照必须真实 `paused=true`，event instance、date、played character 必须与提交前一致，public
revision 必须有效；任一漂移仍立即 RED。聚焦测试新增了与 R618 相同的“起始运行、提交时已暂停”路径，并与正常提交、起始即暂停、
日期/事件/玩家漂移路径一起通过。`test_run_zhongguo_promo_capture.py`、`py_compile` 与
`git diff --check` 均 GREEN。

## 接口与伴随资产

本包没有 MCP schema/version、DLL、游戏文件、启动配置、加载顺序或公共接口变化，因此不需要修改 open_kaishek 兼容层。
本次也没有新增原版事件定义知识；现有通用资产未变。

## 下一步

下一次 CK3 启动从新轮次 R619 warmup 开始。只运行一轮新的连续八段 P2 source capture；R618 所见
`already_paused` 回执应继续通过完整稳定性门。如果出现其他真实 RED，仍在首次阻点停止并做最小审查，不扩大为重复长跑或全库审计。
