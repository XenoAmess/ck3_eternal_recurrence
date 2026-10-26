# resume63：M1成员写入与可选检查

`machine_id: xenoamess-full-tower-eb9d2c1186`，2026-10-26 UTC。结论限定于当前PE的一个RF：**两次可见 `2C7DED0` 调用不是成员ID写入的必经前置**。它们属于persistent validity、join或其他检查仍未证明；不能推成全局没有验证、自然继承已接续或当前成员都合格。问题来自[M1单题卡](../ck3-native-ai/2026-10-27-m1-member-validity-followup.md)。

## 原件与实际采样

原PE101040248 B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，imagebase `0x140000000`；1.20.0.4 / build25734779为来源合同，不是loaded资格。先查已持cache，没有覆盖该RF的完整body；这是所查目录的结果，不是全库不存在的证明。

当前PE中包含writer `2603E46` 的RF确认为 `[2603AF0,26041D6)` / unwind `525FD10`，row132250，文件offset98425656，原12 B为 `f03a6002d641600210fd2505`。实际二分用了17条12 B探测，共204 B元数据；PE头与完整SHA读取另计，不能说总IO只有12 B。

确认边界及cache缺失后，只补854 B `[2603AF0,2603E46)` 和886 B `[2603E60,26041D6)`，复用原26 B。新段SHA分别为 `1a73273e4e9c7f055cae207fdc12ce93fa7c0fa6ca8f591f52f4790f66d8764a`、`d28af401af56dd51fdc3c36ca86975cac9dfcada5e815c507e45ffd5c97ee498`；组装1766 B的SHA为 `6b629517b32864d453905389eeb0f9fb360159ff621fba5ee1a9197033debd5e`。Rizin实际读取完整1766 B，包含26 B重复，不能记为1766 B全部新增。

417条的VA/size/bytes与Rizin PDF逐条一致；85个signed相对目标（53分支、32call）独算一致。独立74块/121边与agf逐值一致；另有2个间接call，RET `26041CF`、INT3 `26041D5`。INT3作为trap终点，不误加正常fallthrough到RF外；异常、恢复及unwind未覆盖。所有34个call的跨过程行为仍opaque，自动签名不授ABI。

## 写入、检查与反例

R15来自entry RCX，RBX为receiver+48的成员vector；entry EDX保存为EDI，经low24索引、容量、完整ID比较解析出R13，失败可选fallback。行跨度20h；旧count选择行后，`2603E56`写row+C=`[R15+10]`，`2603E5D`写row+8=`[R13+18]`，与当前reader的owner/member字段角色对应。没有据此建立公开函数签名。

输入byte地址为entryRSP+28；其业务名和真实caller取值未知。byte非零时，`3BA7→3D22`绕过两次 `2C7DED0`。byte为零时，3BCE传RCX=R13、RDX=R15、R8指向连续五个01、R9=0；AL非零才走append。AL零时第二次3C10传诊断缓冲，后续本地返回路径没有append。

M1给出可满足的普通路径：有效非fallback角色、n=0且无duplicate、输入byte=1、leader=-1；wanted1触发reserve，返回可访问行且count仍0，delta1初始化一次后到3E42/3E56/3E5D。不借signed overflow分支。该见证以不透明call正常返回及所列效果为条件，是局部符号赋值，不是CK3实测。它否定“这两个可见call必经”的局部说法，不能命名其gate或否定其他过程内/跨过程验证。

本RF没有显式receiver+40 target赋值；opaque callees仍可能改状态。member+1B8所指对象的+110写入，与当前actor+1C0 land/targeting指针分开，不能混字段。自然继承caller、实际输入byte、target重绑、loader/default、loaded mod合并及持续资格触发仍UNKNOWN。Java继续将当前actor/date/revision绑定的成员行作为观察，不把身份有效行升级为“持续资格已执行”；本题没有新增DTO、SRC改动或实机资格。领域解释见[M1前向记录](../ck3-native-ai/2026-10-26-m1-rea-resume63.md)。

## 关闭与成本

最小close命令先用真实旧终态/PID做过exercise，约3869字符。新鲜卡16:49:45.101598Z开始；decoder16:50:07.871、Rizin16:50:21.063Z完成close。随后先执行最小close，16:50:33.729Z四个own PID均不存在，0 owned/MCP/exec，早于16:52:45.101598Z截止；原close的payload未分析标记保持不改。

| 计量范围 | 实际结果 |
| --- | --- |
| decoder墙钟 / owned峰值 | 0.466 s / 25341952 B |
| REA service墙钟 / Rizin owned峰值 | 4.908 s / 592994304 B |
| authority至最小owned close | 48.628 s，后继机械核对/独审/富metadata不在内 |
| outer联合峰值、Job0 / Shared / tokens | NOT_MEASURED / NOT_GRANTED / NOT_MEASURED |

Rizin exit0/complete/未截断、仅strings跳过warnings；正证还包括上面的字节/分支/图核对，不能只靠exit0。首个后继checker把Map键传成对象，修正后又明确INT3是trap；都没有重跑backend。16:52:51Z Native点值为logical1086117 B/native1127848 B，非历史峰值，后续metadata另增；case8 MiB，physical release0，不续原provider卡。没有Game/Steam动作或新增游戏日，也没有提速/token收益比较。

## 精确索引

原件根为 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-member-validity01/`：

- [CASE-RECEIPT01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-member-validity01/CASE-RECEIPT01.json>)：11900 B / `ef93b88da5e2894bd521e199173dd9bcb0594e40aaba53fc8f75a4713f4ccd83`，固定两新段、held26、原byte/PDF/图、官方命令和成本。
- [CASE-CLOSED01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-member-validity01/CASE-CLOSED01.json>)：2104 B / `53fdad10698bb8246f9285cb55f42b5c81e726469abb62da5055dacb5cc3af82`，仅原最小owned close。
- [INDEPENDENT-M1-REVIEW01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-member-validity01/INDEPENDENT-M1-REVIEW01.json>)：7921 B / `13d885a20d05d6a50390a3bf345900908d333a14fae40bc7aad39c1bad032300`，17:00:00.458Z另建独审。

下一可定位边是 `2C7DED0` 的actual gate/参数含义，或真实caller如何给输入byte；需要另立问题和预算，本页不授后继查询。
