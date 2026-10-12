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
- Scope C Source20 completed a separate 2,933,220-byte `.pdata` scan of
  244,435 records. Each chosen destination has one containing entry and equals
  its beginning: `[45513488,45513601)` and `[45513744,45513857)`, both 113 bytes.
  It read no bodies and retained all formal qualifications as false.
- The first independently admitted Scope D attempt, Source21, stopped before
  any EXE read. Its decoder import succeeded, but its package-version comparison
  failed. Installed distribution metadata reports Capstone 5.0.9, while the
  installed module declares `__version__` 5.0.7. These fields must be qualified
  separately; neither establishes an observed native engine version.
- The independently corrected Scope D Source22 actually exited 0. It read
  exactly 226 bytes and saved all 54 instructions across the two complete
  113-byte intervals. The actual module path and module 5.0.7, distribution
  5.0.9 and two named text pins matched the separate new admission. The engine
  version remains unknown. Source21's zero-read failure remains unchanged.
- Scope E Source24 had a separate Root numeric admission and actually exited
  0. It read only two independent 64-byte windows, at RVA 75428416 and
  75428992; all 128 bytes and 16 complete QWORD cells were saved. Their raw
  bytes are identical. The 512-byte gap, common address and two secondary
  contexts were not read. No decoder, target follow or new whole-EXE hash ran.
- Scope F Source25 had its own Root numeric admission and actually exited 0.
  It read one complete 2,933,220-byte `.pdata` range in 45 exact reads, parsed
  and validated all 244,435 records, and retained all sixteen prior pointer
  occurrences. All pre/post and final EXE stat checks matched. No target body,
  unwind, string, decoder or additional whole-EXE hash was read.

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

Root selected and completed only the two full 113-byte intervals from the actual
Scope C lookup. Both allocate an object with argument `0x138`, install several
RIP-relative addresses, set the DWORD at `+0x40` to `0x165`, copy the input DWORD
at `+0x10` into the new object at `+8`, set byte `+0xC` to zero and return the new
object. This is construction/initialization evidence; it does not read a
qualified skill scalar or establish the input as a Character receiver.

The five distinct RIP-relative destinations are 71987760, 75428416, 75428688,
75428992 and 75429264, within the recorded `.rdata` geometry. The three direct
callee destinations are 69352340, 57854576 and 10517600. Their values identify
possible next inputs, without authorizing new pointer windows, callee bodies,
callback ABI or formal getter use. Generic callees are not automatically followed.

The selected final primary windows contain the following address coordinates
in both contexts. These are eight observed cells per window, not an established
complete table or callable slots. Duplicate addresses retain their distinct
context/offset observations.

| Offset in each window | Target RVA | Arithmetic file offset | Observed classification |
| --- | ---: | ---: | --- |
| `+0` | 57862592 | 57859520 | full eight-byte raw-backed `.text` coordinate |
| `+8` | 8725184 | 8722112 | same |
| `+16` | 45034960 | 45031888 | same |
| `+24` | 8725440 | 8722368 | same |
| `+32` | 10542224 | 10539152 | same |
| `+40` | 57855488 | 57852416 | same |
| `+48` | 8725184 | 8722112 | same |
| `+56` | 14238688 | 14235616 | same |

At Scope E's completion, the seven unique target coordinates were proposed
inputs for a separate `.pdata` lookup. Source25 subsequently completed that
lookup, with the following metadata results:

| Target RVA | Complete metadata lookup | Unique interval, when present | Bytes |
| --- | --- | --- | ---: |
| 57862592 | entry equals begin | `[57862592,57862680)` | 88 |
| 8725184 | no containing record | unresolved | — |
| 45034960 | entry equals begin | `[45034960,45035050)` | 90 |
| 8725440 | no containing record | unresolved | — |
| 10542224 | no containing record | unresolved | — |
| 57855488 | entry equals begin | `[57855488,57856730)` | 1242 |
| 14238688 | no containing record | unresolved | — |

Absence of a containing `.pdata` record does not prove that a target is not a
function or entry. The three unique intervals qualify only metadata ownership;
their bodies and unwind data remain unread. No formal dispatch consumer,
Character receiver, return type, scale or callback ABI is qualified. Equality
of the first 64 bytes does not establish equality of the whole tables or a
complete negative certificate for skill getters.

## Installed education script source

The support effect explicitly forwards a martial focus as `$SKILL$=martial`.
It chooses a random current guardian as `educator`; without a guardian it uses
the court owner's tutor, then guru. A requested guardian does not establish
which educator the effect actually selected.

In `scope:educator`, the selected skill and learning terms are multiplied by
authored factors 0.4 and 0.2 in the success weight. The success entry's base
weight is 60, and its effect separately adds two education points. The culture
expression contains `value=10`; it is not independently established as an
add-ten operation. Optional House predicate semantics and native value encoding
remain unresolved. Script thresholds and displayed trait ranks do not qualify
a typed numeric getter or current education outcome.

The complete support failure branch has base weight 40, negative-intellect
terms and a missing-educator term of 20; it contains no education-points write
or selected-skill/learning term. Later helpers and notification code do not
close the final education-trait writer. The complete `educate_child` acceptance
hook binds ward/guardian role aliases and delegates to
`educate_child_interaction_effect`. Its two relation setters occur inside
`show_as_tooltip`, so they do not prove an actual guardian relation. The
separately observed complete wrapper at `00_interaction_effects.txt:1977–1984`
calls `education_flags_tooltips_effect` in ward scope, then calls
`ward_depart_effect` in its incoming scope. Source23's earlier command-path
failure and education locator Source22's imprecise JavaScript mtime
serialization remain preserved.

Source24 observed the complete flags helper at `:1986–2127`. Requested culture
and faith conversion set ten-year flags on the ward; the age branches choose
descriptions and do not perform conversion. University acceptance requires the
authored option and location branches. Its payer is `puppet_or_actor`, using
`monumental_gold_value` with the conditional House reduction, not an observed
fixed gold amount. The ward receives university and conditional Confucian
learning modifiers; the non-university Confucian branch adds a modifier, not a
trait. This complete helper contains no direct guardian-relation, education
points, focus or final-rank writer. The outer `ward_depart_effect` was not found
in this one file; travel, relation afterstate and the full acceptance chain
remain unresolved. This is installed source text with stable metadata, not a
runtime build pin or observed player outcome.

Source25 subsequently located the complete `ward_depart_effect` in
`00_education_effects.txt:3288–3471`, rather than Source24's interaction file.
The six exact named candidates were checked once, with stable metadata; the
184-line body was then read once and shared among fourteen source lanes.
Source24's earlier limited-file absence and unknown remain historical facts.

The no-travel branch has an actual authored relation writer: when the specified
guardian lacks the specified ward relation, line 3343 sets guardian→ward inside
`hidden_effect`. This differs from the earlier tooltip setters. The branch also
transfers the ward's culture/faith character flags to guardian→ward relation
flags and removes the character flags; it does not perform conversion. Neither
the flags nor the setter prove an actual current relation or conversion result.

Travel-needed branches instead create plans and two-year role-valued
travelling/waiting variables, with separate named start/cancel/arrival hooks.
Those hooks remain unread. The ward's ten-year requester variable stores
`puppet_or_actor`; none of these expiration literals is an education-point
value or acquisition cadence. This complete body does not directly write
education points, focus, final trait rank or the support effect's selected
educator. Nested effects and hooks keep those wider outcomes unresolved.

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
| `sdk85-source-preparation/sdk86-candidates/m6-primary-cell-pdata-source20/SOURCE20-ROOT-PRIMARY-CELL-PDATA-RESULT.json` | 4003 | `8955f55e16d52cec68478f2d1fdaf91e579468d9d072558f7e53f1d32b4e96c0` |
| `sdk85-source-preparation/sdk86-candidates/m6-primary-cell-body-source22/SOURCE22-ROOT-PRIMARY-CELL-BODY-RESULT.json` | 9616 | `94a450c8c132345786f9c3429219c06fe2613d071462656d412b887d89abf3e5` |
| `sdk85-source-preparation/sdk86-candidates/m6-primary-cell-pointer-source24/SOURCE24-ROOT-PRIMARY-CELL-POINTER-RESULT.json` | 11107 | `b02c49fd91af3ebc50529c14db119a46d52bd863a09237e2aa706ccd0c874a38` |
| `sdk85-source-preparation/sdk86-candidates/m6-primary-pointer-owner-source25/SOURCE25-ROOT-PRIMARY-POINTER-OWNER-RESULT.json` | 6917 | `10ec9ef2ba501c6c5fae5b18abe5eee29360d6211d8c412fdd181f763f74fe5d` |

Source24's new reviewed plan is 5808 bytes, SHA-256
`64d677d5d63e453508d8cb988ecc9348edfb8afd0903922167aad4a5e84c4927`;
its independent numeric admission is 3860 bytes, SHA-256
`9ddf9c51c3d6d8c8b72aa9312c87fc6e4a4271c81e4ed71453065a47784a9c2e`.
The leaf used 47114 source bytes and 11605 output bytes under its separate
64 KiB allowances. Root read the entire result; each selected range was read
once, all pre/post stat checks matched, and elapsed intake was 0.0290521 s.
The education text contracts are the separate
`g2-education-accept-consumer-source23/SOURCE-CONTRACT.json` and
`g2-education-accept-consumer-source24/SOURCE-CONTRACT.json` leaves under the same
candidate parent. Their decoded source-line transcripts do not claim byte-exact
original-file hashes. Two whole-contract static reviews passed; no live
education, guardian or native-getter qualification was added.

Source25's independent numeric admission is 6213 bytes, SHA-256
`29dcc7b1a0280974f55e4f573f9fcc0355e3de7e0756f26850f0b77beb695747`;
its reviewed plan is 8383 bytes, SHA-256
`7417a333f24d25c17fea312669d366f257a8919604b5e0911a7d083315889cd0`.
The leaf used 53204 source bytes and 7424 output bytes. The sole intake took
1.0582305 seconds. Root read the complete result and retained all three matches
and four complete-scan missing results without assigning semantic function types.
The education Source25 contract is
`sdk85-source-preparation/sdk86-candidates/g2-education-ward-depart-consumer-source25/SOURCE-CONTRACT.json`.
Root read its full decoded 184-line transcript; the contract explicitly removes
leading indentation and does not claim a byte-exact installed-file copy.

Source21's separate failed body result retains zero read bytes, zero instruction
rows and the actual decoder import failure. The installed source intake is
`ROOT-INSTALLED-CAPSTONE-SOURCE-METADATA.json`; no package installation, engine
version query or extra decoder import was used to establish its text facts.

Two independent parallel source groups analyzed the retained rows; Root read
their final contracts and preserved the conservative saved-slot qualification
above. This is source review, not a test-suite or runtime acceptance claim.

All research leaves use the original source allowance and review deadline,
2026-10-12 16:47:28.264315 UTC. Copying, correcting or adopting findings does not
renew that deadline. Necessary active evidence receives explicit review under
the [common storage policy](../storage-retention-policy.md); expired artifacts
may be consolidated or reclaimed with an exact small receipt.
