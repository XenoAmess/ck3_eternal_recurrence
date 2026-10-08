# R0029 首次构建专项失败及最小回归修正

2026-10-08，机器 `bf-202609141645-5434332d4d`，mod `li-yu-dao`；完整 run ID `bf-202609141645-5434332d4d--li-yu-dao--R0029`，execution ID `8492501a-7834-4fe5-af41-c86f65b598cf`。本阶段仅分配编号和构建输入，**没有启动 CK3、attach、运行 SDK 实机或读取存档正文**。整个一期仍 **NOT_GREEN / 暂估75%**。

## 实际首次构建

输入提交 `8c0ddff7c477311e18f0a4517566df412e5f49c9` 已普通 fast-forward 推送。独立源码导出 `C:/lr29s1`、全新 MSVC 构建 `C:/lr29b1`，8项产物实际编译成功，12项 private flag ON、player control OFF、testing ON；未复用旧 objects/DLL。六项 focused 中名册、宗教Title、challenger graph、numeric scope、army-route构造器均 exit0，mailbox registration focused exit1。

失败原 stderr 全文为 `production actual4 Confucian registration missing`，51B，SHA-256 `1fb60f08a869aab6f605dbd6ba231d7a52fd8dc50c6136f5c60281cc4a326a13`。该测试要求 assembly executor 注册后立即出现 `#endif`，误拒了本轮同一 flag 内新增的 actor-cache executor。生产代码的两行缓存注册不能为消除旧测试错误而移除。

原实际结果 `BASE/r29-native-build-20261008-001/RESULT.json` 1063094B，SHA `f68e826202ac6325597f7e7b09b4e127823be2cd42a32b0717aeefe916148a40`：`actual_compilation_pass=true`、`actual_focused_tests_pass=false`、`original_outer_exit_code=1`。原 wrapper `BASE/r29-root-native-build-original-exec-20261008-001/RESULT.actual.json` 1413B，SHA `fa3ca6eba93768b3827878ac746ecf946a43c4bad1a08fe5e91368af8ce8c764`。没有跳过失败项进入 metadata 或实机。

Defender 普通构建登记仍实际 `settings_failed`；receipt SHA `abaad038cf4ba162fd0824bc91b717dce160bb554ff9b1d535bde9f97aa75ac4`。这是独立环境失败，不得与编译成功或本次测试误拒混为一项，也不得从旧精确路径排除外推本轮新路径已生效。没有为此安装 broker、重复管理员 COM 调用或改变系统设置流程。

## 修正与真实回归

只改 `native_bridge/src/main_thread_query_mailbox_v1_test.cpp`：生产 source 检查要求 1.20.0.4 同一 assembly flag 内同时存在 assembly 和 actor-cache 两项注册；保留 1.20.0.3、Title、Graph 检查。新增独立 cache fixture executor，验证未登记拒绝、暂停门、安装、实际 submit/drain/reclaim 和 uninstall清空；另验证仅 cache slot 开启时仍可安装、白名单拒绝其他 executor、实际执行一次并清空。

全新 `C:/mq29f1` 仅编译生产 mailbox.cpp 和修正后的 test.cpp，实际 compile exit0；原 focused CLI 对真实 production source 的正例 exit0，`PASS checks=63`。外置负例只删掉 1.20.0.4 cache 两行注册，实际 exit1并返回同一51B错误，覆盖 R28 的真实漏接。没有运行不相关旧 suite、修改历史 lr29s1/b1、替换 DLL 或授实机通过。

独立 focused 结果 `C:/mq29f1/RESULT.actual.json` 3191B，SHA `8313ec6c0544ea1bc41de907af7128e80290e85938518e73815af6e8abcf662d`。此回归只证明 mailbox 和生产注册约束，不是后继完整 DLL 或游戏资格。

[专项回归永久索引](focused-regression/INDEX.json)及其原件ZIP保留前后源码、补丁、真实编译/正负例argv与stdio；测试EXE仅记录原路径和SHA。归档工具首轮CRLF投影失败另保留在外置原路径，修正归档不重跑测试，不覆盖原构建失败。

## 原件与官方 CI

[源码构建归档](source-evidence/INDEX.json)永久保存30件原始构建/测试/stdout/stderr、原执行与环境回执；ZIP成员逐件核对。原存档和二进制仍保留在原路径，本次没有复制二进制或读取存档正文。[ROOT入库实际回执](ROOT-IMPORT.actual.json)记录9件归档与CI文件的逐字节复制。

精确 `8c0ddff7c` 的 [Official Runner](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37729515030/job/113155217275)与 [Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37729515003/job/113155217680)实际 SUCCESS。Li Yu workflow **NOT_TRIGGERED / NULL**，官方 push `ca3888b11393df33425789532b3b6604d658ff55 → 8c0ddff7c` 的20路径没有匹配专题过滤条件；不能写专题 CI GREEN。完整原API与结构化步骤见[精确CI报告](ci-evidence/REPORT.md)及其ZIP，保留一次连接拒绝失败；完整job log下载0次，producer stdout NULL。

## 后续

沿用尚未启动游戏的 R0029 allocation，在 iteration002 新路径从修正发布后的真实 clean HEAD 重新导出、构建和取得实际 metadata。001所有输入、失败输出和旧 HEAD CI保持历史原样。之后仍从原R10的0240真实存档冷载，SAVE后G2/G3再读缓存并与同帧保存投影逐项比较。R27六项 factory 保护失败、有效newT冷载、B5、C3和I4尚未通过；缓存读口源码或fixture通过不改变这些边界。

`BASE = C:/workspace/ck3_lyd_runtime_20261004`。当前Steam保持离线；后继实机需另取当次新鲜离线原图和本机排他占用。
