# CK3 1.20.0.4 补员 wrapper slot8 的真实拷贝路径

精确读取 `476A560` 的8字节得到 `f07a974201000000`，按已验 PE preferred base `140000000` 得到唯一代码目标 `2977AF0`。它的完整131B、34条指令已闭合，完成带 owner+desired 的固定对象拷贝，没有写 military+4A9，也没有闭合提交后的执行时机。

机器 `desktop-3fevhd2-1c74096080`；时间、完整字节、分支和读取账本来源见[来源合同](evidence/military-refill-wrapper-slot8-copy-12004.json)。精确EXE SHA为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。新增 data8B/meta168B/code131B，共17次读取；slot与唯一unchained函数均先保全原始字节和 fsync 账本，再解释或解码。没有扫描其他slot、重哈希整EXE或跟读callee。

`476A560 = 476A520 + 8×8`，实际caller的RCX首qword为476A520，因而这是该wrapper的slot8，而非凭地址猜出的任意factory。实际函数在2977B05以ECX=0x30调用未读取的4223B94，将返回对象的最终首descriptor设为476A520、对象+18的内嵌descriptor设为476A4F0。它逐字段复制来源wrapper的+8/+C/+10/+14/+20/+24/+28，并通过输入RDX指向的holder返回对象。

来源owner完整ID在wrapper+24、desired字节在+28，分别复制到新对象同偏移；相对内嵌descriptor为+C/+10。+20的常量1也被复制，但该dword是否refcount没有在本轮源证，不能因先前字段名称推断其业务角色。对象拷贝路径已证，C++业务类名、分配函数内部及命令执行槽仍未命名。

| 已闭边 | 结论 |
| --- | --- |
| 原版控件→1303D40→12FF8D0 | 接收者+218选来源Character；读其+1C0 military→4A9，得到desired=(旧字节==0) |
| slot8→2977AF0 | 保持完整ownerID与desired的对象拷贝；本体没有flag写 |
| 后续37F06D0 | 已证实际call与载荷，不知道同步执行还是排队 |

取得只读getter接收者的第一缺口也已精确收窄。held `3E4C090` 在调用final之前，从argblock+B0索引数组中选取由+BC计数指定的最后一个signed32索引，再取运行期variables[index]：16B一项，+0是pointer、+8是type，要求type635。R0180目标chain0/flag0/finalkind3，最终3E4C202传给1303D40的RCX才是该实际pointer。callback+F0在此前被包装为GuiContext，不能当MilitaryView，也不能直接读取[F0+218]。

最小生产接线应复用existing Military tree/query：先在固定source/profile、ownerthread/modal/worldrevision保护下取得稳定type635接收者，再读receiver+218，校验Character完整代际，复用现有Character+1C0/+4A9严格读口；DTO需保留owner、fallback/availability、raw字节和enabled。其第一个未闭解析函数是实际3AC3B55直接调用的 **3AC3EF0(context, variablesbuffer)**，本包没有读取；3E4BC50的参数准备也未读。先闭固定resolver，不能新增任意指针查询或通过执行OnClick冒充只读getter。

正常切换应沿已证原版外层控件dispatch，保持原生world/modal/ownerthread保护、固定表达式descriptor和once票据，随后独立读取同来源owner的4A9。实际flag执行器应从已证476A4F0的来源ABI/注册确定；没有槽位角色证据时不能猜一个Execute slot。这里没有点击、状态转移、actualADD或完整R06资格。
