# Native 与研究成果集成回执

最终候选：`d88f25140bcacb23f9a36ecfed92c89eb9c001f5`。
基线：`d4f377d97b7a4f97ac85151610adbc4d4df818f8`；独占 detached worktree：`C:/w/e2native1002`。
23 个线性提交、114 个改动路径，工作树干净，`git diff --check` 通过，无 merge、无 push。
根代理可把自己的 32 个提交从 `d9bac1d5fa89a6a68bb3755f1487f46863513e24` rebase 到本候选。

已整合研究链 `c4e871823` 的 12 个独有提交和 `ff1b17dc2` 的 6 个提交；研究链首三个补丁已在主线，rebase 自动跳过。
内容包含历史战斗 transition/phase trace、scope character variable monitor、UI navigation、H2743 stock predicate/private query、H3937 单次 route contact 与 queued wake/retry、采集与诊断保全工具。
旧版研究记录与输入保持其原有版本范围。

冲突处理中保留主线 1.20.0.2/1.20.0.3 接线、bookmark 枚举值 18、新版 callbacks、当前 frame writer。
新旧 mailbox callback 同时保留；历史 ingame UI 枚举使用 19，避免与新版 bookmark 冲突。
1.19 capability 基数合并为 105；de-jure 查询序列移出无关 truce opt-in 条件。
新增 registry 回归证明历史 UI 与 de-jure 查询不会在两个 1.20 adapter 上被广告为支持。

相对最新基线，524 个受保护路径零字节变化，包括既有 `ck3_12002*`/`ck3_12003*` native 文件、`native_session.py`、`runtime.py`、任务总线和 AGENTS。
CLI 只增加历史 H3937 专用命令，保留最新主线的 minimized-session 行为。
2 MiB frame 上限只调整运输容量；SCOPED 仍经 1.19 namespace、旧版绑定与 exact-build admission。
H2743 生产 opt-in 维持默认关闭。

验证使用明确的 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python 3.14.7。

- Python a01：145 tests + 201 subtests PASS。
- 最新主线 session/runtime Python a02：75 tests + 28 subtests PASS。此后 Python 文件零改动。
- Native a02：MSVC Release 20 个目标构建 PASS；18/19 CTest PASS，保留 mailbox source-contract RED。
- 最新主线 a03：MSVC Release 9 个目标构建 PASS；6/8 CTest PASS，保留 mailbox 与 feast fixture RED。
- a05：修复后的 mailbox 与 feast router 两个 CTest PASS；production DLL 和 injector 构建 PASS。

最终有 20 个独立 Native 定向用例的有效 PASS 覆盖。先前 RED 未改写或删除。
Mailbox source contract 现在同时校验 typed dispatch helper 的 callback/原 queued budget，以及 worker 的 stale-revision、snapshot、binding、submit、completion 顺序。
Feast fixture 现在单独编译 router，并仅对该测试 executable 启用三个被 mock 的 private route；链接纯 fixture support 和 protocol readers。
生产 DLL 的 private opt-in 未改变；其 bytes 与修复前 a03 DLL 完全一致。
a04 的首次 fixture 链接 RED 及其 artifacts 也已保全，补齐 protocol linkage 后 a05 通过。

旧版磁盘 fixture：`C:/Users/1/ck3-upgrade-integration-20261002-a01/installed-before/ck3.exe`，95,206,008 bytes，SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
新版磁盘 fixture：`C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101,039,736 bytes，SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。
两者按各自 CMake 变量传入，哈希复核通过。本子任务未启动 CK3，未采样新版实机，未制造视频人工 signoff。

完整 source/commit/path/artifact SHA 回执：`native-source-final-receipt.json`。
测试回执：`native-source-validation-python-a01/`、`native-source-validation-python-a02/`、`native-source-build-validation-a02/`、`native-source-build-validation-a03/`、`native-source-build-validation-a05/`。
旧构建完整 logs 与 DLL/EXE 快照在 a03 的 `pre-a04-build-artifacts/` 和 a04 的 `pre-a05-build-artifacts/`；最终实际 build directory 为 `C:/w/e2nb1002a03`。
