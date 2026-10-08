# CK3 mod升级提速与公共验收入口（2026-10-08）

后续普通版本迁移的工程目标是正常数小时完成，尚无实测耗时或完成ETA承诺；新引擎结构、ABI变化及核心逆向另计。提速来自集中适配、减少重复启动和自动连续消费，不改变各产品发布前源码业务合同。当前批次正式6/10（60%）。

MCP、native bridge、服务、状态/事件读取及启动/退出管理已经是共享底座。各mod独立的是fixture、business case data、adapter及正式构建；冻结版本是当次可复现证据。成本来自尚未集中覆盖的实际capability缺口、consumer不同历史snapshot及人工GUI/多轮冷启动。**永久规则：所有未来mod acceptance从[tools/ck3_mod_acceptance.py](../tools/ck3_mod_acceptance.py)公共入口选一份common runtime manifest；产品不选择或复制host/source/native版本，公共问题在共享层修一次。**旧冻结永久保留，新run消费共同绑定的当前版本。

本轮实际例子：[QOL R31](C:/workspace/ck3-upgrade-20261007/qol12004-continuous-prepare-01/R31-D5-precise-pre-submission-cause39-01/R31-D5-PRE-SUBMISSION-EXCEPTION-AND-JOURNAL-FACTS-39-01.json)D1–D4日推进成功，D5提交前revision expected21/current22不匹配，在request sequence增加/请求创建前异常，不能算D5业务已执行；[TED R11](C:/workspace/ck3-upgrade-20261007/ted-r0011-camera-binding-red-readonly-resource-01/ROOT-TED-R0011-A117-MINIMAL-CLOSED-CARD-40.md)相机缺少合法`binding.episode_run_id`，native dispatch前被拒；[RMTM R12](reclaim-the-motherland-effective-single-heir-2026-10-08.md)的完整物理own0与同holder realm single-heir TRUE是合法effective baseline，旧own-member断言误判。三者分别涉及共享提交边界、consumer绑定和fixture语义；旧RED/ANDFAIL保留，源修复或静态合格不代替实际验收。

按以下顺序落地，复用现有底座和工具：

1. **本轮先解真实阻点。** 集中完成提交前revision消费、普通saved-scene完整binding与有效继承法联合断言，让原MCP业务链连续执行。typed读取提供状态/事件真值，合同要求的GUI亲审保留；TED holder/休战尾验不跳过。失败只修实际阻点，保留原场和原预算；无变化输入复用适用回执，符合既有热修条件的Python修复保持同一受管进程，不盲重播已提交动作。
2. **公共入口统一版本与编排。** 产品身份/build入口沿用[workshop/products.json](../workshop/products.json)；验收case、adapter、required MCP tools与预算已接入[tools/ck3_mod_acceptance_products.json](../tools/ck3_mod_acceptance_products.json)。原版diff到产品影响路径的映射继续施工。共同manifest的一次必要既有capability实机qualification供各consumer复用，不按mod重复whole build/full matrix；产品本身业务要求仍执行。CK3现场串行，其他准备并行。记录各phase实际elapsed，GUI-only真实业务单独标明已验/未验；导航ACK、host GREEN、正常退出或plan不能代替业务PASS。
3. **下次升级由原版diff安排重跑。** 集中适配共享native/runtime，再把原版脚本/数据及实际ABI变化映射到产品依赖，选择需重跑的既有检查和路径；只复用输入、版本和生产路径适用的证据，不把旧build实机PASS外推新build。兼容迁移、无关功能和宣传截图分开安排，各自满足原交付要求。不删除原RMTM 36 families/day14 cap、真实死亡继承/忠臣/九席合同，也不新增平台、门禁或理论审计。

当前公共CLI及产品adapter/data已接入代码树，registry覆盖14产品/19 cases，17个source-ready、2个blocked；代码接入完成不授14产品LIVE PASS；首次统一TED R13/a121已实际运行，typed/GUI取得本场信用，但共同自动闭场未通过。此前14产品/8优先case的plan消费作为准备历史保留。共享host/源码已收敛，Source6 delta/index与native已冻结；冻结及plan不等于common实际qualification。[RMTM R13/a120闭场43](C:/workspace/ck3-upgrade-20261008/rmtm-r0013-qualified-business-unfinished-readonly-resource-01/ROOT-RMTM-R0013-A120-MINIMAL-CLOSED-CARD-43.md)的D3 effective_single_heir资格及D2–D4日推进成立，原D1停步/ACK保留；六部/预算、C3–C6、真实死亡/post-law/full36未验，source/business=false。正常GUI/独立OS0/native0/cleanup、keeper0/CAS6391 done只授闭场。旧14天case未在原TTL内完成全验收；后续拟在原producer 10..30准入内显式选10，day14 cap/36合同保持，这是未来配置，不追认旧场或承诺PASS。

发布后缓存验收遵守[永久两项政策](workshop-cache-acceptance.md)：实际Steam下载的已发布cache文件exact match正式树，CK3确实从该cache路径mounted/loaded目标产品；不重跑fixture、事件、选项、特质、cooldown或其他业务。发布前源码业务、Notes/changelog及原发布交付不变。统一消费已接入，首次实际qualification及各产品业务结果仍须如实记录；依赖映射与diff驱动继续施工，不把代码接入写成已提速的实测事实。

## 当前公共CLI与本机共同版本

当前`--help`实际提供`plan / prepare / allocate / preflight / run / verify`六个模式，所有模式共用`--runtime / --products / --product / --case`。本机[local映射](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/runtime.local-entry-bound09.json)选择唯一[FINAL08 manifest](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/SHARED-RUNTIME-MANIFEST-FINAL-08.json)，后者绑定shared Source07/index、canonical host与native DLL/injector；local文件只提供本机Python、游戏/userdir/artifact根及原launcher/queue/allocator路径。换机器统一绑定本机local路径，产品adapter不传host/source/native/host_args，不复制一套运行时。旧runner和冻结只保留原证据及底层实现。

上述六个模式是未来新 mod run 的唯一操作路由。旧 `run_acceptance.py`、`run_vivhite_acceptance.py`、terminal/product runner 及其历史命令只供只读证据、library 与原业务断言复用，不直接作为新启动入口；旧冻结不被改写。产品 builder、静态检查和不启动游戏的原 preflight 继续保留，不能凭这些结果授实机资格。公共 local 映射始终指向当次唯一全局 manifest，不按产品另选 host/source/native。`de-jure-conquest`、`change-holding-types`、`li-yu-dao` 的 basic-load case 只授加载边界，其原玩家功能合同仍待独立业务证据。


从仓库根的`cmd.exe`执行，以下只读例子选择当前真实TED case：

```text
tools/.venv/Scripts/python.exe -B tools/ck3_mod_acceptance.py plan --runtime C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/runtime.local-entry-bound09.json --products tools/ck3_mod_acceptance_products.json --product tributary-expansion-directives --case production_ui
```

后续模式使用相同四项选择参数，按下表替换`plan`并追加参数；尖括号是当次真实路径/新编号占位，不是已有attempt的重跑命令。

| 模式 | 附加参数与实际职责 |
| --- | --- |
| `plan` | 展示共同manifest、case与host argv；`NOT_RUN / NOT_ASSESSED`，不启动游戏。 |
| `prepare` | `--case-inputs <本次输入JSON> --prepare-output <未用过的外置目录>`；adapter准备fixture/saved-scene输入，生成`prepared-case.json`，此时未分配/未启动。 |
| `allocate` | `--prepared-case <prepared-case.json> --attempt a<新序号> --keeper-output <新目录> --previous-live <上一实际闭场live> --previous-keeper <原keeper目录> --previous-release <原CAS回执>`；存在中间screen epoch时加`--latest-screen-release <最新实际释放回执>`。分配run ID/冻结argv/登记现场并启动原keeper，输出`ready-context.json`；该进程保留keeper HANDLE等待其真实退出，此时不启动CK3。 |
| `preflight` | `--prepared-case <prepared-case.json>`，分配后再带`--run-context <当次context>`；读取本次pin/预算/能力及输入绑定，exit0不授实机资格。 |
| `run` | `--prepared-case <prepared-case.json> --run-context <当前已亲审离线/nonce并完整绑定的context>`；调用原reviewed launcher、shared host及产品adapter连续业务/原正常闭场。仅READY或launcher0不授产品PASS。 |
| `verify` | `--prepared-case <prepared-case.json> --run-context <同一实际context>`；消费该场adapter、GUI和normal-close结果，case边界与business分别判定；不启动/重跑业务，`product_release_pass`仍为false。 |

2026-10-08首次统一TED R13/a121已完成实际运行：[prepare](C:/workspace/ck3-upgrade-20261008/ted-save25-first-unified-prepare-01/prepared-case.json)的正式16文件exact，preflight exit0；同一公共CLI只allocate一次，CAS6396/register→keeper READY实测1.416秒，恢复真实saved scene约4分30秒，6条typed rows PASS。Root亲审天德县属于夏realm，以及A→D夏·嵬名两岔停战至1071.9.17，两项GUI尾验取得本场信用；不把局部耗时当完整迁移耗时，也不授其他产品PASS。

正常Quit的独立retained OS0/native0及cleanup/thread TRUE成立，但共同client等待host finally才会产生的字段，形成闭场循环等待；Root严格复核原场Event后仅一次finish_hold救援，原run exit2、verify进程exit0但case_acceptance_pass=false/normal_close=NULL保留，正常出口未自动通过。[实际闭场47](C:/workspace/ck3-upgrade-20261008/ted-unified-a121-client-closure-resource-01/ROOT-TED-R0013-A121-COMMON-EXIT-FAILURE-RESCUED-CLOSED-47.md)绑定keeper实际exit0→CAS6461 done/resources[]；原typed/GUI与正常退出事实不被该公共缺口抹除，首次统一整链也不追认PASS。共同done Event消费修复已进入Source03；自动正常出口仍需实际验证，不另造产品host。已消费输入/state/allocation不重放，原失败/历史冻结保留，正式仍6/10（60%）。

## Source03共同版本、无CK3检查与R14实际边界（历史）

R14/a122当时全局为Source03/host `cd7561f9…`、FINAL04 manifest `91197f38…`、local bound05 `96164…`；当时CLI选用bound05；当前示例已改为bound06。R13/a121所用Source02/FINAL03/bound04保留原冻结历史。产品仍只消费公共版本，不能分叉独立host/source/DLL。

既有无CK3检查为[entry 10项](../tools/test_ck3_mod_acceptance.py)、[adapter 9项](../tools/test_ck3_mod_acceptance_adapters.py)、[completion 3项](../tools/test_ck3_mod_acceptance_completion.py)：覆盖全部14产品/全部case同host/source/DLL，product与case两层都拒绝8种override（host/source_root/source_index/native/dll/injector/engine/host_args），真实`managed_session_done` Event与原native0/完整cleanup联合判定，[portable资料](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/ROOT-PORTABLE-ADAPTER-TESTS-REVIEW08.md)，以及verify FALSE/null/非严格true返回exit2。本机source guard 10、adapter 9实际exit0，completion 3实际PASS复用；这些既有检查可作为无Steam/无CK3 CI门禁，不授业务PASS。后继新HEAD官方CI终态按实际回执另记，本文未重跑测试/构建或矩阵。

TED [R14/a122闭场48](C:/workspace/ck3-upgrade-20261008/ted-unified-a122-d1-failed-readonly-resource-01/ROOT-TED-R0014-A122-D1-SHARED-PAUSE-FAILURE-CLOSED-48.md)保留actual startup fixture资格及D0 typed PASS；已提交的首日`case-natural-day-0001`因共同pause读回丢失complete same-owner frame失败，不重播，未到production GUI。host于11:31:23.237773 UTC RED/thread/cleanup闭场，Source03真实done Event TRUE仅证明生命周期结束；原retained PID24956/ctime1791458801.1143658实际exit1、normal ROOT/native0 proof均NULL，未授正常Quit/normal0。共同run exit2、keeper80379实际exit0→CAS6474 done/resources[]保留；`normal-quit-awaiting`早值NULL不证明无host error。共同pause修复仍由shared owner施工，正式仍6/10（60%），不授14产品PASS，不重复缓存业务。

## Source04当时操作指针与R15、CI实证（历史）

R15当时全局统一选[Source04/FINAL05/bound06消费卡](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/ROOT-SHARED-SOURCE04-MANIFEST05-BOUND06-CONSUME-01.md)：host `9e5e0ca4…`、FINAL05 `b6b64d76…`、bound06 `bbc16743…`；旧Source03/FINAL04/bound05与R14失败原证据保持。R15/a123原D1单次stepok TRUE（12:04:54.825233 UTC），但client随后报`ValueError: Original actual day interval/event boundary not proved`，在production GUI前停止；不得把stepok外推为完整日间隔/事件边界或业务PASS，不重播补证。

[R15最终薄卡50](C:/workspace/ck3-upgrade-20261008/ted-unified-a123-day-proof-failed-readonly-resource-01/ROOT-TED-R0015-A123-SHORT-DAY-FAIL-NORMAL0-CLOSED-50.md)确认Root于12:11 UTC正常GUI Quit后，共同自动normal-close已实际qualified：原PID25528/ctime1791460808.2981422 retained OS0/actual_retained_os0 TRUE，原managed_session_done TRUE、native process_exit0及cleanup_proven/treegone TRUE；client自己仅一次`acceptance-normal-exit-finish-hold`于12:11:47.886758 UTC ok TRUE，host于12:11:49.191553 UTC GREEN/thread/cleanup TRUE/error NULL。该实证只关闭自动正常出口缺口；原run74639实际exit2仍是业务day-interval失败，verify实际exit2仅因业务前停未生成`ted-verdict-input.json`，业务/GUI保持未验，不追认case PASS。keeper96664实际exit0/last6494/thread TRUE/failure NULL→CAS6495 done/resources[]；正式仍6/10（60%）。

提交`d705eb32122ed2450cff6d6de0387f14ae457024`的[精确官方CI run 37772066872](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37772066872)在step31真实报`ModuleNotFoundError: No module named 'psutil'`，属于mocked allocator测试的CI依赖，不是host实机错误，该失败保留。CI修复patch已由Root实际apply；本机adapter9 PASS 0.786s、completion3 PASS 1.361s、pause3 PASS 0.292s复用，不重跑旧测试/矩阵或下载原始CI。后继exact SHA官方CI终态仍待实际回执；公共底座与源码业务合同、全部未来产品公共入口及缓存永久两项规则保持，不授release信用。

## Source05统一正常日结果与下一场

R15小原件证实实际完整暂停帧从53144328推进到53144352，但普通host结果未输出客户端及QOL共同要求的`requested_interval_complete`。[中央修复](C:/workspace/ck3-upgrade-20261008/r15-campaign-normal-day-result-schema-01/ROOT-CAMPAIGN-NORMAL-DAY-RESULT-CENTRAL-SCHEMA-FIX-FINAL-02.md)仅在既有`.4 native_campaign`完整暂停、同owner及达到目标日期门禁之后，输出`requested_interval_complete=True / event_boundary=None`。原legacy、one-life事件分支、客户端及产品断言不变；三个真实方法回归一次PASS，旧R15 FAILED不补字段、不追认PASS。

[Source05实际封存](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/ROOT-SHARED-SOURCE05-MANIFEST06-BOUND07-PREPARED-CONSUME-01.md)exit0、10.26秒，仅换一个host并继承6903来源行；host `a460500d…`、FINAL06 `91c97887…`、bound07 `0d518e32…`，native `ed510…`及原预算、launcher、lease保持。未运行的QOL/RMTM仅另建prepared元数据更换顶层manifest pin，其他对象一次核对相同，不重prepare或重hash产品文件。QOL下一场已实际allocate为R32/a124，register6498→keeper READY6499约1.53秒，preflight exit0；尚未授业务或发布PASS。RMTM自然事件中断及真实继承控制流另由共享owner补齐，不能制造one-life anchor或从时间差推死亡结果。

## R32实际结果与公共事件、旧入口整改

R32/a124 使用 Source05 实际取得原防御23项/禁止5项和final6本场信用，五个实际24小时日推进全部通过，日期从53144328到53144448。Root随后经正常GUI切换至原赵曙角色34422，真实native root读回celestial government、independent及持有hegemony14022；尚未提交Root检查点时，原正常Quit预留期限到达，case错误为 `TimeoutError: Original normal Quit reserve reached; pending Root phase remains GAP`。run96522实际exit2，normal-close-qualified FALSE；host于13:15:09 UTC结束、done/thread/cleanup TRUE、进程树消失只授资源收尾，不授正常GUI/native OS0或整场PASS。keeper15899实际exit0→CAS6549 done/resources[]。原失败与已经消费的state保留，不将它标为unused。

迁移适配器原 `primary_title.key=e_song` 断言既不符合normalized DTO，也不符合原 `has_title=h_china` 合同。原11候选提出GUI debug tooltip补齐key/fullID，但共同runtime的debug_mode=False且拒绝debug启动，该候选缺少可执行的取证路径，Root已撤回未提交的11补丁；不能给下一场新增不可取得的门禁。现由共享title-holder补齐只读stable key，后续adapter联合实际key、holder、owned partition、角色/日期/政府/独立性及同owner完整暂停帧核对原持有关系，不要求该title为primary、不猜ID或制造DTO key。补齐与新场业务仍待完成，R32失败不追认PASS。

公共host现已增加显式 `native_campaign` 自然事件边界分支；客户端传递原 `allow_event_boundary` / `allow_actor_change`，事件查询使用当前实际正整数instance ID。提前事件不计完成一天，不选择事件选项，不从角色变化推死亡或继承。原one-life episode合同和默认正常日路径保持；八项实际host方法回归通过。十四个旧直接实机main入口现于分配/启动前返回2，引导公共六模式；只读preflight、prepare、fixture emitter及既有library断言仍保留。产品不能另选一份host处理同一公共缺口。

精确提交 `e287f619c74e36880e9c1b12b3afc837773a13b6` 的[官方CI 37777691611](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37777691611)和[线性历史CI 37777691555](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37777691555)均已实际成功；该结论不外推到后续提交。[并行磁盘清理](ck3-native-ai/disk-cleanup-2026-10-08.md)恢复约13.29 GB可用空间，验收原始证据保留。正式发布仍6/10。

[Source06/FINAL07/bound08实际封存](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/ROOT-SHARED-SOURCE06-MANIFEST07-BOUND08-RMTM-CONSUME-01.md)exit0、7.206秒，仅替换公共host为208994 B、SHA `1ebdd6a2f136543ba1580054bad4b43129cdde214c3f602f17c241a4f84d381e`并继承6903来源行，native `ed510…`、原预算/launcher/lease保持，未重建native或全树重哈。唯一FINAL07 SHA `693002ea…`、bound08 `5624ed2a…`；未运行的RMTM只创建manifest pin变化的prepared sibling，其他深字段一次exact equality TRUE。R32已消费的QOL未创建unused sibling；产品adapter和公共client仍作为当次主仓输入绑定。

## Source07：共同title key与启动报告写入

[Source07/FINAL08/bound09实际消费卡](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/ROOT-SHARED-SOURCE07-MANIFEST08-BOUND09-RMTM-CONSUME-01.md)成为后续全部产品唯一共同版本。新增title-holder只读key沿用既有当前`.4` title模板getter，联合同Title/fullID与两次一致读取；base holder可用性和key可用性分别保留，key不可读不编造值。`h_`只允许显式point reader，center-map既有b/c/d/k/e路由保持。当前`.4` normalizer要求完整四个新增字段；旧`.3`可省略整组，不接受部分字段。QOL adapter按原`has_title=h_china`核实际key、holder及owned partition，不要求primary=e_song。

实际增量构建97 TU、复用473对象，完整570对象DLL链接exit0、159.029秒；新DLL9001472 B、SHA `d1d4dd3f10f545e3cd3f05ae99a44f157848bff13ff12bfc6315d90418ff7d04`。唯一成功的定向CMake测试只编译新fixture一TU，输出9个实际生产代码synthetic packet，真实normalizer23检查通过；前05/06/07链接失败保留，没有执行fixture或游戏。该声明的测试EXE已取得管理员Defender精确实际读回。六项[portable normalizer回归](../tools/test_title_holder_stable_key_contract.py)与四项[QOL原持有关系回归](../tools/test_ck3_mod_acceptance_song_holding.py)实际通过，不代替新增key实机读取。

共同host211316 B、SHA `3dfecfff0bf12548801c4a9fa104bb4f9e7e16131fb3cf0b2865fdb7bd65d487`将每个启动poll的完整观察行append到JSONL；只有普通成功/等待poll把全报告checkpoint限为最多每5秒一次，错误、准入、ready、phase、managed done和最终报告仍即时写入，原最终完整观察列表保留。poll频率、读取与预算不变。六项[真实writer/sidecar回归](../tools/test_ck3_mod_acceptance_poll_reporting.py)及三项completion检查通过；尚无CK3启动前后速度比实测。

全局封存实际exit0、2.951秒，6904来源行相对Source06只有9项delta；6903 native-input未改行用hardlink继承，新host独立写入、nlink1。旧host/index/native输入不改写，无全树重hash、无第二生产编译或旧矩阵重跑。RMTM未用prepared仅换顶层manifest pin，其余深字段exact相同；QOL另行公共prepare原unused13输入，已用R32不重放。

TED下一场R16/a125已公共preflight exit0、单次allocate，register6550→keeper6551 READY约1.540秒。首次Steam recovery因前景磁盘旧提示无法SetFocus而失败，原launcher在CK3启动前拒绝；关闭已无实际空间阻点的提示后，新的窗口位移与双nonce原图经Root亲审Steam离线，14:21:17 UTC实际启动Source07。该场production UI和正常退出尚待结果；原R15失败与其独立normal0信用保持。
