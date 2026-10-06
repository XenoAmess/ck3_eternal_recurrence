# 本机 CK3 1.20.0.2 兼容工作交接

交接日期：2026-10-02，北京时间。仓库：`C:/workspace/ck3_eternal_recurrence`。

## 恢复执行与最新顺序（2026-10-04 用户指令）

用户已要求接手续做，原交接时的停止安排解除。本机升级执行固定顺序：**白绮独立版第一、自动建造第二、其他mod随后、天朝特色制最后**（用户本次称“天朝365”，仓库产品为361制）。保持不冲突工作尽可能并行，优先产品占用前台和实机槽；后台开发、证据和发布准备持续推进。

每个产品独立达到正式验收门槛后立即发布该产品，不等全部产品。用户已明确授权逐个上线；每次仍完成正式staging、实际上传、完整Steam Change Notes匿名精确回读、订阅缓存复核及永久changelog提交/推送，随后第一时间将Steam恢复离线。未通过门槛不能宣称该产品发布完成。

当前实际游戏已为1.20.0.3/build25652598，以下1.20.0.2段落保留为原交接事实。
**2026-10-05 最新增量：白绮 1.0.2 已实际公开，entry1791128346 完整 Change Notes 精确回读，新下载缓存 27/27 字节匹配；Steam 已恢复离线，screenCAS2415释放。正式发布记录见[1.0.2 changelog](release-changelogs/vivhite-courtier/1.0.2.md)。上传原生回调超时 UNKNOWN 保留，没有重复上传，实际结果由公开与缓存独立证实。** 自动建造接续占用前台；其余产品并行准备，天朝361最后。下面尚未上传、日志未归因等条目保留为此前各时点的历史事实，不代表此增量后的白绮状态。

用户 2026-10-05 追加低优先级任务：白绮独立版及琉焰卿原版创建廷臣时均增加具体礼仪选择；**全部 mod 的1.20翻新维护完成之后才启动**。已纳入[产品任务清单](product-technical-roadmap.md)，不扩入当前发布门槛。

### 2026-10-05 自动建造发布增量（提交北京时间 04:56）

自动升级建筑维护版 `4.0.3` 已实际更新到 Workshop `3800124956`，正式 tag `auto-upgrade-buildings-v4.0.3` 与源码 commit `7dc8d31e51d16fda1b1d7aaae231dccf4af9b97b`，上传 `stage=complete / EResult=1`，提交 UTC `2026-10-04T20:56:18.893772+00:00`。匿名回读公开 entry `1791147378` 完整 Notes 与冻结全文精确相等：495字符、16行、1128字节、SHA-256 `32ae0d84c9adc347e353d00e4b1c926da259724e29f64c47c96dd44f66d3fbc5`；公开标题、描述、作者及 AppID/visibility 同时匹配，旧公开 entry 正文保持原样。

当前六图标修复生产包 R0014 已完成真实六图标显示、第三项／第二步／一次 Confirm、四flags `true/false/true/true` 和自然16日384小时，金币243→93、同活玩家和episode保留；harness GREEN并清理关闭。修复前六条VFS空texture在本次实际范围为0，zeroID0；仍有58court＋30formatter，其完整正文与实际无mod基线匹配，次数未声称全等。R0010核心33＋R0011继承3是独立证据，不能写成单场39；原R0010 RED/UNKNOWN、R0012观测RED、R0013 VFS6均保留，当前验收范围通过不改写历史。

发布目录 `C:/workspace/ck3-upgrade-20261005/aub-workshop-publish-4.0.3-01` 绑定原生回执、正式17、匿名全文和下载事实。fresh download 已完成，目标开始前不存在，实际985263字节、timestamp1791147378、subscribed=false；真实缓存17/17文件共985263字节已精确复核，无descriptor归一化；新formal-rebuilt-02无ID重建的manifest/ZIP与上传原件逐字节相同，默认Documents/mod已新建版本4.0.3的canonical outer指向rebuilt、ID只在outer。收据为 `C:/workspace/ck3-upgrade-20261005/aub-workshop-publish-4.0.3-01/postpublish-local-verification-01.json`，SHA-256 `847191b5d1e4c34421f102d08083bba712360f06add221400ea3d88a7c85b6de`。永久changelog及本增量仍须root合入master提交推送。Steam已恢复离线，fresh-window原图已直接审阅“离线模式”。当前确认实际公开的产品为白绮与自动建造；两产品实机／公开上传／完整Notes／缓存／离线门禁已取得，本次永久文档提交推送完成后本轮正式产品收口为2/10（20%）；不能提前把尚未推送的文档记为已完成。

见[自动建造专题](ck3-1.20.0.3-auto-upgrade-buildings-compatibility-2026-10-05.md)与[4.0.3 发布记录](release-changelogs/auto-upgrade-buildings/4.0.3.md)。下面时点的“自动建造待上传”和UNKNOWN表述保留为历史，优先读取本增量和当前专题的范围。其他已授权mod继续并行，天朝361最后；廷臣具体礼仪选择仍等全部1.20翻新维护之后。

### 2026-10-05 并行接续增量（北京时间 02:36）

前台继续 P1 自动建造；白绮发布已经闭合，无需重跑。当前会话允许 root 加 64 个子任务，按独立工作分配，并保持游戏、桌面与 Steam 单一执行者。其他八个待维护产品的源码候选、完整更新说明及必要构建已并行准备；候选与发布草稿不能记为正式上线。

自动建造 R0010 已在实际 1.20.0.3 完成核心 **33/33 各一次、FAIL 0**，92 个完整自然日，以及一次原版 bookmark.1070 选项与关闭后状态核验。第 93 次时间推进跨真实死亡时，验收工具的单生命守卫报 `running advance left its alive anchored map`，会话为 RED，已实际清理关闭；继承三项仍 **0/3**。下一场 R0011 是同一 17 文件生产投影的独立继承专项，保留原断言与真实死亡/原生 Continue，不重复前 33 项，不能合称单场 39 项通过。最终日志 139 块中 58 块与原版基线完整正文一致，其余 81 块仍 UNKNOWN，不作无依据豁免。外置证据：`C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--auto-upgrade-buildings--R0010/`；关闭归因 packet：`C:/workspace/ck3-upgrade-20261005/aub-r10-log-and-release-draft-agent-01/closed-boundary-packet-01.json`。

待发布候选为自动建造 4.0.3、肃清曼荼罗 1.0.1、体验优化 1.1.1、重整河山 0.4.1、驱策朝贡国 1.0.1、天朝经商贪腐维护版 1.0.1、牛来 1.0.3、永恒轮回 1.0.2，均声明 1.20.0.3。体验优化另修正反向朝贡防御资格所用原版义务旗标；主版七语同步已有 110 项特质目录和礼仪继承文案。各产品的必要静态与候选构建收据独立保留，尚未取得新版实机的产品仍为 NOT_RUN；正式 tag、上传、公开 Notes 精确回读、缓存和最终 changelog 均未补造。天朝 361 按用户顺序最后处理。正式发布进度仍是 **1/10（10%）**。

**03:40 接续增量**：上述八产品候选及永久草稿共79文件已通过复审、提交并推送到 `master`（`60dbab0c7cec7213d63d634842f65aff6ec72006`）。自动建造 R0011 已通过原三项继承断言与 DONE，各一次、FAIL0；实际罗贝尔死亡后 root 在原生窗口一次选择继续扮演罗杰，次日原生日期、活玩家与政策保留均有证据，8个实际步骤全部完成，harness GREEN且清理关闭。生产17文件与R0010完全一致，旧生命terminal与R0010 RED保留。首次速度选择发生了回执截图扩展名错误，未重试或补造历史回执；后续独立原图及实际snapshot确认速度1。见[自动建造新版专题](ck3-1.20.0.3-auto-upgrade-buildings-compatibility-2026-10-05.md)。

同仪器化纯原版 R0003 未启用任何 mod，实际自然推进245天，保持原活玩家与episode，关闭/cleanup通过。其127个formatter块与R0010的78个、R0011的22个具有同一完整正文；一条AI加冕报错与R0010完整正文/multiset相同。这证明这些报错无需AUB即可发生，不证明各旧实例第一调用者或完整因果等价。原版另有一条TGP脚本错误，独立保留。R0010剩下两个event ID=0的加载报错仍未归因；下一接点是只加载17文件生产包、不加载夹具的对照与真实政策UI。严格RED和未发布状态仍保留，不能把本轮功能33＋3写成单场39项或正式release完成。

最新白绮结果见[1.20.0.3专题](ck3-1.20.0.3-vivhite-compatibility-2026-10-04.md)：核心加载3/3、R0012面板入口4/4、business默认值8/8、R0016九项文本9/9及R0017新版特质实际交付均通过；正式发布结果见上述增量，完整GUI自动化研究仍在后台。以十个本轮产品为分母，正式发布收口为1/10（10%）；历史30%主要迁移工作包口径不可混用。C盘满盘事故后已完成安全清理和资产无损压缩，空闲曾达到20GiB，见[清理记录](maintenance/c-disk-cleanup-2026-10-04.md)。

2026-10-04后续R0016已实际取得九项显示文本9/9（年龄30、六技能各6、价格120、金币247），
全13步实际通过并已关闭游戏/释放screen。整体启动观测超时RED及58条未归因加载日志保留，
完整GUI与正式发布尚未完成；真实字段、DLL、运行依赖补齐和清理证据均见上述1.20.0.3专题。

2026-10-04 22:38 后续纯原版对照 R0002 已实际 4/4 步通过并关闭，屏幕 CAS 2366 释放。相同 b01 DLL/injector、同四项 profile 字节，仅启用 mod 列表为空，复现 R0016 的 58 条加载报错；去时间戳后的全部正文相等，因此不能把这组报错归为白绮独有错误。候选产品现为 1.0.2，补齐七语 Rite 文案并通过静态及 27 文件双构建；新增特质实际交付检查准备中，尚未正式上传。通用 GUI 完整研究已转后台，发布聚焦本次产品适配行为。

用户最后指令是“温和地完成手上的每件工作，不要再开启新的工作，然后编写交接文档到 docs”。本轮按此结束：收妥既有 TED 报告，正常关闭正在等待的 361 会话，恢复桌面，保存证据并提交交接。未继续启动游戏、功能验收或新诊断。原先预计 04:30–06:00 的后续验收时间表已取消，本文的恢复入口不代表自动续跑安排。

## 接手时先知道的结论

项目 master 同步和本机游戏更新已经完成。CK3 从 **1.19.0.6 / build 23530548** 更新为 **1.20.0.2 Crozier / build 25588574**。十个玩家产品的源码迁移及必要静态工作已交付，但**全部 mod 的兼容性任务尚未完成**。

上一轮进度口径为 **30%，即 3/10 个主要迁移工作包已按其明确范围收口**：肃清曼荼罗核心、体验优化的总督/付款/代表交互、天朝经商贪腐的政府迁移/第四档/代表决议。这个分母不是功能用例数，也不是正式发布进度；这些产品的未覆盖边界和日志限制仍保留。AUB、TED 有实际核心通过证据，但未归因日志或 UI 缺口使其不能计入完整兼容收口。不得把 descriptor 的版本声明、parser、native harness 的 GREEN 或正常退出当作产品全部功能通过。

总览及历史增量见[本机滚动记录](ck3-upgrade-all-mods-2026-10-01.md)。本交接的最新状态优先于历史记录中的“继续”“正在执行”“待取得桌面”等时态。

## 环境已经收好

- CK3 真实安装：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。当前 EXE SHA-256：`ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`。仓库中的参考链接被 Git 忽略。
- 最后受管游戏正常退出，退出码 0；进程树、job 和看门狗均清理完毕。交接时 CK3 及本轮启动/验收控制进程 inventory 为空，没有待执行的桌面输入。
- 显示设置已从验收用 2560×1440 恢复至原来的 **1024×768、60 Hz**；系统枚举与 `pyautogui.size()` 均读回一致。
- 恢复后的原始桌面截图已直接审阅：Steam 明确显示“当前处于离线模式”，底部状态亦为离线。收尾没有切换联网。
- 桌面资源已释放，协作子任务按“准备完成、实机未运行”收尾；主任务总线的 done 表示这次交接完成，不表示全产品兼容完成。
- 没有上传 Workshop，没有发布 tag，没有进入七语正式翻译或 Steam Change Notes 发布流程。家徽编辑器的已授权 1.19 DDS pack 未在本轮更新。

收尾证据目录：`C:/workspace/ck3-upgrade-20261001/wrapup-20261002-01/`。`closeout-report.json` SHA-256 为 `2d363fab9df05168196483a9f4c8945ab60f67e12c2004f2381ad83826c8d856`；它绑定最终截图、分辨率回执、最后会话的退出/清理和启动阶段停止原因。此目录是本机外置证据，未把大型过程素材提交进 Git。

## 十个产品的最终状态

| 产品 | 已交付的源码及实际证据 | 尚未完成 / 下一接点 |
| --- | --- | --- |
| [永恒轮回](ck3-1.20.0.2-eternal-recurrence-compatibility.md) | 新特质目录、Rite、原生继承窗投影迁移；L0 通过。R0003 廷臣五阶段 UI、三项新增目录价格和 Aluk Rite 交付实际通过；有真实引擎保存。 | 真言宗仅预览；冷载入、白绮独立与双顺序、真实死亡/结算/跨进程导入、无继承人共七 cell **0/7**。日志有未使用变量，死亡消费者尚待实机。 |
| [白绮独立版](ck3-1.20.0.2-vivhite-compatibility-2026-10-01.md) | 独立 1.20 trait 快照、Rite、LF 字节合同及 L0/parser 已交付。 | 独立加载、双 mod 两顺序实际 **NOT_RUN**，包含在七 cell 内。 |
| [肃清曼荼罗](ck3-1.20.0.2-remove-mandala-compatibility-2026-10-01.md) | R0001 原 9 个核心断言通过，日志零错误；兼容声明 1.20.0.2，15 文件可复现构建。主要核心工作包收口。 | 加速派发夹具证明核心链；自然年流转及保存/载入不由此推定。 |
| [体验优化](xqol-ck3-1.20-compatibility-2026-10-01.md) | 天朝继承/退位/死亡/关闭 guard、行政 17 标记与 6 次实际开关、两名候选 UI、代表改信/释放/赎金通过。修复 1.20 余额上限和 recipient 报价上下文；R0004 真实强/弱牵制付款边界通过。兼容声明 1.20.0.2，27 文件构建。主要已列范围收口。 | 复杂防御 **NOT_RUN**；其他家族、slider、宗教负门禁和处罚 tooltip 仍有 GAP。R0003/R0004 非空日志及误调分支保留，不称全产品零错误。 |
| [重整河山](reclaim-the-motherland-ck3-1.20-compatibility-2026-10-01.md) | 新版原生臣服、政府预算、头衔后果迁移；30 项测试和 L0 通过，当前构建 36 文件。 | 隔离实际 **NOT_RUN**；预算/臣服/复辟 UI 入口已准备，51 与 50 门槛仍有 GAP。夹具先换玩家再杀前任，不能据此声称实际原生死亡窗通过。 |
| [驱策朝贡国](ck3-1.20.0.2-tributary-expansion-directives-compatibility-2026-10-01.md) | 修复夹具与原版 `scope:target` 的名称冲突，保留原 13 断言及 16 生产文件。R0005 原核心全通过，真实投降、同实例保存/载入及玩家/日期/无战争读回。兼容声明和必要静态/构建已交付。 | 最终 **85 条错误**；3 项严格 UI 检查仍部分/GAP，严格 `INCOMPLETE_OR_RED`。未覆盖胜利/白和/贡额等。 |
| [天朝经商贪腐维护版](ck3-1.20.0.2-celestial-commerce-corruption-compatibility-2026-10-01.md) | 从新版原生政府保留机制，仅增加经商能力。R0001 原 11 标记、真实决议、退出第四档和三年冷却通过；22 文件构建，兼容声明 1.20.0.2。主要已列范围收口。 | 2 条明确夹具 unused flag 诊断仍使严格零错误门 RED；第二事件 typed getter 有 GAP。其他档位、never-corrupt、独立财政转移与保存/载入未覆盖。 |
| [自动升级建筑维护版](ck3-1.20.0.2-auto-upgrade-buildings-compatibility-2026-10-01.md) | 新 potential/Rite/DLC 门禁迁移。R0001 原 39 标记及罗贝尔→罗杰真实死亡继承、3 个继承政策检查通过。兼容声明 1.20.0.2，当前构建 17 文件。 | **93 条未归因错误**，严格仍 RED。生产+空夹具对照已准备但 **NOT_RUN**；不得凭文件来源直接豁免。 |
| [牛来](ck3-1.20.0.2-ox-here-compatibility-2026-10-01.md) | L0、可复现构建及 parser 通过；12 核心标记与实际拒绝/招募/到达 UI 方案准备完毕。 | 隔离实际 **NOT_RUN**。 |
| [天朝特色 361 制](ck3-1.20.0.2-zhongguo-compatibility-2026-10-01.md) | 新原版依赖审计、8 组静态通过。接入并发文案更新后修复四处按钮长度，32/33 聚焦检查通过，1034 文件双构建可复现。 | R0002 在规则选择阶段停止，**未 Apply/Start，功能核心 NOT_RUN**。旧人工审阅 manifest 不绑定四句新文案，保持 RED，未伪造人工批准。 |

`ck3_autonomous_player/mod_bridge` 是开发桥，不是第十一个玩家产品。已有 7 项测试及 parser 6/6 通过，实际桥请求 **NOT_RUN**，profile/probe 仅准备完成。

## 最近两项实机工作如何结束

### TED R0005：已经完成证据收口

完整 run：`4-8e1c2f1861--tributary-expansion-directives--R0005`。下列路径均相对外置根 `C:/workspace/ck3-upgrade-20261001/`。

- 原 13 required markers 各一次、0 FAIL；16 production + 6 fixture 文件无漂移。实际战争 ID 4 投降后消失；同实例载入后玩家仍 34440、1066-09-17、暂停/速度 1、无战争。
- 真实保存：`native/profiles/ted-profile-05/profile/save games/大辽皇帝，耶律弘基_1066_09_17.ck3`，10,979,194 bytes，SHA `39422882c8f9fc08b69d8cfb73011ce7beffe67cf23a92a0724119bfd06951a9`。
- 保存/载入不是冷启动；载入后的目标持有者、朝贡关系、停战未独立 UI 核验。不能把三项完整 UI 合同写成 PASS。
- 最终 error.log 为 85 个 `[E]` / 199 个非空物理行，SHA `c1232badbec0ba5c9a0ff25da4ebf1f6a61b201ccfb71c93f4135d3597528519`：2 夹具 flag、25 formatter `negative_value`、载入新增 57 个 court-scene trigger + 1 个 culture-set 错误。报错原版路径仅证明位置，不证明全部根因。
- `live/<run>/file-only-closeout-01/report.json` SHA `6e9873835614f6a07606cd859f93e59699a0bcfef0ffea953a724740dbce4949`；`strict-functional-result.json` SHA `47c5afaec4339f0dd6b2defd3b723d08e0b6d273b15f59f4e5fd51490e6cec93`。严格 RED 与原 GAP 保留。
- 正常清理证明在 `live/<run>/root-cleanup-01/cleanup.json`。源码兼容声明及核心证据已由 `cc9a08d84` 交付，本次只提交最终补充报告。

### 361 R0002：按用户要求正常结束

完整 run：`4-8e1c2f1861--zhongguo-style--R0002`。在新游戏规则页，驱动无法取得三组规则的真实选中项；`startup-01/STOPPED.json` 明确停止在 Apply/Start 前。随后只检查了类别菜单，没有选规则或开始游戏。停止原因尚未归因，不能称产品机制故障，也不能称规则核对成功。

用户收尾指令后，对已绑定 PID/creation time/profile 的游戏窗口发送 `WM_CLOSE`。`user-wrapup-window-close-01.json` 保存身份与原因；游戏退出码 0。最终 `native-report.json` 是 RED，错误为会话在 map readiness 前结束；同时 `cleanup_ok=true`、`managed_session_thread_finished=true`、job 0、tree gone、watchdog absent。这个 RED 与启动阶段未完成、用户结束会话相关，功能步骤列表为空。

完整原图、12 次规则搜索/滚动及全部回执保留在 `live/<run>/`。当前 `native/profiles/zhongguo-profile-02` 仍是已经准备好的 1034 文件 production；830 份 TXT/GUI 及夹具相对此前准备输入不变。接手者先看停止证据，再决定是否修正规则定位；本轮未继续排查。

## 未关闭问题的证据边界

**AUB 日志**：2 条零 ID 报错早于 on_game_start/核心标记；1 条 AI coronation 及 90 条 `positive_value` formatter 也不是由死亡继续按钮首次引发。时间更正、来源扫描、对照方案已写进产品专题。只发现原版简中 `house_relation_latest_change_amount` 的 `#weak` 后缺空格候选，尚无受控因果证明；没有修改安装游戏或产品去压掉日志。

已有报告：`aub/live-delivery-attempt-01/report.json`、`aub/log-attribution-followup-01/report.json`、`aub/zero-id-file-review-01/report.json`。后者 SHA `1154c968f54a93c879f117c9514b353a41c78f47211c02f332a6617126b6847e`。生产+descriptor-only 空夹具不能隔离单一定义/引用，结果变化也只能证明移除整组夹具的相关性。

**体验优化日志**：R0004 付款证据是在后续误调未初始化改信 dispatcher 前保存的，付款五标记/八条件有效；那次额外调用造成的 303 个真实 runtime errors 永久保留。更正附录 SHA `71fc04cf9b889aa4c99e4e09568ad616c1f1f288e7a47a9ac4abeb1bf6f95ce6`，原报告不覆盖。R0005 行政场 error.log 为零，只适用于该场。详见[付款修复专题](xqol-native-payment-context-2026-10-01.md)。

**主 mod 日志/保存**：R0003 保存 68,450,662 bytes，SHA `52e8d94ef42e6d3f61c83e9cef92da8a5898347e51947fa76577ee637cf4341e`。收口报告为 `audits/courtier-main-ui-R0003-closeout/report.json`。五种 unused variable 各两次，其中两个 curse rarity 是已记录的旧例外，三个 settlement 变量有 native 消费者源码但实际死亡尚未验证；不添加虚假读取或扩大忽略。

**361 审阅**：当前按钮长度修复已提交 `f189a0711`；最新 32/33 与旧输入的 52 failures + 1 error 必须分开。剩下一项是人工审阅字节绑定，不是机器运行成功就能签核。不得为了日常兼容开发伪造 approval 或强行开启七语发布审计。

## 已准备好的恢复入口（本轮均不执行）

外置根简称 `B = C:/workspace/ck3-upgrade-20261001`，Python 为本仓库 `tools/.venv/Scripts/python.exe`，版本 3.14.7，命令使用 `-X utf8`。依赖已经安装；切换 checkout/worktree 后必须显式复核解释器与依赖，不能静默回落裸 Python。本项目的 Windows 自动化仅使用 Python。

### 主/白绮七 cell

统一 driver：`B/audits/courtier_continuous_driver_20261001.py`。以下占位参数须替换为当次实际身份，不可原样执行：

```text
tools/.venv/Scripts/python.exe -X utf8 <driver> execute-cell --screen-authorized --scenario <scenario> --product <product> --run-id <新的完整ID> --state-dir <B/native/profiles/profile> --offline-proof <当次已审recovery.json> --out <新的输出目录>
```

| scenario | product | 真实 profile 名 |
| --- | --- | --- |
| main-cold-reload | eternal-recurrence | courtier-main-ui-profile-04 |
| vivhite-ui | vivhite-courtier | courtier-vivhite-ui-profile-02 |
| dual-original-first | vivhite-courtier | courtier-dual-original-first-profile-02 |
| dual-vivhite-first | vivhite-courtier | courtier-dual-vivhite-first-profile-02 |
| main-writer | eternal-recurrence | courtier-main-writer-profile-03 |
| main-reader | eternal-recurrence | courtier-main-reader-profile-01（实际 writer 成功后生成） |
| main-no-heir | eternal-recurrence | courtier-main-no-heir-profile-01 |

旧 r7 bundle 的双顺序短目录名漏了 `courtier-` 前缀；使用上表真实目录。profile04 保留真实 `xar_checkpoint.ck3`、`xar_episode_seed.ck3`、原 `driver-state.json` 和 `checkpoint-input-validation.json`。冷启动自动沿用 R0003 immutable pipe `\\.\pipe\ck3_upgrade_4_8e1c2f1861__eternal_recurrence__R0003`；新 run ID 不能替换旧 anchor。原进程已关闭。

writer 必须取得实际死亡、结算、分数 N 与稳定 tutorial bytes，然后调用：

```text
tools/.venv/Scripts/python.exe -X utf8 <driver> prepare-reader --writer-report <writer输出/actual-death-settlement.json> --fixture-name courtier-120-reader-actual-r1 --profile-name courtier-main-reader-profile-01 --out <B/audits/courtier-reader-actual-prepare-r1>
```

先初始化 reader，再复制真实教程 bytes；不能植入计分位。当前普通开局 actor 必须动态绑定，不能把历史 ID 31254 写死。no-heir 需实际引擎取消继承人与真实死亡/终局 GUI，不能由夹具 ACK 代替。

### 其他既有准备包

| 工作包 | profile（均在 `B/native/profiles/`） | 已有工具 / 下一步边界 |
| --- | --- | --- |
| AUB 最小对照 | aub-production-empty-fixture-profile-02 | `B/aub/production-empty-fixture-prepare-01/handoff.json`；17 production + 空 fixture descriptor，仅 loader、普通罗贝尔开局及真实政策菜单。不开启循环、不重跑 39 核心/死亡。 |
| RMTM | rmtm-ui-profile-01 | `B/audits/xqol-rmtm-operator-009/fixture_live_operator.py`；scenario `rmtm-ui` → `ui_after_chaos` → 实际预算/臣服 UI → `rmtm-continue` → `restoration_decision_ready` → 实际复辟 UI。 |
| QOL 复杂防御 | xqol-defense-only-profile-01 | `B/audits/xqol-defense-operator-011/fixture_live_operator.py`；使用 **011**，旧 010 的 CLI choices 失败保留。原 setup → 真实生产 auto callback 首次 `xqol.101` → 原 readiness ≥2 天 → verify；30 天失败，不能手动首调制造成功。 |
| 牛来 | ox-profile-01 | `B/native/five-product-ui-profile05-01/` 的启动 driver、functional operator v2 和严格 collector；12 核心及拒绝/招募/到达实际 UI 均 NOT_RUN。 |
| 361 | zhongguo-profile-02 | 同一 five-product 包；先审 R0002 的规则停止证据。规则定位未修，不应直接声称具备完整连续通关能力。 |
| 开发 bridge | mod-bridge-profile-01 | `B/audits/mod-bridge-001/bridge_snapshot_probe.py probe --run-root <新的live根> --output <新的输出目录> --ownership-task ck3-standalone-live-20261001 --timeout 60`；只能写桥自己的唯一 `take_snapshot` 请求。不是字面上的完全只读操作；不使用 native fixture write-inbox。 |

five-product 启动入口必须带子命令 **`execute`**；缺少它会 exit 2，R0002 那次未启动 UI 的参数失败也保留。正式 frozen runtime 在 `B/native/five-product-ui-startup-executable-01/frozen_standalone_live_runtime.py`，SHA `af14e6b68bd6f516fcf5e15f3154f9e94d10c0e57ae4a3da7f1d93744e0b484f`。不把合成 guard 通过写成实际产品通过。

### 下一次获准继续时的启动前提

1. 先读根 AGENTS 和[隔离验收合同](ck3-1.20.0.2-isolated-product-live-acceptance.md)，登记新任务并 `poll --ack`；确认唯一桌面负责者，取得 `ck3-screen:acquired`，不要与其他机器/任务争用。
2. `git fetch` 后 `git rebase origin/master`。当前交接前主线为 `cc9a08d84a22e66faa80038562d4bcee60f02f38`；最终交接 commit 可由本文的 Git 历史定位。此前收口提交还包括 `3a71c707a`（QOL）、`bb4519f82`（XCCC）、`679383862`（AUB 来源复核）。禁止 merge/force push。
3. 用 `tools/ck3_live_run_id.py allocate --mod <canonical>` 取得新的完整 ID；所有 attempt/profile/输出保持独立，失败记录和素材永久保留，不复用旧 run。
4. 原来的离线证明已过期。先冻结启动 argv，再由 `tools/desktop_steam_offline_recovery.py` 取得当次新鲜离线截图并直接审阅，在有效窗口内启动。普通验收保持 Steam 离线；如必要联网，遵守账号占用及及时恢复离线规则。
5. 五产品共用外置 helper `C:/workspace/.codex-task-bus/ck3_upgrade_native_session_20261001.py start`，参数含 `--product`、`--run-id`、`--state-dir`、`--offline-proof`、`--plan B/native/plans/compatibility-map-only.json`。基础 source 固定为 `B/native/source-d19e794`，不要把当前远端所有 native 能力默认视为已经在本机验证。
6. 原生候选 DLL SHA `c02b8d83d5ddef813a69d3cf9745d51e889ba3961342fe70cad2dce2761c87ab`；injector SHA `523d22dc3bcedf3be5fd399275049d451b430296a30cb1acd077aafccdf3628e`。基础 17 signatures / 7 vtables / 34 instructions、4 C++ / 10 harness 检查不等于 advertised 功能全集实测。旧 1.19 ABI runner 不可盲目解除版本锁。
7. 当前桌面是 1024×768；旧截图点位不可复用。任何坐标输入都先读真实截图尺寸和当前桌面，用 `tools/desktop_coordinate_map.py --receipt` 及明确内容矩形换算。键盘须确认英文 0409、目标 HWND 和焦点；文本需完整读回。进入 map-ready 后另看真实 HUD，控制速度 1 并读回，不能由 ACK 推定。
8. typed getter 缺失、unmaterialized fullscreen、部分 UI 合同和非空日志均保留 GAP/RED。验证与风险相称，一次通过或形成可复现 RED 后即提交/普通推送，再处理下一工作包；不要重复未变输入的检查。

建议接手顺序只是待办参考：先审 TED/AUB 既有日志与最小对照边界，再选择尚未实际运行的主/白绮七 cell 或 RMTM、QOL 防御、牛来；361 先解决启动规则核对。没有本轮续跑时间承诺。

## 证据与仓库边界

`B/baseline/` 保存旧 EXE/manifest/trait/succession GUI 和 3591 个旧原版 TXT；`B/new-build/identity.json` 绑定本机新游戏。`B/audits/`、各产品目录、`B/live/<完整ID>/` 和 `B/native/profiles/` 保存 staging、日志、PNG、输入回执、存档、驱动状态及失败 attempt。接手时保留这些目录，不为收口清理或覆盖。

本次交接提交只包含本文件、滚动状态更新和 TED 最终报告补充，未新增机制修复或启动新的检查。必要验证是文档 diff、链接/路径和证据身份复核；不重新运行已经完成的 L0/parser/游戏矩阵。

正式 Workshop 发布仍须另行进入发布阶段：使用各产品 allowlist staging，按真实当前文件数和 builder 合同验收；补齐七语及发布审计，再完成上传、订阅缓存、永久 changelog 与匿名 Steam Change Notes 全文精确回读。本文没有把开发兼容结论转换成发布事实。

## 2026-10-05 05:51 肃清曼荼罗 1.0.1 正式公开与本地发布门禁闭合

本增量追加真实新状态，历史 NOT_RUN / NOT_PUBLISHED、失败 attempt 和旧版本证据保持原样。

CK3 1.20.0.3 R2 已实际闭合 GREEN：Root 真实 Robert / 默认规则 / mrm_enabled Apply + Start 一次，core12 + final3 + finish 共16/16，八个完整单日共192小时，同 actor31254 / episode native-31254-9aa18b987d4f，十 marker 各一 FAIL0、最终 error.log 0B、实际 finished_at / cleanup / thread 均通过。[R2闭合 packet](C:/workspace/ck3-upgrade-20261005/remove-mandala-r2-log-boundary-agent-01/closed-r2-full-body-comparison-02/final-mrm-r2-comparison-packet-02.json) SHA `f1b5001e3959790df9c073fdb376456c08e93ef23f3228fb00952651f6858802`。

真正正式 tag `remove-mandala-v1.0.1` 对应 commit `94e6ec4d75f7a165ed8aad885d33f019c92b336d`，已由 Root 推送。官方正式 [manifest](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/formal/mod_remove_mandala-v1.0.1.manifest.json)为 **2,741 B**，SHA `5e85c692effdbb44c7944a09dd53fefe217cd0a0628e98bd80f0de54ff79dd61`；[ZIP](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/formal/mod_remove_mandala-v1.0.1.zip)为 **776,824 B**，SHA `86d4e24f6a6d87c6582268d688b6d299d350f5a2b9bbeed1ce9fa7f482a19f8e`。正式 15 文件与实际 R2 生产包精确相同，见 [root-prepublish-freeze.json](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/root-prepublish-freeze.json)。上传后独立官方重建 `formal-rebuilt-02`，15 文件与原正式树逐字相同，内层 descriptor 不含 remote ID；原上传树保留。

目标 item `3797711947` 已实际单次上传，未重播 Submit。[native-publish-receipt.json](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/native-publish-receipt.json)为 stage=complete、EResult=1，`submitted_at=2026-10-04T21:42:09.844955+00:00`（2026-10-05 05:42:09 Asia/Shanghai）。独立匿名 [verification.json](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/anonymous-readback-01/verification.json)为 **18,747 B**，SHA `1fec35efd06647e99853d4e93d89f978c06a4e85dcd5a9fc3fb8b19b776aa1a7`，三端点完整 HTTP200，owner `76561198273714027` / App `1158310` / item / public / title / description 精确。最新条目 entry ID **1791150129** 的 HTML 解码及换行归一化全文为 **1,929 字符 / 25 行 / 2,693 UTF-8 B**，SHA `a54b823c817e0aa26a0f3e84426d3523a2a5b280b7aab0e03c57586fec1c7657`，与提交前完整冻结 Notes 精确相同；原 HTTP bytes、headers、时间、URL 和全文均保全。SDK 回调和匿名全文是独立证据。

历史失败保持原样：两次旧缓存 verify 均报 `mismatch: descriptor.mod`（`cache-verification-01/02` stdout/stderr）；两处 native probe 工具错误（顶层及 `fresh-download-after-cache-preservation-02/native-probe-result-01.json`），其原错误与 stdio 未删除；首次 download 的工具 ACK / exit0 不代表业务成功，实际业务 `failed / CACHE_ALREADY_EXISTS / started=false`。Root 将旧 **1.0.0 缓存 15 文件**保全到 `old-1.0.0-cache-preserved-01`，[preservation receipt](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/old-cache-preservation-receipt-01.json)为 byte_exact=true；另一次独立 probe 实际 logged_on=true、owner/app 正确。上传始终只有一次，没有重放 Submit。

之后必要在线的独立 [fresh download receipt](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/fresh-download-after-cache-preservation-02/native-download-result-01.json)实际 `ok=true / complete / callback EResult=1`，耗时 **9.816 秒**，cache 在启动前不存在，install size **777,243 B** / timestamp **1791150129**，installed=true、needs_update=false、subscribed=true；沿用原已有订阅，未改订阅。官方 **STRICT** 缓存 verify03 实际退出码 0：[stdout](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/cache-verification-03.stdout.txt)记录15文件，stderr空；15文件与正式manifest逐字节精确，descriptor 无ID，**没有使用 descriptor 归一化或 remote-ID 例外**。正式上传后重建的 manifest/ZIP 也与原正式构建逐字相同。

新 canonical 用户外层 `.mod` 之前不存在，实际创建后 **254 B** / SHA `7d93a3ec498006dc82e0e48074de8fa4e85b6809edb243beac291f87c3b70da8`；canonical remote ID 仅留此外层。最终恢复的 [fresh Steam 原图](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/offline-restored-fresh-02/probe-1/steam-moved.png)已由 Root 直接审阅“离线模式”，**393,754 B** / SHA `7ff29bcc313f3ce1deb5a968b0c557a151375a12014f37ad3ac075d85b7375c9`，不是第一次恢复后再次联网前的旧画面。汇总 [postpublish-local-verification-01.json](C:/workspace/ck3-upgrade-20261005/mrm-workshop-publish-1.0.1-01/postpublish-local-verification-01.json)为 **6,006 B**，SHA `f661df3ad7d8ae7027ecaa1c0aa6fe249aafc3c358e8ff09e39b06fd1258955e`，实际本地收口时间 `2026-10-04T21:51:26.370152+00:00`。

本产品实机、正式构建、单次上传、公开完整Notes、fresh cache15、无ID重建、canonical outer和最终Steam离线已全部实际完成。兼容专题、永久changelog、本交接及[发布证据索引](release-evidence/remove-mandala/1.0.1.json)一并提交至master；实际文档commit和远端读回保存于同次外置发布目录的release-closeout-01.json。正式源码tag与文档收口commit分别记录。描述、README和完整1929/25 Notes不改，不重播upload或已通过实机。历史准备的NOT_RUN/NOT_PUBLISHED属于当时日期边界，不能读成当前候选状态。周期dispatcher加速检查不外推自然一年、关闭规则或独立保存/载入。

## 2026-10-05 牛来 1.0.3 正式公开、实机与屏幕实际闭合

本增量只追加实际新状态；旧 1.19、候选、失败 attempt 与原始素材继续保留，不反向改写历史。当前公开版本为 `1.0.3`，上一公开 `1.0.2` 为历史基线。

R2 `4-8e1c2f1861--ox-here--R0002` 的实际业务与简体中文 UI 复核为 **PRODUCT PASS**：拒绝、招募均经 Root 真实最终确认各一次，唯一勇士到庭、身份与勇武、强制骑士／适用时的零薪勇士、情人与秘密、不兼容性取向下勾引及零薪断言均通过。12 个必需标记各一次，两个 FAIL 均零；initial5 与 final3 实得通过。原 frontend 查询在执行前超时，恢复只读检查通过；原完整 runner `RED` / `HARNESS_RED` 与原 error 保留，不能写为整个 runner GREEN。actor38665 / PID17096 / generation1 全程暂停于 1066-09-15（raw53144328），没有自然日或重载验收信用。实际 `finished_at=2026-10-04T22:33:02.531798+00:00`、cleanup=true、thread=true；关闭后原始 error.log 为 **0 B**，SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，没有旧日志白名单或免除规则。

实际闭合 [thin12](C:/workspace/ck3-upgrade-20261005/ox-r2-log-boundary-agent-01/closed-r2-product-harness-and-root-ui-receipt-12/final-ox-r2-product-PASS-harness-RED-thin-receipt-12.json) SHA `95d14c09740801649315d63eb843d85c060a97f56ee4cdadd8d8dddf0cb001fa`，及 [full10](C:/workspace/ck3-upgrade-20261005/ox-r2-log-boundary-agent-01/closed-r2-current-full-body-comparison-10/final-ox-r2-current-full-body-comparison-10.json) SHA `298deb8d65e74f3cc042977f5705cdd3881e4ad321dfd3b5f1b985afaeec026c` 分别绑定业务／运行器边界、Root 原图、实际输入及完整日志来源；旧 UNKNOWN / RED 不改成通过。

正式源码 tag `ox-here-v1.0.3` → `27233b21273959c85d4f2b85bd7519e53fcf99a1` 已实际推送。item `3790635143` 的单次 SDK update 已于 `2026-10-04T22:49:42.938448+00:00` 实际完成，stage=complete / EResult=1；独立匿名三个端点 HTTP200，owner/App/item/public/title/description 精确，新 entry **1791154182** 的完整更新说明 **1130 字符 / 21 行 / 1600 UTF-8 B**，SHA `bf8f774e66f834c114dba47378608b3e7b7871e4694287a5c841a9e843643e8a`，与提交前完整冻结字节精确相同，旧条目保持原样。SDK 成功与公开全文回读分别记录。

实际 fresh 下载耗时 **9.404 秒**，开始前 cache 不存在，callback EResult=1 / installed=true / install **717537 B**，时间戳1791154182；该回执 subscribed=false，不写为新订阅成功。官方 STRICT cache verify 实际 exit0 / **22 文件**、stderr空；未使用 descriptor 归一化或 ID 例外。正式上传后独立重建、canonical 源／两正式树／缓存共四处内层 descriptor 均无 remote ID。canonical outer **228 B** / SHA `d14d58a80f2cafad96694e7f1a91f61b925d30e38c787ce59964543e336bee6c`，ID 仅留用户外层。Root 已直接审阅最终新鲜 Steam 离线原图，SHA `612498a9b80f65a06cb01b7b8c21208faa16c5bcf81ce6eb151000cdbec40dc7`；本地实际汇总时间 `2026-10-04T22:55:06.499921+00:00`。

屏幕任务 `ck3-upgrade-screen-20261004-a42` 的真实 CAS 完成回执为 sequence **2756**、state=done、resources=[]，已释放屏幕；没有根据命令 ACK 推定释放。后续 QOL 占用不改变此历史释放事实。

永久 [发布证据索引](release-evidence/ox-here/1.0.3.json) 与 [changelog](release-changelogs/ox-here/1.0.3.md) 分别记录发布与版本差异。**本轮永久记录的 master 提交、推送及远端回读仍待 Root 实际执行并追加 release-closeout 回执**；没有虚填未来 master commit。源码 tag 与最终文档收口 commit 分开。此脚本不重播实机、上传或下载，不改公开描述与 Notes 正文字节。

## 2026-10-05 接续增量：正式完成4/10，体验优化付款范围通过

牛来永久记录已实际提交、推送并核对远端 `68e323a2738d1d74403f259c75d2576dc6f01532`；[最终发布收口](C:/workspace/ck3-upgrade-20261005/ox-workshop-publish-1.0.3-01/release-closeout-01.json)为 `RELEASE_COMPLETE`。以上待推送措辞保留为写入当时的历史。白绮、自动建造、肃清曼荼罗、牛来共 **4/10（40%）** 正式完成，不能把未发布产品的单项通过计入此分母。

体验优化付款 R7 在同一游戏进程内完成原五步及实际一天推进，24小时、同actor34422/PID18580/generation1；10项付款标记各一次、三类FAIL为零，新增scope三标记各一次、scope FAIL为零。首次开局通知造成的资格超时及完整领地DTO缺口保留，完整harness为RED；实际会话 `2026-10-05T00:45:00.956256Z` 闭合，清理及线程退出通过。见[当前角色资格与真实范围](ck3-native-ai/ck3-12003-current-actor-fixture-qualification-2026-10-05.md)。宗教 R8 在D0取得15项/FAIL0和scope身份，原四步及另三项只读查询实际finished，于 `2026-10-05T01:09:42.968610Z` 正常hold到期GREEN闭合，清理及线程退出通过；未执行finish_hold，完整领地读取仍unavailable，当前日志的夹具编码提示及原版court块另存不泛豁免。此结论仅覆盖限定宗教场景，不能记录为产品已发布。防御新有限场景输入正在并行准备，旧one_life严格入口阻塞保留。

原版创建器 R10 因未在900秒内取得完整暂停地图而超时，原业务16项未执行，已实际清理退出；最后heartbeat ready不授予完整snapshot或00 anchor。已准备另一份未用冷profile，复用现有typed普通Robert开局，完整规则实际回读与原one_life/00资格保留；不改旧现场或计时。writer33/33、reader12/12既有实测范围保留，无继承人及新创建器GUI仍待前台。

本轮并发调整：前台运行体验优化付款／宗教；后台同步准备防御、领地读取诊断、原版新冷输入和发布文案、永久知识记录及C盘清理。重整河山、驱策朝贡国、经商贪腐已封存执行卡，等待前台，不重复未变输入的检查；天朝361最后，具体礼仪选择仍在全部翻新维护之后。C盘另完成精确19份已闭文本无损压缩，API尺寸差112.64MiB；全部内容SHA与原mtime保持，详见[清理记录新增](maintenance/c-disk-cleanup-2026-10-04.md#2026-10-05-新闭场文本无损压缩精确19文件)。

**2026-10-05 后续失败与诊断增量：** QOL防御R9真实D1/24小时后仅4/23 required、外置关系夹具FAIL2；partial收尾后harness GREEN且清理完成，a48 CAS2900/resources=[]已释放，产品防御未通过。Main R11已earned真实90规则Apply全映射、strict00、D1及初始化7/16，但Root外置调用错用了实际MCP清单不存在的`ck3_activate_ingame_decisions_v1`，原harness RED与受管cleanup保留，a49 CAS2931/resources=[]释放；不归游戏崩溃或已证mod错误，cancel/119/default/custom348未证。68个engine块中10个与R10完整正文exact，其余58个court/12种正文仍UNKNOWN。新source05 trace-only DLL构建与11纯合同通过只支持下一新冷场诊断，真实held-title branch仍UNKNOWN；queue NEW02的当场工具名预写guard与3纯测试已交付，unknown/mixed零control写。证据集中于[当前角色资格专题新增](ck3-native-ai/ck3-12003-current-actor-fixture-qualification-2026-10-05.md#2026-10-05后续失败边界与工具名守卫)，旧失败和旧输入不改，不能获得额外产品或发布信用。


## Main 1.0.2 实际发布与永久记录（2026-10-05 23:26 Asia/Shanghai）

琉焰卿原版 item **3784706360** 已实际上传 **1.0.2 / v1.0.2 / 36aa60f5aac2ae53bc8fa56db36a7df5a38dd095**；上一公开版为 **1.0.1 / v1.0.1 / e9cc6c82aa8c9c24518f4e9c2f118a074b1292f7**。SDK 在 15:26:02.172289 UTC 返回 stage complete / EResult 1。匿名回读新 entry **1791213961** 的完整 Notes 为 **2150 字符 / 21 行 / 3044 UTF-8 B**，SHA `ec2e429a398d1a42d32049bd24e3a8ba1655d3205f7eacfa6ce94d751f5ce3ac`；owner、app、item、公开可见性、标题、描述全部精确，旧条目保持原样。

正式 staging 为 **86 文件**；manifest SHA `905085a23887afaa4a2588219363ee068b88ca7aba1ff1d757f8c2cf05e6a875`，ZIP SHA `5a0408333c45c2221b3987c18ef9192b4a0ae2386013bed6f1cc8b1eef59c177`。旧缓存完整迁移保留后取得 fresh download EResult 1；正式 builder 的 workshop-cache verify 实际通过86文件。上传后重建 pristine 的 manifest/ZIP 一致，内层 descriptor 无 remote_file_id；Steam 恢复离线由 Root 亲审原图 nonce `05b228296a1a`。发布屏幕 a62 的实际 keeper exit0/last3547 后，CAS3548/done/resources[]，已释放。

R20 八值、正常 OS0、16/16、EOF 和已赚 Writer33/Reader12/Creator16/R15cold 只按原范围复用。Pub01 EResult2、网络中断、旧匿名 UNKNOWN、第一次命中旧缓存及其校验失败原件保留；不重传已成功版本，不重跑已经通过的验收。[永久 changelog](release-changelogs/eternal-recurrence/1.0.2.md) 与 [发布证据索引](release-evidence/eternal-recurrence/1.0.2.json) 已作为本次 master 记录；实际 commit/push/远端核对保存于 `C:/workspace/ck3-upgrade-20261005/main-workshop-publish-1.0.2-actual-R20-02/release-closeout-01.json`，该回执实际闭合后累计正式完成 **5/10（50%）**。

体验优化唯一新场 `4-8e1c2f1861--xenoamess-quality-of-life--R0011` 已实际启动，前置只读 observer 在 launch 前运行，尚不授予防御业务或正式发布信用。重整河山 operation03、驱策朝贡国 operation04、经商贪腐 operation12 的 Source05 入口已准备，业务实机仍待前台。天朝361最后；任意具体礼仪选择仍在全部1.20维护之后。另一台机器的窗口保留记录不限制本机验收。


## 本机模组维护增量（2026-10-06 01:08 后补录）

此节实际编制 UTC `2026-10-05T17:11:20.577046+00:00`，仅记本机模组，不改另一机器 M/BG 的整体状态或早会基线。此前未完成记录按原时点保留。

正式迁移完成 **5/10（50%）**；白绮、自动建造优先工作均已完成，琉焰卿原版 1.0.2 的永久发布 commit/push 为 c55db0c3，最终证据索引已在 f8bbcb849 入库。

体验优化 R11 已取得实际资格、initial2 和 D0 审阅。唯一 24h 推进为 53144328→53144352，原 23 条业务只有 startup4，出现 `reverse_contracts_setup` 和 `composite_relationship_setup_not_ready` 两项 FAIL；原版拒绝测试样本的 forced 朝贡契约，前提修订只进入新候选。游戏正常退出 0、job0、所有观察器实际退出，a63 CAS3596/done/resources[]。[原业务和清场交接](C:/workspace/ck3-upgrade-20261005/xqol-r11-live-monitor-agent-01/HANDOFF-R11-CLOSEOUT-01.md)保留；不把清场 GREEN 当作业务通过。新 fixture03 使用真实原版忠顺 effect 并保留目标、非同盟与真实旗标检查；新 cold12 仍未消费／未启动。

兼容版本专项已完成：8 个已公开 1.20 产品 tags-only 实际 SDK 成功，匿名完整标签、Compatible Version 右栏及旧 Notes 全文均精确核对；内容 handle、描述及预览 handle 保持。14 个正式构建路径接入同一映射、14 双构建与 7 个静态校验通过。规范、产品表、8 份永久修订和证据已普通提交／推送至 master **f8bbcb849a571e7179d337cb45a991b00582ab6b**；Steam 恢复离线，a64 CAS3611 实际释放。详见[规范](workshop-compatible-version.md)和[永久证据](workshop-metadata-revisions/2026-10-06-compatible-version.json)。此项不增加正式产品发布数。

当前前台继续体验优化；重整河山、驱策朝贡国、经商贪腐并行更新新 descriptor 的正式输入绑定，业务实机仍待各自新场。旧公开 1.19 产品随真正 1.20 发布添加版本标记；天朝361最后，具体礼仪选择在全部维护之后。用户对另一台机器的游戏窗口安排不限制本机。


随后源码独审确认，忠顺候选03对当前宋的 celestial 政体不适用：原版 Obedience 条件只在支持该机制的政府生效。因此03保持 CHANGES_REQUIRED，未消费新场。改为审查候选02：在真实结义资格存在时设置原契约，再走原版正常解除盟约；解除后的真实 forced flag 与非同盟必须由新场严格断言决定。实际保持尚未验证，不新增产品通过信用。

## 本机体验优化 R12 实际归档（2026-10-06）

只追加本机实际新状态，旧R10/R11、未启动候选和失败原件保持原样。R12 `4-8e1c2f1861--xenoamess-quality-of-life--R0012` 在同actor34422/PID21744/generation1完成D0→D5共120小时，raw53144328→53144448。D1正例38528的 `reverse_positive_native_prejoined` 已实测，说明当时在同War4中已有参与，未证明原版或mod加入因果；不能写成“从未加入”。D5原防御14项必需标记各一次，原矩阵PASS且FAIL0，但新增反向场仍有 `reverse_positive_participating` 与 `reverse_matrix_done` FAIL2，合计19/23，产品防御未全通过。

正例参与检查是四项合取。相邻负例PASS已在同target/War4证明primary_defender=root宋，其余正例朝贡关系、forced flag、参与状态三个D5原子仍UNKNOWN；不能从联合FAIL推断“已退战”或宣称生产召援已定位。两份实际进度为 [D1](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0012/defense-first-day-root-01/progress.json) 与 [D2–D5](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0012/defense-after-d1-root-01/progress.json)；完整限定见 [防御维护追加](xqol-1.20.0.3-defense-maintenance-2026-10-05.md#2026-10-06-r12-实际归档原防御14项通过反向正例联合检查仍失败)。

游戏真实正常退出0，native shutdown0/tree_gone/cleanup=true/job0/全部库存[]，观察器实际退出、四个原PID均gone；95ff在partial finish中对已退出游戏自动取snapshot报错，完整runner RED和原错误仍保留，cleanup/thread=true。[闭合薄证据](C:/workspace/ck3-upgrade-20261006/xqol-r12-thin-report-observer-agent-01/actual-closed-cleanup-and-observer-exit-01.json)4093B、SHA `92eecbec35e500ec822112d9639fe4497fde867cbdd1b6cc86b2e410d20b914b`；[a65实际释放](C:/workspace/ck3-upgrade-20261006/xqol-r12-close-current-original-root-01/actual-a65-screen-release-01.json)CAS3647/done/resources[]，本机02:18:17。清场成功不授予业务或发布信用；体验优化1.1.1尚未发布，本场不增加正式完成产品数。

## 本机重整河山 R0001 实际归档（2026-10-06）

只追加本机新场，不覆盖旧准备、失败或历史实机。R0001 `4-8e1c2f1861--reclaim-the-motherland--R0001` 于UTC18:23:12.956974用新a66/Source05/9ea实际启动，CK3 PID20392/generation1；资格 **FAILED_AFTER_SINGLE_START_NO_RETRY**。首root查询前actor31254、native2/MCP revision3、event=null、owner pump ready，但宋资格两marker各0；30秒后返回 `timeout_cancelled_before_execution` / executor_enter=null，未执行held-title读取，不能归因QOL首府ID0。没有核心业务、日数或生产UI信用。Root只按真实映射关闭intro一次；后续pure diagnostic通用queue因原error非空拒绝、没有dispatch，未重发Start。

Root正常Quit Desktop一次，native于18:33:55.704776实际OS0/shutdown0/job0/tree_gone/full cleanup、全部库存[]；18:38唯一Lifecycle02 finish只收口不发game action，原root error及死后snapshot错误保留，完整runner仍 **RED**，18:38:37.718127结束、cleanup/thread=true。观察器已gone；keeper3667后[a66实际释放](C:/workspace/ck3-upgrade-20261006/rmtm-core-r1-context-failure-original-root-01/actual-a66-screen-release-02.json)CAS3668/done/resources[]，本机02:41:36。[最终闭合薄证据](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/actual-final-closed-thin-receipt.json)2972B、SHA `5dad6d1697c6ce668fe2d6d22d03c07eccbb2857472381e690b6d5ee75f9a97f`；[首次准入](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/before-first-root-admission-thin-receipt.json)与[查询原始边界](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/rootquery-and-lifecycle-thin-receipt.json)保全，不把清场成功改成业务通过。

未来hostguard SHA `81a1a36dba7845543dfc9c7131d611879aa40078e92154aa6fbce35787aa81d8` 的16项离线边界PASS仅SOURCE/PURE；operation06 freeze `ced5ba341cfe3f8003d6f8f10bd249951059fbfadd619e7ab3a5c18cab946150` 为未分配/未运行，保留原full DTO、资格binder、单Start、400秒deadline和UNKNOWN不重试，不称actual修复。完整路径与新旧边界见[重整河山追加](reclaim-the-motherland-ck3-1.20.0.3-readiness-2026-10-05.md#2026-10-06-r0001-实际失败正常退出与下一候选边界)。0.4.1仍未发布，正式完成产品数不增加。

## 本机体验优化 R13/a67 当前失败增量（2026-10-06）

R13本轮Source08 diagnostic DLL `b1fe516b8168eca65a260882d560e25e9df22a030e2de626bcd554b310c7e017` 实际启动，生产27文件/原threshold不变；首map19:11:11、宋34422为19:11:56，intro约19:16才由Root关闭。资格已于UTC19:15:55.626788发生 `actual QOL scope actor did not crossbind and stabilize before deadline` TimeoutError，binding缺失、rows0；whole-query/newtype_tag与D1/D5都未执行，不授业务信用。[实际薄报告004](C:/workspace/ck3-upgrade-20261006/xqol-r13-thin-report-observer-agent-01/report-state-004.json)保留。

Root真实WM_CLOSE/noautosave/Quit Desktop后，native于19:18:59.930959以process_exit OS0/shutdown0结束，job0/tree_gone/full cleanup、库存[]、watchdog22492 absent；原runner error不改。a67屏幕CAS本次仍待Root真实回执，未预写释放。R14只另建冷run、保持原资格门禁和400秒deadline，不延长期限；尚不增加通过或发布数。限定及session证据见[防御维护追加](xqol-1.20.0.3-defense-maintenance-2026-10-05.md#2026-10-06-r13a67-当前实际资格失败)。

R13补充分层：现存日志scope3各1/FAIL0、宋34422/`han_8052` proof存在，截止前crossbind仍未完成，binding=null/initial rows0；独立完整原wire扫描root query/result/trace各0。[9028B非EOF失败回执](C:/workspace/ck3-upgrade-20261006/xqol-r13-thin-report-observer-agent-01/FAILURE_NON_EOF_01.json)保留该边界，不能写scope不存在或仅以rows0推断没有原生查询。

R13后续实际收口：runner UTC19:24:40.359928为RED、原Timeout保留，cleanup/thread=true，唯一finish_hold仍因死后snapshot失败；thin/raw/harness gone，observer3672/session62510实际exit0。[3144B最终闭合](C:/workspace/ck3-upgrade-20261006/xqol-r13-thin-report-observer-agent-01/ACTUAL_NATIVE_HARNESS_OBSERVER_CLOSEOUT_02.json) SHA `82501663bc080c3861a59b2d1dcc6092721fc51771af1b971adce14c44db08bc`。keeper3688/thread=true/exit0后，[a67实际CAS](C:/workspace/ck3-upgrade-20261006/xqol-cold13-close-current-original-root-01/actual-a67-screen-release-01.json)3689/done/resources[]于UTC19:25:31.764299完成；此前待释放措辞为历史记录。R14现已唯一启动harness19988，不写诊断、D1/D5或业务通过。

## 本机体验优化 R14/a68 实际限定结果（2026-10-06）

R14资格UTC19:34:40.278299完成、initial2+diag4共6rows全OK；Source08 request `step-112-3221d07e7ddb`/PID20452/gen1/rev4/D0/queryseq1实际title16850/index4/held9of9/capital0，getter completed/nonnull=true、tag读取成功 `0x4E756C6C` Null/stock no-province=true，whole-root仍unavailable。[40905B非EOF原trace](C:/workspace/ck3-upgrade-20261006/xqol-r14-actual-native-root-trace-attribution-agent-01/ACTUAL_R14_INITIAL_ROOT_TRACE_NON_EOF_01.json) SHA `1e197f21a9d26ec18550e78ec19600551d16e496928170d83b76a0b0ecdbd189`，只证明此观察范围。

原hold20:04:45.968318自动闭合harness GREEN/error=null/cleanup-thread=true，但native stop/processcode=null/shutdowncode1，不记正常OS0或product PASS。Root22:17:36实际D0 review后controller在新增control前拒绝 `No active clean hold`，D1/D5未执行、review不可供新场复用；raw/thin均实际exit0且全部game/harness/watchers gone，keeper3864后[a68实际CAS](C:/workspace/ck3-upgrade-20261006/xqol-cold14-firstmap-current-original-root-01/actual-a68-screen-release-01.json)3865/done/resources[]于UTC22:25:05.454799完成。title/getter语义待源码核查，未增加修复、业务或发布信用；此前R13及失败历史保留。

R14[最终EOF薄收据](C:/workspace/ck3-upgrade-20261006/xqol-r14-thin-report-observer-agent-01/FINAL_EOF_THIN_01.json)6919B、SHA `0bd551826d92b17eb56df362473d5b849c0c35d373050cdcda9ec4bc7068b56f`：原必需标记仅4/23，三FAIL族与两reject各0，真实root query/result/trace各1；engine error.log EOF实际17415B，归因仍未知，不能写0或产品通过。
