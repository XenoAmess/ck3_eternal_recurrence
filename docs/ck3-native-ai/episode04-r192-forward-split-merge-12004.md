# R192：分军后的角色迁移与合军物理守恒（1.20.0.4）

本场已正常保存、退出与释放。它得到一次实际分军和随后一次未录制的合军，原录制控制器仍为 RED；R09 整卡未关闭，反向独立冷加载同 S0 对照仍待完成。

`source=60de49f61d23b9c3437af4544c3f12bb28445429`，a31；机器 `desktop-3fevhd2-1c74096080`，R0192，Robert 历史1128/实际31254。三帧都暂停在 `53146632`。Public Unit93 对应 Native CArmy85，两种 ID 不能当作相同。

|层次|F0|F1 分军后|F2 合军后|
|---|---:|---:|---:|
|全局已读33个唯一物理槽 current/max|1935/1935|1935/1935|1935/1935|
|全局缓存 current/max|1945/1945|1944/1944|1945/1945|
|所选物理队列|250/250|93为75，child为175|250/250|
|所选缓存|250/250|75/75＋175/175|251/251|

F1 child Public16777378/Native16777371。原 commander34232 留在93；实际 typed child commander 是36445。Army18 同时少了 ArRg65：DATA count0、cache1/1、Character36445、predicate=true、F8=65。其物理1185/1185、DATA、stock300、cap300、Dweight1185均未变。原严格 unrelated cohort gate 因该角色槽消失失败，不能回写为通过。

F2 child 实际消失、93/85存续、typed commander34232不变；新增 ArRg16777281 的 DATA count0、cache1/1、Character36445、predicate=true、F8=16777281。不是新增真实士兵。实际字段支持同人物三态关联，未观察创建写入口，不授实时 producer 因果或骑士成员身份。

所选四个 persistent16793863～16793866 的物理 current/max、DATA身份保持；F1和F2实际 guard138均1，CanReplenish/ChunkCanReplenish均false，prepared148均0。正式枚举含义仍独立于这些 raw 值。

实际合军输入 D=75、S=175，Q100000 shares=30000/70000；库存100/100的贡献30＋70=100，返回库存100、cap100。生产消费者匹配；不同库存阳性和上限截断均未取得，不能据此声称已实验辨别权重或 clamp。

录像为33.6秒/1008帧的 split partial，非计划120秒完成。四格审阅有原生 hover 遮挡；Merge不在该段，不能授完整清洁动作链、推进日或精确业务PTS。

[便携原件、精确来源和限制](evidence/episode04-r192-forward-split-merge-12004/source-index.json)。默认验包只需 Python 标准库：

```text
python -B verify_portable.py r192-forward-evidence.zip
python -B verify_portable.py r192-forward-evidence.zip --repo <exact-source-checkout>
```

第二条只回放已固定的小输入及原生产纯消费者，不调用SDK、不读取大Driver、游戏存档或视频。归档中独立 consumer 原源码保留本机取证路径，不能把其历史 CLI 当作跨机通用入口。本分析 owner 的大Driver读取为 F0=0、F1=1、F2=1；两帧采用同一 read_bytes 的 SHA与解析，没有先哈希后再读。
