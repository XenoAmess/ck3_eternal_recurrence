# CK3 1.20.0.4 固定原生 Military 窗口入口

本增量提供已有 `ck3_execute_step(step="activate-ingame-military-v1", expected_revision=...)` 的固定语义动作。不新增任意widget click、顶层query或MCP工具，不放宽旧Knights/OpenView gate。构建开关 `XAR_CK3_ENABLE_INGAME_MILITARY_OPEN_PRIVATE_V1` 默认OFF，ON依赖已有frontend owner admission；capability仅actual `.4` descriptor广告。

source-only候选机器 `machine_id: desktop-3fevhd2-1c74096080`，观察/检查 `2026-10-15T20:26Z` 至 `20:36Z`；精确时间/source SHA/argv见外置 `C:/ck3-e04-resume-20261015-a01/refill-toggle-actual-next-a09/MILITARY-OPEN-DELIVERY.actual.json` 及其回链。未执行SDK、游戏、桌面、EXE构建/运行或主树写入，没有实机打开信用。

## 固定来源与实际receiver

原版 `game/gui/hud.gui` 227658B，SHA-256 `77d0beedefe23eee22b24c1c0b160ae5ee8ec938868d3f4b7ae76296347a6ac6`。491-503行常规HUD唯一source：`widget_hud_main_tab` name=`tab_military_tutorial_uses_this`，其maintab_button onclick=`[ToggleGameViewData('military', GetPlayer.GetID)]`。不能用猜测的`tab_military`或无data的ToggleGameView，也不随意fallback到另一nomadic面板。

Root R0177实际034只读topbar响应：时间 `2026-10-15T20:26:14.272107Z`，272727B，SHA-256 `2f5ac05b68c816d773ded1640d602e2cb8921fb211799b9c91b1e35c717fd894`，完整281行。唯一source锚点实际path `2/0/0/3`、一个直接子按钮 `2/0/0/3/0`；两者visible/enabled。实际anchor vtable RVA76958128，button vtable RVA76961544。完整祖先为 `ingame_topbar/main_tabs/[unnamed]/[unnamed]/tab_military_tutorial_uses_this/[unnamed button]`。这些path只作当次证据；实现每次从fresh census唯一named锚点重新取得provider-private path，并核实际class/父链/context，不能接受caller path或硬编码当次index。

## 派发与后验

复用已迁移`.4`的Decisions固定HUD模板。Native executor核exact `.4` EXE SHA、已加载LookupWindow/ShortcutActivate/StrictDescendant/ButtonBase各32B pins、application-owner/TLS/paused stamp、revision/PID/connection generation/alive actor/map snapshot。重新resolve实际GUI owner/context，完整topbar census，核unique固定name/一个direct button/actualclass/逐层name-vtable-parent-context/visible-enabled以及现有modal guard，再经 `DispatchFixedGuiWidgetNativeV1` 构造原生semantic输入。没有直接写开关byte或调用旧OpenView RVA。

已经visible则不Toggle。`dispatch_attempted`在native调用前消耗；bridge只提交一次ticket，已running的timeout继续等同ticket，绝不重派。Native after独立重新resolve/traverse `military_view`、重读owner/snapshot；即时ACK保留真实pending。Python固定step coordinator先持久x-create/fsync once claim，再派发一次；lostACK或未知结果保留claim，无再次调用。之后仅重复已有只读military census，每次前后核同episode/PID/generation/actor/date/paused frame；只有完整root实际effective_visible才返回verified。native_handled/root_available/ACK不能替代此后验。

Native step接在同一 `FrontendGuiRouteMailboxContextV1` typed op与现application executor上；bridge fixed request parser、`.4` adapter capability、GameAdapter step map和defaultOFF CMake宏一并接通。Python在NativeDriver既有execute-step入口识别该固定step，调用小coordinator模块；MCP/service保持通用execute路由。没有把旧 `.4` Knights拒绝规则改成允许。

本动作只证明军务窗口root可见；不证明MilitaryView业务owner、补员switch、实际自然ADD、渲染文字或checkbox selected状态。补员业务仍按 [callback专题](military-refill-toggle-callback-12004.md) 继续actual callback对象+8 source链与独立raw4A9读回。

## 当前验证与下一执行

四个相关native TU（新executor、frontend route、`.4` adapter、GameAdapter）在target8 overlay下、开启新宏的focused `/Zs`实际退出0。两个新synthetic行为检查通过：pending ACK必须等later实际visible root；lostACK后第二次请求不产生第二次dispatch。target8+本增量按序`git apply --check`通过。大bridge.cpp与native_driver.py以相对patch-hunk保存，避免超a09共享2MiB；NativeDriver变更全文在内存AST解析通过。没有在此运行完整native build，Root必须以新flag完成实际a08构建/部署后才可执行。

首次实机保留native ACK、durable claim/result、独立military tree实际visible及相同episode/frame，失败不热改、不重放未知动作。当前已有016 Knights拒绝原件继续保留；此新source能力不能倒写旧失败或旧实机结果。所有a09输出计active32MiB池，截止 `2026-10-16T07:45:01.597Z` 不延长。
