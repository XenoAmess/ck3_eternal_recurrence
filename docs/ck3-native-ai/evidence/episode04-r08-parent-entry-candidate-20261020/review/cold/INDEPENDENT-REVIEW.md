# Parent-entry a04 / fixture-a02 独立源码审阅

machine_id: desktop-3fevhd2-1c74096080。17:15硬界内离线只读；没有Git、编译、broker、游戏或SDK动作。最终作者索引FIXTURE-SOURCE-INDEX.prepared-a02.json的12份源文件全部按bytes/SHA实际读回，core a03与fixture-a01原件保留。

结论是 SOURCE_ONLY_REVIEW_WITH_EXPLICIT_QUALIFICATION_GAPS。已发现的3处源码问题在新版本中得到最小修正；没有剩余必须阻止“按source-only角色保全”的发现。不能由此授予native cold/ABI/Windows unwind/安装/实机通过。

1. a03把local_player_id与full_id比较的真实错误已在core-a04修为独立非零。逐字节核仅此一处核心变化；fixture实际保持1/33388，未篡成相同ID。非零本身不证明owner join：真实同窗player/Character/进程/来源连接仍须公共admission producer，不能由该bool或私有seed代替。

2. 这是能调用真实代码的fixture源码，不只是Python镜像。ASM哨兵走实际Thunk→实际16B原prefix→surrogate Body→原return；检查volatile/nonvolatile入参、原RSP/return slot、两个栈参数、16个XMM、x87/MXCSR和返回RAX/XMM0/调用次数。生产a04 C++被直接include进fixture TU，真实ArmOnce与StopAndSnapshot路径会被运行；CMake指candidate-a04，且冷EXE显式依赖component库而不重复link core。

3. entry f.rflags断言位于原prefix之前，故与最初user flags比较合理。原prefix的SUB98会按原逻辑改变算术flags，不能把Body后的flags要求全等初始值；当前Body没有采RFLAGS，本文不额外授予该项证明。PUSHFQ对RF/VM的架构限制、AVX上半状态等仍沿作者未资格边界。

4. Unwind源码使用实际RtlLookupFunctionEntry与Windows RtlVirtualUnwind；生成器拟从将来自己的新EXE读取完整两函数span，Capstone逐条解码，边界来自emitted bytes，而不是直接从Python源模型枚举。预期栈上下文仍按独立线性指令状态构造；它是针对真实OS unwinder的合成CONTEXT测试，不是实际CPU停在每个PC的现场trace。本轮没有编译或执行它。

5. 初版Unwind仅检查RBP/RBX/R14而漏RSI/RDI/R12/R13/R15；a02已将全部seed非易失寄存器加入真实结果断言。初版33条重复入口case也可满足count>32；a02加两函数COUNTS、真实function range、起点/升序/分组、duplicate和期望总数检查。仍须在将来实际run中绑定生成器源/EXE身份与两span SHA、完整case文件SHA及--unwind实际输入；同文件里自报COUNTS不能独立证明未改动的每条实际边界，不能只凭passed_checks计数授全覆盖。

6. Admission测试现在用独立fixture_prefix_reads证明1/33388实际到达故意NOPprefix拒绝，而不是只以总reads>0冒充Identity完整成功。localPlayer0仍应在任何read前拒绝。它刻意不写真实prefix、不pin，不是Install成功或Restore通过。

7. StateRoutes通过明确私有owner seed覆盖真实ArmOnce/OFF/busy/readfail/overflow/invalid-state分支；seed不是普通游戏admission资格。并发测试确实用8个线程4096次ASM调用及真实原body atomic计数，允许OFF前实际零target；它不保证每一种调度交错，注入active=1也不冒充实际卡住producer。完整写保护/patch/flush/rollback失败与全线程quiescence屏障仍未实现。

可进行下一步的是新有限构建/两精确EXE设置/真实Windows冷资格的独立计划，不能复用旧A08/A41或把20个Python/source/model检查当native结果。之后仍需启动期安全安装与MapReady同owner late-arm公共接线；现在运行链没有进入这个hook。null支付记录不能推断零军费，R08/payer/cadence/c-d writer信用不变。
