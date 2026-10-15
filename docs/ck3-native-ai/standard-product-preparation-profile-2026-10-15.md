# 产品准备回执与正常退出静态预检（2026-10-15）

More Tenets Slots 的真实 48 文件候选在 public prepare 后，完整 host 静态预检报告 `public preparation and selected runtime identities differ`，没有启动 CK3。产品适配器自行写了私有 preparation schema，且缺少选定引擎身份；原有正常退出 profile 投影只接受标准 fixture 准备回执。

现在产品适配器在 `materialize_product_profile` 和产品字节核对之后，调用：

```python
profile = finish_product_profile(context, profile, provenance={...})
```

helper 保留原 profile 返回字段并增加 `preparation` pin。它复用选定 source 的 `engine_identity`，核对当前游戏版本及 EXE SHA 与 shared runtime 一致，写入 `ck3-mod-acceptance-prepared-product-v1` 回执及标准 startup evidence。回执包含 `state_dir`、`profile_dir`、完整文件路径/字节数/SHA、原 product inventory 和产品自有 provenance；明确 `fixture_mounted=false`，不生成 fixture start policy、存档或启动权限。

`normal_exit_profile.project_profile` 接受这一标准产品 schema，同时保留原 fixture 路线。产品回执的引擎身份、startup 文件列表及 hash map 必须一致，每个文件仍须位于实际 profile 下且匹配原准备字节。私有 schema、身份不符或准备后改动文件仍拒绝，不能把任意来源改名后直接准入。

通用协议与 helper 归框架；产品保存来源、真实候选源码和具体场次回执归独立产品仓库。本次原始 RED 位于该项目 `artifacts/bugfix-20261015/native-v11-legacy-005-full-host-preflight-stdout.json`，旧 runtime005 及失败原件不改写。后继 runtime006 仅合入本次准备 helper 与投影校验的增量，继续复用已选择的 native DLL。

离线回归覆盖真实 `materialize → finish → normal-exit inventory build/verify` 调用链、engine 不符、准备前后文件/清单改动及私有 schema 拒绝；与既有 profile 回归合计 13 项通过。完整产品 public prepare→wrapper/profile 静态预检另存实际回执；准备或静态预检通过不授予实机、正常退出或产品业务通过资格。
