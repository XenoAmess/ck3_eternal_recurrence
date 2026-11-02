# Compatible-method instrumentation software witness

This isolated software fixture qualifies one **Quarkus 3.40.1.1 / Java21 / Maven3.10.0** route: only an existing method return body changes, while the actual JVM, application/dependency loader, delegate object and worker thread remain unchanged. The existing worker and a fresh invocation both observe the changed method result. This is separate from loading new dependency types through a replacement runtime loader.

**Business integration checkpoint:** the running business host identified as **45424** was reported with `instrumentation=false` at this handoff. This witness did not query or change it, and the business path has not been integrated or accepted. No end-to-end speed or saved-game-day benefit is claimed.

## Fixture and configuration

The seven reactor source/POM/config files are exact verified inputs. All probe/delegate types exist at the initial compile. Only the existing `BusinessRevision.value()` return literal is modified after startup; no class, field, method signature, annotation, resource or configuration is added or removed during the positive change.

The standard vendor Maven dev goal is used, without the separate fresh-additional-archive prototype. Its launch property is `-Dquarkus.live-reload.instrumentation=true`. The initial host configuration explicitly indexes the otherwise plain business dependency:

```properties
quarkus.index-dependency.business.group-id=org.xar.research
quarkus.index-dependency.business.artifact-id=instrumentation-business311
```

The source basis is the fixed tag's `ApplicationArchiveBuildStep`: `quarkus.index-dependency` is a BUILD_TIME map, converted into artifact-specific index inputs; matching runtime dependency directories are indexed. `CombinedIndexBuildStep` installs the archive composite as `RuntimeUpdatesProcessor.lastStartIndex`. This config fixes the observed private fixture gap; it does not imply a gap in every dependency or the current business application.

The probe starts its counter in `@PostConstruct` and closes/joins it in `@PreDestroy`. It publishes an actual private nonce, PID/birth, loader identity, delegate UUID/identity, original thread ID and monotonically increasing counter. The retained thread repeatedly invokes the modified method. An agent JVM argument is recorded, but the positive also requires the official completed-instrumentation log and unchanged identities; the argument alone is insufficient.

## Recorded negative and positive

The first private run entered instrumentation but the old ClassInfo for the existing business dependency was absent. `ClassComparisonUtil` threw a NullPointerException; the official catch then performed a full application restart. The method value changed, but the loader/delegate/thread changed too, so the no-restart oracle correctly failed. The original probe also had a thread-owning field initializer that produced two creation tokens per startup. Both failures remain recorded.

The followup changed only the initial exact-artifact indexing configuration and the probe's managed-bean lifecycle initialization. It retained the original positive assertions. The actual JVM/birth, both loaders, delegate UUID/identity and thread remained unchanged; progress increased **24 to 112** and both worker and fresh invocation returned the new value. Compiled existing-class bytes changed **432 to 435**. The official log completed instrumentation with no restart. Exactly one delegate was created and its original token closed once with a completed join; private nonce-bound shutdown returned202, the owned wrapper exited0 and the private port became free without force.

The first software run lasted **51.538368s** and was an oracle RED despite Maven's normal build completion. The positive run lasted **62.9041848s**. Their process durations sum to **114.4425528s**; first software BEGIN through final END spans **795.29391s**, including failed attempts, source/model work, resource coordination and waiting. Earlier prospective preparation is outside that named wall. Owner-active time is unknown. The framework's local `0.541s` reload log is a suboperation, not a saved-day or end-to-end performance metric.

## Running the archived witness

`run-witness.cjs` is a mechanical public path/config projection of the verified private runner. It has **not been rerun for publication**. The source/POM/config inputs and semantic assertions are preserved; the public wrapper's environment/path parameterization needs normal review before a new execution. No current business endpoint is used.

Use a Node.js executable with built-in `fetch` and a separately authorized executor. Set `INSTRUMENTATION_FIXTURE_WORKSPACE` to an absent, absolute private directory; `INSTRUMENTATION_MVN` to the actual Maven executable; and `INSTRUMENTATION_JAVA_HOME` to the actual Java21 directory. Optional variables are `INSTRUMENTATION_FIXTURE_PORT` (default8127), `INSTRUMENTATION_REPOSITORY_TAIL` (explicit comma-separated existing lookup repositories), and `INSTRUMENTATION_MACHINE_ID` (otherwise not recorded). This archived wrapper is Windows-only and uses the actual `SystemRoot` for owned cleanup. Before any fixture/host IO it rejects paths containing whitespace/control characters, `& | < > ^ % !`, double quotes or parentheses. The workspace, Maven executable, Java home and SystemRoot must be absolute; each comma-separated repository-tail path must also be absolute and within that restricted domain. An empty tail is allowed. This deliberately narrow path contract avoids CMD expansion and the separate inner JVM-argument whitespace parser; it does not claim general quoting for arbitrary Windows filenames.

Run the archived script with that executor, rather than starting this source tree against a business service. It copies the exact seven inputs into the new workspace and launches a private standard Maven dev reactor. Repository writes resolve fixed versions only into the new workspace's primary; existing tails remain availability-checked lookup inputs. There is no install/deploy, fabricated repository tracking or third-party JAR modification. This is routing and ownership logic, not an OS sandbox claim.

The actual private execution inherited one allowed CPU and used Maven512MiB plus fork512MiB/metaspace256MiB. The public Node script retains the JVM limits and initial180s/body90s waits, but does **not** establish OS CPU affinity or an outer330s guard; those are the authorized executor's responsibility. It checks the private port is free, binds responses to its nonce/PID/birth and stops only the owned fixture. Its fallback can force only that newly spawned owned wrapper tree. Never repoint it at an existing business host.

## Source and capability boundaries

The official instrumentation path requires a real agent handle, initialized startup index, an enabled flag, no forced/watched-file restart, no added/deleted classes, compatible class structure, both extension predicates and successful JDK redefinition. None of those guards is removed. An active long-running frame keeps its old bytecodes; only later invocations of the modified callee are witnessed here. Static initialization is not rerun.

`IsolatedDevModeMain.firstStart` configures the flag from the first runner's config. Its ordinary `restartApp` path does not refresh that setter. `RuntimeUpdatesProcessor` has an explicit live override/toggle and an official console caller, but this unit establishes no authorized reachable control in the current console-disabled business host. Changing a resource to true is not evidence that an already configured false flag changed. Business integration and qualifying actual edits remain separate work.

Framework source references are in SOURCE-PROVENANCE.md. This unit does not qualify arbitrary method edits, new public dependency types, existing-business object invariants, live adoption, gameplay or performance.
