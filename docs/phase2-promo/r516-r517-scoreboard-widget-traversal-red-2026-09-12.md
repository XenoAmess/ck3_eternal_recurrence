# R516/R517：scoreboard widget traversal RED

## 结论

R516/PID `134936` 完成 authenticated Frontend warm-up 并终止；R517/PID `95796` 随后作为唯一 CK3 加载 product save。loader、native readiness、paused seed、HUD、feature manifest 均 GREEN，FFmpeg 只在上述门禁后启动。

首个 scoreboard source query 被 native 接受，绑定 `snapshot_revision=3`、`date_raw=53147016`、player `29037`、provider session `4782B9D0F7370A534DFDDEBE312FD79F`。它返回 `widget_not_instantiated`，而非 R515 的 `acl_inconsistent`，证明 list-only ACL 修复已经越过原故障。

## 根因与最小修复

provider 已正确先定位 `zg361_scoreboard_window`，再从该真实 window 做固定名字的 descendant lookup；问题是 DFS 的总访问上限仍为 `4096`。当前 `zg361_scoreboard.gui` 有 7,604 行和 4,347 个 widget-like blocks，且 generated list page 大量展开，固定 allowlist 中的后段页面可能在达到旧上限后仍未访问。

修复只把 `kMaximumWidgetTraversal` 从 `4096` 调到 `8192`。固定名字、最大深度 64、单节点 child count 4096、window root、ACL、动作和 schema 全部不变。该 DLL 改动需要新轮次，不能热重跑；不触发 open_kaishek 的接口/协议/数据/version/dependency 同步。

## 证据

- attempt：`Z:\ck3_mod_rewrite\_runtime\p2-capture-r516-r523-6b5eb57-20260912`
- outer report：`166FAC64B7CFDAE30322843098DE751CBEB7AF28C4B11FA97BE04F79A88B82A6`
- inner report：`AB10A4BF9287F254F8CBC365144362682E9550105347872FF52529C4B35C2A81`
- driver state：`479E42313FF688C06D9F8E234E2B417ECBEF97CAD382558C92435059A8C6DCFB`
- cleanup：`C0C536E69F3F49407530381E54A645D6593DC3624235AEE53CAC7846D2BC40FB`
- failed take：3,789,081 bytes，`989AC82615AA8CA196C39A85304EBAB472C6149854D4050462DC6342BAFFD3F6`
- timeline：`784E12A8E3D3C066DC6DF8FD867049C71C174E87BA204F12253252D1F9C5291D`

失败 take 无 clean span，P2 素材仍为 `0/8`。R516/R517 与所有旧轮次均已终止，CK3/FFmpeg 为零。下一次实际启动为 R518 Frontend warm-up、R519 gameplay；只复验计分板 source/open/visible 链并继续八段录制。

## 落地与新构建

- 根仓修复：`183907537ccf2425e8c3ff06de781c3b19f56d5e`，已与 `origin/master` 同步。
- Release bridge：`C4D3B0867CFA1F1337A79CA48324E3DF5E9EF4D657F9D52EDA14D0E2690C6C11`。
- injector：`1C7B547728DB7C9F9AAA79AC5A8E10FE4EF797E81A85B38EF4A1E901924A7F1F`。
- focused test：`C1946DFDCA9229D0C68EB2D2B97A67566A16D3C6910F2B700E7ED33051689B14`，exit `0`。
- build receipt：`8FA23926A39E03871576896E7618DF53F1C516C2C4FADCE453E2D5536D0A7D6C`；全部 candidate switches 为 OFF。

构建未启动 CK3、未消耗轮次。下一次有界 attempt 从该 DLL 和同步后的 root HEAD 建立。
