# REA 学习过程

machine_id: `xenoamess-full-tower-eb9d2c1186`。初次于2026-10-26T12:43:23Z整理；新增条目附UTC。来源阅读、真实工具和Game验证分开。

- **来源阅读｜选框架**：REA6.8.0提供Evidence/provider/投影，非已证效率。published229与runtime仅保3 schemas分开；[版本来源](sources.json)。

- **真实工具｜同后端对照**：相同PE/Rizin命令两对冷样本，direct5.3282/4.6010s，REA8.9364/6.4378s。此次封装较慢，未测token，不能外推语义工作流。[实验原件](experiments.md)

- **真实工具｜Windows失败**：辅助JVM小堆阻断后，仅隔离启动脚本七处堆参数改为LOCAL_PATCHED；随后PE导入/分析约901s达到900s启动预算，未得伪代码或同会话第二次结果，不授warm。[cold03](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/GHIDRA-MCP-COLD03-RESULT.json>)

- **来源阅读＋独立窄核**：seed不把默认auto-analysis缩成函数；disable仅registered。UTF16须用实际next_offset，N/N只本view；原字节/函数/调用图/Loaded分别证明。[工具与源码](tools-and-context.md)

- **2026-10-26T10:09:02.094835200Z｜历史工具读回**：tick-rea01 outer PASS/exit0/Job0，但stdout空、stderr parser error且completion=complete。过程完成不授命令语义成功；此例为CLI，MCP同类处理仅源审。[terminal](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/evidence/managed/slot3/r13_war_declare/tick-rea01/terminal.json>)（9152B/SHA `8b8e5f104d13c9cde028ea9d40c33da9da2f82ebd6858bf6cc5c95f1d31ee1f9`）。

- **2026-10-26T12:43:28.870199Z｜真实工具**：case01的106B/29指令独立Capstone全同，但RF外stub报错、逻辑续边未知，仍PARTIAL。总1610.24s：等卡957.37、卡→首child362.14、首child→末terminal20.25、末terminal→close270.48；REA child仅6.28s。协调/guard未独立拆时，不能归因整体REA或token。[闭场](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper01/CASE-CLOSED01.json>)/[完整成本](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper01/TIMELINE01.json>)

- **2026-10-26T13:04:17.094552Z｜真实工具/范围修正**：case02复用106B、增126B，三RF232B/64指令与独立CFG20块31边一致，局部qword ADD闭；5callee/异常/world未知，未持UNWIND flags，不称whole逻辑函数。全链603.06s（等卡204.97、卡→首child62.96、末terminal→close282.04），REA child15.52s；范围不同不比提速。[闭场](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/network-helper02/CASE-CLOSED01.json>)/[成本](experiments.md)

- **2026-10-26T13:42:09.618945Z｜真实Node-only复用＋独立逐值核**：仅包装历史Evidence，MCP import/get complete/get summary/export/close成功，child 11.131843s/exit0/Job0，close后58734B导出仍在；record值/类型/ID/params/null profile未变。serialized CallToolResult complete131281B、summary2183B；摘要仅元数据，无图/操作数，不能答CFG20/31或+308→config+20 ADD。压小不等于同质量或token节省；无新PE/Rizin/Ghidra/Game。[READBACK](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/evidence-reuse01/READBACK01.json>)（10907B/SHA `83966253141d208ab0ac425d4bedef002b9faa54b7424e717cd8f944443230d8`）。

最终close为13:49:58.539990Z；active-A→close1116.28s（等卡376.74、卡→首child133.93、terminal→close594.32），child非全链。闭场元数据晚卡19.54s，不授720s整窗PASS。[复用时间线](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/evidence-reuse01/TIMELINE01.json>)

本页不授Game或token验收；执行由r13单卡负责，未知边界与后续最小路线见[工具页](tools-and-context.md)。
