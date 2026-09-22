# M5 首继承人五候选联盟投影：私有接线

状态：`static-ready private query`，未在真实 paused CK3 帧运行；不代表联盟会建立、M5 联合选择完成或 G2 状态改变。冻结 CK3 1.19.0.6，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。来源与界限见 [候选联盟投影 ABI](m5-r0082-candidate-alliance-projection-abi-2026-09-22.md)、[R0082 五候选缺口](m5-r0082-joint-selector-field-gap-2026-09-22.md) 和 [原生婚姻树](marriage-and-alliance.md)。

默认关闭的 `XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1` 依赖原有私有首继承人合法性查询选项，但不依赖私有婚姻动作选项。只有原有公共 campaign-root 在同一 native revision 指明首继承人、接着私有 `query-observed-first-heir-marriage-legality-v1` 返回合法候选行，才能调用新 `query-first-heir-candidate-alliance-projection-v1-private`。调用者提供 `expected_revision`、`legality_query_sequence` 和动态发现的 `candidate_id_0` 至 `candidate_id_4`；五个完整 CharacterID 必须互异且各自唯一存在于当前 final-legal 行。R0082 的五个示例 ID 仅供证据定位，不写入查询或策略。

该查询在已验证暂停的 application-main mailbox 依次重新构造每一候选五角色 context，执行原生 redirect、refresh、finalize、Can Send、接收者最终答复，核对身份与先前合法行后，在 context 销毁前调用精确构建的原生联盟 pair helper。每行返回 matrilineal option 是否选中，以及最多三个潜在 pair 的完整 CharacterID、当前是否已结盟、双方是否有 realm data、若被接受是否进入联盟创建尝试；失败返回 typed unavailable，不把未知写成 `false`。查询前后核对同一 paused snapshot/date/revision。输出没有原生排名、效用、婚配成功承诺或联盟结果，且不提交任何动作。

Python 私有入口为 `NativeDriver.query_first_heir_candidate_alliance_projection_private_v1(legality=..., candidate_character_ids=[...])`。它不进入正式 step registry、公共 capability 广告或 MCP；与既有下游/open_kaishek 的接口影响为**无公开协议变化**。私有实验 DLL 必须显式开启上述 CMake option。下一门是同一冻结 DLL 在真实 paused 存档中读五条不同 final-legal 行；之后还需婚姻/订婚结果类型、候选收益/长期承诺、联合机会成本、正式动作、独立后置和下一轮消费，不能因本页的静态测试通过宣称 M5 GREEN。
