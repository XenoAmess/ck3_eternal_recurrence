# R0007 后继共享修复

`machine_id: 4-8e1c2f1861`，实际验证结束 `2026-10-25T00:03:27.418328Z`。原始失败和实际退出分类保留在 [R0007 报告](R0007-2026-10-25.md)。本记录仅证明修复与离线回归完成；后继实机另记。

共享 driver 在 scripted-widget query/action 的原生 claim 或分派之前，最多进行八次只读稳定帧采集，间隔 50ms。只有本场实际遇到的两个 owner 计数差一、其余 owner/线程/日期/读取状态合格时允许等待；原严格 owner 校验继续执行。采样跨越玩家、日期、revision、进程、pipe 或连接身份时拒绝。不会重新提交动作。实际 seq5331→5332 的采样窗口、持续不稳定和身份漂移已进入持久回归。

公开 queue 在原宿主错误后调用与 host 相同的 `require_failed_host_normal_exit_plan_v1`，只允许原合同中的单步正常退出查询／请求／观察。业务动作、组合计划与清理完成后的队列仍拒绝，来源和 deadline 检查保留。

实际完成的原命令组共 **196 tests，0 skip，所有最终命令原 wait=0**：完整 GUI SDK Python step 22 项（含独立进程 UNKNOWN continuation）、失败宿主退出 step 59 项、既有 seam 三组 98／11／6 项；另有实际 CLI 注册 14 项及对应静态检查。完整 GUI 合同和两个 queue 模块检查通过；大 driver 的静态范围是完整修改方法，不外推整个存量大模块。未重编内容不变的 native，序列化 EXE 继续精确绑定旧资格。

首次测试静态类型错误、缺少原实际 fixture 环境导致六项 skip 的中间 RED 均保留；补齐后执行完整受影响命令组，不把跳过计为通过。SDK 已绿的同一源码没有重跑无关矩阵。

原证据 `C:/workspace/rrf-development-20261024/public-chain-a01/r7-owner-exit-a03/VALIDATION.actual.json`，7817 bytes，SHA-256 `b7924ef352b81824b17125961c6699fd0c3b9c3bcf6eb17937de17a17ab6672f`，逐项绑定实际命令和六份受测来源。生产 driver SHA-256 `9532b12926f311607b1db3831daece54ec91bf9976c1b6c66d6ff54ab9cbee53`；公开 queue `0a1b9ec4931b953160f148db00b587b747d986810d8391ac2e074c1c937204ea`。

同期 GUI 后继 `06-live-staging` 已实际 build／verify 均 0，67 文件，仅 GUI 与 05 不同。14 Java 来源与五份 fixture 未变，不重复 Maven 或生成 fixture。后继运行会重新冻结最终 clean HEAD、实际资格和准入，不热改 R0007。
