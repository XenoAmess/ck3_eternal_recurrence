# R0141 原生机制研究失败实机保全（2026-10-01）

本轮为 **RED：第一次角色 UI 被原生 modal 准入拒绝，未推进日期，六项继续 pending**。SDK 与进程收尾成功不代表机制或界面验收成功。

实际绑定 private commit `fda53e7b3e83053f235be3d5725a6238b89db9f0`、DLL `1B3AC08147D86D34D69390331D2AD7C486B64C07D4F795E10DA4A3E5DE2CE324`（3,553,792 bytes）、PID6320。desktop run `desktop-3fevhd2-1c74096080--vanilla--R0141` 与 native episode `native-29829-08fa9723ff63` 分别保全；actor29829 / War4 / Army18 / Combat16777218 / victim33437 / killer34120。

暂停日期始终为 `53146848`（12/29）；目标 `53146872` 没有采到。monitor BEGIN 和额外 pre-UI checkpoint 已保存，immutable SHA `AE6D79341BA5DA19427AC490C03140E4A71BD8C025A743442855AAF69C6C27C9`；它不是主 before 样本。本轮没有主 before/after pair、没有 +24，也没有实际 nextday 角色、名单、完整战斗窗或 hover 画面。

唯一一次 `ck3_open_character_window_v1(character_id=33437, expected_revision=5)` 位于原 journal 第359行。MCP `is_error=false/CALL_COMPLETED`，实际原生 `accepted=false/available=false/dispatch_invoked=false`，原始原因 `modal_context_blocks_navigation`。本次原 parsed command_result 已完整保全，SHA `32774778FDCC8E8E1FA510CA4D87029756F1FFDEC69B365E5B4A2C96B5AFD765`；parsed JSON 不称为 pipe wire bytes。actual date/thread/GUI owner 门已真实通过，RNG owner0 是诊断而非拒绝门。

之后只读 PID6320 的双次 RPM 命中同一原 GUI context/owner，读到 count1 与隐藏的 `JominiMultiplayerEndPreparationConfirmation`（原 D0=B8、effective-hidden bit08 set）。失败当刻 native return 没有 count/vector 字段；后来 RPM **不能冒充失败调用当刻原始 count**。原版 ShortcutManager `0x36E1C70..0x36E1CA6` 倒扫 effective-hidden，而本轮旧源码只看 count!=0，二者构成有据的原因推断。新修复保留所有 owner/paused/date/fullID/actor/context 门，任何有效可见 receiver 仍拒绝，全隐藏才允许；4源只经实际3Release TU、native fixture/CTest与24Python离线验收，SOURCE READY SHA `BED9386BAD72A03160BBDFC2BCA0C6B4268BC8C3274580EACEBA6A6018FC334F`。后续 source-progress 不属于本轮 source/DLL/实机，不改写本轮 RED。

被动 monitor 已实际 drain、flags0、detours_uninstalled=true，4条记录保留。预arm七个 death_management 定义不等于实际执行，也不证明本次唯一死亡路径。SDK job exit0、进程树 cleanup_proven/tree_gone=true，受管 CK3 termination code1 原样保留。root直接审阅恢复原图，native readback逐字段匹配原模式1024×768；新恢复任务 done seq3428/resources[]，旧 expired task waiting seq3426/resources[]。

六项仍为：骑士次日角色界面、骑士名单变化、完整战斗窗、骑士选择器、本次受害者唯一实际死亡执行路径、本案13域完整可变状态链。`global_mutable_bundle_complete=false`。C08 AST/mock 用例与骑士准备回执仅证明离线/准备合同，actual run verifiers 均 NOT_RUN，不能补本轮机制字段。

[全资产索引](R0141-current-research-originals/all-assets-index-a01.json)保全6024项原件完整路径/bytes/SHA；842项合理小文件以二进制原样复制并重新比较 original/current SHA，大文件与编译/缓存仍永久外置，PNG不裁切替代。新目录 scoped `.gitattributes` 禁止原始字节被Git换行归一化；canonical index/blob检查由根授权提交者继续。本归档未改旧证据、a04/a07、视频配置/素材/字幕，未render/export/upload/signoff，也未操作Git或master。
