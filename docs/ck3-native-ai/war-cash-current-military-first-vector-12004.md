# CK3 1.20.0.4：当前维护费 getter 的首个向量来源28C43A0

现有 actual4 current-maintenance getter `2C13F60` 的 public null-third-argument 路径，在 `2C141D7` 调用 `28C43A0(Character, local80B output)`，再把返回的十qword向量加到最终输出。本轮完整读到这一唯一callee `28C43A0..28C4532`，402B/95条指令、220Bmetadata/20reads。它没有直接把向量写入 settlement 的 `context+28/+30`；其末尾仍有未展开的 `24E1E80`。这不是军事已付金额闭合，`maintenance_attribution=unclosed`。

精确游戏1.20.0.4 / Steam25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。机器desktop-3fevhd2-1c74096080。本轮只离线读取具名唯一函数，复用已qualified frozen image及PE mapping，没有whole EXE hash、其他callee读取、SDK、注入、游戏/桌面或native EXE执行。计划、实际时间、精确字节及失败attempt见[原件索引](acceptance/2026-10-16-current-military-vector28c43a0/ARCHIVE-INDEX.json)与[source合同](acceptance/2026-10-16-current-military-vector28c43a0/SOURCE-CONTRACT.actual.json)。

## 完整source的直接关系

1. entry RCX保存为Character；entry RDX保存为out。函数先清零out80B。
2. 28C43CB读取 `*(Character+1C0)`。非空时把其`+278`作为ID数组描述对象；为空则使用源中具名static fallback descriptor。描述对象的首指针与signed32 count(+0C)决定4B ID序列。
3. 第一registry解析完整ID，复核对象+10中的ID；不成立时用该registry的fallback对象。只在其dword+18==0时继续。
4. 取第一对象+178处的ID，经另一registry解析并复核+10，失败使用第二fallback对象。对象类别名称未从本轮source取得，不把两个registry命名为Army、MAA、mercenary等。
5. 28C4490..28C44F9把第二对象`+130,+138,...,+178`的十个qword分别加到out的十个qword，按原始64位ADD保留低64位；本轮没有源内饱和或费用分类声明。
6. 所有迭代结束后，`28C451A CALL24E1E80(out,originalCharacter,0)`，其side effect尚未展开。之后返回原out指针。

因此，“第一向量”在此仍包含一次未知尾部处理，不能把已看到的循环sum当成整个返回向量已经完全闭合。source只支持它是既有当前维护费query中的一个向量来源，不能自动称它为实际钱包扣款或某一原始settlement term。

## 与 R08 raw terms 的边界

此处的`+278`属于 `*(Character+1C0)`。正NET路径里 `*(Character+1B0)+278` 的wallet funding tracker是另一条对象来源，不能因offset相同把二者合并。out里的+28/+30是本函数独立80B输出缓冲区地址，也不是secondary context的两个signed64 term。

本函数没有直接读取或写入 `secondary context+28/+30`。这只限制本体的明确字段边，未知尾callee及调用者/别的写者仍需单独来源，不能据此宣称引擎没有任何关联。另一向量 `2C142B0` 属独立并行scope，本轮没有读取或替它作结论。

[R0178的两个真实copy store](war-payment-r0178-writer-source-12004.md)只闭合`+18→2C0`、`+20→2C8`。[NET分配函数](war-payment-net-settlement-allocation-12004.md)只闭合负NET如何按raw c/d形成标量。本轮没有把query rate向量、这两个copy或某个数值相等升级为已付军事分量。

下一唯一具名source候选是实际directcall的 `24E1E80`，输入(out80B,Character,0)。只有Root另授.pdata≤512B/read≤48/fullbody≤8192B范围才继续，本轮未读。即使该向量最终有类别，仍需explicit writer/caller来源把它接到本次经济settlement和实际payer wallet，才可能关闭军事applied component。

## 普通clone读取

[小archive](acceptance/2026-10-16-current-military-vector28c43a0/originals.zip)保存402B、完整asm、plan/check/read/执行回执、已有846B caller及身份/layout元数据；不含游戏EXE/DLL、媒体或新的live观测。a01曾因准备脚本传输中的非ASCII箭头而SyntaxError，Python未执行、EXE读取0B；该失败记录保留，a02是独立有效attempt。

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-current-military-vector28c43a0/verify_repository.py
```

该stdlib verifier只核对文件/archive原字节、caller的relative CALL、唯一402B范围和已声明source edge，不执行游戏/历史executor，也不重新授予其他机器当前观察资格。Agent可以复用source关系和unknown边界，不能把query rate当作已支付军费，不能把缺失的c/d业务语义补零。

## 2026-10-16追加：来源库存现状

本页“尾callee未展开”与“下一唯一source候选”保留本次402B封包时点。后来已封的[24E1E80完整尾处理](war-cash-current-military-vector-tail-12004.md)与[第二向量2C142B0](episode04-maintenance-callee-2c142b0-12004.md)现可直接复用，不重复读取同一body。尾处理只修改独立out槽0/6/7；第二向量的局部累加器也不是settlement context+28/+30。其与军事已付分量、payer及周期的缺口见[当前归因路线](episode04-r08-next-maintenance-attribution-12004.md)，不由来源库存更新抵扣。
