# 宝物效果显示与空槽间距修复

用户报告的两种现象分别来自显示入口遗漏和空槽分隔符，不表示事件型异能已经失效。

原版宝物悬浮提示使用 `ARTIFACT_EFFECT`，包含受益条件和 `Artifact.GetModifierEffects`；宝物详情页直接调用后者。它们不会自动枚举本产品保存在宝物上的异能、诅咒变量。旧版只在管理事件中调用 `XalwAffixes` / `XalwCurses`，因而这些机制说明没有进入正常效果栏；能变成数值修正的部分仍可能出现在原生数值列表中。

0.1.2 给原版 tooltip 本地化追加 `Artifact.Custom('XalwEffects')`，并将同一 getter 追加到详情页原有数值文本。条件与数值文本保留，普通宝物返回空字符串。自定义说明在打开页面时从当前宝物读取，不写入宝物原说明，不重复添加修正，不要求旧物重新觉醒或等月度更新。

旧版固定用换行连接六个异能槽和两个诅咒槽；空槽 getter 返回空字符串，但分隔符仍占一行。现在汇总直接连接槽文本，只有有内容的槽在自身开头带一个换行。标题与机制说明之间仍留一个换行，条目之间不再按空槽数留白。七种既有外语只调整分隔符与共用引擎 token，原译文逐项核对保留，没有新增翻译任务。

## 原版来源与兼容性

本机安装 game 根为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`。静态来源检查使用 CK3 1.20.0.4，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

- `gui/shared/cooltip.gui` 的 `artifact_tooltip` 在两个受益分支都显示 `ARTIFACT_EFFECT`。
- `localization/*/inventory/inventory_l_*.yml` 的该键包含原有 `SelectLocalization` 受益前缀及 `GetModifierEffects`。本产品用 `localization/replace/` 的九份纯 token 文件覆盖此键。
- `gui/window_artifact_details.gui` 的效果文本被唯一锚点替换；规范化原文 SHA-256 为 `4628fce2891719759e4e52587a4decb781aac92178c02778cc944b8656505683`。生成器拒绝其它原文，反向投影须精确恢复原文。

详情页为原版文件投影。另一个模组若也替换该 GUI 或 `ARTIFACT_EFFECT`，需要加载顺序或兼容补丁；本次没有声称覆盖所有 UI 模组组合。

## 验证边界

离线回归使用生成的真实字符串，覆盖首槽、末槽、跨空槽、多槽、满槽和无内容，并验证普通宝物的空回退及详情页保留数值文本。九语静态检查已通过。离线检查不等于游戏画面验证；实机结果和正式发布回执记录在对应 0.1.2 发布记录。

本次确定性预验复用现有 brace/projection 与 localization parser。`open_kaishek` 对 CK3 GUI 的布局和原生动态文本渲染无覆盖，记为 not-applicable；不以字符串夹具代替引擎画面。
