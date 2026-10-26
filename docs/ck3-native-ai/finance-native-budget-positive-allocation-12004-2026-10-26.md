# 正金额通知的原生分配算法：1.20.0.4

`machine_id: xenoamess-full-tower-eb9d2c1186`；最新共享取源时间2026-10-26T00:06:56.748306Z。静态身份为1.20.0.4/build25734779/SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。没有Game、native invocation、构建、生产修改或资金到账信用。

`19EAE80..19EB3AB` 的五份原件完整覆盖1323字节、361条指令、40个局部跳转，均落在实际指令边界，唯一RET为19EB3AA。最初42字节只是entry fragment；181+11、1079+10都按真实控制流取得，没有从pdata邻接推断整函数或UW CHAIN。闭合范围是直接函数体，不是全部callee或脚本getter。

## 原件和复核

共享原件根为 `D:/ck3-state/ck3-java-g2-native-static-resume61/<batch>/capture01/`：

| batch / 原件 | 字节 | SHA-256 |
|---|---:|---|
| batch05/window-004.raw | 42 | cfd22e19679329da9b10490ffb0efe217da4da9a9aa2720144c444cfc19b311d |
| batch06/window-023.raw | 181 | af25663b838c10931656c3dd4d5a08ffda4ae2a568531ff3c012d11e0e94b91a |
| batch07/window-006.raw | 1079 | 0ef1501d3e1713bdff4332ac9a8451c5b21635519119a4d9201202b647d2c0b9 |
| batch07/window-007.raw | 10 | 2da3bb1202c4f7df99fd1783dbc3e3053614a7216764208426e6ac96ee0d480c |
| batch06/window-024.raw | 11 | 3fb34a98f7ff08a2a4b7d0d18e20f456f9e60cca8019c08029566cdcf4ed54bd |

只在内存拼接校验，SHA `8a527dd4961ed9ddc4ecad7c0581d5542511b1faf0e06c3856f89f36e68e706e`，没有写替代raw。三个capture回执的三phase退出0、Job0、来源MATCH和input CLOSED均是取源结果，不是业务完成。

本岗 `AI-CHEST-POSITIVE-ALLOCATION30.json` 保存全指令、40条边、RIP地址及阶段分析。`AI-CHEST-PLAN30.json` 绑定14份来源，实际最终check/render均exit0，见[同源图](finance-native-budget-positive-allocation-12004-2026-10-26-graph.md)。plan工具只检查结构和文件字节；另以capstone核对局部指令边界，均非语义或运行验收。3个业务case仍pending。

## 实际字段和分配顺序

C为输入context，A为signed R8。S0是entry读取的[C+20]；quota、target使用后续重读S1、S2，不增加指针一致性或原子性假定。

| raw mode | P：四个qword槽 | D：四个辅助qword槽 | quota signed32 | target signed64 |
|---|---|---|---|---|
| 0 | S0+160 | S0+180 | S1+230 | S2+1E0 |
| 3 | S0+1A0 | S0+1C0 | S1+234 | S2+210 |

P、D只是tracker字段，不能命名为四个独立钱包或完整每笔分配回执。正常0/3路径不消费传入R9；gateway的literal第四参数4选择该分派路径，不据此命名引擎enum。

1. S0为空或A<0直接epilogue，无callee、无tracker写。A=0不被该entry guard拒绝。
2. 先补P0至quota×100000。整个A适配缺口时，P0加A，D0=A、D1..3=0，直接返回；否则先填缺口、写D0并减少剩额。P0已达quota时不做此阶段D0写。
3. P1低于target时，取signed min(target缺口，当前内联定点乘法“剩额×global5C687C0”)，补P1、写D1并减少剩额；没有额外非负或百分比夹值。
4. own-tier28AC690索引global5449C20指向的int32表，将P3先补到该floor×100000。余款耗尽或剩额<=0即可返回。
5. 正剩额按global5449C60指向的四个qword权重分别做同一内联定点乘法，加到P0..3。各项使用同一个阶段输入剩额；这些加权新增值没有同步逐项加到D0..3。
6. global5449CA0指向四个signed32 cap。cap<=-1禁用限制；超cap×100000时夹P，并从对应D扣超额。暂存O每次被**覆盖**为本次超额，不是全部超额之和。
7. 四乘积之和T不等于阶段输入剩额时，O再加“剩额−T”。最后P3、D3均加O，再沿实际寄存器恢复路径RET。

不能把O的覆盖改成累加，不能强制四权重之和为1，也不能声称最终P3必在硬cap以内。D不镜像全部加权新增值，不能用D总和充当钱包delta。这里记录真实字节算法，不以假想输入宣布游戏bug或改policy。

定点乘法含大小数分支及截断路径，signed64加减保留机器语义；摘要不等于无限精度算式后一次取整。当前global数值和注册名称未取证，不将5C687C0直接称为运行中的0.6，也不授各表定义名。

## 调用方与消费边界

[初始化保存链](finance-native-budget-storage-12004-2026-10-26.md)在已有余额上重建tracker，application17另有credit通知入边。[Loan21 gateway](loan-native-target-gateway-and-event-lookup-12004-20261026.md)的literal4分支在基础writer调用后尾跳本函数；[基础ADD顺序](loan-native-account-add-order-12004-20261026.md)有其独立actual source。Refund的310DB20入边由该owner审阅，不回授本包退款资格。

正常0/3只调用own-tier；unsupported mode另调用3F7AA40并使用literal全局fallback，未展开其callee业务。正常分支没有钱包writer，但它**修改tracker**，不能作为新readonly getter调用，也不证明此前writer或整个金融事件已经完成。

war_chest_gold、war_chest_gold_maximum的当前注册/getter、定义名、缓存和日历更新仍unknown。共享索引未持相应named getter map，未为此扫描EXE。没有新ABI、预算、construction放行、借款退款credit或首场前置。新增游戏日0。

Z图先在D量测8650字节；连同本篇按含atomic/close的峰值核对，仍在本岗128KiB内；D小源低于2MiB。复核2026-10-26T08:00:00Z，不自动续期。
