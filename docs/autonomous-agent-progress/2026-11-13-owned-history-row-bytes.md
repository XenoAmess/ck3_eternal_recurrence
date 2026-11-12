# 已验证 Driver 的逐历史行纯 JSON 复用（2026-11-13）

实际 BOOT 栈反复进入 `DriverFrameEvidenceLoader.projectOwnedHistoryRows` → `DriverJson.object` 重建历史行。两个具名不可变 Driver 原件的历史从169行增加到170行，其中169个原 UTF8 行片段共4337616B逐字节相同。这是输入重复证据，不是运行缓存命中率或提速证据。

本单元只在现有同线程、实际 owner／Session 解码作用域中，对私有 decoder 已登记的 Driver 身份启用行复用。先按 `Arrays.hashCode` 查找，再逐字节确认完整行；碰撞的不同内容仍在原位置解析，预算允许时替换该 hash 槽。公有或作用域外 Complete 保留原解析。原件重开、hash、严格 Driver 解码资格、owner 回调、完整 projection 和错误位置不变。

私有缓存最多1024项、16MiB保留的 key bytes；达到上限后仍查命中，停止新增 hash 项。计费包括私有 key clone，并对碰撞替换扣旧加新；该16MiB不是整个 DOM／JVM 堆上限。成功切换历史 Driver 保留纯行缓存；原 owner／Session 拒绝、嵌套失败、decode／replay／投影失败、discard及外层 finally 清理。没有新 public API、类型、全帧或权限缓存。

## 有限验证

Actual与formal分别单TU编译为原有两类，并复用同一测试的四项独立运行，均4P0FES。测试使用实际 ImmutableArtifactStore、ContinuityWriter、NativeOutcomeArchive及同 Session scope，核两种 profile 下不同 Driver 的相同行对象复用、public assembler完整输出与原件三回调顺序；`Aa`／`BB`实际数组 hash 碰撞必须保持不同内容；外部 Complete、owner／Session／线程／跨scope与失败清理均走真实 API。碰撞不要求永久保留旧对象。未重复旧333／366套件。

机器资格：`F/SOURCE68-ACTUAL-FORMAL-WHOLE4-AND-152JVM-COST01.json`（22277B／`8b6b65040ebed73a071b2798914a51f27225dd30c83250e884a7cbc39930abaf`），F为 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01`。actual whole4于16:29:46.768202Z释放，formal于16:33:11.978659Z释放；同Test四类复用。正式版保留原 OriginalBytes record／capture／load／full尾部，不抄 active 的 CapturedOriginals 类。

两次完整模型响应均保留；九块生产修改部分采用。Owner修正残留泛型及冗余cast，将线性扫描改为 hash索引＋fullbytes确认与替换计费，并补漏掉的 owner拒绝／replay／null参数失败清理。静态缺陷不记为实际 javac RED，本单元首次实际编测均通过。

后到实际Runtime68仅采用Loader单叶：同host161132正常fullreload，4f9236f3／restart1于16:36:35.6251486Z START、16:39:08.2610349Z LOOP，旧C60与真实ticket1459正常恢复；STOP→LOOP361.0176549秒，0新增日／SAVE。原件 `R/attempt68/ACTUAL-LOOP68-AND-FULL-HANDOFF-COST01.json`（5283B／`81c0d1b8142cc498dbca00d5cadbd518d9c588b70bb4eda9e7bac986b8d5492d`），R为 `D:/ck3-state/resume91-runtime/quarkus-dev307-runtime`。

这是单叶装载与正常恢复回执，尚未取得实际rowmemo hit或速度证据；未新录JFR、ThreadPrint或counter。原66／67恢复修复保留，Source65小型manifest未混入；正常fullreload不外推HCR，10秒／新增确认保存日仍待真实连续窗口。
