# R215 R08：c/d writer → 同次 NET 的最小真实取证路径

本件为离线源码候选。研究主树 `191568c281bbde92feeb9f96fe40736be1b63ca8`，a36 原生源 `7a342116d8aaa8a4c645941199c3ef1abd0a7c8f`，机器 `desktop-3fevhd2-1c74096080`。只消费已保留 exact .4 小 source/asm 和既有 observer 合同；新 EXE 读取、SDK、DR、桌面、构建、主树及 native source 修改均为零。当前 R214 继续原 core-only actor。R215 的实际身份、容量和 DR 授权尚未产生，不能由本文授予。

## 确切消费点与账户写回

已保存 28F7840..28F7C9E 父函数的 RDX 是实际 Character，保存到 RBP。`28F7931: 48 8B CD` 将它放入 RCX；`28F7934: E8 D7 F3 FA FF` 调 28A6D10，返回 28F7939。此前本函数没有 CALL，只更新 secondary context 的 +3E8/+3F0；没有 c/d 的直接生产 store。后续 ExpenseContext、军事费率和 +4A0 分支均在此调用之后，不能充当同次更早 NET 的直接输入来源。

28A6D10 的确切输入和正路径：

| PC | 原 bytes / 指令 | 当前可证关系 |
| --- | --- | --- |
| 28A6D16 | `48 8B 81 C0 01 00 00` MOV RAX,[RCX+1C0] | secondary 为指针，Character 保存在 R15 |
| 28A6D29 | `4C 8B 40 28` MOV R8,[RAX+28] | c 的实际读取；不是 writer |
| 28A6D32 | `48 8B 98 C0 02 00 00` MOV RBX,[RAX+2C0] | a |
| 28A6D39 | `48 2B 98 C8 02 00 00` SUB RBX,[RAX+2C8] | a-b |
| 28A6D45 | `48 8B 70 30` MOV RSI,[RAX+30] | d 的实际读取；不是 writer |
| 28A6D4E/52 | `49 8D 3C 30` LEA RDI,[R8+RSI]；`48 2B DF` SUB RBX,RDI | wrap64 NET=a-b-(c+d) |
| 28A6D6A/71/74 | ADD RCX,F8；MOV R8,R15；MOV RDX,RBX | wrapper=*(Char+1B0)+F8，原 Character 与实际 NET 参数 |
| 28A6D77 | `E8 C4 80 FB FF` CALL285EE40 | 正 NET ADD；返回 28A6D7C |
| 285EE54/57/5F | MOV RBX,RDX；MOV RDI,RCX；MOV RBP,R8 | leaf 保存 amount、wrapper、Character |
| 285EE67 | `48 01 5F 08` ADD [RDI+8],RBX | 真正个人账户写，地址为 *(Char+1B0)+100；写后 PC 285EE6B |

负路径现有两次个人 SUB：28A6E00→285EED0，return28A6E05；28A6EBD→285EED0，return28A6EC2。实际 store 为 `285EEF7: 48 29 5F 08` SUB [RDI+8],RBX，写后285EEFB。它们使用已闭合 28A6B50 的两阶段整数分配，不可强制两笔之和等于 deficit，也不能仅按 c/d 次序命名军事币种。

正路径的 whole-callback entry/return 对账已能由 a36 kind2/caller28A6D7C 保全，包括 raw四项和 unwind parent；它没有观察 285EE67 指令级写前/写后，也没有整个 settlement invocation 的唯一 token。c/d 真正 writer PC 当前未持有；父函数、两个复制 MOV 与 scheduler 均不能替代它。

## 现有 a07 probe 能做、不能做什么

精确旧观察器是 `maintenance-writer-cold-a01/build-a07/maintenance_writer_cold_observer.exe`，历史 SHA `67e5f6c0bb43ff0c00116be7356da25d792d1eb275a85fe719bf0b7bff32cce9`，102912B。历史 build-a07 绑定 source-a08 `cold_observer.cpp` 23688B/SHA `24b9d584ee451ef822c6386484efcda2578072cb5569ce1740b910e3bbadd0ee`。当前仓库 cpp 另含 optional copy-caller，不是旧二进制的依据，不追加该参数。

旧二进制已有 DR0=secondary+2C0、DR1=+2C8、DR2=+28、DR3=+30 的四个 write/LEN8 slot；固定 DR7 mask 为 0x99990055。最短有效新观察目标就是 DR2/DR3 的真实 post-PC、GPR 和精确有效地址，不重新研究 raw4/+4A0，也不需要重定向四槽。a/b 事件仍保留且计入全四槽 128 次上限。

它的 trap 原件包括实际 thread/generation、QPC、FullID、Character/context、slot/address、DR6、RIP_after、通用寄存器、last-observed before 与 post-write after。保留同值写。RIP_after 不是指令起点；before 不是原子写前值。terminal 明确 `full_window_all_writes_covered=false`，actual writer game date 为 null。因此 **同 window、同值、同线程或相近 QPC 均不能直接授同次 NET join**。付款 event clock/sequence 不是这份 raw 的 QPC，不能编造二者精确时间映射。

新鲜 c/d post-PC 是下一唯一有限 source 入口：以 post-PC-1 申请包含指令末字节的 actual .pdata/root，完整解码实际函数，找到恰好结束于 post-PC 的 store，再用已保存实际 GPR核对写址是否覆盖 secondary+28/+30、store width 与来源寄存器。对于 string/SIMD/会更改基址的 store，post-state 不足时如实保留，不能通用倒推 pre-state。只取得 copy 时继续追它的直接输入/实际 caller，不能当场授 military producer。

## 新发现的真实执行阻断：原 null episode

旧 `build_card.make_card` 要 expected.episode 为非空 str；现 prepare adapter 将 snapshot.episode_run_id 与 --expected-episode(str) 全等比较。更关键的是 **build-a07 对应 frozen source-a08 第236行也在进入 Probe 前要求 meta.episode_id 非空且仅含标识字符**。这不是后来 optional copy-caller 新增的门。

R213 普通 native_campaign 已实际保留原 episode=null。若 R215 同样是 null，旧 a07 **不能原封运行**：Python 预备先拒，即便只放松 Python，native parser仍会在 attach 前 exit2。不能填 `None`、`unknown`、runID或自行拼装 native-* 当假 episode。未来新场若原始合法模式本就提供实际非空 episode，可按原合同运行；不预授这种现场。

要支持原 null EP，最薄正确修改是独立 observer 输入版本支持显式 `session_basis=native_campaign_owned_no_load`，将原 episode 保留为 null，并绑定实际 PID/FILETIME、connection generation、player FullID、controlled window/epoch、实际 GameState witness、Character/context 与 no-load 合同；原非空 episode 路径继续原校验。涉及 observer Config/parser/start JSON、prepare metadata、actual consumer bind_inputs，以及 build_card/公共 wrapper 的 optional episode DTO。不能改成无条件删除 EP 守卫。此修改需要独立小 observer 冷资格及其新 EXE/SYSTEM登记，不是 a36 DLL 新构建。本轮按 Root 禁构建/禁 source 改要求，仅列出精确范围，不生成或套用该修改。

`root_r212_writer.py` 还硬锁旧 H2、runtime、scene、cap、prior county result；不得在 R215 直接执行旧 --adopt/--execute。可复用的是其中已核公共 seam：`r08_writer_common_adapter.collect_current_context`、`bind_legacy_driver` 与 pinned `writer_root_driver.prepare/observe_prepared/finalize`。新场仅绑定 Root 最终实际 inputs，保持同一个公共 CaseClient/retained handle，不重新初始化游戏或新建 host。当前 bind 的 prefix 为 r207-...兼容前缀，新 scene 内仍须独一 request ID。

## 后继一个自然日的最小窗口

1. 从 Root 将保留的 Mar31 normal checkpoint 新冷载；只在 actual owned identity/paused/map-ready/alive/无 modal 后准备。普通 cap external=false 不够，需独立 Root 实际 DR supplement、同卷预算和唯一 slot owner；不与 R06 probe/debugger重叠。若原 EP=null，先解决上一节的实编 ABI 门，不以失败场学习该已知错误。
2. 暂停态完成正式 --for-observation、fresh natural_phase ON、payment enable合同及独立 query读回。保存本次 Character/context 四值、实际 window/epoch、PIDFT/gen/player/GameState 以及 before snapshot/cash 原件；中间不 Save/load。Mar31→Apr1 仅是本次候选机会，不是已证 settlement cadence。
3. 复用现 prepare_writer_admission.py **--prepare-only**，timeout30000、max-slot-hits128。预备可45s在观察窗外完成。其实际 ADMISSION.argv 是唯一启动来源。不要把准备挤入3s hook，也不要先启动 observer再慢速做整包读。
4. Root 持 Popen 仅启动一次，真实 ready:true 且 armed_thread_count>0 后走既有 fresh snapshot/cash guards；old writer 在开始后18s内不满足 headroom就不提交 day。只提交该原有 canonical one-day一次，结果未知不重投。native实际观察最多30s，整个actor自然退出/收尾45s；一天若未落在实际watch覆盖内，结果仅部分。
5. Root独立 after snapshot/cash，原payment window仍同epoch，保全原记录，再等 observer自然终态。消费实际 restored/detached/pending/线程恢复；不强杀。query、consume、payment disable、natural OFF/clear和终日期新Save在正常关闭前完成，保留原normalclose预算。
6. 现二进制这一窗口的成功产物是 **实际 c/d writer post-PC + 完整源请求**；不是预先承诺 maintenance paid。命中c/d后才有必要定位其源函数和军事类别。无命中、128被a/b占满、超时或无generic callback都不否定payer/cadence。

## 同次 NET 真正还需哪一条低影响桥

当 c/d producer 的具体军事语义已有 source 时，最薄同次桥是现有 payment observer 增加 **28A6D10 一个专用 entry/return source slot**，不加 top query/新 SDK 动作/通用trace框架。已持完整16B前缀 `41574883ec40488b81c00100004c8bf9`，全部整指令且无 RIP-relative；入口 Character在RCX，不能误用父函数入口的RDX。沿既有 trampoline/原调用一次/return bits/采样permit/session/sharedclock 实现，另有 actual fixture资格后才能启用。

entry建立 TLS settlement token，保留实际 caller、Character/context、四原始值；ADD及两个SUB子记录保留这一 parent entry event；return发布完整parent。消费要求同clock/thread/session/Character、parent.entry < child.entry < child.return < parent.return、完整retention和原函数called/returned，正路径对实际 NET/余额对账，负路径保持两笔真实amount及allocator舍入。producer store若发生在该parent之前，必须用实际producer source/调用生命周期和明确的状态消费关系接入，不能谎称它在parent内部。

精确未来修改范围：`include/xar_bridge/war_payment_passive_12004.hpp` DTO/optional parent；`src/war_payment_passive_12004.cpp` TLS+原调用边界；`src/war_payment_runtime_12004.cpp` source slot+defaultOFF安装/回滚；`src/war_payment_json_12004.cpp`；Python `war_payment_observations_v1.py` strict join；必要独立 focused fixture/宏传播。不是修改 boarding predicate 来接纳任意NET。该桥只闭合“同次结算应用”，c/d军事语义和 cadence仍由真实producer与跨机会记录分别证明。本轮没有 native patch。

最小可闭业务链应最终同时具备：c/d实际store与业务源 → 本次消费的component → 同次settlement token → 真实钱包store/原始payer身份 → 本次actual date/调度入口。一个支付样本可证本次payer/amount，不能单样本证明全局周期。视频当前只可说“已找到四项进入个人NET的精确读取/写回链，正等待c/d真实writer”；不能说已付军费、月初必结或相同值复制代表支付。
