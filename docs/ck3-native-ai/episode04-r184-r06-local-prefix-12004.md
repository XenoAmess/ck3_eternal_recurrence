# R184 R06：先保全稳定 local entry，再决定 receiver 后续

机器 `desktop-3fevhd2-1c74096080`，离线分析于2026-10-16T12:48:04Z。基线为`163530f1bbcabe5a97854625b3fab7568006ee65`；精确a27/native与本场PID/generation/episode/date见[小证据](evidence/r184-r06-local-prefix-12004.json)。本文是闭场后整合候选，没有修改冻结仓库、连接SDK、操作桌面、构建或新增游戏查询。

R184已打开军务，547控件完整树的根可见；普通补员外层index220可见，帝国分支index238隐藏。两者都在pass1/read51/depth8终止。`definition_present=null`和`raw_definition_entry_count=null`支持本次a27诊断修复已经在实际查询中工作；不能再把问题归因于窗口没打开。真实receiver、toggle、ADD仍未成立。

## 最小下一改动

**在同一固定补员表达式里增加独立双读的`local_definition_entry_only`来源叶**，只读取callback所属context的本地definition及匹配type635 entry，发布其mode/flag、direct presence、provider vtable/slot2 RVA；不先扩大8层父链上限。现有candidate的父链失败不应永久遮住下一条已经可读取的具体provider源码边。

这不是把失败capture的partial直接放进`entries`：旧`receiver_entry_candidates_12004`仍按原合同返回unavailable、index/key null、entries空、selected=false。新叶有单独source/scope、status、stable_double_read及独立完整identity；只有本地prefix两次原始读完全一致、原frame/source/owner守卫都通过才发布。无匹配项也要显式区分完整本地查找无匹配与读取失败。数据只含模块RVA/现有标量，不泄漏context/entry/direct/provider地址。

施工可复用现有`once`的前半段：抽出callback声明/index/type635、本地definition/count与first-match entry读取，保存完整private identity；旧父链计算继续使用它。若旧计算在depth8等后续阶段失败，保存原failure诊断，再做一次**只到local entry的复核**。两次prefix相同才构造新叶；复核失败只令新叶unavailable，不能改写原失败原因。两次读取、父链和所有新叶共享原4096读/64KiB/20ms计数与每tree4capture限额；不能为它另加一套宽松预算。

新增consumer字段必须明确`scope=local_definition_entry_only`、`current_variable_table_observed=false`、`native_receiver_selected=false`。本地ancestor_depth固定0，不增加原8层或entry数量上限。需要改动的实现点仅为现有reader/result结构、serializer、严格Python合同及聚焦fixture；无需新MCP工具、新动作或原生表达式执行器。

## 来源为什么支持此边，而不支持直接调用getter

- 已持完整`3AC38C0`在`3AC3AD0..3AC3B34`，先按callback block+98/+A4声明key查本地definition+90/+9C、stride50、key+48，并调用匹配entry的`3AC1C00`。随后才在`3AC3B55`进入父链`3AC3EF0`。这使本地entry成为可独立完整观察的前缀，而非必须等整条父链结束的未知布局。
- 已持`3AC1C00`中mode0和mode1分别在`3AC1D9A`、`3AC1D85`将entry+0写到variable并返回AL1；mode2及更大非负mode沿entry+38的实际provider vtable+10分派。发布这个slot2 RVA能提供唯一下一源码入口；不能在它出现以前猜callee或执行provider。
- `3AC3EF0`在local flag非零时不将receiver放入pending；parent flag非零且resolver AL1才移除pending。故local direct/provider记录不总等于最终变量值，不能以“local有pointer”授予native selected。
- `3E4C090`还先调用尚未在本包闭合的`3E4BC50`，再从临时variables取最后receiver index、type/pointer，最终call到1303D40。直接调用3AC38C0会走临时分配、provider与最终业务call；它不是只读getter。直接调用3AC3EF0需要调用期间才存在的variables表，也不能用callback+F0替代MilitaryView。

取得新本地叶后的唯一分支：若有合法provider slot2，按其实际RVA做一次独立有限`.pdata`/完整body源计划，闭合它的参数与写入行为，再决定纯getter接线；若本地叶为direct，也仅提供候选owner供独立身份验证，不跳过pending父链和变量表证明。若没有合法provider且父链仍必需，下一步才另立**显式新profile**研究有界更深遍历；原8层profile不能静默换成16/32。当前树没有各层trace，read51不能反解实际链长度，也没有依据选一个能保证到达的更大数字。

## 必需的新反例与验收边界

新fixture应证明：local entry稳定而第8层父链耗尽时，新local叶可用且旧candidate仍unavailable；只在第二次local prefix改变mode/flag/provider/slot2时拒绝新叶；local所需字段未读全不得借首pass partial发布；first-match后不可读尾项仍不读取；额外复核耗尽原总预算时不授新叶。原有8层、source/frame、unavailable与no-selected测试仍保持。

R184小证据精确绑定原响应、a27构建回执中的DLL/injector/host SHA以及runtime identity，并标明`local_entry_observed=false`：**本场尚未取得这里提议的本地prefix叶**。它只是最小可施工下一口，不能写成本次receiver、补员开关或实际ADD通过。
