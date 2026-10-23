# R17：真实付款、续期与到期（进行中）

`machine_id: pc-20260924rtuf-f11af23c08`，观察截至2026-10-23T01:24:22Z。EXT 为 `D:/workspace/ck3-living-artifacts-20261022`。五份真实保存已确认首次扣款、续期扣款及旧到期事件保留新期限。本场尚未完成，不授自然到期、恢复成长、冷加载或发布资格。

## 冻结来源与启动

c19 `0b96283d7d3eed696ffca6ddb3ac2f3459651776` 仅在 c18 上增加声明的初始 fixture 印记输入；正式57文件与 c18 相同，不夹入最新主线 host/native。a28外置产品清单使用hold10800/timeout12000，保持212自然日上限、7保存、1200调用和5项业务断言。配置、Prepared、runtime与原a24均未覆盖。

新卡为 `EXT/environment/storage-timer-a28-20261023-a01`：单份own D5GiB/C2GiB、other D512MiB/C0，截止2026-10-23T23:45:49.521031Z。原a26未来预留被串行替换，旧卡保留；fresh双trigger实际0，服务→readback→真实producer存储校验通过。没有删除资产或将候选回收算为空间。00:12:10Z精确三域为881466700 B；随后核得本场媒体11379433 B，原9MiB估计少1942249 B，合计修正为892846133 B，仍低于本场5GiB。保留原 `EXT/environment/storage-r17-own-snapshot-01-20261023-a01/snapshot.json`，补正于同目录 `media-correction-a01.json`；场次继续写入，后续保存需重新观察。

公共allocate `20261022T235020545328Z-allocate` 实际分配 `pc-20260924rtuf-f11af23c08--living-artifacts--R0017`，keeper a28于23:50:25Z就绪。23:51:08Z后台原生probe确认Steam offline/true，随后bound preflight实际0，public run `20261022T235111186915Z-run` 启动。实际CK3 PID13076、出生1792713085.5974245；host3652，actor31254、generation1、初始date_raw53144328。原游戏、host、public、keeper与保存服务仍在运行，不提前报告退出码。

## 已观察的五份保存

| 保存 | 实际日期 | 装备 | 等级/XP | 金币 | 威望 | 压制期限/chain |
| --- | --- | --- | --- | ---: | ---: | --- |
| timer-checkpoint-01 | 1066.9.15 | 否 | L1/92 | 248 | 2200 | 无/0 |
| timer-checkpoint-02 | 同日 | 是 | L1/92 | 223 | 2150 | 389437/1 |
| timer-checkpoint-03 | 1066.11.14，第60日 | 是 | L1/92 | 231.77073 | 2154.13220 | 389437/1 |
| timer-checkpoint-04 | 同一暂停日 | 是 | L1/92 | 186.77073 | 2104.13220 | 389527/2 |
| timer-checkpoint-05 | 1066.12.14，第90日 | 是 | L1/92 | 191.39497 | 2106.19830 | 389527/2 |

两份Save与同日原生钱包一致，首次实际扣25金、50威望；第二保存压力8。初始Save确有 `xalw_feeding_imprint`，类型flag、raw identity为null、值 `primary_armament`。这是声明的fixture输入，不是喂养动作或90日持久化通过。两份producer原wait均0；原件与melt分别约71MB/104MB，现有保存守卫保持。

第三、四保存于同一暂停日期对比，实际再扣45金、50威望，压力10→18；期限由389437延至389527，chain1→2。第四份producer于00:47:49.460210Z实际wait0。第90日的第五份producer于01:08:17.478186Z实际wait0，解析结果保留新期限和chain2，装备及L1/92未变；初始印记此时为null。它证明旧到期事件没有清除续期，不替代第180日的自然到期检查。

库存回调于00:01:02Z保留原生预意图拒绝，Root没有追加通用库存查询。新原图与同尺寸坐标工具仅打开一次库存，延迟原图实际显示5件宝物、★目标402及空武器槽，随后交由原冻结adapter原生装备并独立读回。人工审阅为 `EXT/environment/r17-inventory-root-review-a01.json`；canonical点击回执为 `EXT/media/r17-inventory-open-a01.png.json`。

01:24:22Z实际原生快照为自然第126日，无active event或pending interaction。仍须等第180日自然到期及后一个月成长；原游戏、保存服务和keeper继续运行。

Save4后精确用量见 `EXT/environment/storage-r17-own-snapshot-02-save4-20261023-a01/snapshot.json`（SHA `7676bf012fcef0996f96ed0a6653e988fc76d90c0780911f76ad6f6934aebbb4`）：三域1463592600 B，实际媒体10文件11379433 B，own合计1474972033 B，5GiB余3893737087 B。下述第二通知的原report早于采样，已包含其中；不重复加计。此为该次采样，后续输出仍须重核。

## 原生中断及冷加载准备

第52日的 `bookmark.1070` 实例3已先保存原生窗口、双方角色、10个saved scopes加root及三个实际显示选项，既有c19策略27项检查成立，选择显示第三项一次。原生选择3→null后，独立同暂停帧确认窗口消失；军队before/after均unavailable，不授250兵或claim效果。只读post曾使用不存在的工具名，公共队列在派发前拒绝；保留失败，再用实际 `ck3_take_snapshot` 读取，没有重放选择。离线来源与既有规则精确匹配，见 `EXT/environment/r17-event-0001-offline-analysis-a01.json`（SHA `829cda106b255019fe0033c6c5e50218898fa0c477236329248f489431fb8d9e`）。

第73日婚约通知实例117440607按既有 `arrange-marriage-reject-only-v1` 策略单次拒绝，native rejected与独立通知消失分别记录；本机四份原版来源及两份冻结策略SHA与R16已核来源一致。离线回执为 `EXT/environment/r17-interaction-offline-analysis-0002-a01/result.json`（SHA `0e85b2a40396b8135b3b2ae717173ed8f92e308a0659a2f4d7ed6c9ff87d8064`），不授婚姻变量或其他效果。

a27冷加载准备只引用真正renewed04的retained `original.ck3`，71482465 B、SHA `bd7cedc41a3bcf3c38ee84a011276dc3beddbca704efeea4e674bb2587f70ea7`；八项来源闭合，未复制该原件。现成cold入口先公共prepare消费完整saved_campaign，再以显式Prepared公共plan，最后preflight，三项原wait均0。未执行不读取case_inputs的unbound plan，未allocate/run或授予冷加载资格。新formal-only profile63文件2079161 B，完整小包2306698 B，计父other512；见 `EXT/environment/cold-public-prepare-r17-a27/result.json`（SHA `a8a6a695de30bacff57b01ffb921f0376d4af99efe3b81e688a63af903026e76`）。

## 保存服务时限维护

既有ignored operator服务原固定等待7200秒，现支持显式 `--wait-seconds`，缺省7200保持，本场传12000；没有改冻结SDK、公共请求或游戏动作。原22项回归、两个完整模块strict及12项参数/原期限循环回归实际0，无Save或游戏调用。服务源码SHA `655d2d348bfd18d1f9332632ac784ec295af000b31014b0f83d931af3c3cc0e3`，小回执 `EXT/environment/checkpoint-service-timer-wait-a01/result.json`。它属于操作包维护，没有持久CI覆盖信用。
