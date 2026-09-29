# H2743 守方投降：最窄同帧原生输入包

状态：**只读前态输入可束缚，投降效果不可投影。** 本候选不新增 CK3 原生调用；它消费 #448 已实现的 `query-defender-de-jure-exit-terms-v1-16777231` 双读、两者之间的 `query-war-termination-options-16777231` 和前后暂停原生快照。[纯函数](../../ck3_autonomous_player/src/xar_autoplayer/bridge/h2743_surrender_preaction_inputs_v1.py)只生成 `same_frame_preaction_inputs_only`，不会形成正式退出条款或动作。没有启动 CK3、调用 loaded-effect preview、执行 `setup/resolve`、推进日期或投降。

真形状测试夹具从已封存的 [attempt-12 原始 payload](h2743-defender-dejure-partial-truce-attempt-12-2026-09-29.md)提取，保留两份 baseline 与 options 的字段值，前后大型 snapshot 只留本投影所需字段；夹具 SHA-256 `361CD303E1ABBDA6EB1365C2C605BB9CE51AE78E264342251FB23A456462F0CA`，每个原件 SHA 写入[夹具](../../ck3_autonomous_player/tests/fixtures/h2743_surrender_preaction_attempt12.json)。提取后的 JSON **不是原始文件字节或完整游戏快照**，原件留在外置 append-only attempt；验证本候选不能代替已有 runner 的完整同帧与二进制门。函数要求显式给出精确 checkpoint SHA claim，并标 `source_bytes_authenticated_here=false`；输入包自身不校验原存档字节。

输入包**只接受 attempt-12 精确帧** `native:3`、public/native revision `4/3`、raw date `53217264`、connection generation `1`、checkpoint SHA `A501…E9`、episode `native-29829-2bc2d599f7f9`、WarID `16777231`、主攻 Landolf `30097`、主守 Robert `29829`、CB index/key `17/individual_county_de_jure_cb`，并比较**完整活动战争签名**。两份 baseline 和一次 options 的 `backend_id` 必须各自精确为 `native-headless`；整体换成 `synthetic-mock` 也拒绝，不能叫作原生观察。两个 native baseline 的投影结果必须完全相同；options 的六字段、当前合法与接受、`terms_observable=false` 必须一致。即使前后帧、两份 baseline 和 option **一致漂移**到 `native:4`、revision `5/4`、date `53217288`，仍须拒绝，不能给新帧贴旧 checkpoint SHA。原生 driver 的 MCP 投影已省略原始 CB index/key 与 `same_frame_stable` 字段，本函数只为了调用既有严格式 validator 临时重构三项校验参数，**不把它们再当独立读数发布**；CB 还需直接 options 校验，稳定性还需双读与前后快照。旧或伪造的有符号结果、资源缺行、休战 days、错误 WarID/版本/战分/连接代次全部拒绝。

| 当前可发表的输入 | 明确边界 |
| --- | --- |
| 目标有序 Title ID `[2128]`、当前 holder `33435` / personal liege `29829` | 仅前态；`scope:target` 和 old→new 未读。 |
| Landolf/Robert 各七类，共 14 行资源余额；两方 gold 前态分别 `22861397/100000`、`111861020/100000` | FP2 真实 payer、欠款、贡献条件未读；两方 gold 是**可能 payer 的余额**，不是付款额或 signed delta。 |
| 同帧 FLEX owned-perk key 命中 `false`、双方游牧 flag `false`、合取 `false`，以及脚本候选方向 `30097→29829` | FLEX 还未证明完全等价 stock `has_perk`；SHORT/LONG/BORDER_RAID_PAIR 未读。V5 全槽值只属结构候选。脚本方向基于[六份精确原版源码](h2743-surrender-effect-input-contract-2026-09-29.md)，不是新 live effect trace。 |

`script_candidate_days`、**受降后的**实际 `expiry_date_raw`、FP2 payer/owed amount、运行时目标 scope、威望因子 F、实际 enabled-effect selector/tree、title/封臣变动、14 行有符号资源结果、`directed_truce` 均为 `null`。特别是已有 `RaiktorActualTruceExpiryV1` getter 只以**当前玩家作为 owner**读取**已存在、已应用**的关系槽；H2743 所需新关系 owner 是攻方 Landolf，且未来投降尚未发生。不能复用它把受降后到期日读成当前值。`setup_de_jure_cb` 写 context row，`resolve_title_and_vassal_change` 写变更队列，旧 broad preview 曾崩溃；当前没有可证明只读的 native 结果槽或完整启用效果树 selector。

因此始终 `effect_projection_complete=false`、`material_complete=false`、`recommended_outcome=null`、`action_literal=null`。本分支只做可复核的最小输入包和负例门，不创建 `query-war-end-effect-inputs-v1` 假入口。若 H3937 先提供可用同帧 roster，它能补参战者/贡献读数，但**不能独自解开** FP2 owed 变量、scope/F、两条脚本根的实际 loaded dispatch、RNG/延迟效果或未来休战持久化。新的实机 producer 必须单独编译新 DLL、pin 精确 SHA、另开 attempt，并等待高优先级屏幕任务释放。

聚焦测试：`test_h2743_surrender_preaction_inputs_v1.py` 普通及 `-O` 均 7/7 GREEN；夹具包含真实同帧 baseline/options 字段，负例检查一致漂移的新帧、三项同改合成 backend、局部帧/完整战局签名漂移、错误 checkpoint claim、缺资源、伪造 material/truce、选项 CB 改变以及双读余额漂移。这验证输入边界，不代表完整退战决策。
