# 2026-10-10 本机容量追加：Source15、R61/R62与无损压缩

此页追加[此前R57/R59记录](storage-retention-2026-10-10-local-capacity-recovery-followup-r57.md)，只计C机器`4号执行者`的实际动作，不与LYD或其他机器回收混计。旧截点和失败原件保留。策略1.0.0、C卷总量511,776,722,944 B、配额51,177,672,294 B不变；其他仓库归属及未知外部增长仍null。

## 构建与冻结实际闭账

native build70首次遗漏父CMAKE_CXX_FLAGS而exit15，原失败保留；同预算/原截止内recovery02成功，21 compile+552 qualified reuse=573 TU，DLL link及10项focused检查通过，406.81秒、children0。DLL9,078,784 B / `27db8da0c740b3334ce661b73d4ef618de87fda24f3b91f705f3b31bef7bfe19`。四根metadata allocation路径上界419,736,344 B含继承硬链接，不能当净增长；配额保守计完整2GiB。build70 closed回执7,476 B / `8ff681f38caae3b87d7067ed5138062418bab7c19afdb3b4786e5d619084974b`。

Source15唯一indexed copy2实际copy8.89秒/总12.07秒，producer0/children0；logical130,642,714 B，AllocationSize未知，保守计完整256MiB。freeze72 closed回执2,788 B / `d37c7a4ba1bf5195a90afade6a7ed7a74294734aac7d557b1b7a02dcc5d5115b`。两项回执位于`C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/`，分别为`native-level-two-targets-after-a161-01-reservation-70-closed.json`及`source15-indexed-copy2-after-build70-01-reservation-72-closed.json`。旧qa12/Source14、native来源和失败输入未改。

随后三个精确清单实际回收：CCC18旧单链接500文件22,986,752 B、R58五张冗余导航PNG15,343,616 B、已退休bad-config单对象9,875,456 B。原生身份、独占HANDLE、删除前journal与删除后缺失均成立；qualified替代对象、原日志、typed pools、代表图及输入保留。对应`old-native18-a162-actual-42.json`、`R58-nav-retired-a162-actual-75.json`、`bad-config-object-a162-actual-77.json`。此截点累计30,731,752,792 B /571,744文件，不含压缩。

## R61与Source13必要回收

R61/a162于09:43:14.316949Z真CLOSED，normal/OS0/native0、allocator9933实际0、keeper0、三closure、CAS8298 done/resources[]；业务仍未通过。[原事实](../ck3-native-ai/shared-acceptance-source15-and-startup-revision.md)中的两相百万差不授整场PASS。三根一次metadata上界414,113,048 B，未超过原2GiB峰值；只清已闭profile生成shadercache3,816文件/161,276,720 B。另五份原文本NTFS无损压缩省2,306,048 B，六份已compressed跳过。

当时下一场仍净缺29,593,600 B。Root明确退休Source13 executable tree，与Source15 relative_path/bytes/既有SHA一致6,901行；五个不同文件、旧index/manifest、原日志与历史绝对引用均保留。仅必要19个单链接重复文件实清32,649,216 B，failures0，无树inventory或正文hash；fresh FileID/volume/size/mtime/reparse/nlink、独占HANDLE、无当前consumer/writer及Source15可读counterpart均核实。旧根不能再声称直接可执行，应在新根以Source15等值行加五个保留差异重建。

实际回执`old-source13-a163-actual-86.json`为1,853 B / `c274967ec01e0732146cfe770dfc375125ef21c0625f5b2b7325987cc9483859`；R61 cache回执`C04-reclaim-a162-01-summary-23.json`为2,421 B / `7e27a98aea96c8bb3eda66a2d3f092aed864d8e9ca2605251def84d17e326e38`。此截点累计30,925,678,728 B /575,579文件。R62之后实际closed、释放与回收见下文，不覆盖这一历史截点。

## R62与四个构建产物无损压缩

R62/a163于10:03:10.184426Z真CLOSED：retained OS0/failure lifecycle、allocator64997实际0、keeper0、三closure、CAS8307 done/resources[]，原run2/verify2、normal=false不变。原POST3,791 B / `77c7aae340cb966431ccb317022affb2e43a3196ebb00fd517084070d6c097e3`；2GiB reservation实际释放，三根metadata上界263,676,504 B。只清其生成cache3,760文件/156,676,912 B，失败0；报告、存档、输入及必要图保留。另一份文本无损压缩省1,269,760 B，五份已compressed跳过。

累计实际删除现为 **31,082,355,640 B /579,339文件**，不含无损压缩或卷free变化。`a163-01-summary-23.json`为2,373 B / `a2d831f63d9d00b80ad1a723860c5f92d7c61ac15e4b805a8e2d36ea023c7b64`。

Root随后明确允许四个已闭构建输出NTFS无损压缩：runtime.lib、bridge.cpp.obj、ck3_12002_adapter.cpp.obj、ck3_12002_semantic_adapter.cpp.obj。四项成功/失败0，actual allocation省 **84,586,496 B**，逻辑正文不变，mtime/FileID/links保持，继承既有SHA；未新增完整正文hash。后两项links5的同一inode压缩影响已在授权范围内。DLL/EXE/source/index与失败证据未改。耗时3.056831秒，卷free只增84,242,432 B，残差344,064 B不擅自归因。

`native-lossless92-four-qualified-actual.json`为5,069 B / `038d1ddd193073e568e2990be5b44d19df286a29fec2868ffb4f63d316169aa0`。另从既有metadata中选50个更早CLOSED文本fresh核identity/COMPRESSED/writer，全部已compressed，0正文hash/0重复压缩/0树扫描；`old-text-compression93-fresh50-metadata.json`为41,075 B / `93dc627ad5b9c2e7b37732b8c71a720f6123af7ecdec508214074f86a54e2b68`。本节回执根均为`C:/workspace/disk-cleanup-20261010/resume-05/`。

## 后继门槛与保留期限

下一独立实机场仍要求 **30,071,062,528 B**：2GiB单场peak+6MiB其他未消费预算+6GiB系统/应用aggregate规划+20GiB安全余量。10:24:04Z fresh free29,802,262,528 B，仍缺268,800,000 B；CK3进程为空、a164未allocate，pagefile logical5,736,935,424 B与mtime稳定，未知卷变化不编造原因。Root Git窗口未关闭，须新clean HEAD及fresh容量准入后才可启动。

目前仅按既有索引审阅旧派生副本及已知旧cache，候选不是已释放。原始来源、原片、失败attempt、配置及必要业务证据继续保留；详细availability/journal按30天到期归纳，薄摘要180天复核，不自动续期，不降低业务合同、Steam离线或容量公式。


Source16冻结、12批旧副本退役及R63真实闭场后的容量记录见[追加](storage-retention-2026-10-10-source16-r63.md)，原时点数据保持历史原样。
