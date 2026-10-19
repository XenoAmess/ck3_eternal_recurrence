# C7录像镜头：已调度，所见实际回执失败

用户怀疑有实际依据。已有小回执证明本场镜头worker确实启用、能识别热点并排队，但本审计所见最近实际结果持续是`failed / camera_retry_cooldown / unavailable`；原生`camera_postcondition_verified`及`coverage_verified`均false，没有镜头成功应用或视口跟随的证据。不能拿`scheduled`当作镜头已移动，也不能仅凭实现代码写“已生效”。

`machine_id: xenoamess-full-tower-eb9d2c1186`；本次身份及读取时间`2026-10-19T09:17:09.103494Z`，来源`tools.ck3_live_run_id.current_machine_id()`；实际源码8e1e59f0。全部路径、字节、SHA和范围保存在[独立小回执](evidence/c7-camera-actual-outcome-audit-2026-10-19.json)。只读既有closed JSON，无Game、MCP、桌面、Driver/SAVE或录制视频读取。

| 已封观察 | 调度与热点 | 最近实际结果 |
| --- | --- | --- |
| AUTO3057/3059/3103 | scheduled1234/1235/1256；热点是war_objective，Lanciano2604 | latest_actual1233/1234/1255全部failed/camera_retry_cooldown；native84/84/88 unavailable、zoom=-1、camera后验/coverage=false |
| runtime交付的30cycle3864–3924 | 30原AUTO hash核对；22条保留camera摘要、均scheduled且识别war_objective2604 | 22个最近实际观察均failed，同native104 unavailable，无camera/coverage通过；其余8条army-strengths小投影无camera字段，按unknown |
| 更晚封存AUTO4100 | scheduled1738；已识别battle、army33554800、province2604 | latest_actual1737仍failed/camera_retry_cooldown，native106 unavailable，camera/coverage=false |

这里30cycle是runtime交付的最新现成closed compact，不是声称4100之前绝对最新30轮。8条`query-army-strengths-v1`结果只保留`status/selected_step/plan/result/result_location`，递归也未见camera字段。M4对实际src06的独立源审已确认：`bridge/army_strengths_mcp_result.py:86–104`构造小summary时显式省去`camera_follow`，此前Service已经schedule；因此缺字段不证明worker关闭或没有尝试，更不能补猜其成功。

调度是异步的：当前schedule ACK与`latest_actual`属于不同request，原字段也明示`same_frame_with_gameplay_claim=False`。上表准确结论是“这些观察到的最近已完成实际请求失败”，并非把每条当前排队请求都冒称已完成失败。Native不可用结果中的`[1787,2510,1787,2510]`是点/请求bounds，不能拿来证明实际viewport已经居中或覆盖全境。

无热点后的全境缩放在这些输入中没有合格实际样本：保留摘要的窗口都有war_objective或battle锚点，也没有对应quiet-overview成功/视口pair。是否因当前源码的战争/军队条件持续清空quiet计时、最小化/first-desktop门阻止提交，交M4独立源码审；本回执只证明最终未通过，不把一个可能的source原因硬当作本次原生cooldown的唯一原因。

runtime明确没有3059/3103同帧原图pair；Root此前审过的1773日原图不是相同战斗帧，本审计未复用它授viewport信用。没有解码active MKV、整段视频，也没有为审计补采图。当前所见证据足以纠正“镜头已自动生效”的说法；实际热点跟随与全境视口效果仍未验收。

小record复核期限`2027-04-17T09:17:09Z`，无大文件产物。
