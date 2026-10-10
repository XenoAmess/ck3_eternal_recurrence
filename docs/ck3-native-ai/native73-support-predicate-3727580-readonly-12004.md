# Actual1.20.0.4 support predicate3727580

The reached literal CALL3727ECF passes RCX=destination support. Its child has
no .pdata row. A64-byte literal seed and32-byte necessary own CFG tail capture
close both RETs in `[3727580,37275D1)`:81 semantic bytes,
SHA-256 `b6fc1f958d8d7b65f65a02cc528d3fd1dcfb17d30db9b080427a80511426e98d`.
The15 trailing INT3 bytes in the96-byte bounded packet are excluded.

The complete function has no memory stores, global operands or child calls.
It first reads signed count10 at support+1C. A nonzero count loads data10 at
+10 and the final32-byte element's DWORD+0C; a signed value greater than−1
returns AL1. Otherwise it loads QWORD data30 at+30 and signed count30 at+3C,
then visits72-byte rows and tests BYTE+44. Reaching the computed end clears
RAX before RET and returns AL0. A matched nonzero row pointer returns AL1.
ScalarDWORD+28, referenceDWORD+48, WORD+4C and BYTE+4E are not read.

The consumed fresh-empty projection reads only copied bytes1C..1F,
30..37 and3C..3F, requiring a defined mask for every byte. Both signed counts
must be0. A defined data30 QWORD is required because the native code reads
it even for an empty vector; its value does not change AL0. Unconsumed
header fields and scalar28 do not need defined masks. Nonempty element
operands remain unknown in this minimal API, including negative counts.

53c owns the source-defined80-byte copied support and calls this pure leaf
within35c's existing current frame. It supplies no physical clone identity.
The20e final helper compares AL0 with SETNE(referenceDWORD+48,FFFFFFFF).
The fresh reference−1 produces DL0, so equality returns before the queue,
lock and BYTE+4E store. This leaf introduces no native evaluation or effects.

53c's new whole-projector fragment covers this new consumed call once in
35c's current quote compound under10. There is no standalone40d fixture or
replay of previous cost, Army, role or calendar qualification. This worker
does not build or run tests. Source contract and freeze precede this code.
