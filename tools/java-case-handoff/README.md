# Original controller and Root phase protocol

This pure Java build support module reads the existing acceptance controller's files. It submits no game command and grants no capacity or launch admission. Quarkus remains the product host; this module needs no separate service.

After submitting a Root phase result, the original controller owns date advancement. Before another Root action, invoke `CasePhaseHandoff --wait <request-path> <bytes> <sha256> <unique-output>` and consume the original exit code. Exit 0 requires the next adjacent phase's actual `awaiting`, the previous phase's complete accepted assertions, the same immutable run context and original HOLD deadline, a healthy host, and completion of every published control. Previous acceptance alone grants nothing. Never issue Root days while waiting for the controller's next phase.

Requests use the `Request` record in `CasePhaseHandoff.java`. File pins require exact absolute path, integer byte length and SHA-256. Keep FILETIME and deadline identity strings out of JavaScript numeric round trips. The request's timeout is finite and never extends the original HOLD or its 180-second Quit reserve. A failure, consumed next checkpoint or identity change must stop the caller; timeout is not permission.

Use the machine's default `mvn` (at least 3.10.0), with an explicitly qualified project output root:

```text
mvn --batch-mode -f tools/java-case-handoff/pom.xml -Dcase.handoff.output=<approved-output-root> verify
```

The persistent regression covers the actual file producer/consumer route, including the P2 acceptance / missing P3 race and published controls that have not yet appeared in the native report. The product static workflow runs the same complete Maven verification command. Machine-specific qualification and failed-run evidence belong in their separately bound receipts.
