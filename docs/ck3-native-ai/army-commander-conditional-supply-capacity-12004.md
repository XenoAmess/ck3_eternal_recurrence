# 1.20.0.4 候选统帅的条件补给容量

既有 `ck3_query_army_commander_candidates` 可在同一次只读查询中附带每名候选人的 `conditional_supply_capacity_v1`。它读取候选人当前的真实 modifier aggregate，解释原生容量公式；不任命统帅，不把一般统帅评分换算成容量。使用者仍须独立检查 `can_assign`。

该字段是条件值：假定任命后仍使用此次观察到的候选 aggregate。字段固定 `assignment_applied=false`、`assumption=candidate_aggregate_unchanged_after_assignment`。实际任命可能改变上下文或缓存，须在正常任命后重新读取军队实际容量，才能声称容量已应用。

## 实际来源

- 游戏 1.20.0.4，Steam build 25734779，EXE 101040248 字节，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
- 本次机器 `desktop-3fevhd2-1c74096080`，有限读取时间 2026-10-15 20:28 UTC。复用既已核真的冻结 EXE 身份，不重复整文件哈希。
- 实际 `.pdata` 函数 `0x2C53BF0..0x2C541F9`，1545 字节，SHA-256 `b204d281bd06699cbd6863383696d131ff798c91168d79c7467e8879386c3873`。unwind `0x52B5C58`，头 `11240b00`，flags=2，无 CHAININFO。
- 本次新读取只有函数体 1545 字节与 metadata 16 字节。先 plan/check，再按已持有 section map 和 `.pdata` 缓存定点读取；未扫 EXE、未执行游戏。
- 可重建原始字节、完整反汇编和来源回执见 [有限源码索引](evidence/episode04-commander-conditional-capacity-12004/source-index.json)。

ABI 为 `int64_t* capacity(outRCX, CArmy* RDX, detailR8)`。只解释 `detail=null` 路径。`Army+0x120` 解析当前统帅；有效 Character 的实际 CALL `0x2C53C7D -> 0x28C3AC0` 取得 aggregate。无效统帅返回 loaded FULL。此候选能力仅对已由既有查询解析的候选 Character 读取该 aggregate，不制造临时 Army。

## 完整数值公式

有符号定点比例 `Q=100000`：

```text
FULL = actual runtime qword(image_base + 0x5C68C70)
A = candidate aggregate modifier[0x1D3 = 467]
M = candidate aggregate modifier[0x1D4 = 468]
left = wrap64(FULL + A)
right = wrap64(100000 + M)
conditional_capacity_raw = native_fixed_mul(left, right)
```

FULL 的实际读取 PC 为 `0x2C53CF7`，无统帅路径为 `0x2C54154`。两个 modifier 是 aggregate 的 `+0x68` key 目录、`+0x74` count、`+0xD0` values 的实际查找，不是 quality。接线复用既有 `get_character_modifier_aggregator` 与 `read_character_modifier(aggregate+0x68,out,id)`；每个有效候选仍只调用一次 aggregate getter，在既有 siege modifier 之后读两个容量 ordinal。

`native_fixed_mul` 保留原生两个分支，而非无限精度乘积：若两个操作数均满足 unsigned `wrap64(v+0xB504F333)<=0x16A09E666`，结果为 `trunc0(wrap64(left*right)/100000)`。否则以有符号 greater/lesser 拆分，`q=trunc0(greater/100000)`、`r=wrap64(greater-wrap64(q*100000))`，结果为 `wrap64(trunc0(wrap64(r*lesser)/100000)+wrap64(q*lesser))`。每次低 64 位 IMUL/ADD 均保留溢出语义，除法朝零。

`0x2C53E13` 的 null-details 分支直接跳至最终计算，实际结果写入 `0x2C540FC` 或 `0x2C5414F`。容量 getter 没有 clamp；本字段也不添加上下限。库存后续裁剪属于另一调用，不能据本字段宣称发生。

## Wire 与消费边界

老 `.3`、旧 fixture 默认不启用新 observer，候选行无此键；消费者也保留显式 null。只有 exact `.4` binder 启用并绑定 loaded FULL 地址。

非 null 对象的精确键为 `schema/status/source_character_id/scale/loaded_full_raw/additive_modifier_raw/multiplicative_modifier_raw/conditional_capacity_raw/assignment_applied/assumption/unavailable_reason/provenance`。四个 raw 值均为 canonical signed64 十进制字符串或 null，零不代表缺失。provenance 的两个 RVA 使用 JSON 整数。`available` 要求真实候选身份、全部输入和精确公式一致；`unavailable` 保留已读的原始输入，derived 固定 null 并给出原因。

候选 generation、Army 身份或 loaded FULL 在查询内变化时，清除 derived 并保留输入，不把失败当容量零。不存在来自旧快照、一般评分或当前统帅的补值。查询仍使用原暂停/owner/Army 身份合同；没有新增 query、MCP 参数或动作。

Python 严格入口为 `xar_autoplayer.bridge.army_commander_conditional_capacity.normalize_candidate_conditional_supply_capacity_v1`。策略须使用该入口验证同一候选、exact `.4` schema 与 provenance，再读取容量。条件容量不改变原候选资格或旧提案排序。

## 当前资格

2026-10-15 离线实跑完成原生公式静态断言及三个变更 TU 的 MSVC `/Zs /std:c++20 /W4 /WX` 检查；正式 Windows defines 为 `NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE`。早期 syntax-a01 漏这些 defines，发生 min/max 宏冲突；该失败保留，syntax-a02 使用正式参数通过。

Python portable contract tests 覆盖缺失/null、旧 `.3` 拒绝非 null、符号/零/溢出与 fast/slow 分支、部分输入保留、错误候选/来源/伪造结果拒绝。具体当前执行回执由主线入库时绑定。

尚未生产部署或取得实际 CK3 候选容量查询；未实际任命统帅。源码资格、离线编译/消费资格与实机资格须分别记录。外置过程资产本轮按 Root 的 `2026-10-16T07:45:01.597Z` 复核，不自动延长；入库知识和代码按仓库管理复用。
