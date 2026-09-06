# R151 管理者恢复的疫情通知中断（2026-09-07）

R151 从 `ed3b8caef3d2ebdac375a84db15bca21f307148d` 冻结源构建
`phase2-full-release-r151-ed3b8ca`。正式投影为 1,031 files / 32,278,871 bytes，产品树
SHA-256 为 `196e557e06ffa09ef488c819168f16237f5466089ab0d8087ac3f977398e4205`；投影 manifest
SHA-256 为 `dae4f8e6f3b4a4d0ac903164b9abaa594ecde6cebeef67eb7dca69bf2dce2b75`。它包含已闭合的
Workforce/Endgame 中文文案修复。`Z:\p2m151_pre2_a\preflight.json` 为 GREEN，SHA-256
`537da667172c9110f4730c2d424c86bf6b6100c32e639beddfcaabea67e2a8e8`。

实机 loader 完成 303/303，fatal 为 0；最终 CK3 PID `116360`、connection generation `1`、
restart count `0`。管理者 CharacterID `32904` 保持 alive。在默认 5 速清理 active B1 时，runner 于
`date_raw=53148360` 暂停在原版 `epidemic_events.1100`，因为它尚无精确中断合同而 fail-closed；未到
clean review boundary，也未生成 manager seed。

原版 1.19.0.6 的 `game/events/dlc/ce1/epidemic_events.txt` 证明该事件是领地出现疫情的通知，不代表
玩家角色已经染病或死亡。事件打开前的 immediate 已登记 epidemic 并写入县级疫情效果。R151 的 MCP/native
current-event context 将 root 绑定到玩家 `32904`，并给出完整 saved scopes：

- `epidemic: epidemic`
- `province: province`
- `infected_county: landed_title`

原生事件定义有三个 option；R151 没有御医，因此实际只显示两个按钮，native indices 为 `(0, 2)`。native 2
会设置 30 日 `seeking_epidemic_treatment` 并调度 `health.3001`；native 0 不创建后续事件链，仅在玩家同时是
governor 且有 governor trait 时执行原版 `increase_governance_effect = -2`。验收恢复因此固定选择 option 1 /
native 0，并在提交前绑定玩家、日期窗、三个 typed scope、完整可见按钮映射与单次出现上限。任一形状漂移仍 RED。

专项 interrupt 测试 normal 与 `-O` 均为 9/9 GREEN；seed runner normal 与 `-O` 均 GREEN。R151 manager
recovery、runner report、cleanup 的 SHA-256 分别为
`38f2be0a6c9eadbbbb098e31fa6d9b4b66d1726c62e6afdfc9b0071bced45c0c`、
`a1cedc38887c32e14e5052169bb47ea2ce18ed639b7c67ebd1a7f122d5b7de62`、
`fbaa96b71d450d0a927b4bd97b212cc754796ee6d28b4f9c616638333d97937d`。cleanup GREEN，最终 CK3
inventory 为空。本轮没有加载性能 RED，因此无需新增产品 effect 拆分；现有用途分片上限继续强制执行。
