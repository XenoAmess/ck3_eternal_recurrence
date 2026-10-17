# Episode04：统帅任命拒绝的可观测性

`machine_id: desktop-3fevhd2-1c74096080`；2026-10-17。

R197 的统帅任命返回 `state_changed`，没有足够证据判定五项前置条件中的哪一项失败。该历史动作仍为 unknown，不能重新投递，也不增加饥饿扣兵或统帅任命成功资格。

本次在原生产路径补充诊断：`ck3_autonomous_player/native_bridge/src/bridge.cpp` 的任命入口在拒绝时记录第一个失败条件、请求与 worker revision、是否实际尝试读快照及读回比较结果。五项条件依次为 revision 一致、worker 已初始化、存在上次快照、原生快照读取成功、与上次快照相等。原生读取保持短路且最多一次；拒绝发生在提交 mailbox 之前时明确记录 `dispatch_submitted:false`。原来的拒绝、暂停和后续业务约束继续适用。

`ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py` 将任命原生拒绝异常中已存在的 request/result frame 原样持久化到失败 history，保留异常、unknown 与 `never_replay:true`。其他动作和没有 request frame 的异常不产生这份任命结果。

新增 `ck3_autonomous_player/tests/unit/test_army_commander_native_rejection_history.py` 使用真实 Driver 初始化、真实 history 写入和临时磁盘，只在执行边界注入拒绝；三个用例检查任命原件保全、无关动作和缺失原件，不重试。2026-10-17 本机唯一执行为 **3 passed in 2.92s，exit 0**；没有运行新的 C++ 镜像 harness。回执为 `C:/ck3-e04-resume-20261015-a01/r05-main-diagnostic-apply-a01/RESULT.actual.json`，stdout 100 B，SHA-256 `672ca03a44166f3fa988c081b3bf7266851268c0df9fb9fca587dd518d80dc1c`。

C++ 编译及新实机拒绝样本尚待下一轮真实 native 构建和观察。本次交付的是诊断与失败原件保全能力，R05 的自然饥饿物理扣兵仍待正例。
