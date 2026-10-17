# R196：R01普通战争新T0研究核心闭合

来源机器`machine_id: desktop-3fevhd2-1c74096080`。Root实际决策时间`2026-10-17T02:22:35Z`，source`611bc985ae95f477dd7314df11f8602cd1e595f3`、native a33；R196运行PID36072/create134366756638003884/gen1/episode`native-31254-2bac783421ef`、actor31254、CK3 1.20.0.4/build25734779。本文不将这台机器当时的安装、Steam、部署或运行资格外推给阅读者机器。

Root已按原R01卡采用这次普通Robert谱系的新军事T0：正常来源链、真实活跃war4、可控原生Army、同帧完整读数、实际目标/周边点和正常保存。不是重新1066开局，也不是把R195 control改名为ABC。[Root决策原字节](evidence/episode04-r196-r01-ready-t0-12004/root-research-decision.json)也保存在下列单份无损归档内，研究从7/14增至**8/14（57.14%）**；R01不在业务R03–R13的11张中，故业务仍**5/11（45.45%）**，合格动态**0/11**、正式ABC**0/3**。研究接受不是视频审阅或human signoff。

## 同帧军事输入与选择

Root在R07基线前的暂停零日窗口执行8项只读：full Army18 strengths、typed commander、private cash、独立war4 occupation、2644/2645/2619三次native preview和末尾独立snapshot。起止F为native:3/public4/native3、raw53148192，实际actor/episode/位置不变。完整Driver11,163,208B、SHA`f4112efd6481162da25dfdd1171e85605ea21cd913578a14a1fa11de618e4897`只保留一个压缩member；MCP compact summary不是full DATA。

现有`evaluate_episode04_ready_t0_12004`实际返回`military_t0_frame_ready=true`、`normal_t0_saved=true`、`loss_sampling_ready=true`和`missing_inputs=[]`。Army18对应signed CArmy18，实际统帅31254，21ArRg/21DATA完整，1173/1195兵，stock/cap300/300，钱包raw25804687/scale100000。合法空DATA角色保留；未要求满员或低stock，也没有为T0执行Move/Halt或自然日。

| 采用项 | 本次实际证据 | 边界 |
| --- | --- | --- |
| 共同目标2644 | 完整war4 occupation的holding2195/county2191、holder45449、territory defender，未占领无siege；available route2635→2645→2644 | 没有实际抵达或ETA |
| 陆路节点2645 | 独立available route2635→2645 | 是A直达路线前缀，不能称已证明C的不同路线；resupply=false |
| 当前补给候选2619 | 自持holding2232/county2231、holder31254、attacker，未占领无siege；available path，native resupply eligible=true、loaded gain2000000/Q100000，limit6122/usage0 | 是当前条件输入；未观察抵达或stock增加，不授B两点growth |

2619实际路径为2635→2634→2633→2627→2626→8753→2629→2630→2631→2624→2619。该snapshot四支敌军当前都在2624；其中16777228的目标是2619，真实route为[1036,1038,8651,2619]。没有整路controller/occupation连续证明，也没有本包的native actual-contact/projected-threat horizon，因此不保证未来安全通过、到站或stock上涨。原R01只要求识别当前合法目标和可用周边点；这些真实风险不被改成额外的未来B门槛。

原R01允许本战争无可用海路时，在同战役另一真实合法移动窗口做现金卡。本文不发明海目标、海边类型或登船结果。R07/R08费用、B两处actual stock增长、完整C路线、三次独立coldload和90日结果仍独立。

## 保存与来源

本次复用identity已完成的新正常保存，没有再Save或覆盖identity guard。checkpoint与已有独立episode seed的实际原件metadata同为73,689,226B、SHA`274dea9f86a62c4a4963b603ccc5b07932c3fdca8442cb53661af2cff5a1eaaa`；原save响应20,336B、SHA`8869ef10fc45cb5ed43c54131b69de99dd3b9fb8e1a7ba45b26f26eb4eb81dda`，与本F日期/actor/episode相同。归档包含原identity、save响应、保存关系manifest、prepared/environment manifest、bounded header及Root实际决策，**不包含73MB存档**。

原R0171正常Robert key Start来源和29829错误期望的显式纠正继续保留；历史人物1128和runtime31254不混用。旧source card当时的机器安装未完成语句仍是原历史记录，不能覆盖R196 actual资格。original绝对路径仅为原机来源标签，便携回放不会访问它们。environment manifest也不被改称独立queried loaded-feature manifest。

## 跨机只读回放

[单份无损solid XZ原件](evidence/episode04-r196-r01-ready-t0-12004/r196-r01-originals.solid.xz)、[逐member offset/精确SHA索引](evidence/episode04-r196-r01-ready-t0-12004/source-index.json)与[回放器](evidence/episode04-r196-r01-ready-t0-12004/verify_portable.py)共同保存原响应字节、一个完整Driver、Root决策及语义input绑定。回放器只在内存中解压和验SHA，调用仓库现有pure consumer并核对原actual结果；不读原盘符、不解压展开件、不加载save、不需要CK3、SDK或桌面。纯consumer实际import闭包按相对文件pin核对，不对全仓增加source gate。压缩使用Python标准库LZMA2/preset7-extreme，16MiB字典；这不是可加载存档包。

```text
python -B -X utf8 docs/ck3-native-ai/evidence/episode04-r196-r01-ready-t0-12004/verify_portable.py --repo . --output NEW_VERIFICATION.json --verification-machine-id ACTUAL_OR_UNKNOWN
```

一次离线回放结果只证明封存证据的精确字节与现有pure consumer一致；Root闭卡决策仍是来源机器当时的事实。不得因此声称阅读者机器安装/Steam离线/native部署/运行/大save可读已经合格。现有研究plan在实际F和R196真实operation window上绑定并通过check/render；该绑定记录创建于采集之后，不冒称事前审批或授新live窗口。

存储沿统一1.0.0策略：同shared128MiB池中的本lane总限512KiB；只有一个压缩archive，没有另存11MB展开Driver、save、EXE、视频或截图。小合并证据180日复核，派生封包helper48小时复核，不自动延续大存档保护。
