# M7 Graph244 路由消费见证245

新增 `LoadRowReferenceGrowthRouting245Test`，通过公开 `bind/invoke/tail` 检查 Graph244 的路由保留：旧27条与新增3条精确 DIRECT Call，以及1条实际 Tail。每条已接纳路由在成熟生产体的首个真实 Memory 触点抛出该 probe 独有异常，并校验操作、地址、写入值及此前 GS 次数。Memory 不返回虚构数据；提前使用 budget/Float32 会拒绝。

有限范围为31次首触点、96个 foreign Call、33个 foreign Tail、1次直接 GS，共161个顶层操作。两条 lazy 路由各有一次 GS 转交，合计3次。foreign 路径验证原参数对象、原返回对象和一次调用。此程序使用公开 standalone main，非 JUnit，不生成 XML 或 JUnit 测试数；首触点后的 NormalReturn 与完整 callee 算法不在覆盖范围。

2026-11-01 UTC，父岗取得 fresh 单资源后唯一执行：编译 exit0/0.6486159秒，随后 main exit0/0.1362410秒，stdout 为 `route-admission245 complete; no normal-return/native claim`，stderr为空。COMPILE BEGIN 20:12:26.434728 至 MAIN END 20:12:27.316888 的完整窗口为0.882160秒；两进程 reported 耗时合0.7848569秒，phase间0.034796秒包含于完整窗口。原92个缓存 pin、源码/参数 cutoff与新增3个 class保持一致。无旧源重编或旧 Test 重跑。

两次6000-token有限方法生成请求均完整 stop。首轮整体拒绝；纠正轮仍漏7条旧路由及完整 foreign 矩阵，最终仅保留其23条已核正确 admission语句与1条 Tail，owner补齐其余部分。未发第三轮。独立244诊断另记，其两处源码误报整体拒绝。

准备V01完整保留，REV02移除未引用兼容wrapper的额外准备门：完整前缀有4个兼容wrapper，其中仅2个不在原pin清单，早期计数混淆已勘误；实际引用40个顶层类型均由原92个pin解析，未追加pin。Test、原compile参数与原准备回执均未改。

结果只授离线软件路由消费见证；不授 Native/TLS/FP环境、自然分配、完整算法、Game运行、保存日、提速或 M7/G2整体完成。
