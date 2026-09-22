# 战争影片实机入口：原生桥重建与预检

日期：2026-09-23。服务于[重做 W8](war-video-research-rebuild-2026-09-23.md)，当前尚未启动 CK3，未拍摄新素材。

旧片取材使用的已有 DLL 缺少三项正式 1066 开局 capability，导致 no-launch RED。
本轮读取源码后确认 `frontend_gui_route_v1.hpp/.cpp`、`ck3_11906_adapter.cpp` 和 bridge dispatcher 已有对应实现。
下一步是以 private selected-bookmark/Robert 配置构建新 DLL，再读取实际 capability 和运行后置；无需把旧 DLL 的缺失永久视为取材不可用。

## 实际构建阻点与修复

- `bridge-build-r1`：调用环境没有 `cmake`；保留 environment RED，随后显式取得 x64 Visual Studio 环境。
- `bridge-build-r2`：CMake configure 成功，但 `build_fresh.py` 读取 `rules.ninja` 时抛出 `UnicodeDecodeError`。
  本机只有中文 2052 compiler resource，CMake 将 `msvc_deps_prefix` 以 CP936 写入，旧 helper 假定整个文件 UTF-8。
- 修复 [build_fresh.py](../../ck3_autonomous_player/native_bridge/tools/build_fresh.py)：按 bytes 找到唯一 prefix，仅该值先尝试 UTF-8、再尝试 CP936，写回正确 UTF-8 前缀；其余规则字节不变。
  原有 UTF-8 与乱码恢复分支保留。既有 [helper 测试](../../ck3_autonomous_player/tests/unit/test_native_bridge_fresh_build_helper.py)增加真实混合编码回归，**7 项通过，0.911 秒**。
- `bridge-build-r3`：使用修复后的 helper 在全新目录重新构建；完成情况将在此追加，不能将 configure 或测试通过当作 DLL 已可运行。

三个 attempt 永久保留于 `D:/workspace/ck3_war_film_research_20260923/bridge-build-r{1,2,3}/`，
包括 request、build log、已完成 attempt 的 completion 及工具路径。未修改旧 RED 为 GREEN。
使用本工作树 `tools/.venv/Scripts/python.exe`，MSVC 19.51.36256.0；游戏 EXE 实测为 1.19.0.6 基准 SHA。

```text
tools\.venv\Scripts\python.exe ck3_autonomous_player/tests/unit/test_native_bridge_fresh_build_helper.py
```

native 构建参数为 `--focused-feudal-start --feudal-1066-selected-bookmark-private --feudal-1066-target-robert --build-jobs 2`。
`open_kaishek` 对此包为 not-applicable：正在编译 C++ 入口，未执行游戏脚本夹具或有限运行时。实际开局/观测前还须另行评估适用子集、确认 Steam 离线并取得唯一 CK3 槽。

## r3 真实构建后的二次修正

`bridge-build-r3` 的 266 个构建步骤完成，但 helper 在原有依赖检查中拒绝产物：
Ninja 没有记录 `ck3_11906.cpp.obj` 对 `ck3_11906.hpp` 的依赖。这不是新 DLL 的运行通过。
原因是本机 cl 的 `/showIncludes` 仍输出 CP936，而上一修复把 CMake 已正确检测的 prefix 转成 UTF-8；
Ninja 按字节匹配，前缀不相同就不能识别头文件依赖。上一段“写回正确 UTF-8”仅记录 r3 的尝试，现已被实际构建证据否定。

本次保留合法 CP936 prefix 的原始字节，新增 `direct-2052-cp936` 结果，仍允许原有 UTF-8 和已证实的乱码恢复分支。
将原回归测试改为检查**字节保持**，同一解释器 7 项测试通过（1.040 秒）。
`bridge-build-r4` 在新目录重新构建；依赖完整性、源码指纹和 focused CTest 均继续强制执行。
r3 日志及失败收据永久保留，未复用其构建目录，也没有放宽门禁。

## r4 构建与实际 no-launch 预检通过

`bridge-build-r4` 已完成 266 个构建步骤、两项 focused CTest（均通过，0.43 秒），
`ck3_11906.hpp` 的依赖记录检查与前后源码指纹检查均通过。
DLL SHA-256 为 `3C80CE33450C8D2668E4A8CD23168787FABD2B7A3BD8FC3F352175B2C16C517D`，
injector SHA-256 为 `D522868A59039EB106DD123364D9D990A909B5ABD7472F16CF6FF78A3EC3A9F2`。

实际预检又发现项目 capture wrapper 错把 Python 的 selected-candidate 投影常量当作 DLL command capability。
`native_driver.py` 的 `query_frontend_selected_1066_feudal_candidate_v1` 实际调用已存在的
`probe-frontend-bookmark-model-v1`，并核对选中模型、日期、政府与角色键；没有独立同名 native command。
已修正 wrapper 的字节字符串门，仅检查真正调用的五项 native capability，并在收据写明投影 provider。
没有删掉开局后的角色和暂停地图后置验证。

本 worktree 环境显式补齐 MCP 2.0.0、pywin32 312、图像依赖；之前的缺依赖、无效 pipe 参数与多余 capability
分别保留为 `capture-preflight-r1/r2/r3` 的 no-launch RED。`capture-preflight-r4/preflight.json` 现为
`READY_FOR_BOUNDED_LIVE_ATTEMPT`：五个实际 DLL 字符串齐全、唯一 Robert bookmark、四项正式 MCP 工具可列出，
tasklist 与 Toolhelp32 均为 0 个 CK3 进程。该状态仍不证明实际开局、可用镜头或任何 AI 因果。
