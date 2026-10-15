# 公共验收入口的官方 GUI 后备路径

`tools/ck3_mod_acceptance_gui.py` 供公共 `ck3_mod_acceptance.py` 的六个 phase 调用 `dispatch(args)`。全局 shared manifest 明确 `execution_mode="gui_only"` 才走此路径，旧 native 路由不变。它解决真实游戏升级后既有 native DLL 无法匹配的窄缺口，不迁移宗教 AI，不修改或复制旧 DLL。

本轮来源是 [More Tenets Slots 用户反馈整改](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/4193b2b/docs/bugfix-report-2026-10-15.md)与本机 CK3 1.20.1：当前 EXE 与旧 1.20.0.4 runtime 绑定不同。历史 LYD 0.1.2 缓存场曾在公共 native 启动前被 hash 门禁拒绝，随后仅以普通启动验证缓存加载；那份菜单结果不授业务资格。永久来源见 [LYD缓存回执](release-changelogs/li-yu-dao/0.1.2-evidence/cache-acceptance.json)。MTS 产品源码、业务夹具及本轮具体证据留独立仓；公共后备入口、租约、进程与证据边界供其他 mod 复用，因此归框架。

## 配置合同

公共 main 增加 `--gui-review`，其他参数沿用 `mode/runtime/products/product/case/case_inputs/prepare_output/prepared_case/run_context`。`dispatch` 返回普通字典；阻塞使用 `ValueError`，由公共 main 记录实际失败。`run` 的 `RED` 和 `verify.case_acceptance_pass!=true` 必须返回非零，不能因没有抛异常而当作通过。

runtime 保留 `schema="ck3-mod-acceptance-runtime-v1"`、`manifest` 精确 pin 和 `python/repo_root/game_dir/userdir_root/artifacts_root` 配置路径。manifest 使用原 `ck3-mod-acceptance-shared-runtime-v1`，要求 `execution_mode="gui_only"`、`game.version/exe_sha256`，不能携带非空 `native`。运行时只执行 actual game EXE；产品不能提供 host/source/native/engine/host_args/execution_mode。

runtime 的 `allocation` 必须明确提供：

```json
{
  "lease_repo": "<committed-clean-owner-checkout>",
  "lease_module": {"path": "<reviewed-screen_bus_lease.py>", "bytes": 0, "sha256": "<actual-sha>"},
  "task_bus": {"path": "<reviewed-source-cli>", "bytes": 0, "sha256": "<actual-sha>"},
  "bus_dir": "<installed-bus-root>",
  "state_root": "<live-run-id-state-root>",
  "task_prefix": "<short-screen-task-prefix>"
}
```

路径来自机器配置，不在实现中固化操作者路径。`lease_module` 消费独立已核验文件，现有仓库实现位于 `promo/ck3_native_war_ai/integration/screen_bus_lease.py`；不向生产 import path 注入旧 promo package，也不声称最新 `xar-promo` wheel 含该文件。实际复用其 `ScreenLeaseKeeper`、`checked_cli_pair`、`checked_owner`、`call_bus` 与 `checkout_head`。source CLI 与 `bus_dir/bin/codex_task_bus.py` 必须是不同路径且同 SHA。

product 只声明 `runtime_mod_key`、`external_mod` 与 cases。每个 case 明确 `id`、`budgets.timeout/quit_timeout/poll_interval/max_prepare_bytes` 和非空 `required_business_evidence` 键列表。timeout/quit_timeout/字节预算均为正有限值，poll 为0.1至5秒。产品源仓可通过输入 `source_repo` 冻结 clean HEAD，框架源码与 lease checkout 始终冻结。

`case_inputs` 至少含：

- `staging`：产品正式构建目录。
- `formal_manifest`：精确 pin，文件列表接受 `{path,size或bytes,sha256}` 或按相对路径索引的相同信息；逐文件匹配正式 staging。
- `settings`：普通 `pdx_settings.txt` 的精确 pin，必须含实际 CK3 `"language"={...value="..."}` 块。
- `mcp_fallback_evidence`：可读取并匹配 SHA 的非空证据 pins，说明实际 MCP/native 缺口。
- 可选 `plain_configuration`：原四份普通配置 pins，提供时复用 `materialize_product_profile()`；只有 settings 时复用相同 `checked_copy` 与外层 descriptor 投影逻辑，不人为要求三份无业务作用的旧文件。
- 可选 `warm_cache`：明确的 shadercache 输入目录。只复制至新 profile 的 `shadercache`，不授缓存命中或性能资格。
- 可选 `source_repo`：产品 clean 源仓目录。
- 可选 `debug_mode`：literal boolean，默认false；true才添加原生游戏 `-debug_mode`，供console fixture、文本存档等验收动作使用，不授native bridge资格。
- 可选 `save`：明确存档的精确pin，复制到隔离 `save games` 并计入准备预算；由操作者经官方菜单加载，可在同场切换新局和旧档，工具不自动读档。

先按通用存储策略取得本轮容量准入。模块另外核准备输入字节预算与当前可用空间；它不是通用容量预约器，不替代 Root 的容量预约/存储闭账。

## 六个阶段

`plan` 只显示选定 runtime、预算与业务键。`prepare` 先核游戏和源码，再逐文件核正式产物，在配置的 userdir 根下创建唯一 profile；独立 mod 副本、外层 descriptor 与 `dlc_load.json` 只启用该产品。语言写为 `l_simp_chinese`，原 settings 不改；其他语言不新开实机场。准备结果永远 `NOT_RUN/business_pass=false`。

`allocate` 检查本机 CK3 为0、总线无 screen owner、源码 clean、准备输入未消费，使用现有 `ck3_live_run_id.allocate_live_run_id()` 分配本机本mod唯一编号，并在总线注册唯一 screen task。注册后至 run 之间必须在600秒内完成离线审阅；这段期间尚未启动 keeper，不能无限等待或用普通 heartbeat恢复过期租约。

`--gui-review` 指向 Root 直接审阅后的 JSON，要求 `run_id`、`runtime_manifest`、`reviewer`、`reviewed_at_utc`、`direct_image_review=true`、`steam_offline_confirmed=true`、`frame` pin、`image` pin。复用 `check_fresh_frame` 检查实际窗口位移、像素、时间、尺寸与来源，随后核 Steam PID 仍存在。工具不从旧图或进程存在推导离线。

`run` 在同一进程保留 ScreenLeaseKeeper 与原始 CK3 Popen，复用 `exclusive_launch_lock`，CreateProcess 前再次核 CK3 为0及新鲜 CAS；使用独立 userdir，只有输入明确要求才开启 debug mode，无 native注入。Root 继续通过官方游戏UI执行用例与正常 Quit；模块不自动点击。运行期间每5秒核被冻结源码，180秒按既有 CAS keeper续租。原始 Popen.wait返回后记录实际退出码，停止 keeper后按最后 sequence精确释放 screen。

run目录的 `STOP`、timeout、源码或租约故障只请求原 PID 可见顶层窗口 `WM_CLOSE`，记录 `window-close-request.json`；这种退出即使返回0也不能获得 process/normal/business通过。quit预算后仍活着则写 `ROOT_STOP_REQUIRED.json`，继续保留原句柄及正常情况下的keeper直到操作者关闭；不强杀、不丢失原句柄、不伪造清场。

`verify` 将实际原进程退出、keeper/CAS闭合和 GUI业务分别输出。没有 `business-review.json` 时业务只为未完成。review必须明确实际 `run_id/case/reviewer/direct_image_review=true/passed=true`；`facts` 为每个 required业务键提供 `passed=true` 与可读取、SHA匹配的 `evidence` pins；另要求 `normal_gui_quit=true` 与非空 `normal_quit_evidence`。字段齐全但 Root 未明示通过不会授PASS。STOP/窗口关闭、退出码0、静态/准备/截图存在均不替代业务验收。此阶段始终 `product_release_pass=false/native_capability_pass=false`。

## 验证边界

`tools/test_ck3_mod_acceptance_gui.py` 只做离线回归：正式字节与实际游戏身份拒绝、隔离简中准备和 warm输入、禁止native、有限预算、真实无害Python子进程的原始 wait与模拟STOP关闭，以及业务/正常Quit证据缺失拒绝。它不启动CK3、接触桌面或Steam、领取总线、不授本轮实机通过。正式实机仍须由 Root 从公共入口执行和记录。

2026-10-15 首次验证：上述8项通过（0.595s）；公共路由2项通过（0.005s），验证默认native路由保持和GUI的RED返回非零；既有公共入口22项通过（0.993s）。这三个定向检查没有运行CK3，GUI实机仍为NOT_RUN。执行命令分别为 `python -B -X utf8 -m unittest test_ck3_mod_acceptance_gui -v`（最初8项）、`python -B -X utf8 -m unittest test_ck3_mod_acceptance_gui.PublicRoutingTests -v` 和 `python -B -X utf8 test_ck3_mod_acceptance.py`，工作目录为 `tools/`。

2026-10-15实际执行配置Python的 `-B -X utf8 -m unittest test_ck3_mod_acceptance_gui -v`（工作目录 `tools`），8项全部通过，unittest耗时0.595秒，进程退出0。该次包含显式旧档复制；STOP测试的窗口请求被mock，只有两个无害Python子进程真实创建和wait。没有游戏或实机业务通过信用。
