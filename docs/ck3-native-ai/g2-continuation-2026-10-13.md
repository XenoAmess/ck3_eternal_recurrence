# G2 接续实施（2026-10-13）

接续 [休假交接](../handover/2026-10-13-g2-native-maintainer-vacation-handoff.md)，实施输入为干净的 `6feaef84953fdaf0d26244744a5c4ddbb75286c6`。用户要求的 64 个并行研究任务按 M0–M7、每组协调者兼研究者及七个专项执行；本次复用原任务继续实施，没有将任务数当作能力完成度。

## 首包实现与验证边界

| 组 | 实施结果 | 定向验证与剩余边界 |
| --- | --- | --- |
| M0 | 普通策略接入已有守方白和；多战争先消费已资格终局；runner 接受既有 terminal_score_defeat；统一只读终局材料摘要 | 白和 1、多战争 7、runner 1、摘要 5 个新增用例通过。actual4 最终接收方 evaluator 的 flag0 来源仍未闭合，保持 unavailable；没有编造答复 |
| M1 | 核心完整、可选规则未知的同帧根查询可用；根查询省去完整 history 复制；透传 nullable immediate_liege；当前风险材料与实际 Driver 形状一致 | 根查询消费 1、history 所有权 1、liege 4、实际风险链 2 个新增用例通过；风险摘要不声称解决分封或最优继承 |
| M2 | .1070.c 明确有界选择理由，新增军队的独立材料比较；Feast 当前意见 utility；Rite fulfillment 材料；自然派系要求独立适配器 | 19 个新增 leaf/dispatch 用例及 Rite Service 连接用例通过。`.1001` 缺少完整当前军事决策输入，适配器不自动选择；不以任意兵力阈值替代来源 |
| M3 | 在原事件循环和 SDK 队列中包装既有继承交接，先保留 pending，再消费原 completed，采用后立即返回 successor SAVE 对 | 9 个新增异步用例首次通过；30 回合 fresh 演示仍在角色/episode 改变处停交 Root，不把离线夹具算自然继承 |
| M4 | MCP 透传既有 LIFE 配置；赠礼 preview 稳定优先危险且未开战派系；原 tier-one 建设目标优先占用既有有界扫描预算；已解决赠礼可独立读回 | LIFE 与赠礼注册连接用例通过；建设扩展矩阵先复现 RED、最小修复后 GREEN；未扩大扫描 cap。通用 Council task 来源研究不等于新增实机能力 |
| M5 | 强攻传入 commands；四个资源消费层允许合法 ArmyID 0；目的地专属拒绝继续现有候选；宣战保留原请求并核唯一实际战争身份；婚配关系字段保留 | 新增强攻、路线、ArmyID、Driver 连续性及 Service latch 用例通过。非空开战脚本仍须实际 tuple/Node 和具体 operator 来源，不能由 CB 名字授权 |
| M6 | 普通 Service 回合复用现有 Sway completion、termination、opinion 观测；runner 使用同一实现；终止轮询不复制完整 history；Sway startup 先建立 execution session | 新增连接及有限返回用例通过；startup 顺序回归为源码检查。已有 Feast bootstrap 保留，没有重复新增 API 或门禁 |
| M7 | 生命周期消费真实字典；bridge_pid、hello、launch PID 一致；supervisor 保留 queue/application 实际代际句柄，配对确认后才 RPC；pending 保持原 SDK、仅诊断和 collect 原请求 | 生命周期、代际/退出回执与连接握手的新增检查见外置逐项回执；wrapper 退出不能代替 application 内核退出。实际 cold recovery 另记 |

所有源码/离线夹具结果与实机结果分别记账。首包不重新验收旧 M0–M5 矩阵，不给 G2 总体、稳定战争、M6/M7 整局能力授予完成信用。

启动前实际进程检查还发现本机 venv `python.exe` 是重定向器。队列自身份按实际 base interpreter 核对；SDK application 直接启动同一 base interpreter，并显式加载固定 venv 依赖（含 `.pth`），要求 MCP 2.0.0。真实短进程检查独立于 Game；不能把 redirector wrapper 的 PID/退出码算作 SDK application。

## 输入、容量与构建

本机外置工作包 `R = D:/codex-ck3-background-spill/g2-remediation-20261013`，本次回执在 `R/resume01`，新开局 attempt 在 `R/fresh-robert02`；旧 `fresh-robert01` 及硬链接冻结输入保持原样。所有任务共用原 8 GiB 组预算；`STORAGE-CONTINUATION-ADMISSION.json` 记录续作实际容量检查，不新增 64 份预算。

原复核期限仍为 **2026-10-13 16:58:39.018273 UTC**，重型新写入最迟在前 15 分钟停止。冻结、原始返回、测试失败和派生资产均按 [统一存储策略](../storage-retention-policy.md) 在该时点复核；保留不是永久承诺。独立录像最多 1200 秒/1 GiB。

Native 增量构建：B7 只补编 bridge 与赠礼 router 两个直接链接 TU；B8 再补编 construction 一个 TU，并重建 612 成员 runtime archive、重新链接。没有全量重编或热替换 DLL。B8 的 retained 对象继续继承 B6/更早的混合来源，不能声称当前 HEAD 全树已重编。

```text
R/native-profile/build08/native.dll
18260992 B
SHA-256 75fa14e95e0deedb0db7e05b3530e238631d7fb475ecadfb542300bfbb57dc80
```

实际 compile/archive/link 均返回 0；Native 生产组当时合计 1,237,829,676 B / 2 GiB。源码顺序修复、编译成功、实际冷载和业务效果是不同证据层级。

## 新罗贝尔实机记录

首包提交时尚未启动新 Game/录制。后续须由 Root 在新 clean freeze、任务总线 CK3/屏幕独占、已接受的 Steam 离线确认下执行：独立录制开始且文件增长、亲审首帧后，route/New Game/1066 Robert Start 各一次，核初始角色、日期、ordinary/no-pact 生命周期和 SAVE 对，再运行完整普通规划器。最多 30 turns，每 5 turns 核对并保存；unknown 保留原结果与原请求，不重送。

实际日期推进、动作结果、配对 SAVE、录像、Node 输入和正常/强制退出分别追加当次回执；本段准备状态不能充当这些事实。

## 外置交付索引

- M0：`R/resume01/m0/{white-peace,multiwar,cold-terminal,postconditions}`；最终接收方保留来源缺口。
- M1：`R/resume01/m1/{history01,lane1,lane2,lane4,continuity01}`。
- M2：`R/resume01/m2/coordinator/DELIVERY01.json` 与各 leaf 首次/更正回执。
- M3：`R/resume01/m3/DELIVERED.json`。
- M4：`R/resume01/m4/coordinator/FREEZE-DELIVERY.json` 与建设 RED→GREEN、LIFE、赠礼连接回执。
- M5：`R/resume01/m5` 中 Strategy 集成和各首次结果。
- M6：`R/resume01/m6/ordinary-sway/{DELIVERY,FREEZE-SOURCE-PINS}.json`。
- M7：`R/resume01/m7` 及 `R/fresh-robert02` 中 harness 固定与逐项验证回执。

外置证据到期回收后须明确记录原件不可读，不以同名文件冒充原始证据。
