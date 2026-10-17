# 《CK3：信仰与权力》第一期文案输入

`script.json` 保存158条已冻结中文旁白与英文副字幕、逐句 claim/来源跨度/shot 映射及三处真实结果槽。文字覆盖采用条件、关系与作用域、新建、名额、成本和退出规划；静态规则锁定1.20.0.4。所有完整节目镜头仍待实际素材绑定，三处结果槽的 `zh`、`en`、`outcome` 保持 `null`，不能用占位台词提前配音。

`authoring-project.json` 是 ProjectConfig 相容的文案投影，沿用系列 adapter/preset ID。章节均为 `planned`，`artifact_ids` 均为空；它不声明任何媒体、完成时码或成片资格。未写结果槽不投影为可配音 cue。通用工具的 authoring 验证通过，只证明该配置结构有效。

`tts-recipe.json` 保存 `zh-CN-XiaoxiaoNeural`、`-5%` 等原请求参数及逐 cue 精确文本 SHA/缓存指纹。缓存指纹按0.3.0公开 `tts_fingerprint` 计算，包括 provider 身份与版本；它不证明某台机器有对应缓存。重用现有音频时仍核对原请求、音频 SHA 和实际时长。不要静默改标点、去空白或替换术语。更换声音、provider版本或文字后，重新生成指纹并听审；本文件不触发TTS。

实际时长与外置证据只在 `sample-index-4-8e1c2f1861-20261017.json`。其中49.621354秒是该机器样段容器实际时长，49.600秒是作者视频时间；158条cue的实测配音时长也只属于所列原件，不能作为其他机器或最终全片的默认时间线。该样段仅展示准备事件与暂停地图，原debug遮挡保留；源02中断RED，没有采用或clean成绩，完整1×观看、听审和签核仍待完成。索引里的绝对路径只用于定位来源机器证据，不是构建前提。

`producer-api-proposal.json` 保留形成生产入口前的合同提案。当前[仓库生产入口](../integration/README.md)提供 `project`、`synthesize` 和 `context-sample`；可移植提取版目前通过离线合同与作者配置检查，未重跑媒体渲染。真实 build 每次重新查询官方正式 Release，记录实际 wheel SHA、解释器和CLI；音频、raw、运行身份、容量准入与媒体工具路径由当前执行者显式提供。无需也不得为读取本目录启动CK3、连接MCP、取屏或访问那些历史机器路径。

来源解释与游玩智能体规划合同见 `docs/ck3-native-ai/faith-and-power-episode01-planning.md` 及其 claims/scenario JSON。句内的来源 key 只证明相应固定定义；真实业务仍须同帧身份、原生许可、一次提交与独立后态。
