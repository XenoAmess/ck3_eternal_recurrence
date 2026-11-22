# 保留观察器的21日自然续行

`market-evolution-continuation21` 是专门续读一个已经保存原D14状态的 `market-evolution` 观察器的公共saved-campaign案例。新场本地0／16／21分别对应原观察累计14／30／35；不ARM、不新emit、不重设基准，也不修改原案例的0／14／30／35或fresh ARM要求。原R71 run2／verify2／D14 GAP永久保持，未来新案仅授其自身有限观察结果。

## 输入与fixture复用

普通 `product_dir`／`plain_configuration`／真实 `post_start` 保持原公共规则。`prebuilt_fixture_manifest` 指一个create-only派生元数据文件。`market_evolution_continuation` 必须恰含：

| 字段 | 真实来源 |
| --- | --- |
| `schema` | `ck3-market-evolution-continuation21-input-v1` |
| `source_archive` | 最新原D14独立物理归档receipt的FilePin，不读SAVE载荷作输入检查 |
| `source_facts` | 该归档的原observer facts FilePin，包含基线加14天完整15条记录、原epoch和native identity |
| `source_closure` | 原场正常关闭及done/resources空的实际release FilePin；原case可为PARTIAL，不要求将它改成PASS |
| `original_fixture_manifest` | 上述facts.request.observerManifest的原Java E6 manifest FilePin |
| `observer_native_id`／`observation_epoch` | facts同一原observer的真实正story身份及原整数epoch，不填未来对象 |

派生manifest保留原schema、observed_at_utc、fixture_root、6producer来源及12个原文件逐字节身份，不复制或改写原manifest。唯一两项语义差分为 `case_id=market-evolution-continuation21`，以及receipt的required_markers只保留原最后一个 `XFMAT: TEST PASS market_evolution_35_daily_samples_observed`。这不是新emit：前三个once-only标记已在原ARM／首次捕获时写过，后继日志不伪造它们；基线用同一原15记录、Root审阅与独立读回证明。最终35标记仍必须在新场真实出现一次。Generic会反投影检查派生manifest的全部字段，原公共materializer照旧核完整12叶／来源／机器／复制；其他case不获得manifest不匹配例外。

## 三个阶段

基线从声明的最新D14 savedPair载入并独立再保存，先核同一observer、原基准、原15条身份／日期记录及完整金融冷图。QA读者沿原已完成的编译证明逐项复核，不因新案重编Java、Native ABI、金融脚本或计时器。本场不允许ARM／新epoch／补旧日／强制AI／修改价格或到期日。

本地16天读取累计30天的31条记录，本地21天读取累计35天的36条记录。各阶段必须恰有一份本阶段独立facts报告作为Root evidence；报告的原归档、原Java manifest、epoch、observer、每条record ID／金融日／first及latest Native日期必须保持相同源并连续。不能以native+21或端点金融差替代这些记录，缺日、重复身份、改旧15条、过期源或日历错位均拒绝，不插值。相同原E6读者仍传累计14／30／35，不能传本地21冒充累计21。正常观察期间发生的金融变化全部保留，不要求跨日Whole相等。

沿原命令300秒／readiness1800秒／run10800秒／hold3600秒／退出预留180秒；新合同上限21自然日、最多3份256MiB物理SAVE。资源仍须由Root基于真实新场／新期限准入，源码候选不分配资源或执行动作。shared entry拥有唯一正常退出；实际事件及未答复inbox使用现有公共受限路径，不自动选择选项或回复。

最终新case与GUI合同只可能通过“同一原35日观察窗口读全”，`business_pass`、`product_release_pass`、全市场dailycoverage、容量／性能仍false。AI发行、无地／低阶资格、成本、退款、上市、退市、到期与新闻分别保持真实availability／occurred及独立资金证明；64币截断不能作世界无发生结论。原R69失败、R70有限中文kind10阳性及R71部分结果不重写。

## 软件候选验证范围

新增NoGame测试通过实际Generic prepare／共享engine缓存／materializer／run／Root阶段协议／verify执行，仅在机器身份、JSON档案及日进输送端口使用明确软件夹具。包含21次单日调用与3阶段映射、原12叶保留、原PARTIAL可正常续行、错误源／epoch／observer／manifest／日期／缺日／重置旧记录和缺终标记拒绝。它们不是CK3真实调度、资金或性能证明；源码封包时未编测。原35日case、普通一日门及其余病例未放宽。
