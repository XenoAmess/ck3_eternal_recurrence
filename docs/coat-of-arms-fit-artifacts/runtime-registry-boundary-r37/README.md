# CoA runtime registry boundary R37

> 结论：`bounded_negative`。对 exact CK3 `1.19.0.6`，当前没有足够证据安全发布 runtime CoA definition/resource winner 查询；
> Gamma G4 因此保留现有 hash-bound `base_game_only` / `resolved_overlay` 合同，不把二进制字符串或静态装载投影升级成引擎事实。

## 本轮确认了什么

[`evidence.json`](evidence.json) 绑定 95,206,008-byte `ck3.exe`，SHA-256 为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。该 exact 可执行文件包含：

- `coat_of_arms_manager_database[_keys|_values]`；
- `coat_of_arms_manager_name_map[_keys|_values]`；
- `coat_of_arms_manager`；
- `coat_of_arms_dynamic_definitions.cpp` 与 `coat_of_arms_script_database.cpp` 路径标签。

这些标签证明引擎内部确有相应命名状态，但不提供 accessor RVA、对象生命周期、容器布局、线程合同、definition merge、
resource resolver 或来源身份。仅凭标签反推内存并公开 MCP 会把“能找到字符串”冒充“有稳定 ABI”，不满足本项目 fail-closed 门禁。

## 当前可公开的能力边界

- `ck3_query_coat_of_arms_definition_catalog_v1` / `ck3_read_coat_of_arms_definition_v1`：exact-build 基础游戏静态源码，明确
  `engine_mount_observed=false`、`vfs_winner_claimed=false`，不含 DLC/mod override。
- `ck3_project_coat_of_arms_vfs_asset_winner_v1`：完整 live mount receipt 加源字节的 direct-DDS 投影，明确
  `engine_resolver_called=false`、`resource_registration_observed=false`、`replace_path_applied=false`、
  `definition_merge_applied=false`。
- Pages：只消费逐文件 SHA-256 与 winner-set hash 绑定的素材包；未知 definition/texture 保真导出并显示证据限制。

因此本轮没有新增 `runtime_registry` MCP。后续只有在 exact build 上取得只读 accessor、稳定对象/容器合同、重复/循环/缺失
fail-closed 行为以及原生对照后，才能新开版本化能力；R37 不妨碍这类后续研究，但禁止在证据出现前提升产品声明。

## 复验

```text
py tools/test_audit_coa_runtime_registry_boundary.py
py tools/audit_coa_runtime_registry_boundary.py --ck3-executable C:\SteamLibrary\steamapps\common\CRUSAD~1\binaries\ck3.exe --output docs\coat-of-arms-fit-artifacts\runtime-registry-boundary-r37\evidence.json
```

第一条是跨平台 source-contract 回归并已加入官方 Windows static CI；第二条读取本机 exact executable 并重建冻结证据。
