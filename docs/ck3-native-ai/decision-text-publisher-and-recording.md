# 独立决策文本发布器与录制接口

新录制使用 `tools/g2_saved_campaign/decision_text_publisher.py` 的独立进程，再由 OBS 的 `text_gdiplus_v2` 读取文本。发布器不创建窗口，不操作游戏，也不连接 OBS。正文标题固定为“智能体实时决策”；进程、来源和游戏身份写入隐藏的 `.binding.json` 与 JSON 回执。旧蓝窗的退役规则见 [退役说明](../../promo/ck3_faith_and_power/integration/legacy-decision-panel-retirement.md)。新发布器没有旧窗 PID、HWND 或旧 provider 身份的兼容入口。

配置 schema 为 `xar.ck3.decision-text-publisher/v1`，必须显式提供：

- `machine_id`、`session`、`state_root`、`decision_text_file`、`current_request_path`、`feed_root`。
- `qualification_only`：正式录制必须为 `false`。
- `game`：实际 PID、`creation_filetime`、`creation_date`、HWND、`desktop_id`。
- `game_launch_receipt`：实际启动回执的完整 `{path, bytes, sha256}`。

所有配置输出路径必须位于该 session。Root 在新的实际配置准备完毕后，可使用：

```text
python -B -X utf8 tools/g2_saved_campaign/decision_text_publisher.py --owner --config <actual-config.json> --binding <actual-session>/ROOT-DECISION-TEXT-PUBLISHER-BINDING.json
```

owner 保留 publisher 原始 `Popen` 句柄，读取实际 PID、创建时间与可执行文件，再核对孩子自己写出的 `STARTED.json`。Windows venv 的 `sys.executable` 可能是产生另一 PID 的启动器，因此 owner 使用当前进程真实 kernel image 的可执行文件启动仅依赖标准库与固定纯格式器的 worker。回执同时保留请求的 `sys.executable` 和实际 engine 路径。已有启动 intent 而结果未知时拒绝再启动。

Root 正常停止时，只创建该配置 `state_root/STOP`。owner 等待孩子的正常退出，并封 `OWNER-CLOSED.json`；不会调用 kill 或 terminate。孩子自己的 `CLOSED.json` 不冒称它已观察到自身 kernel exit。

## 预提交与结果发布

真实 `GameplayBridgeService.before_submit` 回调先封原计划与 relay，再调用：

```python
ack = decision_text_publisher.wait_text_published(
    actual_plan_path,
    publisher_started_pin,  # 完整 {path, bytes, sha256}，不是 Path
    timeout_seconds=5,
)
```

发布器验证实际持有的 `CURRENT` 请求、序号、选定步骤、游戏 PID 与出生日期，读回来源精确 pin，写出文本后才发 `TEXT_PUBLISHED`。调用方必须等这个 ACK 才能从实际预提交回调返回；超时不放行业务。手动维护 cue 必须显式声明不是 AUTO 或 Service 回调，也没有提交业务。

`TEXT_PUBLISHED` 证明该进程实际发布了绑定来源的文本文件，`OBS_draw_ack` 始终为 `false`。它不证明 OBS 已画出文字。结果显示通过同一 API 显式提交有实际来源、当前请求与序号绑定的 compact relay；不会自动扫描整个回执目录，也不会为显示结果重读大型 Native payload。ACK 只对 compact projection 的发布负责。

`ROOT-DECISION-TEXT-PUBLISHER-BINDING.json` 使用 `xar.ck3.decision-text-publisher-binding/v1`，包含 `machine_id`、`publisher_started` 完整 pin、`publisher_sources` 中 publisher/view 两个完整 pin，以及 `OBS_draw_ack=false`。由 `PublisherOwner.seal_binding` 在实际 STARTED 后 create-only 生成。

## OBS 与首帧门禁

`tools/ck3_obs_capture.py` 的新 provider schema 为 `xar.ck3.obs-window-capture.v3`，新组合模式为 `game_decision_text`。`launch_recording` 接收实际 `placement_receipt` 与 `decision_publisher_receipt`；后者指真实 publisher 的 `STARTED.json`。旧 `overlay_receipt` 被拒绝。新 take/job 及 OBS 启动前均检查精确旧蓝窗类，包括隐藏窗口；发现旧窗时留给原 owner 正常关闭，不启动新录制。

`decision_text_admission.verify_segment` 保留连续录制、同 Game 出生代、来源进程、录制存活、存储准入、时间与输出根目录的检查。人工首帧 schema 为 `xar.ck3.decision-text-first-frame/v1`，要求 Root 真正审阅冻结的 game/scene PNG、`decision_text_visible=true`、旧蓝窗不可见，以及明确 `stage=frontend` 或 `saved_map`。发布 ACK 不能替代这些像素证据。

新开局 owner 还须保留更严格的 MainMenu 守卫：`frontend_screen=main_menu`、实际菜单与文本像素审阅、录制早于前端操作、此前前端动作数为零、`map_ready_claimed=false`，并显式校验两种 session 字段与实际录制一致。通用首帧门禁不自动授予新开局资格。

自动续段使用独立 `automatic_text_continuity` 分支，核真实新 source、非黑冻结图像和 game/scene 差异；它不声称人工审图或精确文字 draw ACK。`recording_recovery_adapter.py --decision-text-publisher` 只恢复已验证 AUTO 后的 `RecordingPaused`：正常清理旧 OBS、真实 publisher、实际新首帧、零 RPC attach/resume，再结算原 AUTO 一次。未知启动 intent 不重试。混合业务故障的 `--attach-only` 新分支尚未准入，当前明确拒绝。

## 验证边界

静态 CI 运行 `test_decision_text*.py` 与旧窗退役测试，并设置 `XAR_DECISION_TEXT_PORTABLE_ONLY=1`，只使用替代 OS/OBS 边界，不调用实际 EnumWindows，也不要求真实子进程。独立 Windows 子进程测试留作本机证据，CI 明确跳过。便携测试覆盖当前请求与文本 ACK 的守卫、源错配拒绝、合成 PNG 连续性，以及门禁与恢复顺序。`qualification_only=true` 的软件夹具不能通过正式录制门禁。

2026-10-18，本地源码与普通 Python 子进程资格在 `machine_id: xenoamess-full-tower-eb9d2c1186` 核实；03:09:07Z 的 `TEXT-PUBLISHER-SOURCE-QUALIFIED02.json` 记录 venv owner 实际 engine、publisher 173656 / creation FILETIME 134367665464322381、文本 ACK 与正常原句柄 exit0，SHA-256 为 `ae6eb075f984edde7c34471fb440c6bc4faa87f58e182ab30de02433eccdb919`。这是来源机器当时的软件资格；新场次仍需实际依赖、容量、OBS source、首帧和前端操作门禁，不代表已完成新录制实机验收。

早期 `47aa9bcce8811a2b248417a5b7848ffff7662b1bc04df0520340d95394ac62f6` 在 base Python 下真实通过，但 Host05 使用 venv 时发现启动器与 worker 的 PID 不同，门禁正确拒绝。失败 child 已正常 STOP；因原 owner 异常退出后原 Popen 句柄丢失，闭场证据诚实记录为随后取得的 exact-FT 句柄观察，未追认原句柄退出。新源码 `e969030afa11d3f59109bb075f82b1b69ac295bc5d8ae7ca4f994a1301a492f7` 才补齐实际 engine 启动资格。旧失败、COW01 与交付01均保留。

此前共 87 项相关本地测试通过；修正后以正确 venv 解释器复验了 15 项新测试与 8 项退役测试。扩跑旧 OBS 测试的第一次尝试曾因夹具漏 mock 新增门禁而发生一次只读 EnumWindows，发现当前旧蓝窗；没有桌面输入或状态变更。该失败记录保留，夹具修正后的 56 项 OBS 测试才是无实际桌面访问的通过结果。不能将全部历史测试表述为“零 desktop”。具体回执与来源见 [源码资格记录](decision-text-publisher-source-evidence-2026-10-18.json)。
