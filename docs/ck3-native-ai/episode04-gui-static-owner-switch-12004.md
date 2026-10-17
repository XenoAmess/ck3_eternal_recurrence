# type635 静态来源 owner 的只读补员开关（1.20.0.4）

本增量复用既有 military tree/opener 返回 family，在稳定的 `definition_frontier_continuation_depth8_12` 内增加可选 `static_direct_owner_switch_12004`。没有新 MCP、query、hook、provider调用、临时变量表求值或游戏写入。`XAR_ENABLE_GUI_REFILL_STATIC_OWNER_SWITCH_12004` 默认OFF，ON要求既有frontier continuation ON（后者要求parent prefix ON）。

依据是机器 `desktop-3fevhd2-1c74096080` 的 R194/a32 实际静态来源：depth8 first key635 match为mode1/flag1/direct非空，其+218解析Character31254且完整代际/Char magic通过。原 full depth8/read51/pass1 unavailable保留；新叶只说明该来源Character的开关输入，不代表native已选择最终receiver。R194没有新开关叶，不能追认raw4A9实机资格。

完整 `.4 12FF8D0` source（SHA `ce0f29a8f9228a72d7dc913150238fe2a0bdbbe660353d425fa377653aa11a0e`）给出：12FF8EC receiver+218；12FF91D Character+1C0；12FF929 military+4A9；12FF932 null military合成0。本实现不调用该会构造命令的原生函数，只在原continuation已验证Character的分支复用同一个4096reads/64KiB/20ms预算safe-load；不取fallback、不用当前玩家或Army身份替代owner。

两次原capture分别读取新字段并独立join。新字节不可读/两次变化只使新叶unavailable、观察值清null，不抹去已独立稳定的mode/flag/direct/owner来源。新读仍计入原共享预算；总预算耗尽时原整体预算门继续生效。不开第三次捕获，不添加额外理论fence。

| 结果 | raw_byte_4a9 | enabled / value_basis |
| --- | --- | --- |
| 可读nonnull military，raw0 | 0 | false / raw_military_byte |
| 可读nonnull military，任意非零raw（包括2） | 实际0..255 | true / raw_military_byte |
| 实际 military pointer为null | null | false / native_null_military_zero |
| 身份未核、不可读、变化、来源不适用 | null | null / null；status unavailable并保留原因 |

available还要求owner_full_id与同depth parent entry的已验证owner完全一致、mode1/flag非零/direct非空，`stable_double_read=true`。`current_variable_table_observed`、`native_receiver_selected`、`provider_invoked`始终false。堆地址不发布；native source frame/public绑定原样保留。旧生产profile缺叶保持unknown，严格consumer不会补0或false。

新增4个Python用例通过生产callback consumer，覆盖raw0/2/null分支、读取失败与变化的独立资格、owner/depth和raw/basis派生反例、旧叶缺席及owner未核。受影响的R194实际643行census兼容消费通过，明确新叶仍缺席。没有重跑全矩阵。

新增同源native focused fixture直接调用生产reader及serializer：ON输出8行（raw0/raw2/null组件/byte不可读/组件不可读/字节变化/owner失配/flag0被过滤），OFF输出1行并证明未读+1C0/+4A9。目标 `xar_test_gui_refill_static_owner_switch_on_12004`、`xar_test_gui_refill_static_owner_switch_off_12004`，均独立header-only、C++20、MSVC /W4 /WX /EHsc，无runtime链接，无assert依赖。此lane禁构建，native compile/run/wire均 **NOTRUN**；未来Root正常producer+精确EXE资格后执行，再用外置 `run_focused.py --repo-root <integrated-repo> --wire <ON.jsonl>`，OFF加 `--off`，通过实际生产strictconsumer。不得把fixture与Python结果称为游戏开关或补员业务结果。

来源基线 `d7135ca3bf40c33c2d5416242ce844077f1e8cbe`；构造、测试、最终target pins与相对patch见外置a42 delivery。没有新EXE源读取、SDK、桌面、主树写入或native构建。
