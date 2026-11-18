# 地产类型转换 1.0.1：CK3 1.21.0

本机 `machine_id: desktop-3fevhd2-1c74096080`。目标CK3 1.21.0／Florin，build26622941，EXE SHA `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。只更新原维护版工坊3812510834，上游3337428403继续禁止作为发布目标。

当前为1.0.1源码候选，业务、发布与缓存尚未通过。生产六个决议／转换effect／守卫／GUI与九语原字节保留；descriptor声明更新后，静态门同步核1.0.1／1.21.0。已定位新版holding类型、原版holy order selector、费用及innovation文件，不把可解析或改兼容号当实机适配通过。

沿公共单一GUI runtime，不使用旧Native。原effect矩阵保持完整；外置夹具可选择新GUI模式：只把原矩阵的调度改为零日开局入口、增加隔离1000金币，并提供前态／后态探针。真实生产城市决议、Rossano选择及扣款、保存和载入均必须由实际官方UI执行；探针不替代这些操作。保存重载、六名称与警告、六类effect及负门禁分别记录，不将基础加载case冒充业务通过。

已观察的静态RED：新版 `00_holdings.txt` 3790B／SHA `a3e97a3095d1da5058d8040e612634f632c85f9ba0ec6bf50a93aef2af31bd3e` 不再直接定义primary_building，而以primary_district引用 `common/districts/holding_districts.txt` 的主建筑。旧校验因此六类全部误报absent。已改为逐一核定同一holding→对应district→对应building，不能在全文件任意找到主建筑便算匹配；TARGETS改为具名四字段合同并同步所有消费者。真实新版六条链通过，替换holding的district、替换district的building、删除district定义均被拒绝，原失败保留。

离线资格：17文件双构建可复现；九语格式／六组原版来源／选择器方法静态门GREEN。原fixture与GUI fixture的完整production-effect事件逐字相同，GUI producer八文件清单往返／BOM检查通过。Open Kaishek对6份正式脚本／GUI及5份fixture脚本通用parse均退出0，不授1.21语义profile；前5份正式精确输入复用首次成功，首次脚本错误把历史纯文本Notes送入parser的失败保留，随后只校验正式allowlist及fixture。完整两份修改的prepare/validate文件strict mypy通过，显式MYPYPATH解析共享tools、imports skipped，不宣称全依赖图通过。原件位于 `D:/ck3-state/upgrade-20261118/cht-offline-a01/`（旧模型RED）与 `cht-offline-a02/qualification.json`（软件资格）；业务仍NOT_RUN。
