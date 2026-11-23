# 已闭场独立存档退役与可用性

2026-11-23，机器 `4-8e1c2f1861`。本记录只整理已完成操作的元数据，没有再次读取存档载荷、删除、压缩或登记新预算。

四批共退役 **56份独立canonical存档原件**：old8 actual02为8份，old16 actual01、endpoint16 actual01、continuation16 actual01各16份。它们是已被后继实际证据取代的独立检查点，不能称为重复副本。**这56个原literal路径已不可读**；原ARCHIVE收据只保留历史身份，不能再作为该路径当前可读的证明。

四次原APPLY都返回 **2**：各批`failure=null`，退役件数均完成，但各自空间目标未达到。原完整SHA、独占句柄／短CAS及before／after可用性记录保持；ARCHIVE收据、Raw、Audit、Whole、日志与原失败不改写。[可用性索引](../../docs/maintenance/evidence/2026-11-23-financial-markets-closed-independent-save-retirements.json)逐件列出56个原路径及完整SHA，并指向各原结果的before／after FilePins。

另列的R77维护属于不同对象：6个已闭场profile别名副本删除原返回0，4168个生成shader文件删除原返回0；两项均不增加上述56份独立canonical的计数。R75 wallet source及R77 baseline、post-help、terminal四个canonical外部归档保留，具体原件pin在同一索引中。

各操作的free before／after、原AllocationSize及逻辑退役字节分别保留，不合并宣称唯一卷收益。不据本记录退还历史spent，不授后继场准入、新保存日或金融业务通过。后继恢复须使用保留的实际基线，不能重试打开已退役路径。

## 后继补记：另5份独立原件退役，累计61份

residual5原APPLY返回 **2／5.1388321秒**，5份均已退役，`failure=null`、空间目标未达到；不能改成操作成功返回0或追认新场准入。以下五个原路径已不可读，原完整SHA、before／after及保留的ARCHIVE／Raw／Audit／Whole／日志索引见同一可用性JSON新增批次；前四批56条未改。

- `C:/workspace/ck3-market-task-20261118/financial-physical-saves-R0033/delisting33-baseline01/xar_checkpoint.ck3`
- `C:/workspace/ck3-market-task-20261118/financial-physical-saves-R0033/delisting33-day4-01/xar_checkpoint.ck3`
- `C:/workspace/ck3-market-task-20261118/financial-physical-saves-cold01/cold-next-baseline01/xar_checkpoint.ck3`
- `C:/workspace/ck3-market-task-20261118/financial-physical-saves-redemption-existing01/redemption-existing01-terminal01/xar_checkpoint.ck3`
- `C:/workspace/ck3-market-task-20261118/financial-physical-saves-independent-seed19/seed19-baseline01/xar_checkpoint.ck3`

另有R78六个profile别名副本和4352个生成cache文件实际删除原返回0；R77三份及R78四份canonical归档仅原地无损NTFS压缩，内容SHA、FileID、mtime／birthtime和原元数据pin保持，仍可读。两份压缩结果均原return2／targetfalse，未改写为目标达成。这些副本／cache与压缩不计入61份独立原件退役。

本轮384MiB维护、256MiB软件及64MiB residual三项实际新准入保留，最新owner上限386434747394字节；历史spent／upper不退款。各操作free窗口及AllocationSize分别保留，不合计成唯一卷回收，也不以该维护记录授后继Game或业务资格。
