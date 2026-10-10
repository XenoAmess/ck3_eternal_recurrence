# 2026-10-10 本机容量恢复与单场实机准入

本摘要绑定实际原子准入 `C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\admin-a158-reservation-49.json`：4462 B / SHA-256 `8edc765d7ead2920488b9d2abeb8e74478c0c6957bca85862784a258382ede9a`。本机为 `4号执行者`，仅 C: 固定卷；策略版本 `1.0.0`。

## 范围与容量

- 本卷 total **511,776,722,944 B**，准入时实际 free **30,266,368,000 B**；不采用另一机器1TB维护样本。
- 已完整覆盖 canonical仓库、ck3-upgrade-20261001/03–10、本任务已知清理目录及screen anchor；20261002实际不存在。另将经.git/commondir/backlink确证的两个MAIN linked worktree计入预算，均未删除其源码或Git成果。
- 两linked roots：ck3_eternal_recurrence_mcp_upstream_20260923、ck3_generic_log_mcp_20260923，分配上界合计 **1,798,988,544 B**。
- 回收前既有owned分配保守上界60,544,793,112 B，加linked上界，减精确单链实清回执，再保守加64MiB新审计和8MiB新薄产物，当前项目占用上界 **34,274,169,912 B**。原库存硬链接按路径计数，可高估，未冒充实测unique物理占用。
- 有效配额 **51,177,672,294 B**，没有临时超配额。连同本场peak和other预留仍余 **14,747,630,126 B**。
- damengsan_suite、uuii、crusader_kings_3_dev等独立/未知owner根未认领、未删，size/可回收量为null；它们的现占用已体现在卷free，未知大小不记为0。

## 实际回收

| 分类 | 文件数 | logical B | actual AllocationSize释放 B |
| --- | ---: | ---: | ---: |
| 生成shadercache | 429,122 | 16,891,412,796 | 14,807,815,920 |
| 可重建native中间物 | 1,922 | 2,410,164,277 | 1,069,047,808 |
| 退役transport与派生观察导出 | 1,430 | 18,029,092,469 | 9,813,823,488 |
| 过时GUI过程图 | 188 | 419,047,194 | 419,512,320 |
| 同索引逐字节可恢复旧源码副本 | 97,840 | 1,837,874,214 | 2,034,909,680 |
| 合计 | 530,502 | 39,587,590,950 | **28,145,109,216** |

首个真实删除批次前free **2,366,930,944 B**，准入free **30,266,368,000 B**，卷净变化 **27,899,437,056 B**。该净变化不等于上表回收；其中包含新审计/薄产物写入及未知并发变化。残差 **-245,672,160 B**，未知外部增长仍null，未算作回收。

每批最多1000个精确文件；resolved绝对路径/同项目边界、reparse、原用途/后继替代、当前无writer/consumer、原PID身份及native file identity均核验。单链文件经逐项0share独占HANDLE设删除、关闭HANDLE后路径缺失回读；plan和availability逐项对应。多链接源码和未核类别保留，未将逻辑长度当作回收分配量。没有全盘正文hash或全库存复制。

所有原native-report/session、必要业务truth/exit/失败代表、save/config/独有或变化源码均保留。旧RED、非零退出和未完成业务能力原样；旧snapshot/lease缺项未伪造成normal0/三closure。Source14和qa12/s的22项差异继续保持，不宣称能互换。

## 精确预算与预留

```text
30,266,368,000 >= 2,147,483,648 + 8,388,608 + 6,442,450,944 + 21,474,836,480
= 30,073,159,680 B
准入额外余量 = 193,208,320 B
```

- 独占本卷ledger HANDLE内写成单一a158行政任命预留2GiB；原hold1800/reserve90/timeout3000/naturalday0/cmd300/readiness400/.05合同不变。只授权此场，不让merit/ransom/RMTM/361/Workshop共享信用；完全闭场后再释放和分别fresh准入。
- other8MiB为Root4、CI1、disk1、readonly helpers2的保守未消费额度。已闭四小prepare逻辑6,293,125 B，未消费0，不双计。所有活跃cleanup已闭；旧cleanup额外未消费预留释放为0，剩余retention cap不作写入信用。
- system6GiB为owner规划增长预留，依据pagefile5,736,935,424 B额外一份向上取整，不是已发生增长或预测；安全余量20GiB来自本机公式。
- fresh local任务总线有限读500条，无另一个新鲜local live PID writer claim；执行前无CK3/native/Git/media重型writer。未知他owner已占用/并发增长保持null，不使用旧远端记录充当本机预留。

## 审计与保护边界

- 必要plan+journal限额64MiB实际分配、256MiB逻辑；实际 **64,053,712 B / logical254,081,434 B**，已NTFS无损压缩，已经compressed者不重复hash。新审计自身压缩节约单列，未再从原资产回收/项目基线重复扣除。
- 实际审计回执：`C:\workspace\disk-cleanup-20261010\resume-05\final-pre-admin-04-own-audit-compression-27.json` / SHA-256 `e5a43656e05e404960bc40c96201c65312dc03902ea1202cd039ad3b356c2fdc`。
- 保护当前Source14完整materialization/manifest/index、qa12/s/generatedbindings/index10/actual11/qualified fd1f DLL、精确C07 injector、C07workshop/src实际import、QA27-07/08必要正式树/当前prepared/profile/pins、R56下一allocator链、56个历史file-only scopedtruth和R54/55/56必要失败代表。C05未来正式Workshop实际SDK uploader/steam_api64.dll及明确support保留，不扩为整个C05。
- 保护沿各自owner/purpose/next-use精确项登记，最迟2026-10-17复核且不自动续期，不保护整个C10或整个历史场。原56文件清单review为2026-10-17T05:29:58Z。R35原CAS缺项、无法识别cache和未执行候选仍保留，不改变历史事实。
- 精确plan/availability位于 `C:\workspace\disk-cleanup-20261010\resume-05` 下各`*-plan-*`及`*-availability-*.jsonl`，本轮详细记录至少保留至 **2026-11-09T06:13:29.858598+00:00**；薄摘要/删除availability回执保留180天，review **2027-04-08T06:13:29.858598+00:00**。退休路径记为deleted/unavailable，不悄悄重建同名历史证据。
- 完整库存/逐实际回收回执pins汇总：`C:\workspace\disk-cleanup-20261010\resume-05\storage-coordinator\final-before-admin-48-volume-C-checkpoint-30.json` / SHA-256 `c8977b51cc0ddf4c5065c07c6fa2c62ca248445f9f4c9719835c7d512427b195`，其actual_recovery_receipts为上表唯一计量依据。

本文件为外置入库候选，MAIN未改；Root在原场闭合后的Git窗口接收，并依既定rebase规则提交。
