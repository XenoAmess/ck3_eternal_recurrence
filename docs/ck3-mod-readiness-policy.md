# 未来启动就绪预算至少 1800 秒

2026-10-15 用户明确要求：400 秒过小；后续同类启动就绪预算中低于 1800 秒的默认值统一提高到 1800 秒，更大值保留。此政策属于共享验收基础设施，对本仓及外置产品 catalog 的新场次共同生效。来源是独立项目 `ck3_mod_more_tenant_slots` 本轮用户反馈整改；具体产品业务与实机证据仍留该项目。

公共 `Selection` 不改产品的 `case.budgets` 原合同。`effective_budgets.readiness_timeout` 使用 `max(requested, 1800)`，其余 command、poll、hold、退出与业务预算保持原值。显式未绑定的 null 仍是阻塞，不能由下限替用户补输入；无效值、布尔值及非有限数字拒绝。

plan、prepare 结果及新 `prepared-case.json` 记录 `readiness_policy`：原请求、有效值、下限、是否实际提高，以及 `explicit-user-instruction-2026-10-15` 来源。新 prepared 的政策必须与当前选择相等。host argv 的 `--readiness-timeout` 与 `CaseClient.wait_hold()` 使用同一个有效值；`readiness-window.json` 同时保存原请求和实际窗口秒数。原初始 plan 本来执行业务时，客户端仍使用原 `timeout` 分支，不将业务预算改成就绪预算。

现有内置 catalog 中部分 adapter 精确校验旧 `original_budgets`。保留这些 requested 合同即可：中央有效下限阻止它们或外置 catalog 继续产生新的400/900/1500秒就绪窗口，不为本政策批量改写产品业务合同。

当前未冻结的主 host、公共 agent CLI 与遗留研究 CLI 共33处 argparse readiness 默认值已提高到1800（26个文件）。预览 operator 四条入口也对旧 manifest 请求应用下限，保留更大值；两个私有 observer 函数默认值同步。canary 的固定业务预算与检查节奏保持，readiness 执行要求改为至少1800，结果仍须精确匹配本次实际请求。遗留 CLI 的存在不解除未来 mod 必须使用公共六阶段入口的规则。

旧 frozen/source、实际 argv、窗口和结果均不修改。当前源码不会把旧400秒 frozen argv 重新解释为1800秒后授予通过；历史消费应使用其原冻结版本。MTS R0017 实际原生 Start 已 ACK，资源夹具日志晚于原 host 就绪超时才出现；这解释了扩大未来启动窗口的必要性，不能证明旧场业务已通过。其原400秒公共超时、后续 host 夹具就绪超时，以及 managed stop/CK3 exit1均保留，正常退出与 native0不授信用。

离线验证覆盖外置 catalog 请求400/900/1500提升、1800/2400保留、其他预算不变、null显式绑定、prepare政策、政策篡改拒绝、客户端等于/超过截止时间、原 host 早退、原业务预算分支和原适配器入口顺序。CLI默认用AST检查，不导入或运行游戏。预览 operator 回归使用现有模拟进程，canary 回归只做静态准备和执行前拒绝；没有本轮实机或产品PASS含义。

实际验证共121项通过：公共 Selection/readiness 五个模块43项（2.888秒）、预览 operator69项（1.982秒）、canary9项（0.776秒），均exit0。命令使用配置的Python `-B -X utf8 -m unittest`，公共模块在 `tools/` 运行；preview从仓库根运行 `tools.test_g2_preview_operator`，并以当前仓库和 `ck3_autonomous_player/src` 配置PYTHONPATH；canary用unit目录的单文件discover。第一次preview因调用目录缺少`tools`包失败，第二次因未配置agent源码导入路径有1项ERROR；修正测试环境后69项通过，未改测试断言绕过导入失败。全部变更Python源码AST解析与`git diff --check`通过，未修改历史artifacts或外置冻结源码。
