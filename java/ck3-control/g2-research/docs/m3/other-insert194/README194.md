# Other insertion caller binding 194 — package 58

This source-only package connects the actual MapInsert191 call at C3BBC1 to the 23-byte C3A5F0 wrapper. The binding derives wrapperBodyRsp from the current result RDX minus 0x70; the wrapper derives its child body by a further 0xB0. Eight remaining typed callbacks forward to the supplied fallback.

The package adds two main sources and one manual witness. Build from these three sources plus the five existing source files listed in SOURCE-LIST194.json. Run org.xar.ck3.research.m3.other194.OtherInsertWitness194 as a manual main. Its byte script uses one ordered cursor and explicit mapped input/effects; it does not need the old 191 Book or Host. No Maven or CI integration is added.

The parent recorded the first two-source production strict compile at 2026-10-31T21:29:26.108635–21:29:26.638481Z (0.5298429 s, exit 0). The one new witness strict compile ran at 21:31:03.877103–21:31:04.743401Z (0.8662982 s, exit 0); the first four groups ran at 21:31:04.744081–21:31:05.295684Z (0.5516094 s, exit 0). Packaging performs no additional compile or run.

The four groups consume 39 observations: 29 Memory observations and ten port calls, including two frame-path ports and eight delegation ports. Ten final byte cells are checked. The qualified recursive frame observes flag 0x33002FA0 and pointer slot 0x33002F00 for result 0x33003000. Foreign Memory and foreign-site rejection precede scripted observations. This void consumer does not observe the wrapper long return; a second insertOther recursion is not exercised. Exception transparency is not forced, and these observations do not establish full parent branches, hardware atomicity, raw ABI, MXCSR, EH, Native or Game behavior.

Four real model POSTs completed: three stop and one length, zero transport retries, observed phase peak two. The wrapper retains the R1 executable body after owner comment deletion, so it is not a whole raw adoption. The binder is R1 decoded raw source with no owner edits. The witness discards its length-limited first candidate and partially adopts R2 frame DATA with owner corrections and owner fixture/run/delegate code. Its independence record remains at the earlier source freeze; later packaging reads frozen production source.

SOURCE-LIST194.json records actual local raw bytes, formal worktree raw bytes, and Git HEAD blob bytes separately. InGameIdlerEventDispatch.java is 2735 bytes in the physical CRLF worktree and 2655 bytes in the Git LF blob; only explicit CRLF-to-LF comparison is asserted. The additive patch preserves the three new raw source files; publication LF handling belongs to the formal writer. No local evidence or cached classroot is included.

Publication only normalizes Git line endings and trailing line whitespace, preserving original EOF. SOURCE-LIST separately identifies original first-compile physical source hashes and publication_git_LF identities. The original RESULT and local first receipts remain unchanged.
