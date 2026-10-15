# XQOL fixture support compatibility（2026-10-15）

本次只修正历史合同对共享prepare源码的陈旧pin。原10984B来源为Git blob `c63ad18a62e69cefd60f406bb5198382d1e26a09`，SHA-256 `4dff30b3023d34cb2eb7923e52d81184da2cab4f301fc8a7c7b454277a003981`；当前12881B为`4221d9bab91706ba0e6ba07a21b1944adf71f71e9cc4c1a54ce8c9117b3dbbab`。

实际逐字节与AST复核表明，原文件完整保留为当前文件前缀；尾部仅新增无装饰器、无调用型默认值的`finish_product_profile`定义。既有函数、签名、导入和模块级执行均不变。该新入口只供product-only profile收口使用，原XQOL fixture仍调用未变的`materialize_fixture_profile`，所以原fixture行为无需调整。

七个共同依赖该helper的XQOL合同只更新support_files中的这一项bytes/SHA；fixture源码、事件、原计划、预算、marker、原版/赎金业务条件及实际validate_contract实现全部不改。PAM两层inverse和赎金inverse的完整JSON仍逐字段一致，仅共享helper元数据变化，因此相应三个完整SHA重新冻结。以下并列保留原值和新值，不把历史原值改称错误。

| inverse | 原支持版本SHA | 当前兼容支持SHA |
| --- | --- | --- |
| pam_before_boundary | `cf720e3a30f56fe637118dbdf6fbf88811f3c972db5ca60d109523c47d785510` | `eb44bc2e1c9b352e67749b8bc2f5040ab0c82b8298f2497023f2e95448fce910` |
| pam_before_slot_diagnostic | `049eb0c6fcb366df23f71048c7905f845490517541aeb7668ee6e3642ee858e8` | `d9c09fcb6d785bb25ed0c301a0f1ae3e4ba3b8356365fe29e31b34ca806270ab` |
| ransom_before_atomic_receipt | `1c391554ad054865cdf49ca22a718b992201cd5fc3cfcd175c0c576425e7a0cf` | `52877e54d11256a9d061fccd00c744b86e888a350b7005f60e8c26212a76b900` |

新增窄测试会还原每个合同的旧helper pin并对整份原JSON做bytes/SHA精确比对；同时验证原prepare前缀与唯一新增定义，覆盖七个实际支持合同及错误helper大小/hash、fixture hash和预算篡改仍拒绝。错误不靠可优化移除的语句处理；测试方法在Python优化模式下仍工作。

这是离线源码/契约兼容验证，不是新的CK3实机、产品业务、工坊发布或全套官方CI通过。旧失败run及原pin保留；最终是否进入master及新官方CI结果由实际整合回执另记。

新增窄回归类由既有followups入口直接导入，官方原步骤调用该入口时会一起发现；无需新增全套CI或另一套runner。
