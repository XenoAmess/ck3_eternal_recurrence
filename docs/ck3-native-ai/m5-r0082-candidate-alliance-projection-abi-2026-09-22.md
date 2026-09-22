# M5 R0082：候选婚配的原生潜在联盟投影（私有 ABI）

状态：`static-ready private core`；未接 application-main、未注册查询或 MCP、未做 paused 实机验证，绝非 M5 联合策略或婚姻结果 GREEN。冻结 CK3 1.19.0.6，`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；源码基线 `master@0ec9b2271c2cdf88bd250b80be6ed518effb0bcc`。此前 R0082 同一帧有玩家 29829、首继承人 38822、657 个不同 final-legal 家庭候选，列表前五条的 CharacterID 为 `16778038, 16778252, 16778632, 16778730, 16778737`；这些 ID 只用于重放定位，不是策略写死的目标或原生排名。

## Exact-build 调用链

原版 `CMarriageInfo` 的 UI producer `0x126D4E0` 在 `0x126D5E4` 调 `0x22846B0(finalized_context, native_pair_vector)`；另一个 AI preview 在 `0x1273366` 调同一 helper。更重要的是，实际婚姻联盟 effect `0x2283470` 在 `0x2283508` **也先调用同一 helper**，再遍历候选 pair，用 `0x2661E00` 检查既有联盟和双方 `CCharacter+0x1B8` realm data，满足时才进入 create-alliance effect。`0x22846B0` 从 context 的 `+0x2D8/+0x2DC/+0x2E0/+0x2E4` 解析四角色完整 ID，再调用 `0x29615E0`；后者最多在三个静态 append site `0x296162A/0x296166A/0x29616AA` 写入 `0x20` 字节的 pair row。row 前两个指针是潜在联盟双方，后两个是实际婚配双方。其原生 inline owner vtable `0x413C270` 的初始化容量为 3，故私有 adapter 可用 `0x18` header + `0x68` inline owner 保持本次只读调用的原生容器 ABI。

`0x2282E99` 把固定 option ID slot `0x57EB680` 交给 `0x2C40770`，是该 context 的 `matrilineal` 选项；`0x57EB964` 则是 grand wedding，现有 outcome classifier 已持有。这里输出的只是 **选项是否被选中**，不是对同姓继承、子女王朝或联盟维持期限的臆测。若男女角色相同，原生婚姻执行分支的有效 lineality 还依角色本身，不能把 option bit 当最终结果。

源码与调用边由新 `research/fixtures/marriage_candidate_alliance_projection_v1_source_contract.json` 及 `verify_marriage_candidate_alliance_projection_v1.py` 以完整 EXE SHA、函数 span hash、direct call 和 option-slot 相对寻址固定。新 `marriage_candidate_alliance_projection_v1` adapter 只接受**已构造并 finalized、已通过该候选原生最终合法性**的 context；读出的每个 pair 用四角色完整 ID、当前 `is_allied_to`、双方 realm data 判定 `would_attempt_if_accepted`。空 pair list 是合法观测；ABI/身份/option 不可读时返回 typed failure，不写假零或不完整 row。它不调用婚姻提交、联盟创建、UI 构造或任何 MCP 注册。

## 串行接线与剩余门

1. 在共享 CMake 中以默认 OFF 的私有 option 编入该 `.cpp` 与 focused fixture test；不触碰公开能力广告。仅在现有 paused application-main R0082 后续查询路径中接入：公共 campaign-root 再绑定玩家/首继承人、同帧原生合法候选；用户显式给出至少五个**不同、当前 final-legal** 的 candidate ID，逐一构造并 finalize 同一五角色 context，在销毁前调用本 adapter。查询返回每行 actor/heir/candidate、native revision、双方潜在联盟 ID、option selected、existing alliance、`would_attempt_if_accepted` 或 typed unavailable；不伪造 `native_rank`。
2. 同一查询复用现有 `marriage_native_outcome_classifier_v1` 给出婚姻/订婚预计类型，并在 application-main 前后核对同一 paused revision/date。若这一路缺失，不把它与联盟投影混称 M5 逐行价值完成。
3. 使用新的冻结 DLL 在真实 paused R0082 兼容存档读至少五个不同 final-legal 候选，保留每行和校验信息。此 read-only 门通过后才可讨论正式联合选择；联盟 pair 只是 effect 的**候选输入**，最终仍须 typed 提交、后续新 paused frame 的双向关系/联盟实际读回、下一 turn 消费和必要 cold restore。接收者拒绝、事件/战争变化或后续 break-alliance 都可能使投影与实际不同；不能把本预览当作承诺或结果。

本包 focused MSVC x64 Debug `/W4 /WX` 和 Release `/W4 /WX` 各 1/1 CTest GREEN，exact-build Python normal 与 `-O` source verifier GREEN。无 CK3 实机、无正式消费。M5 仍 `not_started`，G2 分母和状态不变。
