# 严格解码作用域中的历史行投影复用

post62 的真实显示采样栈仍经过 Assembler 的历史行原字节解析。原 Loader 已在有限的实际 archive Session 中复用严格解码的 Complete，但同一 Complete 再次投影时仍逐行解析。原333真实 writer/store/archive 路径可在同一作用域两次 loadFull 返回相同 Driver，且每次继续重读原件；本单元针对这一可执行重复路径。采样显示 top40 共252/270样本、尾18未显示，不能把 read76 全归此处，样本也不是 CPU 时间。

沿原四项／64MiB私有解码作用域，只保留最近一个实际内部解码 Complete 的不可变历史模型 List。成员资格使用私有 entries 值的对象身份；外部 Complete、无作用域及公开 projectFull/assemble/Complete 构造保持原严格解析。Reader 私有 nominal 产物携带实际 decoder，完整投影、普通装配与公共 replay 均在原历史字段构建位置取得行；未提前解析或增加外部 owner callback。所有归档原件读取、hash、callback 次数与顺序保留，首次投影和 Incomplete 的原错误边界不变。

Driver 切换、驱逐、解码异常、已接入 replay 失败／Incomplete、嵌套失败和外层 finally 清除新单槽。它不能提供 Guard、Session、Source 或动作许可，没有跨作用域缓存、调用方提供的 AST、parser/RawJson/Snapshot 修改或期限延长。正式变体保留 OriginalBytes、NativePacketInput 的生产者及 finally 清理、NativeBodyStage 和旧公开接口；没有用 active 全文件覆盖正式差异。

actual 三 TU／11类和 formal 三 TU／14类分别首次编译0。actual 新 Store whole4、原333 owner/thread/poison精确一项＋原366 whole2、formal复用同一新 Test whole4分别4P／3P／4P，均0F／0E／0skip、输入不变且CLOSE释放。新测试检查完整语义、每次原件重开和 CAS 篡改拒绝、不可变行、异Driver／驱逐／严格解码失败／Incomplete清理、嵌套／外线程／退出新作用域、warm public Full及外部Complete不借memo、公有伪Full拒绝后合法load。原333其余五项和原366测试未改写，366产物复用，formal未重编新测试。

原件根 D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01，机器 xenoamess-full-tower-eb9d2c1186，2026-11-12。actual ACTUAL1419B／`5eb6e07522069ce6fa4573e7e94665f964980fe1abf2a0c2b57339939736ab83`、CLOSE204B／`ed318ad25684279ddd0107bd02369da355fdff5ad0c7d7fa75c596a7797ce24b`；formal ACTUAL1493B／`c48438b6ea5bd4b75783e511a8a97f9d7666c572cc9c80144fb683f60db9c414`、CLOSE204B／`307d0d6f4e621f688e77891939902916268f475114de8984a3b625c52b4790fa`，对应 owned-history62-{whole4-junit01,formal-whole4-junit01}。有限旧边界在 owned-history62-old333-366-junit01。

首 Test 的两处 checked IOException 不符合原 Function callback，修正版只作 unchecked 包装并检查原 cause，生产 callback 签名未扩。原编译RED保留；一个已被前置合格类遮蔽的旧 mutable C alias预检拒绝为0JVM，未当源错误或追绿。两次模型候选均拒收、零hunk采用；生产由owner接管手写，独立helper提供真实归档测试。

该资格只证明所调用的软件边界，不授线上 scope 命中比例、实际装载或墙钟收益；正式发表不是现场采用前置。新增确认保存日与10秒目标继续按独立实际连续窗口验收，不用样本、软件通过或累计旧保存日替代。
