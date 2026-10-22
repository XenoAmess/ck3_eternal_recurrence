# 活武器：验收执行与结果合同

2026-10-22。本文配套[总测试方案](test-plan.md)和[内容矩阵](content-acceptance-matrix.md)，用于接入公共验收器和保存可核验结果。**当前入口为 `core_continuous` v3，七次实际保存后验与四档普通管理喂养的范围见[v3方案](feeding-shortcuts-and-core-v3.md)。R0008已启动，状态记为 `RUNNING_R0008`，尚不授予业务PASS或发布通过。**

这项启动事实属于 `machine_id: pc-20260924rtuf-f11af23c08`；原始host记录的启动时间为2026-10-22T10:46:26.850656Z。出处是外置 `D:/workspace/ck3-living-artifacts-20261022/live/pc-20260924rtuf-f11af23c08--living-artifacts--R0008/run-context-r8-a01.json` 和同目录 `native-report.json`；后续业务与终态以该场原始记录及单独结果报告为准，不从启动状态推断。

历史：v1在R0002因错误的固定runtime角色身份而BLOCKED；同场后续独立动作确认装备及两个自然日推进，第三天读回失败。随后v2引入当次身份绑定与三次实际保存后验，其制定时状态为待重新实机运行。来源机器、原件、失败清理及真实截图见[R2记录](runtime-r2-issues.md)，后续已发生范围另见[R7记录](runtime-r7-star-growth-and-interruption.md)。各旧场结果保持原件，不由v3追认通过。

## 1. 复用公共入口

后续仅从[公共六模式入口](../../tools/ck3_mod_acceptance.py)执行`plan / prepare / allocate / preflight / run / verify`。产品不复制host、DLL、启动器、屏幕keeper、正常退出或SDK下载。通用协议见[公共说明](../../docs/ck3-mod-upgrade-fast-validation.md)。历史文件中的固定本机路径不作为本产品运行参数。

已登记product key为`living-artifacts`、runtime_mod_key为同一产品身份；Workshop ID保持null。[公共产品清单](../../tools/ck3_mod_acceptance_products.json)的`core_continuous`使用[产品adapter](../tools/acceptance_adapter.py)和[v3合同](../tools/core_continuous.contract.json)，覆盖首阶段真实装备、自动月成长、卸下停经验及四档连续喂养入口。七次实际保存的原始状态与独立原生owner/equipped、材料库存身份交叉，不使用隐藏动态logger。普通管理决议通过原生MCP打开、选择和确认，之后由原生事件选项进入四档候选及具体材料确认；原宝物自选交互保留，尚不把接口可用认作实机喂养通过。详见[v3方案](feeding-shortcuts-and-core-v3.md)及[保存后验合同](checkpoint-observer-contract.md)。历史v2因没有通用宝物选择通道而将喂养记BLOCKED，原结论不改写；其他完整矩阵仍需各自实跑。`static-and-basicload`保留原配置，但空`required_startup`与未绑定`post_start`不能通过共享prepare，状态为BLOCKED，不能凭历史plan把它称为可运行。

登记前先实现真实adapter，提供`prepare_case / run_case / verify_case`，可提供`validate_contract`。配置冻结其path/config、initial_plan、startup mode/state_dir、预算、required_mcp_tools、normal_close及实际业务范围；所需工具必须已存在且source_build_ready，不用占位能力或空adapter满足形式检查。

## 2. 六阶段的职责与命令模板

共同四参数固定为`--runtime <本机共同映射.json> --products tools/ck3_mod_acceptance_products.json --product living-artifacts --case <实际登记case>`。早期`core_continuous`已执行不启动游戏的plan与动态加载检查；当前R0008的prepare、allocate、启动及实机结果须分别由前述当场原件取证，不能以早期检查代替。

```text
py tools/ck3_mod_acceptance.py plan --runtime <本机共同映射.json> --products tools/ck3_mod_acceptance_products.json --product living-artifacts --case core_continuous

py tools/ck3_mod_acceptance.py prepare --runtime <本机共同映射.json> --products tools/ck3_mod_acceptance_products.json --product living-artifacts --case core_continuous --case-inputs <当次输入.json> --prepare-output <全新外置目录>
```

后续沿用同一共同四参数，替换mode并追加真实输出：

| 阶段 | 参数/输入与允许的结论 |
| --- | --- |
| plan | 只描述选择及缺口，`NOT_RUN / NOT_ASSESSED`，不分配、不启动 |
| prepare | `--case-inputs`、`--prepare-output`；生成prepared-case并绑定正式投影/夹具/adapter等SHA，状态为`CASE_PREPARED_NOT_ALLOCATED_NOT_RUN` |
| allocate | `--prepared-case <prepared-case.json> --attempt <新attempt> --keeper-output <新目录>`；按公共实际链提供previous-live/previous-keeper/previous-release或首次bootstrap，存在中间释放时提供latest-screen-release；不可伪填“上场已闭场”。生成真实context并由公共流程分配机器+产品run ID，不另手工预分配第二次 |
| preflight | `--prepared-case`，分配后加`--run-context`；核EXE来源、manifest、能力、输入、预算等；exit0不代表启动或业务通过 |
| run | 同一prepared-case及run-context；准入后公共launcher/host调用一次adapter.run_case，最后执行normal_close |
| verify | 同一prepared-case及run-context；消费这场实际case、GUI和normal-close结果，不再运行业务；case_acceptance_pass、business_pass与产品发布结论分别记录 |

`allocate`的首次启动/历史关闭参数采用所绑定公共源码的实际合同；本方案不复制一套简化allocator。无法核对上一真实状态时先完成该状态核验，不拿其他机器的关闭回执代用。

公共Selection一次只选一个`--case`，没有`--cases/--all/--reuse-session`。当前`core_continuous`在一次run_case内编排首阶段四子项并分别记录，完整LW-G/F/T/I/A/C/X矩阵继续分阶段接入；最后由公共入口做一次正常退出。不能向多个公共run重复投同一已消费context来制造进程复用。

## 3. 现场与身份

启动前按当前[后台离线查询](../../tools/steam_offline_state_probe.py)运行：

```text
py tools/steam_offline_state_probe.py --receipt <当次新回执.json>
```

只接受新鲜`status=offline`且`offline_mode=true`及其实际来源/身份绑定。旧公共说明中的“离线画面/nonce/亲审截图”不覆盖2026-10-21新指令；不为离线查询激活、移动Steam或截图。不可用时保持启动未执行，继续独立离线工作，不自动切换Steam在线。

若实际选择的公共版本仍消费旧截图门槛，先在共享层完成后台回执合同接入并绑定当前context；产品不恢复截图步骤，也不另起一套launcher绕过公共入口。CLI参数存在不等于其历史画面语义仍可沿用。

实际run绑定machine_id、UTC观察时间、CK3 EXE SHA/build、PID/出生时间、pipe/generation、产品与原版来源、正式manifest、actor/date以及唯一run/attempt。使用公共受管流程取得本机唯一CK3/屏幕资源；GUI专属业务以实际控件和状态读回，MCP为默认，OCR不参与真值。

运行时需要保持clean frozen checkout时，候选代码和文档在外置runtime保全，正常退出及租约释放后再写回；不修改运行中的冻结HEAD来追认变化。纯Python合同热修只有在已加载mod/native/游戏状态未改变时可同PID/实例/generation继续；原始失败保留，结果未知动作不重复提交。

## 4. 测试输入与证据目录

后续adapter的case inputs至少引用：正式staging manifest、外置fixture manifest、角色别名到真实身份的绑定、物品清单、当前月度/季度结算定义、每子例预算、随机控制范围、启用内容registry版本以及case与要求的映射。fixture与正式产品分开，正式包不携带测试按钮或强制随机逻辑。

原生事件身份由实际provider合同提供；无原生唯一ID时，先定义并验证可保持来源唯一性的组合身份。不能用日志行号、通知标题或临时GUI index冒充真实事件。所有证据引用绑定自身producer和SHA，物品/角色64位身份用规范十进制字符串；未知保留缺失/合法null，不用0或空字符串补位。

外置attempt建议结构如下，仅是文件布局，不另造运行协议：

```text
attempt/
  inputs/                  # manifest、fixture、actor/item绑定与规则版本引用
  observations/            # 受影响对象的最小只读前后态、源事件和UI结果
  case-results.jsonl       # 每子例、每必要子项的结果
  checkpoint/              # 只有冷载/恢复真正需要的存档和身份摘要
  common/                  # 引用公共prepared/context/run/verify/close结果
  run-summary.json         # 已完成、失败、阻塞、未运行及实际范围
```

不为每个小例导出整个游戏；能复用同一真实源和快照的证据只保存一份，通过引用关联。关键前后态可以同文件保存，但必须能独立读回真实结果，不能只有被测函数打印的“已成功”。截图用于中文显示审阅和必要GUI记录，不替代材料消失、钱包或秘密状态。

## 5. 单一结果字段合同

验收目录已在[共享产品类型模型](../tools/living_artifacts_acceptance_model.py)使用 TypedDict/dataclass 和 Literal 分支实现严格 JSON 校验及序列化往返，目录中的63项仍为 `NOT_RUN`。下表描述逐 cell 的 v1 结果合同；核心 adapter 的整场 v2 结果是另一种明确命名的消息，不将旧整场 v1 回执自动迁成 v2。

| 字段 | 类型与语义 |
| --- | --- |
| `schema_version` | 严格整数1，所有结果分支必填；改字段时同步生产者、消费者与持久化解析 |
| `case_id` | 方案中唯一ID，如LW-G03；内容子项另有稳定`subcheck_id`，不混用公共case名称 |
| `status` | NOT_RUN / RUNNING / PASS / FAIL / BLOCKED / NOT_APPLICABLE；原始失败与修复后结果另条记录，不能覆盖失败成PASS |
| `execution` | NOT_RUN时null；实际运行时为已验证对象，含公共case、run_id、machine_id、观察UTC、实际build/EXE、PID/出生时间、pipe/generation和输入版本引用 |
| `evidence_scope` | offline / fixture_live / natural_live / cache_load；PASS必须说明仅覆盖哪一层，不自动升级为natural_live |
| `input_origin` | fixture_generated / production_checkpoint / normal_campaign，附原件引用；无fixture模块不等于存档中的物品天然掉落 |
| `requirement_refs` | 有序引用数组，指向本次设计/图鉴及具体条目、版本/SHA |
| `actor_refs` / `artifact_refs` | 实际验证的原生引用数组；别名另字段保存，不把P1当原生角色ID |
| `source_event_ref` | 原生事件证据引用或null；不需事件的离线/静态项可为null，需事件却未知不能PASS |
| `fixture_controls` | 有限类型的夹具输入/随机控制说明与证据引用，未控制时为空数组；禁止任意伪造终值 |
| `before_refs` / `after_refs` | 原生只读观测EvidenceRef数组；有需要则另原生结果S引用，以分离原版与模组增量 |
| `assertion_refs` | 对独立期望值与后验比较的产物引用；不能仅调用生产计算器，再拿其自身输出作期望值 |
| `elapsed_wall_ms` | 实际非负整数或尚未执行时null；游戏时间另存有效GameDate起止，不混算现实离线时间 |
| `reason` | NOT_RUN/FAIL/BLOCKED/NOT_APPLICABLE必填具体原因；PASS可为null |
| `deferred_checks` | 必需但未完成的子项ID数组；非空时该case不能宣称完整PASS |

EvidenceRef统一包含实际path、SHA-256、producer、所属run/观察时间；JSON日期、数组与ID编码复用产品和公共合同。布尔不能冒充整数，float不能冒充计数/序号；数组顺序有意义，tuple统一编码为JSON数组后再比较。不存在的前后态为空引用并说明原因，不能用“空值等于0变化”判成功。

初始结果示意：

```json
{
  "schema_version": 1,
  "case_id": "LW-G03",
  "status": "NOT_RUN",
  "execution": null,
  "reason": "尚未执行该子例的实际业务与独立后验",
  "deferred_checks": []
}
```

这是状态分支的最小示意；实际生产模型按分支明确哪些证据字段必填，PASS必须有真实execution及必需断言，BLOCKED的“尚未启动”和“已启动但缺后验”分别保留，不能靠宽泛Any/cast/type ignore压掉差异。

## 6. 汇总、失败与收尾

run-summary分别列每层通过范围、FAIL/BLOCKED/NOT_RUN、启用/储备内容、真实源事件资格、玩家/AI/无地覆盖、冷载和多机范围。只有对应case必需子项都通过才可标该case PASS；未启用内容明确不在本次范围，不用占位effect把它变成“已验”。

失败先区分产品机制、原生观测/事件来源、环境/加载或公共运行器；即使公共闭场失败，已有真实业务后验仍按其实际范围保留，不能抹成未发生；公共正常关闭也不能反向证明业务通过。公共verify的`product_release_pass`保持其原含义，不据exit0宣告整个产品发版完成。

结束按公共GUI Quit与独立retained进程观测证明本场owned CK3已退出，再完成keeper/CAS资源释放，保持Steam离线。超时/失败后记录实际收尾状态，不能把强杀当正常退出。现场资源和原件按[统一存储策略](../../docs/storage-retention-policy.md)开始/重写入前/闭场检查，保留必要恢复输入并限期复核。

发布后的[缓存验收](../../docs/workshop-cache-acceptance.md)复用公共`workshop_cache`：真实Steam下载文件与正式包一致、CK3实际加载即可。没有itemID时不进入；不挂业务fixture，不重跑本方案。Steam Change Notes公开全文、正式changelog与其他发布交付继续依仓库合同，不由本文件授予发布授权。
