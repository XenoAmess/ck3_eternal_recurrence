# R219 缺失 keeper report 的异常前驱资源准入

`machine_id: desktop-3fevhd2-1c74096080`。2026-10-20T02:31:56–02:31:57Z 按[休假交接](../handover/2026-10-20-war-episode04-vacation-handover.md)及原始小文件读回 R219 / `desktop-3fevhd2-1c74096080--vanilla--R0215`：keeper 最终 `report.json`、原 parent exit 回执确实缺失；host 原始 Popen wait 为 0，原 `normal-close-result.json` 仍为 `normal_close_qualified=false`。本轮没有补造 keeper report、`thread_exited` 或 CK3 OS 退出码；host 0 不授予正常闭场资格。

[公共 allocate](../../tools/ck3_mod_acceptance_allocate.py) 复用既有 `ck3-mod-acceptance-failed-live-resource-closure-v1`，新增明确的 `closure_kind=expired-keeper-missing-final-report` 分支。该分支核原 frozen/READY/prepared、host wait、keeper 和 CK3 原身份、交接来源 SHA；从原 keeper 指向的 canonical bus 精确核事件 **7124→7127**、过期时长、`waiting`/空 resources 和 `retirement.business_status=unresolved_red`，随后检查当前原进程身份、runtime/controllers、屏幕 owner 及 PID/unsafe/watchdog controls 均已缺席。新场仍走原有本机身份、最新前驱、冷输入、存储和屏幕准入。

结果仅为 `previous-shared-failed-live-expired-keeper-resource-closed`。回执保持 `original_keeper_wait_proven=false`、`keeper_thread_exit_proven=false`、`original_ck3_exit_code=null`、`native_cleanup_qualified=null`，正常闭场、typed exit、业务和发布资格全部 false。现存 keeper report 不能借该分支绕过；其他前驱仍使用原路径。没有启动游戏、相机、屏幕或 keeper，没有重读／重哈希大 native report、存档。

- [真实缺失复现与当前进程读回](evidence/episode04-r219-abnormal-predecessor-20261020/actual-validation.json)：原无条件读 keeper report 抛 `FileNotFoundError`；候选核真实资源闭合通过。
- [实际 CLI 输入](evidence/episode04-r219-abnormal-predecessor-20261020/actual-inputs.json)、[资源闭合输入](evidence/episode04-r219-abnormal-predecessor-20261020/failed-live-resource-closure.json)、[canonical release](evidence/episode04-r219-abnormal-predecessor-20261020/screen-release-canonical.json)：沿用四个既有 `--previous-*` 参数；原件路径、大小、SHA 均已固定。归档副本保留原始路径绑定，执行时按实际 CLI 输入消费并重新读取现场。
- [focused tests](evidence/episode04-r219-abnormal-predecessor-20261020/focused-tests.json)：28/28，含新增 13 项、既有 failed-resource 10 项、pre-READY 5 项；覆盖 public `allocate_and_keep` 真实路由、错误 task/sequence、canonical 篡改、活跃进程／screen、残留 controls 和负资格。该测试只使用夹具。
- [精确应用回执](evidence/episode04-r219-abnormal-predecessor-20261020/integration.json)：2026-10-20T02:34:54Z、HEAD `8e9642adceb686e0457b3cb866ab5c3c9436040f` 基线检查后，将已验候选及测试逐字节应用主树；源码 SHA `c69937b6595d6b63a63626e2e31dff2189cdd18a1b2ad5bf76047d09d74c9cd5`，未重复无变化测试，native tree 未改。

上述进程、路径和机器状态只属于所标机器和观察时刻。外置小输入是下一次分配的活跃前置；新场分配成功后复核，最迟于 2026-10-27T02:34:54Z 按通用存储策略复核；本次未删除资产。
