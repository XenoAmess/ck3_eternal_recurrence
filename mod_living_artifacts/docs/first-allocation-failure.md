# 首次分配的启动前失败

机器 `pc-20260924rtuf-f11af23c08`，实际观察 2026-10-21T20:40:21.019Z。候选源码为 `46cac62bd05a09c7742f48326c314504c20ea5c4`，公共 `prepare` 与 `preflight` 成功；首次 `allocate` 实际返回 1：统一编号器未登记 `living-artifacts`，在创建 canonical 实机 ID 之前抛出 `LiveRunIdError`。

原命令、stdout、stderr 保留在外置 `D:/workspace/ck3-living-artifacts-20261022/environment/public-operations/20261021T204017894355Z-allocate/`。同目录的 `original-codex-tool-event.json` 是原始工具输出事件的精确摘取；`root-tool-observation.json` 明确区分事后提取和当时原始 HANDLE 等待回执，不补造原始 completion。

本次尚未进入 CK3，未授予任何业务通过或正常游戏退出结论。已消耗的机器准入 intent 和 prepared profile 原样保留，不能删除、改名或换 canonical state root 来重置历史。下一步在共享分配层明确退役这一有证据的 pre-ID 失败，再使用同一机器链锁和编号器执行新的准入；当前不是实机验收完成记录。

补登记同时增加真实编号生产者到持久化消费者的回归：活武器与原版产品独立计数，拒绝将内置产品冒充 external mod。13 项编号器回归及该模块严格类型检查通过；与游戏实际作用无关。

2026-10-21T21:01Z 后续记录（同一 `machine_id`）：公共恢复流程已验证并退役上述 pre-ID 失败，随后真实分配 `pc-20260924rtuf-f11af23c08--living-artifacts--R0001`，没有重置计数器。21:02:12Z 的公共 `run` 在写入 launch intent 前实际拒绝：分配器固定了执行 checkout 的辅助脚本路径，但独立冻结启动器要求它自身目录下的同一套脚本路径。CK3、host 和 native session 均未启动。

root 写入合作停止标记后，原分配器实际等到 keeper 退出 0；21:06:34Z 完成屏幕 CAS 释放（293）和管理完成事件（294）。[永久摘要及原件 SHA](evidence/prelaunch-r0001-2026-10-22.json)分别绑定拒绝、原始等待和闭场证据。此场不授予游戏正常退出、业务验收或发布结论。公共修复同时固定实际启动器辅助脚本的完整路径，下一场使用新的 profile 和正常前驱链。
