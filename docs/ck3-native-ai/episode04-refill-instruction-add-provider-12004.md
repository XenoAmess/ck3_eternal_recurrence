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
