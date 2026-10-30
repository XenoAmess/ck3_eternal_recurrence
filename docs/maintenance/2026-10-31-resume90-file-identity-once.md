# 文件身份读取改为单次元数据观测

machine_id: `xenoamess-full-tower-eb9d2c1186`

执行时间为 `2026-10-30T16:46:06Z–16:46:09Z`（本地日期10月31日）。
当前worker98的真实线程位于历史动作原件读取中的文件元数据I/O；本项仅处理
`IdentityBearingFileAttributes.read` 内部嵌套的重复采样，不把线程取样当作完整耗时归因。

原普通read每次执行两次NIO attributes与两次WindowsStamp，再比较其间是否改变。
但实际内容读取者 `LedgerFiles.read` 在读取内容前后已经各读取一次identity；
`PortableEvidenceReader` 同样在内容读取前后取得identity。
这使一次外层内容读取包含四个WindowsStamp、四次NIO attributes。

本项普通read只取得一次NIO attributes与一次WindowsStamp，返回实际NIO属性和
精确Windows身份。该基础API现在表示一次元数据观测；它不证明任意操作期间文件未变。
外层内容读取的前后观测、字节长度、内容SHA与实际引用解析由各内容读取者处理。
没有新增缓存、启动检查、失效平台或审批链。

WindowsFileIdentity中的卷号、128位FileID及创建FILETIME仍为规范十进制字符串；
Win32长路径转换、原生reparse拒绝和实际句柄关闭仍使用原实现。
专用 `readWithOrdinaryParents` 与其双阶段父路径API没有改动。
单次普通read的WindowsStamp与NIO调用数各从2变1，是源码操作次数；
未测量整批提速，也未宣称单次NIO与原生采样是一个原子文件系统快照。

候选基于已发表 `15e9a06332c860fab9817a05359fab9c1b0281fa`，
该叶原SHA为 `630d7af59d02c8eb05a14901081670c7921ae9af46cc41ed316d77df93afd347`，
与运行源S的同叶一致。仅在D盘复制该叶及两个现有测试类，没有复制工作树或改S/MB。

实际验证：

- `javac --release 21 -Xlint:all -Werror`：exit0，1.440秒。
- 两个完整现有类 `IdentityBearingFileAttributesTest`、`IdentityBearingFileAttributesLongPathTest`：13/13通过，0跳过，进程1.454秒。
- 用例实际创建文件、目录、同内容同mtime替换、junction及406字符长路径，继续验证完整十进制身份和原专用父路径行为。

没有新增仅复述实现的测试，没有为这项操作次数削减重复执行旧baseline绿色组。
当前回归不包含完整reactor、完整CI、Game动作或真实新增游戏日；
实际运行采用仍由runtime90执行，正常开发源交付由java_delivery90执行。

D小包：`D:/ck3-state/resume90-root/identity-once/DELIVERY.json`；
原命令、退出码及日志为同目录 `strict-compile.json`、`physical-metadata-tests.json` 与 `.log`。
无本地模型请求、Native/Game操作或新业务worker。D派生输入与测试输出按通用存储策略
于 `2026-11-06T16:46:10Z` 复核；生产源码与持久测试继续作为活跃输入。
