# R226：已正常闭场的有限负例

`machine_id: desktop-3fevhd2-1c74096080`。本页依据2026-10-21 09:12:27 UTC的[原owner闭场记录](evidence/episode04-r226-normalclosed-20261021/OWNER-CLOSED.actual-a01.json)，不表示再次启动或重新验收。

R226实际启动一次、split一次，Move/day/observer均为0。独立读回的子军为175兵，补给100、上限100、月变化+20，未观察到增长，也没有形成可授予B的headroom。R08未启动；1050秒收尾余量守卫没有因窗口即将结束而放宽。

普通Save、OFFclear和GUI正常Quit已完成，retained OS/native/host/keeper/allocator实际退出均为0，现场资源于08:59:13释放为CAS7840/done。原public wait2、热修wait1和各次已知失败保持原样；实际split已经消耗，不能重发。

Other组件逻辑占用68,188,499B，超过64MiB上限1,079,635B。这项历史FAIL不因场景总量仍低于1GiB或后来正常退出而转为PASS。没有删除文件来追认旧预算。

Save原producer的`consumer_rehashed=false`保持；另一次闭场后的独立同句柄读核有自己的原件。二者不混写，`one_life_identity_proven=false`也不改变。闭场成功没有增加B、ABC、付款或fullR08业务信用。

原owner记录列出19份小证据。本批按原字节归档，不复制大Save或native-report；共享入口的20件知识闭包保持原18项，只更新入口与执行图的绑定。
