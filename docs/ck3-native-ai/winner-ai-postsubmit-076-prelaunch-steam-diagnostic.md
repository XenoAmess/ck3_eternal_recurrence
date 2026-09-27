# 076 终局后移动延长回放：Steam 启动前新鲜度 RED

截至 2026-09-27 01:15 UTC，076 **没有启动 CK3**，没有新增原生移动、ETA 或队列 apply 证据。078 已干净退出，076 的来源、旧 AI observer DLL、runner、任务总线及独立 074 基准均已离线冻结；阻点是无法独立确认当前 Steam 仍处于离线模式。此处的 RED 只判启动前门禁，不改变 072/074 已采集的原生战斗与 AI 字段。

外置原始材料保存在 `D:/workspace/ck3_native_war_ai_promo_work/episode01-winner-ai-postsubmit-extended-attempt-076/`，机器可读汇总为 `steam-prelaunch-diagnostic.json`。077/078 的采集器 RED 不被用于填充 076 的业务结果。

| 检查 | 原始观察 | 可推出的结论 |
| --- | --- | --- |
| 当前窗口身份 | Win32 HWND `198194`、`steamwebhelper.exe` PID `5820`，进程创建于 `2026-09-26T07:14:02.195467Z`；窗口可见、前台，原始矩形 `[0,0,962,768]`。 | 确有当前进程与窗口；不能由此推出其业务在线状态。 |
| 桌面截图 | 076 `steam-before.png` SHA-256 `2BB7A8CC1F556230AE57259845EB046C07D1F202D4CBDD42A97479DEDFE380C7` 与 074 对应图逐字节相同；移动 20 像素的 `steam-moved.png` SHA-256 `9E2E22DCCCB13B320ECA50BCD8CDFA30A824C6CF6AB61D08D7AEB8170A0B9ED3` 也与 074 对应图逐字节相同。图中显示的任务栏时钟停在 `4:06`，诊断时系统 `time /t` 为 `09:14`。 | 窗口边界变化证明桌面合成对窗口移动有响应，但相同像素和时钟异常不能证明 Steam 内容是当前帧；旧图中的“离线模式”不得重用为 076 门禁。 |
| UI Automation / Win32 文本 | `steam-live-inventory.json` 与 `steam-uia-inventory.json`：Steam HWND 只有顶层 Window 和四个空 Pane；无可读“离线模式”语义文本。 | 当前离线状态不能靠这条只读语义链确认。 |
| Steam 离线意图 | `steam-offline-intent.json`：当前 `steam.exe` PID `6288` 于 `2026-09-26T07:13:46Z` 启动；`steamui_login.txt:1233` 记 `Start offline - 1`，后面至 EOF 没有匹配的在线切换标记；`loginusers.vdf:8` 为 `WantsOfflineMode=1`。脚本只投影这几个字段，不导出账号数据。 | 同次启动与持久偏好均支持离线意图，但历史日志和配置不能单独签实时 UI 状态。 |
| 独立窗口采样 | `steam-printwindow-diagnostic/receipt.json`：`PrintWindow` 返回 1，但直接窗口位图全黑；桌面窗口区域也黑。 | 返回码并不等于取得可用状态画面。 |
| 可恢复重绘 | 一次缩小窗口未达到请求矩形，finally 恢复到原矩形；之后移动 37 像素并请求 `RedrawWindow` 返回 1，窗口再次恢复原矩形。新图显示黑窗口，任务栏时钟仍为 `4:06`。 | 产生新哈希不等于刷新 Steam 内容；不把黑窗口或像素差当成离线证据。 |
| 最后恢复探针 | `steam-restore-diagnostic/receipt.json`：最小化确实发生，随后恢复/置前，`DwmFlush` 返回 0；原矩形和可见性均恢复。前后桌面图 SHA-256 同为 `46AC6B166815DF44E7CEE04AD677E04953ED3D8C6FA18A1C9827BBF2D5BC18E1`，直接窗口图 SHA-256 仍为此前黑图的 `AA2FC528E59CA603ED1007386326EDBF127BF3783053BDAF73DD1A3331190D19`。 | 这次可恢复重建也未产生可读的当前 Steam UI，不能签“实时离线”。 |

因此 076 停在 **prelaunch RED**，不生成 `steam-offline-receipt.json`，不调用 `start.py`，不将尚未发生的回放写成 movement 阴性样本。`input-freeze-v2.json` 绑定当时最新 master `9d2cfd72b44f9bd78c237af8cf572901964f4d27`，并说明旧 `E8FB321D985880EC3079E2BBC9406663457C2F790445751CEDDDE522F0412ED6` DLL 是这条独立 AI replay 的冻结输入，不与 078 的战宽 observer 混用。实际重启准备时还需再 fetch/rebase 并重新冻结当时版本。

下一次必须在**独立新 attempt** 中取得当前 Steam HWND/PID/create time 绑定的、新生成且可见内容真正变化的原图或等价原生状态读回，人工确认其“离线模式”；仅凭文件时间、窗口位移、不同哈希或历史图片不通过。之后重新核完整 capture receipt、源档/EXE/DLL SHA、前次 CK3 clean exit、任务总线资源释放，再运行有限天回放。若仍无法确认实时离线状态，继续留在启动前 RED。不得为了打通门禁切换 Steam 在线模式或覆盖 076 原始材料。
