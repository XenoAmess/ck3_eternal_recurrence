# Promotion source product/native dual-build freeze (`1c69658`)

## Result and honest boundary

The schema-4 formal no-launch result is `READY_TO_SERIAL_LIVE` on canonical
`1c696588dfdb02f9be051220db06cf303f3f9f99`. The native bytes were built from
`cac1e85b616827a9ae11d755dd71f119325e6f3f`; the intervening commit changed
only the Phase2 runner, focused tests and ledgers, and the verifier confirms
the native aggregate remains exactly equal. The current runner is separately
pinned at SHA-256
`C737547F103D8068A64E77721A5C8EAF7FE6625AB074014F14EDF9C1DCDA4548`.

This freeze did not start CK3 and does not claim paused-live evidence or
production advertisement. It deliberately records two different builds:

- the B7 default build has all 23 `XAR_CK3_ENABLE_*` flags OFF;
- the B3/Phase2 live candidate has only
  `XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1=ON` and the
  other 22 flags OFF.

The ON build is private candidate evidence, not the default or a production
promotion. The descriptor source gate added at `cac1e85` is present, and both
configurations pass the adapter-registry contract.

## Source and validation freeze

| Scope | Files | Bytes | Aggregate SHA-256 |
|---|---:|---:|---|
| tracked `mod_zhongguo_style` product tree | 975 | 81,920,855 | `C6860A0986E30F8D78621D1F26E345C45FEA2476FEED3CBB1E7956293C2F3E29` |
| native C/C++/CMake source | 298 | n/a | `18738E1C38A542E5B3AE8CE8179D29366DC5CE39D7DAF2C5BCBB71B8664CBB81` |

`validate_local.py`, both effect generators in `--check` mode, and the Phase2
central runtime generator check are GREEN. The explicit-AND trigger, its
generator and its focused test have individual hashes in the manifest. Effect
shards remain within the requested boundary: feedback/promotion/PIP has 275
effects in 39 files at 1-10 per file; compensation/LTI has 148 effects in 25
files at 3-9 per file. No file exceeds 20.

Both fresh MSVC Release configurations passed **94/94 CTest**. The discarded
r1 configuration attempts selected Cygwin Ninja from ambient PATH and failed
before compilation; neither appears in a candidate root.

## Frozen external evidence

Default root:

`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-product-native-default-candidate-cac1e85-20260904T104203Z`

Compensation-ON root used by the single future command:

`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-product-native-compensation-on-candidate-cac1e85-20260904T104203Z`

| Profile/file | Bytes | SHA-256 |
|---|---:|---|
| default `xar_ck3_bridge.dll` | 2,425,856 | `BB10E12E0A166B9E405FE6E712F352D178377909EF5B672D3108E68A4001F4D7` |
| default injector | 39,936 | `FBCD994CDE7934AC9B34D08551397CDBBB0677C038B098EADD9E183E3B7AC1C5` |
| default cache | 20,072 | `6DCFB0D07DEE6F9B4A9682504A57E9C057BEE00BBF58C127AF593D48994E3268` |
| default CTest log | 18,767 | `2F64ABECF0BAC21FF0DEB95186060BE3BB34B2926DB224C6EE6DC9EFBDEAB7E8` |
| compensation-ON `xar_ck3_bridge.dll` | 2,425,856 | `1A787A9F7D8429DB7E8B4DCE3879E59FB1D793BAF5A1BAEE07D8E915F286BCD1` |
| compensation-ON injector | 39,936 | `FB73AFBD8CFF64F26F2B3FA3E1C46C9B6ADCF52193403DD56D06AB8D319EB870` |
| compensation-ON cache | 20,071 | `C2F07C2ABC428DD102B135C6D2B48F4447B70B46D1C915E717680CB401018404` |
| compensation-ON CTest log | 18,767 | `06391F9A741E932A22ACACE7A6C188F46B739DFADDB03CE0E652B3F3983B7CF1` |
| frozen schema-4 manifest | 11,375 | `E2AF344F3E72FEF018DBE51ADB3DC2960A8828179CBF0A4B079D1B31FC122911` |
| formal no-launch cell | 12,964 | `C23902114E31E6B7CE4CA01934AF901AFFE2DEAD117870ED14B8C5CCAF8F3276` |

The previous schema-3 manifest remains immutable at SHA-256
`E778470FF5733E0E5A737F192B82B1B29F52DF2CBBAB5BA7D0BE46C40B13AE5A`.
It is RED on current source; the schema-4 verifier extends it by exact hash,
adds the complete product fingerprint and two exact cache maps, and removes no
current source fingerprint check.

## Exact capability flag profiles

The complete flag names are:

`COLD_MAP_VFS_OBSERVER_V1`, `G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1`,
`G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2`, `G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1`,
`G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1`, `G2_TRUCE_PRIVATE_CAPTURE_V1`,
`G2_WAR_BOUND_LOSS_CANDIDATE_V1`, `G2_WAR_BOUND_PRIVATE_CAPTURE_V1`,
`PHASE2_COMPLETION_OBSERVER_V1`,
`PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1`,
`PHASE2_POST_CALL_OBSERVER_V1`,
`PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1`,
`PHASE2_PRODUCER_IDENTITY_OBSERVER_V1`,
`PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1`,
`PHASE2_WRAPPER_ENTRY_OBSERVER_V1`, `STARTUP_FAILURE_CONTAINMENT_V1`,
`STARTUP_PARTICLE2_STAGE_RECORDER_V1`, `STARTUP_RBX_NULL_CALL_GUARD_V1`,
`STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1`,
`ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1`,
`ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1`,
`ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1`, and
`ZHONGGUO_SCOREBOARD_PRODUCTION_V1`, each with the `XAR_CK3_ENABLE_` prefix.
All are OFF in default; only promotion-compensation is ON in the private live
candidate.

## Single future serial command

The manifest freezes one runner-owned command using the compensation-ON pair,
pipe `\\.\pipe\xar_ck3_bridge_zg361_73b910c45fd64f098cc2d6791eaaba52`,
and absent artifact root
`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-product-native-live-attempt-cac1e85-20260904T104203Z`.
It has not been executed. Readiness stays `static-ready-live-pending` until the
serial CK3 gate produces and reviews a real paused `zg361pp.147` artifact.

## R9 top-level instantiation finding

The later `f3af7e0` R9 attempt proved that the fixed query reached a stable
paused played-owner frame but returned
`widget_not_instantiated` for the promotion root and all four descendants. CK3
did load the `.gui` asset, so asset loading alone is not evidence that a
scripted top-level window has entered the GUI owner's searchable instance set.

The follow-up candidate appends a fixed, read-only comparison to the existing
unavailability string: it asks the same exact-build `FindTopLevelWidget` ABI
for `zg361_scoreboard_window`, `zg361_decision_bridge_window`, and
`zg361_mechanism_bridge_window`. Caller input cannot select names. This is a
diagnostic distinction only: the promotion result remains unavailable and no
action capability is promoted. The MSVC Release compensation-ON build at
`Z:\b3probe-msvc2` passed 94/94 CTest; DLL SHA-256 is
`3CC51415C225792A0D09E8B937A207D588BFD471C79220A301AF8C7DE553D9D6`.
