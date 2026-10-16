# R08：copy 首个 callee 的关联 ID 清理（1.20.0.4）

新静态来源 `[28D6170,28D63E1)` 的625B普通 own-body 过滤/压紧关联 raw FullID occurrences，并扣减 descriptor count。它没有固定的 secondary context+28/+30 或 wallet 直接 store；**这不排除数组实际别名、未扩 helper 或整条调用链的副作用**。c/d producer、payer、币种、实际 military paid amount 与 cadence 仍 unknown，R08 整卡与动态分子均不增加。

来源机器 `desktop-3fevhd2-1c74096080`；原观察 `2026-10-16T16:39:43.114580+00:00`，原提交 `d05b0c780b615faa714fdf0535403bb2e6941faf`；CK3 **1.20.0.4 / Steam25734779**；EXE SHA-256：

`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`

新源计费625B code、220B metadata、20 reads，全部逐读 ledger 已 durable 保存，raw 先于 decode 落盘；`.pdata` flags0 的普通 unchained body覆盖183条指令、34个内部跳转和3个 direct CALL。整合的实际机器/UTC、来源包与原始成员 SHA 见[便携记录](evidence/episode04-r08-copy-callee28d6170-12004/portable-source-a07.json)。这次整合没有读取 EXE、SDK、游戏或桌面，也不追认来源机器的运行资格到其他机器。

## 静态 caller 与实际场次的区别

[R0178 已入库来源](acceptance/2026-10-16-r0178-maintenance-writers/ARCHIVE-INDEX.json)保留完整695B `28A63E0`，其中 copy store是 secondary context+18→2C0、+20→2C8。原件里的 `28A6535 E8 36 FC 02 00` 真正指向新叶；callee CALL 属于**已持源代码指令**，没有新增 runtime CALL 观察。R0178 命中前面 copy store 不能证明之后的 CALL 已执行，更不能外推到 R186。

新包 retained caller 的 bin/ASM/source receipt/PE mapping 四成员与 d05 canonical ZIP 对应成员逐字节相同。原 `CALLER.actual.json` 的 `callee_not_yet_read=true` 是采集前 intake历史；它和随后完整新 SOURCE 一并保留，不覆盖旧事实。补正 `ROOT-DELIVERY.actual-a02.json` 修复旧 copyplan 漏掉的3个 portable-index依赖，旧 receipt与所有来源 bytes不变；本包将其18项final输入全部保全。

caller 的 RCX 是 `*(Character+1C0)+368` descriptor地址；RDX 指向 local QWORD，**该 QWORD 才保存 Character 指针**。把 RDX 本身命名为 Character 或 payer 会读错一层。

## 过滤条件与普通写入

descriptor首QWORD指向4B raw FullID occurrence数组，signed DWORD+0C是count；不会去重。元素经 registry5D1FC58/fallback5D1FC48，low24 index/capacity、16B row+8 pointer与完整DWORD+10 generation校验解析。fallback继续过原tag/ID门，lookup失败不能直接改为原生false。

先要求对象DWORD+14==5363686D（Schm tag）且DWORD+10!=-1。raw mode(+30)==1时，再把+34 ID经Title registry5D1DAF8/fallback5D1DAE0解析，比较对象DWORD+128与 Character DWORD+18 FullID。其他mode在28D6259/28D634E调用opaque `2A500F0(object)`，返回指针与 caller Character指针比较；该helper未展开，不能叫 payer resolver。

首个reject以前保留前缀，后项满足条件时在 `28D636A` 将raw DWORD复制到较前的保留位置。正常非负、不溢出、header不被外部改变的域内保持保留项相对顺序；循环会重读count，不能由此宣称并发安全或无限整数等价。

末尾 removed=wrap32(count-kept)，signed removed<=0 返回0；正数路径在28D63C1调用opaque `4226860(data+kept*4,data+count*4,R8=0)`，随后 **28D63C6 对当时 descriptor+0C 做 SUB removed**，并返回removed。第三参数在此路径按原算术确为0，但helper全部副作用未证，不擅自命名memmove；count store也不能改说无条件MOV kept。

本体直接非stack写是数组DWORD复制和descriptor count扣减。没有固定wallet store只是 own-body 结论：数组别名、opaque helper `2A500F0`/`4226860`、外部修改和传递调用仍未知。count<=0也先读descriptor首QWORD；返回0可表示空/非正count或没有移除，不表示费用0、没有业务对象或没有writer。

## Agent 与视频的复用边界

智能体可将本叶记录为已证关联ID清理，不把count/removed用于现金或军费数值决策。视频可说明“这条callee的本体是关联ID过滤，尚未给出c/d军费生产地址”；不能说整个刷新链不写钱包、已付金额、每日/月结，或将source CALL当现场调用镜头。

剩余链仍为 unknown producer → secondary context+28/+30 → 同一次settlement/application → 实际payer wallet。下一有用输入是由Root另行准入的新真实8B write post-PC/regs/thread/window，而非本包继续猜helper或授权推进。既有[local88来源](episode04-r08-local88-components-12004.md)、[contract贡献链](episode04-r08-contract-contributions-12004.md)和独立tier来源不因本叶增加业务资格。

## 无源机器盘符的离线校验

```text
python -B -O docs/ck3-native-ai/evidence/episode04-r08-copy-callee28d6170-12004/verify_r08_copy_callee.py
```

只需标准库与本目录便携JSON；原625B、全部指令/分支、durable ledger/metadata、原plans/check/render/reader、695B caller/原receipt/PE映射及补正历史均以exact压缩原件嵌入。源ZIP原件SHA：`0dbd5daea0423a357b26de116d831523c3241b1de0c41ff8bc01c099c34fa368`；625B SHA：`32cff14d40f5c72c6cf8ff036ce0aa6950d6741236e4ed46f08edb2bca802c1b`。默认不执行保存的采集脚本，不读历史C盘路径或联网。可加 `--extract-originals <不存在的新目录>` 原样提取所有记录。

校验层为frozen bytes/readledger/declared source edges；不重新反汇编，也不独立证明人工语义或实机行为。原作者3个故障拒收记录原样保留，整合只跑新增portable组合，不重跑旧矩阵；旧容量例外不续期。成片human approval和paid/cadence继续未完成。
