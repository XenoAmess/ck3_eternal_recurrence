# R0177 a07 当前输入字面记录

machine_id: desktop-3fevhd2-1c74096080。记录时刻见 INDEX.actual-a01.json；来源是 R0177 010/012/013/023 具名响应及 010 外层 army_history_evidence 所绑定的完整 Driver JSON。运行时身份原件的 SHA 与原文附在 CURRENT；日期为 53146632，paused。同一记录不能外推其他机器或场次。

CURRENT 保留 county floor、refill permission 和 military callback slot 原字面值。observations 的 source_id、identity_context_id、literal_id 分别索引 literal_tables.originals、identity_contexts、literal_values；json_pointer 指向精确原件。相同 literal 的去重不删除任何 occurrence。Army public ID 与 native CArmy ID 分别保留。

CONTEXT 的 observations 直接带 literal，county_loss_application / county_current_movement 是四军完整原 leaf。supply_ 开头的完整 family 限 Army18/93；两个显式标为 sliver 的记录仅保存选定 scalar/gate 字段，不能当完整 Army/family 送入 normalizer。其余 contributors、clock、30 phase、next-pair、rate、resupply family 未裁剪。

本次四军 floor 均为 base10000 / second0，raw1D4=0；县 condition 为 no_stored_route。Refill 231 个 chunk occurrence 中 77 available、154 not_applicable，不能当成 231 个唯一 persistent。Available 中 11 个不同 persistent 解析到 Character31254，4A9=1。GUI 506 widgets 中 129 fallback、377 not_button_base，callback 方法名和 click action 均未提供；slot2 不授业务 callback 资格。military 尚未打开是 Root 的现场说明，root_available=true 本身不能证明界面打开。

012 基础现金值和 023 observer/control 原 body 保留。023 control accepted=true、capture_enabled=true、retained_records=0，但 current_raw_context_v1 未出现；这不是维护费归因或原因定位。Source/cold/当前值不能替代县损耗、补兵 ADD、供给 stock、维护费等实际因果通过。此时尚未观察闭场回执。

两个 inspection/extract_a07_current_*.py 入口只接受显式路径，不查询游戏、不扫描 latest、不读 save/video/native binary。当前 record 是带原件 SHA 的 literal 投影；本仓库不包含完整原 response/30MB Driver JSON，因此不声称可离线复算其完整 raw。

原件与外置保护仍至 2026-10-16T07:45:01.597Z；本次不延长。共享代码可跨机器复用，本机状态和结果保持机器绑定。
