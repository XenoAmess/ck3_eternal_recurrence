package org.xar.ck3.control.service;

import java.io.InputStream;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectionArtifactAuthority;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputCodec;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputRef;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;
import static org.xar.ck3.control.contracts.projection.ProjectionArtifactInputContract.exactRef;
import static org.xar.ck3.control.contracts.projection.ProjectionArtifactInputContract.fileRef;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionArtifactInputReaderTest {
    @TempDir Path directory;
    record Bindings(SourceBinding source, RuntimeBinding runtime) { }
    static final class MutableClock extends Clock {
        Instant now = Instant.parse("2026-10-23T00:00:01Z");
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { return this; }
        @Override public Instant instant() { return now; }
    }
    final class Fixture implements AutoCloseable {
        final Path root, slot, lease, source, runtime;
        final MutableClock clock = new MutableClock();
        final ProcessIdentity owner, host;
        final Scope scope;
        final ControlBuild.FileRef scopeRef;
        final URLClassLoader loader;
        ProjectionArtifactInputReader.Observation observed;
        ControlBuild.BuildReceipt verificationResult;
        java.util.function.IntConsumer duringBuildVerification = count -> { };
        final AtomicInteger buildVerifications = new AtomicInteger();
        final ProjectionArtifactInputReader reader;
        Fixture(long budget) throws Exception {
            this(budget, java.util.function.UnaryOperator.identity());
        }
        Fixture(long budget, java.util.function.UnaryOperator<Bindings> alteration) throws Exception {
            root = Files.createTempDirectory(directory, "case-").toRealPath(); slot = Files.createDirectories(root.resolve("custody/input")); lease = root.resolve("lease.json");
            source = root.resolve("source.json"); runtime = root.resolve("runtime.json");
            Path build = root.resolve("fixture-build-metadata.json");
            String className = "org.xar.ck3.control.service.ArtifactProducerFixture";
            String resource = className.replace('.', '/') + ".class";
            Path jar = root.resolve("producer.jar");
            try (JarOutputStream output = new JarOutputStream(Files.newOutputStream(jar)); InputStream input = getClass().getClassLoader().getResourceAsStream(resource)) {
                assertNotNull(input); output.putNextEntry(new JarEntry(resource)); input.transferTo(output); output.closeEntry();
            }
            loader = new URLClassLoader(new java.net.URL[]{jar.toUri().toURL()}, ClassLoader.getPlatformClassLoader());
            owner = new ProcessIdentity(11, "123456789", root.resolve("owner-java.exe")); host = new ProcessIdentity(12, "123456790", root.resolve("host-java.exe"));
            // This typed file is deliberately not an actual build: native/full-build acceptance
            // is a package-only injected fixture, never a production accepted receipt.
            Path originalSource = Files.writeString(root.resolve("fixture-source.java"), "original fixture source");
            Path ownerSources = Files.createDirectories(root.resolve("build-tools/src/main/java/org/xar/ck3/control/build"));
            var sourcePins = new java.util.ArrayList<ControlBuild.FileRef>();
            sourcePins.add(ControlBuild.FileRef.measure(originalSource));
            for (String name : java.util.List.of("ProjectionArtifactAuthority.java", "ProjectionArtifactInputOwner.java", "MapAdmissionServiceOwner.java")) {
                sourcePins.add(ControlBuild.FileRef.measure(Files.writeString(ownerSources.resolve(name), "fixture source: " + name)));
            }
            var jarPin = ControlBuild.FileRef.measure(jar);
            var matched = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
            var fixtureBuild = new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, "fixture-machine", clock.now.toString(), "PASS", root.toString(), root.toString(), root.toString(),
                    matched, matched, ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.STANDARD_8_MIB,
                    sourcePins, sourcePins, java.util.List.of(jarPin), java.util.List.of(jarPin),
                    null, null, null, null, null, java.util.Map.of(), null);
            Files.write(build, ControlBuild.strictMapper().writeValueAsBytes(fixtureBuild));
            verificationResult = fixtureBuild;
            var buildRef = ControlBuild.FileRef.measure(build);
            Bindings bindings = alteration.apply(new Bindings(new SourceBinding("fixture-machine", buildRef,
                    fixtureBuild.sourcePins(), fixtureBuild.compiledSourcePins()), new RuntimeBinding("fixture-machine", buildRef,
                    "session-1", owner, ProjectionArtifactAuthority.ownerSources(fixtureBuild), fixtureBuild.producerRuntimePins())));
            Files.write(source, ProjectionArtifactAuthority.encodeSourceBinding(bindings.source()));
            Files.write(runtime, ProjectionArtifactAuthority.encodeRuntimeBinding(bindings.runtime()));
            scope = new Scope("scope-1", "session-1", "fixture-machine", owner, InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE,
                    slot, lease, budget, Instant.parse("2026-10-23T00:00:00Z"), Instant.parse("2026-10-23T00:02:00Z"),
                    fileRef(reference(source)), fileRef(reference(jar)), buildRef, fileRef(reference(runtime)), className);
            Path configured = Files.write(root.resolve("scope.json"), ProjectionArtifactInputCodec.encodeScope(scope)); scopeRef = fileRef(reference(configured));
            Files.write(lease, ProjectionArtifactInputCodec.encodeLease(new Lease(scopeRef, host, scope.issuedAtUtc(), scope.expiresAtUtc(), Purpose.FULL)));
            observed = new ProjectionArtifactInputReader.Observation("fixture-machine", owner, host);
            // Native/full-build qualification is supplied by the original Owner in production.
            // This explicit package-only fixture supplies typed metadata, while all I/O, SHA,
            // file identity, callback lifetime and the producer's real JAR CodeSource are actual.
            reader = new ProjectionArtifactInputReader(exactRef(scopeRef), "fixture-machine", configuredScope -> observed, loader, clock, ignored -> {
                duringBuildVerification.accept(buildVerifications.incrementAndGet()); return verificationResult;
            });
            reader.bindCatalogOwner(java.util.List.of(new ProjectionHost.CatalogOrigin(className, jar.toString(), java.util.List.of(
                    new org.xar.ck3.control.contracts.projection.ProjectionDispatcher.OperationProfile(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, 65_536, 490)))));
        }
        ProjectionArtifactInputRef input(byte[] bytes) throws Exception {
            Path input = Files.write(slot.resolve(INPUT_NAME), bytes, java.nio.file.StandardOpenOption.CREATE_NEW);
            return new ProjectionArtifactInputRef(reference(input), reference(lease));
        }
        @Override public void close() throws java.io.IOException { loader.close(); }
    }
    private static ExactRef reference(Path path) throws Exception {
        byte[] bytes = Files.readAllBytes(path);
        return new ExactRef(path.toString(), bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static void unavailable(org.junit.jupiter.api.function.Executable action) {
        var error = assertThrows(ProjectionProtocolException.class, action); assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, error.code());
    }
    @Test void actualLargeOriginalBytesUseAnActualJarCodeSourceAndNeverWidenTheInlineWire() throws Exception {
        byte[] raw = ("{\"opaque\":\"" + "x".repeat((8 << 20) + 1) + "\",\"decimal\":1.0}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        try (var fixture = new Fixture(raw.length)) {
            var claim = fixture.input(raw); AtomicInteger calls = new AtomicInteger();
            String result = fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, input -> {
                calls.incrementAndGet(); assertArrayEquals(raw, input); return "{\"status\":\"plan\"}";
            });
            assertEquals(1, calls.get()); assertTrue(result.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 490);
            assertEquals(fileRef(claim.leaseRef()), fixture.reader.current().leaseRef());
            assertEquals(8 << 20, org.xar.ck3.control.contracts.projection.ProjectionJson.MAX_BYTES);
            assertArrayEquals(raw, Files.readAllBytes(Path.of(claim.inputRef().path()))); // Server did not delete or rewrite the client-owned input.
        }
    }
    @Test void wrongOperationOutsideRootExtraFilesAndActualBudgetAreResourceRefusalsBeforeComputation() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)); AtomicInteger calls = new AtomicInteger();
            java.util.function.Function<byte[], String> callback = value -> { calls.incrementAndGet(); return "unused"; };
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.WARCASH_EVALUATE, claim, callback));
            Path outside = Files.writeString(fixture.root.resolve("outside.json"), "{}");
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, new ProjectionArtifactInputRef(reference(outside), claim.leaseRef()), callback));
            Path extra = Files.writeString(fixture.slot.resolve("another.json"), "{}");
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, callback)); Files.delete(extra);
            Files.writeString(Path.of(claim.inputRef().path()), "longer");
            var larger = new ProjectionArtifactInputRef(reference(Path.of(claim.inputRef().path())), claim.leaseRef());
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, larger, callback)); assertEquals(0, calls.get());
        }
    }
    @Test void leaseExpiryAndSourceDriftAfterTheCallbackDiscardTheResult() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> {
                fixture.clock.now = fixture.scope.expiresAtUtc(); return "must-be-discarded";
            }));
            fixture.clock.now = Instant.parse("2026-10-23T00:00:01Z");
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> {
                try { Files.writeString(fixture.runtime, "runtime-changed"); } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
                return "must-be-discarded";
            }));
        }
    }
    @Test void exactProcessGenerationAndLeaseHashAreRechecked() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            fixture.observed = new ProjectionArtifactInputReader.Observation("another-machine", fixture.owner, fixture.host);
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> "unused"));
            fixture.observed = new ProjectionArtifactInputReader.Observation("fixture-machine", fixture.owner, new ProcessIdentity(12, "123456791", fixture.host.executable()));
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> "unused"));
            fixture.observed = new ProjectionArtifactInputReader.Observation("fixture-machine", new ProcessIdentity(11, "123456792", fixture.owner.executable()), fixture.host);
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> "unused"));
            fixture.observed = new ProjectionArtifactInputReader.Observation("fixture-machine", fixture.owner, fixture.host);
            Files.writeString(fixture.lease, "{}"); unavailable(() -> fixture.reader.current());
        }
    }
    @Test void identicalBytesAtAReplacementIdentityCannotQualifyTheOriginalInput() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            Path input = fixture.slot.resolve(INPUT_NAME);
            var modified = Files.getLastModifiedTime(input);
            var originalIdentity = org.xar.ck3.control.build.SharedSourceFiles.nativeFile(input).identityKey();
            AtomicInteger calls = new AtomicInteger();
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> {
                calls.incrementAndGet();
                try {
                    Files.move(input, fixture.root.resolve("original-input.json")); Files.write(input, raw); Files.setLastModifiedTime(input, modified);
                    assertNotEquals(originalIdentity, org.xar.ck3.control.build.SharedSourceFiles.nativeFile(input).identityKey());
                    assertEquals(modified, Files.getLastModifiedTime(input));
                }
                catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
                return "must-be-discarded";
            }));
            assertEquals(1, calls.get()); assertArrayEquals("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8), Files.readAllBytes(input));
        }
    }
    @Test void callbackBusinessAndInternalFailuresKeepTheirOriginalTypesWhenCustodyIsCurrent() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var domain = new ProjectionDomainRejection("actual domain refusal");
            assertSame(domain, assertThrows(ProjectionDomainRejection.class, () -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> { throw domain; })));
            var fault = new IllegalArgumentException("internal indexing fault");
            assertSame(fault, assertThrows(IllegalArgumentException.class, () -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> { throw fault; })));
        }
    }
    @Test void changingTheOwnedDirectoryIdentityCannotRebindItsContents() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var inputIdentity = org.xar.ck3.control.build.SharedSourceFiles.nativeFile(fixture.slot.resolve(INPUT_NAME));
            var slotIdentity = org.xar.ck3.control.build.SharedSourceFiles.nativeDirectory(fixture.slot);
            Path custody = fixture.slot.getParent();
            var directoryIdentity = org.xar.ck3.control.build.SharedSourceFiles.nativeDirectory(custody);
            var modified = Files.getLastModifiedTime(custody);
            AtomicInteger calls = new AtomicInteger();
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> {
                calls.incrementAndGet();
                try {
                    Path retired = fixture.root.resolve("original-custody");
                    Files.move(custody, retired); Files.createDirectory(custody);
                    Files.move(retired.resolve(fixture.slot.getFileName()), fixture.slot); Files.setLastModifiedTime(custody, modified);
                    assertEquals(inputIdentity, org.xar.ck3.control.build.SharedSourceFiles.nativeFile(fixture.slot.resolve(INPUT_NAME)));
                    assertEquals(slotIdentity, org.xar.ck3.control.build.SharedSourceFiles.nativeDirectory(fixture.slot));
                    assertNotEquals(directoryIdentity, org.xar.ck3.control.build.SharedSourceFiles.nativeDirectory(custody));
                } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
                return "must-be-discarded";
            }));
            assertEquals(1, calls.get());
        }
    }
    @Test void proofReplacementAtIdenticalBytesAndOversizedArrayClaimsRemainResourceFailures() throws Exception {
        try (var fixture = new Fixture(org.xar.ck3.control.contracts.StrictJson.MAX_SAFE_INTEGER)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var arrayOverflow = new ProjectionArtifactInputRef(new ExactRef(claim.inputRef().path(), (long) Integer.MAX_VALUE + 1, claim.inputRef().sha256()), claim.leaseRef());
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, arrayOverflow, raw -> "unused"));
            var modified = Files.getLastModifiedTime(fixture.source);
            var originalIdentity = org.xar.ck3.control.build.SharedSourceFiles.nativeFile(fixture.source).identityKey();
            AtomicInteger calls = new AtomicInteger();
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> {
                calls.incrementAndGet();
                try {
                    byte[] old = Files.readAllBytes(fixture.source); Files.move(fixture.source, fixture.root.resolve("original-source.json")); Files.write(fixture.source, old);
                    Files.setLastModifiedTime(fixture.source, modified);
                    assertNotEquals(originalIdentity, org.xar.ck3.control.build.SharedSourceFiles.nativeFile(fixture.source).identityKey());
                } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
                return "must-be-discarded";
            }));
            assertEquals(1, calls.get());
        }
    }
    @Test void captureModeRefusesAConfiguredArtifactScopeBeforeAnySourceRead() {
        Path missing = directory.resolve("must-not-open.json").toAbsolutePath();
        assertThrows(IllegalStateException.class, () -> new ProjectionHost("fixture-machine", java.util.Optional.empty(), java.util.Optional.empty(),
                java.util.Optional.empty(), java.util.Optional.of(missing.toString()), java.util.Optional.of("1"), java.util.Optional.of("a".repeat(64)), true));
        assertFalse(Files.exists(missing));
    }
    @Test void leaseExpiryDuringThePostGuardItselfCannotReturnAnEarlierCurrentResult() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            fixture.duringBuildVerification = count -> { if (count == 2) fixture.clock.now = fixture.scope.expiresAtUtc(); };
            AtomicInteger calls = new AtomicInteger();
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> { calls.incrementAndGet(); return "expired-during-post-guard"; }));
            assertEquals(1, calls.get());
        }
    }
    @Test void aForeignParsedBuildCannotReplaceTheRootPinnedReceiptEvenWhenTheFileIsRestored() throws Exception {
        try (var fixture = new Fixture(2)) {
            var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)); AtomicInteger calls = new AtomicInteger();
            Path receipt = Path.of(fixture.scope.buildReceiptRef().path()); byte[] original = Files.readAllBytes(receipt);
            var modified = Files.getLastModifiedTime(receipt);
            fixture.duringBuildVerification = count -> {
                if (count != 1) return;
                try {
                    var mapper = ControlBuild.strictMapper();
                    var foreign = mapper.readValue(original, com.fasterxml.jackson.databind.node.ObjectNode.class);
                    foreign.put("observed_at_utc", "2026-10-23T00:00:03Z"); Files.write(receipt, mapper.writeValueAsBytes(foreign));
                    fixture.verificationResult = mapper.readValue(Files.readAllBytes(receipt), ControlBuild.BuildReceipt.class);
                    Files.write(receipt, original); Files.setLastModifiedTime(receipt, modified);
                } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
            };
            unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim, raw -> { calls.incrementAndGet(); return "must-not-run"; }));
            assertEquals(0, calls.get()); assertArrayEquals(original, Files.readAllBytes(receipt));
        }
    }
    @Test void exactHashedButUnrelatedBindingsRefuseBeforeAnyDomainComputation() throws Exception {
        java.util.List<java.util.function.UnaryOperator<Bindings>> alterations = java.util.List.of(
                value -> new Bindings(new SourceBinding(value.source().machineId(), value.source().buildReceiptRef(),
                        value.source().sourceRefs().reversed(), value.source().compiledSourceRefs()), value.runtime()),
                value -> new Bindings(new SourceBinding(value.source().machineId(), value.source().buildReceiptRef(),
                        value.source().sourceRefs(), value.source().compiledSourceRefs().subList(1, value.source().compiledSourceRefs().size())), value.runtime()),
                value -> new Bindings(value.source(), new RuntimeBinding(value.runtime().machineId(), value.runtime().buildReceiptRef(),
                        "another-session", value.runtime().ownerProcess(), value.runtime().ownerSourceRefs(), value.runtime().ownerRuntimeRefs())),
                value -> new Bindings(value.source(), new RuntimeBinding(value.runtime().machineId(), value.runtime().buildReceiptRef(),
                        value.runtime().ownerSessionId(), value.runtime().ownerProcess(), value.runtime().ownerSourceRefs().reversed(), value.runtime().ownerRuntimeRefs())),
                value -> new Bindings(value.source(), new RuntimeBinding(value.runtime().machineId(), value.runtime().buildReceiptRef(),
                        value.runtime().ownerSessionId(), value.runtime().ownerProcess(), value.runtime().ownerSourceRefs(), java.util.List.of(value.source().sourceRefs().getFirst()))));
        for (var alteration : alterations) {
            try (var fixture = new Fixture(2, alteration)) {
                var claim = fixture.input("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
                AtomicInteger calls = new AtomicInteger();
                unavailable(() -> fixture.reader.withInput(ProjectionOperation.MILITARY_COMBAT_ROLES_NORMALIZE, claim,
                        raw -> { calls.incrementAndGet(); return "must-not-run"; }));
                assertEquals(0, calls.get());
            }
        }
    }
}

/** Compiled fixture bytes are packaged into a real JAR; the reader uses that class's actual CodeSource. */
final class ArtifactProducerFixture { private ArtifactProducerFixture() { } }
