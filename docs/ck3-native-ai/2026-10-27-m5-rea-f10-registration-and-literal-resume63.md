# M5：F10 注册参数与宗主参战保证 literal（resume63）

machine_id: xenoamess-full-tower-eb9d2c1186。观察：2026-10-26 UTC；本地落文：2026-10-27 Asia/Shanghai。前向补充 [A149D0 共享槽 getter](2026-10-27-m5-rea-calleea149d0-resume63.md) 与 [C2 子谓词](2026-10-27-m5-rea-callee24c3be0-resume63.md)，旧页当时 UNKNOWN/失败/时限边界不改。

当前 PE 的注册本体把 `this+F10` 的地址与字符串 `suzerain_war_participation_guarantee` 的描述符共传给同一 helper。原版该合同默认级为 `none`。这闭合了“调用者请求哪个名称”的有限问题；helper 实际写入、初始化成功、该 receiver 与 getter 返回对象的别名关系、运行中槽值仍未取证，不能把本页转换成合法召集、到场或胜率结论。

## 输入与真实闭场

PE 为 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101040248B，SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。前后 SHA 相同；完整 hash IO 与新增语义字节分列，不复制 PE、不启动游戏，不授加载资格。

证据根 `T=D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases`：

| case（T 下） | 唯一新范围 | actual close / 原件 |
| --- | --- | --- |
| `resume63-m5-termreg31c7680-01` | fresh RF12 + body351；RF `[31C7680,31C77DF,52D8878]`，row170144/file98880384；body file52193920 | 22:24:15.905Z；`CASE-CLOSED01.json` 2106B / `4dbb4e65ed8d253935f747839b091ce72f8781ea5c442ffc01f83c268a2bd640` |
| `resume63-m5-literal48c95c8-01` | RVA48C95C8/file76317640，仅96B，无新 header/RF | 22:37:26.876Z；`CASE-CLOSED01.json` 1513B / `2d01dfb316822650f1ed2f08c3a7330d62d81eebadc6aed8643ed3b62d8fb22e` |

两 case 分别绑定新300+60卡，按窗先 minclose 后领域审查；own PID 缺席、0 owned，原 close 的 PAYLOAD_UNASSESSED 不改。各实际阶段退出0；96 operation=literal reader，沿用 `CAPSTONE-DIRECT-*` 文件名但未执行指令解码。

351 的 Rizin 硬帽1GiB/30s、Capstone256MiB/20s；96 单 Node256MiB/20s、heap64MiB，实际峰值均未触帽，详见各 receipt。outer Job0/joint peak 为 NOT_MEASURED，heap 不等于 OS 硬帽。slot4 已释放，exit0 不授领域资格。

## 351B 本体：地址和描述符共传

`raw/body-031C7680-031C77DF.bin` SHA256 `7c3b148a1c8a08188589625153dfc7686af5cf502f8f4262fc0972c67a30359f`。76条覆盖351B，与 Rizin 逐 VA/size/bytes 相同；独立 signed displacement 重算4个 CALL、7个 RIP target。正常 CFG 单块0边、RET31C77DE；4个 CALL opaque，IDIV 可异常，非完整语义闭合。

entry RCX 在31C76A7保存到 RBX。读取 globalQWORD5CBF1A8 指向对象的 DWORD+AC 与 this+5C，31C76DA 执行 signed IDIV；31C7718 明确写 BYTE[this+EE0]=1。三次31C86B0分别共传 this+EF0/+F00/+F10，另调2E5B110。显式写入与 opaque 副作用禁止把它当只读 getter 调用；末次 helper 的 RAX 返回，未建立 bool/init-success 合同。

F10 链逐条为：

| RVA | 原字节 | 机器级作用 |
| --- | --- | --- |
| 31C7791 | `488d05301e7001` | LEA RAX，按下一指令+signed disp 算得48C95C8 |
| 31C7798 | `c745d024000000` | local[-30] length36 |
| 31C779F | `4c8d83100f0000` | R8=&this+F10 |
| 31C77A6 / 31C77AA | `488945c8` / `4c8d4dc8` | local[-38]=literal地址；R9=&local[-38] |
| 31C77AE | `c645d400` | descriptor flag0 |
| 31C77C5 | `e8e60e0000` | opaque CALL31C86B0 |

RCX 另指向地址来自48C9588的局部描述符（length17/flag0）；最后 setup 未显式重设 RDX，helper signature 未闭合。LEA 只是形成地址；Rizin 自动字符串/global零值/类型/警告保原输出，不作原字节证据。仅机械计算的 F10 literal 新开 case，未 follow helper。

`CROSSCHECK01.json` 3703B / `3bd0245687916f07367a08e3ef13851741d7c425634d45f04c7bf383ba3e5580`；`CASE-RECEIPT01.json` 7388B / `4be87fce955cd78905b189cebc364ca5d30598e5b958ff9111e3465ac56dcd75`。后者当时 literal pending 保持原样，由本页与后继 literal receipt 补充。

flatEvidence/portableBundle RAM 序列化后各只落 gzip，无未压/temp副本；RAM gunzip 重核字节/SHA/JSON值/stdout UTF8 hash。下列均 SHA256：

| gzip | 压缩B / SHA | 原始B / SHA |
| --- | --- | --- |
| `REA-DIRECT-EVIDENCE01.json.gz` | 8448 / `647b781b4c524da6d7cc3c3d5fe3c29c3babd0eeb285ca999e532a06d4a93d92` | 67592 / `f68790ff56c69abfef23ee081a8670e03c1632ef32d2d61eab9185db30302bfe` |
| `REA-DIRECT-BUNDLE01.json.gz` | 8768 / `d59262730967ed9e26873cd25871d18c27633fc6c8f150cdba4f36ada02e1ee6` | 67868 / `91b3bb8182c9bc09267fdf84025b207a6b4091e05f8bc7db80a878153f296d35` |

## 96B literal 与原版定义交叉

`literal96.bin` 96B / SHA256 `7e8cfca70875b15ede3fd67e17dcfbfcb8237ed2c9250a33270fa92e84dbb183`。first NUL=36，正好等于 descriptor length0x24；仅此前作 fatal UTF8/BOM保留/编码往返，得到 `suzerain_war_participation_guarantee`。NUL 后余字节仅保全，不解释成指针或相邻对象。持有 .rdata tuple（rva71147520/raw71142912/rawbytes17124352）映射，fresh SHA 后一次读96B，不复用旧 .2 同 RVA 身份。

`CAPSTONE-DIRECT-STDOUT01.json` 1450B / `a580ea5dcdefd64479e0a215c7ffaa342c6d8692f6096582ce511cb9ab65eeff`；后继 `CASE-RECEIPT01.json` 3039B / `5a35474d907cd1a8ebaed53dece97053b0be3c96860b59345fc76877c767e81e`。

原版 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/subject_contracts/contracts/special_contracts.txt`，20800B / SHA256 `6740231d6158f14850d7e0b819427fe69407a1ee08649df7af847c0fa8b19dd3`：804定义该合同，807–808 none 的 default=yes，815 available，822 flag=`tributary_contract_suzerain_guarantee_override`。831起的 mandala 合同是另一个 key，其 available 为默认；raw 请求名并非 mandala。GUI position 不能证明运行时 byte index；合同 score -2/+2 不能当作军力评分。静态默认声明不证明 loaded key+9F28 的当前 default byte。

REA63 held/RAM 独审已回读，两 case 均为 `INDEPENDENT-REA63-REVIEW01.json`：351 case 2800B / `f486ec750611ad83c6e1b95d7b896bfefae10071f161a8becd046176a471852f`；96 case 2652B / `a1ebcd14a240f5e7e4b23a33eff485870aa8ef69089dd3ed9978cfa68d1885a9`。分别独核逐字节/11 targets/gzip 与 NUL/UTF8/原定义；0新 PE/provider，原 raw/close 不动。

## 接回 caller 与 Java 消费者

C2(24C5260)从 A149D0 返回对象+F10取 key；opaque A11F60 返回值与调用后重读 end 比较，先算 `p2=(P==endAfter?0:P)`，只有 `p2!=0 && child106(receiver,key).AL==0` 才 AL1。不能默认 lookup 前后 collection 稳定。child106 比较所选 byte 与 key+9F28，SETE 仅规范 AL；miss/负 low32 index 选择0仍可能相等，完整 EAX 未规范。结合已有字段合同可提出“宗主保证 level/default 检查”的解释；注册 receiver 与 getter 返回对象别名未闭合，不能称运行 F10 已命名。lookup/helper 内部、当前槽值与合法资格仍未知。

原 mandatory230 后各过滤有条件：仅 `*config.slot3==1` 才进入 sameConf→宗主ID比对→C2；同宗主时 C2.AL非0跳过该次 raw 累加，零才继续。贡献仍是 candidate.land+308 或0的 qwordADD。不能把条件性的网络分量过滤改写为“不允许召集该候选”，也不能把邦联 DWORD、raw总量、到场推断和胜率混同。邦联来源边界见 [现有字段溯源](2026-10-27-m5-confederation-field-provenance-resume63.md)。

现有 Java `WarEntryAssessmentCodec` 继续消费来源/帧绑定的 native network decomposition；`WarEntryCandidates.claim` 继续按实际 `actual_power_ratio_raw` 排序，并校验双方分量。其 projection 保留有效到场、战斗、成本/退出与校准缺口，自动宣战资格仍 false。本页补原生分量来源，不新增 DTO/veto/生产权限；源码与既有27项局部测试未改/重跑，无实机信用。运行中初始化结果及 key/level 来源仍缺，后继只按实际 consumer 需要提有限 seed，不采完整 generic engine。
