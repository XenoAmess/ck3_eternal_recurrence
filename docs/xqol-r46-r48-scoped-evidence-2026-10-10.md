## 2026-10-10：R46—R48 原用例结果及 R48 同场只读补充验收

本轮沿用同一 Source13 / fd1f 统一运行时。以下是各原用例的限定范围证据，不把单例结果推为整个 QOL 产品发布通过；正式产品仍为原 27 文件。没有重跑已通过业务，没有改写旧输入、原日志或原 public run/verify 退出码。

- **R46 / a146，`selfpaid_ransom`：限定用例通过。** public run=0、verify=0，原 12 个自然日完成，12 个 required 各出现一次、两个 forbidden 均为零。实际验证正常全额自付赎金、1 金自付赎金及 landed 自付者排除，case/gui qualified=true，business_pass/product_release_pass=false。统一自动正常退出 qualified=true，保留的 OS handle 实际 exit=0、严格 native zero proof=true，keeper 与 allocator 实际 exit=0，CAS **8055** 已释放、resources=[]。
- **R47 / a147，`pam_positive`：原基线失败，业务未执行。** public run=2、verify=2，原 25 个初始化原子仅 `actor_sf_le0` 为 FALSE、`actor_sf_ge0` 为 TRUE，其余 24 个为 TRUE。实际 actor full CharacterID=34422、target=47030；这里只能证明实际精神满足度为正，未证明具体值或来源。原 `SF==0` 断言与后续奖励断言不放宽。统一失败关闭实际完成：保留的 OS handle exit=0、failure_shutdown_proof=true，keeper/allocator exit=0，CAS **8064** 已释放、resources=[]；`normal_close_qualified=false` 和原 RED 仍保留，不能记为正常关闭验收或 PAM 通过。
- **R48 / a148，`religion_rite_outcomes`：原 run=0、verify=2 保留；同场只读补充验证原宗教边界通过。** 原业务自然推进 2 日，11 个 required 各一次、forbidden=0。旧验证器将初始化 scope 中的全日志长度/SHA 与两日后完整日志直接比较，导致误拒。实际差异只有 `log_bytes`/`log_sha256`：初始化日志 1,727,230 B，最终 1,742,417 B；最终日志的初始化前缀 SHA 精确等于原记录，full CharacterID=34422、scope 原始块、所有边界与其他字段完全一致。5679 B 的最小验证器修复同时严格核对完整最终 raw pin、原初始化前缀 bytes/SHA、原完整 scope 及最终稳定 scope，未忽略真实漂移；一个新增纯回归覆盖成功追加与 14 个拒绝分支，已有测试未重跑。同场补充仅读取原有字节，case/gui qualified=true，business_pass/product_release_pass=false；未再次运行 public verify，未修改旧 prepared/hook/result。原统一自动正常退出 qualified=true、保留 OS exit=0、严格 native zero proof=true，keeper/allocator exit=0，CAS **8072** 已释放、resources=[]。

R49 / ordinary_async 诊断截至本次恢复仍为 **PREPARED_ONLY / NOT_RUN**：现有目录只有准备及差异证据，没有 R0049/a149 分配或运行回执。不得把 R45 的旧失败猜成已取得 R49 原诊断原子。PAM 精确 0 初始化也仍待合法来源修复；当前 .4 的动态 change 会受 modifier、定点精度与小于 1 点不执行规则影响，`-current` 不能预授为通用精确清零。

以下 SHA-256 均为完整值；表内路径前缀 `C10` = `C:/workspace/ck3-upgrade-20261010`。

| 证据 | 路径（相对 C10） | bytes | SHA-256 |
| --- | --- | ---: | --- |
| 唯一运行时选择 | `root-source13-adoption-01/runtime.adopted-source13-native-fd1f-queue04-05.json` | 10820 | `a5aecdf94d6e3dcf35f2462011ba6a743668605729627f6d272542cf8c460e91` |
| Source13 manifest | `shared-source13-prepare-01/SHARED-RUNTIME-MANIFEST-SOURCE13-NATIVE-FD1F-01.json` | 46108 | `26b229556f0b97cfac3b7d0172dd55f97f39f410c476de97f01a0eb1c5361c18` |
| R46 原结果与完整关闭 | `qol-original-cells-runner-01/selfpaid_ransom--a146-path02/POST-RUN-CLOSE-05.json` | 4457 | `37a28c626498ebfc58300daec53165de2d9a1ca70d1abc76d1e16f6711f3df1f` |
| R47 原失败与完整关闭 | `qol-original-cells-runner-01/pam_positive--a147/POST-RUN-CLOSE-05.json` | 3683 | `8fe8b4a499cc6729a4519982172c507feb1bd8d651d3ee5c7917c1d83f62a580` |
| R47 当场基线诊断 | `qol-live-pam-ordinary-readonly31/r47-actual32/ROOT-R47-PAM-BASELINE-DIAGNOSIS32.md` | 3651 | `640d7806d791c1a0319311fbf8d4656597a8c19f9daac34a2ccdcb055e889e68` |
| R48 原退出码与完整关闭 | `qol-original-cells-runner-01/religion_rite_outcomes--a148/POST-RUN-CLOSE-05.json` | 3651 | `dafabb44e6f5b3fd6670f98d483f213cde91dcea7cb6245073fd520a82269549` |
| R48 精确前缀/scope/marker 薄诊断 | `common-religion-append-verifier-01/R48-RELIGION-SCOPE-APPEND-THIN-01.json` | 3948 | `823092353aae3432a862801aa7fbede5a04b3c1766f114f8ea051470a507ebd7` |
| R48 同场只读补充验证 | `common-religion-append-verifier-01/R48-READONLY-EXISTING-BYTES-CANDIDATE-VALIDATOR-FINAL-02.json` | 3672 | `605aa910f22780a0ab8ef39b08f5126fcf3e459cf2e630e93f70cea616465c00` |
| 最小修复及单回归候选 | `common-religion-append-verifier-01/CANONICAL-RELIGION-APPEND-VERIFIER-WITH-SINGLE-REGRESSION-FINAL-02.patch` | 5679 | `7055cab389cfe757563b6cbfdd8aec839ddb927b42a939a17f93c27581a462f4` |
| 修复离线检查与补充消费卡 | `common-religion-append-verifier-01/COMMON-RELIGION-APPEND-VERIFIER-FINAL-02.json` | 2710 | `e677fed106db7246ffbb7f6fd08aa65fcf89946f87636d31b67fa63091cf7fd1` |

R48 原最终 raw 位于 `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0048/case-output/religion-debug-original.raw`，1,742,417 B / `bdea356a57917ef53c6a1697d53f8289d3a8a690b8d958e1533b83bf3f334c72`；初始化前缀 SHA 为 `8fa9a61c8e07ae13e9d79bad2f7622a63716a110a43cc0745ba4af1a351c5c74`，scope 块 307,442 B / `3467dc166a505fb8898bc396314b0551d1a0207fd1d6359509053d1dd2afe910`。完整原始结果、frozen argv 与源/合同 pin 由上述同场补充回执绑定。
