# M6 stock skill source boundary, 2026-10-12

The installed CK3 1.20.0.4 source investigation has not yet qualified a stock
numeric martial/learning getter, its Character receiver or its return scale.
G2 stays at 6/8 accepted families; M6 and M7 remain incomplete. No new ordinary
day credit or natural succession is claimed by this source work.

The EXE identity is 101,040,248 bytes, SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
Root retained the previous whole-file identity; the following operations did not
repeat its whole-file hash or run the Game/SDK.

## Actual bounded reads

- Scope A read 2,933,476 EXE bytes: four 64-byte contexts and one complete
  2,933,220-byte `.pdata` scan. It found nine exact owner intervals and four
  raw-context targets with no containing entry. The description pointers contain
  required-level questions; they are not secondary vtables or a numeric ABI.
- Scope B Source17 stopped during preparation: two expected description strings
  omitted `the`. It read no new EXE bytes and produced no body result. Its failed
  attempt is preserved separately.
- The explicitly corrected Source18 read 2,081 bytes: 2,017 bytes across nine
  owner intervals and four 16-byte raw contexts. It saved all 524 linear
  instruction rows, with no rejected row or recursive callee follow.

Full `.pdata` intervals and complete linear decoding do not establish complete
logical functions. The 18-byte interval beginning at RVA 57849856 and the
32-byte interval beginning at RVA 14399424 have successors outside their
observed ranges. `after_linear_terminator` does not imply unreachable code.

## Findings used to choose the next read

RVA 66384512 performs descriptor/byte processing, case folding, a 32-bit
FNV-1a-shaped hash and DWORD lookup/candidate handling. Its return register width
does not establish a Character ID or skill value.

RVA 57851152 has locking, key mixing, conditional payload writes and a virtual
call. The address of the saved incoming R8 stack slot is passed to a callee;
the later row write uses the post-call slot value. Equality to original R8 is
unproved. This body cannot qualify as a closed read-only numeric skill getter.

The two retained constructors link a returned DWORD to an allocated object's
field at `+0x10` and a later association call. Required-level description text
and this association flow still leave the authored skill expression, semantic
callback, receiver extraction and units unresolved.

Root selected two metadata-only candidates. The observed primary-address cells
at offsets `+8/+16` contain RVA 45502928 for the martial-associated constructor
and RVA 45502960 for its learning comparator. Existing raw bytes begin with
`e93b290000` and `e91b2a0000`, respectively. Fixed rel32 arithmetic gives
candidate destinations **45513488** and **45513744**. This arithmetic grants
neither an instruction boundary nor callability. The other two context patterns
give neighboring candidates, 45513360 and 45513616, which are deferred.

The next selected operation is a fresh, separately admitted `.pdata` lookup of
only the two chosen destinations, with no body read. Scope D body ranges and
byte budgets must come from the actual lookup result. Generic container and
allocator callees are not automatically followed.

## Small evidence references and retention

These local evidence names are relative to
`D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/`.
They are finite research inputs, not permanent availability promises.

| Evidence | Bytes | SHA-256 |
| --- | ---: | --- |
| `sdk85-source-preparation/sdk86-candidates/m6-vtable-pdata-intake-source16/SOURCE16-ROOT-VTABLE-PDATA-RESULT.json` | 15416 | `baffc4b47396047d6645703f9ccaa5d334ac371c4af7ec8404e844a33579bc90` |
| `ROOT-SOURCE17-ACTUAL-PREPARE-STOP.json` | 2205 | `b5fada5a4da0bcd6e2f8c2f38ee6e54d4443059b8add9da95b40e11cdb2e7228` |
| `sdk85-source-preparation/sdk86-candidates/m6-stock-getter-body-source18/SOURCE18-ROOT-BODY-RESULT.json` | 50562 | `4ddf3023ae9b24eb1fc24b2d5e81d68129d5a181ec94507c4ad4e4d1598e5c2f` |
| `ROOT-M6-SOURCE18-ACTUAL-BODY-THIN.jsonl` | 51043 | `b128890c4dc7a811d88cf00e08b23a3a59b1af5c366718439f9e4929b72a8cd7` |
| `ROOT-M6-PRIMARY-CELL-CANDIDATE-ARITHMETIC.json` | 2934 | `8c47a81fc47077d5ea1694b1c1b21281fe0bd3fba5f3963d5888c899df33e7fd` |

Two independent parallel source groups analyzed the retained rows; Root read
their final contracts and preserved the conservative saved-slot qualification
above. This is source review, not a test-suite or runtime acceptance claim.

All research leaves use the original source allowance and review deadline,
2026-10-12 16:47:28.264315 UTC. Copying, correcting or adopting findings does not
renew that deadline. Necessary active evidence receives explicit review under
the [common storage policy](../storage-retention-policy.md); expired artifacts
may be consolidated or reclaimed with an exact small receipt.
