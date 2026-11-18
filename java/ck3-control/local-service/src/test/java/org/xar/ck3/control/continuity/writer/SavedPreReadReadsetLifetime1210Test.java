package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Owned Windows DATA only. No Game, source issuer, SAVE, admission or adopted Driver is fabricated. */
final class SavedPreReadReadsetLifetime1210Test {
    private static final Instant NOW = Instant.parse("2026-11-18T00:00:00Z");
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(64, 8L << 20, 132);
    private static final byte[] RAW = "{\"owned_saved_data\":true}".getBytes(StandardCharsets.UTF_8);
    private static final TransitionAuthority NEVER = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState before, Request request) { throw new AssertionError("no preview"); }
        @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new AssertionError("no commit"); }
    };
    @TempDir Path temporary;
    @BeforeEach void actualWindows() { assertTrue(Platform.isWindows(), "real Windows HANDLE semantics are required"); }

    private static ObjectNode state() {
        var row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", "saved-readset1210-owned");
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0); row.putNull("latest_binding");
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static final class Fixture implements AutoCloseable {
        final Path root; final Layout layout; final ExactRef source; final StorageWriteGuardTestSupport storage;
        final ImmutableArtifactStore.Config config; final ContinuityWriter writer; final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException {
            this.root = root; Files.createDirectory(root); byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "actual reviewed owned-temp source", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), "saved-readset1210-owned");
            storage = StorageWriteGuardTestSupport.create(layout);
            config = new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8L << 20);
            var store = new ImmutableArtifactStore(config, storage);
            writer = new ContinuityWriter(layout, List.of(source), NEVER, Clock.fixed(NOW, ZoneOffset.UTC),
                    new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        ExactRef publish(byte[] raw) throws IOException { return writer.locked(same -> archive.preserveArtifact(same, raw, 1024)); }
        @Override public void close() throws IOException { storage.close(); }
    }
    private static final class Reader implements AutoCloseable {
        final StorageWriteGuard noWrites = StorageWriteGuard.noWrites();
        final ContinuityWriter writer; final NativeOutcomeArchive archive;
        Reader(Fixture original) throws IOException {
            var store = ImmutableArtifactStore.readOnlyExisting(original.config, noWrites);
            writer = ContinuityWriter.readOnlyExisting(original.layout, List.of(original.source), NEVER,
                    Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), noWrites);
            archive = new NativeOutcomeArchive(store, writer);
        }
        @Override public void close() throws IOException { noWrites.close(); }
    }
    private static final class MutableClock extends Clock {
        Instant now = NOW;
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException(); return this; }
        @Override public Instant instant() { return now; }
    }
    /** OPEN_EXISTING requests access but writes/deletes/renames nothing. */
    private static void qualifyOpen(Path file, int access, boolean allowed) throws IOException {
        HANDLE handle = Kernel32.INSTANCE.CreateFile(file.toAbsolutePath().toString(), access, 7, null, 3, 0x80, null);
        int error = Kernel32.INSTANCE.GetLastError();
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            if (allowed) throw new IOException("owned access qualification failed: " + error + " " + file);
            assertEquals(32, error, "actual custody must deny sharing rather than a missing path or ACL"); return;
        }
        try { assertTrue(allowed, "forbidden current native access succeeded: " + file); }
        finally { if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("owned test HANDLE close failed"); }
    }
    private static void held(Path file, boolean expected) throws IOException {
        qualifyOpen(file, 0x40000000, !expected); // GENERIC_WRITE
        qualifyOpen(file, 0x00010000, !expected); // DELETE is also required for rename
    }
    private static Path commit(ExactRef ref) { return Path.of(ref.path()).resolveSibling(ref.sha256() + ".commit.json"); }
    private static byte[] sourceOriginal(NativeOutcomeArchive archive, ExactRef ref) throws IOException {
        try {
            var method = NativeOutcomeArchive.class.getDeclaredMethod("verifyRetainedSourceOriginal", ExactRef.class);
            method.setAccessible(true); return (byte[]) method.invoke(archive, ref);
        } catch (java.lang.reflect.InvocationTargetException problem) {
            if (problem.getCause() instanceof IOException io) throw io;
            if (problem.getCause() instanceof RuntimeException runtime) throw runtime;
            if (problem.getCause() instanceof Error error) throw error;
            throw new AssertionError("unexpected checked source reader failure", problem.getCause());
        } catch (ReflectiveOperationException problem) { throw new AssertionError("actual source-reader boundary missing", problem); }
    }
    private static <T> NativeOutcomeArchive.SavedPreReadReadSet<T> seal(Fixture caller, Reader old,
            Clock clock, ActionPorts.CheckedArchiveRead<T> proof) throws IOException {
        return caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame,
                sourceSame -> old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, clock, NOW.plusSeconds(60), proof)));
    }
    private static void verify(Fixture caller, Reader old, NativeOutcomeArchive.SavedPreReadReadSet<?> sealed) throws IOException {
        caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame -> {
            sealed.requireCurrent(old.archive, sourceSame); return null;
        }));
    }

    @Test void actualCommitPayloadHeadAndSourceHandlesSurviveNewSourceSessionsUntilClose() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var ref = original.publish(RAW); var clock = new MutableClock(); var proofs = new AtomicInteger();
            var firstSession = new AtomicReference<ContinuityStorePort.Session>();
            try (var sealed = caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame -> {
                firstSession.set(sourceSame);
                return old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, clock, NOW.plusSeconds(60), bound -> {
                    proofs.incrementAndGet(); assertArrayEquals(RAW, old.archive.readArtifact(sourceSame, ref, 1024)); return "archived DATA";
                });
            }))) {
                assertEquals("archived DATA", sealed.value());
                held(Path.of(ref.path()), true); held(commit(ref), true); held(original.layout.snapshot(), true);
                held(original.root.resolve("anchor.json"), true); held(Path.of(original.source.path()), true);
                caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame -> {
                    assertNotSame(firstSession.get(), sourceSame); sealed.requireCurrent(old.archive, sourceSame); return null;
                }));
                verify(caller, old, sealed); assertEquals(1, proofs.get(), "post-READ qualification must not replay history");
            }
            held(Path.of(ref.path()), false); held(commit(ref), false); held(original.layout.snapshot(), false); held(Path.of(original.source.path()), false);
        }
    }
    @Test void referenceOfAloneStillCapturesBothActualPublicationHandles() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var ref = original.publish(RAW);
            try (var sealed = seal(caller, old, new MutableClock(), bound -> old.archive.artifactStore().referenceOf(ref.sha256(), ref.bytes(), 1024))) {
                assertEquals(ref, sealed.value().reference()); held(Path.of(ref.path()), true); held(commit(ref), true); verify(caller, old, sealed);
            }
            held(Path.of(ref.path()), false); held(commit(ref), false);
        }
    }
    @Test void actualExternalSourceProofOutsideTheInstalledSourceLaneAlsoRetainsItsHandle() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            Path proof = original.root.resolve("separate-source-proof.json"); Files.write(proof, RAW, StandardOpenOption.CREATE_NEW);
            ExactRef ref = LedgerFiles.read(proof, 1024).pin().reference();
            try (var sealed = seal(caller, old, new MutableClock(), bound -> sourceOriginal(old.archive, ref))) {
                assertArrayEquals(RAW, sealed.value()); held(proof, true); verify(caller, old, sealed);
            }
            held(proof, false);
        }
    }
    @Test void wrongArchiveIssuerPermanentlyInvalidatesTheSealedReadset() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            try (var sealed = seal(caller, old, new MutableClock(), bound -> "DATA")) {
                assertThrows(IOException.class, () -> caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame -> {
                    sealed.requireCurrent(original.archive, sourceSame); return null;
                })));
                assertThrows(IOException.class, () -> verify(caller, old, sealed));
            }
            held(original.layout.snapshot(), false);
        }
    }
    @Test void expiryFailureCannotBeResurrectedByMovingTheClockBack() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var clock = new MutableClock();
            try (var sealed = seal(caller, old, clock, bound -> "DATA")) {
                clock.now = NOW.plusSeconds(60); assertThrows(IOException.class, () -> verify(caller, old, sealed));
                clock.now = NOW; assertThrows(IOException.class, () -> verify(caller, old, sealed));
            }
        }
    }
    @Test void aNewPreviouslyAbsentCanonicalPathRejectsTheOldCut() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var absent = new AtomicReference<Path>();
            try (var sealed = caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame ->
                    old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, new MutableClock(), NOW.plusSeconds(60), bound -> {
                        absent.set(sourceSame.head().absent().stream().filter(path -> Files.isDirectory(path.getParent())).findFirst().orElseThrow()); return "DATA";
                    })))) {
                Files.writeString(absent.get(), "unexpected owned-temp path", StandardOpenOption.CREATE_NEW);
                assertThrows(IOException.class, () -> verify(caller, old, sealed));
            }
        }
    }
    @Test void foreignThreadCloseInvalidatesButOwnerFinallyStillReleasesEveryHandle() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var sealed = seal(caller, old, new MutableClock(), bound -> "DATA");
            try {
                CompletableFuture.runAsync(() -> assertThrows(IOException.class, sealed::close)).get(5, TimeUnit.SECONDS);
                held(original.layout.snapshot(), true); assertThrows(IOException.class, () -> verify(caller, old, sealed));
            } finally { sealed.close(); }
            held(original.layout.snapshot(), false);
        }
    }
    @Test void eachBudgetFailureIsTypedAndReleasesPartialCanonicalCustody() throws Exception {
        var limits = List.of(new ActionPorts.HistoricalReadLimits(1, 8L << 20, 132),
                new ActionPorts.HistoricalReadLimits(64, 1, 132), new ActionPorts.HistoricalReadLimits(64, 8L << 20, 4));
        var reasons = List.of(ImmutableArtifactStore.SavedReadsetFailure.ENTRY_BOUND,
                ImmutableArtifactStore.SavedReadsetFailure.BYTE_BOUND, ImmutableArtifactStore.SavedReadsetFailure.HANDLE_BOUND);
        for (int index = 0; index < limits.size(); index++) {
            final var selected = limits.get(index);
            try (var original = new Fixture(temporary.resolve("source" + index)); var caller = new Fixture(temporary.resolve("caller" + index)); var old = new Reader(original)) {
                var ref = original.publish(RAW);
                var failure = assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class, () ->
                        caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame ->
                            old.archive.sealSavedPreReadHistory(sourceSame, selected, new MutableClock(), NOW.plusSeconds(60),
                                bound -> old.archive.artifactStore().referenceOf(ref.sha256(), ref.bytes(), 1024)))));
                assertEquals(reasons.get(index), failure.reason()); held(original.layout.snapshot(), false); held(original.root.resolve("anchor.json"), false);
                try (var next = seal(caller, old, new MutableClock(), bound -> "fresh DATA")) { verify(caller, old, next); }
            }
        }
    }
    @Test void caughtHistoricalFailureStillRejectsAndClosesAnAlreadyProducedCandidate() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var missing = new ExactRef(original.root.resolve("artifacts").resolve("0".repeat(64) + ".bin").toString(), 1, "0".repeat(64));
            assertThrows(IOException.class, () -> caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame ->
                    old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, new MutableClock(), NOW.plusSeconds(60), bound -> {
                        assertThrows(IOException.class, () -> old.archive.readArtifact(sourceSame, missing, 1024)); return "must not escape";
                    }))));
            held(original.layout.snapshot(), false); held(Path.of(original.source.path()), false);
            try (var next = seal(caller, old, new MutableClock(), bound -> "next DATA")) { verify(caller, old, next); }
        }
    }
    @Test void caughtTransientSourceAcquisitionFailureCannotAdmitAnEmptyReadset() throws Exception {
        try (var original = new Fixture(temporary.resolve("source"))) {
            var missing = new ExactRef(original.root.resolve("missing.bin").toString(), 1, "0".repeat(64));
            assertThrows(IOException.class, () -> original.writer.locked(same -> original.archive.inHistoricalReadScope(same, LIMITS, bound -> {
                try (var custody = original.archive.openTransientOwnedCASLeaseScope(bound, same)) {
                    assertThrows(IOException.class, () -> custody.retainQualifiedSource(missing, 1024));
                    assertThrows(IOException.class, custody::requirePreparedCustody);
                }
                return "caught errors cannot grant success";
            })));
        }
    }
    @Test void abandonedAdmittedTransientScopeFailsAndDoesNotStrandTheOwnersNextScope() throws Exception {
        try (var original = new Fixture(temporary.resolve("source"))) {
            assertThrows(IOException.class, () -> original.writer.locked(same -> original.archive.inHistoricalReadScope(same, LIMITS, bound -> {
                var custody = original.archive.openTransientOwnedCASLeaseScope(bound, same);
                custody.retainQualifiedSource(original.source, 1024); custody.requirePreparedCustody(); return "unclosed admitted custody";
            })));
            held(Path.of(original.source.path()), false);
            original.writer.locked(same -> original.archive.inHistoricalReadScope(same, LIMITS, bound -> {
                try (var custody = original.archive.openTransientOwnedCASLeaseScope(bound, same)) {
                    custody.retainQualifiedSource(original.source, 1024); custody.requirePreparedCustody(); custody.verifyAndClose();
                }
                return null;
            }));
        }
    }
    private static Object savedField(Object holder, String name) throws ReflectiveOperationException {
        var field = holder.getClass().getDeclaredField(name); field.setAccessible(true); return field.get(holder);
    }
    /** Controlled owned-temp failure: the original HANDLE stays open and cannot be recycled. */
    private static final class SavedCloseFault implements AutoCloseable {
        private HANDLE actual;
        private SavedCloseFault(Object ledgerDocument) throws ReflectiveOperationException {
            var lease = (org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.ReadOnlyLease) savedField(ledgerDocument, "lease");
            var field = lease.getClass().getDeclaredField("handle"); field.setAccessible(true);
            actual = (HANDLE) field.get(lease); assertNotNull(actual); assertFalse(WinBase.INVALID_HANDLE_VALUE.equals(actual));
            field.set(lease, new HANDLE(com.sun.jna.Pointer.NULL));
        }
        @Override public void close() throws IOException {
            HANDLE original = actual; actual = null;
            if (original != null && !Kernel32.INSTANCE.CloseHandle(original)) throw new IOException("owned original HANDLE cleanup failed");
        }
    }
    @Test void actualExternalCloseFailureRemainsUnknownOnEveryLaterClose() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var sealed = seal(caller, old, new MutableClock(), bound -> "DATA");
            Object capture = savedField(sealed, "originals");
            var entries = (java.util.Map<?, ?>) savedField(capture, "external");
            Object entry = entries.values().iterator().next();
            Pin expected = (Pin) savedField(entry, "expected");
            try (var fault = new SavedCloseFault(savedField(entry, "lease"))) {
                assertNotNull(fault.actual);
                IOException first = assertThrows(IOException.class, sealed::close);
                held(Path.of(expected.reference().path()), true);
                IOException repeated = assertThrows(IOException.class, sealed::close);
                assertSame(first, repeated.getCause(), "an API retry cannot prove a previously failed native release");
                assertThrows(IOException.class, () -> verify(caller, old, sealed));
            } finally { assertThrows(IOException.class, sealed::close); }
            held(Path.of(expected.reference().path()), false);
        }
    }
    @Test void actualCommitCloseFailureRemainsUnknownInBothArchiveAndCasHolders() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(original)) {
            var ref = original.publish(RAW);
            var sealed = seal(caller, old, new MutableClock(), bound -> old.archive.artifactStore().referenceOf(ref.sha256(), ref.bytes(), 1024));
            Object capture = savedField(sealed, "originals");
            var cas = (ImmutableArtifactStore.SavedReadsetCapture) savedField(capture, "cas");
            var heldPairs = (java.util.Map<?, ?>) savedField(cas, "held");
            Object pair = heldPairs.values().iterator().next();
            try (var fault = new SavedCloseFault(savedField(pair, "metadata"))) {
                assertNotNull(fault.actual);
                IOException first = assertThrows(IOException.class, sealed::close);
                held(commit(ref), true); held(Path.of(ref.path()), false);
                IOException repeatedCas = assertThrows(IOException.class, cas::close);
                assertSame(first, repeatedCas.getCause());
                assertSame(first, assertThrows(IOException.class, sealed::close).getCause());
            } finally { assertThrows(IOException.class, sealed::close); }
            held(commit(ref), false);
        }
    }
    @Test void samePhysicalLockPathDoesNotPermitAForeignSourceWriterSession() throws Exception {
        try (var original = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller"));
                var old = new Reader(original); var foreign = new Reader(original)) {
            assertEquals(old.writer.originalLockPath(), foreign.writer.originalLockPath());
            try (var sealed = seal(caller, old, new MutableClock(), bound -> "DATA")) {
                assertThrows(IOException.class, () -> caller.writer.locked(newSame -> foreign.writer.readOnlyFrom(newSame, foreignSame -> {
                    sealed.requireCurrent(old.archive, foreignSame); return null;
                })));
                assertThrows(IOException.class, () -> verify(caller, old, sealed), "correct later Session cannot resurrect the failed issuer check");
            }
            held(original.layout.snapshot(), false);
        }
    }
    @Test void unsigned64BitFileIdDifferenceCannotCollapseIntoAnAdmittedSourcePin() throws Exception {
        try (var original = new Fixture(temporary.resolve("source"))) {
            assertThrows(IOException.class, () -> original.writer.locked(same -> original.archive.inHistoricalReadScope(same, LIMITS, bound -> {
                Pin actual = same.capturePin(original.source, 1024);
                String highFileId = "18446744073709551615";
                if (highFileId.equals(actual.identity().fileIdDecimal())) highFileId = "18446744073709551614";
                var identity = actual.identity();
                var forged = new Pin(actual.reference(), new FileIdentity(identity.volumeSerialDecimal(), highFileId,
                        identity.creationFiletimeDecimal(), identity.modifiedInstant(), identity.bytes()));
                try (var custody = original.archive.openTransientOwnedCASLeaseScope(bound, same)) {
                    assertThrows(IOException.class, () -> custody.retainQualifiedSource(forged, 1024));
                    assertThrows(IOException.class, custody::requirePreparedCustody);
                }
                return "caught mismatch cannot become actual physical custody";
            })));
            held(Path.of(original.source.path()), false);
        }
    }


}
