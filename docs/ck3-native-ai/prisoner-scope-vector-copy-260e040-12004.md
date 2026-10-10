# Ransom scope vector copy at actual260E040

Build1.20.0.4, held SHA98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518.
The actual373ACF0 scope clone calls8895D0 on destination+18, then at373ADAE
calls260E040 with RCX=destination+18 and RDX=source+18. This module supplies
the source-defined vector part to43's logical clone shape, used by35's current
selected prisoner quote. A logical clone has no fabricated numeric native
physical identity.

The exact251B260E040 body spans five `.pdata` fragments. Same-vector RCX==RDX
returns without copying. Its distinct initialized-destination branch reads
the source data QWORD at+0 and signed count DWORD at+C, clears destination
count, and compares that count against destination capacity.48c's independently
closed8895D0 initializer supplies capacity8, data=self+20 and allocator=self+18.

For source count<=8, destination count receives the original signed DWORD.
Counts<=0 enter no element loop, leaving inline bytes undefined and preserving
the nonnull data/allocator self relations. Counts1..8 copy exactly24 bytes per
element, using16B `movups` and8B `movsd`. The native loop performs no element
tag check, constructor, destructor or pointer fixup. Any pointer-looking raw
bits in these cells remain the original copied bits. The observer repeats the
source payload and its pointer/count metadata before exposing this shape.

Relative to the parent scope, data is logical clone+38 and allocator is clone+30.
Only the copied inline prefix `[38,38+count*24)` becomes source-defined. Other
inline bytes remain outside the defined mask; storage's zero initialization
is not evidence of native zero contents. Source data identity is retained as
input evidence and is never used as destination data identity.

These relations also qualify the exact inline free branch: caller supplies
RCX=clone+30 and RDX=clone+38 to vtable448D2A0+10, whose actual target is855830.
At85583A the wrapper forms RCX+8, compares it to RDX at855844 and jumps855847
to the epilog endingRET855869. This branch reaches no backing allocator,
despite the data pointer being nonnull. It is separate from48c's constructor
null-input branch proof.

For count>8,260E098 calls allocator vtable+8 with size=count*24 and alignment8.
Named slot448D2A8 resolves to actual855870, exact held body51B. Root assigned
this wrapper to11. Its allocation result identity and effects are not supplied
by this module, so this branch remains explicitly unavailable here. The target
old count is zero before allocation, so its prior-element migration loop does
not run. No native copy, allocator, initializer or free is executed.

API: `ReadPrisonerScopeVectorCopy260E04012004(access, frame, source_scope)`.
The35 source frame must qualify the same original source scope. The parent
must require `copied_shape_ready` before consuming destination relations or
the defined inline mask. Outer current-query frame and source-clone role
bookends remain with35/43; this leaf performs only guarded source reads.

Necessary no-allocation source was frozen before code in46d/SOURCE-CLOSED-46d.json
SHAaff3eba597939a670c47481cdb70282f583f5c1525a1d5846fdb7abb401b7cff.
Fresh evidence is251 code bytes plus one8B named slot, captured cache-first
under shared D O_EXCL range claims.48c initializer and47b855830 evidence are
reused. The seven new no-main cases join35→10's sole new ransom compound;
the author performs no compile, test or game invocation. Prior46/M7/default
qualifications are neither rerun nor extended to this new source consumer.
