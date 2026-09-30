# J-d11 增援：两个暂停时点的最小补采入口

状态：`OFFLINE_ENTRY_VERIFIED_LIVE_NOT_RUN`。本代理未启动 MCP/SDK/CK3、未占屏、未推进日期或获得新 UI。执行源固定为 `C:/w/jdcap0930` 的 `475bdbffd2c0fc96b4188c394eeea80a780b672a`，不得接收 master 内容。共享 capture 源和原生二进制不改，所有旧尝试保留。

默认 `desktop-gdi`。根已在独立骑士 run 直接审阅真实 CK3 GDI 原图；增援仍需自己的当前原始桌面、尺寸、焦点与完整战斗面板门禁。骑士 WGC 成功也不代替本 run 的桌面门禁。

## 实际入口与最小动作

1. 根使用单次 SDK 会话，依次 `operator_get_capabilities → operator_get_status → operator_preflight_job → operator_handoff_job`；验证 profile SHA、同机身份、排他进程及精确文件。
2. 复用冻结 a15 的 HWND/PID 焦点、原生相机居中、原图、mapper 和完整战斗面板门禁。布局 180 秒、两幅稳定原图和实际根审阅保留。
3. `before`：snapshot/control → 真实面板 PNG → 根审阅当前相对兵力条 hover 点 → 正式 mapper move → 战宽 tooltip 原图 → 根读回 → 再 snapshot。日期、revision、native_revision、snapshot_id 和暂停状态必须一致。两幅原图绑定同一暂停状态，不能称作 join hook 的瞬时画面。
4. 验证 Army 18 实际 `controllable=true` 且 `army_state=combat`，符合固定 executor 一天 horizon。独占写不可重试 intent，创建本次 recoverable checkpoint 并读回 control。BEGIN 绑定 Combat 16777218、Army 22，开启 join-width/full-entries。
5. 只提交一次 `ck3_execute_step(life-advance)`。即使 ACK 模糊或超时也不重发；只读检查实际 next-day paused actor/date/control，从 raw53146488 到 raw53146512。验证通过后尝试 FINISH，失败或缺回执独立保全，不阻止采集 `after` snapshot/control/真实面板与 tooltip 原图。
6. 两点实际原图取得后才评估 trace 完整性：phase status/failure_flags/实际 boundary，width 三个 boundary，full-entry 两个 boundary，日期/Combat/Army/token/checkpoint 与 detour 撤除分别报告。`PAUSED_PAIR_OBTAINED_TRACE_INCOMPLETE_UNREVIEWED` 只表示暂停材料取得，绝不表示 trace 闭合。最后核对同 owner finish、空 cleanup inventory 和实际 SDK job exit。

没有 600 秒录像或 FFmpeg。cache、regiment current、derived 各口径保存在原回复中；当前暂停后 control 不能冒充 join-return 瞬间。UI 数字必须实际抄读，不要求复现旧 A01 893/1603、827/4106。可见日历日期也实际读图，不能沿用未经读回的 dXX 日期推算。

## 12 项离线验证

报告：`C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-10-trace-after-ui-binding-offline/offline-verification.json`，SHA-256 `8679EA444F8F951117400EF43B6BF6650E56B6E3686A3DAE9EA1CD94E7729EB5`。

实际固定 source/lock/pair/checkpoint/a15 helper SHA、实际 CLI/help、operator profile loader、原生返回 schema、暂停漂移拒绝、唯一日期调用及缺离线审阅拒绝均通过。直接调用冻结 capture 的 `bind_a04_ui_target` 与 `validate_a04_ui_gui_source_binding`，正确 AppData d11 根通过，错误外置根/错误前缀/不同 state-output 父目录被拒绝，未创建目录或启动游戏。failed1040、缺 FINISH 回执及读到保存失败回执的三条离线流程夹具都确认继续收后帧一次，且不把 failed trace 标完整。夹具没有制造实际 UI。

旧 NOT_RUN profile04 永久保留，不再启动。先前推荐的外置证据目录 `C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-live-attempt-01` 不符合 A04 UI source-track gate，已纠正；旧代码已保存在 `reinforcement-attempt-09-trace-gap-implementation/prior-encoding-gdi-wgc-source/`。attempt-02/03/04/06/07/08/09/10 的原证据不覆盖。

open_kaishek 预验为 `not-applicable`：既有 parser/IR/finite-runtime/replay 语义不能证明 native callback/detour、原版一日 executor、paused revision 与 Win32 原图。当前 `Z:/workspace/open_kaishek` 不可用，commit/profile/version 如实 null；记录 exact exe/save/receipt/pair SHA，没有把未执行的引擎称作 GREEN。Python 流程检查单独保存。

## 当前正确区域编码

operator job 和 SDK server 都用 `-X utf8=0 -B`。SDK 显式给服务器子环境 `PYTHONUTF8=0`、`PYTHONIOENCODING=utf-8`，固定 operator 的 capture 子进程继承它。profile/adoption/generation/SDK receipt 记录实际命令及这两项覆写，不输出完整环境或凭据。解释器选项不进入 capture 的 `sys.argv`，没有改变冻结 admission intent。实际中文 Windows native process inventory 已用这些设置读回成功。

根于22:02 UTC再次查询最新正式 Release，仍 v0.2.1，wheel SHA `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`；prepare 再读实际主 venv Python3.14.7、安装 wheel 来源、版本与 null SOURCE overrides。新输入使用 `root-attempt-03/promo-release-and-interpreter-probe-a02.json`。

## 根后续命令

只有本次实际 Steam 离线 receipt 和当前 CAS 是待填输入。task必须仍属根当前 owner，不能仅凭曾经的 sequence3168 推断。三个新 attempt 路径均须不存在。

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -X utf8=0 -B C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/reinforcement/minimal-consumer/paused_join_pair.py prepare --offline-receipt <本次实际Steam离线审阅receipt路径> --latest-release-readback C:/Users/1/ck3-a04-mechanism-evidence-20261001/root-attempt-03/promo-release-and-interpreter-probe-a02.json --screen-task-id war-reinforcement-screen-20261001-a05 --screen-expected-sequence <当前CAS整数> --live-root C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-06-d11-paused-join-live-20261001-a01 --output-dir C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-09-live-profile --frame-backend desktop-gdi
```

唯一真实 SDK launch：

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -X utf8=0 -B C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/reinforcement/minimal-consumer/run_paused_join_sdk.py --profile-preparation C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-09-live-profile --evidence-dir C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-10-sdk --request-id jd11-paused-pair-20261001-attempt01-root --monitor-timeout 3900
```

封存 admission 的 900 秒 frontend/1200 秒 interactive/180 秒 recovery argv 保持原样。完成两点材料即 finish。prepare 只替换 admission 放行的 state/output/pipe/offline/CAS，再直接执行实际 A04 source-target 只读 gate；不修改原始 save/receipt/pair/DLL/native source。

## 真实画面回执

材料位于 `reinforcement-attempt-10-sdk/paused-pair-controller/`。按每个当前 `*-review-request.json` 直接审阅原图，写同名 `*-review.json`。schema沿用 `xar.jd11.a15.root-ui-review/v1`：stage、固定source_head、真实reviewer、timezone-aware observed_at（60秒以内）、root_actually_viewed、approved_for_current_action、当前expected_ck3_pid/expected_foreground_hwnd、精确frames identities、current_ui_region_reviewed和非空root_visible_evidence。未审阅不能写true。

| 阶段 | 额外实读字段 |
| --- | --- |
| 00-root-focus | 按请求列出的当前 HWND 和原图使用冻结 root_window_focus.py；实际 CLI 由 controller 输出。 |
| 01-pointer-move | 当前 observed_point、preview_content_rect、reviewed_safe_region；正式mapper两轴独立换算。 |
| 02-battle-panel | battle_panel_already_open；需要click时提供当前原始桌面点和内容矩形。 |
| 03-final-layout | camera_stable、full_battle_panel、date_actor_army_battle_readable、overlay_free。 |
| before-width-hover / after-width-hover | relative_soldiers_tooltip_target_reviewed，当前兵力比例条目标、图像内容矩形、审阅区域。 |
| before-readback / after-readback | full_battle_panel、date_actor_army_battle_readable、battle_width_tooltip_readable、this_battle_top_counts_readable、counts_sources_bound_to_this_battle；visible_values真实整数battle_width/player_soldiers/opponent_soldiers，root_visible_evidence记可见日历日期与角色/战争/军队/交战对象。 |

战宽 hover 目标来自原版 `window_combat.gui:646` 的 `CV_TT_RELATIVE_SOLDIERS`，中文文本带 GetCombatWidthBreakdown；294/312 等对比条小字不能当战宽。

可显式选 `--frame-backend hwnd-wgc`，原始窗口 PNG 标为 `desktop_full_frame=false`、`mouse_coordinate_source_allowed=false`，记录当前PID/创建时间/HWND/窗口矩形及帧尺寸，永不称桌面全图。只允许实际根审阅的单次 Win32语义 foreground与原生居中；未打开完整面板不可点击，也不移动鼠标打开tooltip，缺战宽UI则如实记缺口。默认GDI不加载或要求外部WGC库。

任何日期请求一旦发出便不重发。native次日暂停验证失败时保全实际请求与RED并同owner清理；trace失败独立记录，已验证次日的原图继续保全。两点UI取得、trace采样完整性、成片1×审阅和签核是不同事实，不相互替代。
