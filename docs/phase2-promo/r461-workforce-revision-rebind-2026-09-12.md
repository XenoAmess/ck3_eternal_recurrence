# R461 Workforce owner 查询 revision 重绑

## 实机 RED

- exact build：CK3 `1.19.0.6`，`ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 当前轮次 R461，bridge PID `122896`，connection generation `1`。
- 输入存档 SHA-256：
  `93745B2FE52AD31D7878D22BD1AB7898D3D09AA97AFB2BEAC1C009FC17964527`。
- 产品树 SHA-256：
  `84443728419E390024936809778C98D4BF4B529747FF776DE0F2FD4DC97E58CE`。
- RED：`native gameplay step failed: ZhongGuo workforce owner revision is stale`。
- 冻结证据：
  `Z:\ck3_mod_rewrite\_runtime\p1-stage10-stage11-r460-r461-20260912-attempt02\live-artifacts\terminal-stages-red.json`。

## 根因与调用链

Stage 9 的 `.390` 摘要已确认并关闭。Stage 11 的自然推进第一次执行
owner-view Workforce terminal probe 时，调用链为：

`zg361_phase2_terminal_stages_action_cell.observe_workforce`
→ `BridgeService.query_zhongguo_workforce_owner_snapshot_v1`
→ `NativeDriver.execute_step`
→ native bridge `query-zhongguo-workforce-owner-snapshot-v1`。

`resume-map` 已提交，但 Python 仍短暂读到上一个 paused public snapshot；native
主线程处理只读查询前，游戏帧已推进，因而 exact-build revision 门正确拒绝旧帧。
失败帧保留了 `resume-map` 后紧接 stale query、再由异常收尾 `pause-map` 的命令历史。
这是 snapshot 到只读 query 之间的时序竞争；没有证据表明 Workforce 产品状态损坏。

## 最小合同补丁

只在 Stage 11 owner-view 只读 probe 内识别四种已定义的 paused binding/revision
瞬态错误。命中后记录旧 revision、日期和错误，返回调用方让既有 production
entry 立即取得新 snapshot；不提交游戏输入、不重启 CK3。连续四次仍不能取得稳定
绑定时保持 RED，避免把系统性故障拖成长跑。其他 bridge、schema、DLL、游戏文件和
产品脚本均不变。

验证范围只覆盖 `test_zg361_phase2_terminal_stages_action_cell.py` 的正常与 `-O`
双模式。修复后按 Python 合同热恢复规则，在当前轮次 R461 原位 retry。
