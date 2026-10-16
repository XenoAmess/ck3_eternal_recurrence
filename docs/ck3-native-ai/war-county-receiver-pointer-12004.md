# County 参数到 relation receiver：1.20.0.4 原生来源

来源机器 desktop-3fevhd2-1c74096080；精确 EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，Steam25734779。
本次只读唯一函数 `[24D4ED0,24D4F90)`192B：49指令、12个唯一内部跳转；
224B元数据、21次读取。未调用游戏/SDK，未读取2C09620或任何外部callee。

已闭131B wrapper2C09DF0在2C09E53以原County参数为RCX调用24D4ED0，
实际RAX随后成为2C09620的RCX；原actor经RDX转发，R8D为0。这个实际receiver
不能仅由地图上的“敌县”、holder或occupier标签替代。

24D4ED0先检查County+3E0的CoDa magic及`*(County+20)+85C`的Prov magic。
任一失败直接返回Character fallback全局5C67570的内容，不是bool false。
通过后唯一外部CALL24D4EFD→24D4D20仍以County为RCX；若返回对象+1C为Char
且完整ID+18不为-1，就直接返回该指针。这个callee尚未展开，不能给其返回值
擅自命名holder/controller。

该Char检查失败时，函数使用County+18完整ID解析Land registry5D1DAF8，
失败选Land fallback5D1DAE0；然后取解析或fallback Land对象+128的完整ID，
解析Character registry5C67568。只有对象+18与完整ID相等才返回该实例，
其他失败均返回Character fallback5C67570。低24位只用于索引；完整代际仍参与比较。
此体不直接读取County+848，未证明Land+128的正式holder语义，也不保证fallback
内容属于该County或具有有效当前角色身份。

因此可供智能体复用的是**带分支和fallback边界的Character形状/registry指针来源链**，
不能把County+18当现有county_title_id，不能把helper receiver当已知县主、占领者、
敌人或本人。当前最终condition false没有暴露本次具体分支/receiver，不能反推它。
下一唯一具名来源候选为24D4D20；必须另获有界授权，本次没有跟读。

原件在[小归档](acceptance/2026-10-16-county-receiver24d4ed0/county-receiver-source.zip)，
[成员索引](acceptance/2026-10-16-county-receiver24d4ed0/ARCHIVE-INDEX.json)记录每项精确bytes/SHA。
归档含完整bin/asm/49条指令表/12分支合同/原始逐次读取账本、plan check、来源绑定，
以及已持wrapper的131B原始字节和原合同。历史C盘路径只作来源元数据，普通clone
的重放不会打开这些历史位置。

仅用标准库即可验证ZIP CRC、全部成员SHA、raw与49条连续指令的逐字节对应、12个
相对跳转目标、唯一opaque CALL与wrapper实际CALL，复查预算和先保存的逐次read原字节：

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-county-receiver24d4ed0/verify_source_archive.py --archive docs/ck3-native-ai/acceptance/2026-10-16-county-receiver24d4ed0/county-receiver-source.zip --index docs/ck3-native-ai/acceptance/2026-10-16-county-receiver24d4ed0/ARCHIVE-INDEX.json
```

需要查看某一原件时可用标准`zipfile`读取上述索引中的成员；如需解压，使用新的外置
目录，不覆盖旧attempt。这个重放只验证已保存来源，不声称重新采集、运行原生函数、
实机R04正例或relation业务语义已闭合。
