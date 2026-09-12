# 重整河山 0.2.0 发布本地化审阅

执行日期：2026-09-13（Asia/Shanghai）

产品：`mod_reclaim_the_motherland` 0.2.0

基准语言：English、简体中文

发布语言：English、Français、Deutsch、日本語、한국어、Polski、Русский、简体中文、Español

## 审阅范围

- 沿用 0.1.1 已审阅的 13 个产品文案键与 89 个生成朝号键。
- 0.2.0 在每种语言新增 10 个二期产品键：游戏规则及两个设置、设置说明，以及【人心向背】总结事件的标题、三种正文和按钮；同时按新机制修订既有规则说明。
- 九种语言均为 UTF-8 BOM、正确的 `l_<language>:` header，并保持 112/112 同构键：23 个产品文案键加 89 个生成朝号键。

## 术语与文案结论

- 中文产品名统一为《重整河山》；DLC `All Under Heaven` 的中文概念在仓库文案中统一为《溥天之下》，没有残留其他中文译名。
- `Chinese Hegemony`、`Age of Warlords`、`Mandate`、`Later Dynasty`、`Proclaim the Restoration` 沿用 0.1.1 的已审阅术语。
- 二期新增概念稳定对应为 `The Choice of the Loyalists / 尊王诸侯的抉择`、`Divided Hearts / 人心离散`、`Unwavering Loyalty / 誓死尊王`、`Where Allegiance Lies / 人心向背`。
- 简体中文规则说明明确写成旧天子“仍保有亲自持有的领地和其他头衔”，与产品实际只销毁中华霸权、跳过旧天子头衔裁剪的实现一致。
- 玩家可见文案只描述政治后果，不出现“相同百分比”“原版效果”“测试角色”“标记”等实现或验收术语。
- 总结事件使用角色名字投影，并在实机中验证忠臣、叛臣及按钮文本均可见；最终文案不把角色头衔误并入姓名。

## 自动审计与实机边界

- `validate_reclaim_the_motherland_static.py` 已通过九语同构、BOM/header、空值、英文占位、格式 token 与本地化引用检查。
- `build_reclaim_the_motherland_release.py --check` 已对 32 文件发布投影完成可复现双构建。
- 简体中文已用于源码树 L1 与 Workshop fresh-cache L3 的完整实机矩阵；【尊王诸侯的抉择】、【人心离散】和【人心向背】均在真实 CK3 1.19.0.6 流程中加载并显示。
- 法、德、日、韩、波、俄、西七种语言沿用模型候选经结构、格式、语义和术语复核的发布边界；没有英语占位，但不声明母语者签校或逐语言实机截图。

完整运行与发布证据见 `mod_reclaim_the_motherland/docs/acceptance-report.md`；上一版审阅基线见 `docs/reclaim-release-localization-review-2026-09-09.md`。
