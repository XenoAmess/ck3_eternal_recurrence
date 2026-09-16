# CK3 家徽 fit-index v2

状态：浏览器合同与 exact 1.19.0.6 静态 pack 验证通过；它是 WP3 的搜索索引基础设施，不单独等同于图片质量提升或原生像素验收。

## 目标与边界

v1 已把 1,619 个可生成资源缩成 32×32 RGBA8 atlas，但浏览器首次搜索仍要逐项计算内容边界、质心、跨度和 18×18 描述符。
v2 保留该 atlas 的精确字节并新增内容寻址 feature sidecar。正式页面只通过静态 GET 读取 manifest、atlas、sidecar 和最终入选 DDS；
不读取游戏安装、不调用 CK3/MCP/Java/Python，也不上传用户图片或拟合数据。

旧 `ck3-coa-fit-index-v1` 素材包仍可导入。它没有 sidecar 时，在 Worker 启动前由浏览器对已校验的 RGBA atlas 使用同一确定性算法
计算特征；不会静默伪造 v2 状态。`ImageFitResult.provenance.shapeFeatureIndex` 分别报告预计算和 fallback 项数。

## 二进制合同

manifest 的 `fit_index.schema` 为 `ck3-coa-fit-index-v2`，`features` 使用：

- schema：`ck3-coa-shape-features-v1`；
- format：`F64LE_SCALARS_F32LE_DESCRIPTOR`；
- 32-byte header：8-byte `CK3FIT2\0` magic，随后六个 little-endian uint32，依次为 version、记录数、RGBA 分辨率、描述符边长、
  scalar 数和 record bytes；
- 每条 1,400 bytes：13 个 float64 scalar 加 18×18 个 float32 descriptor；
- scalar 顺序：归一化 max-exclusive 内容边界 4 项、内容质心 2 项、内容跨度 2 项、平均 alpha 能量、平均 premultiplied RGB
  三通道能量、平均右/下相邻强度差轮廓能量；
- shape intensity 为 `alpha × max(R,G,B)`；若颜色能量小于 alpha 能量的 5%，改用 alpha，保证黑色不透明 emblem 不被误判为空；
- 内容阈值为 `0.04`，描述符在实际内容边界内按固定像素中心取样。

浏览器在构造任何候选前同时验证 atlas/sidecar 的 URL 目录约束、精确 bytes、SHA-256、header、record 数、字段顺序及全部数值的
有限性和 `0..1` 范围。任一项不符便 fail closed；不会部分采用 sidecar。

## exact 1.19.0.6 回执

| 字段 | 值 |
|---|---:|
| fit 条目 | 1,619 |
| RGBA atlas bytes | 6,631,424 |
| RGBA atlas SHA-256 | `6FA0A2FF6510730EDA5F64F55EEC81044209761C03E7FA4120CD1D14C21B0A2F` |
| v2 feature bytes | 2,266,632 |
| v2 feature SHA-256 | `76429584EE906D7E0B2AEA4163FF2ABF690E6254571CB267CE281B402063DC26` |
| manifest bytes | 1,043,868 |
| manifest SHA-256 | `27C8E427FE8EFF58411EF3C209BED2154058EF808317551C0001DDD5E19CEC96` |
| 原 RGBA atlas 对比 | `fc /b`：无差异 |

生成发生在独立临时目录；verifier 通过后才晋级 manifest 与新 sidecar，临时目录随后删除。构建只读明确的 CK3 1.19.0.6 根，
当前 manifest 相比最初 v2 fit-index 证据只新增 VFS receipt；RGBA atlas 与 feature sidecar 的 bytes/SHA 均未改变。
没有启动或连接游戏。

## 验证

从 `coat_of_arms_editer_of_ck3` 执行：

```text
python tools/verify_web_asset_pack.py public/asset-packs/ck3-1.19.0.6
pnpm exec vitest run src/domain/assetPack.test.ts src/domain/shapeFeatures.test.ts src/domain/imageFitter.test.ts
pnpm test
pnpm build
pnpm verify:production-boundary
pnpm exec playwright test e2e/i18n.spec.ts
```

已覆盖 v1 兼容、v2 manifest、sidecar hash/header/字段合同、黑色 alpha fallback、透明边界/通道/轮廓计算、Worker 候选传递和页面
版本显示。质量候选、hunter 重跑及原生对照仍按 WP3 独立验收，不用本基础设施门禁替代。
