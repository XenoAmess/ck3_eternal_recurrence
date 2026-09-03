# CK3 启动 guards 与 workforce 分段实机证据（2026-09-03）

本轮只做 observer-only 启动：固定 Steam CK3 1.19.0.6（EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`），不读档、不游玩、不触碰商店/付款；每轮使用一次性 userdir，Frontend 后 WM_CLOSE，且记录 cleanup。

| 变体 | 运行证据 | 结果 | 备注 |
| --- | --- | --- | --- |
| bare + guard-on bridge | `_runtime/formal-guard-on-bare-20260903-r1/report.json` | GREEN：Frontend，exit 0，`cleanup_proven=true` | guard-on DLL SHA-256 `99BC4656D8258789803046A73B2B7798EAAA9C72B586D91CD28A8751365A89E9` |
| event-core + 全语言 localization | `_runtime/formal-phase2-event-locfull-20260903/report.json` | RED：Total on_action 881 后 timeout，exit 1，cleanup GREEN | error.log 0；261 files / 15,924,897 B；排除 loc 缺失因素 |
| workforce blocks 0–161（left） | `_runtime/formal-phase2-workforce-left-full-20260903/report.json` | GREEN：Frontend，exit 0，`cleanup_proven=true` | 264 files / 12,932,133 B；segment 1,638,028 B，SHA-256 `83E38BBD214DECF48E546E60DB4F37B1006DFAFCEDE1EB448883411F613A1EAA`；截断段产生 21 个预期 Unknown effect/Unexpected token |
| workforce blocks 162–323（right） | `_runtime/formal-phase2-workforce-right-full-20260903/report.json` | GREEN：Frontend，exit 0，`cleanup_proven=true` | 264 files / 14,282,642 B；segment 2,981,378 B，SHA-256 `AA50319D1331896E41EB9DE7BC80D1167A3BAC3E4725C50FD85D42DAADACC1E1`；同样有 21 个截断段解析错误 |

结论：guard-on bridge 本身能到主菜单；event-core 在补齐全语言 localization 后仍卡在 Total 881（且 parser/loc error 为 0）。Workforce 左、右分段分别可到 Frontend，因此当前 stall 只在完整组合/跨段依赖或特定完整块交互中出现，不能把任一半段单独判定为根因。所有 run 结束后 CK3、injector、watchdog 进程清空。

补充：将两半作为不同文件名同时加载的 disposable A/B
`_runtime/formal-phase2-workforce-split-20260903/report.json` 也到达
Frontend（exit 0、cleanup GREEN）。该轮 error.log 仍有 21 个截断段解析错误；后续取证指出当前分段器在 BOM/块边界可能产生 corruption，故该结果仅作启动可达性记录，不能作为生产拆文件修复依据。
