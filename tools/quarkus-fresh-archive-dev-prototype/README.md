# Fresh additional-archive dev entry prototype

This is a software-qualified prototype for Quarkus **3.40.1.1**, Java **21**, Maven **3.10.0** (Resolver **2.0.24**). It is not wired into the application's current launcher or default build. Its isolated reactor executed a newly compiled public dependency class after a runtime-loader restart **inside the same JVM**. It does not demonstrate object/delegate preservation or compatibility with arbitrary new classes and extensions.

The three source files, owned plugin descriptor and POM here are exact payloads from that successful private software run. The repository normalizes only the manifest resource from 25-byte CRLF to 23-byte LF; its original archive bytes remain recorded separately. When assembling a JAR, use standard manifest encoding and termination. The inherited descriptor is preserved, including original description whitespace. They contain no machine-specific path. The descriptor was derived from the official fixed-version plugin descriptor; its dev implementation and explicit `freshArchiveOutput` parameter belong to this prototype. It retains other inherited goal descriptors to support the fixture, but this unit qualifies only the exercised dev/compile/augmentation route. Do not infer all inherited goals have been independently validated. No third-party JAR was modified.

`FreshArchiveDevMojo` subclasses the official `DevMojo` through its protected `modifyDevModeContext` hook. It requires `-Dxar.dev.fresh.output` to identify an **absolute, already existing business classes directory**. It registers an application-owned entry before bootstrap. `FreshArchiveDevEntry` reuses the original application model and dependency provider, adds that directory as a fresh additional application archive and its own origin as an additional deployment archive. It obtains a preparation object defined in the replacement augmentation loader before startup. `PreparedDevSession` runs the original isolated dev lifecycle with that loader as the temporary TCCL and restores the previous TCCL in `finally`.

## Fixed-version integration recipe

This folder is a source/resource archive, not a promise that `mvn package` has been tested. The successful artifact was assembled from three Java21 strict-compiled classes plus the resource entries in this folder, with the manifest line-ending projection described above. Use an explicitly resolved compiler classpath from the fixed vendor plugin's actual dependency graph, including its real provided Maven plugin annotations; do not suppress missing-class metadata warnings or fabricate stubs. Package those classes and `src/main/resources` into an application-owned JAR, with this POM available at its coordinate and at `META-INF/maven/org.xar.research/fresh-archive-dev-maven-plugin/pom.xml`. Assembly or repository installation in another environment needs its own source/identity review.

In an isolated reactor, retain the official `io.quarkus.platform:quarkus-maven-plugin:3.40.1.1` extension and configure this owned plugin's build/generate-code/generate-code-tests executions. Compile the business module first so the output directory exists. The exercised command shape was:

```text
mvn -nsu -B -ntp -f <REACTOR_POM> -pl host -am   -Dmaven.repo.local=<NEW_PRIVATE_REPOSITORY>   -Dmaven.repo.local.tail=<EXISTING_LOOKUP_REPOSITORIES>   -Dmaven.repo.local.tail.ignoreAvailability=false   -Dquarkus.live-reload.instrumentation=false   -Dxar.dev.fresh.output=<ABSOLUTE_EXISTING_BUSINESS_CLASSES>   compile org.xar.research:fresh-archive-dev-maven-plugin:1.0.0:dev
```

This is a template, not shell-specific quoting guidance. Supply actual absolute paths using the execution platform's tested quoting. The fork must use the same private primary repository and explicitly tracked lookup tails; the software witness also set its own `QUARKUS_LOCAL_REPO`. Fixed-version dependency resolution was allowed only into the fresh private primary. It did not install/deploy into the shared repository or fabricate `_remote.repositories` records. This is a repository routing statement, not an OS sandbox claim.

## Recorded result and limits

The successful software run retained actual PID and birth, changed runtime/dependency loader from restart0 to restart1, and executed the real newly compiled `AddedType.class` (410 bytes) through an existing consumer: `BEFORE_NEW_PUBLIC_CLASS` became `AFTER_NEW_PUBLIC_CLASS`. Private nonce-bound shutdown returned 202, the owned wrapper exited 0, the port became free, and no forced cleanup was used.

Four earlier isolated runs failed at distinct stages and remain part of the result: owned plugin resolution, an unnecessary bridge plugin-descriptor dependency, standalone plugin BOM/dependency resolution, then a ServiceLoader type-identity failure before application startup. The local TCCL correction was compiled once and the next software run passed. Internal interface/provider defining-loader IDs were not recorded, so the earlier failure's unique internal topology is not asserted.

The full window from the first software BEGIN to the fifth software END was **3355.3302 seconds**, including failures, source/model work, coordination and waiting. The five software process durations sum to **284.1493297 seconds**; the four compiler process durations sum to **8.8387663 seconds**. Neither sum is owner CPU time. Owner-active time is unknown. Earlier preparation and standalone library witnesses are outside that named wall window.

The prototype's startup `Error`/cleanup boundary is not production-qualified. No production source adoption, current application reload, gameplay, saved-day or performance benefit follows from this software result. Compatible existing-method instrumentation is a separate capability and is not established here.

## Source provenance

The framework sources and original descriptor came from Quarkus tag `3.40.1.1`, especially `DevMojo`, `DevModeMain`, `IsolatedDevModeMain`, `CuratedApplication`, and the fixed `quarkus-maven-plugin` artifact. The additional descriptor resource entries preserve the actual owned artifact's payload. The official source repository is https://github.com/quarkusio/quarkus/tree/3.40.1.1 . The original framework is Apache-2.0 licensed. This folder does not redistribute the vendor JAR.
