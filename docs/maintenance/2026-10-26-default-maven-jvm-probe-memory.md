# 默认 Maven 的前置 JVM 与受管内存

`machine_id: xenoamess-full-tower-eb9d2c1186`，2026-10-26 UTC。这是本机默认 Maven 3.10.0 / JDK 21.0.10 的实际诊断，不是安装路径规范。

新增 `MavenArgumentFileTest.actualDefaultMavenConsumesTypedFrozenPropertiesAndTheOriginalCliGoal` 用实际命令行默认 `mvn`、离线最小 POM 验证属性文件和 CLI 目标。第二轮八整类实际为69项、68通过/1失败；该方法内部 Job 在0.273181秒观测峰值2,222,010,368 B，超过384 MiB，退出124、active0、stdout/stderr空。失败发生在 Maven 配置解析之前，不能归为配置仍不兼容。

## 实际原因与修复

本机实际安装的 `C:/apache-maven/bin/mvn.cmd:194` 在启动 Maven 主 JVM 前先执行：

```bat
"%JAVACMD%" --enable-native-access=ALL-UNNAMED -version >nul 2>&1
```

这一步没有展开 `MAVEN_OPTS`。测试先清除 `JAVA_TOOL_OPTIONS`，只通过 `MAVEN_OPTS` 设置堆与其他预算，因此前置 JVM 未收到相同限制，输出又被重定向。生产 `ControlBuild.buildEnvironment` 已同时设置两者；测试修复为在本次子进程环境中复用同一有限 JVM 配置：

```text
-Xms16m -Xmx128m -XX:MaxMetaspaceSize=96m
-XX:ReservedCodeCacheSize=32m -XX:MaxDirectMemorySize=32m
-Djava.io.tmpdir=<本次获准的独立数据盘目录>
```

不修改全局环境，不提高384 MiB上限，不修改 WindowsJobProcess。默认 Maven 的绝对安装路径只作为本机观察来源，后续执行仍选择各机默认 `mvn`。

JDK21默认初始堆比例1.5625%，128 GiB对应约2 GiB；原峰值减2 GiB为74,526,720 B。这是官方实现支持的解释，不是原失败 JVM 的实测堆计数。WindowsJobProcess 使用新匿名 Job 和其实际 handle；没有证据表明它误计父进程。压缩类空间的地址预留也不能直接当作全量已提交内存。[JDK21启动参数](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)、[OpenJDK21.0.10初始化](https://raw.githubusercontent.com/openjdk/jdk21u/jdk-21.0.10-ga/src/hotspot/share/runtime/arguments.cpp)、[Windows Job 内存结构](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)。

## 实际复验

同一原方法、同一384 MiB限制、同一SRC/BUILD/m2/TMP复验：外层 Maven 10.0095244秒、退出0；实际默认 Maven 3.10.0 的离线 POM 输出 `BUILD SUCCESS`，v2 config仅属性、原 `verify` 目标从CLI进入。内层 cmd PID244484、出生FILETIME `134375016069787160`，退出0、1.8202643秒、峰值238,931,968 B、active0、无stopReason。FILETIME按规范十进制字符串保存。

- [Host实际回执](</D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration/MAVEN-DEFAULT-STARTUP-REGRESSION-ACTUAL03.json>)：4747 B，SHA `6e6ef627c6c47ca9370bbfc5c9bfa26e4b93ff00f522a5344e7c6cc082d918d6`。
- [独立复核](</D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/MAVEN-DEFAULT-RESUME63-INDEPENDENT-RESULT03.json>)：20066 B，SHA `d887d818307056506f88ea9470279000855d56a72d38ef146ed624ee697caf27`。

单方法XML实际1通过，不能把它与第二轮旧68项相加，宣称新69整类已经通过。后继需完成共享accounting修复的受影响测试及一次完整Tools VERIFY。直接开发Maven外层没有Job量测；只对内层真实受管Job报告上述内存与终态。
