# Resume63：2C7DED0 的 target、flags 和 AL 传播

machine_id: `xenoamess-full-tower-eb9d2c1186`。本题为离线 PE 观察，不选 live actor、不启动 CK3/Steam。来源为新 case `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-gate2c7ded0-01/`；旧 member-validity case 的 caller 已先独立审阅。**本地机制可读，join/persistent 的领域命名仍 UNKNOWN。**

## 可证伪问题与范围

实际 caller `2603BCE` 传 RCX=已解析 member、RDX=faction receiver、R8=连续五个初始 `01`、R9=null。AL 非零才走 append；AL 零后 `2603C10` 以另一组五 `01` 和非空输出对象重调，第二返回 AL 不再决定 append。caller 的第五 stack byte 非零可绕过两次调用；其业务含义和自然继承 trigger 仍未知。

本题检查 callee 的正常返回 AL、五字节与 nullable 输出参数、target 来源，允许原始 AL 不归一化、输出改变资格或副作用、target 来源不同、opaque call 等反例。先查 `shared-span-cache`/`function-match-core` 文件名共 8879/333 项，无覆盖 RF 完整 body；这是声明 scope 内未命中，不是全盘不存在。历史 pdata 只作 locator。

fresh PE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，101040248 B，image base `0x140000000`；build 来源合同 1.20.0.4/build25734779，不授 loaded qualification。新鲜 pdata row153797 为 `[2C7DED0,2C7E1E7,52B878C]`，raw12 `d0dec702e7e1c7028c872b05`，文件偏移98684220；二分实际17行共204 metadata B，header/全文件 hash I/O 另计。入口相同、RF≤4096、缓存未命中后才固定读取791 B；没有跟 callee/globaldata/incoming/vtable。

新 raw `raw/new-02C7DED0-02C7E1E7.bin` SHA `ff4fafaf336cc499bddcdf6b5c186b69eb163a9928e5370b27cfbdebed4cd76d`。Capstone197条与 Rizin pdf 逐 VA/size/bytes 相等；42条直接转移独算 signed displacement（26 branch、16 call）；独立正常 CFG 为36 blocks/60 edges、2间接 call，唯一 RET `2C7E1E6`，没有范围外非 call 边。opaque call 正常返回、Win64 nonvolatile 保存是局部分析前提，不覆盖异常/unwind/并发修改。flat Evidence 与 portable 单 record 按 JSON 值、类型、数组顺序 deepEqual。

## 有限机制

- entry `RDX+40` dword 按既有 faction 字段合同解释为 target full CharacterID；按 low24/capacity/slot+8/对象+18完整 ID 校验解析，失败走 fallback，未在本地拒绝 fallback。首调用 `2C7D920` 的 RCX=member，RDX=该 target 指针，R8=原 flags 指针，R9=`faction+20` type 指针，第五 stack 参数=原输出对象。
- 首返回记作原始低字节 P0，`MOVZX EDI,AL` 保存。P0 为0且输出为空时直接失败；非空输出使执行继续。首 helper 内部如何读取五 flags、如何执行资格或生成输出尚未知。
- 首 helper 返回之后才读原 flags 指针 `+2`；非零时调用 `2603A90(faction)`，其 AL 非零构成一个本地失败条件。首 helper 拿到同一指针，未证明只读，因此初始五 `01` 不能证明此时仍为 `01`。其余四字节在本 RF 无直接读取，不代表首 helper 不用它们。
- 后续重新读取 `faction+44` leader full ID并解析；与 member ID 不同才走 `28BC250(leader,member)`，读返回对象+20，再经另一 registry 的 full ID/对象+8 校验读取对象+358。该检查的领域类型及 helper 副作用不在本题闭合；不能把前后读取当作一个不可变 frame。
- 两个本地失败块在输出为空时早返回0；输出非空时调用输出/清理链并清 DIL，再继续。末调用 `2602720(faction,member,output)` 的 AL 也可令结果为0。R9/output 既用于本地分支，又传给首 helper 的第五参数及末 helper 的 R8，不能宣称它只影响诊断文本。
- 在正常 Win64 callee 保存 RDI 的前提下，正常返回 AL 只会保留原始 P0 或清0；没有将非零 P0 归一为1。`MOVZX EAX,DIL` 路径零扩展这个原始字节，早 `XOR AL,AL` 路径不保证 EAX 高位。没有证明 helper 是 pure，也没有证明 R9=null 与非空的资格等价。

Rizin 自动字符串注释只是工具注释，未单独补读其 global 原件。脚本名、错误文本和 Rizin 自动 signature 均不能代替 type loader→字段→实际 evaluator 的绑定。本题没有命名 `is_character_valid`、`can_character_join` 或 persistent-validity；Java 不据此新增“已知 persistent=true”字段。当前 actor/date/revision/member-row 的真实观测与 UNKNOWN 保持分开。

## 工具、成本与闭场

沿已安装官方 REA service 和原 OwnedCommand/WindowsOwnedProcess，Node heap128 MiB；新 case 独立 TMP/export/stdout。provider 限1 GiB/30s、decoder256 MiB/20s，card work120s+close60s；最多4独立 provider 并发，本题 slot1。普通 research-plan check=0，`--for-observation`=2，offline-only 无 live window 的拒绝原样保存。

decoder 420ms、job peak25272320 B，close17:24:38.596Z；REA 4583ms、Rizin job peak593039360 B，close17:24:52.291Z，service.close 无错误。新语义791 B；Rizin复读791 B与decoder不同工具的重复明确计数，不称“总 I/O 只有791 B”。provider 输出未截断，PE hash 前后相同。outer/joint peak 与 outer Job0 均未测，不授 Shared、native dossier 或 Game 资格。

先最小 close，再机械/领域分析：`CASE-CLOSED01.json`2091 B SHA `c7bd86d3401de151f015c075ea2bec04543c6e9a66ecae8e5765c8f769022bcf`，17:25:05.420Z，card T0→70.886s，早于17:26:54.534174Z；4个实际 owned PID 均不存在，0 owned/MCP/business exec。此成本只到最小闭场，不是完整研究耗时。原 close 的 `PAYLOAD_UNASSESSED` 不回填。

机械原件 `CONTROL-FLOW01.json`4292 B / `933b6ab071ea92512b81b98fa730747e2dc50480ad6fa315e0f066b50b829adc`；`CROSSCHECK01.json`3931 B / `60683b48915da71e6141f158b00d89971811421371aeea9eca17e41c6bcc95c5`。M1 后继独审 `INDEPENDENT-M1-GATE-REVIEW01.json`7913 B / `121f9ebc5bd666a038ba9257415e694c2f2d18d4e0a83a48b02192ae676ba88d`，实际17:34:55.639Z，独立重核字节、signed targets、正常 CFG 和全部 AL 返回，保上述 UNKNOWN。

富 `CASE-RECEIPT01.json`10942 B / `a823b23e0e0ae2f01097e4f37ff81cadea2db35dcf323e699d094fbe20cf1100` 在最小 close 后另行 CREATE_NEW。执行卡 T0 至该 receipt 为833.929s，包含独审、方法协调与记录；准备前的缓存/框架阅读未完整计时，因此整个研究总耗时未测，不能把70.886s或4583ms当作它。一次后态摘要误包含整个 provider stdout，终端预览截断；独立文件未截断，核对均基于原件 SHA/JSON。原件导航由 [sources.json](sources.json) 前向登记。

完整领域命名的下一断边是实际首 helper `2C7D920` 及 loader 映射。Root 已另授850 B有限问题；仍须新 PLAN、资源卡和 fresh300s work+60s close，不在本 case 自动扩读或续旧180秒卡。
