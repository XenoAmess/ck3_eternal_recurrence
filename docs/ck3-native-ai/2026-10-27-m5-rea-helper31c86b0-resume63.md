# M5：31C86B0 写穿 F10 的有限证明

machine_id: xenoamess-full-tower-eb9d2c1186。采样：2026-10-26 23:54 UTC；独审/落文：2026-10-27。前向补充 [351B注册与96B请求名](2026-10-27-m5-rea-f10-registration-and-literal-resume63.md)，旧原件不改。

已证 helper 显式写穿入口 R8。接回调用者，正常路径写 registration owner+F10 的QWORD及 owner+F18 的BYTE1；owner=getter返回对象、返回指针的请求项身份、运行DB与战争合法性仍 UNKNOWN。

## 本体机制

- 31C86D7 `498bf8`：RDI=entryR8；RSI保存entryR9，R14保存entryRCX。
- 31C86DD 调 A149D0，返回保存RBX。描述符QWORD+0送RDX、DWORD+8送R8D，31C86FB调opaque3F7E220；此前RCX未显式恢复，不猜完整formal或径称hash函数。
- EDX=上次返回低32位，RCX=RBX；31C8705调opaqueD2BEC0，返回p=RAX。
- 31C870A `488907`：QWORD[RDI]=p；31C870D `c6470801`：BYTE[RDI+8]=1。
- 随后才比较DWORD[p+38]与4744624F；31C8718唯一JE至31C8870。相等直接epilogue；不等走局部描述符构造和8个opaque调用，再到同一RET31C888C。

两次store在分支前，所有正常RET必经，前提为前置调用返回且Win64非易失寄存器约定成立。没有p前置null检查：可先写null/byte1，再在[p+38]异常。byte1不证明初始化成功。相等路径RAX=p；不等路径RAX为末次883A40返回值，无bool规范。长路径没有其他显式[RDI]写，但opaque/alias/并发/异常影响未闭合。

helper实际使用A149D0返回值作为D2BEC0的receiver，闭合lookup receiver来源；registration owner是否也等于该对象仍缺证明。entryRCX是另一局部描述符。D2BEC0可能返回请求项、fallback或其他值；原请求名与原版none默认声明不追认为运行F10/key+9F28值。

## 范围与原件

case根 `R=D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m5-helper31c86b0-01`。PE前后SHA256均为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。fresh RF row170184=`[31C86B0,31C888D,510E44C]`，12B@file98880864；本体477B@file52198064。显式新增489B；完整hash/loader IO另计。未follow或执行native/游戏。

raw477 SHA256 `74b152cbf671ecfae21e547871a337c4b9d9506d83bf807cb0a1bb3b13710e39`。102条逐VA/size/bytes与Capstone/Rizin一致；独算11CALL+1JE+4RIP。手建3块3边：入口→871E、入口→8870、871E→8870；唯一RET888C，无外非call边。计数/正常CFG不替代callee与异常闭合；自动字符串/signature/日志注释不作语义证据。

R下以下文件均SHA256：

| 文件 | B / SHA |
| --- | --- |
| `CROSSCHECK01.json` | 5011 / `e1c2928ab68dab9dfb769c3cd3895a564b3be1a7d01965734dea438eb95f6eb0` |
| `CASE-RECEIPT01.json` | 7407 / `b0399d16e2444421633f36bccee7c988a4565fc33730d80f130f82fe7c79209d` |
| `INDEPENDENT-REA63-REVIEW01.json` | 5005 / `f59b19b0b668270ebfd092ba8982573a3662d9543dda086f99921381fd91c297` |
| `CASE-CLOSED01.json` | 2100 / `aab4095a8bcef14da3d6ba7b9d7953ddda1cf3aa1d4468a118f534409baf97a3` |

REA63于00:00:56.154Z仅held/RAM独核，0新PE/provider。flat96128B→gzip11565B、bundle96404B→gzip11748B，只落gzip；原/压完整SHA、gunzip往返、单record deep值与stdout UTF8 hash均在receipt/cross保全，无未压/temp副本。

新300+60卡T0=23:53:41.350326Z、close窗至23:59:41.350326Z；实际先解码→单minclose，再REA→最终minclose，23:54:59.353Z按窗关闭、0owned/4PID缺席，全部退出0。Rizin峰592207872B<1GiB，Capstone24813568B<256MiB，未触帽/service.close无错。outer Job0/joint peak未测。首次binder字段校验失败与一次实际采样事实见EXEC/receipt。原close的PAYLOAD_UNASSESSED不改，后继review不复活旧卡。

Java仍只消费现有来源/帧绑定的native network分量及actual ratio；[C2/child106边界](2026-10-27-m5-rea-callee24c3be0-resume63.md)不抬权。条件性的raw累加过滤不变成召集veto、有效到场或胜率。无源码/Maven/测试/DTO/bridge变更，automatic_declaration仍false；M5真实候选、唯一提交与独立后态仍需实机验收。
