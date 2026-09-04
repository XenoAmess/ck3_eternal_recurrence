# Projects/metrics source-capture no-launch freeze (`5c54014`)

状态：**static-ready-live-pending**。本页冻结 production source capture 的
fresh private candidate；本工作包没有启动 CK3、没有执行 gameplay action、没有写
checkpoint/registry，也没有修改共享 runner 或 production 脚本。

## 冻结身份

- canonical source：`5c54014c7317bd2446bd342d7205cf00fe024dc9`；其祖先包含
  production 修复 `953634265ebf298cec3f2cf3065060e577dc8d17`；
- exact CK3：`1.19.0.6`，`ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
- native source：292 files，fingerprint
  `AAE0588178B082B7A10391792BE889C3D5976E51906485B380C22DCBBBC0A388`；
- machine-readable manifest：
  `ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_projects_metrics_source_capture_no_launch_candidate_5c54014_20260904.json`。

fresh MSVC 19.51.36248.0 / Ninja / Release build 显式打开私有
`XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=ON`，但仓库中的
source option 仍为 `OFF`，production advertisement 仍为 false。冻结产物位于
`Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-source-capture-no-launch-5c54014-20260904T080922Z\candidate-build`：

- `xar_ck3_bridge.dll`：2,361,856 bytes，SHA-256
  `61F307CFFB9999B9D740732449FB4A8517B8454EA942E0FFC746054347A08601`；
- `xar_ck3_bridge_injector.exe`：39,936 bytes，SHA-256
  `86F0099C0AAC14066DA391D0FBAC398D08229FC5E7CEF377A958505E155AF5AE`；
- `CMakeCache.txt`：19,702 bytes，SHA-256
  `E379EE5DEBA16E28D91B9B10305756D594E1E890C57ADAB9ADFD1FF73051BC75`。

## Production 与文件边界

离线门禁同时读取 generator 与 generated product：同一 central cycle 中 stage 7
固定为 Credit/Project producer（`zg361_cp_open_portfolio_effect`），stage 8 固定为
Metrics/Delivery consumer（`zg361_p3_open_portfolio_effect`），serial pump 中的顺序
也是 7→8。provider 的 fixed allowlist ID 为
`zg361-cp26-direct-p3m229-lineage-v2`，40 字段由 15 个 direct CP26 字段、1 个 P3
cycle 字段和 24 个 P3 source/result 字段组成。

source capture 只接受 `checkpoint_state=cp26_ready_p3_absent`：真实 CP26 A/B receipt
已闭合、同一 cycle 的 P3 initializer 尚未运行。其余 available 状态仍为
`p3_initialized_source_not_ready`、`p3_source_ready_result_pending` 与
`p3_result_committed`；capture registry 必须是 schema 2。ACK、fixture、console 或
clone 均不能替代这条 provider-observed business state。

Central generator 当前为 10 个按用途拆分的 effect 文件，顶层定义数为
`3 / 2 / 9 / 2 / 6 / 3 / 3 / 1 / 3 / 1`；最大 9，满足目标 1–10，硬上限 20，
`>20` 例外为零。验证器按括号深度统计顶层 definition，避免把 effect body 内没有
缩进的 Clausewitz 行误计为新 effect。

## 离线验证

- fresh native build 完成；Ninja dependency database 对 `ck3_11906.cpp.obj` 与
  `ck3_11906_adapter.cpp.obj` 分别记录 6/22 dependencies，均包含
  `ck3_11906.hpp`；
- focused native CTest：3/3 GREEN（adapter registry、projects/metrics reader、
  projects/metrics mailbox）；
- candidate verifier：normal 5 passed；`-O` 5 passed（仅 pytest 对 `-O` 的既知
  warning）；
- central generator `--check` GREEN；central tests normal 38/38、`-O` 38/38；
- production choreography 6/6、source checkpoint 7/7 + 3 subtests、action cell
  6/6、Python provider/contract 13/13；四组 `-O` 结果相同；
- source-capture preflight 12/12 checks GREEN；action preflight 14/14 checks GREEN；
- frozen-candidate preflight 21/21 checks，结果 `READY_TO_LIVE`。

最短复核命令：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools/verify_zg361_projects_metrics_no_launch_candidate.py --manifest ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_projects_metrics_source_capture_no_launch_candidate_5c54014_20260904.json --check
```

## 精确 CK3 命令（本工作包未执行）

以下命令已经绑定唯一 pipe、candidate pair、state root、exact game directory 与
`--cold-start-checkpoint`。它只在该 state profile 已通过独立步骤 materialize 为
product-only，并包含 hash-bound `xar_checkpoint.ck3` 后才可执行；本次没有制造该
save，也没有建立 live-attempt 目录。

```powershell
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'Z:\ck3_mod_rewrite\_root-promo-split-20260902\ck3_autonomous_player\agent.py' --state-dir 'Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-source-capture-no-launch-5c54014-20260904T080922Z\live-attempt\state' --game-dir 'Z:\SteamLibrary\steamapps\common\Crusader Kings III' --bridge-mode native-headless --bridge-pipe '\\.\pipe\xar_ck3_zg361_projects_metrics_5c54014_080922' --bridge-dll 'Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-source-capture-no-launch-5c54014-20260904T080922Z\candidate-build\xar_ck3_bridge.dll' --bridge-injector 'Z:\ck3_mod_rewrite_process_assets\zg361\projects-metrics-source-capture-no-launch-5c54014-20260904T080922Z\candidate-build\xar_ck3_bridge_injector.exe' native-session --timeout 21600 --cold-start-checkpoint
```

manifest 另行冻结 route A 的 `observe-ui` 与 owner `32904` 的
`capture-checkpoint` 精确命令；只有真实 owner-visible `zg361cp.26`、随后同一
lineage played-subject / distinct-AI-owner / event-free paused response 同时成立时，
才允许写 schema-2 registry。

## 尚未闭合的 live gate

候选 live-attempt
`projects-metrics-source-capture-no-launch-5c54014-20260904T080922Z` 仍为唯一、未创建、
未开始、未消费的 absent attempt。当前没有真实 CP26 A/B UI receipt、没有
`cp26_ready_p3_absent` paused provider receipt、没有 checkpoint bytes/SHA/date/lineage，
也没有 schema-2 registry。因此本页不声称 fixture-live、production-live primitive、
production-live loop 或完整 GREEN；默认 capability advertisement 必须继续关闭。
