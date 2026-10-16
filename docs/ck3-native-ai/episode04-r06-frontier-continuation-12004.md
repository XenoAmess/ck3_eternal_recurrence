# R06：仅续读已观察 frontier8 至 depth11（1.20.0.4）

本增量在既有 `ck3_inspect_gui_window_tree_v1({window_kind:"military"})` 的固定补员 expression 中增加可选 `definition_frontier_continuation_depth8_12`。没有新增工具、caller 指针、路由参数、provider 执行或 GUI 动作。原 full candidate 的 depth8 unavailable 和独立 prefix0–7 保留。

依据是 R189 两处实际控件的稳定8节点前缀：0/4 是 mode0/flag0/direct0，1–3 count0，5–7 definition null；所有边为 `context_e8`，frontier8 context 存在，实际 eligible provider RVA集合为空。它只证明0–7范围内的情况。见 [便携实证](acceptance/2026-10-17-r189-parent-prefix/EVIDENCE.actual-a34.json)及[最终变量来源](episode04-r06-type635-variable-origin-12004.md)。单读 frontier8 若 definition null 或无 key635，无法判定后续 receiver 是否存在，因此采用 depth8–11 的独立双读候选段。

机器 `desktop-3fevhd2-1c74096080`；源码基线 `6bf30840af44231653f8e914389b59c8798f2cc1`。本工作包只写外置候选，不读新 EXE、不构建、不执行 native、不联系 SDK、CK3 或桌面。Python 冷 case 与未来 native fixture / 实机资格分别记录。

## 生产接线

新 `XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004` 默认 OFF，并要求 `XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004=ON`。需要新叶的下一次生产配置同时打开两者；OFF 时新叶不发布。复用现有 exact `.4` source pins、owner-thread/frame/GUI owner 保护和最多4固定 callback；Driver、MCP schema、动作入口均不增加参数。

现有第一次完整 capture 在 depth8 保存实际 frontier 与 visited0–7，然后保留原 failure。开启新开关时，先从该 frontier 读8–11；第二次 capture 从根独立复核 prefix，再从其独立 frontier 读8–11。按“前缀A→续段A→前缀B→续段B”的顺序比较 private identity、每项 mode/flag/原始值/解析出的 RVA 及停止状态。不会把两次捕获的不同 frontier 拼接。没有第三次根遍历。

总预算仍是原单 leaf 的4096次读、64KiB、20ms协作式 deadline，没有另开预算。first-key-match、definition+108 优先/否则 context+E8、parent flag4C 过滤与 mode 分支均沿已闭 `.4 3AC3EF0/3AC1C00`。flag0 provider 只记录 present，不解引用；只有 eligible dynamic provider 才读取模块内 vtable/slot2 RVA。mode0/1 且 flag非零是原生静态 pending 终点，续段不再读取其 parent。provider return 和最终变量表依旧 unknown。

## availability 与停止结果

新叶只有在 prefix 已独立 available、两次续段完整且一致、共享预算通过时 available；`available` 的对象是**有界来源段**。`current_variable_table_observed`、`native_receiver_selected`、`provider_invoked` 固定 false。

| stop_reason | rows / stop_depth | 确切意义 |
| --- | --- | --- |
| `depth_limit` | 4行8–11；stop_depth12；next_context_present=true | 当前上限截断，depth12 definition 未读；更深 receiver unknown |
| `null_end` | 1–4行；stop_depth 为最后节点下一深度；next=false | 已读 parent 为 null；不是 provider 失败或免费补员 |
| `cycle` | 0–3行；stop_depth 为重复节点深度；next=true | 节点与已访问0–11内身份重复；不解引用重复节点，不称原生已终止 |
| `static_direct_terminal` | 最后一行有 flag非零/mode0或1；stop_depth 为该行；next=null | 若 pending 到达该项，原生 resolver 会 AL1；parent 不再读，`parent_edge=not_read_native_static_stop`、parent_present=null。空 direct 仍不等于有效 receiver |

每行发布 depth、definition_present、原始 count（无 definition 为 null）、first_match_entry_index（无命中为 null）、first key635 match（至多1项）、mode/flag/direct/provider presence/实际 RVA，以及实际 parent 分支与 presence。全段 receiver_variable_index 是同一稳定声明索引；表内命中 index 与它分别记录。raw heap 指针不发布。

读取失败、非法 count、共享预算不足或双读变化产生独立 unavailable 子叶；rows为空、stop/index/type 等观察值为 null。可带原失败 capture 的 typed diagnostic（depth上限12），不能把 unavailable 解释成无 provider。原 full failure 仍保持第一次 depth8/pass1，而新诊断仅属于续段。

## 验证与下一步

4项新增 Python 行为检查通过生产 `normalize_callback_binding_rows_12004`，涵盖正常实际 RVA/flag0过滤、null/cycle/static 停止、跨前缀索引/伪造停止/越界与 unavailable unknown。旧矩阵没有重跑。

新增单个 `gui_refill_frontier_continuation_12004_fixture.cpp` 直接调用生产 reader 和 serializer，包含 provider RVA 双读变化、不可读、depth12不读、flag0 provider不解引用以及三种提前停止。CMake target 为 `xar_test_gui_refill_frontier_continuation_12004`；本任务禁构建，因此 **native compile/fixture/wire NOTRUN**。Root 按标准 build producer 与精确 EXE SYSTEM verified 流程执行后，可对 fixture 输出逐行调用生产 callback consumer；外置 `run_focused.py --wire <actual-wire.jsonl>` 已准备。

下一次 live 仍只需同一条 military tree 查询。若新叶给实际 eligible slot2 RVA，才围绕那个唯一源地址作有限完整函数研究；若仅有 filtered entry 或 depth_limit，不能授 getter、receiver、toggle、actual_ADD 或业务失败资格。
