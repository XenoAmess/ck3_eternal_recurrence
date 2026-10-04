# CK3 1.20.0.3 原生 HUD Decisions 入口

本能力只打开 stock Decisions 窗口并独立证明实际可见，不选择某个决议、执行 Take 或读取 mod 控件值。
首次实机为 [白绮 R0006](../ck3-1.20.0.3-vivhite-compatibility-2026-10-04.md#白绮先加载-r0006核心通过空列表错误消失真实-decisions-入口通过)，2026-10-04；完整 creator GUI 仍未通过。

## 接口与资格

真实 MCP 工具 `ck3_open_ingame_decisions_v1(expected_revision: int | None = None)`，未知参数拒绝；
mutation、non-idempotent。原生 step `activate-ingame-decisions-v1`，capability
`game.command.activate-ingame-decisions-v1`；没有此 capability 的 DLL 拒绝执行。
新增构建开关 `XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1` 默认 OFF，ON 时要求既有 frontend MODEL/SELECTED_START admission；旧版本不广告此能力。

只接收 exact `.3`、存活玩家、map-ready、暂停的实际 snapshot，绑定 revision、episode、PID、actor、generation、date 与 application-main owner。
GUI 原生代码、HUD source 和 ancestry/context/visibility/enabled/vtable/callback/modal 均重新核验；已有 Decisions 可见时不 Toggle。
`ingame_topbar` 是 op27 的新固定只读 scope。2048 节点/2MiB 有界预算及截断拒绝保留；不使用 OCR、鼠标、键盘或 guessed child index。
真实 receiver 来自完整 topbar census 中唯一 `tab_decisions` 的直接子节点，并逐层重读；源文件的模板形状不能代替 runtime 资格。

本次 exact EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；
vanilla `game/gui/hud.gui` SHA `77d0beedefe23eee22b24c1c0b160ae5ee8ec938868d3f4b7ae76296347a6ac6`。
LookupWindow、ShortcutActivate、StrictDescendant、ButtonBase slot13 四段已加载代码各 32 bytes 独立核对，未沿用 `.2` ABI。
最终复用原 `DispatchFixedGuiWidgetNativeV1` 一次，原函数体保留。

## 单次派发与实际结果

派发前以 x-create 保存并 fsync episode/PID/actor claim，失败不删除，重连不改变其 key。
丢失 ACK 时不重派；原生 executor 未完成时保存同一 ticket/context，不提交第二次请求。
dispatch 后重新 resolve 和遍历 `decisions_view`、重读 owner/snapshot；即时 ACK 只记 native after。
Python 随后只轮询既有只读 op27，前后重查同一实际 episode/frame；later 根实际可见才返回 verified。

R0006 的真实结果：

| 观察 | 实际结果 |
| --- | --- |
| topbar census | 完整 281 节点，receiver `2/0/4/0/0` 合格 |
| 原生派发 | 一次；handled=true |
| 即时 after | 完整 63 节点，visible=false，pending |
| wrapper later census | 完整 301 节点，`decisions_view` 根 visible=true |
| 另一次独立 op27 | 完整 483 节点，根 visible=true |
| 玩家后态 | 同 episode/PID/generation，暂停、存活、无事件 |

wrapper 最终 `postcondition_verified=true` 绑定 later tree；`native_ack` 保留即时 pending 原件。
即时 `native_after_visible=false` 与后续 verified 不是同一次观察，不把 ACK 写成窗口已经打开。
此能力没有 rendered-text、selected-state、tooltip-state 或 business-model 信用。

## 构建和证据

外置根 `C:/workspace/ck3-upgrade-20261004/white-decisions-opener-agent-01/`。
原 c2a5 输入永久保留；新 `source-hud-01.freeze.json` SHA
`e3923c620c91ddf7d44937f0327272af6834455e0f9dedbd55bb2d0ad303a5b8`，4572 文件。
Release/jobs2 实际编译 DLL/injector 成功，DLL SHA
`ff45a6adc3ebbfe95f84f70ef3ead9015c418fb97bfd124893c9c32b10591a2c`。
7 个新聚焦检查覆盖 complete topbar、binding/native-proof 拒绝、lost-ACK 持久 claim 及 pending 后必须实际可见；
当次源码的 MCP 2.2.0 实际注册 134 普通工具，加两个 migration harness 工具进入实机。
当前 master 后续另有新增工具，其数量不由旧冻结 SDK 报告推定。

current-master 接续补丁只适配四处 CMake 插入并保留旧 war 条款；其余已审段落保持，原 dispatcher 不改。
两模块全部旧函数体和移除声明新增后的完整 Python AST 精确保持；当前真实 SDK baseline 141→142，只新增 opener，旧工具合同及明确 topbar enum 增量已核对。
root 集成 7 项聚焦测试通过，收据位于 `white-opener-root-integration-01/`；current-root 候选 packet SHA
`d554d53893e70822c4259bee74b0ba07145237b7f1a6e95e564f535829bb5465`。
current-master 本次尚未另编译整份 DLL，不能用旧 frozen candidate 的 DLL SHA 给新版全源授编译或实机信用。

完整实际报告 SHA `8890a05f0dd22753bbfed543932d436f5bd3e7fd468874dcc6e112df7612409d`，核心与 GUI 首段先后分开保全。
source/DLL/生产 mounts/原生 wire/MCP calls/claim/result 和 current Steam 离线 nonce 证据均绑定该 run；闭合 CAS1992。
下一施工入口是稳定 decision key→实际 row/DataContext→Take，再证明产品生产 bridge 的内层 panel 可见；本能力不覆盖该后段。
