# 当前子女材料源与 Python 消费（CK3 1.20.0.4）

2026-10-11 源码交付：`current_child_relation_materials_v1` 使用既有暂停态 family job 与相同查询的所选子女输入；严格解码、capture 和决策输入投影均保留该可选字段。状态为 **research / SOURCE_ADOPTED_NOT_RUN**。最高用户指令已取消新测试、导入、编译与实机执行，本包没有申请 GO，也没有回放既有 Guardian 5/19/9/21 资格。

## 实际源码路径

1. `bridge.cpp` 从既有 `child_inputs` 的 available/partial 行取各 `character_id`，保留完整 signed32 位模式为 uint32，复制给既有 Guardian job。成功复制空行列表时可得到已绑定空列表；失败复制保持未绑定。
2. `ck3_12004_current_child_relation_materials.hpp` 逐个所选 full ID 调用拥有副本的 generic peer carrier，再调用 named-material projection。`guardian_factory_discovery_job_v1.hpp` 输出可选 `current_child_relation_materials_v1`，沿用原 before/after/reclaim/completion 资格。
3. `validate_guardian_factory_create_inputs_v1` 先沿用原 command/request/native revision/date/played/heir/completion 校验，再解码该字段。完成的集合与同查询规范化 `child_inputs.rows` 的 uint32 ID 顺序完全一致；partial 输入行仍可提供已选 full ID，不额外要求所有子叶可用。
4. `capture_with_connected_driver` 在返回值中保留严格解码后的字段；`project_guardian_family_decision_inputs_v1` 独立深复制它。没有新增查询，也不重算 native relation 或教育结果。

## 字段含义

顶层 `roster_bound` 描述所选输入的绑定，`collection_available` 描述逐行集合是否完成。完成集合不等同于每个 peer 或 named-material 观察均可用。原生异常分支可能留下未完成 ID 副本；该 unavailable 外壳不被解释成已知空集合。completion 未通过时，原生输出 bound/collection false 与空 ID/行列表。

每个子女保留其 full ID、raw address 与 `resolved` / `known_null` / `unavailable` 状态。peer 行保留物理顺序、重复 full ID、raw material QWORD、可空 lookup/observed full ID/tag/address 及独立身份资格。已观察的零值与不可读的 null 保持不同。

`guardian_named_material.named_material_present` 是 generic peer 材料对当前 named descriptor 的源投影：available true/false 均为可见事实，unavailable 保持 null。材料 true 可以同时具有 known-null 或 unavailable 的角色 witness；不要求所有 peer 身份解析成功。材料 false 不证明 `Character.HasGuardian` 缺席，known-null peer 也不证明 guardian-null。本包不赋予 guardian 角色等价、已任命教育者、教育 fallback、自然 C8 触发或 action 成功结论。

## 精确源交付

生产文件共 9 个：26 peer carrier、25 named material、48 focus readonly、52 bundle/job、55 child helper/Bridge、59 strict/capture。Bridge 仅包含 55 的具体消费 hunks；不覆盖完整共享 Bridge，也不包含 authored case 或旧首包补丁。

- 原生 job：`8dee65c8c6f5a9252ca7403c2a504c5e99dfe010fe05ed70b9d8b3bec5c251e7`
- bundle：`3292d0e147473ea0c53a0f62d65fa9c52c28e60ef94412d8426e5e58045c2acc`
- peer carrier：`1675608170c6c2b065b329042e58f759b40591b484e0f8b9ec1d73218e762d58`
- named material：`4a275fb07134e7f56d6ae3e6a05a4cdb4653acd82ad7d5ca0e62be66631519a0`
- Python strict：`e67d3f04d405e3d90808d506ab1cf5db5ca5a8553e4985cb2e8e6a3d491d99f1`
- capture：`e9e680fd94923c2dc5937cbc7aa7820bcae071b6e04b5e98cc3359dd1fa7bc0e`

外置交付根为 `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-59/background-g2-offline-20261011/guardian-child-materials`。`ROOT-G2-CURRENT-CHILD-PRODUCTION-ADOPTION-MANIFEST.json` 与 `patch-current-child-production-nine.diff` 固定所有生产源、当前 preimage 和 patch。原首版 Python a193/68e postimage 是本次增量基线；Person 独立包保持原样。历史 lower-relation 9/21 资格仍仅覆盖当时的分支，不外推本新字段已验。

存储使用原 59 共用 4 MiB source allowance，不新增预留；活跃源 review 的复核期限仍为 2026-10-11T08:41:22.843427Z，无自动续期。


## Root integration

Recorded 2026-10-11T06:21:46.771176+00:00. Root adopted the nine production files into master and preserved
the actual Bridge hunks. Patch line endings were adapted to the repository.
The root receipt records the actual repository bytes:
[ROOT-CHILD-MATERIAL-SOURCE-ADOPTION-20261011.json](D:/codex-ck3-background-spill/native71-continuation-20261010/ROOT-CHILD-MATERIAL-SOURCE-ADOPTION-20261011.json).
The native build and physical SDK were not changed. Exact archived CK3 is
1.20.0.4 / Steam25734779, executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

```mermaid
flowchart LR
    A[Same-query selected living child full IDs] --> B[Owned native job]
    B --> C[Raw peer inventory and typed identities]
    C --> D[Named material presence]
    D --> E[Existing serializer and strict decoder]
    E --> F[Capture and decision input projection]
    D -. role equivalence unproved .-> U[unknown HasGuardian and selected educator]
```

The next functional dependency is the actual child court-owner and educator
selection/action source. Generic material false alone cannot select a fallback.


## 2026-10-12：普通同查询材料接线源码采用

Root采用三Python文件的ordinary材料入口：已启用private family且有state root时，用一个独占临时目录向原family QueryNative提供sidecar路径；从该同请求完成的原生导出经既有严格validator取`current_child_relation_materials_v1`，交给现有education needs。没有额外query/RPC，也没有调用capture wrapper或保留每轮完整command-result副本。八项完成标志、必需nullable error键、request、暂停前后native revision/date/played/heir、PID/generation与所选子女顺序均沿原资格检查；available、unavailable、legacy absent分别保留。generic witness不能升为已任命educator。

Python最多读4MiB+1并拒绝超限；这是读取上限，不是Native sidecar物理写入上限，实际运行仍受任务整体容量门禁。临时目录正常退出即回收；进程被终止留下的残件按通用策略复核，不宣称自动GC已部署。本次源码已审阅，未运行测试或实机；冻结SDK87/f9仍保留旧普通入口，本增量待后继SDK采用。M6仍partial。


## 2026-10-12：教育材料与总军事值源码接线

Root逐hunk采用Provider V4原生owned DTO和Wiring05 SDK：原成功family查询的同请求导出独立携带`current_child_education_provider_inputs_v1`，保留完整子女roster、重复出现位置、25项特质membership、目标文化参数`better_ward_education`的true/false/null与culture full ID。原before/after、回收、request、实际build、revision、date、played/heir门禁保持；8项完成标志与原可空error仍须通过。当前输入异常不能转成已知空名单；特质membership必须按catalog严格递增，拒绝乱序而不排序。

SDK新pure validator精确校验17个顶层字段与13个行字段，在复制前限制该leaf为64KiB UTF-8 JSON；缺席或null仍为unknown。孤立非null叶不能被legacy早返吞掉。普通transport分别附加教育与generic材料，education needs只读投影两者的独立来源。没有新query、RPC、rank或readiness；实际导师、Rite教育键、education_type/progress仍为null，`m6_inputs_complete=false`与`guardian_role_equivalence_qualified=false`保持。

正式教育脚本的`better_ward_education`检查位于`scope:educator`，不是由参数名称推断的child scope。当前Provider所读同名参数明确属于child文化，只保留该目标的事实，不能替代实际educator的文化输入；guardian相关字段继续null。Source06的15路复核尚未找到权威educator producer，新增外置文件0B。

另采用`total_martial_callback_v1`：通过既有actual4 total-skill绑定读取请求secondary actor的总军事值，保留完整target身份、两次一致采样、原始有符号数值（包括0）、before/after alive及角色bookend。该5-key可选字段与原raw skill及教育表达式来源独立，不能据此更改原教育评分。三处源分别为request技能header、ordinary interaction实现与strict Python decoder。

本批只有源码采用与独立静态审阅，没有运行测试、fixture、FIRST或教育业务重验。冻结SDK87/f9与Native86不含本批增量。后继native owner closure需按实际共享header枚举：Bridge323/492/493三项编译，保留Native86的324/Runtime504及其597成员archive，仅DLL重链；本条是源依赖结论，尚未执行后继构建。M6保持partial。

采用回执：[Provider V4与SDK Wiring05](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-PROVIDER-V4-SDK-WIRING05-SOURCE-ADOPTION.json)、[Martial04](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-MARTIAL04-SOURCE-ADOPTION.json)。来源仍受原4GiB范围和2026-10-12T16:47:28.264315Z复核期限约束，未续期。
