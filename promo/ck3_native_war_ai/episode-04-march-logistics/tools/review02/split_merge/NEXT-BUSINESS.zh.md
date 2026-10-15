# R09 下一 scene：反向合军与不同库存/容量

准备机器 `desktop-3fevhd2-1c74096080`，观察时间与研究源HEAD见外置 `START.actual.json`。只有Root可在新的a07普通会话调用阶段；本准备件没有SDK、游戏、桌面、EXE读取/执行、构建或主树写入。原共享512MiB、active32及2026-10-16T07:45:01.597Z截止不延长。未来source、run、PID/create/gen/episode和原生合法性不能沿用R0176。

当前 `root_relay.py` 只有主军作为destination的合军，未保存stock/cap/weight小投影。增量只补反方向、fresh既有pair的pre-merge以及无新请求的supply-clamp后验。旧R0176默认仍要求dcda/sequence176/selected93；新scene显式传入 `--source-head <实际normal构建HEAD> --run-sequence <实际分配sequence>`，它们必须匹配当前checkout、context和runtimeproof。原machine/exactEXE、进程创建时间、原期限、capacity、独占Root transport和onceclaim守卫保持。

另传 `--module-pins <MODULES.next-scene.pins.json> --module-pins-sha256 <该原件SHA>`。其中十个生产文件和sidecar仍逐字节校验；这是研究时已有生产代码的冻结列表，不宣称它所属的旧HEAD就是未来runtime。如果a07这些生产字节另改，须由Root在实际source冻结时重新审阅同一十文件列表并给新pin/SHA，不能清空列表或仅改source标签绕过。所有阶段使用同一helper SHA、context/proof/request-helper SHA与case绑定，不在阶段间改参数。

## 反方向最短链

Root先冻结R176后继正常seed的SHA与来源，再在新scene保存独立baseline；所有阶段加 `--army-id 93 --merge-destination sibling`。

1. `baseline`：fresh全roster、一次complete普通strength query、各available军的完整DATA/role与独立current commander、stock/cap/native D weight；末尾same-frame snapshot。
2. `split-once`：只提交一次 `split-army-half-93`，claim先于请求。`post-split`只读独立后态，动态集合差发现唯一sibling、完整CUnit→CArmy generation、250实体DATA与各ArRg occurrence守恒，并分别保存每军stock/cap和实际统帅。
3. `merge-once`：冻结的实际sibling作为D，93作为S；真实step为 `merge-armies-<fresh sibling>-with-93`，不能填历史162。`post-merge`独立核D保留、93消失、全部DATA与role/统帅、库存/容量/两stage权重算式。`supply-clamp`只复算已保存packet和原merge回执，零新query/动作。

这只新增两个动作（one split、one reverse merge），不重跑旧forward微实验。snapshot/caps/query不算动作。角色造成unrelated strict失败时完整observation已先保存，立即交离线分析；旧59/34232例外不自动迁移到新scene，不重发split/merge。

冻结卡R09要求“从该新微实验baseline独立试反向”。R176现seed的93已由34232统领，旧微实验baseline的93无统帅，故不能仅凭人数250相同，把旧forward与新reverse称为同S0双方向比较。反方向本身可新增实测；整卡公平双向关系要有两个独立normal cold-load且完整baseline相同的arm证据，或Root取得真正旧baseline的正常seed。不能从一次merge终态直接反转，再授独立baseline信用。

## 不同库存/容量与upper clamp

Root给出的待重读输入为：93/94/95各250、stock100/cap100；18为1195/1195、stock300/cap300；93实际统帅34232。这些是R176后继seed资料，未来scene先读回。只有同stock100的split/remerge通常不能区分加权与upperclamp。库存是绝对单位，不能用stock/cap百分比或GUI整数替代raw/Q100000。

已有typed接口：`ck3_query_army_commander_candidates_v1`返回每candidate真实CanAssign/最终资格、native base quality等；`ck3_execute_step`的真实任命step由生产 `assign_army_commander_v1_step(army_id,character_id)`生成，即 `assign-army-commander-v1-army-U-to-character-C`，仍需fresh capability/step、原生Validate及onceclaim/独立readback。候选没有发布candidate capacity；quality不等于容量，siege modifier/current movement也不替代capacity。不存在已验证“capdecision”数值预测接口。本增量不自动挑人或新增任命动作helper。

可先用普通合法任命获得不同当前cap，但只在任命后的fresh strengths确认实际stock仍高于新cap、当前commander确为所选人、完整physical DATA保持后才冻结实验输入；任命可能同时改变角色关系，须单独保留，不能假定300会存留或指定人物一定可任命。若CanAssign/Validate false，保留真实原因，不换通道或写内存/save。

如选择两个**既有**军而不split，用独立新case，固定如 `--army-id 93 --merge-source-army-id 18 --merge-destination source`（93为D，18为S；实际双方须同地合法）。依次调用 `pre-merge → merge-once → post-merge → supply-clamp`：仅一次merge动作。pre-merge先保存全packet observation，完整pair/gate通过后才生成可提交phase。这里不授split/反向独立baseline信用。若需要split后换将，再用无 `--merge-source-army-id` 的 `pre-merge`刷新同日输入，须保留原pair generations与全部available physical DATA/occurrences。

不同precap/stock不保证upperclamp：18统帅可能被merge选中使postcap仍300。每次只核实际结果，不事后换将“修”该次结果。D权重必须使用D行 `merge_supply_destination_weight_raw`；S权重使用该次原生current_soldiers（生产getter已核完整ArRg sum）×100000，不误用S作为D时的weight。

计算各share=`trunc(w*100000/(wD+wS))`，各contribution=`trunc(share*原stock/100000)`，先逐军两次截断再求和。以**合后实际cap**取clamp，与合后stock exact比。仅 `preclamp > post_actual_capacity` 且实际库存精确相符时 `upper_clamp_observed=true`；相等边界、零weight分支、缺值或不吻合均不给upperclamp资格。纯算术吻合不观察源PC、不证明全部producer。若实际complete DATA变动或unrelated strict失败，保留packet并停止此资格，不为追求clamp重发动作。

全卡仍另欠完整动态30–60秒split→merge→survivor/commander/queue/supply镜头与冻结arm关系。Root负责新scene录制；本helper不二次start recorder、不推进日期、不自动开游戏，固定 `R09_full_card_closed=false`。四个新增离线behavior检查只验证reverse onceclaim、真实postcap的算术界限、新run/source绑定及坏premerge保全，不授实机资格。
