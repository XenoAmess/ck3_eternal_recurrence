# H2743 守方 de-jure 退出只读实机 attempt-11

2026-09-28 的精确 H2743 checkpoint 在本机完成一次受管只读重放。证据根目录：
`D:/ck3-research-artifacts/war31-h2743-20260928/attempt-11-dejure-baseline-no-launch/`。
`live-dejure-readonly-v3/read-only-result.json` SHA-256
`647D0A2804E6F5E7F6402813332E40885578496E8474129FFC52A45F47B00F8D`。
旧 attempt-10 因 runner 只等 300 秒而在地图加载期间 RED，保留原件，不把它追认为成功。

## 准入与受管退出

- 新 `ready-summary.json` SHA-256 `7A58CA10D52D7B5EEF889F4ED137BA3F78AF1FC326DEE309D4D3674C1CD5F04B`：prepare、rebind、preflight 均 exit 0，未启动 CK3。
- 新 Steam 窗口位移与像素变化截图 `steam-frame-01/steam-moved.png` SHA-256 `36BC70121C326A9826389996EF90918208AE0053FCA66B79B7116DFB33CD8A88`；直接审阅画面左下角“离线模式”。`steam-gate.json` SHA-256 `1845080E270967F92D59C3FB4D3471D11E237DAE70B631DB333882E651CAF88B`。
- 精确输入 save `A5012030…5106E9`、source driver `F31460BA…15069`、family sidecar `12D7B2B0…4B5724`、source DLL `8C3A9523…7A8A5C`。本次 loaded module **路径及当前磁盘字节**审计：CK3 EXE `2D00FF31…3DB86`、候选 DLL `6689ED3B…1B17E`、injector `C89F1A91…A84FF`；不声称已校验内存映像字节。
- `lease-heartbeats.jsonl` SHA-256 `5873A337F079E396AD4235783FB47166F23FFDDB707ECE4648183D8CA37EE581`，读取期每分钟独立续租，均为 `renewed`。`session-exit.json` SHA-256 `F1C5F309BFE386F878002410863BEA0F8D506CB54F8BB71C41353A67042459EC`：supervisor returncode 0、stdout reader 结束、CK3 PID 空、源及候选哈希复验匹配。随后任务总线 seq1862 于 14:39:17Z 标记 `done/resources=[]`，独占屏幕释放。

## 同一暂停帧读数

前后快照均为 `native:3`、revision 4、native revision 3、date raw 53217264、connection generation 1、episode `native-29829-2bc2d599f7f9`；WarID 16777231，Robert 29829 是主守方，Landolf 30097 为主对手。两次 `query-defender-de-jure-exit-terms-v1-16777231` baseline 完全相同。原始 payload SHA-256 分别为 `692ACA05F79C2E0D8EACB1144721D908D1D3BFE22B98B223AEBB3C360A5BA08A` 和 `0E164265CE05A25515735D2058D2387CE3AB1E8F4AF006E07ABDE862A369B153`。

baseline 只证明目标 Title2128 当时 holder 33435、其直接个人领主 29829，以及双方 14 行资源**余额**和 2 行月度金币收入。`material_complete=false`，`title_vassal_delta=null`、`signed_resource_delta=null`、`directed_truce=null`。这三项空值不能变为零，也不能从前态推断终战后领地或现金。

同会话 `query-war-termination-options-16777231` 的 request/envelope/payload SHA-256 分别为 `FD2C5068A33C0D4673145A8533F2F4FFF834E5485B25030AF192A6535AD498D8`、`A15347875644C005FB5975FA5F09AD2464E457EBA52CF5FC2BBFD30F58FF0D2D`、`D7C6A50F5120944B4C53C42B52D0C64734BE9B169235F1C5764B3AABEA0DD2EB`。原生 CB 为 index 17 `individual_county_de_jure_cb`；此帧守方投降合法、对方会接受，white peace 和 victory 不可用。投降选项本身仍明确 `terms_observable=false`、`terms.status=unavailable`、`terms.reason=cb_specific_terms_not_observable`。这是**直接只读查询**，并无正式 planner `selected_step` 或 `priced_command` 身份，不能单凭它填 R0266 即时费用 0。

本次未执行投降、白和平、日期推进或其他游戏动作。V2 比较器仍拒绝 H2743：runtime target scope、终态 title/vassal 图、动态 CB 威望因子、14 行资源签名差额与条件支路、实际单向休战期限、同帧续战损失上界均缺。当前可复用退出动作前置合同继续 fail closed，不授权终战提交。

## 同帧续战风险的窄投影

[只读投影器](../../ck3_autonomous_player/native_bridge/research/project_h2743_attempt11_continue_risk.py)将上述已清理的精确 `read-only-result.json` 与其 SHA 绑定的前快照喂给已交付的 `formal-defender-continue-risk-envelope-v1`。外置 `continuation-risk-v1.json` SHA-256 为 `2C9458861E5E03F8C095AC6324E003F86221DDC6DBF713DE807A75CC4777E68F`。同帧只确认玩家相对战分 `-12`、敌军 `50331920` 在玩家附庸省份 `2628` 围城、当前计时估计剩 `1` 日；`date_raw 53217288` 是估计完成点，**不是上界**。本次没有同帧路线接触查询，接触边界仍为 `typed_unavailable`。投影固定 `continuation_loss_upper_raw=null`、`material_comparison_ready=false`、`recommended_outcome=null`、`action_literal=null`，不能用一日围城时钟推出应投降或应继续。投影聚焦测试检查同帧估计和源/清理/时钟缺失拒绝，普通及 `-O` 模式各 2/2。
