# Episode02：R0149 增援与完整同帧补证

2026-10-02，本轮独立从 D11 检查点载入，只推进原版一天：1066.12.14 → 12.15。实际原版加入链、完整暂停画面、两份不可变存档均完成核对；这组证据用于 a08 视频优化。R0148 的六项受控骑士机制结论保持独立，见 [六项缺口结论](episode02-r148-six-gap-closure-2026-10-02.md)。

两张新原图都在一个帧内包含日期、暂停、双方身份、战斗窗全边框、底部全部兵种/骑士行及完整相对军力提示。面板上方人数 893/1603 → 827/4106；提示中另一个人数口径 827/1546 → 740/4047；基础战宽 1645 → 2467、最终战宽 1480 → 2220、森林 90%；底部我方 11 → 11，敌方法里斯 13 → 17。不能把不同人数口径或事件瞬间混写成一个字段。

原生记录有 7 个阶段、3 个增援/战宽边界与 2 份完整 entry，flags 均为 0。Army22 新增 13 条兵团记录，敌方条目 27 → 40、我方 24 → 24；原 51 条 entry 的九列在加入入口至返回保持一致。返回时两侧缓存分别对齐 entry 总量，基础/最终宽度写回，首个敌方出伤收到宽度 2220。次日存档与 UI 时刻又存在真实缓存差值，原值保留，不把原生 hook 写成暂停 UI 同帧。

前存档 rev4/native3 与前图 rev5/native4 属于同日期的不同快照；后日存档和图为 rev8/native7。两份存档通过真实 Rakaly 0.8.19 解码，51 项端点核对通过；原生独立审计 132 项通过。global bundle / original trace readiness 仍为 false，不外推整场战斗、未来到达或所有条件。

证据位于 `C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0149-actual-join-control-audit-reinforcement-a01/`：

- `R0149-finite-reinforcement-facts-a01.json`：21,669 B，SHA-256 `A91B333219864C161999FE74D4C6040B05A9EBCBA2D9BB3D9E8C1EC6C3D19819`。
- `R0149-finite-reinforcement-audit-seal-a01.json`：40,502 B，141 文件，SHA-256 `CB92CEF25B3D59C3BF4C658B6BB6C8B1AEFE2FB02300E9D20E1AACFB035D5E9D`。
- `native-final-a05/R0149-current-original-join-phase-control-audit.json`：395,820 B，SHA-256 `EF56443D98ADAD30596E630F67BFF87602B0E37C8F3A557AF90F74FF540B22C2`。
- `saved-endpoint-decode-a02/R0149-two-save-finite-combat-endpoint-verification.json`：10,263 B，SHA-256 `2DA691ECEB03D3A335FB294E563500DE0EF8466009A74E3461C829270892FD7C`。

游戏与注入器已停止，SDK completion actual exit 0；原桌面 1024×768 已实际恢复，新 Steam CK3/BG3 两张原图都直接审阅为离线。screen CAS 3645 已释放资源，其过期 claim 的 `business_status=unresolved_red` 原样保留，实际完整采集完成由 root 独立回执说明。root 回执为 `C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-13-reinforcement-full-frame/R0149-root-finite-capture-completion-a01.json`。

历史 evaluator RED、失败 stdio、初次缺 pair 的预检、后存档入口错误和所有原图/存档均永久保留。本研究停留在私有分支；没有拉取、合并或推送 master。a08 的机器检查与人工按 1× 完整观看签核仍是不同交付条件。
