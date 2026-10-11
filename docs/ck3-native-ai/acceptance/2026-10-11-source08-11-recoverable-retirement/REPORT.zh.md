# Source08–11 可恢复退役实际结果

32批原始结果均完整成功，按原索引共删除31624个非host文件，gross逻辑字节563,263,222；四个原host与全部目录保留。复用现有排他句柄/父目录非reparse/native身份/SHA guard，逐项恢复来源先验→intent→disposition→close→absent；本摘要只消费原小结果，不再次读取目标或ledger。

141个差异blob已实际复制并读回，共10,721,390 B。Source15及原host覆盖其余旧内容；旧source-index、O7/O8/O10/O11元数据/Git objects、Cbr2/3、当前13–15、所有cache/SAVE不在候选内。原混合commit/host身份不改；旧validator需要旧路径正文时必须先实际恢复，不能声称退役后的旧payload仍完整在线。

最初closure源码在ROOT只读审阅中被拒，原因是parent argv与实际ROOT wrapper不同；它未执行，没有actual失败命令或失败回执。后继仅修该接点，首次实际闭账使用closure-command-001，不重跑preserve/32批。旧源码保留为SOURCE_ONLY_REVIEW_REJECTED_NOT_EXECUTED，actualfailure为NULL。

实际恢复预约已CLOSED，未来预约0。CAS/ledger/小回执新增占用由闭账carry单独进入下一准入；唯一 `CREDIT-EVENT.actual.json` 使用gross563,263,222，不减CAS、不将净量再扣一次。事件尚未claim/consume，不重复旧五SAVE、R52、R54或本轮其他清理credit。实际allocation API总和626178752 B与逻辑字节分列；并发free差值不归因于本批。

事实及32批原件pins见 `FACTS.actual.json` → `CREDIT-EVENT.actual.json`。原PLAN、RECOVERY、ADMISSION、CLOSED和六条原命令均仅精确引用；不复制141条blob索引、逐文件ledger、完整source或大输入。ledger30天、摘要180天复核；恢复链的保留期限仍须由owner管理。

没有CK3/native/business新验收、MAIN/Git修改或自动GC部署事实。旧RED原记录不变。
