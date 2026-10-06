# 休假交接：第4期战争视频——行军、补给与损耗

2026-10-04。用户已同意下一期选题，并明确要求计划和交接文档入库。**接手后的首要目标是按[第4期导演与研究计划](../../promo/ck3_native_war_ai/episode-04-march-logistics/director-plan.md)完成这期20–40分钟的视频，编辑目标30–35分钟。** 暂定标题《大军为什么越走越少？——CK3 行军、补给与损耗》；核心问题是把足够的兵，以能打仗的状态按时送到战场。

本次交接范围是已确认的计划、既有研究入口、素材和后续执行步骤。第4期尚未选定主案，没有新实机实验、正式录像、配音、电影或上传；文档交付不能记成影片完成。此前Steam升级和主线整合已经完成，不重新开启旧分支整合或升级任务。

## 接手先读

| 顺序 | 文档 | 用途 |
| --- | --- | --- |
| 1 | [根AGENTS](../../AGENTS.md)与[任务总线协议](../codex-task-bus.md) | 当前授权、线性Git、屏幕/Steam/输入规范、素材保全和发布边界。 |
| 2 | [第4期导演案](../../promo/ck3_native_war_ai/episode-04-march-logistics/director-plan.md) | 32分钟参考结构、P0研究、A/B/C对照、镜头和完成标准。 |
| 3 | [第3期扩充交接](2026-10-03-war-episode03-expansion.md)与[研究报告](../ck3-native-ai/2026-10-03-war-episode03-expansion-report.md) | 最近的用户审片要求、已讲内容、可复用存档与素材身份、失败attempt及终态。 |
| 4 | [补给容量与损耗](../ck3-native-ai/army-current-supply-capacity-attrition-12003.md)、[行军与抵达](../ck3-native-ai/army-march-remaining-timeline-12003.md)、[补员](../ck3-native-ai/army-regiment-replenishment-raised-reserve-12003.md) | 已有原生入口、实测字段和研究边界。按各节日期及实际append读取，不停留在较早static-ready结论。 |
| 5 | [系列路线图](../../promo/ck3_native_war_ai/series-roadmap.md)、[制作工作流](../../promo/ck3_native_war_ai/production-workflow.md) | 旧集序为历史规划；工具接口与版本按执行时最新正式Release核对。 |

本包阅读源码基线为 `21bfb186d381ae3eba63dbf8b6594508cd00f929`，它不是本包最终提交SHA。接手先fetch并rebase最新主线，核对上述专题有无新增实测，再推进尚未完成的工作。

## 已完成与当前状态

| 项目 | 实际状态 |
| --- | --- |
| 用户选题 | 已同意行军、补给与损耗；20–40分钟，目标30–35分钟。无需重新询问选题范围。 |
| 本工作包 | 计划及本交接，另更新系列入口；实际commit/push和对应CI由最终交付回执记录。 |
| 第3期最终扩充视频 | 已制作并经机器审计；30:37.388，273,653,717字节，SHA-256 `41B7B59922D3D8397E750656E347D2DD6C7985801217F19B34CC3ABD06752175`。 |
| 第3期交付 | 已复制到固定OneDrive目录，两次客户端元数据确认同步；独立远端文件SHA未核验，人工1×完整观看/听审及signoff未提供。 |
| 第3期主线 | 提交 `8e55b31cd2ad5fccd5586da329a3e58e500b775e` 已推送，官方CI [37123014820](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37123014820)成功。 |
| 遗留研究文件 | 465个家徽实验已按原字节归档，提交 `199f96b89e62e2f0a1ab9816796c1b2af2066f2b` 已推送，官方CI [37134403295](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37134403295)成功；保留原失败/待验状态。 |
| 第4期研究/视频 | 既有原生研究可复用；本期新增P0实验、A/B/C正式素材、全文、音频、渲染和交付均未开始。 |

近期已完成工作不要重跑或重新编码来“补交接”；需要新结论或新成片时，建立新attempt并保留旧字节。

## 机制成熟度与具体缺口

既有专题绑定 CK3 **1.20.0.3 / Steam build25652598**，EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`。这是已研究build；接手核对实际安装和加载内容，版本变化就更新新证据，旧证据保持原身份。

| 机制 | 可直接复用的依据 | 下一步 |
| --- | --- | --- |
| 当前补给、容量、月贡献、损耗率 | v43暂停帧已经原生实读：补给100、容量300、当前月贡献+20、损耗率0 | 用新主案跨实际结算边界采样，确认日期与人数写回；这四个值只属于历史Robert帧。 |
| 当前路线、进度、抵达估计 | 已有完整stored route和原生时序，Robert至2610、2604已有独立实际到达 | 正式拍摄停止/改道/锁定前后，记录预计日期与实际抵达。整日四舍五入日期不能冒充精确到达tick。 |
| 补员 | 首record、persistent与chunk回链已有部分实测；v43的40行中26行可用、14行没有首record | 区分补员与补给恢复；剩余record和净人数转移如被口播引用，沿现有专题补齐。 |
| 分兵、会合、合军 | 可复用既有军队操作及观察接口 | 新采操作前后补给和兵团身份；补给合并与当地负担的精确规则未由本计划确认。 |
| 原生AI补给地点选择 | 有stock输入与局部链 | 最终评分/调度/自然选择未闭合，留作后续专题；本期玩家后勤主线可以继续。 |

研究时最易误报的三处：**当前损耗率不等于已死亡人数；当前月贡献不等于未来实际补给增量；军团最大人数减当前人数不等于立即可集结reserve。** 无法排除补员、战斗、集结和分合军时，人数差仅记为净变化，继续取得需要的因果证据。

## 接手后的第一批工作

1. **登记与更新基线。** 新任务register、poll --ack、list；fetch后rebase到最新master。确认没有同目录冻结会话或文件所有权冲突，记录实际HEAD、解释器和游戏build。纯文档/文件研究可并行，受管游戏和屏幕操作由协调者独占。
2. **先完成P0-TERM。** 从当前原版简中localization、GUI及真实tooltip提取术语和单位，建立“key—原文—界面—截图—口播用词”表。工作称呼只作为待校对词，不直接冻结进全文。
3. **筛选并冻结主案。** 优先检查威廉1066研究存档；验证补给压力、合法分兵与两条路线是否足够清楚。另选案例时保留独立身份，不把Robert研究数字塞进威廉镜头。冻结起始存档和每个独立回放条件。
4. **完成最小因果实验。** 先补P0-SUPPLY、P0-LOSS和P0-MOVE，再补分兵/合军与补员区别。针对真实缺失字段沿已有原生专题施工，复用已完成getter，不能为假设问题重复开发整套接口。
5. **按A/B/C取材。** 使用同一冻结出发档的独立回放；每个回放都保存日期、路线、兵数、补给、支付事件与实际到达。单变量实验负责机制因果，完整方案负责决策比较。
6. **冻结口播再制作。** 逐句主张与动态clean span一一绑定，保留条件和身份；小样听审后完整配音，用真实音频重算20–40分钟时间线，再渲染和审计。

主案与机制未闭合前，不先生成30分钟全文TTS或正式长片。M1至M5的工作包、完成条件及状态更新方式统一以导演案为准；本交接不建立另一套分叉进度表。

## 素材、环境与回执位置

| 位置 | 内容及使用方式 |
| --- | --- |
| `D:/workspace/ck3_eternal_recurrence/` | 主工作区；新计划在 `promo/ck3_native_war_ai/episode-04-march-logistics/`。默认从最新master直接工作，需要真实隔离时用短路径detached worktree。 |
| `tools/.venv/Scripts/python.exe` | 本次已核对的主解释器，Python3.14.7。新隔离树优先使用其约定相对venv；回用主解释器要显式指定并验证依赖。 |
| `promo/ck3_native_war_ai/episode-03-siege/expansions/2026-10-03/project/` | 第3期冻结全文、章节、镜头、主张和编辑来源；可参考格式，不能更改旧输入解释历史素材。 |
| `C:/ck3-war-episode03-expansion-20261003-a01/` | 第3期生产、TTS、失败attempt、最终电影、机器/AI审阅、客户端同步及Git/CI回执。入口 `root-final-completion-a01/receipt.json`。 |
| `D:/ck3-war-episode03-expansion-20261003-a01/` | 第3期研究、编辑、cutlists与正式制作冻结；具体raw/save路径从其冻结索引解析，避免只凭文件名猜测来源。 |
| `C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode03-Siege-Expansion01.mp4` | 用户已收到的第3期最终片；按上述SHA识别，不替换。 |
| `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/` | Robert原生研究的实际packet与来源保全；例如 `army-supply-attrition/`、`army-march-progress-actual/`。各专题保存精确路径和边界。此目录内历史“当时最新”存档不直接当作当前普通战役续跑点。 |
| `D:/ck3-git-checkout-audit-20261003-a01/` | 主目录同步、465个原文件备份与归档、199f96b89推送/CI、最终干净工作区回执。不是第4期媒体素材目录。 |
| `D:/ck3-war-episode04-plan-20261004-a01/` | 本次纯文档任务的启动/检查/推送与CI回执；最终按实际生成的 `git-delivery-a01/completion.json` 和 `ci-a01/terminal.json`识别提交与结果。本文冻结时尚未预填这些结果。 |

大素材在外置目录保全，Git保存意图、源码、小型索引与报告。取得新存档/录像后核对完整来源和SHA；旧外置路径不存在时先报告缺失并寻找冻结索引，不制造同名替代件。

## 延续用户已明确的审片要求

- 原生界面要大，不能长时间把画面拆成定位与局部放大的两块静图；优先动态游戏录像，实际按钮与状态结果必须看得见。
- 所有概念使用当前游戏原生中文；“增援”发生歧义时分别说明军队到场、补员和合军。
- 主持叙述先解释条件和操作，再说明代价；比较人数、补给与日期时标明主体、前后时点和单位。
- 人物开场使用漂亮且准确的书签/人物页面，不用丑陋的加载存档页面代替介绍。
- 文本完整校对通顺程度、听众理解、研究边界和与前几期的重复。待确认机制写进研究台账，完成后再进核心口播。
- 第4期预算32分钟，最终20–40分钟；不为了凑长度保留低信息静帧，也不悄悄删掉核心研究却宣称全部讲透。

## 执行与交付合同

实机开始前取得新鲜Steam离线证据，领取任务总线 `ck3-screen:acquired`并按租约/keeper规范操作。旧截图和“上次离线”记录不替代本次确认。桌面点击使用原始截图、实际桌面尺寸、`desktop_coordinate_map.py`及receipt；键盘先确认英文布局和真实焦点。不得把本次纯文档任务视作已获屏幕租约。

开始实际promo工具链任务或新run前查询独立仓库最新正式GitHub Release，记录精确wheel SHA、解释器及真实help。Skill、通用包、CK3 adapter与项目preset的职责按根AGENTS执行；不虚构CLI，不改旧run，不删除失败或中间素材。

棕金包装、中英字幕及唯一音乐沿用系列。逐字节绑定新成片的完整解码、字幕/声音/画面审计与AI实际编码帧审阅；人工1×完整观看/听审、signoff单独记录，机器PASS不能代填approval。

预定第4期交付文件名 `CK3-War-AI-Episode04-March-Logistics-Review01.mp4`，尚未生成。使用固定OneDrive客户端目录，只放用户指定的单个视频，复用既有同步设置；如实记录本地复制、客户端同步与独立远端校验各自状态。外部平台上传仍需独立明确授权。

每个完成的独立工作包默认commit/push，推送前poll --ack、fetch/rebase；仅普通fast-forward push，等待对应exact SHA官方CI终态。采用新短期分支确有必要时，完成后及时回主线并依根AGENTS清除分支ref；历史提交和素材用既有归档方式保全。

## 可直接交给接手者的任务说明

> 继续制作第4期《大军为什么越走越少？——CK3 行军、补给与损耗》。先读本交接与第4期导演案，再登记任务、更新主线和研究状态。先提取原生中文术语，选定并冻结主案，完成补给/损耗结算、路线修改和分合军的最小因果实验，再从同一出发存档独立拍A/B/C。已有研究按真实身份复用，缺失因果补齐后才冻结口播。目标30–35分钟、交付20–40分钟，大原生界面、动态操作视频、清晰条件和代价。所有旧素材与失败attempt保留；单个指定最终MP4通过固定OneDrive客户端目录交付。完成工作包及时线性提交推送，报告实际CI与同步结果。

## 文档提交后的CI复核

首个三文档包已通过32分钟预算、21个本地链接与既有来源核对，并以 `311187b0bd3e69e24b70f01ae6b7ba70df7c7ef8` 普通推送到master。[官方CI37139691990](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37139691990)实际失败：`test_public_cunit_mcp_contract.py`仍直接读取终局查询参数的顶层`minimum`，而该接口已允许null上下文，整数范围位于`anyOf`整数分支。原生产接口及service均已声明并支持该nullable语义，不能为修测试撤销它。

修复只更新MCP契约测试：验证终局查询的integer/null两种schema分支、合法null转发，同时保留所有军队ID的0及上限、布尔/浮点/字符串/越界拒绝检查；其他必填军队参数继续拒绝null。与CI相同的四份测试在普通及`-O`模式均实际通过，各为30 tests、351 subtests；没有游戏/原生transport调用，没有修改生产API。

首次失败回执保留在本任务外置目录的 `ci-a01/terminal.json` 与 `ci-failure-a01/`，本地两模式回执在 `ci-repair-tests-normal-a01/`、`ci-repair-tests-optimized-a01/`。测试修复与本节为独立收口提交，真实普通推送及官方新CI结果分别由随后生成的 `git-delivery-a02/completion.json`、`ci-a02/terminal.json`记录；本节冻结时不预填其SHA或PASS。首轮CI失败不回改成成功，第4期研究与媒体状态不因测试修复增加信用。



## 2026-10-04 接手后的首批增量

用户已授权开始高并发研究与拍摄。接手者应继续读[第4期研究总账](../../promo/ck3_native_war_ai/episode-04-march-logistics/research-status-20261004.md)及[证据索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/candidate-index.json)，不要停留在本交接初版“尚未开始”的时间截面。首批TERM/SUPPLY/LOSS/SPLIT/MOVE/REFILL、主案、费用及capture文件包已经交付；静态、offline fixture、历史live与本期live分层记录，不能混加完成信用。

当前已核对Jan11登陆候选SHA `d94be518cc52fefb62d896de8fabc8bd560f49674925049dab863cef77a1e14b`，尚待新冷载检查后保存第4期A/B/C出发档。真实补给时钟及`army_update_clock_v1`已在主线，复用现原语；逐团actual人数与Halt最小增量已入源码，Root负责严格构建、部署和当前案例后读。原生构建收据built不等于新实读；截至Root文件研究切点尚无本期SDK/新游戏日/录像，Halt f853官方CI失败待修，其他研究包不因该CI等待而停止。

后续先取得当次新鲜Steam离线及当前运行输入，再闭合总账的六项P0门槛与11项真实tooltip；同档独立拍A/B/C后才冻结全文、配音和成片。旧原片、失败候选、环境RED及既有存档原样保留。Root另存本批文档真实commit/push与exact SHA官方CI；本增量不预填影片或交付完成事实。


## 2026-10-05 R0169接手增量：原始术语齐，继续先筛正值B

后续从[研究总账](../../promo/ck3_native_war_ai/episode-04-march-logistics/research-status-20261004.md)及[R0169 portable索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0169-terms/index.json)继续。按原定义，十一项术语原始研究已齐，各自编码绑定10/11；移动锁定Jan25同paused首边61.875%两原图在rawfinish后保持encoded=null。不要再重复已闭getter或把Root八个实际编码单帧扩大为24全审/连续clean/1×签核。库内小JSON与只读脚本可跨机器复算数字，外置PNG/录像仍按原path/hash保全。

本地B到Arun1508实际+9日仍无正月补给，两半current/max/27FullID保持，总6746/6747；不是ABC回放，完成仍0/3。下一独立有限warmup先核实际友好资格和whole正月值，再保存新的共同出发档，不沿用静态titlehistory或预览当抵达/友好证明。Dfullkeeper失败与已完成媒体PASS各自保留；Root已证明SDK/游戏树收口。未响应route probe、付款流水、饥饿阈值/独立归因、clean段、全文/TTS/成片/1×/签核/指定OneDrive视频交付仍待各自真实证据。


## 2026-10-06 实际 Review01 制作收口追加

最终六章Review01实际输出28:55.80，69段中文与326组双语字幕；新整片机器审计PASS，Root实际看过18张最终编码单帧。A抵达观测(49,51]，B第38日冻结条件变化而停止，C抵达观测(75,77]且15次采样偏差保留；本片没有ABC因果赢家。真实低库存饥饿扣兵、补员/付款流水、精确50%锁定和AI最终选点评分仍是研究缺口。正式审阅包为pending-human-review，人工1×完整观看与签核尚未完成。OneDrive结果及最终知识/代码相对包入口见[最新实际交接](2026-10-06-war-episode04-review01-delivery.md)；旧attempt、RED和当时NULL不回改。
