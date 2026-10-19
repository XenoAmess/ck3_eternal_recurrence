# M1：Driver长期持久化热路窄审（2026-10-20）

CLOSED / SOURCE_REVIEW_ONLY。machine_id=`xenoamess-full-tower-eb9d2c1186`，本轮实读 `tools/ck3_live_run_id.py machine`；源观察UTC `2026-10-19T16:07:22.030325+00:00`至16:11:38.818493Z。本轮0当前/closed Driver正文、SAVE、Game RPC、benchmark、矩阵、生产源码修改；M7 Runtime/NativeDriver custody段不动。

Root报告closed Driver为19,641,271B、约day2504，本文没有读该文件或取得其SHA/历史行数/耗时，不将该总尺寸当成history大小。runtime提供C16准备复用的d804/src13冻结源码；其当时SDK尚未constructor，源码pin不能证明新C16已经写出相同性能结果。

## 真实热路：已缓存JSON编码，仍完整写文件

冻结 `bridge/native_driver.py`：

- `_record_command` L11143：成功且属于现有deferred-read-only集合的query暂缓保存；其余记录调用 `_persist_driver_state`。所以不是所有读查询都立刻写，失败/非deferred命令和各明确barrier仍可触发全量保存。
- `_encode_driver_state_locked` L11473及L11508，把当前metadata和完整command_history交给 `driver_state_json_parts`，L11526生成完整不可变bytes。
- `_persist_driver_state` L12021：write lock跨编码与原子替换，state lock下冻完整bytes后释放；随后把全部bytes交 `write_bytes_atomic`。并发新增query仍可重新置dirty，未改变该合同。
- `environment.write_bytes_atomic` L338：整个payload写入同名.tmp，再 `os.replace`；计时与非计时分支均如此，未添加fsync。CPU编码缓存不等于增量文件写入。

`driver_state_history_json.py` L13已经是 `ensure_ascii=False, separators=(",",":")`。head/tail每次编码；同history list的已有行bytes缓存，只编码新增行；新list、缩短或显式invalidate才重建，缓存上限256MiB。因此“每动作重新indent2序列化全部历史”不符合此冻结源码。无论旧行是否重编码，当前完整history仍参加整文件拼接和.tmp写入。若barrier频繁且history持续增长，单次拼接/写入仍随N增长；不能只凭单次短测保证30年1秒/日。

再次改compact在这条Driver路径没有新增格式收益。全局 `write_json_atomic` 虽保留indent2，Driver热路用的是 `write_bytes_atomic`；修改全局格式会波及其他文件，不能解决此热路。trace/UI原始回执的indent2也不是Driver history encoder。本文未从当前Driver测出各字段占比，实际压缩率与CPU节省均unknown。

## 一个可立即施工的最小改动：少复制一次完整bytes

仅建议下次常规源码更新、由NativeDriver owner在安全维护点改一行，本轮未apply：

```python
# 当前
return b"".join(serialized_parts) + b"\n"
# 候选
return b"".join((*serialized_parts, b"\n"))
```

两者逐字节相等，包括字段顺序、UTF-8内容与末尾换行；不改变JSON对象语义、锁、缓存可变buffer的冻存时机、dirty合同、原子替换或恢复格式。当前先分配整文件join结果，再为加换行分配/复制完整bytes；候选在一次join中直接包含换行。源码上能确定少一个N级临时bytes及复制，不能把Root报告的19,641,271B等同于每次精确N，也不能在没有timing样本时宣称降低多少毫秒。它不减少完整I/O，不能单独解决长期复杂度。未来仅需既有encoder边界下必要的精确bytes等价检查，不要求新业务矩阵。

## WAL已有实现，生产阻点也具体存在

实验目录README明确uninstalled/default-off。对src13精确检查：`bridge/driver_state_wal_v1.py`不存在；native_driver没有 `XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1` 字面量；native_session无该helper导入。不能把CI58实验或仓库提交当作实际SDK采用。

实验真正提供的是“冻结base+有界journal”，不是无限append文件：helper `publish_journal` L279每次仍canonical编码并原子重写整个journal，8MiB上限；单delta256KiB。可降低eligible连续日推进对完整历史base的反复写入，但barrier/容量会合并，真实收益取决于实际命令分布，本文没有采样，保unknown。

最小上线阻点不是缺一个环境变量：

1. helper尚未进入生产包，两份reader/writer patch必须针对当前generation重基。原 `load_native_driver_state_for_resume_payload` L1699只接受format1/2；实验active base故意封成format3，使老直接reader拒绝。需同时更新原生Driver恢复入口和native_session冷检查，不能只启writer后让cold路径读取旧base。
2. active journal跨PID采用被patch明确拒绝；SAVE/restore/非eligible/close及闭owner materialize必须维持完整v2 barrier与两文件提交/崩溃规则。这要与当前M7 custody交接共同维护，不能热改正在运行的SDK或盲清journal。
3. patch的 `life-advance` 通用成员资格比已资格的单日范围宽，会容纳尚未资格的多日名字；README已明确该缺口。route-horizon另有实际paused/24raw/一日/仅deadline/一tick/无overshoot/无事件交互的窄守卫。最小生产接线应只允许已证单日/严格route范围，其它沿现full barrier，不把generic名字当资格。

canonical consumer还要逐个接好：src13 `native_session.validate_cold_start_checkpoint_for_pipe` L1761直接json.loads，再交 `cold_checkpoint_validator.validate_cold_start_checkpoint_payload_for_pipe`（L34只收format2）。NativeDriver的format3在L1699返回None，不能让WAL损坏/缺base也沿“无恢复状态”继续；实验patch明确重抛JournalInvalid。

once状态不只在Driver：src13 L7608 `reject_unresolved_claims` 和L7613 claim存在检查禁止重试，原生调用前L7632先落 `claimed_result_unknown_no_retry`。实验 `materialize_closed_directory` 只产新目录v2 Driver，不迁这些claim/result sidecars；需沿M7 canonical custody交接，不能把materialized_v2当“所有未知动作已恢复”。既有 `consolidate_closed_pair` 按marker提交、`recover_aborted_activation` 只撤无已提交行header；不能用它清有行/损坏journal或once标记。

这不是要求新增存储框架，也不要求重做旧fault矩阵。先按当前writer/reader/custody合同把现有受限WAL接线做完整，保持失败/未知动作不重放；在真实正常日推进自然数据上取得实际append比例、full-barrier频率和耗时，才有依据谈长期收益。旧实验保留了对象值等价、key order/原bytes曾不等的历史事实；没有保留可用timing样本，本审不补速度信用。

## 精确源pin

S=`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src13/xar_autoplayer`；E=`ck3_autonomous_player/experimental/driver_state_wal_v1`。下表只读源码，不是任何Driver/SAVE正文：

| 源 | Bytes | SHA-256 |
| --- | ---: | --- |
| S/bridge/native_driver.py | 1620598 | db9f8fb05483146abe1bea7c00d5ec4c53e5fc6a9c370133ba7e8ff7ebedb3da |
| S/bridge/driver_state_history_json.py | 3584 | 1ad843c2347e2e1b07c007aa9dd45d4011baa70253b07f7a16695fab3dd1fc46 |
| S/environment.py | 58031 | 5d29d19d44c83a5425fb75b97ddb118a6c51a1e1f1f98184570850ad94a6a582 |
| S/native_session.py | 76078 | d41880fbaec6f7648822237cefae7db02d06fc86d790622742ea86631ddb94f8 |
| S/cold_checkpoint_validator.py | 4766 | d89180d9abbcffcd71a33387826b751e31ecd7709683576e35cbb5358d4509a3 |
| E/driver_state_wal_v1.py | 20272 | fdca7355377e957bbbcffcef509988e3f34f488ef3340256dfdf7214534303c1 |
| E/bridge-native_driver.py.patch | 15292 | f695f9c6a08688da15db51932b0a8ed7c74e1ec4ab66e9201c1f970b115304ac |
| E/native_session.py.patch | 1265 | 553029dd5acbc1f641cef3e409738b188e67abb9dab0571fc6ceba170bf54e29 |
| E/README.md | 4095 | 60d35a524be1242096a03a90c283398867bf4fc287e67ac7d24984e31046d3f5 |

本轮只新增本review，硬8KiB；实际bytes/SHA闭场报告。Root minor2MiB池下8KiB承诺卡 `MINOR2MiB-M1-DRIVER-PERSIST-SOURCE8KiB-COMMITMENT01.json` / `fc4ec95e9aa04d5be56e87470318474b05b8cd29b806c1cb4fd8e026e9cee26a`。producer_closed=true/future0/external0/allocatednull/physical_credit0；不改变旧code3/Native30额度或原期限。

