# R0065：原版儒家反馈版首帧校验失败，现场已释放

运行 ID：`bf-202609141645-5434332d4d--li-yu-dao--R0065`，本机日期 2026-10-12 CST；下表使用 UTC。产品为 0.1.1 开发版，Workshop `3817934804` 仍公开 0.1.0 Beta，本轮没有上传。

## 已交付的玩家反馈修改

源码已在 `5941fc3425d1be53340da46b305ac154a8c548b9` 及其祖先提交推送 master。36 个新增礼仪直接归属原版 `confucian_faith`，保留经学、道学、主礼仪与既有信条状态；旧共宗仅留历史兼容定义。36 信条各具常规增益、代价与个人效果；对立领袖决议显示 16 项资格条件。详情见[原版儒家接入](../../../../mod_li_yu_dao/docs/vanilla-confucian-integration.md)及[数值表](../../tenet-modifier-design-2026-10-12.md)。

该精确提交三项 CI 均成功：正式构建 `38167725459`、[LYD 检查](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38167725694)、线性历史 `38167725558`。本轮 builder 实际返回 0，生成新的 71 文件 staging，没有复用含旧 `hidden_trigger` 错误的 A26 staging。这些检查不证明游戏内传播或旧档迁移。

## 实际运行

| UTC 时间 | 事实 |
| --- | --- |
| 19:44:18 | ROOT 直接审阅窗口位移后的实时 Steam 离线画面。 |
| 19:44:44 | 公共 run 启动，冻结上述源码提交、Native058 和新 staging。 |
| 19:45:03 | CK3 PID `7400` 创建，creation time `1791747903.6653767`。 |
| 19:58:58 | snapshot 成功：map ready、paused、alive 均 true；runtime actor `31254`、date `53144328`、generation `1`。 |
| 随后 | adapter 硬比旧 runtime 编号 `29829`，抛出 `Feedback needs original living paused Robert 29829`。七阶段业务均未开始，没有入门、择学、个人选择或领袖业务结果。 |
| 20:19:24 | ROOT 通过原 host 共享队列提交一次角色窗口导航。接口列表有该工具，实际后端却返回 `current native UI supports army query and select only`。异常触发 host 失败清理；没有取得人物姓名。 |
| 20:19:30–31 | managed session 终结，job/tree/control cleanup 通过；shutdown 游戏 exit `1`，原 host 实际 `Popen.wait()` 返回 `1`。不是正常 GUI Quit 或 OS0。 |
| 20:28:52 | 原公共 run 按原 hold deadline 收口，实际返回 `2`；没有延期或重放。 |
| 20:29:18 | ROOT 直接审阅新的 Steam 位移画面：底部“离线模式”、桌面时钟 04:29 CST；随后实际恢复原显示 `1024×768 / 32bit / 60Hz`。 |
| 20:29:57 | 原 keeper STOP 后，原 allocator 实际 wait `0`。 |
| 20:30:19 | screen CAS release 实际返回 `0`，sequence `5024→5025`、done/resources=[]；没有残留 CK3/controller/supervisor。 |

游戏为 Steam CK3 `1.20.0.4`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。Native058 DLL 为 12,861,440 B，SHA-256 `4bb79c021c95f66e786eaa8c539a4d0631ab476a1e881800ab8fb980c516bcb9`；开启既有 Robert 书签目标及 religion context/personal parameters 只读编译选项，不授实机能力信用。

## 后继与验收边界

原版 `00_bookmarks.txt` 中 `bookmark_rags_to_riches_duke_robert` 指向历史角色 `1128`，`norman.txt` 对应 Robert/Guiscard。`29829` 是旧运行时假设，不能作为历史 ID。后继应复用现有 host 的 `frontend_fixture_start_submission` 与 `frontend_fixture_business_context` 两段真实证明，确认 Robert 书签与开始结果后，再绑定首个 paused frame 的 runtime actor，并保持后续 actor/PID/generation/date 一致。不能直接全局替换为 `31254`。

本次唯一终态 native 投影没有保存早期书签证明；末 64 KiB frontend 日志仅证明当前 actor/frame。因此 **本次 `31254 = Robert` 仍 UNKNOWN**。只读设计已封，未采用代码、热修或启动下一轮。现有 adapter 异常后立即进入 normal-close，没有从关闭等待返回业务的热接续入口；公开角色窗口工具与后端支持不一致也须在使用前处理。

本版信条选取、常规与个人效果传播/叠加/取消、同 faith 择学、16 项提示和存载均未取得实机通过证据。旧 B4/C3/I4 状态保持，一期仍 NOT_GREEN。旧试玩存档不承诺自动迁移。

## 有限证据与空间

run 根为 `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0065`；admission 为 `C:/workspace/ck3_lyd_runtime_20261004/i4-root-storage-admission-20261012-028`，峰值 512 MiB，沿原总额度和 review 时间，不自动续期。

- admission 中 `terminal-native-summary.actual.json`：5,234 B，SHA-256 `e3fefd34a70309a7aa07c97345e528cd08df7697e9f9f3b40fd1471c062d8a06`。唯一终态正文投影，保留异常、exit 1 及完整 shutdown；后续只消费小投影，没有再读 native 正文。
- run 中 `keeper-stop-proof-001.json`：5,265 B，SHA-256 `545e98b429b8c7c6833721b138492c9467f2e908aac3a066dbd4595bc65bf820`。
- release `stdout.log`：1,287 B，SHA-256 `21e8be24e5dd8ef43c4d1a82e8bc4aa6c2bf2dd5d877fb3739e54602549aed13`。

此前按精确清单清理 R62/R63 过期、可重建的 profile shadercache：7,488 文件，295,768,556 B，八批实际返回 0；保留 R64 受保护缓存、存档与失败证据。本轮没有复制共享 cache，不声称已复用或命中。空间 credit 仅由 A28 认领一次。

一个 source-only 代理在 A27 关闭后误写了 10,545 B 的身份调查包。旧 closure 原件保留，这笔写入在 A28 峰值内记账，不改写历史回执或重复扣减 cache credit。
