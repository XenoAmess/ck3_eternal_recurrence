# Synthetic 361 vertical slice (offline only)

This document records the first executable pipeline for `open_kaishek`.
It is deliberately a synthetic fixture, not a CK3 adapter or a live
certification artifact.

## Slice boundary

The fixture models one small part of the B2 appeal/PIP area: mechanism `014`
with three namespaced operations and a finite state sequence:

```text
delivered -> appeal_open -> closed
```

`Synthetic361Fixture` generates the UTF-8-BOM source
`common/scripted_effects/zg361_synthetic_014.txt`.  Its bytes are passed
unchanged through the following stages:

```text
generated .txt bytes
  -> Parser (lossless CST and diagnostics)
  -> Validator (synthetic schema and parameter arity)
  -> StrictIrCompiler (typed IR with source spans)
  -> IrExecutor + RuntimeKernel (finite in-memory state)
```

The synthetic profile is `zg361-synthetic-014`, uses an all-zero executable
fingerprint by design, and certifies only the three fixture handlers.  The
profile must never be substituted for `ck3-1.19.0.6`.

## Fail-closed rules exercised

- A parser error yields an empty, non-executable IR program.
- An unknown nested operation yields `UNSUPPORTED_UNKNOWN_OPCODE` and never
  reaches the runtime.
- A known CK3 opcode from the exact-build profile is still
  `NOT_CERTIFIED`; the executor refuses the whole program before any write.
- Runtime handlers reject illegal state transitions and choices with an
  explicit `INVALID` result; no default branch silently mutates state.
- `IrExecutor` performs an executable preflight, so unsupported instructions
  cannot execute a prefix and then disappear.

## Reproduce

From the repository root (the local Maven cache is used for the offline
verification environment):

```powershell
cmd /c "set MAVEN_OPTS=-Duser.home=C:\Users\xenoa&& mvn -o -Dmaven.repo.local=C:\Users\xenoa\.m2\repository -pl kaishek-zg361-profile -am test -f open_kaishek\pom.xml"
```

`Synthetic361PipelineTest` contains the positive file-boundary and execution
assertions plus the unknown-opcode and CK3-not-certified negative paths.  A
successful run is evidence for the `runtime-fixture` level only.  It does not
prove CK3 equivalence, MCP differential certification, scheduler behavior, or
product-live readiness.
