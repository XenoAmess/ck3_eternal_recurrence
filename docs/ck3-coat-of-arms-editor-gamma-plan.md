# CK3 家徽编辑器 Gamma / 1.0 收口计划

> 状态：执行中（2026-09-21）
>
> 基线：`master` `c7f4392b0ce36b6b288b3303c5e277dacd513b04`
>
> 产品目录：`coat_of_arms_editer_of_ck3/`
>
> 前置阶段：[Beta 工作计划](ck3-coat-of-arms-editor-beta-plan.md)的 WP0–WP7 已全部通过；本计划不重开已经闭合的 Beta 门禁。

## 1. 目标

Gamma 的目标不是继续堆叠近似能力，而是把现有纯浏览器 Beta 收口成可以长期维护的 `1.0`：

1. 长耗时拟合即使遇到 IndexedDB 配额、站点数据清理或浏览器切换，也有可校验、可携带的恢复路径。
2. 浏览器渲染、CK3 原生 framebuffer、战役保存/重载和运行时资源胜者分别建立证据；任何一层缺证都继续显示限制。
3. 正式 GitHub Pages 始终是纯前端，用户图片和项目文件不上传，CK3/MCP/native bridge 只属于开发验收。
4. 最终形成一个可复现、可公开回读、版本与 exact asset pack 身份明确的 `1.0` 发布闭环。

## 2. 已有基线

- Beta WP0–WP7 全部通过，Quarkus/REST 生产路径已退役。
- CK3 `1.19.0.6` 基础素材包 1,630 项逐文件 hash 校验，Pages 按需加载 DDS 与搜索 shard。
- 15 例剪贴板语法矩阵、大于 128 KiB 的 MCP v2 Apply/Copy、七图原生像素与 Copy/reapply、
  `_default.dds` `textured_emblem` 和 `parent` 边界均有冻结证据。
- 128/1024/10,000 预算、暂停/继续、跨刷新 checkpoint、取消/重启、项目自动保存和三候选 Pareto 已通过。
- 当前诚实边界仍包括：并非所有 shader/VFS 组合都有原生像素证据；`replace_path` 不建模；没有通用 runtime
  definition-registry winner API；自定义家徽的战役保存/重载持久化尚未形成独立矩阵。

## 3. 不变约束

- 生产站点不得安装、启动、查看或连接 CK3，不依赖 MCP、Java、Quarkus、Python 或 Steam。
- 用户图片、项目和 checkpoint 只在浏览器本地处理；不得新增上传、遥测或远端存储。
- 所有可移植文件必须版本化、大小有界、解析 fail closed，并绑定精确内容 SHA-256；不得把成功读取 JSON 当作身份一致。
- 原生验收优先使用 typed MCP；能力不足先补结构化 MCP，不用 OCR、固定坐标或肉眼判断替代。
- exact build、asset-pack manifest、VFS receipt、输入和输出证据必须分开记录；静态 projection 不得冒充引擎内部 registry。
- 每个工作包一次必要验证后立即提交、rebase、push；原生工作包只有在 CK3 独占槽可用时才启动游戏，Steam 默认离线。

## 4. 工作包

### G0：便携拟合 checkpoint（P0，0.5–1 工程日）

状态：`passed`（2026-09-21）。

交付：

- 新增 `ck3-coa-portable-fit-checkpoint-v1` 文件合同，把目标图像/金字塔 RGBA、exact 输入 SHA、素材包 manifest SHA、
  用户预算、算法版本、模型和安全搜索游标封装为有界 JSON。
- envelope 对确定性 payload 做 SHA-256；导入时先检查文件大小、schema、hash、RGBA 长度/规范 Base64，再复用现有
  persisted-checkpoint 身份与游标校验。
- 页面提供中英文“导入/导出拟合 checkpoint”；IndexedDB 写入失败时，已导入的合法文件仍可在当前标签页恢复。
- 单元测试覆盖 typed RGBA round-trip 和 payload 篡改拒绝；production build 仍为零后端路径。

退出条件：目标单元测试、完整 Vitest、production build 与 production-boundary verifier 全绿；计划状态更新为 `passed`。

完成证据：

- `pnpm exec vitest run src/domain/fitCheckpointStore.test.ts src/i18n.test.ts`：2 files / 6 tests GREEN。
- `pnpm exec playwright test e2e/portable-fit-checkpoint.spec.ts --reporter=line`：合法文件跨刷新恢复与篡改拒绝 2/2 GREEN。
- `pnpm test`：19 files / 90 tests GREEN。
- `pnpm build` 与 `pnpm verify:production-boundary` GREEN；production bundle 的五类禁用后端标识均为 0。
- `verify_web_asset_pack.py` 对 `public` 与 `dist` 的 exact 1.19.0.6 pack 均复验 1,630/1,630 项 GREEN；
  manifest SHA-256 为 `27C8E427FE8EFF58411EF3C209BED2154058EF808317551C0001DDD5E19CEC96`。

### G1：运行生命周期与配额恢复（P0/P1，1–2 工程日，依赖 G0）

交付：

- 对 `QuotaExceededError`、IndexedDB blocked/abort、站点存储不可用分别给出可操作状态，不吞掉失败原因。
- 增加存储估算和写入前大小说明；估算只作提示，不能替代真实事务结果。
- 将安全 checkpoint 扩展到当前未覆盖的高成本阶段；每种恢复必须绑定 run revision，禁止旧 worker 结果污染新 run。
- 为 WebGL context loss 建立同 run 重建或显式 CPU fallback 合同，并证明恢复后指标仍由 CPU reference 门禁。

退出条件：故障注入 E2E 覆盖 quota、blocked、context lost 和刷新/导入恢复；无未捕获 promise；恢复前后模型与指标一致。

### G2：原生 framebuffer 证据收口（P0，1–2 工程日 + CK3 槽位）

交付：

- 对当前最终 Pareto 文档而非历史候选执行 MCP-only Apply → calibration → framebuffer → Copy/reapply。
- 预先冻结 MAE、color MSE、edge loss、空间最差块和 Copy/reapply 噪声门限；失败保留 RED attempt，不调门限追结果。
- 为已支持 shader 路径更新能力矩阵；未覆盖 texture/shader 继续保真导出并显示“无原生像素证据”。

退出条件：目标矩阵有 hash-bound 报告、原始 framebuffer、摘要与 exact commit；网页不声称 GPU 逐字节一致。

### G3：战役持久化（P0/P1，1–3 工程日 + CK3 槽位，依赖 G2 的稳定捕获能力）

交付：

- 分开验证角色设计器 Finish、进入战役、手动保存、退出、重载、重新打开目标角色/王朝/头衔家徽。
- 每一步记录稳定对象身份、Copy 回读语义摘要和 framebuffer；不以“Finish 成功”推断 savegame 已持久化。
- 明确 ruler/dynasty/title 三种目标实际支持范围；无法稳定寻址的目标不纳入通过声明。

退出条件：至少一条正式支持路径完成 fresh-userdir 保存/重载闭环；其余路径有明确 passed/limited/not-supported 状态。

### G4：运行时 VFS / definition registry 边界（P1，2–4 工程日，可与 G3 独立）

交付：

- 先研究并证明是否存在可版本化、只读、边界稳定的 runtime CoA definition/resource winner 查询点。
- 若可行，typed MCP 返回 source identity、mount ordinal、逻辑名和内容 hash；重复、循环、缺失与 build 不匹配全部 fail closed。
- 若不可行，冻结负面证据并保持现有 `resolved_overlay` 导入合同；不把 `replace_path`、静态源码顺序或 mount receipt
  猜成 engine winner。

退出条件：能力矩阵与产品提示只升级实证覆盖的格子；未知 definition/texture 仍可无损导出。

### G5：1.0 发布门禁（P0，1–2 工程日，依赖 G0–G4 的目标范围冻结）

交付：

- 从干净 checkout 执行 pack 逐文件校验、Vitest、无 CK3/无后端 Playwright、跨浏览器核心流程、production build、
  构建后 pack 复验和 production-boundary 扫描。
- 更新 README、能力矩阵、版本标签、限制与证据索引；清除已被新证据取代但仍写成“当前”的陈旧状态。
- GitHub Pages workflow 部署后，从 canonical URL 回读 commit/time、核心静态资源、离线恢复和生产零后端请求。

退出条件：所有必须门禁 GREEN，公开页面与仓库能力矩阵一致；任何原生 RED 不被文案掩盖。

## 5. 顺序与停止条件

执行顺序为 `G0 → G1 → G2 → G3`，`G4` 可在不占 CK3 槽时独立推进，最后执行 `G5`。

出现以下情况立即停止对应路径并保存证据：

- portable 文件超过上限、hash/identity/游标不一致或引用了当前 pack 不存在的资源；
- 原生 bridge、EXE build 或 asset-pack identity 不匹配；
- Steam 在线且账号显示其他机器正在游戏；
- 只能依靠 OCR/固定坐标才能声称结构或持久化成功；
- Pages 生产 bundle 出现 CK3、MCP、Java、Quarkus、localhost API 或用户内容上传路径。

## 6. Gamma 完成定义

Gamma 完成不等于“所有 CK3 家徽能力完全实现”。完成条件是：

1. 长耗时任务有 IndexedDB 与便携文件两条可验证恢复路径，并对失败给出可操作结果。
2. 浏览器、原生 framebuffer、战役持久化、VFS/registry 四层证据互不冒充。
3. 支持格子有 exact-build 原生证据；未支持格子在 parser/preview/editor/serializer/native evidence 五列中明确降级。
4. Pages 从干净 checkout 自动构建部署，纯前端、离线可用、用户数据不上传。
5. `master`、公开 Pages 版本标识、能力矩阵和冻结证据指向同一发布 commit。
