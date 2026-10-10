# 2026-10-10 Source16 冻结及旧执行副本回收追加

本记录追加到既有 R61/R62/无损压缩记录，不覆盖原时点或旧 pin。策略 1.0.0；仅本机 C 卷，total 511,776,722,944 B，项目 quota 51,177,672,294 B，已纳入两个 MAIN linked worktrees；其他 owner 未归属根仍 null、未清理。

Source10–12 仅旧完整索引与 Source15 relative_path/bytes/既有 SHA 相同的单链接文件获退役。12 个实际批次共删除 8,002 files，释放 actual AllocationSize **254,754,816 B**。每批最多 1,000 indexed metadata 候选，所有批次 failures=[]；Source10 多硬链接路径保留。剩余 8,702 indexed same rows 仅 logical 26,171,366 B、actual allocation=null，因小文件审计成本和不足补容量停止，未扩大根。6901/6901/6900 整组数不是删除数。

- `old-source10-12-a164-b01-actual-98.json`: 1664 B / SHA-256 `8fa3a3dbb552182df1bd2de5d2cde259d9d282383c3f1b93c0c202f324673917`；actual 133779456 B / 667 files。
- `old-source10-12-a164-b02-actual-98.json`: 1661 B / SHA-256 `6195ed116f5e25a35714e3af30add4fcb6f72ccdc3feb0464a1519cdd9fb5dc7`；actual 22884352 B / 667 files。
- `old-source10-12-a164-b03-actual-98.json`: 1661 B / SHA-256 `a3d5ad417d7e10b1426ba4ad3882468ef10b20e1328285a59de47aec0a46a4a5`；actual 17285120 B / 666 files。
- `old-source10-12-a164-b04-actual-98.json`: 1661 B / SHA-256 `6041c6f3e472c459b87ab39b9f19cda08d63c21e9130974dfdb93d48b1cfcf2e`；actual 14233600 B / 667 files。
- `old-source10-12-a164-b05-actual-98.json`: 1661 B / SHA-256 `7fbe91385997e49b70e9a36118f0fe7a2fd4fd017116304f5b1c8608911d8754`；actual 12267520 B / 667 files。
- `old-source10-12-a164-b06r-actual-98.json`: 1662 B / SHA-256 `321d113b37d8032d1277b13da091a430c059c185f4663c147fd559f7e95c7551`；actual 10911744 B / 666 files。
- `old-source10-12-a164-b07-actual-98.json`: 1658 B / SHA-256 `ef5deb5ca189e59204161e1ed0fd7e9ac4bec502082d92bce725a0ffb4ba9a01`；actual 9105408 B / 667 files。
- `old-source10-12-a164-b08-actual-98.json`: 1658 B / SHA-256 `d958cb1a6dbcb44d0471616ce339b25c28e4b85c8499487ca631a02b5b292368`；actual 8196096 B / 667 files。
- `old-source10-12-a164-b09-actual-98.json`: 1658 B / SHA-256 `9316d2d7bf84d872d2d960259f58fe9771578f51be64ad775c084aed2cea47f6`；actual 8183808 B / 666 files。
- `old-source10-12-a164-b10-actual-98.json`: 1659 B / SHA-256 `a4f7f88faf55d8e8df5d9f60cd97f87c82a38e35d1d3ceaaf1aa3a99a007e610`；actual 6971392 B / 667 files。
- `old-source10-12-a164-b11-actual-98.json`: 1659 B / SHA-256 `fe63e74026e2fbbe8695f620e9988191ef3fbf4c79baec426cb4c0591ea351c9`；actual 5464064 B / 667 files。
- `old-source10-12-a164-b12-actual-98.json`: 1659 B / SHA-256 `24d9e0f0b1e725faed4616a046c7bb23da0dbcbadee636f8b6b6f73e8c57672d`；actual 5472256 B / 668 files。

Root 之后仅续授权已退休 Source13 中 indexed same rows 的必要大项。`old-source13-a164-actual-105.json` 1861 B / SHA-256 `229fc5b036682e18bf014285ab511b57cda7f7d76d577123e94d5f7a397a2c9a`：本轮 1,000 files、actual **54,792,192 B**、failures=[]。此前原 19 files /32,649,216 B 已明确排除，不重复计入。本轮旧副本净删除分配合计 **309,547,008 B /9,002 files**。

累计真实删除 **31,391,902,648 B /588,341 files**；该累计不包含 NTFS 无损压缩收益，不把 logical/path sums 或 volume-free delta 当实际回收。每项核绝对路径边界、无 reparse、原生 FileID/volume/size/mtime/nlink、当前 consumer 与 writer、独占 HANDLE；journal-before-delete + fsync 后删除，关闭 HANDLE 后确认路径不存在。Source15 counterpart 可读且索引不变；全部 changed/old-only、旧 indexes/manifests、原 logs/FAIL/证据与 selected14/15/16/native27db/DLL/injector 保留。退休旧树不再宣称原绝对路径可直接执行；在新根按旧 index 从 Source15 同字节行加保留差异行重建，历史原引用不改。

Source16 仅一次 6905 inherited hardlinks + 独立新 host；实际 producer 7.9240059 s/children=[]，新独立 logical 3,362,269 B，继承 path logical 130,408,504 B。实际 AllocationSize=null，不把硬链接 path sum 当新增物理占用。冻结100匹配 close SHA `5d9d9b7ce1dd1eb7c2daa6126a0561d1f25b3591dd854fefefb16d735c190ff1`，full **16 MiB** 保守入 usage 一次，活动 reservation 已释放。旧 b06 counterpart nlink 因本次合法继承 +1，FileID/volume/size/mtime/allocation 不变；原 b06 plan 保留，b06r 只刷新这666行 metadata 后实际执行，未绕过独占验证。

四 unused siblings28 原 Root 小池 256 KiB 已 closed；两次 publicprepare29 各仅一次 exit0/children0，logical 2,184,904 B，实际 AllocationSize=null，独立 full **4 MiB** 保守入 usage 一次且活动 reservation 已释放。未启动 CK3 或重新 native build。

本轮 cleanup audit cap 由 Root 有界批准为 actual **80 MiB**、logical **304 MiB**，旧已写计入且不 reset。本文生成前实际 audit 75723528 B，logical 295401509 B；明细保留30d后归纳清理，薄摘要/availability180d复核，不无限保存。审计不计成回收收益。

PAM+ a164 新鲜准入：`C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\pamplus-a164-source16-after-a163-02-reservation-52.json` 18617 B / SHA-256 `3420152f29bd1cdb106b15547f0e0537c2eefe6272a9e32ee5d428defbf42f1a`。MAIN `b57d4ee9cf10306af0ea40b04bc49e514376f73c` clean，Source16 runtime a3cd2dc5、manifest47866，prepared30372/8580a387；available **30075432960 B >= 30071062528 B** = peak2GiB + other6MiB + unmanaged system/application reserve6GiB + safety20GiB，headroom **4370432 B**。current_project_usage conservative upper **35523298424 B**；quota仍满足。System6GiB覆盖非受管系统/应用规划增长，包括外部Paseo fetch，其实际 remaining=null，不伪填0或加成未知受管reservation。

容量准入只允许这一场，不能写成业务 PASS。实际前后 volume-free 变化含同时的独立冻结/prepare/审计与未知外部增长；不把残差归因到本任务。新场结束须原 POST/allocator/keeper/CAS 全闭后重新预算，不沿用本场2GiB credit。

## R63实际闭场后的追加

R63/a164于11:01:02Z真实CLOSED后才释放原2GiB活动reservation，原allocator实际0、keeper0、CAS8321 done/resources[]及三项closure均成立。仅清本场已关闭profile的可再生cache：3780 files、actual AllocationSize **157999920 B**、failures=[]；`C04-reclaim-a164-01-summary-23.json` 2420 B / SHA-256 `ab2855d0ccb55eb1476c42e48b344caf3165e7be0d864f4d549f662a44915dc2`。累计actual deletion **31549902568 B /592121 files**。另文本无损压缩1 success/5 already-compressed skip/0 fail，actual gain **1474560 B**，与删除分开统计；`a164-closed-text-compression-05.json` 1396 B / SHA-256 `54edd3a7c8ee8e95779feabc5aaf04790a419b2cd77bd3e1b2a7cd78868819a9`。两件原回执均位于`C:/workspace/disk-cleanup-20261010/resume-05/`。原FAIL、输入及证据未删。

新merit a165 fresh检查：available **29753810944 B**，required仍 **30071062528 B**，真实缺 **317251584 B**；quota upper35632592272 B仍满足。`storage-coordinator/merit-a165-source16-after-a164-01-capacity-blocked-52.json` 3068 B / SHA-256 `0d23f8cff890cb2fbdefa96ce46bdf0a2b52f1e5eebc8fe3ff88994195830963`。未allocate，不沿用上场credit或降低门槛。

a164预约free30075432960到release29597683712减少477749248 B；三个指定闭场根allocation pathsum上界267261000 B，两者差210488248 B未归因。free delta受其他系统应用及未涵盖输出影响，不伪指某个进程，也不据此声称本场cache/压缩没有执行。旧Source10–13小批回收已停止，剩余logical候选不能当已释放actual；后继只审有依据的大额闭场候选。

## 19:22 CST：已知派生大项及早期cache定点退役

先清2份旧git archive及10个wrong-flags拒绝对象：actual **157409280 B /12 files**、failures=[]；精确commit已cat-file可读，提取源码/producer/index/27db DLL/正确对象/原FAIL保留。`known-large-derived-12-actual-113.json` 1098 B / SHA-256 `473c398df1c6363cc343e3911b7981dbda82e6f821f48ec3f867df3b088fb7f3`。原plan11460 B / `daaf797466d446c0ddce1db5a76d8c9e73ce2879b2b9f63ddbe66e5f202df0ee`，不重复计算前轮已清大lib。

Root随后以当前owner身份明确退役C01早期vanilla与remove-mandala两个R0001/userdir/shadercache及Vivhite旧索引中1822个识别cache；[精确决定](C:/workspace/ck3-upgrade-20261010/root-resume-05/retire_original_generated_cache_04.md)只作用生成缓存。其历史CLOSED仍未知，不补造资源或业务信用；当前sole operator无CK3/lease，后继只用Source16及新state。所有非cache profile、save、input、logs和证据保留，11个异常0字节tmp排除。

三个旧cache实际 **189745728 B /9302 files**、failures=[]；`retired-original-cache-114-summary.json` 14866 B / SHA-256 `014a50f8dae817cf087285c608abd1e8615628c3df3fdac89c2f182f9587fc16`。两轮合计actual **347155008 B /9314 files**；累计actual删除 **31897057576 B /601435 files**，压缩收益另列。上述回执均在`C:/workspace/disk-cleanup-20261010/resume-05/`，无新全盘扫描或大件重hash。

实际free **30093332480 B**，高于原scene门槛30071062528 B共22269952 B；该观察尚不是reservation。原cache回收期间volume仅增加183648256 B，较actual少6097472 B，残差未归因。audit实际77175736 B<83886080 B，logical301192208 B<318767104 B，未reset。新clean MAIN发布后仅一次fresh原子准入merit，不再扩扫清候选。
