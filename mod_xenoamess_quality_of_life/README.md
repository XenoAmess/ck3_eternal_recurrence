# XenoAmess的体验优化

面向《十字军之王 III》1.19.0.6 的独立体验优化 Mod。当前开发版本为 1.1.0；Workshop 上的上一公开版本仍为 1.0.2，二期尚未发布。

## 功能

- 自动选择继任：行政制、贤能制或天朝制的独立玩家可阻止自己成为下属官职的兜底继承人，仍由原版候选池中得分最高的合资格人物接任。
- 别把封臣给我：阻止下属行政制 AI 把封臣向上转交给玩家，关闭时只清理本 Mod 拥有的保护标志。
- 自动召集防御援军：被宣战时自动召集全部当下可免费加入的 AI 盟友、受保证宗主、朝贡国、摄政和免费家族成员。
- 批量要求改信：用 0–100 滑动条设定原版接受值门槛，向领内所有达到门槛且可合法要求改信的 AI 发出请求，并在全部答复后汇总同意、拒绝人数。
- 批量牵制索款：可选择只收足额款，或向金钱大于 1 的目标收取其现有全部整数金钱；均复用原版“索取钱财”互动并消耗牵制。
- 批量赎囚：可选择只接受足额赎金，或从至少有 1 金钱的愿意付款 AI 处收取现有钱财；每笔交易后重新检查付款能力。
- 批量附条件释放：对每名愿意的 AI 囚犯选择“获得牵制、招募、要求改信”中数量最多的兼容组合，同规模按牵制、招募、改信排序。

前两项只向受支持的独立行政制、贤能制、天朝制玩家显示；二期通用批处理决议向所有非 AI 统治者显示，实际目标仍须通过对应原版互动门禁。

## 开发与验证

```powershell
py tools/gen_xqol_phase2.py --check
py tools/validate_xenoamess_quality_of_life.py
py tools/test_build_xenoamess_quality_of_life_release.py
py tools/build_xenoamess_quality_of_life_release.py --check
```

机制合同见 `docs/mechanics.md` 与 `docs/phase-two-vanilla-contract.md`，实机矩阵见 `docs/acceptance-plan.md`。正式发布必须等实机验收、Workshop 上传、订阅缓存复核和 changelog 全部完成。
