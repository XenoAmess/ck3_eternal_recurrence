# 本机 CK3 1.20.0.2 兼容工作交接

交接日期：2026-10-02，北京时间。仓库：`C:/workspace/ck3_eternal_recurrence`。

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

外置根简称 `B = C:/workspace/ck3-upgrade-20261001`，Python 为本仓库 `tools/.venv/Scripts/python.exe`，版本 3.14.7，命令使用 `-X utf8`。依赖已经安装；切换 checkout/worktree 后必须显式复核解释器与依赖，不能静默回落裸 Python。本项目禁止 PowerShell。

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
