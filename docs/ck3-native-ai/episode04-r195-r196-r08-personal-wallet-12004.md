# R08：R195/R196 实际个人钱包回调的最窄新消费（1.20.0.4）

四个已闭 terminal journal 共31条付款家族记录，个人钱包只有 **2条 ADD、1条 SUB**。唯一 SUB 是已独立闭合的 R196 登船300000；排除后，没有剩余个人 SUB 候选，也没有 return28A6E05/28A6EC2 的 c/d share SUB。**这不证明军费为零，也没有关闭 R08。**

machine_id: `desktop-3fevhd2-1c74096080`。历史原件为 R0195/R0196、source611bc985…/a33；本次离线消费者与引用的当前 source 身份见[源索引](evidence/episode04-r195-r196-r08-personal-wallet-12004/source-index.json)。未调用 SDK、游戏、桌面或新 EXE 读取，未复制/解包 Driver、存档、旧大原件或重跑旧生产矩阵。跨机可复用代码和历史原文，不能据此认可目标机运行状态。

## 全部实际 personal SUB/ADD

下表日期分别是 record 自身 native date 的 low32 与原始 absolute_day；顶层 query 日期、文件时间没有回填旧 callback。角色来自 before/after 原始账户，而不是窗口 actor；ADD 的角色是收款主体，不叫 payer。个人 writer 本行 `resource_kind_raw/component_raw` 三条均为-1。已知登船的 parent gateway resource0/component3 另由既有合格链绑定，不能把-1自动补0。

| 回调 | record date low32 / absolute day | 方向与 raw 参数 | 实际角色 FullID | caller return RVA | 实际钱包字段地址 | 整callback余额bits |
|---|---|---|---|---|---|---|
| R195 s1 | 53148336 / 389514 | personal_ADD 205712 | 31254 | 0x28a6d7c | 0x255b7dab570 | 25804687 → 26010399 |
| R196 s1 | 53148336 / 389514 | personal_ADD 205712 | 31254 | 0x28a6d7c | 0x27592cde570 | 25804687 → 26010399 |
| R196 s2 | 53148936 / 389539 | personal_SUB 300000 | 31254 | 0x28b99b2 | 0x27592cde570 | 26010399 → 25710399 |

三条均是各自 window/epoch 内 sequence3（物理512环槽2）；环槽不跨 clear 作为身份。账户字段均实际 alias `receiver+8 == character_extension+0x100`；两场地址不同，不能互换。具体 PID/创建时间/generation/window/epoch、entry/return clock/thread/sequence、receiver/second pointer、前后余额与原件精确 member/offset/SHA 均保留在[完整 typed 输出](evidence/episode04-r195-r196-r08-personal-wallet-12004/PAIR-CALLBACKS.actual-a03.json)。余额边界是整个原函数 entry/return，不能声称单条原子 store 或新增“支付 accepted”。

R195 旧小型 clarification 没留 receiver/amount 等，因此当时正确保留 unknown。本次从已有便携包的完整精确 cash 原件重新取得该 actual 账户/金额/字段；没有从 R196 指针或窗口 actor 给旧投影补值，也没有改写旧记录。

## 两臂共同出现的是同日期 ADD

两个独立进程都在53148336/absolute389514保留一次 ADD205712，账户余额均25804687→26010399；caller-return均28A6D7C，unwind parent均28F7939。各自同callback四项为 `a=423188,b=0,c=217476,d=0`，完整 before 算式 `wrap_i64(a-b-(c+d))=205712` 与参数一致，after 两边界值相同。

这加强了“同S0两臂在同日复现该正额钱包入账”的实际证据；它是**跨臂复现，不是同一条时间线上重复结算**。每臂只有这一条该 ADD，不能授日/月收费 cadence。217476只是该算式的 raw c 输入，不能称作已付军费；两端 c/d 相同也不能证明中间无写入或找出 producer。

既有源已闭28A6D77→285EE40、return28A6D7C；parent28F7939也已有实际源关系。本次没有把旧 parent 当新发现、没有再扫 E8 或读取 opaque enum。负 NET 源中28A6E05和28A6EC2分别消费 c/d share，但本次四窗均没有这种实际 SUB。两个 share 仍未命名为军事类别，现有 journal 也没有唯一 settlement-parent token，不能靠同日相邻序号拼成同次结算。

## 付款排除与下一缺口

登船 SUB 的排除复用[原生产合格结果](evidence/episode04-r196-r07-boarding-pair-12004/PRODUCTION-PAIR-REPLAY.actual-a01.json)：同 segment/window3/payment epoch3/writer sequence3/payer31254/amount300000/26010399→25710399。新 consumer 逐项绑定该结果；单个 `source_boarding_call_chain_matches` flag 不足以授排除，也没有重跑旧登船业务资格。

本输入没有给出新的非登船实际扣款或 c/d store 地址，故停止沿本对照臂静态扩张。`paid_military_amount_raw/payer/cadence/c_d_producer_store_rva` 全部为 null，`maintenance_attribution=unclosed`。下一有信息量输入必须是新场真实 c/d 写入（明确同代 context/线程/事件、写指令/寄存器）并进一步取得 source 含义，或真正出现的非登船 SUB 与源读取/分量/账户的唯一因果链；不能用更多相同正 ADD、cached2C0/2C8 copy、净钱包差或月率 getter 代替。旧 observer 候选的目录名不是新场分配/准入。

## 复用入口

新增 stdlib 模块 `ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_personal_callbacks_v1.py`。CLI 参数为 `--control-root <R195 canonical evidence根> --treatment-root <R196 canonical evidence根> --output <不存在的新JSON>`；只在内存按现有 manifest 精确切取两个 portable ZIP 的4份 cash，不依赖来源机器绝对路径。它输出观察与 typed unknown，不接入 live policy，也不新增公共 MCP 命令。

新6例及审查新增3例 focused 因果边界测试通过：实际主体不被窗口 actor/RAX替代、负SUB参数不被改为正付款、错误账户alias/未返回/跨window拒绝、raw boarding flag不能代替既有合格结果。旧矩阵和旧生产 pair/control replay 均未重跑。保留原件由既有 canonical 包负责；本新增候选按通用存储策略七日复核，不复制原 ZIP。

审查补充：所有真实个人wallet回调都保留，另显式列 `subject_is_current_player/own_player_personal_account_qualified`；NPC不得改写为窗口actor。缺失c/d端点保留unknown，不能以None==None输出相等。一般SUB的最终payer角色仍未知；只有绑定既有合格登船结果的row填写payer，实际账户subject始终单列。
