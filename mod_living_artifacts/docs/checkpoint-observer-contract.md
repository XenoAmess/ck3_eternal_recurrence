# 核心验收：当次身份与保存后验 v2

此合同取代核心 case v1 的固定 runtime actor 和隐藏事件动态日志。旧 R2 prepared、冻结 c03、实际 BLOCKED 结果及失败日志保持原件；新版 Python 合同不能修改旧 prepared 的 caller/source 守卫。

本次实际来源机器为 `machine_id: pc-20260924rtuf-f11af23c08`，观察日期为 2026-10-21 UTC / 2026-10-22 Asia/Shanghai。证据来自公共 R2 `pc-20260924rtuf-f11af23c08--living-artifacts--R0002`，原 PID 10924 / generation 1；这些整数只描述该场，代码不将其作为下场常数。

## 当次角色身份

[StartupActorBinding](../tools/startup_actor_binding.py)消费公共 host 的原始 report 和 frozen argv：argv 中的唯一前端策略必须与策略原件、host 快照、准备输入 SHA 一致；实际原生前端选中 `bookmark_rags_to_riches_duke_robert` 并单次 Start，随后两个独立 native campaign-root 观测须与各自 snapshot 的角色、PID、generation、日期、revision、EXE 一致，并具有递增的主线程 pump epoch。后续 snapshot 固定该次 runtime actor/PID/generation，不允许漂移。

`history_id=1128`是原版书签输入身份。R2 实际 runtime actor 为31254；历史别场的29829不能约束本场，也不能将31254替换成新的固定值。R2原始来源独立摘录位于外置 `environment/r2-native-observation-a01/observation.json`。

## 保存后验

R2 的隐藏事件 `debug_log` 没有可见事件的动态本地化上下文。原来 `XALW_INPUT_V1` / `XALW_SAMPLE_V1` 中命名 scope 表达式产生实际 `Data error in loc string`，不能充当 getter。仓库已有同类实机结论见[语法踩坑](../../docs/grammar/pitfalls.md)。新版外置 fixture schema2仅写初始物品、初始经验和持久物品引用，输出静态 READY；不排每日观察事件，不改生产状态，不输出动态日志。

实际原生 `ck3_save_checkpoint` 输出的保存状态、当前日期、路径、大小、SHA与原件必须一致。R2原件为71,157,378字节的原生 `SAV...U1` binary，不是plaintext/ZIP。Root 使用从官方 GitHub 实际下载并校验的 Rakaly 0.8.22，以 `--unknown-key error`严格熔化，实际退出0。原件 SHA为`40578998616b6cf3d1834f98b7ff4f518f9cf590d0bdeb6975066e89dcc7272e`；熔化文本104,693,391字节，SHA为`cd088933295bd7a38340c3bd93051f5656e542ac7de2265483a5a74e1dede034`。路径与工具回执保存在该任务外置 `observations/r2-checkpoint-a01/`，不作为其他机器的工具安装证明。

[checkpoint_artifacts.py](../tools/checkpoint_artifacts.py)只解析指定玩家与 `artifacts.artifacts` 中的实际记录，区分同编号的其他数据库、缺变量与原生typed-zero，保留原始64位 identity 十进制字符串。R2实际玩家变量 `xalw_fixture_target` 的 `type=artifact/identity=402` 对应真实物品402；另四件为403/404/405/406。全部保存 owner为31254，四档稀有度依次为common/masterwork/famed/illustrious。402保存初值为level1、XP92、pending0、growth0、last_month12801、resonance20。原生只读 personal-use另证实owner、owned_ids与equipped=false。此时的保存值不等于后续当前内存值；后续动作必须再保存和独立原生读回。

## 公共 Root 回调

新版 adapter 仅调用既有 CaseClient 的 `snapshot / execute_plan / advance_day / root_checkpoint`，不建立host、client、启动器或关闭通道。每次实际MCP保存后，Root收到 `living-artifacts-checkpoint-readback-request-v1`，按统一存储策略保全该份原件、严格熔化并返回[ReadbackResponse](../tools/checkpoint_callback.py)的精确字段。返回的保存/熔化/工具/argv/实际process回执均须带文件Pin；process回执另绑定机器、run及实际退出0。缺少实际工具、token不识别、保存或来源不一致时返回真实阻塞，不能编造 completed 回执。

固定 argv 为 `melter melt original --format ck3 --unknown-key error -o melted`。回调只负责离线文件处理；游戏保存由原公共MCP提交。解析结果再与同日期原生 owner、inventory membership、equipped谓词交叉，不能以源码、回调ACK或保存后的旧截图替代。

新核心case最多三份保存后验：实际9月15日初值、16个真实日推进至10月1日的首次月结、卸下后再31个真实日至11月1日。有限72天/420调用预算不变，不按日保存大文件。三阶段预期分别是1/92/growth0、2/0/growth1、保持2/0/growth1；喂养仍明确BLOCKED，等待真实普通宝物选择流程。

新版v2保存回调还未实机执行；R2原场的Root离线熔化与独立读取只证明其真实来源和当时保存状态，不自动验证新版整个adapter，更不代表12异能、8诅咒、中文界面或发布通过。生产可见事件本地化暂不因隐藏logger缺上下文而批量改动，待真实管理页另验。

## 离线回调执行工具

[checkpoint_producer.py](../tools/checkpoint_producer.py)执行 `--spec <新规格.json>`，规格由 `ProducerSpec` 明确定义，预先固定原公共 awaiting 请求、当次身份、runtime manifest、官方 Rakaly 发布及下载回执、EXE 和统一存储五项输入 Pin。工具校验原生快照、机器和原 hold 剩余时间；按同一存储策略核当前容量、既有预留和输出上界，不创建另一套预留或回收规则。随后保全唯一原件、严格熔化并记录真实 Popen PID/退出码、argv、stdout/stderr、来源 FileID/mtime 的十进制字符串及完成或阻断响应。

`living-artifacts-checkpoint-melt-process-v2` 是当前唯一进程回执合同；消费者不接受旧 v1 代替。成功进程的 stdout/stderr 允许真实 0 字节，保存、EXE、argv 和回执仍须非空。失败响应保留实际原因与诊断，空日志也能作为精确 Pin 保留，不能写假内容凑非空。JSON 往返和真实良性子进程的成功、失败、超时及输出上界均有离线回归；没有因此取得 CK3 live 信用。

## 库存界面回调

原生 ITEM 查询先确认实际 inventory view；已可见时直接继续。若原 MCP OPEN 返回 R2 实测的精确前置错误 `RuntimeError: Inventory opening requires the existing actual managed-source inventory`，同时没有 result，且冻结 guard 文件 SHA 与[合同](../tools/inventory_gui_contract.py)一致，才允许通过已有 Root checkpoint 请求实际 GUI 打开。包含相同文字的其他错误不算此拒绝；未知提交不重发。

Root 响应绑定当次 run/PID/generation/actor/date/目标和原拒绝，必须附真实原图、统一坐标映射回执与点击后原图。校验器重算独立 X/Y 变换，核真实 PNG 尺寸、前后桌面尺寸及 HWND/PID；随后 adapter 重新 snapshot 和 ITEM，实际 view 可见才继续。回调 ACK 本身不能取得装备或 GUI 业务通过。输入桌面不可访问时返回真实 blocked；发出点击但结果未知时保留 outcome_unknown。这条新回调仍待下一场实机验证。
