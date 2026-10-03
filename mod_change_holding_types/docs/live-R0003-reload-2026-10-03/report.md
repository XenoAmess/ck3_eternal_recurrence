# R0003 保存重载与干净生产矩阵核验候选

本轮 `bf-202609141645-5434332d4d--change-holding-types--R0003` 在 CK3 `1.20.0.3`／Steam build `25652598`／固定 EXE SHA 上取得保存重载和修正后生产矩阵 PASS。结论仅适用本机精确 build；九语视觉与正式发布尚未完成。

原始 snapshot001 捕获时 `map_ready=false`，没有人物状态，不能用于重载成功结论。采用实际 ready 的 snapshot002：`map_ready=true`、runtime 人物 `31254`、同一 `date_raw=53144328`、暂停、金币 `846`，与 R0002 真实 GUI 执行后相同。加载保存 bytes 的 size 与 SHA 也复核一致。原生状态断言另证实 Rossano 保持玩家直辖城市，未选中的首都保持城堡。

后继 fixture02 通过 10 项生产 effect 矩阵：六目标转换、同类型拒绝与不变、实际 AI actor 阻止、非男爵领拒绝。加上两项保存状态断言，共 12 PASS，具备 START／END 和 AI actor 到达标记，无 FAIL。inbox 返回 `native_executed=true`、`marker_confirmed=false`；PASS 依据实际引擎 debug markers。捕获的 error.log 为 0 字节，此轮消除了 R0002 的重复城堡初始化诊断；失败原记录仍保留。

只读英文截图可见六个决议名称、城市成本 400、玩家／和平／直辖已建且未出租／无在建／City Planning 条件。默认目标是 Trani，对应中文“特拉尼”。建筑损失与政府／继承警告已渲染；detail 图的悬浮提示遮住警告右半行，另一帧处于淡入过渡，尚需稳定且无遮挡的全文截图。不能以当前两帧声称警告全文视觉验收已完成。

七种新增语言的视觉验收仍 pending，格式／token 覆盖不能替代实机渲染或母语审阅。父任务准备 R0004 以 debug flags 冷载并检查九语；本报告没有使用未来结果，生产 runtime 与 R0002 同字节。保存状态、生产 effect、英文视觉与真实 GUI 付款是不同证据，各自记录。

逐文件证据、SHA、状态及边界见 [JSON](report.json)；相对证据路径以本报告外置保留快照目录为根。R0003 clean matrix 不等于整个 release 完成，清理、公开页面和 Change Notes、fresh cache、永久 changelog 等仍需独立回执。
