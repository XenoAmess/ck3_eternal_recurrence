# 发布文档与最终源码一致性复核

日期：2026-10-03。范围：只读源码、发布草稿和静态证据归档。**没有修改runtime／fixture，没有启动CK3，也没有上传。**

复核 [完整Steam Change Notes草稿](steam-change-notes-1.0.0.txt)、[Workshop BBCode](workshop-description.bbcode) 与最终三档CB、`greatwar.txt`、`djc_war_effects.txt`、descriptor。当前16个runtime SHA与 [正式静态报告永久副本](release-static-2026-10-03-R0002.json) 全部一致；这是文件读取比对，不是新的引擎验收。

| 文档合同 | 当前源码依据与文案处理 |
| --- | --- |
| 作者与维护身份 | 致谢白绮并链接原作3600021457；计划创建独立新物品，不更新上游；没有添加作者授权声明 |
| 版本 | 1.0.0，目标CK3 1.20.0.3 Crozier，descriptor为1.20.*；明确不能外推整个1.20系列实机通过 |
| 玩家限制 | 三档ai=no及allowed_for_character内is_ai=no；hook仅处理真人主攻击者；描述AI无进攻入口 |
| 费用 | 公国等级2／威望100／虔诚200，王国等级3／500／1000，帝国等级4／2500／5000；保留两种原版费用修正，以宣战UI最终值为准 |
| 参与者 | 自有hook读取本场CB目标县，收集其top liege，排除攻击者、自有封臣及已有参战者；告知可能同时面对多个强敌 |
| 胜利 | 仅目标法理县、当前防守方realm，排除本人及自有封臣，并接管男爵领；未自动分封 |
| 盟友与中立 | 改为“当前战争进攻方盟友及仍保持中立的领土”；避免将已加入防守方的旧外交盟友错误描述成永不转移 |
| 白和平／战败 | 不转移领土。白和平保留威望、按性格压力及停战；战败保留正统性、威望、封臣评价与停战 |
| 战败赔款 | 仅主防守者真人时：正月收入支付3年收入，否则medium_gold_value金额；AI主防守者不走该脚本分支。已补入两份发布文本 |
| 存档 | 保留公开CB ID；只启用原作或维护版一个；已有大圣战及保存重载未验，不能声称无缝迁移 |
| 未验场景 | 明确保留自动军队和并发战争回归限制；没有把普通战争开关或脚本end_war等同完整玩法验收 |
| 九语 | 仅format-certified，未声称九语界面均实机通过 |

## 静态报告归档

来源：`C:/workspace/two-mod-maintenance-20261003/mod_de_jure_conquest-release-static-R0002.json`。精确另存 `docs/release-static-2026-10-03-R0002.json`，两者SHA为 `54cbd92efdb19c4918f5ce28348539ec1618b847ccf6ee12863c0572924d4738`。canonical LF指最终runtime输入；来源JSON采用CRLF，副本保留原始bytes，未重新序列化。旧报告未修改。

## 发布前草稿冻结

下列数据来自 [机器回执](release-documentation-review-2026-10-03.json)，全文HTML解码与LF规范化后的公开回读尚未发生。草稿后续修改需重新冻结，不能把这些SHA作为任意新文本的身份。

| 草稿 | UTF-8字节 | LF字符 | 行 | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| Steam Change Notes | 3067 | 1213 | 31 | `6f338589f9130371019d409a32fc45011c26cbd35c54e34be252fadf54164076` |
| Workshop BBCode | 2685 | 1125 | 31 | `c330b9a68e6a59391e1790b8bb87dcee92c8b77c0cfbd5c34bae238260155506` |

字符数包含换行，行数按splitlines计。两份文案现采用LF，字节SHA与LF文本SHA一致。初始维护版本标initial baseline，仍明确发布前草稿。最终实机结果、物品ID、上传、缓存回读、Steam Change Notes entry和永久changelog由根执行者完成后追加。
