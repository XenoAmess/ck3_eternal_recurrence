# Phase-two runtime caller `0x3407D9C` (2026-09-02)

The bounded wrapper-entry live is GREEN: runner SHA-256
`0556C55EF7D26535A8D9B5F0199BCA32CDB178323DE95F48678B2D38B4683BE7`
and postprocess SHA-256
`D74E8345B51E87F73B5DF6C65B7766B4618748FCE0FD8DFD9CD374D736B054F8`.
The final heartbeat reports 1,220 total entries and last sampled tuple caller
`0x3407D9C`, scheduler owner `0x22ED9921A00`, producer-list carrier
`0xF282FFEE70`, thread 44900. Only one final heartbeat is retained, so this
identifies the last sampled caller and must not be described as the distribution
of all 1,220 entries.

The callsite belongs uniquely to PDATA function `[0x3407C70,0x3407F80)`,
unwind `0x4C3DD40`, full bytes SHA-256
`A262CC81AFD1235583E2AA6618D48106CA1557BB227AF6A0DAB63CBC60000F17`.
The stripped executable supplies no source-symbol name; PDATA and full-function
bytes are the exact owner identity.

Before call `0x3407D9C`, `RCX` loads the scheduler owner pointer from global RVA
`0x5772E98`; `RDX` is a caller-local object at `[RSP+0x30]`; `R8` passes through
the function's third argument; `R9D` is a derived batch count after excluding
empty range, mode 3 and count 1. The fifth wrapper argument is the address of a
caller-local producer-list at `[RBP+0xE0]`; the sixth passes the caller's fifth
stack argument from `[RBP+0x260]`. The producer list stores a begin pointer at
`+0x0`, count at `+0xC`, and descriptor pointers whose task and owner fields are
at `+0x18` and `+0x20`.

Normal continuation is `0x3407DA1`. The local argument object is destroyed
first. If the destination descriptor list is empty, `0x3407DCC` calls
`0x3B67B80`; otherwise `0x3407DE1..0x3407E0D` appends through `0x3B67DE0` and
clears source storage with `0x817F80`. The caller then releases producer storage,
performs reverse and forward state-zero retry sweeps over the destination list,
releases tasks and destination storage, and normally returns at `0x3407F7F`.

The next distinct private seam is the exact post-wrapper continuation
`0x3407DA1`. Bytes `[0x3407DA1,0x3407DAF)` form a 14-byte instruction-aligned
anchor `90488B4C24684885C97411488B01`, SHA-256
`65A4228B227424B730FA6F7A84DD15602E2063FD9227733901135CF00E4805A4`.
A read-only observer there can inspect `RBP+0xE0`, its begin/count, each
descriptor task/owner, task callback vslot2 and state, filtering vslot2 target
`module+0x88B480`. This captures the selected synchronous task before the
producer-list transfer, retry and release paths. It is proposed only; this static
package does not install it or start CK3.

The reproducible extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\runtime-caller-3407d9c-static-extract.json`,
SHA-256 `4D79ABEBBB2AA41A02E0762B4874DB85768BD8A5A45B648FD91D5495DF27817D`.
