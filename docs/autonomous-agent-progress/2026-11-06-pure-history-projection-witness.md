# 纯历史投影重复输入见证：2026-11-06 14:21 UTC

性能与功能同时推进，本记录补充[瓶颈与功能缺口切点](2026-11-06-performance-and-functional-frontier.md)。它只验证冻结 DATA，没有引入缓存、修改 Java 或进行实机采样。

两个实际历史 manifest 的 Native/public 帧分别是 `941/838` 和 `942/839`，原 Native packet SHA 不同；两者却引用同一份完整 Driver：4754359 字节、version314、SHA-256 `d3fcc2d7823ce15ede72239f7ee744023a518ea81ba1328697236c7af909a815`。transport、episode epoch 和 observation version 也相同。因此完整帧结果的输入不同，纯 Driver 历史投影的输入则存在重复。

实际 `DriverObservationAssembler.java`（21653 字节、SHA-256 `142270559dcb907c72cdff8bfb7eb6996ffd48f9a63a2e2ab6cca65f04427980`）第147–148行，把 `commandHistory` 中每个 `originalRow` 再经 `DriverJson.object` 组装为 `native_command_history`。这是待评估的有限纯投影；完整 frame、source、owner、原件验真与当前准入均在此范围之外。

唯一 Runtime owner 已冻结上述单个 Driver 正文。独立读取确认 206 行历史，index 为1到206；两次独立解码的有序 token 树完全一致，保留对象成员及数组顺序、整数和小数词法，拒绝重复 JSON key。比较用 token 向量为7512643字节，SHA-256 `2f908b96681c95ef044b1a52d0ab3c2656702bac73961eea4c47db2a6263ed29`；这是离线见证格式，不是 Java 输出大小、分配量或性能指标。

尚未执行实际 Java codec、比较完整 snapshot 输出或测量业务提速。实现前还需核对当前合格 codec 与解析边界，用有意义的 Java DATA 用例验证等价值及异常行为，再证明有限作用域和保留上限。即使复用纯投影，每次 archive、哈希、frame、owner 与准入校验仍需完整执行；历史引用相等不授予当前权限。

证据位于 `D:/ck3-state/resume91-root/pure-history-projection-independent86/`：

| 证据 | 字节与 SHA-256 |
| --- | --- |
| `INPUT-WITNESS01.json`：两个 manifest 与实际 Assembler pin | 2087；`c1c044a51ff3fab989c31dead9fbd00710c2fdeaa2a960fdc324e4c4853b8b59` |
| `INPUT-WITNESS02.json`：单个冻结 Driver 正文验真 | 2731；`1a8958d9b0d1cdc9d494431d69a296b77c085228b9a592aeb6cd367696d3b7aa` |
| `HISTORY-TOKEN-EQUIVALENCE03.json`：206行有序 token 见证 | 1809；`bb8d774433e0db8b688507bea3bc0a7e303402fb1bfe93882a3beb64335b9e9b` |

功能切点也需更正：r55 已在14:01:28.8165941因原历史联合校验失败，未到 LOOP，HEAD1446/C55不变，无新 SAVE。P085 源审和编译通过不代表实际恢复通过；Life 三源及新增两回归用例已通过，仍待新的实机 full-plan。固定1266、1347、1412资料尚不足以确定首拒字段，有限失败诊断正在单独必要验证。原局30个未保存日保留，整体 G2 仍为6/8，10秒目标未达到。

## 14:43 UTC：独立 Java DATA 用例通过

新增的 `PureHistoryProjectionDataTest` 首次仅编译该测试1TU、输出1CF，通过；随后仅运行一个新方法，**1P、零失败/错误/跳过**，128 MiB、CPU1，实际运行4.8961638秒，14:41:45.584706释放全部资源。未重编生产或支持代码。

该用例用已有合格 D classpath 的 `DriverStateSnapshot.decodeComplete` 两次独立解码固定 Driver，按上述 Assembler 的纯投影表达式比较206行 `OpportunityJson` 值和编码字节，并检查有序原行、连续 index 及原 JSON 防改副本。它证明这份固定输入在这些明确的合格依赖下具有等价纯投影，未调用完整 `projectFull`，不证明当前宿主已加载相同依赖、缓存安全或业务提速。4.896秒是该测试耗时，不能当作省时量或游戏日速度。

记录位于 `D:/ck3-state/resume91-root/pure-history-projection-independent86/native-test-first01/`，JUnit XML 38916字节，SHA-256 `a74ca9db599ecaaf611475b8445f7bd42da76f3fd8880e8b94c0ad336bb9a625`。

恢复诊断的后到事实：r56 在14:30:18.4997973实际失败，首拒 capture147、第六项 ordered actionRows，前五项通过，后四项未执行。双方 Driver 版本26和SHA相同、均13行，但首行39与81不同；这证实 P085 无条件改流会破坏85→147的原样前缀。第三版已撤该转换，改为差异时严格使用捕获当时真实回执链比较，源审与必要首编已通过；真实历史行为回归及再次实际恢复仍待回执，不把软件通过算作 LOOP。
