# 二期实机启动阻点（2026-09-03）

这不是宣传片脚本或二期 mod 内容错误，而是当前 CK3 启动环境的最小复现问题。

## 已复现事实

| 运行 | 桥接 / mod | 结果 |
|---|---|---|
| Default 桌面最小启动 | 无桥、无 mod | 约 1.3 秒后 `C0000005 @ ck3+0x1DABD89` |
| Default 桌面二期 seed runner | 无启动保护桥 | 同一 `0x1DABD89`，loader/database 尚未出现 |
| Default 桌面二期 seed runner | 四项启动保护 + Cold-Map 只读 observer | 越过上一地址后在 `ck3+0x3BE33A9`（`VFSOpen ` 冷启动错误分支）退出 |
| Sandbox 桌面二期 seed runner | 无桥 | 协议/截图门禁在启动前 typed RED；未产生素材 |

所有运行的进程树均已清理；crash dump、exception、session cleanup 和 relay JSON 保存在
`Z:\\ck3_mod_rewrite\\_runtime\\phase2-seed-20260903\\`。当前真实 footage 仍为 `0/8`，两个目标 MP4 均不存在。

## 解锁动作

1. 在能稳定启动同一 CK3 `1.19.0.6`（EXE SHA-256
   `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`）的正常 Windows 交互桌面上，先做无 mod/no-bridge 最小启动。
2. 最小启动稳定后，原样执行 `run_zg361_phase2_seed_capture.py`，生成新的 canonical seed；旧 seed 合同禁止直接提升。
3. 新 seed 通过 paused/map-ready、PID/generation、事件和 save-checkpoint 校验后，再执行八段 clean capture 和只读 footage intake。
4. intake 完成后再次核对宣传工具 fresh clone（当前已冻结 `origin/main`=`57c42fca13ea459432c1caf76e069a1fbccf602c`），才允许启动两版 TTS、字幕、渲染、审阅和导出。

## 交付口径

两个版本仍是同等优先级的独立最终交付：人物版和制度群像版各自拥有配置、旁白、字幕、候选、审阅、导出和 SHA-256。当前不能给出“已成片”或固定日历时间；从实机启动恢复并取得 8/8 素材后，采集与 intake 约需 `20–40` 分钟，之后每版候选制作约 `45–90` 分钟，另加两轮真人审阅。

## Steam/安装路径判别（06:18）

为区分“绕过 Steam”与“游戏副本路径”两类原因，又用 Steam 库中的原始安装路径
`Z:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe` 做了无 mod、无 bridge、隔离
userdir 的裸启动。该副本与项目参考副本的 EXE SHA-256 相同，仍在约 1.3 秒后以
`C0000005 @ ck3+0x1DABD89` 崩溃；异常与 minidump 保存在
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\steam-library-bare-01\crashes\`。

因此当前证据已排除“仅因使用项目副本”这一解释；根因仍位于 CK3 启动环境/二进制加载边界，尚未进入 mod loader 或数据库初始化。

## GDPR 参数判别（06:20）

又按 Steam 历史实际命令行补上 `-gdpr-compliant`，使用同一 Steam 库 EXE、`-nographics` 和全新隔离
userdir 启动。参数拼接已在第二次尝试中校正为单一 `-userdir=<path>` 参数；结果仍约 1 秒后
`C0000005 @ ck3+0x1DABD89`。对应 exception/minidump 位于
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\gdpr-bare-02\crashes\`。

这排除了“缺少 GDPR 同意参数”作为当前早期崩溃的解释；仍未进入 mod loader、seed 或数据库初始化。

## cwd 判别与转储指令（06:26）

最后做了一次工作目录对照：使用同一 Steam 库 EXE、`-gdpr-compliant`、`-nographics`，但将 cwd 从
`binaries` 改为 Steam 常规的游戏根目录。仍在约 0.8 秒后以 `C0000005 @ ck3+0x1DABD89` 退出，
证据在 `Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\rootcwd-bare-01\crashes\`。

对 minidump 的离线反汇编显示故障指令为 CK3 自身 `.text+0x1DABD89` 的
`movsxd rdi, dword ptr [r14+0x4c]`；异常线程的 `r14` 是小的无效值（本次 `0x7d8`），表明是
游戏内部早期对象/表尚未有效初始化。该证据不指向项目 bridge 或 mod 文件，也不授权修改游戏二进制。

## 图形后端判别（06:31）

使用 Steam 库原始 EXE、游戏根目录 cwd、`-gdpr-compliant`、`-renderer=opengl` 与 `-nographics` 做了最后一次图形路径对照。
结果仍约 1 秒后 `C0000005 @ ck3+0x1DABD89`；exception/minidump 保存在
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\opengl-bare-01\crashes\`。
至此 D3D11、nographics、OpenGL、cwd、GDPR 和安装副本差异均未改变故障地址；启动参数试错收口，下一次启动只在外部桌面或 CK3 安装状态发生真实变化后进行。

## Steam `-applaunch` 入口判别（06:44）

通过当前已运行的 Steam 客户端执行了一次隔离 `-applaunch 1158310`，仍使用历史用户目录的可写副本、`-gdpr-compliant` 和 `-nographics`，未加载 Mod，也未进行任何购买或商店操作。Steam launcher 正常退出，但 20 秒内没有 CK3 子进程，也没有生成新的 crash artifact；因此该入口没有提供可用游戏会话，双片素材仍为 `0/8`。这不改变前述裸启动崩溃结论，后续不再重复同一 Steam 入口试错。

## 历史用户目录副本判别（06:42）

为排除“空 isolated userdir 初始化”因素，将已知有历史运行记录的 `C:\Users\xenoa\Documents\Paradox Interactive\Crusader Kings III` 复制到
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\userdir-cloned-history-01`，原目录未改动；随后使用 Steam 库原始 EXE、`-gdpr-compliant` 与 `-nographics` 做无 Mod 裸启动。进程约 1.16 秒后仍以
`C0000005 @ ck3+0x1DABD89` 退出，崩溃工件位于该隔离目录的 `crashes\ck3_20260903_064242\`。历史配置/缓存副本没有改变故障地址，因此不能把问题归因于空用户目录；在外部桌面或安装状态改变前，不再重复同类 userdir 复制试验。
