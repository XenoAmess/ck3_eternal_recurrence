# Native32 finite offline production builder

This separate source package preserves the sealed Native31 and Native32 diagnostic
sources. It recompiles all four known consumers of the changed observer header:
bridge, commands, observer core, and installer. It inherits actual Native31 argv
and linker-library order, keeps the 807-byte macro overlay, and reads the 335
remaining objects and two archives in place.

`producer.py plan` only creates an independent bounded plan. `build` requires the
owner's pinned execution card, the same producer and source identities, a fresh
object/output directory, and the fixed review deadline. It never loads the DLL,
contacts a Game/SDK, installs a broker, registers an EXE, or deploys an artifact.

The historical Native31 producer remains a failed producer with an independently
qualified artifact. This builder does not repeat its assertion that an inlined
CommitInsertion helper must have a standalone linker symbol. Instead it verifies
the essential compiled core functions against linked DLL bytes outside relocation
fields and verifies mapped relative-call targets, as well as the exact six PE
exports, four new direct objects, archive exclusion, source/stat guards, and the
absence of debug output. These are offline artifact checks, not runtime, drain,
unknown-request recovery, clock correctness, or performance qualification.

Portable tests use synthetic original argv and COFF/PE bytes. Local recipe review
also uses the pinned actual Native31 command receipts; missing external inputs
fail closed. No network fetch or fallback to the current production tree occurs.

Output caps are finite ceilings; the monitor can terminate a subprocess after a
sample detects an excess. Sampled allocation plus the filesystem guard is recorded
as sampled evidence, never advertised as an exact instantaneous peak or RSS.
