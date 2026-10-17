# 圣地圣物窗口归属修复（1.20.0.4）

机器：`4-8e1c2f1861`。本文封存时间：`2026-10-17T14:31:10.215156+00:00`；实际进程观察：`2026-10-17T14:18:15.309149+00:00`。这是 R6 实机 RED 的原因诊断及离线修复资格；修复后尚未冷载取得真实 getter 或动作结果。

R6 已通过原生界面查询打开圣地 14，但权限 reader 返回 `holy_site_window_registered_owner_unavailable`。Root 执行只读 probe（PID 21920、创建时间 1792244644.324554）后证明 `window+98` 指向 `CInGameInterfaceIdler`，等于 admitted `jomini_owner`；`owner+10` 是独立的 `CIngameInterfaceIdlerGfx`。原 typed helper 把这两个角色误作同一个对象，因而在合法窗口处提前拒绝。原件、SHA 与时间见[资格回执](holy-site-relic-typed-owner-binding12004/qualification-a01.json)。probe SHA 为 `95f98799b0581dece92315205cca759c3deeb0ec5b84d77683db00b01340e7af`。

静态来源也闭合相同关系：原构造器 `17D4D40..17D4EF4` 把 RDX 写入 `window+98`、R8 写入 `window+A0`；`B0EA60..B0EAEC` 从 `handler+40` 取 RDX，R8 为 handler，构造结果发布到 `handler+5D8`。精确 body SHA、缓存小包 SHA 和追加的 consumer 研究见[来源复核](holy-site-relic-native-actions12004/window-binding-source-review-a03.json)。本修复没有再次扫描 CK3 EXE。

typed helper 现在要求 `window+98 == admission.jomini_owner`，并把该 owner 独立加入前后 Capture 稳定比较。`owner+10 -> gfx+88 -> handler` 路径、两份窗口 vtable、`window+A0` 回指、实际 root、site/artifact 的完整 ID、slot 行、owner 线程/TLS、暂停与 modal 守卫全部保留。旧测试构造器的单个字段同步改为 owner，避免后续构建重新引入错误角色假设；原旧源和生产器保持不变。

新短构建目录 `bui03` 实际执行 10 项 focused 检查，产出 7 个完整 `command_result`：不同 owner/Gfx 的合法形态、选择后保留 slot、foreign/null owner、动作前 owner 漂移、错误 handler 回指、动作后 owner 漂移及供奉 ACK。没有执行旧 30 项矩阵。新构建使用生产 core 和逐字冻结的 16 个生产纯 parser/formatter 函数，明确不是完整 DLL 链接，也没有执行游戏引擎函数。7 包与 `focused-qualification-a01` 逐字节一致；其中 2 个正常包还与旧 `whole-packet-a03` 一致。完整包及原始输入通过 source-bound manifest 交给独立 Python/MCP consumer，consumer 的实际结果单独记录。

供智能体规划使用：native 窗口绑定失败应保存具体 reason 和当前帧，不能由该错误推断“没有圣物”或“供奉条件不足”。修复冷载后先重读权限、候选、选择与预览，再决定是否供奉/取出。callback 后 owner 漂移时仍保存真实 dispatch ACK，结果保持 `verification_pending`、独立后态未知，禁止盲重试。供奉/取出成功仍须独立读取玩家/圣地所有权和实际槽位；本包的 `action_ready`、业务后态资格均为 false。

原始复现由外置 `qualify_typed_owner_binding_a02.py` 驱动：它执行 `a01` 的相同原生构建配方，改用新 `bui03`/`focused-qualification-a02`，并固定修正后的 fixture SHA；已存在输出拒绝覆盖。CMake 入口是 `ck3_autonomous_player/native_bridge/cmake/relic_owner_binding_focused12004/CMakeLists.txt`，显式传入 base stage、repo root 和生产纯函数 TU。新复现必须使用新的短 build/output 目录，保留 source-freeze、构建原始 stdout/stderr、EXE 和包 SHA；不得复用名字覆盖原资格。

原始进程证据、源码和本资格在 `2026-10-24T14:31:10.215156+00:00` 复核用途；衍生构建于 Root 整合后 48 小时内评估回收，按仓库通用存储策略保留仍在解决问题所必需的输入与小型摘要。
