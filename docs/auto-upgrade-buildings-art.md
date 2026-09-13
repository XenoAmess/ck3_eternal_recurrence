# “自动升级建筑”决议插图

## 当前资产

- 人物参考：`images/glassfire_avatar.png`，SHA-256 `635FE7827B75008AF4D72C234C071A8D18593D26D2CFE0EF336A3B24CD77A935`。
- 定稿源图：`images/auto_upgrade_buildings_decision.png`，`1983×793` PNG，SHA-256 `8411B32F663E4208B66D446B5DE9A59AA109A210923850C7243F47F759C52805`。
- 最终视觉要求：人物忙于处理堆积的建筑图纸与公文，神情安静、悲伤、疲惫，而非愤怒或急躁；保留参考图的绿色代码雨、RGB 错位、扫描线与青红赛博撕裂。
- 最终生成提示词：`images/auto_upgrade_buildings_decision_prompt.txt`。

源图由 Codex 内置图片生成能力按用户逐轮反馈生成。提示词和人物参考用于记录创作意图；生成式模型不承诺从提示词重新得到相同字节，因此已选择的 PNG 才是后续投影的权威源。

## CK3 投影

运行：

```powershell
py tools/compose_auto_upgrade_buildings_decision_art.py
py tools/compose_auto_upgrade_buildings_decision_art.py --check
```

脚本读取源图真实宽高，按目标 `1100×440` 比例居中 cover-crop，不拉伸，然后生成 DXT1 DDS：

`mod_auto_upgrade_buildings/gfx/interface/illustrations/decisions/decision_auto_upgrade_buildings.dds`

当前 DDS SHA-256 为 `B41C0961BE1EE9B8046CC2CA439E611C1200664779974CFD9DD6962D7AD688F1`。启用与禁用决议共同引用该资产。静态校验会从权威 PNG 重新编码，并逐字节比较 DDS，同时检查尺寸和 DXT1 FourCC。

加入该 DDS 后，正式 Workshop staging 从历史 15 个运行时文件增加为 16 个；源 PNG、提示词和生成脚本不进入 Workshop payload。
