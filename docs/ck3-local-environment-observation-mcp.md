# CK3 本地环境观测 MCP

## 分层与工具

本能力把可复用的只读观测放入现有两层，不从外部 mod suite 复制项目硬编码：

| 层 | 工具 | 固定根/allowlist | 副作用 |
| --- | --- | --- | --- |
| gameplay/native stdio MCP | `ck3_inspect_save_artifacts_v1` | setup 登记的 isolated `state/profile/save games` | 无 |
| gameplay/native stdio MCP | `ck3_query_engine_diagnostics_v1` | 同一 isolated profile 的固定 logs/crashes | 无 |
| gameplay/native stdio MCP | `ck3_query_engine_log_literals_v1` | 同一 isolated profile 的单份固定日志 | 无 |
| operator/local-environment MCP | `operator_query_steam_workshop_status_v1` | operator profile 冻结的 Steam root、CK3 app 和 Workshop items | 无 |

ordinary seed/checkpoint rebinder 仍是 runner 内部的有防护复制步骤，不公开第二个任意复制 MCP。Steam 查询
也不进入 gameplay bridge；它不依赖游戏内 ABI，不应污染 native snapshot/action 合同。

## 工具合同

### 存档 artifact

`ck3_inspect_save_artifacts_v1()` 没有参数。它只枚举已配置 profile 的 `save games`，每项返回文件名、
profile-relative path、bytes、SHA-256 和格式判定：

- ZIP：执行 `testzip`/CRC，要求 `gamestate`，返回有界成员元数据；
- 原生 SAV header：只报告 `header-only`，不声称正文已解析；
- 其他内容：`format=unknown`、`integrity=none`。

MCP input schema 是封闭对象，任意 `path/root/glob` 或未知字段都被拒绝。

### 运行诊断

`ck3_query_engine_diagnostics_v1` 只读 `error.log`、`debug.log`、`game.log`、`system.log`、`gui_warnings.log`
和固定命名的 crash package。单日志上限 64 MiB；调用方只能调小/调大已设上界内的 tail、
fingerprint 与 crash package 数量，不能传路径或 regex。响应包含 E/F/W occurrence、bytes/SHA-256、
受限 tail/milestone、归一化指纹，以及受限异常摘要和 tracked-file hash。日志行/指纹组均不得解释为 bug 数。

`ck3_query_engine_log_literals_v1(log_name, literals, sample_limit=3)` 使用同一固定日志名集合，只接受
1—16 个非空、单行、大小写敏感的字面量，单项最多 160 字符；返回每个字面量命中的行数、最多 5 条
有界样本、扫描字节 SHA-256 与总行数。它不接受 regex/任意路径，也不把零命中扩大为超过 CK3 自身
日志封顶之后的结论。该工具用于定向验证低频错误，不依赖指纹排名前 N 项。

### Steam/Workshop 状态

`operator_query_steam_workshop_status_v1(target_id)` 使用 operator profile 的 `steam` allowlist。响应读回：

- Steam executable、`WantsOfflineMode` 值和 allowlist 进程 PID；
- app manifest/build、manifest hash、安装目录、EXE hash 与冻结期待值比较；
- Workshop manifest/hash，以及每个 allowlist item 的 installed/latest manifest、cache/descriptor 存在性和
  descriptor hash。

它拒绝额外 app/item/path 参数。未上收 Steam 上线/离线切换、URI、Console download、Workshop 更新、
UIA 或固定坐标能力；这些都是外部写操作，不能由一次通用状态查询隐式授权。

## 安装、注册与验证

gameplay/native 三个工具随现有 per-user stdio server 注册：

```text
py ck3_autonomous_player\codex_mcp_setup.py setup
py ck3_autonomous_player\codex_mcp_setup.py doctor
```

`plan.local_profile_observation` 记录工具名和固定 profile root；doctor 使用官方 MCP client tool listing
验证三者可见，但不读取真实存档/日志。新注册后必须新开 MCP client session，再以实际 listing 确认。

operator 层复制并审阅 `ck3_autonomous_player/operator-profile.example.json`，通常把实际部署 profile 放在
仓库外；启动与注册方式见 [通用操作者 MCP](operator-mcp.md)。实际 listing 应有六个 `operator_*` 工具，
capabilities 的 `steam_workshop_status_configured=true` 只证明 profile 配置存在。

## 隐私、权限与 ACK/readback

- profile 不得包含 Steam/Codex 密码、cookie、token 或 bearer credential；工具不会返回 `loginusers.vdf`
  的账户字段，只提取离线标志。
- 响应会包含本机绝对 Steam/cache 路径；日志 tail、crash 摘要可能包含本地运行信息。只面向本机受信任
  MCP client，发布报告前应做最小必要摘录和脱敏。
- 四个工具均为 readback，不是动作 ACK。`manifest_exists`、进程 PID 或 RPC 成功不等于 Steam 已更新、
  游戏已启动或 mod 已加载；只有冻结期待值比较和对应文件 hash 能支持各自的窄结论。
- seed rebinder 的“复制完成”也必须连同复制后逐文件 SHA readback 才成立；它不证明 CK3 已成功加载存档。
