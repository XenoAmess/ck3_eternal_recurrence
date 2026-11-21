# 登记、认购退款与本地原生气泡验收

这是独立的 issuer-refund-toast 用例，使用正式金融脚本及已有公共后台通道。
最多一个自然日、三份真实物理保存，每份不超过256MiB，退出预留180秒。
新场必须重新取得实际来源、工具资格、存储与期限准入；不继承旧场的grant、PID或未消费动作。
本用例不改变原17个用例，也不给债务危机、20种叙事、全体人类玩家或全产品信用。

## 三阶段

1. D0基线：绑定实际最新外部归档及当前actor。保留本场新基线SAVE、audit、raw、whole和实际PRIMARY。
   可以先通过正常GUI调整发行主体/微型目标/认购额等输入，再检查并保存基线；
   这些原始query/activation也须直接保留在基线evidence。它们不授任何直接金融状态setter。
   正常GUI检查成人存活人类、合法非系统未冻结PRIMARY、可用free至少200分、
   无pending offer/发行冷却，且微型商业公司登记可用。任一资格未知或不足，
   明确NOT_OBSERVED，零新增日正常退出；不得注资、清冷却或换角色来强行满足。
2. D0业务：发行主体选择“商业公司”(type6)，微型目标20，通过登记按钮和event100各一次真实确认。
   实际登记费100分；同一新币正常认购1金，实际冻结100分(价格20分/手时5手/500单位)。
   点击“撤销筹备并退款”，核对event102捕获的实际新币后确认一次。
   原版本1发行凭据须证明同一PRIMARY真正收费；认购reservation最终state3/status2/remaining0，
   当前币state6/trading0/首次refund_news_recorded和kind10须来自真实退款收尾。
   D0前后现金、reserved、手续费及全部旧义务独立对账后保存第二份SAVE。
   实际新coin及subscription的原生/永久身份必须在完整基线中不存在；不猜下一ID。
   业务失败、UNKNOWN或退款未成均保留原件并NOT_OBSERVED停止，不推进一天、不重按确认。
3. 原生一日及显示：D0业务深校验通过后，由公共CaseClient原有advance_day选择真实Native/Host路径。
   仅本用例将同一个原始日控制与两个ck3_query_current_interface_toast_v1只读行放入同一计划。
   fresh-before、后端选择、日投影、一次提交、实际结果和strict build守卫保持。
   两查询之间沿用Host正常Full读取；不新增timer/clock，不另行手动推进或让默认driver再推进一天。
   原生日操作遇到实际事件边界时不重试；可保留零日NOT_OBSERVED并退出。
   查询结束后才保存第三份物理SAVE，再运行既有独立audit/raw/whole和NewsToastAuditCommand。

## Root证据形状

所有阶段响应仍须有当前run_id、reviewer=/root、每条原始required_assertions以及实际evidence FilePin。
所有extras引用的归档、audit/raw/whole、动作、capture和Java join报告必须直接并入该阶段evidence，
不能只把它们藏在另一个manifest内。先用原函数深校验，再正式发布Root响应，等待下一个实际awaiting。

输入case_inputs.issuer_refund_toast只接source_archive与scenario_id；实际源必须逐字绑定public saved_campaign。
不允许输入预测新coin、news或reservation身份。Root业务阶段提供refund，状态只能OBSERVED或NOT_OBSERVED。
OBSERVED含before_archive/after_archive、三组gui_actions、完整facts、audit/raw/whole/reconciliation。
facts只使用现有共享Clausewitz parser生成的实际整数分/引用，不写并行parser，不把missing默认0。
完整键表由_irt_refund约束；issue_receipt采用真实xfm_issue_receipt_*版本1变量。
本窄例要求topup0，且D0原始free足够，不需要Gold浮点换算或任何余额setter。
每组动作都有本次实际query+activation；登记和撤筹还各有当前event查询+确认。
二次支付、关联方“外资”、提前上市或直接调用script effect均不能代替正常路径。

第三阶段的physical_archives须按顺序保留三份，terminal_*来自第三份；预日事件边界可只保留前两份。
day_capture必须是当前held客户端生成的文件，固定包含原计划、原actual-results与两个原DTO的pins。
toast=NOT_OBSERVED时必须保留明确原因和证据。OBSERVED只接两个既有Java新闻关联报告。
报告request.toast须分别等于两个原DTO，request.save须等于第三份归档。
第二个报告必须实际VISIBLE和LOCAL_NATIVE_JOIN_MATCH，指向本次新币kind10、实际actor/event/day。
两个捕获的进程、连接代际、线程、viewer、日期、title/description和recipient/display-entry/actor必须一致，
且第二次completedApplicationFrame严格增加。原query after_snapshot必须同进程/actor/代际/日期并暂停。

## 信用与失败边界

退款收尾创建持久新闻事实；它不证明发送或当前可见。普通/离世两队列合计每天最多3条，
旧消息可先被发送。观察到另一个旧金融消息可保留其实际报告，不能授本次新kind10信用。
available、empty、hidden、visible_pending_frame、身份缺失或未取得新帧都不是送达。
两个读取不保证一定捕获阳性；不得为验收重发通知、重放业务或让AI/角色死亡。
既有Java报告deliveryConfirmed/allHumanDeliveryConfirmed/financialCertified仍必须false，
本用例只授已观察的新退款事实与一个本地原生对象的实际来源关联，不改这些字段。
终态NOT_OBSERVED仍正常关场；公共退出、资源释放和所有原失败各按真实回执处理。

不增加金融生产效果、SDK、NativeABI、observer ARM或强制业务setter。
20种危机文案继续采用非血腥、无实施步骤的既有设计；不通过制造死亡穷举它们。

既有App17审计元数据可能接近16MiB。实际超门时保留原失败与已完成SAVE，
只按已有有据元数据后继处理，不放宽共享SAVE/SDK/parser门、不补造或再存一份SAVE。

角色身份沿用SDK/Java的规范signed32 CharacterID，范围-2147483648..2147483647，单独拒绝-1。
当前actor、PRIMARY holder、controller/news_actor、发行receipt.actor和subscription.buyer，
以及两个原生/Java报告中的角色身份均保留同一有符号值；不取绝对值，不转成uint或补码十进制。
0是允许的角色身份；+号、-0、前导零、bool/float或越界值拒绝。Story、永久ID和所有金额仍使用原uint规则。
此启动入口的有符号角色支持只适用于本窄case，其他17case与日期的原校验不变。

边界：这里修正的是本窄case的Generic身份校验与来源关联。现有公共Selection在
 tools/ck3_mod_acceptance.py:821–823仍独立要求saved player_id>0；本包不修改该公共入口，
故负角色完整Generic软件链不授负角色公共CLI启动资格。当前31254场不受此旧门影响。
