# R08：local88 的descriptor、分类与差值子链（1.20.0.4）

本次追加24C4150、2C6A810、24C4790和D1/D2精确64B。它们解释local88内部raw依赖，仍不赋资源4、全局字段、key或结果以收入/军费/币种业务名。`maintenance_attribution=unclosed`，`paid_military_amount_raw=null`、`cadence=null`，不增加研究整卡或动态分子。

来源及整合机器 `machine_id=desktop-3fevhd2-1c74096080`，整合时间 `2026-10-16T15:03:11.646846+00:00`；整合时仓库HEAD `c743520929d4f9a82c17c908b218075018598e2d`仅作读入上下文，四原包各自源提交/观察时间保持原值。来源图像固定为 CK3 1.20.0.4 / Steam25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本次零EXE读取/哈希、游戏/SDK/桌面/构建/主树写入，不把源码知识升级成R185 native已安装或已通过。

前链见[合同贡献与slot专题](episode04-r08-contract-contributions-12004.md)。[portable source bundle](evidence/episode04-r08-rate-application-12004/local88-components-a05.json)只pin a04数据，不复制其全源；新四包的SOURCE、raw ZIP、analysis、所有勘误、关键原capture及失败/重新封包历史均按精确原字节内嵌。旧原件不改；C盘字串只作出处，默认离线入口只用仓库相对文件。其他机器不沿用来源机器安装、权限、PID、容量或实机资格。

## 24C4150：一项基础调用，最多四项条件ADD

完整 `[24C4150,24C4304)`436B/113ins/9jump/11call。D是caller复制的32B descriptor，P28/P20分别来自selectedObject+28/+20，B为可空reporting receiver；本路径B=0。`28C3AC0(P28)`得到的同一个container供所有2C4D530调用使用。

基础调用以WORD[D+0]为rawkey；随后依源码顺序最多四项：

1. `2C4CA30(P28,P20)` EAX非0时取WORD[D+signextend(EAX)*2]；本体没有index范围/正负/sentinel检查。
2. 从`28C2DF0(P20)`对象和其table按D+10/D+14生成调整后的receiver，调QWORD[D+8]；仅AX!=FFFF才转发该rawkey。
3. P20+1B0链的magic等门通过后，选择其receiver或未读global fallback，调QWORD[D+18]；仅AX!=FFFF才转发该rawkey。
4. P20context存在、+1D9 byte非0且2917540(P20) AL真时，取WORD[D+6]，这里没有FFFF门。

每次2C4D530参数保持scale100000/stack6 DWORD0；optional返回指针的首QWORD逐次wrap64 ADD到*out64。**ownbody无初始化MOV/清零，只有四个条件ADD**；基础helper的RAX也未作输出值使用。因此不能把本函数写成“已证明零初始化后的五项和”，更不能把未读2C4D530自动命名成已验证modifier读取。正常返回原out指针，无own clamp。P28/P20业务类型、lookup/output初始化/副作用和callbacks仍按本包未展开处理。

## D1/D2：64B数据与四个未扩读callback

仅读`.rdata [443A530,443A570)`64B，四次16B，raw SHA `3dfa39e3481775f0a529571a9c45331e9ff022da7927a58511091826f5ffff86`。D1/D2各32B；本包没有读字符串、相邻块或callback body。

| descriptor | offset0/2/4/6 WORD literals | +8 callback RVA | +18 callback RVA | signed DWORD+10/+14 |
| --- | --- | --- | --- | --- |
| D1@443A530 |013F/0141/0143/0145 |24C1840 |24C81F0 |0/0 |
| D2@443A550 |0140/0142/0144/0146 |24C1850 |24C81E0 |0/0 |

QWORD是preferred image base140000000下的VA，减该base得到RVA，**不是本次runtime地址**。D1进入24C7C42的additive stage，D2进入24C7C82、之后先加100000再与旧项fixedmul。关系index只有恰为1/2/3时才选这里对应已知WORD；本包不证明实际只返回这些index。相邻奇偶值不代表业务名称，同rawkey多次到达仍保留源顺序，不去重。

D+10/D+14为0也不能把callback1 receiver简化为A+8：`DWORD[QWORD(A+8)+0]`这个未读table调整项仍存在。四个具名callback只做地址链接，不追callee，不能因为地址落.text就补出函数业务。

## 2C6A810：raw分类，G+4CC为signed DWORD

完整 `[2C6A810,2C6AAC5)`693B/187ins/46jump/6call。普通RET为2C6AA89，其后同frame blocks跳回共同epilogue，不能遇首RET就截断。它按context非零count选首ID，做FullID/registry/fallback解析，再沿Land-tagged对象+108祖先和+128 holder比较；kindRaw4另调未展开helper，不能给rawkind4起正式业务名。

原SOURCE的`type_evidence.G`用了word+4CC措辞，661B `TYPE-WIDTH-CORRECTION.actual.json` SHA `77e4332711cb8fe55f1413424c9009fe36021a49779c3614d7b2947e80276acc` 明确：**G+4CC是32位DWORD，当前比较按signed32**。真实`2C6AA6A 3b83cc040000 CMP EAX,DWORD[RBX+4CC]`后为signed JL，不能读成WORD16。原SOURCE与附带纠正同时保留，不重签原文。

正常EAX范围为raw0/1/2/3，不命名关系种类：caller对1跳过rawfactor缩放，对2选另一factor，0与3选同default factor但保留不同原因。直接holder、G bit47、kind4返回ID、祖先holder匹配后的G+4D6/阈值/feature/typepair各按源分支；不把未读global feature当默认true，不假设+108链一定无cycle，也不把P20/P28或G重新命名为payer。6个call internals未展开。

## 24C4790：1936累计charge，唯一968B混合区

原捕获区 `[24C4790,24C4B58)`唯一**968B**，raw SHA `fcdd1e0d69b62cd9743e224418ebbb3177d4d873068309b933dabb6ef976b33e`。其中918B指令区（210ins）、2B padding、两张各24B的DWORD跳表；不能把tables当指令。入口可达205ins，5条secondary-dispatch指令无入口可达前驱，但仍在同一保存区，未删除。两个dispatcher及全部CFG边由原analysis保存。

第一次线性decode在读后失败，没持久化raw/逐读ledger；旧RED保留。后来做metadata恢复与一次raw-first recapture，**累计收费1936B**包含同一968B区的两次读取，第一次charge是同immutable span的重构，**不是原ledger**。metadata≤440B、reads≤40只是保守上界。完整audit tar.xz及最后container-correction ZIP与新raw/analysis同存，不制造首raw一直可读或“1936B唯一源码”的事实。

入口signed delta32<=0直接RET，无S dereference/store、global read或CALL。delta>0时actual selector=5选global地址rate@5C692D0、cap@5C691C0；这只是raw位置，值/业务名未读。其余0..5位置保存在原SOURCE；只有selector>5才用rate=cap=100000，不能把actual5也填该默认。

```text
product = wrap64(signextend(delta32) * raw_rate)
reduction = min_signed(product, raw_cap)
factor = wrap64(100000 - reduction)
S = NativeMulQ100000(oldS, factor)
```

本叶不对reduction设下界，也不钳factor或最终S；native fast/slow的signed、商余和wrap路径保留，不能换成无限精度乘法。caller较后才把最终normal out64夹到[0,100000]。null C使delta=-1，所以此叶保留S；不是写0。B=0跳过所有reporting/helper CALL，B非0路径及异常handler未展开。新source也没有给全局raw率/上限命名，更没有提供一次实际付款。

```mermaid
flowchart TD
  L88["24C7BB0 local88 candidate"]
  D1["443A530 D1 raw32B"]
  D2["443A550 D2 raw32B"]
  pair["24C4150 base helper plus0..4 optional ADDs"]
  class["2C6A810 raw0/1/2/3"]
  difference["24C4790 signed delta transform"]
  unknown["Global values, key/unit/currency names and paid/cadence UNKNOWN"]
  D1 -->|"24C7C42 additive-stage descriptor"| pair
  D2 -->|"24C7C82 before add100000 and multiply"| pair
  pair -->|"callee output base initialization still unknown"| L88
  L88 -->|"24C7D6E; raw1 skip, raw2 alternative,0/3 default"| class
  L88 -->|"24C801D; actualselector5 and optionalB0"| difference
  difference -.->|"global raw addresses known; values and units not read"| unknown
  pair -.->|"2C4D530/callback bodies not expanded in this package"| unknown
```

## 复用与验证

先接a04数据，再接本包的三个全新path；不修改a03/a04旧专题或源码。仓库根执行：

```text
<project-python> -B -O docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/verify_r08_local88_components.py
```

候选阶段可分别以`--bundle`、`--prior-bundle`指定两份relative.patch；验证器只在内存提取完整new-file JSON。它校原件SHA、指令与混合table CFG、signed DWORD勘误、四条incoming CALL、四条RIP literal边和64B/readledger；不会follow callback、读EXE、建游戏状态或证明业务语义。`--extract-originals <不存在的新目录>`可无损还原全部原JSON/ZIP/tar.xz，历史绝对路径从不作为输入读取。paid/cadence/币种与unit继续unknown，source/cold证据不替代实机付款或R08整卡验收。
