# R0013：准备通过后，礼仪写入口在发现阶段被拒

`machine_id: 4-8e1c2f1861`；本场绑定主源 `8d49d0e028ab79e53331e984555a266911426464`。依据Root于2026-10-18T08:58Z的现场归纳、08:53:50.436032Z的源码负责人回执及首调用原件整理，[小型来源索引](evidence/faith-power-r0013-rite-discovery/source-pins.json)保存逐件SHA、观察面和未读大文件边界。本页不修改系列经验页或冻结源。

## 实际完成的步骤与首个阻点

R0013准备已实读成功：罗贝尔当次原生full ID31254，Christianity8／Catholic13，当前与主流Roman礼仪均为0，虔诚20000、marker1／forbidden0。信仰窗口typed打开后，另一次查询确认visible=true。这是明示准备状态的结果，不能替代下一步教改权限或采用结果。

首实际调用是 `ck3_execute_player_rite_creation_action_v1(operation="open_create_draft", expected_source_rite_id=0)`，08:47:30.696009–08:47:30.888937Z返回 `ok=false`，错误文本为“this DLL does not implement the exact .4 Rite action candidate”。负责人沿现有链确认它在发送前被Python capability检查拒绝；没有创建草稿、教改或采用动作ACK。本场没有达到这些动作的原生Can／确认／独立后态，不能将这个错误当成游戏业务条件拒绝。

实际hello首行来自PID5464、08:32:52.572980Z，缺少 `player_rite_creation_action_v1`；复用负责人保存的首行SHA `555f18bbad4f62959517f662228c59aa1a28e45240ebb5e061768031235704a9`，未重新读大wire。负责人确认a08编译flag为ON、实际DLL已有固定分派，漏的是HelloFrame广告。因此通用错误文字不等于执行器代码未编入，也不等于原生写动作已经收到请求。

## 测试观察面与端到端链

此前请求／wire夹具和编译各自真实通过，证明了那些输入、适配与编译观察面；它们没有覆盖“DLL实际hello → capability发现 → 工具分发与发送 → 原生许可 → 一次执行 → 独立后态”整条链。此次首调用揭示的是发现阶段的实际缺口。可迁移的做法是用每项测试的真实边界陈述结论，并让后继实际握手与调用补齐缺失的一段；测试数量和源码存在都不能替代该连接。发现握手遗漏也不意味着需要重写整个控制器或重跑全部业务。

最小C++候选在既有HelloFrame按原flag、enabled及exact.4条件追加已编入domain key，候选696B，SHA `31905c1f566648f1a9000acb94bb72b787a52b1978f47f88106af151bfea02eb`。在上述回执截点它未合入main、未编译、未加载；后继须用真正加载的新DLL与实际会话另行确认，本文不给它生效信用。

## 磁盘补丁与现场加载态

原MCP child的注册closure保留driver，普通import已缓存首次失败时的模块，已部署会话没有合法reload入口。修改磁盘Python不会改变这个child的执行代码；终止唯一stdio child又会触发受管host清理，不能拿它冒充保现场热修。

外置Python私有接缝候选15136B、SHA `ec709627d849ffbf801656a7bf7990d3c14024a7ec5aa3ceff69e101b6a8ee2f`及2个通过测试保留为探索证据。测试使用真实记录hello驱动生产Driver primitive，endpoint结果为合成unavailable，没有native／game调用。因现场不能热加载，Root放弃将该额外支路并入主线，选择正常闭场后加载C++握手修复。区分磁盘代码、已加载模块／二进制和会话状态，才能判断现有合法热恢复是否可行；本次未新增reload平台，也不授该Python方案当前Can或action_ready资格。

## 物理存档与恢复资格分别记录

08:54:12.888423–08:54:14.252668Z的预教改保存回执记录物理存档68958787B，SHA `62d18fe254d658356671269f194319a316729394da6f38b32da0d503bae1cd58`；原操作者另实际读过文件。本页只核小回执，不读取或重新散列69MB存档。原 `driver_state_replace_receipt` 仍为 `unconfirmed/save_binding_mismatch`：有物理文件不等于公共保存绑定正确，更不等于已经冷载恢复成功。其记录的native_campaign检查点缺少旧one-life绑定字段，不能把文件存在追认为该绑定已通过。

它比原64MiB分量估计多1849923B；Root在既有704MiB whole内调整分项，未增加存档次数或覆盖旧回执。后继公共冷载、恢复身份和真实加载结果仍待验证。规划智能体只能把它列为有物理证据、恢复未资格化的候选输入，不能将其作为已可用的恢复点。

## 后续实际闭场，不改变首个RED

Root于08:58Z归纳时闭场仍在进行；本页随后核对同机、同PID5464的小型终态原件追加结果：原CaseClient保留HANDLE读得实际OS退出码0，native记录结束于09:04:49.539218Z、退出码0；host正常闭场回执结束于09:05:20.650900Z，`normal_close_qualified=true`、`business_pass=false`。该回执的host_error=null不覆盖原host进程退出码：原Popen实际等待public0（09:05:21.138462Z）、host1（09:05:21.359039Z），keeper原父进程回执为0（09:07:40.460269Z）。首个发前拒绝原件仍存在，不能将host1改写为0。

09:07:50.384400Z任务总线CAS11751实际释放，resources为空，来源仍绑定8d49d0e。闭场完成只证明本次正常退出与释放；未补发草稿、教改或采用，也未使存档绑定或公共恢复变为可用。下一次实际加载新DLL与新会话才能继续验证握手和写入口；R0012失败与R0013准备通过分别保留，不能跨场追认。

## 后继源码整合截点

`2026-10-18T09:16:33.521023+00:00`，Root在实际释放后更新远端master并应用上述C++小修。原场次与源负责人回执仍绑定8d49；本条只证明源码已修，新a09尚未构建、加载或取得教改／采用资格。

沿既有MCP注册的三个工具为`ck3_query_player_rite_creation_action_context_v1`、`ck3_execute_player_rite_creation_action_v1`、`ck3_collect_player_rite_creation_action_result_v1`。调用方显式启用`--private-player-rite-creation-actions`，native对应`XAR_ENABLE_RITE_CREATION_ACTIONS12004=ON`，默认保持关闭。它们复用现有Driver、完整原生许可与一次提交／独立收集结果；新机器仍核自己的exact build与实际hello，不能从本记录取得已部署或实机成功资格。
