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

## 后到要求：简短条目、悬停与当前阶数

用户在发布前补充：条目只展示简要文本，悬停后展开描述；只展示当前阶数的效果，随阶数变化的数字用彩色文字。本次统一应用于异能和诅咒。

每个槽的 custom localization 同时匹配能力 ID 与该槽阶数，选中具体的简短条目。条目使用原版同一 `ARTIFACT_EFFECT` 调用链已经使用的 `#TOOLTIP:localization_key #L 文本#!#!` 格式；对应的目标文本在生成时选好阶数，不包含 `ROOT.Artifact` 或保存 scope 的 getter。因此延迟悬停不依赖原宝物 scope 在 tooltip 切换后继续存在。

原版依据为 `localization/english/inventory/inventory_l_english.yml` 的 `ARTIFACT_EFFECT_HAS_CAN_BENEFIT` → `ARTIFACT_EFFECT_REQUIREMENT_TT`；原文件17435B，SHA-256 `fd3bb294db01a6332970cecf646c7a1b7867134b300ef1b02d2c71d7b62ff63b`。源码依据不是新增悬停已经实机通过的证明。

12个异能与8个诅咒在九语中各有33组数值三联值。`living_artifacts_display.py` 按原顺序选择当前阶数并用原版 `#M` 以黄色强调数字；支持 `-15/30/45` 的共同负号、`+5/10/15` 的共同正号及逗号小数，不转换浮点数或排序。固定的8压力、365日、12期等不被改写，也不因它们是数字而着色。七语仍复用原译文，只机械选择数值及添加引擎标记。

本次新增悬停和阶数回归后，58项相关模块测试、九语发布静态及五个完整修改模块 strict mypy 均实际通过。新源 `a509ed8665a9a6ba6de113651b8b09786d51e7db` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/41916912032)进一步完成239项产品测试、6个完整源码 strict 检查及9项、8项共享回归。最初235项及旧画面对应先前展开式版本；本次悬停画面和发布按新回执记录，不借用旧画面授予通过。

R0002实机015确认简短条目，016确认二级悬停只含50与5；同时发现初选 `#V` 只是变亮，没有明确色彩，因此颜色验收不通过。安装版 `gui/preload/textformatting.gui`（8892B，SHA-256 `44a3801dace9610ce5d9d5a463bc7e8184252ee7f974af7945e78d3be24bfc8a`）的223–274行明确 `V → value → color_white`，`M → mixed_value → color_yellow`。后继改用 `#M`，统一黄色只表达阶数相关数值，不按正负号猜测机制的利弊。原失败包没有上传。

最终源码 `be9abc9928598b543bf10e0c4be8890cf337ad28` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/41925238206)完成239项产品测试、6个完整源码 strict 及后续9项、8项共享回归。R0003的014–016实际画面由Root直接审阅：原生效果旁保留简短条目，二级异能只显示黄色50与5，一级诅咒只显示黄色-0.4与+15，固定十二期保留。原Popen正常返回0，公共GUI-only verify退出0，业务及case通过；该窄UI合同不授予全玩法或Native资格。画面、正常退出、工坊上传与真实下载证据见[0.1.2发布记录](../../docs/release-changelogs/living-artifacts/0.1.2.md)。
