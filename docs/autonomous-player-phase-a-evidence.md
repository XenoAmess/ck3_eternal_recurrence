# CK3 自主玩家 Phase A 实机证据

## 结论

Phase A 已于 2026-08-22 达到退出标准。提交
`11ab443050132341bb27f6f924d792772f397396` 的冻结候选，在同一准备环境下连续三次启动本机 CK3 1.19.0.6，
均以 production、非 debug、精确单项【琉焰卿的永恒轮回】到达可见主菜单，并在 supervisor 终止 CK3、完整进程树归零后
完成受保护存储复核。三次 `shutdown_attestation.ck3_exit_code` 均为 1，不证明游戏内 graceful exit。

这项结论的唯一 acceptance claim 是
`isolated_single_mod_visible_main_menu_only`。三次报告都写明 `valid_score_episode=false`；它们没有进入游戏规则页、
角色大厅或地图，不证明 Growth+100 已由大厅实际采用，也不构成玩法、策略或分数证据。

## 冻结指纹

| 项目 | 值 |
|---|---|
| agent/runtime 提交 | `11ab443050132341bb27f6f924d792772f397396` |
| 环境 SHA-256 | `4a02303bea47dd23dd70d3577618031e075dfd4e4d5d94df713cb37e5d78e0ab` |
| 规则 profile SHA-256 | `6cca52869f5bc32de1b509dd63255f8847875134933e936f97125ebc6be092f7` |
| production tree SHA-256 | `82079c205f7af1d2651a2cc2fad673c7b8f316b7bef43026cedd4ef6dbed7e1a` |
| 游戏版本 | `1.19.0.6` |
| 规则 | 原版 81 个声明默认 setting + `xar_on` + `xar_inherit_100` + `xar_score_growth` |

## 连续三次运行

| 次序 | run ID | 结果 | 引擎诊断 |
|---:|---|---|---|
| 1 | `20260821T180045Z-a3c49b20` | GREEN | 非零；本 mod 命中为零 |
| 2 | `20260821T180248Z-7ad2dd83` | GREEN | 非零；本 mod 命中为零 |
| 3 | `20260821T180531Z-9c6bb34b` | GREEN | 非零；本 mod 命中为零 |

证据包保存在本机 `%LOCALAPPDATA%\XarAutoplayer\runs\<run-id>\`，不提交个人路径、Steam 元数据、截图和约 2 MB
保护快照到仓库。每包包含 `environment.json`、`production.manifest.json`、带 SHA-256 链的 `events.jsonl`、最终
`report.json`、压缩的 protected before/after 快照，以及主菜单、OCR、fresh 引擎诊断等 artifacts。

三份报告已由 `xar_autoplayer.runtime.validate_smoke_report()` 重新读取并计算事件逐项摘要、previous link、最终 tail 与
report 绑定的一致性。该无密钥 hash chain 不是数字签名，也不能防止拥有写权限的人重写整条链。随后又逐项断言：

- `finalized=true`、`ok=true`，且环境指纹完全相同；
- CK3 命令行无 debug 参数，视觉证据为两帧稳定【新游戏】；
- enabled inventory 精确为 `mod/xar_autoplayer.mod`，唯一隔离 mod mount 指向 production tree，未知 mount 为零；
- fresh 日志只有一个 session marker，并在退出后再次解析得到同一结果；
- Job 成员从 1 归零，双源最终 CK3 inventory 为空，认证 watchdog 与所有控制文件消失，`cleanup_proven=true`；
- production tree 未变；真实 profile 与 Steam userdata 的受保护语义回到 baseline，并连续稳定 5 秒；Workshop descriptor
  内容哈希和已注册目标树的路径/大小/mtime 元数据在退出后一次快照中等于 baseline；
- `engine_diagnostics.current_mod_diagnostics=false`。

Phase A 的失败契约另有三类证据，不能错误归入上述三次成功 smoke：

- `20260821T175600Z-506fd491` 在 watchdog 父进程身份不匹配时于 CK3 创建前 RED；
- `20260821T175750Z-dcbdeff4` 在 suspended CK3 的 WMI 路径不可读时 fail closed，CK3 在 resume 前由固定句柄终止；
- 该冻结候选当时的测试套件共 33 项，32 通过、1 项默认跳过。其中原生 Windows 测试覆盖 suspended→Job→resume、`TerminateJobObject`
  回收实际生成的进程树、真实 process handle 的 shutdown 合取、PID/nonce/WMI 歧义拒绝；默认跳过的 watchdog 父对象桌面集成
  用例已另行显式运行并 GREEN。

冻结 Phase A 证据产生时，尚未做“CK3 resume 后强制杀死 supervisor”的完整崩溃注入。此后 2026-08-22 已执行两次真实
`crash-smoke`，但均为 RED：第一次在 CK3 创建前识别出 venv interpreter redirector；第二次已进入可见主菜单并完成
post-resume 注入，却在 watchdog 与 Job teardown 竞态中安全地保留 unsafe marker，未获得 `cleanup_proven`。因此这两次只作为
故障发现证据，不能补写为 Phase A GREEN；Phase B 接入 gameplay policy 前仍须由新提交、新 profile 的 crash-smoke 取得完整 GREEN。
该后续门禁已由 runtime 实现提交 `98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26`、环境
`5e7fb63ef98a7fd802caa864b64c593053c68bfb5f1798321cde6b02d6cd0d5f` 的
`20260821T220127Z-crash-adc0ac63` 完成；它不回写、替换或扩大本页冻结三连的 Phase A claim。

## 非零诊断边界

三次报告均为 `clean_engine_boot_required=false` 且 `engine_diagnostics.zero_diagnostics=false`。本机 Steam Cloud 中已有一份
旧 PoD 存档；即使隔离 profile 无存档且 `cloud_save=no`，CK3 前端仍枚举其 meta。meta 中 17 个规则 key 与两张贴图引用和
fresh `error.log` 全部匹配。与此同时，引擎 enabled inventory 精确只有本 mod，其他 mount 均命中由已安装 `.dlc` descriptor
推导的白名单或唯一隔离 production tree。因此现有证据高置信地把这些诊断归因于旧云档元数据，而不是隐藏加载了第二个 mod。

这个判断尚未用 ProcMon/ETW 建立因果 I/O 轨迹，所以不得把三次 GREEN 称为“零错误”或“干净引擎启动”。

## 下一门槛

Phase B 必须在同一合法性边界内新增纯视觉规则页、大厅、地图 HUD 和通用模态窗口分类；策略进程只能收到截图/OCR/模板等
玩家可见白名单字段。第一条可计分证据至少还需要：视觉确认 Growth+100、正常 UI 新开局、完成契约与首轮交易、在同一时间线
游玩至自然死亡，并读取玩家可见结算。任何工程日志进入策略、未知窗口盲点、回档重掷或环境漂移都使该局无效。
