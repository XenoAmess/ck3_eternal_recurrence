# M4：军费查询贷款 collector 的单 object 资格与采用范围

`machine_id: xenoamess-full-tower-eb9d2c1186`；机器身份由本活动再次运行 `py -B tools/ck3_live_run_id.py machine` 读回。实际编译观察时间为 `2026-10-19T05:57:41.090889Z` 至 `05:57:45.666447Z`，来源是获准外置 child 的 `COMPILE01.json`；完整 producer、命令、依赖和采用前源码 SHA 见[追加记录](evidence/holy-order-loan-war-cash-collector-object-2026-10-19.json)。旧 source-only 合同、getter object 与九例合成资格均未改写。

本次只编译 `research/holy_order_loan_war_cash_attach_12004.cpp`，首次返回 0，失败 attempt 为 0。真实 cl `/Bv` 为 19.51.36257.0，命令使用 `/c /std:c++20 /permissive- /Zc:__cplusplus /EHsc /W4 /WX /utf-8 /DNOMINMAX /MD /O2`，单 worker 为 BELOW_NORMAL。实际读入 586 份 header，源文件前后 SHA 相同。object 为 86,049 B，SHA `9257c595898ad057284b32f8e52c4a13d4120e4aa33cda1f9cd4a6cfcaebff22`。没有链接、执行 DLL/EXE、重跑 getter fixture，也没有接触 Game、RPC、Driver、SAVE 或当前 Native26/C5。

该结果证明这个 collector 与实际 headers 可被同一 producer 编译。它不授予当前原生 ABI、真实本金数值、完整贷款条款、债务、到账或动作资格。所有尚未到账的资金信用仍为 0。

## 五处共享源码的后继最小范围

以下路径均相对 `ck3_autonomous_player/`，本轮只读，尚未修改。旧 SHA 完整保存在追加 JSON；列在这里便于独占时核对。

| 叶与旧 SHA | 授权后只改的范围 |
| --- | --- |
| `native_bridge/include/xar_bridge/ck3_12003_war_cash_current_reader.hpp` · `655a22a9c7707cb50634abf9a4bb4c9b9ddd17ba502918c81bfa3ef71e316a69` | `ActorResources` 末尾新增一个 optional collector observation 和所需 include；原钱包、收入、军费字段及 readiness 不变。 |
| `native_bridge/src/ck3_12003_war_cash_current_serializer.cpp` · `280a1bdf15b096a115f758d1f50b74b5dd46113fa972dbcc75aea99476c8b1d3` | `SerializeCurrentResourcesV1` 增加可选 `.4` loan 子叶及局部 serializer；只在 outer actor/native revision/date 与 collector owner/frame 一致时输出其独立来源。缺少子叶时保持既有输出。 |
| `native_bridge/src/bridge.cpp` · `68ad29060e19a17727ab7b961a4efbe7f21f5f036ac252a9e6cd40b98ac833b1` | include 与 `ExecuteWarCashCurrentResources12004` 中现有 `ReadActor` 后、`query.completed`/`FinishQueryMailbox` 前的一次 collector 调用。复用已经进入的 envelope、snapshot 和 pump stamp；不新增 query/step/权限，不变更原提交、等待、回收与后验 snapshot 比较。 |
| `src/xar_autoplayer/bridge/war_cash_private_transport_v1.py` · `e33f43c54fe4fa0960383065931a1b2179b8b40b706393f628a94dbb6b6d4249` | 在现有 normalizer 中独立验证可选 loan 子叶；错误仅将该子叶标为不可用，不能使有效的原 cash DTO 整体不可用。原 query 函数和公共权限沿用。 |
| `src/xar_autoplayer/war_mercenary_consumer_v1.py` · `bfbf3770e346502b46cbedaa528b3e5cf87ea5c61c52329eb89faebfc4a9007e` | 现有融资观察增加明确的 optional cash DTO/full planning source frame 输入；只补 loan 观察，不改变雇佣/建设预算、战争动作、采购 epoch 或结果未知不重放规则。 |

资格 gates、十槽原生数值费用和本金 quote 分别保留 ready/unknown。normalizer 只能将决议费用子项交给既有 `project_holy_order_loan_decision_observation_v1`，其“尚未具备完整条款”约束不放宽；本金另以实际 getter 的已清理 owner 和同帧来源为依据。负数/零与 unavailable 分开，Q100000 不转为浮点金币。任何子项失败均不改变当前钱包，也不能改变原 cash 总体 status。`existing_debt_principal_raw` 仍未知，到账 false，funding credit 为 0。

## 普通 planner 的真实交接缺口

当前 `bridge/service.py:2295` 只传 snapshot/history/capabilities 给战争 consumer，没有 cash DTO/full planning source frame。月度采集器的 cash packets/source_frames 是局部数据，不能当作已经存在的普通 planner 缓存。已有 transport 的 actor/native revision/date 绑定也不包含完整 episode、连接、PID 等身份，不能单独替代完整 planning frame。

因此上述五叶可以先完成 Native DTO、normalizer 和 consumer 纯输入口，但普通 planner 真正使用它还需要 Root 协调 Service 的窄交接，且必须来自已实际取得、完整同帧的查询结果；本研究不虚构历史包、不新增隐式 RPC，也不使当前 C5 等待。Service 当前只读 SHA 为 `9a22d369ffc245c7a26439a55819461a5c296a4fce015d1cf0ba85f86055e81e`。既有融资缺口对象位于 `wartime_construction_cash_v1.py:58`；可由 consumer 合并独立 loan 观察，无须改写原观察器的 unknown 基线。本轮不修改这两处。

## CMake 最小输入与编译闭包

后继采用只需在现有 `xar_ck3_12002_runtime` 增加三个明确输入：

```cmake
target_sources(xar_ck3_12002_runtime PRIVATE
  research/holy_order_loan_decision_costs_12004.cpp
  research/holy_order_loan_principal_12004.cpp
  research/holy_order_loan_war_cash_attach_12004.cpp)
target_include_directories(xar_ck3_12002_runtime PUBLIC research)
```

当前 runtime 的 `research` 是 PRIVATE；若 PUBLIC `ActorResources` 嵌入完整 collector type，就必须让该 include 需求传给下游。bridge 已有 PRIVATE research。已有 adopted-domains/prisoner 输入提供绑定实现，不增加 target、查询路由、测试平台、Native archive 副本或 EXE。禁止 glob 所有 research cpp，否则会吸入 fake fixture。

这三个输入不等于只重编三个 object：`ActorResources` 布局变化要求所有实际使用该定义的 TU/archive 按同一 header 一致编译，不能把新 bridge 接到旧 Native26 runtime archive。下一次确有维护需要时，先以 Ninja 实际 header 依赖计算闭包和输出预算，再在独立候选构建中采用；本轮不运行 configure/build。采用前 CMake SHA：`CMakeLists.txt` 为 `efa4008fe05dc92fc0eb182531260b63061720cbfe6d23987f914e0e21a65604`，`cmake/adopted_domains_12004.cmake` 为 `8d65631e51ee6d320d639f15f77010447960b7234fa3824a13ff7256fb49c73c`。

## 有界存储与闭场

本活动 exact child 为 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/m4-collector-object01`，计原 other-research 128 MiB，aggregate 硬上限 8 MiB，包含新增 repo 小记录。编译期间每 25 ms 采样 logical high-water 为 164,217 B，仅为采样下界；报告写入后的最终量另见 canonical `CLOSE01.json`，不能将前者称为最终/瞬时或 physical 峰。allocated 未核为 null，不返还父预留或物理信用。全部 producer 关闭，遗留进程 0、未来写入 0；旧 closed child 不重开。源与采用方案保留至原派生复核期限，闭账及精确 logical/self 大小以 canonical manifest 为准。
