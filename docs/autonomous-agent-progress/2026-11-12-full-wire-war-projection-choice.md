# 按完整请求长度选择现有无损战争投影

原整数组引用投影先写入 marker，随后已有 item 字典投影会因此退出；大量重复战争 item 仍留在模型请求中。现在从同一完整、未投影的数据树分别生成两种已有无损表示，比较包括 policy 提示在内的完整 HTTP 请求字节数，严格更小时才选择 item 字典。相等或可选分支失败时保留原表示；原表示的完整编码先执行，原编码错误继续向外抛出。原数据树、事实、观察来源、时间与两个投影算法保持。

正式变体保留此前 history、root 字典、Council、known-pending 和 capability 的差异，只移入本次选择逻辑。正式单生产 TU 首次编译得到完整4类，再复用未改的测试2类对正式产物运行完整4项，实际4P／0F／0E／0skip。测试独立展开两种格式、校验完整真实请求基线逐字相同、保留其他 HTTP 字段与提案 body hash，并覆盖真实完整 wire 的 tie 与原 strict 编码失败。原固定 class hash 的历史测试没有修改或被算作已通过。

需要外置完整请求原件的测试发布在 `local-service/src/qualification/java`，只在显式资格运行中设置 `xar.choice.event13.request`；没有把本机原件路径加入默认 Maven 测试。原件为1838824B／`614a3104234e4dc45ab5da6de2cb18c8264e11e88ea6f0ea16da6e4d2b84c1c4`。该请求已带旧投影，因此测试对历史展开后的字段／值／数组顺序作等价验证，不声称恢复未保存的旧对象成员位置。

软件索引：`D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/FORMAL49-4CLASS-FOUR-FULLWIRE-DATA-SOFTWARE01.json`（5034B／`0aa849e3ddd3c5345c8b59f9d20849b7e83bf3009df2e06b7eda839f273fb831`）。正式 whole4 原 ACTUAL 为1438B／`b3610ecec5256a7fc04d6b3c035e1768f38ca9599d2c06fbb32920d5ae21441d`，exit0、accepted、输入未变、CLOSE释放。首160MiB prospective准备拒绝没有启动 JVM，保留原件；后继176MiB工程范围单独记账。机器 `xenoamess-full-tower-eb9d2c1186`，2026-11-12离线资格；当前机器标识通过原 `tools/ck3_live_run_id.py machine` 只读取得。

核心三处修正来自本地模型第二个完整响应；owner保留该核心并抽出纯 DATA 入口。模型提供的测试不符合实际接口／原件形状而弃用，正式测试由 owner09 独立实现。首个失败响应及唯一返工成本保留，不将坏测试计作采用。

本次是源码与离线软件资格，尚未 Runtime 采用，也没有在线请求尺寸、模型耗时或新增保存日收益。正常运行不等待本次 Git 发表，后续只在 Runtime 的真实必要边界采用；不修改已派发请求或重发业务模型调用。
