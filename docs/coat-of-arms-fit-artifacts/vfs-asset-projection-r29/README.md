# VFS direct-DDS projection R29（离线回放）

R29 使用 R28 已冻结的 34 条 exact-build 原生挂载回执，在不启动 CK3 的情况下回放新的 direct-DDS winner 投影算法。它用于先验证算法和证据边界，不等同于新 MCP 工具已在原生会话内被调用；该缺口由 R30 闭合。

## 输入与完整性

- 输入：`vfs-mount-order-native-r28/report.json`
- checked-in 输入 bytes：`1,174,238`
- checked-in 输入 SHA-256：`17FA7AFABD23C3EEAF79D346897DDC6984BE75E582F05A06067CD07E44B22093`
- 本目录 `report.json` bytes：`41,070`
- 本目录 `report.json` SHA-256：`A53564585145E1D323137F4AFA2AB23C9EB95A220ABC5F1A85AE2B94A08B8A0A`

## 结果

| 逻辑路径 | 候选 ordinal | 投影 winner | SHA-256 |
| --- | ---: | ---: | --- |
| `pattern_checkers_06.dds` | 3 | base game 3 | `58B4322BBE5046AFEDC4E350F283A1AAEF48A6E86A5A40BF5FDB20321C519849` |
| `pattern_xar_vfs_replaced_earlier.dds` | 33 | earlier mod 33 | `58B4322BBE5046AFEDC4E350F283A1AAEF48A6E86A5A40BF5FDB20321C519849` |
| `pattern_solid.dds` | 3、34 | later mod 34 | `0EE08A10EE4C71278C0ACE98506DD2A520261B20E040B353B7DA4D13C0616C4A` |
| `pattern_xar_vfs_replace_later.dds` | 34 | later mod 34 | `ED859E29211712AC51E2BFF108CBAB58A72B48F62C1D875494CB036979B71A0C` |

四项均有 winner、均绑定同一实时挂载回执，且都显式声明没有调用 CK3 内部 resolver。R29 只证明“完整挂载顺序 + 可检查源字节 + 已由 R22/R23 证明的 direct-DDS 后挂载优先规则”能产生确定性投影。

## 复现

```text
set PYTHONPATH=ck3_autonomous_player\src&& tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\replay_coat_of_arms_vfs_asset_projection.py --report docs\coat-of-arms-fit-artifacts\vfs-mount-order-native-r28\report.json --game-directory C:\SteamLibrary\steamapps\common\CRUSAD~1 --logical-path gfx/coat_of_arms/patterns/pattern_checkers_06.dds --logical-path gfx/coat_of_arms/patterns/pattern_xar_vfs_replaced_earlier.dds --logical-path gfx/coat_of_arms/patterns/pattern_solid.dds --logical-path gfx/coat_of_arms/patterns/pattern_xar_vfs_replace_later.dds --output docs\coat-of-arms-fit-artifacts\vfs-asset-projection-r29\report.json
```
