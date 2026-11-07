# 同调用内复用已验证的 Saved Driver 编码

本单元只优化原 checkpoint 验证中的纯编码重复，不改变 `Complete.encode()`、JSON 协议或物理资格。没有部署、Game 查询、worker 启动或当前 head47 准入；P100 被拒绝的诊断链保持停止。

## 确认的重复与改动

原 `buildVerifiedBinding` 先在 `requireSaveProjection` 中编码 saved Driver，随后在 combined SAVE 对比中再次编码同一 saved 对象。当前 `Complete.encode()` 会逐条解析原 history JSON 再建立输出树，因此第二次编码会重复这部分工作。

现在只在私有 nonretained 分支、saved 来自原固定严格物理解码器时，暂存第一次投影检查生成的编码字节。before 与 saved 的 actor 都必须是标准 `BigInteger`，编码不超过 8 MiB，第二次使用必须是同一个 saved 对象。缓冲仅存在于本次方法调用，消费前清除 holder 中的字节引用，失败或返回时也清除；没有字段、全局或 TLS 缓存。

retained／外部供应路径、非标准数值类型、超限、不同对象或再次消费，均使用原固定编码路径。combined 对象仍在原时点真实编码并逐字节比较。原文件检查、hash、ACK、SAVE verifier、lease、current head 的调用顺序保持。

不能整体缓存 `readMaterial` 的结果：它还调用历史周期验证与完整 Driver／物理资格验证，包含实际 writer 状态和回调，超出了纯元数据解析域。本单元没有跳过这些验证。

## 实际软件证据

单 Verifier TU 编译 exit0／7 个原有 class，耗时 3.7038534 秒；新测试 TU exit0／2 个 class，耗时 3.2148807 秒。唯一 DATA 方法实际 1P／0E／0F／0skip，耗时 4.7479777 秒，全部资源于 `2026-11-07T03:48:30.673865Z` 释放。

测试使用原 1475 的 5255697 B Driver、229 行 history 及相应 Pair；本地 228 行前缀只作投影 DATA。固定编码完成回调证明目标 saved 操作数从两次编码降为一次，并验证原字节一致、单次消费、不同对象、比较失败、非标准数值、容量与异常身份／清理路径。计数只指目标 saved 操作数，不是全部编码、解析次数或 CPU。

超限测试的字节数组只验证缓存容量门，不冒充大型 Driver；私有严格来源与 retained 分支门由源码审阅确认，不把 DATA 测试当作实际 Root／物理资格。测试没有可替换 encoder 或私有 proof issuer。

正式前像和后像分别与刚验证的实际源逐字归一后整件一致，唯一差异为换行且没有 text block；六处变更正逆成立。独立复核据此复用同一软件资格，没有为格式重复编译或重跑绿色测试。

## 边界与导航

本次新增包内帮助方法，不能据此宣称仅修改既有方法体的热替能力已验证。后续实际采用仍由唯一运行 owner 在必要边界安排。软件验证不证明 wall-clock、保存日吞吐或 10 秒目标改善。

机器前缀：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/checkpoint-saved-encoding-reuse102/`。

- `SOURCE-CANDIDATE02.json`：3126 B，SHA-256 `178ce183051086dc99e0bc1ecd62895d102c679fbefb11ccc99af87eb85ea06b`。
- `TEST-SOURCE-READY01.json`：3201 B，SHA-256 `2923ae16ff31badd0a740e9266443bbdc32dd26401d539b83b0d86ac7519d9b1`。
- `QUALIFIED02-ONE-VERIFIER-AND-REAL-SAVED-ENCODING-DATA01.json`：49146 B，SHA-256 `aca80d4be331d7e602e4383d79272cbc5f2daebbc5af612620319400244ea0ef`。
- JUnit XML：39366 B，SHA-256 `bc1f626f7c15ba3ec7ac76154468f1c45e4e7ad7747af65424b034083958ed76`。

独立核验：`D:/ck3-state/resume91-root/checkpoint-saved-encoding-independent102/ACTUAL-ONE-CASE-AND-FORMAL-ONLY-EOL-REUSE02.json`，12723 B，SHA-256 `be29cbc7de46732b95b271d5a526e25d7d727e7fadf9aab352c4f85b9e49da48`。
