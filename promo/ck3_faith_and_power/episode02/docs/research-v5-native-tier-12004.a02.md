# Pilgrim tier semantics: exact 1.20.0.4 addendum

Machine:4-8e1c2f1861. Observed UTC:2026-10-21T20:17:17.382366+00:00. EXE SHA256:98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518. Offline static research only; no game/provider/Native execution. a01 files and their then-unknown conclusions remain unchanged.

Source tier blocks accumulate, without pre-fold differencing:XP0..49 uses root;50..99 uses root+50;100 uses root+50+100. Rite/culture blocks apply independently when the actual parameter is present.

30E7980 initializes an empty level;30E9480 creates each level separately;30EA9B0 parses that node. Conditional callback2882470 handles parameter and forwards other fields to2303A70. At2303E92..BA the numeric value is parsed and directly stored in the current block. Conditional blocks also start empty. Actual trait postload30E3D30 checks tracks, threshold ordering/range and parameter validity. Complete28811A0/28812A0 helpers validate IDs and log diagnostics, without subtracting tier values. Runtime30E49D0 merges root then every attained threshold through30E7A10;2303244 adds matching IDs.

| Contribution |XP0..49|XP50..99|XP100|
|---|---:|---:|---:|
|Unconditional travel speed/safety|5/5|5/5|5/5|
|Culture prowess, if prowess_from_religious_traits|2|5|8|
|Track AI-zeal modifier contribution only|0|10|25|
|basic_pilgrimage_rewards piety multiplier|+.05|+.15|+.25|
|Basic learning|0|1|3|
|Basic zealot opinion|5|15|35|
|Basic different-culture opinion|0|0|5|
|mandatory_pilgrimage extra piety multiplier|+.35|+.75|+1.15|
|Mandatory extra zealot opinion|5|25|65|
|Mandatory extra clergy opinion|5|15|25|
|Mandatory extra same-faith opinion|5|5|5|

These are isolated trait contributions. Encouraged/local-rites doctrine enables basic only. Ordinary mandatory doctrine enables BOTH basic and mandatory, plus its own-.25 piety multiplier:these listed sources sum to+.15/+.65/+1.15. Mandatory Hajj enables basic and mandatory_hajj, not mandatory_pilgrimage;listed trait-plus-doctrine totals are-.20/-.10/0. This Hajj example concerns pilgrim, not the separate hajjaj trait. Other virtue/perk/artifact modifiers are excluded. These additive multiplier contributions are not complete monthly piety income.

Direct add_trait initialization is closed too. Registration5D4340 selects factory2D2A570;effectVT48638B8+B0 reaches2D2B9C0 then28BA350. At28BA706..732 each new track is inserted with a QWORD zero. Both28CE030 allocation paths fill the new slots with that value. Already-held trait guard28D6920 rejects before insertion, so duplicate add_trait does not reset XP. Later trait hooks/on-actions may still modify state;their final XP is not claimed.

Exact source pins and body bounds/hashes are in the adjacent pilgrimage-v5-native-tier-12004.a02.json. Source comments were not evidence for aggregation. Missing-limit else_if compilation defaults remain unknown and outside this addendum.

Root review correction (2026-10-21T20:21:31Z, same machine): source root ai_zeal=5 is a separate trait AI field. The table 0/10/25 covers only attained track-modifier contributions; combined AI total and behavior remain unqualified. Original external a02 is unchanged; current JSON records this correction.
