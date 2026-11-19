# 金融 AI 发现恢复与 Native 依赖修复

本记录绑定 `machine_id: 4-8e1c2f1861`。用户要求持续完成整个期货／虚拟货币产品；本工作包不是任务终点。R0031 的 D14 GAP、未观察到气泡送达、失败退出和 D26 最新物理保存保持原事实。

## AI 发现的实际缺口及修复

R31 D14 的 `xfm_ai_count=36605`，head/tail 均缺失；D26 count=36810，但头尾仅指向新角色短链，512 次工作只有 1 次决策。旧 dequeue 将失效 next 当作真实队尾，留下正计数且不能恢复旧角色。现有证据未唯一证明最初何时由引擎使引用失效，也不能将全部稀疏发行归因于 1% 概率。

普通和付费关注两环改为双向局部校验，角色 about-to-die 钩子先摘链。旧 schema 首次真实 AI 回调共享一次 living census；未来仅 dirty 且相隔至少 30 个脚本自然日才能再次扫描。保留全部财产权、冷却、同日去重与付费 TTL；每日总预算及关注 64／1024 上限保持。独立审阅原件为 TASK 下 `ai-discovery-queue-repair-independent-review01/REVIEW.actual.json` 与 `...review02/REVIEW.actual.json`，没有以审阅代替引擎测试。

两笔历史 AI 登记实际自认购 1600 分、外部认购 0，后已失败退款；不能计作新上市。原广告只覆盖少量亲友，公开 IPO 发现正在独立实现，不能因队列恢复就报告“很多币”已经达成。

## 实际软件与构建结果

原件根为 `C:/workspace/ck3-market-live-20261118/operations/`，每项的 `ORIGINAL-WAIT.actual.json`、stdout/stderr 保留原字节。

| 原作业 | 原 wait／墙钟秒 | 实际范围 |
| --- | --- | --- |
| MVN-financial-ai-queue-ordinary01 | 0／18.7360828 | ordinary-only 21 项，无失败、错误或跳过 |
| MVN-financial-ai-queue-attention02 | 0／18.8408863 | 最终双环 23 项，包含原 21 项，不重复累计 |
| TEST-native-profile-v6-linker-class01 | 0／39.7206650 | 当前 v6 公共消费者 13 项，无失败或跳过 |
| BUILD-native-qualification24-02 | 1／168.5399292 | 正式构建内层 4294967295：CoreControl fixture 缺真实 SaveMapped provider；未执行有限夹具，无 Q.actual/PASS |
| BUILD-save61-incremental25-two-targets01 | 4294967295／77.3226534 | CoreControl 已链接；额外 hotfix basic 目标缺 ArmyBase／ActiveWars 及 PlayerArmies provider |
| BUILD-save61-incremental25-two-targets02 | 0／33.8967154 | 同缓存，仅新增 3 个真实 provider TU 编译及 hotfix basic 链接；未执行这两个 EXE |

正常 fetch/rebase 合入远端 `56ef3ebbf` 的 SaveMapped 两目标链接闭包。随后只补 hotfix basic 测试目标的三个真实 TU，并新增 OFF SAVE 拒绝回归：同 owner 上下文先提交非 SAVE，再核 SAVE 不增 clone／queue／delete。生产宏和 SAVE 权限不因链接修复打开。

v6 仍为 803 个生产 TU、208 flags、22 个 reviewed fixtures；其中 CoreControl fixture 因真实 provider 从 11 增至 12 TU。hotfix basic 不属于这 22 项，额外成功链接不授新增 fixture 或该热修游戏资格。新 Q25 的实际完整资格、气泡送达、旧存档恢复及自然业务仍待执行。

## 后到实际 Q25 与公开 IPO 软件结果

20:27:44Z，`BUILD-native-qualification25` 原 wait 0／70.6000909 秒。干净源码 `63e7b98b7bb49b34aa78933c5beec5a26c66ebbb` 的 Q.actual 为 16599B／`bf7c16468d239d86b684284cb59b7a2e692ca16c227edc516c2d463f28ac0c92`；公共消费者 PASS 为 1890B／`0172141ecce9799cfebdad681cefc91588c9503021e8ab727f70f67d18448d10`。发布到专用资格目录的 DLL 为 13501440B／`394d37bb1e0e78525895a4d3c91a66faa08baa778e1fe4c637027eb46e97c28e`。真实完整资格覆盖 803 TU／208 flags／22 fixtures，按原依赖约束复用未变结果；它没有启动或附加 Game，不授气泡送达或新热修 EXE 实机信用。

随后采用公开 IPO 候选02：广告与公开渠道互斥，每次原 AI 机会最多查看一个筹备项目，原概率、储备和真钱认购保持；旧项目通过原币日遍历每天最多64个有界迁移，索引损坏先拒绝再按日重建。新增4个 runtime 叶，当前运行清单220文件。`MVN-financial-public-ipo02` 于20:34:30–20:34:50Z原 wait 0／20.242524秒，35项通过（原AI23＋新IPO12），无失败／错误／跳过。完整模块软件验证、实际新包、同局冷载和自然市场结果仍继续。

## 完整金融验证与原失败

`MVN-financial-current15-verify01` 原 wait 1／123.94879秒，415项中10项容量测试报错、无断言失败：测试 VM 未载入新增 IPO 脚本定义。原失败 XML 在 TASK 的 `software-continuation15-failed01-preserved` 保留。容量测试随后载入真实依赖并支持实际条件分支；原16项断言保留，新增1项检查发行日服务、IPO 轮转／摘除与终态容量释放共存。`MVN-financial-capacity-ipo-consumer01` 原 wait 0／29.1874508秒，17项通过、无跳过。

最终 `MVN-financial-current15-verify02` 于20:49:01.566127–20:51:16.900998Z执行，原 wait 0／135.3348752秒，416项全部通过，无失败、错误或跳过，完成 Quarkus 构建。独立的共享模块 `MVN-financial-shared-current15-install01` 原 wait 0／14.9276248秒、23项通过；其完整源码和 POM 未变，沿原执行窗口复用，不宣称在金融最终窗口重新运行。`software-continuation15-actual02/SOFTWARE.actual.json` 为177794B／`68aceb75ffc437d58ce247a9ae709e7884e731ca471143020d059a118869bcd2`，绑定353个真实源码、220个运行文件、两个真实执行窗口及439个不同方法。

R31 的 D26 保存日期映射为1066.12.7／日序389430，与 `xfm_last_date` 和 `xfm_daily_attempt_script_date` 一致。D14→D26 的12自然日实际增加12次尝试和收盘；累计少1不足以认定持续漏日。原 D14 GAP保留，新 rawprobe 将观察实际调用阶段，不补历史日、不修改已失败断言。以上结果均未授实际新上市、气泡送达或完整产品通过。

## 公共部署的非索引数据删除

完整553路径差异包含真实已删除的 `tools/auto_upgrade_buildings_1_21_0.json`。它不在旧 runtime 索引中，差异行的 before／after 均为空；旧 Java 缺失验证误将它作为 Java 删除而拒绝，Host 资格尚未开始。公共工具现将这类非索引 tools JSON 数据交独立入口核对实际 Git 删除、当前缺失、旧索引缺失及显式回执字段；Python、Native、已索引数据和 case／control 配置没有获得该例外。Java 原合同保留。

`TEST-public-nonindexed-data-deletion01` 于21:04:10.676713–21:04:16.201048Z实际执行，原 wait 0／5.5243381秒，原Java4项与新数据4项共8项全部通过、无跳过。包含真实临时 Git 混合删除至公共 qualify 的正例，以及缺少显式声明、非真实删除、重建文件、已索引和非选择类型的拒绝。它修复部署工具的元数据接线，不授金融业务或新Game运行通过。
