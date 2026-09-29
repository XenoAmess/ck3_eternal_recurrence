# E2-04 a08 d06 骑士第五行身份证据账（2026-09-29）

外置 append-only 原始审计：`D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-v3-media-audit-20260929-a01/e2-04-d06-fifth-row-identity-a01.md`，SHA-256 `1E6ACBDEFD6FF9B89D5E8E391337AA98C6133151973E580ADB37FAC7AE3C8956`。其来源表逐件记录原始 t010 帧、a08 原生 trace、d06 精确存档与 sidecar、独立冷载回执、失败的 V3 响应及全部 SHA。此处只登记剪辑使用边界，不替代外置原件。

| 证据 | 可用结论 | 边界 |
| --- | --- | --- |
| a08 同一次受管日推进的 trace `E53502D3…C14554` 与精确 d06 存档 `F05A48A0…42A0B5A` | trace 的 11 位真实 side 1 骑士依次绑定 Regiment 57–67；d06 存档中 11 位人物的姓名、CharacterID、regiment 与该顺序吻合。trace 勇武序列为 `14,14,13,12,11,10,9,5,4,3,2`。其中第 5 位是 CharacterID `34333` / Regiment `61`，第 4 位是 `32440` / `60`，两人的存档名均为 Geoffroy。 | trace 的 `34333=11` 是事件写回前的输入读数，不是 d06 同帧后态勇武。 |
| 独立冷载的 90 秒录像中原始 t010 帧 `D20B4F3D…1369B2` | 暂停的 1066-12-09 骑士浮窗显示 11 行，勇武序列 `14,14,13,12,7,10,9,5,4,3,2`。11 行姓名和顺序与上述原生名单对齐，10/11 勇武值一致。第 4、5 行均显示“伯爵若弗鲁瓦”，分别为 12、7。 | `34333 ↔ 第 5 行 7` 是完整名单对齐后的强推断；画面没有 CharacterID，不能写作 GUI 或原生同帧直接识别。 |
| trace `records[5].battle_events[1]` 与 d06 存档人物字段 | 原生 trace 记录 `knight_maimed_by_enemy`，目标 CharacterID `34333`；精确 d06 存档中该人物仍 alive，直接 trait 索引含 `120=one_legged`、`115=wounded_1`。 | 事件与存档 trait 是两条证据；未证明 trait 的取得时点、事件是唯一原因、完整 effect write set，或精确四点勇武损失的因果归属。 |
| d06 V3 失败响应 `36150C74…671DD` | d06 冷载已到同一日、War 4 / Army 18 / Combat 16777218。 | V3 请求 RED，无成功的同帧 `CharacterID 34333 → current prowess 7`；Regiment 61 的当前 effective damage/toughness 也仍 RED。 |

可按证据分别讲“a08 trace 记录 34333 的致残事件”和“独立冷载 d06 画面第五行显示 7 勇武”。若将两者合并解释，必须标明完整名单匹配属于**推断**。该单帧及录像仍只有机器 PTS/稀疏画面检查，没有 clean span 认证或人工 1× 完整审阅签核。补齐直接身份数值证据需要同一暂停 d06 帧返回 `character_id=34333, regiment_id=61, current effective prowess=7` 的原生读数，或带 CharacterID 的骑士 GUI 行身份。
