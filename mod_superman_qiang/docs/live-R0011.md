# 《超人强》R0011 正百分比与缩放投影对照

2026-10-04，CK3 1.20.0.3/build 25652598，简体中文。使用与 [R0009/R0010](live-R0009-and-R0010.md) 完全相同的 A0004 22 文件 production。仅增加外置最小夹具，完成测试计划 L2-07 正百分比及 L2-17 仅改变量不重加 modifier 的控制和重复重建验证。

完整 ID `desktop-3fevhd2-1c74096080--superman-qiang--R0011`，UUID `8c8659f7-d805-40c1-9dc1-11899c850dc6`，实际 PID 2184。原始资产永久保留于 `C:/ck3-superman-qiang-20261004/acceptance/`。输入在 `supplement-fixture-a01`，manifest SHA `bc92e921bc4d7d3576aba319c27a9ae21cf9b42abb970b40cb0d074c53b1b6eb`；独立 JAR 对四文件实际 parse/roundtrip，全部 PARSED/exitCode 0/roundTrip true/无诊断。`supplement-grammar-a01/receipt.json` SHA `4fde9144058e5fddcba3ccd2aaad3fcee81b82ff6d495dbb746efc35eaf2c79f`，原 source SHA、corpus、argv、stdout/stderr 均保留。grammar 未替代游戏执行。

第一阶段三个真实 PASS，随后原生暂停、真实 checkpoint 保存并独立解码；第二阶段继续同一进程，等已排程的十天后隐藏事件真正完成，再由原生暂停并保存。判断完成使用真实 END marker，没有把等待时长当作通过。

| 实测输入 | 真实有效技能变化 | 实际账本及保存投影 | 六基础数组 |
| --- | --- | --- | --- |
| 接收者 +50%，双方基础外交 10 | 接收者 15→16，来源者 10→9 | 接收 +1、来源 -1，各一个正确符号 modifier，scale 默认 1 | 双方均 10×6，保持 |
| 来源者 +50%，双方基础外交 10 | 接收者 10→11，来源者 15→13 | 接收 +1、来源 -1，各一个正确符号 modifier，scale 默认 1 | 双方均 10×6，保持 |
| 控制：接收账本 1 并重建，再只把变量改成 3 | 11→11 | 实际账本 3，旧 gain modifier 仍是默认 scale 1 | 接收者 10×6，保持 |
| 控制之后显式生产 rebuild 两次 | 首次 13、第二次仍 13 | 实际账本 3；仅一个 gain modifier，原始 `multiplier=3`，没有叠加 | 接收者 10×6，保持 |

第一阶段 checkpoint 68,456,008 bytes，SHA `5a6f6b27a6ec7caeec22ae292bd7e6fd5321efae115f1aa7a7a47112811b2589`；`save-readback-a01/fixture-readback-v6.json` SHA `190abae4341ab11b0c77bd84ebf79eff9eb5db6c232d9a71f7b5c286d91b56f8`，三个结果均 1，七个真实角色。`phase1-save-gate-a02.json` 对实际 scale 与有效值的控制断言通过。早先 a01 verifier 用字符串包含 receiver 错误识别 case 名里含 receiver 的 donor，原始误判输出保留；a02 改为 role flag 前缀识别，重读同一不可变存档，没有改游戏或夹具。

第二阶段 checkpoint 71,503,708 bytes，SHA `ea6ae54e343b9058b5586a3395ce4f36d6854590107ecc080988707a4807b55c`；`save-readback-a02/fixture-readback-v6.json` SHA `cdc9a54938e26167a08fab62568d1a9ec9adfa7acb0c22097d6176733208f172`。`phase2-save-gate-a01.json`：三个独立角色基础数组/账本/投影断言均通过，holder 65870 的两次真实有效读值均 13，保存原始 modifier 唯一、multiplier 3。root 另只读消费第一阶段存档，确认正百分比的 +1/-2 显示差异与 raw 守恒。

本轮证明百分比取整后面板变化可以与原始修正点不同，以及 scale 在添加 modifier 时取样，生产 rebuild 正确取新变量并保持幂等。原始基础技能不修改。此证据不作为 Workshop 玩法图片，不扩展为随机分布统计证明。

runner SHA `be75646484afa72ee491bfb7d845ef16dcc2be58b11b3495590325b25f4bf04d`，只增加显式 vanilla preparation 与 session 结果范围/真实失败退出码；生产字节不变。新 session report `ok=true` 仅代表正常持有会话和 controlled cleanup 完成，真实产品通过依据是上述独立 gate。启动前新鲜 Steam 离线直接审阅、屏幕独占续租与停止后的完整进程树/watchdog/inventory 保全。下一步是未启用模组的普通旧存档加入 A0004 和干净正常玩法媒体。
