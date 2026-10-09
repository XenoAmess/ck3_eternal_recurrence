# 事务对照夹具修复与保存关系分析（仅离线）

R38 的下一诊断事件错误地要求 holder=root，与刻意省略授封的对照冲突。现有生成器新增 `--control transaction-only`：保留 R34 的三项头衔属性配置，保留同一事件内的 create/resolve，resolve 后设置数值变量 `lyd_factory_diag_empty_transaction_completed=1`，随后触发要求未授封头衔和该标记的终点事件。终点选项只含 name/trigger，不继续 D3。默认 full 诊断的运行内容保留。

实际最终候选002包含六文件。47项结构检查通过；独立 R37 AST 对照证明除新增标记、终点事件及两语诊断标签外，其余 effect、其余事件和事务/transition相同，descriptor和triggers逐字节相同。5项实际回归覆盖默认完整生产逆投影、正确对照、R38旧持有门禁、过早完成标记和非法继续SetHoF；均通过并接入已有静态CI。候选001及其早期标签原文另留，未覆盖。

本轮只读取已固定的三份外置存档。R38保存结果相对R34 D2a：7个政治头衔、46名受查角色及动态头衔18373完整AST相同，新头衔均无holder。R34 D2b仍改变5个政治头衔及10名受查角色的AST。五个消失ID38561、39045、39171、39352、39527自身AST在R34前后不变，仍为Faith107/Rite169，且只有这五个受查候选保存organization107。新增的保存关系核对实际找到organization_manager.database107，含faith107及coat_of_arms_id28837，三份存档该组织记录相同。这不是组织角色或政治继承合法性的原生qualification，更不证明授封丢人的原因。

公共入口实际 `plan` 返回exit2、BLOCKED/NOT_RUN/NOT_ASSESSED，因为本机不存在文档指定的runtime.local-entry-bound11.json及ck3-upgrade-20261008目录。此次未分配新实机run ID、未启动游戏、未把旧R31 runtime作为公共替代版本。下一步需要共同manifest及其准确文件的本机映射，然后将此诊断接入公共产品case；现有basic-load case不能授本项业务信用。

所有实际argv、stdio、退出码、两版候选、原始保存选定AST、独立比较和本轮源码保存在ZIP。存档正文继续外置，其size/SHA在保存观察中绑定。此次交付是诊断工具修复和离线事实；I3b、新T冷载、C3、I4及whole mod继续NOT_GREEN，修后实机NOT_RUN。
