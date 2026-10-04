# R0003：正式代表流程通过，入口提示本地化 RED

本轮 **FUNCTIONAL_REPRESENTATIVE_PASS / UI_LOCALIZATION_RED**，生命周期已关闭；未宣布整体验收GREEN。冻结来源588492d3dbf473226664220b722a04b66ae54bae，CK3 1.20.0.3 / Steam build25652598。

[基线身份](readbacks/baseline/report.json)确认普通1066罗贝尔实际31254／history1128／1015.1.1／奥特维尔。实际路径为天主教rite0/faith13 → [原版道学33/confucian31](readbacks/original-confucian/report.json) → [正式孔门150/common32](readbacks/formal-entry/report.json) → [朱子156/common32](readbacks/zhuxi-chosen/report.json)。[取消研习](readbacks/practice-cancel/report.json)和[取消选派](readbacks/choose-cancel/actual-player-v-entry-and-practice-cancel.json)保持整个玩家存档块及资源不变。

[朱子研习A](readbacks/final-practice/report.json)实际金币259→244、虔诚150→185、学识经验0→40；native与保存压力4，威望2200未变。专断−0.5及野心勃勃+0.25压力增益修正见[原版源码摘录](source-proof/stress/00_traits.excerpt.txt)，基础5修正后的3.75与观测4相符；取整调用链未独立追踪。保存选派tick365及研习tick180。[八礼仪对象图](saved-formal-graphs/report.json)各有三个核心信条，全部faith32、无领袖。

直接原图保留：[入口粉色错误](screenshots/formal-entry-confirm-visible.png)、[选择器](screenshots/choose-reopen-event-visible.png)、[选派冷却阻塞](screenshots/school-cooldown-blocked-visible.png)、[朱子研习事件](screenshots/zhuxi-practice-event-visible.png)、[研习冷却阻塞](screenshots/study-cooldown-blocked-visible.png)、[保存退出](screenshots/normal-exit-desktop-click.png)；[Steam新鲜离线回执](offline/steam-frame-freshness.json)及[原图](offline/steam-moved.png)一并保存，没有缩图或改写。

退出后[error.log](lifecycle/error.log)802字节、SHAa479b73b3510f21a2721d6af36e26c3eca913e33353ff743334bbc6a99673f6c，与先前快照一致；[分类](lifecycle/error-classification.json)仅有两条NOT_character_this_equal_global错误，无此份日志内其他错误块。入口[实际装载源码](source-proof/display/runtime-loaded-R0003.txt)与[运行后修正候选](source-proof/display/after-R0003-candidate/lyd_player_triggers.txt)分开保留；后者未经过本轮实机，不能回写历史RED。

[退出进程](lifecycle/normal-exit-processes-001.json)无CK3且PID5556不存在；[keeper](lifecycle/keeper-FINAL.json)退出无失败seq2674；[CAS完成](lifecycle/screen-release-completed.json)seq2676、resources为空、dirty0/冻结588。[MCP关闭](lifecycle/client-close.response.json)及[session闭合](lifecycle/session-closed.json)保留，session79955 rc0由根代理实际工具完成结果报告，没有仅凭closeACK声称进程退出。allocator状态以[投影报告](projection-report.json)中的实际读取为准。

自然365/180天过期、重载、完整8×3研习、NPC/多人范围和未实现的正式分合均NOT_RUN。完整494文件／142405708字节包永久留在C:/workspace/ck3_lyd_runtime_20261004/r3-acceptance-package-candidate-001；[完整原索引](external-reference/full-package-index-v2.json)、[全494文件哈希与路径](external-reference/all-full-package-files.json)、[全部未导入项及原因](external-reference/excluded-raw-files.json)绑定外置原始资产。七份大存档继续在[checkpoint-index](checkpoint-index.json)所列content-addressed只读目录。

这是逐字节精简投影：只保留代表流程的直接小型回执、对象摘录和七张必要原图，不导入重复SDK封装、其余截图、大日志、keeper轮询或二进制工具。七张不变原图本身已超过约12MB目标，因此没有为尺寸目标压缩或改写原始证据。
