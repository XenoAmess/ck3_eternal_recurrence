# Construction context pointer membership — actual30A6080

The M4 context parent at actual2C25010 calls30A6080 at2C25026. RCX is the
actual04 returned selector object, copied from the parent's entryR8. RDX is the
copied first pointer, from the parent's entryRCX. The parent tests AL at2C2502B;
true takes its literal AL1 return. The paused03 snapshot revision and copied
operand identities are retained by the typed child adapter.

The actual child is125 bytes,30A6080..30A60FD, with held pdata row
`[51011712,51011837,84977560]`. The finite source was frozen before code,
looked up through the shared cache, then acquired once as125 actualnew bytes.
Its reconstructed SHA and exact instructions are in
`continuation-37c/source01/ACTUAL-30A6080-DETAIL.json`. It has no calls.
The source identity is CK3 1.20.0.4 / Steam25734779,
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

The body loads the qword array pointer at receiver+420 followed by the signed
dword count at+42C. For a positive count it repeatedly probes index(count>>1),
compares the copied qword with RDX as unsigned64, advances the base by
(oldcount-half)*8 on below, and halves the count. The native collection order is
preserved. After the loop it compares the candidate pointer with the wrapping
end pointer. An equal end returns AL0 without a candidate read. Otherwise it
copies the candidate qword, returns AL0 when RDX is below it, and uses the low32
candidate index comparison with-1 for the final AL.

A zero count reaches the equal-end path, even with a known null payload.
A negative count skips the binary loop and still takes the final head probe
when the candidate differs from the computed end. Raw zero and high-bit pointer
values retain the child source behavior. The leaf does not sort, deduplicate or
assign a government/object label to the collection.

`ReadConstructionPointerMembership30A6080V1` implements this source tree over
the admitted raw reader, copying at most32 qwords and retaining its probe trace.
`ReadConstructionPointerMembership30A6080ChildV1` is the exact21c typed callback.
The actual arguments must match the copied ContextPredicateInputs selector and
first pointer. Missing reached header or payload copies keep AL unavailable.
Callback availability false leaves the caller's bool unchanged; availability
true can represent native ALfalse. Unreached payload fields are not demanded.
No native getter, allocator or process-clock capture is executed.

The fresh no-main fragment
`RunConstructionPointerMembership30A6080FreshCases12004()` covers zero, positive
and negative counts; duplicate and unsigned high-bit values; exact probe order;
an unsorted source path; missing reached copies; argument binding; and the
availability/nativefalse distinction. Its first compilation and execution
belong to21c/03→10's unique combined qualification. This leaf is SOURCE_NOTRUN.
Earlier Army, person and native qualifications are reused without replay.
