# 可选默认教义 V2 / Optional default doctrines V2

本节记录 CK3 1.21.0.3 / build26785313 的生产合同修复候选，尚未实机通过或公开发布。
This is a production contract repair candidate for CK3 1.21.0.3 / build26785313. Engine qualification and publication are pending.

RRF 不再直接读取可选全局列表。它在既有创建者 Character 调用链中保存新礼仪为 `scope:xar_rite_creation_apply_target_v2`，然后广播 `xar_rite_creation_apply_optional_defaults_v2`。DES 追加自己的子回调，并把完整现存 V1 列表中的真实 Doctrine 应用到这个明确的新礼仪目标。不清列表，不插入占位 Doctrine，不修改来源礼仪。单独加载 RRF 时该回调为空；单独加载 DES 时原注册与初始化继续。
RRF no longer reads the optional global list. In the existing creator Character chain it saves the new Rite as `scope:xar_rite_creation_apply_target_v2`, then broadcasts `xar_rite_creation_apply_optional_defaults_v2`. DES appends its own child callback and applies every registered real Doctrine in the existing V1 list to that explicit new Rite. The registry and source Rites are preserved; no placeholder Doctrine is added. RRF alone has an empty callback. DES alone retains registration and initialization.

V1 `xar_rite_creation_collect_optional_default_doctrines` 和 `xar_rite_creation_optional_default_doctrines` 注册合同保留，因此新 DES 继续服务旧 RRF。没有 DES 的 V1-only 外部 provider 必须自行增加 V2 应用桥；仅注册 V1 列表不再足够，不能声称此组合已兼容所有旧 provider。已有 registry 值不被清除。联合加载时仍将 RRF 放在 DES 之后。
The V1 collector and registry contract remain available, so the new DES still serves the old RRF. A V1-only external provider used without DES must add its own V2 application bridge; V1 registration alone is insufficient. This does not promise compatibility with every legacy provider. Existing registry entries are retained. Keep RRF after DES in the playset.

发布依赖：先发布 DES **0.2.2**，确认 V2 桥已分发，再发布 RRF **0.2.2-alpha**。不得先发表新 RRF 配旧公开 DES 0.2.1：旧 DES 没有 V2 回调，会遗漏默认贡献。两版仍须各自完成实机验收。这里保留 RRF 当前 alpha 版本，不把软件修复视作稳定版晋级。
Publication dependency: publish DES **0.2.2** first and confirm delivery of its V2 bridge, then publish RRF **0.2.2-alpha**. Do not release the new RRF against the currently public DES 0.2.1: that DES has no V2 callback and defaults would be omitted. Each product still needs engine acceptance. RRF remains an alpha candidate.

软件资格覆盖真实源码 AST、旧 RRF 原件消费者＋新 DES、solo RRF、solo DES及新 RRF＋新 DES，并执行实际打包与公共夹具消费者。AST 中同步执行回调只用于检查脚本操作与目标身份，不证明引擎调度。当前原版 `_on_actions.info:95` 说明回调可访问同默认／保存 scope，并与该 on_action 发出的 events 分属执行链；它不单独证明回调与 caller 后续采用礼仪的先后。必须在新场确认 loader 的 used-never-set 错误消失、保存目标有效，并且默认教义在采用及原生定制前正确生效。原两场失败保持失败。
Software qualification executes the real source AST, the frozen old RRF consumer with new DES, solo RRF, solo DES, and new RRF with new DES, plus actual packaging and public fixture consumers. Synchronous callback execution in a test checks operations and target identity, not engine scheduling. Stock `_on_actions.info:95` documents shared default/saved scopes and separate chains for effects and events emitted by that on_action; it does not by itself establish ordering relative to later caller adoption. A new engine session must confirm that loader errors disappear, the saved target is valid, and defaults take effect before adoption and native customization. Both original failed sessions remain failed.
