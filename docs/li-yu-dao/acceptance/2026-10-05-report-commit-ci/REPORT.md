本包只读采集 GitHub，并仅写入外置目录。目标提交：bfe0514650dbb446f6cab2a8543d3e4bf1582aff。

实际 push CI：Official Runner CI，run 37228194002，job 111512127603，completed/success；60 个步骤 success，20 个可选发布步骤 skipped，0 个 artifact。完整 job 日志与每项响应已保存。

Li Yu Dao static checks 在本提交没有 run。按该提交的实际 workflow paths 和 8 个未截断 Git tree，变更仅在 docs/li-yu-dao/README.md 和新 R0006 验收报告树；mod_li_yu_dao、共享读取器、专题 workflow 与其指定 R0002 报告树都没有变化。因此为 NOT_TRIGGERED_DOCS_ONLY，绝非专题 CI PASS。

5 个 workflow 定义保存为实际 UTF-8 字节，并逐项核验 GitHub 返回的文件长度与 Git blob SHA-1；另保存 SHA-256。GitHub 连接器不提供 HTTP 原始传输字节或 headers，包内 body 是工具实际暴露的 UTF-8 字符串字节，response 是完整连接器结果的 JSON 序列化。

workflow registry GET 被连接器白名单拒绝，原始失败响应保留。commit detail 的 300 个文件记录不被当作完整 1170 文件列表；所有路径结论由未截断 tree 验证。

此包不证明新 70 文件候选源、CK3 实机、反复合流/分裂、领袖或重载通过。未触发任何 workflow_dispatch/rerun，未修改 Git、主树、Steam 或游戏。

实际 run：https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37228194002
