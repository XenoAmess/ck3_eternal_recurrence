# 礼与道 R0002 实机证据候选

三轮原生 faith／rite 分合通过；正式欢迎、选礼仪和修习流程仍是 **RED／等待根代理最终验收**。本报告不宣布整个 mod、无错误日志、重载存档或发布验收通过。

这是外置保全包，尚未写入仓库。小型原始回执、两次冷加载的源码与存档对象摘录按原字节复制；完整日志、截图和存档留在原外置目录，以 [index.json](index.json) 的 SHA-256 绑定。该索引不应被后续结果覆盖；新结果应另写增补文件。

| 验收项 | 本轮结论 | 证据 |
| --- | --- | --- |
| 精确 1.20.0.3 native 接入、地图就绪、暂停 | 通过 | [attach](native/0002-attach.json)、[首次 snapshot](native/0003-initial-snapshot.json) |
| 同一玩家三轮合流／分立及延迟断言 | 通过 | [引擎脚本断言 v2](primitive/native-primitive-attestation-candidate-v2.json) |
| 最终保存态对象关系 | 通过只读投影 | [存档 summary](saved-objects/three-rounds.summary.json)；未重载 |
| 原型之外的正式玩家入口与修习 UI | RED／待根代理最终回执 | [状态候选](report-state.json)；不以入口点击 ACK 代替实际状态 |
| 全体错误日志为零 | 不通过／未声明 | [原始 error.log](primitive/error.log)、[精确分类](primitive/error-classification-addendum.json) |
| 全部 36 礼仪／36 信条玩法、多人、AI 传播、发布 | 未验 | 本轮范围只有精确加载样板及原型闭环 |

本轮实际开局是普通 **1066 罗贝尔·吉斯卡尔**。本次 native 玩家 id 是 **31254**，原版历史键是 **1128**；[基线存档身份核对](baseline/identity.verified.json) 同时比对姓名、出生日期、狐狸绰号、奥特维尔家族及历史映射。旧准备回执中“867／29829”是保留的错误元数据，见 [PREPARED.historical.json](run/PREPARED.historical.json)，不能成为当前角色或控制台目标。

游戏来源为 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`，CK3 1.20.0.3，Steam build `25652598`。本轮进程 PID `7564`；EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。当前一次性 userdir、启动 argv 与干净 prelaunch HEAD 见 [launch](run/launch.json) 和 [prelaunch](run/prelaunch-check.json)。没有把历史 1.19 角色 id 或 ABI 当作本次接口。

当轮 Steam 离线由根代理直接审阅新鲜画面中的“离线模式”，且先取得窗口变化及新桌面像素，见 [画面新鲜度回执](offline/steam-frame-freshness.json) 和 [人工回读](offline/offline-reviewed.json)。截图原件 `live-attempt-002/offline/probe-1/steam-moved.png` 以索引绑定 SHA `1655dc8af4f7a6bbf58a22960129eba4ed210e4f75cb9003d142a7514e01efae`；仅截图文件时间不是离线证明。

加载源码的两次修订均保全：

- R0001 为提交 `01a52e6842b0513c78053751304cfe60a963df92` 的 [production manifest](source-r0001/production.manifest.json)，及其当时的 [原型 effects](source-r0001/fixture/common/scripted_effects/lyd_np_effects.txt)。它的真实 RED 仍保留在原 attempt，没有改写成通过。
- R0002 使用提交 `7fd082eab7626239ecb88702d0ebae71f938b259` 的 [production manifest](source-r0002/production.manifest.json) 与 [修正后的 fixture](source-r0002/fixture/common/scripted_effects/lyd_np_effects.txt)。原生装载错误修正实际来自父提交 `be321ac403741aed6036c46d6f1e426e10f26b4d`；两提交的 `mod_li_yu_dao` tree 都是 `5107ad4fa03bb66a663be1acc24f7a74c0ade4a4`。27 个冷加载文件（正式 18、夹具 9）至三轮完成均与首次停止审计相同。

CI 的实际引用见 [只读官方回执](ci/official-ci-readonly.json)：`7fd082e` 的 [Official Runner CI 37163561735](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37163561735) 是 success。礼与道专项的实际 success 是 `be321ac` 的 [37163517527](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37163517527)，不是另一个 7fd 专项 run；两个提交的产品 tree、专项 workflow 和所用 extractor 对象相同。CI 证明静态工作流结果，不能代替本轮实机。

原型由玩家 UI 决议初始化，并使用罗贝尔的实际封臣阿贝拉尔（runtime `36445`／history `1134`）作为受测对象；没有走创建 NPC 的备用路径。控制台提交 `event lyd_np.9000`，省略 id 并锁定本地玩家 31254。原生 MCP 已实际接入，日历推进、暂停、快照、事件选项与保存使用 native 能力。该精确 provider 的 12 个工具没有任意脚本、控制台或 LYD 决议入口，因此只对缺少的入口使用受保护的桌面回退，能力列表及代码哈希见 [v3 输入回执](input/console-v3-execute.receipt.json)。

桌面输入的失败与修正均保留：v1 虚拟 backtick 只有 ACK，实际没有打开控制台；v2 物理扫描码 `0x29` 打开了控制台，但虚拟 Ctrl+A/V/C 没有完成粘贴，读回仍是哨兵，因此 **没有按 Enter**。v3 复用仓库已有物理扫描码 executor，目标窗口确认英文 `0409`、完整复制读回 `event lyd_np.9000` 一致后才提交 Enter。见 [v1](input/console-v1-open.receipt.json)、[v2 拒绝提交](input/console-v2-execute.RED.receipt.json)、[v3 实际提交](input/console-v3-execute.receipt.json) 和 [关闭控制台](input/console-close.receipt.json)。输入提交回执自身仍标注业务后置条件未证实；后续真实日志和延迟断言才证明执行结果。

三轮的 `JOIN_APPLIED`、`DETACH_APPLIED`、`JOIN_D1_PASS`、`JOIN_D30_PASS`、`DETACH_D1_PASS`、`DETACH_D30_PASS` 都各为 **3**，`INITIALIZE_PASS` 与 `THREE_ROUNDS_PASS` 各为 **1**，没有 `FAIL` 或 `REJECTED`。5 次冷却门禁断言通过，测试专用清除冷却也恰好执行 5 次。全部原始 marker 行见 [精确字节摘录](primitive/debug-marker-lines.raw.log)，其原日志行号和原日志哈希保存在索引。

最后一次有界 native 推进因真实 `LYD_NP_THREE_ROUNDS_PASS` 停止，暂停读回通过，见 [advance-cycles-004](primitive/advance-cycles-004-report.json)。终点调试日志前 `1,585,492` 字节 SHA 是 `0cb8fb9d263358901402088685bf7ec5830c2a97d3618086bbbc17975025cdf4`，与有界推进回执一致；其后的产品 UI 日志没有被算作该终点内的断言证据。先前只推进约 50 天的部分 attempt 仍保留，不单独算三轮通过。

断言的真实内容可在冻结 [fixture triggers](source-r0002/fixture/common/scripted_triggers/lyd_np_triggers.txt) 与 [effects](source-r0002/fixture/common/scripted_effects/lyd_np_effects.txt) 查看：接收方主礼仪和原领袖保留、支礼仪的 parent faith、郡与受测角色礼仪同步、旧专属领袖头衔解绑及失去持有者；分立返回的实际动态 faith 成为支礼仪新 parent／main，并建立自己的领袖。D1 与 D30 事件再次检查这些条件。跨 faith 合流查询明确以接收方 main rite 为比较对象，三次观察值均从 `-15.00` 到 `0.00`；没有偷偷修改内容或全局分歧阈值。

三次分立实际返回 faith `106`、`107`、`108`；源码类型／显示名相同不代表相同对象。最终保存态独立读回 anchor faith `33`／rite `150`／领袖 `31254`；branch rite `151`／faith `108`／领袖 `36445`／head title `18417`；受测郡是 `c_camarda`／landed title id `2250`，保存礼仪 `151`。旧领袖头衔 `18372`、`18402`、`18410` 保存为被摧毁、没有当前持有者；faith `34`、`106`、`107` 对象仍存在并有别的 main rite、没有领袖绑定。这证明保存态关系，并不证明旧 faith 无追随者、垃圾回收或保存后重新载入成功。

三轮冻结时 error.log 的真实分类是：

| 类别 | 数量 | 归因与边界 |
| --- | ---: | --- |
| Trigger localization perspective | 3 | 原型 `lyd_np_triggers:3` 的 is_ai、未知调用方的 is_alive、正式 `lyd_player_triggers:3` 的 is_ai；正式 UI 项发生在三轮终点之后，仍是必须保留的真实产品错误 |
| Unknown formatter tag | 165 | 原始字节为 `weak\x08\x15positive_value`；尚未定位，不能无证据归咎 GodName 或声明是无害原版错误 |
| AI coronation invalid activity reason | 1 | 没有记录宿主，归因未闭合 |
| bp3_roaming invalid activity | 27 | 日志直接识别 Irengba／runtime 26904／history manipur019／c_manipur，异于受测两人；未见自定义 AI 活动入口，但没有无 mod 对照，不能排除间接影响 |

上述错误不等于原型状态不变量失败，但它们使“整个产品零错误 GREEN”不能成立。本轮没有凭日志猜测做 GodName 热修正；实际儒家原版宗教层已有神名与代词定义，尚无缺神名 key 的直接错误。

仍需单独验证：正式 36 项选择／修习流程；自然五年冷却与普通 100 虔诚支付；直接分立 main／last rite；分歧达到 100 的自动分立；旧 faith 生命周期与追随者；保存后重载；native AI 传播；正式学统权限与同意机制。测试夹具允许跨越冷却的三轮成功不能替代这些项目。

保全者只读取现成冻结文件并写外置报告，没有向 CK3 发输入、MCP 请求或 native 查询，没有启动／注入进程、改变 Steam／lease，也没有编辑 tracked checkout。根代理持续持有屏幕租约并单独执行正式 UI 验收；其新结果需追加成新的、哈希绑定的增补报告。
