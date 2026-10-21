# 首次分配的启动前失败

机器 `pc-20260924rtuf-f11af23c08`，实际观察 2026-10-21T20:40:21.019Z。候选源码为 `46cac62bd05a09c7742f48326c314504c20ea5c4`，公共 `prepare` 与 `preflight` 成功；首次 `allocate` 实际返回 1：统一编号器未登记 `living-artifacts`，在创建 canonical 实机 ID 之前抛出 `LiveRunIdError`。

原命令、stdout、stderr 保留在外置 `D:/workspace/ck3-living-artifacts-20261022/environment/public-operations/20261021T204017894355Z-allocate/`。同目录的 `original-codex-tool-event.json` 是原始工具输出事件的精确摘取；`root-tool-observation.json` 明确区分事后提取和当时原始 HANDLE 等待回执，不补造原始 completion。

本次尚未进入 CK3，未授予任何业务通过或正常游戏退出结论。已消耗的机器准入 intent 和 prepared profile 原样保留，不能删除、改名或换 canonical state root 来重置历史。下一步在共享分配层明确退役这一有证据的 pre-ID 失败，再使用同一机器链锁和编号器执行新的准入；当前不是实机验收完成记录。

补登记同时增加真实编号生产者到持久化消费者的回归：活武器与原版产品独立计数，拒绝将内置产品冒充 external mod。13 项编号器回归及该模块严格类型检查通过；与游戏实际作用无关。
