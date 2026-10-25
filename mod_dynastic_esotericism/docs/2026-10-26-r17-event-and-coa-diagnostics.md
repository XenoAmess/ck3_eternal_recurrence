# R17 事件形态与纹章保存诊断

`machine_id: desktop-3fevhd2-1c74096080`。本记录在 R0017 闭场后离线补入；来源观察时间为 2026-10-25 UTC，文件日为本地 2026-10-26。只读取已保全回执与原版源码，没有启动 Game、生成新 Save 或改写冻结 runtime。精确来源、文件大小和 SHA 见[小型来源记录](evidence/r17-event-and-coa-source-observation-2026-10-26.json)。

## faith_creation.1021

R17 的原生事件实例 2 在 `date_raw=53144376` 有 17 个 saved scopes。它在 R13 的 16 个 scope 基础上还含 `des_identity_rite`；两者均包含 `differing_doctrine`，不能视作已资格化的 `differing_tenet` 七 scope 或附带 `converted_ruler_capital` 的八 scope 变体。

此次观察已追加到共享持久知识库 [records_faith_creation1021_12004.py](../../ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_faith_creation1021_12004.py) 的 `observations.exemplars`，供公共知识查询返回。它仍为 `scope_contract_qualified=false`、`automatic_selection=false`。自动合同完全未改，规范 JSON SHA 前后均为 `c53e62915766cdb2687675f4417b25b65cefe3623b6679155c6068fe3e0fc8bf`。回归实际将此 17-scope 形态投给现有 resolver／scope checks／推荐入口，确认其继续拒绝。

实际显示 native0／1，操作者按用户已授权的陌生事件续行策略选择第一项。提交回执确认旧实例消失，独立原生查询同日也返回无活动事件。这只证明该实例的处理后态；奖励的实际增量、后来不再出现、宗族族长归属或整案完成均未由此成立。原版选项只有信仰资源奖励，没有改宗、生成宗族或写入族长的效果。

原生 context 的 `founder=31254` 与继承的 `des_requested_dynasty_founder=41288`／`des_selected_dynasty_founder=41288` 分别保留。Faith／Rite／Dynasty／House／doctrine 的不可用 payload 身份继续记为未知，不能从 scope 名称补全，也不能仅凭这些 inherited scopes 归因 head 问题。冻结 R17 runtime-a16 未热改。

原版事件文件完整 SHA 仍为 `419c04b9ca889e96e572b894ec346ae6119af2fd6eb9be4833d6659edfba923e`。1273–1382 行、key token 至闭合大括号、去掉随后换行的原始块为 2833 字节，109 个 LF、0 个 CRLF；原块 SHA `dc10bf5f40558169ccfb0b8a38b4699c1b2f2f7338fd544b780945242fc01919` 已与历史记录相同。先前描述中的“original CRLF retained”与这些匹配字节不符，本次只纠正描述并保留旧描述及机器／时间补注，未改历史原始证据或既有 SHA。人工把块转成 CRLF 会得到另一 SHA，不能追认为历史原件。

## a08 选定纹章对象观察

外置一次性行政候选 `resume-product-a20/operator-reference/observe-selected-save-a08-coa.py` 基于原 a07，增加 `--coat-of-arms`；0 是合法 ID。真实原版 Save 的解引用路径为 `coat_of_arms.coat_of_arms_manager_database.<id>`。它保留选定对象完整 AST（包括重复 emblem／instance）、缺失字段和实际 held-Save SHA、decoder／source-helper pins；沿用每块 512 KiB、总 token 缓冲 4 MiB、JSON 输出 16 MiB 上限。小 selftest 覆盖 ID0、textured／colored／instances、重复 ID 和截断拒绝。原 a07 未改，也没有新增生产 parser。

Root 已在 R17 保全的 day+1／day+2 Save 上运行候选。本次重新校验两份观察文件 SHA，逐对象从完整 `entries` 重算 AST SHA 并比较：

| 保存日期 | Dynasty12156 的 CoA | House12760 的自有 CoA | 完整内容 |
|---|---|---|---|
| 1066.9.17 | 28817 | 28818 | 相同 |
| 1066.9.18 | 28817 | 28818 | 与前日相同 |

四份 CoA AST 的 SHA 均为 `bdd7195e38bdeebf98cbd08b13e0f25ec483a05954fa1b93678647dba232513c`。图案为白底、红蓝颜色和三只 `ce_leopard_passant_guardant.dds`，完整位置／缩放见来源摘要；不是仅比较 `coat_of_arms_id` 或一个纹理字段。Dynasty 与 House 名称均为 `R17 Dynastic Rite`。

两个对象的数据库 ID 不同，完整内容相同；不能把 `set_coa` 内容复制误写为共享同一对象 ID，也不应假设缺少自有字段的其他 House 自动继承。这两次 Save 支持随机 fallback 的图案在两天后态中保持一致。源脚本只有一次 `generate_coa` 调用；保存快照本身不能统计 RNG 调用次数。

该观察未验证冷加载、两个预设教派的原 RGBA 图标实机显示或首位创建者最终族长归属，也不提供完整核心场次或发布通过结论。两个预设的精确图标仍待各自实机验收。a08 的选择集上限及选定图谱也不能证明完整世界所有存活信徒都已被扫描。

## 本次验证

事件知识单元测试 2 项通过。完整数据记录文件通过严格 mypy（含 strict-equality，导入 silent）；完整测试文件通过默认 mypy 检查，旧有未标注函数不外推为严格检查通过。源合同 SHA 前后相同，17-scope 回归继续被现有守卫拒绝。没有新增生产 Python 业务模块、修改业务守卫或宣称产品 PASS。
