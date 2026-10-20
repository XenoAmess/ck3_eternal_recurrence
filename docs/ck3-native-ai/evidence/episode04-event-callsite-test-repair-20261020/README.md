# 公共单日事件测试夹具修复

来源机器 `machine_id: desktop-3fevhd2-1c74096080`，2026-10-20 UTC。仅修复tools/test_ck3_mod_acceptance_event_callsite.py：使用真实完整CaseClient.advance_day，具名guard和execution reserve90，保留事件业务断言，两处对象身份改完整值相等，新增6个非法控制值在报告/提交前拒绝。生产client/native_day/业务代码不改，无SDK/游戏/构建。

[更正根因](ROOTCAUSE.corrected-a02.md)区分原ec7649 CI step94 NameError need、第一候选两identity failures及a02九方法实际PASS；[最终交付](DELIVERY.final-a02.json)保首文未来caption更正，原记录不覆盖。[原focused Popen33892回执](FOCUSED-ORIGINAL-WAIT.actual-a02.json)及[原stderr](focused-stderr-a02.log)绑定exact ec的完整client/native_day Git blobs，见[来源清单](CANDIDATE-SOURCES.prepared-a02.json)。本地Python3.14.7 -O的九方法PASS不冒充CI Python3.13.16或全suite通过，发布阶段不重复旧矩阵。

仅选择小原件逐字节归档；源DELIVERY.actual.json、原ROOTCAUSE.md、88333B完整step94段及fixture/helpers未复制，按这些原收据中的源路径/SHA保refs-only。LOG-EXTRACTION和原GH Popen wait保最小日志出处；首次GH guard拒绝回执明确为原工具transcript整理的派生记录。历史ec/4b9失败保留，新exact head自动workflow另行观察；没有手动rerun。
