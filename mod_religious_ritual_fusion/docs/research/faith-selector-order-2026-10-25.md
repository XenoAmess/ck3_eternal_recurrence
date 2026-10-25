# Faith 来源选择器顺序与现有 MCP 定位路径

观察机器：`machine_id: 4-8e1c2f1861`。二进制复核时间：`2026-10-24T23:55:31.191969Z`（当地 2026-10-25）。本次只读研究，没有启动或操作游戏，没有编译、修改原生/SDK、修改保存或创建完整 melt。

结论：现有选择器可以按真实保存的成员关系计算候选顺序，再以实际控件身份选择和读回来源卡片核验。公开控件查询不提供 Rite ID 或文本，不能直接按 ID 搜索。以下原生顺序证据消除了按猜测行号或遍历 148 次选择的需要；新 Faith 场次仍须先读取自己的 before 保存及实际完整控件树，才能授予该场候选行身份。

## 来源与适用范围

本机实际 `Crusader Kings III/binaries/ck3.exe`：1.20.0.4 / build 25734779，101040248 B，ImageBase `0x140000000`，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。下文 RVA 和字节均直接从该文件读取；不从其他机器的记录继承本机资格。

| 实际读取的文件 | SHA-256 |
| --- | --- |
| `common/decisions/rrf_decisions.txt` | `3a3ad85544e16ed260ac25def4f83b27164737bf5c43166e767b6ab95ebe95cf` |
| 原版 `game/gui/decision_view_widgets/decision_view_widget_select_rite.gui` | `699e47b15bd31dc7faf9e2e9a3824565b305d7bb6767de76997a7a1a7836ea64` |
| 原版 `game/gui/shared/buttons.gui` | `88403785a1acdacc628730aaa101a04b2ae6293e74aa706a93e0e1695f3b1a0c` |
| `gui/rrf_fusion_window.gui` | `0a7db9e971aa8bf5d1388aeb049040919404e1fc5e6c607e2044d7e540f090b2` |

产品 GUI 仍由 Root 维护；表中 SHA 只绑定上述观察时刻，不追认后继编辑。参考保存仅为 R0006：`C:/workspace/rrf-development-20261024/save-oracle-r0006-a01/before.ck3`，68529136 B，SHA `8556df425386174c4316b9fd212c55a91d54c54af85460f07e9cdf80dbbdae4b`。其已保留 `before.actual.json` / `before.inputs.json` / `BEFORE-TERMS.actual.json`。R0007 的实际结果 Rite153/Faith13 不作为新场次的输入，也不套用于后续 Faith 场次。

## 脚本候选与 GUI 条目

`rrf_decisions.txt:52–70` 的 Faith 模式 setup 为：`every_religion_global → every_faith`，排除 `scope:actor.faith`，再 `every_faith_rite`，仅保留 `can_convert_to_rite = yes` 并依次 `add_to_list = item_list`。`is_item_valid` 执行 `rrf_target_faith_trigger`，原生将结果存为条目的 enabled；它不会从 setup 列表删除禁用项。因此计算行号必须保留禁用候选，提交前另外检查目标控件 enabled/clickable。

原版 selector GUI：第 17 行模型 `DecisionViewWidgetSelectScopeObject.GetEntries`，第 25 行每项取 `SelectScopeObjectEntry.GetScopeObject.Rite`，第 27 行调用原生 `OnSelect`，第 28–29 行分别绑定 IsEnabled/IsSelected。它没有搜索框、脚本排序或筛选按钮。其 scrollbox 高 200，行高 60；屏幕外不等于未实例化。

反射登记 `GetEntries` 位于 RVA `0x30ce90`，使用 wrapper `0x18d44b0`；wrapper `0x18d44bc` 的 `48 8d 41 20` 直接取 controller 的 `+0x20` 条目数组。controller 初始化 `0x18d11b0`：`0x18d1328` 调用 setup getter `0x2610e80`；每 16 B Scope 顺序调用 `0x2611060` 检验，再调用 `0x18d48f0` 追加 GUI entry。`0x18d13b0`（file `0x18d07b0`）字节 `4c8d4dd74c8d4567488bd3498d4e20e82c350000` 绑定 tooltip、检验布尔、Scope 和数组；`0x18d1400`（file `0x18d0800`）`4883c310e933ffff` 将输入游标加 16 并返回循环。未发现该路径额外排序或删除禁用项。

## 已闭合的原生迭代顺序

1. **全局 Religion：数据库槽位递增。** `every_religion_global` 登记 `0x371f50 → 0x1d16a30`，工厂 `0x1d23680`，实例 vtable `0x46611d8`，执行入口 `0x1d360a0` 调 collector `0x1cf9ce0`。collector 依 `GameState+0xD458` 数组、`+0xD464` count 原序输出 Scope kind `0xF`。`0x1cf9d00`（file `0x1cf9100`）最短读取：`488b9a58d4000048638264d40000`。
2. **Religion 内 Faith：Religion.faiths 数组原序。** `every_faith` 登记 `0x371e90 → 0x1d17e70`，工厂 `0x1d23120`，实例 vtable `0x4661840`，执行 `0x1d36730 → 0x1cf9900`。collector 解析 Religion full ID 后从 `Religion+0x1E8/+0x1F4` 取 Faith ID 数组和 count，逐 4 B 输出 Scope kind `0xD`。`0x1cf9960`（file `0x1cf8d60`）字节 `488b98e8010000486380f4010000`。不按 Faith ID 重新排序。
3. **Faith 内 Rite：unsigned full Rite ID 升序。** `every_faith_rite` 登记 `0x371ef0 → 0x1d17450`，工厂 `0x1d233d0`，实例 vtable `0x4661418`，执行 `0x1d36420 → 0x1cf9a40`。collector 经 Faith→Rites 映射取得 ID 列表后复制并排序。`0x1cf9b16`（file `0x1cf8f16`）`488d05430fdffe4889442430` 指定比较键 getter `0xaeaa60`（file `0xae9e60`），其机器码 `8b01c3` 即 `mov eax,[rcx]; ret`。小列表排序比较 `0x1cf9b93: 3bc3 7321` / `0x1cf9bcc: 3bc7 7323` 使用 unsigned `jae`；大列表分支使用相同 getter。排序后 `0x1cf9c80` 起将 ID 包装为 kind `0x2A` Scope 并依序追加。不能把保存中的 Faith 颜色匿名块当作 Rite 列表。

全局数组顺序还闭合到了实际重建逻辑，而不只是看到 collector 读数组：构造器 `0x2adce05`（file `0x2adc205`）`498d9f20d40000` 定位 `CReligionManager = GameState+0xD420`，故 manager `+0x38` 是上述全局数组。manager 的 `0x29d8540` 在 `0x29d8559`（file `0x29d7959`）以 `488b4608488d4e08ff5048` 调用第二 vtable 的 `+0x48`，对应 `0x29d8a40`。该函数以 `this=manager+8`：

- `0x29d8b8c` 取 `this+0x18` 的 Religion DB、`this+0x30` 的全局数组；`0x29d8b94` 清数组 count。
- `0x29d8bac` 取 DB slot count；`0x29d8bb4` 从 slot 0 开始。
- `0x29d8bc0` 递增遍历 16 B slot，忽略空指针；`0x29d8bd4` 取对象 `+8` full ID；`0x29d8be1` 调 `0xb02d10` 追加，随后 `inc ebx` 循环。
- 该最小闭合片段 RVA `0x29d8b8c` / file `0x29d7f8c`，96 B：`4d8b7518498d5d3044897b0c418b563c488bcbe82cf90dfe48895d48488d7548418b7e2c85ff743c418bdf660f1f8400000000004863cb4803c9498b4620488b54c8084885d274128b4208894540488d5540488b0ee82aa112feffc33bdf75d4`。

因此全局顺序是 **low 24-bit registry slot 升序，保留对象的完整 generation ID**。R0006 inventory 为全 ID `0..48`，均 generation 0，所以该保存的顺序恰等于 ID 升序。后继若出现 generation 非零，必须按 `id & 0xFFFFFF` 排序，不能直接按 full ID 排全局 Religion。

## can_convert_to_rite 的真实过滤字段

不能把此 trigger 解释成“当前角色已通过所有改信资格”。登记 `0x57e631` 建立 factory vtable `0x4786218`，工厂 `0x2aebea0` 建立 trigger vtable `0x47844b8`；其 slot 27 为 `0x2aea9c0`，只解析 kind `0x2A` 的 Rite full ID，并在 `0x2aeaa1c`（file `0x2ae9e1c`）以 `0fb682e8040000c3` 读取 `Rite+0x4E8` 单字节返回，没有读取 actor、改信费用或教义资格。

保存字段映射也已核实：CRite secondary serializer `0x24f5630` 的 this 是 Rite+0x10；`0x24f57cd` 写 token `0x3870`，`0x24f57e7` 读取 `[this+0x4D8]`，与上述同一字节。静态 token 表 RVA `0x46f6f40` 是 `7038000000000000181f6d4401000000`，即 `0x3870 → VA 0x1446d1f18`，该地址字符串为 `convert\0`。因此保存 AST 的 `convert=yes` 是可用于这个 setup filter 的确切字段；`enabled` 是另一字段，不能替代它。

## 小型保存索引与候选算法

现有 Java `SaveInspector.inspect(Request)` 可在内存返回经过完整 decoder/保存不变校验的 typed Report；CLI 的 1 MiB 报告落盘限制不要求写完整 Report。由 Java tools agent 沿这个已有 producer 分批读取，输出小型 `{Rite id,faith,convert,enabled}`、Religion.faiths 原序和必要 Faith.religion/main_rite，不新增 parser，不写完整 melt。保存、解码器、机器、时间、退出码和小索引 SHA 必须随实际回执保留。

只用该场真实索引计算，不引用历史候选数：

```text
entries = []
for religion in present_religions sorted by (full_id & 0xFFFFFF):
    for faith_id in religion.faiths in saved order:
        if faith_id == actual_actor_faith: continue
        for rite in actual_rites_of(faith_id) sorted by unsigned full_id:
            if rite.convert == yes: entries.append(rite.full_id)
target_index = unique index of actual_target_rite_id in entries
```

要求索引完整、关系无重复/悬空、目标唯一、actor/target 来自相同 before 保存。保存缺字段、关系不闭合或场内候选发生变化时返回 unknown，不用定义默认值补足。R0006 已知 Religion8.faiths 为 `[12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,103]`；Faith103 唯一/main Rite152，仅证明该保存中的关系，不授予新场次行号。

## Root 的最少现有 MCP 步骤

1. 用该场实际 before 保存重新确认 actor Faith、目标 Faith 的唯一 Rite 和上述候选 index；先通过已有 decision 工具打开 Faith 来源选择器。
2. `ck3_query_scripted_widget_controls_v1(root_name="decisiondetail_view", expected_revision="<实际 revision>")`。revision 是规范十进制字符串。必须 `available=true, complete=true, truncated=false`；检查实际 option 数与索引计算数一致。按实际 child_path 的行序识别 target_index 对应按钮，检查 effective_visible/enabled/clickable，并取本次 `widget_id/query_generation/public_revision`。公开工具无 text、Rite ID、搜索、分页或 scroll 参数。
3. `ck3_activate_scripted_widget_control_v1(query_generation="<query 的值>", widget_id="<本次目标按钮>", expected_revision="<query.public_revision>")`，沿原版 OnSelect 派发。不得复用历史 widget ID；UNKNOWN 不重放。选择后用 fresh 查询取下一步按钮并进入草稿，这仍不是最终融合提交。
4. fresh 查询 `rrf_fusion_window`，定位实际来源 B card 的 `rite_button`，用同一通用控件接口激活。产品 `rrf_fusion_window.gui:135` 给 B card 绑定 `rrf_source_b.Rite`，`:195–209` 保留 Rite 并加入 Faith context；原版 `buttons.gui:1500–1504` 的按钮执行 `OpenGameViewData('faith', Rite.Self)`。
5. 用 `ck3_query_faith_power_ui_v1(window_kind="faith", subject_id=0, expected_revision=<fresh 整数 revision>)` 观察当前 Faith；此工具的 revision 沿现有整数合同，与通用控件工具的字符串合同不同。不要预先打开 Faith103 再冒称卡片验证。先 subject0 观察，避免把猜测身份作为断言传入。
6. 公开 Faith query 返回 actual `current_subject_id` / `presentation_ui.subject_id`，没有 selected Rite ID。若该场 before 已独立证明目标 Faith103 只有/main Rite152，来源 B card 打开的实际 Faith103 可结合这份唯一成员关系间接闭合 Rite152。原生 `religion_ui12004.cpp:81–82,127` 私下读 FaithWindow+E8、+258 并校验 Rite→Faith full-ID join，但公开 wrapper 没有导出 Rite 字段，报告不可写成“公共 query 直接读回 Rite152”。错选则取消草稿，保留真实诊断；不要提交融合。

## 控件容量与未验收边界

native census `zhongguo_scoreboard_state_v1.cpp:1835–1910` 遍历实际全部 children，不按屏幕矩形过滤，也不会替游戏创建虚拟化行。上限 2048 widgets；`scripted_widget_control12004_native.cpp:143–153` 对不完整/截断树拒绝提供动作 token。没有现成的公开 scroll/select_scope_object-ID 通道，不为本任务新增 provider。

R0006 实际 `root-execution-a06/02-open-rite-selector.actual-terminal.json` 中 selector 为 168 widgets、5 个完整候选；5 个按钮均 visible/enabled/clickable，路径为 `3/1/2/0/0/0/0/0/{0..4}`。这证明该时刻滚动区域遮住的行仍有原生控件，不保证任意后继都未虚拟化。该树每行 13 widgets，固定部分 103；若后继恰为 148 行且结构相同，则估算 2027 widgets，仅比上限少 21，不能将估算写成实际通过。后继树若截断、候选数不同或目标行不存在，应保留 unknown 并停止该选择路径；不得按 148 或历史 path/ID 盲试。

本记录完成 exact-build 静态链和现有 API 可施工路径。尚未在新 Faith 场次执行目标选择、卡片读回或融合后态验收；后继实际由 Root 追加。该研究不改变 R0007 canonical 结果或其任何保存。
