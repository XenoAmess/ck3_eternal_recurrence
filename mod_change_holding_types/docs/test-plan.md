# 地产类型转换测试计划

日期：2026-10-03。L0 已执行，实机与发布层尚待执行；结果见 [当前测试报告](test-report-2026-10-03.md)。

## L0 离线

- 原始来源 manifest、维护 diff、UTF-8 BOM、括号／引号、descriptor 和本地化 key 检查。
- 使用本机 `open_kaishek` 覆盖的确定性语法子集进行 parse／round-trip，记录工具 commit、profile/version、fixture SHA 与不支持项。无可运行工具时单列 environment RED，不把替代括号检查写成完整引擎语法证明。
- 逐项核验源代码引用的 holding、building、trigger/effect、GUI 或决议接口是否存在于冻结 exact build。
- 验证入口明确 `is_ai = no`；effect 同时核验玩家／拥有关系。相同类型、非直辖、出租、空地及在建边界按源码形成明确合同。
- 按 runtime allowlist 双构建，比较 manifest 与 ZIP bytes，验证 docs、tools、测试符号不入 staging，上游 ID 不入 canonical descriptor。

## 隔离 CK3 关键矩阵

固定入口：1066 Robert the Fox／Robert Guiscard，原版 bookmark key `bookmark_rags_to_riches_duke_robert`、history ID `1128`。不把当前上游来源分析换成其他角色场景。

场景在取得源码后以实际入口和政策细化；不要为了枚举数量测试全部转换排列。

| 场景 | 必须读取的前后状态 | 预期 |
| --- | --- | --- |
| 玩家正常转换至城堡／城市／神殿 | 入口可见性、目标 province ID、holding ID、主建筑、资源 | 正式生产入口改变指定地产，扣款符合文案 |
| 部落转换至已支持的定居类型 | holding ID、主建筑、普通建筑、政府相关状态 | 完成已承诺的转换；兼容建筑与损失符合政策 |
| 已支持的游牧／神殿城塞路径 | holding ID、主建筑、特殊建筑、政府兼容性 | 无解析／运行错误，结果符合范围 |
| 源类型等于目标或无合法目标 | 入口有效性、holding 与资源 | 无误扣款和额外变化 |
| 附庸、出租、非玩家和 AI | 目标列表、所有权、AI 入口 | 无未授权转换；AI 入口关闭 |
| 转换涉及不兼容建筑 | 前后精确 building IDs 与确认文本 | 建筑损失如实提示，不伪称全部保留 |
| 存档与重载 | holding、public flags／variables、入口 | 转换结果保持，旧 namespace 兼容边界诚实记录 |

所有功能断言用原生 MCP／paused snapshot／fixture marker／日志状态，OCR 断言数为 0；截图只作为玩家视角补充。必须测试正式生产 effect，不用测试 effect 直接替代产品机制。有语义能力缺口时保存具体失败和可施工入口，由父任务协调现有 MCP。

已生成外置 `holding-live-fixture-01`，声明 10 个 PASS marker、START／END 及实际 AI actor 到达 marker。六个正路径调用决议自身引用的 `cht_convert_to_*_effect`；另验证同类型不再转换、AI effect 阻止和非男爵领 predicate 拒绝。夹具初始化会将隔离玩家首都地产置为城堡并在矩阵最后恢复为城堡；这是测试初始条件，不能被写作产品正常开局行为。该矩阵不覆盖决议费用、GUI 选择或存档重载。

## 实机前后环境

Steam 默认离线；在本机 task bus poll、领取唯一 CK3 排他槽并直接审阅新鲜离线画面后才启动。使用产品 production staging、外置 fixture、一次性 `-userdir`；不能覆盖真实订阅缓存来测试。启动前 CK3 进程为 0；退出后确认自有进程回收、真实用户资料未变和 runtime bytes 未变。

报告绑定 machine/mod 独立 run ID、source/staging tree SHA、Git commit、CK3 exact version/build/EXE SHA、fixture hash、命令、原生读回、日志、限制和失败 artifact。旧版本实机证据不能外推到本 build。

## 发布验收

只有本产品的关键路径实机 GREEN、必要语言与正式构建门通过后才上传。新物品 ID 与上游 ID 分离；公开标题／描述与完整 Steam Change Notes 分别精确回读，逐文件验证 freshly downloaded subscription cache，重建无 ID staging。仓库永久 initial-baseline changelog 提交并推送到 `master` 后才能标记 release 完成。
