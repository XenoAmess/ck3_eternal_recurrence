# 已闭场独立存档退役与可用性

2026-11-23，机器 `4-8e1c2f1861`。本记录只整理已完成操作的元数据，没有再次读取存档载荷、删除、压缩或登记新预算。

四批共退役 **56份独立canonical存档原件**：old8 actual02为8份，old16 actual01、endpoint16 actual01、continuation16 actual01各16份。它们是已被后继实际证据取代的独立检查点，不能称为重复副本。**这56个原literal路径已不可读**；原ARCHIVE收据只保留历史身份，不能再作为该路径当前可读的证明。

四次原APPLY都返回 **2**：各批`failure=null`，退役件数均完成，但各自空间目标未达到。原完整SHA、独占句柄／短CAS及before／after可用性记录保持；ARCHIVE收据、Raw、Audit、Whole、日志与原失败不改写。[可用性索引](../../docs/maintenance/evidence/2026-11-23-financial-markets-closed-independent-save-retirements.json)逐件列出56个原路径及完整SHA，并指向各原结果的before／after FilePins。

另列的R77维护属于不同对象：6个已闭场profile别名副本删除原返回0，4168个生成shader文件删除原返回0；两项均不增加上述56份独立canonical的计数。R75 wallet source及R77 baseline、post-help、terminal四个canonical外部归档保留，具体原件pin在同一索引中。

各操作的free before／after、原AllocationSize及逻辑退役字节分别保留，不合并宣称唯一卷收益。不据本记录退还历史spent，不授后继场准入、新保存日或金融业务通过。后继恢复须使用保留的实际基线，不能重试打开已退役路径。
