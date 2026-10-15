# CK3 1.20.0.4：四个 raw term 的 writer-PC 观察候选

已完成真实冷夹具和未来默认关闭的观察器源码，尚未 attach CK3；没有已知军事 producer，也没有已付维护费归因。目标是取得新鲜 secondary context 四字段写后PC，再作有限 source 研究。现有 [R0174父链](war-payment-r0174-actual-parent-source-12004.md) 未直接生产四term，不再靠数值命名。

源码位于 [独立research目录](../../ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/CMakeLists.txt)，只增加research源码/工具，不改主CMake或生产默认行为。基于dcda，明确依赖cash当前raw leaf patch SHA `f19482b3e38f15bc927c696efcddad27e010bfee1659606dbae438d932b03622`；该leaf共用原generic默认OFF编译flag，没有新getter/query/detour。运行入场要显式导入新的leaf validator，缺代码即拒绝，不能靠旧normalizer放行。

Character基址按既有production Frame/ActorMatches读取 `+18` FullID、`+1C` magic0x43686172、`+1D0` death pointer空；secondary为 `*(Character+1C0)`，四signed64位于2C0/2C8/28/30。稳定的新鲜context须8B对齐；DR0..3都用write/LEN8、DR7 owned mask0x99990055。以前cold的Regi-shaped +10/+14镜像不能授游戏ABI资格；从未将该错误版本用于CK3。

入场复用现有private现金current-resources query的optional `current_raw_context_v1`；它是当前暂停态raw读回，不是wallet callback。单leaf不证明PID/create/gen/window/epoch，必须同时验证原cash journal/current_session、独立配对snapshot以及Root指定完整身份。future adapter额外要求同host machine-labelled execution gate绑定精确SYSTEM receipt/manifest SHA；不能把普通token ACK或别机旧receipt当本机生效。原SYSTEM receipt没有machine_id时保留其原样，通过原机器实际gate关联，不补造SYSTEM字段。

Native再次核process create/name、精确.4来源资格、mapped image size与已证parent16B anchor，读取四值后及每个停止线程安装DR前复核当前Character/context。该anchor不是整image重新hash。已有DR/TF在attach前预检拒绝；观察阶段所有新线程在Continue前设DR并读回，不只SDK/UI线程。借用debug-event线程handle会DuplicateHandle后由本工具关闭；两处EXIT_THREAD均退休saved map；新thread ownership清旧generation，不能把旧TID状态套到新线程。

每个trap保留实际线程、QPC、FullID/Character/context、精确字段地址、DR6与原始整数寄存器、last-observed before和post-store after。相同值写也保留事件。一次debug event可能命中多个slot，因此event_ordinal与slot_hit_ordinal分开。**RIP_after不是已解码instruction_start**；后者持续null。before只是上次样本，不能宣称原子写前值；admission date只是query时的日期，actual writer game date保持null。

后续仅将真正同image RIP_after转为有限来源请求：用 `RIP_after-1` 找包含写指令末字节的.pdata，这不是猜instruction start；由真实function/root entry有限解码，定位正好结束于RIP_after的指令并复核其写入范围。每scope最多512B metadata/8192B code/48reads；不扫邻居/globalxref。foreign PC先保留unknown，没有module来源不能硬套.4 RVA。

## 实际资格和限制

[原件archive索引](acceptance/2026-10-16-maintenance-writer-watch/ARCHIVE-INDEX.json) 保留每份actual字节/SHA及失败attempt；[最终定向报告](acceptance/2026-10-16-maintenance-writer-watch/TARGETED-QUALIFICATION.final-a01.actual.json) 明确以下区别。

- 历史source-a05/build-a04真实8case全部通过：四字段真实MOV、同值写、新worker、timeout、context变化、默认OFF、unaligned、wrongFullID。独立target main/worker与native readback证明owned DR全6原始值恢复；但当时合成Character镜像+10/+14，不能授actual Character ABI。
- 历史strict consumer实际Python `-B -O` 5个rawcase+24恶例拒绝，通过[严格回执](acceptance/2026-10-16-maintenance-writer-watch/STRICT-CONSUMER.a03.actual.json)。覆盖postRIP伪start、类型/地址/offset/FullID、错误RW/LEN/DR6、未恢复/未detach/假globalcoverage或knownproducer。
- 最终source-a08/build-a07仅补审查相关定向验证，没有反复全跑旧8+24：修正Character+18/+1C后实际4trap及owned DR全6恢复PASS；同一个compiled BeginThreadOwnership函数4检查PASS（不是OS真的复用TID）；occupied DR在DebugActiveProcess前exit2，无raw/ready/SetContext。
- occupied反例的原始全6向量并不完全相等：实际观察到DR6 xorffff0ff0、DR7 xor400，地址和启用/控制位保持。只读Suspend/GetContext/Resume路径也出现此规范化，平台解释仅为推论；**不能宣称该occupied case全6原样恢复**。原严格失败完整保留，最终资格只包含前置拒绝/不接管。无事后改GREEN历史。
- [future adapter拒绝回执](acceptance/2026-10-16-maintenance-writer-watch/ADMISSION-FAIL-CLOSED.a01.actual.json) 只实际测了defaultOFF和旧archive缺新leaf/source的拒绝；没有正向live admission、没有CK3模式执行。当前raw leaf native9-case夹具另仅有源码，90项Python检查属于其独立包；不能混成native实机。

所有运行机器为desktop-3fevhd2-1c74096080，UTC实际时间见原件。知识/代码/归档可移机，进程、地址、SYSTEM设置和观察资格不能迁移。本候选始终known_producer=false、maintenance_attribution=unclosed。

## 复用入口

普通clone可先执行本证据目录的 `verify_repository.py`，只用stdlib验证源码pins、archive全部成员和此文链接，不读游戏。新机器从源码新建external build，不能使用旧EXE或别机SYSTEM gate：

```text
python -B ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/build_fixture.py --repo REPO --build-dir NEW_EXTERNAL_BUILD
python -B -O ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/run_cold_fixture.py --repo REPO --build-dir NEW_EXTERNAL_BUILD --machine-build-record NEW_EXTERNAL_BUILD/MACHINE-BUILD.actual.json --output-root NEW_COLD_ATTEMPT
```

这些新host命令未由历史机代执行；标准producer完成精确项目EXE登记和实际SYSTEM gate后才可运行。未来现场使用prepare_writer_admission.py的真实`--help`，显式enable、fresh两个原始readonly response和所有Root独立期望，并给`--machine-execution-gate`；`--prepare-only`只落入场包。该工具不发SDK query、不推进游戏、不从文件mtime制造新鲜度。Root必须先提供新鲜受控暂停窗口；native会再次复核对象，但不把历史caller指针回填成当前地址。
