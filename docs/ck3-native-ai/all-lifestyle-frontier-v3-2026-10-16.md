# CK3 1.20.0.4 全生活方式花点前沿 v3

2026-10-16；本节是离线源码、实际 MSVC 对象与合成原生数据库夹具证据。Native21 尚未由本子任务加载进游戏，不能据此宣称全类别实机验收或 30 年目标完成。

旧实现不是原版没有可用技能，而是窗口关闭后生产查询只覆盖六项，Native20 先扩为管理 27 项；前置条件和回执仍从当前焦点取点数，因而会漏掉其他生活方式已经积累的点数。此次同时扩目录和真正的目标类别进度来源，保留原版 CanPick、玩家、精确版本、主线程、暂停、日期、revision、episode 以及提交后独立回读守卫。

## 当前原版来源与旧镜像更正

权威目录来自实际游戏启动根 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game`，不是仓库内 `Crusader Kings III` 研究镜像。唯一作者源已落 `ck3_autonomous_player/native_bridge/data/vanilla_lifestyle_catalog_12004_v3.json`；原件 SHA-256 为 `bc74e9eee7e4902771c8018b2e69cded51b781e77323f0d3b936e82bbaf6a117`。

实际有 diplomacy、intrigue、learning、martial、stewardship、wanderer 六类，每类三树、每树九项，共 18 树 162 项；另有六个 lifestyle 定义与 23 个 focus。目录逐项保留完整文件 SHA、block SHA、行范围、父节点、`can_be_picked`、原版 AI 权重及 lifestyle/focus 条件来源。wanderer 定义的 `is_valid` 包含 `has_dlc_feature = wandering_nobles`；把 ID 纳入目录不会绕过原版 DLC、政府、父节点或其他条件。

Native20 的三份管理原件曾取自研究镜像；它们与当前 Steam 文件 SHA 不同。旧资料作为当时来源保留，不能继续标成当前实际 Steam 文件身份；旧 Native20 原版合法性查询和实际加点回执本身不因该来源说明更正而失效。

`tools/gen_lifestyle_all_catalogue_v3.py` 从同一 JSON 生成 Native 映射，可用 `--check` 校验，并用 `--python-output` 逐字节投影 SDK 运行目录。目录只证明作者存在的 key，不证明当前玩家合法可学。

## 生产查询、动作与回执

- `.4` 原生查询先对六类读取真实 XP、等级内 XP、每级 XP、剩余点数和已用点数，双读并检查同帧。该入口复用实际 perk 数据库中的 lifestyle 指针与原版 getter，不调用 CanPick。零点类跳过全部最终合法性调用，未知进度保持 unavailable，不填零。
- 仅有点数的类别进入前沿扫描；当前焦点只有在该类点数大于零时优先，其余按确定顺序。管理沿已验的原四项和后续 domain→wealth→duty 顺序；其他类别按原版作者顺序。这是最小确定策略，并未声称复刻原版 AI 权重选择。
- 对选中的每项调用既有原版最终 CanPick 两次并核对同帧，只返回首个原生合法、未拥有且有可用点数的 `policy_target`。完整进度且无合法项发布 available + 空集合；任何必要来源未知且没有独立合法项则发布 unavailable，不能计作正常无动作。
- `all_lifestyle_progress_v3` 是新增 sibling，绑定 snapshot、native revision、日期、玩家和 episode，固定六个 available/unavailable 行；未知行数值为 null。partial 但有独立已验证合法项可以继续发布该合法项。
- 提交重新检查请求的精确 target，不用新扫描结果代替请求。前置条件在既有 64 行容量的 action observation 中放入目标类别真实点数，同时保留当前焦点身份。回执再次读取该精确 target 的原生类别进度和完整 owned/current-focus 状态，交既有独立回执验证器；不会拿当前焦点点数代替旧类别点数。
- 新能力 `game.state.private-lifestyle-all-frontier-v3` 只在实际 `.4` formal 路由启用时发布；它表示实现覆盖，不代表当前六行一定 complete。普通 perk 没有额外封建制门禁，政府与 DLC 条件仍交原版 CanPick。首次 focus 的既有策略和资格不扩张。

公共 GameAdapter 虚表、Snapshot DTO、既有请求与五个 DLL exports 均未改变。私有 `.4` context 追加六类进度，所有实际头依赖消费者共 20 TU 完整重编，不能把旧对象与新 context 布局混用。

## 构建、夹具与边界

外置包 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p26-all-lifestyle-frontier01`，实际 Native21 `native.dll` SHA-256：`c0208ee8d7be6d974b536ed7c88547f01a24d06838556d9b59d0738cf633de0e`，18,198,016 字节。

`SOURCE-FREEZE.json`、`COMPILE-PLAN.json`、逐 TU `COMPILE-RESULT.json`、`LINK-PLAN.json` 与 `DELIVERY.json` 绑定实际来源和所有保留 link inputs。20 TU 的 MSVC 编译全部通过，保持全境镜头、knownClose、CB policy-file、private Army、日期即时发布、每日 sentinel 等既有功能。Native20 原产物 SHA 保持不变。

25 组焦点检查使用同一完整生产对象和 link inputs，只增加 fixture 对象与测试导出：覆盖 162 ID 唯一性，六类末端技能，零点零 CanPick，当前焦点零点但旧类别有点，当前正点优先，原版 DLC 拒绝，unknown/partial，精确 target 重查和禁止替换，错误线程、任意 key、日期漂移、跨焦点前置/回执点数和实际 `AttachPlayerLifestyleFinalCandidatesV1` ready 位。

`PORTABLE-FIXTURE-FINAL.json` 为 25 GREEN；可移植测试把大型 DTO/数据库放到 heap，适配既有 EXE 默认栈。真实 C++ serializer 的 `ACTUAL-SERIALIZER-QUERY-FINAL.json` SHA `64e09f8a494e86296daeeb0f8b43ac43442e58046a01030f5f2c63af7e156cc7` 已由 Python 端消费。原早期 serializer 夹具手动漏设 ready 位，已保留并明确更正；生产实际 Attach 本来会设 true，未为该夹具错误放宽提交守卫。其他编译与夹具 RED 原记录另存，不冒充生产故障已实机修复。

原生准备任务没有启动项目新 EXE，没有操作 Game、SDK、桌面、OBS 或工作树索引。存储使用 N42 既有 64 GiB 预留内 1 GiB 子预算，父准入来自 `native18-cold-generation01/STORAGE-ADMISSION.json`；构建默认 14 天、关键证据 30 天复核。实机仍待 Root 在保存边界统一加载匹配 Native/SDK，核对新 hello、六类来源、跨焦点加点后的 owned 与点数以及旧 cooldown 一次迁移。热换沿已有审计结论不采用，原生准备任务未调用 Stop/Start、注入或伪造持续推进。

## 公共 SDK 整合

公共 Service 仅移植对应调用、六域 cadence 中的 lifestyle 分支以及原生 v3 能力路由，保留同期其他普通规划能力。新能力只把该域旧目录的负冷却重资格一次；partial、unknown 或失败查询不计入连续无动作，完整原生观察且没有合法目标才形成明确 no-legal 结果。

同一目录生成 Native header 与 Python 资源，`--check --python-output` 已逐字节通过；SDK wheel 的 package-data 显式包含必需 JSON。公共聚焦共 **103 tests、19 subtests 通过**：其中生活方式 92/14，海军同场热连接与原跨日资格 11/5。真实 C++ serializer 输出经过公共 transport→policy→typed submit 选择链，保持 `legal_perk_candidates_ready` 守卫；测试数据库与点数仍为合成，不能当游戏中的实际花点。

公共新夹具完整函数与公共 headers 已真实 MSVC 编译／链接并运行 **25 组通过**，回执位于外置包：`PUBLIC-TRANSPLANT-VALIDATION.json` SHA-256 `d053cb7163cd972062bf1e5c0884ec2f05653a8a8f54fdfbade8e2a7e7656633`；`PUBLIC-FIXTURE-FINAL.json` SHA-256 `ad0a55490115f0a1fb4ffc0845521df9954c9cc054da1992654ef9e782d63fef`。测试只增加 DLL 导出包装，没有新 EXE；公共既有 main/CMake 全目标尚未运行。Native21 原 DLL 未改，当前 Game 的 Native20 两点管理实证仍是前一版本的具名结果，不能外推为六类实机全验。

## 后续实际部署（2026-10-16 UTC）

上述未加载描述是源码交付时的状态。Root 后续已将同 SHA Native21 与 SDK27
加载到 Game6068／FILETIME134366412679616931，进入原 campaign 并完成
两批普通规划，实际推进5日和17日。[当前交接](../handover/2026-10-17-p27-native21-continuation.md)
绑定真实启动、地图／决策窗、独立 SEM／METRICS 和恢复回执。
这增加实际加载与普通流程证据，没有增加六类逐项花点验收；Native20 的两个管理
具名材料结果继续保留，不能扩称162项或其他五类均已实际验证。
