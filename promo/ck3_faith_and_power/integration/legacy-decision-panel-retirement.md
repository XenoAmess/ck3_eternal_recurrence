# 旧蓝色决策面板退役

2026-10-18 用户指令第6条：左上蓝色旧智能体决策面板已废弃，今后新录制不再出现；现有素材允许保留，不必为此重录。本条只退役旧窗口，不停止决策规划、MCP、原生决策界面、决策数据发布或新版 decision UI。

识别到的生产器是 `tools/g2_saved_campaign/decision_overlay_window.py` 的 `NativeOverlay`：原窗口类 `XARG2DecisionOverlay_<pid>`，位于左上 `(24, 88)`。历史本期 `decision_overlay*.py` helper 调用该组件，标题包括“第一期机制实验 · 原生决策记录”或“HOLY SITE CHOICES / 圣地经营”。这是独立 Win32 悬浮窗，不是 CK3 mod/fixture。公共 allocator 配置中的 `allocator_overlay` 是源文件 pin 清单，不是这个蓝面板的启动开关，不能删掉它来禁面板。

当前实现将 `NativeOverlay` 留为明确拒绝构造的兼容导入，旧 `live_decision_overlay.py` CLI 也不再启动窗口。历史 helper 即便继续导入主仓模块，也会在任何 Win32 创建之前失败。只读格式化与决策观察/发布 helper 保留，历史证据、原片和已成片不改。

后续拍摄按以下顺序迁移：

1. 从当前源码重新准备独立 runtime/allocation 并 pin 新 recorder；不要改旧冻结包的输入或清除旧回执。
2. 不启动历史 `decision_overlay*.py` 或旧 `live_decision_overlay.py`。录制入口本来就不负责启动它，继续保持无旧面板的默认流程。
3. 若仍有旧 owner/冻结副本存活，由其 owner 正常关闭。新 take 在创建输出目录、导入 RecorderJob、启动 FFmpeg 之前，会按精确旧窗口类拒绝它；隐藏的旧窗口也不放行；此拒绝发生在 take 名称和 recorder 对象被消耗之前，owner 关掉旧面板后可在同 keeper 用全新请求重试，无需为此重启 CK3。此检查不匹配窗口标题，不将原版或新版决策窗口一概禁用，不自动关闭其他人的窗口。
4. 决策理由与原生回读继续保存到当前知识/请求回执；需要展示时使用当前决策界面，或在剪辑中采用与旁白相符的说明。不能以重新命名旧蓝窗口绕过退役。

起录回执的 `decision_display_policy` 记录旧组件已退役、起录检查旧窗口计数为零及录制入口未启动/挂载旧面板。它只证明起录检查，不是像素验收，也不将旧素材追认为没有面板。历史冻结运行包仍是原字节；不自动修改其他机器或旧包，目标机器需要使用新源码准备并做实际录制检查。

本次候选仅离线验证：构造/CLI 在 Win32 之前拒绝、窗口类过滤不误伤新版名称、旧窗口使新录制在输出/FFmpeg 之前拒绝，以及既有决策数据格式化/发布仍可用。未启动窗口、游戏、Steam 或录屏，不据此声明已有新实机画面通过。

## 旧 OBS 文本发布配置的迁移边界

`recording_recovery_adapter.py` 的 `overlay_source` 是显式配置的 provider。历史配置可能通过 `--decision-text-file` 启动旧 `live_decision_overlay.py`，让同一旧进程既画蓝窗又给 OBS 发布文本。该旧 CLI 现在也会拒绝这条组合启动路径；不能声称旧配置仍可自动恢复，不能为兼容而重新启用蓝窗。

本次没有修改新版 decision UI、`ck3_obs_capture.py` 或独立 OBS 文本源。`decision_observation_feed.py` 与既有格式化/文本发布函数仍可复用，但观察 feed 不是完整录制 provider 的直接替代品：不能把 `overlay_source` 随意改成它，就冒充已有原进程身份/创建时间/启动回执。新界面应使用其实际已支持的发布器，重新准备、绑定并验证对应 provider；没有这样的资格时明确拒绝旧路径，不能伪造 headless 窗口或新入口。

这是旧组件的退役及明确兼容边界，不是停止全项目的决策记录要求。不同机器仍应使用自己的新源码/部署回执；本次离线测试不代表新版 UI 或新录制已在任何机器实机验收。

## 本次验证出处

`machine_id: 4-8e1c2f1861`；观察于 `2026-10-18T02:24:22.201601Z`。基线为 `d1c2bc7eb568a4eab3f55c065adb645a9dbace6f`。外置 `episode01/revision-v4-20261018/legacy-panel/DELIVERY-a05.json`（SHA-256 `419b489782708085cde116c006662bb10d3afe00e3822662a03d306eb03a21de`）保存实际 stdlib unittest 8/8 与 `git apply --check` 退出0；补丁 SHA-256 `2cfcc96276a8f7e59e77c68ed6647e39293d21fe54005c9596c6aa5c76bf0766`。测试使用窗口/进程替身，覆盖旧窗构造前拒绝、精确类名过滤、起录前拒绝及同 keeper 关闭旧窗后可重试；没有启动实际窗口、Steam、CK3 或录制。相同八项已加入静态 CI。
