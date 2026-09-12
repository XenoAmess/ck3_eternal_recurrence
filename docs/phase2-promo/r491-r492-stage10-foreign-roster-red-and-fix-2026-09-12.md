# R491/R492 Stage 10 外来 roster 污染 RED 与最小修复

## 结论

旧轮次 R491 完成前台预热并终止后，当前轮次 R492 作为唯一 gameplay 实例恢复玩家经理 `29037`。loader `303/303`、exact-build native、产品挂载和 material-error 门均为 GREEN。Stage 10 只执行一次正式 MCP handoff 和一次 `run-stage10`，没有 retry。

R492 在 `date_raw=53154120` 到绝对截止 `53157000` 的 120 游戏日窗口内完成 40 次观测，但始终保持 `B1=true / Central=false / PP=false / review-now=false`，最终保留 `stage10_slice_failed` RED。日志同时出现 7 次 `performance season published` 和 10 次 `final callback survivor compaction failed; settlement withheld`。这说明固定产品尾链已经运行，失败不再是观察窗不足；继续延长窗口不会增加诊断信息。

实机还安全处理了 exact-build 原版事件 `spymaster_task.0381` 和 `ep3_governor_yearly.3060`。两轮已终止，CK3、worker、Operator MCP 和端口 `12442` 均为零。P1 保持 `8/9`，P2 最终宣传视频继续硬锁定。

## 根因

冻结 v5 source 的玩家经理 `29037` 身上，持久变量列表 `zg361_b1_subjects` 有 29 个仍存活的 Character 引用；其中只有 6 个同时满足当前 exact case tuple：

- `case_owner=29037`
- `cycle_serial=17`
- `case_serial=17`
- `case_active=1`
- `roster_included=1`
- `case_subject=this`

其余 23 个引用已属于经理 `29628` 的 cycle/case `19/19`，但仍残留在 `29037` 的持久列表。旧 `zg361_b1_prune_unavailable_subjects_effect` 只检查 `is_alive=yes`，因此保留了这些外来引用；后续 agenda/processing 构造却按 exact tuple 只得到 6 个当前 case subject。最终压缩要求 survivor、subject 和 processing 数量一致，于是该状态结构性地无法闭合。

## 最小修复与验证

生成器现在对 `zg361_b1_subjects` 和 `zg361_b1_processing_subjects` 使用同一 exact-tuple 过滤：Character 必须存活，且 owner、subject、cycle、case、active、roster 六项都与当前经理的当前 case 一致；缺字段或任一字段不一致均 fail closed。奖励、quota、rerank、pending/reopen、F 票据和 Stage 10 时间上限均未改动。

聚焦验证为生成器重建、`py_compile`、`git diff --check`，以及 B1 runtime normal/optimized 各 `76/76` GREEN。没有为该单点修复启动 CK3 或扩大成长跑。v5 receipt 绑定的是旧产品树，已永久失效；下一次只能使用绑定本 RED、exact roster 证据和修复后产品树的 v6 receipt，执行一次新轮次短验收。

本次 `source-character-29037.txt` 是为立即定位现行 RED 生成的一次性摘录，只覆盖该角色块，不能作为长期接口。迁移已在下一次 CK3 启动前完成：[`inspect_ck3_save_character_scope.py`](../../tools/inspect_ck3_save_character_scope.py) 接受调用方提供的 save/Rakaly 或 melted 路径、root CharacterID、变量名和持久列表名，输出 `ck3_character_scope_offline_v1`。它不绑定账号、机器路径或轮次；v6 Operator 把报告作为 hash-bound 只读输入消费，其他机器可用同一 CLI 生成并通过自己的 Operator MCP target profile 查询。

真实通用报告为 `41,038` bytes / `74BF50BB83DBA083A767F96E954E1F0EA86D2059D44BA1DC0FE33BEE56F3B328`。v6 receipt 已通过生产 validator 的无启动校验，SHA-256 为 `E363D5EE27421F27DCF80A4B4B6DE174ABCB85343C5116D7D18E5FFDC59FACF8`；修复后产品树为 `C428C42B88A47F6B8834099B6CF8598FB0F405CDC79203EBCAB9752F4E9CB5DC`，projection manifest 为 `DEEF481DAAA202C0A6CED3030F750B355536D1EED406DE520D5BDCEA8D6CB99F`。

## 冻结证据

| 证据 | SHA-256 |
|---|---|
| direct Stage 10 RED | `0B3ADF6C084110E593327BE4367F418E7AFD86539948C42A99D3B7835BACF9EE` |
| managed Stage 10 RED | `23CCC8C102FF51A62C3F625A18230F6CCD98A662C95708C5226B808143307BD9` |
| 最终 `debug.log` | `72C32D5D829E254CEACBEFA58B9EAFE1DC756B0F8F7FC075A1B4A78A3B3668CF` |
| 最终 `error.log` | `A5FD7E8DAE6E3EF627D0F3D5243FC63A11212C1D6CDD59C8426DB06D5C4E21CA` |
| 经理 `29037` 一次性角色块摘录 | `682B05D903E9C57749887E9BD755FA9E5DEB85AB189638C0306494A413378C2B` |
| canonical cleanup | `6CE9E80C8605E813F6047BCBE0827F7D0236424FA472C6238231A0F98F4309A1` |
| managed cleanup | `1FB65E2F0AE82BB84A9422D284D934416AFE66C717F00A506550D330639F53A9` |

R492 使用的旧产品树 SHA-256 为 `B5C0ED99F0C87507E1B8D5DF7E48B96EDDD69DCD57908C0A2CF5D057404B5404`，projection manifest 为 `6BD1867A037CD2F30888A217E44F732A2B769D8E8EC801365E1B5FBB433D1CD3`。下一轮必须产生不同且重新绑定的产品树。
