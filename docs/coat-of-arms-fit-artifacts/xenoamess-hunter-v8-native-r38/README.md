# xenoamess-hunter-v8 native R38

状态：`prepared`。本目录为 Gamma G2 的追加式原生证据入口；运行结果无论 GREEN 或 RED 都不得覆盖此前浏览器证据，也不得通过事后放宽门限改写结论。

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

本 README 在 live attempt 后追加结果和证据索引；`prepared` 不代表 G2 已通过。
