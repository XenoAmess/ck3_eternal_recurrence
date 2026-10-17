# R197：县 P 的 relation 原调用已接通（CK3 1.20.0.4）

执行机器 `desktop-3fevhd2-1c74096080`，场次
`desktop-3fevhd2-1c74096080--vanilla--R0197`，source
`85eb547cca4fddaec4b8a89ec9dd203e6935299c`。本次从 R191 普通 S0 独立载入，
日期53148192，actor31254；不是 R196 入海后态。PID37596、creation FILETIME
134366861170573998、generation1、episode `native-31254-534b7fc4f2ab` 由本场
身份原件绑定；preview 响应本身只带 generation/episode/revision，不独立证明 PID/FT。

本次只提交一次 `preview-move-army-18-to-2634`，expected revision4。
实际 Army18 从2635到2634，剩余路线只有这一边；queried snapshot `native:3`、
native revision3。`county_entry_condition_v1` 和 P trace 可用，最终 condition=false。
本次没有 Move、自然抵达或县物理扣兵观察，**R04 physical positive 仍为 false**。

| 同次 P stage | 实际 relation receiver / actor FullID | pure pair / War sample | 原生实际返回 |
| --- | --- | --- | --- |
| source P | 34960 / 31254 | pair WarID4，selected War 无 fallback，原始+358 byte0，aux=null，direct gate=true | relation ALtrue，P true |
| target P first | 34232 / 31254 | pair WarID=-1；selected War、fallback、+358、aux 比较均 null，direct gate=false | relation ALfalse，P false |
| target P second | 未调用 | 无观测 | null |

两个 relation leaf 均是 `native_original_relation_entry_return_12004`、available、
call_count1、argument match/same thread/FullID 前后稳定。实际 bridge caller RVA
6616941 是 bridge 内回址，不能充当固定 native P caller；各 P stage 的 native
回址仍按其自身字段消费。receiver 是原调用读出的对象 FullID，未据此改名为县法理
领主、控制者或占领者。

这次新增的是 **实际 hook → native DTO → Python typed consumer 的 live wire 证据**。
原 A08 q 中 live wire=false 是其 cold 资格的历史边界，原 q 不改写；本场原件另行补证。
旧 R182 已把失败缩到 target P first，本次进一步给出了真实 receiver、actor、pair
WarID 与直接 War 支路。target 的 -1 是合法哨兵，后面的 War null 是原支路未取，
不是读取失败；不能为这些 null 再增加无用采样或路线扫描。

`unknown_or_inputs=true` 和解释器 `unknown_or_result=null` 均原样保留。直接 War
sample=false 与实际最终 ALfalse，并没有把 `2C09580` / `2C09780` 两个 OR 子调用
的实际入参、是否到达和各自 AL 发布出来。下次施工只考虑在已有 P/relation scope
内观察这两个自然调用，保留原返回、短路和 frame fence；不在当前会话热改。
最窄来源与 consumer 边界见证据目录内 `OR-NATIVE-NEXT.md`、
`OR-PYTHON-BOUNDARY.md`。

这不能授予邻接 Q、县 caller、实际扣兵正例、自动选路或视频 clean span。其余机器可
复用原件、字段合同和结论；本次安装、运行或 hook 实际成功仅证明该机器这一场状态。

精确原件、身份桥、一次离线判读和 SHA 索引见
[source-index](evidence/episode04-r197-county-relation-12004/source-index.json)。
ZIP 内原件逐项保持原字节；不把90KiB本机资格或 EXE/DLL 复制进这个小包，资格完整
原件以 source-index 中的外置 pin 引用。本文件为待 Root 合入的增量候选，不改历史
[relation core](episode04-county-entry-relation-core-12004.md) 的当时未知边界；本场事实
是对其 public DTO 尚未观察描述的后续补证。
