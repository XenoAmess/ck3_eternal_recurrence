# CK3 `textured_emblem` 浏览器预览证据

## 当前结论

浏览器已经能够合成当前 exact 1.19.0.6 唯一注册的纹理徽记：

```text
textured_emblem = { texture = "_default.dds" }
```

实现直接翻译游戏随附的 `coat_of_arms_textured_emblem` shader：采样纹理原始 RGBA，在非 portrait 路径叠加
`coa_mask_texture.dds` 的蓝通道 surface detail，并以绿通道调整 alpha，随后使用 source-alpha blend。纹理层在 pattern
之后、`colored_emblem` 之前进入浏览器构图。未注册 texture 继续保留在解析模型和导出代码中，但不生成伪预览。

## 来源绑定

| 来源 | SHA-256 |
|---|---|
| `coat_of_arms_textured_emblem.fxh` | `432202D6A4FF73743B9445EF802C5B7EEC3346F0D0A51DDBF49C5940B884ABD6` |
| `_default.dds` | `697430F86ABD26B5056A8779E4BF78C7CB526A57B5AD13F02898BA64B89526CC` |
| `coa_mask_texture.dds` | `5FA2A49DC59AEEBA19709B6BB3F9D0B017ACDE7DC576793705EAF85C7F33691E` |

原生 MCP 证据已经证明上述 `textured_emblem` 结构可 Apply，并由 CK3 Copy 保留 texture。R35 又用 reference-free v3 标定和
空间像素摘要闭合浏览器与原生 framebuffer 对照：MAE `0.0072777048`、color MSE `0.0002390189`、edge loss
`0.0271662716`、最差 8×8 空间 MAE `0.0292250253`，均通过运行前冻结的门限。原生 Copy 后重新 Apply 的更严格对照也通过，
MAE 仅 `0.0000153959`。完整证据见
[`textured-emblem-native-r35`](coat-of-arms-fit-artifacts/textured-emblem-native-r35/README.md)。这证明当前 exact pack 唯一注册
`_default.dds` 的浏览器模型在声明阈值内与原生一致；仍不声称逐像素完全相同，也不外推未注册 texture 或额外字段。

## 回归门禁

`renderer.test.ts` 用 1×1 BGRA8 夹具验证无 surface 的确定性 RGBA alpha blend；
`e2e/textured-emblem-preview.spec.ts` 构造独立静态 pack，将半透明 `_default.dds` 与 surface mask 合成，并验证预览中心像素为
`[32, 192, 95, 255]`、界面证据提示出现、完整代码仍可导出且没有非 GET 请求。

```text
pnpm exec vitest run src/domain/renderer.test.ts
pnpm exec playwright test e2e/textured-emblem-preview.spec.ts
pnpm exec playwright test e2e/textured-emblem-native-reference.spec.ts
pnpm test
pnpm build
```

浏览器实现工作包为 `c34b9100`，单样例与原生门禁修复为 `890da192`、`e7100297`。`parent` 的角色设计器剪贴板原生证据表明
有效 parent 不会在该路径物化，因此页面继续保留引用、只绘制显式字段，不冒充展开最终 parent 构图。
