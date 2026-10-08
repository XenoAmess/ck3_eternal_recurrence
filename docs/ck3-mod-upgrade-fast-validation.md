# CK3 mod升级提速与公共验收入口（2026-10-08）

后续普通版本迁移的工程目标是正常数小时完成，尚无实测耗时或完成ETA承诺；新引擎结构、ABI变化及核心逆向另计。提速来自集中适配、减少重复启动和自动连续消费，不改变各产品发布前源码业务合同。当前批次正式6/10（60%）。

MCP、native bridge、服务、状态/事件读取及启动/退出管理已经是共享底座。各mod独立的是fixture、business case data、adapter及正式构建；冻结版本是当次可复现证据。成本来自尚未集中覆盖的实际capability缺口、consumer不同历史snapshot及人工GUI/多轮冷启动。**永久规则：所有未来mod acceptance从[tools/ck3_mod_acceptance.py](../tools/ck3_mod_acceptance.py)公共入口选一份common runtime manifest；产品不选择或复制host/source/native版本，公共问题在共享层修一次。**旧冻结永久保留，新run消费共同绑定的当前版本。

本轮实际例子：[QOL R31](C:/workspace/ck3-upgrade-20261007/qol12004-continuous-prepare-01/R31-D5-precise-pre-submission-cause39-01/R31-D5-PRE-SUBMISSION-EXCEPTION-AND-JOURNAL-FACTS-39-01.json)D1–D4日推进成功，D5提交前revision expected21/current22不匹配，在request sequence增加/请求创建前异常，不能算D5业务已执行；[TED R11](C:/workspace/ck3-upgrade-20261007/ted-r0011-camera-binding-red-readonly-resource-01/ROOT-TED-R0011-A117-MINIMAL-CLOSED-CARD-40.md)相机缺少合法`binding.episode_run_id`，native dispatch前被拒；[RMTM R12](reclaim-the-motherland-effective-single-heir-2026-10-08.md)的完整物理own0与同holder realm single-heir TRUE是合法effective baseline，旧own-member断言误判。三者分别涉及共享提交边界、consumer绑定和fixture语义；旧RED/ANDFAIL保留，源修复或静态合格不代替实际验收。

按以下顺序落地，复用现有底座和工具：

1. **本轮先解真实阻点。** 集中完成提交前revision消费、普通saved-scene完整binding与有效继承法联合断言，让原MCP业务链连续执行。typed读取提供状态/事件真值，合同要求的GUI亲审保留；TED holder/休战尾验不跳过。失败只修实际阻点，保留原场和原预算；无变化输入复用适用回执，符合既有热修条件的Python修复保持同一受管进程，不盲重播已提交动作。
2. **公共入口统一版本与编排。** 沿用[products.json](../workshop/products.json)的key、目录、canonical ID、builder/flags，补产品依赖与既有业务合同映射；该清单目前没有依赖映射。共同manifest的一次必要既有capability实机qualification供各consumer复用，不按mod重复whole build/full matrix；产品本身业务要求仍执行。CK3现场串行，其他准备并行。记录各phase实际elapsed，GUI-only真实业务单独标明已验/未验；导航ACK、host GREEN、正常退出或plan不能代替业务PASS。
3. **下次升级由原版diff安排重跑。** 集中适配共享native/runtime，再把原版脚本/数据及实际ABI变化映射到产品依赖，选择需重跑的既有检查和路径；只复用输入、版本和生产路径适用的证据，不把旧build实机PASS外推新build。兼容迁移、无关功能和宣传截图分开安排，各自满足原交付要求。不删除原RMTM 36 families/day14 cap、真实死亡继承/忠臣/九席合同，也不新增平台、门禁或理论审计。

当前公共CLI候选已review，14产品/8优先case的plan已实际消费；actual adapter仍pending，不能称全部READY或实机通过。共享host/源码已收敛，Source6 delta/index与native已冻结；冻结及plan不等于common实际qualification。[RMTM R13/a120闭场43](C:/workspace/ck3-upgrade-20261008/rmtm-r0013-qualified-business-unfinished-readonly-resource-01/ROOT-RMTM-R0013-A120-MINIMAL-CLOSED-CARD-43.md)的D3 effective_single_heir资格及D2–D4日推进成立，原D1停步/ACK保留；六部/预算、C3–C6、真实死亡/post-law/full36未验，source/business=false。正常GUI/独立OS0/native0/cleanup、keeper0/CAS6391 done只授闭场。旧14天case未在原TTL内完成全验收；后续拟在原producer 10..30准入内显式选10，day14 cap/36合同保持，这是未来配置，不追认旧场或承诺PASS。

发布后缓存验收遵守[永久两项政策](workshop-cache-acceptance.md)：实际Steam下载的已发布cache文件exact match正式树，CK3确实从该cache路径mounted/loaded目标产品；不重跑fixture、事件、选项、特质、cooldown或其他业务。发布前源码业务、Notes/changelog及原发布交付不变。统一消费、依赖映射与diff驱动施工按实际状态更新，不把计划写成已提速的实测事实。
