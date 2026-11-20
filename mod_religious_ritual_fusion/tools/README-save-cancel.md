# 取消前后物理存档比较 / Cancellation Save comparison

The existing `inspect-save` CLI accepts request version **3** only with the
`cancel_unchanged` expectation. Version 2 `inspect_only` and `fusion_selection`
requests retain their existing contract. This is an offline inspection tool;
it never starts or attaches to CK3.

```text
java -Djava.io.tmpdir=<approved-D-temp> --enable-native-access=ALL-UNNAMED -jar <packaged-app>/quarkus-run.jar inspect-save --inputs <bound-request.json> --output <unused-report.json>
```

Bind the actual runtime actor ID, before/after Save pins, decoder executable
pin, current fixture manifest and public `profile-preparation.json` pin.
`save` is the after-cancellation Save; `expectation.beforeSave` is the physical
before-cancellation Save. Neither a historical character ID nor an authored
software fixture ID establishes the live actor. Both files must already be
immutable, separate physical files; different SHA values are not required.
Hard links to one file are rejected. Actual GUI actions and the independent
Save captures remain the Runtime owner's evidence.

The existing `layout` and `selection` identify actor/source Rite/Faith/Religion
records. The expectation's typed `inspectionSelection` additionally requires
exactly one House and Dynasty, metadata, all six required table kinds, no
projections and no structure-census substitute. Paths and IDs must come from
the actual Save. Missing, incomplete, malformed or overflowed input fails;
there is no fallback to an empty inventory or a count-only oracle.

每份 Save 经实际 decoder 完整流式读取两次，分别枚举 Rite 与 Faith 的全部
numeric ID，以及 `none` 槽位；两次完整流的 SHA/字节数必须一致。前后各自
`Inventory=OBSERVED`，且完整 live/none ID 集合相等，才报告 `noNewObject=true`。
每表最多 200000 槽，每个无 discriminator 记录最多 512 KiB，完整枚举预算
64 MiB；超限拒绝，不把部分读取报告为完整。没有生成完整 melt 临时文件。

The comparison reads exact saved Piety currency (decimal text, no float),
current Rite/Faith, House/Dynasty, fixture source references, source core
contract, and full selected source/House/Dynasty records. Campaign/date and
saved-version metadata must match. Result references, charged-cost/cooldown
and committed/unresolved state are forbidden at this cutpoint. Other
persistent variable/list records must remain equal. The only permitted draft
differences are explicitly reported presence/duration differences of the four
**empty** candidate/selection lists and the **empty** `rrf_family_converts`
preview list, all explicitly cleared by the production cancel chain.
Whole-actor equality is neither required
nor used as the oracle.

Before and after must both be closed: absent `rrf_state` and explicit `idle`
are kept distinct and cannot be interchanged. `editing`, `committing`,
`unresolved` and `succeeded` fail. Therefore the intended UI sequence is:

```text
closed draft -> beforeCancel Save -> open -> cancel -> reopen -> cancel
             -> afterCancel Save -> unique production confirm -> afterCreate Save
```

The afterCreate Save uses its own existing fusion-selection and business
checks; it is not an input to this cancellation comparator.

Windows evidence uses a read-attributes/share-read-write-delete handle and
actual FILE_ID_INFO volume/file ID plus created/written/changed metadata.
Both Save identities and the decoder identity are rechecked across the pair;
access time is excluded because reading can change it. Reparse files,
directories, delete-pending files and unavailable identities fail. The small
RRF-local boundary reuses the project's existing JNA version and does not load
the CK3 control service. This detects observed identity replacement; it is not
a claim that external writes were impossible.

Success emits typed `rrf-save-cancel-inspection-v3` evidence with both physical
pins, exact actor values, complete ID sets and explicit draft differences.
It proves the stated persistent snapshot comparison only. It does not prove
that no transient object ever existed, that the whole world is unchanged,
that GUI actions occurred, or that a production callback ran before adoption.
The test-only `melt` child and authored worlds are software fixtures and are
never evidence of actual CK3 decoding or a live cancellation result.
