# CK3 mod升级提速与公共验收入口（2026-10-08）

## 2026-10-10 Source14 已选定

后续未消费产品场唯一使用[Root选定mapping](C:/workspace/ck3-upgrade-20261010/root-source14-adoption-01/runtime.adopted-source14-native-fd1f-queue04-helper03-01.json)，12610B / SHA-256 `1eed7310a0c9314d54d9520d086ba1dce2f2d44d32988b91396c2bbf2f888f67`；共同manifest46927B / `bf326bb7005cd01ec482cbceaee02459dc2cf1400941b1dbe611c02905de60b2`，host234210B / `a20854002470e0f1b1c8f04d7889031560b28b9c89c510df950e72805697dea9`。实际增量物化exit0、7.620秒：6906文件copy2和sizecheck，6905行原SHA继承，只hash新host；native fd1f、queue04、helper03和全部能力合同不变。现有公共plan/Selection/hostCLI/prepare callable一次exit0、0.202秒，没有创建profile或启动游戏。旧Source13、manifest/prepared、R54/R55/R56结果保留，选择不授实机或产品PASS。

7个未消费prepared只创建新manifest-pin sibling；新ransom因observer fixture改变实际public prepare一次exit0、0.799秒，复用c46既有QA27且不重build。下一现场先admin→merit→ransom，UI/PAM−暂不消费待改信机制证据。正式仍7/10。

## 2026-10-10 公共任命采集器实际 hello 合同修正

R51 在发送候选池查询之前拒绝，原因是 collector 和旧测试使用不存在的 `hello.game_version/executable_sha256/bridge_pid`。实际 native HelloFrame 使用 `expected_ck3_version/expected_ck3_sha256/pid`。最终修复只修改公共 `frame_binding` 及真实 schema 测试构造，不改产品业务、host、DLL 或各场预算；所有产品仍走同一个公共 client。

`expected_*` 仅是描述信息，不能单独授实际构建资格。最终 gate 同时要求精确 .4 版本及 EXE SHA、`ck3_build_match is True`、`game_adapter_status=ready`、`game_adapter_id=ck3-1.20.0.4-msvc-x64`，并核 `hello.pid/connection_generation` 与 diagnostics 的正整数实际绑定一致。actor、paused/map-ready、pipe、native revision、date、完整分页、实际候选资格、分数和继任门槛保持。

采用的 [final04 patch](C:/workspace/ck3-upgrade-20261010/common-appointment-hello-schema-fix-02/COMMON-APPOINTMENT-REAL-HELLO-ONLY-FINAL04.patch) 为5878 B / SHA-256 `19a82fcd1516b74ba148e4c08f5d6d6f0f3e02c930ccb401d1a2040f0bf6478e`；公共 helper 为16061 B / `37caab92514512aa8be222984ac206ed30e5d407aaa7a8bd375cdd298a01a05b`。hello/frame/page 相关12项已在前一候选执行，最终04保留这些函数与测试字节；最终04另加载原 title-reference 测试验证2项，实际exit0/0.076855秒，[精确回执](C:/workspace/ck3-upgrade-20261010/common-appointment-hello-schema-fix-02/COMMON-APPOINTMENT-FINAL04-TITLE2-RECEIPT.json)为1485 B / `c8aba03e98dbfa862d94270aca27a9b68ddb8b2e2827b330aa25b5de9e39f5f7`。没有重复无关 template-click 回归，旧R51不追授PASS。

03候选曾误判 native serializer 无顶层 `title_id` 即为公开 MCP schema 缺失；完整追至 `BridgeService.query_title_holder_v1` 后确认 service 实际补齐该字段。因此03未采用，final04完整保留原 title-reference 的顶层及嵌套 ID 一致性校验与原测试。此记录保留纠正，不能从底层 serializer 单独推断公开工具合同。新的实际完整候选池及业务资格仍须在新 public prepare/run 中取得。

同轮 `liege_shared_ransom` 首次公共 prepare 在支持文件 pin 检查中实际退出2：补丁生产器以 `utf-8-sig` 解码新文件，丢掉原候选的3字节 BOM；隔离目录离线检查和 `git apply --check` 均不能证明实际应用后的字节相等。只恢复原 BOM 后，该 fixture 必须精确为24863 B / `56d4678f618632e58dd2a99e74124bc0a818c5350e6f2948ab833a0d2ded0b12`，合同 pin、全部业务正文与其他成功 prepared 不改。原失败保留于 [首次四场准备目录](C:/workspace/ck3-upgrade-20261010/resume-qol-02/public-prepare-four-01/)，后继只重新准备该未成功用例；不得盲目刷新 pin 消除错误。

后续普通版本迁移的工程目标是正常数小时完成，尚无实测耗时或完成ETA承诺；新引擎结构、ABI变化及核心逆向另计。提速来自集中适配、减少重复启动和自动连续消费，不改变各产品发布前源码业务合同。当前批次正式7/10（70%），TED永久发布记录已提交推送。

MCP、native bridge、服务、状态/事件读取及启动/退出管理已经是共享底座。各mod独立的是fixture、business case data、adapter及正式构建；冻结版本是当次可复现证据。成本来自尚未集中覆盖的实际capability缺口、consumer不同历史snapshot及人工GUI/多轮冷启动。**永久规则：所有未来mod acceptance从[tools/ck3_mod_acceptance.py](../tools/ck3_mod_acceptance.py)公共入口选一份common runtime manifest；产品不选择或复制host/source/native版本，公共问题在共享层修一次。**旧冻结永久保留，新run消费共同绑定的当前版本。

本轮实际例子：[QOL R31](C:/workspace/ck3-upgrade-20261007/qol12004-continuous-prepare-01/R31-D5-precise-pre-submission-cause39-01/R31-D5-PRE-SUBMISSION-EXCEPTION-AND-JOURNAL-FACTS-39-01.json)D1–D4日推进成功，D5提交前revision expected21/current22不匹配，在request sequence增加/请求创建前异常，不能算D5业务已执行；[TED R11](C:/workspace/ck3-upgrade-20261007/ted-r0011-camera-binding-red-readonly-resource-01/ROOT-TED-R0011-A117-MINIMAL-CLOSED-CARD-40.md)相机缺少合法`binding.episode_run_id`，native dispatch前被拒；[RMTM R12](reclaim-the-motherland-effective-single-heir-2026-10-08.md)的完整物理own0与同holder realm single-heir TRUE是合法effective baseline，旧own-member断言误判。三者分别涉及共享提交边界、consumer绑定和fixture语义；旧RED/ANDFAIL保留，源修复或静态合格不代替实际验收。

按以下顺序落地，复用现有底座和工具：

1. **本轮先解真实阻点。** 集中完成提交前revision消费、普通saved-scene完整binding与有效继承法联合断言，让原MCP业务链连续执行。typed读取提供状态/事件真值，合同要求的GUI亲审保留；TED holder/休战尾验不跳过。失败只修实际阻点，保留原场和原预算；无变化输入复用适用回执，符合既有热修条件的Python修复保持同一受管进程，不盲重播已提交动作。
2. **公共入口统一版本与编排。** 产品身份/build入口沿用[workshop/products.json](../workshop/products.json)；验收case、adapter、required MCP tools与预算已接入[tools/ck3_mod_acceptance_products.json](../tools/ck3_mod_acceptance_products.json)。原版diff到产品影响路径的映射继续施工。共同manifest的一次必要既有capability实机qualification供各consumer复用，不按mod重复whole build/full matrix；产品本身业务要求仍执行。CK3现场串行，其他准备并行。记录各phase实际elapsed，GUI-only真实业务单独标明已验/未验；导航ACK、host GREEN、正常退出或plan不能代替业务PASS。
3. **下次升级由原版diff安排重跑。** 集中适配共享native/runtime，再把原版脚本/数据及实际ABI变化映射到产品依赖，选择需重跑的既有检查和路径；只复用输入、版本和生产路径适用的证据，不把旧build实机PASS外推新build。兼容迁移、无关功能和宣传截图分开安排，各自满足原交付要求。不删除原RMTM 36 families/day14 cap、真实死亡继承/忠臣/九席合同，也不新增平台、门禁或理论审计。

当前公共CLI及产品adapter/data已接入代码树，registry覆盖14产品/19 cases，17个source-ready、2个blocked；代码接入完成不授14产品LIVE PASS；首次统一TED R13/a121已实际运行，typed/GUI取得本场信用，但共同自动闭场未通过。此前14产品/8优先case的plan消费作为准备历史保留。共享host/源码已收敛，Source6 delta/index与native已冻结；冻结及plan不等于common实际qualification。[RMTM R13/a120闭场43](C:/workspace/ck3-upgrade-20261008/rmtm-r0013-qualified-business-unfinished-readonly-resource-01/ROOT-RMTM-R0013-A120-MINIMAL-CLOSED-CARD-43.md)的D3 effective_single_heir资格及D2–D4日推进成立，原D1停步/ACK保留；六部/预算、C3–C6、真实死亡/post-law/full36未验，source/business=false。正常GUI/独立OS0/native0/cleanup、keeper0/CAS6391 done只授闭场。旧14天case未在原TTL内完成全验收；后续拟在原producer 10..30准入内显式选10，day14 cap/36合同保持，这是未来配置，不追认旧场或承诺PASS。

发布后缓存验收遵守[永久两项政策](workshop-cache-acceptance.md)：实际Steam下载的已发布cache文件exact match正式树，CK3确实从该cache路径mounted/loaded目标产品；不重跑fixture、事件、选项、特质、cooldown或其他业务。发布前源码业务、Notes/changelog及原发布交付不变。统一消费已接入，首次实际qualification及各产品业务结果仍须如实记录；依赖映射与diff驱动继续施工，不把代码接入写成已提速的实测事实。

## 当前公共CLI与本机共同版本

2026-10-10 07:54后继统一为[Source13/mapping05](C:/workspace/ck3-upgrade-20261010/root-source13-adoption-01/runtime.adopted-source13-native-fd1f-queue04-05.json)（10820B / `a5aecdf94d6e3dcf35f2462011ba6a743668605729627f6d272542cf8c460e91`），只变共同host；实际增量生产8.97秒/0，复用同fd1f/queue04/helper03。原unused prepared仅新manifestpin sibling，不重复准备；全部已用场和旧Source12保持。initial-plan失败使用原hold预算的自动链仍待新场，不以源码或纯测试授实机信用。

2026-10-10 06:18当前新场唯一[mapping04](C:/workspace/ck3-upgrade-20261010/root-source12-adoption-01/runtime.adopted-source12-native-fd1f-queue-04.json)，8636B / SHA256 `af28777aee895c2134398ca7497dbdc022ae848879259ace15c0d5623e7a682d`。同Source12 manifest/host/fd1f native及reviewer03 helper，仅control_queue换为已在R44首次实际投递失败收尾的不可变共同producer。旧03/frozen/reject保留；R44原case/run/verify仍失败，22:10:20 UTC原RED/error结束并CAS8000释放资源。四项-O producer检查及host实际失败生命周期共同证明可复用，不按产品重做；原完整业务验收仍各自执行。unused prepared不重做，未来allocation冻结新公共support SHA。

2026-10-10 05:45历史后继使用唯一[Source12/mapping03](C:/workspace/ck3-upgrade-20261010/root-source12-adoption-01/runtime.adopted-source12-native-fd1f-reviewer-03.json)，8076B / SHA256 `8251b000a720092fc8025494946a2d0f627df6f910d4876a6d6d02f6df8d2031`；共同manifest `5d00ca2fc93518151f5b9394a713dab8aae60d7e968abc80a23eabf3838e692a`，native `fd1f33ed63c452ba2fef3313a490db53fd8bfcfc567909c94b4966e1f4f7c5aa`。共同任命/title/PAM/truce和失败生命周期沿用同一份源码及DLL；native仅编20个变化TU、复用552个对象并单次链接。mapping03只换实际reviewer退出helper，既有同manifest prepared复用，不重prepare。

R42原hardgate与R43原head_identity均case qualified，whole business/release=false保持。R43首次实际验证mapping03自动正常Quit及外置v05连续公共run→verify→原keeper→CAS，host结束后约5秒释放资源，真实OS0/native0/thread/cleanup、allocator/keeper0俱全；[原始回执](C:/workspace/ck3-upgrade-20261010/qol-original-cells-runner-01/religion_head_identity--a143/POST-RUN-CLOSE-05.json)。v05只编排已有公共入口与close_attempt，不重实现host/业务/keeper/CAS。保留失败fastfinish和任命provider仍待各自真实qualification，不按产品重复共同成功证明。

以下bound13/bound12及后续Source05–10记录保留当时版本与失败，不作为当前新场选择。bound13曾增加公共自动正常退出三pins，公共真实reviewer合同见[公共操作接点](ck3-mod-acceptance-operator-quit.md)。

当前`--help`实际提供`plan / prepare / allocate / preflight / run / verify`六个模式，所有模式共用`--runtime / --products / --product / --case`。先前本机bound12使用[local映射](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/runtime.local-entry-bound12.json)和唯一[FINAL11 manifest](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/SHARED-RUNTIME-MANIFEST-FINAL-11.json)，绑定shared Source10/index、canonical host与原d1d4 native DLL/injector；local文件只提供本机Python、游戏/userdir/artifact根及原launcher/queue/allocator路径。换机器统一绑定本机local路径，产品adapter不传host/source/native/host_args，不复制一套运行时。已消费场次继续绑定各自旧冻结输入，旧runner和冻结保留原证据及底层实现。

上述六个模式是未来新 mod run 的唯一操作路由。旧 `run_acceptance.py`、`run_vivhite_acceptance.py`、terminal/product runner 及其历史命令只供只读证据、library 与原业务断言复用，不直接作为新启动入口；旧冻结不被改写。产品 builder、静态检查和不启动游戏的原 preflight 继续保留，不能凭这些结果授实机资格。公共 local 映射始终指向当次唯一全局 manifest，不按产品另选 host/source/native。`de-jure-conquest`、`change-holding-types`、`li-yu-dao` 的 basic-load case 只授加载边界，其原玩家功能合同仍待独立业务证据。


从仓库根的`cmd.exe`执行，以下只读例子选择当前真实TED case：

```text
tools/.venv/Scripts/python.exe -B tools/ck3_mod_acceptance.py plan --runtime C:/workspace/ck3-upgrade-20261010/root-source12-adoption-01/runtime.adopted-source12-native-fd1f-reviewer-03.json --products tools/ck3_mod_acceptance_products.json --product tributary-expansion-directives --case production_ui
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

[R16实际闭场54](C:/workspace/ck3-upgrade-20261008/ted-unified-a125-shared-pause-failure-01/ROOT-TED-R0016-A125-SHARED-PAUSE-FAILED-CLOSED-54.md)随后确认首日请求在初始pause-map `already_paused`之后、set-speed/resume之前，被严格same-owner successor的累计reject变化拒绝。原wire的native5含`stress_points=-1`，Python严格拒绝该帧；当次返回仍是旧native4/reject1，之后native6有效帧恢复。不能将旧帧授当前资格，也不能凭恢复补认原请求成功。host14:26:41 UTC RED/thread/cleanup TRUE，原retained实际OS1、normal-close-qualified FALSE；run55297 exit2、keeper32546 exit0→CAS6561 done/resources[]，无生产Send或AI结果信用。共同修复仅针对任何speed/resume提交前的重新准入，尚待实际采用；不改压力值、原postadvance门禁、deadline或R16失败记录。

精确新提交 `7f6f5e6d7bb738011b57725a41848dc9c24f53c5` 的[官方CI 37792399276](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37792399276)实际success（14:34:40 UTC），[线性历史CI 37792399305](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37792399305)实际success（14:26:47 UTC）。共同代码、portable测试与文档已fetch→rebase→普通push，未生成merge或force push。CI不代替该场实机结果或后续提交；正式仍6/10。

## Source08：提交前有效暂停帧重新准入

Root已采用[共享窄修复](C:/workspace/ck3-upgrade-20261008/shared-preaction-paused-readmission-host-01/ROOT-SHARED-PREACTION-PAUSED-READMISSION-FINAL-02.md)，在`.4 native_campaign`原事件分支、任何speed/resume提交之前，只允许已暂停ACK与单次counter0→1、精确已识别的下一native revision压力值拒绝元数据进入等待。旧cached帧不授资格；必须在原deadline内得到native revision实际超过拒绝帧的完整有效暂停帧，原owner、pipe、generation、actor、日期、speed与monotonic都保持。再次reject、其他拒绝原因、身份变化、超时或取消仍失败；不重发pause，不修改压力值，不改原strict successor及推进后门禁。六项[真实方法portable回归](../tools/test_ck3_mod_acceptance_preaction.py)一次candidate PASS，Root采用后永久路径六项PASS；已接入既有CI。

[唯一Source08/FINAL09/bound10封存](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/ROOT-SHARED-SOURCE08-MANIFEST09-BOUND10-UNUSED-CONSUME-01.md)实际exit0、3.564秒；host215332 B、SHA `24414e9b436b6334fc43019cff2754534afcc62a4cf8d1e40aa33048b81eebd2`，仅一host delta并继承6903行，native d1d4及其原构建不变，无重编译/旧矩阵/全树重hash。旧producer误调用被create-only守卫立即拒绝，exit1历史保留，无旧输出改写。

TED原unused root03已公共prepare exit0、0.763秒，QOL原unused13已公共prepare exit0、0.744秒；各仅新增顶层manifest变化的prepared sibling，其余深字段exact相同。TED下一场R17/a126已preflight exit0、单次allocate，register6562→keeper6563约1.544秒，新的Steam窗口位移与双nonce离线原图经Root亲审后实际启动；业务和新增恢复路径实机结果仍待。production_ui required MCP tools只补原实际依赖的execute_step/current_event_window_context两项，不增加新业务合同。

### R17实际资格与公共日志参数修复

[R17实际薄证据](C:/workspace/ck3-upgrade-20261008/r17-preaction-paused-readmission-actual-qualification-01/ROOT-R17-ACTUAL-SHARED-PREACTION-AND-STRICT-FULL-DAY-QUALIFICATION-FINAL-02.md)确认Source08的提交前重新准入成立：旧native3/reject0之后，精确native4/reject1拒绝帧不授资格，实际完整暂停native5才重新准入。D1在14:53:06–14:53:10 UTC完成24小时，完整native9暂停/map/ready成立；same owner/actor/generation保持，set-speed/resume/结束pause各仅一次。原严格拒绝、counter1与所有动作记录保留。

随后的日志查询因公共consumer缺少必填`log_name`被实际MCP声明拒绝；没有生产Send/AI结果信用。host14:53:20 UTC RED/thread/cleanup TRUE，retained实际OS1、normal-close-qualified FALSE，公共run66470实际exit2。keeper60331实际exit0，最终[a126 release](C:/workspace/ck3-upgrade-20261006/resume-root-01/a126-screen-release-01.json)为CAS6578 done/resources=[]。共同D1资格可复用，原整场失败不改为PASS。

Root已修复`_business.literals`与RMTM `_law_phase`两处实际接点，显式传`log_name="debug.log"`，原marker producer、顺序与业务断言不改。新增[公共日志交叉回归](../tools/test_ck3_mod_acceptance_log_contract.py)连接实际consumer函数、实际MCP参数声明与实际日志provider，核必填参数、精确marker计数/重复/禁止项、大小写和16项上限，并覆盖RMTM三phase及QOL原七批；采用后8项实际PASS（1.386秒），接入原CI。无需重编native或重跑已通过的旧矩阵。

精确前一提交`0cd572f0f88b3fa00012842c0f21eba1b985310b`的[官方CI 37795672799](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37795672799)实际success（14:58:59 UTC），[线性历史CI 37795672808](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37795672808)实际success（14:50:28 UTC）；这两项不外推新增日志修复的下一提交。

下一原unused root04实际公共prepare exit0、0.789秒，仅state_dir改为root04，其余case inputs与原合同相同，继续绑定Source08/FINAL09/bound10。R18/a127已单次allocate（6579→keeper6580 READY 1.538秒），Steam窗口位移与两张实际nonce原图经Root亲审离线，15:15:07 UTC实际启动共同host；生产交互与正常退出仍待该场结果。发布后统一menu-only缓存消费另行施工，不重跑缓存业务、不改变R18已冻结输入。

### R18导航失败与共同菜单缓存消费（2026-10-09）

R18/a127随后取得完整D1和实际`debug.log`查询成功，六项原context marker各一次、三个FAIL族为0，实际READY给出本场宋34422、辽34440、西夏37256和天德14684。Root的额外MCP人物导航被[旧episode绑定校验](C:/workspace/ck3-upgrade-20261008/ted-r0018-open-character-error-readonly-33/ROOT-TED-R0018-OPEN-CHARACTER-ERROR-33.md)拒绝，发生在native派发之前；不是人物ID无效或真实GUI失败。15:29:24 UTC host RED/thread/cleanup TRUE，公共run67672实际exit2、retained OS1、normal-close FALSE，无Send/AI结果信用。keeper13708实际exit0→[CAS6597 done/resources=[]](C:/workspace/ck3-upgrade-20261006/resume-root-01/a127-screen-release-01.json)，原失败保留。

Root采用单一`_ingame_ui_v1`窄接线：前后均复用既有camera helper的native_campaign绑定，并核完整managed run binding及实际owner一致；普通episode路径保持。六项[真实函数交叉回归](../tools/test_ingame_ui_managed_binding.py)采用后PASS（3.930秒），加入既有CI。原`.4` UI build-scope只允许army query/select，人物窗口仍明确未准入；不放宽native资格，不给这项修复虚授人物导航信用。R19/a128使用旧冻结Source08、普通GUI人物路线，root05已消费，不能改成新版本的unused输入。

## Source09：统一菜单加载与原 managed UI 绑定

[Source09/FINAL10/bound11 封存](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/ROOT-SHARED-SOURCE09-MANIFEST10-BOUND11-UNUSED-CONSUME-01.md)实际exit0、3.989秒。仅host227490 B（SHA `242c5efeb3968c8f72211def4d32859eedda32c7c9f9e58b4504ab95ee563c4b`）和driver1419062 B两项独立delta，其余6902行继承。native DLL/injector及其构建不变，没有再编译、旧矩阵或全树重hash。

公共菜单加载分支与绑定修复已入主树，六项菜单定向测试和六项绑定交叉回归通过；共享Workshop缓存adapter另有九项定向测试通过。新菜单分支的实机资格仍为NOT_RUN，首次后续正式发布缓存场承担该项验证；不重跑已完成产品。

R19在17:02:39 UTC结束，host报告GREEN、managed thread完成、cleanup TRUE；公共run80125实际exit2，错误为原正常退出预留时限已到且Root业务阶段仍GAP。Root实际确认角色搜索器显示“皇帝，耶律弘基，你的朝贡者”，但未执行Send、未取得AI响应，也未完成Root正常GUI退出；host GREEN不授产品验收信用。[a128 CAS6671](C:/workspace/ck3-upgrade-20261006/resume-root-01/a128-screen-release-01.json)已done/resources=[]，原场输入和失败证据保持。虚拟键输入未改变搜索框，Windows扫描码Ctrl+V后才实际显示完整“弘基”；后续普通GUI输入应沿用已验证扫描码及焦点、英文布局、实际文本读回。

原retained handle在等待截止时为signaled=false、exit_code=null，normal-close-qualified=false，不能声称实际OS1或OS0。[闭场薄卡和新场预算](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-product-specs-01/ted-manual-ui-three-hour-tail-35/ROOT-TED-R19-CLOSURE-AND-THREE-HOUR-TAIL-35.md)绑定四份原始小结果。未来TED production_ui仅将人工hold从3600改为10800秒，command300/readiness900/timeout4800/poll.05及90秒正常退出预留保持；真实D1、Send一次、AI回应、150威望和钱包后果的通过条件保持。三小时是保活上限，业务完成即可提前正常退出，旧场不重新解释。

共用`workshop_cache`已经接入六模式CLI，一份顶层case/adapter供全部产品复用，公开ID取canonical清单，无ID开发版拒绝。唯一共同host新增显式菜单观察支路：不New Game/Start/载入/日推进，实际单次受管launch与两连续完整主菜单观察绑定cache-only六文件profile，原正常GUI/OS0/native0/cleanup沿用。缓存文件直接引用Steam下载目录，原strict helper逐文件核正式manifest；无业务fixture或复制cache。已采用[菜单6项](../tools/test_ck3_mod_acceptance_menu_mod_load.py)实际PASS（2.108秒）及[cache9项](../tools/test_ck3_mod_acceptance_workshop_cache.py)实际PASS（1.068秒），原客户端、allocator和SDK入口保持。详细永久政策见[缓存验收](workshop-cache-acceptance.md)。代码采用不代替首次菜单模式实机资格，后续统一封存供新run消费。

精确日志修复提交`4fa3e50cba036d538ad2c5a7266f60610ea94496`的[官方CI 37799513376](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37799513376)实际success（15:24:15 UTC），[线性历史CI 37799513501](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37799513501)实际success（15:18:09 UTC）。新菜单/绑定采用仍需其精确新提交的CI，不外推旧CI；正式仍6/10。

2026-10-09追加：上述菜单/绑定/cache采用的精确提交`654f38068089e8bf1b683e53cc31a23614372079`已普通推送，[官方CI 37864137963](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37864137963)实际success（00:27:57 UTC），[线性历史CI 37864137896](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37864137896)实际success（00:19:36 UTC）。[终态薄回执](C:/workspace/ck3-upgrade-20261007/remaining12004-formal-publish-cards-01/exact654f-ci-terminal-once-66-01/EXACT-654F-CI-TERMINAL-66.json)只查询当次精确提交，不重跑旧矩阵；CI不授尚未运行的菜单加载实机信用。

TED R20/a129的D1/context成功，Root普通GUI已确认辽帝、外国君主及可选郡列表，但原三小时hold于03:22:24 UTC结束前未Send，公共run实际exit2；没有AI响应或业务通过。原retained handle仍为signaled=false/exit_code=null、normal-close-qualified=false，不能据后来host GREEN/thread/cleanup TRUE补认正常OS0。[四份原始小结果及pins](C:/workspace/ck3-upgrade-20261009/ted-production-ui-unused-root-07/previous-R20-pins.json)保全，[a129 CAS7343](C:/workspace/ck3-upgrade-20261006/resume-root-01/a129-screen-release-01.json)已done/resources=[]。下一场沿用已验证的扫描码输入和跨游戏帧的单次点击；原合同允许选择当场真实合法的外国接壤郡，无需固定搜索天德。实际选项、资助数值、Send一次、AI回应与钱包/战争后果仍须亲审，不用导航ACK补业务信用。

2026-10-09 TED R21/a130沿同一入口完成真实生产交互：Root亲审单次Send后的“拓疆令已受命”，宋金币2407→2357、威望6050→5900，辽金币281→331；实际辽帝耶律弘基向夏宁令嵬名两岔发动争夺天德的朝贡拓疆战争。[原GUI结果](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--tributary-expansion-directives--R0021/case-output/ted-real-production-UI-root-result.json)保留资金数字空白及次要目标裸key两项显示缺口，不能把真实转账50外推为金额显示通过。正常GUI Quit后，原retained HANDLE signaled=true/exit0、native exit0/job0/treegone/control全absent；公共run实际exit0、case/GUI/normal-close均qualified，host于06:36:06 UTC完成thread/cleanup。keeper实际exit0后，[a130 CAS7450释放](C:/workspace/ck3-upgrade-20261006/resume-root-01/a130-screen-release-01.json)为waiting/resources=[]；该过期claim退休状态不改写实际run/正常退出0，也不授完整release。

同日采用[显示修复43](C:/workspace/ck3-upgrade-20261009/ted-ui-display-candidate-43/ROOT-TED-DISPLAY-FIX-CONSUME-43.md)：交互通过原生`localization_values`绑定动态战争金，九语标签改用`$TED_WAR_SUBSIDY|0$`并补齐次要目标标签；金额公式、AI、CB及实际效果保持。既有static、4项针对显示失败的回归测试和一次16文件builder均实际exit0；[新staging manifest](C:/workspace/ck3-upgrade-20261009/ted-display43-staging-once-01/mod_tributary_expansion_directives.manifest.json)仍是未发布候选。新场只沿公共production_ui复核受影响的显示及同一生产交互/正常退出，不重跑旧13项或SaveLoad矩阵。新Notes已冻结为2943B/2127字符/19行/SHA `c3ee3e5d158310d578d55c20c935a7fa5507f30617287a876680f439efd92aff`，仍未发布。


## 2026-10-09 QOL startup两次失败与compact proof25边界

R34原`set_player_character`的NONE/非玩家scope错误触发资格forbidden marker；
[最终盘点](C:/workspace/ck3-upgrade-20261006/resume-root-01/a134-final-inventory-01.json)
为RED/OSexit null，CAS7657资源释放不代正常0。R35已实际宋actor34422，
原proof却因raw scope块hex膨胀至616757B而被原65536B门禁拒绝，未选择startup
事件、未取得guards业务信用；后续ENOSPC/keeperfailure/timeout的
[CAS7697](C:/workspace/ck3-upgrade-20261006/resume-root-01/a135-screen-release-after-keeper-enospc-01.json)
为waiting/resources=[]/unresolved_red，旧失败不改写。

已推送的`36fcbcb0132325ac32c0efbb0a6461f4496fa7e2`只将两个原startup
handler的内嵌hex改为保身份/marker/offset/SHA的原始块引用，未放宽共享64KiB
gate、未改scope parser或产品业务。现有[离线actual R35验证](C:/workspace/ck3-upgrade-20261009/qol-startup-compact-proof-candidate25-01/R35-ACTUAL-COMPACT-STARTUP-QUALIFICATION-VALIDATION-25.json)
为1281B/原loader接受；UI1285B仍仅synthetic，不称修复实机通过。

截止14:33:58 UTC，Root已于14:30:15.625440启动R36/PID19552/原session49690，
使用亲审challenge03/context03；前两次过期nonce保持历史。R36尚在loading并
等待原qualification logs，没有guards业务或normal0结论，未重播已用R35。
磁盘处置与精确归因见[交接补记](ck3-upgrade-handoff-2026-10-06.md)；不改变
公共Source09/FINAL10/bound11合同或增加新平台/验收门禁。TED实际推送后正式7/10，
QOL完整源码验收与发布仍pending。


## 2026-10-10 续办：R36原业务补证与共享用例接入

R36在原预算内通过正常GUI退出：[原normal-close结果](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0036/case-output/normal-close-result.json)为retained OS0、native process_exit0、manageddone/thread/cleanup及normal_close_qualified=true；原keeper实际0/failureNULL/last7787后[CAS7788 done/resources=[]](C:/workspace/ck3-upgrade-20261006/resume-root-01/a136-screen-release-01.json)。主树原parser只接受历史角色的冒号格式，遗漏生成角色的`Internal ID 46792`，故原入口exit2/解析RED仍保留。strict31要求第一条唯一current角色、独立Character全ID标签、真实Root34422及on/off一致，不从saved alias取ID。

[同场追加补证32](C:/workspace/ck3-upgrade-20261009/qol-r0036-guards-supplement-aggregate32-01/actual-same-run-supplement32-01/R36-ORIGINAL-TWO-GUARDS-SAME-RUN-SUPPLEMENT32.json)已实际生成（12321B/SHA d8aed527a47671f95f5874f29e1581214ca0da211dab2f1e7a722dcfd1536a85）：原两次24h推进、真实宋34422、两个subjects46792/28978及原两PASS/FAIL0成立，仅授原guards补充2/2。未重启或重跑业务，不追认原entry run0、不授QOL整体PASS；GUI25及其余独立cells仍待实机。

公共入口现采用[Source10/FINAL11/bound12冻结](C:/workspace/ck3-upgrade-20261009/common-pam-readonly-optin-01/SOURCE10-MANIFEST11-BOUND12-ACTUAL-FREEZE-02.json)。仅两个共享Python文件独立写入、6902原文件无变化hardlink；原d1d4 DLL/injector及预算保持。case可显式声明且required两项既有religion只读MCP查询，默认关闭，不开启整个private工具组。原Source09和既有场次证据不改写。新共有client保留原deadline等待Root退出审阅，并按原case timeout等待原initial business plan，不把400s readiness错用为35步业务上限。

六个原followup、宗教三项（含compact27启动证据修正）和ordinary_async已采用到唯一registry；[11个新prepare实际回执](C:/workspace/ck3-upgrade-20261010/qol-common-source10-prepare-01/actual-prepare-group-result.json)全为exit0，含ui_tail。均用同一Source10；只产生输入/profile，未分配或启动这些场次，不授业务信用。原formal27、断言、自然日和各case预算保持。集成33项针对性测试在纠正构造器mock缺少默认opt-in属性后通过（2.224s）；旧失败输出保留。各owner已有精确SDK/原块/来源检查复用，无whole build/full matrix重跑。

G2持久停战查询16文件源码已合入当前施工树，原Python5/MCP13与Native08增量BUILD_ONLY证据复用；未给其DLL产品runtime资格、未交换d1d4产品DLL、未授G2实机信用。正式发布仍7/10，顺序为QOL→RMTM→361最后→廷臣礼仪/G2。以下与此前记录中的时间截点保持历史含义。

## 2026-10-10 R37：直接观测的工具等待与公共退出接点

正式迁移已 **7/10**（TED永久记录 `a767bd` 已推送），产品共同底座仍为 Source10/FINAL11/bound12。QOL R37原入口session63075实际exit2；readonly9实际PASS（初始13步和GUI后2个snapshot步骤），[UI25原记录](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0037/case-output/ui25/actual-same-live-records.json)为空且25项全remaining。[原normal-close](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0037/case-output/normal-close-result.json)为Rootreview NULL/retained OS0 false/qualified false。host于17:15:16.609127 UTC GREEN/thread/cleanup及进程树消失、keeper23244实际0，只授资源收尾；[CAS7844 done/resources=[]](C:/workspace/ck3-upgrade-20261006/resume-root-01/a137-screen-release-01.json)不补业务或正常0信用。

Root两次工具操作之间16:46:52→17:26:50 UTC的**39分58秒平台等待**为直接观测，原因未证实。已开展的改进是[公共自动Quit接点](C:/workspace/ck3-upgrade-20261010/common-operator-latency-real-r37-01/ROOT-NORMAL-QUIT-AUTOMATION-ROUTE-RESOURCE-01.md)和[真实委派操作者边界](C:/workspace/ck3-upgrade-20261010/common-operator-latency-real-r37-01/ROOT-DELEGATED-GUI-OPERATOR-MINIMAL-BOUNDARY-01.md)：helper仅compile/help及纯binding检查通过，client opt-in在准备；Root拟将下一场唯一GUI custody交ccc，尚未实际委派或实跑。模板自动化必须保存 `automation_actor`、`human_review_claimed=false`，GUI人审保存真实reviewer身份，继续原图/sequence/current-run绑定以及独立OS0/native0/thread/cleanup，原25项业务断言与期限不变。现存R37失败不追认为自动链通过。

并发备料分别为QOL [center-title/title-own-laws两路接线](C:/workspace/ck3-upgrade-20261010/qol-ui-existing-typed-navigation-01/ROOT-EXISTING-TYPED-NAVIGATION-01.md)、RMTM [Source10 core/threshold后继](C:/workspace/ck3-upgrade-20261010/rmtm-source10-consume-01/ROOT-RMTM-SOURCE10-CONSUME-01.md)、G2 [Native08最小资格规划](C:/workspace/ck3-upgrade-20261010/g2-runtime-minimal-qualification-01/ROOT-G2-MINIMAL-LIVE-QUALIFICATION-01.md)，其中QOL两路、CCC reviewer、CI psutil及RMTM threshold声明补丁已由Root采用到当前施工树；RMTM core/threshold新prepare各实际exit0，尚无新游戏。均不增加新产品host或提前授livePASS。Root闭场后完成同hash索引刷新、无冲突rebase、本机49测试PASS/3.058s及普通push `9c8f2986b115c7e1c4d7cf807d60802f5eb8e7bc`；该SHA官方静态venv实际缺psutil的原RED保留，修复已采用但后继提交官方CI尚未验证，不外推SUCCESS。缓存仍只一次实际下载exact formal和实际加载/正常退出，不增加缓存业务。
