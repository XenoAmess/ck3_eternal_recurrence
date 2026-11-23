# 宗族化密教 / Dynastic Esotericism

0.2.4 已完成分离输入的有限实机与纯产品冷载：唯一有效双向绑定且稳定宗家可证的宗族（包括复用原生宗族及可证旧绑定），以所属礼仪的实际在世领袖同时担任宗家家主和宗族族长为目标；只有两个真实职位均对齐才完成。族长错位且有在世支系时，限定该绑定宗族归并到稳定宗家后重算，缺少可证关系或稳定宗家、冲突绑定及原生pending不强修。加载旧档、领袖相关生命周期和年度兜底分别处理，已对齐的局部路径不扫人物。源码／软件、候选构建、实际双职位与头衔副作用、再保存及发布分开记录；实际资格限受控newDY与持久性，不外推复用／旧绑定全路径实机；公开仍以实际发布收据为准。见[本次双职位规则](docs/leadership-continuity-0.2.4.md)及[永久候选更改说明](../docs/release-changelogs/dynastic-esotericism/0.2.4.md)。

0.2.3 已在同一 Workshop3826991345实际更新，71文件下载精确、公开标题／正文／Notes完整回读及独立缓存冷载／正常退出有限闭环已完成；旧档自动初始化、完整旧繁育配置迁移和跨年后全员回宗家／宗家家主的各自有限证据保持，不外推0.2.4双职位修复。见[0.2.3永久记录](../docs/release-changelogs/dynastic-esotericism/0.2.3.md)及[有限交付记录](../docs/maintenance/evidence/des023-finite-publication-and-cache-complete-a1132.json)。

可选默认教义 V2 的兼容范围及 DES→RRF 发布顺序见[中英说明](docs/optional-defaults-v2-2026-11-20.md)。 / See the [V2 compatibility and publication order](docs/optional-defaults-v2-2026-11-20.md).

**0.2.2 已公开发布**于同一 Workshop3826991345，适配 CK3 `1.21.0.3 Florin` / build `26785313`。真实首次宗族化改革和两个独立保存日图、完整公开文字、SDK精确57文件下载及有限独立Saved缓存挂载／载入均已通过；不授完整产品矩阵或GUI菜单case。见[本版永久发布记录](../docs/release-changelogs/dynastic-esotericism/0.2.2-florin.md)，历史候选检查见[适配记录](docs/compatibility-1.21.0.3-2026-11-20.md)。

独立模组预研目录：`mod_dynastic_esotericism/`；产品 key：`dynastic-esotericism`；拟用脚本前缀：`des_`。

0.1.0 已作为初始公开测试版发布：[Steam 创意工坊 3826991345](https://steamcommunity.com/sharedfiles/filedetails/?id=3826991345)。实际游戏业务验收继续进行，完整矩阵与缓存加载验收尚未通过。具体结果以[交付状态](docs/delivery-status.md)与实际回执为准。

需求包括：礼仪创建／改革时选择“宗族化”或“无”；宗族化礼仪创建对应宗族，创建者与全部信徒加入；宗族成员背离对应礼仪时，受到该礼仪信徒的一项 `-100` 好感修正，并被视为具有监禁、处决等惩罚理由。

0.2.0 已作为公开测试更新。它新增基督教大类的“繁育教派”和“白绮教派”，各有独立信仰、同名礼仪及用户提供的图标；生成宗族改用礼仪名称，并修复 NPC 中间建族后未将族长交回创建／改革者的路径。两预置礼仪配有对应纹章；任意自创礼仪无法原生复制图标时，按用户允许的回退使用游戏原生随机纹章，默认家族与宗族保持一致。

0.2.1 补齐两项预置信仰在867.1.1的创建历史，保留繁育／白绮主礼仪默认宗族化及初始化保护。修复代码的静态构建与相关回归已通过；两项普通GUI自定义统治者开局分别由Native和独立存档核对保留各自信仰、主礼仪及宗族化。同一实际信仰列表画面显示繁育8名信徒和白绮0名信徒／0伯爵领，覆盖无初始信徒仍可见的问题。白绮场公共包装因操作延迟超过收尾预留返回2，原结论保留；繁育场公共run与独立verify均退出0，正常资源闭场及普通场次资格通过，原结果`business_pass=false`仍保留，不外推完整产品矩阵。实际上传与公开回读另以发布回执为准。具体范围见[0.2.1记录](../docs/release-changelogs/dynastic-esotericism/0.2.1-preset-faith-startup-fix.md)与[机器可读验收记录](docs/acceptance/preset-faith-startup-0.2.1.json)。

[需求文档](docs/requirements.md)、[测试方案](docs/test-plan.md)、[可行性研究](docs/feasibility-2026-10-24.md)、[发布准备](docs/release-plan.md)分别记录产品合同、验证和实际边界。

正式构建使用 Java 21 与默认 Maven（版本按根规范）：

```text
mvn -f pom.xml -pl :dynastic-esotericism-tools -am -Dsave.build.root=<approved-shared-build-root> -Drrf.build.root=<approved-rrf-build-root> -Ddes.build.root=<approved-des-build-root> verify
java -jar mod_dynastic_esotericism/tools/target/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar build --source mod_dynastic_esotericism --repo-root . --output <new-output>
```

容量受限机器通过 `-Ddes.build.root=<admitted-external-root>` 将 Maven 产物放入已准入的外置根，再使用该根下的 runner。游戏运行本身只加载正式 staging 的原生 CK3 文件，不依赖 Java 服务。`tools/` 的测试夹具、文档和图标生成源码均不进入正式包。
