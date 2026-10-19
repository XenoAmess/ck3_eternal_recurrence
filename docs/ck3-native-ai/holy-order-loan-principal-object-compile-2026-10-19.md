# 玩家 root 本金 getter：首次 object 编译通过

`machine_id: xenoamess-full-tower-eb9d2c1186`，本轮由 `tools/ck3_live_run_id.py machine` 实际读回。编译发生于 **2026-10-19T05:19:37.879295Z 至 05:19:43.101787Z**，实际耗时5.222秒。[完整小证据](evidence/holy-order-loan-principal-object-compile-2026-10-19.json)保存实际 argv、source 前后 SHA、642个传递 header 的 SHA、MSVC组件与输出 pin。

独立 `research/holy_order_loan_principal_12004.cpp` 首次真实 `/c /std:c++20 /permissive- /Zc:__cplusplus /EHsc /W4 /WX /utf-8 /DNOMINMAX /MD /O2` 编译退出0，得到33,310B 的 x64 COFF object，SHA `9b5d5d83ce3a03dc8ad4845b8977af040df8124671e998372861e8d883c3f976`。没有源码修正和第二次编译。旧四叶40,306B的源码、source-only合同与专题均保持原SHA；此处新增记录，不覆盖此前的源码资格边界。

producer 复用 `tools/run_native_msvc.py` 的子环境与 `initialize_msvc`，只调用已安装 VS18 的 `MSVC/14.51.36231/bin/HostX64/x64/cl.exe`；实际 `/Bv` 组件版本为19.51.36257.0。单个编译 worker 使用 BELOW_NORMAL，清除继承的 `CL/_CL_/LINK`，全部 TEMP 位于获准的 D 盘 child。没有 CMake configure、完整 Native 重建、链接或加载 DLL，也没有接触 Game、RPC、桌面、Driver、SAVE、Native26或当前SDK。

这一步证明候选的真实头文件、C++类型和函数指针调用可以编译。它没有编译所调用原生函数的游戏实现，没有执行 constructor、求值或 cleanup，不能证明实际 RVA/ABI、临时 owner 的运行行为、加载中的本金值、资格或资金到账。quote 的资金信用仍为0。

## 最小后继 fixture 闭包

只读解析这个实际 object 的 COFF symbol table，恰有五个项目函数仍需链接定义：

- `.4::BindCoreImage`。
- `.4::ResolveCoreCharacter` 与 `.4::ReadCoreSnapshot`。
- `.4::BindPrisonerNamedImage12004`。
- `.4::religion::BindReligionContextAddonsImage12004`。

因此最小独立 fixture 可以只新增一个 fake TU，提供这五个精确签名的 stub、固定的 fake named definition、constructor/evaluator/allocator计数器以及一个小导出入口；只读链接本次原object。真实 reader body仍来自已编译候选，不需要179MB Native runtime archive、CK3 EXE、Service、Driver 或生产DLL。实际 `.drectve` 的默认库为 `msvcprt`、`MSVCRT`、`OLDNAMES` 和 `uuid.lib`，连同编译器生成的 SEH/security helpers，均需通过同一 producer 的既有 CRT/Windows SDK 输入解析，不能省略或用其他R5业务spy追认。

应限定在几条有区别的路径：正数与原生0只求值一次；第一/第二scratch构造返回失败时只释放已取得owner；求值返回错误out指针时不给quote但依次清理；清理未知时不给quote且仍尝试后续owner；玩家或来源前后变化时拒绝输出。计数器须证明每个owner只释放一次，并区分“attempted”和“verified released”。这些未来fake检查即使通过，也只验证候选控制流和ABI接缝，不验证游戏原生allocator、RVA或实际本金。

Root未提供已核的 principal player-root R5 DLL/export pin；Native26 offline04的M6 termination spy属于另一业务。本轮没有搜索或加载它来替代此项。新fake源码、link argv、DLL/CRT输入和峰值尚未实际资格，不能从33KB object推算整个fixture峰值。是否开展单DLL检查由后继精确计划与存储准入决定，本轮止于object。

外置根为 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/m4-principal-object01`，原共享research中预计1MiB、硬8MiB，含此次新增仓库总结不超过256KiB。闭场小manifest记录实际logical、allocated unknown/null、producer/process closed及future writes=0；不据此返还父预算或推算物理空间。外置派生复核为2026-10-21T05:18:44.932786Z，父期限不续；跟踪记录按通用策略180天复核归纳。
