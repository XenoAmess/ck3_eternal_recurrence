# R08：同一调度体先结算，后调用费率／角色上下文 getter（1.20.0.4）

本次只复核已入库原始字节。来源机器 desktop-3fevhd2-1c74096080，CK3 1.20.0.4 / Steam25734779 / EXE SHA256 98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。没有新 EXE、SDK、游戏、GUI、debugger、native 构建或付款样本。原 R0174 字节与其历史 qualifier 保持原样；不是 R212 运行资格。

## 可证伪的静态结论

已保存的父函数 28F7840..28F7C9E 共1118B、250条指令。在**本函数自身正常控制流**内，所有可达正常返回路径都经过恰好一次 28F7934 CALL28A6D10；在这条 CALL 之前没有其他 CALL。context为空的分支也跳到28F7931，随后执行该结算调用，不能把这个空分支误读成“跳过结算”。

| 精确位置 | 已保存字节／关系 | 可使用的含义 |
|---|---|---|
| 28F7850 | 48 8B EA，RBP=入口RDX | 保存原入口的Character参数；类型合同见原parent anchor |
| 28F7931 | 48 8B CD，RCX=RBP | 传给settlement的是上述同一参数 |
| 28F7934 | E8 D7 F3 FA FF，CALL28A6D10 | 本函数自身正常路径恰好一次的结算调用 |
| 28F7AD5 | E8 A6 82 FC FF，CALL28BFD80 | 位于前述结算之后；仓库ExpenseContextCharacter/TopLiege采用同址绑定 |
| 28F7C30 | E8 2B C3 31 00，CALL2C13F60 | 当前维护费率getter位于之后，且不存在回到更早settlement的本函数控制流路径 |

结论因此限定为：**后面这两次 getter 的本次返回值，不能沿此函数的前向数据流直接生产同次更早结算已经消费的四项输入。** 给已观测NET再减一份此时的current-maintenance向量，也没有被这条来源证明为“扣除实际军费”的合法计算。

这不是“所有 getter 都没有副作用”或“费率永不影响付款”的证明。其他callees的传递副作用、异常、重入、并发写入和前一次调用对下一次输入的影响没有建模。CALL节点按正常返回处理；“恰好一次”只计本函数自身的该callsite，不计callee递归产生的其他invocation。

## 对 payer 和 cadence 的直接影响

入口传递的Character是源调用参数关系，**不是已经独立核验的实际付款账户**。28BFD80在仓库两个actual4工厂中被采用为ExpenseContextCharacter/TopLiege同址入口；本次没有重新证明其native body全部语义。它在这里的调用既然发生在早期settlement之后，就不能凭这个后段参数名把早期钱包记录的payer替换成top liege。payer仍按实际callback的Character/wrapper/own-account/session关系判定。

所有前置分支都汇合到结算，因而这段自身代码没有日/月条件分支可跳过该callsite；**它何时被外层调度调用仍未知**。不能把“每个正常parent invocation一次”改说成“每日一次”或“每月一次”，也不能把一次跨Apr1的同值copy当作月结付款。

下一次已有四槽DR观察若得到+28/+30实际post-PC，先按真实写地址/寄存器解码；如果落在本函数前半部，还必须解释为何与已保存直接写入/控制流关系不一致（版本、错误边界、指针alias或并发），不能自动命名军事producer。若只得到+2C0/+2C8同值copy或零命中，不增加paid/payer/cadence信用。本研究不扩大观察器、不开采样，也不授R212外部DR。

## 原件和可复用检查

[小来源包](evidence/episode04-r08-parent-order-12004/PARENT-ORDER-SOURCE.actual.json)包含原1118B hex、六个历史片段的SHA/源JSON指针、完整250条有字节边界的指令表及来源SOURCE-SPANS整文件pin；不复制EXE或大包。来源原件是[原SOURCE-SPANS](acceptance/2026-10-16-r0174-maintenance-source/SOURCE-SPANS.actual.json)，入口类型沿用[已保存anchor合同](acceptance/2026-10-16-r0174-maintenance-source/PARENT-HOOK-SOURCE-ANCHOR.contract-a01.json)。

```text
python -B -O docs/ck3-native-ai/evidence/episode04-r08-parent-order-12004/verify_parent_order.py --counterexample
```

默认只用标准库：校验版本／片段／整体原字节，依据固定指令边界从原始相对跳转编码构图，逐正常返回检查结算次数与getter先后。它信任保留的指令边界，不声称是独立全x86解码器。已安装Capstone时可加 --independent-decode 重新对照全部边界；作者实际执行了这个额外步骤。synthetic反例把一个前置Jcc改为绕过结算的边，检查器得到正常路径次数集合[0,1]并拒绝“恰好一次”命题；没有执行这些合成机器码。

## 45秒／一个自然日的机会判定

现持有的290DC00任务分发、290FD20索引闭包和28F7840并未闭合外层calendar调度。现有current-cash/payment接口提供已发生record、日期、sequence与窗口身份，没有已证的next-settlement日期或可用于预先Arm的结算phase。45秒observer覆盖一个确实推进的自然日，仍不能保证这个Character在该日被送入上述结算路径。

即使settlement执行，已保存574B源的N/T/wrapper guard也可能不产生钱包记录。空journal不能判“没有settlement”。只有事后保留的同session、同账户、完整known-source钱包子记录，才能说明本次确有该wallet应用机会；kind2 caller28A6D7C与负支已知caller必须按原production consumer分别验，不因callback存在就命名军费。

观察建议因此只是一项可证伪的限定实验：Root独立grant后保存完整入场cash/四raw与journal fence，在实际ready之后推进唯一原生一天，保留终点原件和完整DR清理；有合格c/d PC则推进唯一source定位，无合格trap则保留“该有限、非全覆盖窗口没有保留对应trap”。若同窗口还保留known NET回调，可以补记“确有NET应用机会，但未取得c/d来源”，仍不能证明payer/cadence为假或费用为零。历史Apr1或一次相同raw没有资格成为必中的未来日期。

本结论没有新增主动调度器、date getter或native flag。R212 actual到站后的Root许可、当前自然日循环小原件与现存窗口资格另行绑定；不自动attach，不借普通4GiB/录像时长准入授DR。


[结果](evidence/episode04-r08-parent-order-12004/FACTS.actual.json)和[视频口径](evidence/episode04-r08-parent-order-12004/VIDEO-CLAIMS.actual.json)分列来源结论和业务未知。原件没有变成付款正例；paid金额、军事分类、实际payer和calendar cadence均保持unknown，不增加研究/业务/动态/ABC分子。
