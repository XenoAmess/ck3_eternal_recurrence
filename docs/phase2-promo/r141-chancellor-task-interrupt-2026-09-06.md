# R141 原版尚书任务中断合同（2026-09-06）

## 实机边界

- frozen source：`b764af1538a049d1858f6dc343c7dcee4a17bd3c`。
- no-launch preflight：GREEN；报告 `Z:\p2m141_pre_a\preflight.json` SHA-256 为 `00A33243202615CCFA2BA10DA0891CB304EAC950F0E121AFBC0953A7D58B4161`。
- R130 产品投影仍为 1,031 files，关键 B2 文件逐字节等价 GREEN；本轮只改变 acceptance-only fixture 与 runner 合同。
- CK3 PID `127320`，玩家 CharacterID `32904`，connection generation `1`，默认 5 速。
- 在 `date_raw=53151120` 捕获原版 `chancellor_task.1102`，event instance `16`；B1 仍 active，玩家存活，未发生 owner terminal。
- `manager-cycle-recovery.json` SHA-256：`B04D22BE693115E970F66D87C2004B308B8C35F51BD8FA35A847BA061E1DC423`。
- `runner-report.json` SHA-256：`DACA4220B95641EBA837FA069C054AE7CFF3DFA50B4E1FE937FEFC20D090D416`。

## 精确事件合同

CK3 1.19.0.6 原版 `events/councillor_task_events/chancellor_task_events.txt` 中，事件 immediate 已随机选择一个满足条件的停战目标。该事件只有一个 authored option：`cancel_truce_one_way = scope:target`。没有无副作用或仅确认的替代按钮，因此若要继续时间线只能选择该按钮，但选择前必须完整闭合当前帧。

R141 实机帧的 saved scopes 恰为：

- `councillor`：character `28761`；
- `councillor_liege`：character `32904`，与玩家 root 相同；
- `target`：character `30921`。

窗口只有一个 rendered option，映射 native index `0`，shown/enabled 为 true，fallback/cancel 为 false。runner 合同只登记这个 key、三项 scope 名称/类型、root 关系、单按钮形状与 observation window；任何增删 scope、类型漂移、按钮映射漂移或玩家身份变化仍在操作前 RED。

该中断属于原版玩法副作用，不是天朝二期产品 RED，也不提升逐号 readiness。对应 purpose-split 测试文件现有 4 个场景，仍满足每文件 1–10、原则上不超过 20 的边界。
