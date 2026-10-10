# 2026-10-10 本机 Git 垃圾回收追加记录

本记录追加于同日 `storage-retention-2026-10-10-local-capacity-recovery.md` 和 `storage-retention-2026-10-10-local-capacity-recovery-followup-r57.md`；两份外置源稿与 pin 保持原样，Git 入库副本可能归一换行，原 bytes/SHA 仍指外置证据。机器为4号执行者，唯一 C 卷总量 511,776,722,944 B，执行策略1.0.0。

Root 以 Git 原生 `count-objects -v` 的 garbage5 声明授权仅清下列精确文件，无 GC、prune 或历史改写：

- `C:/workspace/ck3_eternal_recurrence/.git/objects/pack/tmp_pack_6T6B7X`
- `C:/workspace/ck3_eternal_recurrence/.git/objects/pack/tmp_pack_bWfN0R`
- `C:/workspace/ck3_eternal_recurrence/.git/objects/pack/tmp_pack_ELtRcy`
- `C:/workspace/ck3_eternal_recurrence/.git/objects/pack/tmp_pack_fzD38p`
- `C:/workspace/ck3_eternal_recurrence/.git/objects/pack/pack-d80c6d6386c8cee5d925c92af1fa7f7d4920be83.idx`

各项 fresh native 身份、长度和单链接已核；idx 没有对应 .pack。原 producer PID/create_time 未留存，保持 null；现无活跃 Git writer，Root 暂停全部 Git mutation，逐文件零 share HANDLE 另行排除占用。首轮取得独占 HANDLE 后在删除标记处遇 WinError5，实际删除0，失败回执原样保留。fresh stat 确认只读属性；第二轮使用同一独占 HANDLE 的 FileDispositionInfoEx DELETE|IGNORE_READONLY_ATTRIBUTE，不改变 ACL、系统设置或正式 pack 属性，5项均实际缺失，失败0。

本轮删除 logical **958,801,068 B**、实际 AllocationSize **958,803,968 B**。free 从 **29,424,504,832** 到 **30,383,239,168 B**，净增 **958,734,336 B**；净增比删除 allocation 少69,632 B，保留为未归因并发变化。Git garbage 归0；正式 packs5、in-pack141109不变，MAIN HEAD `9f4420d5b22e637ab8d11efb05b73aded8d56538` 前后 clean。当前 a159 screen owner 前后相同，未访问其 CK3 profile/state。

独立新增5项不混入旧879,509,432 B followup；累计删除 **30,144,699,336 B actual allocation / 558,854 files**。压缩 savings 另记。当前 merit 原2GiB预留继续占用；新场仍须原场真 CLOSED、释放后 fresh 单场公式，6GiB系统规划和20GiB安全余量不降，当前free不代表下一场已准入。

实际回执 `C:/workspace/disk-cleanup-20261010/resume-05/git-garbage-a159-exact5-readonly-retry-actual-66.json`：2269 B / SHA256 `98b890f5e36182963b6385e54af2aad86768144388eda02640dc3ccb66418ad9`。首轮失败回执 `git-garbage-a159-exact5-actual-66.json`：2872 B / SHA256 `a14e1199cf3799bbb327ac806f8636fa007f9e6d257078aa4a32a24797fe9121`。同根 plan 与 availability journal 由实际回执精确回链；无资产正文 hash。

审计来自既有 disk1MiB，小包≤128KiB；详细 plan/journal30天到期提炼后清理，薄摘要与 availability180天复审，不自动续期。正式 pack、HEAD/index/refs、跟踪源码、业务证据与活跃输入均不在本次垃圾回收范围。
