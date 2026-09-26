# 自然增援两案：安排、出伤边界还能读到什么（2026-09-27）

对[两次完整七边界回放](battle-reinforcement-and-join.md#2026-09-26两次自然增援的七边界身份同日出伤与逐团写回闭合)再次做只读投影，专门检查掷骰、事件身份和战宽的可见性。投影器 [`project_native_join_schedule_boundary.py`](../../ck3_autonomous_player/tools/project_native_join_schedule_boundary.py) 先调用原七边界投影器，重新核对不可变源存档、游戏 build、桥 DLL、原始回执哈希、七个边界和完整清理，再从同一 `finish` 回执取字段。[机器结果](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_join_schedule_boundary_v1.json) SHA-256 为 `CBB7956D8D3B1F466F3D09FD8C79F8ECD960A7C0FC8954703921747FD59D4DFB`。两个 attempt 分别位于外置 `D:/workspace/ck3_native_war_ai_promo_work/episode01-prearmed-join-live-attempt-026/` 和 `.../episode01-prearmed-join-live-attempt-027/`；是独立回放，不能连成一条随机轨迹。

| 源日→抵达日 | 新军 | side0 兵团数：源日安排后→抵达日首次出伤前 | 同一七边界保留的掷骰 | 原始基础/已结算优势 | 源日安排局部 RNG `word0` 前→后 |
| --- | ---: | ---: | --- | ---: | ---: |
| 11→12 | Army 22 | 27→40 | 7 / 8 | −300000 / −1100000 | 2742185670→2742185677 |
| 21→22 | Army 28 | 39→44 | 3 / 8 | −300000 / −1500000 | 2863158941→2863158949 |

两案都是 CombatID `16777218`，七条捕获记录均无失败标志，抵达日首次 side0 `phase-fire` 入口已经包含新军；来源安排边界和抵达日出伤边界之间，记录在战斗对象上的 `advantage_rolls_raw`、基础优势与已结算优势值未改变。出伤前 side0 `current_fighting_total_raw` 分别 `160317482→410690163` 和 `368409866→470651390`。因此本案至少不能按旧参战人数/旧兵团列表计算到达日出伤；本案出伤使用的优势对象字段仍是这组已记录值。`word0` 是局部随机状态原始字段，前后数值差 `7/8` 不能未经抽签入口对拍就解释成“恰好抽了 7/8 次”。这些记录也不能证明所有增援路线都复用优势，或排除未捕获的中间重算后恰巧值相同。

事件与战宽尚未闭合：七边界里两侧 `scheduled_commander_native_event_load_index` 全为 `null`，只有**进程内指针 token**；`effect_roots` 为空。不能由此命名触发的具体事件、断言没有事件候选，或把 token 跨进程当稳定身份。捕获中没有显式战宽输入/写回字段；`first_fighting_subtotal_raw` 虽可读，却不能直接命名为战宽。现有两案只支持“名单先扩大，再在当日出伤”，尚不支持完整的 roll/event/width/counter 转移模型。

下一次有界实机采集应在同一日更新序列中，对增援加入前后分别读取：战宽输入和计算后字段、可稳定映射的事件 load index 与抽签入口、反制输入和写回，以及局部 RNG 的具体调用点。对于不同路线/阵营/撤退重入另取独立战例；只有两侧输入、阶段出伤和后续回写全链对拍通过，才把这些转移接入智能体的逐日 trial kernel。
