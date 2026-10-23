# R17：真实付款、续期与到期（进行中）

`machine_id: pc-20260924rtuf-f11af23c08`，观察截至2026-10-23T00:15Z。EXT 为 `D:/workspace/ck3-living-artifacts-20261022`。本场尚未完成，不授续期、自然到期、恢复成长、冷加载或发布资格。

## 冻结来源与启动

c19 `0b96283d7d3eed696ffca6ddb3ac2f3459651776` 仅在 c18 上增加声明的初始 fixture 印记输入；正式57文件与 c18 相同，不夹入最新主线 host/native。a28外置产品清单使用hold10800/timeout12000，保持212自然日上限、7保存、1200调用和5项业务断言。配置、Prepared、runtime与原a24均未覆盖。

新卡为 `EXT/environment/storage-timer-a28-20261023-a01`：单份own D5GiB/C2GiB、other D512MiB/C0，截止2026-10-23T23:45:49.521031Z。原a26未来预留被串行替换，旧卡保留；fresh双trigger实际0，服务→readback→真实producer存储校验通过。没有删除资产或将候选回收算为空间。00:12:10Z精确三域为881466700 B；随后核得本场媒体11379433 B，原9MiB估计少1942249 B，合计修正为892846133 B，仍低于本场5GiB。保留原 `EXT/environment/storage-r17-own-snapshot-01-20261023-a01/snapshot.json`，补正于同目录 `media-correction-a01.json`；场次继续写入，后续保存需重新观察。

公共allocate `20261022T235020545328Z-allocate` 实际分配 `pc-20260924rtuf-f11af23c08--living-artifacts--R0017`，keeper a28于23:50:25Z就绪。23:51:08Z后台原生probe确认Steam offline/true，随后bound preflight实际0，public run `20261022T235111186915Z-run` 启动。实际CK3 PID13076、出生1792713085.5974245；host3652，actor31254、generation1、初始date_raw53144328。原游戏、host、public、keeper与保存服务仍在运行，不提前报告退出码。

## 已观察的首两份保存

| 保存 | 实际日期 | 装备 | 等级/XP | 金币 | 威望 | 压制期限/chain |
| --- | --- | --- | --- | ---: | ---: | --- |
| timer-checkpoint-01 | 1066.9.15 | 否 | L1/92 | 248 | 2200 | 无/0 |
| timer-checkpoint-02 | 同日 | 是 | L1/92 | 223 | 2150 | 389437/1 |

两份Save与同日原生钱包一致，首次实际扣25金、50威望；第二保存压力8。初始Save确有 `xalw_feeding_imprint`，类型flag、raw identity为null、值 `primary_armament`。这是声明的fixture输入，不是喂养动作或90日持久化通过。两份producer原wait均0；原件与melt分别约71MB/104MB，现有保存守卫保持。

库存回调于00:01:02Z保留原生预意图拒绝，Root没有追加通用库存查询。新原图与同尺寸坐标工具仅打开一次库存，延迟原图实际显示5件宝物、★目标402及空武器槽，随后交由原冻结adapter原生装备并独立读回。人工审阅为 `EXT/environment/r17-inventory-root-review-a01.json`；canonical点击回执为 `EXT/media/r17-inventory-open-a01.png.json`。

00:15:00Z实际原生快照为自然第16日，无active event；尚无第三保存。后续必须等真实第60日窗口、同日实际扣45金续期及真正renewed04，再等旧期限、自然到期和后一个月成长。冷加载只能消费该实际renewed04及完整来源，不能借用R16压制保存或历史已消费profile。

## 保存服务时限维护

既有ignored operator服务原固定等待7200秒，现支持显式 `--wait-seconds`，缺省7200保持，本场传12000；没有改冻结SDK、公共请求或游戏动作。原22项回归、两个完整模块strict及12项参数/原期限循环回归实际0，无Save或游戏调用。服务源码SHA `655d2d348bfd18d1f9332632ac784ec295af000b31014b0f83d931af3c3cc0e3`，小回执 `EXT/environment/checkpoint-service-timer-wait-a01/result.json`。它属于操作包维护，没有持久CI覆盖信用。
