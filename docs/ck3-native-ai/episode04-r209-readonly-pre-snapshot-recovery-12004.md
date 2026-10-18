# R209：仅对 native 尚未开始的前置快照失败重取一次

本专题的来源是 desktop-3fevhd2-1c74096080 上 R209 的实际错误，源码基线65ce6ae5e55c0e8a855bebb6da3a1ccef08a711f，CK3 1.20.0.4/build25734779。它不是新的实机成功，也不补 R05 正例。

两天实际 exact-day 完成后，第三天 before 的 `ck3_query_army_strengths` 请求 Army[0]、expected_revision11、observed_history_full_v1，在2026-10-18T07:51:55.995903Z→07:51:56.527625Z返回明确 RED：worker=pre_snapshot，native/reader=not_started，pre_snapshot/paused/map_ready=0，submit/wait/reclaim/entered/native_returned 等仍为-1。这证明该次请求未进入 native 查询；它不证明游戏真的取消暂停或没有地图。之后独立清理快照成功。

原544字节 gzip、1142字节解压 JSON 及 SHA 见 [source-index](acceptance/2026-10-18-r209-r05-pre-snapshot-recovery/source-index.actual.json)。原错误保持 RED；代码不改写为成功，也不覆盖旧请求。

最小修复由公共 FullArmyResultClient 识别**完整且完全相同的诊断结构**，要求已完成的错误行、正确查询工具、full profile 和 continue_on_error。它只附加带原公共 control 路径的未开始证明，自己不重取。R05 沿既有 readonly revision-drift 恢复通道，在独立 fresh snapshot 后核同日期、同 PID/generation/episode/actor、暂停、无弹窗和同 Army owner/location，再以新 control ID 查询同 Army/profile，expected_revision 取新帧。第二次失败直接收敛，不产生第三次请求。

native 已开始、submit 改变、诊断字段缺失/变化、未知结果、超时、跨日/跨身份均不适用。Move、clock、initializer、Arm/Resume 不在恢复范围。整数0是合法 Army/CArmy fullID，不当作空值。

新便携 focused smoke 将真实 RED 注入公共 FullArmyResultClient→R05 call/sample，成功 native DTO/传输边界为 synthetic；生产 fresh-frame/target 守卫及 R05 normalizer 仍实际执行。一次 compound 的查询数：成功2，第二次同错2，native已开始1，未知1，跨日1。它不执行 SDK、native 查询或游戏，也不授 live 资格。

真实计时不支持“180秒都花在 full”：四次成功 full 的 tool 部分分别3.999012/4.542421/4.088608/4.246533秒，总16.876574秒。36个公共 controls 的起终跨度183.479066秒，tool 总计约36.70秒，多个 control 之间另有约3.5–4秒间隔；这不是对间隔根因的证明。

day1-after 和 day2-before 的 compact/source + paired after 均为 revision6/native5/native:5/date53147400。后一个重复请求约4.088608秒，至 gz 镜像落盘再约3.130012秒；它另生成15,456,358字节 normalized JSON 和294,701字节 gzip。只有同完整 frame、同 subject/coverage/observer fences 才能考虑复用；同日期本身不足，本修复不增加缓存复用。

明确可分离的后续小改进是让 R05 完整 gzip 镜像承担 normalized consumer 原件保存，条件式省掉公共 helper 的重复 pretty-JSON checkpoint；默认其他 consumer 行为保持。四件重复 JSON 合计61,545,339字节，原 native-wire range/proof 与 gzip 仍需保留。时间收益尚未单独测量，不把整个183秒当作可省空间；本包未改此行为，也未扩通用 observer/queue 框架。

最小 canonical smoke：

```text
python -B -O -X utf8 tools/test_r05_pre_snapshot_not_started_recovery.py --repo-root <repo> --temp-root <new external small scratch>
```
