# CK3 家徽编辑器中英文界面合同

## 范围

GitHub Pages 正式界面提供简体中文（`zh-CN`）和英文（`en`）。首次访问在没有既存偏好时读取浏览器语言列表：任一语言以
`zh` 开头时选择简体中文，否则选择英文。用户通过页首语言选择器切换后，偏好只写入浏览器本地
`localStorage/ck3-coa-ui-locale-v1`，不会产生网络请求或上传用户内容。

语言切换同时覆盖：

- 页面标题、导航动作、图片拟合、进度与指标；
- 代码导入、诊断容器和 CK3 语法能力矩阵；
- 构图预览、候选比较、结构化表单和确定性导出；
- Element Plus 内置组件文案、`html[lang]` 与浏览器标签标题；
- 正式网页可见的素材包、自动保存和拟合运行状态。

CK3 资源名、render-description 源码、SHA-256、合同 ID、shader 名称及原生枚举值属于数据，不翻译。开发期隐藏的本机 MCP
伴随面板不进入正式 Pages bundle 的可见产品流程，其原生 reason 字段也保持来源文本，避免改变证据含义。

## 实现与门禁

实现位于 `coat_of_arms_editer_of_ck3/src/i18n.ts`，使用仓库内类型约束字典，不增加第三方国际化运行时。能力矩阵的英文证据
文字与对应行放在同一个 `capabilityMatrix.ts` 数据结构中，避免语言版本的证据范围发生漂移。

自动化门禁：

```text
pnpm exec vitest run src/i18n.test.ts src/domain/capabilityMatrix.test.ts
pnpm exec playwright test e2e/i18n.spec.ts
pnpm build
```

浏览器测试从简体中文切到英文，展开能力矩阵，并检查正式可见界面除语言选择器中的“简体中文”选项外不残留汉字；随后刷新
页面证明英文偏好持久化，再切回简体中文。该门禁验证界面国际化，不翻译用户导入的源码或项目内容。
