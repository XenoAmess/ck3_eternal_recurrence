R0138 已补到同一原版存档、同一次受管运行的前后两个暂停状态原图与原生读数。日期为 1066.12.14 → 1066.12.15，仅推进一日；actor 29829 / Army 18 / combat 16777218 / province 2633 由实际原生 snapshot/control 绑定。before 公/native revision 4/3，after 8/7；每幅图后另有同暂停帧 snapshot，人工等待之后也重新查询 snapshot/control。47 项原件事实检查全部通过，最终 cleanup inventory 为空。

| 项目 | 前态 | 后态 |
| --- | --- | --- |
| 原图 battle topcounts | 893 / 1603 | 827 / 4106 |
| 原图相对军力 tooltip counts | 827 / 1546 | 740 / 4047 |
| 原图与原生 control 战宽 | 1480 | 2220 |
| 原图基础战宽 / 森林 | 1645 / 90% | 2467 / 90% |
| 原图小数字行（未在此解释含义） | 294 / 312 | 350 / 353 |

本轮 trace 原正文 phase captured、flags 0、7 records；Army 22 的 join-width 3 个边界、join-full-entries 2 个边界和单日 checkpoint 合同已通过独立分类。七条 phase 的 full_mutable_transition_bundle_complete 仍为 false。原版战斗面板下方仍裁切，UI actor/army numeric ID 没有声称可见，hook 瞬间没有声称与 UI 同帧，whole G2 保持 false。真实图片只作本次 scoped supplement，不改写旧失败 attempt、旧 source/DLL 或历史 350/365 口径。

事实回执：[R0138-readonly-facts-verification-a02.json](R0138-readonly-facts-verification-a02.json)，SHA-256 30ACB193768029AD329EC5547A3CA99ED3B42A830593235632A84B4BC9361057。
trace 回执：[R0138-independent-trace-facts-a01.json](R0138-independent-trace-facts-a01.json)，SHA-256 0F4451CAB32179344E2E3F7A926B94AA54B7A26CC140CFECBEC5FD1C1D380942。
直接原图观察：[R0138-direct-original-PNG-observation-a01.json](R0138-direct-original-PNG-observation-a01.json)，SHA-256 E0106401EF323703BF754BCE758F7B231BDF0C28791AC749B22BA6038B5E4091。

这不是视频 1× 完整人工审阅或 signoff；没有外部发布或 OneDrive 操作，也没有接收 master 内容。
