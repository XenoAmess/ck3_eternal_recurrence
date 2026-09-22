# M5 五候选联盟投影：独立只读候选准备

状态：**准备中，尚无 no-launch GREEN 或 paused 实机读回**。本包复用
[exact-build 联盟投影树与私有查询合同](m5-first-heir-alliance-private-query-2026-09-22.md)，
不修改公共 MCP/hello、正式策略或 G2-M5 状态。

| 身份 | 冻结值与来源 |
| --- | --- |
| CK3 | `1.19.0.6-steam23530548`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，本机重新核对 |
| 原始 save | `dev3b_r639.ck3`；SHA-256 `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`，来自 R736/R0082 的未改封建 fixture |
| 上一只读结果 | R0082 首继承人 `38822`、657 个最终合法且无原生 rank 的候选；typed 结果 SHA-256 `D7C3FE9BC820983BE6E747A2415DCDDC69F4FD5A10E88D65DC4543759A8B698A` |
| 新源码 | `71d428b1a9b2d9834256e4d022dab83b83fbda5d` 的独立 detached Z 盘 source worktree；仅作为待实机冻结运行依赖 |
| 候选编译 | 独立 Z 盘目录；`XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1=ON` 与 `XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=ON` 已配置。WAR 优先窗口开始时主动中断单并发 Release 编译，尚无可用 DLL 哈希 |

R0082 运行后的 `driver-state.json` 含死 PID 与一次只读查询，原 manifest
明确不能把它作为冷恢复种子。因此本包从上述**原始 save** 创建全新
`prepare_profile` 状态；没有合法的旧 driver pending action 可重绑，本候选
属于新的 read-only fixture 启动，**不是**从 R0082 继续同一 episode 或
百年主跑 cold restore。原场景使用 `xar_on`；它不会冒充 WAR 的
`ordinary_campaign_succession/xar_off` 配对。

检查过的入口 `run_m5_alliance_readback.py` 是此冻结候选的受控 runner：
`--preflight-only` 核源码、profile、双开关 CMake cache、EXE/save/DLL/injector
哈希以及单实例库存；正式 `--live` 另需唯一 owner 和持久分配器分配的轮次，
然后对同一暂停帧依次查询当前首继承人合法性和五个**动态发现**候选的
私有联盟投影，保存两份原始结果，保持动作数和日期推进为零，并回收进程。
`ids[:5]` 只是确定性的只读抽样，不是收益排序或婚配建议。

后续步骤：待 CK3 唯一实例窗口释放后，增量完成 DLL/注入器构建并记录完整
SHA；在无 CK3 时由官方 `prepare_profile` 建立新 state，复制**只读**原始
save，生成不可变候选清单，运行 `--preflight-only`。以上条件齐备才由
当前唯一 owner 分配新轮次、排队实机。投影结果仅说明接受后原生代码会
考虑哪些联盟 pair 及其当前资格；婚姻/订婚结果、真正的联盟、长期承诺
价格、同帧战争预算和共同效用仍未知，不能因五行 readback 将 M5 记为完成。
