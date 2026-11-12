# 同一次归档加载复用完整 Driver 投影

原 Loader.load 先通过 Reader 产生完整投影，再调用普通 assembler，导致同一组已解析原件重复完整投影。本单元让 Loader 保持原 archive 回调、私有 packet 副本、hash／manifest／Driver 解码与异常顺序，只把同调用内的严格解析结果交给 Reader 私构造的 nominal 值；Assembler 复用这个精确完整投影，继续原 actor、alive、calendar 与全部元数据检查。

构造优化只在最后一次 `new Complete` 的局部范围安装私有 token。token 绑定实际对象身份，一次消费，finally 恢复／移除；公开 Complete 构造器仍保留原完整重投影与断言，调用者不能拿任意公开 FullSnapshot 绕过验证。没有跨调用、跨轮或全局缓存。

正式三叶保留已有 NativePacketInput、parsedNode 等优化，没有以实际运行分支整叶覆盖。正式必要差额为三叶，另两个未改原依赖 DriverJson／OpportunityJson 因当前复用 class 缺其真实既有 API 而首次必要编译，总五 TU／26完整类；首缺依赖 RED 和 partial 输出保留。正式产物再复用未改测试两类运行完整三项，实际3P／0F／0E／0skip。测试真实调用 Loader.load/loadFull，覆盖 profile1／4 完整元数据、公开伪造 Full 被拒、原 archive 三回调顺序、异常同对象与 caller packet 私有副本；没有用投影计数模拟收益。原四套17项未运行，不计作已绿。

资格索引 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/ACTUAL52-WHOLE4-AND-FORMAL37-WHOLE3-SOFTWARE01.json`（7384B／`a37b5f57540dc2bf1d501585aba543c64fb2610f4cfa88876352d30a9915291c`）；正式 whole3 ACTUAL1395B／`01d9154c7666136026349e69a910fd75c6624d596df770e79eac2ff806c4942f`，exit0、accepted、输入不变、CLOSE释放。测试 Helper 在正式 HEAD 的原字节与资格所用9621B／`cd13ffe32fd25820d13cf3ac5616e020ad9853a3f255156c73105731eec01bfd`完全相同。机器 `xenoamess-full-tower-eb9d2c1186`，2026-11-12离线资格。

实际运行变体37已在同局恢复中采用并消费历史；它与本次保留正式优化的变体分开记账。本单元没有证明总墙钟或新增保存日速度改善。公共 Reader replay 的重复投影与 Snapshot surrogate 遍历是另两个后继单元，不计入本次三项覆盖，也不要求运行岗为发表重启当前 worker。
