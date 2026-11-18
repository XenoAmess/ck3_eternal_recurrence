# 地产类型转换 1.0.2：CK3 1.21.0

本机 `machine_id: desktop-3fevhd2-1c74096080`。目标CK3 1.21.0／Florin，build26622941，EXE SHA `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。只更新原维护版工坊3812510834，上游3337428403继续禁止作为发布目标。

当前为1.0.2源码候选，业务、发布与缓存尚未通过。未发表的1.0.1曾保留生产字节并更新声明，但实机启动暴露旧施工trigger已被移除；该tag不移动，保留为失败候选。1.0.2修正生产及原夹具的施工检查，六个转换effect、GUI、金币规则及九语原字节保留。已定位新版holding类型、原版holy order selector、费用及innovation文件，不把可解析或改兼容号当实机适配通过。

2026-11-18T07:34Z，本机1.0.1 R0001仅到主菜单即发现error.log 1041B：生产／夹具旧has_ongoing_construction未知，以及夹具chtt_gui_gold_before未使用。未Start、零业务、零保存，经过真实菜单正常退出，原Popen=0、无WM_CLOSE/STOP、keeper/CAS闭合，保持业务RED。新版原版00_tribal_interactions.txt:55在同样的title_province作用域使用has_ongoing_holding_construction=no，00_building_triggers.txt:11提供该trigger本地化；1.0.2按此同类地产转换入口迁移，不取消施工门禁。夹具期望金币显式从已记录前态计算，修复unused诊断。原1.0.1软件资格只保留其实际范围，不追认为1.0.2或实机GREEN。

沿公共单一GUI runtime，不使用旧Native。原effect矩阵保持完整；外置夹具可选择新GUI模式：只把原矩阵的调度改为零日开局入口、增加隔离1000金币，并提供前态／后态探针。真实生产城市决议、Rossano选择及扣款、保存和载入均必须由实际官方UI执行；探针不替代这些操作。保存重载、六名称与警告、六类effect及负门禁分别记录，不将基础加载case冒充业务通过。

已观察的静态RED：新版 `00_holdings.txt` 3790B／SHA `a3e97a3095d1da5058d8040e612634f632c85f9ba0ec6bf50a93aef2af31bd3e` 不再直接定义primary_building，而以primary_district引用 `common/districts/holding_districts.txt` 的主建筑。旧校验因此六类全部误报absent。已改为逐一核定同一holding→对应district→对应building，不能在全文件任意找到主建筑便算匹配；TARGETS改为具名四字段合同并同步所有消费者。真实新版六条链通过，替换holding的district、替换district的building、删除district定义均被拒绝，原失败保留。

离线资格：17文件双构建可复现；九语格式／六组原版来源／选择器方法静态门GREEN。原fixture与GUI fixture的完整production-effect事件逐字相同，GUI producer八文件清单往返／BOM检查通过。Open Kaishek对6份正式脚本／GUI及5份fixture脚本通用parse均退出0，不授1.21语义profile；前5份正式精确输入复用首次成功，首次脚本错误把历史纯文本Notes送入parser的失败保留，随后只校验正式allowlist及fixture。完整两份修改的prepare/validate文件strict mypy通过，显式MYPYPATH解析共享tools、imports skipped，不宣称全依赖图通过。原件位于 `D:/ck3-state/upgrade-20261118/cht-offline-a01/`（旧模型RED）与 `cht-offline-a02/qualification.json`（软件资格）；业务仍NOT_RUN。

2026-11-18T08:23:33.796717Z，1.0.2公共GUI业务R0002完成原Popen正常退出0、keeper与CAS闭合，未用WM_CLOSE/STOP。六类生产effect／负门禁、六个中文名称与完整警告、真实Rossano城市选择、个人金币1139→939（新版原版费用200）及官方Save/Load同一档均通过，22条marker各一次、FAIL0、零自然日。实际本地保存12,337,646B，last_save与命名档同SHA，重载前后文件身份／SHA不变；读取载入过渡及日期／金币画面后执行后态探针，非仅marker推定保存。

error.log2419B、6条原版trigger localization缺失视角：is_ai first_not来自00_debug_triggers.txt，is_leased_out third_not来自00_province_triggers.txt。原版源SHA和完整诊断已保留；这不是未知trigger／转换失败，但debug界面确有粉色回退诊断，不宣称错误日志为空或原版条件全中文。fixture专用分组标题亦有raw key，不进入正式17文件；六个产品名称与自定义完整警告独立通过。业务范围不含全部建筑保留、八语实机、全部旧档与mod组合。


公共GUI实际业务已通过，真实城市决议／个人费用／保存重载与原effect矩阵分别留证。完整中英Notes已冻结，原条目上传及缓存仍待完成；详细原件为 D:/ck3-state/upgrade-20261118/cht-r2-verify.json。

2026-11-18T08:35Z：地产类型转换1.0.2原条目更新、公开全文、17文件新缓存及实际加载／正常退出均已完成，Steam新后台offline=true。当前完整闭合3/17，继续其余14项。[永久发布记录](../release-changelogs/change-holding-types/1.0.2.md)。
