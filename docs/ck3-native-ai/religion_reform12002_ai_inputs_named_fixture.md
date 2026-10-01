# CK3 1.20.0.2 readonly AI reform inputs named queue

2026-10-01：正式 `permitted_executor_religion_ai_reform_inputs12002` 实际 owning queue 首次 `/O2 /W4 /WX` **1 combined case / 2 queued commands / 11 checks GREEN**。exact-build 为 1.20.0.2，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。

新 named fixture 复用[冻结 generic caller](religion_reform12002_ai_inputs_mailbox_fixture.md)的真实 backing/bindings。清空当前 header 中 generic 和全部其他 permit，仅新 dedicated field 指向 `ExecutePlayerReligionAIReformInputsMailbox12002`。两次命令都走真实 `TrySubmit → owner Drain → actual holder/context/per-member schedule → Finish → Wait/Reclaim → complete command_result`，没有 mock admission、手填 DTO 或追加 protocol metadata。

第一条命令的 actual holder 五项返回 ordinary/player-special/ordinary 三个匹配成员，各有实际独立 schedule，timer 为 -4/null/12。第二条命令的 holder 只有 nonactor 与 default 两项，返回合法 `observed_no_ai`、零 controllers 和实际 null-AI base schedule。所有 actual 输入与 generic case 一致。两份完整协议分别与冻结 generic packet **逐字节相同**，无需再次执行 generic/provider 矩阵或 SDK unit。

## 冻结证据

结果：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\ai-inputs-named\attempt-001\result.json`，SHA-256 `5c68b1739fdc89912298daac792681257afe373b2e5a63e77b9877cc12e8a4e1`。

同目录实际完整 raw packets：

- `wire/multiple-controllers.json`，SHA-256 `40712116527901eb9f251c666f3aa2b43933f3a715839210dd64d023e5b340be`。
- `wire/observed-no-ai.json`，SHA-256 `ef7323474d1d4a1601d25a7b9c431f637539697bba778595b8a6a2bd587b50dd`。

两份均为 `protocol_version=1 command_result`，actual leaf `result.player_religion_ai_reform_inputs` 的 schema 为 `ck3_12002_player_religion_ai_reform_inputs_v1`。actual snapshot_revision=701、date_raw=53175816、actor=50331652、owner capture epoch=3。gate observation complete 为 true，基础 `ai_status=not_supplied` 和 cache/timer null 保留；timer 单位为 `prepare_invocations`。

runner 只把冻结 generic helper 的外层 `main` 在 Z artifact 副本中改名，其内部已改名的 query12 main 不变。新的 named `main` 是唯一执行入口；旧 generic main、AI context/schedule/provider/query12 矩阵、R8 immutable 源均未执行或改动。当前 `main_thread_query_mailbox_v1.cpp` 与 `ck3_12002_query_mailbox.cpp` 两份共享源重新编译，其余 O2 production 对象全部复用。

receipt 保存全部 source/object/helper/header 字段清单与 raw packet hash。`ai-inputs-named/final-source-package.json` 精确冻结本包三份新 owned sources：named C++ test、Python runner 和本文；日/周增量字段在 `ai-inputs-named/report-fields.md`。

production flag 为 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1=1`。`XAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1` 仅 fixture 使用，不加入生产 DLL。需要显式复现时，以结构化 argv 在新 Z artifact 目录执行：

```python
import subprocess

subprocess.run(
    [
        r"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe",
        r"Z:\ck3_mod_rewrite\.task-tmp\g2src\ck3_autonomous_player\native_bridge\research\religion_reform12002_ai_inputs_named_tests.py",
        "--artifacts",
        r"Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\ai-inputs-named\manual-reproduction",
        "--generic-objects",
        r"Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\ai-inputs-caller\attempt-001",
    ],
    cwd=r"Z:\ck3_mod_rewrite\.task-tmp\g2src",
    check=True,
)
```

## Readiness

此证据新增 **static-ready readonly named AI input query fixture**。只证明 actual dedicated runtime admission 与完整 owning caller output；InstallEnvironment/copy/中央 Register/Populate/router 的 whole DLL 验证由 central 独立交付，本 fixture 没有执行安装过程。

`gate_inputs_observation_complete` 表示实际当前输入已观察，不预测 AI 将改革、下次改革日期或动作结果。没有 CK3、pipe、UI、Steam、战争研究、shared mutation 或 Git 操作，没有 live 声明。下一步由 root paused live 验收；root collector 统一提交新三源并合入日/周报告，已通过的矩阵无需再跑。
