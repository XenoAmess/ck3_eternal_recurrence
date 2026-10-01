# G2 后台实施账本：2026-10-01

真实开始记录时间：2026-10-01T14:33:47+08:00。用户明确要求继续并提高并行，且不得占用 CK3。基线为 `9e37d3df4227578fb754d71278810c9492ca948b`，施工树 `Z:/ck3_mod_rewrite/.task-tmp/g2src`；旧 migration 与范围核对树保持冻结。本页承接[八项施工图](g2-offline-work-map-2026-10-01.md)，记录实际施工与交付，不将计划当作完成。

## 当前施工

| 工作包 | 实际范围 | 初始状态 | 实机边界 |
| --- | --- | --- | --- |
| M4 council | 新版候选、四类最终 gate、typed 任命与独立读取 | 正在实现 | paused 候选/门互证、任命后置及 next/cold |
| M4 faction | 完整身份、成员、原生 power/discontent/danger | 正在实现 | 真实派系同帧查询 |
| M4 gift | 原生最终发送、费用、好感预览、typed 操作 | 正在实现，依赖 faction | 合法接收者及 gold/opinion 后置 |
| M5 war cash | 原生维护/费用来源、实际 producer | 正在实现 | 实际战争资源同帧互证 |
| M5 multiwar | 共享军队与全 WarID 的资源聚合，复用预留 | 正在实现，依赖现金来源 | 实际资源争用与联合选择 |
| M5 family obligation | 婚配最终家系、解除婚约成本、联盟战争义务 | 正在实现 | 新版合法关系与具体义务互证 |
| M5 prewar | 真实绑定参与者、原生集结与未来路线输入 | 正在实现 | 合格战前场景；未闭合输入保留明确账本 |
| M6 Sway | 活跃实例、好感、最终发送、typed start、终止语义 | 正在实现 | 实例/提交/完成收益与 next/cold |
| M6 law | active/candidate/final terms、费用、已有 LAW8 源操作 | 正在实现 | 有价值的合法法律后置与资源变化 |
| M6 prisoner | 既有囚犯列表、赎金 final terms、typed 操作与独立结果迁移 | 正在实现，14:35追加 | 真实合法赎金、人物与国库后置 |
| M6 Feast | 现有 Stage1/2/5、宾客、Start、hosted/terminal 语义 | 正在实现 | 合格开始、完整生命周期与收益 |
| M7 campaign goal | 普通目标跨 checkpoint/继承保存并驱动下一计划 | static-ready，19+19 fixture GREEN | 自然继承后的实际消费与冷恢复 |
| M7 government | 新版真实 feature profile 与既有封建选择器 | 正在实现 | 实际 runtime 身份适配互证 |

中央 native owner 统一 CMake、bridge、adapter/worker 和 owner mailbox；中央 Python owner 统一私有查询、版本解析及 MCP 接线。目标续接 owner 与 Python owner 按方法块分工。域内原生链继续拆并行子线程；编译使用 64 jobs，每个 build 目录只有一个写者。

## 输入与验收

唯一新 build 输入是冻结 CK3 `1.20.0.2 Crozier / Steam 25588574`，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。实际 provider 必须先有当前原生树与 exact ABI，再进入同一 MCP 和必要生产路径 fixture。共享 candidate/default 构建、源文件及二进制 manifest 由中央收口；不重跑不受影响的已 GREEN 矩阵。

所有运行只使用文件、编译器、mock/fixture；不枚举或查询 CK3 进程，不连接游戏 pipe，不操作游戏、桌面、Steam或当前 profile。全部临时文件、日志与构建在 Z 盘。新私有动作沿既有默认关闭约定，ACK 不能作为结果；不会通过零填 unknown、变更战争意愿或解除 owner/date hold 来造 readiness。

G2 仍 `3/8`，Robert `3153/36524`，新增游戏日为零。宗教/holy order 保持暂缓，婚姻与战争所需最终判定仅使用最小 opaque 输入；其它政府仍保留既有未实现边界。每包在必要验证完成后独立提交并普通 fast-forward 推送，剩余包继续施工。

## 交付与结果

尚无本轮新增完成或 live 结论。域结果在产出后追加具体 commit、测试、artifact、readiness 与未闭合项。外部协调与构建产物入口：`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/`。

14:35追加第13个源码包：现有囚犯列表/赎金旧版native transport尚需1.20绑定，M6明确要求一项囚犯或制度动作，因此并行移植已有ransom路线。旧R0404/5/6 count0保留为当帧真实空场景，不造囚犯或等待自然阳性worker；新包仅迁existing source与消费，不扩刑罚/宗教框架。

### 14:45:01 M7普通campaign目标续接完成

真实driver/service/planner已保存普通 `dynasty_continuity` 意图，沿persisted-v2与既有hot/cold消费者保留稳定campaign ID。fixture中actor100→200通过已有M3 estate核验，继承进度为1，后继实际下一正式计划选当前ruler婚配查询；同目录rogue历史war-first不会覆盖普通目标，rogue原分支仍保持war-first。native_auto_run报告投影同步加入 `campaign_goal_plan_used`，真实service已输出该字段。

新4项与已有succession15项正常模式通过，组合19项 `-O`通过；没有重复已GREEN的全矩阵。结果[artifact](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/campaign-goal/result.json) SHA `e3e59ce40265ee4f68da9714efb800de7dc3b96944dc6c59c0889dc96aae45f1`，测试receipt SHA `1cf9874e42cc28d20f6698c257af09a498882cc0f638441f75e4a1143804ab8a`，初次fixture断言错误保留。源码与边界见[原生输入/消费专题](../ck3-native-ai/ordinary-campaign-goal-continuity.md)。状态仅static-ready；自然继承、游戏checkpoint/new PID、实际家庭结果和后继回合仍需live。其它12包继续后台，不因本包已到live边界停工。

### 14:46:44 M5默认原生集结合法性源码交付

新版默认集结点最终原生合法性已实现：validator `0x298C2C0` → final legality `0x24A48B0`，只构造临时上下文查询，不submit。实际x64 Release `/O2 /W4 /WX`编译和生产路径fixture PASS，三条exact call-chain ABI verifier PASS。专题：[默认集结](../ck3-native-ai/ck3-1.20.0.2-prewar-default-muster.md)；耐久输出 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/prewar/default-muster-wire.json` 与 `prewar/muster-build/build-receipt.json`。状态只为该原生provider的static-ready，公共query route由中央接线；完整future roster/muster/supply与强制参战provider继续并行实现，不把当前合法性冒充未来军力/补给。实际paused互证仍待live。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 14:48:25 M7新版政府真实feature消费源码交付

既有observer/source adapter/binder现已按双版本真实绑定：1.20 campaign/features原生producer→同帧sourceadapter→语义选择器→owned query serializer。新版44项feature实际含by_god_alone而移除barter_troops；旧版44项profile与136项stockflags继续保持，新版18 government rows/171 flags按冻结原版读取。宗教/holy-order身份仅opaque/deferred，其它政府仍为adapter_spec_ready_not_implemented，未外推18政府策略完成。旧3个fixture与实际new44producer在/Od及/O2/W4/WX通过；stock差异增量后只重建新fixture，最终receipt `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/government/stock-profile-final-v2/receipt.json` SHA `f08560ac3eb9155e2e21e079effdfa9abe994c5e0f3dc173021c7b46e5903169`。新版stock verifier18/171及旧sourcecontract4项GREEN；实际C++available/unavailable JSON→driver→官方MCP SDK list/call6项GREEN，Python/中央permit尚另包接回。专题[新版政府适配](../ck3-native-ai/government-runtime-adapter-1.20.0.2.md)。本包native/source消费static-ready，真实paused、封建正式效果、跨ruler/seed/government仍需live。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。

### 14:50:20 M5强制朝贡参战者实际reader交付

现有强制朝贡参战链已移植真实1.20 direct-slot source reader，读取完整ID并保留原生顺序与重复；实际新版land `+0x1C0`、DB `+0xF00`、default `+0x9F28`已落代码。Exact ABI核对6 spans/10 instructions/7 calls/7 RIP/2 literals及RTTI/stock SHA GREEN，MSVC `/Od`与`/O2 /W4 /WX`生产fixture各11 cases通过，真实serializer JSON已解析。耐久结果：`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/prewar/participants/fixture-result.json`、`abi-verification.json`、`Od/forced-participants-wire.json`及`O2/forced-participants-wire.json`。专题[战前强制参与者](../ck3-native-ai/ck3-1.20.0.2-prewar-participants.md)。本包只提升这一来源static-ready，完整宣战参与者、自愿盟友、集结与未来补给不外推完成；其具体producer与中央MCP route仍并行施工，真实paused最终互证待live。

本包按精确清单独立提交和普通FF交付；公共接线及其它原生包继续后台。无CK3/进程/pipe/桌面/Steam操作，没有新增live、游戏日或G2成绩。
