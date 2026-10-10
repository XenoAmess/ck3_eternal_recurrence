# QOL R69：候选排序已观测，继承人查询范围缺口仍在

2026-10-10，维护范围仍为天朝二期以外原十项迁移，正式交付 7/10。本文不把部分业务事实或源码修改算作新的正式验收。

## R69 实际结果

Source17、administrative prepared-34、a170/R0069 对同一 `d_optimatoi`（title 1861、holder 30599）完成 OFF → ON → RESTORED 三阶段；候选始终为 human 29912、AI 37981。human 原始分数依次为 -93800000、-100093800000、-93800000；AI 为 9200000。每次切换后均合法关闭并重开同一头衔，取得新窗口引用及 revision，候选缓存与 native getter 一致；恢复时 GUI 开关为 false。

继承人画像打开后，调用 `ck3_query_ingame_ui_window_v1(window_kind=character)` 被当前 army-only 能力合同拒绝，未取得带 generation 的完整角色 ID。原错误保存在 `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/administrative_appointments--a170/R69-ORIGINAL-HEIR-WINDOW-QUERY-ERROR-01.json`（5953 bytes，SHA-256 `54ddcdb196bdbceda2536d2afb613db8c76c37e5a8c3fc530a494f0b8ed5e1ec`）。不能放宽 army-only 门禁或把画像、按键 ACK 当作 GetHeir 证据。

run=2、verify=2；保留的 OS exit=1，normal close=false、strict native zero=false、failure proof=false、lifecycle completed=false。14:46:29Z 已确认 CK3 和写入进程退出、allocator/keeper 结束、总线资源释放；这是资源关闭，不是业务或正常退出通过。实际回执 `ROOT-FIELD-RETURN-R69-01.json` 为 12392 bytes，SHA-256 `61969a650e1f33c6d8aeda0555f88975c4689faa5b64c81dbc479fa836895f17`，位于上述 a170 目录。

## 源码诊断及边界

在原只读 character-level 双采样合同中增加 `current_rule_allowed_candidate_tier_ordinal` 和 `candidate_tier`。后者按当前 1.20.0.4 原生 28AC690..28AC71C 的内存读取路径取值，包括 cached-tier=7 的首头衔分支、无 landed extension 分支、头衔完整 ID 校验；不可解析时返回 unavailable。原生资格、等级 floor、窗口/角色身份及池一致性门禁继续生效。

Python 合同允许旧 Source17 同时缺少两个新字段；新字段出现时必须成对、类型及取值合法，不可用时均为 null。新增两项 Python focused tests 实际 PASS（0.002s）。native focused source 共 14 cases，**尚未编译或执行**；没有新 DLL、没有 Source18。预估增量生产编译涉及 21 个对象，需独立磁盘预算后执行，不能把源码审阅写成运行时通过。

现有 campaign-root 的 first-heir 字段仅覆盖当前玩家持有头衔，actor-cached succession 也不提供任意目标头衔 GetHeir。当前目标 holder 30599 不是玩家 29912；不能挪用这两个接口抵扣本项。下一步只补当前目标所需的有界只读能力，先证明实际语义，再进行一次增量构建。

## 可并行继续的原验收

PAM 阴性 prepared-36（30807 bytes，`b12d084f2b74d7e597bf31a3f8ff56607101241637125ee9702524307b1c7ccf`）和阳性 prepared-37（30808 bytes，`737b987e791f74aba111fc70c5efb0e03c3264c19e97e961c109c537aeecad22`）已按 QA27-08 修正嵌套玩家字段，仅完成 prepare，业务未运行。两者在 `C:/workspace/ck3-upgrade-20261010/resume-qol-02/source17-pam-{negative,positive}-nested-publicprepare-{36,37}/prepare/prepared-case.json`。既有 Source17 UI、ransom 及 RMTM/fixed361 输入仍可使用；本次 additive 源码不修改冻结 Source17。

## 历史清理与验证

按当前 storage-retention-policy 1.0.0 清除五个旧入口中 277 行不可达尾部，详见 [清理记录](maintenance/retired-mod-acceptance-entry-tails-2026-10-10.md)。保留统一公开入口、helpers、preflight 及全部守卫；候选的 12 项检查已通过，13 份当前 metadata 未发现 Main 这五个完整 runner 的消费 pin。冻结 Source16 的源码索引仍指向独立树，无需为此重复准备或重编译。

本轮 a170 关闭后再生缓存实际删除 3848 files / 163260624 allocated bytes；累计实际删除 624360 files / 33431644520 allocated bytes。另有文本无损压缩，单独计算，不叠加为删除量。历史完整报告候选尚待用途解除及执行回执，不能提前计入释放量。

此前 master `22bec93f45f60a523bc48ebe16abb1fe767be0f9` 的 [CI 38058365503](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38058365503) 实际 66 success、20 skipped、0 failure；该结果不外推到本文后续提交。QOL 1.1.1 尚未上传，Steam Change Notes 仍为冻结草稿。
