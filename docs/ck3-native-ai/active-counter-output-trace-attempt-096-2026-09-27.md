# 现役反制输出追踪 096：真实调用命中，顺序/线程门拒收

本页接续 [094/095](active-counter-output-trace-attempts-094-095-2026-09-27.md)，只约束 CK3 1.19.0.6、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 和第 11 日冻结存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`。096 实验 DLL SHA-256 `2B3FCE167EADB8EF51F676EF8CE55CADFB2C5B0009EF4DAD4D4756604B859ED1`。原始目录为 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-096`，不覆盖前两次素材。

Steam 客户端显示“离线模式”；本轮独立桌面截图 SHA-256 `6B51D920FE8842106B95B1300898F2F0080DA662AE4651A56ADD9C4CCFA5C408`。截图中的任务栏时钟滞后，故此回执仅证明窗口移动为实时、Steam 离线标签可见，不声称任务栏时钟实时。受管 CK3 会话从相同冻结存档进入地图暂停日，`c096-trace-begin` 接受了 `capture_runtime_counter_output=true`、候选增援 Army 22 与 join width/full-entry 两个选项；一次 life advance 将原生日 `53146488` 推到 `53146512`，phase day 7 推到 8。完整原始 `c096-trace-finish.json` SHA-256 `709DCF9F2A8A04F30AC23A30C3F998526C6B676FE1808D1A960115DA1251EAEF`，只读摘录 SHA-256 `D3AFDCACDB4F1ADFB8A30B3BA572F06D3796FBA33967F9E1A5FC9B823B940EAB`。

反制输出钩子全局命中 12 次，其中 2 次经侧方指针归属到目标战斗，说明 095 的空输出不是“钩子没运行”。这 2 次均通过 caller 和兵团 header 身份门；首个失败码为 `3`，即原实现合并的 committed boundary、side-index 次序或 owner-thread 检查。`count=0, pair_complete=false, sides=[]`；仍**不能把空列表读作反制向量数值为零**。本次 `failure_flags=1048576` 仅含反制输出门，七个边界和双侧身份序列均通过；反制后攻击 `7163402981/1455075113`、伤亡前出伤 `116118762/67660992`（均 Q100000）仍为原生局部观测。完整 `trace` 返回 `trace_unavailable`，不可提升为整场胜率续算输入，也没有完成增援、骑士和动态 entry 的全程对拍。

同一原始 trace 独立捕获了 Army 22 的**真实增援瞬间**：join full-entry `count=2, first_failure_code=0`，进入前 side 0 的 `army_ids=[16777221,16777231,27]`、entry 27 条；进入后追加 22、entry 40 条，新增兵团 13 个。join width 的三个边界也完整：进入前 base/final `1645/1480`，进入后 `2467/2220`，下一 phase day 的出伤宽度参数实为 `2220`。战斗方缓存兵力原始 Q100000 值由 `160317482` 变成 `410690163`。这些是增援和宽度变化的原生实测，**并不自动验证增援后的整日出伤、伤亡或最终胜负**；全局反制门仍 RED。

本轮 `knight_selects=[]` 只表示这个有界窗口没有捕获到对应的骑士选择事件，不能推断战斗中没有骑士，也不能把骑士身份或后续伤病转移视作已验证。

096 已受管退出：`cleanup-check.json` SHA-256 `136FAA65BA09A91614F22BB3EBD464BA7211CC549E8F36EF81E569EACFF7F044` 记录 CK3 进程树清空、job 活进程归零。下一轮独立 DLL 将保留旧码 `3` 的兼容读取，并细分新诊断码：`31` 为 committed boundary 不等于六、`32` 为目标侧方输出次序不符、`33` 为当前线程不是 plan owner；这是拒收原因，不是战斗结果。只有精确读出该原因并修正对应采样合同、得到两侧原生 class 向量且与同帧兵团 census 和真实日界核对，才可考虑接入智能体。修正前的现役整场胜率仍可按已核实的日伤害做近似行动比较，但不得将本轮反制 class 读数充作已校准的概率依据。
