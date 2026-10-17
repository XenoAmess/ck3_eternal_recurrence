# 《CK3：信仰与权力》第一期文案输入

2026-10-18文案修订：用户指出首个19:25审阅版像检查报告。新的[完整中文讲解稿v2](narration-v2.zh.md)已改按玩家问题组织，[修订说明](../../../docs/ck3-native-ai/faith-and-power-episode01-editorial-revision.md)记录原因和事实边界。v2尚未配音或替换视频，不复用旧时码；下文旧稿与历史媒体记录继续保留。

收益补充已落入[主要等级](../../../docs/ck3-native-ai/holy-site-major-grade-value12004.md)、[采用／新建](../../../docs/ck3-native-ai/faith-and-power-adoption-value-12004.md)、[共享圣物与返还](../../../docs/ck3-native-ai/holy-site-shared-relic-value12004.md)三份研究，并接入现有[规划MCP知识](../../../docs/ck3-native-ai/faith-and-power-episode01-value-analysis-mcp-12004.md)。新增真实MCP查询验证通过；原生观察源码已合，编译与补拍待完成。[讲解稿v3](narration-v3.zh.md)已加入具体收益、损失和使用场景，取代上段v2草稿，仍待补拍和重新配音剪辑；旧片不会因文档更新而自动成为新版。

> 2026-10-17后继更正：下列初始记录保留建立时截点；当前结果与媒体见文末[后继状态](#2026-10-17-后继状态)。

`script.json` 保存158条已冻结中文旁白与英文副字幕、逐句 claim/来源跨度/shot 映射及三处真实结果槽。文字覆盖采用条件、关系与作用域、新建、名额、成本和退出规划；静态规则锁定1.20.0.4。所有完整节目镜头仍待实际素材绑定，三处结果槽的 `zh`、`en`、`outcome` 保持 `null`，不能用占位台词提前配音。

`authoring-project.json` 是 ProjectConfig 相容的文案投影，沿用系列 adapter/preset ID。章节均为 `planned`，`artifact_ids` 均为空；它不声明任何媒体、完成时码或成片资格。未写结果槽不投影为可配音 cue。通用工具的 authoring 验证通过，只证明该配置结构有效。

`tts-recipe.json` 保存 `zh-CN-XiaoxiaoNeural`、`-5%` 等原请求参数及逐 cue 精确文本 SHA/缓存指纹。缓存指纹按0.3.0公开 `tts_fingerprint` 计算，包括 provider 身份与版本；它不证明某台机器有对应缓存。重用现有音频时仍核对原请求、音频 SHA 和实际时长。不要静默改标点、去空白或替换术语。更换声音、provider版本或文字后，重新生成指纹并听审；本文件不触发TTS。

实际时长与外置证据只在 `sample-index-4-8e1c2f1861-20261017.json`。其中49.621354秒是该机器样段容器实际时长，49.600秒是作者视频时间；158条cue的实测配音时长也只属于所列原件，不能作为其他机器或最终全片的默认时间线。该样段仅展示准备事件与暂停地图，原debug遮挡保留；源02中断RED，没有采用或clean成绩，完整1×观看、听审和签核仍待完成。索引里的绝对路径只用于定位来源机器证据，不是构建前提。

`producer-api-proposal.json` 保留形成生产入口前的合同提案。当前[仓库生产入口](../integration/README.md)提供 `project`、`synthesize` 和 `context-sample`；可移植提取版目前通过离线合同与作者配置检查，未重跑媒体渲染。真实 build 每次重新查询官方正式 Release，记录实际 wheel SHA、解释器和CLI；音频、raw、运行身份、容量准入与媒体工具路径由当前执行者显式提供。无需也不得为读取本目录启动CK3、连接MCP、取屏或访问那些历史机器路径。

来源解释与游玩智能体规划合同见 `docs/ck3-native-ai/faith-and-power-episode01-planning.md` 及其 claims/scenario JSON。句内的来源 key 只证明相应固定定义；真实业务仍须同帧身份、原生许可、一次提交与独立后态。

## 2026-10-17 后继状态

machine_id: 4-8e1c2f1861；实际补注 2026-10-17T13:16:56.756078+00:00。上文158cue、3个null结果槽与“无媒体/未渲染”说明的是本目录最初冻结输入；本次实读script.json仍158句、3槽zh/en/outcome均null，保留原字节，不把外置后继成果倒填进去。后继已经有R5真实采用、结果声与实际媒体；结果和来源见[R5专题](../../../docs/ck3-native-ai/faith-and-power-episode01-r0005-adoption.md)。

用户本会话2026-10-17选择“先提供本地文件，继续制作（推荐）”。当前机器的[3:34.400采用审阅段](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/adoption-review-build-a01/native-run/derived/direct/episode01-review.mp4)与[29:24.267机制研究讲解审阅版](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/full-review-build-a01/native-run/derived/direct/episode01-review.mp4)已实际本地交付；[统一入口/字幕/逐句稿/时码](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/full-review-build-a01/delivery/LOCAL-REVIEW-README.md)、[短段索引](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/adoption-review-build-a01/delivery/ADOPTION-REVIEW-DELIVERY.json)、[长版索引](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/full-review-build-a01/delivery/FULL-RESEARCH-REVIEW-DELIVERY.json)分别保留精确SHA及QA。短段偏移字幕使用[measured-PTS-text-a02](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/adoption-review-build-a01/delivery/measured-PTS-text-a02)，不继续指向旧时码文本。

长版[静图分类](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/full-build-candidate/FULL-VISUAL-DISTRIBUTION-a01.json)为95.21%，其中机制图89.56%、原生读回静图5.65%，不重复实机区间仅4.79%；它仅是研究讲解审阅版。机器解码/全部帧PTS及字幕检查通过不代替听审、完整1倍观看、clean-span和人工签核。**正式第一期尚未完成。**

[正式21分钟作者方案](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/full-build-candidate/formal-episode01-authoring-a01/formal-authoring.json)另行冻结：目标1260秒，保留70句旧声与11句结果声，已知声819.456秒；未来R6/R7、Faith/Character导航、F-funded准备及新声槽保持null，actual_final_seconds=null、AUTHORING_ONLY_NOT_RENDER_READY。R6晋降/冷却与R7独立退出分支待真实前后态及raw绑定，不从R5采用成功或长版时长推算完成。
