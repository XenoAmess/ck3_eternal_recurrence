# R197 原生 P 响应与 OR 边界

machine_id: `desktop-3fevhd2-1c74096080`；run：`desktop-3fevhd2-1c74096080--vanilla--R0197`。独立只读审查时间 `2026-10-17T05:30:44Z`；响应记录时间 `2026-10-17T05:23:38.068287+00:00`，游戏 date_raw=`53148192`。

原件：`D:/workspace/ck3_native_war_ai_promo_work/e04-r197-county-refill-a01/desktop-3fevhd2-1c74096080--vanilla--R0197/responses/r197-p-preview-once-a01.json`，32,815 B，SHA `522f42fccef31657eb07016d43d58259adbe93beda18ea0678af4e7421615263`；已独立重算吻合。

响应没有 source_head、PID、process creation/FT。其 `body.queried_connection_generation=1`，episode=`native-31254-534b7fc4f2ab`，snapshot=`native:3`，revision=4/native_revision=3；`request_identity` 仅绑定原请求文件。不得凭此响应独立宣称 PID/FT 已验。

source 桥：同 scene 的 `allocated-context.actual-a01.json`，4,126 B，SHA `8c5e37473b87c6564a24066815ece9994f35808360db3cda5813cb1d4363ca9f`。其中 source/runtime/native HEAD 均为 `85eb547cca4fddaec4b8a89ec9dd203e6935299c`，源为 R0191。此为小型分配上下文来源，不能代替实际运行身份回执。

令 P=`body.route_preview.county_entry_condition_v1.predicate_trace_v1.stages`，L=`P[i].relation_inputs_v1`：

| 字段 | source P，i=0 | target P first，i=1 |
| --- | --- | --- |
| receiver_full_id / actor_full_id | 34960 / 31254 | 34232 / 31254 |
| sampled_relation_full_war_id | 4 | -1 |
| auxiliary_identity | null | null |
| selected War / raw +358 | 非空 native identity / 0 | 两者 null |
| sampled_direct_war_matches_aux / gate | true / true | null / false |
| L.returned 与 P[i].returned | true / true | false / false |

两 L 都为 available、call_count=1，线程/参数/身份稳定均为 true；整数及布尔字段类型实际吻合。`actual_bridge_caller_return_rva=6616941` 是 bridge 相对位置，不能当作原生 P caller。第三阶段 count=0，其原生返回为 null。最终 county condition=false；route 本身 available。`actual_loss_observed=false`、`neighbor_Q_observed=false`，没有县损耗正例。

当前 typed consumer 把实际 AL 与纯 direct-War 采样分开；两叶 `unknown_or_inputs=true`。目标 war=-1 只证明纯 direct 分支 false，不能把未观察的各 OR 调用填 false。source direct sample=true 也不能单凭预读推称实际 OR 从未调用。

未来 OR leaf 应新增可选、严格版本化合同；当前 relation 精确 key 集不接受任意附加字段。仅保存自然调用的实际次数、参数/线程/阶段身份与真实返回，不额外调用 callee。只有完整原生观测覆盖才能区分未调用与采集失败；未调用/未知返回均保持 null 并附不同原因。OR 采集失败不抹去独立合格的原 relation AL；矛盾保留原值并报告 unavailable，不制造子调用返回。本次未运行 interpreter、矩阵、Driver、SDK，未改源码或当前会话。
