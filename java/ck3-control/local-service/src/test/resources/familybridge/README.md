# Family Bridge complete-frame software fixture

This derived fixture retains the4-input shape of worker94: native framed packet, original Driver observation facts, Driver state and complete semantic export. It uses neutral owner family-bridge-software-fixture, removes machine/deployment paths and materializes symbolic references under JUnit @TempDir. Unconsumed source references become bounded metadata placeholders. It contains no Game, Native transport, physical lease or current authority.

The template is156233 bytes, gzip24047 bytes; the4 original input bytes total186458. DriverFrameEvidenceLoader and DriverObservationAssembler rebuild Complete from the relocated packet/facts/Driver bytes. Production Driver encoding and exact rewritten hashes are preserved. The typed semantic comparison uses the relocated full export, larger than the receipt limit. Missing or invalid resources fail without a skip or fallback.

RootFamilyBridgeCodecRegressionTest calls the actual package-private producer/decoder used by current/replay, plus the production typed semantic comparator. It verifies that a small reference manifest uses its65KiB receipt budget while referenced semantic DATA remains in the64MiB full lane. Object ordering is irrelevant; changed values, boolean identity tokens and changed nonempty command-history array order are rejected. Wrong manifest schema/shape, duplicate keys, malformed UTF-8, trailing JSON and receipt overflow are rejected.

The old canonical(body,64MiB) and parse(manifest,64MiB) calls are explicit negative controls: StrictJson's configurable input/output API only accepts maxima up to1MiB, so those calls reject even a small valid manifest. This differs from a large semantic body overflowing the default65KiB budget.

These tests do not construct RootRuntimeContext or a fake LeaseSnapshot. They do not call preserve, verify physical custody, issue Native I/O or admit an action. Existing local-service JUnit/resources/default Surefire discovery provide the CI entry:

```text
mvn -T2 -pl local-service -am -Dtest=RootFamilyBridgeCodecRegressionTest -Dsurefire.failIfNoSpecifiedTests=false test
```

Use existing approved build/temporary roots. Maven/CI execution is separate from the D-only isolated run recorded in the candidate handoff.
