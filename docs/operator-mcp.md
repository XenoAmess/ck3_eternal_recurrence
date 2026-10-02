# 通用操作者 MCP 与交互桌面 job handoff

## 适用边界

`ck3_autonomous_player/operator_mcp_server.py` 是通用的 target-side MCP。
它解决的是“当前 Codex 进程不能把子进程放进目标操作者 token / desktop”这一执行边界，
不替代 CK3 gameplay MCP，也不包含任何账号、机器路径、CK3 轮次或具体 wrapper。

本项目按运行机器本地部署：每台机器分别启动自己的 operator MCP，本机 Codex client 只连接本机
endpoint，不跨机器调用其他操作者的服务。Git 只同步服务端代码、部署规范和可复用知识；机器专属
profile、实际 endpoint、凭据与运行中 job 状态由各机器自己持有。把代码带到另一台兼容机器后，
应在那台机器重新部署、注册并核验其本机工具。`operator_get_status` 只代表所连接机器的 live 状态；
另一台机器的状态、旧报告和 Git 投影均不能替代本机查询。

CK3 排他范围也是每台运行机器本地：同一台机器至多一个 CK3 实例，启动前用本机 operator MCP 与实际进程确认本机 owner、RED 和空闲状态。不同机器可以同时各运行一个 CK3；战争同事在另一台机器的窗口不要求本机等待其释放。共享 Steam 账号、资产或同一任务如有真实冲突，仍按各自合同协调；跨机器意图与证据通过 Git 传递，不能调用远端 MCP 或把 Git 当作实时实例锁。

目标侧 JSON profile 冻结以下部署数据：

- `target.id` 与期望 `token_user / desktop / machine`；
- `target.expected.token_user` 必须原样填写目标 server 的 `operator_get_status` 实测 `token_user`，不得自行补域前缀；
- MCP endpoint；
- 可交付 job 的完整 command、working directory、独占进程名；
- 可选的命名 stdin controls；每个 control 的 UTF-8 payload 完全由 profile 冻结；
- handoff 前必须存在并可选 size/SHA-256 复核的输入，以及必须尚不存在的输出。

MCP 调用者不能提交任意命令。公开接口只有：

- `operator_get_capabilities`：读取 server/profile 版本、target 与 job 名；
- `operator_get_status`：读取实际 token、desktop、machine、独占进程 PID 和 job 状态；
- `operator_preflight_job`：只读检查 target identity、命令、输入、输出和独占进程；
- `operator_query_steam_workshop_status_v1`：只读回读 profile allowlist 冻结的 Steam、CK3 build/EXE hash
  与 Workshop installed/latest/cache/descriptor 状态；调用方只能提供 `target_id`，不能提交 app ID、item ID
  或路径；
- `operator_handoff_job`：在同一次调用内重新 preflight，并只启动 profile 冻结的 command。
  `request_id` 对同一 server 实例幂等，返回 `server_instance_id / job_id / PID / log paths`。
- `operator_control_job`：只向仍在运行、且 `target_id / job_name / job_id` 全部匹配的 job 发送 profile
  中按名冻结的 stdin payload。调用方不能提交任意 stdin；同一 `request_id` 重放不会二次写入。
  写入或 flush 失败会保留为 `RED` 结果，幂等重放也不会偷偷重试。

未配置 `controls` 的 job 继续使用 `DEVNULL` stdin；配置了 controls 的 job 才保留 pipe，避免等待交互的
wrapper 因 stdin 永久 EOF 而错误退出。capabilities/status 只披露 control 名，不返回 payload。

## 目标操作者侧一次性 bootstrap

1. 从 `ck3_autonomous_player/operator-profile.example.json` 复制一份仓库外 profile，填入当前目标。
   profile 是每台 target 的部署配置，不提交 token、密码或 bearer credential。
2. 在目标操作者的正常交互 shell 中启动一次 server；该 shell 必须已经位于 profile 声明的 desktop：

   ```text
   "<python>" "<repo>\ck3_autonomous_player\operator_mcp_server.py" --profile "<profile.json>"
   ```

3. 同一台机器上的 Codex client 将该机 profile 的 `advertised_url` 注册为本机 Streamable HTTP MCP
   endpoint，并刷新 client/session。不得注册或调用另一台机器的 operator endpoint。MCP 配置属于
   本机 client 部署，不写进 mod、wrapper 或 live artifact。
4. 先调用 capabilities、status 和 preflight；只有三者指向同一 `target_id` 且 preflight 为 `GREEN`，
   才以新的 `request_id` 调用 handoff。CK3 类 job 的 profile 必须声明 `ck3.exe` 独占门。

Bootstrap 的唯一人工/外部边界是：首次让 server 本身运行在目标 token 与 desktop。
之后 job 继承该 server 的真实 Windows token/desktop；不得从
非目标 sandbox 复制 Explorer token、创建账号专用计划任务，或在 sandbox desktop 重试目标程序。

本仓通用部署约定是由同机 MCP client 连接同机 target-side Streamable HTTP server，endpoint 注册属于
本机 client 配置；已经运行的 session 不会因仓库内新增 server 代码而自动出现新工具。
因此 bootstrap 与 client MCP 注册完成后，必须以实际 tool listing 验证六个 `operator_*` 工具可调用。
只有 profile 包含 `steam` allowlist 时，Steam/Workshop 查询才可用；capabilities 的
`steam_workshop_status_configured` 是配置状态，不是版本或缓存通过证明。

`steam` profile 是 checked-in example 或仓库外可审阅部署数据，只能包含 Steam/library root、固定 app、
预期 build/EXE SHA-256、有限进程名和有限 Workshop item。不得写入登录凭据。第一版只读文件和进程状态，
不切换在线/离线、不启动 Steam/CK3、不打开 URI、不使用 Steam Console、不下载或更新 Workshop，也不使用
UIA/坐标。返回的 `build_matches_expected`、`installed_matches_latest` 与 hash 是实际文件 readback；
进程存在、manifest 存在或一次 MCP 调用 ACK 均不能替代这些 readback。

## Windows 进程清单的输出编码

受管 CK3 runtime 的 [ck3_process_inventory](../ck3_autonomous_player/src/xar_autoplayer/environment.py)
使用 tasklist 与 Toolhelp32 核对完整 PID 集合。实际中文 Windows ACP/OEMCP 936 的无匹配输出为
“信息: 没有运行的任务匹配指定标准。”；stdout SHA `cb1256981f7b3ac53e3cfc7c6a13d4b058702bb707431b31e202abfcf6782f07`。
Python UTF-8 模式会让未指定 encoding 的 text subprocess 将这些 CP936 bytes 错解为乱码，
导致已有 INFO/信息识别拒绝。现在只为这次 tasklist 调用显式设 `encoding="mbcs"`，采用 Windows
ANSI code page；保留原 errors、超时、未知输出拒绝、CSV 解析、两路 PID 不一致拒绝和 Toolhelp 失败拒绝。
此修复不把未知文本当空清单，也不放宽活 CK3 排他门；不声称支持所有 locale/OEM 与 ANSI 不同的情况。

一次 `-X utf8=1` 聚焦验收通过 6 项：实际给定 CP936 bytes 经 harmless Python 子进程重放并由
生产 decoder 正确读取；Toolhelp 指出有进程时仍拒绝空 tasklist，旧乱码仍拒绝，原两路差异、
RPC 失败、Toolhelp 失败与 access-denied fallback 继续保持。未执行 tasklist/Toolhelp、操作桌面、
启动 CK3 或接入 SDK；实际新受管 launch 仍 NOT_RUN。旧失败和冻结候选不由未来修复重新解释。

## 版本与复用

- profile schema：`1`
- server/tool contract：`1.2.0`（profile schema 1 的向后兼容可选 controls/Steam allowlist）
- transport：MCP Python SDK `2.0.0` 的 stdio 或 Streamable HTTP
- 可迁移对象：CK3 自动玩家、天朝二期、其他 mod 实机验收，以及其他机器的 MCP 查询调用方

复制到新操作者或机器时，只替换仓库外 profile 与 endpoint 注册；代码、tool 名和响应 schema 不变。

## G2 source-specific 的 no-launch-first 入口

G2 source-specific lifecycle 使用
`ck3_autonomous_player/native_bridge/research/prepare_g2_source_specific_operator_profile.py`
生成每台 target 的仓库外 profile。生成器要求显式提供 target identity、endpoint、当前 clone、Python、
exact-build 游戏文件、可重定位 runtime bundle、完整 settings + warm shadercache 和输出目录；仓库内不保存
固定操作者、机器路径或固定 `R{n}`。

该 profile 只有 `g2-source-specific-no-launch-preflight`：命令固定为 live adapter 的 `--verify-only`，
没有 `--authorize-private-live`、CK3 stdin control 或游戏进程独占门，因而不能启动或控制 CK3。
所有文件输入均在 operator preflight 中复核 size/SHA-256；adapter 随后再次按冻结 manifest 检查依赖和
完整 warm profile。部署命令、测试边界与 readiness 口径见
[G2 operator MCP no-launch profile](ck3-native-ai/g2-source-specific-operator-mcp-preflight-2026-09-10.md)。
