# R213 同帧现金只读结果

`machine_id: desktop-3fevhd2-1c74096080`；补录 `2026-10-18T17:57:43.295294+00:00`。实际source3661/PID27056/gen1/actor33388/date53148408/原EPnull；三次查询同帧，无采样、day或DR。原件[7249B cash结果](evidence/episode04-r213-bayeux-arrival-12004/R213-CASH-READONLY.actual.json)状态为 `ACTUAL_READONLY_CASH_COLLECTED_NOT_PAYMENT_ATTRIBUTION`。

原raw量以1e5为scale：treasury63728159，gross469940－expense437400＝NET32540；current military386622，all-raised493650。这些是当帧只读项目，不能由NET差或标签推出某笔实际付款、payer、同次NET writer或cadence。军事paid/payer/cadence仍未资格化。

[R08静态settlement父体顺序](episode04-r08-settlement-parent-order-12004.md)只证明保留源码正常路径；[R213行军与后继一天](episode04-r213-bayeux-arrival-and-refill-boundary-12004.md)与此现金帧分列，均不把现金标签当成付款因果。
