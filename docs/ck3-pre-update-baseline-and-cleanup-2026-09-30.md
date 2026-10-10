# CK3 更新前冻结与清理：2026-09-30 历史摘要

> 2026-10-10 主线整合：恢复来源提交 `5adda4997ac36817ccfccc2484f298ddc465a0c8` 的研究。下文“当前”均指原调查时的构建与样本；没有新增实机验收，也没有把结论外推到 CK3 1.20.0.4。文中外置原始路径是历史定位，本次未重新读取那些原件。

原调查记录的冻结目录为 `artifacts/migrations/2026-09-30/pre-update/`。以下数值仅复述旧报告，不证明今天原件仍可读取；当前保留、到期复核和回收统一遵循 [存储策略](storage-retention-policy.md)。旧一次性清理命令不作为当前入口。

| 项目 | 当时记录 |
|---|---|
| 核心归档 | 约 1.475 GB / 1,036 文件；完整旧游戏复用既存安装，没有再复制本体。 |
| 三份旧 EXE | 都为 95,206,008 bytes，SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；版本 1.19.0.6 / Steam23530548。 |
| 数据指纹 | 每份 15,048 个相关文本文件，所比较范围的新增、删除、变更均为 0；纹理和音频没有做重复审计。 |
| 已执行清理 | 201 个构建目录、12 个单独对象文件、10 个旧 worktree；已知原始大小 7,004,886,880 bytes。另13个权限失败目录没有计入该删除量。 |
| worktree 审阅 | 110 个审阅项中10个删除、100个因源码状态或未合入 HEAD 保留；没有据此删除全部622个登记。 |
| checkpoint | `autoplayer-state/profile/save games/xar_checkpoint.ck3`，66,594,755 bytes / SHA `5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F`；角色29829 / date53175816 / history132。 |
| episode seed | 63,874,889 bytes / SHA `46A753F02AAE87299AD9658DA898F5938C1103B251E1EF56AD29FE38E9EAF53D`；角色29829 / date53168784。 |
| 真实缺口 | `%TEMP%/xar-war-entry-production6b-state` 的67,118,175-byte canary已不存在，没有把另一 checkpoint 伪称该 canary。 |

旧 state 副本的绝对路径仍指向原现场，不是可直接运行的新 profile；恢复须在新 state 重绑并重新观测 session/token，不能重放旧 inbox。旧静态62项源码能力清单也不是新的 live hello。

关键旧索引：`backup-files.json` SHA `114AF76E563B9C5FBD1B71D29FA43CD69C81FEED70703FA0DADBA392C684E7FB`；`cleanup-result.json` SHA `EC622148E0ADC556854B44D13C77F7457B91EA668515A12AC84BA0ADCAAFC59B`；`worktree-cleanup-result.json` SHA `3FDDD4E1D4611CE90D7A4834C3A007A441E263F9AC62AACD80D90534F3E70C6D`。

后续两轮分别见 [根目录清理](z-drive-root-cleanup-2026-09-30.md) 和 [旧 runtime 清理](z-drive-runtime-cleanup-2026-09-30.md)；当时没有启动CK3或新增玩法验收。
