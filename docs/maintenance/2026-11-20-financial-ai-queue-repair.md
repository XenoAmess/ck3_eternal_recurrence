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
