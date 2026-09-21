# xenoamess-hunter-v8 native R38

状态：`passed`（2026-09-21）。本目录为 Gamma G2 的追加式原生证据；它不覆盖此前浏览器证据，且首次 live attempt 使用的门限已在运行前提交，运行后未改动。

## 冻结输入

- 当前最终候选：`xenoamess-hunter-v8-pareto-candidates/coat_of_arms.txt`，389,675 bytes，1,024 个 `colored_emblem` 和 1,024 个实例。
- 源码 SHA-256：`C645E429633AD818028D5A2FFE29C9FE1D6364F16102764DEC86EE87B94D1FF0`。
- 浏览器参考图：`pareto-candidate-01.png`，10,342 bytes，SHA-256 `485119A59F96B1A6B2CC436742BFF025C8D9B021EBB95B21CF050DF52C03BB92`。
- CK3 exact build：`1.19.0.6`；`ck3.exe` 95,206,008 bytes，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 所有数值门限和交互限制见 [thresholds.json](thresholds.json)，必须先于首次 live attempt 提交到 `master`。

## 执行合同

1. Steam 必须处于离线模式；启动前 task bus 和进程清单必须确认 CK3 独占槽可用。
2. 使用 fresh userdir 与 typed native MCP 完成 Apply → calibration → framebuffer → Copy/reapply；禁止 OCR、键盘、鼠标和固定坐标。
3. 原始报告和 crop 在外置 append-only run 目录保留；仓库仅收录 hash-bound 摘要、必要 framebuffer/crop 与精确 commit。
4. 任一身份、校准、像素或 Copy/reapply 门禁失败即保留 RED，不改 `thresholds.json`。

## R38 结果

- exact repository head：`c7943033bdd079167e8e4e7482f5912497e65af1`；总耗时 296.82 秒，完整报告 `ok=true`。
- 原始报告位于 append-only 外置目录 `D:/ck3_coa_gamma_g2_r38/raw-report.json`，4,014,852 bytes，SHA-256 `B3FE3032F5C8ACB5496FFC78D1317AF6BE579124A5BCD51094D0408A5177F6C8`；可审阅投影见 [summary.json](summary.json)。
- Steam `WantsOfflineMode=1`，typed MCP-only；OCR、键盘、鼠标均为 false。CK3、bridge DLL 和 injector 身份均由报告绑定；结束后 job active process 为 0，CK3 进程清单为空。
- 九点 UV 校准最大重投影误差 0.463543 px，小于预冻结 2.5 px；没有使用固定屏幕坐标。
- 浏览器参考图 → CK3 原生 framebuffer：MAE 0.0461952、color MSE 0.0185736、edge loss 0.118908、最差 8×8 空间块 0.125018，均通过预冻结门限。
- 原生 Copy 保留 1,024 个逻辑层、`colored_emblem` 与实例以及九类语义字段序列；原生规范化源码为 246,123 bytes，SHA-256 `BB898A87EAA22A1F8E451F73E1778F9DA908F425E62793EAC30883041412DCC3`。
- Copy → reapply framebuffer：MAE 0.0000524955、color MSE 0.000000205865、edge loss 0.000186073、最差空间块 0.000299564，均通过更严格的重应用门限。
- [native-crop.png](native-crop.png) 是首次 Apply 后的 15,095-byte aligned-content crop，SHA-256 `8E71EF63A05DEEE435FE86A0C79E67832660671E62928B6D1B84E79B3A77A4C2`。
- [native-copy-reapplied-crop.png](native-copy-reapplied-crop.png) 是 Copy/reapply 后的 15,106-byte crop，SHA-256 `7692BF8E372760A707F7A2648104A750727610CE961996670DB727F33A5E13E1`。

结论只覆盖当前最终 Pareto 01 的 1,024 个 `colored_emblem` 路径。指标证明预声明容差内的浏览器/原生视觉一致和极低 Copy/reapply 噪声，不声称 GPU 逐字节一致，也不外推未验 texture/shader/VFS 组合。
