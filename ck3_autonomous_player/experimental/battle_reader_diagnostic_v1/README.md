# Uncompiled battle-reader diagnostics

These two review patches retain a completed research candidate. They are not
applied to the production Native or SDK sources and are outside all release
targets. `provenance.json` pins the original patch and source identities.

The production bridge currently collapses nonavailable battle-control reader
statuses into a stable `typed_result=false`. Actual P27 responses 50/54/58
prove that observation, not the failing reader predicate or an ABI defect.
The Native patch propagates diagnostic status/stage through the existing
reader; its SDK companion validates the optional diagnostic fields without
granting prediction, retreat, action credit or replay permission.

Only apply-check and the original Python packet-contract checks were completed.
Affected Native consumers still need compilation/link validation and the SDK
and external classifier need pairing before any controlled deployment. There
is no Native build, live-read success or speed improvement claim for this patch.

Keep this directory as review input. Do not apply either patch to a running
SDK/DLL or count it as part of the Native21 release.
