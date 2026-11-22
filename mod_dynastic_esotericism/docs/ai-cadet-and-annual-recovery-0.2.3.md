# 宗族化宗族：AI 支系限制与年度归宗

本轮用户要求：勾选宗族化后，该绑定宗族的任何 AI 不得创建支系；每年把整个宗族的支系成员迁回宗家，包含玩家。创建限制仍只针对 AI，玩家手动创建保留，但年度也归宗。

本候选沿 0.2.3 旧存档自动初始化修复合并，旧 60 文件候选及既有发布不改写。新增九个生产文件后，开发库存 48、完整语言发行库存 69。它不靠兼容号、每月纠正或改政府实现。

实际绑定判断使用角色的 Dynasty→`des_bound_rite`，并核对 Rite 的宗族化教义、`des_bound_dynasty`、`des_join_house` 与反向身份。不会仅因当前 Faith 相同而禁止其他宗族，也不会因该宗族成员转信其他 Faith 或 Rite 而放过 AI。缺失或互相冲突的绑定不能凭布尔旗标冒充有效对象。取消宗族化后停止限制和年度回扫。

对当前 1.21.0.3 / build26785313 的六个原版文件采用完整同路径覆盖；除入口合法性 guard 外，原定义 AST 保持。覆盖普通支系决议的 validity、AI potential 和真实 effect，命名支系及参数化 found effect，商人、共和国、行政家族路径，以及日本事件本地创建 helper。前置 guard 放在整个相关 effect 入口，防止拦截创建后仍发放声望、头衔或依赖新 House 的后续写入。原本不需支系的商人重领、现任家主与合法行政家主转交继续允许。

这里是当前已核 stock 调用链的覆盖，不能外推成引擎原语禁用。第三方 Mod、控制台或原生调用若直接调用 `create_cadet_branch`，并无已证明的全引擎统一拦截器；年度兜底用于处理实际存在的支系。完整 stock 覆盖也可能与其他修改这些文件的 Mod 发生加载覆盖冲突，后加载者不能被当成仍保留本策略。

## 稳定宗家与旧存档

新建绑定 Dynasty 时，立即记录原 `create_dynasty` 真实产生的第一 House，保存在该 Dynasty 的 `des_cadet_main_house`。复用或旧存档缺少新变量时，遍历该宗族的 House，只有“House founder 精确等于 Dynasty founder”的唯一候选才登记。当前 stock 本身使用 `dynasty.dynasty_founder.house` 识别创始家系；这里进一步要求唯一性，且不取当前 dynast 或某个支系 founder 的 House，不把原 `des_join_house` 必然当宗家。

登记后的 House 不会随着家主、founder 当前 House 或绑定 Rite 的变化被重选。若旧存档无法唯一确定、或保存的宗家不属于该 Dynasty，不随意选一个支系代替：保留诊断并停止该对象的迁回。这是可见的有限兼容边界，不能称该对象已全部归宗。

## 年度处理边界

原 `yearly_global_pulse` 链保留 `des_annual_watchdog`，追加一次 `des_annual_cadet_recovery`。新增 action 同步遍历已登记且双向有效的宗族化 Rite，不另起每日、月度或 delayed queue。只在年度 effect 内先收集该 Dynasty 的非宗家成员，再逐个核对仍属于同一 Dynasty 后 `set_house`，最后清理临时成员列表。月度 binding repair 仅能补登记缺失锚点，不迁人。

代码明确以 `is_alive = yes` 处理所有存活支系成员，包含玩家、AI、不同 Faith 和不同 Rite；已在宗家的成员保持不变。不依赖 `every_dynasty_member` 对死者的默认枚举语义，也不改写死者历史谱系。软件回归证明同一 effect 重复执行后无新增迁移；真正每年一次的调度仍由实际年度 hook 提供，不能把手动调该 effect 冒称已经自然过一年。

## 本次资格与最短实机后继

文件回归分别核：整宗族 AI、玩家创建、非目标宗族、空/冲突绑定、行政合法转交、商人不需支系路径、原六文件未改 AST、稳定/歧义宗家、玩家年度归宗、解绑停扫、snapshot 后宗族改变不迁错人、年度唯一挂点。测试中的小 AST 执行器不提供 Native/游戏语义资格。

真实后继可复用现有 DES 玩家 None→Dynastic 官方选择流程和真实保存读回，按实际绑定读取 Dynasty、宗家、成员 House。至少比较目标 AI、跨信仰目标 AI、非目标宗族 AI、目标玩家四种角色；玩家创建仍能走原条件，目标 AI 原 stock 创建入口被拒。若需要演示旁路已经创建的支系，可由明确的测试 fixture 安排一个真实旁路，再单次调用同一个年度产品 effect，独立保存/读取 House 结果；这只能证明可控 effect，不是自然年度触发。fixture 必须沿既有工具和可执行入口另外取得真实资格，本 Source 不声称已有通用 Execute 能力。

旧无 DES 存档的自动初始化和一次物理保存/独立冷载继续单独签收，不为了本项新增其 Faith/colour 矩阵、每日推进或固定存档数。新年度 action 和创建入口都还需要实际引擎加载/行为验证；当前仅软件通过。
