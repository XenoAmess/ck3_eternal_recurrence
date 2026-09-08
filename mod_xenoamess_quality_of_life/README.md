# XenoAmess 的生活质量

面向《十字军之王 III》1.19.0.6 的独立生活质量 Mod。当前提供两组仅限人类玩家、默认关闭、可随时通过决议切换的行政制功能：

- 自动选择继任：行政制、贤能制或天朝制的独立玩家开启后，玩家本人不再被选为下属行政制领地的 appointment 继承人；原版候选池、资格条件和候选分数保持不变，死亡与卸任均由原版最高分继承人接任。
- 别把封臣给我：开启后，直属领主采用 administrative 类政府的待转移角色会获得原版 `ai_should_not_transfer` 标志，阻止 AI 行政制封臣通过“授予封臣”把人塞给玩家；关闭后只移除本 Mod 拥有的标志并恢复原版行为。

## 用户操作

在“决议”面板的“XenoAmess 的生活质量”组中分别开启或关闭两个功能。决议仅对非 AI、独立且采用以下政府之一的统治者显示：

- `administrative_government`
- `meritocratic_government`
- `celestial_government`

## 开发与发布

```powershell
py tools/validate_xenoamess_quality_of_life.py
py tools/build_xenoamess_quality_of_life_release.py --check
py tools/build_xenoamess_quality_of_life_release.py
```

验收协议与执行记录分别见 `docs/acceptance-plan.md` 和 `docs/acceptance-report.md`。Steam 工坊正文的 canonical BBCode 位于仓库根目录 `workshop/xenoamess_quality_of_life_description.bbcode`；跨机器首发步骤见 `docs/xqol-workshop-publication-handoff.md`。
