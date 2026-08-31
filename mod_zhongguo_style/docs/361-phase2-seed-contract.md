# 361 二期 MCP-only 存档种子合同

状态（2026-08-31）：runner 能力已实现，固定种子合同为 **ready**；是否真的能由
当前版本加载仍须首次 MCP-only 实机给出 GREEN。这不是 production-live 证据。

## 为什么需要固定种子

二期正式批量验收不能使用 OCR、坐标、lobby 导航、旧一期 scenario 或
acceptance-only 测试决议进入地图。因此 runner 只允许 `native_session` 的
`continue_last_save` 路径，并在创建 native driver 与 lifecycle supervisor 以前完成
不可变种子校验。`-continuelastsave` 的既有实机结论仍适用：目标 bytes 必须至少
物化到隔离 profile 的 `save games/autosave.ck3`；本 runner 同时写入根目录
`last_save.ck3`，二者逐字节相同。

权威机器合同是仓库根的 `tools/zg361_phase2_seed_contract.json`。它固定：

- source profile、相对/绝对存档路径、bytes、SHA-256 与 mtime；
- CK3 `1.19.0.6`、EXE SHA-256、两项 enabled mod ID，以及来源
  product/fixture tree SHA-256（后两项只作 provenance）；
- paused/map-ready 状态、`date_raw`、native CharacterID、历史角色 `han_8052`；
- 两个隔离安装槽和 `native_session_continue_last_save` 启动方式。

安装成功后仍不能只信文件合同。首次 paused MCP snapshot 必须再次精确匹配
`date_raw` 与 native CharacterID；结果写入 `04_phase2_seed_loaded.json`。任何差异都
是 RED，不得回退视觉判断。

## 2026-08-31 本机候选清点

共找到四组唯一 save bytes；每组保留的 `autosave.ck3` 与 `last_save.ck3` 相同。

| 来源（均位于 `Z:\ck3_mod_rewrite_process_assets\zg361`） | bytes | SHA-256 | product tree / 报告 |
|---|---:|---|---|
| `phase2-worktrees/.../zga_20260830_191131_7e82d061_native_state/profile` | 52,902,730 | `98687d21fe816a4a42d1d6bef85cea9d8a0ed9e74d53cdeadf653b0d3a57ecb3` | `ddac4703...` / GREEN |
| `promo/captures/zga_20260830_0930_clean_2fa2ac8_mcp_native_state/profile` | 52,779,998 | `6b583d73d7a4cc1e5c17fcbc4da329900cf7b235f2de1afce099571dac6420fe` | `450e0abc...` / GREEN |
| `promo/captures/zga_20260830_0651_current_cdda2f5_mcp_native_state/profile` | 52,758,400 | `3e6fd8a54541cd260701cf702d060a3fd839b9c3ee305a2261d512b74db11424` | `450e0abc...` / RED |
| `promo/captures/20260829-071346-core-live-take02_userdir` | 53,001,534 | `be9b76bfd6b9c927cf63c85930e8b094f9b633f3c5c1b0676b8b31bbf4dbdab1` | `4c43a339...` / RED |

最新候选的 save、顶层 `report.json` 与 `evidence-index.json` 哈希仍与合同一致，
并作为当前 bootstrap seed。它有两项必须诚实保留、但不应凭空升级为安装门禁的
provenance 限制：

1. 它产生于 product tree `ddac4703...`；2026-08-31 18:41 对当时施工树做的一次
   只读 bootstrap 得到 `bc9b37ff...`。CK3 存档本来就应能随相同 mod ID 的更新加载，
   且目前没有旧树存档无法加载的实证。因此来源树只记录 provenance，绝不要求与
   当前代码逐字节相等；当前树由本次 bootstrap digest、加载后 mount inventory 与
   loaded-feature manifest 验证。
2. 该 autosave 不是 typed `save-checkpoint` ACK 的产物。报告能证明真实宋帝
   `han_8052` 曾映射到 CharacterID `32904`，也能看到最终 `date_raw=53147016`，
   但只能按文件时间相关联，不能证明这两个字段属于这份 exact save bytes。
3. 更早三组候选的 product tree 更旧，其中两份顶层报告本身为 RED。

因此当前合同为 `ready / blocker=""`。安装阶段校验 save hash/size/mtime/header、
exact game/EXE、相同 mod ID、source report/index 哈希、来源树 provenance，以及
source report 中 `han_8052 -> CharacterID 32904` 的真实角色绑定；**不比较来源树和
当前树是否相等**。任一实际安装条件不符时，`--phase2-live-batch` 会在创建 native
driver、supervisor 或 CK3 进程以前写 `00_phase2_seed_install.json` RED；纯
`--preflight` 会在一次性临时 profile 中执行同一 dry-install 后清理，全程不启动 CK3。

## 加载后的判定与替换条件

本合同声明 `date_raw=53147016 / CharacterID=32904`，但旧 autosave 没有 typed
save-checkpoint ACK，故日期只是待验证假设。首次加载后必须先通过当前 mount 与
loaded-feature manifest，再由 paused MCP snapshot 精确核对 date/player；不一致就
立即 RED，不得 OCR 猜测或偷偷换存档。

若 CK3 实机证明旧 save 无法加载、date/player 不符，或当前功能所需状态确实缺失，
再用真实角色和 typed `save-checkpoint` 捕获新 seed，冻结新的 save、report/index、
game/EXE、mod IDs、source trees 与 date/player。没有这类实际故障时，不得仅因普通
开发改变 product tree 就反复废弃种子。synthetic 正负回归覆盖：来源树与当前树不同
仍可安装、来源报告真实角色绑定、矛盾 ready/blocker 拒绝，以及 load 后 date/player
不一致 RED；真正的 production-live 仍必须由新的 exact-build 实机 artifact 给出。
