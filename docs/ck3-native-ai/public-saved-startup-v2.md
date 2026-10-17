# 存档启动 v2 的公共 Selection 接线

`machine_id: 4-8e1c2f1861`；源观察时间 `2026-10-17T10:33:02.600819+00:00`。范围仅为离线源码、公共 `Selection.preflight` 的合成输入测试与外置候选；未修改活动源码，也未 prepare、allocate、启动或操作 CK3。

已实现的 host 支持批准场景的 `ck3-saved-campaign-startup-case-contract-v2`，通过实际两个 owner 帧后绑定当前进程事件实例，再以独立 runtime v1 合同验证。公共 `tools/ck3_mod_acceptance.py` 仍只收 v1：五个固定字段、正整数事件实例和 `admit_saved_startup_event` 函数。因此，合法 v2 会在进入 host 前被拒绝；原公共代码对同一合成 v2 的实际 preflight 已复现此拒绝。

候选只扩充这一个校验分支。v1 的字段、具体实例与原函数要求保持。v2 要求六个准确字段、`profile_id=faith-and-power-e01-abbasid-867`、`event_instance_id=null`、`xar_faith_h01_prepare.1`、日期 51394920、原生选项 `[0,1]`，并只收现成纯函数 `qualify_prepare_event_from_save`。玩家、ROOT 和日期仍绑定被选存档；函数、依赖和合同均保留文件 pin 校验。它只接通输入资格，不提供业务 proof，也不省略 host 的实际 owner 帧、原生窗口和独立 fresh 后验。

公共最小完整测试 `test_public_saved_startup_v2.py` 六项通过（0.730 秒）。覆盖旧源码实际拒绝合法 v2、候选合法 v2 仅 source preflight 通过，以及未知 profile、固定实例、错定义/日期/选项、布尔选项、额外字段、foreign function/state/actor、依赖变化的拒绝。旧 v1 正向仍通过，null 实例和错误函数仍拒绝。合成测试的通过不证明实机工具资格、存档加载或任何 normal/PASS 结果。

补丁 `public-saved-startup-v2.patch` 以原活动文件 SHA-256 `84690059b07e9d8740606fd02fe74701218246297738a1fffbab89ba51b803ac` 为来源，只含公共 preflight 的两个上下文 hunk。集成时按上下文合并补丁，不能拿完整候选文件覆盖活动树中其他合法修改。原始来源 pin 见同目录 `public-candidate-source-pins.json`。

R4 从 F 母档冷载的四文件投影仅含 descriptor、原事件定义、两语 localization；没有 bookmark 或 on-action registrar。实际物化必须使用 `materialize_product_profile(context,event_only_dir,configuration)` 后 `finish_product_profile`，并将显式 `saved_campaign_startup_case_contract` 携带进 adapter 返回的 `startup`；公共 prepare 会采用返回的整个 startup，不能只在 products 中声明后又在返回值丢失。B 的选择和保存属于 Root 的后续显式动作，initial plan 保持只读。
