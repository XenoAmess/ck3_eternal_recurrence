# P109：预算只编解码声明的snapshot角色

普通spending/current路径每次调用 `OrdinaryFinanceCollector.budget()` 都会组装并parse完整snapshot，数MB native history不被预算消费。本单元只替换wrapper.snapshot为独立预算角色；原codec已用FullJsonTree大limit，这是CPU/分配优化，**不是64KiB功能修复**。原inputs、四个完整domain ledgers、campaign root、state/head一致检查和所有预算判断保持。

私有budgetSnapshot按原值copy-present：paused/map、actor ID、native/date/snapshot/public revision、每行war_id和完整pending interaction值。非Obj/Arr错误形状、不合法war行、重复行及missing/null/value差别不洗白；pending的false/0/[]仍nonnull，不能变clear。融资角色没有增加pending。本单元增加私有方法，源码/软件通过不授冻结Runtime的body-only热替或实际采用。

模型一次200/stop，UTC19:21:53.501→19:22:06.145，TTFT2368.27ms、total12643.78ms、prompt17070/output1710、cached=null。核心角色语义partial采用；owner复用已有纯member selector/stream，未采用遗漏Map/ArrayList imports及冗长整方法输出。原件在 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/budget-snapshot-performance109/model01`。

## 新DATA

必要Collector1TU exit0/12class/5.2765332秒；新Test/main1TU exit0/2class/4.5571881秒，仅三个新方法3P/0F/0E/0skip，7.1487441秒，19:34:30.109026Z close。未重编或重跑旧codec/旧case。

30项既有budget corpus逐项在原snapshot、同snapshot加未消费139行history、角色snapshot之间比较完整typed Request、Policy Result及encode bytes。额外验证Budget特有非法war行必须拒绝、missing/null ID为unknown、重复ID按行数、pending三态；publicbudget用四个原软件向量domain全文和同state/head验证原文档/root/snapshot字节不变。资源37430B，SHA `bd3aea63baf65c1fcbe36310d629cd3813343ca29e2f3de3b68603db8ec7b338`；POM只引用该既有资源，不复制原料。

这些是original-producer软件输入加未消费扩展DATA，不是原完整FinanceCurrent、实际账本准入或新保存证明。

## 实际有限同输入ABBA

旧P108已编Collector为A，新P109为B，其余classpath与输入相同；固定四JVM A0/B0/B1/A1，CPU1/384MiB/45秒，各2warm+4measure，全部8warm与16measure保留。计时完整publicbudget的wrapper组装、encode、decode和observe，不删慢样本、不强制GC、不设速度assert。

| 每模式8个实际测量 | A | B |
| --- | ---: | ---: |
| 中位ms | 18.22445 | 0.2783995 |
| 均值ms | 19.222762625 | 0.735387375 |
| 范围ms | 16.8624–22.7528 | 0.1172–2.489399 |
| 主线程实际分配bytes（均值/中位相同） | 51992952 | 28872 |

组件中位约减少98.47%、主线程分配约减少99.94%；完整wrapper3403002→1064B。四JVM输入snapshot3402157B和root各自SHA固定，结果694B/SHA `f463be75ab7cb0f5e5a5828f5a0fc8b25f2055bb8e645ba7f39fbb973cf45c24` 全同。

**整process并未更快**：两次ACTUAL进程合计A7.9696502秒、B8.1413520秒；outer全窗A9.3364754秒、B9.7467725秒。load、setup、main、warm和原样本分别保留，组件差异不授整个进程、HTTP或游戏日速度。末资源实际close为UTC19:35:04.792321Z。

原件：`D:/ck3-state/resume91-native-integration/p109-budget-test01/QUALIFIED-P109-PUBLIC-BUDGET-SOFTWARE-AND-ALL-ABBA.json`（25772B，SHA `3e23066e1084a44cd8c5877f5b2c8eef19234ca232dc105ae61e2c4f9f4599c8`）；全部样本 `ALL-ABBA-SAMPLES.json`（10882B，SHA `e6d7c219c7d144eaaf18070793f0648c051f447b8976393460c13bb934bd9269`）。Root独读摘要 `P109-ACTUAL-ABBA-REVIEW.json`（9090B，SHA `71d38289d9232f40adf2ec936cec24e7ca7421fba909ff77a77ee654813b82a4`）在 `D:/ck3-state/resume91-root/post-vacation-20261107`。

下一P110为cashContext/Focus及Gift archive验证重组的同一角色闭环，须保完整政治CB、后继Construction收入材料和新command表示边界；另有原全文归档1MiB边界待P111解决，不裁原件绕过。持续目标不结束；原UNKNOWN/P100/Guard保持，本轮新增确认保存日0，10秒目标未达。
