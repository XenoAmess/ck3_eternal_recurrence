# P43 四批自然材料与民粹最后通牒复核

有限审计固定为已完成 FULL0107、0168、0231、0302，未追踪后续活跃流程。四批正常结束，读到的120份 MET 均为 living Robert31254／同 episode；92份普通计划的 dynasty goal 都是 reconciled_successions=0，Feast no_tracking。7份既有 SEM 没有终态或继承 reconciliation；未发现可增加 M6/M7 验收信用的 Sway／Feast 终态。G2仍6/8；13份超过本次256KiB投影上限的 AUTO 未分类，不能把本审计写成全部字段的全覆盖。FULL累计日数也不是当前连续稳定窗口。

AUTO325、329、363的 Feast opportunity 明确返回 `unsupported native gameplay step`，普通流程继续；这证明当前实例机会输入仍缺，不证明宴会已举办。

## 实际让步及材料边界

AUTO193面对 faction_demand.1001／instance41／calculated3571001，当前可见且可用的只有 native2（API3，授独立）与 native3（API4，拒绝并开派系战）。原版另两项是文化／信仰转换与 state-rite 转换妥协，本次隐藏，不可凭四个原生定义数猜可选项。原选择 native2 已真实 advanced，不能撤回、重放或改写。

授独立项实际调用 `successful_popular_revolt_outcome_effect`；非 state-faith 分支会收集派系县所属公国内仍归目标 top realm 的县，再转移／独立，因此它并不保证只影响 target2200一个县。拒绝项直接 `faction_start_war(title=scope:target_title)`，存在战败风险。该事件绑定没有同帧派系战力，原版 AI 权重也未实际求值；不能宣称拒绝无条件最优。

已落实际 held-estate 从 SEM44 的 [2196,2200,2230,2231,2262] 缩为 SEM225 的 [2230,2231,2262]；新 estate binding 精确 native4191，与 AUTO193 post 一致。MET192→194 同游戏日、native4190→4191，战争数2→0。这是领有集合缩减及战争数消失的真实时点材料，尚无新 holder 独立标量查询，不夸称所有因果已闭合。2200=c_siracusa 已由原首战材料绑定；2196=c_messina 目前只有同 stock source-order +6 的推导，明确保留为推导。首战确胜、且当时2200入领地的历史事实不变，不能推为当前仍持有。

## 已知策略为何仍漏，以及最小候选

初始58组仅 character_event 静态 seed，明确不携 letter_event 的旧局 ID；本次原 before 为 unknown，按用户规则选可用选项。既有拒绝 hook 另硬锁旧 calculated3551001／f4179448指纹，本局3571001／14b787d2即使学成 known，也仍不会命中。batch0168两个事件都已被旧 P39 wildcard worker 分析并发布源知识，unresolved=0；通用 source-reviewed 分类本身仍是 first-rendered，不能代替语义优选。

外置单叶候选仅修已知 exact 源的当前 ID 绑定：保留 .4 源 SHA、完整选项目录指纹及原来的 Native/PID/generation/frame/actor/roles、两按钮映射、enabled 与 advertised step 守卫，以当前计算 ID 重算应有 exact 指纹。通用 letter rebind 仍不放开；unknown 仍按既有兜底继续。选择延续已批准的保地、接受派系战风险策略，并明确记录两条可见代价、力量未知和反事实非最优声明。现43源／游戏未改。

已用实际 MET192+AUTO193 投影及现生产只读 source loader 复现旧 known hook 仍选 API3，候选选 API4。29项聚焦测试通过：10个本局动态绑定／普通 Strategy 注解和 hook／Service 前后采集与 receipt，19个改动叶相关旧兼容。Native动作与拒绝回执均为合成 seam，无新战争、胜利或保地信用。错误 native2 回执仍保留、禁止重放、不给业务成功信用。

源、四批、before/after、学习发布、held材料、测试和候选精确 SHA 见同名 AUDIT JSON。下一步仅在必要维护窗口评审 COW；不要为该研究停当前游戏。

[本仓库AUDIT投影](evidence/p43-populist-current-source-and-natural-audit-2026-10-17.json)保留精确来源。本批已将该单叶候选窄合公共源码并运行相关旧／新测试；当前SDK43冻结源未改，合成拒绝回执不记作本次实机拒绝或保地成功。

## 2026-10-18 机器身份补注

本页及对应 AUDIT 的历史材料记为 **`machine_id: unknown`，所属机器未核实**。两份保留原件均没有 `machine_id`，也未附可绑定至该次历史采集的机器身份原始证明；原 AUDIT 的 `at_utc=2026-10-17T13:10:29.372929+00:00` 及全部历史结果原样保留。路径、盘符、角色、Git commit，以及现在能读取文件的机器，均不能用来追认历史执行机器。

本次只追加身份说明；补注执行的 `machine_id: xenoamess-full-tower-eb9d2c1186`，实际审计 UTC 为 `2026-10-18T02:33:55.180567+00:00`，身份出处为当次 `python -B -X utf8 tools/ck3_live_run_id.py machine`。该身份仅证明此次补注的执行机器，不赋予 P43 历史安装、环境、部署、实机或录制事实以当前机器效力。

出处为[保留的 AUDIT 投影](evidence/p43-populist-current-source-and-natural-audit-2026-10-17.json)及本页。AUDIT 补注前 SHA-256 为 `4c65c1ba58e7cddebdd99e5a049fba05ec28d4af7af22d0c0abfa6af913a1eed`，补注后为 `04df7c14ffa2f3cd33c819d7d33ced3c1c884ce270edf442e244a1c761ad5af7`；新增字段保留原件的精确字节重建方法，既有字段和值未改。本次未读取旧 Driver、SAVE 或媒体正文，Game／MCP／SDK／OBS 调用为0，业务及 G2 信用新增为0。
