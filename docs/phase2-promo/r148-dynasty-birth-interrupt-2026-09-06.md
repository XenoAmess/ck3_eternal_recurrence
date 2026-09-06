# R148 原版宗族新生儿中断（2026-09-06）

## 实机结果

- frozen source：`d8640b588debf27f8a80b1d59f5ddcb2c89c98cf`；源代码 ZIP SHA-256：
  `e5e666ef4295a9ba34d5cf48e745dd39e5d19977551318a3c43c71129f1c5224`。
- no-launch preflight GREEN：3,188 个 tracked files 与 ZIP 完全等价；R130 的 1,031 文件产品投影及四个关键
  B2 effect 继续逐字节 GREEN。
- CK3 只启动一次，PID `17616`；默认 5 速、玩家 CharacterID `32904`、connection generation `1`，
  fixture 生存保护只安装一次。
- runner 精确处理 `tribute_mission.1002` / `.1005` 后继续推进；本轮未重现 R147 的随机精神压力响应。
- B1 仍 active 时，runner 在 `date_raw=53154408` 暂停于新原版事件 `birth.1010`，按未知事件 fail-closed；
  因此尚未到达 clean review boundary，也没有执行同日 GUI 激活脉冲。
- `manager-cycle-recovery.json` SHA-256：
  `e6633aa9c9a9661484268371609e49a405099d951ce8ffda078c1559445de581`；
  `runner-report.json` SHA-256：
  `97fbbe9d0e229220b59b01066fe7027fef323027a24c61c7e6b9897d51b0e8bd`。

## 精确原版合同

CK3 1.19.0.6 原版 `events/birth_events.txt` 证明 `birth.1010` 是“由非 AI 的同宗族宿主为新生儿命名”的通知。
出生和默认姓名在窗口打开前已经成立；事件 immediate 只播放音乐并保存母亲配偶 scope，唯一 option 没有玩法 effect。
当前实机帧中：

- root 为玩家 `32904`；`child=16790642`、`father=real_father=spouse_of_mother=36354`、
  `mother=35997`；
- `is_bastard`、`is_child_of_concubine`、`matrilineal` 均为 typed boolean scope；
- 只有 native option 0 可见且可用。runner 只确认该按钮，不操作命名 widget。

合同绑定 exact event key、五个 typed character scope 的家庭关系、三个 boolean scope、完整八-scope 集合与唯一
native option 0；父亲/配偶关系或 scope 形状漂移都会 RED。该合同只覆盖 R148 的精确事件形状，不是 birth namespace
通配规则。

玩法状态、事件身份、scope 和按钮都来自 MCP/native；顶层 OCR/image 仅用于非玩法 legal-consent/front-end gate，
`coordinates_used=false`。本轮是验收线新原版中断，不是产品 RED，不改变逐号 readiness。
