# 验收磁盘不足与历史素材保全

2026-10-04，D 盘实际剩余 0 字节。R0008 的 shader cache 准备复制返回 `WinError 112`，没有提交 CK3 启动；该轮 partial profile、错误和运行身份按 environment prelaunch failure 保留，不记为产品 RED。下一轮使用新的 R0009 身份和 `C:/ck3-superman-qiang-20261004/acceptance/` 输出根目录，SDK 和 A0004 staging 仍读取 D 盘冻结输入。容量检查时 C 盘剩余 107,566,346,240 字节。

为了恢复 Git 和任务总线的必要写入空间，仅迁移已经正常停止的历史 R0006：

- 原路径：`D:/ck3-experience-drain-feasibility-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0006/`。
- 永久保全位置：`C:/ck3-superman-cold-archive-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0006/`。
- 4,831 个文件、546,849,601 字节先以 `copy2` 复制，然后逐文件核对原件与副本的大小、SHA-256 和完整文件库存。全部一致后才移除 D 盘原目录实体，并立即在原路径建立指向副本的 NTFS junction。旧文档、脚本和收据中的原路径继续可读，素材内容没有删弃或覆盖。
- 完成后 D 盘实际剩余 556,630,016 字节。后续新验收、保存与发布 attempt 继续写 C 盘，避免再次耗尽 D 盘。

完整原始库存、校验结果、时间及 junction 命令后态保存在 [迁移收据](C:/ck3-superman-space-a01/r6-migration-resume02.json)。第一次迁移脚本在已完成复制及逐文件校验之后，因 Windows `Path` 排序与序列化 POSIX 字符串排序不同而在库存断言处停止，尚未移除原目录；原脚本、第一次收据与错误保留。第二次使用一致的字符串排序重新核对库存及全部原件/副本 SHA，再完成迁移。没有移动其他任务素材、R0007 或当前运行输入。

第二次迁移收据 SHA-256 为 `192c854de4b4b363cef508904c366aa7933bc74b8e9f7d3804572bdcbe7919a8`。本页只记录环境恢复与保全，不证明 R0009 机制、界面或发布通过。
