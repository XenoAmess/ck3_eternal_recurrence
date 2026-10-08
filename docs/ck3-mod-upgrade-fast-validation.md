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

当前`--help`实际提供`plan / prepare / allocate / preflight / run / verify`六个模式，所有模式共用`--runtime / --products / --product / --case`。本机[local映射](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/runtime.local-entry-bound05.json)选择唯一[FINAL04 manifest](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-shared-runtime-01/SHARED-RUNTIME-MANIFEST-FINAL-04.json)，后者绑定shared Source03/index、canonical host与native DLL/injector；local文件只提供本机Python、游戏/userdir/artifact根及原launcher/queue/allocator路径。换机器统一绑定本机local路径，产品adapter不传host/source/native/host_args，不复制一套运行时。旧runner和冻结只保留原证据及底层实现。

从仓库根的`cmd.exe`执行，以下只读例子选择当前真实TED case：

```text
tools/.venv/Scripts/python.exe -B tools/ck3_mod_acceptance.py plan --runtime C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/runtime.local-entry-bound05.json --products tools/ck3_mod_acceptance_products.json --product tributary-expansion-directives --case saved_gui_tail
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

## Source03共同版本、无CK3检查与R14实际边界

当前全局为Source03/host `cd7561f9…`、FINAL04 manifest `91197f38…`、local bound05 `96164…`；上面的当前只读CLI例子已指向bound05。R13/a121所用Source02/FINAL03/bound04保留原冻结历史。产品仍只消费公共版本，不能分叉独立host/source/DLL。

既有无CK3检查为[entry 10项](../tools/test_ck3_mod_acceptance.py)、[adapter 9项](../tools/test_ck3_mod_acceptance_adapters.py)、[completion 3项](../tools/test_ck3_mod_acceptance_completion.py)：覆盖全部14产品/全部case同host/source/DLL，product与case两层都拒绝8种override（host/source_root/source_index/native/dll/injector/engine/host_args），真实`managed_session_done` Event与原native0/完整cleanup联合判定，[portable资料](C:/workspace/ck3-upgrade-20261008/ck3-mod-acceptance-unified-entry-01/ROOT-PORTABLE-ADAPTER-TESTS-REVIEW08.md)，以及verify FALSE/null/非严格true返回exit2。本机source guard 10、adapter 9实际exit0，completion 3实际PASS复用；这些既有检查可作为无Steam/无CK3 CI门禁，不授业务PASS。新HEAD官方CI终态在实际commit/push后另记，本文未重跑测试/构建或矩阵。

TED [R14/a122闭场48](C:/workspace/ck3-upgrade-20261008/ted-unified-a122-d1-failed-readonly-resource-01/ROOT-TED-R0014-A122-D1-SHARED-PAUSE-FAILURE-CLOSED-48.md)保留actual startup fixture资格及D0 typed PASS；已提交的首日`case-natural-day-0001`因共同pause读回丢失complete same-owner frame失败，不重播，未到production GUI。host于11:31:23.237773 UTC RED/thread/cleanup闭场，Source03真实done Event TRUE仅证明生命周期结束；原retained PID24956/ctime1791458801.1143658实际exit1、normal ROOT/native0 proof均NULL，未授正常Quit/normal0。共同run exit2、keeper80379实际exit0→CAS6474 done/resources[]保留；`normal-quit-awaiting`早值NULL不证明无host error。共同pause修复仍由shared owner施工，正式仍6/10（60%），不授14产品PASS，不重复缓存业务。
