# Steam 桌面画面冻结时的离线状态证据边界（2026-09-27）

结论：本机现有只读证据**高度支持 Steam 以离线模式启动，却不足以严格证明检查瞬间仍处于离线模式**。因此不能用启动日志、`WantsOfflineMode`、无外部 socket 或 Steamworks 的连接状态替代实时 UI 门；076 已保持 prelaunch RED，未启动 CK3。此结论也适用于后续需要同一 Steam 门禁的受管 CK3 attempt。原始 076 图像冻结诊断见 [076 启动前记录](winner-ai-postsubmit-076-prelaunch-steam-diagnostic.md)。

外置只读研究目录为 `D:/workspace/ck3_native_war_ai_promo_work/steam-offline-runtime-proof-static-20260927/`。其中 `runtime-inventory.json` SHA-256 `708C48E5C7DA1F25F98C4FA0F84691D9B95D381D76276F037873C9BFF97E239D`，只含进程身份、socket 类别和日志文件元数据，不导出远端地址、账号或日志全文。`client-symbol-scan.json` SHA-256 `EF04A7977870D382BC75E26A7EE2C3A86E0DDCF0999062D887DA60A0C74E81F6`，`client-export-scan.json` SHA-256 `603C94A435032AEF12EC8C6A978460204D94A01487D88449C5DD0890510F86D1`，`offline-string-context.json` SHA-256 `0C09231B23CFCAF2E642BA70F2645A18779251A6B21553676D643FBF9795B940`。这里的脚本只读取本机文件和当前 OS 元数据，没有加载 DLL、调用私有接口、启动 CK3 或切换 Steam 模式。

| 观察 | 证据层 | 严格含义 |
| --- | --- | --- |
| 当前 `steam.exe` PID `6288` 创建于 `2026-09-26T07:13:46Z`；其 UI `steamwebhelper.exe` PID `5820` 创建于 `07:14:02Z`。 | 当前进程身份 | 可以把日志中的本次启动与仍存活的进程关联；进程存活不说明模式。 |
| `steamui_login.txt:1233` 于同次启动记 `Start offline - 1`，该文件此行后至 EOF 没有匹配的在线切换文本；`config/loginusers.vdf:8` 的 `WantsOfflineMode=1`。 | 启动记录、持久偏好 | 支持启动与用户意图；无法证明其他内部路径不会静默切模式，也无法证明日志是全量事件源。 |
| 2026-09-27 01:24 UTC 的 8 个 Steam 相关进程共 11 条 INET socket；4 条 `ESTABLISHED` 均为 loopback，没有观察到外部 `ESTABLISHED`。 | 瞬时 OS 网络快照 | 无连接可能发生在离线模式，也可能发生在在线模式网络故障、暂时断开或两次采样之间；不能据此确认模式。 |
| 本次 `steam.exe` 启动参数没有 `-offline` 或 `-offlinemode`；config 扫描只有上述 `WantsOfflineMode`。 | 启动参数、文件 | 没有发现更强的启动锁定；即使有参数也只能证明启动意图，不能代替运行时回读。 |
| Steamworks `ISteamUser::BLoggedOn()` 返回的是客户端对 Steam 服务器的**实时连接**，其 false 还可能由本机网络或 Steam 服务器故障造成；`ISteamFriends::GetPersonaState()` 是好友可见状态。 | 官方 API 语义 | 前者 true 可作为联网连接的反向警报，但 false 不证明离线模式；后者不能证明客户端模式。[ISteamUser 官方说明](https://partner.steamgames.com/doc/api/ISteamUser#BLoggedOn)、[ISteamFriends 官方说明](https://partner.steamgames.com/doc/api/ISteamFriends#GetPersonaState)。 |

本机 `steamclient64.dll` SHA-256 `CABA4826AA3501039D095AEE1843A6BFB270FB43A3AB4455B2D6733223579FEE`、`steamclient.dll` SHA-256 `E9E961C914A418B6A3C597822BDC920BDEA62C842FF42DE23DC306331DA563F8`。两者的名字表均有两处 `GetOfflineMode`，紧邻 `SetOfflineMode`；64 位 DLL 第一处位于文件偏移 `0x12F68C0`（RVA `0x12F82C0`），前 416 字节有 `IClientUtils` 标签，周围还有 `GetConnectedUniverse`、`GetServerRealTime` 等方法名。第二处位于文件偏移 `0x1305FD8`（RVA `0x13079D8`）。PE 各 41 个导出里没有 `GetOfflineMode` 或 `IClientUtils` 直接导出，仅有 `CreateInterface` 等工厂。**这是潜在原生运行时读口的静态候选，不是已确定的接口、ABI、返回值或安全调用。** Getter 与 Setter 相邻，错认方法槽位可能改变 Steam 模式；当前不调用它，也不把字符串当回执。

要建立独立于画面的严格替代门，至少需在精确 DLL SHA 下证明私有 getter 的接口注册、准确槽位与签名、只读调用路径和返回值与实际 Steam 模式的关系；还需能绑定当前进程、拒绝 IPC 失败或陈旧缓存、在 capture 前后读到一致状态，并用独立可信状态交叉验证。未满足这些条件前，`capture_session` 不增加替代门，不把上述间接证据组合成 `offline_verified=true`。即使未来实现，其 receipt 也应显式标为 `native-runtime-readback`、携带 DLL/进程/接口身份和前后原值；与 `visual-ui-readback` 分开，不伪称人工看到了实时 UI。当前可安全交付的只是 `runtime-offline-unverified` 诊断。
