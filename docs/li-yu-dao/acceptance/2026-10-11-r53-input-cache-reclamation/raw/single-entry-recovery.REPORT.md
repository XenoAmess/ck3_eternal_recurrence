# R53 单入口与原预约恢复专项独立审阅

结论：**SOURCE_REVIEW_PASS**，最终工作流 005 / ROOT 请求作者 H003 无必须先修项。本结论仅覆盖源码与已存在的小回执接缝，不是准入、删除或闭账运行成功证明。

此前独立审阅遗漏了旧 thin 的重复 `main()`。旧 thin 先执行已含 `if __name__ == '__main__': main()` 的投影，再次调用 `main()`，导致首调用已创建预约、第二调用拒绝。该遗漏在本次纠正；旧审阅与 outer1 失败均保留，旧 PASS 不能作为原入口可执行的依据。

本次仅读 21 个不同小文件、60,517 B，完成 38 项 AST、固定字符串和原件 pin 检查。未 import 或执行任何 producer/helper，未执行准入、plan、apply、close、tests、process/SDK/game，也未读取 cache/SAVE/PE/native payload。逐项结果见 [CHECKS.source-review.json](CHECKS.source-review.json)。

最终源码为：

- `r53-input-cache-retirement-sourceonly-20261011-005/INDEX.json`：3,141 B，`fa3adea890613f88c713eb239fc0a6dddaba17302451c6363c4f6dd6c78aad98`。
- `r53-input-cache-root-request-author-sourceonly-20261011-003/INDEX.json`：1,166 B，`c62beb8e24e2fb16047c0491004f8eac596b4df6e7f0ce0bf8c6378897e5a499`。
- 恢复认证 helper：4,442 B，`7a1dee183022384e739f1c0b1efcf5f53ae70c38d5cadd0602000bc9fb3d5d60`。

三个新 thin 均只有 `from bind_mature import selected` 与一次 `exec(compile(selected(...)))`，外层第二个 `main()` 已删除。005 相对 004 helper 的唯一字节变化是固定错误末行的 `\\n` 字面改为 `\\r\\n`；原 581 B stderr 确为 CRLF。005 close 与 H003 ROOT 作者都精确绑定新 helper 的 size/SHA，旧 004 原件不变。admit/serial 投影沿原冻结字节，未引入再次准入；ROOT 后续 close 应使用 005/H003。

认证依据是固定的原命令、AD、stdout、stderr、ROOT 请求与旧 thin 六个原件：其实际 size/SHA 均匹配。原命令真实 `exit_code=1`；首 AD 20,246 B，`cc49135e1cc4bf0a9d9dc89f4d43f87fd13f45c78221bfb549bfa471f6b7e2f7`。唯一 397 B stdout 的 APPROVED 指向该 AD，原请求 writer_scope、argv/source/request 与使用量加 48 MiB 均吻合；AD 时间在原命令开始、结束之间。原 stderr 的第二入口 create-only 拒绝与旧 thin 源码一起支持“第二调用在输出目录检查处停止”，并非把 outer1 改成成功。

非零命令例外仅接受这一次精确固定的 outer1/AD 组合。正常 command0 分支不变。close 仍记录原 `exit_code=1`，且必须取得字典形式的恢复证据，再写入 `original_admission_outer_failure_recovery`；缺少该证据不能闭账。H003 同步使用相同认证，新增有限 W004/H002 小源码范围计入 post-admit 计量，不把原预约改写、重放或再收费。

原配额、48 MiB 峰值、锁/现场门禁、过期时间、成熟 held-SHA 删除尾部与单次信用合同未在本补丁更改。实际 plan/apply/close 结果、删除量与 CREDIT claim 在本记录中均不授信；应引用 ROOT 此后的原始运行回执，不由本 SOURCE_REVIEW_PASS 推导。
