The retained `termination_six_query_projection.json` is copied byte-for-byte from
`ck3_autonomous_player/tests/unit/fixtures/termination_six_query_projection.json`.
Its original projection source references are preserved; it is neither a new live
native observation nor a complete original native response.
The original projection does not declare its source machine: source
`machine_id: unknown`. A new capture's machine ID identifies the differential
test execution only, and does not identify or requalify that historical game.

`producer-golden.json` is captured once by the explicit Java
`WarQueryCadenceGoldenCapture` tool from the existing Python producer and all seven
existing unit tests. Default Java tests consume the committed result without
running or requiring Python. Input hashes bind each fixture mutation to exactly
the input used by that producer.
