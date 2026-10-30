# 本轮验收不用的Workshop本地缓存回收

- `machine_id: desktop-3fevhd2-1c74096080`
- 记录时间：2026-10-30T15:39Z；实际删除时间见下表。
- 授权：用户本轮明确要求删除Steam下载中本轮验收不用的mods，再继续验收。
- 范围：可重新下载的本地载荷；未退订，未改变ACF、用户目录外层`.mod`或playsets配置。

## 实际完成

| 项目 | 精确删除根 | 文件 / 空目录 | 已删文件分配量 | 原命令终态（UTC） |
| --- | --- | ---: | ---: | --- |
| Azur `2471250202` | `C:/SteamLibrary/steamapps/workshop/content/1158310/2471250202` | 2,295 / 76 | 2,329,661,520 B | 15:20:34.374916700Z–15:20:58.624091500Z，原wait 0、未超时 |
| RICE `2273832430` | `C:/SteamLibrary/steamapps/workshop/content/1158310/2273832430` | 4,419 / 194 | 1,379,529,064 B | 15:24:04.646604500Z–15:24:48.061569800Z，原wait 0、未超时 |
| 合计 | 两个精确item根 | **6,714 / 270** | **3,709,190,584 B，约3.45 GiB** | 均为2026-10-30 |

这是文件实际分配量合计。RICE最后回执观察C卷可用49,632,161,792 B；回执显式记录并发空间变化不归因于删除，不能把卷前后差值全算作本轮释放。两个旧载荷现已不可读取，精确Plan、逐批删除日志和原终态仍在；不制造同名替代证据。

## 保留边界

本轮C36、RT100、formal56及三文件fixture/profile只装载product+fixture，无这三个候选ID依赖。旧的非当前`Initial playset`仍保有82个enabled Steam项，Azur、RICE和POD三个候选都在该历史配置中；“本轮不用”不能外推为“所有playsets均无引用”。原配置保留。

五个长期禁回装ID `2291024373`、`2993056101`、`2962333032`、`3192256710`、`2224124758`在以下三根的15个0 B普通文件保护占位均保全，未修改其屏障：

- `C:/SteamLibrary/steamapps/workshop/content/1158310`
- `C:/SteamLibrary/steamapps/workshop/downloads/1158310`
- `C:/SteamLibrary/steamapps/workshop/temp/1158310`

POD `2216659254`**未删除**。最初整批计划在内部120秒有限扫描边界失败，原wait 1（2026-10-30T15:10:28.085617900Z–15:12:30.341591300Z）；只有12份部分清单、共12,000叶，无完整顶层Plan，零删除。后继逐item计划仍保留120秒边界；严格Maven编译和真实临时fixture producer→executor资格均通过，未用超时放宽替代完整清单。

执行前后台Steam读回仍为offline，RICE的新鲜观察为2026-10-30T15:23:50.344774Z。本次未切换在线。本记录只证明本地清理，不证明新的容量准入或Game业务验收。

## 实际证据

证据根：`C:/ck3-dynastic-esotericism-20261024/resume-product-a20/core-a30-administration/workshop-local-cleanup-a01`。下列Pin已实际读取并重算；Azur/RICE Plan分别创建于2026-10-30T15:18:15.036616800Z、15:23:12.463158800Z。

| 相对证据根的文件 | bytes | SHA-256 |
| --- | ---: | --- |
| `PLAN-AZUR-a01.json.gz` | 3,513 | `979ef65ee067993776054b34bd64fd6657e09ed78f33be0365bae4c8782d43d4` |
| `EXECUTION-AZUR-a01-ACTUAL.json` | 564 | `df3c565316eb8b3a28768d04b596e57b3d314d914f647c1744218ea3c0c39315` |
| `ROOT-EXECUTE-AZUR-a01.original-wait.actual.json` | 1,900 | `954447d8111096ec540ebca302709dba0e8633812447b15129c8aa7893b7dfd6` |
| `PLAN-RICE-a01.json.gz` | 7,483 | `6c6e5287fc7e19afcfc80c692e3377e677caaa24617d8520e8282b8cbcbe4e9b` |
| `EXECUTION-RICE-a01-ACTUAL.json` | 565 | `8b090aeca34c0b74d33c1976a35e7856b690ed37f37979e05f8e3ad614b873db` |
| `ROOT-EXECUTE-RICE-a01.original-wait.actual.json` | 1,899 | `7338f4b8cb5e3d7e0f5b9102a28ae90b45b48f41f82b34c1dde90c2f20ac8ad4` |
| `ROOT-ACTUAL-WORKSHOP-PLAN-a01.original-wait.actual.json` | 1,484 | `7a477a411c48ed669b8879f6abd37b5ecdce21b315e7305ba8316432b7c50c5a` |
| `QUALIFICATION-a03.json` | 573 | `eb0f391797b8d037cdec95ba54a7408118bbf498f8d999bc0f0a1d7f8092da76` |

另一次四份旧facts stdout退役不计入上表：`C:/ck3-dynastic-esotericism-20261024/resume-product-a20/operations-core-a41/source99-a01/capacity-support-retirement-facts-a01/ACTUAL-a01.json`，4,740 B、SHA `72f5a2078212012514e1961a9025d09fe7ef84d33d849f6eb7e347191bdbe9f7`，观察2026-10-30T15:12:12.171086500Z。其支撑包计费净减少311,296 B，physical credit及reservation delta均为0；旧路径原字节通过保留的ZIP及映射读取，不算Steam释放量。

接续状态见[恢复执行记录](../handover/2026-10-29-dynastic-esotericism-resume-progress.md)。本维护记录未改Source100、冻结运行图或代码，未执行Git操作。
