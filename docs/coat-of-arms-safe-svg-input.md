# CK3 家徽编辑器安全 SVG 输入合同

状态：`WP6 in_progress / safe SVG sub-gate passed`  
日期：2026-09-15（Asia/Shanghai）  
实现提交：`d5dce949`

SVG 现在可作为图片拟合输入，但不会被原样插入 DOM，也不会进入 CK3 代码。浏览器先解析 XML，按白名单拒绝危险或无界结构，再把净化后的
SVG 通过短生命周期 `blob:` URL 解码为 `ImageBitmap`；URL 在解码函数返回前撤销。随后只把 RGBA 像素交给既有纯浏览器拟合器。

冻结的资源边界：SVG 文件 ≤ 2 MiB，栅格宽高各 ≤ 4,096，元素 ≤ 5,000，嵌套深度 ≤ 64。支持 `path`、基础形状、group、defs、
clip/mask、文档内 use、线性/径向渐变等有限矢量元素。只允许白名单属性，`href`/`xlink:href` 只能是当前文档 `#id`，CSS `url()`
只能是 `url(#id)`。

以下内容在图像解码前 fail closed：DOCTYPE/ENTITY、`script`、`foreignObject`、`image`、iframe/object/embed/media、动画、style 元素或
属性、任何 `on*` 事件属性，以及 `http:`、`https:`、`data:`、`file:`、`javascript:`、`vbscript:` URI。由于不允许文本和 CSS，
字体加载与 CSS import 也不在输入面内。该策略有意牺牲复杂 SVG 兼容性，换取静态 Pages 环境的确定边界。

`e2e/safe-svg-input.spec.ts` 已证明：带内部 clipPath 的 320×240 SVG 能生成本地预览并启用拟合；外部 image、外部 use、script 和 onload
分别被拒绝；整个测试对 `evil.invalid` 的请求为 0，所有非 GET 请求为 0。全量 Vitest 15 文件/74 项及生产 build 同次通过。

复现命令（`coat_of_arms_editer_of_ck3/`）：

```text
pnpm exec playwright test e2e/safe-svg-input.spec.ts --reporter=line
pnpm test
pnpm build
```

此证据证明浏览器净化和无外传边界，不证明任意复杂 SVG 均受支持，也不代表 SVG 内容会进入 CK3；最终 CK3 输出仍只使用独立素材包内的
原生 DDS 元素重建。
