# 通用操作者 MCP 与交互桌面 job handoff

## 适用边界

`ck3_autonomous_player/operator_mcp_server.py` 是通用的 target-side MCP。
它解决的是“当前 Codex 进程不能把子进程放进目标操作者 token / desktop”这一执行边界，
不替代 CK3 gameplay MCP，也不包含任何账号、机器路径、CK3 轮次或具体 wrapper。

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

   ```powershell
   & "<python>" "<repo>\ck3_autonomous_player\operator_mcp_server.py" --profile "<profile.json>"
   ```

3. Codex client 将 profile 的 `advertised_url` 注册为 Streamable HTTP MCP endpoint，并刷新 client/session。
   MCP 配置属于 client 部署，不写进 mod、wrapper 或 live artifact。
4. 先调用 capabilities、status 和 preflight；只有三者指向同一 `target_id` 且 preflight 为 `GREEN`，
   才以新的 `request_id` 调用 handoff。CK3 类 job 的 profile 必须声明 `ck3.exe` 独占门。

Bootstrap 的唯一人工/外部边界是：首次让 server 本身运行在目标 token 与 desktop。
之后 job 继承该 server 的真实 Windows token/desktop；不得从
非目标 sandbox 复制 Explorer token、创建账号专用计划任务，或在 sandbox desktop 重试目标程序。

本仓通用部署约定是由本地 MCP client 连接 target-side Streamable HTTP server，endpoint 注册属于
client 配置；已经运行的 session 不会因仓库内新增 server 代码而自动出现新工具。
因此 bootstrap 与 client MCP 注册完成后，必须以实际 tool listing 验证五个 `operator_*` 工具可调用。

## 版本与复用

- profile schema：`1`
- server/tool contract：`1.1.0`（profile schema 1 的向后兼容可选 controls）
- transport：MCP Python SDK `2.0.0` 的 stdio 或 Streamable HTTP
- 可迁移对象：CK3 自动玩家、天朝二期、其他 mod 实机验收，以及其他机器的 MCP 查询调用方

复制到新操作者或机器时，只替换仓库外 profile 与 endpoint 注册；代码、tool 名和响应 schema 不变。
