# Native71 接班整合与 R0087 续跑

## 原目录整合结果

用户要求先清理、提交原目录，再接续休假交接；进一步明确所有变更须“合入 master 或删除”，并要求64并发。原目录处于旧 `codex/dynastic-movements-20261005` / `14c13457952ee89da3e6889c29075477584948f3`，与当时 master 历史分叉，不能整支覆盖主线。

最初用 `codex/archive-original-residue-20261010` / `1515c4349e7c26dc38686060c58164314d497928` 临时保全71修改、142删除和27新源文件，共240项；这一步仅为保全，未完成整合。随后64个互不重叠工作包逐项比较原变更与 evolved master，最终 **3 merge / 237 delete / 0 deferred**。协调者统一执行，完整文件级结论与证据在 [逐项结果](2026-10-10-original-residue-resolution.json)。

合入的独有内容是2026-09-01 Kaishek 独立仓库收口日报、W36周报，以及仍被主线R1/R2/R3报告引用但缺失的迁移计划。迁移计划明确历史版本，更新当前授权和Python命令模板。其余残留已被主线接收、后续实现替代或属于一次性脚本，旧副本不再保留为待办。142项Kaishek删除继续符合独立拆仓边界，源残留中已无 master 缺失且待删除的实体文件。归档分支在主线提交和官方CI终态后删除；不保留归档 ref 作为交付。

前置整理记录已推入 master `2a4e7819b3fbeef1d3b05108a8d5493cc5dfc5df`。首次全量切换时因未按约2.59GB树预算检查Z盘而失败；这是执行错误。新检出派生资料曾可逆移动到 `D:/codex-ck3-background-spill/maintainer-resume-20261010/failed-checkout-files/`，不涉及旧原件；最终回收结果另记。当前原目录采用稀疏检出，包含SDK、tools、docs、CI及三套主mod；历史本地产物/嵌套工作树仍按通用存储策略处理，不能把 Git clean 声称为这些历史资产全部物理回收。215条本地精确输出排除规则不替代源码整合。

## R0087 的真实结果

完整ID `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0087`，execution `4112b211-8952-4c52-83e8-17162ee2b06b`。接班恢复输入为6066/H10013/raw53289912和完整12流。SDK clean detached pin、Native71 source/compiled/archive/qualified canonical 均为 `16da78339cdff5c1a462e20bc301684594a3f800`；沿用已资格DLL，不重编、不重跑旧FIRST，也不改写保留的旧物理owner来源。

新鲜Steam窗口已实际审阅“离线模式”，Toast保持禁用。第一次prepare因稀疏检出缺 profile/workshop 传递依赖而RED，未启动游戏；同pin补齐依赖后的attempt02 profile/copy/rebind/preflight全部exit0。新CK3 owned PID115548、Robert29829、原普通战役episode、XARoff。07:15:51Z实机新paused资格 **13/13 GREEN**，无窗口焦点抢占。

现有普通OODA的首次响应及7个后继turn完成查询→规划→操作→观测，实际前进1天并于07:34:56Z成功SAVE。新持久基线 **6067/H10026/raw53289936**，episode `native-29829-2bc2d599f7f9`；checkpoint **104,787,543 B**，SHA-256 **`fffd9e8b35caa8a0af67fa979261c8ccbf1cf8d01d8efe85ebe4a3670cceba0e`**。初始同日期SAVE与冷恢复不增加天数。Sway continue、opinion60、贡献45，未观测terminal；建设receipt查询不等于completed/useful-income闭环。

SDK exit0。stock Desktop点击等待中，协调者提前请求custody stop，Game最终exit1；记 **harness close RED**，没有正常Game退出证明，也未证明native crash根因。owned runner exit0、Game/injector gate为空。完整十流加release/construction supplements **3/3 exit0**，Driver全体复制、不裁剪历史；keeper最后sequence1613后 **CAS1614** 释放。闭场新知识见 [测试流程](../testing-workflow.md)：必须先等待Game独立exit回执，再停止custody。

MCP100%、G2 5/8、NW2 2/4、M4false、M6partial、M7incomplete、自然继承0保持。此次交付增加的是Native71真实冷恢复及1天已保存的production loop证据，不是整代自治完成。

## 证据与接续

本次外置根 `D:/codex-ck3-background-spill/maintainer-resume-20261010/`，关键相对路径：

- `r0087-managed-attempt02/operator/ROOT-R85-COLD-PAUSED-SNAPSHOT-QUALIFIED.json`：真实13项资格。
- `ordinary-one-day-save/BOUNDED-RESULT.json`：1天循环、6067计数及最终SAVE来源。
- `r0087-freeze-metadata/ROOT-ACTUAL-SAVED-CHECKPOINT-BINDING.json`：实际checkpoint字段。
- `SDK-qualify-EXIT.json`、`close-stock-desktop01/ROOT-STOCK-DESKTOP-RESULT.json`、`close-custody01/ROOT-CLOSE-OBSERVATION.json`：分别保存SDKexit0、Gameexit1、custody关闭；不得混为正常退出GREEN。
- `r0087-freeze-execution/ROOT-ACTUAL-COMPLETE-FREEZE-EXECUTION.json`、`SCREEN-KEEPER-STOPPED.json`：完整freeze与CAS释放。

**下一恢复入口**为 `r0087-saved6067-freeze/RECOVERY-INPUT-PACKET.json`，十流回链 `ROOT-SAVED-TEN-STREAM-FREEZE.json`，两份supplements在同freeze目录；必须带全Driver/12流。当前基线限期保护至2026-10-17，下一次接续/存储复核重新按实际用途判定，不无限期保护所有旧副本。继续沿exact16da/Native71资格输入；新的原版观测/策略施工仍先补对应原生树与实机证据。建设下一watch raw53290008只是调度时点，不是完成ETA；优先观察真实completed/material/useful-income，随后推进M6/M7。

### 2026-10-10 16:05 CST 主线发布与 CI 修正

64包的逐项整合与R0087实机记录已普通推入 master `295105131ecbe334235f9da8051c862952af9a95`。该 SHA 的 [Official Runner CI 38035783581](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38035783581) 实际 failure：第46步 Python-only 检查在逐项结果 JSON 的历史删除记录中检出旧 shell 名称及旧脚本后缀。检查器9项测试通过；[Linear history 38035783594](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38035783594) success。没有据此声称官方静态全部GREEN或 CLA / signed 状态成立。

本次只修正记录表示：3项已删除旧脚本的原名拆成路径 stem 与 `removed_file_extension` 元数据，仍可精确还原全部240项；历史说明不保留可执行旧入口。未修改检查器或添加豁免。`py tools/validate_python_only.py` 本地实际 GREEN，下一主线提交等待官方终态后删除临时归档ref。进度入口及路线图同步真实6067基线和退出RED，未扩大readiness。

07:48:47Z已回收首次失败检出产生的5,889个派生文件，共585,854,918逻辑字节；删除对象逐项与当次新增文件清单匹配，不涉及原输入或当前完整freeze。回执为外置根下 `FAILED-CHECKOUT-COPIES-RECLAIMED.json`。本任务创建的临时operator HTTP helper也已关闭，回执 `OWNED-OPERATOR-SERVER-CLOSED.json`；旧任务operator保持原所有权。SDK、Game、owned runner已退出，screen CAS1614已释放。后续只剩主线CI及ref收口，不新增游戏重放或审计包。

### 2026-10-10 16:17:45 CST 归档 ref 已删除，整合收口

修正提交 master `a22e0291ec88587d282ce64ca413fc6bc4fbc928` 的 [Official Runner CI 38036746599](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38036746599) 与 [Linear history 38036746593](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38036746593) 实际 success。此前29510513的Python-only RED保留，未重跑旧SHA。官方CI通过后，已删除远端及本地 `codex/archive-original-residue-20261010`，并删除本地 `codex/native71-maintainer-resume-20261010`；实际时间 `2026-10-10T08:17:32.035760+00:00`。复核远端归档查询为空、本地两ref均不存在；没有删除其他维护者ref。回执 `D:/codex-ck3-background-spill/maintainer-resume-20261010/OWNED-INTEGRATION-REF-CLEANUP.json`。

最终240项均已处理，**3合入 / 237删除或由现有主线替代 / 0待办**；64审阅包全部完成。原目录现在沿master集成，归档不再作为待处理工作保留。实际游戏基线6067、完整12流恢复包、Game关闭harness RED和存储限期保持前述事实，不因Git收口增加能力完成度。本段为删除后的永久记录，随后独立提交并正常推送。

### 2026-10-10 19:39 CST Native72 actual output pins, complete SDK and R0088 normal close

Native72 的实际输出摘要只计算一次，记录在 `D:/codex-ck3-background-spill/g2-native72-build01/attempt01/NEW-OUTPUT-DIGESTS.json`：DLL 14,953,472B / SHA-256 `d67a07ec59477dfc83a72190190e11bb3a03f8103bdf939dccd975d640867f80`；真实 Runtime archive 151,032,024B / SHA-256 `b0954f692ae15b86851d086127eb95f0e27204d6755e129c79e1424438c89a17`。生产编译 pin 仍为 `2a33d969671540d9e7ddb0124ef3cee90e433b00`，498/498 实际 compile、archive、DLL link GREEN，789 objects/487 Runtime members 的混合来源保真。兼容既有 loader 的小型 canonical 位于 `D:/codex-ck3-background-spill/g2-native72-canonical01/ROOT-PARENT-RUNTIME-INCREMENTAL-DLL.json`，manifest 8,898B / SHA-256 `7cc98b26085cdb57471636cf9c18d32b134897bc806feae9866032c0064db30f`；未覆盖71 canonical、未重算旧二进制、未把新文档 HEAD 冒充实际编译 pin。

完整 SDK 已实际 materialize：`D:/codex-ck3-background-spill/ck3-sdk72`，detached source `cbc2a704780595d87f4ae1643c0240dc5d96bb68`，43,635 tracked inputs / 2,592,504,057 source bytes；一次 materialization receipt 为 `D:/codex-ck3-background-spill/native71-continuation-20261010/SDK72-MATERIALIZATION.json`。现有 venv、完整依赖树与5份便携 runtime-entry 使用既有路径；峰值3,308,103,929B纳入原有并行20GiB子额度，未另创重复额度。SDK源与 Native72 编译/archive pin 分别记录。已推送源cbc2的 Official Runner38047289851 和 Linear38047289845 实际success。

R0088 以第8个独立正常日 SAVE6075/H10085/raw53290128收口，SAVE104,661,262B / SHA-256 `47c5e27dbd989efd1d87b0c0c1eff9af4883009ca3c71549cc8ce2ac13ddd17a`。SDK于11:15:48Z独立exit0，Game于11:19:20Z独立exit0；只使用一次WM_CLOSE及一次已查看stock确认按钮的后台点击。随后 full12 freeze3/3实际GREEN，完整Driver2,961,207,410B，恢复输入为 `D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/r0088-saved6075-freeze/RECOVERY-INPUT-PACKET.json`，既有十流及release/construction两补充完整保留。custody stop wrapper 的一次无structured-response解析失败原件保留且未重发；一次只读status独立确认owned job exited/exit_code0、CK3/injector=[]、gate errors={}。keeper已正常join/CAS release，resources=[]，不把wrapper RED改称成功或新能力故障。

Native72冷加载正在沿现有恢复入口执行，01持有新keeper，实际 fresh Steam offline proof、Toast DWORD0与精确冷计划已落盘；此记录尚无新Native72 paused/live资格。普通可玩循环不等待下一源码波。新13c/29b/57c connected生产路径以及58c实际wire→strict→perCi消费已GREEN，中央当前40个有效资格；原C2597夹具失败保留，仅修入口并复用15个生产/fragment objects，Python14新checks独立通过。数值依赖必须由实际键/Q64匹配证明，不以同身份替代数值；FullPerson/FullEntry仍false。17b-provider strict的实际夹具日期遗漏仍在必要修复，尚未记整包GREEN。G2仍5/8、NW2仍2/4、M4false、M6partial、M7incomplete、自然继承0；四目标建筑没有新完成，Sway仍既有continue，新增SAVE不自动授予这些结果信用。

远端归档整合有实际进展：commit `f7d37c7cb9544d61ef58b49efbc0cb57d14979be` 已正常push，补回最终r18字幕及4处缺失历史记录，字幕SHA与原交付一致；保留同事新master `4d2fce86`/`1c21780f`。12个已patch-equivalent旧refs，加film/forecast两个已采用refs，合计14远端refs已实际删除。只剩dynastic/heresiarch/living-saints三个共享分支的净缺失内容由04收口；不是最终0残留交付。执行凭据为 `D:/codex-ck3-background-spill/native71-continuation-20261010/ROOT-REVIEWED-ARCHIVE-INTEGRATION.json`。64个代理槽位已分配，02持续复用完成者推进独占源码叶，不派理论安全审计、不重放旧资格。每个采用结果仍进入master；失败原件及当前恢复/构建输入按既有期限保留，不能当作未整合源码堆积。

### 2026-10-10 19:44 CST remote archive integration

17个已审remote refs最终全部按“已等价采用或补齐缺失价值，再删除ref”收口，0deferred。film/forecast实际采用commit `f7d37c7c`；共享product patch采用18旧路径+1索引，488旧变化由主线替代不回拷。[逐ref resolution](2026-10-10-remote-branch-resolution.json)与D执行凭据记录真实master push及最后3ref删除。没有新archive或强制push，实际Native2a33/SDKcbc绑定不被文档提交重label。

### 2026-10-10 20:25 CST Native72 actual cold GREEN and live family regression; qualified Native73 source

Native72 R0089 的真实 cold 13/13 GREEN 于11:53:19Z闭合，Game181556、Robert29829原普通战役、SDK source `cbc2a704780595d87f4ae1643c0240dc5d96bb68`、DLL source `2a33d969671540d9e7ddb0124ef3cee90e433b00`。完整Driver/full12恢复保留；fresh Steam offline proof、Toast0、唯一owned listener均按现有入口执行。新paused campaign-root确实给出5个 `task_owner_monthly_piety_v1` raw0/scale100000，有效零值不授予收入或M4完成信用。实机Army218104048的原生CArmy67109093、siege268435564/province2606及Entry字段已记录，但本轮尚未完成新的ArmyStrengths查询。

真实家庭查询于11:55:44Z报 `native conception observation is malformed`；第四个普通回合于12:13:42Z同错exit1，R0089仍SAVE6075/H10088/raw53290128，新增游戏日0。前3个成功普通调用仅取得4个目标construction的新partial材料，raw work分别98666710/102500007/99166708/104055561、cold divisor0，未出现完成/新income。失败原件为 `D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native72-r0089/managed/operator/gameplay-responses/310-r0089-native72-days01-07-chunk01-000004-normal.json`。同一次家庭query的native原frame未留存，guardian factory sidecar仍缺失，不能伪造观测。

确定性生产路径复现确认actual guarded observer的 `guarded_current_actual4_pair_provider_shortcircuit` 与SDK仅接受legacy `conditional_actual4_pair_provider_shortcircuit` 不一致。最小parser修复只接受这两种确实存在的来源标签，其他类型/raw/status/语义校验不变。中央10四TU compile/link0、一次实际guarded observer→current serializer wire0；当前Root parser及原SDKcbc加同区域修复分别对同wire通过，旧拒绝、legacy和5个必要拒绝case均保留。actual结果为 `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-55/native72-guarded-source-fix/focused-guarded-source01/RESULT.json`，wire SHA-256 `ca04e353a04ccca6c24af06718cceb4da98175e08fb2d95ab56741c07e8b67cf`；修复目前是已验证源码，实际live恢复待新完整SDK正常cold，不热改当前SDK。相同CPP/Python已作为永久可选4TU回归入口纳入仓库，无旧资格重放。

本次采用已真实connected验证的physical Person keys/values/tail→B/A→perCi数值消费、默认conception resolver及完整conditional provider，新增production Runtime TU总数8（physical5/default1/provider2）。第一次数值compound夹具C2597失败及必要入口修复保留，已编译production objects复用；47小patch上下文失败和Git换行差异保留，只按已冻结baseline/owner候选字节完成有限采用。所有聚合CMake增量保留，不覆盖已采用内容。纯conditional provider/默认compound和实际wire→strict→perCi消费均已有真实GREEN，不重做旧FIRST/旧leaf。FullPerson/FullEntry仍false，M7自然输入与Army下一包尚未合入本pin，future13startup不混入。完整采用凭据为同目录 `ROOT-ACTUAL-NEXT-SOURCE-ADOPTION.json`、`ROOT-ACTUAL-PROVIDER-AND-FIXTURE-ADOPTION.json`、`ROOT-GUARDED-SOURCE-PERMANENT-ADOPTION.json`。Defender实际admin_required/noAdd仍独立pending，未新增UAC流程。

远端17个归档分支已逐项采用或等价删除，最终8352ba4e正常push后server heads只剩master；详见 `docs/handover/2026-10-10-remote-branch-resolution.json`。64代理槽位继续复用独占函数施工，实际live actor只有01。G2仍5/8、NW2仍2/4、M4false、M6partial、M7incomplete、自然继承0；研究/fixture/source已闭不冒充production loop或complete。当前优先交付这次真实阻断修复的cold恢复及新增正常日SAVE，再推进Army新query和实际guardian采样。

### 2026-10-10 20:49 CST Native73 actual production GREEN, complete SDK and normal cold recovery

`37a54f99a3466989882bd62c9d85947a10d373db` 已正常commit/rebase/push，保留同事master `7fea752c` 及两份滚动报告内容。64个采用路径/5,581新增行；Official Runner CI38051964642与Linear38051964604均实际success。Root工作树在生产冻结时clean；后续报告HEAD不冒充编译或SDK source。

Native73实际prepare/projection0，12:30:22Z开始16jobs生产编译，12:33:28Z结束exit0；478/478 actual compiles，319对象原位复用，最终797objects/Runtime495members（170retain、317replace、8new）。父Native72的231条Ninja输入与558条actual command保留各自证据边界；新完整command rows566，无missing basis/dependencies/unclassified。实际构建凭据为 `D:/codex-ck3-background-spill/g2-native73-build01/attempt01/PRODUCTION-BUILD-RECEIPT.json`。新DLL15,038,976B / SHA-256 `850d84b501d8d9340304b0674838082994456674b0f92d72be0dc8972eec6c4b`，真实Runtime archive152,606,608B / SHA-256 `758fc2864e3187289ff980fc22fdcb04e6c8645a014b42b10d2c7cbe25240cba`，各只stream一次；旧binary未重hash。新loader canonical `D:/codex-ck3-background-spill/g2-native73-canonical01/ROOT-PARENT-RUNTIME-INCREMENTAL-DLL.json` actualGREEN，manifest8,873B SHA65946261aeb323c81c8f5bca7cabef883c197b2de5c9f48ecd1c6fec4adf6c3b。native qualified/compiled/archive pin均37a54；混合父对象的旧来源/unknown不改写。

完整SDK73已实际物化exit0：`D:/codex-ck3-background-spill/ck3-sdk73`，detached37a54，43,722 tracked files /2,593,367,019source B；entry `D:/codex-ck3-background-spill/native73-sdk-inputs`。实际执行凭据 `D:/codex-ck3-background-spill/native71-continuation-20261010/COMPLETE-SDK73-EXECUTION.json`。86 game assets共6,279,998B未变化，finalmanifest SHAe26b0594fc71eaa78decdf78b87ff056d2e46503715118fdf64a3484321a9b40，复用全部已有asset摘要，无旧opaque读取。Native73 nested2GiB和SDK73 nested3,309,323,243B实际admitted在原parallel20GiB中，无新增global reservation、无SDK72热改。

R0089正常关闭实际完整顺序：SDK12:24:03Z exit0；独立stock Desktop Game18155612:27:04Z exit0；full12 freeze12:27:36Z三批3/3 exit0；custody actualjob exited0/CK3及injector=[]；keeper12:28:40Z exit0/CAS resources=[]。stop wrapper原RED是job already exited0，raw保留且未重试；不把stop request改记accepted。本轮SAVE6075/H10088/raw53290128，新day0。完整12为3,145,459,731B，Driver2,961,335,234B，恢复packet `D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native72-r0089/r0089-saved6075-freeze/RECOVERY-INPUT-PACKET.json`。

只有已退休active Driver工作副本在12:36:13Z被单文件回收2,961,335,234B；已存在copy_completed/GREEN receipt、对应size及owned五PID退出证据直接复用，未重hashopaque，冻结中的完整Driver与12流及失败raw均保留。下一cold共同峰20,633,555,815B低于21,474,836,480B原runtime cap，余841,280,665B；没有扩额度。Native73新cold按现有路径实际prepare进行，fresh Steam位移图和“离线模式”原图GREEN/Toast0、新keeper精确绑定SDK73；一次启动前keeper旧SDK72字段错误已在任何Steam/Game/allocate前正常release0并保留，之后新绑定成功。此时尚未声称新13cold或家庭live修复通过。实际新family frame/guardian两factory sidecar、新ordinary回合和SAVE仍为下一交付。

并行新Army48对象/link及selective native fixture已实际GREEN，原fixture地址alias失败和必要修复保留，46对象复用/只补必要两TU/已通过前5场景零重放；59新wholequery nativeGREEN，Python消费待独立真实packet，尚未纳入本37a编译pin。自然19输入/56c strict→consumer8groups已GREEN，新wholequery仍验证中，不混旧FIRST/未资格startup。能力边界仍G2 5/8、NW2 2/4、M4false、M6partial、M7incomplete、自然继承0；编译/更多case不代替实机可玩结果。

### 2026-10-10 21:01 CST Qualified natural pair observation reaches master source

Root已实际采用11包/38唯一mappings：被动自然pair19、真实五参数provider45、RNG sample18、条件threshold20、incoming sourcebinder53、strict/consumer56、仅3个已资格startup hooks、家庭query wire与永久fixture、两个最小CMake登记。新增6个production TU（Bridge5/Runtime1），原17b/default provider及guarded来源标签修复完整保留。采用凭据 `D:/codex-ck3-background-spill/native71-continuation-20261010/ROOT-ACTUAL-NATURAL-M7-ADOPTION.json`，最终采用manifest SHA-256 `c79a07b801945bcf75a90d429ffdc54dddf5a14869390c166e80a2c74e4714ec`；所有共享文件按实际baseline核对后增量apply，未覆盖共享CMake其他hunks。

复用19唯一自然connected native GREEN、56实际8组strict→consumer GREEN；55新增3wire及5strict验证实际GREEN，首次头include缺口保留，只补必要闭包并复用已成功serializer对象。永久actual19 journal与同字节main、55新wire main/Python已纳入仓库，旧19/default/17/guarded资格零重放。有效结果为 `continuation-10/m7-natural-pair-connected01/RESULT.json`、`continuation-56c/root-first/RESULT.json`、`continuation-55/addon-natural-query/focused-natural-query-retry02/RESULT.json`，均位于上述D目录。原incoming/monthly角色、充分消费native算术的因果和当前session实际自然捕获仍unknown；原生字段/完整Bridge build与下一cold资格继续推进，不把fixture/source闭合称为生产live或M7complete。

01当前以实际Native73+SDK73固定37a54正常恢复R0090，12:52:04Z唯一allocate、full12 prepare/release/construction restore均exit0；不热用本次新master源码。新Game PID/cold13/家庭修复live/SAVE进展尚待实际回执。本包明确排除待资格Army/Entry/M4源码。后续优先：Root按已GREEN自然源并入master并准备Native74增量，Army59实际Python消费闭合后独立采用；01先完成当前家庭真实query及普通回合，继续同一原普通战役。G2 5/8、NW2 2/4、M4false、M6partial、M7incomplete、自然继承0仍不变。


### Native73 live family and private sidecar repair (2026-10-10T13:32:24.357375+00:00)

R0090 actually cold-loaded Native73/SDK73 at compiled source `37a54f99a3466989882bd62c9d85947a10d373db`. Its family observation at raw date 53290128/native revision 2 succeeded: heir 38822, spouse 38718, bilateral relation true, both age 22, and the complete living-child count is zero. The prior source-tag parsing failure is resolved in the real paused frame. The private guardian enrichment independently failed because Windows backslashes were rejected by `JsonStringField`, so the existing discovery job was not created.

The SDK now sends the same destination with forward separators and retains the private command-result object; the private native reply records the actual export stages. The existing provider and ordinary family response remain in use. Two new permanent fixture files and their optional target are included. The single connected native/Python boundary test compiled and linked successfully and executed once with exit 0; no Game query, factory lookup, old fixture replay, Create/Evaluate ABI or actual guardian readiness is claimed. Defender registration independently rejected source provenance before invoking settings. Qualification: `D:\codex-ck3-background-spill\native71-continuation-20261010\continuation-55\native73-guardian-sidecar-audit\focused-guardian-sidecar01\RESULT.json`. Adoption: `D:/codex-ck3-background-spill/native71-continuation-20261010/ROOT-GUARDIAN-PATH-REPAIR-ADOPTION.json`.

R0090 subsequently completed four independent construction observations, marriage, war termination and ArmyStrengths. The real Army query reported player army 218104048 with 1843/2367 soldiers and opponent army 134218098 with 393/536 soldiers. The seventh ordinary turn failed at the prisoner collection with `nonwar private snapshot revision is stale or malformed`; its original 410 response and the paused scene are retained for the minimal production fix. Current SAVE is 6075/H10091/raw53290128: this run has advanced zero new days. The running SDK73 is unchanged. Natural-conception source integrated at `c98cb8b9` awaits the next compiled cold build. G2 5/8, NW2 2/4, M4 false, M6 partial, M7 incomplete and natural succession 0 remain unchanged.

This repair is committed and pushed directly to master; its commit is the change introducing this entry. No archive branch is created.


### Qualified Army, Entry and Activity packages; actual prisoner diagnostic (2026-10-10T14:15:15.332517+00:00)

The 64-agent source wave has converged into independently qualified packages. Root adopted the Army native entry's 105 mappings in 23 packages, including 21 new production TUs (10 Bridge/11 Runtime), source-closed read-only helpers, the sole 48-source compound and precise startup registration. Native compound compile/link/run succeeded; 59's native whole-query wire also succeeded. The Army Python package adds 18 files independently: its necessary selective tail passed once, while prior native and already-passed Python sections were reused. Positive full consumer/release numerical stages and current game-load epoch remain unobserved. The obsolete mixed startup hunk was rejected without changing Bridge and explicitly superseded by the final Army-only startup; the stale CMake patch was replaced by the current-baseline increment preserving Natural/Guardian. Receipts: `ROOT-ACTUAL-ARMY-NATIVE-ADOPTION.json`, `ROOT-ARMY-NATIVE-APPLICATION-CORRECTION.json`, `continuation-59d/central-new-wire01/python-only-retry04/RESULT.json`, all under `D:/codex-ck3-background-spill/native71-continuation-20261010/`.

Entry adds seven Runtime TUs and reuses the existing writer and process clock. Its sole first connected fixture passed nine Side scenes, the sixteen-scene preceding-capture export and the getter export without recompiling successful objects or replaying old tests. Startup installs preceding capture, Side capture and getter capture in that order after the existing writer. Actual outer Combat invocation and full Entry readiness remain unknown. `ROOT-ACTUAL-ENTRY-ADOPTION.json` binds the source; `continuation-31c/central-connected-link02/RESULT.json` is the actual link/run receipt. The future Combat-query sibling is a separate pending package.

Activity's exact-build finite switch now includes the three missing destructor/played-ID/province-fallback bindings. Its new three-input native→serializer→existing strict-parser compound passed. The prisoner failure diagnostic preserves the original guard order, acceptance conditions and one-read limit and reports the failed conjunct plus owned snapshot differences. Its sole nine-case production-helper fixture passed; this improves the next real failure observation and does **not** claim the R0090 stale failure is fixed. Python source review found correct public/native revision handling and no evidenced Python fix. `ROOT-ACTUAL-QUALIFIED-TAIL-PACKAGES.json` binds both packages.

R0090 closed normally: SDK exit0 at13:57:59Z; independent Game193160 exit0 at14:02:57Z; full twelve-stream recovery freeze GREEN3/3 at14:03:29Z; owned custody exited0 and keeper/CAS resources empty at14:04:52Z. The sole retired active Driver duplicate was reclaimed14:06:57Z (2,961,364,129B), retaining the complete frozen Driver, all twelve streams and all failure/query originals. Final SAVE6075/H10091/raw53290128 advanced zero new days in R0090. Root transferred3GiB within its existing80GiB reservation from growth to runtime (runtime23/growth17/parallel20/safety20); total and expiry are unchanged. Native74 build2GiB and complete SDK74 estimated3,310,121,409B are child allocations inside parallel20, with final source binding still required.

This commit is the coherent source input for the next Native74 incremental production build and complete SDK74. The running/last compiled Native73 remains at `37a54f99`; source adoption is not live credit. G2 5/8, NW2 2/4, M4 false, M6 partial, M7 incomplete and natural succession0 remain unchanged. Next: build/canonical/full SDK, normal cold recovery, once real guardian metadata capture and once ordinary prisoner diagnostic, then resume observed-day SAVE advancement. All adopted changes commit and push directly to master; no archive branch is created.
