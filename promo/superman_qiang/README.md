# 《超人强：越超人越强》宣贯视频

本轮先交付三份完整中文导演稿，依据2026-10-04正式发布的1.1.0。每份都有逐镜头时间码、完整口播、画面与字幕、声音设计、素材编号及待拍清单。

| 导演稿 | 时长 | 用途 |
| --- | ---: | --- |
| [2分钟宣传片](02m/director.md) | 02:00 | 用宫廷悬念吸引玩家，留下核心玩法和查看入口 |
| [5分钟玩法导览](05m/director.md) | 05:00 | 从一次正常勾引讲到第一次实际操作，解释平手、随机与气泡 |
| [10分钟完整入门](10m/director.md) | 10:00 | 逐例解释反向吸取、健康、记录、旧存档与策略取舍 |

三份同名director.json是本项目的结构化导演意图，方便后续配音和剪辑取词；不冒充工具链的storyboard或composer格式。台词与时间码以各版稿件为准；[共同导演意图](production-brief.md)规定画风和规则，[素材与论点清单](asset-and-claim-ledger.json)记录已有静帧的精确来源及待制作项。

## 画面与口播

建议1920×1080、16:9、简体中文字幕，一位自然清楚、略带戏谑的中文叙述者。沿用成年国王与成年王后的红金宫廷主视觉；开头有悬念，规则段落放慢，关键UI读数时留白。两行字幕以内，数字和人物信息错开，游戏原图保持比例。

已有宣传插画、正常勾引事件静帧和新版通知静帧。新游戏录像尚待拍摄：每版在具体镜头里标出P01–P04。规则动画G01–G04也尚待制作。既有静帧可以后期推拉，但不能声称是连续操作录像；实际健康转移难以自然取到时使用明确标注的规则动画。测试夹具不能进入宣传画面。

## 框架记录

本任务已查询独立工具链的最新正式GitHub Release，使用同一已核验解释器中的xar-promo-toolchain 0.2.1，wheel SHA-256为f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621。版本和安装来源精确匹配，[工作流指南](https://github.com/XenoAmess/xar_promo_toolchain/blob/v0.2.1/codex-skill/promo-video-pipeline/SKILL.md)用于本轮原生项目与素材留存。

每个版本都有原生promo-project.json，包含时长上限、中文旁白与字幕cues。真实init创建的planning-scaffold-20261004保留初始快照；填入完整导演意图后，再用start-run建立director-draft-20261004-a01。十分钟稿最后修正累计转移示例与固定差距条件，另起a02绑定修订；a01原样保留。当前场景全部为planned。导演稿、共同意图和素材清单通过真实preserve命令进入run内的内容寻址存储，历史manifest保留。完整文件与SHA校验结果见[evidence/director-planning-20261004/](evidence/director-planning-20261004/README.md)。

generic/default沿用框架中性的初始化标识。正式制作阶段再接入本产品的实际adapter/preset/composer；本轮达到导演稿authoring阶段，未运行媒体plan/build，也未生成配音、音乐或成片。框架验证不代表成片审阅或外部发布。

在仓库根目录可复核各版原生文档，例如：

```text
tools\.venv\Scripts\python.exe -m xar_promo validate promo/superman_qiang/02m/promo-project.json --profile authoring --json
tools\.venv\Scripts\python.exe -m xar_promo validate promo/superman_qiang/02m/runs/director-draft-20261004-a01/run-manifest.json --profile authoring --json
```

05m、10m使用相同路径结构。修改后用新run绑定新的精确字节；旧导演快照、录像、音频、字幕、中间编码和失败attempt永久保留。后续取材使用正式1.1.0的22文件staging，遵守Steam离线、屏幕排他及原始坐标/输入合同。成片的机器审查、1×完整人工观看、字节绑定签核与实际视频交付分别记录。
