# R06 instruction-local ADD 发布候选

machine_id: `desktop-3fevhd2-1c74096080`；来源观察 `2026-10-16T00:07Z`；
代码基线 `c4992c304d196135d9590799d69ffb3c9f5510e6`，实际 CK3 1.20.0.4
EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
本候选仅源码/新 Python 反例，不读取 EXE、不构建或运行项目 EXE、不接触游戏/SDK/桌面，
不修改 Root 主树。没有新增 CK3 actual ADD 或完整 R06 资格。

当前 a09 已含 `research/refill_add_hwprobe_12004.cpp`，但普通 native CMake
只发布旧 war31 helper，没有这个 production executable target。已验冷包的
`refill_cold_observer.exe` 只有 `--fixture-meta`，强制同目录 synthetic
`refill_cold_target.exe`；不能拿它的 build/SYSTEM gate 当成 CK3 sampler。
现有 `consume_cold_refill_add.py` 也明确只授 synthetic item。

本候选新增独立 CMake project `research/refill_add_live_12004`，目标
`refill_add_hwprobe_12004` 直接编译既有 production 源。选项
`XAR_ENABLE_REFILL_ADD_HWPROBE_12004` 默认 OFF；OFF 的程序返回3，不开进程。
ON 仍要求原有 `--enable` 和完整九组实际参数。没有新任意地址、fixture offset、
MCP gameplay action 或 instruction detour；固定实际 `2A98B88/2A98B8B`。

生产 source ABI 和原指令已由[硬件观察合同](episode04-refill-hardware-add-observer-12004.md)
及[八例冷资格](episode04-refill-hardware-add-cold-qualification-12004.md)提供。
本增量不重做8例，不把 synthetic 原片升级为 CK3。新 CMake/生产 binary 尚未编译验收；
标准 producer、源码冻结、精确新 EXE SHA 与实际 SYSTEM exclusion、Root 的独立窗口
仍是运行前置条件。冷 EXE 的旧 exclusion 路径不能转移到新 binary。

## 实际存在的命令接口

构建使用既有 `tools/run_native_msvc.py`，没有新假 launcher。Root 应先在政策允许的
research 根冻结 source（保留 live project 与其 `../refill_add_hwprobe_12004.cpp`
相对拓扑）及全部输入 pins，再用实际 source/build 根替换以下占位项。
本页没有声称这些新输出路径已经获得执行准入：

```text
py tools/run_native_msvc.py --source-dir <frozen-research>/refill_add_live_12004 --build-dir <approved-new-tinyroot>/build --defender-external-candidate refill-add-live-12004 --cmake-define XAR_ENABLE_REFILL_ADD_HWPROBE_12004=ON --configure --build --target refill_add_hwprobe_12004
```

producer 或 SYSTEM 实际读回失败时不运行。只有 Root 核过对应新 EXE/源冻结/机器和容量
门禁、唯一游戏 owner 及有限观察计划，才能使用生产 `wmain` **已经存在的参数语法**：

```text
<verified-refill_add_hwprobe_12004.exe> --enable --pid <actual-pid> --thread <actual-native-tid> --regiment <full-u32-Regi> --slot <0..6> --created <actual-process-FILETIME> --timeout-ms <1000..300000> --raw <fresh-NDJSON> --ready <fresh-ready-JSON> --machine-id <actual-machine-id>
```

`--thread` 来自当前同 PID/create-time 的实际 native owner/core event，既有观察合同
的 `Token.thread_id` 可复用（`army_observed_phase_contract_12004.py`）。不能使用 Python/
SDK caller 的 TID，不能从其他进程或旧 scene 继承。Full Regi/slot/ArRg/CArmy 来自当次
完整 DATA cohort。必须等 ready 文件确认选定线程已武装，才推进自然窗口；本观察器
不负责暂停/推进游戏。timeout、100000 总 trap 上限、未知/失败不重试为成功的边界保持原样。

## 生产 wire 与独立消费者

native raw v2 增补实际 guard 读取并比较的9B十六进制、selected TID/full Regi/slot、
timeout、真实全 trap ordinal、原始 caller context 和总 trap budget。ADD、MOV/CMP、
RF 恢复、保存/恢复 DR、detach 流程没有改写。两次 trap 间的原指令由 CPU 执行，
没有 replay/emulation；现场没有 synthetic 独立 ADD counter，不能伪造一个。

`normalize_instruction_local_refill_add_12004(raw_bytes, binding)` 严格检查完整六行 wire、
生产来源和实际9B、PID/create/TID/完整 Regi/slot/ArRg/CArmy、相邻全 trap 次序、252B
七槽仅当前 DWORD 变化、整数 DWORD 模加、q signed/unsigned、全部 DATA 顺序和别名、
native pair 及真实 clean restore/detach。q0、负q、wrap 分别保留，不夹零或去除别名。

`binding` 的 schema 为 `xar.ck3.refill_ADD_12004.owner_binding.v1`，必须包含：

| 字段 | 实际来源 |
|---|---|
| machine_id / pid / process_created_filetime / thread_id | 当前机器、进程代际与 native TID |
| exact_executable_sha256 | 当前真实运行 .4 的 frozen/runtime 准入 |
| regi_full_id_u32 / physical_slot / arrg_full_id_i32 / army_full_id_i32 | 当前完整 DATA cohort |
| connection_generation / episode_run_id | 当前 Root 场次身份；不是该 ADD 的自然父 token |
| source_admission_receipt_sha256 | Root 已独立核过的当前 source/runtime 原回执 pin |
| observer_build_and_SYSTEM_gate_receipt_sha256 | Root 已核过的新 sampler build/SYSTEM 原回执 pin |

消费者验证这些值与 native wire 对应，并保留 pins；它不代替 Root 对原回执的真实性、
权限及新鲜度核对，`owner_admission_authority_verified_here=false` 保持明确。
输入必须来自已准入的真实 native sampler，不能把构造 JSON 当实机事实。
`consume_live_refill_add.py --raw ... --binding ... --output ...` 是本包实际实现的只读
消费入口，输出独立 instruction item，不启动或连接游戏。

`attach_instruction_local_refill_add_12004` 可把该 item 作为
`instruction_local_ADD_v1` 附到现有 NET qualification。旧顶层 `actual_ADD_observed=false`
及原 missing 输入保持原来源语义；新 item 自己记录一条实际物理 ADD。
没有共同 active-core carrier，不能把它归给某条 entry/return NET；natural/core token、
native event date 仍 null，整窗覆盖、toggle effect、完整 R06 qualification 仍 false。

本候选≤256KiB，计入父 active32MiB 池；a09 根总上限仍2MiB，原复核截止
`2026-10-16T07:45:01.597Z`，不自动延长。Root 后续独立构建/现场证据不能由本源码包预授。


## 2026-10-17：R197前固定指令 producer 的 q 来源增量

machine_id: `desktop-3fevhd2-1c74096080`；本轮观察时间
`2026-10-17T03:46Z`；检查起点 `d59568127d96454fcbd99088cb93dbc092e0e53b`，
交付按两处实际 preimage SHA 绑定，Root 后续独占提交不视为本 lane 写入。
本增量只复用 held .4 原件，不打开/哈希游戏 EXE，不调用 SDK/游戏/桌面，不构建。
旧段落的构建及 UI 能力状态属于当时记录；当前 Root 已接真实 checkbox slot13
enable/disable，本增量不重新研究权限 reader 或授予新的 toggle 实机结果。

真正兵员写点没有变：`2A98B53 -> 262C9B0` 返回非零后，
`B80` 从 `[RAX-4]` 读 signed q-index，`B84` 从
`[RSP+20+4*q_index]` 装 EDX，`B88:0150F4` 执行
`ADD DWORD[RAX-C],EDX`，`B8B` 是即时独立后态点，尚未执行其 MOV。
`RAX=Regi+28+physical_slot*24`，所以**真正 current 目的为
`Regi+1C+physical_slot*24`**，七槽拷贝从 Regi+18 开始，其槽内 current 偏移4。
物理槽与 q-index 必须分别保存。后续 `BEF` pairclear 和整个 core 返回净差都不能
替代这个 ADD；正 NET、cash personal_add 及入口 wrapper 均不是同一 source。

现有 `army_regular_core_passive_12004.cpp` 仅安装15B入口 detour，保存 entry/return
七槽/DATA，当前 qualifier 的 `instruction_local_ADD_producer_not_published` 正确。
宏 `XAR_ENABLE_REFILL_CORE_INVOCATION_PARENT_12004` 默认0；开启时共同 TLS token
仅包围真实 synchronous original call。外部 debugger 无法调用目标线程 TLS，
没有可从该15B detour直接复用的任意指令完整寄存器/XSTATE trampoline。

已有 fixed `refill_add_hwprobe_12004` 是独立 source-only producer 路线，
不是已装入 DLL 的 journal publisher。真正仍缺的是**当前精确 source/build/SYSTEM
及冷验准入后的安装/实际采样**；同线程 native publisher 还缺独立冷验证的执行入口。
源码和 synthetic 通过均不等于已采 actual ADD。本轮不把该工具接入 R197。
不需要新游戏字节、全 EXE 扫描或全局 fence 来证明上述固定写点。

本次候选只升级既有 hardware raw 为 `hwprobe_raw.v3`：目标两次 trap 各增加一次
28B guarded read，保存 `[RSP+20,RSP+3C)` 的实际 stack window，独立核查所选 DWORD
等于 EDX。只在 q-index 0..6 时派生所选槽；这是收集边界，不声称 native 本身做了
这个 bounds check。不可读、超界或不匹配保留 `stack_q_source_complete=false`，
不能退回 v2 冒称 q 来源闭合。前/后完整28B还必须一致。
原九组 CLI 参数、固定 B88/B8B、默认 OFF、CPU 原 ADD 一次、finite hits/timeout、
线程 ownership、DR restore/detach 及完整 FullID/物理七槽/DATA捕获均保持原实现。

`normalize_instruction_local_refill_add_12004` 同时接受原 v2 与新 v3。
v3 先严格核新字段，再复用原 v2 全部 identity/物理模加/DATA/clean-detach 规则；
输出保留**原始 v3 raw SHA**，并增加 `instruction_stack_q_source_v1`。
其 source path 是依据 exact .4 PC 的控制流推论：request 非零进入物理循环；
不是声称当场读到了 AL，也不声称采得各 permission/needs/manpower 分支。
EDX 是原生已生成的 q DWORD；没有另加一层 cap，也不把它叫 uncapped request。
原 request loop 若有多个 chunk 共享 q-index，最终 stack DWORD 也不能反推每个写者。

新 item 仍独立于 core NET：`native_core_token=null`，自然父/日期未知，
整窗覆盖、toggle effect、完整 R06 business qualification 都为 false。
下一次 Root 应先冻结**该新版本** producer 与 consumer，履行新 binary 的标准构建及
精确 SYSTEM 实际读回，再做独立冷验证；新 q 分支未获 native 编译或运行资格。
以后若需同线程自然归因，应在单独冷夹具验证真实 thread-local instruction 入口，
复用共同 invocation token，并实证完整上下文保全、原 ADD 一次和 cleanup；
不把本次 q 数据接线当作该安装层。

新增测试仅覆盖这条 q seam：物理槽与 q-index 不同仍成功、q/EDX失配、读取失败或
布尔别名、超界/短窗口、其他 q 槽被改、v2重标签拒绝，以及零/负/wrap和旧 NET
资格不升级。构造 wire 只证明严格消费者行为，不是实机输入。
本轮 external root 上限128KiB，独立新任务额度；没有续签旧32/512MiB池或旧截止时间。
精确 patch、source pins、5方法/9子例实际结果与容量收口见本轮交付回执。


### R197 a02：共用真实 RPM 函数的冷验证入口（尚未构建）

machine_id: `desktop-3fevhd2-1c74096080`；准备于 `2026-10-17T04:09Z`。
本独立≤64KiB候选顺序接在 a01 v3 patch 后，a01 原件保持不动；
本轮只做 source/patch 拼接检查，没有运行 CMake、MSVC、项目 EXE、SDK 或游戏。

`refill_stack_q_source_12004.hpp::ReadRefillStackQ12004` 是 v3 producer
实际调用的同一函数：q-index边界、地址加法溢出、一次真实 ReadProcessMemory 的
28B长度及 EDX 一致性核验。函数保留 status、read_attempted、实际 bytes_read/
Win32错误及原字节，未把短读或失败填成成功。GetCurrentProcess 的合法 -1 pseudo-handle
可用于冷夹具，不把它当成无效句柄。原 v3 wire 字段与 Python 消费合同保持不变。

新增明确 target `refill_stack_q_cold_12004`，`EXCLUDE_FROM_ALL`，编译选项
`XAR_ENABLE_REFILL_STACK_Q_COLD_12004` 默认 OFF。OFF二进制返回3且不读取进程内存。
ON入口仅接受 `--cold-self --machine-id <当次实际machine_id>`，无PID、远程地址、RVA、
worker或fixture offset参数。它只用自身局部7DWORD缓冲；fixture_rsp只是
q地址减20的函数参数几何，不是采得的CPU RSP。输出也明确RSP未观测、ADD未观测、
DR未安装、core token为空、完整R06为false。

以后由 Root 在获准 research 根冻结源码，使用既有 standard producer 并核验
新EXE对应的实际 SYSTEM 回执，才可构建/运行。以下只是已实现入口的调用形式，
不声称占位路径已被准入，也不授权现在执行：

```text
py tools/run_native_msvc.py --source-dir <frozen-research>/refill_add_live_12004 --build-dir <approved-new-build> --defender-external-candidate refill-add-live-12004 --cmake-define XAR_ENABLE_REFILL_STACK_Q_COLD_12004=ON --configure --build --target refill_stack_q_cold_12004
<exact-SYSTEM-verified>/refill_stack_q_cold_12004.exe --cold-self --machine-id <actual-machine-id>
```

Root仍需确认 standard producer 接受新增声明 target、精确源码/输出路径和SYSTEM读回；
本包没有新launcher或绕过producer。CMake把实际 helper/fixture 的文件 SHA 编入回执。
实际执行后只能证明真实本机 RPM 共用 q 函数能读出局部28B、识别EDX失配、
捕获前后不变及非选中q槽变化，并在索引/地址溢出时未尝试RPM。
前后窗口一致性仍由既有 strict Python consumer裁定，cold fixture没有替换该合同。
它不证明 CK3 的真实RSP/线程/FullID/DATA、DR生命周期、原ADD一次、实际指令样本、
toggle effect或同线程token。没有重跑旧9个Python子例，也没有借旧cold observer授v3资格。


### R197 a03：未来真实 ADD 的最短闭环与两项先修

machine_id: `desktop-3fevhd2-1c74096080`；离线检查 `2026-10-17T04:38Z`，
主树观察 `85eb547cca4fddaec4b8a89ec9dd203e6935299c`。
a01/a02原件不改，本delta接在二者之后；没有SDK、EXE读取、构建、原生运行或R197安装。

复用现成 external debugger 即可先取得一个 physical ADD，不必先造 DLL 中间指令
trampoline。`ArmThread` 在 debug event 暂停点，针对 fresh owner TID 保存DR0..3/6/7、
拒绝占用DR/TF，安装固定B88/B8B并读回。`OwnDebugThread` DuplicateHandle拥有线程，
`RetireDebugThread` 同时删除handle、armed集合及saved DR，不能复用另一代际状态。
`GetContext`取得的是该目标线程实际寄存器，不是Python/SDK线程或query线程的TLS。
Full Regi/slot/ArRg/CArmy仍必须来自当次完整DATA cohort；fresh PID/create-time、
native owner TID和byte guards在attach前、arm前及ready处核对，ready后才由Root推进。

本轮补两项真实源码缺口：旧 `SyntheticAdd` 没有初始化RSP+20..3B，旧8例无法证明
v3目标线程的q来源。现在只加5条MOV：覆盖完整7DWORD，再按实际RCX q-index写EDX；
保留RAX/EDX/RSI/RSP/flags、原ADD和其后MOV/CMP及独立执行计数。
这只准备未来冷进程的真实stack窗口，没有新增native通过证据。
另在production主循环和cleanup循环的EXIT_THREAD分支中，先retire全部状态，
选定TID退出即 `selected_thread_exited_during_probe` RED；原owner绑定不会接纳同数TID
后来复用的新线程。非选定线程正常退出不触发该RED。此规则尚未经过OS冷执行。

现有清理可继续复用：`ClearThread`恢复保存DR并GetContext读回（Dr6仅核低4状态位），
`ClearAll`、超时DebugBreakProcess取得暂停点、SuspendAndClearAll fallback、实际
ContinueDebugEvent返回及DebugActiveProcessStop。strict v3仍要求真实clean终态和完整pair。
旧冷target的独立auditor与ADD计数可复用；旧cold observer是分开的历史clone，
不是当前production精确translation unit的冷资格，也不能覆盖新ownership/selected-exit分支。

下一独立冷窗口的最小施工：先实际执行a02共享RPM小target，只授局部q函数；
再复用既有cold target、gate/audit和runner，为当前production Probe加**单独cold-only
translation-unit入口**，保留production九组参数与CK3 fixed-site guard。
目前虽有fixture_sites内部参数及编译guard，wmain没有cold CLI，不能直接拿现EXE接冷metadata。
适配只需已知synthetic sibling的sites和两处mock registry slot（旧cold Resolve已具名实现）；
serializer必须输出独立synthetic schema/site地址，禁止把固定CK3 RVA或production v3 wire
用于该冷target。然后只验新增q与selected-thread-exit差异及当前Probe的实际DR恢复/清理，
不重建框架、不重跑整套旧矩阵。这里描述下一入口，尚未声称实现或执行该cold TU。

冷资格成立后，Root另冻结新producer build/SYSTEM/runtime及单目标有限观察窗口，
使用原 `--enable` 九组参数，待fresh ready后推进，严格消费native v3原六行+owner binding。
首条item可证明固定B88物理ADD、q源、FullID/slot/DATA及DWORD模加；自然core token仍null。
`CurrentNativeInvocationContext12004`只能由实际core线程读取。若要同一core NET因果，
下一最小边是沿既有original-once wrapper复制该线程active invocation/entry event标量，
给外部两trap独立稳定读回；不能用query TLS、TID、日期、RSP返回地址或QPC猜token。
不需要新EXE字节来施工这些已知源码边，也不引入全局fence。


### R197 a04：可构建的 shared-Probe cold-only 入口（源码候选）

machine_id: `desktop-3fevhd2-1c74096080`；准备 `2026-10-17T04:47Z`，主树85eb不改。
a04顺序接a01→a02→a03，旧包冻结。新 cold TU 直接include当前production cpp，
只改名其禁用的wmain；Probe、ReadHit、共享q函数、线程ownership和DR清理均编译同一正文。
`XAR_ENABLE_REFILL_V3_COLD_PROBE_12004`默认OFF，OFF入口返回3且不打开进程。
ON入口只接受旧cold metadata七组参数；先拒绝重复/超长/越界metadata，核同目录
`refill_cold_target.exe`实际映像、进程代际、module base及sites/mock slots均在该image内，
再沿Probe在attach/arm/ready时复核。production九组CLI不变，不能传fixture sites。
冷编译只能使用既有synthetic两处registry slot，不能回落到game-shaped fallback地址。

新CMake target `refill_v3_cold_observer_12004` EXCLUDE_FROM_ALL，输出basename为
`refill_cold_observer.exe`，仅为复用旧runner双EXE合同；**必须新build目录、新source/hash/
SYSTEM门禁**，不覆盖或继承旧同名binary证据。ON另声明既有`refill_cold_target`，使用a03
更新的synthetic asm与原target/auditor。标准producer未来只build这两个明确target。
冷raw/ready使用独立shared_probe_cold schema，site输出synthetic地址；pair明确
`CK3_actual_ADD_observed=false`。production wire仍是v3，严格production consumer拒绝冷源。

没有新driver/worker：旧runner增加`--shared-v3`与显式`--case`，前者必须提供后者，
不自动重跑旧八例。旧cold consumer对新schema额外核完整28B q、index/EDX和前后不变，
仍要求原始raw SHA、独立DR audit/ADD once计数与synthetic来源。未来先做单个normal：

```text
py tools/run_native_msvc.py --source-dir <frozen-research>/refill_add_live_12004 --build-dir <new-approved-cold-build> --defender-external-candidate refill-add-live-12004 --cmake-define XAR_ENABLE_REFILL_V3_COLD_PROBE_12004=ON --configure --build --target refill_cold_target --target refill_v3_cold_observer_12004
py <frozen-research>/refill_add_cold_12004/run_cold_fixture.py --repo <actual-repo> --build-dir <new-exact-SYSTEM-verified-build> --output-root <new-attempt> --shared-v3 --case normal
py <frozen-research>/refill_add_cold_12004/consume_cold_refill_add.py --case <new-attempt>/normal --output <new-synthetic-item>
```

上述为已实现CLI形状；Root仍需确认producer多target参数、受准source拓扑和新路径SYSTEM实际
读回，本文不预授执行。仅源码/新离线wire拒绝与四包组合检查，本轮未构建或执行native，
未触SDK/game/DR。selected TID单独退出及同数重用的OS case仍待独立冷验证，normal不能
代替它；common core token/carrier未实现。冷通过也只授shared-Probe synthetic资格，
不授真实CK3 ADD、自然父归因、开关效果或完整R06。
