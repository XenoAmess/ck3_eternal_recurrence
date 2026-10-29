package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual small-directory accounting and cold issuer joins. Synthetic grants never authorize project execution. */
final class ControlBuildAccountingTest {
    @TempDir Path temporary;
    private static final Set<String> SCOPES = Set.of("source_snapshot", "build", "private_tmp", "artifacts", "logs");
    record Fixture(ControlBuild.Config config, ControlBuild.AttemptCapacityRelease release, Path source, Path snapshot, Path build, Path accounting) { }

    @Test void actualAttemptGuardMeasuresOnlyItsScopesAndKeepsSharedRepositoryUnknown() throws Exception {
        Fixture fixture = fixture("bounded");
        Path old = Files.createDirectories(fixture.config().workRoot().resolve("build/previous-attempt"));
        Path cache = Files.createDirectories(fixture.config().workRoot().resolve("m2"));
        Files.write(old.resolve("old.bin"), new byte[65536]); Files.write(cache.resolve("retained.bin"), new byte[65536]);
        var oldRef = ControlBuild.FileRef.measure(old.resolve("old.bin")); var cacheRef = ControlBuild.FileRef.measure(cache.resolve("retained.bin"));
        var accounting = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        assertEquals(ControlBuild.AccountingMode.CONSERVATIVE_VOLUME_ATTEMPT, accounting.mode());
        assertEquals(ControlBuild.RepositoryAccountingState.CONSERVATIVE_VOLUME_COVERAGE, accounting.repositoryAccountingState());
        assertNull(accounting.mavenRepositoryBaselineBytes()); assertNull(accounting.mavenRepositoryCurrentBytes());
        assertEquals(SCOPES, accounting.logicalBytesByScope().keySet()); assertEquals(SCOPES, accounting.nativeAllocatedBytesByScope().keySet());
        assertTrue(accounting.logicalBytesByScope().values().stream().mapToLong(Long::longValue).sum() < 65536);
        assertTrue(accounting.nativeAllocatedBytesByScope().get("private_tmp") > 0);
        assertEquals(accounting, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(accounting), ControlBuild.WorkpackageAccounting.class));
        oldRef.verify(); cacheRef.verify();
        // Removing a current output does not erase the observed peak.
        Path added = fixture.build().resolve("current.bin"); Files.write(added, new byte[8192]);
        var peak = ControlBuild.accountWorkpackage(fixture.config(), () -> {}); Files.delete(added);
        var after = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        assertTrue(after.logicalBytesByScope().get("build") < peak.logicalBytesByScope().get("build"));
        assertEquals(peak.peakNewLogicalBytes(), after.peakNewLogicalBytes());
        assertEquals(peak.peakNewNativeAllocatedBytes(), after.peakNewNativeAllocatedBytes());
    }

    @Test void currentAttemptCannotUseMissingPrivateTemporaryRootOrForeignRoots() throws Exception {
        Fixture fixture = fixture("reject");
        String python = System.getenv("XAR_ORACLE_PYTHON");
        assertNotNull(python, "Same admitted CanonicalOracleEnvironment must precede critical accounting execution");
        Map<String, String> environment = Map.of("XAR_ORACLE_PYTHON", python);
        Path settings = fixture.config().workRoot().resolve("logs/build-reject-settings.xml");
        List<String> released = ControlBuild.releasedReactorVerifyArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(), environment, Instant.now());
        String actualTmp = "-Djava.io.tmpdir=" + fixture.release().workpackageAccounting().measuredRoots().get("private_tmp");
        assertEquals(List.of(actualTmp), released.stream().filter(value -> value.startsWith("-Djava.io.tmpdir=")).toList());
        List<String> capture = new ArrayList<>(released); assertEquals("verify", capture.removeLast());
        capture.add("-Dmaven.test.skip=false"); capture.add("-DskipTests=true"); capture.add("package");
        var releaseRef = ControlBuild.FileRef.measure(fixture.config().capacityRelease());
        assertEquals(capture, ControlBuild.completedCaptureArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(), capture, releaseRef, Instant.now()));
        List<String> wrongTmp = new ArrayList<>(capture); wrongTmp.set(wrongTmp.indexOf(actualTmp), "-Djava.io.tmpdir=" + fixture.config().workRoot().resolve("scratch"));
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(), wrongTmp, releaseRef, Instant.now()));
        // The original overload remains the legacy shared-scratch metadata contract.
        assertTrue(ControlBuild.reactorVerifyArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(), environment)
                .contains("-Djava.io.tmpdir=" + fixture.config().workRoot().resolve("scratch")));
        List<String> physical = new ArrayList<>(released); physical.add(physical.size() - 1, "-Dxar.accounting.padding=" + "x".repeat(9000));
        assertTrue(MavenArgumentFile.required(null, physical));
        MavenArgumentFile.prepare(fixture.source(), fixture.snapshot(), null, physical);
        assertEquals(physical, MavenArgumentFile.readManifest(fixture.snapshot(), physical).arguments());
        assertTrue(MavenArgumentFile.readManifest(fixture.snapshot(), physical).arguments().contains(actualTmp));
        assertTrue(ControlBuild.mavenExecutionBatchText(null, physical, fixture.snapshot()).lines().allMatch(line -> line.length() <= MavenArgumentFile.CMD_LIMIT));
        Files.delete(Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp")));
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(fixture.config(), () -> {}));
        var mapper = ControlBuild.strictMapper(); ObjectNode release = mapper.valueToTree(fixture.release());
        ((ObjectNode) release.path("workpackage_accounting").path("measured_roots")).put("build", temporary.resolve("unrelated").toString());
        Files.write(fixture.config().capacityRelease(), mapper.writeValueAsBytes(release));
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(fixture.config(), () -> {}));
    }

    @Test void completedV6ReadsIndependentAccountingPinAndRejectsSelfConsistentSmallHoldsOrForeignVolume() throws Exception {
        Fixture fixture = fixture("cold");
        var terminalFixture = ControlBuildTest.completedReceiptFixture(temporary.resolve("real-terminal"));
        var accounting = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        Files.write(fixture.accounting(), ControlBuild.strictMapper().writeValueAsBytes(accounting));
        ControlBuild.BuildReceipt receipt = completed(fixture, terminalFixture.receipt());
        Path receiptPath = temporary.resolve("scoped-build.json");
        Files.write(receiptPath, ControlBuild.strictMapper().writeValueAsBytes(receipt));
        assertEquals(receipt, ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receiptPath)));
        assertEquals(terminalFixture.receipt().completeDeployment().size(), receipt.completeDeployment().size());
        assertFalse(receipt.completeDeployment().contains(receipt.workpackageAccountingRef()));
        for (String mutation : List.of("small-holds", "foreign-root")) {
            ObjectNode body = ControlBuild.strictMapper().valueToTree(accounting);
            ObjectNode volume = (ObjectNode) body.path("volumes").get(0);
            if (mutation.equals("small-holds")) {
                volume.put("all_holds_bytes", 1); volume.put("required_free_bytes", 1 + volume.path("system_growth_reserve").longValue() + volume.path("safety_reserve").longValue());
            } else volume.put("volume_root", temporary.toString());
            var changed = ControlBuild.strictMapper().treeToValue(body, ControlBuild.WorkpackageAccounting.class);
            // Each row remains internally coherent. Only the real cold consumer's issuer join can reject it.
            ControlBuild.requireVolumeQuote(changed.volumes().getFirst());
            Files.write(fixture.accounting(), ControlBuild.strictMapper().writeValueAsBytes(changed));
            Files.write(receiptPath, ControlBuild.strictMapper().writeValueAsBytes(completed(fixture, terminalFixture.receipt())));
            assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receiptPath)), mutation);
        }
    }

    @Test void soleMapperAndVersionCodecKeepOriginalV5WireAndRejectCurrentPassWithoutItsPin() throws Exception {
        var fixture = ControlBuildTest.completedReceiptFixture(temporary.resolve("old-wire"));
        var mapper = ControlBuild.strictMapper(); byte[] old = mapper.writeValueAsBytes(fixture.receipt());
        assertFalse(mapper.readTree(old).has("workpackage_accounting_ref"));
        assertEquals(fixture.receipt(), ControlBuild.decodeBuildReceipt(old));
        assertEquals(fixture.receipt(), mapper.readValue(old, ControlBuild.BuildReceipt.class));
        assertEquals(fixture.receipt(), ControlBuild.verifiedCompletedReceipt(fixture.receiptRef()));
        ObjectNode changed = (ObjectNode) mapper.readTree(old); changed.put("schema", ControlBuild.SCOPED_BUILD_SCHEMA);
        changed.set("final_logical_bytes_by_part", mapper.createObjectNode());
        assertThrows(IOException.class, () -> mapper.treeToValue(changed, ControlBuild.BuildReceipt.class));
        changed.putNull("workpackage_accounting_ref");
        assertThrows(IOException.class, () -> ControlBuild.decodeBuildReceipt(mapper.writeValueAsBytes(changed)));
        changed.put("schema", "xar.java-control.actual-build/v4");
        assertThrows(IOException.class, () -> mapper.treeToValue(changed, ControlBuild.BuildReceipt.class));
    }

    @Test void actualVolumeQuoteChecksAllHoldsAndUsesNoFreeSpaceIncreaseAsDeletionCredit() throws Exception {
        Path root = temporary.getRoot();
        var admitted = new ControlBuild.VolumeObservation(root.toString(), 1000000, 800000, 200000, 300000, 4000, 900000, 1000, 1000, 2000);
        ControlBuild.requireVolumeQuote(admitted);
        assertThrows(IOException.class, () -> ControlBuild.requireVolumeQuote(new ControlBuild.VolumeObservation(root.toString(), 1000000, 3000, 997000, 997000, 4000, 1000000, 1000, 1000, 2000)));
        assertThrows(IOException.class, () -> ControlBuild.requireVolumeQuote(new ControlBuild.VolumeObservation(root.toString(), 1000000, 800000, 200000, 899000, 4000, 900000, 1000, 1000, 2000)));
        assertThrows(IllegalArgumentException.class, () -> new ControlBuild.VolumeObservation(root.toString(), 1000000, 800000, 200000, 199999, 4000, 900000, 1000, 1000, 2000));
    }

    @Test void actualEntryCreatesOnlyItsMissingTemporaryChildAndRetainsOriginalCustody() throws Exception {
        Fixture fixture = fixture("entry-tmp");
        Path root = Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Files.delete(root); // Reproduce the real first invocation, not the old fixture's pre-created directory.
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(fixture.config(), () -> {}));
        byte[] release = Files.readAllBytes(fixture.config().capacityRelease());
        ControlBuild.PreparedTemporaryRoot prepared;
        try (var entered = ControlBuild.prepareWorkpackageTemporaryRoot(fixture.config(), () -> {})) {
            prepared = entered; entered.requireCurrent(); assertEquals(root, entered.root());
            assertTrue(Files.isDirectory(root, java.nio.file.LinkOption.NOFOLLOW_LINKS));
            Files.writeString(root.resolve("owned-child.tmp"), "ordinary Maven temporary mutation"); entered.requireCurrent();
            assertTrue(ControlBuild.accountWorkpackage(fixture.config(), entered::requireCurrent)
                    .nativeAllocatedBytesByScope().get("private_tmp") >= 4096);
            assertThrows(IOException.class, () -> ControlBuild.prepareWorkpackageTemporaryRoot(fixture.config(), () -> {}));
            Path foreign = root.resolveSibling("foreign-tmp");
            assertThrows(IOException.class, () -> Files.move(root, foreign)); assertFalse(Files.exists(foreign));
            Files.writeString(fixture.config().capacityRelease(), new String(release, java.nio.charset.StandardCharsets.UTF_8) + " ");
            assertThrows(IOException.class, entered::requireCurrent);
            Files.write(fixture.config().capacityRelease(), release); entered.requireCurrent();
        }
        assertThrows(IOException.class, prepared::requireCurrent);
        assertTrue(Files.isDirectory(root), "Closing custody never erases an actual attempt's output");
        Fixture wrong = fixture("foreign-tmp-root");
        Path correct = Path.of(wrong.release().workpackageAccounting().measuredRoots().get("private_tmp")); Files.delete(correct);
        ObjectNode altered = ControlBuild.strictMapper().valueToTree(wrong.release());
        Path unauthorized = temporary.resolve("not-an-admitted-tmp");
        ((ObjectNode) altered.path("workpackage_accounting").path("measured_roots")).put("private_tmp", unauthorized.toString());
        Files.write(wrong.config().capacityRelease(), ControlBuild.strictMapper().writeValueAsBytes(altered));
        assertThrows(IOException.class, () -> ControlBuild.prepareWorkpackageTemporaryRoot(wrong.config(), () -> {}));
        assertFalse(Files.exists(correct)); assertFalse(Files.exists(unauthorized));

        // Actual public build entry must prepare the missing TMP before its first shared guard.
        // Existing snapshot/build stop this software case before any Maven version probe or child.
        Fixture entry = fixture("whole-entry");
        Path entryTemporary = Path.of(entry.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Files.delete(entryTemporary);
        String oldJnaTemporary = System.getProperty("jna.tmpdir");
        try {
            System.setProperty("jna.tmpdir", entry.config().workRoot().resolve("scratch").toString());
            IOException stopped = assertThrows(IOException.class, () -> ControlBuild.build(entry.config()));
            assertEquals("Build attempt already exists", stopped.getMessage());
            assertTrue(Files.isDirectory(entryTemporary, java.nio.file.LinkOption.NOFOLLOW_LINKS));
            Path logs = entry.config().workRoot().resolve("logs");
            assertFalse(Files.exists(logs.resolve("build-whole-entry.json")));
            assertFalse(Files.exists(logs.resolve("build-whole-entry-version.cmd")));
            assertFalse(Files.exists(logs.resolve("build-whole-entry-version.stdout.log")));
            assertFalse(Files.exists(logs.resolve("build-whole-entry-version.stderr.log")));
            assertTrue(Files.isDirectory(entry.snapshot())); assertTrue(Files.isDirectory(entry.build()));
        } finally {
            if (oldJnaTemporary == null) System.clearProperty("jna.tmpdir");
            else System.setProperty("jna.tmpdir", oldJnaTemporary);
        }
    }

    @Test void mutableDescendantDisappearanceRestartsCompleteCensusWhileNonMissingAndImmutableFailuresRemainStrict() throws Exception {
        Fixture fixture = fixture("mutable-delete");
        Path root = Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Files.write(root.resolve("stable.bin"), new byte[4096]);
        Path disappearing = Files.createDirectories(root.resolve("duplicate/wave2-planning"));
        var reached = new java.util.concurrent.CountDownLatch(1);
        var removed = new java.util.concurrent.CountDownLatch(1);
        var workerFailure = new java.util.concurrent.atomic.AtomicReference<Throwable>();
        var seen = new java.util.concurrent.atomic.AtomicBoolean();
        var rootVisits = new java.util.concurrent.atomic.AtomicInteger();
        Thread deletion = Thread.ofVirtual().start(() -> {
            try {
                if (!reached.await(5, java.util.concurrent.TimeUnit.SECONDS)) throw new IOException("Actual census did not reach deletion boundary");
                Files.delete(disappearing);
            } catch (Throwable failure) { workerFailure.set(failure); }
            finally { removed.countDown(); }
        });
        ControlBuild.WorkpackageAccounting measured;
        try {
            measured = ControlBuild.accountWorkpackage(fixture.config(), () -> {}, path -> {
                if (path.equals(root)) rootVisits.incrementAndGet();
                if (path.equals(disappearing) && seen.compareAndSet(false, true)) {
                    reached.countDown();
                    try { if (!removed.await(5, java.util.concurrent.TimeUnit.SECONDS)) throw new IOException("Actual concurrent removal timed out"); }
                    catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
                }
            });
        } finally { deletion.join(6000); if (deletion.isAlive()) deletion.interrupt(); }
        assertFalse(deletion.isAlive());assertNull(workerFailure.get());assertTrue(seen.get());
        assertEquals(1, rootVisits.get(), "A natively confirmed absent descendant needs no whole-root restart");
        assertFalse(Files.exists(disappearing));assertEquals(4096L, measured.logicalBytesByScope().get("private_tmp"));
        var quiet = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        assertEquals(quiet.logicalBytesByScope(), measured.logicalBytesByScope());
        assertEquals(quiet.capacityReleaseRef(), measured.capacityReleaseRef());
        assertTrue(measured.nativeAllocatedBytesByScope().get("private_tmp") >= 8192);

        // A typed non-missing IO failure cannot borrow disappearance handling, even on mutable output.
        assertThrows(java.nio.file.AccessDeniedException.class, () -> ControlBuild.accountWorkpackage(fixture.config(), () -> {}, path -> {
            if (path.equals(root.resolve("stable.bin"))) throw new java.nio.file.AccessDeniedException(path.toString());
        }));
        Files.createDirectory(disappearing);
        IOException unknown = new IOException("unclassified metadata failure, not a typed native missing-path result");
        assertSame(unknown, assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(fixture.config(), () -> {}, path -> {
            if (path.equals(disappearing)) { Files.delete(path); throw unknown; }
        })), "A later absent path cannot launder an unclassified IO failure into a retry");
        Fixture immutable = fixture("immutable-delete");
        Path original = immutable.snapshot().resolve("src/main/java/ReceiptInput.java");
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(immutable.config(), () -> {}, path -> {
            if (path.equals(original)) Files.delete(original);
        }));

        Fixture unstable = fixture("unstable-delete");
        Path unstableRoot = Path.of(unstable.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Path regenerated = Files.write(unstableRoot.resolve("regenerated.bin"), new byte[1]);
        var attempts = new java.util.concurrent.atomic.AtomicInteger();
        IOException exhausted = assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(unstable.config(), () -> {},
                new ControlBuild.InventoryObserver() {
                    @Override public void beforeCheck(Path path) throws IOException {
                        if (path.equals(unstableRoot)) attempts.incrementAndGet();
                        else if (path.equals(regenerated)) Files.delete(path);
                    }
                    @Override public void afterMissingAccountingEntry(Path path) throws IOException {
                        if (path.equals(regenerated)) Files.write(path, new byte[1]);
                    }
                }));
        assertEquals(8, attempts.get());
        assertTrue(exhausted.getCause() instanceof java.nio.file.NoSuchFileException);
        assertTrue(exhausted.getMessage().startsWith("Mutable attempt scope remained unstable after 8 complete census attempts"));
    }

    private record NestedReceipts(ControlBuild.BuildReceipt before, List<ControlBuild.BuildReceipt> values, ControlBuild.CaptureBuildReceipt capture, String after) { }

    @Test void nestedReceiptConsumersUseOneValueWhileRootTrailingAndActualWriterBoundsStayStrict() throws Exception {
        var fixture = ControlBuildTest.completedReceiptFixture(temporary.resolve("nested-wire"));
        var mapper = ControlBuild.strictMapper();
        var receipt = fixture.receipt();
        // Record/codec DATA only; this synthetic capture shape is never passed to a qualification reader.
        var capture = new ControlBuild.CaptureBuildReceipt(ControlBuild.CAPTURE_SCHEMA, receipt.machineId(), receipt.observedAtUtc(), "codec-data", "software-codec",
                ControlBuild.CaptureQualification.TEST_COMPILED_CAPTURE_ONLY, ControlBuild.CaptureTestState.NOT_RUN,
                receipt.sourceRoot(), receipt.compiledSourceRoot(), receipt.deploymentRoot(), receipt.sourcePostcheck(), receipt.compiledSourcePostcheck(),
                ControlBuild.TargetKind.SERVICE_FAST_JAR, receipt.sourceLimitProfile(), receipt.sourcePins(), receipt.compiledSourcePins(), receipt.completeDeployment(),
                receipt.producerRuntimePins(), receipt.capacityReleaseRef(), receipt.mavenToolchain(), receipt.javaExecutableRef(), receipt.toolchainProbe(), receipt.mavenResult(),
                List.of("package", "-DskipTests=true", "-Dmaven.test.skip=false"), fixture.receiptRef(), fixture.receiptRef(), fixture.receiptRef(), fixture.receiptRef(), fixture.receiptRef(), Map.of());
        var nested = new NestedReceipts(receipt, List.of(receipt, receipt), capture, "following sibling must remain available");
        byte[] body = mapper.writeValueAsBytes(nested);
        assertEquals(nested, mapper.readValue(body, NestedReceipts.class));
        assertThrows(IOException.class, () -> mapper.readValue(new String(body, java.nio.charset.StandardCharsets.UTF_8) + " {}", NestedReceipts.class));
        ObjectNode large = mapper.valueToTree(fixture.receipt()); large.put("error", "x".repeat(4 << 20));
        // Internal record construction remains separate from the finite actual input/output envelope.
        ControlBuild.BuildReceipt internal = mapper.treeToValue(large, ControlBuild.BuildReceipt.class);
        assertThrows(IOException.class, () -> ControlBuild.buildReceiptBytes(internal));
        assertThrows(IOException.class, () -> ControlBuild.decodeBuildReceipt(mapper.writeValueAsBytes(large)));
    }

    private record CriticalResult(String schema, String machineId, String observedAtUtc, int tests, int failures, String state) { }

    /** Same eight persistent JUnit bodies, usable before full Maven after Root's private bootstrap qualification. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IOException("One exact fresh absolute case-root argument required");
        Path root = Path.of(arguments[0]);
        if (!root.isAbsolute() || !root.normalize().equals(root) || Files.exists(root)) throw new IOException("Fresh canonical absent critical accounting root required");
        SharedSourceFiles.plainAncestors(root); Files.createDirectory(root);
        var suite = new ControlBuildAccountingTest();
        suite.temporary = Files.createDirectory(root.resolve("case01")); suite.actualAttemptGuardMeasuresOnlyItsScopesAndKeepsSharedRepositoryUnknown();
        suite.temporary = Files.createDirectory(root.resolve("case02")); suite.currentAttemptCannotUseMissingPrivateTemporaryRootOrForeignRoots();
        suite.temporary = Files.createDirectory(root.resolve("case03")); suite.completedV6ReadsIndependentAccountingPinAndRejectsSelfConsistentSmallHoldsOrForeignVolume();
        suite.temporary = Files.createDirectory(root.resolve("case04")); suite.soleMapperAndVersionCodecKeepOriginalV5WireAndRejectCurrentPassWithoutItsPin();
        suite.temporary = Files.createDirectory(root.resolve("case05")); suite.actualVolumeQuoteChecksAllHoldsAndUsesNoFreeSpaceIncreaseAsDeletionCredit();
        suite.temporary = Files.createDirectory(root.resolve("case06")); suite.nestedReceiptConsumersUseOneValueWhileRootTrailingAndActualWriterBoundsStayStrict();
        suite.temporary = Files.createDirectory(root.resolve("case07")); suite.actualEntryCreatesOnlyItsMissingTemporaryChildAndRetainsOriginalCustody();
        suite.temporary = Files.createDirectory(root.resolve("case08")); suite.mutableDescendantDisappearanceRestartsCompleteCensusWhileNonMissingAndImmutableFailuresRemainStrict();
        System.out.println(ControlBuild.strictMapper().writeValueAsString(new CriticalResult("xar.java-control.critical-accounting-tests/v1",
                WindowsJobProcess.currentMachineId(), Instant.now().toString(), 8, 0, "PASS_SOFTWARE_ACCOUNTING_ONLY_NOT_GAME_OR_FINAL_TOOLS_QUALIFICATION")));
    }

    @FunctionalInterface
    private interface NativeMutation { void mutate(int sample) throws IOException; }
    private static ControlBuild.InventoryObserver metadataObserver(Path target,
            java.util.concurrent.atomic.AtomicInteger samples, NativeMutation mutation) {
        return new ControlBuild.InventoryObserver() {
            @Override public void beforeCheck(Path path) { }
            @Override public void afterStandardMetadata(Path path) throws IOException {
                if (path.equals(target)) mutation.mutate(samples.incrementAndGet());
            }
        };
    }

    @Test void realHeldMetadataRacesRetryOnlyMutableScopesAndKeepStrictFailures() throws Exception {
        Fixture growing = fixture("metadata-growing");
        Path file = Files.write(growing.build().resolve("growing.bin"), new byte[1]);
        var originalIdentity = SharedSourceFiles.nativeFile(file).identityKey();
        var samples = new java.util.concurrent.atomic.AtomicInteger();
        var complete = ControlBuild.accountWorkpackage(growing.config(), () -> {},
                metadataObserver(file, samples, sample -> {
                    if (sample == 1) Files.write(file, new byte[65536]);
                }));
        assertTrue(samples.get() >= 2, "The actual mismatching held sample must be rejected before a complete retry");
        assertTrue(complete.logicalBytesByScope().get("build") >= 65536);
        assertEquals(65536, SharedSourceFiles.nativeFile(file).logicalBytes());
        assertEquals(originalIdentity, SharedSourceFiles.nativeFile(file).identityKey());

        Fixture directory = fixture("metadata-root-directory");
        Files.setLastModifiedTime(directory.build(), java.nio.file.attribute.FileTime.fromMillis(1000));
        Path child = directory.build().resolve("new-child.bin");
        var directorySamples = new java.util.concurrent.atomic.AtomicInteger();
        var directoryResult = ControlBuild.accountWorkpackage(directory.config(), () -> {},
                metadataObserver(directory.build(), directorySamples, sample -> {
                    if (sample == 1) Files.write(child, new byte[4096]);
                }));
        assertTrue(directorySamples.get() >= 2);
        assertTrue(directoryResult.logicalBytesByScope().get("build") >= 4096);
        assertTrue(Files.isRegularFile(child));

        Fixture immutable = fixture("metadata-immutable");
        Path source = immutable.snapshot().resolve("pom.xml");
        var immutableSamples = new java.util.concurrent.atomic.AtomicInteger();
        IOException immutableFailure = assertThrows(IOException.class,
                () -> ControlBuild.accountWorkpackage(immutable.config(), () -> {},
                        metadataObserver(source, immutableSamples, sample -> Files.writeString(source, "changed"))));
        assertEquals(1, immutableSamples.get());
        assertTrue(immutableFailure.getMessage().contains("immutable source: " + source));
        assertInstanceOf(SharedSourceFiles.NativeFactsChangedException.class, immutableFailure.getCause());

        Fixture creation = fixture("metadata-creation-identity");
        Path creationFile = Files.write(creation.build().resolve("identity.bin"), new byte[1]);
        var creationSamples = new java.util.concurrent.atomic.AtomicInteger();
        var creationFacts = new SharedSourceFiles.NativeFactsChangedException(
                new SharedSourceFiles.NativeFacts(1, "10", "20", 1),
                new SharedSourceFiles.NativeFacts(2, "11", "21", 1));
        IOException creationFailure = assertThrows(IOException.class,
                () -> ControlBuild.accountWorkpackage(creation.config(), () -> {},
                        metadataObserver(creationFile, creationSamples, sample -> { throw creationFacts; })));
        assertEquals(1, creationSamples.get());
        assertTrue(creationFailure.getMessage().contains("immutable creation identity: " + creationFile));
        assertSame(creationFacts, creationFailure.getCause());

        Fixture exhausted = fixture("metadata-continuously-changing");
        Path busy = Files.write(exhausted.build().resolve("busy.bin"), new byte[1]);
        var busySamples = new java.util.concurrent.atomic.AtomicInteger();
        IOException unstable = assertThrows(IOException.class,
                () -> ControlBuild.accountWorkpackage(exhausted.config(), () -> {},
                        metadataObserver(busy, busySamples, sample -> Files.write(busy, new byte[sample % 2 == 1 ? 2 : 1]))));
        assertTrue(busySamples.get() >= 8 && busySamples.get() <= 64, "Finite exact samples and full censuses must not spin forever");
        assertTrue(unstable.getMessage().contains("Mutable attempt scope remained unstable"));
        assertTrue(unstable.getCause().getMessage().contains(busy.toString()));

        Fixture other = fixture("metadata-untyped-failure");
        Path otherFile = Files.write(other.build().resolve("other.bin"), new byte[1]);
        var otherSamples = new java.util.concurrent.atomic.AtomicInteger();
        IOException untyped = new IOException("native source facts changed between exact identity APIs");
        IOException otherFailure = assertThrows(IOException.class,
                () -> ControlBuild.accountWorkpackage(other.config(), () -> {},
                        metadataObserver(otherFile, otherSamples, sample -> { throw untyped; })));
        assertSame(untyped, otherFailure.getCause());
        assertTrue(otherFailure.getMessage().contains("operation=nativeHeldFile; path=" + otherFile));
        assertEquals(1, otherSamples.get(), "Matching error text must not acquire typed retry authority");
    }


    @Test void liveTemporaryCustodyRetriesMutableFactsAndKeepsIdentityAndFiniteFailuresStrict() throws Exception {
        Fixture fixture = fixture("custody-live-metadata");
        Path root = Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Path parent = root.getParent(); Files.delete(root);
        var armed = new java.util.concurrent.atomic.AtomicBoolean();
        var parentSamples = new java.util.concurrent.atomic.AtomicInteger();
        var childSamples = new java.util.concurrent.atomic.AtomicInteger();
        var mode = new java.util.concurrent.atomic.AtomicInteger();
        IOException untyped = new IOException("native source facts changed between exact identity APIs");
        var creationChanged = new SharedSourceFiles.NativeFactsChangedException(
                new SharedSourceFiles.NativeFacts(4096, "10", "20", 1),
                new SharedSourceFiles.NativeFacts(4096, "11", "21", 1));
        ControlBuild.InventoryObserver observer = new ControlBuild.InventoryObserver() {
            @Override public void beforeCheck(Path path) { }
            @Override public void afterStandardMetadata(Path path) throws IOException {
                if (!armed.get() || (!path.equals(root) && !path.equals(parent))) return;
                int sample = (path.equals(root) ? childSamples : parentSamples).incrementAndGet();
                if (path.equals(root) && mode.get() == 2) throw creationChanged;
                if (path.equals(root) && mode.get() == 3) throw untyped;
                if (mode.get() == 1 && path.equals(root))
                    Files.setLastModifiedTime(path, java.nio.file.attribute.FileTime.fromMillis(sample % 2 == 0 ? 1000 : 2000));
                else if (mode.get() == 0 && sample == 1)
                    Files.setLastModifiedTime(path, java.nio.file.attribute.FileTime.fromMillis(2000));
            }
        };
        ControlBuild.PreparedTemporaryRoot retained;
        try (var prepared = ControlBuild.prepareWorkpackageTemporaryRoot(fixture.config(), () -> {}, observer)) {
            retained = prepared;
            var parentIdentity = SharedSourceFiles.nativeDirectory(parent);
            var childIdentity = SharedSourceFiles.nativeDirectory(root);
            Files.setLastModifiedTime(parent, java.nio.file.attribute.FileTime.fromMillis(1000));
            Files.setLastModifiedTime(root, java.nio.file.attribute.FileTime.fromMillis(1000));
            armed.set(true); prepared.requireCurrent();
            assertTrue(parentSamples.get() >= 3, "Held parent race retries before independent path identity check");
            assertTrue(childSamples.get() >= 3, "Actual live temporary root race retries before independent path identity check");
            assertEquals(parentIdentity, SharedSourceFiles.nativeDirectory(parent));
            assertEquals(childIdentity, SharedSourceFiles.nativeDirectory(root));
            assertThrows(IOException.class, () -> Files.move(root, root.resolveSibling("foreign-custody")));
            armed.set(false);
            Files.writeString(root.resolve("ordinary-maven-child.tmp"), "actual mutable temporary child");
            prepared.requireCurrent();

            childSamples.set(0); mode.set(1); armed.set(true);
            Files.setLastModifiedTime(root, java.nio.file.attribute.FileTime.fromMillis(1000));
            IOException busy = assertThrows(IOException.class, prepared::requireCurrent);
            assertEquals(8, childSamples.get(), "One custody check has exactly eight finite samples and no whole-census retry");
            assertTrue(busy.getMessage().contains("Mutable accounting metadata remained unstable after 8 exact held samples: " + root));
            assertInstanceOf(SharedSourceFiles.NativeFactsChangedException.class, busy.getCause());

            childSamples.set(0); mode.set(2);
            IOException identityFailure = assertThrows(IOException.class, prepared::requireCurrent);
            assertEquals(1, childSamples.get());
            assertSame(creationChanged, identityFailure.getCause());
            assertTrue(identityFailure.getMessage().contains("immutable creation identity: " + root));

            childSamples.set(0); mode.set(3);
            IOException untypedFailure = assertThrows(IOException.class, prepared::requireCurrent);
            assertSame(untyped, untypedFailure.getCause());
            assertTrue(untypedFailure.getMessage().contains("operation=nativeHeldDirectory; path=" + root));
            assertEquals(1, childSamples.get(), "Error text never acquires typed mutable retry authority");
            armed.set(false); prepared.requireCurrent();
        }
        assertThrows(IOException.class, retained::requireCurrent);
        assertTrue(Files.isDirectory(root));
    }


    @Test void realHeldDeletePendingDescendantsRestartCompleteMutableCensusAndKeepOtherStatesStrict() throws Exception {
        Fixture fixture = fixture("native-delete-pending");
        Path file = Files.write(fixture.build().resolve("actual-disappearing.bin"), new byte[1]);
        Files.write(fixture.build().resolve("retained-stable.bin"), new byte[8192]);
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(file),
                0x80, 7, null, 3, 0x00200000, null);
        assertNotEquals(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE, handle);
        var changed = new java.util.concurrent.atomic.AtomicBoolean();
        var samples = new java.util.concurrent.atomic.AtomicInteger();
        try {
            var measured = ControlBuild.accountWorkpackage(fixture.config(), () -> {},
                    metadataObserver(file, samples, sample -> {
                        if (changed.compareAndSet(false, true)) {
                            Files.write(file, new byte[65536]);
                            assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.DeleteFile(SharedSourceFiles.nativePath(file)));
                            var state = assertThrows(SharedSourceFiles.NativeEntryStateException.class,
                                    () -> SharedSourceFiles.nativeHeldFile(handle)).state();
                            assertTrue(state.onlyDeletePending());
                        }
                    }));
            assertTrue(changed.get()); assertTrue(samples.get() >= 2);
            var complete = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
            assertEquals(complete.logicalBytesByScope(), measured.logicalBytesByScope(),
                    "Discard the interrupted partial census and measure the complete remaining tree");
            assertTrue(measured.logicalBytesByScope().get("build") >= 8192);
            assertFalse(Files.exists(file));
        } finally {
            assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle));
        }

        for (var state : List.of(new SharedSourceFiles.NativeEntryState(true, false, false, false),
                new SharedSourceFiles.NativeEntryState(false, false, true, false),
                new SharedSourceFiles.NativeEntryState(true, true, false, false))) {
            Fixture strict = fixture("strict-entry-" + (state.reparse() ? "reparse" : "kind") + "-" + state.deletePending());
            Path path = Files.write(strict.build().resolve("strict.bin"), new byte[1]);
            var seen = new java.util.concurrent.atomic.AtomicInteger();
            var rejected = new SharedSourceFiles.NativeEntryStateException(state);
            IOException failure = assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(strict.config(),
                    () -> {}, metadataObserver(path, seen, sample -> { throw rejected; })));
            assertEquals(1, seen.get()); assertSame(rejected, failure.getCause());
            assertTrue(failure.getMessage().contains(path.toString()));
        }

        Fixture immutable = fixture("immutable-delete-pending");
        Path original = immutable.snapshot().resolve("pom.xml");
        var immutableSamples = new java.util.concurrent.atomic.AtomicInteger();
        var pending = new SharedSourceFiles.NativeEntryStateException(
                new SharedSourceFiles.NativeEntryState(false, true, false, false));
        IOException immutableFailure = assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(immutable.config(),
                () -> {}, metadataObserver(original, immutableSamples, sample -> { throw pending; })));
        assertEquals(1, immutableSamples.get()); assertSame(pending, immutableFailure.getCause());

        Fixture root = fixture("root-delete-pending");
        var rootSamples = new java.util.concurrent.atomic.AtomicInteger();
        IOException rootFailure = assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(root.config(),
                () -> {}, metadataObserver(root.build(), rootSamples, sample -> {
                    throw new SharedSourceFiles.NativeEntryStateException(
                            new SharedSourceFiles.NativeEntryState(false, true, true, true));
                })));
        assertEquals(1, rootSamples.get());
        assertTrue(rootFailure.getMessage().contains(root.build().toString()));

        Fixture untyped = fixture("untyped-delete-pending");
        Path unknown = Files.write(untyped.build().resolve("unknown.bin"), new byte[1]);
        IOException arbitrary = new IOException("ordinary non-reparse non-delete-pending source required");
        var unknownSamples = new java.util.concurrent.atomic.AtomicInteger();
        IOException unknownFailure = assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(untyped.config(),
                () -> {}, metadataObserver(unknown, unknownSamples, sample -> { throw arbitrary; })));
        assertSame(arbitrary, unknownFailure.getCause());
        assertTrue(unknownFailure.getMessage().contains("operation=nativeHeldFile; path=" + unknown));
        assertEquals(1, unknownSamples.get());
    }


    @Test void boundedCleanupWaveWaitsBetweenCompleteCensusesAndPreservesOriginalLimits() throws Exception {
        Fixture fixture = fixture("paced-cleanup-wave");
        Path root = Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Files.write(root.resolve("retained.bin"), new byte[8192]);
        Files.write(root.resolve("wave-1.tmp"), new byte[4096]);
        var firstVisit = new java.util.concurrent.atomic.AtomicLong();
        var removals = new java.util.concurrent.atomic.AtomicInteger();
        var completeCensuses = new java.util.concurrent.atomic.AtomicInteger();
        long waveNanos = java.util.concurrent.TimeUnit.MILLISECONDS.toNanos(250);
        var result = ControlBuild.accountWorkpackage(fixture.config(), () -> {}, new ControlBuild.InventoryObserver() {
            @Override public void beforeCheck(Path path) throws IOException {
                if (path.equals(root)) {
                    long now = System.nanoTime(); firstVisit.compareAndSet(0, now);
                    completeCensuses.incrementAndGet();
                } else if (path.equals(root.resolve("wave-1.tmp")) && System.nanoTime() - firstVisit.get() < waveNanos) {
                    Files.delete(path); removals.incrementAndGet();
                }
            }
            @Override public void afterMissingAccountingEntry(Path path) throws IOException {
                if (path.equals(root.resolve("wave-1.tmp")) && System.nanoTime() - firstVisit.get() < waveNanos)
                    Files.write(path, new byte[4096]);
            }
        });
        assertTrue(removals.get() > 0, "The real mutable file must disappear during at least one interrupted census");
        assertTrue(completeCensuses.get() > 1 && completeCensuses.get() <= 8);
        assertTrue(System.nanoTime() - firstVisit.get() >= waveNanos,
                "Do not consume all complete retries before the actual finite cleanup wave can settle");
        var quiet = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        assertEquals(quiet.logicalBytesByScope(), result.logicalBytesByScope());
        assertTrue(result.logicalBytesByScope().get("private_tmp") >= 8192);
        assertEquals(381072, ControlBuild.WORKPACKAGE_INVENTORY_LIMITS.totalEntries());

        Fixture cancelled = fixture("paced-cleanup-cancel");
        Path cancelledRoot = Path.of(cancelled.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Path transientFile = Files.write(cancelledRoot.resolve("vanishing.tmp"), new byte[1]);
        var active = new java.util.concurrent.atomic.AtomicBoolean(true);
        IOException cancellation = new IOException("actual retry guard cancellation");
        assertSame(cancellation, assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(cancelled.config(),
                () -> { if (!active.get()) throw cancellation; }, path -> {
                    if (path.equals(transientFile)) { Files.delete(path); active.set(false); }
                })), "A cancelled live guard cannot wait through backoff or obtain a successful partial census");
    }

    @Test void confirmedMutableSubtreeAbsenceHandlesMoreThanEightRemovalsWithoutRestart() throws Exception {
        Fixture fixture = fixture("sixteen-removed-subtrees");
        Path root = Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Files.write(root.resolve("retained.bin"), new byte[8192]);
        for (int number = 1; number <= 16; number++) {
            Path directory = Files.createDirectories(root.resolve("junit-wave-" + number)
                    .resolve("missing-module/native-transport/src/test"));
            Files.write(directory.resolve("fixture.bin"), new byte[128]);
        }
        var roots = new java.util.concurrent.atomic.AtomicInteger();
        var removed = new java.util.concurrent.atomic.AtomicInteger();
        var confirmed = new java.util.concurrent.atomic.AtomicInteger();
        var actual = ControlBuild.accountWorkpackage(fixture.config(), () -> {}, new ControlBuild.InventoryObserver() {
            @Override public void beforeCheck(Path path) throws IOException {
                if (path.equals(root)) roots.incrementAndGet();
                if (path.endsWith(Path.of("missing-module/native-transport/src/test"))) {
                    removeFixtureTree(root, path.getParent().getParent().getParent()); removed.incrementAndGet();
                }
            }
            @Override public void afterMissingAccountingEntry(Path path) throws IOException {
                int attributes = com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes(SharedSourceFiles.nativePath(path));
                int error = com.sun.jna.Native.getLastError();
                assertEquals(-1, attributes); assertEquals(3, error); confirmed.incrementAndGet();
            }
        });
        assertEquals(16, removed.get()); assertEquals(16, confirmed.get()); assertEquals(1, roots.get());
        assertEquals(8192L, actual.logicalBytesByScope().get("private_tmp"));
        var quiet = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        assertEquals(quiet.logicalBytesByScope(), actual.logicalBytesByScope());
        assertTrue(actual.nativeAllocatedBytesByScope().get("private_tmp") >= quiet.nativeAllocatedBytesByScope().get("private_tmp"),
                "Already observed ancestor allocations remain conservatively charged after their later removal");
        assertNull(actual.mavenRepositoryCurrentBytes()); assertEquals(381072, ControlBuild.WORKPACKAGE_INVENTORY_LIMITS.totalEntries());
    }

    @Test void recreatedMutableEntryResamplesAndAncestorRootOrKindReplacementRejects() throws Exception {
        Fixture recreated = fixture("actual-recreated-entry");
        Path root = Path.of(recreated.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Path file = Files.write(root.resolve("recreated.bin"), new byte[1]);
        var once = new java.util.concurrent.atomic.AtomicBoolean();
        var censuses = new java.util.concurrent.atomic.AtomicInteger();
        var actual = ControlBuild.accountWorkpackage(recreated.config(), () -> {}, new ControlBuild.InventoryObserver() {
            @Override public void beforeCheck(Path path) throws IOException {
                if (path.equals(root)) censuses.incrementAndGet();
                if (path.equals(file) && once.compareAndSet(false, true)) Files.delete(file);
            }
            @Override public void afterMissingAccountingEntry(Path path) throws IOException {
                if (path.equals(file)) Files.write(file, new byte[32768]);
            }
        });
        assertEquals(2, censuses.get()); assertEquals(32768L, actual.logicalBytesByScope().get("private_tmp"));
        for (String mutation : List.of("ancestor", "root", "kind", "denied", "unknown")) {
            Fixture changed = fixture("missing-rejection-" + mutation);
            Path changedRoot = Path.of(changed.release().workpackageAccounting().measuredRoots().get("private_tmp"));
            Path parent = Files.createDirectory(changedRoot.resolve("parent"));
            Path missing = Files.write(parent.resolve("removed.bin"), new byte[1]);
            IOException denied = new java.nio.file.AccessDeniedException(missing.toString());
            IOException unknown = new IOException("unclassified disappearance lookalike");
            IOException rejected = assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(changed.config(), () -> {},
                    new ControlBuild.InventoryObserver() {
                        @Override public void beforeCheck(Path path) throws IOException { if (path.equals(missing)) Files.delete(path); }
                        @Override public void afterMissingAccountingEntry(Path path) throws IOException {
                            if (!path.equals(missing)) return;
                            switch (mutation) {
                                case "ancestor" -> { Files.move(parent, changedRoot.resolve("old-parent")); Files.createDirectory(parent); }
                                case "root" -> changeFixtureCreationTime(changedRoot);
                                case "kind" -> Files.createDirectory(missing);
                                case "denied" -> throw denied;
                                case "unknown" -> throw unknown;
                                default -> throw new AssertionError("closed fixture mutation");
                            }
                        }
                    }));
            if (mutation.equals("denied")) assertSame(denied, rejected);
            else if (mutation.equals("unknown")) assertSame(unknown, rejected);
            else {
                assertEquals("org.xar.ck3.control.build.ControlBuild$AccountingIntegrityFailure", rejected.getClass().getName(),
                        "Only the actual shared typed identity/kind guard grants this rejection proof");
                Path expectedPath = mutation.equals("root") ? changedRoot : mutation.equals("ancestor") ? parent : missing;
                assertEquals((mutation.equals("kind") ? "Accounting entry kind changed during absence confirmation: "
                        : "Observed accounting ancestor identity changed: ") + expectedPath, rejected.getMessage());
            }
        }
    }

    private static void changeFixtureCreationTime(Path directory) throws IOException {
        String original = SharedSourceFiles.nativeDirectory(directory).creationFiletimeDecimal();
        long changed = new java.math.BigInteger(original).add(java.math.BigInteger.valueOf(10000)).longValueExact();
        var value = new com.sun.jna.platform.win32.WinBase.FILETIME();
        value.dwLowDateTime = (int) changed;
        value.dwHighDateTime = (int) (changed >>> 32);
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(directory),
                0x100, 7, null, 3, 0x00200000 | 0x02000000, null);
        if (com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))
            throw new IOException("Fixture creation-time open Win32=" + com.sun.jna.Native.getLastError());
        try {
            if (com.sun.jna.platform.win32.Kernel32.INSTANCE.SetFileTime(handle, value, null, null) == 0)
                throw new IOException("Fixture creation-time mutation Win32=" + com.sun.jna.Native.getLastError());
        } finally {
            if (!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("Fixture metadata close failed");
        }
        assertNotEquals(original, SharedSourceFiles.nativeDirectory(directory).creationFiletimeDecimal());
    }

    private static void removeFixtureTree(Path boundary, Path subtree) throws IOException {
        if (subtree.equals(boundary) || !subtree.startsWith(boundary)) throw new IOException("Exact owned descendant fixture required");
        try (var entries = Files.walk(subtree)) {
            for (Path path : entries.sorted(java.util.Comparator.reverseOrder()).toList()) Files.delete(path);
        }
    }

    /** Restrict only explicitly owned fixture directories; original control handles restore their exact DACLs. */
    private static final class NativeReadDenial implements java.io.Closeable {
        private final Path path;
        private final int mask;
        private final com.sun.jna.platform.win32.WinNT.HANDLE control;
        private final com.sun.jna.Pointer descriptor,originalDacl;
        private final byte[] originalBytes;
        private final com.sun.jna.platform.win32.WinNT.ACL restricted;
        private boolean denied;
        private NativeReadDenial(Path path,int mask,com.sun.jna.platform.win32.WinNT.HANDLE control,
                com.sun.jna.Pointer descriptor,com.sun.jna.Pointer originalDacl,byte[] originalBytes,
                com.sun.jna.platform.win32.WinNT.ACL restricted) {
            this.path=path;this.mask=mask;this.control=control;this.descriptor=descriptor;this.originalDacl=originalDacl;
            this.originalBytes=originalBytes;this.restricted=restricted;
        }
        static NativeReadDenial open(Path path,int mask,Path ownedFixtureRoot)throws IOException {
            Path actual=path.toRealPath(),owned=ownedFixtureRoot.toRealPath();
            if(!actual.startsWith(owned)||actual.equals(owned)||(mask!=1&&mask!=0x80))
                throw new IOException("Only isolated fixture descendants and exact LIST/READ_ATTRIBUTES rights may be restricted");
            var kernel=com.sun.jna.platform.win32.Kernel32.INSTANCE;
            var api=com.sun.jna.platform.win32.Advapi32.INSTANCE;
            var handle=kernel.CreateFile(SharedSourceFiles.nativePath(path),0x20000|0x40000|0x80,
                    7,null,3,0x00200000|0x02000000,null);
            if(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))
                throw new IOException("Native5 fixture control unavailable; Win32="+com.sun.jna.Native.getLastError()+" path="+path);
            var descriptor=new com.sun.jna.ptr.PointerByReference();boolean retained=false;
            try {
                var dacl=new com.sun.jna.ptr.PointerByReference();
                status(api.GetSecurityInfo(handle,1,4,null,null,dacl,null,descriptor),"GetSecurityInfo");
                if(dacl.getValue()==null)throw new IOException("An existing non-null fixture DACL is required");
                var original=new com.sun.jna.platform.win32.WinNT.ACL(dacl.getValue());
                int length=Short.toUnsignedInt(original.AclSize);
                if(length<8||length>60000)throw new IOException("Bounded original fixture DACL required");
                byte[] exact=dacl.getValue().getByteArray(0,length);
                var world=new com.sun.jna.platform.win32.WinNT.PSID(
                        com.sun.jna.platform.win32.Advapi32Util.convertStringSidToSid("S-1-1-0"));
                var deny=new com.sun.jna.platform.win32.WinNT.ACCESS_DENIED_ACE(mask,(byte)0,world);
                int added=Short.toUnsignedInt(deny.AceSize),capacity=Math.addExact(length,added);
                var restricted=new com.sun.jna.platform.win32.WinNT.ACL(capacity);
                restricted.getPointer().write(0,exact,0,exact.length);
                restricted.getPointer().setShort(2,(short)capacity);restricted.read();
                if(!api.AddAce(restricted,Byte.toUnsignedInt(original.AclRevision),0,deny.getPointer(),added))
                    throw new IOException("Fixture deny ACE unavailable; Win32="+com.sun.jna.Native.getLastError());
                var result=new NativeReadDenial(path,mask,handle,descriptor.getValue(),dacl.getValue(),exact,restricted);
                retained=true;return result;
            } finally {
                if(!retained) {
                    if(descriptor.getValue()!=null)kernel.LocalFree(descriptor.getValue());
                    if(!kernel.CloseHandle(handle))throw new IOException("Fixture control close failed: "+path);
                }
            }
        }
        private static void status(int code,String operation)throws IOException {
            if(code!=0)throw new IOException("Native5 fixture "+operation+" failed; Win32="+code);
        }
        private byte[] actualDacl()throws IOException {
            var current=new com.sun.jna.ptr.PointerByReference();var storage=new com.sun.jna.ptr.PointerByReference();
            try {
                status(com.sun.jna.platform.win32.Advapi32.INSTANCE.GetSecurityInfo(control,1,4,null,null,current,null,storage),"GetSecurityInfo(actual)");
                if(current.getValue()==null)throw new IOException("Actual fixture DACL disappeared");
                int size=Short.toUnsignedInt(new com.sun.jna.platform.win32.WinNT.ACL(current.getValue()).AclSize);
                if(size<8||size>65535)throw new IOException("Bounded actual fixture DACL required");
                return current.getValue().getByteArray(0,size);
            } finally { if(storage.getValue()!=null)com.sun.jna.platform.win32.Kernel32.INSTANCE.LocalFree(storage.getValue()); }
        }
        private static String digest(byte[] bytes)throws IOException {
            try { return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)); }
            catch(java.security.NoSuchAlgorithmException error) { throw new IOException("SHA-256 unavailable",error); }
        }
        private void deny()throws IOException {
            if(denied)throw new IOException("Original DACL must be restored before another restriction");
            status(com.sun.jna.platform.win32.Advapi32.INSTANCE.SetSecurityInfo(control,1,4,null,null,restricted.getPointer(),null),"SetSecurityInfo(deny)");
            denied=true;
            byte[] actual=actualDacl(),expected=restricted.getPointer().getByteArray(0,Short.toUnsignedInt(restricted.AclSize));
            var fields=java.nio.ByteBuffer.wrap(actual).order(java.nio.ByteOrder.LITTLE_ENDIAN);
            if(actual.length<28)throw new IOException("Actual deny ACE is absent");
            System.out.println("native5_fixture actual_acl path="+path+" revision="+Byte.toUnsignedInt(actual[0])
                    +" size="+Short.toUnsignedInt(fields.getShort(2))+" count="+Short.toUnsignedInt(fields.getShort(4))
                    +" first_type="+Byte.toUnsignedInt(actual[8])+" first_flags="+Byte.toUnsignedInt(actual[9])
                    +" first_size="+Short.toUnsignedInt(fields.getShort(10))+" first_mask="+fields.getInt(12)
                    +" first_sid="+java.util.HexFormat.of().formatHex(actual,16,28)+" raw_sha256="+digest(actual));
            if(!java.util.Arrays.equals(expected,actual)||actual[8]!=1||actual[9]!=0
                    ||Short.toUnsignedInt(fields.getShort(10))!=20||fields.getInt(12)!=mask
                    ||!java.util.Arrays.equals(java.util.Arrays.copyOfRange(actual,16,28),
                            com.sun.jna.platform.win32.Advapi32Util.convertStringSidToSid("S-1-1-0")))
                throw new IOException("Actual deny ACL/ACE differs from exact constructed fixture ACL: "+path);
        }
        private record OpenObservation(boolean opened,int error) { }
        private OpenObservation observeOpen(int access)throws IOException {
            var kernel=com.sun.jna.platform.win32.Kernel32.INSTANCE;
            var reopened=kernel.CreateFile(SharedSourceFiles.nativePath(path),access,7,null,3,0x00200000|0x02000000,null);
            int error=com.sun.jna.Native.getLastError();
            if(!com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(reopened)) {
                if(!kernel.CloseHandle(reopened))throw new IOException("Unexpected fixture read handle close failed");
                return new OpenObservation(true,error);
            }
            return new OpenObservation(false,error);
        }
        void denyAndConfirmNative5(NativeReadDenial parent)throws IOException {
            // LIST on a parent independently grants READ_ATTRIBUTES on a child; both exact rights must be denied.
            if(mask!=0x80||parent.mask!=1||!path.getParent().equals(parent.path))
                throw new IOException("Exact isolated parent/child fixture restrictions required");
            parent.deny();deny();
            var parentOpen=parent.observeOpen(1);var childOpen=observeOpen(0x80);
            System.out.println("native5_fixture native_op=CreateFile share=7 disposition=3 flags=0x02200000 parent_access=1 parent="
                    +parentOpen+" child_access=128 child="+childOpen+" path="+path);
            if(parentOpen.opened()||parentOpen.error()!=5||childOpen.opened()||childOpen.error()!=5)
                throw new IOException("Native5 fixture unavailable after actual parent/child ACL readback: parent="
                        +parentOpen+" child="+childOpen+" path="+path);
        }
        void restore()throws IOException {
            if(!denied)return;
            var api=com.sun.jna.platform.win32.Advapi32.INSTANCE;
            status(api.SetSecurityInfo(control,1,4,null,null,originalDacl,null),"SetSecurityInfo(restore)");
            var current=new com.sun.jna.ptr.PointerByReference();var owner=new com.sun.jna.ptr.PointerByReference();
            try {
                status(api.GetSecurityInfo(control,1,4,null,null,current,null,owner),"GetSecurityInfo(restored)");
                if(current.getValue()==null)throw new IOException("Restored fixture DACL disappeared");
                int size=Short.toUnsignedInt(new com.sun.jna.platform.win32.WinNT.ACL(current.getValue()).AclSize);
                if(size!=originalBytes.length||!java.util.Arrays.equals(originalBytes,current.getValue().getByteArray(0,size)))
                    throw new IOException("Fixture DACL restoration differs from original bytes: "+path);
                denied=false;
            } finally { if(owner.getValue()!=null)com.sun.jna.platform.win32.Kernel32.INSTANCE.LocalFree(owner.getValue()); }
        }
        @Override public void close()throws IOException {
            IOException failure=null;
            try { restore(); } catch(IOException error) { failure=error; }
            var kernel=com.sun.jna.platform.win32.Kernel32.INSTANCE;
            if(kernel.LocalFree(descriptor)!=null) {
                var error=new IOException("Fixture security descriptor release failed: "+path);
                if(failure==null)failure=error;else failure.addSuppressed(error);
            }
            if(!kernel.CloseHandle(control)) {
                var error=new IOException("Fixture control handle close failed: "+path);
                if(failure==null)failure=error;else failure.addSuppressed(error);
            }
            if(failure!=null)throw failure;
        }
    }
    @Test void realNative5OnPrivateTmpDescendantRestartsWholeCensusAndGenericDeniedStillRejects()throws Exception {
        Fixture fixture=fixture("native5-tmp");Path root=Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
        Files.write(root.resolve("stable-a.bin"),new byte[4096]);Files.write(root.resolve("stable-b.bin"),new byte[8192]);
        Path victim=Files.createDirectory(root.resolve("restricted-directory"));
        var changed=new java.util.concurrent.atomic.AtomicBoolean();var armed=new java.util.concurrent.atomic.AtomicBoolean();
        var restored=new java.util.concurrent.atomic.AtomicInteger();
        var roots=new java.util.concurrent.atomic.AtomicInteger();
        try(var parent=NativeReadDenial.open(victim.getParent(),1,temporary);
                var restriction=NativeReadDenial.open(victim,0x80,temporary)) {
            // The production catch invokes this guard after the real metadata failure, before opening another census.
            CiBootstrap.IoGuard active=()->{
                if(armed.compareAndSet(true,false)){parent.restore();restriction.restore();restored.incrementAndGet();}
            };
            var actual=ControlBuild.accountWorkpackage(fixture.config(),active,new ControlBuild.InventoryObserver() {
                @Override public void beforeCheck(Path path)throws IOException {
                    if(path.equals(root))roots.incrementAndGet();
                    if(path.equals(victim)&&changed.compareAndSet(false,true)){restriction.denyAndConfirmNative5(parent);armed.set(true);}
                }
                @Override public void afterMissingAccountingEntry(Path path) {
                    if(path.equals(victim))fail("A present ACL-denied directory cannot be treated as missing");
                }
            });
            assertTrue(changed.get());assertEquals(1,restored.get());assertEquals(2,roots.get());
            var quiet=ControlBuild.accountWorkpackage(fixture.config(),()->{});
            assertEquals(12288L,actual.logicalBytesByScope().get("private_tmp"));
            assertEquals(quiet.logicalBytesByScope(),actual.logicalBytesByScope());
            assertEquals(quiet.nativeAllocatedBytesByScope(),actual.nativeAllocatedBytesByScope(),
                    "Discard all interrupted totals, including the already counted root directory");
        }
        var generic=new java.nio.file.AccessDeniedException(root.resolve("stable-a.bin").toString());var visits=new java.util.concurrent.atomic.AtomicInteger();
        assertSame(generic,assertThrows(java.nio.file.AccessDeniedException.class,()->ControlBuild.accountWorkpackage(fixture.config(),()->{},path->{
            if(path.equals(root))visits.incrementAndGet();if(path.equals(root.resolve("stable-a.bin")))throw generic;
        })));assertEquals(1,visits.get());
    }
    @Test void persistentNative5ExhaustsEightCensusesAndRootImmutableOrOtherScopeNeverRetries()throws Exception {
        for(String kind:List.of("persistent","root","source","build")) {
            Fixture fixture=fixture("native5-"+kind);Path tmp=Path.of(fixture.release().workpackageAccounting().measuredRoots().get("private_tmp"));
            Path root=kind.equals("source")?fixture.snapshot():kind.equals("build")?fixture.build():tmp;
            Path victim=kind.equals("root")?root:Files.createDirectory(root.resolve("restricted-directory"));
            var changed=new java.util.concurrent.atomic.AtomicBoolean();
            var armed=new java.util.concurrent.atomic.AtomicBoolean();var denials=new java.util.concurrent.atomic.AtomicInteger();
            var roots=new java.util.concurrent.atomic.AtomicInteger();var restored=new java.util.concurrent.atomic.AtomicInteger();
            try(var parent=NativeReadDenial.open(victim.getParent(),1,temporary);
                    var restriction=NativeReadDenial.open(victim,0x80,temporary)) {
                if(kind.equals("root")){restriction.denyAndConfirmNative5(parent);changed.set(true);denials.incrementAndGet();}
                CiBootstrap.IoGuard active=()->{
                    if(kind.equals("persistent")&&armed.compareAndSet(true,false)) {
                        parent.restore();restriction.restore();restored.incrementAndGet();changed.set(false);
                    }
                };
                var failure=assertThrows(IOException.class,()->ControlBuild.accountWorkpackage(fixture.config(),active,path->{
                    if(path.equals(root))roots.incrementAndGet();
                    if(path.equals(victim)&&changed.compareAndSet(false,true)) {
                        restriction.denyAndConfirmNative5(parent);denials.incrementAndGet();
                        if(kind.equals("persistent"))armed.set(true);
                    }
                }));
                if(kind.equals("persistent")) {
                    assertEquals(8,denials.get());assertEquals(8,restored.get());
                    assertEquals(8,roots.get());assertTrue(failure.getMessage().contains("8 complete census attempts"));
                    assertInstanceOf(java.nio.file.AccessDeniedException.class,failure.getCause());
                    assertTrue(failure.getCause().getClass().getSimpleName().equals("AccountingNativeAccessDenied"));
                    assertTrue(failure.getCause().getMessage().contains("Win32=5"));
                    assertTrue(failure.getCause().getMessage().contains("operation="));
                    assertTrue(failure.getCause().getMessage().contains(victim.toString()));
                } else {
                    assertTrue(changed.get());assertEquals(1,denials.get());
                    assertTrue(roots.get()<=1,"Root, immutable source and non-TMP scope must reject immediately");
                    if(!kind.equals("root"))assertInstanceOf(java.nio.file.AccessDeniedException.class,failure);
                }
            }
        }
    }
    private static ControlBuild.AttemptAccountingAuthority publicationCaps(Fixture fixture,long logical,long nativeBytes,
            long wholeLogical,long wholeNative)throws Exception {
        var mapper=ControlBuild.strictMapper();ObjectNode release=mapper.valueToTree(fixture.release());
        ObjectNode authority=(ObjectNode)release.get("workpackage_accounting");
        ((ObjectNode)authority.get("logical_caps_by_scope")).put("logs",logical);
        ((ObjectNode)authority.get("native_caps_by_scope")).put("logs",nativeBytes);
        authority.put("maximum_new_logical_bytes",wholeLogical);authority.put("maximum_new_native_bytes",wholeNative);
        Files.write(fixture.config().capacityRelease(),mapper.writeValueAsBytes(release));
        return mapper.treeToValue(release,ControlBuild.AttemptCapacityRelease.class).workpackageAccounting();
    }
    @Test void actualAccountingPublicationUsesProfileEnvelopeAndKeepsLogicalNativePartAndWholeLimits()throws Exception {
        for(String kind:List.of("standard","resumed","native-part","logical-whole","native-whole")) {
            Fixture fixture=fixture("publication-"+kind);
            Files.write(fixture.config().workRoot().resolve("logs/build-"+fixture.config().attempt()+"-test.stdout.log"),new byte[8192]);
            long normal=4L<<20,whole=32L<<20;
            var authority=publicationCaps(fixture,normal,kind.equals("native-part")?2L<<20:normal,
                    kind.equals("logical-whole")?2L<<20:whole,kind.equals("native-whole")?2L<<20:whole);
            var original=fixture.config();
            var profile=kind.equals("resumed")?ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261025_R7:ControlBuild.SourceLimitProfile.STANDARD_8_MIB;
            var config=new ControlBuild.Config(original.sourceRoot(),original.workRoot(),original.capacityRelease(),original.attempt(),
                    original.ownerTask(),original.mavenCommand(),original.javaHome(),original.minimumMavenVersion(),original.timeoutSeconds(),
                    kind.equals("resumed")?ControlBuild.TargetKind.SERVICE_FAST_JAR:original.targetKind(),profile);
            assertEquals(kind.equals("resumed")?4<<20:2<<20,ControlBuild.receiptMaxBytes(profile));
            var accounting=ControlBuild.accountWorkpackage(config,()->{});
            if(kind.equals("standard")) {
                var pin=ControlBuild.publishAttemptAccounting(config,accounting,authority,()->{});
                assertEquals(accounting,ControlBuild.readCompletedAccounting(pin));
                var retained=SharedSourceFiles.observe(Path.of(pin.path()));
                assertThrows(IOException.class,()->ControlBuild.publishAttemptAccounting(config,accounting,authority,()->{}));
                SharedSourceFiles.assertUnchanged(retained);pin.verify();
            } else {
                assertThrows(IOException.class,()->ControlBuild.publishAttemptAccounting(config,accounting,authority,()->{}));
                assertFalse(Files.exists(fixture.accounting()),"No over-reservation publication may be created");
            }
        }
    }

    @Test void completedRetainedSourcesSurviveRealHeadCasWhileLiveAdmissionsStayStrict() throws Exception {
        Fixture fixture = mutableReservationFixture("completed-head");
        var terminal = ControlBuildTest.completedReceiptFixture(temporary.resolve("completed-head-terminal"));
        var accounting = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        var accountingRef = ControlBuild.publishAttemptAccounting(fixture.config(), accounting,
                fixture.release().workpackageAccounting(), () -> {});
        var wire = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(accountingRef.path())),
                ControlBuild.CompletedWorkpackageAccounting.class);
        assertEquals(ControlBuild.COMPLETED_ACCOUNTING_SCHEMA, wire.schema());
        assertEquals(accounting, wire.accounting());
        assertEquals(fixture.release().workpackageAccounting().reservationSourceRefs(),
                wire.reservationSources().stream().map(ControlBuild.RetainedAccountingSource::originalRef).toList());
        assertEquals(wire, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(wire),
                ControlBuild.CompletedWorkpackageAccounting.class));
        String python = System.getenv("XAR_ORACLE_PYTHON");
        assertNotNull(python, "The same admitted oracle environment precedes this accounting regression");
        Path settings = fixture.config().workRoot().resolve("logs/build-completed-head-settings.xml");
        List<String> verify = ControlBuild.releasedReactorVerifyArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(),
                Map.of("XAR_ORACLE_PYTHON", python), Instant.now());
        List<String> capture = new ArrayList<>(verify); assertEquals("verify", capture.removeLast());
        capture.add("-Dmaven.test.skip=false"); capture.add("-DskipTests=true"); capture.add("package");
        Instant captureCompleted = Instant.now();
        var releaseRef = ControlBuild.FileRef.measure(fixture.config().capacityRelease());
        assertEquals(capture, ControlBuild.completedCaptureArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(),
                capture, releaseRef, captureCompleted, accountingRef));
        Path receiptPath = temporary.resolve("completed-head-receipt.json");
        var receipt = completed(fixture, terminal.receipt());
        Files.write(receiptPath, ControlBuild.strictMapper().writeValueAsBytes(receipt));
        var receiptRef = ControlBuild.FileRef.measure(receiptPath);
        assertEquals(receipt, ControlBuild.verifiedCompletedReceipt(receiptRef));
        var originalHead = fixture.release().workpackageAccounting().reservationSourceRefs().getFirst();
        Files.writeString(Path.of(originalHead.path()), "{\"storage_revision\":2}\n");
        assertThrows(IOException.class, originalHead::verify, "The real mutable head did change");
        assertEquals(receipt, ControlBuild.verifiedCompletedReceipt(receiptRef),
                "Completed evidence consumes its retained exact original source, independent of a later CAS");
        assertEquals(capture, ControlBuild.completedCaptureArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(),
                capture, releaseRef, captureCompleted, accountingRef), "The actual capture command consumer also uses retained sources");
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(),
                capture, releaseRef, captureCompleted), "The old overload must not find unpinned snapshots");
        List<String> wrongTmp = capture.stream().map(value -> value.startsWith("-Djava.io.tmpdir=")
                ? "-Djava.io.tmpdir=" + fixture.config().workRoot().resolve("scratch") : value).toList();
        assertThrows(IOException.class, () -> ControlBuild.completedCaptureArguments(fixture.config(), settings, fixture.snapshot(), fixture.build(),
                wrongTmp, releaseRef, captureCompleted, accountingRef), "Retained sources cannot weaken the exact original command/TMP contract");
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(fixture.config(), () -> {}),
                "Historical source bodies must never renew a current lease");
        assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(receiptPath),
                "The active accepted-receipt route must still validate the current original lease");
        accountingRef.verify(); receiptRef.verify();
    }

    @Test void completedV2RejectsMissingForeignChangedOrWrongTypeSourcesAndRetainsOtherProofs() throws Exception {
        Fixture fixture = mutableReservationFixture("completed-source-reject");
        var terminal = ControlBuildTest.completedReceiptFixture(temporary.resolve("source-reject-terminal"));
        var accounting = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        var accountingRef = ControlBuild.publishAttemptAccounting(fixture.config(), accounting,
                fixture.release().workpackageAccounting(), () -> {});
        byte[] original = Files.readAllBytes(Path.of(accountingRef.path()));
        Path receiptPath = temporary.resolve("source-reject-receipt.json");
        var mapper = ControlBuild.strictMapper();
        for (String mutation : List.of("missing", "missing-field", "null", "foreign", "body", "body-type", "bytes-type", "holds", "machine")) {
            ObjectNode body = (ObjectNode) mapper.readTree(original);
            var sources = (com.fasterxml.jackson.databind.node.ArrayNode) body.get("reservation_sources");
            if (mutation.equals("missing")) sources.remove(0);
            if (mutation.equals("missing-field")) ((ObjectNode) sources.get(0)).remove("body_base64");
            if (mutation.equals("null")) body.putNull("reservation_sources");
            if (mutation.equals("foreign"))
                ((ObjectNode) sources.get(0).get("original_ref")).put("path", temporary.resolve("foreign-head.json").toString());
            if (mutation.equals("body"))
                ((ObjectNode) sources.get(0)).put("body_base64", java.util.Base64.getEncoder().encodeToString("wrong".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            if (mutation.equals("body-type")) ((ObjectNode) sources.get(0)).put("body_base64", true);
            if (mutation.equals("bytes-type")) ((ObjectNode) sources.get(0).get("original_ref")).put("bytes", true);
            if (mutation.equals("machine")) ((ObjectNode) body.get("accounting")).put("machine_id", "foreign-machine");
            if (mutation.equals("holds")) {
                ObjectNode volume = (ObjectNode) body.get("accounting").get("volumes").get(0);
                volume.put("all_holds_bytes", 1);
                volume.put("required_free_bytes", 1 + volume.path("system_growth_reserve").longValue() + volume.path("safety_reserve").longValue());
            }
            Files.write(fixture.accounting(), mapper.writeValueAsBytes(body));
            Files.write(receiptPath, mapper.writeValueAsBytes(completed(fixture, terminal.receipt())));
            assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receiptPath)), mutation);
        }
        Files.write(fixture.accounting(), original);
        Files.write(receiptPath, mapper.writeValueAsBytes(completed(fixture, terminal.receipt())));
        var receiptRef = ControlBuild.FileRef.measure(receiptPath);
        assertNotNull(ControlBuild.verifiedCompletedReceipt(receiptRef));
        Files.writeString(fixture.source().resolve("src/main/java/ReceiptInput.java"), "final class ChangedReceiptInput {}");
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(receiptRef),
                "Frozen accounting does not waive original source/deployment/runtime/terminal proof checks");
    }

    @Test void legacyAccountingWithoutRetainedBodiesRemainsStrictAfterRealHeadChange() throws Exception {
        Fixture fixture = mutableReservationFixture("legacy-head");
        var terminal = ControlBuildTest.completedReceiptFixture(temporary.resolve("legacy-head-terminal"));
        var accounting = ControlBuild.accountWorkpackage(fixture.config(), () -> {});
        Files.write(fixture.accounting(), ControlBuild.strictMapper().writeValueAsBytes(accounting));
        Path receiptPath = temporary.resolve("legacy-head-receipt.json");
        var receipt = completed(fixture, terminal.receipt());
        Files.write(receiptPath, ControlBuild.strictMapper().writeValueAsBytes(receipt));
        var receiptRef = ControlBuild.FileRef.measure(receiptPath);
        assertEquals(receipt, ControlBuild.verifiedCompletedReceipt(receiptRef));
        Files.writeString(Path.of(fixture.release().workpackageAccounting().reservationSourceRefs().getFirst().path()),
                "{\"storage_revision\":2}\n");
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(receiptRef),
                "No old v1 receipt may acquire retroactive source bodies or be silently promoted");
    }

    @Test void finalPublicationRechecksFreshSourcesAndChargesRetainedBodiesToItsRealEnvelope() throws Exception {
        Fixture changed = mutableReservationFixture("publication-head-race");
        var accounting = ControlBuild.accountWorkpackage(changed.config(), () -> {});
        var calls = new java.util.concurrent.atomic.AtomicInteger();
        var head = changed.release().workpackageAccounting().reservationSourceRefs().getFirst();
        assertThrows(IOException.class, () -> ControlBuild.publishAttemptAccounting(changed.config(), accounting,
                changed.release().workpackageAccounting(), () -> {
                    if (calls.incrementAndGet() == 4) Files.writeString(Path.of(head.path()), "{\"storage_revision\":2}\n");
                }));
        assertFalse(Files.exists(changed.accounting()), "A changed live source cannot publish a completed snapshot envelope");
        Fixture large = mutableReservationFixture("publication-large-body");
        var mapper = ControlBuild.strictMapper();
        var oldHead = large.release().workpackageAccounting().reservationSourceRefs().getFirst();
        Files.writeString(Path.of(oldHead.path()), "x".repeat(100000));
        ObjectNode financial = (ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(large.release().workpackageAccounting().financialSourceRef().path())));
        var refs = List.of(ControlBuild.FileRef.measure(Path.of(oldHead.path())), large.release().policyRef());
        financial.set("old_heads_and_policy_refs", mapper.valueToTree(refs));
        Files.write(Path.of(large.release().workpackageAccounting().financialSourceRef().path()), mapper.writeValueAsBytes(financial));
        ObjectNode release = mapper.valueToTree(large.release());
        ObjectNode authority = (ObjectNode) release.get("workpackage_accounting");
        authority.set("reservation_source_refs", mapper.valueToTree(refs));
        authority.set("financial_source_ref", mapper.valueToTree(ControlBuild.FileRef.measure(Path.of(large.release().workpackageAccounting().financialSourceRef().path()))));
        Files.write(large.config().capacityRelease(), mapper.writeValueAsBytes(release));
        var updated = mapper.treeToValue(release, ControlBuild.AttemptCapacityRelease.class);
        var largeAccounting = ControlBuild.accountWorkpackage(large.config(), () -> {});
        assertThrows(IOException.class, () -> ControlBuild.publishAttemptAccounting(large.config(), largeAccounting,
                updated.workpackageAccounting(), () -> {}), "The 128 KiB bound includes retained source bytes");
        assertFalse(Files.exists(large.accounting()));
    }

    private Fixture mutableReservationFixture(String attempt) throws Exception {
        Fixture original = fixture(attempt);
        Path head = original.source().getParent().resolve("mutable-head.json");
        Files.writeString(head, "{\"storage_revision\":1}\n");
        var mapper = ControlBuild.strictMapper();
        var refs = List.of(ControlBuild.FileRef.measure(head), original.release().policyRef());
        Path financialPath = Path.of(original.release().workpackageAccounting().financialSourceRef().path());
        ObjectNode financial = (ObjectNode) mapper.readTree(Files.readAllBytes(financialPath));
        financial.set("old_heads_and_policy_refs", mapper.valueToTree(refs));
        Files.write(financialPath, mapper.writeValueAsBytes(financial));
        ObjectNode release = mapper.valueToTree(original.release());
        ObjectNode authority = (ObjectNode) release.get("workpackage_accounting");
        authority.set("reservation_source_refs", mapper.valueToTree(refs));
        authority.set("financial_source_ref", mapper.valueToTree(ControlBuild.FileRef.measure(financialPath)));
        Files.write(original.config().capacityRelease(), mapper.writeValueAsBytes(release));
        return new Fixture(original.config(), mapper.treeToValue(release, ControlBuild.AttemptCapacityRelease.class),
                original.source(), original.snapshot(), original.build(), original.accounting());
    }

    Fixture fixture(String attempt) throws Exception {
        Path base = Files.createDirectories(temporary.resolve(attempt)).toRealPath();
        Path source = Files.createDirectory(base.resolve("source")), work = Files.createDirectory(base.resolve("work"));
        Path snapshot = Files.createDirectories(work.resolve("scratch/source-" + attempt)); Path build = Files.createDirectories(work.resolve("build/" + attempt));
        Files.createDirectories(work.resolve("scratch/" + attempt + "-tmp")); Files.createDirectories(work.resolve("logs"));
        Path deployment = Files.createDirectories(build.resolve("ck3-control-build-tools")); Files.createDirectory(deployment.resolve("lib"));
        Files.writeString(deployment.resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar"), "synthetic archive fixture");
        Files.writeString(deployment.resolve("lib/fixture.jar"), "synthetic dependency fixture");
        String pom = "<project><modelVersion>4.0.0</modelVersion><groupId>fixture</groupId><artifactId>receipt</artifactId><version>1</version></project>";
        for (Path tree : List.of(source, snapshot)) {
            Files.writeString(tree.resolve("pom.xml"), pom); Files.createDirectories(tree.resolve("src/main/java"));
            Files.writeString(tree.resolve("src/main/java/ReceiptInput.java"), "final class ReceiptInput {}");
        }
        Path policyPath = base.resolve("policy.json");
        Files.writeString(policyPath, """
                {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                "safety_floor_bytes":1000,"safety_ceiling_bytes":1048576,"safety_volume_fraction":0.0000000001,
                "default_project_quota_ceiling_bytes":9223372036854775807,"default_project_quota_volume_fraction":1.0,"quota_override_max_hours":1}}
                """);
        var policyRef = ControlBuild.FileRef.measure(policyPath); var mapper = ControlBuild.strictMapper();
        var policy = CiBootstrap.readPolicy(Files.readAllBytes(policyPath)); Path volumeRoot = work.getRoot().toRealPath();
        var store = Files.getFileStore(volumeRoot); long total = store.getTotalSpace(), usable = store.getUsableSpace(), used = total - usable;
        var budget = CiBootstrap.calculate(policy, total, usable, 32L << 20, 64L << 20, 1L << 20, used);
        Instant opened = Instant.now().minusSeconds(2), review = opened.plusSeconds(1800); String machine = WindowsJobProcess.currentMachineId();
        String letter = volumeRoot.toString().substring(0, 1).toUpperCase(java.util.Locale.ROOT);
        ObjectNode financial = mapper.createObjectNode();
        financial.put("schema", "xar.java-phase1.resume56-r3-financial-supplement/v1").put("machine_id", machine)
                .put("status", "RELEASED_EXPLICIT_ROOT_AUTHORIZED_0830_REVIEW_SUCCESSOR_WITHOUT_CAP_INCREASE").put("issuer_task", "/root/budget_fast_lane")
                .put("observed_at_utc", opened.toString()).put("review_at_utc", review.toString()).put("quota_review_at_utc", review.toString())
                .put("shared_canonical_m2_growth_hold_once_bytes", 64L << 20).put("whole_R3_cap_after_bytes", 64L << 20)
                .put(letter.equals("D") ? "all_holds_including_current_R3_bytes" : letter + "_other_unspent_holds_bytes", 96L << 20)
                .put(letter + "_quota_bytes", budget.effectiveProjectQuota());
        financial.putNull("current_whole_project_actual_usage_bytes");
        financial.set("old_heads_and_policy_refs", mapper.valueToTree(List.of(policyRef)));
        financial.putObject("reserves").put(letter + "_system_growth", budget.systemGrowthReserve()).put(letter + "_safety", budget.safetyReserve());
        ObjectNode original = financial.putObject("fresh_observations").put("machine_id", machine).put("observed_at_utc", opened.toString()).putObject(letter);
        original.put("total", total).put("used_upper", used).put("actual_cluster_bytes", 4096);
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(volumeRoot.toString(), 0x80, 7, null, 3, 0x00200000 | 0x02000000, null);
        SharedSourceFiles.NativeFile identity;
        try { identity = SharedSourceFiles.nativeHeldDirectory(handle); }
        finally { assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle)); }
        original.putObject("native_root_identity").put("api", "BY_HANDLE_FILE_INFORMATION").put("volume_serial_decimal", identity.legacyVolumeSerialDecimal())
                .put("file_index_decimal", new java.math.BigInteger(identity.legacyFileIdHex(), 16).toString());
        Path financialPath = base.resolve("software-financial.json"); Files.write(financialPath, mapper.writeValueAsBytes(financial));
        Map<String, String> roots = Map.of("maven_repository", work.resolve("m2").toString(), "source_snapshot", snapshot.toString(),
                "build", build.toString(), "private_tmp", work.resolve("scratch/" + attempt + "-tmp").toString(),
                "artifacts", work.resolve("artifacts/" + attempt).toString(), "logs", work.resolve("logs").toString());
        Map<String, Long> scopes = Map.of("source_snapshot", 4L << 20, "build", 4L << 20, "private_tmp", 4L << 20, "artifacts", 4L << 20, "logs", 8L << 20);
        var authority = new ControlBuild.AttemptAccountingAuthority(ControlBuild.ATTEMPT_AUTHORITY_SCHEMA, attempt,
                ControlBuild.FinancialLayout.CAPACITY_SUPPLEMENT18, ControlBuild.FileRef.measure(financialPath), List.of(policyRef), roots,
                scopes, 32L << 20, scopes, 32L << 20, 64L << 20);
        var release = new ControlBuild.AttemptCapacityRelease(ControlBuild.ATTEMPT_RELEASE_SCHEMA, machine, opened.toString(), review.toString(),
                "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE", "software-actual-scope-test", policyRef, List.of(base.toString()),
                work.resolve("m2").toString(), work.resolve("build").toString(), work.resolve("scratch").toString(),
                Map.of("m2", 64L << 20, "build", 64L << 20, "tools", 64L << 20, "scratch", 64L << 20, "artifacts", 64L << 20, "metadata_logs", 64L << 20),
                Map.of(volumeRoot.toString(), budget), Map.of(), 128L << 20, 64L << 20, authority);
        Path releasePath = base.resolve("software-release.json"); Files.write(releasePath, mapper.writeValueAsBytes(release));
        var config = new ControlBuild.Config(source, work, releasePath, attempt, release.ownerTask(), null, Path.of(System.getProperty("java.home")),
                "3.10.0", 10, ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        return new Fixture(config, release, source, snapshot, build, work.resolve("logs/build-" + attempt + "-accounting.json"));
    }

    private static ControlBuild.BuildReceipt completed(Fixture fixture, ControlBuild.BuildReceipt terminal) throws Exception {
        Path deployment = fixture.build().resolve("ck3-control-build-tools");
        List<ControlBuild.FileRef> pins = new ArrayList<>(List.of(ControlBuild.FileRef.measure(deployment.resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar")),
                ControlBuild.FileRef.measure(deployment.resolve("lib/fixture.jar"))));
        pins.sort(java.util.Comparator.comparing(ControlBuild.FileRef::path));
        var match = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
        return new ControlBuild.BuildReceipt(ControlBuild.SCOPED_BUILD_SCHEMA, terminal.machineId(), Instant.now().toString(), "PASS",
                fixture.source().toString(), fixture.snapshot().toString(), deployment.toString(), match, match,
                ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.SourceLimitProfile.STANDARD_8_MIB,
                ControlBuild.sourceManifest(fixture.source()), ControlBuild.sourceManifest(fixture.snapshot()), pins, terminal.producerRuntimePins(),
                ControlBuild.FileRef.measure(fixture.config().capacityRelease()), terminal.mavenToolchain(), terminal.javaExecutableRef(), terminal.toolchainProbe(),
                terminal.mavenResult(), Map.of(), null, ControlBuild.FileRef.measure(fixture.accounting()));
    }
}

/** Executes the persistent targeted JUnit bodies without running the unrelated unchanged suite. */
final class AccountingMetadataRegressionMain {
    private AccountingMetadataRegressionMain() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IOException("One fresh absolute targeted-case root required");
        Path root = Path.of(arguments[0]);
        if (!root.isAbsolute() || !root.normalize().equals(root) || Files.exists(root))
            throw new IOException("Fresh canonical targeted-case root required");
        SharedSourceFiles.plainAncestors(root); Files.createDirectory(root);
        var accounting = new ControlBuildAccountingTest();
        accounting.temporary = Files.createDirectory(root.resolve("new-metadata"));
        accounting.realHeldMetadataRacesRetryOnlyMutableScopesAndKeepStrictFailures();
        accounting.temporary = Files.createDirectory(root.resolve("retained-disappearance"));
        accounting.mutableDescendantDisappearanceRestartsCompleteCensusWhileNonMissingAndImmutableFailuresRemainStrict();
        var nativeFiles = new SharedSourceFilesNativePathTest();
        nativeFiles.directory = Files.createDirectory(root.resolve("immutable-native"));
        nativeFiles.heldSnapshotsStillRejectRealFileAndDirectoryRacesWithTypedFacts();
        System.out.println("{\"schema\":\"xar.targeted-native-metadata-regressions/v1\",\"status\":\"PASS\",\"methods\":3,\"scope\":\"software_only_not_full_Maven_qualification\"}");
    }
}

/** Runs persistent real custody and shared-sampler regressions with actual native APIs. */
final class TemporaryCustodyMetadataRegressionMain {
    private TemporaryCustodyMetadataRegressionMain() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IOException("One fresh absolute targeted-case root required");
        Path root = Path.of(arguments[0]);
        if (!root.isAbsolute() || !root.normalize().equals(root) || Files.exists(root))
            throw new IOException("Fresh canonical targeted-case root required");
        SharedSourceFiles.plainAncestors(root); Files.createDirectory(root);
        var suite = new ControlBuildAccountingTest();
        suite.temporary = Files.createDirectory(root.resolve("live-custody"));
        suite.liveTemporaryCustodyRetriesMutableFactsAndKeepsIdentityAndFiniteFailuresStrict();
        suite.temporary = Files.createDirectory(root.resolve("original-custody"));
        suite.actualEntryCreatesOnlyItsMissingTemporaryChildAndRetainsOriginalCustody();
        suite.temporary = Files.createDirectory(root.resolve("shared-sampler"));
        suite.realHeldMetadataRacesRetryOnlyMutableScopesAndKeepStrictFailures();
        suite.temporary = Files.createDirectory(root.resolve("disappearance"));
        suite.mutableDescendantDisappearanceRestartsCompleteCensusWhileNonMissingAndImmutableFailuresRemainStrict();
        var nativeFiles = new SharedSourceFilesNativePathTest();
        nativeFiles.directory = Files.createDirectory(root.resolve("immutable-native"));
        nativeFiles.heldSnapshotsStillRejectRealFileAndDirectoryRacesWithTypedFacts();
        System.out.println("{\"schema\":\"xar.targeted-temporary-custody-metadata-regressions/v1\",\"status\":\"PASS\",\"methods\":5,\"scope\":\"software_only_not_full_Maven_qualification\"}");
    }
}

/** Executes the persistent native-entry-state regression plus the five retained sampler/custody methods. */
final class TemporaryEntryStateRegressionMain {
    private TemporaryEntryStateRegressionMain() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IOException("One fresh absolute targeted-case root required");
        Path root = Path.of(arguments[0]);
        if (!root.isAbsolute() || !root.normalize().equals(root) || Files.exists(root))
            throw new IOException("Fresh canonical targeted-case root required");
        SharedSourceFiles.plainAncestors(root); Files.createDirectory(root);
        var suite = new ControlBuildAccountingTest();
        suite.temporary = Files.createDirectory(root.resolve("entry-state"));
        suite.realHeldDeletePendingDescendantsRestartCompleteMutableCensusAndKeepOtherStatesStrict();
        var nativeFiles = new SharedSourceFilesNativePathTest();
        nativeFiles.directory = Files.createDirectory(root.resolve("strict-held-state"));
        nativeFiles.heldDeletePendingEntriesStayStrictAndCarryExactTypedFlags();
        TemporaryCustodyMetadataRegressionMain.main(new String[] {root.resolve("retained-five").toString()});
        System.out.println("{\"schema\":\"xar.targeted-native-entry-state-regressions/v1\",\"status\":\"PASS\",\"methods\":7,\"scope\":\"software_only_not_full_Maven_qualification\"}");
    }
}

/** Executes only the new pacing path, the actual failed compiler fixture, and retained seven native/custody methods. */
final class ScopedInventoryRetryRegressionMain {
    private ScopedInventoryRetryRegressionMain() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IOException("One fresh absolute targeted-case root required");
        Path root = Path.of(arguments[0]);
        if (!root.isAbsolute() || !root.normalize().equals(root) || Files.exists(root))
            throw new IOException("Fresh canonical targeted-case root required");
        SharedSourceFiles.plainAncestors(root); Files.createDirectory(root);
        var accounting = new ControlBuildAccountingTest();
        accounting.temporary = Files.createDirectory(root.resolve("paced-cleanup"));
        accounting.boundedCleanupWaveWaitsBetweenCompleteCensusesAndPreservesOriginalLimits();
        var profile = new FeatureSourceProfileR4Test();
        profile.temporary = Files.createDirectory(root.resolve("actual-full-accounting-fixture"));
        profile.actualFullAccountingPersistsAsTypedCompilerEvidenceAndKeepsItsTemporaryRoot();
        profile.temporary = Files.createDirectory(root.resolve("actual-private-temporary-consumer"));
        profile.missingAttemptTmpIsCreatedBeforeTheActualCompilerGuardAndStaysHeldThroughFailure();
        TemporaryEntryStateRegressionMain.main(new String[] {root.resolve("retained-seven").toString()});
        System.out.println("{\"schema\":\"xar.targeted-paced-inventory-and-source-fixture-regressions/v1\",\"status\":\"PASS\",\"methods\":10,\"scope\":\"software_only_not_full_Maven_qualification\"}");
    }
}

final class MutableSubtreeAccountingRegressionMain {
    private MutableSubtreeAccountingRegressionMain() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IOException("One fresh exact fixture root required");
        Path root = Path.of(arguments[0]);
        if (!root.isAbsolute() || !root.normalize().equals(root) || Files.exists(root)) throw new IOException("Fresh canonical fixture root required");
        SharedSourceFiles.plainAncestors(root); Files.createDirectory(root);
        var suite = new ControlBuildAccountingTest();
        suite.temporary = Files.createDirectory(root.resolve("sixteen-subtrees"));
        suite.confirmedMutableSubtreeAbsenceHandlesMoreThanEightRemovalsWithoutRestart();
        suite.temporary = Files.createDirectory(root.resolve("recreated-and-identity-rejections"));
        suite.recreatedMutableEntryResamplesAndAncestorRootOrKindReplacementRejects();
        suite.temporary = Files.createDirectory(root.resolve("typed-and-immutable"));
        suite.mutableDescendantDisappearanceRestartsCompleteCensusWhileNonMissingAndImmutableFailuresRemainStrict();
        suite.temporary = Files.createDirectory(root.resolve("recreated-wave"));
        suite.boundedCleanupWaveWaitsBetweenCompleteCensusesAndPreservesOriginalLimits();
        suite.temporary = Files.createDirectory(root.resolve("ordinary-scope-contract"));
        suite.actualAttemptGuardMeasuresOnlyItsScopesAndKeepsSharedRepositoryUnknown();
        suite.temporary = Files.createDirectory(root.resolve("root-admission"));
        suite.currentAttemptCannotUseMissingPrivateTemporaryRootOrForeignRoots();
        suite.temporary = Files.createDirectory(root.resolve("native-facts-rejections"));
        suite.realHeldMetadataRacesRetryOnlyMutableScopesAndKeepStrictFailures();
        suite.temporary = Files.createDirectory(root.resolve("delete-pending-rejections"));
        suite.realHeldDeletePendingDescendantsRestartCompleteMutableCensusAndKeepOtherStatesStrict();
        suite.temporary = Files.createDirectory(root.resolve("real-prepared-consumer"));
        suite.actualEntryCreatesOnlyItsMissingTemporaryChildAndRetainsOriginalCustody();
        System.out.println("{\"schema\":\"xar.targeted-confirmed-mutable-absence-regressions/v1\",\"status\":\"PASS\",\"methods\":9,\"scope\":\"software_only_not_full_Maven_qualification\"}");
    }
}


