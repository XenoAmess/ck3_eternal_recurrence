# M5 五候选联盟投影：独立只读候选准备

状态：**no-launch READY；尚无 paused 实机读回**。本包复用
[exact-build 联盟投影树与私有查询合同](m5-first-heir-alliance-private-query-2026-09-22.md)，
不修改公共 MCP/hello、正式策略或 G2-M5 状态。

| 身份 | 冻结值与来源 |
| --- | --- |
| CK3 | `1.19.0.6-steam23530548`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，本机重新核对 |
| 原始 save | `dev3b_r639.ck3`；SHA-256 `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`，来自 R736/R0082 的未改封建 fixture |
| 上一只读结果 | R0082 首继承人 `38822`、657 个最终合法且无原生 rank 的候选；typed 结果 SHA-256 `D7C3FE9BC820983BE6E747A2415DCDDC69F4FD5A10E88D65DC4543759A8B698A` |
| 新源码 | `71d428b1a9b2d9834256e4d022dab83b83fbda5d` 的独立 detached Z 盘 source worktree；仅作为待实机冻结运行依赖 |
| 候选编译 | 独立 Z 盘目录；`XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1=ON` 与 `XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=ON`；Release DLL SHA-256 `F9AECCDE8DDEDE06AF651835AEA1471AA018F614F445CCC46462D88FEAC3E5DB`，注入器 SHA-256 `0F2C4F395E11F2E32B2AD478F51A9926E9F1253ED6AB417CF030A6E09788C6F5`，CMake cache SHA-256 `2C033B116A9BACF13D09032ABC2DECE03660A35AD1CB6984195DAFD48C54C06E` |
| prepared profile | 官方 `prepare_profile(xar_enabled='xar_on')`；环境 SHA-256 `EF86E3B78E21F4ED32C7E586F2C91B10734D648269CBE2DDB0562BBE13D04ED1`；单 mod `mod/xar_autoplayer.mod`、`disabled_dlcs=[]`；新 driver 尚不存在 |

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

候选资产位于
`Z:\ck3_mod_rewrite_process_assets\g2-m5-alliance-readback-71d428b-20260922\`。
已冻结 `no-launch-manifest.json`（SHA-256
`DE71CECD5CD0C6EC2004B47AFE6BE01505E81C347DD1492ACB622B14AD137A32`）
和 runner（SHA-256 `E809588BBC1BB42B9A0A90124401DEB48A445B344CCB9B994DB4E60254BBD3CA`）。
manifest 的 `status` 记录创建时仍待 preflight；当前结果以以下报告为准。
官方 profile 生成后复制**只读**原始 save，
并运行 runner 的 `--preflight-only`：返回 `READY_NO_LAUNCH`、受管 CK3
库存 `0`、`ck3_launched=false`。持久 `no-launch-report.json` SHA-256
`F3A3E62693292AC916CD2D36331B1369FDA986EB0FCDDD8D26AE7998FFE1279A`。
这只关闭启动前的静态/环境准备，不是查询或动作证据；WAR 下一候选优先占用
唯一 CK3 实例。

之后唯一 CK3 owner 须重新核进程与版本、由持久分配器分配 **新轮次**，
再用此候选根的 `run_alliance_readback.py --candidate-dir <上述目录>
--live --round-ledger <新轮次分配文件> --evidence <全新证据目录>` 进入有界
只读查询。不得把本候选 `no-launch READY` 直接当成启动授权。投影结果仅说明接受后原生代码会
考虑哪些联盟 pair 及其当前资格；婚姻/订婚结果、真正的联盟、长期承诺
价格、同帧战争预算和共同效用仍未知，不能因五行 readback 将 M5 记为完成。
