# CK3 native MCP：按 Windows 用户安装与 Codex 注册

状态：注册/自检层可用；复用现有 native provider，不新增第二套换人实现。

仓库入口为 `ck3_autonomous_player/codex_mcp_setup.py`。它只做四件事：

1. 为当前 Windows 用户创建独立 Python venv，并只安装 MCP SDK/Windows transport 依赖；
2. 用 Codex CLI 注册仓库现有的 `ck3_autonomous_player/mcp_server.py`；
3. 固定该用户独享的 MCP server name、named pipe、state directory 和 CK3 userdir；
4. 在不启动 CK3 的前提下检查 Python/MCP SDK、Codex 注册、通用换人接线和可选 native 产物。

该入口不会创建 named pipe、不会运行 `native-session`、不会注入 DLL，也不会启动 CK3。计划中出现的
native build/session 命令只是 JSON 字段，只有操作者另行执行时才会生效。

## 当前账户的一键安装与注册

在仓库根目录运行：

```powershell
py ck3_autonomous_player\codex_mcp_setup.py plan
py ck3_autonomous_player\codex_mcp_setup.py setup
py ck3_autonomous_player\codex_mcp_setup.py doctor
```

`setup` 会在当前账户的 `%LOCALAPPDATA%` 下创建：

```text
XarAutoplayer\codex-mcp\<account-slug>\venv
XarAutoplayer\codex-mcp\<account-slug>\state
XarAutoplayer\codex-mcp\<account-slug>\state\profile
```

同时注册：

```text
server: xar-ck3-native-<account-slug>
pipe:   \\.\pipe\xar_ck3_bridge_mcp_<account-slug>
```

注册命令指向 per-user venv 和当前 checkout 内的 `mcp_server.py`，driver 固定为
`native-headless`、transport 固定为 `stdio`。已有同名且完全一致的配置会幂等返回
`already_registered`；同名配置不一致时默认拒绝覆盖，只有显式 `setup --replace` 或
`register --replace` 才会调用 Codex CLI 替换。

per-user venv 只安装 `mcp==2.0.0` 与 `pywin32==312`；项目 Python 源始终从当前 checkout 的
repository-local bootstrap 加载，不复制源码，也不会为纯 native MCP 安装视觉/GPU 依赖。

Codex 在每个 Windows 账户自己的 `~/.codex/config.toml` 中维护注册。完成注册后新开一个 Codex
会话，让该会话重新发现 MCP 工具。

## xenoa 与 CodexSandboxOffline

不要从 `xenoa` 的进程代写 `CodexSandboxOffline` 的 Codex 配置，也不要让两者共享 state、userdir
或 named pipe。分别登录或以对应账户启动 shell，在每个账户中各运行一次同样的 `setup`：

```powershell
# 在 xenoa shell 中
py ck3_autonomous_player\codex_mcp_setup.py --account xenoa setup

# 在 CodexSandboxOffline shell 中
py ck3_autonomous_player\codex_mcp_setup.py --account CodexSandboxOffline setup
```

执行写操作时，入口会核对 `--account` 与当前 Windows 账户；不匹配直接 RED。`plan` 仍可为另一账户
生成预览，例如：

```powershell
py ck3_autonomous_player\codex_mcp_setup.py `
  --account CodexSandboxOffline `
  --local-app-data C:\Users\CodexSandboxOffline\AppData\Local `
  plan
```

每个 state 根都有 `portable-mcp-layout-v1.json`，doctor 要求其账户、server、pipe 和路径与当前计划
逐项一致，避免误接另一个账户的 episode/checkpoint。

## 通用换人能力

注册层直接复用公开 MCP 工具：

```text
ck3_set_played_character_v1(character_id, expected_revision)
game.command.set-played-character-v1-N
```

典型调用顺序是先用 `ck3_take_snapshot` 取得暂停帧及 `revision`，再把该 revision 与目标
CharacterID 传给换人工具。目标必须存在、存活且未被另一玩家控制；地图必须 ready 且暂停；DLL 必须匹配
CK3 `1.19.0.6`、EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

换人是显式 operator action，不会进入 autonomous planner。成功只认 native readback 的
`switched/already_played`、目标 CharacterID、paused/map-ready 和 `postcondition_verified=true`。

## Native 产物与严格 doctor

注册 MCP 不等于 CK3 native session 已就绪。fresh build 产物被 Git 忽略；换机器后应在 x64 Visual
Studio developer shell 中运行 `plan` 输出的 `fresh_native_build_command`，或直接调用：

```powershell
& ck3_autonomous_player\native_bridge\tools\build_fresh.ps1 `
  -BuildDir <new-empty-build-dir> `
  -Ck3ExecutablePath <CK3-root>\binaries\ck3.exe
```

然后把 fresh DLL/injector 显式交给 plan/doctor：

```powershell
py ck3_autonomous_player\codex_mcp_setup.py `
  --game-dir <CK3-root> `
  --bridge-dll <build-dir>\xar_ck3_bridge.dll `
  --bridge-injector <build-dir>\xar_ck3_bridge_injector.exe `
  doctor --require-native-assets
```

严格 doctor 会计算 CK3 EXE SHA-256，并要求 exact build、DLL、injector、per-user venv、layout marker、
Codex stdio 注册和通用换人源码接线全部就绪。它仍不会启动 CK3。

带 `--bridge-dll/--bridge-injector` 的 `plan` 会额外输出 matching `native_session_command`。该命令必须
由同一 Windows 账户另行运行，并与 MCP 使用完全相同的 pipe/state。它属于 CK3 启动环节，仍受项目的
CK3 排他串行门约束。

## 另一台机器

另一台机器不要复制现有 `tools/.venv` 或 ignored build 目录：Windows venv 的 `pyvenv.cfg` 会绑定创建
它的 Python 安装绝对路径。最短复用流程是：

1. clone/rebase 到目标 commit；
2. 安装 Python 3.11+ 与 Codex CLI；
3. 准备完全匹配的 CK3 `1.19.0.6`；
4. 在目标账户运行本页 `setup`，重建 per-user venv 和 Codex 注册；
5. 用 fresh helper 在本机构建、测试 DLL/injector；
6. 执行严格 doctor；
7. 另行启动 plan 输出的 matching native session。

若 CK3 EXE SHA 不同，注册层仍可安装，但通用换人 native capability 不可用；必须先为新 build 逆向并
接入新的 adapter，不能复用 `1.19.0.6` 的 RVA/ABI。

现有 streamable HTTP transport 不用于本流程。native bridge 控制的是本机 CK3 进程与本机 named pipe，
因此每台机器本地运行 stdio MCP 是最短、最明确的复用方式。
