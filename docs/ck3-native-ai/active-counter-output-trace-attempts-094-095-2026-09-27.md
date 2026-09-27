# 现役反制输出实机追踪 094/095：门禁与空向量的边界

本研究只适用于 CK3 1.19.0.6、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，源第 11 日冻结存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`。实验 DLL SHA-256 `999305F817F3D871D88EB6607ED7407DB32A5320B848921B24087D83AA184A2F`。外置原始目录分别为 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-094`、`...-095`；历史原件不覆盖或改写。

094 在同一暂停日得到 battle-control，但 `capture_session.py` 的 Python 私有请求白名单没有转发新加的 `capture_runtime_counter_output` 字段。`c094-trace-begin` 在驱动层返回 `Private phase trace request fields differ from the bounded contract`，**未安装钩子、未推进游戏日期**。随后 `c8b4066c9` 加入显式 bool 转发与拒绝 finish/非 bool 的测试，9 项热服务合同测试通过。094 按受管 finish 退出，清场成功；不能把它当作原生反制实测。

095 使用该修正后的采集器，从原始存档另开会话。独立移动截图 SHA-256 `76EF652170B84387946D13C6EAF8939117C208BD35964E135B4468CB1380F463` 已目视确认 Steam 左下“离线模式”，桌面时钟 `17:53` 与 UTC+8 对齐，窗口位置恢复。原始 `c095-trace-begin` SHA-256 `ACA0295F894F6F76E3F008A0D49CD099A52A881D061594BD98BC1F2FCAF2EC31` 接受新 opt-in；`c095-life-advance` SHA-256 `2F4C7373AB21376C89DB26CDD91FEF6D2478FF0B0A32254A71D5EFA42F8B3C69` 将日期由 `53146488` 推至 `53146512`，第 11 日主战 day 7 变第 12 日 day 8。前后 battle-control 的原始 SHA 分别为 `9BC8A02FC01C741D540A8C6C10C0C2FD1CF37B4F5272D650CDF25B3AB9897B79` 与 `E4869E45BE1C8304CDF2DA8248D041623911BF90DD64E03078741BD85FA2D6D7`，两次均返回 `active_counter_inputs_v1.status=available`，但这只是各自暂停帧的 operand census。

原始 `c095-trace-finish` SHA-256 `3AA706DEF991530A415EF124BB15A021592491EB751A4A0DD910A5C7E775F5E8` 返回 `trace_unavailable`，`failure_flags=1049616=1048576+1024+16`：新反制输出门、最终查询门和边界身份门都失败。新字段明确是 `requested=true, pair_complete=false, count=0, sides=[]`；**不能解释成反制向量全为零或原版没有使用反制**。同次原生局部数值仍捕获反制后攻击 `7163402981/1455075113` 与伤亡前出伤 `116118762/67660992`（均 Q100000），但其成对局部成功不解除完整追踪 RED。`16+1024` 的已知原因与 090 相同：Army 22 于当天加入 side 0，此次 begin 未把它预绑定，七边界后段无法通过身份检查。反制输出 `count=0` 另有独立根因，不能仅由增援解释；当前回包没有区分钩子未触发、未命中目标战斗或 native header 校验失败。

095 的 `readonly-summary.json` SHA-256 `CFFB45E460A547734F7635D1BC80D7122FB47BDB5EB109F63AC18FD43B3267AB` 由复制 094 的脚本生成，内部 `attempt` 数字误写 94；以目录、`c095-*` 原始请求/回包和本页 SHA 为准，不编辑原件以免抹去生成器错误。`cleanup-check.json` SHA-256 `E6C736C20DEA2E59927F2B2F52151FFF20AFCC0C30CBE74060A65EE32C368C8F` 证明 capture 返回 0、job 活进程最终 0、CK3 进程树清空。

下一次独立 attempt 的 begin 需同时传 `candidate_joining_army_id=22` 与 `capture_runtime_join_width=true`、`capture_runtime_join_full_entries=true`，并加默认关闭的钩子诊断：调用次数、命中目标战斗次数和首个失败门。只有诊断记录及双方 class 向量成对，且真实日界 entry、主参战者、context 与 088 同帧模型及增援后 census 交叉核验，才考虑从“被动诊断”升级为续算输入。现役整场胜率和游玩智能体的该缺域门禁维持未闭合。
