# 现役优势原始输入：暂停帧可读叶子与重算时序（2026-09-27）

本页只针对 CK3 `1.19.0.6-steam23530548` 的 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。只读的 [`verify_active_advantage_pause_leaves.py`](../../ck3_autonomous_player/native_bridge/research/verify_active_advantage_pause_leaves.py) 先复核既有缓存/分项链，再核原版构造函数 `.pdata` 范围、23 处精确字节和 10 个直接调用目标。冻结[夹具](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_pause_leaves_11906.json) SHA-256 为 `D8B90C658FBC86639776BB161D66095628C7BCE4FBACB1661C556C2ACF21E23F`；聚焦测试会拒绝构造写回、刷新调用或函数 owner 篡改。本轮未启动 CK3、未读取实时进程，也未开放新的生产字段。

## 原版来源与先后

| 时点 | 原版精确事实 | 输入含义 |
| --- | --- | --- |
| 构造 `CCombat` | `0x2303D9C` 将传入目标 `CProvince*` 写到 Combat `+0x6B8`；`0x2303DEC` 先清零 `+0x6FD/+0x6FE`；`0x2303E70` 从同一 `+0x6B8` 取目标，`0x2303E77` 调 `0xBC24E0`，`0x2303E7C` 把返回的 `AL` 写到 `+0x6FD`。owner 是 `0x2303CF0..0x230402A`。 | `+0x6FD` 是**存储的目标省份谓词结果**，不是从优势残差算出的战术常数。项目既有 precontact 模型把该谓词称为 `province_has_holding`；这条新字节链只证明同一 target 与写回关系。没有穷尽间接写入者，不能保证此字节整个战斗永不改变。 |
| 每次优势缓存生成 | `0x2308D66/0x2308D72` 对两侧调 `0x23CBCE0`，`0x2308D82/0x2308D95` 传当前 `+0x6B8` 目标给两侧 `0x23CC2B0`；之后 `0x2308D9A` 才读 base，`0x2308DAF/0x2308DC6` 才调两侧 total，`0x2308DCE` 写回 `+0x710`。 | 当前暂停时读取的 side 聚合器不能直接当作**下一次刷新后**的求值结果。`+0x710` 是最近一次生成的缓存，不一定对应暂停时 roll/将领。 |
| 选将与将领输入 | `0x2307E2C` 从当前 side 读取 full CharacterID，`0x2307E54` 校验解析对象 `+0x18`；不匹配时 `0x2307E5A` 取全局 fallback 对象。`0x2307E7A` 将该对象传给 `0x2307680`；其 `0x23076B8` 读有符号 `CCharacter+0xD8`，`0x23076BF` 乘 `100000`，随后还有 modifier helper 和 `0x23079FE` 的嵌套聚合调用。 | `+0xD8` 已由[角色技能 ABI](combat-phase-events.md)闭合为**统率 martial 整数点**。暂停帧可以在 generation-valid 的实际选中角色对象上复制该整数；没有可解析角色时不可把 ID `-1` 等同于原版 fallback 对象的统率。统率乘积只是将领分项初值，并非完整 `commander_raw`。 |
| side 分项 | `0x2307EB5` 的主聚合调用使用当前 side modifier 聚合器；helper `0x23074C9` 读取 Combat `+0x6FD`，零值在 `0x23074D1` 跳过条件项。将领内部另有 `0x23079FE` 对同一 helper 的嵌套调用，先并入将领分项。 | 当前 `+0x6FD` 可直接复制为**条件分支叶子**，但完整 `aggregator_raw` 还取决于两侧 modifier set、目标上下文、relation 和调用时刷新后的状态。主聚合与嵌套聚合不得重复相加。 |

## 最小只读暂停帧合同

在现有受管暂停静止点、generation-valid CombatID 和同一 snapshot revision 下，可新增**诊断性**叶子块。读取前后必须复核 Combat full ID、目标 Province 身份、日期/phase/day、两侧 side→Combat 回指、选中将领 full ID 和角色 `+0x18` generation；任一漂移整块 unavailable。只复制当前 `Combat+0x6B8` 所指 Province 身份、`Combat+0x6FD` 原字节、每侧选中将领 ID 及可解析角色的有符号 `+0xD8`，并与同帧已有的 `base +0x6C8`、`cached +0x710`、两侧 roll 绑定。不得在暂停查询中重调 `0x2307680`、`0x2307230`、`0x23CBCE0`、`0x23CC2B0` 或 `0xBC24E0`。`+0x6FD` 应同时保留原字节与 `==0` 分支布尔值；不能假定所有非零值只可能为 `1`。

该块最多可声称 `current_pause_stored_leaves_observed`。它**不**足以把现有 `active_combat_resume_inputs_v1` 的 `next_day_non_roll_advantage_sources` 从 missing 改为 ready：将领的完整 modifier 与 side 聚合值须在下一次原版刷新及 helper 调用边界动态观测或建立更深的逐输入求值镜像；选将、技能、战斗事件、增援与目标上下文可在中间改变。若选择进一步暴露 modifier 容器，需逐项定义 source identity、数量、顺序、scale、有效期及相同 revision 的原调用等式，而不能仅传指针或把本次 `commander_raw/aggregator_raw` 复制成未来日常数。

下一次实机对拍应在同一 CombatID 的暂停帧复制上述叶子，再在 `0x2308D50` 原调用入口及两次 helper 调用时复制相同身份/叶子，核对构造存储字节、刷新前后、fallback 是否出现、角色统率与 `commander_raw` 初始项；另覆盖事件和增援日。原调用观测器的最终返回只能作为**该次已发生求值**的证据，不能替代未来日输入。
