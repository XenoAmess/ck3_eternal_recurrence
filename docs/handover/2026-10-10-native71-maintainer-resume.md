# Native71 接班整合与 R0087 续跑

## 原目录整合结果

用户要求先清理、提交原目录，再接续休假交接；进一步明确所有变更须“合入 master 或删除”，并要求64并发。原目录处于旧 `codex/dynastic-movements-20261005` / `14c13457952ee89da3e6889c29075477584948f3`，与当时 master 历史分叉，不能整支覆盖主线。

最初用 `codex/archive-original-residue-20261010` / `1515c4349e7c26dc38686060c58164314d497928` 临时保全71修改、142删除和27新源文件，共240项；这一步仅为保全，未完成整合。随后64个互不重叠工作包逐项比较原变更与 evolved master，最终 **3 merge / 237 delete / 0 deferred**。协调者统一执行，完整文件级结论与证据在 [逐项结果](2026-10-10-original-residue-resolution.json)。

合入的独有内容是2026-09-01 Kaishek 独立仓库收口日报、W36周报，以及仍被主线R1/R2/R3报告引用但缺失的迁移计划。迁移计划明确历史版本，更新当前授权和Python命令模板。其余残留已被主线接收、后续实现替代或属于一次性脚本，旧副本不再保留为待办。142项Kaishek删除继续符合独立拆仓边界，源残留中已无 master 缺失且待删除的实体文件。归档分支在主线提交和官方CI终态后删除；不保留归档 ref 作为交付。

前置整理记录已推入 master `2a4e7819b3fbeef1d3b05108a8d5493cc5dfc5df`。首次全量切换时因未按约2.59GB树预算检查Z盘而失败；这是执行错误。新检出派生资料曾可逆移动到 `D:/codex-ck3-background-spill/maintainer-resume-20261010/failed-checkout-files/`，不涉及旧原件；最终回收结果另记。当前原目录采用稀疏检出，包含SDK、tools、docs、CI及三套主mod；历史本地产物/嵌套工作树仍按通用存储策略处理，不能把 Git clean 声称为这些历史资产全部物理回收。215条本地精确输出排除规则不替代源码整合。

## R0087 的真实结果

完整ID `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0087`，execution `4112b211-8952-4c52-83e8-17162ee2b06b`。接班恢复输入为6066/H10013/raw53289912和完整12流。SDK clean detached pin、Native71 source/compiled/archive/qualified canonical 均为 `16da78339cdff5c1a462e20bc301684594a3f800`；沿用已资格DLL，不重编、不重跑旧FIRST，也不改写保留的旧物理owner来源。

新鲜Steam窗口已实际审阅“离线模式”，Toast保持禁用。第一次prepare因稀疏检出缺 profile/workshop 传递依赖而RED，未启动游戏；同pin补齐依赖后的attempt02 profile/copy/rebind/preflight全部exit0。新CK3 owned PID115548、Robert29829、原普通战役episode、XARoff。07:15:51Z实机新paused资格 **13/13 GREEN**，无窗口焦点抢占。

现有普通OODA的首次响应及7个后继turn完成查询→规划→操作→观测，实际前进1天并于07:34:56Z成功SAVE。新持久基线 **6067/H10026/raw53289936**，episode `native-29829-2bc2d599f7f9`；checkpoint **104,787,543 B**，SHA-256 **`fffd9e8b35caa8a0af67fa979261c8ccbf1cf8d01d8efe85ebe4a3670cceba0e`**。初始同日期SAVE与冷恢复不增加天数。Sway continue、opinion60、贡献45，未观测terminal；建设receipt查询不等于completed/useful-income闭环。

SDK exit0。stock Desktop点击等待中，协调者提前请求custody stop，Game最终exit1；记 **harness close RED**，没有正常Game退出证明，也未证明native crash根因。owned runner exit0、Game/injector gate为空。完整十流加release/construction supplements **3/3 exit0**，Driver全体复制、不裁剪历史；keeper最后sequence1613后 **CAS1614** 释放。闭场新知识见 [测试流程](../testing-workflow.md)：必须先等待Game独立exit回执，再停止custody。

MCP100%、G2 5/8、NW2 2/4、M4false、M6partial、M7incomplete、自然继承0保持。此次交付增加的是Native71真实冷恢复及1天已保存的production loop证据，不是整代自治完成。

## 证据与接续

本次外置根 `D:/codex-ck3-background-spill/maintainer-resume-20261010/`，关键相对路径：

- `r0087-managed-attempt02/operator/ROOT-R85-COLD-PAUSED-SNAPSHOT-QUALIFIED.json`：真实13项资格。
- `ordinary-one-day-save/BOUNDED-RESULT.json`：1天循环、6067计数及最终SAVE来源。
- `r0087-freeze-metadata/ROOT-ACTUAL-SAVED-CHECKPOINT-BINDING.json`：实际checkpoint字段。
- `SDK-qualify-EXIT.json`、`close-stock-desktop01/ROOT-STOCK-DESKTOP-RESULT.json`、`close-custody01/ROOT-CLOSE-OBSERVATION.json`：分别保存SDKexit0、Gameexit1、custody关闭；不得混为正常退出GREEN。
- `r0087-freeze-execution/ROOT-ACTUAL-COMPLETE-FREEZE-EXECUTION.json`、`SCREEN-KEEPER-STOPPED.json`：完整freeze与CAS释放。

**下一恢复入口**为 `r0087-saved6067-freeze/RECOVERY-INPUT-PACKET.json`，十流回链 `ROOT-SAVED-TEN-STREAM-FREEZE.json`，两份supplements在同freeze目录；必须带全Driver/12流。当前基线限期保护至2026-10-17，下一次接续/存储复核重新按实际用途判定，不无限期保护所有旧副本。继续沿exact16da/Native71资格输入；新的原版观测/策略施工仍先补对应原生树与实机证据。建设下一watch raw53290008只是调度时点，不是完成ETA；优先观察真实completed/material/useful-income，随后推进M6/M7。
