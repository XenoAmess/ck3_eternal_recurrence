# 本轮验收不用的Workshop本地缓存回收

## 2026-10-30最终执行追加：三项缓存均已删除

`machine_id: desktop-3fevhd2-1c74096080`。以下为16:57Z后的最终清理状态；原15:39Z记录继续保留在后文，其中“POD未删除”是当时的真实边界，现由本追加更新。用户订阅、ACF、外层`.mod`及playsets配置不变。

| 缓存ID | 实际删除文件 | 已移除空目录 | 文件实际分配量 |
| --- | ---: | ---: | ---: |
| Azur `2471250202` | 2,295 | 76 | 2,329,661,520 B |
| RICE `2273832430` | 4,419 | 194 | 1,379,529,064 B |
| POD `2216659254` | 12,549 | 860 | 2,389,218,936 B |
| **合计** | **19,263** | **1,130** | **6,098,409,520 B，约5.68 GiB** |

POD精确根为`C:/SteamLibrary/steamapps/workshop/content/1158310/2216659254`。原执行2026-10-30T16:55:54.534836600Z–16:57:01.580601200Z，67.0461191秒，**原wait 0、未超时**。Root随后以程序独立读回三项根均不存在。POD本地原载荷现已不可读取；精确Plan、逐批journal和原始终态可查。三项是当前验收不用、可重新下载的缓存，不代表历史playsets无引用；旧非当前`Initial playset`的82个enabled Steam项及三个候选引用仍保留。

执行前后台Steam观察2026-10-30T16:55:44.272453Z仍offline。五个禁回装ID在三根的15个0 B保护占位及ACL均保全。POD执行后的C卷可用读数为51,820,036,096 B；回执仍明确`concurrent_free_changes_not_attributed=true`，不能将并发free差值全部归因于删除，也不把这项读数当新场容量准入。

A04仅将POD单项完整扫描上限设为180秒，其他项仍120秒；真实fixture producer→executor原0，验证POD-only180s/other120s及拒绝blind replay。旧120秒失败证据保留，不追认为通过。20份失败中间part已有限退役：manifest记载原保守分配量1,335,296 B，新manifest及actual共10,108 B另计，**不是已扣新元数据的净额，也不并入上表Steam载荷合计**；首尾样本、全部原wait、错误及成功Plan/ACTUAL保留。20份旧中间part路径不再可直接读取。

证据仍位于下文所列`workshop-local-cleanup-a01`根，新增Pin已实际读取、重算：

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| `POD-a04.json.gz` | 27,335 | `16b63970f759e23b14387d1bb4e8098f76639b9ec3c89b8829a6ff712302862d` |
| `EXECUTION-POD-a04-ACTUAL.json` | 561 | `d2ebfc098c9e5088afe9c55f5dba63ce373f4e38a0f8c8c48faddb4661876542` |
| `ROOT-EXECUTE-POD-a04.original-wait.actual.json` | 1,890 | `5902c7014c7e4fdbb22d2a8bf0066d7477e9548c4ca6f977d6a39f447d37fe75` |
| `RETIRE-FAILED-PARTS-a01.manifest.json` | 3,100 | `f3f61403aede2294fd59b3d0721802ae0456661e552cc948060e33c0d163a8f8` |
| `RETIRE-FAILED-PARTS-a01.actual.jsonl` | 7,008 | `1f65310255076a100a2e7aa3d611bebcaff20e0cea1a54f0f6f2169fc154cf9f` |

清理不等于业务验收完成。R43母档与独立Reader有效，整场仍ERROR；POD后的`SOURCE_ONLY / NO_GAME`闭场容量复核于17:12:03.909191600Z仍原1，无fresh、无新admission，无a64分配或新Game。完整物理/配额错误未保留分卷明细，不猜拒绝在哪一卷。

最终后台新观察：Steam fresh 2026-10-30T17:18:50.257408Z仍offline/true，原wait0、未超时；17:19:20.365513Z读回CK3进程空、三项根均不存在。`Admin/ROOT-FINAL-CLEANUP-OBSERVATION-a01.actual.json`为1,209 B、SHA `6618f068340d1f68cb0ca2d65b06d88d9776d6258a9b3e26f7edc4874877c5d3`（`Admin=C:/ck3-dynastic-esotericism-20261024/resume-product-a20/core-a30-administration`）。Cfree51,818,975,232 B及Dfree21,602,742,272 B仅为观察值，不外推准入；17:12完整容量拒绝仍保留。

## 15:39Z历史记录（原边界保留）

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

R43闭场、共享修复与CI主线见[修复及后继记录](2026-10-30-pre-product-seed-absent-profile-tail-repair.md)。本维护记录未改Source100、冻结运行图或代码，未执行Git操作。
