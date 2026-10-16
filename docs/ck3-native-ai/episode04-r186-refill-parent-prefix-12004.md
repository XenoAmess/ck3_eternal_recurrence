# R186：本地 type635 的 mode0/null 与下一段父链取证

R186 的两个稳定本地匹配项均为 **mode0/flag0/direct=false/provider=false**。这是已经完整读到的匹配 entry，不是没有匹配项。它只排除了这两个本地 entry 的 provider 分派；完整父链仍在 depth8 前停止，不能写成“补员 provider 不存在”或“军队页没有 MilitaryView”。下一次唯一实验应继续使用既有 military-tree query，保留已访问 8 层的稳定前缀，不点击补员按钮，不追 null provider，不调用表达式/provider。

机器 `desktop-3fevhd2-1c74096080`；R186 query 时间 `2026-10-16T16:38:46.692522Z`，PID16240/create134366417898733491/gen1、episode `native-31254-68303c9ae4fb`、actor31254/date53148432、native3/public4、pump25852/ticket7。原件1,029,909B/SHA `899bdbf59aa7a539b37af73631af2ed5776d4ccacb82a600f6d77a623c115f81`。本研究只读取 Root 提供的已封小摘要和两个2,699B精确切片，没有读取整树、游戏 EXE/save 或接触 SDK/桌面。来源与精确 byte spans 见外置 `r186-r06-actual-analysis-a01/ROOT-DELIVERY.actual-a01.json`（SHA `f65176ae60295bea5445c310c9a926f00c503342397eb8f08873197511ec9f5a`）。本候选基于 `d05b0c780b615faa714fdf0535403bb2e6941faf`；离线机器/时间、原始 source 与候选 pins 在 a31 delivery 中。R186 历史帧不可充当下一场 fresh admission。

## 实际叶与源码含义

实际 outer 路径 `0/0/0/2/3/0/0/0` 可见且 enabled，另一路 `0/0/0/3/5/0/0/0` hidden 且 enabled；两者本地 count1/active1、index0/type635、present=true/stable=true，唯一 entry 是 mode0/flag0，两个 presence=false、vtable/slot2/owner 均 null。full 候选共同保留 pass1/read51/depth8、`candidate_parent_depth_exhausted`，其 index/key=null、entries=[]、stable=false。第8层 definition/count 为未知，不能用 read51 反推真实链结构。

本轮复用已持 actual `.4` 完整原字节：`3AC1C00`449B/SHA `8efccb73…6e43cfc`，`3AC3EF0`879B/SHA `476ac967…5b5a2a7`，`3AC38C0`927B/SHA `52fe6866…6d9506`，`3E4C090`406B/SHA `f166a756…9ca292`。没有新的 EXE 读取。

1. `3AC38C0` 先按声明 key 查本地 first match，再在 `3AC3B34` 调 `3AC1C00`。mode0 经 `3AC1D45→3AC1D9A`：把 entry+0 写入临时 variable+0，将 variable+0C 写1，AL=1。R186 该 entry+0 已稳定为 null；这个分支根本不读取 provider+38。这里的 AL1 不证明最终 receiver 已解出。
2. `3AC3EF0` 重新查本地 key；`3AC401C/4020` 只有 entry+4C 非零才跳过加入 pending。R186 flag0 使该变量仍需父链处理，不能用本地 resolver 的 AL1 把它当成终值。
3. 首个 parent 优先来自 local definition+108，零时取 context+E8（`3AC40CF..40EF`）。之后每层 context+E0 可为空；查 key 的 first match 后，必须 parent entry+4C 非零才在 `3AC41A9` 调 resolver。flag0 的 parent entry 即使含 provider 指针也被过滤，不能按 provider presence 认定其会调用。匹配且 flag非0 的 mode0/1 静态返回AL1，会从 pending移除；dynamic provider 的返回状态当前没有观察。
4. 父层继续边为其 definition+108 优先、否则当前 context+E8（`3AC41F0..420F`）。这不是 GUI `child_path` 的父控件链。`3E4C090` 还先调未在本包闭合的 `3E4BC50`，再读取临时 variable 后调用 final target。当前没有执行这条 callback，不能把只读 tree 的“未调用 provider”写成游戏动作失败。

原版 `window_military.gui` 当次读回111608B，SHA `4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac` 与已持 source 一致。根第8/9行是 `[GetVariableSystem]`、`[GetPlayer]`；第488/898行 onclick 是 `[MilitaryView.OnMilitaryReinforcementClick]`，checked 第493/903行是对应 getter。root datacontext 不等于当前 type635 的最终 receiver；两处局部 null 可能由继承环境补齐，但谁构造/提供它仍须观察。不能用当前玩家或根 context 替换 receiver。

## 已施工的最小候选

`XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004` 默认 OFF。ON 时仅扩展现有 `receiver_entry_candidates_12004`，新增可选 `definition_chain_prefix_depth8`；没有新 MCP、hook、ring、native getter、任意地址/RVA参数或 provider 调用。

原 full 首次触发 depth8 上限后，复制原失败字段；在同一 load 闭包、4096次/64KiB/20ms总预算内，把现有第二次 local-only复核改为“至相同 depth8 边界即停”。不读取第8层 context+E0，不增加层数，也不做第三次复核。两份完整私有 identity（包括全部经过的 key前缀、context/definition/table/entry/provider与parent指针）及公开 rows 一致，才授新前缀 available。首个失败/循环/预算/不稳定不拼 partial。旧 full status/entries/index/失败诊断和 local 独立资格不改。

每行严格记录 depth0..7、definition presence/count、0或1条完整 first-match descriptor、实际采用的 `definition_108`/`context_e8` 边及 parent presence。所有 heap 指针仅用于私有一致性检查，不输出。available 明确 `walk_complete=false`、frontier_depth8/context_present=true；frontier definition/count仍未读，`current_variable_table_observed=false`、`native_receiver_selected=false`。unavailable 要求 rows空、稳定false、index/key/frontier全部null。

严格 consumer 复用旧 entry 的宽度、RVA和owner规则；另拒绝行跳号、不完整边、空 definition 捏造表/definition边、flag0 parent 捏造 provider/owner解引用、越过 mode0/1+flag非0静态终止点，以及 local/count/descriptor不一致。保留 a30 的 full/local 一致性门。原 profile没有新叶时仍是 unknown，不能补空数组当“没有父候选”。

## Root 下一次只读一次与停止规则

Root 后续在新 source/build 准入后，先定向验证 `xar_test_gui_refill_parent_prefix_12004`，再按正常 producer 构建 ON profile。这里均未构建运行。进入 fresh paused/map-ready、actor/episode/PID/create/gen/source一致的场次，沿现有 opener取得军务窗口可见后验，然后仅调用一次：

```json
{"window_kind":"military"}
```

工具仍是 `ck3_inspect_gui_window_tree_v1`；existing Driver 的前后 snapshot/frame/public binding 不变。只消费两处固定 source-qualified expression 内的 `receiver_entry_candidates_12004.definition_chain_prefix_depth8`，先过生产 strict normalizer。没有新请求参数或第二 endpoint。

| fresh 严格结果 | 可复用结论与下一动作 |
| --- | --- |
| parent key未匹配/definition为空 | 只排除这一已读层；按该行实际边解释，不授最终 receiver |
| parent匹配且flag0 | 该 entry 被父 resolver 过滤；即使provider_present=true也不能追其null/未读slot |
| parent匹配、flag非0、mode>=2、模块slot2非null | 得到这一条实际可候选 provider source RVA；下一仅对该唯一入口建有限 source plan，仍不执行它 |
| 8层均无具名合格slot2 | 只闭前缀，深层仍unknown；到此停，不能扩大cap或重复同query期待自动改变 |
| unavailable/缺叶/跨帧/不稳定/预算超限 | 保留具体缺口并停，不把它解释为无receiver或免费补员 |

已完成4项新的 production callback consumer 用例（含 filtered provider、local冲突、静态终止矛盾、frontier/partial/unknown），并实际消费 R186 两个原始小叶，确认未凭候选新增父链事实。新增 native fixture源覆盖稳定8层、flag0 provider不解引用、depth8 definition不读、parent边来源/parent mode复核变化及共享deadline；它和 serializer wire均 NOTRUN。本候选不授 MilitaryView getter、补员toggle、开关业务后验或 actual ADD。
