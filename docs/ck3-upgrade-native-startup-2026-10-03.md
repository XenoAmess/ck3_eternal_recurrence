# 兼容接续：本机 `.3` 原生启动 R0002–R0005

本包接续 [2026-10-03 接手记录](ck3-upgrade-resume-2026-10-03.md)，只记录真实准备与首次启动。主/白绮七 cell 仍为 `.3` 实机 **0/7**；AUB 没有到地图、政策菜单或自动建造循环。

## 冻结输入

复用已有 `.3` 原生迁移源 `f4e1bb33fd1c31820b6d2fe29be8185d51663703`，冻结树位于 `C:/workspace/ck3_uuii/_runtime/upstream-migration-20261003-root-a01/native-wake-sdk-dependency-root-a01/source`。只启用已有的 1066 bookmark model、selected-character Start 和 Robert target 三个构建开关，没有修改该源树。新构建目录为 `C:/workspace/ck3-upgrade-20261003/courtier-agent-01/native-robert-frontend-build-01`：404/404 构建成功，model test 通过；registry test 因既有 strict-combat mapping 失败，原 RED 保留，不能称全 registry 通过。

DLL 为 4,539,392 bytes，SHA-256 `561bfe3fd38d20cbca750bcd3724ea1967f80e8c040f555e714eb13c6293ec9a`；injector 为 39,936 bytes，SHA-256 `740f7155ab3340b889baf51c0dc7bbe9f5cc6f8a0cdc52eb055a40ad4fef00cd`。本机游戏 EXE 仍为 `.3` / build 25652598 / SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

外置 harness 使用实际 MCP route/NewGame/selected Start，不用 OCR、键盘或鼠标导航。文件 `courtier-agent-01/run_ck3_12003_product_mcp_live.py` SHA `42cce1ef9fdbfad5c8e87144292f71821a8dceea16e37549338ebd3b2d662680`；实际输入在 run 的 `frozen-argv.json`。AUB 17 文件生产投影、descriptor-only 空 fixture、85 项原版默认规则的准备依据见 [AUB/TED 后续准备](ck3-1.20-aub-ted-log-continuation-2026-10-03.md)。

官方 singleton runtime fingerprint 调用缺少 CUDA/rfc3339-validator 依赖，保留 **ENVIRONMENT_RED**，没有生成指纹。此次使用已有的显式 `--fixture-profile` 隔离启动路径；文件/source/EXE/DLL 绑定不能替代 runtime fingerprint 或 native save state 指纹。

主/白绮另有六个可独立准备的 `.3` cell：main UI、Vivhite UI、两种双 mod 加载顺序、writer、no-heir。reader 必须等真实 writer，cold 必须等真实 Robert checkpoint。准备报告 `courtier-agent-01/remaining-courtier-cell-preparation-01/report.json` SHA `816db235cddb962e199fa7a3eaff7e22c9365a4ca6345af2e2a17738195caa76`；14 个实际挂载目录的 parser 证据逐字节绑定在 `courtier-parser-evidence-bound-01.json` SHA `312484bdc2eefc26aa6181590bfbaca208a806bae8f5e52a311ae625f24e238b`。未改文件复用原检查，仅 changed writer/no-heir fixture 新检查 5/5、6/6，通过且零 error。均不是实机通过。

## 当次离线与屏幕占用

屏幕 task `ck3-upgrade-screen-20261003-a01` 于 13:09 UTC 领取独占，keeper 固定 clean checkout `6440948e73490808f78977daa44fa672fa3bcb74`。原始桌面为 1920×1080，当前 desktop size 相同。恢复工具反复取得相同背景画面，背景时钟停在 19:19；没有据文件时间判断整幅桌面已恢复。

13:24 UTC 的新 attempt `steam-offline-a03` 确认 CK3/录制进程为零、唯一 owner 和实际 C 盘 bus。随后依据已有桌面恢复合同，临时原生 challenge 窗口产生两次不同 nonce。执行者直接审阅 `steam-challenge-a03/challenge-2.png`，读到 `0c538bf9675c`、当前 UTC 和同一原图内 Steam 的“离线模式”。PNG SHA `f6011f6b4d62ce0de3e0007851cf2fc127e08b38d1ef95ce14b6777523edb717`。这只证明新 challenge 像素及同图离线标识，未证明整幅背景实时；没有切 Steam 在线、重启 ToDesk 或坐标点击。

两次过期证据的启动前拒绝均发生在 Popen 前，没有启动 CK3；原 review 和命令失败保留。实际启动直接审阅后随即执行，收据在 run 的 `offline-visual-review-a02.json`（文件名保留当时操作，内容绑定 a03）。

## 真实运行结果

Run **`4-8e1c2f1861--auto-upgrade-buildings--R0002`**，执行目录 `C:/workspace/ck3-upgrade-20261003/live/4-8e1c2f1861--auto-upgrade-buildings--R0002`。13:24:43 UTC 建立 native 会话，实际 CK3 PID 14020；原生 DLL、hello、心跳、mailbox 与 MCP 已接通。初始 executor rejection/unavailable 随游戏加载过去，不视为 mod 失败。

13:26:11 UTC 首个可用 typed route 是 `bookmarks`。当前驱动只允许初始 `main_menu`，于是报告 **RED**；没有调用 NewGame 或 selected-character Start，没有开始战役。`native-report.json` SHA `48536131cf8b669cd9301247253b03011e233d3b69a85280ceedc38a90d1435c`，原始 MCP/native wire 和 stderr 全部保留。13:26:33 的 `loading-observation-01` 保存了当时日志，error.log 为零 bytes；这只是加载观察，不能写为完整 loader 门禁通过，更不能和旧 `.2` AUB93 条错误作单变量因果比较。

退出由受管会话进行 containment：`cleanup_ok=true`、最终 job active 0，CK3 exit code 1、清理前仍有一个活动游戏进程。故记录为清理完成，**不记正常游戏退出**。13:28 UTC 本机复核 CK3 为零，keeper 停止且 CAS release 成功，随后才更新 checkout。

后续诊断已定位两个具体驱动阻点：无 checkpoint 的 owned launch 固定 `-continuelastsave`，但 route=`bookmarks` 本身不足以证明可操作的实际 picker，需要 typed tree；`.3` adapter 的 hello 目前遗漏已启用 flags 对应的 bookmark model/selected Start capability，Python 会在缺 capability 时拒绝下一步。修复必须保持真实注册与条件一致，不能绕过缺失声明。后续使用新源/二进制、新 run 和新 userdir，旧 R0002 原样保留。

## 已采用的前端接线修复

`.3` descriptor 现在按已有 MODEL 和 SELECTED_START 开关分别发布 bookmark model、selected character 与 selected Start 的能力声明。默认开关未改变；没有新建这些底层动作或放宽 exact-build gate。`game_adapter_test` 的单一 `--frontend-private-capabilities-only` 模式核对真实 descriptor 与对应编译开关，CMake 向测试传播 MODEL 开关，并注册独立 CTest，避免为了此修复重跑已知 strict-combat registry RED。

外置新源 `courtier-agent-01/source-f4e-frontend-caps-01` 从原4552文件逐项验证复制，只有三文件接线补丁。13:43 UTC 新构建及聚焦 descriptor 测试通过，输出 model=1、selected_start=1；未取得 OFF 构建或实机结果。收据 `native-frontend-caps-on-attempt-01/result.json` 保全完整命令、stdio、freeze与产物。新 DLL SHA `34160bbf673097d0ac9944d2e8ff54e6c80b55dd47e339598d85be01e1d58f60`、injector SHA `831914e9e3ab03f03ffe8f78dab8a029b8b7a030fd2a01f1aa7145bbf1feeaee`；上一组二进制未覆盖。

既有永久入口 `ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py` 增加可选的 stock Robert 原生前端启动，不新增完整 `.3` 副本。它在实际 route/tree 保全后，才允许主菜单 NewGame；直接 bookmarks 另需显式 CLI 选项、完整且未截断的实际树、唯一 root/character_selection/start/pick-any 控件与当前可见性。最终仍由已有 typed Start 独立核对 stock Robert model、日期、政府及地图，树中有按钮本身不证明选中了 Robert。冷 checkpoint 与 SDK fixture 模式不使用这条新启动路径。

只读诊断选项保全 route/tree并有限 hold，禁止发出 Start，结果不计战役或产品验收。三个聚焦离线检查通过：已有 SDK error 路径、fixture episode queue，以及新 picker admission 的有效输入/截断/错误 scope/缺失 Start/重复 Start。已跑结果在 `frontend-tree-harness-v2-validation-01/report.json`，回归测试并入原测试文件；没有重复运行。当前主线 harness 与外置 v2 的文本归一化内容及 Python AST 相同，字节差仅为换行；实际 run仍各自绑定原始 bytes。

R0002 最终 state/live 的1950文件另保存于 `aub-empty-agent-02/r0002-closed-packet-01/closed-state-and-live.zip`，逐文件解包读回 SHA相同；原目录保留。新 profile04 准备于 `aub-empty-agent-02/native/profiles/aub-production-empty-fixture-profile-04`，preparation SHA `807771332e6b167e2072283eb40648003106e9270beb6e50218f8f603e80f138`，17+空1文件与85 defaults复用精确来源、未复用旧 runtime state。仍是准备状态。

## R0003：瞬态路由不能证明可操作窗口

新 run **`4-8e1c2f1861--auto-upgrade-buildings--R0003`** 使用上述 profile04 和[已完成的规则组合DLL](ck3-native-ai/frontend-game-rules-1.20.0.3-2026-10-03.md)，外置 v3 harness SHA `7a19371d8e9db3ef13f3d169cd6ee748a73f06b70effb0cdeac16d2eea24ee8f`。固定 clean checkout `57dee2e9072ba25aa03913f75f505210b2a4b6b1`，screen task `ck3-upgrade-screen-20261003-a02`。14:28:54 UTC 直接审阅新 challenge 原图中的 `bd716d1761fb` 与同图 Steam“离线模式”；PNG SHA `0ac3b89ab6ada22e73da450e715c23cbc2730dc7bdc1f0c159dae67834fc490a`。背景时钟仍停滞，证据范围仍只限 challenge 像素和同图离线标识，没有切在线或重启 ToDesk。

14:29 UTC 实际启动 CK3 PID18028。14:30:39 的首个 positive route=`bookmarks` 后，原生树返回 `scope_root_name=_root_`、`truncated=true`、512 widgets，Bookmarks/picker/Start 实际不可见；规则 query 为 `bookmarks_route_unavailable`，下一次 route 也不可用。Python opener 在派发原生打开命令前拒绝。故真实规则选项、规则 controller、NewGame、Apply、Start 均 **NOT_RUN**；这次不是原生 Apply 失败或产品脚本失败。最终 `native-report.json` SHA `6ed5394f31436923a6e49bfa7bf49b589d66a2b5a92ce24276bf5cec0bd40ff5`，61 次启动观察与全部 wire/stdios保留在新的 run 目录，旧 R0002未覆盖。

受管结束仍为 containment：exit1、清理前活动游戏1、最终0、cleanup=true；现有 runtime 的 `stop_tracked` 在 job 仍活动时执行 TerminateJobObject，没有正常 quit 尝试。不能把此结果记为正常退出或持久化 flush。14:49:39 UTC 再次核验 CK3=0，keeper thread退出、failure=null，按 last_sequence1711成功 CAS释放为1713，随后才修改主 checkout。

永久 harness 修复为 route→完整、可见且匹配 scope 的 tree→route，连续两次一致后才 ready；遇 unavailable、截断或不可见立即清零 streak。规则诊断另核对唯一、可见且 enabled 的 `game_rules_button`，不以固定等待时长证明 ready。每次失败 observation仍保存；等待或打开失败先保留有限诊断 hold，最终维持原 RED，不重发已派发动作。该 hold 的 `frontend_read_only` plan仅允许四个无参数只读 query，避免地图尚未建立时的 after_snapshot阻断维护；其他 plan合同不变。

新聚焦回归覆盖本次原始瞬态、不可见 root、streak清零与两次一致放行，PASS；旧 SDK/episode/tree测试未重复。报告 `courtier-agent-02/frontend-v4-focused-validation-01/report.json` SHA `05c12093a0257827b66f2cc358d27c26b7b89e697e6a876256f6779a3f863fe2`。外置 v4 final SHA `47c0f77e8a9ba10fb68d3a538402e9ba138c48a50b44608333b3aad9c2da92b5`；只改 Python 等待，不需新DLL。下一验证使用新的 profile/run，不能改写 R0003为通过。

## R0004：真实入口是主菜单

新 run **`4-8e1c2f1861--auto-upgrade-buildings--R0004`** 使用相同完成DLL、上述v4和新 profile05，preparation SHA `a5af09b7dd13d52a1178100068499e05327f56bbf4c6c6ccad825af99ee8169a`。profile仅从相同17生产文件、空fixture1文件、85规则纯输入构造，未复制profile04的运行缓存。原R0003的1949文件另存ZIP并逐项读回，SHA `a200fbc69b828b0530e5f3e20b6fe4f3d19d159078b852892fbefb06c4d53f1d`，原目录保留。

固定 clean source `2c28a7bec5235db0baa46fa4286fa09a0224664f`；screen task a03。当次14:58:42 UTC原图直接读到nonce `b79d1bc00c39`及同图Steam“离线模式”，PNG SHA `d07205e7682a315c9c3d209d91511fd46762f0b57b198cba794929788e8609df`，没有扩张冻结背景的新鲜度结论。14:58:59实际启动CK3 PID9636。

此次驱动保留加载瞬态后继续读取，最终稳定在 `main_menu`，实际 `mainmenu_panel_bottom` scope完整、未截断、246widgets，唯一 `new_game_button` 当前可见且enabled。原rules-only诊断要求Bookmarks且不允许NewGame，所以543次观察后超时；没有派发任何游戏输入。这个结果证明此前Bookmarks不是稳定初始入口，不能靠延长等待到达规则页。最终报告SHA `a4b30c27909e5a938b420c5771f0bf070a8643ba7fe173c3388e1eacba52ddb4`。

90秒hold中实际执行了四项 `frontend_read_only` 控制：route/tree/rules/pipe均返回ok，未触发地图after_snapshot。规则 query明确ready=false/`bookmarks_route_unavailable`，不记规则通过。15:05:31受管containment完成，exit1/job1→0，随后本机CK3=0；keeper最后1729、failure=null/thread退出，15:06:39 CAS释放1730。仍无正常退出、战役Start、地图或产品通过。

永久harness新增显式 `--frontend-rules-diagnostic-new-game`，仅与bootstrap+diagnostic-only+rules-diagnostic共用：从两次一致的真实主菜单调用一次已有typed NewGame，保全request-before-call；回调异常或未verified ACK均禁止重试；再等两次一致的Bookmarks tree，才打开/读取规则。默认rules诊断保持零NewGame；没有角色选择、Apply或Start。新单一聚焦测试覆盖默认零动作、显式一次动作及回调丢失不重试，CLI两路径与孤flag拒绝PASS，旧测试未重跑。外置v5 SHA `c78246a124b56188b45d898b791a5eeca6e5ea614fc9102ce252f3f02b985b72`，报告 `courtier-agent-02/frontend-v5-focused-validation-01/report.json`。下一新run才可验证该动作。

前端接线 `6e11ba8dd` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37128219251)、规则读取 `57dee2e90` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37129633661)、一致等待 `2c28a7bec` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37131442194)实际均success，不能替代上面的实机边界。

## R0005：NewGame完成，Bookmarks树触预算上限

新 run **`4-8e1c2f1861--auto-upgrade-buildings--R0005`** 使用相同DLL、新v5以及独立profile06；preparation SHA `b281a9d1b383ad2ffd9edcd0a925e8bc85f2cd291de040ec1d696bc0cfc79e28`。R0004原state/live另保全3819文件，ZIP逐项读回SHA相同，ZIP SHA `d4d7e84d50817a2ed407ff2bbc34d8cb150d5e831d327c640cbb9e1776c0d9ad`，旧目录未删除。profile06仍仅从17+空1+85纯输入构造，未导入运行缓存。

固定clean master `760ce9736c358b0d177f5e564680edf5f360af0c`；screen task a04。当次15:15:37 UTC直接读到nonce `d0fa8b132f12`和同图Steam“离线模式”，PNG SHA `30b84a833eaf7d1fbe82c3fd170a53b18a1effa6f8b4de942e4a9ae30dc53e4a`；仍无整幅冻结背景实时声明。实际CK3 PID18716/creation1791040556.1846728。

两次一致主菜单证明后，真实 `ck3_activate_frontend_new_game_v1` 调用一次，独立route读回Bookmarks，`status=verified`，不是只记录ACK。随后actual `frontend_bookmarks` root当前可见，`game_rules_button`与`pick_any_character_button`可见且enabled；树触512节点硬上限，`truncated=true`。驱动保留截断结果并拒绝ready；最终在规则打开之前超时。故 **NewGame原语有本机实际信用**，规则打开/controller值/角色选择/Apply/Start/产品仍NOT_RUN。最终报告SHA `713a58a4e4cde9625157f372fb1380e436e37a21b5c475c5fa0ec2bc292f1b0e`。

受管结束仍exit1/job1→0的containment，随后CK3零；keeper最后1747、failure=null/thread退出，15:26:06 CAS释放1748。下一候选核对原生树预算、Python上限、transport与栈占用，保留截断拒绝；这次512下界不证明总节点数。旧源/DLL/v5/R0005继续保留，不能在完成产物上修改预算。

显式诊断提交 `760ce9736` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37132350327)已实际success，仍与本机上述原语结果分开。

## R0006：完整书签树与实际规则选中值

10-04 00:06–00:09（Asia/Shanghai）运行 **`4-8e1c2f1861--auto-upgrade-buildings--R0006`**，execution `c4777f13-e33a-456c-97b6-3ab06c811b47`。clean master `f8d8793c4e608d028b6228daba860919bf381b43`，使用新2048预算组合DLL及独立profile07，preparation SHA `a04d90ff04f77945150afef6bcb72942155a34f211fadebed41e3a60d35aa4a8`。外置v7来自该master永久harness精确bytes，SHA `326907da1fd979b6f97292a7b14e8a03f8c283c2a0bd3dff5c21e556818b9bb3`，实际help exit0。DLL/injector及4567源freeze见[组合产物](ck3-native-ai/frontend-game-rules-1.20.0.3-2026-10-03.md#有界窗口树组合)；f4与master基底差异仍有表，未宣称全树相同。

新屏幕a05独占期间，16:06:29 UTC原始1920×1080图直接核对nonce `b77eb402342f`和同帧Steam“离线模式”，PNG SHA `8b89e5999403f0f5d88b318f8899a15721dfe62c4eb8d3da57c570486b1ae4cf`；冻结背景不作实时声明。CK3 PID16072/creation1791043611.0490716。一次typed NewGame获得独立Bookmarks route verified；两次一致actual `frontend_bookmarks`树 **1846行、truncated=false**。规则打开一次返回observed，再独立读取86对实际 `CJominiGameRulesGui.current_selections`，同PID16072/generation1的querySequence84→85→88。GUI选中值仍 `applied_settings_proven=false`。

85对prepared vanilla defaults全部匹配，没有缺失或不同；额外真实对为 `empire_faith_gate=empire_faith_gate_off`。它来自安装目录 `game/common/game_rules/01_empire_faith_gate_rules.txt`（200bytes，SHA `c04dc35c7d3cd4a0c414a1b61435d013d8601014d378cbed102e7b12733d64a9`），本次未改该文件，也不把86项总数称为85项vanilla快照。hold前三项typed只读route/tree/selected查询PASS，无地图after_snapshot；actual `game_rules`局部树 **283行、truncated=false**。

根执行者追加的第四项control误写工具名 `ck3_native_pipe_status`，被 `frontend_read_only` allowlist在派发前拒绝；因此全局原报告RED与该输入保留，不重发前三个PASS查询。此错误没有游戏输入；实际未调用Select、Apply、角色选择或Start，产品与七cell新增通过均为0。最终[原报告](C:/workspace/ck3-upgrade-20261003/live/4-8e1c2f1861--auto-upgrade-buildings--R0006/native-report.json) SHA `4f69cee7729ce20b16e9f5d74e683fdf6a6cb8e5c6df6d851f494de47df3f015`；[单独原语汇总](C:/workspace/ck3-upgrade-20261003/live/4-8e1c2f1861--auto-upgrade-buildings--R0006/primitive-summary.json)没有改写全局状态。

16:09:28 UTC受管containment exit1/job1→0，CK3零、harness消失；keeper最后1763、failure=null/thread退出，16:12:09 CAS释放1764。没有正常退出或教程落盘证明。下一独立run才执行显式规则选择/Apply、actual-instance比对与stock Robert Start。源码组合的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37135465150)实际success，仅属官方L0。

## R0007：实际规则提交与普通罗贝尔地图

10-04 00:24–00:30（Asia/Shanghai）运行 **`4-8e1c2f1861--auto-upgrade-buildings--R0007`**，execution `0dae232c-c2f7-463d-926c-330b02c3f6f1`，clean master `91194e193467550450ed36bc82e2345c3e19a3a0`。复用R0006完成的精确v7/DLL/injector，独立profile08 preparation SHA `757954b69e91f32cb5e5576e7497312cecdb1ea20725c6958c46cef0de6d66fe`。17生产+空1+85默认值纯输入重新构造，未复制runtime；原prepare wrapper收据循环缩进错误及独立全25文件读回复核均保留，不重跑准备。R0006原目录3048文件/132,824,104bytes双读SHA manifest已冻结，index SHA `5e6047ab194c29acc6043ccdc05221a71a2b994968c5f958236f96ac2f6e0b8d`；磁盘有限，未加冗余ZIP，原目录不清理。

当次原图直接核nonce `5179c8b46201`及Steam“离线模式”，PNG SHA `a69917fe122df0c5a3e90f24042c6d068cec18c76a44da5cc35d64e9f8f07e78`。CK3 PID15780/creation1791044660.7874236。显式pre-Start意图仅 `difficulty→normal_difficulty`，精确JSON SHA `4304dc9c69e7cef705f96ecd542c4bbb4cdd016c8e593b5941879f6d1373b198`。当次current实际已是normal，Select independent readback成功，但 `native_invoked=false/native_next_calls=0`，不记非零Next信用。一次原版Apply→Hide返回observed；另一次window query证明关闭，later **CGameRuleInstance.selected_settings** querySequence101/PID15780/generation1真实读取86对，与完整请求对完全一致，`applied_settings_proven=true`。GUI与ACK本身仍为false。阶段内snapshot_calls=0/actions_retried=false。

随后重新取得两次一致Bookmarks/picker证明；选择实际 `bm_group_1066/bm_1066_rags_to_riches/bookmark_rags_to_riches_duke_robert/feudal_government`，一次stock Start之后由snapshot和同revision campaign root证明map ready、paused。date_raw53144328；**当次native player_character_id=31254**，government feudal、primary title2230/duchy，local player1、revision3。旧计划固定29829不能外推至该build/mod组合；后续ROOT事件与settle必须从当次snapshot/root动态绑定，不能改硬编码为31254。当前root接口不含stable title key，未从numeric2230伪推d_calabria。

地图snapshot计划一项PASS，全局[报告](C:/workspace/ck3-upgrade-20261003/live/4-8e1c2f1861--auto-upgrade-buildings--R0007/native-report.json)实际GREEN，SHA `784ade90c4eccecd900d10f97dcdf89c83d41a3cda5933347f3bfa1779e22a23`；[原语汇总](C:/workspace/ck3-upgrade-20261003/live/4-8e1c2f1861--auto-upgrade-buildings--R0007/primitive-summary.json) SHA `f4224e26fc5b4a8d8deb515fc249d5df192991d33480cb77acfcc6e03d73d942`。该GREEN只覆盖上述启动原语，未启用AUB、未验策略/功能或任何主/白绮cell。真实error.log17,415bytes保留待单独分类，不能把harness GREEN写成无错误。

16:30:52 UTC完成；containment仍exit1/job1→0，CK3零/harness消失、keeper最后1780/failure=null/thread退出、CAS1781释放，未正常quit。只读源码复核确认settle的持久化判据直接read_bytes真实tutorial.txt、校验精确纪录token与连续两次同size/SHA；实际达到该判据后可用同bytes冷reader，无需虚构正常退出。目前该持久化仍未运行。现master已有独立 `.3` succession-modal provider，完成的f4组合没有采用且flag OFF；不是说所有当前master都没有该分支。

## 后续身份锚点修复

R0007实读原生ID差异已回链原版bookmark/history来源：罗贝尔的script/history ID为1128，native31254是当次runtime CharacterID；旧29829不属于可跨build固定身份。两个prepared fixture content无29829硬编码，错误在旧执行plan/reader helper。永久harness新增显式 `kind=episode_identity_anchor`：首次actual paused/alive one-life snapshot→现成campaign-root(expected同revision)→第二snapshot完整帧一致后，才保存唯一episode/PID/generation/实际角色锚点；禁止重绑。事件ROOT及settle来源引用该episode，死亡后不会改成继承人。仅显式 `expect` 的 `{"$ref":...}`启用动态比较，旧literal行为保持，没有引入不存在的 `$before` 语法。

最小两文件补丁SHA `33759c8cf69200df404c81c733bb0a2eda4206cf566acb87f8dc05f6966c387c`，四项新聚焦身份检查PASS，覆盖nativeID变化、错误ROOT/stale revision、PID/generation连续性、死亡后原episode及literal兼容。初稿测试patch换行导致apply-check RED保留，LF最终包装check PASS，检查未重跑。外置v8 SHA `5e3bfb5347dacf8285cee2349e2c3655e756075562ab53c57e5b55cdcdd10f5f`来自同字节永久harness；旧v7/10计划及完成native源/DLL均保持原样。新writer/noheir计划位于 `C:/workspace/ck3-upgrade-20261004/courtier-runtime-identity-agent-01/execution-plans-runtime-v8-01/`，尚未执行，实际窗口必须逐phase读回后才提交下一输入。
