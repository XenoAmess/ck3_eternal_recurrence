# M1：自然 quiet-realm 请求50失败定位（2026-10-19）

CLOSED / SOURCE_AND_CLOSED_OBSERVATION_ONLY。machine_id：`xenoamess-full-tower-eb9d2c1186`，本轮经 `tools/ck3_live_run_id.py machine` 实读；源码核pin时间 `2026-10-19T12:36:44.677145+00:00`。C12业务源 `d35b59325f48b981ddeca6db294f253e45cc9d48`。0Game/MCP查询、截图、活Driver/SAVE读取、构建、热改、矩阵。当前游戏正常推进，旧审计与共享源不改。

结论：实际realm请求到达Native相机写入阶段，随后未通过稳定后验。不是“没有触发”。`target_changed`却不能唯一归因用户/UI抢镜或几何算错：冻结Native29将四种失败合并为status7，现有摘要又未保留区分字段。尚无证据证明realm几何必败；本次没有获得实际全境视图验收。

## 唯一自然输入

runtime封闭投影 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/C12-QUIET5873-CAMERA-ONLY-86.json`，3,257B / SHA-256 `f26249ca4ff55790fbaba51bdb3527fbd8d5d9a9551200259806a162b0d34ad8`。本轮先核尺寸、SHA，再读内容。machine_id同当前机器；owner observed_at为 `2026-10-19T12:35:17.041980+00:00`。

owner先精确核原closed `runtime/p37-responses/5873-1-result.json` 为94,419B / `71d45db8c47ed8112d9e5a8fec825bcb657056374007e469b93a77a4a812bda6`。本轮未重读原响应或扫描runtime。

| 实际字段 | 值与绑定边界 |
| --- | --- |
| outer AUTO | 5873；life-advance-one-day；service executed；12:31:01.962039Z至12:31:04.653857Z |
| 新camera工作 | auto-camera-3fbe70355ce3-479；scheduled |
| 摘要中的旧完成工作 | auto-camera-3fbe70355ce3-478；failed/unavailable/camera_retry_cooldown |
| 旧工作带回的Native结果 | request_sequence50；target_changed；county_count9；zoom_index15；bounds[1787,2214,1982,2510]；native_elapsed_us46 |
| Native后验 | camera_postcondition_verified=false；coverage_verified=false |
| 478工作当前hotspot | war_objective；war16777269；province2633；b_messina/c_messina |
| outer planning frame | complete；native:931/revision581/Native931；date_raw53197968；actor40526；episode native-40526-1bec95182886；connection_generation2；Game15512 |

outer5873、camera479、旧工作478、Native50不是同一请求。Native50原提交rawdate、actor/epoch、intent、target/current、client_size、县ID没有落入摘要，保持unknown。outer planning frame不能补作Native50的提交帧或声称same-frame。status数值7是冻结enum与实际字符串的对应推导，原投影未独立序列化数值码。46微秒仅原提交阶段耗时，不是等待稳定或失败耗时。

## Native29的status7并不只有“目标被人改了”

冻结 `camera_presentation_v1.cpp::Advance` L164–181：主线程stamp、50ms节流和mailbox sequence检查后，只有同一已接纳request且camera指针/settle计时存在，才执行：

```cpp
std::array<float, 6> current{}, target{};
if (!Read(camera_, CurrentOffset, current) ||
    !Read(camera_, TargetOffset, target) ||
    !Finite(current) || target != result_.target) {
  settle_until_ms_ = 0;
  Publish(Status::target_changed);
  return false;
}
result_.current = current;
if (current == target) Publish(Status::settled);
else if (now > settle_until_ms_) Publish(Status::unavailable);
```

合并的四类为：读current失败、读target失败、current任一float非finite、实际target六float与原期望target不等。本次没有读成功标志、失败时current或实际target，四者均不能排除。`target != result_.target`是精确float比较；target含NaN也会不等。单纯current正在插值、尚未到target不会触发status7，正常继续等；五秒超时是status6。

失败return先于 `result_.current=current`。因此即使保留完整Result，status7的current仍是上次成功存入Result的值，可能只是提交时值；result.target始终为原期望目标，局部的失败时实际target没有发布。result.date_raw也是提交时Snapshot日期，不是失败时日期。不得把这些字段标成失败时双端读回。

status5 preempted是另一些分支：提交前有事件/交互，或写入前sequence变化。提交后游戏自身改变target可落入status7，但没有区分UI、其他相机逻辑、引擎约束/正规化或camera对象失效。只有状态名不能给这些候选排序，更不能认定是合法UI preemption。

## 本次可排除哪些提交阶段失败

该冻结源只有L177发布target_changed；新request在L189清空旧Result、camera和settle状态。由本次request50的county_count9、bounds、zoom15及status7，控制流支持：

1. 实际经过realm分支。hotspot不填county_count；query在取得bounds后退出，不建立settle状态。
2. 提交时map/alive、actor/date（不未来且不超过7日）、事件/交互、唯一owned HWND和非零client守卫通过。不据此外推提交后状态。
3. 旧subrealm reader返回9个县ID，其ComputeBounds/UnionBounds全部通过。Native29未采用新M1 ABI完整性组件；未输出县ID，不能声称包括所有封臣或realm精确只有9县，更不能与domain2直接比较。
4. camera解析、blocked位、transient X/Z、ViewportExtent、bucket表与terminator、zoom index范围、zoom/angle读取、finite和canonical化均通过。
5. L311–313要求canonical化保持X/Z中心；当场中心改变应报status27。因此“本次canonical化当场移动中心而被拒”不能解释status7。
6. L324–328的zoom index写入、六float目标写入、current读回helper返回成功；L329记录46微秒，L331建立最多五秒settle。Write是SEH保护的memcpy，不含写后重新读target比较，不能升级为最终应用验收。

所以不是县域bounds、geometry terminator、zoom索引或canonical中心守卫阶段直接拒绝，也不是没走realm写入。提交后目标被重新约束、其他相机逻辑改目标、settle读回异常均仍未知。几何不适合视觉覆盖也没有被这些守卫证明或排除。

bounds跨度X195/Z296；按冻结算法整数中心应为X1884/Z2362。这里只是源码可计算结果，**不是原请求target读回**。Python realm padding固定float .32，Native结合真实client aspect求extent，再查原生bucket/zoom/angle表。本摘要没有client_size、实际extent、bucket表、zoom距离/角度及原target，不能从bounds+index15重算实际视野，也不能断言太近/太远。

## 摘要裁剪与coverage语义

`NativeCameraPresentationClient.latest` L231–245原本组装actor/date、县ID、client_size、target/current等。随后 `LatestCameraFollowWorker._reference` L60–80仅保留status/request_sequence/county_count/zoom_index/bounds/两种后验/native_elapsed_us。5873就是schedule返回的这一有界旧工作引用。

关键已有值因public摘要设计被裁掉，不是本轮新查询失败。即使后续保留原值，也必须标清其提交/上次成功观察语义，仍不能冒充失败时观察target。本轮没有去活对象或Driver补读。

冻结Native29的coverage_verified从不写1，该false不能解释为已测得九县没覆盖；它与status7判定无关。camera_postcondition_verified仅settled且zoom index合法时真，本次false正确表示未验稳定。相机失败也不推翻outer AUTO业务executed。

## 处置与最小后继入口

本轮不改几何、不放宽比较、不强写、不重放request50。Service L817–839只匹配本Service记录的request_sequence，失败去重后进入30游戏日backoff；本次cooldown不是新realm提交。当前war_objective是静态目标，按policy不阻静默；本投影没有原quiet_since/intent，不能独立重验首次静默长度或认它为失败原因。旧审计“backoff期间已观测新活动却不清quiet锚”是独立缺口，不能解释本次写入后status7。

若下一正常源码维护需要可归因证据，最窄入口是复用现有相机通道，不增每cycle Game查询：

- SDK失败有界引用保留已有actor/date/client_size/target/current，并绑定原提交sequence/source frame与sample语义。完整16,384县ID不应每次塞AUTO；count加有界hash/单次小pin即可。这里只保存已存在值，不补semantic query。
- Native settle将read-current失败、read-target失败、current非finite、target实际不等分开，并记录此次读成功标志；若要判谁改变目标，还须保留期望target与实际观察target，不能覆写原目标冒充原ACK。当前Result布局没有观察target/差异字段：新增需版本化mailbox及ABI审查，不能偷塞当前布局或借用coverage位；不能混入冻结Native29。单独增加错误status可先分离读失败，但仍不能回答谁改目标。

这些是确凿诊断缺口的施工入口，不是已确认几何修复。只有后续自然观察能分开上述条件，才有证据选择合法preemption、引擎正规化或几何/对象生命周期修复。当前全境实际验收、Native30资格及业务信用均不增加。

## 冻结来源与闭场

N=`D:/codex-ck3-demos/2026-10-19-robert-v20261019-native29-camera01/source`；S=`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src11/xar_autoplayer/bridge`。本轮只读具名源码核SHA，未读DLL/OBJ/大依赖manifest：

| 源 | Bytes | SHA-256 |
| --- | ---: | --- |
| N/src/camera_presentation_v1.cpp | 15775 | 656055437114c216f8703197cc010f4443025969d16cece5fd63333bce3c6abf |
| N/include/xar_bridge/camera_presentation_v1.hpp | 3124 | 976491c0821a651fd6d38ff05427a5a6ed0810ae06776ecede16241348cbfc10 |
| N/include/xar_bridge/realm_camera_geometry_v1.hpp | 2180 | bf38c223793d44d2904a62fe2903078f37079c9c5562abf9d8bc679536ecc80a |
| S/realm_overview_camera.py | 13511 | 5878650d997058411b6d73b2ad531147a8441632339c18957890b28b5d4cd037 |
| S/auto_camera_follow.py | 9245 | 8b1a2ef99f73ccd5a31696173cc9e9544530f8bdd83507559fcc882ebec3b9b1 |
| S/service.py | 871839 | b6e078c2397b355aac9bed24834ad4921c7083b477234d2d66438fd32933a3af |

[旧source审计](g2-m1-c12-quiet-realm-camera-source-audit-2026-10-19.md) 保持14,958B / SHA `118ab52084bac0902daaf661da46830c0c2b9e8423e5e407dd9e395d0756c764`，本报告仅补自然失败。

仅新MD/before0/硬16KiB；实际net及SHA闭场回报。producer_closed=true/future0/external_outputs0/allocated_bytes=null/physical_credit0。原other128/原review `2026-10-20T01:48:56.993837Z`，无新重型child或源期限续期。

