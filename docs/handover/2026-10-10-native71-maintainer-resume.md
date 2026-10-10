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
