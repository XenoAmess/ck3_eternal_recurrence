# CK3:信仰引擎二期 V6 黄色版：休假交接

**当前成果是24分30秒的黄色完整审阅版《朝圣在奖励什么？》，已本地交付。制作已收束，没有待续拍或待完成的编码进程。完整人工听看、用户内容签收仍待，不能把“一期成功”外推为二期已获认可。**

用户本次要求：“你要去度假了。平稳收尾手上的工作，编写交接文档，输出到docs。”本次只收尾和交接，不开启下一轮研究、拍摄、配音或渲染。

编写日期2026-10-22（北京时间）。`machine_id: 4-8e1c2f1861`，本轮重新运行 `tools/ck3_live_run_id.py machine` 核对；接手基线 `caf5ff5bf81f102b7b1cf01d7ab074eb2d2943de`。文件核对实际时间 `2026-10-22T09:57:31.553529Z`，进程观察 `09:57:31.580796Z`。本次小型核对见[机读回执](../ck3-native-ai/evidence/faith-engine-episode02-v6-vacation-handover-20261022.json)。

## 1. 接手从这里开始

| 顺序 | 入口 | 作用 |
| --- | --- | --- |
| 1 | [二期入口](../../promo/ck3_faith_and_power/episode02/README.md) | 当前黄色视频、字幕、讲稿；旧版仅为历史。 |
| 2 | [本轮制作记录](../../promo/ck3_faith_and_power/episode02/docs/production-v6-local-review-2026-10-22.md) | 原片、声音、黄色修订、实际媒体检查与研究边界。 |
| 3 | [连续导演稿V6](../../promo/ck3_faith_and_power/episode02/docs/director-v6-pilgrimage.md)、[自审](../../promo/ck3_faith_and_power/episode02/docs/director-v6-self-audit.md)、[图表分页](../../promo/ck3_faith_and_power/episode02/docs/director-v6-screen-tables.md) | 当前叙事与固定算例，不从旧七章案重开。 |
| 4 | [当前研究说明](../../promo/ck3_faith_and_power/episode02/docs/pilgrimage-current-knowledge.md)、[机器可读索引](../../promo/ck3_faith_and_power/episode02/docs/knowledge/pilgrimage-current-12004.json) | 七个研究包的有效结论、继任关系、来源与未知。 |
| 5 | [智能体参考入口](../ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md) | 研究怎样被游戏智能体查用，以及动作资格边界。 |
| 6 | [品牌](../../promo/ck3_faith_and_power/series-brand.json)、[制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md) | 黄色图表、声音、配乐、文字与实机表达规范。 |
| 7 | [一期成功交接](2026-10-20-faith-engine-episode01-success-handover.md) | 一期已经讲完的内容与用户已确认的成功基线。 |

## 2. 当前交付与身份

以下路径均属于机器 `4-8e1c2f1861`。跨机接手必须重新确认实际文件可读，Git中的路径记录不等于媒体已传到另一机器。

| 项目 | 当前结果 |
| --- | --- |
| 主题 | 朝圣在奖励什么？区分支出、活动评价、虔诚奖励、人物成长。 |
| 内容 | 33段旁白、196组中英字幕、28页主表、四段实机界面。 |
| 时长 | 44102帧，24:30.067；101秒额外静读已包含。 |
| 媒体 | H.264、2560×1440、30fps；AAC、48kHz双声道。 |
| 文件 | 70,102,554 B。 |
| 视频SHA-256 | `a73ead885dc93390a644e6ff65fb2607d3f705a452e7a467c210ff10a276f5d4`，沿原生产者记录；本轮没有重哈希视频。 |
| 制作结果 | 原PID13544于07:46:17.841701Z等待返回0；完整AV解码、44102帧PTS及五个配乐窗口通过。 |
| 有限画面检查 | Root于07:49:24.658285Z直接审阅五张最终编码帧，黄色配色、公式脚注及字幕分区通过。 |
| 审阅状态 | 本地审阅版；完整人工1倍速听看和用户内容签收未完成，未上传平台。 |

| 文件 | 本机直接入口 |
| --- | --- |
| 当前黄色视频 | [episode02-review.mp4](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/episode02-review.mp4) |
| 双语字幕 | [episode02.bilingual.srt](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/text/episode02.bilingual.srt) |
| 中文字幕 | [episode02.zh.srt](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/text/episode02.zh.srt) |
| 英文字幕 | [episode02.en.srt](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/text/episode02.en.srt) |
| 实际完整讲稿 | [episode02-script.md](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/text/episode02-script.md) |

本轮核对上述五个交付文件的存在和大小；四个小文本SHA与原交付索引一致。另核六个关键小输入／回执的字节与SHA。没有再次解码、抽帧、播放或重配音。

本机按用户[交付偏好](../maintenance/machine-preferences/4-8e1c2f1861.video-delivery.json)仅本地交付；不要求配置、重试或上传OneDrive。该偏好持续到用户明确变更，不因本次休假或过程资产到期而撤销。

## 3. 用户要求与目前内容

用户否定了早期版本与一期重复、东拼西凑、像游戏实况、没有讲深机制的问题。当前主题已经收窄为朝圣专题，讲解应提供玩家观察机制的新视角。不能回到“已有圣地，下一笔资源投在哪里”的旧七章拼接，也不要为凑足30分钟扩写；用户已明确无需严格30分钟。

用户要求的四个方向均有研究与导演内容：

1. 活动配置与意图：10项活动配置、29项旅行选项。旅行选项中12项有显式费用，17项无直接cost定义，后者不等于整趟免费。共享意图机制有四类；R32本次天主教人物菜单实际显示深思熟虑、行善、热忱三项，不能普遍称固定四选一。
2. 宗教差异：禁止、鼓励、当地仪式、强制、朝觐五种朝圣态度，分别解释资格、奖励与身份；“允许朝圣”是资格，不另算一档态度。麦加初始化直接授予身份与完成一趟朝觐分开。
3. 朝圣者影响库存：169条来源条目，其中118条按主片处理，51条历史／生成人物／调试来源以分类说明和参考资料处理。不能宣称169条均已逐项口播。
4. 费用、虔诚和经验：用同一组F0条件拆解，再以F1—F3解释单项变化；脚本模型、当前界面报价、实际扣款和完整旅程分别记账。

研究与演示基于CK3 **1.20.0.4**，已绑定的EXE SHA为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本轮交接没有重新哈希EXE，也没有证明当前安装可直接用于下一场。

## 4. 容易讲错的结论与研究缺口

- F0的176只是已展开脚本费用模型，独立主管出发俸禄L仍未知；R32的70是另一份配置预览，未出发付款。不能互相拟合，也不能把未知当0。
- 同一活动表现增加10分是否跨档，要看起点。示例65→75使主虔诚112.5→150；事件即时25虔诚另列。费用距离输入与奖励距离输入分别指定，不能互推。
- 经验执行器将trait与track增益加到1后单次乘，向零截断，再加旧经验并夹到0—100。原XP80时，基础请求20或40都只实际增加20；不能把请求量当到账量。
- 官方简中名称以本地化key与引用链为准，包括中世纪早期、旅队主管、个人信条、主流礼仪、户部／户部尚书、朝觐者／朝觐妇。参阅当前索引绑定的三份术语JSON，别按习惯改译名。

近期费用研究最明确的三个继续入口见[旅行费补记](../../promo/ck3_faith_and_power/episode02/docs/research-v6-travel-fee-boundaries.md)：

| 未闭问题 | 已知边界 | 下次需要补的证据 |
| --- | --- | --- |
| 主管出发俸禄L | GUI接收当前／已选主管；0.10金币月薪不是L | exact .4 getter到script key、实际root及两个称职度scope的构造与求值。 |
| 补给 | 无地冒险者且随营地旅行的独立显示门，独立资源 | GetProvisionsCost的producer与实际输入；不拿隐藏区或其他补给常量代替。 |
| 最终合计与付款 | TravelPlanner与ActivityPlanner是两层报价；现有有界reader读取当前ActivityPlanner +0x1B10 | 两者聚合、主管／选项包含关系、负费用钳制、人数去重及扣款消费者。 |

这三条不是全部剩余未知。当前索引还列明脚本值转raw、异常抵达缺limit默认语义、动态来源实际激活、共享娱乐上游合并与其他人物CanPick、通用冷却、灵性满足日历变化及AI整体消费等问题。接手者应从 `retained_unknowns` 逐项读取，不能因XP静态算术已闭而把整套机制写成全部验收完成。

## 5. 研究确实可以给游戏智能体使用，接线范围要分清

当前JSON索引绑定七个研究包的14份原件、字节数、SHA、JSON Pointer继任关系；游玩智能体先读 `consumer_contract`、`effective_claims`、`retained_unknowns`，再按 `subject_package_ids` 下钻。旧包中只被部分继任的句子不能整句改成“已解决”。

R32观察与旅行费补记是索引生成后的补充，沿[智能体入口](../ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md#2026-10-22-r32观察与费用边界补记)读取，不回写旧包的观察时间。原有知识MCP能检索部分历史topic与已分析事件；V6新研究索引本身没有因此自动接入普通auto。

始终保留 `action_ready=false`、`ordinary_auto_consumes=false`。可读研究不是当前CanPick／CanStart，不是动作执行授权或新业务成功。换角色、存档、机器或build，要重新读实际身份、配置、许可、价格和后态。历史一次性建制已有账本，不得为了补片重新提交未知或已消费的操作。

## 6. 黄色视觉、声音与制作输入

用户最后指出“图的颜色为什么不是我们系列的黄色，而是蓝色？”直接原因是独立图表生成器写死青蓝色板。已按既有 `full_diagrams.py` 重新生成55张图，替换273处引用；文字、字号、bbox、阶段、声音、字幕和切点不变。原蓝色完整稿在 `O/full-grant`，黄色版在 `O/yellow-revision-a01`，不得混用通过结果或覆写原attempt。

`O` 为本机工作根：`C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01`。关键文件以O为基准：

| 路径 | 用途 |
| --- | --- |
| `yellow-revision-a01/authoring/YELLOW.FORMAL-INPUT.actual.json` | 实际黄色剪辑输入，661697 B，SHA99894377…71182。 |
| `yellow-revision-a01/authoring/PROJECTION.actual.json` | 证明仅55图引用与存储grant变化，反投影回a10相同。 |
| `yellow-revision-a01/graphics/REPLACEMENTS.actual.json` | 55张新旧图pins与273处引用。 |
| `yellow-revision-a01/graphics/yellow_graphics.py` | 本次代码原生图作者入口；依赖的旧生成器仍在O内，不能只拷这个文件就称可重建。 |
| `yellow-revision-a01/sample/RENDER-DELIVERY.actual.json` | 视频、字幕、原wait、AV／PTS／音乐及来源的精确索引。 |
| `yellow-revision-a01/sample/final-palette-review-a01/VISUAL-REVIEW.actual.json` | Root最终五帧有限配色审阅。 |
| `yellow-revision-a01/FINAL-STORAGE-CLOSURE.actual.json` | 混合资产的分类、期限、原占用上界与future0。 |
| `full-authoring/final-a10.*` | 原33段作者资料、声音投影、机制证据及时间轴；仍被黄色输入引用。 |
| `root/n02-n15-voices-a01/DELIVERY.actual.json` | 两段补声与196组字幕；另31段沿原声音，不复制或重配。 |

黄色正文色板：底色 `#211813`，面板 `#32251d`，激活面板 `#49371f`，强调 `#d5b26b`，正文 `#f0e5cf`，次要字 `#b9a98f`，线框 `#69533c`。沿[品牌记录](../../promo/ck3_faith_and_power/series-brand.json)读取。封面D「秘仪符刻」及人物的青色数据幽灵属于既有封面方向，不意味着正文机制图改回青蓝。二期没有另行制作或签收新封面。

声线实际为 `zh-CN-XiaoxiaoNeural`、rate −5%；N02／N15仅两次新请求，31段旧音保留。沿原SentenceBoundary和实际测量同步字幕，不能拿旧文字时长估算替代22:49.067的基础帧时钟与最终24:30.067。配乐为 `quiet-courtly-tension.wav`，旁白0dB、音乐−17dB，循环、淡入2秒／淡出8秒，不新增自动响度处理。

本次使用正式 `xar-promo-toolchain 0.3.0`，wheel SHA `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`。黄色轮次最新版本查询先因网络失败，07:23:19Z正面重查仍0.3.0；此时间晚于启动，原失败和顺序保留。下次新run仍须按AGENTS查询届时最新正式版，不把0.3.0永久固定为最新。

解释器为本机 `tools/.venv/Scripts/python.exe`，隔离工具包在 `O/pipeline/pkg`，项目adapter在仓库 `promo/ck3_faith_and_power/integration/src`；实际媒体与字体pin见 `O/pipeline/MEDIA-RUNTIME.actual.json`。Windows操作使用Python与显式cmd.exe入口。若确需重制，先检查现有音频／图／证据引用的可用性，再建新不可变run和有限预算；不能直接复跑绑定过期grant的 `authoring/run_formal.py`。

## 7. 拍摄和现场已经收束

本次场次 `4-8e1c2f1861--faith-engine--R0032`：人物31254、日期raw53144328、天主教Faith13。拍到类型、实际三项意图、主管月薪0.10、基础60＋距离10＝70报价。四段VFR原片分别187／219／205／205帧，交付各选真实2—7秒后重采样，不能把最终150帧当原片帧数。

没有出发、任命、支付或推进新游戏日。原游戏正常退出0、公共run等待0，keeper已结束；Root CAS13272释放拍摄，独立CAS13274释放显示恢复任务，05:53:39Z实际恢复1024×768。完整证据在 `O/filming/FILMING-FINAL-CLOSURE.actual.json`。

最后一次Steam后台离线正面观察为 **05:57:56.501287Z**，`offline=true`；本次交接没有重查Steam，不把该时间改成现在。下一次启动仍取新鲜后台离线回执，不抢屏幕或截图。

本轮09:57:31Z只读OS查询未见CK3、FFmpeg、FFprobe，也未见命令行绑定O的存活进程。制作Root、完整剪辑、原生拍摄、显示恢复任务均已done且resources为空；旧waiting准备条目已于09:58:16Z行政关闭，保留原等待历史。没有强杀、重启、占屏或改动其他任务。

## 8. 存储与休假边界

统一遵守[通用策略](../storage-retention-policy.md)及[参数](../storage-retention-policy.json)，版本1.0.0。黄色闭场清点的4KiB上界159,010,816 B是07:50:57Z历史值，不冒充当前全项目实占。本轮09:56:36Z实际卷空闲91,869,704,192 B；未全盘扫描、回收或据空闲变化推算项目增长。

| 对象 | 原期限／后续动作 |
| --- | --- |
| 黄色图、抽帧、中间编码 | 2026-10-24T07:50:57Z起按48小时规则评估；重建所需小输入与用户待审用途单独判断。 |
| 黄色MP4、字幕与讲稿 | 2026-11-21T07:50:57Z按30天规则复核；当前用户待审不是永久保留授权。 |
| 精简记录、作者输入与回执 | 2027-04-20T07:50:57Z按180天规则归纳；Git跟踪资料不进本地逐文件删除器。 |
| R32原片与原生证据 | 沿各自闭场清单的30天分类；不整树套最长保留。 |
| 旧蓝色版及失败派生物 | 已被后继替代，可按精确用途／可重建性评估；不能无限保存，也不能无清单删目录。 |

本轮仅小型交接文字与Git更新，没有重型写入。旧生产预留已释放，黄色grant与配额例外在08:00Z到期；**不得拿旧文件的active字段当作现在仍有额度**。本次休假不续期、不重新启动生产；接手者若要重制或补拍，应从实际当前占用、其他预留与系统增长重新准入。删除前须查用户永久保留索引并保全当前必要输入。

## 9. Git、验证与接手次序

关键来源：补声冻结 `b916d652`；导演及两段修订发布 `0264e27d`；黄色build实际启动源 `4df7c932`；黄色品牌修订 `defdce517`；最终媒体入口与交付记录 `904970176`。这些历史source不因最新master改变而重标。

09:57—09:58Z查询发现：904970176的官方static在“Enforce Python-only Windows automation”失败，指向另一份既有[罗贝尔休假交接](2026-10-22-robert-source32-a41-recovery-vacation-handoff.md)第48行的shell名称文本；线性历史检查成功。本轮只将该句改为明确的Python／cmd.exe说明，不改其恢复结论或生产代码。接手基线caf5ff5b的官方static当时仍在运行，不能写成全绿。

本轮实际执行同一Python-only step的两条现成命令：9项现有测试通过、0跳过，随后完整仓库检查于10:07:15Z返回PYTHON-ONLY GREEN。新交接24个本地链接存在，回执JSON往返检查通过；命令、时间及结果见机读回执。该本地通过不替代后继commit的官方CI终态。媒体、游戏和研究测试沿原结果，不再重复执行。

接手建议按以下顺序：

1. **先完整听看当前黄色MP4并收集用户意见。** 教学价值按是否讲透统一机制、是否形成新判断评价；不要将用户让休假视为内容已签收，也不因旧待办自动重拍。
2. **有具体修订意见再改对应内容。** 变声音或时钟就同步字幕与映射；单纯图面修改沿原声音。先比较系列色板与代表画面，保留真实失败版本和精确来源。
3. **继续研究优先补会改变决策的缺口。** 先读当前索引和三条费用边；研究可并行，单机CK3保持排他，图表及导演候选与实机冻结树按文件所有权隔离。不能为填并发重复解码、重配未变音频或建立无实际问题的新门禁。

交接完成后本线程不保留后台任务、场景、写入预留或发布动作。若用户后续明确要求继续，由接手者从这份交接及当前master恢复。
