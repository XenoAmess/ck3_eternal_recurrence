# B3 manager 第二次 live RED 与 event 闭包修正版候选（2026-09-04）

状态：**第二次 live 为 material-projection-event-closure RED；修正版为 GREEN_NO_LAUNCH / static-ready-live-pending。** 本文不把 preflight、ACK 或 schema 冒充 live，也不声称 B3 已完成。

## 第二次 live RED

- artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\b3c-ce458af-20260904-0613Z\artifacts-live`
- outer `report.json` SHA-256：`2F44D5C06549D0EA6CCDB977A602441C92276CDE80138686648249E003AEFF2F`
- cell `report.json` SHA-256：`3852B4620AC2E4CA0B41F526C6771AE1446AEE623BFE37110AC158B770ACB9AE`
- `cell/final_error.log` SHA-256：`E1CAF82E07B3EE6E4B75D9545BA4576EFC5E8424E656A909B32CA3085839DED4`
- `evidence-index.json` SHA-256：`DFF94EBAE25F8557E91B40FD4A72C04BF378405613C638E9AF10849C101E4CFF`
- cleanup：GREEN，`failed_checks=[]`，收尾后 CK3 进程数为 0。

本轮日志只有两个具体 event-not-found 首错：`zg361p2c.2` 与 `zg361p2c.1`。调用者均位于 `common/scripted_effects/zg361_phase2_central_003_dispatch_control_effects.txt`，真实 provider 为生成文件 `events/zg361_phase2_central_001_serial_dispatch_events.txt`。因此超时之前已经存在可证实的实体闭包错误；本轮不是纯 loader-performance RED，不触发文件体量 A/B。

## 闭包修复

freezer 现在同时维护两层检查：

1. 从 `zg361_p2c_stage_10_manager_governance_effect` 出发递归解析 effect → event → effect/event 语义调用链。
2. 对投影中所有已物化 effect/event 定义执行 unresolved custom-call 门禁，以覆盖同一 provider 文件内也会被 CK3 编译的 sibling 定义。

旧 r2 投影的回归精确得到语义缺失 `zg361p2c.1`，物化投影缺失 `zg361p2c.1/.2`。修正版从真实 production release provider 经过 9 轮 fixed point 新增 229 个 provider 文件；扩展记录 SHA-256 为 `A0D16C53A6F64C5AE63DAD69A69DDF74B91FAFF7621279CE197F23A5DDE51C27`，对应 canonical release manifest SHA-256 为 `698C69042C92860043203394DD798B7753B454F858398D62FFE4D182DB53A589`。

最终语义闭包为 1,548 effects / 364 events，物化投影为 3,581 effect 定义 / 935 event 定义；missing effect=0、missing event=0、duplicate provider=0。

## 修正版 no-launch 候选

- canonical base：`a07887a7e8d3d4079ed620e56a49f94afc659740`
- exact source commit：`4ee7e92ef1c88e0e138febd76c4afc59c299ddcf`
- candidate：`Z:\ck3_mod_rewrite_process_assets\zg361\b3e-27b66b3-20260904-063948Z`
- projection：541 files / 20,967,862 bytes
- projection tree SHA-256：`BDADC1F2093A382E0849168A5000396610CE8068BE47CB3CBDEEE8E9BE64B757`
- projection manifest SHA-256：`B769CA3E36E42CB30AE667B91B7F7B54B7648B5AB3C0F28144B18A4C82D9C0AD`
- native source fingerprint：`96AA92DD599A45CF39E528ABD2033B4F879CCA32B079C074575442FF80062A4E`
- DLL SHA-256：`7550A81DF8C9F752ABE558FFAA346FA2165E472A290C1ED20A645E52AA2D0DD4`
- injector SHA-256：`6B3C6B413B1E485C7F695B1D9A1FCCC6D5F8BED27382FE9FFB654D6A179D5970`
- native tests：92/92 GREEN；日志 SHA-256 `A2633488C219F1DBB0F66FF4503512D202A75E705CCBC1A546D04A1814A6FFDD`
- central/manager generator checks、normal/-O tests、freezer normal/-O tests：8/8 commands GREEN
- formal no-launch preflight：GREEN；日志 SHA-256 `FDE8AAE3FC13A1210AEE3BD94F98E452E80143CE1F03B2CD36208E3091122B4D`
- signed manifest：`phase2-b3-event-closure-no-launch-attempt-a07887a-2026-09-04.json`，SHA-256 `561C106142447F297046FF8A663A90C65008546AC8BD0CDA1BF376A5B13A9D1F`

## effect 文件边界

相对冻结 B2 r10 baseline，本候选有 266 个新增/替换 effect 文件；`delta_over_hard_max=[]`，没有任何新文件超过 20 个 effect。B3 manager 仍为 7 个用途分片 / 43 effects / 单文件最大 10。整树中三个超过 20 的文件均为冻结 B2 之前继承的历史 provider，未被本候选新增或放大；本轮没有例外申请。

下一步只能用 manifest 内唯一 pipe 与唯一命令串行启动一次 CK3。成功前 B3 继续标记为 `static-ready-live-pending`。
