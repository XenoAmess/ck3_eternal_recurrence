# 宗教礼仪融合：2026-10-29 休假交接

> **2026-10-29续工入口**：后续R0057五项UI和R0058三项冷载补验已分别通过、正常关闭；原12／20完整矩阵、SDK续行、county地图颜色及Steam缓存仍有缺口。最新事实见[续工实机记录](../../mod_religious_ritual_fusion/docs/live-review-resume-2026-10-29.md)与[0.2正式发布准备](../../mod_religious_ritual_fusion/docs/publication-0.2.0-alpha-prepared-2026-10-29.md)。0.2正式90文件包已验证、tag已推送，尚未上传；四张补验图已本地导出JPEG、未公开。**以下正文保留交接当时状态，不以续工补验倒改原场次。**


用户最新要求：“你要去度假了。温和地收尾手上的工作，梳理交接文档到docs中。”因此停止继续实机、发布及下载，让已运行命令正常结束后交接。**产品尚未完成最终验收，0.2.0-alpha 尚未发布。** 续工先读本文；[10月26日交接](2026-10-26-religious-ritual-fusion-review-handoff.md)保留历史效力，其“最后一次游戏”已不是当前状态。

`machine_id: 4-8e1c2f1861`；本机观察时间均为UTC。仓库 `C:/workspace/ck3_eternal_recurrence`，本机获准工作根在C盘，不套用另一台机器的D盘映射。最后生产代码提交 **`16e74ec285fd727b886a41f2e38652e41e246494`**，已普通push至origin/master；本文之后的文档提交不追认为此前构建或游戏的源码提交。

## 当前状态

- 最后实际游戏 **R0053 / a63**，源码 `ca1add42c2491a8265ffba1a2f8401254ea8ba11`。已正常退出并释放SCREEN；业务仍incomplete。
- R0053确认创建按钮正确禁用，但原因正文空白、悬停只有通用说明。当前源码已修，**修复后尚未重新进游戏**。
- C17已完成freeze、六链资格及runtime metadata。收到收尾指令后停止，**未执行public plan、prepare、preflight、allocator或Game；没有Prepared，新state不存在**。
- 最终完整构建及消费者回归 **236项，零失败、零跳过**，另有整个兼容模块mypy strict/strict-equality通过。它们不替代实机验收。
- 商店最后一次匿名回读为2026-10-29约01:50Z：同一条目 **3826756673** 共15图，末尾9图明确为未发布0.2.0开发预览；公开下载仍0.1.0-alpha。本轮未再提交内容、Notes或图片。
- 14:09:45Z后台原生Steam探测为offline=true；14:09:47Z任务总线无SCREEN owner。未为确认Steam状态激活窗口或截图。最终原始闭场记录在下述O17；续工必须重新取新鲜状态。

## 资料位置及关键身份

```text
R   = C:/workspace/rrf-development-20261024
Q   = R/review-fixes-a01
DEV = Q/java-ui-tooltip-dev-a01                    # 复用开发源码、Maven输出和缓存
DP  = DEV/metadata/runtime-preparation-a01
J   = DEV/metadata/final-creation-blocker-CI-a01
C15 = Q/cold-R0046-final-a01                       # R0051、R0052等冷载资料
C16 = Q/ui-tooltip-final-a01                      # R0053，已结束
C17 = Q/ui-creation-blocker-final-a01              # 新修复runtime，从未启动游戏
P17 = C17/metadata/runtime-preparation-a01
O17 = C17/metadata/handoff-close-a01
N   = R/build/native-incremental-a09                # 冻结，未重编
H   = C:/workspace/.codex-task-bus/storage/volume-C-current.json
```

大文件保留在外置工作根，不复制进仓库。精确argv、原始wait、日志及完整输入Pins在相应封包中；续工先读回，不凭路径追认资格。

| 原件 | bytes | SHA-256 |
| --- | ---: | --- |
| `J/COMMAND-VALIDATION.actual.json` | 462760 | `682a21fe2b0cfcd3c9f26730e58cbcb3e85a3dcff094441ac019e3dcb61b3aa3` |
| `J/ARTIFACT-GRAPH.actual.json` | 247470 | `b7aefb424b77de523524464470ad15a04b73e9772d6aaa91bb218f8c08fb0d26` |
| `P17/C17-PREPARATION-WRITERS-CLOSED.actual.json` | 14742 | `8b92d55356e97a157208ccca24b6fcda8e56b6860337b5eab3691dd43a631f53` |
| `P17/source-freeze-a01/source-delta.actual.json` | 4920 | `f58269d5db8e2e7f465d085c1d2a12f92ab28740b71896073849ac2f34e63360` |
| `P17/qualification-a01/RESULT.actual.json` | 2625 | `baa579d3e0d699ad93f5866030538c624e818544d52c80edf05aa61b1422b6ff` |
| `P17/runtime-a01/runtime.local.json` | 12895 | `5383886a2140ae8cc32ff6129557ca48b5e538094ccaf4166e760ba535e3701f` |
| `P17/runtime-a01/manifest.json` | 96797 | `5c517bdab0921e85f238a226ffc49e897e85dad76caa99de9abb7dcf64473829` |
| `P17/PRODUCTS.ui-creation-blocker-and-cache-a01.json` | 5270 | `f26b7d4d2f0799274db8af8f8ae4f25e3c3efd23a3db8d28dfaf9f76704134ad` |
| `P17/ui-creation-blocker499.case-inputs-a01.json` | 1979 | `8779cb7789ade5cbd8bf69088254aeae1aca6a912310da2ec99851a542947c1f` |
| `P17/PRODUCT-PROJECTION.actual.json` | 65756 | `3467b576113321ab2782acf12d41fb463ee0b5567c883ad501fec152e6e954d7` |

## 已修实现与真实验证

`b1bf48eff` 将创建原因改为七个独立Customizable Localization分支：操作者、来源、重新校验、内容、核心数量、双方贡献、实际报价。页面与悬停共用 `RRF_COMMIT_BLOCKERS`；GUI悬停采用纯本地化键 `RRF_COMMIT_HOVER`。通过分支输出空文本，失败分支自带换行；九种语言同步，现有153个键。共享触发器沿用原条件，原创建IsValid/Execute、取消及可见性守卫保持。见[机制说明](../../mod_religious_ritual_fusion/docs/creation-blocker-localization.md)。

`16e74ec28` 修正既有非法转义回归的过期锚点：当前纯键GUI不能继续查找旧 `Localize('RRF_COMMIT_TT')`。测试仍向三个真实生产GUI引号内部注入非法转义，调用真实ContentValidator并核当前行列号，没有放宽验证或跳过测试。

按用户要求复用同一DEV，先增量、最后完整验收，没有重新复制全图或重编Native。默认 `mvn` 本机实测3.10.0，Maven home目录名 `C:/apache-maven-3.9.16` 只是观察事实，不是后续命令应锁定的绝对安装路径；Java为本机GraalVM25.0.4.1。

| DP执行目录 | 原始结果与范围 |
| --- | --- |
| `09-create-blockers-selected-tests` | wait1：GUI中的字面换行转义被真实验证器拒绝；失败保留，随后将换行移入YML。 |
| `10-create-blockers-selected-tests` | wait0：局部15项通过。 |
| `11-create-blockers-full-verify` | wait1：173项中旧GUI测试锚点1项失败；完整RRF报告保存在 `DEV/metadata/full-build-failure11-preserved-a01`。 |
| `14-current-hover-selected-tests` | wait0：修正锚点后局部19项通过。 |
| `15-create-blockers-full-verify` | 原PID6048/wait0：默认Maven、offline、`-T2`、完整三个模块verify；SaveCore10、RRF116、DES47，共173项零跳过。 |
| `16-create-blockers-complete-five-consumers` | 原PID6844/wait0：真实tools cwd执行完整五消费者63项，进程导入前选择新JAR。 |
| `17-create-blockers-final-strict` | 原PID18560/wait0：整个 `tools/test_compatibility_mod_profiles.py` 的mypy strict/strict-equality。 |

236=最后完整173+最后完整Python63，局部/重复/历史执行不重复计数。全部原Popen wait已消费。reactor列出三模块不代表三模块全部重编；沿用编译缓存，修改的测试在相应增量阶段实际重编。J封包含873个前后源码Pins和55文件图；proof种类为 `COMMAND_VALIDATION`，保留消费者真实tools cwd，不伪装成根目录的 `COMMAND_SOURCE_EXECUTION`。

旧ca1产物55文件、模块JAR、133份源码及旧资格已先归档 `DEV/archives/ca1-artifacts-a01`，身份见 `RETENTION.actual.json`，之后才复用DEV输出。不要以旧证明中的可变DEV路径声称旧字节仍未变化；冻结Native、SDK及旧游戏runtime未热改。

## R0053：失败、保存及关闭

运行 `4-8e1c2f1861--religious-ritual-fusion--R0053`；CK3 PID220，出生时间 `1793279302.748633`。实际Steam EXE为1.20.0.4，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，不能替其他机器核版本。

玩家31254，Rite150/Faith13/Religion8，1066.9.16暂停、虔诚499。Native正常选择同Faith来源B151，免费打开草案。默认三核心缺B方贡献，报价500；实际按钮enabled=false/clickable=false，但原因正文空白。Native父button_group取消一项核心后2/3，原因仍空。没有创建或付费；取消一次，原窗口实际隐藏，钱包仍499。只读 `rrfa.30 no_product_change_readback` PASS一次；一个Native checkpoint后独立held V4确认草案、结果、冷却变量均不存在。

关键资料在 `C16/metadata/normal-close-a01/root-business-oracles-a01`：

- `R0053-PARTIAL-BUSINESS-final.actual.json`：6023B / `48ced46edf0142ff6727a00013bcd884673787016561048bf1e51a1662cba9f4`，最终4/5，business=false。
- `R0053-PARTIAL-BUSINESS-before-offline.actual.json`：717072B / `66215f5148baf727bdcff2f1d1f62f14bbe8e812b6c7522ba94908b64b30c1a6`，完整选定Native事实。
- `single-V4-a01`：一次decode、原wait0、同一拒写/拒删原生句柄身份及raw SHA前后不变。没有完整before-save清点，不能外推全部对象字节相等。

checkpoint为 `C16/managed-states/review-zh-ui-tooltip499-a01/state/profile/save games/xar_checkpoint.ck3`，68414721B / `ba8ebb3a0d32e7e1de03d52c7c05ba7f46b1da5529682c311220039a3b644a84`。

两张真实诊断PNG在 `C16/screenshots/ui-R0053`，均有进程/lease/坐标/悬停sidecar且Root已查看；因显示空白缺陷，**未作为合格宣传图上传**：

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| `01-default-draft-disabled-create.png` | 4236095 | `b84fd8677699344c8993517b8d4cc8a65413d6df79294dc35ee19b1fb6ce7c76` |
| `02-two-core-disabled-create.png` | 4237656 | `ca187551cb5c771576eb42d93ec2945cbb3fb5b290ed241a55041cb801bf78d5` |

13:26:19Z正常关闭：NativeOS0、独立保留OS0、host0、allocator/keeper0，public/verify均2；Root原PID17764/wait2已消费。SCREEN释放14607，显示恢复1024×768。原件 `C16/metadata/public-operations-a01/root-execution-a63/ALL-ORIGINAL-TERMINALS.actual.json`；Root原wait在 `C16/metadata/runtime-preparation-a01/ROOT-SERIAL-UI-a63-original-a01/ORIGINAL-WAIT.actual.json`。原phase incomplete不重写，正常资源关闭不授业务PASS。

## 八项要求的续工边界

R0052部分业务原件：`C15/metadata/normal-close-a01/root-business-oracles-a01/R0052-PARTIAL-BUSINESS.actual.json`，19168B / `f12b642f59e90c814c9557cffe9558cc8a9d503c51db29688b71d6a2b16399a6`；原场19/20，缺完整自然禁用决议提示。R0046/R0051/R0052的incomplete继续保留。

| 要求 | 已有实际证据；尚需注意 |
| --- | --- |
| 界面布局、滚动、长文 | 已有正常草案、原生改革、长名称及结果实拍；最新原因正文待重验。 |
| 创建提示、禁用原因 | R0053禁用正确、文字失败；新代码和回归通过，尚无新实机。 |
| 独立组及顺序 | 已见同Faith在前、跨Faith在后及合法入口亮起，两模式均真实创建。 |
| 决议不再总灰 | 合法亮起已验；修复后的自然灰色决议完整提示待测，特别是持久冷却/缺新来源。 |
| 删除“检查选项” | 代码及已拍新草案已移除，选择自动校验。 |
| 四名、图标、颜色、美德罪恶、改信 | 已有长名称、图标/RGB、7美德+7罪恶、8家属+1封臣采用，同ID免费原生定制及35天后态；SDK continuation身份为空仍GAP。 |
| More Tenets Slots | 无MTS三项、搭配MTS四项已实测，不声称100项实测。 |
| DES可选及通用扩展 | 无DES默认、联合DES非宗族化→宗族化、四核心及35天维护后态有证据；兼容限原生枚举标准教义组，不包含任意第三方GUI副作用。 |

500/1000费用分别为同Faith/跨Faith创建，已测来源仍同Religion8，不声称跨Religion实测。实际宗教地图着色缺county样本仍GAP。历史对比55/60对象仅在有来源窄词法规则下等价，另5角色39处收入/兵力真实变化保留；原archive=false不改true。

## 接班后的执行顺序

1. 重核机器、根映射、Git、任务总线和统一存储策略，读O17闭场及H。旧scene/prep全部关闭，不复用旧G、capacity gate或Steam离线凭据。Java沿用DEV，文档变更不要求重复全量构建；Nativea09不因本次GUI改动重编。
2. C17的FREEZE/SIXQ/BUILD原PID12284/19108/11956均wait0；runtime于14:10:36Z完成。closure明确 `STOPPED_AFTER_RUNTIME_BEFORE_PUBLIC_PLAN_OR_PREPARE`。90文件投影是验收投影，不能发布。global runtime按workshop_cache选取74项能力；cache模板NOT-READY，未提供真实下载/正式manifest。
3. 若沿用C17，独立审查新的范围、时限和容量并重新授予准备写入，再使用既有公共plan/prepare一次。需改路径/当前源码绑定时走freeze/qualification/build_runtime，不能热改冻结图。state预定 `managed-states/review-zh-ui-creation-blocker499-a01/state`，目前不存在。C16的v3/499 fixture本轮29 producer Pins、11 payload文件均raw-equal，可验证后复用，不需无故重新生成。
4. fresh499场沿1800/3600/900预算：默认三项应显示B贡献+499费用原因，减为两项应再显示核心数量原因，实际按钮仍禁用。取消、Native后态、单checkpoint、held V4分别证明；拍两张原始全幅PNG及sidecar。该外部narrow case只有5项，不能算原注册12项整场PASS。
5. 独立保存态的自然灰色决议可复用 `Q/cold-R0045-retry-a01/checkpoints/day35.ck3`，69117980B / `001e9f169c346037de53925b4adcfc0e28db3f4c5e038f077f1c30d1cb89a676`，配C15 v5 completed_snapshot被动fixture、MTS48+DES56闭包。仅day0提示，不必再推进35天/做新checkpoint；仍须Native只读 `rrfa.22 faith_persisted_readback`，不可删mandatory marker。fresh499不替代此冷载。
6. 业务核完后整理合格宣传图、永久changelog和版本说明，再用Java/Quarkus显式90文件canonical manifest生成正式staging。正式release需真实tag解析到相应干净源码，目前未创建0.2.0正式tag；只更新同条目，不上传fixture/源目录/验收投影。
7. 上线仅用于发布/下载；完整标题、说明、Notes、图顺序及公开原图均须匿名回读，再取得真正Steam缓存执行workshop_cache公共验收，最后恢复离线。缓存加载不替代业务实测。

`C17/metadata/generic-ui-serial-candidate-a01/serial-ui-a64.once.py`、scan/gate及 `admit-C17-UI.once.py` 均**未执行、未获Game授权**。a64里的16:15Z仅是假定期限，未签发对应scene G；admission候选假定Prepared已存在，现在不成立，不能直接运行。旧场ready-context、PID/birth、query_generation、widget_id及截图helper都不得当作新实例绑定。

## 商店、缓存与留存

用户确认已完成Chrome物品所有者登录，提供[图片管理页](https://steamcommunity.com/sharedfiles/managepreviews/?id=3826756673)，无需再次索要密码/验证码；届时实际核会话有效性。已公开15图及说明见[截图索引](../../workshop/religious_ritual_fusion_screenshots.md)和[R0046公开回读](../../mod_religious_ritual_fusion/docs/evidence/workshop-media-readback-R0046-2026-10-29.json)。Native追加预览先冻结完整现有顺序，文件严格小于1MiB；真实PNG只作JPEG编码、保留尺寸、不裁切/生成像素，再独立读回CDN字节。未知提交不重放，EResult1不替代回读。

10月25日本机目标DownloadItem曾EResult37/install_info=null；新发布后仍需一次有实际身份的新下载。永久本地阻装项 **2291024373、2993056101、2962333032**，策略 `C:/ProgramData/CK3WorkshopLocalPolicy/blocked-items.json`。不得自动放开DACL、全局退订或编辑ACF绕过；另一台机器五项策略不套用此机。若再有冲突，保留新回执后提出精确处理方案。

R0052 shader及重复restored copy此前已回收3825文件，Allocation229785680B已计gross addback，不得重复记账；完整原输入已不能全部重验，canonical、两份save、图片及冻结证据保留。

R0053只准备候选，**未删除、未记账**：3740 shader文件，逻辑146942067B、Allocation155353904B仍在；两份68414721B save、图片及167项保护引用保留。候选 `C17/metadata/R53-retirement-candidate-a01`：PLAN50919B/SHA `1279d8d86b9ed20fd78eb6765dc2997cea985dde94d0e828e0f207ba92fbd24b`；WRITER-CLOSED6888B/SHA `b4ae767729cf7537630db7a238507cc44999dd1ee6b18dcb166c72309737d824`。最初inventory原wait1（聚合误用HEAD字段）保留，四批完整落盘后的恢复聚合实际成功；不把原1改0。以后采用需重新核最新HEAD、原生身份、保护项、用途及精确执行准入。

统一留存策略继续适用，不永久保留所有场次或缓存。当前Nativea09、新Java图、C17冻结输入、R0052关键保存态、R0053缺陷及236回归的代表证据为复工必要输入，沿当前账本于 **2026-11-01T04:00:00Z** 复核，不自动续期或自动删除。已回收原件必须保持“不可读取”的真实状态，不制造同名替代证据。

最终闭场容量、写入额度撤销、原wait及无活动进程检查以 **`O17/TASK-CLOSE.actual.json`** 和 H 为准；闭场full scan原PID16468/wait0已于14:15:08Z消费。旧48MiB prep额度只用于本次收尾，不传递给接班者。
