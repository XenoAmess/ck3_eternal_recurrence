# CCC 启动介绍通知与 D0 准入（2026-10-06）

`4-8e1c2f1861--celestial-commerce-corruption--R0005` / a78 的原始超时和完整 RED 保留。该场只有一次 Start；不是 NoSpace。原 qualification 两项各一次、两 FAIL 族为零，但最终 202 帧都停在 native event instance 1，H81 的 event-free owner 双帧门槛没有通过，因此没有执行 campaign-root query。启动等待超时后原 900 秒 hold 截止约 11:23:11，受管清理完成，报告约 11:23:14 finished / RED。

root 在同一 PID 12492 / generation 1 暂停现场，按原图坐标合同关闭介绍，保全原失败报告字节，然后追加两帧 snapshot、原 qualification query、campaign-root query；四步实际成功。两帧 native:4 / revision 5 / date 53144328 / actor 34422，active_event=null，owner/current TID 均为 21528，owner epoch 从 125053 到 125083。原生 root 证明 `celestial_government`、title 14022 / raw tier 6 / `hegemony`、independent=true、top_liege=34422、immediate_liege=null。这符合原 post_start policy；依据 actor 变化推断 34422 是官员的早先推论撤回，不降低或改写政府、等级、独立门槛。

实际 root：[a78-hot-observe-current-root-06.result.json](C:/workspace/ck3-upgrade-20261006/resume-root-01/a78-hot-observe-current-root-06.result.json)，112151 bytes，SHA-256 `2d96e56ae5891162a4887b3e8c464ea3c1853dde6110b3af604ce104f111a6b2`。薄事实、两帧 SHA 与更正保存在 [actual-a78-root-and-frames-thin-10.json](C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/actual-a78-root-and-frames-thin-10.json)。这些只证明现场观察，不追认旧 D0 或旧 RED 为 GREEN。

原图是“王朝兴衰——政通人和”，sole button 为“愿本朝江山永固，万世其昌！”。实际安装的 .3 原版 `events/dlc/tgp/tgp_dynastic_cycle_events.txt` 第 44–218 行是 `tgp_dynastic_cycle.0051`，整文件 SHA-256 `C2DB00C1C245131DC78741C2BDAC7232C97B22DB2212205FFD327CA4CB0E3CB7`。第 184–191 行 immediate 已播放音乐、写入介绍 flag、保存 start；第 192–217 行唯一 authored native0 选项只有条件显示名称和 clicksound，没有 gameplay effect 或 after。手工关闭不是 typed eventcontext 或 MCP 选择信用。

按 AGENTS 的 vanilla registry canonical 规则，新建通用 [exact .3 介绍记录](../../ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_dynastic_cycle_intro_12003.py)，由 [registry](../../ck3_autonomous_player/src/xar_autoplayer/vanilla_events/registry.py) 按实际 event key 查询。旧 Source10 的该 key 查询 unavailable 留档；没有假称它原先已注册，也不猜未实读的 saved-scope 形状。原版来源证明该选择不依赖 scope 产生业务效果，原始 typed context 全部保存。

[正式 runtime harness](../../ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py) 在一次 Start 后，先查原 qualification，遇到事件便读取本帧 actual typed context 和 exact-build registry。只有 reviewed startup acknowledgement、实际玩家 ROOT、唯一 shown/enabled native0 与公共 option1 相符时，预写 once 记录，再调用已有 `ck3_select_event_option`；随后独立 fresh snapshot 证明同 PID/generation、actor/date、paused/map-ready、event=null。未知事件或 unavailable context 立即保留诊断失败，进入原 hold，给 root 原 900 秒现场补 GUI；丢失返回或任何失败不重放请求。不以截图猜 key，也不把所有单选项事件自动关闭。

正式 harness 同时接入 H81 已有的 qualification 先行与原 event-free owner 双帧 gate。该 gate 的 AST 与冻结 H81 一致；仍要原资格日志和严格递增 owner epoch 后才发 full-root query，再由原 exact-frame business binder 两帧确认当前 actor。没有改 policy、原 command/readiness timeout、900 秒 hold、原生 binary 或 mod 输入。

只对新失败路径执行了一次现有 unittest 中的 `FixtureStartupNoticeTests`：3 项 PASS，1.935 秒。实际 a78 的薄 snapshot/root 用于生产 wait 函数确定性复现；typed intro response 是明确的离线 fixture，尚无下一场实际 MCP intro 选择信用。三项覆盖通知正常一次选择后通过原双帧准入、未知事件不选择/不查 root、选择响应丢失后不重放。原 11 项 core 及无变化的既有 H81/diagnostic 验证不重跑。open_kaishek 不适用：本包是已有 typed RPC 的 Python 启动流程与原版静态通知合同，无可复用的脚本 gameplay effect 子集。

首次 canonical 冻结与源码合回边界保存在 [SOURCE11_CANONICAL_STARTUP_INTRO_PACKET_16.json](C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/SOURCE11_CANONICAL_STARTUP_INTRO_PACKET_16.json)，4528 bytes，SHA-256 `36a325a84ed57ef2d5569e6bee0bc9697da8f77ebf71e92148b70e2908e9798c`。16 版永久保全，审阅补项后的当前候选为下述 18 版。新 Source11 树归本工作包 `/root/write_diagnostic`：

- `C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/strictcopy_source11_python_intro_16`：严格从原 Source10 canonical index 2638 项复制，2637 项逐字节相同，仅 registry 改动并新增一个介绍记录，共 2639 文件；所有 native 源码相同。
- [新 runtime](C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/runtime_harness_H81_startup_intro_16.py)：121504 bytes / SHA-256 `c76faa6ce455c9b0ffea30ad7e2f64d583d85416467641c57d33ebbb3a75d7ae`；来自冻结 diagnostic H81，只替换 wait 并增加本次 helper；gate/wait/helper 与正式源码 AST 相同，其余 H81 definitions 不变。它保留 H81 的既有 normal-exit/hold overlay，不冒充当前 master 全树。
- DLL 继续使用 Source10 原 `build-01/xar_ck3_bridge.dll`，5565440 bytes / SHA-256 `f150c4cf1aa8a121ab44ab41d3052b0b7db6729644a7958bd53156abf682d754`，未重编。

旧 Source10 原 index 2638 文件已全项验证 SHA 不变。先前一次 registry 查询漏用 `-B`，生成了 index 外 59 个 CPython 3.14 cache 文件；缓存保留在旧树，不删除，不进入新 canonical tree。含缓存的 15 版候选保留但不采用；运行始终带 `-B`。下一场须绑定新 runtime 和新 agent-source-root，重新分配 run/profile/pipe/control 输入，旧 Source10/H81、旧场 profile/report/冻结输入不覆盖。候选未启动 CK3，D0 与剩余生产 GUI/正常退出仍待实际现场验收。

审阅发现 AGENTS 第 444 行的每次通知自动处理证据要求尚缺截图与 userdir 文件哈希。18 版在通知操作前后使用既有 `pyautogui.screenshot` primitive，保存本次 report 相邻 `startup-notice-evidence/event-<actual-id>-before.png` / `after.png` 的完整原始桌面像素、实际尺寸、bytes 和 SHA；不裁切、不覆盖。只在 root 已获授权的同一现场屏幕 custody 中执行。按钮前态保存 actual typed context 的全部 options（包括 resolved_name、shown、enabled），后态保存独立 fresh native event/options；返回异常时明确记录后态 native unavailable，仍保全 after 原图，不重放选择。

前后哈希来自本次实际 `args.state_dir/preparation.json` 声明的 `profile_files`，并核对其 profile_dir 等于本次 `state_dir/profile`。CCC 声明六项为 dlc_load、fixture/product 外层 mod、pdx_settings、presets、tutorial；记录各自实际路径、存在性、bytes 和 SHA。游戏内 `tgp_dynastic_cycle_intro_event_flag` 没有声明的 userdir marker 文件，明确 `unavailable / proven=false`，不把配置文件哈希不变解释为 flag 写入或产品验收。以原始截图保全画面；OCR 不运行，选择与 GREEN 仍只消费 typed 状态。

对应既有三项用例只 mock screenshot primitive，真实 capture helper 写入离线图片并读取临时 profile 的六项文件，检查 before/after 文件哈希、按钮状态与异常时 after 保全；代码变化后一次复测 3 PASS，2.242 秒。它们不提供真实桌面、原生查询或游戏内 flag 信用；未扩矩阵、未重跑原 11/core。

当前交付：[SOURCE11_NOTICE_CAPTURE_PACKET_18.json](C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/SOURCE11_NOTICE_CAPTURE_PACKET_18.json)，6185 bytes / SHA `fbf3122afa440c279088b88dafa31c46e52693bc7b5ae7879f4cd4f844631a16`；新 agent-source-root 为 `C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/strictcopy_source11_python_intro_18`，2639 项全与 16 版 canonical source 逐字节一致。新 [runtime18](C:/workspace/ck3-upgrade-20261006/write-diagnostic-resume-agent-03/runtime_harness_H81_startup_intro_capture_18.py)，124408 bytes / SHA `1e4ef69e718f8b84dd92586d1bc2bc30019120923efc90c434d19f35b5fb834b`，仅在 runtime16 上新增 capture helper 并更新 acknowledgement；其余 definition AST 不变，gate/wait/ack/capture 与正式源码一致。16 的 source/index/packet/runtime 原字节均核对保留，仍复用原 Source10 f150 DLL，无 native 重编、预算或 policy 改动。下一场采用 18 版，实际 D0 与截图证据仍待实机。
