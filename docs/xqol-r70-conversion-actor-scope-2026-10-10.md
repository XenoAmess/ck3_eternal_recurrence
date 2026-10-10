# QOL R70：批量改宗的 actor 作用域

2026-10-10，仍只处理天朝二期以外原十项迁移，正式交付 7/10。R70 的业务步骤完成不等于整场验收通过。

## 原场事实

Source17、PAM 阴性 prepared-36、a171/R0070 完成原 35 步和 12 个自然日。accepted=1、refused=0、pending 移除、收件人的 Catholic/Roman 身份、两项原版奖励各执行一次、piety 和 spiritual fulfillment 前后精确断言均通过。最终合法度可读为 raw=373599200、scale=100000；效果回调同步合法度差值仍为 UNKNOWN，不能用跨日终值补齐。

整场 run=2、verify=2：原错误日志有五次 `is_ai` wrong-scope，不能通过删掉 fixture 栈或放宽门禁消除。正常退出合格、保留 OS exit=0、native zero=true、host GREEN；allocator 本人回读 0、keeper 0、CAS 8477 done。15:29:14.777420Z 现场资源实际关闭，Main 交还 Root。

薄证据根：`C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_negative--a171/`。

- `ROOT-FIELD-RETURN-R70-01.json`：11672 B，SHA-256 `45070f6d3323bbfb3c95ce5ee9b5d76a1b526eae43ef92da2773e1f2927a895c`。
- `R70-ORIGINAL-ERROR-CLASSIFICATION-01.json`：6428 B，SHA-256 `9b03cc17702d2ed60feda6415eebb50e85d91954aa913d3c2d27e160c740d179`。
- 原 `case-output/original-error.raw` 位于 `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0070/`：22753 B，SHA-256 `b23082a4fb115f9ed4f7c3d8d561f6187cc7c221944ae0122da212cbca2cb9d4`。

## 已确认的原因及修复范围

本机 CK3 1.20.0.4 的 `game/common/character_interactions/_character_interactions.info:570–573` 明确规定 `is_available` 的 root 为 actor。原版 courtier/ruler 改宗交互都在这个字段使用裸 `is_ai` / `is_adult`。生成器把原 body 直接放入私有交互 `is_valid` 后，根为 none，导致 R70 正式生成文件第 84 行报错。

最小修复仅在生成器复制 `is_available` 时保留显式 `scope:actor`。原 `is_shown`、`is_valid_showing_failures_only` 及其公共 trigger 当前已显式指定角色，继续保持原 body；不改为 recipient 或 puppet。发送前完整原版 admission 保持，pending 阶段仍只检查纯条件，不能恢复会因已有 pending 而自我拒绝的递归 full-validity 查询。生成文件只由生成器更新。

最小修复已应用，真实生成输出只改变两处 actor 包裹。默认产品 validator 新增独立结构检查：直接读取 stock 三个字段，反解 actor 包裹并核完整原 body，而非复用生成器产生预期。Root 增加不依赖安装 CK3 的最小 scope fixture 回归并接入既有 CI 步骤；本机另以真实 stock 运行同组检查。六项 tests 实际 PASS（0.092s），生成器 `--check` 与完整产品 static validator 均实际 exit=0，27 runtime files 保持。

候选 patch 为 8554 B、SHA-256 `b4bac2fba2bda5ba6b9533560fdca5540c2ad70e578a46e1f97d6cb8c66bd45e`，位于 `C:/workspace/ck3-upgrade-20261010/pam-actor-scope-candidate-01/`；Root 的 CI fixture 增量及实际检查另记于 `root-resume-08/scope-and-nonce-adoption-01/`。候选封包曾因磁盘分配取整达到 201560 B，超过 192 KiB 上限 4952 B；原 FAIL 保留。仅回收四份与 Main 完全相同、无后续消费者的未变生成副本，实际释放 86488 B，没有删除变更输出或重跑已通过检查。

尚未给新源码实机通过。后继应使用新正式 staging 和公共 prepare，保留原步骤与错误门禁；R70 不追认，不重复已赚取的其他业务矩阵。

## 可复用的截图采集入口

历史外置双 nonce 采集器已收编为 `tools/steam_offline_nonce_capture.py`，操作方式见 [公共本机启动卡](ck3-mod-acceptance-local-launch.md)。Root 实际执行新入口 `--help` 返回 0，尚未执行新入口的 UI 采集。它只生成两张原图及辅助记录；操作者仍须亲审 nonce 像素和 Steam 离线画面，不替代公共 launcher challenge/proof 或自动判断离线。

Source18 原生增量构建取得独立 512 MiB / 900 秒预算，实际从 15:40:43Z 开始，294.464 秒完成。21 对象编译、库归档、完整 DLL 链接以及 14 个原生 focused cases 均实际 exit=0，新 EXE 的 Defender 精确路径设置实际读回 verified。原脚本在归档前错误解析多行 RSP，失败原件保留；恢复仅修分词并复用已编译对象，没有重编或重置预算。

实际薄结论为 `C:/workspace/ck3-upgrade-20261010/source18-combined-native-build-01/SOURCE18-COMBINED-NATIVE-THIN-FINAL-01.json`（5611 B，SHA-256 `7d7fc40693545127e038119d5b19ea3f73948d41ee57130233a97e4f8b66ebc5`）。冻结 DLL 为 9087488 B、SHA-256 `b4b19bcdb27076e0958d9e27a75da239798b459d017ee9e19720752ac86101be`。这只是 build/focused PASS；完整共享运行时尚未冻结、未 live，不能借此追认 R69，也不能把 character-window 身份读取当成原生 GetHeir 函数。后继仍须由真实目标头衔的继承人入口与点击链证明关系。
