# M1 exact-target .text stream locator

machine_id: `xenoamess-full-tower-eb9d2c1186`; 2026-10-26 UTC. This was a Root-authorized temporary research payload under the installed REA OwnedCommand/ProviderProcess infrastructure. It is not an official REA stream operation, a new production runner, or a native dossier.

The fixed query searched only mapped `.text` RVA `[1000,43D9848)`, file `[400,43D8C48)`:71141448 B, excluding440 B alignment padding. It sought raw five-byte E8rel32 targets to exact2603AF0, capped at128 candidates. A1MiB buffer plus4-byte carry handled chunk boundaries; no fulltext copy was retained. Two streamed whole-file SHA checks bound the current101040248 B EXE to `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.

The complete reported scan covered71141444 possible starts and1233859 raw E8 positions, yielding six candidates:

| Raw RVA | Containing RF from current selected metadata |
| --- | --- |
| 2786593 | 2785FD0..27866AD |
| 29B75E6 | 29B7590..29B75F0 |
| 2A6D946 | 2A6D620..2A6DA58 |
| 2CE377D | 2CE35F0..2CE3901 |
| 2CE697F | 2CE6790..2CE6A3D |
| 2CE6D76 | 2CE6A40..2CE6E31 |

These were **raw candidates, not calls**. Reused PDATA occupied2933220 B; selected row/neighbor validation read16 unique current rows/192 B. RF coverage does not establish instruction boundaries or normal reachability. The two scoped cache roots had9212 filenames and no overlap with any of the six RFs; this is not a whole-disk absence claim. The separately authorized [96 B query](resume63-m1-caller29b7590-result.md) later verified only the second candidate.

Requested PE reads totaled273226232 B: two identity passes202080496, text71141448, header4096 and RF192. Held PDATA I/O is additional; physical disk traffic/cache misses were not measured. The query child took649ms with native owned-job peak33452032 B under a256MiB hard limit and30s timeout; payload timing was519.9694ms, endpoint RSS47083520 B. These metrics cover different scopes and do not establish an end-to-end speed benefit.

Minimum close was20:37:28.800Z,146.547s after fresh authority T0; exact owned PIDs were absent. The later8567 B receipt has SHA `cf9d91f09080cf3913532a6033518acb5c37950323261e27992c5616e39bdec5`; the6510 B M1 independent review has SHA `4cd4b13467409307b87861cfb7c67713fd4ab4192a97310c3575adb7b1866d76`. It checked six signed targets, selected RFs, argv/source/carry invariants and capture equality. It did not independently reread the fulltext or recompute its reported stream SHA/count. Actual read-call count was not logged;68 chunks is only nominal, and the invariant also handles short reads.

[Source index](sources.json) binds the plan, close, review and receipt. Original PLAN/card1MiB allowance is retained; Root's later actual256KiB cap was consumed separately, with complete closing upper188416 B. Original close remains PAYLOAD_UNASSESSED. Outer joint peak/Job0, full preparation/research time and token benefit remain unmeasured. No Game/Steam action, Java adoption, producer trigger or natural-inheritance qualification was established.
