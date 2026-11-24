# CK3 1.21.0.3 源迁移候选

`machine_id: desktop-3fevhd2-1c74096080`，CK3 1.21.0.3 / build26785313，EXE SHA `859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`。版本是本次安装事实，不授予 Native 能力。

0.1.3 是未发表候选，原 living-artifacts-v0.1.2 标签及其历史验收保持不变。此次只更新既有 source projection、生成兼容 metadata 和源版本，玩法、AI、定价、成长、诅咒与原业务断言不变。

Core 唯一投影是 `gui/window_artifact_details.gui`。旧 1.20.0.4 原件 normalized SHA `4628fce2891719759e4e52587a4decb781aac92178c02778cc944b8656505683`，新原件 `7adb6a61fb18c1a6e490654caf7b33a3d6a2374c35b26a9db818be5bd1104f07`。新原版 line13 仍以 ArtifactDetailsView.GetArtifact 为上下文，line336 唯一 GetModifierEffects 插点仍在效果栏；只追加 Artifact.Custom('XalwEffects')。新版 line414–436 的 vbox、原描述和商人宪章滥用立场 Custom/ScriptValue 全文保留。该方法按查看中的 Artifact 求值；XalwEffects 仍是 type=artifact 的现有定制本地化，普通宝物 fallback 为空。没有新游戏事件调度或角色 scope 切换。

Content 的 26 个已审原版来源与 Core 合为 27 个 SourcePatch，均经既有 project/recover 对实际新 stock 检查，完整 render_files 产生 59 个生成文件。其余 8 个 runtime-inventory 成员为既有翻译/封面，继续保留；没有复制或重新生成图片。全部原版正文在逆投影后恢复为精确 normalized 新源；BOM/LF 是既有生成规范。生成、静态与工具回归不等于 CK3 执行。

`product.py` 的 GAME_VERSION/EXE_SHA256 仍为旧 1.20.0.4/98702 Native 身份，不能用脚本 descriptor1.21 或新 source pin 冒充新版 ABI/Full/Actor/协议/保存资格。prepare_fixture 仅改 ScriptEmitter descriptor 的 supported_version，原输入合同、身份、NOT_ASSESSED 和 game_started=false 不变。旧实机失败、成功与未知动作均不复用为新版资格。

本候选的正式 ZIP/完整发布 builder、新 Native/GUI/真实装备/成长/喂养/AI/诅咒/冷载/保存/工坊发表均须另行验收；本次未执行，不据源码兼容外推通过。

## a1480 actual content-modifier load errors (current267)

The retained actual a1480 game.log and error.log report nine product-owned unknown
modifier fields in xalw_content_modifiers.txt: three county_opinion_add and six
monthly_county_control_growth_add. These are not fixture or vanilla warnings.
The authoritative content renderer and its generated runtime definitions now use
popular_opinion_add for the existing county opinion penalties (-15/-30/-50), and
monthly_control_change_when_below_baseline_add for both artifact slots' existing
control-growth penalties (-0.2/-0.4/-0.7). Current stock00_definitions defines these
fields; ordinary county modifiers and the current overseer character trait supply
actual source consumers. The latter is additive recovery below the current control
baseline, not a multiplier or an above-baseline penalty. Florin's baseline system
is not claimed identical to the old fixed control system in every state.

IDs, curse ranks, equip/unequip projection/removal, quarterly chance/count limits,
instant county-control losses, two-year local unrest and all other runtime files
remain unchanged. Existing67 candidate, Frozen/runtime products, old profiles and
all previous failures are preserved. The narrow tree/value/mutant regressions are
Source only here; compilation/test/generator checks, rebuilt67 and actual fixed
Game load must be reported separately. Current feeding/SDK business does not prove
this repaired modifier file has been loaded. No old engine errors are erased.
