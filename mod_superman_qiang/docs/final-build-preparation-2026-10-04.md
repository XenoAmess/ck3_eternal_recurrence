# 最终构建与 GitHub 附件回读准备

本文件是操作准备。最终技能下限行为与实机矩阵结论确定后，由发布执行者提交源码、创建并推送 `superman-qiang-v1.0.0`，再生成新 staging。初轮 `builder-L0-A0001` 保留原样，不作为已完成最终发布的证据。

## tag 与正式包

现有构建 wrapper 校验 tag 名与版本并记录当前 HEAD；它不会创建 tag，也不自行证明该 tag 已解析到当前 commit。发布执行者先核对以下两个 commit 相同，确认本产品构建输入已提交，再执行新构建：

```text
git status --short
git rev-parse HEAD
git rev-list -n 1 superman-qiang-v1.0.0
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\build_release.py --output D:/ck3-superman-qiang-20261004/final-tagbound-A0001/mod_superman_qiang --git-tag superman-qiang-v1.0.0
tools\.venv\Scripts\python.exe mod_superman_qiang\tools\build_release.py --verify D:/ck3-superman-qiang-20261004/final-tagbound-A0001/mod_superman_qiang --manifest D:/ck3-superman-qiang-20261004/final-tagbound-A0001/mod_superman_qiang.manifest.json
```

`final-tagbound-A0001` 必须尚不存在；如已用过，使用新的 attempt 名。首次 CreateItem 尚无 item ID，因此 manifest 的 `workshop_item_id` 为 null；真实 ID 仅在创建成功后的新证据中记录，不倒填本轮历史。当前账本版本正式 staging 为精确 22 文件，README/docs/tools/夹具均不上传，内层 descriptor 无 `remote_file_id`。A0001/A0002 的历史 21 文件报告保持原样。

## GitHub 附件

附件使用正式构建同级的 `mod_superman_qiang.zip` 和 `mod_superman_qiang.manifest.json`。创建 GitHub release、上传附件由发布执行者处理；应先冻结实际文件的完整 SHA-256，不复用初轮候选的摘要。

已准备可复用、标准库实现的外置只读回读助手：`D:/ck3-superman-qiang-20261004/verify_github_release_assets.py`。它使用本机实际 `gh release view` / `gh release download`，仅下载显式列出的附件，并与显式给定本地文件的大小和完整 SHA-256 比较。默认只输出本地 plan，不查询远端、不创建目录；`--download` 才会 GET 和下载，始终不创建 tag/release、上传或修改附件。

正式附件上传后可运行：

```text
tools\.venv\Scripts\python.exe D:/ck3-superman-qiang-20261004/verify_github_release_assets.py --repo XenoAmess/ck3_eternal_recurrence --tag superman-qiang-v1.0.0 --asset D:/ck3-superman-qiang-20261004/final-tagbound-A0001/mod_superman_qiang.zip --asset D:/ck3-superman-qiang-20261004/final-tagbound-A0001/mod_superman_qiang.manifest.json --output D:/ck3-superman-qiang-20261004/github-asset-readback-A0001 --download
```

回读目录必须为新目录。助手保留命令 argv、stdout/stderr、下载字节及 `readback-report.json`，失败也不删除或覆盖。当前仅完成本地 plan 的实际执行验证，未执行附件远端回读，不能据此声称 GitHub 发布或附件验证已完成。该检查只证明下载附件与指定本地字节相同，Steam 发布及实机验收仍引用各自证据。
