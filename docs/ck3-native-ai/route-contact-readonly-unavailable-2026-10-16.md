# 完整接触路线不可用的只读终局

机器：`xenoamess-full-tower-eb9d2c1186`。本记录于2026-10-16 01:57 CST补录；实际原错误发生于2026-10-15 17:33:23.612541Z。阶段是源码与离线合同通过；协调者已报告P07同Game续接，尚未由本记录授予新不可用分支的实机通过信用。

## 实际触发与原始边界

N42 P06 AUTO16查询军队318767248到省2635的八个敌军接触时间线；己军当时已位于2635。原生返回`CK3 could not build a complete contact route`，`typed_query_failure_v1`为route/typed_result，executor进入且结束、frame_stable=true、typed_result=false、等待completed、SEH code0。旧SDK把这个已结束的只读“不支持”向上抛成MCP错误，无法让普通规划器继续评估现有受守卫候选。

原件：[P06 AUTO16](D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p06-responses/0016-1-result.json)，SHA-256 `ef7d19cb7775a287360d6b59b4972ec6742e5649ae5479fb45d5fcb550d2fcbb`。该回合保持失败，不重发、不追认成功。原MCP诊断投影截断了完整原生请求／响应；入库夹具根据原诊断、完整计划step及METRICS身份重建包络，明确标记`synthetic_envelope=true`，不冒充保留的完整原包。

## 正规化与策略识别

NativeDriver只捕获实际`_NativeCommandRejectedError`，核对canonical只读route parser、request/response protocol1、同request ID、同step、原正整数native revision、ok=false、精确错误文本及完整typed failure。等待未知、执行异常、其他错误或帧不稳定继续抛错。它只读取现有semantic publication一次，核对暂停、map-ready、角色存活和完整snapshot/public/native/date/actor/episode/generation/PID身份；敌军tuple必须不变。没有第二次原生query、移动、日期或业务提交。

结果schema为`xar.route-contact-readonly-unavailable.v1`，status=unavailable，accepted/available/business_submission/replay_allowed均false，route_contact_horizon=null；完整原请求／响应和同帧读回保存在`readonly_unavailable_evidence`。历史行仍`ok=false`，结果正常返回Service。Service外层`executed`只代表这次只读处理函数返回；外部classifier必须给零动作、日期和实质成果信用，不能据外层状态赋信用。

策略仅修改`_current_frame_route_contact_query_failure`。公共前置版本缺完整lease／scope_status，因此一并收回同一个helper中已验证的generation、episode、date和原生revision绑定；当前不可用DTO另外绑定actor、PID和同帧读回。过期lease不永久锁住新帧，未知失败仍受守卫。没有可用horizon就不能称contact-free；后续选择仍走已有路线／战斗守卫，不改变战争意愿、力量准入或军队动作合同。

## 验证、来源与部署

公共增量在`3ad913a804b704d72c4682221c5160c0abb83b7f`上精确移植，保留公共Native拒绝异常中的raw-return-receipt扩展。AST核对仅改Native两个已有方法、增加两个纯helper，以及Strategy一个helper；已有available-route资格分支逐字相同。未包含另包单日speed5修改，也没有重编Native DLL。

一次公共focused验证：**16 tests通过，0.591秒**，包括7项Native/Service链、原6项策略lease及producer/过期/未知边界；另有11项原包拒绝负例和10项帧／敌军变化子场景。现有Service.execute_step、planned execution和auto_turn实际方法使用有限fake transport执行，正常返回DTO并保留失败历史。available路径夹具只验证控制流，normalizer使用隔离stub；不替代原生几何资格或实机结果。

可复现命令：

```text
python -B -X utf8 -m unittest discover -s ck3_autonomous_player/tests/unit -p "test_*route*unavailable*.py"
```

公共夹具在`ck3_autonomous_player/tests/unit/fixtures/route_contact_typed_unavailable_v1.json`，保留原错误SHA、机器ID及合成包络说明。外置[公共测试回执](D:/codex-ck3-demos/2026-10-14-robert-30year/route-contact-unavailable-p06/PUBLIC-FOCUSED-TESTS.json) SHA-256 `a1c3a698981d97c0fcff921b0b2e8c28dadccc39f8cfacf21ee97f1de502c5e2`；[原候选交付](D:/codex-ck3-demos/2026-10-14-robert-30year/route-contact-unavailable-p06/DELIVERY.json) SHA-256 `012949b97b89a32317810f0dd1418fd851e6781217751932c598890572b208b3`。原策略测试SHA为`459a34a4b3e7059f01b9560d26abe54207ed7df9f5e019cb3da0e9ca558644f6`，producer合同测试SHA为`2efb72c19cb68b247f5c3671780e24d0ccbfcb4b2188a4a87a44acebcd391056`。

P06 Native输入SHA为`5b449440b762dde0f1baf34cd29ab30757730aab229c8a1e3f2d507bb3d86b6a`，独立输出为`4329b216156e8bdb5b58f812d38d647d7d79ce2c48b73f617170d6892677a7fd`；P07实际SDK使用合并另包后`d1af257e…`，不能把公共源字节等同其整叶pin。下一步在自然普通回合观察新不可用结果是否被零信用消费，不重放AUTO16；三十年演示与最终成绩继续由主流程结算。

本包无现场操作，不改Main、隔离runtime或冻结SDK。新增均为小型源码／测试／记录；D卷开始观察free=1,121,275,932,672B，未据此声称并发重型写入准入，未清理任何历史资产。外置工作包为派生物48小时、原错误按其原工作包用途与期限复核；协调者仍在消费的冻结输入不得据本记录删除。公共源码按Git维护规则保留。
