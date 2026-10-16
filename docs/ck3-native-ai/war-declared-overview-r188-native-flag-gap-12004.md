# R188 宣战概要：SDK注册与a29 Native开关不一致

来源机器 `desktop-3fevhd2-1c74096080`；实际2026-10-16 UTC，R0188、PID12060、CK3 1.20.0.4／Steam25734779。历史runtime/source为 `d05b0c780b615faa714fdf0535403bb2e6941faf`；本次知识整合基线为 `53c559aa7f0caca8bc1c92b0c6f44b2ef8f72011`。其他机器可复用下列配置与源码关系，不能据此取得安装、运行、权限或关闭窗口资格。

R188实际 `ck3_query_war_declared_overview_v1(expected_revision=43)` 返回 **is_error=true**，正文为 `Native does not advertise this fixed war overview operation`。SDK工具目录公开query/close只证明接口注册，不能证明当前Native广告了能力。原版stock root为 `war_declared_overview`；其底部“召集部队！”对应dismiss与右上X均绑定 `WarDeclaredOverviewWindow.Close`，没有raise回调。此次实际阻点发生在Native capability准入，未取得typed窗口结果或Native Close后验。[typed错误原件](evidence/episode04-r188-war-overview-native-flag-gap-12004/native-query-error.actual.json)与[既有Close来源及dispatch修复边界](war-declared-overview-close-pointer-dispatch-fix-2026-10-15.md)分别保存。

## 实际配置根因

a29不是单纯遗漏一个默认值：CMakeCache明确 `XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1:BOOL=OFF`；真实configure argv显式传入同名 `=OFF`。实际158项feature BOOL中22项ON，该项OFF且全部cache值匹配。a29准备器继承a28完整flag map，runner又要求exact22 ON集合；随后d05增量producer记录 `configured=false`，沿用此前配置。[实际全flag map](evidence/episode04-r188-war-overview-native-flag-gap-12004/a29-configure-flags.actual.json)和[精简配置事实／原件pins](evidence/episode04-r188-war-overview-native-flag-gap-12004/configuration-facts.actual.json)可移机复核数目与来源，不需要读取来源机EXE。

可复用实现是 [CMakeLists.txt](../../ck3_autonomous_player/native_bridge/CMakeLists.txt) 的既有option及common runtime PUBLIC compile definition，和 [run_native_msvc.py](../../tools/run_native_msvc.py) 的 `--cmake-define NAME=VALUE`／`configure_command`。同一宏在 [bridge.cpp](../../ck3_autonomous_player/native_bridge/src/bridge.cpp) 门控capability广告、step准入与owning-thread mailbox执行。[冻结原始source spans](evidence/episode04-r188-war-overview-native-flag-gap-12004/source-spans.actual.json)保留各自行号与SHA；这是已存在的实现，不需要另造provider或窗口系统。

## a30仅为最小配置候选

[完整13KB候选map](evidence/episode04-r188-war-overview-native-flag-gap-12004/a30-feature-flags.candidate.json)只将 `XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1` 改为ON，其余157项保留，158项总数不变、ON数22→23。未来新a30 producer须按新map更新预期ON集合/数量，在新configure计划中替换原单个OFF定义；不能修改历史a29 cache/runner，也不改变CMake全局默认。

该既有开关同时控制war-declared query/close与war-results query/close四个操作。正常构建后仍须核实际cache、common runtime及bridge编译define、新DLL来源、fresh Native hello和SDK能力匹配；未来自然可见窗口上的一次typedClose必须另得真实 `closed_verified` 后验。候选中的新source/buildroot为null，**本专题不声明a30已构建、部署或通过实机**；不能把build、fixture或能力字符串替代关闭结果。

## 本次UI fallback与像素可用性

Native query失败后，Root按新原尺寸截图及coordinate_map对右上X仅click一次。[原map小回执](evidence/episode04-r188-war-overview-native-flag-gap-12004/coordinate-map.actual.json)保留source/desktop均2560×1440、完整preview bounds、实际映射点、PID12060前后焦点一致、click_completed与failures=[]。这些是该次来源机数据，不是以后可复用的坐标常数。

Root直接审阅后图确认通知已消失、仍Mar31 paused；worker没有重做像素审阅。此结论标为 **guarded UI fallback**，`native_closed_verified=false`，没有Native Close动作或战争应战/召集部队信用。[分层事实](evidence/episode04-r188-war-overview-native-flag-gap-12004/ui-fallback.actual.json)保留此前query错误和独立视觉后态。

[前图metadata](evidence/episode04-r188-war-overview-native-flag-gap-12004/before-close.metadata.json)、[后图metadata](evidence/episode04-r188-war-overview-native-flag-gap-12004/after-close.metadata.json)及[manifest](evidence/episode04-r188-war-overview-native-flag-gap-12004/manifest.actual.json)保存两PNG的原路径、大小、SHA、来源machine_id和时间。**仓库未复制PNG像素**；其他机器只能消费这些小证据，实际阅图需要访问来源机或取得另行核验的精确副本。SHA和本地绝对路径不证明移机后能读图，也不构成人工整片签核。map原件缺machine_id的事实保留；新增wrapper用两张明确machine_id的原回执及同PID/HWND/尺寸关联补注，不改写旧原件。

后续普通游玩继续复用 [ordinary_war_declared_overview_v1.py](../../ck3_autonomous_player/src/xar_autoplayer/ordinary_war_declared_overview_v1.py) 和 [typed transport](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_transport.py) 的固定窗口查询、一次Close与pending不重发规则。关闭概要不代替完整战争规划；这不是active_event或普通character interaction，不填造event ID或套用交互左侧拒绝。
