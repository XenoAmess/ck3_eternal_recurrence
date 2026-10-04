# 2026-10-04 导演筹划记录

这是《超人强》1.1.0三版导演稿的authoring记录。

- [framework-version.json](framework-version.json)：当次查询的最新正式版本、安装wheel来源、精确SHA-256、解释器与已核验CLI接口。
- [authoring-validation.json](authoring-validation.json)：初次三版实际CLI调用与退出状态，连续120/300/600秒时间线、口播文本一致性、素材ID、逐场字数及完整原生文件/哈希验证。
- [authoring-validation-a02.json](authoring-validation-a02.json)：十分钟稿审阅后修订的真实新run与完整authoring校验；明确累计转移由多笔±1组成，固定差距要求双方只与彼此往来。
- [final-checks.json](final-checks.json)：当前三份稿件与所选run的精确字节、场景数、文件一致性、来源摘要及交付检查。
- [asset-and-claim-ledger.json](../../asset-and-claim-ledger.json)：已有静帧与产品依据的精确字节摘要，以及待拍/待制的画面范围。

三版当前绑定的run：

| 版本 | 原生run |
| --- | --- |
| 02m | [director-draft-20261004-a01](../../02m/runs/director-draft-20261004-a01/run-manifest.json) |
| 05m | [director-draft-20261004-a01](../../05m/runs/director-draft-20261004-a01/run-manifest.json) |
| 10m | [director-draft-20261004-a02](../../10m/runs/director-draft-20261004-a02/run-manifest.json) |

每个director run保存五份输入：完整Markdown导演稿、结构化导演稿、共同导演意图、素材论点清单和框架版本记录。每次preserve前的manifest都由工具链保存在manifest-history。初始planning-scaffold-20261004继续绑定初始化时的空章配置；新版run才绑定完整的planned场景与口播cues，不覆盖初始历史。10m的a01保留初稿，a02绑定当前修订。2分钟稿的内部显示码已在入run前统一为合法MM:SS；初稿和修正回执保存在外置A0001的02m-original-before-timecode-format-fix/。

外置过程目录为C:/ck3-superman-qiang-promo-20261004/director-planning-A0001/及A0002/，保留GitHub最新发布原始返回、精确版本指南、CLI帮助、操作argv、stdout/stderr和当次辅助脚本。本仓记录足以复核稿件字节与原生run，外置原始过程继续保留。

逐场字数除以镜头长度只是口播预算。数字的实际读法、停顿和配音长度要在真实生成音频后核对。本轮没有新游戏录屏、TTS音频、音乐或视频；没有媒体plan/build、媒体audit、完整观看、signoff、export或外部视频发布记录。不能把authoring通过写成成片完成。
