# Saved Driver 编码：一次有限组件测量

本次只测量已发表 P102 的纯 SAVE 投影和 combined Driver 比较，未启动 worker、查询 Game、执行 SavedLive 或处理原 UNKNOWN。没有修改生产源码、`Complete.encode()` 或编码协议。

## 方法与范围

同一 JVM 使用固定的原 1475 Driver（5255697 B、229 行 history）与 Pair，并构造不授权限的本地 228 行前缀。A 模式执行原逻辑的第二次 saved 编码；B 模式复用同调用内的已有字节。两者仍执行相同的投影检查和 combined 编码，编码完成 observer 均为 null。

两轮顺序分别为 ABAB、BABA；每轮先按该顺序预热，再按该顺序测量，最终每模式四个原始样本。没有强制 GC、删除慢样本或速度断言。两模式都保留第一次编码，供组件计时结束后计算 SHA；这是共同测量 harness 的缓冲寿命，不冒充旧生产二进制对照。组件计时包含清理，不含后置 hash 和输出；完整 main／进程窗口仍保留这些开销。

配置为 CPU1、`-Xmx128m`、初始 45 秒预算、最多 16 KiB 输出。实际 JVM 为 OpenJDK 21.0.10+7-LTS，报告可用处理器 1、max heap 129761280 B。只新增编译 benchmark TU：exit0／1 class／3.1163074 秒；生产 class 未重编。

## 全部测量样本

单位为毫秒。序号是各模式自身的原始顺序，不表示同一时刻的配对。

| 序号 | A：原第二次编码 | B：同调用复用 |
| --- | ---: | ---: |
| 1 | 199.2963 | 187.1938 |
| 2 | 244.8050 | 133.3509 |
| 3 | 192.9580 | 154.8705 |
| 4 | 182.6569 | 147.2337 |
| 算术均值 | 204.92905 | 155.662225 |
| 中位数 | 196.12715 | 151.0521 |

本次组件样本的均值差为 49.266825 ms，约为 A 均值的 24.0%。这只是单 JVM、固定输入、共同 harness 的描述性结果，不是完整 checkpoint 管线、旧生产版本、稳定态统计或实际保存日吞吐的提速结论。

全部预热也保留：第一轮 A262.3640／B155.0951／A208.0219／B145.8865 ms；第二轮 B144.3844／A187.7959／B139.4865／A208.3336 ms。16 次操作的实际编码 SHA 均与原 Driver 的 `092b7df3…` 一致。

## 完整窗口

输入读取与 hash 为 61.7423 ms；解码与本地前缀构造为 989.6306 ms；建立预期编码 marker 为 169.3593 ms。预热完整墙钟 1475.2425 ms，测量及 marker 完整墙钟 1471.7283 ms。main 从入口至最后输出前为 5.2752572 秒，独立 managed ACTUAL 的完整进程窗口为 5.8603287 秒，exit0，资源于 `2026-11-07T04:52:18.644190Z` 释放。

VM uptime 的 1390 ms 是 begin 记录读取时的值，不能拿来精确扣除启动耗时；上述子项也不作为全部 main 开销的穷尽划分。编译和整个测量窗口均保留，不从原任务端到端保存窗口中删除。本次新增确认保存日为零。

## 可审阅原件

完整 21 条原始记录见[原始 stdout](evidence/2026-11-07-checkpoint-encoding-component.raw.jsonl)，5212 B，SHA-256 `980628dcb2e4afca63c65d6a7765a8fb1762420e1693bde7e0dd67f43824d6d8`。[benchmark 源码](../../java/ck3-control/application/src/test/java/org/xar/ck3/control/application/checkpoint/SavedEncoding102ComponentBenchmark.java)是手动 main，不会作为普通 JUnit 测试自动启动。

[本地分析器](../../java/ck3-control/tools/benchmarks/analyze_saved_encoding102.py)接受明确指定的原 stdout、managed ACTUAL 与新输出文件三个路径，只读原件、不覆盖既有输出。它要求所有 21 条记录、原始顺序、全部样本和成功 ACTUAL；移植后使用同两份原件复算，与原分析的全部记录及统计逐项相同，没有重跑 JVM。

机器目录前缀为 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/checkpoint-saved-encoding-reuse102/`：

- `BENCHMARK-SOURCE-READY01.json`：4256 B，SHA-256 `64536dd3d7e7faabbaa981f314ed8675842dc96386cf91d01ccb785a6210941a`。
- `benchmark01/ALL-SAMPLES-ANALYSIS01.json`：9960 B，SHA-256 `8c001a56e0b6639c2380daf9a8b10b4120ab2451eba26954e0f4f32770b6dfb7`。分析保留所有原记录和 ACTUAL pin，没有新增 JVM、重新取样或过滤窗口。

源码独审为 `D:/ck3-state/resume91-root/checkpoint-saved-encoding-independent102/FINITE-COMPONENT-ABAB-BABA-SOURCE03.json`，9390 B，SHA-256 `006b2bc2b749adffa28c92b6d5b373577b7ae3c260aa809f7e8feabddf37ebf0`。
