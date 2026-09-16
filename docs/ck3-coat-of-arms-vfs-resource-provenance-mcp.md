# CK3 家徽 direct-DDS 来源投影 MCP

> 状态：R30 exact `1.19.0.6` 原生 MCP GREEN。能力是基于实时完整 mount receipt 与源字节的确定性 direct-DDS winner projection，不是 CK3 内部 resolver 或 CoA registry 的调用结果。

## 为什么补这项能力

R22/R23 的 reference-free framebuffer 已证明 direct DDS 在受控目录/ZIP 夹具中的后挂载优先行为；R28 又通过结构化 MCP 收齐 34 条 caller-local mount 顺序。但仅有 mount 顺序仍不能回答“某一逻辑路径在哪些 source 中实际存在、投影 winner 的精确字节是什么”。

新工具 `ck3_project_coat_of_arms_vfs_asset_winner_v1` 将两类已有证据连接起来：

1. 从当前 bridge diagnostics 读取 exact-build、无失败、无覆盖、ordinal 连续的 `physfs_mounted_data_observer_v1`；
2. 只接受 `patterns`、`colored_emblems`、`textured_emblems` 下已规范化的相对 `.dds` 路径；
3. 有界检查每个已观察目录或 ZIP，读取 DDS header、bytes 与 SHA-256；
4. 按 R22/R23 已实证的 direct-DDS 后挂载优先合同选择最后一个候选；
5. 在结果里固定写出未覆盖的引擎语义，禁止上层把 projection 升格成 resolver 事实。

输入 schema 是关闭的双必填对象：`game_directory`、`logical_path`，未知参数拒绝。当前有界值为 128 mounts、每个 archive 50,000 members、单个 DDS 16 MiB、逻辑路径 512 characters。挂载回执不完整、路径截断/越界、source 消失、archive member 大小写歧义、非 DDS、executable SHA 不匹配都会 fail closed。

## MCP 输出

主要字段：

- `status`：`projected_direct_asset_winner` 或 `not_found_in_inspectable_mounts`；
- `candidates`：按 mount ordinal 的全部命中项，含 source kind/path、asset bytes/hash 与 DDS 摘要；
- `winner`：最后一个候选，未命中则为 `null`；
- `inspected_mounts`：每个 mount 的类型和是否命中；
- `provenance.mount_receipt_sha256`：对有序 ordinal/path/raw-result 投影的绑定；
- `provenance.claim_scope=direct_dds_path_winner_projection_only`；
- `engine_resolver_called=false`、`resource_registration_observed=false`、`replace_path_applied=false`、`definition_merge_applied=false`。

## R29/R30 结果

R29 先对 R28 冻结回执离线回放，四条路径全部得到确定结果。R30 随后在新原生会话中由官方 MCP 实际执行相同四个 query：

| 路径 | 候选 ordinal | winner ordinal | winner SHA-256 |
| --- | --- | ---: | --- |
| `pattern_checkers_06.dds` | 3 | 3 | `58B4322BBE5046AFEDC4E350F283A1AAEF48A6E86A5A40BF5FDB20321C519849` |
| `pattern_xar_vfs_replaced_earlier.dds` | 33 | 33 | `58B4322BBE5046AFEDC4E350F283A1AAEF48A6E86A5A40BF5FDB20321C519849` |
| `pattern_solid.dds` | 3、34 | 34 | `0EE08A10EE4C71278C0ACE98506DD2A520261B20E040B353B7DA4D13C0616C4A` |
| `pattern_xar_vfs_replace_later.dds` | 34 | 34 | `ED859E29211712AC51E2BFF108CBAB58A72B48F62C1D875494CB036979B71A0C` |

R30 为 34/34 mount success、0 failure、0 overwrite；9 次 MCP 调用、0 omission；完整报告 SHA-256 为 `AA21DA1D45CB5DB3D2048A1EEE7DE3EF368DA9FFA5A1C3EC09442CEA1F4181C4`。证据见 [R29 replay](coat-of-arms-fit-artifacts/vfs-asset-projection-r29/README.md) 与 [R30 native MCP](coat-of-arms-fit-artifacts/vfs-asset-projection-native-r30/README.md)。

## 对最终网页的影响与剩余缺口

直接影响不是“拟合图立刻更像”，而是提高 asset pack 的可信度：开发工具可以据实生成 direct-DDS source receipt，网页继续离线验证并消费 hash-bound winner set，避免把未解析的本地覆盖偷偷混进 pack。

WP6 仍保持 `in_progress`，因为以下能力尚未闭合：

- CK3 内部 resolver/CoA registry 的结构化单资源 provenance；
- `replace_path` 对注册前后时序的真实引擎语义；
- definition merge 与 DLC/mod definition winner；
- `textured_emblem` 的原生像素对照。

在这些缺口补齐前，浏览器只能把 direct-DDS projection 标为开发期来源证据，不能承诺与所有 CK3 资源解析路径完全一致。
