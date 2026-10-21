# Source31 与 A18 冷准备交接（2026-10-21）

machine_id: xenoamess-full-tower-eb9d2c1186
observed_at_utc: 2026-10-21T02:01:46.902965+00:00
范围：本机 Source31 软件来源资格、A18 冷准备和公共 CI 修复。源码、离线资格与实机成绩分别核算。

Source31 canonical 为 `12e81b52c736baec02a85f32098bae5bdaa66a31`。两份物理 SDK 导出各含 1466 文件、59317740 字节；BASE 为 406541 字节，SHA-256 `0bdcfc8eb9262daf4bd5f677bdca9445b40a7e7d668f13976f02b36633a54c4a`。实际资格包含每份 84 项、共 168 次执行（61 项新上下文加 35 项父级回归，交集 12）；每份分别核实 537 个 SDK 模块来源，0 失败、0 跳过、0 SDK RAM 替换、0 RPC、0 Game 调用。测试加载器仅在 RAM 编译固定 Git 测试字节，不替换 SDK 源码。

机器原始资格为 `source31-sdk-prep01/SOURCE31-ACTUAL-DUAL-ORIGIN-QUALIFICATION01.json`，4207 字节、SHA-256 `ae5976ef5ae24a0f2705eb8a7be7259cc314af3df563c1c53abf083e319c5ca3`，观察时间 2026-10-21T01:34:26.479182+00:00。本提交的[资格副本](../ck3-native-ai/evidence/source31-dual-origin-qualification-2026-10-21-xenoamess-full-tower-eb9d2c1186.json)保留其原始字节。它限定为离线软件资格，没有授予 Native32 实际加载或 A18 运行态准入。

A18 采用新的 main、owner 和永久测试：`prepare_source31_a18_cold_union_v1.py` 62131 字节（`d4ee3ab7749fcef403616aa800077e1e75fe5524b49d85d8493571d9fe3c77ad`）、`prepare_source31_a18_owner_metadata_v1.py` 32080 字节（`9adb2ebc1e23f732115b9af9013f53dc6fc07af67d298b297684c12b6543340d`）、`test_source31_a18_cold_union_v1.py` 25063 字节（`2200c7ee90a6d66943f45f588157409f7b85106883629af68006aef4ff3d3713`）。owner 只接受 Source31/v2 Native32 来源合同，拒绝旧 v1。纯 API 中发现并修复的真实缺口包括同值浮点 bytes、重复 parent rows 与六份补丁记录为 null；永久反例保留，不靠上层固定输入掩盖。

新测试实际 17 项、280 个子用例、0 跳过，audit hook 证实测试自身没有 D 盘资产 open 或进程启动；更新 main 后于 01:58:54Z 再通过同一新增入口。完整 40 文件类型命令曾发现独立 skip 检查漏掉的 A17 共享类型交互：局部变量分别接收 Path 与字符串；仅改循环变量名后，01:58:52Z 实际 strict/strict-equality 为 0 错误。最终主源码配合新的 FULL02/Steam02，完整 145 文件冷图已重新执行并封存：`P18/A18-COLD-PLAN01.json` 4449 字节／`a2c049b9783a9aa6128235d6c9070a91df78ce70ad424437ea0f087719db3cfb`，`A18-COLD-QUOTE01.json` 178877 字节／`c48a34adb91b9b9f8d357959c982f6628ff302f4a0919fa9333615129a8420ad`，`A18-COLD-RAM-QUALIFICATION01.json` 15113 字节／`9b01fe088724c8825ab02e83151d8170610f3b19340ec1a130770f4d2a056e6a`。已核 source113、47/8/23/26 及 display19+3，准备峰值 2142208 字节。上述回执资格仅为冷准备，不授予 U18、Game 或实机成绩。公共 epoch 清单已同步 41 项来源，其修改范围静态通过，不声称旧 ledger 整叶 strict 为绿。

本线程上一公开交付为 `e2578b59273b886a7ab58eff24ba76a161d84e6c`。其 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39527335355/job/118984968403) 在步骤 20 因旧 cleanup fakeGate 缺少现代 Save 合同的 client 身份而失败；步骤 19 成功，22/39/55/94 跳过。[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39527335415/job/118984967457) 成功。远端 CI 的 machine_id 为 unknown，不能当作本机游戏结果。

修复仅更新 `tools/test_r08_cleanup_and_sampling.py` 的正例夹具，保留 36 条原断言及真实 begin_save/verify_save 守卫，保留 unknown 不得 replay 的语义。该叶实际全文件 strict/strict-equality 通过；工作流步骤 20 的五条原始命令均已实际通过，共 17 项、无跳过。前 3 组通过后，执行监控曾因过小的 16 KiB 单叶估值中止第 4 组；这不是测试断言失败。按实物修正 component 估值后，仅续跑第 4/5 组，最大报告 18790 字节，原 1 MiB 总帽内完成，临时根清理至不存在。初次中止与曾遇句柄占用的清理失败作为历史事实保留；最终没有重跑已通过的前三组。依赖实际为 mcp 2.0.0、pytest 9.1.1，与工作流一致。上述本地绿尚不能改写旧远端失败。

工作流只修改原第 39 步：在原类型命令追加 Source31 两工具、A18 三文件和 cleanup 测试，34 文件扩大到 40；unittest 列表只新增 A18 模块。仍为 143 步，环境保持，原 55/94 索引与命令不变。实际 workflow 为 75949 字节、SHA-256 `7029a2169c37b4868324c101f2ec84ea50acec9acf78118f882c4bc711a2f4de`；增量 400 字节，原位写入、FileID 保持、分配未增长。PyYAML 结构、roundtrip 和逆向恢复原字节通过。原 17 项 R08 和旧 43 项软件测试不重复。记录冻结时，本包尚无新精确提交的远端 CI 结果。

本轮没有新增游戏天数或 G2 完成信用。原局仍为 5429/10950 日、G2 6/8；路线图为 M0–M7，M6 终局与 M7 的实际 H 加广度尚未完成。智能体的字段合同、错误处理与软件回归覆盖已改善，其实际业务收益仍须由后续原局读回确认。1 秒/日目标未达，30 年未完成；原始墙钟连续保留，不以新 attempt 重置。
