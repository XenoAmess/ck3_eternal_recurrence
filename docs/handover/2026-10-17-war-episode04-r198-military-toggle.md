# 战争四期 R198 军务开关与正常闭场交接（2026-10-17）

`machine_id: desktop-3fevhd2-1c74096080`；实机观察 `2026-10-17T10:14:41.301716+00:00`、闭场释放 `2026-10-17T10:28:21.469463+00:00`。run `desktop-3fevhd2-1c74096080--vanilla--R0198`，source/runtime `dc031358981450ae3f8e40c6234b7f27fd4662ef`，CK3 1.20.0.4。身份PID24728、creation filetime134367039851411170、generation1、episode `native-31254-a9475f27e7e8`、actor31254、date raw53148192；源为R191正常闭场，不使用R197异常退出后的新checkpoint。

[post-R197 native资格](../ck3-native-ai/episode04-post-r197-native-admission-12004.md)只证明本机生产字节、SYSTEM读回和focused cold。A03先链接失败后sourcefix成功；旧D cold虽编译两EXE但SYSTEM因源绑定拒绝。A04新C root构建与SYSTEM成功、admission原生exit0，wrapper因stdout后缀期望不符exit1；A05复用该admission原件、新跑shared-v3 normal及strict consumer，未重跑旧矩阵。跨机器必须重新核构建、设置和实机。

[R198专题及小原件](../ck3-native-ai/episode04-r198-military-toggle-12004.md)证明一次军务打开与唯一原生disable：owner31254、同source child、同日期线程的raw `4A9` 在前ticket7为1，动作包即时`native_after_switch`仍1，后续ticket9/pump90065稳定为0，结果`verified_desired`。15/20秒hold期间一直暂停；`provider_invoked=false`、`native_receiver_selected=false`，没有自然补员ADD、付款或县边损失资格。不能把source/cold PASS替代这次live，也不能把这次局部live替代R06整卡。

Film Start→Finish `NORMAL_TREE_EMPTY`、guard error null、partial false；正常Save回执5,264 B／SHA-256 `3fc07750458cac695677eab6d28db3bb9a47e36a808a82ead4b8253ea801aed5`绑定checkpoint73,689,233 B／SHA-256 `09c5bf2f2aa3dad559a602c292ede45868d90c185bf491fb2e958f849f5bf9a0`。游戏exit0、screen task资源空，录制原片只在原close元数据中有路径/大小/hash，本交接未读raw、未审全解码/PTS/clean/1×/人工签核。动态 **0/11**、ABC **0/3**；现行v2研究 **9/14（64.29%）**、业务 **6/11（54.55%）**，原R07-v1严格 **8/14、5/11**。

下一步先做R198媒体真实审阅，再设计R06自然日ADD/receiver/provider正例；R04县P、R05自然驻扎上限等旧缺口仍独立。R197的timeout/shutdown exit1原件与异常S0边界保留，不因本场正常退出改写。全部本机安装、Steam、SYSTEM、容量及录制事实只对上述machine ID有效；其他机器可复用知识与校验代码，现场状态须重新读回。
