# 《礼与道》度假交接：2026-10-06

用户要求：“你要去度假了。平稳结束手上每件任务，不要再开启新的任务，然后编写交接文档到docs，提交推送。”本轮据此停止开发和实机续跑，现有并行支线已交付封存包并结束。后续只完成已经进行中的源码同步、必要回归、证据归档及提交推送。没有启动 R0013、新的 clean HEAD 导出／构建、游戏或新代理，也没有发布创意工坊。

一期完成度暂估 **70%**，属于工作量估算。**整个 mod 尚未验收通过。** 已证明同一战局可以吸收→拆分→再次吸收，最终吸收后的冷重载也通过；正式宗主章程、争统及完整修习矩阵仍待验。原定 10 月 7—9 日节点因用户暂停撤出执行安排，恢复后再依据实机结果重新排期。朝代分隔仍在二期。

## 已提交的源码及证据

源码与三份报告已在 `master` 提交并推送：

```text
ee752979e75029a86e972f9cdcc7a793dc6705dd
Add Confucian readonly queries and preserve cycle acceptance
parent: fdcf91183f33a049d111fd4267f1079eabfb6d06
mod_li_yu_dao tree: 6ac828e3539b668e6b2dcf11d3dbd198fab6c4c2
```

推送进程退出码 0，远端范围为 `fdcf91183..ee752979e`，随后本地 HEAD 与 origin/master 相同且工作树干净。服务器提示必需的 `CLA / signed` 尚未提供并允许当前推送；这不是 exact-head CI 通过证据。本轮不启动新的 CI 跟踪任务。历史 `632f0a57a` 的通用 CI 成功、专题与 CLA 未触发，不能外推到这次提交。

集成先后两次 rebase，因远端并发更新第一次 push 被拒绝，没有 force push 或 merge。两次冲突均为 `native_bridge/CMakeLists.txt` 尾部；保留远端新增 include 和本轮两个原生测试目标。第二次远端同时更新 shared `service.py`，因此再次运行必要的 17 项 Python 回归，实际退出码 0。两个重放后的回归回执分别为：

- `BASE/r13-root-rebased-python-focused-tests-20261006-002`，09:45 UTC，17 项通过；stderr SHA `6857947ffb3e07a5a0f8c6ae7534b2825ad40101b9b5c5e6ac444b13a6d14164`。
- `BASE/r13-root-rebased-python-focused-tests-20261006-003`，09:50 UTC，17 项通过；stderr SHA `a49c28930689b6ddd3758d12bedfb1a20da30f640c15b907bd1c8f6baf0a4446`。

原始 argv、RESULT、stdout、stderr 已收入本次[完整归档索引](2026-10-06-li-yu-dao-vacation-evidence-complete/INDEX.json)。没有在 rebase 后重编 native，因此历史 DLL **不能作为新 master 的编译或实机资格**。

## 真实验收边界

| 工作包 | 已取得结果 | 遗留 |
| --- | --- | --- |
| I1 经学、道学及选派入口 | 代表入门、取消、朱子择师／修习保存回读通过；36 礼仪、36 信条、36 修习内容已在源码 | 不能把代表路径外推为全部 36 派通过 |
| I2 授权及反复分合 | R10 正式吸收／拆分 183／120 项；R11 再次吸收 100 项、同一战局循环 10 项；R12 最终冷重载 58 项通过 | 使用明确记录的夹具冷却／重试重置；自然五年冷却及 365 日到期未验 |
| I3b 宗主章程 | 正式授权链源码已经整合；名册、资格与宗教头衔只读查询／存档检查器已接入 | query→同帧 checkpoint 转换器未安装；正式成立、各级签署、原生头衔、争统及重载未验 |
| C3 争统 | 正式准入源码及检查器存在；已有当前宗教头衔读回 | 实际独立 NPC 在任宗教领袖未建立；完整 challenger／sponsor 原生集合仍只有外置草稿，无第 24 项封装 |
| I4 完整内容矩阵 | 八项正式 L0 通过；外置 016 矩阵和请求模板封存 | 36 派完整修习、拒绝／撤回／到期／重载等实机矩阵未跑；军会／圣物未实现 |
| 二期 | 历史学派与内容设计已有 | 朝代分隔尚未实现 |

永久报告及原始索引：

- [R0011 再次吸收及同战局循环](../li-yu-dao/acceptance/2026-10-06-r0011-632f0a57a/REPORT.md)，[实际入库回执](../li-yu-dao/acceptance/2026-10-06-r0011-632f0a57a/ROOT-IMPORT-CHECKS.md)。INDEX SHA `85aa58f2a6de0e5177bcd7986a9dc190f6ffc1fb20b88245c26b5b7b8a3fdd81`；2,180 条原始引用、1,665 个唯一对象。
- [R0012 最终冷重载](../li-yu-dao/acceptance/2026-10-06-r0012-632f0a57a/REPORT.md)，[实际入库回执](../li-yu-dao/acceptance/2026-10-06-r0012-632f0a57a/ROOT-IMPORT-CHECKS.md)。INDEX SHA `02937bdf1b2b38b103f723860827b27fcc559ee6b66b7fa5e0f6242ef53c62b3`；532 条引用、381 个对象，复用 R11 STATE 时没有重读旧存档。
- [宗主／争统只读源码 L0](../li-yu-dao/acceptance/2026-10-06-post-r12-readonly-source-l0/REPORT.zh.md)，[实际入库回执](../li-yu-dao/acceptance/2026-10-06-post-r12-readonly-source-l0/ROOT-IMPORT-CHECKS.md)。INDEX SHA `c161c13feb1d8c143e59bccf33e33d49efccba51b5028cf84237be15775d4f07`；48 个源码目标、17 项 Python 回归、两项首次 native 测试及 Python-only 检查。

历史 UNKNOWN、首轮失败、部分日志覆盖及旧 attempt 保持原文。观察到的 readonly 值不等于业务授权通过；顺序切换角色也不能当作同轮全部人类玩家签署。

## 已整合 MCP 能力

默认正式 MCP 仍为 **21 项工具**。显式 `--confucian-readonly-tools` 或 `create_server(confucian_readonly_tools=True)` 时为 **23 项**，新增：

```text
ck3_query_profile_confucian_assembly_predicates_v1
ck3_query_profile_confucian_religious_title_v1
```

这是两项儒家只读查询，不能与 player-control 的 23 项配置混淆。只接受严格正 uint64 的 `expected_revision`，进入 native 时使用 canonical `expected_snapshot_revision`。信仰完整角色名册、资格、礼仪及县名册，宗教 Title 完整代际 ID、持有人、四项属性及法律均有源码读取路径；script-owned 和 owner-Faith 仍需独立 typed 存档证明，不能填造 NULL。

新增 native flags 默认 OFF：

```text
XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1
XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1
```

构建时使用原有 8 项加两项新开关，共 10 项 ON；player control OFF，testing ON。安装的 20 个 native、23 个 checkpoint reader 和 5 个 Python 目标在 root 的精确应用回执中记录。提交前 13 个 JSON 做 CRLF→LF、两个 parser 去掉末尾额外空行，JSON／AST 含义保持；[归档](2026-10-06-li-yu-dao-vacation-evidence-complete/INDEX.json)中的 `r13-root-reader-line-ending-projection-20261006-001/RESULT.json` SHA 为 `5454f67b92fe4c29e5e13cd56a13f7d144e3434c1bb09ed4b319e61852af3f8a`。旧原件哈希不追改。

### 历史构建不能复用为新 HEAD 资格

`C:/lyd13-native-20261006-001` 是 `632f0a57a` 加本轮 dirty 源码的历史构建。canonical MSVC Release、64 jobs、四个 target 实际编译成功，但 wrapper 外层退出码 1，原因是 Defender WMI 设置失败；首次 CMakeCache CRLF 正则核验也错误返回空 flags，从而跳过测试。这两项原始失败已保留。

补充核验修正换行解析后，**没有重新构建**，首次运行了两个已编译的测试：名册测试实际 `PASS checks=70 actual_reader=true actual_serializer=true live=false`，宗教 Title 测试退出码 0。该补充不能覆盖原始环境 RED，更不能证明 rebase 后的代码已编译。

| 历史产物 | 字节数 | SHA-256 |
| --- | ---: | --- |
| DLL | 6,806,528 | `c0a48a4cd7ecdeb402f62426a17a62ac34e4635fda2bf4a6fb3ca87bdc059fbf` |
| injector | 39,936 | `d22db5c67597889fdbf62620e604c4612ec9c7386be04f1ff05c43fa1ebcaf9a` |
| 名册测试 | 119,808 | `ad69d9233ff397d730a0e9116844b23c51a718cd793ac24d9fac7e2792ffc75e` |
| 宗教 Title 测试 | 100,864 | `b72cb24651a62d4b1b947e01363cf9a1ddb27f7c32ca09623f77e2a8138a03ad` |

实际构建回执为 `BASE/r13-root-actual-native-build-20261006-001`；首次测试补充为 `BASE/r13-actual-compiled-first-focused-supplement-20261006-001`。原始构建目录、3,454 件编译输入／输出保留，不清理；新恢复轮次应以新 clean source 构建并获取自己的 Defender 实际读回。

## 游戏现场已经结束

R12 原 CK3 PID 3276、creation FILETIME `134357481751404466` 已从保留的原句柄观察到退出码 0。MCP Client PID 14412 关闭、keeper PID 16440 结束，CAS 释放序号 **3303**；Client 和 keeper 的 OS 退出码没有取得，保持 NULL。

实际关闭边界：

```text
BASE/r12-root-actual-closed-boundary-20261006-001/PREVIOUS-BOUNDARY.actual.json
SHA-256 fb36f6044473f4e3ad22c652a2fb9c4ba29d8f8c63180c3f7b8f079451498d9f
```

本次收尾的只读进程 census 未发现 CK3、该轮 MCP 消费者或 R11／R12 keeper，三个已知 PID 均不存在，读取异常为 0，没有发送任何进程信号。回执 `BASE/vacation-root-closeout-observation-20261006-001/PROCESS-CENSUS.json`，SHA `37fd7041aea446c49b38a3725ad25c63c5f8551c034e277624a7d6a8f96d2a67`。总线新鲜 list 无 screen holder；旧的无关任务若 stale，未接管或改写。

本机永久 CK3 实机授权继续有效，见[授权原文与范围](2026-10-05-ck3-lyd-local-permanent-runtime-authorization.md)。恢复开发时无需再次要求用户同意使用本机 CK3。仍需当次新鲜 Steam 离线画面、独占 screen lease 和精确 source/profile。R12 08:07:58 UTC 的离线图是历史事实，不是未来启动的离线证明。本轮没有改变 Steam 模式，也没有进行桌面／OCR 兜底操作。

## 恢复时选择正确的存档

本文 `BASE` 固定指 `C:/workspace/ck3_lyd_runtime_20261004`。大存档正文不进 Git，原件永久保留；本次归档没有读取这些存档正文。

### 宗主章程：原 R10 的 0240 分立存档

```text
BASE/live-attempt-010/checkpoints/0240-detach-second-post-save/checkpoint.ck3
91,669,783 bytes
SHA-256 1d98f0d2482c02477f460127044690b1df128e806b2ffbfab399e945e3551a1d
```

这个分支 Faith107 的主礼仪是 169，**没有 HoF**，HoR169 是 actor31254。actor31254 和 NPC65865 属礼仪169；接收方 NPC65866 是 Faith104／Rite159。Faith104 主礼仪159、Faith106 主礼仪187。历史 JOIN2／DETACH3、nonce16、result1、reset6，冷却1825天、学校349；钱包 1043 gold／3150 piety／2200 prestige／XP0，日期 token53144712。I3b 本身不需要人为重置分合冷却。

正式路线必须由 `lyd_i3b_begin_decision` 进入：实际代表事件410及 seal→学者411→所有受影响人类412→逐派三分之二和最终签署413→原 native factory/commit。不能以旧测试夹具直接执行 charter 原语冒充正式链通过。公开事件 option 编号与 native index 的关系是 `public = native + 1`。

实际形成宗教 Title T 后，C3 只把 **该新 T** 交给同 Faith NPC65865，证明真实独立在任领袖再挑战。保持 HoR169、七个政治头衔和其他人物身份；不制造第二个 factory，不用 HoR 维修或伪激活替代前提。

### 最终循环保持性：R12 的 0005 存档

```text
BASE/live-attempt-012/checkpoints/0005-final-join-cold-reload-save/checkpoint.ck3
91,739,977 bytes
SHA-256 736f01563e8e82687a9b5bb7d18d988359ea32e69b4b122c9dd3d868b1c96a98
```

58 项检查已经通过：Faith104 主159，Rite169 parent104／HoR31254／无 HoF；Faith107 主188，Faith106 主187。历史 JOIN3／DETACH3、nonce20／serial20／result1／reset8，钱包743／1650／2200／XP0。stress 的存档值 NULL 与 native0 分别保留。该终局不适用于需要 Faith107 主169的 I3b 基线。

## 未合入候选及各支线收尾

以下包均只保存在外置目录及惰性档案。source-only、partial draft、未来 HEAD／PID／Title／revision／业务通过状态原样保留；**本次封存没有安装或执行候选**。完整归档 INDEX `209957 bytes`，SHA `5debf3e63540798a6452d93f8c20016c5405764e8a2b68cbe56ed64a5dbcb7d6`：284 条引用、243 个唯一 gzip 对象，压缩总计622674字节。还原方法见[归档说明](2026-10-06-li-yu-dao-vacation-evidence-complete/README.md)。

| 外置包，均为 BASE 下路径 | 状态／下一入口 |
| --- | --- |
| `i3b-sdk-checkpoint-qualification-adapter-20261006-001` | 未安装的 add-only 转换器，EXPORT-MANIFEST 10目标；最终 `sdk_checkpoint_qualification.py` SHA `cee4573ec1fd8e9151869d2cb63733297b795d1c36acdd82c06631845db588c3`，15项新测试通过。采用修后的候选，不用首轮3fdf版本 |
| `i3b-sdk-checkpoint-seam-review-20261006-003` | 独立复核四类负例、9子例通过；旧 review002 FAIL 保留。真实 compiled/session/checkpoint绑定仍为 NULL |
| `i3b-r13-formal-route23-20261006-001` | 0240 正式路线、60项 MCP 请求模板（47正式＋13查询／保存）、5个资格窗口；ROOT-ENTRY 第一次snapshot为 `{}`，未运行 |
| `c3-native-challenger-graph-addon-20261006-001` | **部分草稿**，10目标（4共享＋6新增）；未评审、编译、测试、应用，Python/MCP第24工具未写。共享 before 来自旧 native003，恢复时只增量 rebase hunks，禁止用旧 CMake/bridge 全文覆盖新 master |
| `i3b-current-faith-challenger-sponsor-abi-contract-sourceonly-20261006-001` | exact-build ABI研究；Faith数组+0xC0、count+0xCC、stride8；challenger full Title ID +0／sponsor +4。容量+0xC8未知，不能假定。`challenger_sponsor` 按 challenger-holder 当前Faith，须与旧ownerFaith集合区分 |
| `readonly-revision-inline-sourceonly-20261006-001` | 只读 revision JSON helper 的源码候选；39表案例＋4动态案例仅为拟议测试，未执行，不为此单独扩大施工范围 |
| `i3b-is-imprisoned-abi-contract-20261006-001` | is_imprisoned 静态链及10项指令检查完成；live=NULL；读取失败不能记成“未囚禁” |
| `lyd-r13-official-mcp-private23-template-20261006-001` | 14项新增 source-only 检查通过；保留once/queue/原句柄退出；未来资格未绑定，不能沿用旧632的8flag gate接受新10flag DLL |
| `r13-clean-source-metadata-routing-20261006-001` | 11项新门禁通过；旧dirty DLL vs旧export CMake差异正确拒绝；default21/explicit23官方 metadata 尚未实际捕获 |
| `r13-canonical-head-export-helper-20261006-001` | 10项纯叶检查通过；要求真实40位HEAD与新输出。拟用 `C:/lr13s1`；导出未执行，恢复时重新确认目录可用 |
| `r13-clean-native-build-helper-20261006-002` | 新 clean HEAD native构建模板；拟 `C:/lyd13-native-clean-20261006-002`；显式actual HEAD＋execute、4目标／2focused tests，修正CRLF。没有执行构建 |
| `r13-launch-profile-input-templates-20261006-001` | 原9字段profile、已知第10字段正常退出、14字段freeze输入；未来cold、profile、guard、lease、PID全NULL。`live-attempt-013`尚未启动 |
| `r13-c3-private23-route-adaptation-20261006-001` | C3 N2/N4–N13 对实际I3b新T与NPC65865的未来操作表；G3当前宗教Title读回不能证明完整challenger/sponsor；script marker仍NULL |
| `i4-matrix-resume-review-20261005-001/pf8-frozen632-cold-inputs-016` | 162引用／130payload／153正式21模板。仅索引与报告进入本次归档，其余原件外置保留；36派108付费＋36取消、14修习4类路线；5代表成功＋3负例只是待执行矩阵 |

各包原始 INDEX、SHA和全部小型候选／回执在归档 INDEX 中逐件关联。I4 INDEX SHA `f3bf4bd225dd9bada1a1ea24e00e099266e62a8bbc97ad1468e2afabadcea4c6`。此前内容校订、经疏原典、R6–R12读回、MCP回执与正常退出、切人能力、CI及容量检查支线均已结束，已有主线报告或外置封存；没有仍在运行的子任务。

封存 importer 首次遇到独立 review 的 INDEX.files 为字典而失败；第二次准备迁移 partial 时 Windows 返回 WinError5，迁移没有完成。原42个 gzip对象、原 importer、两次失败事实保留在[partial回执](2026-10-06-li-yu-dao-vacation-evidence/PARTIAL.json)，未删除或覆盖。第三次兼容 list/dict/artifacts，写入新 `...evidence-complete` 目录成功；这只是归档工具修复，不是产品测试 RED。

## 恢复顺序

1. 用户恢复任务后，读取本交接、[产品进度](../li-yu-dao/2026-10-06-progress.md)、[验收矩阵](../../mod_li_yu_dao/docs/acceptance-matrix.md)及最新 master；按总线协议登记新执行段。复用报告，不重跑无变化历史案例。
2. 按 converter 的 add-only manifest做最小集成；保留现有 parser机械投影，不用旧dependencies覆盖。转换器必须绑定实际同checkpoint、source/session/PID、native/publicrevision及日期；G2/G3 capture_epoch互相独立，不能要求相同。无法读取的字段继续NULL。
3. 取得新的干净HEAD export，运行新canonical native构建和两项focused tests，分别记录编译事实及Defender设置事实。随后实际捕获官方 default21／explicit23 metadata；旧dirty构建不能冒充新clean资格。
4. 沿用本机永久授权，取得新鲜Steam离线像素和独占lease，以0240真实存档建立新cold/source/profile/privateSDK Client；执行新G2/G3读回及同帧保存资格，再走I3b正式完整批准、factory/commit、独立save/delta和冷重载。
5. 用实际新宗教Title建立NPC在任领袖。评审并增量实现C3完整challenger/sponsor查询及显式24工具封装；取得新原生读回后执行正式争统、拒绝／撤回／死亡／清理／重载，不以当前G3单Title替代全集合。
6. 完成I4矩阵，包括natural expiry与重载。无HoF分支和有HoF分支分别用真实存档，不通过删除已建立领袖来“准备”普通修习。
7. 每轮保留原始失败、UNKNOWN与过程资产，验收报告落地并提交推送；全一期仍需要实际业务结果才能标GREEN。正式Workshop发布是后续独立交付，本轮未进入发布阶段。

本机只用 Python／cmd 路径，无 PowerShell。MCP-first仍有效；GUI/OCR不能成为游戏状态真值或业务通过证据。所有旧原片、存档、runtime、构建输入、partial和失败 attempt永久保留。最后的交接提交以本文件的 `git log -1 --` 为准，不要求在文档内自引用其提交SHA。
