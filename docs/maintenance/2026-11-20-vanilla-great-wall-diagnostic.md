# Florin 纯原版 Great Wall 对照

machine_id: `desktop-3fevhd2-1c74096080`。2026-11-19 UTC／11月20日上海时间；实际1.21.0.3 Florin/build26785313，EXE114758264B、SHA256 `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。

公共零mod分支在来源HEAD `530dc59fd0a2c3a15e5283abfcf2e2cd00365400`执行独立cold profile，四份精确普通配置及空`dlc_load`，无产品、夹具、warm缓存、debug参数或DLL。实际菜单显示checksum e02c且无修改标记；与AUB相同1066书签人物罗贝尔／阿普利亚，到1066-09-15暂停世界后正常退出，零自然日／零SAVE。它是独立随机世界，不是AUB同一存档或相同随机种子，历史号1128不冒充Native动态角色ID。

实际原Popen21204于21:33:47.802979Z返回0，原session16980已消费exit0；退出自动保存未勾，无WM_CLOSE／timeout／强杀。keeper无故障退出、CAS10738释放。公共verify实际退出0，diagnostic与case完成；业务、产品发布、Native及baseline_error_waiver均false。[完整对照审阅](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/vanilla-r02-diagnostic-review.json)、[最终闭场](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/vanilla-r02-close.json)。

原版启动前世界阶段已产生完整1005B Great Wall诊断，与AUB R26相同的Expected11／found8、`great_wall_china_gate.txt` near17。只在分析内存中各移除首10字节`[HH:MM:SS]`后，余下995字节整条message逐字节相同，SHA256 `13f1a4ce22737f3bc8041e60d761510e2d02942359365aefad2590e957f6b414`；两个完整原文件未改、未过滤，原版raw SHA为`40cd0a6b773b7a90525fd2c0a6b5056a1b3a3c228a8bd673a2a8ba9ade9d04b0`。这证明该诊断可在无mod启动重现，不把其他产品的新诊断或整产品验收自动豁免，也不宣称raw日志零错误。此前967B安装文件与本地depot清单一致的来源事实见[AUB记录](2026-11-20-aub-gui-reentry.md)。

初次本机配置用未注册的runtime键，在分配前失败；后继一个未启动态分配也已正常CAS释放并保留NOT_RUN。正式R0002重新公共prepare，精确绑定修正后products，未修改旧prepared或复用编号。资源a02补计旧未启动分配及两state小文件20480B，原a01不改，260MiB cap结论不变。

本场4168个可重建shader按五批精确退休，分配192101776B、零失败；源码、所有完整日志、配置源和实际画面保留，旧shader路径不可再读取。pending／result各用`storage_short_commit`固定短CAS，最大锁持有0.0072555秒，所有hash、句柄、删除在共享锁外，未复用旧broad-lock executor。[实际清单汇总](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/vanilla-r02-shader-short-cas.json)。整卷净增188895232B，小于单项分配回收量；差额不归给未知writer。Game260MiB与闭场12MiB未来已闭0。

## 保全压缩与旧清单纠正

已闭自有Java target的2364个class原位NTFS压缩，分配57769984→32960512B，实际省24809472B；11个已知旧Native DLL／LIB为251396096→106483712B，实际省144912384B。逐文件前后字节SHA、FileID、creation/write均相同，compression属性明确变化；无删除、源码／SDK内容或主工作区index/config修改。两者合计169721856B（约161.9MiB），不将整卷变化都归它们。[Java](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/closed-java-targets-ntfs-compression.json)、[Native](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/retained-native-outputs-ntfs-compression.json)。原未来2MiB／160MiB均已关闭，后继容量只用fresh free，不把历史节省再次相加。

旧归档中October超人R2/R5/R7的11284条shader路径，当前全部已不存在。首个清理尝试在planned0／deleted0就被守卫拒绝，本轮未退休这些文件，也不知道何时或由谁移除，不能把归档中的约444MB当作现存容量或本轮回收量。该失败结果通用`historical_deleted_paths_unreadable=true`字段不适用，已追加明确纠正，原件不改。[现状核对与纠正](evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/historical-shader-inventory-stale-correction.json)。
