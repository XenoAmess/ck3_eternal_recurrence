# “自动升级建筑”上游冻结记录

状态：2026-09-11 已取得并冻结上游字节；尚未完成 CK3 1.19.0.6 兼容性修复。

## 来源身份

- 产品：自动升级建筑（Workshop 页面显示“自动升级建筑（新版）”）
- 原作者：白绮
- Steam Workshop item：`3596580780`
- 页面：https://steamcommunity.com/sharedfiles/filedetails/?id=3596580780
- 页面更新时间：2025-11-13（Steam API `time_updated=1763091317`）
- 下载时间：2026-09-11（Asia/Shanghai）
- 下载方式：主 Steam 客户端短暂上线并订阅；文件完整后立即恢复离线模式
- 下载缓存：`D:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3596580780`
- 本地只读原始快照：`D:\workspace\ck3_eternal_recurrence\_runtime\upstream-3596580780-original-20260911`
- 文件数：`7`
- 总字节：`127804`
- 规范化 tree SHA-256：`E878367B2A105CC3C9EFFA2D63543A6EB983BF13FC8557C8F5B6DF5BFEB595B7`

tree hash 输入按相对路径排序，每行是 UTF-8 编码的
`<path>\0<size>\0<SHA256>\n`，路径分隔符统一为 `/`。

## 原始文件清单

| 路径 | 字节 | SHA-256 |
| --- | ---: | --- |
| `common/decisions/build_decision.txt` | 1345 | `C77A6ABA6E33E0EC941E1140A23ABCD1EC5826BE786CE5D789BFCE065C6EB992` |
| `common/scripted_effects/build_scripted_effect.txt` | 26844 | `62A6D55FA4D427353E61BBA92B61CF96D2D6FFC44BB75C7CEBEA4605DE69314A` |
| `descriptor.mod` | 117 | `B63C9DCB425DD2CE5FF1A9DB1EA2D853F644ADE7FE4444087DDE7F09E44F0B11` |
| `events/auto_build.txt` | 1593 | `620BE03D04024D12CF091877DA8596F6488FC49AF50F93C220A9E9290FDAFE2D` |
| `localization/english/auto_build_l_english.yml` | 777 | `0672B027F627D2E103AACE685095E5DE7EF8529A15155F2C37B8E2A708A13290` |
| `localization/simp_chinese/auto_build_l_simp_chinese.yml` | 649 | `697FA620ABFAF44FD16B6588A27D1A4E178949C5501D84BE09231260EC8FF1FB` |
| `thumbnail.png` | 96479 | `5F12562FDB9399C1A028DB4BF79308C13CA9566F131EE8B35C2F56C2DDEF33FD` |

## 仓库导入规则

`mod_auto_upgrade_buildings/` 是可维护源码，不是原始证据目录。首个导入只允许一项规范化差异：删除内层
`descriptor.mod` 的 `remote_file_id="3596580780"`。上游 ID 只作为来源身份记录；不得把它当作本仓库维护版的发布目标，
也不得重新写入 canonical descriptor。

运行时修复必须继续保留上游公开的事件命名空间 `auto_build`、事件 ID `auto_build.0001/.0003/.0004`
与角色 flag `enable_auto_build`，除非同时提供旧存档迁移。

## Steam 离线证据

目标目录稳定为 7 文件、127804 字节后，客户端连接日志在 2026-09-11 22:04:34（Asia/Shanghai）记录用户主动登出且不自动重连；
Steam UI 底栏显示“离线模式”。上线前后 CK3 EXE SHA-256 都是
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，未发生游戏二进制更新。
