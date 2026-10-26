# 原生财政目标向量：actual 1.20.0.4 的19EA9A0

机器 `xenoamess-full-tower-eb9d2c1186`；共享静态取源时间 `2026-10-25T22:35:03.776658Z`。EXE绑定为1.20.0.4 / build25734779 / SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。安装见证02复用未变元数据与原哈希，不证明已加载进程，也不是本轮重新完整哈希。

本次完整取得 `[19EA9A0,19EAD85)` 的997字节，解出273条指令，末尾 `19EAD84 RET`，无未解码尾字节。它通过角色自身等级和已采用的all-raised维护费入口生成80字节输出，只写槽0、槽6。**输出保存位置、两个war_chest脚本getter、定义注册与刷新时机仍未闭合。**

## 来源与验证

原件 `D:/ck3-state/ck3-java-g2-native-static-resume61/batch03/capture01/window-046.raw` SHA `30141de6650748e4c99d3f0d9d465b6d7b1846c19f983647115222cac2fd03a2`。实际共享回执 `resume61/b64_execution/BATCH03-RESULT01.json` 为32698字节，SHA `460cb1a0294518eccb7c0ba5d22da7b93d51976f98d13e2c7c3b73dc8303acbb`，对应windows[46]。input CLOSED、三阶段outer/child退出0、Job0和前后来源检查MATCH只证明有限静态取源执行。

本体的cached pdata row84853 / unwind51BFCD4界定997字节。旧 .3 同长候选仅用于导航，当前调用、字段和算式均由实际 .4 字节确认，没有按减0x20授语义。

本岗 `AI-CHEST-BODY25.json` 保存273条完整指令与分析；`AI-CHEST-PLAN25.json` 绑定12份来源并生成[同源图](finance-native-budget-target-12004-2026-10-26-graph.md)。最终check/render均exit0，检查范围只为记录结构和来源字节。初稿把静态读源case误标observed，检查器拒绝；最终移除此case，保留3个真正pending问题，没有live observed信用。

## 实际输入、调用与输出

| 当前位置 | 字节可证事实 |
|---|---|
| 19EA9BE / 19EA9C1 | RCX保存为输出指针；Character来自输入RDX对象的qword+18 |
| 19EA9C8 | 调用已采用的own-tier28AC690，不是谱系最大等级 |
| 19EA9D0–19EA9DB | 取global5449BE0指向的int32表，以sign-extended tier索引；表项乘100000得到B |
| 19EA9EA | 已采用的2C152B0接同一Character及局部80字节输出 |
| 19EA9F3–19EAA02 | 调用者全部80字节输出清零 |
| 19EAA06 / 19EAAC0 | 两次读同一signed dword global5C687BC，各乘100000后参与定点乘法 |
| 19EAABD / 19EAB53 | 首写槽0和槽6（+30） |
| 19EAD63 / 19EAD84 | 返回原输出指针并RET |

本体没有tier索引范围检查，也没有当前表项值。own-tier的既有140字节来源和缓存边界见[等级专题](episode04-r08-classifier-tier-threshold-12004.md)，本轮复用。

2C152B0复用已有actual4现金binding与80字节ABI。b64找到其已保存完整828字节cache `shared-span-cache/new-02C152B0-02C155EC.bin`，SHA `3ea4f4f7df2dfd67f56ec3927988dd2c2c6f92cb186fb926d5c3c2f811caddcc`。这是旧cache复用，不是新增EXE读取；[all-raised费率与已付流水的界限](war-payment-maintenance-cache-source-12004.md)继续有效。

## 当前计算树

M为2C152B0的十槽局部输出，B为tier表项乘100000，N为global5C687BC乘100000。`mulq`、`divseq`只缩写当前内联指令序列：

```text
out[0..9] = 0
base0 = mulq(M[0], N)
base6 = mulq(M[6], N)
out[0] = base0
out[6] = base6
if M[6] <= 0:
    out[0] = signed_max(B, base0)
else:
    R = divseq(M[0], M[6])
    out[0] = signed_max(base0, mulq(R, B))
    out[6] = signed_max(base6, mulq(100000 - R, B))
return out
```

其余八槽保持零。正槽6分支的除数是M[6]，没有改成M[0]+M[6]；R也没有夹在0到100000。不能为符合“比例分配”的直觉改写。

`mulq`含小范围直接乘法和较大数拆分；`divseq`含直接有符号除法、分母量级分支及拆分。简写不保证对全部int64输入等同无限精度计算后一次截断，也不是新生产数值合同。本体直接写入仅输出和栈，不是钱包writer；未全面展开的callee副作用不能据此概括为全链无副作用。

installed `common/defines/ai/00_ai.txt:163–189` 声明MIN_WAR_CHEST等级表、MONTHS_OF_MAINTENANCE_IN_WAR_CHEST=18、PERCENTAGE_INTO_WAR_CHEST=0.6，文件SHA `3af5d4100789bad56570e05c5852f35783605813957de7a5129d23142a116120`。但本包未取得当前注册到5449BE0/5C687BC的边，也未读回global值。旧 .3 地址、文本和计算形状不能替代注册证明。

## 已有初始化caller与缺口

已保存 `current-context-update-body01.json` 为12781字节，SHA `5a9a9187bde9e3924c67bbe8739b59b44957d3fe667c282d19aada1558f43bd6`，raw自19E7CF3起1024字节。真实指令包含：

- `19E7D1E → 19EAD90`：RCX为原context，EDX=0；R8来自Character+1B0对象的+100，缺对象为0。
- `19E7D9D → 19EAD90`：RCX仍为原context，EDX=3；R8为通过Land tag/full-ID守卫的首个owned Land+318，失败为0。

entry检查context+2D，已初始化时跳19E7E71；body末尾置该byte为1。entry/body为chained片段，首个19字节pdata不是完整函数；19E7E78起switch表不作指令分析。

19EAD90有cached精确边界 `[19EAD90,19EAE7F)`、239字节、row84854/UW512DE20。本体尚未取得，故图中19EAD90→19EA9A0仍为虚线；不能声明已经调用、写入某strategy字段或具有已知刷新周期。下一请求仅查这239字节，不做全image xref/literal扫描。

## 自动游玩消费边界

[HoF资金链](finance-hof-gold-source-chain-12004-2026-10-26.md)及[Finance16消费者](finance-war-chest-authored-consumers-12004-2026-10-26.md)使用war_chest_gold和maximum。Finance16还证明冒险者雇佣分别比较warChest与gold。这些脚本不建立本体输出到getter的关系。

本包没有当前钱包、付款、退款、借款到账、雇佣或到场结果，没有termination报价、预算修改或首场新门槛。NET军费计一次、all-raised替换当前率一次、未知资金不预支、UNKNOWN不重放继续适用。新增游戏日0，不增加M0–M7实机验收。

本岗D小源上限2MiB、Z独立docs上限128KiB；本篇与图在额度内，复核时间2026-10-26T08:00:00Z，不自动续期。大原件保留共享引用。
