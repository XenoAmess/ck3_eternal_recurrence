# Guardian factory private capture: Windows path boundary

The Native73 R0090 family read succeeded, but its private factory enrichment
failed because the SDK sent a Windows path that the native control parser could
not read. The retained `family-result.json` was available at native revision 2,
date 53290128, with first heir 38822 and spouse 38718. The private capture failed
with `family query produced no private sidecar; retain family-result.json`.
There was no retained native command-result object from that call.

The exact production chain explains the failure:

1. The capture helper constructed a Windows `Path` for
   `guardian-two-factory-source.json` and passed it through the connected driver.
2. The private family transport serialized `str(sidecar)`. The endpoint's compact
   JSON encoding escaped its backslashes.
3. Native `JsonStringField` accepts unescaped strings and rejects every
   backslash. The family branch discarded the failed parse, leaving an empty
   path. Its nonempty-path gate then omitted the existing factory discovery job.
4. The independent family observation still completed successfully.

The transport now uses `sidecar.as_posix()`, preserving the same absolute
Windows destination while supplying a string accepted by the existing native
parser. Ordinary family queries retain their response shape. An explicit
private capture also preserves the command-result JSON object before family
normalization as `guardian-family-command-result.json`. This is an owned JSON
object, rather than a claim to have retained the original pipe bytes.

The private native envelope records path parsing, job creation/reclaim,
execution/frame/metadata observation, completion attempt, file writing and its
actual error. These stages remain separate from family availability. A written
sidecar can still contain two unavailable rows; a qualified frame can still have
missing factories, unreadable slots or an outside-image slot with no RVA.

The existing discovery provider already reads only the two fixed keys
`has_relation_guardian` and `has_relation_ward`, their lookup records, four
unassigned virtual slots and bounded RTTI. This repair adds no provider,
initializer, Create/Evaluate call, guardian membership claim or pair readiness.
Create and Evaluate meanings require actual captured metadata and subsequent
source closure.

The new permanent boundary fixture is
`native_bridge/tests/guardian_factory_sidecar_transport_focus.cpp`, driven by
`tests/guardian_factory_sidecar_transport_focus.py`. It connects the production
SDK request encoder to the unchanged native parser and sidecar completion,
reproduces the old path rejection, preserves the original family result object,
checks private write-error reporting and emits two explicitly unavailable rows.
It performs no Game query and supplies no actual factory or ABI facts.

Source evidence is frozen in the external repair packet's `SOURCE-FREEZE.json`
and `ROOT-CAUSE.json`. The actual R0090 failure and original normalized family
remain unchanged. Test execution and the eventual cold SDK/runtime outcome are
reported separately in the packet's final delivery; the running SDK73 is not
modified by this repair.

The sole new connected compound actually passed: two `/W4 /WX` C++ compilations,
one paired link and one Python compound returned zero. Python invoked the new
native boundary executable once; no old metadata/lookup fixture, Game query or
factory evaluation was executed. The result is recorded at
`native73-guardian-sidecar-audit/focused-guardian-sidecar01/RESULT.json`.
The exact new EXE's Defender request was rejected by its source-provenance
validation and settings were not changed; exclusion remains pending. Whole
Bridge compilation and the next normal cold SDK/runtime adoption remain Root's
separate boundary.
