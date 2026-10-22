# Python → Java：渐进迁移执行方向（2026-10-22）

用户已选择按组件逐项迁到 Maven + Quarkus + Java。**一期以 Java contracts + 单个 loopback Quarkus map composer 为首个实际切换目标**；读取资格、预算/评分及 continuity 纯 reducer 是后续候选，尚未实现。自动游玩沿现有合格链推进，迁移工作并行。

[2026-10-19 评估](python-java-migration-assessment-2026-10-19.md)保留历史，本次渐进方向优先。不承诺工期/速度；源码已有，尚无编译/JUnit/调用/切换通过信用。

## 为什么从合同开始

`machine_id: xenoamess-full-tower-eb9d2c1186`，`tools/ck3_live_run_id.py machine` 于 `2026-10-22T11:51:15Z` 实际 exit 0。[耗时审计](ck3-native-ai/robert-source32-runtime-turnaround-audit-20261022.md)与 [N45 闭场](ck3-native-ai/evidence/robert-source32-a45-zero-rpc-closeout-20261022.json)绑定原时刻与来源：

N45 FILETIME int/string 合同失配在最后消费者拒绝，周转 1131.489009 秒、新增保存 0 日。N41 FULL 35.3458871 秒/6 未保存日；Army AUTO 6.083374 秒中原生 read+serialize 仅 0.686448 秒，其余不能追认为 Python CPU。owner 128 KiB/SDK 源 1 MiB 上限也是合同失配。

Java 先减少合同漂移与失败周转。查询、推进、保存、Root 等待分别计时；1 秒/日只看完整已保存窗口及累计墙钟。

## 一个构建工程，逐项替换

采用**一个 Maven reactor + contracts 模块 + 一个薄 Quarkus 宿主**，不造五个微服务。当前源码在 [父 POM](../java/ck3-control/pom.xml)、[contracts](../java/ck3-control/contracts/pom.xml)、[local-service](../java/ck3-control/local-service/pom.xml)。后续纯组件纳入同一 reactor；宿主常驻复用，不每 RPC 启 JVM。

| 顺序 / 候选模块 | 确切生产边界 | 初期收益与保留责任 |
| --- | --- | --- |
| 1. `contracts-codec` | [current_saved_basis_v1.py](../tools/g2_saved_campaign/current_saved_basis_v1.py) 的 ExactRef/JSON 域；[file_stat_identity_v1.py](../tools/g2_saved_campaign/file_stat_identity_v1.py)；[shared owner](../tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py) 的 CampaignMapAdmissionV1 | record、sealed 状态模型及集中 codec，收敛生产者/全部消费者；先迁独立叶，不直译大 owner |
| 2. `admission-evidence` | [cold_runtime_admission_contract_v1.py](../tools/g2_saved_campaign/cold_runtime_admission_contract_v1.py)、[current_saved_campaign_preflight_v1.py](../tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py)、basis/owner 纯检查 | 只读小回执/引用/来源图；原 reader、SDK cold validator、真实 reducer 和锁内重验继续授准入 |
| 3. `policy-core` | [war_emergency_budget_v1.py](../ck3_autonomous_player/src/xar_autoplayer/war_emergency_budget_v1.py) 纯预算；[campaign_development_score_v1.py](../ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py) 纯算术 | 差分固定输入/输出；军费、承诺、应急资金、未知区间、360 月分母和舍入保持，不改策略或补观测 |
| 4. `continuity-core` | [current_saved_continuity_v1.py](../tools/g2_saved_campaign/current_saved_continuity_v1.py) 纯 reducer/预演 | 影子重放小事件；原 Python writer 唯一持锁提交，文件锁/事务后迁 |
| 5. 扩展 `control-host` | [current_saved_campaign_feeder_v1.py](../tools/g2_saved_campaign/current_saved_campaign_feeder_v1.py) 与原监督调度接口 | 一期宿主仅 map composer；未来协调既有 Python runner，消费真实退出/超时/终态。Game/SDK/Task/录制 custody 暂不迁 |

以上是施工顺序，未授资格。native_driver、service、owner、basis、feeder 混有 Python AST、原生证据、恢复与 Windows 身份，不整包直译。

## 一期实际范围与切换闭环

已读源码：[CampaignMapAdmissionComposer](../java/ck3-control/contracts/src/main/java/org/xar/ck3/control/contracts/CampaignMapAdmissionComposer.java) 与 [HTTP resource](../java/ck3-control/local-service/src/main/java/org/xar/ck3/control/service/CampaignMapAdmissionResource.java)。配置只监听 `127.0.0.1:8089`，入口 `POST /v1/map-admissions/compose`，身份 `GET /v1/map-admissions/identity`。输入上限 65536 B、输出 16384 B；输出为 Python-opaque JSON 原字节，不能让 REST 再将 byte[] 编成 base64。

目标链：**Root 已审看的实际小输入 → Java composer → 原字节回执 → Python warm/feeder/Queue 全部消费者**。Java 不读 Game、文件、进程、ledger 或 native pipe，不替 Root 断言已审看，不授恢复资格。ExactRef/GameGeneration/FILETIME codec 是该链的共享合同。

先用原件/fixture 作 shadow 差分，再切该生产者链。比较接受/拒绝、错误类别、结果及往返；覆盖 N45 故障、错/缺/未知字段、bool/浮点/越界、重复 key、非法字符、missing/null/[]、来源 SHA/身份漂移。消费者、兼容及回归同步迁移，不用 int/string 双接收兜底。

沿既有 CI 验 Java HTTP→Python 消费者与独立进程；涉及 cold/warm/请求合同仍执行完整对应 step。软件、来源、恢复预演、真实调用及实机通过分别记录，当前均未获信用。

不将整份 Driver/SAVE 跨 HTTP 往返或为 shadow 重读大正文。大 JSON 热点将来按解析、复制与 IPC 总成本实测；旧 SHA 绑定原字节，“值相同”不替代字节证据。

### Maven 环境与真实 RED

`machine_id` 同上；`J=D:/codex-ck3-demos/2026-10-22-java-phase1`。实读 `J/DEFAULT-MAVEN-3100-ACTUAL01.json`（12:20:12.065470Z）：官方 SHA-512、113 vendor file SHA-256 已核；fresh cmd exit 0，默认 Maven 3.10.0、home `C:/apache-maven`、Java 21.0.10；where 两项原 C 路径、PATH 未改。

实读 `J/DEFAULT-MAVEN-CAPACITY-ANNEX01.json`（12:20:06.318177Z）：C free 15465930752 B＜20 GiB safety；用户明确“允许本次约 12 MiB 替换”，仅本次例外，通用策略不变。旧安装备份 `C:/apache-maven-before-3.10.0-20261022`，48 小时复核点 `2026-10-24T12:20:06.318177Z`，不自动续期。

实读 `J/logs/maven-02.actual.json`：12:06:09.648430Z–12:08:15.186826Z，exit 1、125.538393 秒、source unchanged、build 0、无部署；代理 RED 未进入编译/JUnit。`J/logs/MAVEN03-DIRECT-ROUTE-PROBE01.json` 于 12:12:08.784010Z 记录 Central direct HEAD 200。Root 12:20 后操作报告：03 默认 CMD syntax RED，约 0.33 秒、未 Java；04 短修进行中。工具链安装、网络可达均不等于 Java build/JUnit PASS。

## 字段与运行合同

- 跨 Python/JavaScript 的 FileID/FILETIME 用规范十进制字符串；旧 Python-only opaque JSON 保留精确整数 ABI。Java uint64 用范围校验的 `BigInteger`/值对象，拒绝负值/溢出/非规范形式，不经 double/JS Number；数值接口另核安全整数域。
- 显式区别 missing/null/[]，不靠默认零/Optional/空集合合并。整数 token 拒 bool/浮点/字符串强转；金额/评分保留定点或 BigDecimal 精度/舍入，不改 double。
- Quarkus 默认 Jackson 会忽略未知字段；本项目应显式开启 `quarkus.jackson.fail-on-unknown-properties=true`，在统一 ObjectMapper/codec 禁止不合法 coercion，并验证重复 key、数值 token、必填和可空。仅有 Java 类型或校验注解不足以证明原输入合法。[Quarkus JSON 官方文档](https://quarkus.io/guides/rest-json/#configuring-json-support)
- 参数/返回值用集中约束和 `@Valid`，文件/JSON/原生入口仍实际校验；错误类型、业务拒绝、未知与内部失败分支明确。[Quarkus Validation](https://quarkus.io/guides/validation/#rest-end-point-validation)
- ledger 保持单 writer；Java reducer 先做纯预演，提交仍由原 writer 在原锁内重验。Java FileLock 与既有 Windows 锁/rename、FileID 等价性未经实际验证前不换。UNKNOWN 请求、未确定效果、原恢复事件与原 T0 不重放、不清空、不重置。
- 控制服务消费真实 child exit、超时、Job/进程终态、原生后态、保存结果；HTTP 成功或 Task ACK 只证明调用层结果。并行只扩展无冲突研究和读取，单个游戏的动作、NEXT 与资源 custody 仍串行。

虚拟线程用于等待型并发，不加速 CPU 规则/CK3 主线程，不授权并发游戏动作；原生阻塞仍实测，解析/计算不放无界线程。[Quarkus virtual threads](https://quarkus.io/guides/virtual-threads/#virtual-threads-are-useful-for-io-bound-workloads-only)

## 第二阶段：收敛来源图与源码生成

第二阶段再迁 [prepare_current_saved_campaign_cold_v1.py](../tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py) 的 Plan→Quote→来源表→固定点/部署图，改用显式模型、受版本管理模块与数据，减少 AST/源码生成，不让 Java 继续拼 Python。

验收保留外层来源表、部署闭包、固定点、导入路由与 reader 上限；65 叶/Source31 fixture 与 67 叶/Native32 图分别记录。新实现进入新 tuple/新图，冻结 SDK/runtime 和历史原件不改，不热改现场。

## 本轮反思落实到执行

- 并发产物未及时汇成可执行主链：Root 每轮先列一个实际阻塞，合并最小生产者/全部消费者闭环；独立线程持续旁路产出，只有新证据改变主链才追加工作。
- 冷启/准入反复消耗：在启动前执行已要求的真实失败路径，首批 SAVE 后同 Game 连续批；不为每个研究包或每批重新冷启。
- 下载环境未先核实：首个真实 Maven 请求同时核有效 settings/代理路由、目标卷余量和指定安装路径；失败先读内层终态，不反复空跑重试，不把 HEAD 200 当构建通过。
- 合同分散：以 map composer 一个真实切换链检验共享模型；不扩为重写大 owner/全仓整改。以上复用现有校验和回执，不新增无限门禁。

实施包固定 JDK/Quarkus/依赖与产物，不按网页 latest 自动更新。[Quarkus Maven](https://quarkus.io/guides/maven-tooling/#working-with-multi-module-projects)规定多模块/CDI 索引接法。

本叶仅改本文，未执行构建/测试/Game/外部仓库操作。

## 12:36–12:38Z 软件与发布实证（追加）

`machine_id: xenoamess-full-tower-eb9d2c1186`。本节覆盖当前完成状态；前文未编译/调用通过与 02/03 RED 保留为 12:22Z 前历史，不抹去失败。

- 实读 `J/logs/maven-07.actual.json` 及所引 stdout：12:28:14.401735Z–12:28:44.430420Z，完整 reactor `verify` exit 0，30.0290497 秒；11 JUnit，0 failure/error/skipped；Job 峰值 639901696 B，最终 active 0。compiled source 与原源码 pins 一致，contracts、local-service 均 SUCCESS。
- 实读 `J/logs/JAVA-PYTHON-MAP-INTEGRATION05.json`、对应 stdout/stderr：12:36:40.503583Z PASS；client/test 两个完整叶 strict 检查 exit 0；6 项实际 HTTP 测试全部 OK、0 skip/失败，包含原 Queue/feeder/reducer 的三条闭合 lineage。两个检查 Job 最终 active 0；原 Java 服务仍由原 owner 持有。该验收 Game RPC/ledger 写入 0。
- 实读 `J/logs/client-n46-map-e90880ecb92241949213bef1c893d1d8.outcome.json`：12:37:02.403415Z，`JAVA_MAP_PUBLISHED_FROZEN_CONSUMER_VALIDATED`；536 B map 与 Java 原响应 SHA 相同；Python fallback、旧 builder 调用和 Game RPC 均 0。授软件/当前 map 发布范围，不授 FULL/SAVE。
- Root 操作报告：N46 FULL11543 于 12:37:58Z register/run 0；这里只记调度 ACK，尚未核实际推进、SAVE 或完整批耗时。Java 完整 planner、后续 reducer、G2/30 年与 1 秒/日均未因此完成。

本叶仅追加既有证据；未重跑构建/测试或操作 Game。Root 本次明确放宽本文总帽至 12 KiB，追加仍限 2 KiB。
