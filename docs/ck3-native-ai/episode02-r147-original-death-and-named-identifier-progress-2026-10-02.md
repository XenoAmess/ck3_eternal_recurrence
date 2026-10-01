# Episode02 R0147 原版死亡参数与通知身份补采

截至 2026-10-02 03:58（Asia/Shanghai），六项研究仍按 **4/6，约 67%** 记录；不以新增字段、离线测试或局部因果核验代替完整闭合。视频未开始新一轮改稿、渲染或交付。继续先完成机制研究，再据此优化战争第 2 期，并统一棕黄色系列配色。

本轮使用独立冻结 checkout `C:/w/e2cap1001h`、commit `0a1272ecf8e6eb08bbf1632249c9dc60fe25cd77`。Release DLL 为 `03EB2A0FB97CD804EE62644D5C2C548A22D8E7C68CDDF6F06EFEAAC09F9CD5FF`，实际 native session 为 `native-29829-81523c969e9c`，PID 1860，创建时间 `1790881722.9741042`。daily token `458465814405553892` 与 monitor token `458465814405561105` 分别绑定本轮原件。没有拉取、吸收、合入或推送 master。

实际仅从 `53146848`（1066.12.29）推进一天至 `53146872`（1066.12.30），FINISH 各一次。角色与战斗展示窗口在 BEGIN 前关闭；采样结束并卸载后才重新打开次日页面。原版角色页、双方完整名单、未裁切完整战斗窗与四个保存端点全部保全并由 root 实际审图。目标 33437 从存活、勇武 4 变为死亡标记、显示勇武 2；相关敌方 34120 仍存活、勇武 7，界面威望从 301 变为 451。左名单 11→10，目标移出；右名单保持 19、相关敌方仍在列。显示勇武变化不等于存档基础技能发生同值变化。

原 scoped journal 为 184 条、7 个 phase、flags 0。独立严格因果验收 78 个 gate 通过，目标死亡请求、入队及提交各 1 次；有限 entry/owner 对账与四份真实存档解码通过。新增 original commit enter/return 局部读数均实际读到六参：同一 manager、victim、reason、完整 64 位 date、killer、artifact；实际 reason 为 `death_battle`，date 为 `300064544408663288`，artifact 指针非空但原版引用 ID 为 `-1`。该局部片段还与真实 request/enqueue queue 和 invocation 87、thread 12516 对应。不得将 artifact 的无效引用写成空指针，也不得只保留日期低 32 位。

**monitor 原始 RED 保留。** 实际 13 条记录、未截断、detours 已卸载，但整体 flags 4；signature writer 的 enter/return 为 flags 4。命名死者的四个快照 read false，不能当成 missing 或猜成目标骑士。prearm 标识表计数 51543，邻接实际原版 flag 解码读数为 51544、epoch 0；这与冻结 named reader 的 `current_count == prearmed_count` 检查不兼容。精确失败阶段当时未发布，故只记录已证不兼容条件，不捏造失败阶段。下一修复必须允许同 epoch 的合法 append，同时保持预置索引/原名称、当前头两次读取、完整 scope 与 generation 验证，并发布实际 header 和明确失败原因；必须使用新源码、新 DLL 与新 run，不能更改 R0147 原件。

本轮补充了一次独立只读 Windows `PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ` 结构采样，只有实际 compiled node 的 identity、children 与 optional 元数据读取，没有调用原版谓词、getter、虚函数或额外游戏日期。采集绑定当前 PID/create/module/EXE，局部两次与全图复读稳定，并经过 fresh native pre/post snapshot 和完整 battle control 复核。结构验证通过不证明实际选择了哪个布尔分支；growth/accolade 的有限域解释仍需单独核验，完整 13 域及 global mutable bundle 均不宣称完成。

采集 owner 与 SDK 实际 exit 0，确认无 CK3/录制/注入进程后恢复原 1024×768 桌面并通过任务总线 CAS 释放屏幕。root 实际查看新恢复图中的 Steam 离线文字及页脚。首次恢复误传 preflight 而被拒绝的尝试原样保留，随后以真实 alignment readback 完成恢复；没有切换 Steam 在线。

原件入口：

- [root 本轮停止与审阅封存](C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-11-original-commit-and-scripted-identity/R0147-current-capture-root-stop-seal-a01.json)，7,373 B，SHA `B3DD02A61E41410699815A4F4D3D76E426AF9242EEF0B4656FA7E3AB9EE0B06B`。
- [原始 monitor RED 与六参局部诊断](C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0147-monitor-RED-actual-diagnosis-knights-a01/actual-diagnostic-attempt-01/R0147-monitor-RED-diagnosis-and-local-six-parameters-a01.json)，30,127 B，SHA `AED55E08CAA8161291ACED4B18C3CBCE8DE2CDEFE5CDFE5D6BF77B7B8C4FA402`。
- [本轮完整因果与四保存审计目录](C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0147-four-save-causal-entry-owner-audit-reinforcement-a01/)。严格因果通过与 monitor RED 必须分别陈述。
- [当前 optional 结构原始读取](C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0147-optional-recursive-live-root-a01/collection.json)，29,278 B，SHA `D562463D95669760C916AEA83F769CA1B34C5CE8F639E0876ADB4A8C61342A55`；[独立 post 验证](C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0147-optional-recursive-live-root-a01/post-verification.json)，1,555 B，SHA `130D14699FCA8A927A9953038EF6027D8F7873FCE2DDF308B431A3956EAC7FCC`。

下一轮 `root-attempt-12-identifier-append-safe` 仅完成工具准备，尚未构建、启动或采样。该准备不改变旧 run 的配置、字段或结论。进入下一轮前重新查询了工具链最新正式 Release：实际仍为 0.2.1，wheel SHA `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，使用显式核验的主工作树 venv 解释器。
