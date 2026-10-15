# 战争四期：本机恢复与 Review02 前置

本记录的 `machine_id` 为 **`desktop-3fevhd2-1c74096080`**，由 `tools/ck3_live_run_id.py machine` 实际取得。2026-10-15 的本轮工作根为 `C:/ck3-e04-resume-20261015-a01/`。以下安装、容量和桌面事实仅属于这台机器；其他机器复用代码与知识时，重新取得自己的身份与实际读回。

## 版本与现场

- 更新前本机仓库为 `9fbeabad1c4435bf16f79b8714e5078885daf5b1`；已通过 fetch/rebase 更新到远端主线。中途磁盘满导致的失败已保留回执，恢复后正常完成，没有 merge 或强推。
- 2026-10-15T06:52:20Z 的本机 skill `inspect` 读到 **CK3 1.20.1 / Steam build25870654 / public**。实际游戏目录为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`，客户端在 D 盘。不能据其他机器的回退记录宣称本机已经是 1.20.0.4。
- 07:04:41Z 本机缓存列表确实列出 `1.20.0`，其说明为 `Old Version 1.20.0.4 (Crozier)`；实际选中项仍为默认公开版。缓存列表不是当前服务器可用性证明。
- 07:37:07Z Root 实际审阅本机新桌面：下载页明确显示 Steam 离线模式，画面时钟为15:37。**本段记录时尚未上线、提交版本切换、完成下载或启动新实机。**
- 目标 tuple 为 **1.20.0.4 / build25734779 / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`**。它是待验证目标，不是本机现有 EXE 的验收结果。

本机证据：工作根下的 `steam-inspect-a01/result.json`、`steam-list-cached-a01/result.json`、`steam-downloads-offline-a06/{desktop.png,uia.json}`。历史 [skill 切换资格](../../skills/steam-ck3-versions/references/qualification-2026-10-15.json)缺少来源机器身份，已明确标 `machine_id: unknown`；原始成功事实与证据 pins 保留。

## 拍摄入口已修的具体故障

旧 [capture_bootstrap.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py)固定要求 1.20.0.3；仅换新 DLL 无法准备 .4 拍摄。现增加显式参数：

```text
prepare --expected-game-version 1.20.0.4 --expected-character-id 29829
```

其余必需路径参数仍按实际 `prepare --help` 提供。新 .4 准备及载入核实际安装版本、Steam build、EXE hash 与完成状态；录制开始核原生 adapter、实际玩家 Robert29829、同一 PID 和 connection generation。新 prepared、环境和本入口执行回执带 canonical machine ID，.4 prepared 不接受缺失或异机身份。历史 .3 prepared 不改写，也不追认所属机器。

外置候选完成16项原版本守卫检查及8项机器身份增量检查；Root 应用后实际验证顶层和 `prepare --help`、`git diff --check`。这些是代码/CLI 验证，**不代表本机 .4 冷启动、录制或业务研究通过**。

公共原生 frontend 已有 .4 Robert 入口；新生产构建须同时启用：

```text
XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1=ON
XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1=ON
XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=ON
```

不能沿用旧 a08/.3 DLL 的资格。构建复用 `tools/run_native_msvc.py`，三个目标为 `xar_ck3_bridge`、`xar_ck3_bridge_injector`、`xar_ck3_bridge_host`，Release、jobs16、`BUILD_TESTING=OFF`；实际编译、精确路径 Defender 登记及新原生 hello 另行结算。

## Review02 仍要取得的结果

已有 .4 exact-day sentinel、loss writer/supply callback journal、regular-core 自然阶段及完整队列查询代码应直接复用；既有来源或他机资格不抵扣本机新观察。`observed_history_full_v1` 才包含相关历史族，默认查询缺事件不能解释为没有损耗。

本机新版研究与拍摄尚未开始。顺序为：版本完成并恢复离线 → 最小运行时资格 → 至少10个真实单日采样 → B 的1/1/统帅微实验 → 围城、县界、饥饿及补员的实际执行与完整整数 → Halt/改道及真实后果 → 登船实际支付与维护结算 → 同一新T0的完整 A/B/C。费用率和钱包净差不能替代实际支付，旧 B 中止及 C 两日采样偏差不能追认为合格比较。

新案只用 Robert29829 原普通战役；旧 William/.3 片段如引用须独立标清主体、版本和历史范围。核心主张闭合后才写长配音及重剪，不用“未确认”口播继续承担主片结论。人工1×完整观看与 signoff 仍是独立交付，不能用机器审计替代。

## 容量与工具输入

按统一存储策略已回收本机部分旧派生、重复副本和三段已释放用途的旧 .3 原片，保留关键 PNG/native 台账；三段原片不可重建，连续像素历史及重新抽样能力已失去，不能写作被后继录像完整覆盖。精确可用性及删除结果在工作根的 `capacity-lane/`、`story-lane/`、`d-raw-dedup-lane/`；计划量不算实际释放量。

07:31:45Z 的 C 盘获准项目根盘点完整、unknown0，逻辑占用153,148,384,783B；空闲36,186,443,776B。该时点固定 OneDrive 项目目录仅做本地 metadata/NO_RECALL 读取，未读正文、下载、改同步或删除云文件。新重型写入仍须按卷由 Root 串行登记峰值、系统增长、安全余量与限期配额例外；不把 C 盘余量当 D 盘余量。

07:26:03Z 实际查询独立工具链最新正式 GitHub Release，仍为 `v0.2.1`，wheel SHA-256 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`，与仓库 requirements 一致。本机选用 `tools/.venv/Scripts/python.exe`，Python3.14.7，实际 `xar-promo --version` 与顶层 help 通过；尚未创建新版 render run。外置 `promo-release-probe-a01.json` 保存此次查询，后续新 run 仍按届时正式最新版本复核。
