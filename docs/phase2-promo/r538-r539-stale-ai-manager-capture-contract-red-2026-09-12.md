# R538/R539 旧 AI 经理捕获合同 RED 与玩家经理改线

日期：2026-09-12（Asia/Shanghai）

## 实机结果

旧轮次 R538 完成 Frontend 预热并终止后，旧轮次 R539 作为唯一 gameplay
实例通过 loader、exact-build native、paused seed、feature manifest 与 FFmpeg
门。它完整通过前两段：`phase2_fact_quota_calibration` 的真实榜单开关和
`phase2_receipt_appeal_pip` 的 `zg361b2.40` option 1、同案 `state 1 -> 2`
以及结果榜单都为 GREEN。

第三段在任何经理动作前停止。请求的旧 seed owner/subject 是
`32904/29037`，AI-owned provider 返回
`status=unavailable / unavailable_reason=owner_filter_mismatch`。该 provider
按合同不泄露实际 owner/case，所以本轮没有猜测另一名 owner、没有放宽过滤器，
也没有重试或延长运行。R539 cleanup 为 GREEN；R538、R539、FFmpeg 与 injector
均已终止。未完成的原始 take 保留为 RED，不计入 P2，因此 P2 仍为 `0/8`。

关键 artifact：

| Artifact | SHA-256 |
|---|---|
| capture plan | `A504F3F05556D4F181868CEF8F789E69337A81E621BA2F9EB635C81F9E057A47` |
| raw MKV（42,870,428 bytes） | `CE0ABC8785F158003AB1CD79F615468AEDED0A82658DB5158000543208E645EE` |
| timeline | `3A0360A7EE3C5C61B009D9B617A0E6F47BB6510DE59681C572B3EFD676115F7F` |
| B2 action | `45214853829B2C7517E8AA1BC605979737850DFF9EB6F4F97EB287F511DF0D37` |
| B2 result scoreboard | `0AF807F36865C03B3514428FF0AA1B2A8A0CE8FA272FC22013AEFEA50469C1A1` |
| manager RED | `162E10996979F9A95F19C45BD1B2DE374972826AE626EAEB44D0D6353E3414E4` |
| cleanup | `A516B19612CAB08088DA974E12595EECC9A53AB9C1B7FEDD73583C8E92710133` |
| final report | `98A23693CB00F450A4F1F2EC17D030771DD03421304ED906C68E6098202B47C9` |

## 根因

这是宣传捕获合同落后于现行产品路线，不是当前 mod 的 B1 产品故障，也不是
native 读取器把正确 owner 读错。旧 P2 编排仍调用
`run_phase2_ai_owned_case_gameplay_action_cell`，并从 9 月 4 日 seed 的 selector
身份要求一个 AI owner 后台完成 B1。其间产品已按玩家限定不变量停止 AI 年度
B1，并在 R480–R504 把 Stage 10 改为真实玩家经理路线：玩家经理完成 B1 公示，
产品调度 `.90`，直属上级作为 owner/root 打开玩家 subject 的 F/AK，最后到达
可见的 `zg361mg.120`。R504 已用同帧 manager-governance provider 证明 F
`state=5 / active=false`，P1 因而达到 `9/9 GREEN`。

R66 还修复过旧 B1 双角色持久字段碰撞；旧 seed 中残留的 `case_owner` 与 selector
不一致可以解释本次 `owner_filter_mismatch`，但现行玩家限定产品已经使“修复旧
AI case 后继续拍”本身成为错误方向。P2 必须复用已验收的玩家经理路线。

## 最小改线

- `run_zhongguo_phase2_capture_attempt.py` 新增独立
  `--manager-source-receipt` 输入，并把它传给正式 runner 的
  `--phase2-manager-source-receipt`。planner 在启动前校验 receipt、checkpoint 与
  当前 product projection 的 `source_tree_sha256`。
- 新的通用 validator 接受现有
  `zg361_stage10_player_publication_source_v7`。当前真实 receipt
  `B687CC04...FFBA` 绑定 checkpoint `50B713F2...C7E4`、玩家经理 `27181`、
  直属上级 `36354`、`date_raw=53155680`，其产品树
  `C428C42B...B5DC` 与当前 P2 projection 相同。
- 第三段在 clean span 前通过既有 managed checkpoint restore 恢复该 source，
  确认 event-free paused map，然后调用既有 `run_stage10_player_subject`。不扩展
  冻结的四项 source-checkpoint registry。
- action 新增默认不改变原行为的 `acknowledge_terminal` 参数；宣传调用传
  `False`，在 F 终态由 provider 验证并保存后保留 `.120` 供 clean hold。统一
  finalizer 在镜头结束后负责确认该单选项并清空 surface。ACK 仍不作为业务
  后置条件。
- 经理镜头、review plan 与 checklist 均改为玩家经理/直属上级 F-case 语义；
  旧 AI-owned provider 仍保留给其已有诊断和其他已证明的合同，不再是这段宣传
  片的入口。

## 聚焦验证与边界

receipt validator 已直接接受上述真实 v7 receipt 与 65,244,992-byte checkpoint。
聚焦 normal 测试覆盖 receipt 字节/产品树绑定、Stage 10 终态保留、经理 source
restore、旧 AI action 不被调用、planner 参数传递和既有 promo plumbing；共
`51 tests` GREEN。Python compile 与 `git diff --check` GREEN。没有为这项
Python/文档改线启动 CK3、重建 DLL 或扩大为全仓测试。

该工作包改变正式捕获 CLI 和 producer context 的数据合同，根仓提交后必须同步
open_kaishek 兼容说明。它不改变 mod 游戏文件、native DLL、Operator MCP 1.1
版本或 wire schema。下一次只创建一个新 capture attempt；若第三段再次 RED，
保留首个失败并停止，不为单段开启永久长跑。
