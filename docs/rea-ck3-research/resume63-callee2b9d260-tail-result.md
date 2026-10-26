# resume63：2B9D260 后继字节与真实失败

`machine_id: xenoamess-full-tower-eb9d2c1186`；2026-10-26 UTC。新增64 B已取得，有限正常路径支持AL比较假设；**REA的RAM128重解未完成，180秒闭场预算失败**，两项分开记录。接续[第三题前缀](experiments.md#resume63第三题64-b前缀保留partial)。

## 来源与有限结论

原PE为101040248 B、SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`、imagebase `0x140000000`；1.20.0.4 / build25734779为来源合同，不是loaded身份。新读仅 `[2B9D2A0,2B9D2E0)` 64 B，SHA `2a7ec569281a76e975de44e1d4ec82fbdec972e71f4d97d04393795abc891475`。旧C3的64 B按文件/raw SHA复用，RAM拼128 B的SHA为 `8b99fbb6de23dc4763b1964d1fb5853aff032482cf9fb79193c1e8921cda50fb`；2A0不是指令入口。

新增开头 `c0 c3 32 c0 c3` 补旧29E的 `0f94`，得到 `SETE AL`、RET2A1，以及2A2的 `XOR AL,AL`、RET2A4。从原entry可达69 B/21条、10块12边，无call或范围外非call边。后59个新增字节属于未归属的padding/邻段，不能算入目标body。前17条62 B已有C3双decoder；本题末四条以Capstone与raw手核支持，**没有新Rizin128逐指令一致结论**。

限定正常、无访存异常路径：各输入先读qword `+1C8`，非空取所指对象dword `+80`，空则取 `FFFFFFFF`。两值任一为该bit pattern就走AL0出口，否则CMP两值后SETE AL。因此AL为“两值均非FFFFFFFF且相等”，仅AL归一化，EAX高位未归一化。实际caller1A200C0对AL非零跳过显式累计；字段领域含义、完整ABI、异常/unwind、当前world可达性及兵力/到场/胜率仍UNKNOWN。无Game或Java采用资格。

## 原命令失败与预算

REA先p8新64 B，结果与独立原件一致。计划随后打开hex RAM映射并p8/pDj128；实际 `ol.j` 仍显示原PE descriptor，`omj` 在Rizin0.9.1不存在，命令列表停止，未得到RAM映射或128解码正证。实际help给出的列图接口为 `omlj`。虽provider exit0/complete/未截断，不能把此结果算RAM重解成功。

官方 [v0.9.1 io_malloc.c](https://raw.githubusercontent.com/rizinorg/rizin/v0.9.1/librz/io/p/io_malloc.c) 支持hex URI解析到内存，[mapping文档](https://book.rizin.re/src/basic_commands/mapping_files.html)说明open/address接口；这些源审不替代本次未完成的实际观察。没有发wx或写PE，也未创建128 B磁盘副本。

| 计量范围 | 实际结果 |
| --- | --- |
| decoder / owned峰值 / close | 0.425 s / 24813568 B / 16:20:58.337Z |
| REA service / Rizin owned峰值 / close | 4.913 s / 597905408 B / 16:21:13.898Z |
| 新卡T0 / work截止 / close截止 | 16:20:23.032152 / 16:22:23.032152 / 16:23:23.032152Z |
| 实际最小close / 完整窗口 / 逾期 | 16:24:41.431Z / 258.399 s / 78.399 s |
| outer联合峰值、Job0 / Shared资格 | NOT_MEASURED / NOT_GRANTED |

work已过后没有启动修正或任何新provider。闭场长脚本的本地8191字符守卫在exec前拒绝，拆小闭场后真实逾期；未把它写成OS执行失败或按窗PASS。provider在work内关闭与整体闭场LATE分别保留。service.close无错误；own4PID在16:24:41及中断恢复后的16:32:50Z均读回不存在，0 owned/MCP/exec。富receipt与独审后续追加不修改原close。

## 精确原件与后继

原件均在 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-tail01/`：

- [CASE-CLOSED01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-tail01/CASE-CLOSED01.json>)：4458 B / `cf776bec2958083bca3325a6d4bb1e114f1cebb2f46f677613688d250911e327`。
- [CASE-RECEIPT01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-tail01/CASE-RECEIPT01.json>)：5498 B / `d87db2d180b11c010b29a0798f64b4f5b3c4ba76fc77352cc8aca12bab0c2dec`，传递固定raw、flat/bundle、实际命令和crosscheck。
- [POST-INTERRUPT-READBACK01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-tail01/POST-INTERRUPT-READBACK01.json>)：1244 B / `467049fe0f860bb961cdd496f0de91492bf21a621adb4a529db82450e64d5000`。

M5在16:33:31.780Z独立复核old/new raw、ModR/M、6个signed分支与entry可达图，69 B raw SHA `a8d3a287e71ac776278bf065d85921890ae4742cee77da5d2efc99ba1bf8a823`。正常AL假设成立，若B为candidate实际DWORD或FFFFFFFF，则 `EAX=(B & FFFFFF00) | AL`。196个RAM辅助代数例不算native/JUnit。独审原件 [INDEPENDENT-M5-REVIEW01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee2b9d260-tail01/INDEPENDENT-M5-REVIEW01.json>) 在16:34:57.662Z另CREATE_NEW，5614 B / `91ef2b4abfdf1ff61fbca6ec71155dc9e09c9825fdba74f40d0e78e1c5596ee1`，原close的LATE/PENDING不改；[M5领域记录](../ck3-native-ai/2026-10-27-m5-rea-callee2b9d260-normal-path-resume63.md)明确不授128 Rizin成功。

16:27:14Z Native点值20files/3dirs含root、logical97431 B/native140160 B，非历史峰值；后续metadata另增，physical release0。原16 MiB case额度保留，不续旧执行卡。Root已要求不为Rizin形式补测C4。下一题按新PLAN、预验证最小close与新鲜容量卡独立排期，无自动扩读。
