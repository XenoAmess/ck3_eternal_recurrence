# C7 首份继承 SEM 的有限续行

机器：`xenoamess-full-tower-eb9d2c1186`。观察时间：2026-10-19 08:13:39 UTC。来源为 [软件资格回执](evidence/c7-succession3851-resume-software01.json) 及其中逐项绑定的 FROZEN77；本文不授予其他机器实机资格。

3851 的原生 SEM 已成功保存。共享交接叶在首份 SEM 返回后的显示步骤导入旧 provider，因此在原 `automatic_handoff` 第415行验证前失败。原交接 audit 只有3851 `received`；Continue、CAP、UI 检查和 SAVE 尚未进入。1839 普通回合已结算，但 `pending_natural_succession` 和旧 campaign goal 仍在，单独清 halt 不能完成继承。

恢复叶严格匹配这份首 SEM、状态、原 audit、原错误、Game PID/出生代、Queue 源和未用3852。它在隔离命名空间运行原交接函数，只替换两处显示 import 为已采用 C6 provider，并使用独立 `RESUME3852` audit 名。原函数其余 AST 完整保留。原3851先经真实 C6 relay 确认，再作为第一次 SEM 的返回值供给一次；不产生该 SEM 的 RPC 或重用其 sequence。之后所有 Continue、CAP、UI、SAVE 等步骤由原算法生成唯一新编号，并执行原业务后验。

软件资格运行真实 C7 `run_request_loop`、基础 `consume_sequence`、`halt_request` AST。原3851供给后，下一次模拟调用为3853 `ck3_auto_turn`；故意使该模拟调用失败，验证新的未知动作保留在3853、旧1839状态未被伪结算。四个精确负例均拒绝。所有写入捕获在内存，所有会话调用为模拟；未执行实机恢复，也未冒称未来完整交接已经通过。

唯一 owner 的采用顺序：

1. 核对 review manifest 与 FROZEN77 的原件、当前 NEXT3852、原 source/state/failed audit 均未变化，确认 C7 进程未导入 known-owner 动态入口。
2. 保留旧 `root_p37_known_owner_recovery.py` 原字节，采用 review 中追加有限分支的版本，并 create-only 安装 `root_p37_succession3851_resume.py`。原已加载 Queue、共享 handoff、SDK 和 provider不改。
3. 将 review 内精确3852请求交既有本地请求通道；不写回共享 CURRENT-REQUEST。该指针保持3851，直至原 SEM 的 C6真实发布完成，再由原算法正常发布新步骤。
4. 独立读回 `SUCCESSION3851-RESUME-SETTLED.json` 与新 audit。只有原尾段真正提交才产生成功回执，其 `final_semantic_response` 和 `final_frame` 是下一次 current-map 绑定来源。
5. 原尾段会更新 `initial_frame`；下一 FULL 前按原 camera 合同取得继承后真实 frozen pair 与 Root primary review。T0、终点和原录制 first-frame 锚保持历史意义。

复现软件资格：

```text
py tools/g2_saved_campaign/qualify_succession3851_resume_v1.py
```

生成独立 review（不会采用或发布请求）：

```text
py tools/g2_saved_campaign/prepare_succession3851_resume_v1.py --output-root Z:/ck3_mod_rewrite/_runtime/c7-succession3851-review02
```

单次 intent 持久化后不能重跑本恢复。后继失败仍保留真实新请求和未知结果，由原队列 halt，不重发原动作。
