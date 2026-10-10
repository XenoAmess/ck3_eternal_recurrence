# Holder / resolve 阶段公共诊断

2026-10-10 接入 `li-yu-dao / holder-stage-diagnostic`，用于收窄 R47 空事务对照后仍未知的继承缓存变化原因。R49已完成实际诊断捕获、公共run0/verify0及正常闭场；仍观察到45→40，诊断无正式 I3b、C3、I4 或产品通过信用。[实际结果](acceptance/2026-10-10-r0049-holder-diagnostic/REPORT.md)。以下分时记录保持当时状态。

## 输入和动作

公共入口绑定同一 Source08 runtime、现有只读继承缓存/事件查询与正常退出能力。产品输入为合法 R34 D2a 未授封存档、原 71 文件正式产品、四份配置及独立六文件开发 overlay；不改原 `transaction-only-control` case。

六件 overlay 由已入库的 `mod_li_yu_dao/tools/build_factory_diagnostic.py` 生成。沿用其必填 `--source-root`、`--source-head`、`--export-report`、`--export-report-sha256`、`--output`，新增组合 `--control full --heir-log-probe --stop-after-holder`。新模式明确标注实际生成器；旧默认 full 和 transaction-only 输出保持。不得手改生成结果。

同一 D2b 事件内依次记录事务容器创建前、创建后、holder 赋值后、resolve 后的 `every_title_heir` scopes，原 create/change-holder/resolve 的顺序和原子性保持；不新增中间事件 yield、缓存变量写入或日期推进。D2b 结束事件只保留身份/条件及无 effect 的停止选项，不继续 D3 SetHoF。

公共 adapter 先核当场 actor、暂停日期、事件与完整有序 45 人名单，只提交一次 option 1。随后取得真实完整后置名单，允许观察到 40、45 或其他实际数量；先执行唯一 SAVE，再用既有 reader 读取一次存档正文。保留 actor 完整 landed AST、七政治 Title 完整后置 AST/原 hash 对照、新 Title holder，以及原生与保存名单的实际差异。空事务专用完成变量允许 absent，不借用原空事务通过条件。

## 证据边界

四段脚本日志是 heir iterator scopes，**不是四个中间 actor cache 原生快照**。实际日志是否提供完整 ID 和稳定顺序尚未合格；getter 可能触发 lazy refresh。缓存旧值是否在非空授封事务中重新计算仍是待判别假设，不预写成已找到原因。日志缺失、截断或无完整身份保持 UNKNOWN；`diagnostic_capture_complete` 只表示前后原生与存档投影收齐。

正式 B4 仍保留完整 45 人、87/88 项保护要求。诊断即使顺利捕获变化，也不授正式 B4 PASS。正常退出继续由公共原句柄、native 和 cleanup 收据判定。

当前缓存 helper 的 key 包含完整 mod 字节及启用的外层 descriptor。新 overlay 恢复 holder 并改变终点，相对 R47 并非纯日志改动，因此旧 seed 不能按现 key 复用；不改写旧 key、seed 或原 attempt。下一场须明确处理这项输入成本，不能把缓存复制或源码测试当成实际命中或启动成功。

## 16:07 本机公共准备

公共 prepare 于 08:06:51 UTC、绑定 plan 于 08:07:04 UTC 实际 exit 0，blockers 为空。选用 Source08、合法 D2a seed、71 文件产品及统一生成的六件 overlay，未选 shader seed，未 allocate、preflight 或运行游戏。这里的 overlay 来自核验输入的纯生成结果，没有另行执行完整 CLI export。profile 到 Oct17 08:06:50 UTC 复核，原配额例外 Oct12 到期，不自动延长。[实际准备回执](../ck3-native-ai/acceptance/2026-10-10-holder-stage-public-source-only/PREPARE.actual.json)。

当前已发布 adapter/generator 在后继 `a22e0291e` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38036746599) 成功，终态更新时间 08:16:33 UTC。`1179a5313` 和 `532035269` 的原 Official 失败保留；其 Python-only 元数据问题由并发后继修复，不将源码检查或后继 CI 成功写为实机通过。

随后采用[公共 graphics footprint v2](../ck3-native-ai/graphics-cache-footprint-v2.md)，完整业务冻结保持，旧 seed/key 不改写。25 项 portable suite 成功；后继 Source09 与新的 v2 seed 仍待实际生产与预算，不把源码采用写成诊断实机已跑。

16:55追加：Source09 / 新 v2 seed 已实际生产，独立 case002 的公共 prepare、plan 与无现场context preflight 均 exit0；来源图形投影相同而完整业务digest不同，旧seed/key/期限不改。新4GiB峰值已登记且未闭账；下一步为当次新鲜Steam离线亲审和公共allocate/run，实机仍NOT_RUN。[精确准备记录](../ck3-native-ai/acceptance/2026-10-10-graphics-cache-footprint-v2/PREPARE.actual.json)。

## 验证

17:35追加：R0048 实际在启动证明合同处 RED，尚未执行 option / SAVE。adapter 的来源说明多放在外层，未满足 host 的 exact 字段集合；已改为内层 `proof`，以真实 R48 帧调用完整 host 校验函数的新两项回归通过，MAIN 全7项回归通过。原 host1/managed cleanup、keeper0、CAS4416、Steam离线亲审与预算关闭已记录；不授正常 GUI 退出或业务信用。case adapter 实际从 MAIN 独立冻结，不属于 Source09 index，修复后新 prepare 可复用现 runtime/v2seed，无需另建 Source10。[失败、修复与闭场](acceptance/2026-10-10-r0048-holder-startup-contract-red/REPORT.md)。

主树采用后，5 项 adapter 测试及 3 项新生成器 AST 测试实际 exit 0，已接入原官方 CI。检查覆盖改变名单仍唯一保存、过期/不完整查询拒绝、七 AST 差异及完成变量缺失保留、去掉四个日志块后事务完整 AST 相同、D2b 停止且不继续 D3、非法模式拒绝。[精简实际回执](../ck3-native-ai/acceptance/2026-10-10-holder-stage-public-source-only/VALIDATION.actual.json)。没有重跑旧业务矩阵或旧实机。
