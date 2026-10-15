# 战争窗口优先规划的无用复制（2026-10-15）

普通规划器选定窗口优先计划后，不再执行本轮 faction、construction、council、M5 等普通消费者。旧实现仍为它们构造私有 snapshot/history，并在 Driver 的受锁规划视图返回后重新挂回完整 history。窗口分支随后提前返回，`plan_turn()` 又对整个结果执行 `deepcopy`，复制了本轮不消费的历史与世界投影。

本次仅在 `window_priority` 已确定时、受锁视图返回前移除这些 `_private_*` 消费输入，保留窗口优先标记供既有分支判断。公开计划、来源帧、摄像机输入、冷却记账以及原提交路径不变；普通非窗口分支仍获得原有历史视图。修复没有关闭任何领域能力，也不删 Driver 历史或改变窗口查询、关闭资格、ACK/实际关闭验证及重放规则。

## 实际归因

N40 P02 的实际 `0006-1-result.json`：actor 31254、date_raw 53233368、Native revision 3、public revision 2、generation 2，选择 `query-war-results-window-v1`，原请求 `war-overview-query-52e2b1344a1e417b99fa62c71d0c89b3`。结果为真实隐藏窗口，未尝试 dispatch，不能称为本场可见窗口关闭验收。

同场 `ordinary-stage-timings.jsonl` 用 Windows share 7 只读采样，未读取活跃 Driver 文件：

| 区间 | 实测 |
| --- | ---: |
| 整个 AUTO6 | 4.918398 s |
| `service.normal_plan_turn` | 4.703977 s |
| 其中 `_plan_turn_internal` | 2.244839 s |
| 其中 succession preparation | 0.570414 s |
| 规划返回后至完整响应结束的时间上界 | 0.212429 s |

`normal_plan_turn` 结束于 04:59:17.575139Z，完整响应结束于 04:59:17.787568Z。因此这次 4.918 s 主要发生在 SDK 规划，不能归因于 Native 战争窗口扫描。`_plan_turn_internal` 返回后还有约 2.454 s；源码显示这一段主要剩下最终 `deepcopy(planned)`，但没有该 copy 自己的计时，归因属于源码与阶段边界的推断。

succession 区间内另记录一次 full-state persistence 0.475951 s，包含 UTF-8 编码 0.041082 s、临时写入 0.422291 s、replace 0.010059 s；这些是嵌套阶段，不能与上表重复相加。该份日志没有窗口 Native 内部的扫描、名称读取、snapshot 或 mailbox 独立计时。0.212429 s 也包含提交前回调、transport、校验及 MCP/队列返回，不能当作扫描时间或 10 ms 验收。

原始来源位于 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation40-cold-prep/`；外置候选及回执在同获准根的 `war-window-plan-copy-fix01/`。运行叶精确基于 `sdk-p02/src/xar_autoplayer/bridge/service.py` SHA-256 `6021a872d5d6e7d1dd3bd74ef8b57f6de6061cac213684238547c8f83fe26350`。永久源码只应用对应小 hunk，没有用外置运行叶覆盖开发树其他改动。

## 定向验证和边界

`test_service_window_priority_copy.py` 的七个 portable 场景使用完整合成 frame/history，运行真实 Service 与 NativeDriver 受锁规划视图方法。覆盖查询、关闭意图及无动作 pending，内部视图与兼容 fallback，证明来源帧和决策保留、不复制无用 payload、不改变受保护历史、不提交新动作；另验证普通消费者仍收到其四域历史视图。

外置五项检查另使用实际 AUTO6 的计划/来源帧，以及四份不可变 P13 的完整 Native declarable results（各 728 行）。公开输出一致，历史行/result 身份及内容未变。该小型历史样本的三个配对运行中位数为旧版 8.817 ms、新版 0.353 ms；它不是活跃完整历史的重建，不能外推为本场全部规划的加速或实机验收。

```text
python -B -X utf8 -m pytest -q -p no:cacheprovider tests/unit/test_service_window_priority_copy.py
```

本包没有改 Native DLL，也没有重启 Game 或录制。开局 LIFE-first 及部分 M5 提前返回有相似的私有输入保留形状，但有各自仍需消费的字段，未在本包更改，也没有给出它们的实机复制耗时。完整 MCP 改善和长期每游戏日吞吐仍由后续同局 SDK 温替换后的实际回执证明。
