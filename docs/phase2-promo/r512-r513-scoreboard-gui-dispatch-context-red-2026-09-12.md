# R512/R513 scoreboard GUI dispatch-context RED

## 结论

R513 已实机证明 R511 的 transport discriminator 修复有效：同一条
`query-zhongguo-scoreboard-state-v1` 请求被 native mailbox 接受，并绑定在
`native revision=3 / public revision=4 / date_raw=53147016 / player=29037 /
paused=true`。随后 provider 返回 typed `unavailable`，原因是
`gui_root_unavailable`。这不是记分板业务失败，也没有任何游戏输入发生。

根因已经收敛到一个真实 native 实现错误。只读 state resolver 沿 GUI 全局链取得
第三个对象后，又取 `third+0x3D0` 的 owner-lookup host 和其 `+0x08` owner；它把
owner-lookup host 误作为 GUI dispatch context 返回。后续 modal receiver 读取因此在
错误对象上访问 `+0x290/+0x29C`。同版本 action dispatcher 已明确从第三个 GUI 链对象
读取 modal vector，并通过 `third+0x3D0 -> +0x08` 单独解析 top-level owner。

不采用延时或长时间重试。R513 在 loader 303 callbacks、In Game、HUD、paused world、
player binding 和 request transport 全部 GREEN 后才查询；继续读取同一错误地址不会增加
证据。最小修复只让 state resolver 同时保留正确的第三链对象和 owner，不改公开 schema、
capability 名、变量 allowlist、widget allowlist 或动作语义。

## 轮次与证据

- 旧轮次 R512：Frontend warm-up，PID `51356`，结束后进程树归零。
- 当前轮次 R513：`-loadsave=autosave`，PID `210220`，唯一 CK3 实例。
- source commit：`54b305940604493aa392a42e9da48104faf6c58d`。
- bridge DLL：`16CBA80CFF2AAF07FC644A27B012C0D9947812C47440B9CB47731C873630451D`。
- driver state：`_runtime/p2-capture-r512-r519-54b3059-20260912/capture_native_state/native-session/driver-state.json`，
  `38190` bytes，SHA-256 `EDCB5600EAFFC6135C2BF42F5869488CBBAA0E86AF7EF80E7CD55E5CDAEA144E`。
- outer report：`4370670` bytes，SHA-256
  `CF6A34BC2B2CBB333097F88634AA74951457D26A1FECD10FBB84EBA91BE9C2C9`。
- cleanup：`30900` bytes，SHA-256
  `000A8B8E4C5F1F0C72DDC7EBDE1D988C41E0084918D4F786791C838C1E285614`，GREEN。
- 失败 take：`3603145` bytes，SHA-256
  `E82B3DE7E4C9AE1A33750714FA34BA1ACFC7521D19D55CC02CBF7E609C13AA5B`；
  clean span `0/8`，保留为失败证据，不进入剪辑。

R512/R513 均已终止，CK3 实例数为 `0`。R513 是
`CAPABILITY_RED / business NOT_EVALUATED / harness GREEN / lifecycle GREEN`；
P2 raw capture 保持 `0/8`，首段继续 PENDING。

## 最小施工与验收

1. 在 native-mode focused fixture 中明确构造两个不同对象：第三 GUI 链对象持有
   `+0x290/+0x29C` modal vector，`third+0x3D0` host 只持有 `+0x08` owner。
2. 修正 resolver，让 context 返回第三链对象，owner 仍按既有 owner 链解析。
3. 只运行 scoreboard state focused native target 和相关 Python choreography 测试；
   不扩大到全量 L0。
4. 构建新 DLL 后，下一次 CK3 使用新轮次；只有 paused live query 真正 available，
   才关闭本 RED 并继续八段录制。

公开协议没有变化，open_kaishek 只需记录上游 native conformance 修复，不需要 schema 升级。

## 源码修复结果

`ResolveGuiContextAndOwner` 现在把第三 GUI 链对象保存在 `context`，同时用独立的
`owner_lookup_host` 完成 `third+0x3D0 -> host+0x08 -> owner`。focused native
fixture 把三者放在不同地址，明确断言 context 不能等于 owner host。

- `xar_ck3_zhongguo_scoreboard_state_v1_test.exe`：GREEN。
- `tools.test_zhongguo_phase2_event_choreography_runner`：normal `15/15` GREEN；
  optimized `15/15` GREEN。
- ABI JSON parse 与 `git diff --check`：GREEN。
- CK3：未启动，当前轮次仍为 R513，实例数 `0`。

R513 RED 在新 DLL 完成一次真实 paused available query 前仍保持 current blocker；
源码修复通过不能冒充 live capability closure。
