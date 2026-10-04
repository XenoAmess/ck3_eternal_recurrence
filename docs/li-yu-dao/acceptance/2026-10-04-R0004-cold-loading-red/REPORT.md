# 礼与道 R0004：冷加载失败，未进入正式流程

本轮结论为 **NATIVE_LOADING_RED**。实际冻结提交 `01b4dda39505929c1245de699e67862f4130a02e`，产品树 `a86935a77eb31d70e7c95ba5ae564e0fb66f3d9a`；CK3 1.20.0.3 / build 25652598。两套[官方 L0 CI](ci/README.md)已成功，但实际冷加载出现产品与夹具错误，不能据静态成功给实机通过。

实际加载输入为 34 个生产文件、7 个普通入口夹具文件和 7 个 I2 输入夹具文件，逐项匹配[原 PREPARED 哈希](inputs/PREPARED.json)。生产 [manifest](inputs/production.manifest.json) 与两份夹具渲染报告原样保存；I2 使用实际加载的 candidate-001，后来的修复候选未混入。

## 实际报错

[退出后的 error.log](logs/post-exit/error.log)共 **63 个 `[E]` header**、13926 bytes，SHA `f043185cac5a5c71bab312c3795d5178c3efa07f368b97e30bd6d553bc725454`。分层详情在[分类账](error-classification.json)，计数不把 game.log 复本再加一次，不把重复实例当独立根因。

| 层次 | 实际条目 | 判定 |
| --- | ---: | --- |
| 产品 unknown trigger | 4 | `has_same_core_doctrines` 两条及 `divergence…` 两条，来自生产 consent trigger；产品冷加载 RED |
| I2 夹具 unknown trigger | 1 | 夹具里的 `has_same_core_doctrines` 未被引擎识别 |
| I2 夹具 create_character 验证 | 4 | 两个定义同时指定 employer/location：各一条 Script system error 和 PostValidate；没有 NPC 实际创建信用 |
| 产品变量 used-never-set | 10 | 五个 c3 变量各记录两轮；native E，未豁免 |
| 产品变量 set-never-used | 14 | c2/c3 原生使用检查，单独保留 |
| I2 夹具变量 set-never-used | 30 | r4 输入/观察变量，单独保留 |

产品 unknown trigger 是生产定义在实际引擎加载时被拒绝，不归入夹具豁免。夹具 employer/location 是定义 PostValidate 失败，不能说 setup 已运行。变量使用条目发生于原生脚本使用检查；它们没有证明实际操作中出现 unset/退款等结果，也没有证据允许忽略。后续修复须另绑新输入，本轮原件不改写。

## 执行与界限

[实际 launch](run/launch.json)启动 PID 19184/create_time 1791105678.3486943，窗口 HWND 2295626。没有进入 campaign，没有 native attach 或 MCP 游戏调用，没有鼠标/键盘输入。普通 Robert 身份、正式 I2 议案/同意/取消/拒绝/落实、D+1、D+30、保存重载全部 **NOT_RUN**；不得沿用 R3 的实际角色 ID。

`loaded-lobby.png` 是原始命名，[实际画面](screens/loaded-lobby.png)中 Steam 处于前景并遮挡 CK3；[元数据](run/loaded-lobby.json)同样记录 Steam foreground，不能证明大厅或加载完成。root 报告两次 SetForegroundWindow 都失败；本地未留独立原始命令 stdout/stderr，也没有成功 focus receipt，因此仅保留[实际 helper 源](source/helpers/r4_focus_capture.py)和此明确证据边界，不制造成功或失败执行回执。

启动前[新鲜 Steam 位移原图](offline/steam-moved.png)、[原 freshness receipt](offline/steam-frame-freshness.json)与[root 离线审阅](run/offline-reviewed.json)绑定同一 moved hash，实际标签为离线模式；它们不替代 CK3 加载完成证据。

[退出后实际设置文件](inputs/pdx_settings.txt)读到简中、windowed、1600x900、cloud_save=no；autosave=YEARLY，与请求 NEVER 不符。这里仅记录设置文件真实值，未取得 campaign 中的设置 UI 验收。

## 生命周期闭合

root 于 09:31:52 UTC [posted WM_CLOSE](run/normal-close-request.json)；该请求本身不算退出，随后 09:33:26 UTC [独立进程读回](run/normal-exit-processes-001.json)确认 CK3 列表为空、PID 19184 不存在。没有 process kill，未开 campaign，也没有存档/flush 信用。

[keeper FINAL](lifecycle/keeper-FINAL.raw.json) thread_exited=true，failure/entry_error=null，序列 2686；其中 screen_released=false 是 keeper 停止时的原值。[后续 CAS 2687](run/screen-release-completed.json)实际 resources=[]、done、dirty_entries=0。分配器[实际 completed-red 回执](run/allocator-completed-red.stdout.txt)绑定 R0004 / execution 84425881-d38d-4595-a106-9f08799633c2 / sequence 4，于 09:33:52 UTC 写入。

## 永久投影与省略

本包只逐字节复制必要源文件、原日志、回执、PNG 和 35 文件官方 CI 包；不裁图、不编辑原日志，不复制 DLL/EXE、ZIP、shadercache 或大量 keeper/poll journal。[全部外置索引](full-external-index.json)记录命名 R4 根中的每一个原文件及省略理由；全部原件保留在各自 external 原路径。根目录[JSON 报告](report.json)和 index 绑定投影原字节。本包生成未修改 checkout，未调用游戏、Steam 或 CI。
