# Native26：Native25 精确冻结闭包上的性能增量

机器为 `xenoamess-full-tower-eb9d2c1186`。2026-10-19 UTC 实际构建与离线检查通过，当前游戏仍使用 Native25；本包没有加载生产 DLL、注入、重启游戏或启动新项目 EXE。证据入口是 [资格摘要](evidence/native26-performance-build-qualification-2026-10-19.json)，实际构建根为 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-native26-performance01`。

候选 DLL 为 `build/native26.dll`，18,442,752 B，SHA-256 `eaee4443f083ae5055232b908fdb5c6555aa75084801fd24654224b090032184`。它只包含已审 JSON 五叶、actor 四族和 M6 termination 单常量 gate 增量。未用当前 master 的 Native 整树替换旧冻结输入，未加入后继 county 或更多 CB 家族研究。

## 实际输入与完整 consumer 闭包

基线是 Native25 原 `p38-prewar-v2-mailbox-native25-01/final01/native.dll`，SHA-256 `a1448baa860a88826cbb9ae50ab67c93506560f2772c0515e4ef51e934002f40`，并复用其原 final rsp、356 个 direct 对象和 612 成员的 Native18 runtime archive。原对象、冻结源码与头文件只读引用。

[consumer 计划](evidence/native25-successor-consumer-plan-2026-10-19.json) 按实际 recipe/sourceDependencies 重算，全部 968 个输入均有 Includes 来源。private declarations layout 的 118 个 consumer 全部重编，另加 3 个仅 JSON 源叶，共 121 个对象（21 direct、100 archive）。原 28,820 个冻结头文件路径只读核 SHA，没有整份复制。两版历史 declarations header 的所有 consumer 现在都唯一使用新 overlay；不能据此追认或否定旧实机业务结果。

JSON 来源固定为 `652e873a` → `d90d5e79`；actor 来源为 `d761b3ce^` → `d761b3ce`。M6 在实际 Native25 router SHA `ed55cf48…feff` 上只增加 `kSwayCompletionTerminationStepV1` 的 `.4` 白名单判断，产物源码 SHA `bac63779…ceb9`。M6 原 provider/mailbox/serializer 不变。

实际 MSVC 为 14.51.36231，`cl.exe` SHA `315a654ea116864516a1674858e587e535e3bc3045ff32ed2f2739a2c1ec5640`。121 个对象全部 PASS，各自实际 Includes 验证新 layout header 唯一生效，无旧 header 混入；其余原项目 Includes 不引入未审路径。

新 archive 从原 rsp 的完整输入重建，替换 100 成员，其余 512 payload 保持原 SHA。全部 612 个实际 COFF payload 按名称、字节数和 SHA 多重集逐一相等；旧替换路径没有残留。librarian 的内部成员顺序与 rsp 不同，原 rsp 输入顺序保持。final link 只换 21 direct 对象、1 archive 与输出路径，其余参数顺序不变。候选与基线 PE 的导出名称、ordinal 一致。

## 离线验证与边界

普通子 Python 只加载独立 fixture DLL，生产 DLL从未加载：

- JSON 原 9-case harness 使用保留的旧/新真实函数 body，并以这次生产编译的实际 DTO header closure 重编；escaping、null、数字、空值和大型嵌套输出逐字节等价。
- CB 原 ordered/callback fixture 连接本次真实 declarations 对象及新 archive，通过完整候选、原顺序、yes/no/unknown、shadow 和 frame-drift 等原断言。
- M6 以真实 `.4` stock descriptor 常量、原生产 router body 和原 R5 spy 验证 termination gate、完整参数及 owned recorder；缺 recorder、未注册后缀继续拒绝，execution/invalidation gate 未放宽。它只证明 dispatcher 接缝；不证明原生 provider 的自然终态、目标游戏业务结果或收益。

`offline04/RESULT.json` 为最终 PASS，SHA `9724237f902feb9bbd2b08e8de77af8c48e08b267eb5412e183ba848b838344c`。真实失败均保留：prepare 初次误要求 librarian 内部顺序；offline01 过宽 archive 拉入无关 fixture 依赖；offline02 缺 terminal executor spy；offline03 手写小写 SHA 未通过 stock 的严格 descriptor 判断。最终改用原 stock 常量，无修改生产源码、放宽 descriptor 或伪造资格。

actor gate 仍默认 OFF。[零 mod 来源准入](evidence/native26-actor-zero-mod-source-admission-2026-10-19.json) 使用当前机器带身份补注的实际 ROOT-CLEAN-CAMPAIGN-MOD-ABSENCE-ACTUAL 与 launch 小证据，未追认 missing-machine06。11 个依赖定义在原版根内唯一，当前检查的 DLC 无相应覆盖。未来冷进程采用前仍需新鲜 loaded-source/运行 tuple 核对及 shadow；不把旧进程的零 mod 状态自动移到新进程。

## 负载、容量与后续采用

双 BELOW_NORMAL worker 的实际生产编译窗为 04:08:32.870423–04:14:07.855237 UTC。GetSystemTimes 记录 32 logical processor 的全系统 busy 为 3.5296%，只作当前游戏样本的重叠负载注记。归档及链接各约 1.84、1.86 秒。未做当前游戏 AB；没有声称本包已达到 1 秒/实际游戏日。

历史 profile 的来源机器仍为 unknown：四族占 152,844/2,529,581 次评估，历史 evaluator 成本 697,751,500 ns。它不是当前硬件的预计节省，不能把当前几秒的 RPC wall 全归因到这些调用。后继更多家族另行源审，本包没有为其改规则或重编。

存储 child 在同一 64 GiB 总额内获准最大 768 MiB；全部失败、临时、对象、archive、map、DLL 和日志实际闭场为 611 叶、322,051,593 logical B，allocated unknown/null，future writes=0，所属 build/fixture 子进程=0。`FILES-CLOSED.json` SHA `721434aa98f43ffe541cb170ae53266d12eeb446c69f9719a83434d67b8f145f`；不因此释放父预算或推算物理空间。原父复核期限 2026-10-20T01:48:56.993837Z 保持。

可复现生产器为 `tools/g2_saved_campaign/{plan_native25_successor_20261019,audit_native26_actor_loaded_sources_20261019,build_native26_performance_20261019,validate_native26_offline_20261019,close_native26_performance_20261019}.py`。构建严格执行 prepare → compile → archive → link → offline → close，使用新准入的 create-only 外置根；当前已闭 child 不覆写。实际 producer、源与编译命令均有 SHA/回执。后续采用需单独排定，当前局不等待本包，也不热替换 Native25。
