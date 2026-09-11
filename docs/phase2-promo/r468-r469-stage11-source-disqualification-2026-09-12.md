# R468/R469 Stage 11 短验收与来源淘汰

## 结论

R468/R469 已完成一次且仅一次、绝对上限为 10 游戏日的 Stage 11 后继验收。`f14220f2488acad3b64613501a0415fb7fdc1a8b` 对只读快照换代竞态的最小修复得到实机验证：第一次 Workforce owner 查询收到 `ZhongGuo workforce owner snapshot changed or is not ready` 后，runner 没有提交游戏输入，改取新快照；后续查询成功，连续重绑计数恢复为 `0`。

该存档仍不能提供 Stage 11 验收。它从 `date_raw=53313360` 推进到绝对截止 `53313600`，未出现 `zg361we.360`，Workforce provider 始终没有 owner、AL case 或 portfolio 身份。运行因此按硬上限保留 RED，Stage 11 仍为 `NOT_EVALUATED`。这个输入的 Stage 10 用途已在 R467 淘汰；本轮又永久淘汰其 Stage 11 用途，不得再次重放或延长窗口。

T0 P1 保持 `6/9 = 66.7%`。未完成项仍是 Stage 10、Stage 11 和代表性终态 cold restore；P2 最终宣传视频继续 `LOCKED`。

## 冻结输入与 Operator 绑定

- exact build：CK3 `1.19.0.6`；`ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- production tree SHA-256：`84443728419E390024936809778C98D4BF4B529747FF776DE0F2FD4DC97E58CE`。
- 输入存档：`Z:\ck3_mod_rewrite\_runtime\p2r357_endgamesource_state\profile\save games\autosave.ck3`，`101,827,548` bytes，SHA-256 `F7A3AC56E1CEC7B6CA7CC449B9160E087779BCD503A8A6A647241AF9931CB3B6`，起始 `date_raw=53313360`。
- 运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage11-near-source-r468-r469-f14220f-20260912`。
- activation：`3,917` bytes，SHA-256 `9C948A5D3617F9F699643DC8FA45B968411B7FDDFACD3BA56C983849E8AEE6DD`；target profile：`7,790` bytes，SHA-256 `5DE8551542B23E1F209182436DE82BA80EB94F8DA5835E07DC86EB94A62E092D`。
- direct preflight：SHA-256 `3740B4E33CEA14461E169AE1E93A86FD5F6ECA2CB9E71A737B9D5CD7D4E57139`；MCP preflight：SHA-256 `60F648F4FF472E85CCDC3C2E9D5FC3838BDAAA3E065CEEB6C8C9EF56CC7C06C7`，全部检查 GREEN。
- Operator target：`local-interactive-operator-r468-r469-p1-stage11-near-f14220f`；job ID `2b08b615-6451-4491-8298-29707d39b8d5`。

## 单实例轮次

- 旧轮次 R468 为 frontend warmup，PID `134516`。它在 `12.701 s` 到达认证 Frontend，随后 `tree_gone=true`、`cleanup_proven=true`；确认清空后才启动下一实例。
- 当前轮次 R469 为唯一 gameplay PID `209980`，connection generation `1`。全程没有第二个 CK3 实例。
- R469 停于产品 RED 后由 Operator 执行受管清理。canonical cleanup 为 `33,100` bytes、SHA-256 `3CE3ACB78D3F5C40DEDDBD33263D2C0F890B9E6D1ABF139007E3C3ABC2BC4F51`；managed cleanup 为 `34,739` bytes、SHA-256 `044EB67B75EB9D7E31AE42DF4C27F02B572B931D3AFFB9A6817012B7EA47D7F0`。两者均为 GREEN。
- 当前轮次 R469 与旧轮次 R468 均已终止；CK3=0、Operator MCP=0，端口 `12433` 已释放。

## 实机证据

R469 在 `.390` 后第一次 Stage 11 provider 调用遭遇旧轮次发现的快照换代返回。证据账本记录：

- `attempt=1`；
- `stale_revision=8`；
- `date_raw=53313408`；
- `state_mutation_submitted=false`。

runner 随后取得新快照并成功查询。最终 `stage11_consecutive_query_rebinds=0`，证明修复只处理读绑定，没有吞掉失败、提交选择或改变业务后置条件。

在起点与截止点，provider 都只读到 Central subject `30317`、cycle `4`、case `3`；以下 Stage 11 身份始终不存在：

- `zg361_we_al_owner`、AL subject/cycle/case/state/active/revision；
- source owner/subject 和 P2C/AL serial；
- portfolio closure、status、cycle 与 terminal 字段；
- `.360` receipt；
- Central `stage11_status`。

最终 provider 为 `status=available`，但 `readiness.ready=false`、`terminal=false`、`unavailable_reason=workforce_owner_identity_not_bound`。这表示只读查询服务可用，而目标业务身份尚未在该世界状态中建立。到 `date_raw=53313600` 仍没有 `zg361we.360`，不能把它解释成 Stage 11 产品失败，也不能把缺少终点解释成通过。

主要冻结件：

- RED：`live-artifacts/terminal-stages-red.json`，`1,031,901` bytes，SHA-256 `09A0D388B6D400996CE133CB5599AA721362DE27148BB977AF63DFCFF266E63D`。
- loader error scan：`11,076` bytes，SHA-256 `92BDC988B5BA58673286270A5339C8677E5D85D9F8397365500679F3AFEBE869`。
- 截止 checkpoint：`101,794,783` bytes，SHA-256 `41950848E416EC8A232DF13FE9E7448324E6F690C880D1B46D6F57B551F1D1F7`，仅用于保存失败现场，不可作为新的 Stage 11 source。

## 后续边界

后续 Stage 11 只能使用离线证据先证明已存在 `zg361_we_al_owner`、active AL case 和 portfolio/source identity 的冻结存档，或在其他必要实机工作自然抵达 `.360` 时现场冻结。没有这种证据时不得再启动 CK3 猜测来源。

本轮未改公共 MCP capability/schema、DLL、游戏文件、启动配置或加载顺序，open_kaishek 不需要代码同步。只读 rebind 逻辑构成可复用 Operator/runner 资产；本轮没有新增接口。最终宣传视频锁未触碰。
