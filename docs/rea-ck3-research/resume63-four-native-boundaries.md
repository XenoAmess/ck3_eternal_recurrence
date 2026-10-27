# resume63：角色转移、继承末门、取消输出与生命周期元数据

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-27 UTC。CK3 1.20.0.4/build25734779，EXE 101040248B，SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，image base `0x140000000`。沿用[REA工作方法](resume63-framework-workflow.md)；以下是有限静态研究，Java实机G2仍0/8。

- M0：`[CF5950,CF5A36)`完整RF230B，46指令、3块3边。含`+2D8/+2DC/+2E8`的6个DWORD全位复制，随后`CF9AE0`仍不透明。`+330`先取源P/清源，再读目标Q并可能虚调用，最后写目标P；源目标别名反例否定“源最终必零/唯一所有权”。支持已落Native读取最终context、answer后重验角色及Java完整signed ID合同；不授战后验收。
- M3：`[1D63DB0,1D63ECC)`完整RF284B，64指令。真实getter fallback经过外部规则，原caller的R8D0选择`372DF10`分支，但跨不透明调用后该callee实际R8未知。正常AL保留不等于已归一布尔；不能照抄为Java年龄或title首候选规则。继续原getter/currentframe及原生forecast/实际successor比较，自然继承未验。
- M4：`[2C42820,2C428E0)`raw192B，无PDATA RF；54线性/50入口可达指令，3RET、末4CC不可达。三路写原RCX的DWORD并返回其地址，正常路径保R10/R11；不把入参R10追认为原caller初始receiver。沿`RDX+130`分流读取`+128/+12C`身份表及选中对象字段；表的业务含义仍未知。只补齐原470B caller的输出与跨调用事实，不授完整CanCancel、净退款或到账；Java空报价/credit0保持。
- M7：已证handle生命周期callee的`UW@53FE0BC`仅取本record16B，v1/flags3/count4，直接handler RVA`4225A64`、无chain；未读handler或语言数据。只完成下一入口定位，异常/取消终态仍未知，state3仍不授业务成功，不新增Java状态DTO。

四题均实际使用官方REA raw后端；实际provider窗口未重叠，最大1，并非四后端并发。首卡至末闭场574.965s，不含准备及独审；代码题有独立解码/p8核对，及时闭场、owned0。M0另有M5独审；原件保留完整边界。722B代码/UW范围不代表总I/O：各题还进行整PE身份读取，M3单次SHA+postfstat，M0双SHA；M7已报告约600MB显式逻辑I/O。provider耗时不等于整研究耗时，不报告整体提速或token节省。

原件根为 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/`。以下bytes/SHA已实际读回：

- [M0结果](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m0-context-transfer-cf5950-01/CASE-RESULT01.json>)：7349B / `cc5c18f898def68066d4ad6da25c4e46a8e5778ef661bc1f0a2b470f1db04478`。
- [M3回执](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m3-fallback-gate284-01/CASE-RECEIPT01.json>)：6737B / `8a03d54ca6286cbf81113ba3633e81a29e2547f25f81273b0b5053ef92af696a`。其后限缩见同目录`BUDGET-CLOSE01.json`，2112B / `67bdeff7091be4a71766623636c48ecf5e80f5f9a397b85ab8b4f804f6d804c2`。
- [M4观察](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m4-owner-output2c42820-raw192-01/ACTUAL-REVIEW01.json>)：15114B / `540c133c347103fe6db9e55220a204666f15ab4501a1050b1d15c69ef85f4b6c`，owner记录，独审另记。
- [M7结果](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m7-handle-unwind01/RESULT01.json>)：9846B / `8264d80b087b3f4087848d046ce540fbe38a4919017f4434323d1964c2ae61f7`。
