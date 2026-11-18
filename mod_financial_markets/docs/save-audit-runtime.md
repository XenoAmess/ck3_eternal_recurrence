# 物理存档审计

金融工具复用共享`ck3-save-core`的plain/ZIP/显式decoder读取，命名Quarkus入口为`save-audit`。默认validate/build入口保持原用途。审计只读指定物理文件，不连接Game或修改游戏状态。

命令为`audit --inputs request.json --output unused-external-report.json`。请求须显式给机器、仓库、源SAVE的真实路径/bytes/SHA、实际编码布局、零或一个冷载SAVE与decoder。输出使用外部已有父目录下的新文件，拒绝覆盖。实际加载的审计和parser源码资源、POM及代码来源在处理前后核对；旧同版本jar不能冒充本轮实现。

请求路径与规范物理路径分别保留，前后核samefile、属性及SHA。所选故事单条最多512KiB、总计64MiB、记录最多200000；共享旧schema与原4MiB保留限制不扩大。大市场可能触发限制，必须记录真实拒绝并根据实际需要调整，不能截断后假称完整。

先从真实1.21物理SAVE核版本/格式、数值scale、story与character引用类型、故事表和global exchange。缺变量、未知type与省略identity不得默认为零。币/账户/仓位/债务按永久ID、原生story引用及法律holder核对；技术story_owner不等于产权人。金额分别核现金、冻结、费用和基金，债权不当现金。

冷比较需要另一个真实进程载入后、同暂停日期的物理SAVE及独立装载证据。同文件复制或对象总数相同不能证明冷载。候选报告始终`financialCertified=false`；exit0只代表已选择字段约束成立，exit2为不完整/冷比较不同，exit3为约束冲突，exit1为输入或处理失败。真正业务认证由实际动作、完整财务读回和运行证据共同判断。

2026-11-18，machine_id`4-8e1c2f1861`：共享原10项回归及金融完整160项通过，其中两项SAVE JUnit复用52个合成断言；这不是1.21实际编码、命名入口实用或冷载通过。对应原件位于`C:/workspace/ck3-market-live-20261118/operations/MVN-save-core-audit01`与`MVN-financial-ai-save-full01`。
