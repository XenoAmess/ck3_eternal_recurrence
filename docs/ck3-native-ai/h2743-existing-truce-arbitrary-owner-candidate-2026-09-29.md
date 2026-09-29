# H2743：任意 owner 的投降前既有休战槽只读候选

状态：**源码及原生 ABI 静态验收；候选默认关闭；尚未构建 DLL 或受管实机双读。** 本页只处理 H2743 守方投降**之前已经存在**的 Landolf `30097`→Robert `29829` 有向关系槽。新命令 `query-h2743-preaction-existing-truce-v1` 不求值休战天数、不创建关系、不执行投降、不推进日期，也不返回本次受降后尚未产生的 expiry。正式退出比较仍 `material_complete=false`、`recommended_outcome=null`、`action_literal=null`。

## 精确输入与身份门

候选仅在 CMake `XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=ON` 时编入；默认 `OFF`，与旧 G2 current-player reader 隔离。[核心读口](../../ck3_autonomous_player/native_bridge/src/h2743_preaction_existing_truce_v1.cpp)检查暂停/地图就绪、玩家 Robert、raw date `53217264`、活动 WarID `16777231`、主攻 Landolf、守方当前玩家为主战领袖、目标 Title `[2128]`。原生适配器以完整 WarID/generation 解析在役 War，再读主攻守、active CB index `17` / key `individual_county_de_jure_cb`、目标列表和 War/CB 对象指针；前后两次对象身份必须一致。双方人物以完整 CharacterID 解析、检查未死亡，并在两次关系读后重新解析为同一指针。

命令请求必须同时携带 `expected_revision`、`expected_date_raw=53217264`、`expected_snapshot_id=native:3`、`expected_episode_id=native-29829-2bc2d599f7f9`、checkpoint SHA `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9` 和 EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。桥接核对请求和已发布 revision，并在核心读口前后另读完整 Snapshot；不匹配拒绝，内部读口的漂移返回 typed `unavailable`。**episode、snapshot ID、checkpoint SHA 和 EXE SHA 在此是请求 claim；原生 Snapshot/War 不包含 driver episode 或存档文件字节。** 输出固定 `episode_authenticated_here=false`、`checkpoint_bytes_authenticated_here=false`；外部 runner 仍必须核存档、driver、sidecar、DLL/EXE bytes、episode 与同帧会话。不能因原生命令 ACK 自称 source bytes 已认证。

## 只读值与失败语义

精确 EXE 的 `HasTruce` RVA `0x26631E0`、`GetTruceEndDate` RVA `0x2663250` 都调用只读 relation lookup `0x2610840`。核心以 owner Landolf、toward Robert 的指针按这个方向各读两次 `HasTruce`；仅 `true` 时各读两次 expiry。前后完整 Snapshot、War/CB 身份、人物指针、关系存在值和 expiry 必须一致，已有 expiry 必须晚于当前 raw date。真且稳定发布 `status=existing_truce` 与 `preaction_existing_expiry_date_raw`；两次均无关系发布 `status=no_existing_truce` 且 expiry `null`；任一读取/身份/日期/代次/数值漂移只发布 `status=unavailable`、具体 reason 与 expiry `null`。外层 `backend_id=native-headless` 只在独立受管 live attempt 成功后才是实测证据；目前没有此类结果。

`CAddTruce` 的 get-or-create `0x26108F0`、duration evaluator `0x3373000` 不在候选调用链。序列化字段 `post_surrender_actual_expiry_date_raw`、`script_candidate_days`、`recommended_outcome`、`action_literal` 恒为 `null`，`effect_projection_complete=false`、`material_complete=false`。即使将来读到一个真实旧槽，也不能推断本次投降会覆盖、合并或保留它；FP2 真实付款、CB title/封臣变化、loaded effect tree、延迟效果仍缺独立证明。

## 静态证据与下次构建门

[来源/ABI 验证器](../../ck3_autonomous_player/native_bridge/research/verify_h2743_existing_truce_source_abi_v1.py)逐字节固定本候选 C++/桥接/CMake/协议/旧 reader 的 18 份源码；另核开启候选时 capability 条目与 `kCapabilityCount` 同时增加；调用已有精确 EXE 提取器核 PE、八个原生区间和只读/可变调用边，再核六份原版 CB/on_action/FP2/EP3/休战脚本及两条最低必要根。[冻结产物](../../ck3_autonomous_player/native_bridge/research/h2743_existing_truce_source_abi_v1.json) SHA-256 `536D4A6E96A8D73537278DB452713C00339D3A8528B960E419D6A84C5B7933E9`，明确 `static_source_abi_verified_build_pending`、`loaded_dll_sha256=null`、`live_observed=false`；改变任何 source/ABI/script bytes 或把动作/未来值填实都会使 `--check` RED。它不证明新 C++ 已编译，也不认证运行进程的内存映像。

已提交的[原生单测源码](../../ck3_autonomous_player/native_bridge/src/h2743_preaction_existing_truce_v1_test.cpp)覆盖正确方向、已有/无旧槽、两次 has/expiry/War/Snapshot 漂移、错日期/Title/重复 WarID 和 exact-build 门；需在另排的受管构建窗口编译执行，当前**未运行**。Python [静态负例](../../ck3_autonomous_player/tests/unit/test_h2743_existing_truce_source_abi_v1.py)普通及 `-O` 各 5/5 通过；精确 EXE `--check` GREEN，错 EXE exit 2。上述验证只发生于磁盘，不是 live 旧槽读数。

后续才可构建独立候选 DLL，记录源码 commit、编译选项、新 DLL SHA、原版脚本/EXE/source manifest SHA，加入 runner 的显式 candidate 和 no-launch gate。屏幕释放后取得新鲜 Steam 离线证据、任务总线独占、独立 append-only attempt，先核 source/placed save/driver/sidecar/injector/DLL，再仅在同一暂停帧执行双读；任何 RED 保留回执并停下。此项读口不会使守方投降条款完整，不能解除正式第 36 turn 或终战动作守卫。
