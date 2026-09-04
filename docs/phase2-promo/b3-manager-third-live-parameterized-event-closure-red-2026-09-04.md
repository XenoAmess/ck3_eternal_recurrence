# B3 manager 第三次 live RED 与参数事件闭包 r4 候选（2026-09-04）

状态：**第三次 live 为 material-projection-parameterized-event-closure RED；r4 为 GREEN_NO_LAUNCH / static-ready-live-pending。** preflight、编译测试和 schema 均不冒充实机能力；在新的 live artifact 形成前，B3 仍未完成。

## 第三次 live RED

- artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\b3e-27b66b3-20260904-063948Z\artifacts-live`
- 时长：312.77 秒；CK3 到达 Frontend，但未进入 Load Save/In Game
- outer `report.json` SHA-256：`504591432CA9E39D75A646AE5C1F133AB62F567C181533F27C40C7E9E7867784`
- cell `report.json` SHA-256：`B0F0657421FB5EBC09973F0B9CA7A763370949C57BFBECF53BC30E49D2107A7D`
- `cell/final_error.log` SHA-256：`A09CA7136D4A83D836D5C691287540B48C4C1225388A1F8F0581BD16E098F6D3`
- `cell/final_game.log` SHA-256：`A8007348CF52AB6D10AF8157DC95C55EFD05EBC9FADE372CBBE0EBF262D7DA81`
- `evidence-index.json` SHA-256：`0F2C9461B09D4FEFB26D43DC190767AEB152D619829D90680BE44669C4D4575E`
- cleanup：GREEN，`failed_checks=[]`；本次冻结前 CK3 进程数为 0。

两份最终日志各有 14 条、14 个唯一的 `Event not found`：`zg361we.4804`、`zg361cl.100`–`.105`、`zg361cl.200`–`.204`、`zg361ip.202`、`zg361ip.302`。调用位置共同指向 `common/scripted_effects/zg361_case_kernel_001_shared_helpers_effects.txt:154` 的 `zg361_case_kernel_schedule_deadline_effect`。

直接原因是 helper 使用 `trigger_event = { id = $EVENT$ ... }`，调用者再以 `EVENT = zg361...` 传入事件 ID；旧 B3 analyzer 只解析直接 `id = zg361...` / scalar event，漏掉了参数实参边。因此，本轮在超时前已存在可复现的实体闭包错误，是 material closure RED，不是纯 loader-performance RED；不触发文件体量 A/B。

## 修复与完整闭包

提交 `9ef686bf3bfa0778ed259e7dc7e9e2722057640b` 将 `EVENT = <custom-event-id>` 纳入 reachable 和全 material 两层图，并提供可复用的固定点 projection expander。对旧 r3 product 的反向回归得到：reachable 缺 5 个事件，而全物化树缺 20 个事件。除 live 已走到的 14 个外，还包括 `zg361ip.203`–`.205` 与 `zg361ip.303`–`.305`；它们是同一批已物化 sibling effect 的 concrete 参数事件，必须一并闭合，不能等下一次实机逐个报错。

r4 从当前 canonical release 的真实 provider 做 3 轮固定点扩展：

1. 为 20 个参数事件加入 4 个 event provider 文件。
2. 为这些 event body 递归加入 17 个 effect provider 文件。
3. 再加入 2 个末端 effect provider 文件。

最终新增 23 文件；语义 reachable 为 1,868 effects / 560 events，全物化投影为 3,698 effect definitions / 985 event definitions；missing effect=0、missing event=0、duplicate provider=0。扩展证据 SHA-256：`6049DCFBA73877469A072C404C5FA4EBB6E14E2ACE527C76D07B3AA718BBF79A`。

## r4 no-launch 候选

- canonical base：`1341251dd028b68adf5a4adeb497c94acf3a9471`
- exact freeze source commit：`70fa29f3e4a1ae2a9ae60781f66529dec9fd11eb`
- candidate：`Z:\ck3_mod_rewrite_process_assets\zg361\b3f-1341251-20260904-070920Z`
- signed manifest：`phase2-b3-parameterized-event-closure-no-launch-attempt-70fa29f-2026-09-04.json`
- manifest SHA-256：`D4F69286EDA900DF14BA0FF3604137A49E7E9E322D6EEAFA47E68B3F1E924EE7`
- projection：564 files / 21,590,413 bytes
- projection tree SHA-256：`7EA579A72A6C714EAA2C4CD4CC4C479EB6E0B7AA720FE461FBA54C8114A01041`
- projection manifest SHA-256：`3A7517E6B4AE9FBB415EDDB8F2D666414C9BDE61A56F6C4639E5AE8F30F31289`
- native source fingerprint：`590FAE6DE49B44F992DE48C4C4E16CFA2D1E3AF05E4A0C3EF1294B4F802FCC51`
- DLL SHA-256：`FF507EB90E3D2550C98F401508CFD5C150B3CD9094BC9C783A0CC3C9F7E0C284`
- injector SHA-256：`86ABF19AE7F727178FC614759855D9C9750A781F68697AD62CC583A7B91D096B`
- native tests：92/92 GREEN；最终 ctest 日志 SHA-256 `9F2EF2B2BD904DFEBCB427E7B2DC405A113A241EECA82CD82B2EE3596CC45AA3`
- central normal/-O 38+38、manager normal/-O 49+49、freezer normal/-O 11+11、expander normal/-O 1+1：GREEN
- formal no-launch preflight：GREEN；日志 SHA-256 `DB3E27858D4B8CDCC8DC58217F7D15BE20018A9CE9D6D6A5F90205CDD28F9CAD`

首次 r4 preflight 曾因 canonical runner 已增至三个 Workforce fixture 调用、而 fixture test 仍断言两个调用而 RED。提交 `70fa29f3e4a1ae2a9ae60781f66529dec9fd11eb` 只把测试更新为“一处定义 + 三处调用”，未修改 runner/product/native；失败日志与 RED manifest 保存在 candidate 根目录，随后正式重签为全绿。

## effect 文件边界

相对冻结 B2 r10 baseline，`delta_over_hard_max=[]`。本轮闭包新增的 19 个 effect provider 文件全部为 1–10 个 effect，最大 10；B3 manager 仍为 7 个用途分片 / 43 effects / 单文件最大 10。整树仅有三个超过 20 的冻结历史 provider，本轮未新增、未扩大，也没有提出例外。

唯一 live 命令已固化于签名 manifest 的 `launch.windows_command`。执行后必须以新的 paused/provider-observed artifact 判定 B3；在此之前只保持 `static-ready-live-pending`。
