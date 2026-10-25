# 礼仪宗族名称与纹章

本轮为源码准备，尚未进行游戏加载、实际建族、存档或视觉验收。名称实现覆盖实际 Rite 对象；繁育教派、白绮教派两个预置 Rite 使用各自精确图标，其他 Rite 使用用户随后允许的原生随机宗族纹章。**任意自创 Rite 的实际图标复制仍无已核脚本入口；随机方案是明确授权后的替代行为，不是通用精确图标复制。**

本机观察：`machine_id: desktop-3fevhd2-1c74096080`，`2026-10-25T15:24:16.734295Z`。来源为安装于 `C:/SteamLibrary/steamapps/common/Crusader Kings III` 的 1.20.0.4 文件。EXE 为 101,040,248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本轮重新读取文件哈希；历史版本来源见 [原来源清单](evidence/source-observation.json)。精确文件、有限字节切片及边界见 [本轮研究回执](evidence/rite-identity-source-12004-2026-10-25.json)。未启动游戏、读取进程内存、变更 Steam 或写入 Workshop。

## 名称的真实来源与生产调用

`des_apply_rite_identity_effect` 使用 Rite scope，只接收 `var:des_bound_dynasty`、`var:des_join_house` 已存在且 House→Dynasty→Rite 回链一致的绑定。它保存当前 Rite 为 `des_identity_rite`，对新 Dynasty 调用 `set_dynasty_name`，对新 House 调用 `set_house_name`。九语共用唯一动态名称键：

```text
des_rite_dynasty_name:0 "[des_identity_rite.GetNameNoTooltip]"
```

这读取实际 Rite 的名称，包含用户在原生创建界面命名的动态 Rite，不由 Faith 名称、创建者姓氏或某个预置本地化键代替。名称 effect 在首次成功建族后执行一次；不会按日覆盖后续玩家手动改名。家主与宗族长转移使用另一路生产 effect，本 helper 不修改角色或族长。

原版证据为 `common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt:45–47` 的 `set_house_name = japanese_dynasty_name`，对应 `localization/english/dlc/tgp/dlc_tgp_japan_decision_events_l_english.yml:32` 的 `"[new_head.GetDynasty.GetNameNoTooltip]"`。这证明名称 effect 通过本地化键求值保存 scope 派生名称的实际用法。EXE 内置说明分别为 `set_house_name=<dynamic_description>`、`set_dynasty_name=<dynamic_description>`；原版 `gui/window_faith.gui:136` 使用 `Rite.GetNameNoTooltip`。上述文件和二进制字节均已绑定 SHA。

## 两个预置 Rite 的纹章

`common/coat_of_arms/coat_of_arms/des_rite_coa.txt` 定义 `des_procreation_rite_coa` 与 `des_vivhite_rite_coa`，分别只有一个 `textured_emblem`。纹理为 `gfx/coat_of_arms/textured_emblems/des_procreation.dds`、`des_vivhite.dds`；正式树应与各自 `gfx/interface/icons/faith/` 下的图标逐字节相同。使用 RGBA 原色，不经 `colored_emblem` 重新着色，不添加其他图案、分区、文字或背景纹理。源纹理透明像素保留；盾形裁切、底板及省略背景 pattern 后的实际渲染仍待实机确认，不能声称视觉验收已通过。

helper 在精确 `this = rite:des_procreation_rite` 或 `this = rite:des_vivhite_rite` 分支中，将相应 CoA 同时写给绑定 Dynasty 与 House。这避免只改其中之一导致家族窗口与宗族窗口图案不一致。分支未发出实机成功回执；提交 effect 的源码不能替代存档后态。

其他 Rite 仍复制实际名称，并在绑定 Dynasty scope 内调用一次 `generate_coa = yes`，随后在 House scope 内调用 `set_coa = scope:des_identity_rite.var:des_bound_dynasty`。House 复制已生成的同一个 Dynasty CoA，不再次随机。完成请求后清理旧源码版本的 `des_rite_coa_unsupported` 诊断变量；当前源码不再新写入该变量。原生 effect 请求仍待存档后态验收。

用户后续明确授权：“任意自创礼仪的图标复制，如果确定无法使用原宗教的图标，允许实现为按照游戏机制随机新的宗族图标。”这覆盖早期仅记录不支持诊断的实施边界。[原研究回执](evidence/rite-identity-source-12004-2026-10-25.json)保留当时的事实，没有倒改为随机方案已验收；新增生产路径与有限原生证据见 [随机方案追加回执](evidence/rite-identity-random-fallback-12004-2026-10-25.json)。

源级核验的依据为 EXE 内置 `generate_coa` 说明明确接受 landed title、Dynasty、House；`CGenerateCoAEffect` 支持 mask getter RVA `0x2cd7b20` 包含 Dynasty/House 类型，实际 evaluator `0x2cd8220` 将 type `0x13` 分派至 `0x2cd8516`、type `0x14` 分派至 `0x2cd8434`，分别生成并写回 Dynasty、House 的 CoA。原版 `common/scripted_effects/00_decisions_effects.txt:2937、2947、2989` 也实际在 House scope 使用 `generate_coa = yes`。

House 接收 Dynasty CoA 的跨类型输入没有依赖说明文字的猜测：原版 `events/dlc/tgp/tgp_japan_decision_events.txt:2022–2025` 在 `house = { ... }` 中执行 `set_coa = dynasty:japanese_minamoto_seiwa`，`2064–2067` 对 Taira 同样执行。新增路径沿用这一原生 House←Dynasty 合同，仅以已绑定的动态 Dynasty scope 代替静态 Dynasty ID。

## 通用图标复制的原生脚本缺口

以下地址全部是上述 EXE 的 RVA，不是跨版本地址，也不授予原生函数调用资格：

| 研究路径 | 实际观察 | 本轮结论 |
| --- | --- | --- |
| `set_coa` | 内置说明限定 landed title、Dynasty、House 的 CoA/同类对象；未提供 Rite 图标参数 | 不编造 `set_coa = scope:rite` |
| `generate_coa` | 内置说明接受 `yes` 或 CoA template-list 键，支持 Dynasty/House | 可用于已授权的随机纹章；不是接受动态纹理的 `create_dynamic_coa` |
| `has_icon` | 实际类为 `CHasFaithIconTrigger`；支持 mask getter `0xa0a850` 返回 `0x1000`；eval `0xa0aaa0` 仅接受 scope type `0x0d`，读取 Faith `+0x1f0` 字符串 | 原版模板中的 `scope:faith = { has_icon = ... }` 不能套用于 Rite |
| `textured_emblem.texture` | render-description 文件校验 `0x35022f0` 使用静态字符串和固定 `gfx/coat_of_arms/textured_emblems/` 路径；调用来自数据库纹理校验循环 | 不把 `texture = "[Rite.GetIcon]"` 冒充动态求值 |
| dynamic CoA definitions | 原版 `_dynamic_definitions.info` 的名称必须匹配 landed title，由 trigger 选取预定义 CoA | 不支持给任意动态 Rite 创建新纹理对象 |

原版 `gui/window_faith.gui:4304` 等确实以 `texture = "[Rite.GetIcon]"` 直接显示 Rite 图标；GUI 纹理绑定不等于可保存、可赋给 Dynasty/House 的 CoA 对象。原版 `common/religion/rite_icons/_rite_icons.info` 还允许动态 Rite 从图标池中选取图标；仅按预置 Rite ID 分派无法覆盖这一实际结果。

原宗教/Faith 图标也已先核对：原版 `common/coat_of_arms/template_lists/colored_emblem_lists.txt:896` 的 `religion_icons` 列表通过 Faith `has_icon` 选取 `ce_religion_*.dds`，未匹配时使用 `ce_star_08.dds`；`common/coat_of_arms/coat_of_arms/03_religious_icons.txt` 再使用 `colored_emblem` 与随机颜色/模板。它是原生宗教主题纹章生成器，并非直接输入 Faith/Rite 的实际 RGBA 图标。没有已核的通用原图直用入口，所以不以该着色/回退列表冒充原宗教图标完全相同，而使用本次明确授权的随机路径。

精确 NUL 名称扫描未发现 `create_dynamic_coa`、`set_rite_icon` 或 `rite_has_icon`。这是补充的负面证据，单独不能证明不存在所有间接原生机制；结合上述已闭合的 effect、trigger 和纹理加载边界，本轮没有找到可交付的通用纯脚本实现。未通过新增 native bridge、修改 EXE、替换运行中图或用另一个 Faith 的图标掩盖缺口。

## 剩余验收

下一次获准的冻结运行应读取通用动态 Rite 的实际名称与新 Dynasty/House 名称，验证序列化、保存及冷载后仍一致；分别读取两个预置 Rite 的实际图标、Dynasty/House CoA、全部纹理加载错误与视觉结果。自创 Rite 应得到一次原生随机生成的新 Dynasty CoA，并证明 House 使用同一对象且冷载后保留；不得把两次随机结果偶然近似当作一致。完整产品还需独立验收最终族长、教义、继承和原有业务矩阵；本文件不为那些阶段授予通过资格。
