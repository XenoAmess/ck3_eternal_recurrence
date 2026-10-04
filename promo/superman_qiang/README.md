# 《超人强：越超人越强》玩家宣传片

**当前选用[2分钟稿的宣传创意](02m/director.md)，成片允许1分30秒至5分钟。** 约130秒的分镜轴用于安排节奏，最终长度随配音和素材调整。

本片要让玩家想把模组装进自己的战役。主线是“赴约前，先看看谁才是猎物”：变强的诱惑、宫廷的反转、简短实机查履历，再交给玩家下一封邀请。详细算账和实现机制已从选定稿移出。

- [完整宣传导演稿](02m/director.md)：逐镜头完整旁白、画面、屏幕短文案和声音设计。
- [制作选择与时长](production-selection.json)：唯一选中项目、90–300秒范围、废弃方案与历史留存。
- [共同导演意图](production-brief.md)：面向玩家的叙事、视觉与制作取舍。
- [Suno 单曲配乐输入](music/suno-brief.md)：Style、纯音乐结构标签、排除项和建议设置；配音固定为晓晓。
- [素材与事实资料](asset-and-claim-ledger.json)：内部素材编号与来源。
- [本轮框架记录](evidence/player-trailer-selection-20261004/README.md)：新配置、新run及完整authoring验证。

## 废弃方案

[5分钟稿](05m/DEPRECATED.md)与[10分钟稿](10m/DEPRECATED.md)已按用户决定废弃，不参与本片拍摄、配音或剪辑。原始run和内容寻址快照保持原样，[首轮三稿记录](evidence/director-planning-20261004/README.md)仅是历史。

## 制作与框架

使用当次查询确认的最新正式xar-promo-toolchain 0.2.1，同一主worktree解释器与正式wheel来源匹配。02m/promo-project.json写入当前中文旁白cues与300秒上限，player-trailer-20261004-a01保存修改后的精确配置和导演输入。原生schema只有上限字段，因此90秒最低长度由production-selection.json和导演稿的duration_policy明确表达；没有虚构通用schema字段。

已有宣传插画与正常实机静帧；新录像、G04/G05、配音、音乐和成片尚待制作。generic/default当前仍是中性初始化标识，媒体composer在实际制作阶段接入。当前完成创意选择与authoring修订。
