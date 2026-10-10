# I3b 正式 B4 公共验收入口

2026-10-10 已接入公共入口的 `li-yu-dao / i3b-formal-b4`。这是源码交付，实机 **NOT_RUN**；不代表一期、B5、C3 或 I4 通过。当前正式 factory 字节仍与已失败的历史输入相同，取得具体修复或新的判别输入后才执行，不重复相同 B4。

## 实际执行合同

使用公共 `tools/ck3_mod_acceptance.py` 的 plan、prepare、allocate、preflight、run、verify，runtime 由公共 manifest 选择。产品 adapter 不另选 host/DLL，也不恢复旧私有 runner。

- 唯一输入是合法 R29 B3 已签署存档、71 文件正式产品、四份配置及精确固定的小型资格/基线/reader request。prepare 校验输入与投影；历史签署证书只证明来源，当场资格必须重新观测。
- 当场核 `lyd.430`、actor 31254、暂停日期、serial 3 / nonce 6 / phase 2 与原生选项 `[0, 2, 3]`。新 B3 SAVE 后取得完整 G2 Faith 成员/谓词和 G3 Title 查询，并检查原 87 项保护以及原生/存档完整有序 45 人名单。
- 只提交一次公共 option 1（原生 index 0），未知 ACK 不重放。公共动作响应的实际字段为 `option_index`；`native_option_index` 属于事件展示，不能代替该字段。
- 核新的 `lyd.431` 实例与 numeric 结果，取得真实完整后置名单。名单改变仍继续第二次 SAVE、G3 和原 88 项保护，保存 RED 证据；不得提前抛错而丢失存档，也不得把 45 人保护改成 40 人。
- B3/B4 新 SAVE 各读取一次正文，原始签署基线正文不重读。保存两份新 checkpoint，避免第二次 SAVE 覆盖第一次证据。B4 通过仍须独立 B5 冷载，再以同一个真实新 T 继续 C3。

共享 MCP 仅在既有 Confucian 只读 opt-in 明确启用时增加 `ck3_query_confucian_assembly_predicates_v1` 注册；底层 service/driver/native provider 已存在，本包没有重编 native。Source08 历史冻结不含这项新注册，未来正式场必须先绑定包含该改动的后继共享源码，不能改写旧冻结来追认。

正常退出继续使用公共原句柄、native 与 cleanup 证明。需要人工 GUI Quit 时，ROOT 在亲审取消自动保存的原图和最后一次映射点击结果后，立即用 [原期限内审阅工具](../../tools/ck3_mod_acceptance_manual_quit_review.py) 写入原请求响应；不得等退出后才补写或补认 R47 的逾期响应。

## 验证与出处

主树采用后实际执行 14 项 formal adapter 测试及 4 项真实 MCP 注册/参数模型测试，均 exit 0；新 formal 测试已接入原官方 CI。覆盖完整保护比较、当前 numeric/owner/revision、改变名单后仍保存、唯一提交及实际公共 DTO 字段。测试不启动 CK3，不授业务信用。

[精简实际回执](../ck3-native-ai/acceptance/2026-10-10-i3b-formal-public-source-only/VALIDATION.actual.json)固定候选及本机测试原件身份；外置候选 001 的原 17 项验证和 002 的单项实际 DTO 回归保持历史原样，不据此改写旧实机结论。

下一实际诊断使用独立 holder/resolve 场景，在同一事件内记录有限 heir scope 并停在 D2b 后保存。日志 getter 可能触发 lazy refresh，不能直接当成缓存写入链；正式 B4 的完整保护要求保持。
