# R0140 当前原生机制研究保全（2026-10-01）

本轮结论为 **RED：第一次角色 UI 准入失败，未推进日期，六项证据继续未闭合**。

实际运行绑定 clean private commit `0bb40ba1495c4bb15f24e152799d1f62eb1a2420`、DLL `405040213C99F1FBC73AC2C9236EDBED7E2DD416289F87431D687FB366D167D3`（3,551,232 bytes）、PID 832。桌面 run 为 `desktop-3fevhd2-1c74096080--vanilla--R0140`，原生 episode 为 `native-29829-5abfe990ef98`；二者没有互换。actor 29829 / War 4 / Army 18 / Combat 16777218 / victim 33437 / killer 34120。

加载后保持暂停 `date_raw=53146848`（原版日期12/29）。monitor BEGIN 与额外 pre-UI 保存完成；唯一一次 `ck3_open_character_window_v1(character_id=33437, expected_revision=5)` 在 MCP journal 第397行失败：`native UI binding mismatch: date_raw`。计划中的 `53146872` 是目标次日，未作为本轮后态读数。

当次失败回执原 heartbeat 明示 owner/current thread 13000、RNG owner 0、TLS initialized/marker 1、7396 consecutive paused-owner epochs。错误 UI RNG-owner 准入会早退并留下默认结果日期0，这是 **实际 stamp + 精确源码推断**。当次原 parsed native UI command_result 没有被保全，不能将推断的 `owner_fresh_snapshot_admission_failed` 或日期0称作 wire 回读证据；原外层 MCP 错误本身已经原样保全。

monitor 已实际 drain/卸载，SDK owner job exit0，游戏清理回执 `cleanup_proven=true/tree_gone=true`、最终子进程数0。该受管停止的 CK3 termination code 为1，不能改写为游戏正常 exit0。显示实际恢复1024×768，CAS screen release返回0。清理成功只说明生命周期收尾，不是研究GREEN。

被动 monitor 本轮没有实际 writer 或 house-call 证据；victim 33437的原 getter初始读数不能外推到killer 34120。arm元数据不等于角色变量初值；预arm的七定义不等于七个事件实际执行。旧同线程投影门失败与原记录保留，后续修复不会改写本轮结果。

仍待完成：骑士次日角色界面、骑士名单变化、完整战斗窗、骑士选择器、本次受害者唯一实际死亡执行路径、本案13域完整可变状态链。`global_mutable_bundle_complete=false`。R0139/R0127历史原件保持原样，不填补R0140没有观察到的字段。

后续 private commit `fda53e7b3e83053f235be3d5725a6238b89db9f0` 属于采样修复及离线验证，下一次全新冻结 DLL / 实机 attempt 才能提供新的角色、窗口或机制证据。其 UI/monitor source freeze、负例与根 commit/check-out 回执已单独分类为 pending-live；它不是R0140实际源码，不使R0140变GREEN。

保全文件：[5891项全资产索引](R0140-current-research-originals/all-assets-index-a01.json)、[696项精确复制核验](R0140-current-research-originals/copy-verification-a01.json)、[来源绑定事实](R0140-current-research-originals/derived-facts/R0140-actual-facts-a01.json)、[本轮汇总](current-native-research-R0140.json)。2 MiB以下合理过程文件与原PNG采用原字节复制并校验；大save/大图/编译文件/游戏缓存仅登记永久外置路径+bytes/SHA，无裁切或替代。所有新文件均create-only；旧素材、视频config/composer/字幕/素材以及frozen source均未修改，未render/export/upload/signoff，未执行Git或master intake。
