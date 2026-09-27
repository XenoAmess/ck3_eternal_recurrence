# WAR31 持久停战槽的精确方向（2026-09-28）

[原版停战脚本链](war31-dejure-truce-script-2026-09-27.md)静态给出本次进攻方胜利的单向效果方向 `30097 → 29829`，[投降后的存档差分](war31-r0197-one-shot-live-result-2026-09-28.md)读取到人物对 `(first=29829, second=30097)` 只有新增 `truce_1`，到期 `1079.11.17`、result `victory`。此前不能仅凭字段名猜测 `truce_1` 对应哪一方。新增[只读槽方向投影器](../../ck3_autonomous_player/tools/project_war31_truce_slot_direction.py)把精确版本的存储、序列化、反序列化和原生方向查询连成一条可复核链。

执行时重新校验 CK3 `1.19.0.6` EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、已验证的存档差分报告 SHA-256 `84154554437CE96FB751DC6DB23E65847CA974CD92917A2FCB32B12C3FC11634` 和两份 Rakaly 文本 SHA，并重新解析人物对。冻结的外置结果是 `D:/ck3-research-artifacts/war31-live-20260927/attempt-05/truce-slot-direction-01.json`，SHA-256 **`B92589268FD699258A626994A780A6C620EDAD2E43EFD2015BF588BE2C1C1BCD`**。工具只读 EXE 和保存文件，没有启动 CK3 或重复提交投降。

| 精确原版证据 | 结论 |
| --- | --- |
| 字符串表 `0x42BF8D0/0x42BF8E0` | token ID `0x2B52` 对应 `truce_0`，`0x2B53` 对应 `truce_1`；字符串 RVA 分别为 `0x429A390/0x429A400`。 |
| 关系序列化 `0x23655ED→0x236561B` 与 `0x236564B→0x2365672` | 关系对象 `+0x28` 写作 `truce_0`，`+0x58` 写作 `truce_1`。反序列化 `0x236508C–0x23650A0` 对 token `0x2B52` 选 `+0x28`，否则该分支选 `+0x58`。 |
| 原生持久日期查询 `0x2663272–0x26632B7` | 查询 owner ID 与 relation `first`（`+0x08`）相等时选 `+0x28`；与 `second`（`+0x0C`）相等时选 `+0x58`。`has_truce` 函数 `0x26631E0` 使用相同两方向槽。 |
| 原版 `CAddTruceEffect<0>` `0x2EDB1A9–0x2EDB1EA` | 写入时也按 owner 是否为 `first/second` 选择 `+0x28/+0x58`，随后写日期；与读取方向一致。 |
| WAR31 战后精确保存 | 关系块 `first=29829`、`second=30097`，新增 `truce_1`，故**已保存的方向是 owner `30097` → toward `29829`**，到期 `1079.11.17`、result `victory`。 |

这条保存层方向与原版 `add_truce_one_way` 的进攻方 `30097` 对防守方 `29829` 脚本方向吻合。结论的范围是**这份精确保存中的既存停战方向和到期日**；战后保存比动作即时原生帧晚六天，不能由此声称捕获了 `add_truce_one_way` 写入指令的同帧时间线，也不能推断其他战争、其他版本或条件效果的所有停战。`same_native_frame_binding=false` 与报告中的 `causal_attribution=not_proven_for_every_intervening_save_write` 保留这些边界。此前文档的“槽位方向未验证”是产生本证据前的历史状态，后续引用应以本页为准。

聚焦校验：`<verified-python> -m pytest ck3_autonomous_player/tests/unit/test_project_war31_truce_slot_direction.py -q`，普通与 `-O` 各 `2 passed`，覆盖人物对两方向映射及缺失／未知槽拒绝；实际 EXE opcode、token 表、保存哈希和重新解析由上述外置报告验证。合成测试不冒充实机读回。
