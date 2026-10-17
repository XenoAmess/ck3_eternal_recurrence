# 受管 OBS profile 的首次启动标记

`machine_id: xenoamess-full-tower-eb9d2c1186`。公共 `prepare_profile` 已完整生成独立 profile、scene collection、编码与本地认证配置，因此将 `General/FirstRun` 初始值从 `false` 改为 `true`。这是未来新 profile 的预防性一致性修复，未修改当前录制 provider 或已有 profile。

[OBS 30.0.0 固定原版源码](https://github.com/obsproject/obs-studio/blob/34ef67e212f24a085a63705a0ab81e3401c8eca4/UI/window-basic-main.cpp#L2255-L2268)表明：只有原先 `FirstRun` 为假、没有用户 `LastVersion` 且输出未 active，才排队自动配置向导；原值为假时还会先回写为真。主窗隐藏另依赖系统托盘可用、托盘设置及最小化标志，见[同源 2139–2141 行](https://github.com/obsproject/obs-studio/blob/34ef67e212f24a085a63705a0ab81e3401c8eca4/UI/window-basic-main.cpp#L2139-L2141)。旧受管 builder 已写 `LastVersion=503382018`，启动已有 `STARTF_USESHOWWINDOW`／`SW_HIDE` 和最小化参数。因此本次单行修复不能证明旧失败由向导导致，也不能保证任意环境都不会出现前台窗口。

实际首录 attempt `259e4d82-d03d-4c15-8978-eb8329310df7` 因前台从 `9708842` 变到归属本次 OBS 的 `25241084` 被守卫拒绝；该 OBS 为 `100200 / FT134366925031094503`，随后正常退出码0、输入解绑。`GetProfileList` 的207错误只是暂态，后续已连接，不将它写作最终失败原因。启动前 INI 没有保全，无法复原当时完整向导条件。[精简原件和来源](research/obs-preconfigured-first-run/README.md)保留原失败，不追改为成功。

公共配置生成、不能覆盖已有配置、隐藏启动等待及前台归属共13项离线测试通过，仅 mock OS／OBS 边界，不启动任何进程或连接端口。新录制是否成功仍以其独立实际回执为准；连续30年稳定、低于1秒／日及0.5秒／日目标均未完成。

2026-10-17版本补核：来源方确认本次实际 OBS 为30.0.2.0，前述30.0.0保留为同族源码旁证。现另核[30.0.2固定提交的向导条件](https://github.com/obsproject/obs-studio/blob/b45a73296f4f898e2ed455023020058075c30bab/UI/window-basic-main.cpp#L2256-L2268)与[隐藏条件](https://github.com/obsproject/obs-studio/blob/b45a73296f4f898e2ed455023020058075c30bab/UI/window-basic-main.cpp#L2139-L2141)，上述条件一致；[精确版本小回执](research/obs-preconfigured-first-run/OBS30.0.2-EXACT-SOURCE-REVIEW.json)不替换旧核对。具体失败窗口原因仍未知，代码与测试无变化。
