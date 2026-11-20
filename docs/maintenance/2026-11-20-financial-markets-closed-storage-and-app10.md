# 已关闭存档的空间回收与 app10 来源

machine_id: `4-8e1c2f1861`。本记录只整理原执行回执，未新增 Game 操作、读档、编测或资格。完整路径、原 wait/log、每个文件的逻辑身份及 SHA 见[事实索引](evidence/2026-11-20-financial-markets-closed-storage-and-app10.json)。

原08压缩窗口仍为退出码2、5.8249184秒：受单文件保守临时余量门拒绝，下一文件未提交，原1.5GiB场次目标未达到。它的17次既有尝试、已保留内容和拒绝回执不因后续成功改写，也不重放原作业。

本轮三个独立作业的真实结果如下：

| 原作业 | 原退出码 | 原墙钟秒 | 实际范围 |
| --- | --- | --- | --- |
| RECLAIM-exact-restored09 | 0 | 3.1847722 | 仅2个关闭场次的旧 restored 副本；相同内容归档保留 |
| COMPRESS-closed-financial-saves10 | 0 | 33.5646154 | 13份关闭 SAVE 原地 NTFS 压缩；测得目标达到 |
| PACKAGE-save-audit-app10 | 0 | 14.8626697 | 仅新 save-audit-app10；`-DskipTests`，未重测 |

被回收副本与留存内容的映射为：

- `C:\workspace\ck3-market-live-20261119y\managed-states\financial-cold-reload01\state\profile\save games\restored_campaign.ck3` → `C:\workspace\ck3-market-task-20261118\financial-physical-saves-R0033\delisting33-day14-01\xar_checkpoint.ck3`；164311623字节，SHA256 `1c61e43aceb52da3481a433d7e09e1a3cdf290ce74befca1617f88ad2525e7a9`。
- `C:\workspace\ck3-market-live-20261120a\managed-states\financial-cold21\state\profile\save games\restored_campaign.ck3` → `C:\workspace\ck3-market-task-20261118\financial-physical-saves-cold01\cold-next-baseline01\xar_checkpoint.ck3`；164315118字节，SHA256 `def5ef61b87a8b134e79714938d2cc727e34755a0c375b9407b2d3981933e920`。

这些是原09同时持有独占句柄并核同 SHA 后删除旧副本的事实；目录、最新R35基线和历史失败保留。后续10仅改变13份SAVE的物理分配与压缩属性，各自逻辑字节数、SHA、FileID、卷、创建时间及mtime均保持。压缩前后按文件测得分配量减少1450872832字节；卷可用空间最终31883841536字节，变化不唯一归因于单批作业。此历史测量不是新的实时空间读数或新场次准入，不回退旧spent或延长期限。

app10捕获保存真实入口JAR、manifest的15条Class-Path、完整55文件Quarkus闭包，以及6份包内producer-source与当前源码精确相等的证据。app09和旧final20仍是原历史产物；没有把旧包重新命名或重签为本轮代码。容量协议软件的474金融方法与原shared23合计497 distinct、358源文件，属于原软件验证；打包、压缩、回收和本事实索引均不授Game推进、395日容量、性能、金融业务或完整产品通过。
