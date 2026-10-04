# 1.1.0 发布前的文档检查修正

正式标签 `superman-qiang-v1.1.0` 保持指向 `f7fde816e295a62807ab636ee2d93cf307ea69cf`。该源码的两次官方工作流 [37181368580](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37181368580) 和 [37181372794](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37181372794) 均在仓库禁用脚本检查失败：健康验收入口文档中的一句否定说明包含被检查器禁止的名称。该说明没有执行脚本，但违反了检查器对文档文本的要求。

随后只将该句改为“下面命令均使用Python与CMD”，普通推送文档修正提交 `c821c19fd9ffe719b57831586b4c709952fab42f`。本地完整仓库检查通过，官方 [37182221607](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37182221607) 全部成功；其《超人强》测试、静态校验及确定性构建步骤也成功。

没有移动正式标签，没有修改任何运行代码。22个正式文件逐字节等于标签、受验收A0004及修正后的工作树；[正式构建](formal-build.snapshot.json)、[逐文件对照](runtime-byte-equivalence.snapshot.json)、[文档修正记录](documentation-ci-correction.snapshot.json)和[官方完整响应](official-ci.snapshot.json)分别保留这一事实。不能将后续工作流成功改写成原标签的两次工作流成功。

两次失败工作流的完整原始响应和日志保留在外置 `C:/ck3-superman-qiang-media-redo-20261004/ci-doc-correction-A0001/`，字节哈希由文档修正记录绑定；历史失败未删除或覆盖。上传继续使用标签绑定的正式包。
