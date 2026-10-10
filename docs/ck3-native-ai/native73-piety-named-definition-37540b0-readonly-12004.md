# Actual37540B0 named-definition numeric projection

Actual CK3 1.20.0.4 Steam25734779 source is the complete 534-byte runtime body
`37540B0..37542C6`, SHA-256
`6800f437dd8a2e909a4ef05c2e2cdc35f58a627217ea56a1e04a61849dcccc09`.
The source and tree were frozen before this candidate.

ActualA0F0B0 calls this body at A0F2AF when expression+B8 is nonzero,
provider+B0 is NULL, literal R8 is zero and named-definition expression+A0
is nonnull. RCX is that selected named definition; RDX is the actual caller
pack, and R9 is the original named tuple. This candidate does not resolve a
name or replace the selected identity.

The numeric branch loads QWORD named-definition+70. If it is NULL, BYTE+7A
controls whether 3754213 replaces the initialized EDI0 with DWORD+60. The
return 37542A3 copies EDI to EAX. A zero byte returns source-defined zero and
does not require a readable DWORD+60. A nonzero byte preserves the exact
DWORD as signed int32. Pack, inputR8 and named tuple have no numeric demand
on this closed branch.

`ReadPietyPriceNamedDefinition37540B0Readonly12004` uses the common22e guarded
access ABI and takes actual named-definition identity plus unchanged full64
revision. It copies only demanded branch operands and recopies them before
publishing optional EAX. Equal bookends express conditional copied-input
consistency; they do not prove an atomic snapshot, freshness, profiler
effects, or actual native consumption. Missing access, a read failure,
changed operands or nonnull provider leave EAX unavailable.

The nonnull provider branch calls vtable+30 with provider+8, temp output,
original pack, original inputR8 and original named tuple as stack5. It then
calls 37498A0(temp, original named tuple). That frontier remains unknown.
Optional profiling calls 9DC3C0, 4221DB0, 40C62D0 and 37421C0 are also outside
effect qualification. This adapter executes no native producer or profiler.

The no-main fragment `RunPietyPriceNamedDefinition37540B0Focus12004` is new
and remains unexecuted locally. It belongs in the connection owner's sole
new numeric compound. Prior44 prefix and cleanup qualifications are separate.
