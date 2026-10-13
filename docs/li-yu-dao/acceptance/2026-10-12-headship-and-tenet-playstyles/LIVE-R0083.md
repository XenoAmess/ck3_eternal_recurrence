# R0083：白沙选项与 T35 付费已执行，原时限和正常退出均 RED

2026-10-13 至 2026-10-14（北京时间），R0083 使用源码 `2d27096c9879f88c52fef0e94a3a6158cc2f6296` 和 CK3 1.20.0.4。正式 83 文件 manifest SHA-256 为 `c3c8a398ff97c9b1af360b642bf235a973020be6613bceb7de196eae616cb1bc`，ZIP SHA-256 为 `89a46e81149c6619628ca61025a9bdb9da94cd91976efb6e89e35d82a390636b`。实际 profile 与正式构建逐字节相同，启动标记出现一次，无 LYD 范围引擎解析错误。首个基线 ROOT 检查点按时 complete：实际玩家31254为原版 `confucian_faith` Faith31、当前礼仪32、主礼仪33；游戏“经学”面板可见信仰领袖“无”。这部分取得实机信用。

ROOT 通过游戏决议确认“入儒门，习经礼”，按当前原生事件 `lyd.1` 选择唯一选项；再确认“择师问道”，实际翻过 `lyd.10`、`lyd.11`、`lyd.12`，在 `lyd.13` 选择显示为“白沙之学”的原生选项2。此处有决议、事件画面和原生选择回执，**未在选择后单独读回当前礼仪 ID**，不能把该项记为完整后验。随后“静坐求得”正式决议产生 `lyd.1034`，选择付费原生选项0；实际 GUI 威望2200→2050，符合150费用。第二项“授业传经”导航因原准备阶段只余不足300秒、总保留不足900秒被适配器拒绝，未确认或付费。学识、在世廷臣、各活跃礼仪候选、议案、代表、投票、签署、宗主实施及政治保护均未完成。

本轮 **business_pass=false**。准备阶段固定期限于 `2026-10-13T15:53:22.452150Z` 左右触发 `TimeoutError: Original normal Quit reserve reached; pending Root phase remains GAP`。ROOT 的第13检查点 partial 回执在期限后才写入，不能追认为按时完成。原 normal-quit 请求已生成，但 ROOT 未在原 host 保留截止 `2026-10-13T16:26:35.254699Z` 前提交已取消自动存档的最终映射点击。该时刻 retained handle 未发信号，`normal-close-result.json` 的 `normal_close_qualified=false`，无 OS0 或 native 清理信用。之后 CK3 在 `16:38:02Z` 的桌面采样中已不存在；**退出原因未知**，不能据此称为正常 GUI Quit。ROOT 当时已打开退出对话框，但自动存档仍被勾选；随后一次过期截图点击被坐标守卫拒绝，未执行最终退出点击。

keeper 收到 STOP 并退出0；桌面实际恢复1024×768。`16:49:26Z` 原始桌面截图显示 Steam“离线模式”且无 CK3。屏幕独占在 `17:09:08Z` CAS 5613→5614 释放；由于租约已过期，回执明确为 `expired-own-claim-released`，业务状态 unresolved_red。A51 有限存储授权于 `17:16:07.895625Z` 到期，四根在 `17:13:13Z` 前完成保守结算：实际逻辑量544,519,790 B，额外 allowance33,554,432 B，项目 carry **140,998,854,385 B**，未消费峰值归零，低于固定上限141,327,031,211 B；物理卷 free 变化未归因于本轮。存储 coordinator 直到 `17:23:12Z` 才标记 done，晚于授权到期，不能声称所有生命周期收尾均按时。重跑显示恢复脚本时误用输出重定向，截断了原 `display-restore-001.json`；保留此失误，实际1024×768由后续桌面截图与结算时直接读取证明，不伪造原回执。

下次不得以 R0083 的选项提交代替存档后验。优先复用 R0079 已保存的真实资格存档，先验证它与当前候选的加载和状态兼容性，再从代表接受继续；若从新局重来，须缩短逐页人工停顿并让正常退出与存储的时限共同控制，预留足够的退出和结算时间。继续保持 Steam 离线、独占现场、原生选项精确核对及非通过状态；0.1.2 尚未发布，Steam 公开版仍为 0.1.1 Alpha 内部测试。

外置原件：`A51=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-nomination-storage-admission-20261013-051`；`RUN83=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0083`；`CASE034=C:/workspace/ck3-common-runtime/cases/lyd-release012-keypaths-20261013-034`。依[全机器存储策略](../../../storage-retention-policy.md)到期评估，不永久保留原件。

| 关键原件 | SHA-256 |
| --- | --- |
| `A51/BASELINE-PROFILE.actual.json` | `3c2c371cfeac13046bda56e0223614b0a5faecba770cbb90bafcfe48380eafb4` |
| `RUN83/case-output/release012-baseline-0001-root-result.json` | `4301dd1f33107374c7ea3979d9f2ad9b6601bd41113e4dfc93185c7fab1d9a01` |
| `RUN83/case-output/release012-preparation-0008-root-result.json` | `24e7ab1dfbdb307c1fcf0297f5b2eb94dc4751d3f4990d70d11ddc13a5073abf` |
| `RUN83/case-output/release012-preparation-0011-root-result.json` | `98ef9b557745c30ff79092f99a466e7b0adae29669cc0bc31a0132c31cb11096` |
| `RUN83/case-output/case-error-preserved.json` | `3eab808ed3b9edb8f71a327b615caa327c2f8066f376b16936af8b98919a25d7` |
| `RUN83/case-output/normal-close-result.json` | `becb83b35fe4a236a9c71229aed3a54fb53edd3717de1814676dc0b112c8b07e` |
| `A51/CLOSED-RESERVATION.actual.json` | `473845ddf921f906ae6f964f33e0dd846873f5ff3529042a9bbd56f6ca7fd4be` |
