# R152 管理者恢复的神道访客中断（2026-09-07）

R152 从 `0ecba409bea674ea3cc72297a1896d9f5eb87f6e` 冻结源构建
`phase2-full-release-r152-0ecba40`。正式投影为 1,031 files / 32,278,871 bytes，产品树
SHA-256 为 `196e557e06ffa09ef488c819168f16237f5466089ab0d8087ac3f977398e4205`；投影 manifest
SHA-256 为 `a4811730f2b6f133954beabe710540179065d34a55d3403e30b5af7ab9da3aed`。
`Z:\p2m152_pre2_a\preflight.json` 为 GREEN；实机 loader 完成 303/303，fatal 为 0。

实机使用单一最终 CK3 PID `192464`、connection generation `1`，默认 5 速恢复 active B1。它先按既有
精确合同消化 `tribute_mission.1002` 与 `tribute_mission.1005`，两次 drain 均 GREEN。随后在
`date_raw=53150712` 暂停于原版 `tgp_movement_events.0150`；未知事件门禁按设计 RED，未发送任何选择。
管理者 CharacterID `32904` 保持 alive。本轮随机序列没有再次生成 `epidemic_events.1100`，因此不把上一轮
新增的疫情通知合同写成已完成实机复验。

CK3 1.19.0.6 原版源码将该事件定义为天朝政体下的神道僧侣来访。MCP/native context 绑定 root 到玩家
`32904`，并给出完整的两个 saved scopes：

- `other_ruler: character`，CharacterID `29646`
- `monk: character`，CharacterID `16783528`

原版共四个 authored option。R152 不满足 diplomat-only 联盟路线的 trigger，因此 native index 0 隐藏；
三个可见按钮严格映射到 native indices `(1, 2, 3)`，而 snapshot authored option count 仍为 4。native 1
写入永久改宗折扣并使 zealot vassal 降低好感；native 2 启动随机外交 duel，可能改变僧侣信仰或好感；
native 3 无 RNG 与后续事件，仅接纳僧侣，并给玩家中等外交经验或威望、给派遣者有限好感及按 trait 结算
stress。验收恢复因此固定发送 authored option 4 / native index 3，不能把“第三个可见按钮”误写成 option 3。

新增合同要求日期在产品观察窗内、玩家/root 一致、两个不同且非玩家的 character scope、恰好两个 scope、
可见 native `(1,2,3)` / authored count 4 及单次出现上限全部匹配，否则继续 fail-closed。专项 interrupt
测试 normal 与 `-O` 均为 10/10 GREEN；seed runner normal 与 `-O` 均 GREEN。该用途测试分片至此封顶为
10 个场景，后续新事件测试另建用途分片。

R152 manager recovery、runner report、cleanup 的 SHA-256 分别为
`36284973e6ae2f451ffc1fb39bf3afa5a0823b6e7cb05fb57b50ef2af5a4b776`、
`06f4cb6c97fd48579efe5f5b6a92a4f143c90b7792b1cc8c86b8bd4e28874622`、
`4ba446528eb8cba690741b2b0fec50e415b2e327347a1faf47cbfac7add50919`。cleanup GREEN，restart count
为 0，最终 CK3 inventory 为空。本轮没有新的加载性能 RED；产品 effect 的用途分组与每文件数量上限保持强制。
