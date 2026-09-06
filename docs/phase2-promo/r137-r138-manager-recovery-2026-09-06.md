# R137–R139 管理周期恢复取证（2026-09-06）

## R137：第二次 owner terminal

- frozen source：`e093b54c4ab6c75b9d6b877c56c0d577fb7af6d4`
- 最后有效帧：玩家 `32904`、`date_raw=53149440`、B1 active。
- 拒绝帧：`date_raw=53149464`、actual player `36354`、expected player `32904`、CK3 PID `127068`、connection generation `1`、`one_life_terminal_reason=played_character_changed`。
- 结论：第二次已取证的角色死亡/自然交接，不是重连或产品 RED。现有接口没有死亡原因字段，因此不能声称是病死。
- `Z:\p2m137_a\manager-cycle-recovery.json` SHA-256：`A6272403A91CDD4A382158DDB636BE50F58B8B8E3AC4F676C5370A4C02E0F008`
- `Z:\p2m137_a\runner-report.json` SHA-256：`C7DA701BC1BDA01B4BC16EBA6706E0048CBAF7D997DFDED50B5D32253CE27AC4`

## R138：贡礼回报事件

- R138 完全复用 R137 frozen source 与已 GREEN preflight；没有代码或产品树变化，因此未重复同一轮静态预检。
- 玩家 `32904` 存活，严格 `tribute_mission.1002` 拒收分支成功执行；随后在 `date_raw=53150184` 捕获 `tribute_mission.1005`。
- 实机 saved scopes 为前一帧 14 项加 `rejected_concubine` flag 与 `decided_on_treasury_reward` flag，共 16 项。
- snapshot 有 7 个 authored slots；可见 native indices 为 `0,1,2,3,5,6`，monk 路线 native 4 隐藏。
- native 0–3 会支出玩家资源或发放更强奖励；native 6 拒绝整个贡礼并给贡使添加 -50 opinion。固定 native 5 只向 AI 贡使发放通用合法性，不消耗玩家资源，然后按原版 after 链完成抵达结算。该选择仍是原版玩法状态变化，不得描述为无效果通知。
- `Z:\p2m138_a\manager-cycle-recovery.json` SHA-256：`78E254E2940E52CA314364D5D7FA4E332E8CA7C40E0DBF80986A646A8C3E934F`
- `Z:\p2m138_a\runner-report.json` SHA-256：`AE17917E722ECC8B522B1E5D01CEE88D9160D7419E5ED975BECA3DCFA0D5ECF7`

## 健康保护门禁

R138 没有发生角色死亡，所以用户授权的“三次连续角色死亡后添加健康值与 buff”仍未满足。当前已确认的同类 owner terminal 是 R133 与 R137 两次；R134 启动超时、R135/R136/R138 随机事件阻塞均不计入死亡次数。

## R139：贡礼回报的第二个 scope 集合

- R139 的 `tribute_mission.1005` 仍为相同 7 个 authored slots、相同可见 native indices `0,1,2,3,5,6`；按钮契约没有漂移。
- 本轮没有 `concubine_character` 与 `rejected_concubine` 两个临时 scope，其余 14 个 scope 名称、类型、别名关系全部匹配 R138。
- 验收契约将 R138 的 16 项和 R139 的 14 项登记为仅有的两个完整名称集合；`concubine_character`/`rejected_concubine` 若出现仍必须分别为 character/flag。其他缺项、增项、类型或按钮映射变化继续 fail closed。
- `Z:\p2m139_a\manager-cycle-recovery.json` SHA-256：`739E2D1F5B0DBA9C877D465E29C620E13EB457CD16A77F5030EF0CC63F6B64E6`
- `Z:\p2m139_a\runner-report.json` SHA-256：`758B64240F8D8085EF6C7C61586CDF360A03509235F147DA8FA9F2E098F8B537`
- R139 是已知事件严格形状 RED，不是 owner terminal，不累计健康保护次数。
