# Episode 04 R182：行军抵达与县边 P 原生回值（CK3 1.20.0.4）

本记录只归纳外置 R182 原始响应与闭场证据。执行机器 `machine_id: desktop-3fevhd2-1c74096080`；场次 `desktop-3fevhd2-1c74096080--vanilla--R0182`，原生 episode `native-31254-8e3d88fb82cc`、进程 PID 14392、connection generation 1。2026-10-16 04:37–05:48 UTC 的准备、运行与闭场回执均标有该机器 ID。此场从 R181 的普通 checkpoint 接续，**不是新的 1066 开局或 ABC T0**。实际角色 full ID 31254；罗贝尔来源意图、正常存档和 2048 字节头部的 `1.20.0.4`／“公爵罗贝尔”字面值由 `runtime-actor-identity.actual-a01.json` 串起，但未解码出历史 ID 1128 到运行时 31254 的直接字段。

环境读回为 Steam CK3 `1.20.0.4 (Crozier)`、enabled mods 空；EXE `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101,040,248 bytes，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。04:40:54 UTC 的生产构建资格回执绑定 runtime source `6e17d0d4ca39719af41f40fb619c3da92472981a`、native build source `2e6291c798d852c9058c9956dd44cccff72d65d5`，二者 `ck3_autonomous_player/native_bridge` 差异为空；实际运行前有同机新鲜 Steam 离线画面审阅。出处为本场 `prepared-a01/environment-manifest.json`、`production-build-qualification.actual-a25.json`、`steam-offline-reviewed.actual-a25.json`，不外推到其他机器。

## 县边原生结果

Army18、actor31254、mode1、`army_1d4_raw=0` 的同次原生 preview 给出如下有限结果。这里的 P 是 `2C09DF0(actor, County)`；三个阶段依次对应 source P、target P 首次、target P 第二次。`available` 的最终 false 不是调用失败，也不等于已发生县损耗。

| 日期 raw / 实际 first edge | 共同门及 P 阶段 | 原生最终结果 |
| --- | --- | --- |
| 53147712，2644→2637（请求终点2637） | definition byte 均1、县对象不同、target CoDa；source P **1次 true**，target P 首次 **1次 false**，第二次未调用 | `native_condition_passes=false`；短路发生在 target P 首次，未进入邻接 Q |
| 53147712，2644→2636 | 县对象相同；三个 P 阶段均未调用 | false；不能据此解释 P 内部 |
| 53147712，请求2635的 first edge 2644→2645 | 县对象相同；三个 P 阶段均未调用 | false；远端2635不是此次谓词的 target County |
| 53147928，2635→2634（请求终点2634） | definition byte 均1、县对象不同、target CoDa；source P **1次 true**，target P 首次 **1次 false**，第二次未调用 | `native_condition_passes=false`；同样未进入邻接 Q |

两条不同县边在本场把 R181 的未知合取项收窄到**目标 P 首次返回 false**；这只说明该两次调用的实际返回，不证明其内部为何 false，也不证明其他县边全为 false。2635 的路线预览为 `[2645,2635]`，不能把请求的远端终点当作 first edge。

## 行军、原片和数值边界

05:04 UTC 对 `move-army-18-to-2637` 的一次提交返回 `native DLL does not implement gameplay step`；05:10 的后验仍是 date53147712、Army18 位于2644、无移动目标，故该失败尝试没有行军或损耗资格。随后对已支持的 `move-army-18-to-2635` 提交被接受，回读路线 `[2645,2635]`。自然逐日推进到 date53147928 的 d09 原生快照中，Army18 在2635、移动目标为空、路线空、状态 `sieging`；05:37 的正常存档再次绑定该位置。这证明**正常抵达**，不把动作 ACK 当抵达证据。

05:14–05:18 UTC 录下的 `raw-r182-a01/raw.mkv` 为 180.000 秒、2560×1440、30 fps、H.264 单视频流，无音轨，228,543,290 bytes，SHA-256 `cc17504348085bc3bb5c02655a31b424bd6406f6106707c15d29a2a651e5b0fe`，录制进程正常结束。离线抽帧显示约171–178秒有自然日期变化，其中 **174–177秒仅是可剪辑候选**；0–170秒大部分暂停，片内至179秒尚未显示抵达。未逐帧认证连续 clean span，未获人工 1×／最终片签核；后续原生到达读数不能倒填成片内画面。抽帧和边界见 `review-r182-a01/review-report.md` 及其 `frame-manifest.json`。

Army18 原生 full strength 查询在起点与到达后均为 **1184/1195 士兵**，current supply raw 均为 `30000000/100000`，current attrition fraction raw 从 `0/100000` 到 `1000/100000`。两个端点的士兵净数相同；没有逐次物理扣兵正证据，不能把预览中的 loaded loss 参数或 attrition fraction 当作实际扣兵。2637 预览的当前/目标省份补给上限为5875/4562，目标 native resupply eligible=false；到达后2635→2634预览为9880/5292，目标 eligible=true。这些是预览供给输入，不是实际补给流入回执。军事 GUI 树可读（547 widgets），但 type635 的两个候选 leaf `widgets[220]`、`widgets[238]` 均为 `status=unavailable`、`candidate_memory_unreadable`，`native_receiver_selected=false`、无变量索引和条目；没有点击或实际补员资格。

## 闭场与精确来源

05:48:26 UTC 的 `r182-close-a01/CLOSED.actual.json` 记正常 UI 退出、进程 exit 0、屏幕租约释放和原片保留；`NORMAL-SAVE.actual.json` 记 date53147928 的 checkpoint，73,446,058 bytes、SHA-256 `af291da7e2af3b8b0870dc3aa21291b55452a78e08a241994ba6358411c7c96b`。闭场明确 `raw_clean_spans_certified=false`、`human_video_signoff=false`，不新增 R04/R05/R06 资格。原片与存档仍为待复核对象，按项目过程素材永久保留规则保存。

以下路径均相对外置根 `C:/ck3-e04-resume-20261015-a01/live12004-refill-receiver-a23-a01/`；响应前缀 `desktop-3fevhd2-1c74096080--vanilla--R0182/responses/`。SHA-256 固定本次读取的精确证据字节。

| 证据 | SHA-256 |
| --- | --- |
| `r182-county2637-a27-03-preview.json` | `15b3d1a8d3a65fcf9cf3ba9626b9d0684cef5a07ba7d277fc2ada252fefabb7a` |
| `r182-county2634-from2635-a59-03-preview.json` | `4da9acbb5106e978170c4b34cbfa533e64c8eea6f13f557bc857db8a725db9d1` |
| `r182-arrival-d09-a56-d01-s0-final.json` | `ac0cbf36607bb875cefeeb0f7a40881e305694700d87f564f5db8c50d5b62a0c` |
| `r182-postarrival2635-a60-03-strengths.json` | `3a632e6ae3fc62616fa4f1ed8c66001693f72ac2cb529838d3a05a626a3f7330` |
| `review-r182-a01/review-report.md` | `e96dc494169d7af6cf671e0c61cd4cea6e83a3535db12c4a66d5d54b00743655` |
| `r182-close-a01/CLOSED.actual.json` 中固定的原片 | `cc17504348085bc3bb5c02655a31b424bd6406f6106707c15d29a2a651e5b0fe` |

其余直接回执：`film-move-2635.actual-a49.json`、`type635-refill-projection.actual-a30.json`、`r182-media-probe.actual-a54.json`、`r182-close-a01/NORMAL-SAVE.actual.json`。这些仍是同一机器本场事实，未执行新的 SDK、CK3 或桌面操作。
