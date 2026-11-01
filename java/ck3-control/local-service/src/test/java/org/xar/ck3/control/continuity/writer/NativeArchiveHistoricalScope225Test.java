package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.ArtifactRole;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.OriginalArtifact;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome;
import org.xar.ck3.control.contracts.presentation.PresentationObservation;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;

/** Real owned Windows archive/store integration, implementation-aware. No Game, issuer, full graph or speed claim. */
final class NativeArchiveHistoricalScope225Test {
    private static final String MACHINE = "historical-scope-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final java.util.Set<StorageWriteGuardTestSupport> scopes = new java.util.LinkedHashSet<>();

    @AfterEach void closeScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : scopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        scopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException {
            this.root = root;
            Files.createDirectory(root);
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "actual reviewed fixture source", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = StorageWriteGuardTestSupport.create(layout);
            scopes.add(storage);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("archive fixture must not commit"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
            row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
            row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
        }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }


    /** Leaves inHistoricalReadScope inherited from the actual interface default. */
    private static final class DefaultArchive implements ActionPorts.OutcomeArchive {
        private final ActionPorts.OutcomeArchive delegate;
        DefaultArchive(ActionPorts.OutcomeArchive delegate) { this.delegate = delegate; }
            @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { return delegate.preserve(original); }
            @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { return delegate.load(original); }
            @Override public ExactRef preserveRequest(NativeRequest original) { return delegate.preserveRequest(original); }
            @Override public NativeRequest loadRequest(ExactRef original) { return delegate.loadRequest(original); }
            @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { return delegate.referenceOf(original); }
            @Override public ExactRef requestReferenceOf(NativeRequest original) { return delegate.requestReferenceOf(original); }
            @Override public ExactRef preserveRead(PlanningReadReceipt original) { return delegate.preserveRead(original); }
            @Override public PlanningReadReceipt loadRead(ExactRef original) { return delegate.loadRead(original); }
            @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { return delegate.readReferenceOf(original); }
            @Override public ExactRef preserveRecord(ActionRecord original) { return delegate.preserveRecord(original); }
            @Override public ActionRecord loadRecord(ExactRef original) { return delegate.loadRecord(original); }
            @Override public ExactRef recordReferenceOf(ActionRecord original) { return delegate.recordReferenceOf(original); }
            @Override public ExactRef preserveReceipt(ActionReceipt original) { return delegate.preserveReceipt(original); }
            @Override public ActionReceipt loadReceipt(ExactRef original) { return delegate.loadReceipt(original); }
            @Override public ExactRef receiptReferenceOf(ActionReceipt original) { return delegate.receiptReferenceOf(original); }
            @Override public ExactRef preserveMaterial(RawJson original) { return delegate.preserveMaterial(original); }
            @Override public RawJson loadMaterial(ExactRef original) { return delegate.loadMaterial(original); }
            @Override public ExactRef materialReferenceOf(RawJson original) { return delegate.materialReferenceOf(original); }
            @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { return delegate.preserveNativeFrame(original); }
            @Override public byte[] loadNativeFrame(ExactRef original) { return delegate.loadNativeFrame(original); }
            @Override public ExactRef preservePresentationArtifact(OriginalArtifact original) { return delegate.preservePresentationArtifact(original); }
            @Override public OriginalArtifact loadPresentationArtifact(ArtifactRole role, ExactRef original) { return delegate.loadPresentationArtifact(role, original); }
            @Override public ExactRef presentationArtifactReferenceOf(OriginalArtifact original) { return delegate.presentationArtifactReferenceOf(original); }
            @Override public ExactRef preservePresentationOutcome(OriginalOutcome original) { return delegate.preservePresentationOutcome(original); }
            @Override public OriginalOutcome loadPresentationOutcome(ExactRef original) { return delegate.loadPresentationOutcome(original); }
            @Override public ExactRef presentationOutcomeReferenceOf(OriginalOutcome original) { return delegate.presentationOutcomeReferenceOf(original); }
            @Override public ExactRef preservePresentationObservation(PresentationObservation original) { return delegate.preservePresentationObservation(original); }
            @Override public PresentationObservation loadPresentationObservation(ExactRef original) { return delegate.loadPresentationObservation(original); }
            @Override public ExactRef presentationObservationReferenceOf(PresentationObservation original) { return delegate.presentationObservationReferenceOf(original); }
            @Override public ExactRef preserveFrontendWindowCaptureRequest(FrontendWindowCaptureRequest original) { return delegate.preserveFrontendWindowCaptureRequest(original); }
            @Override public FrontendWindowCaptureRequest loadFrontendWindowCaptureRequest(ExactRef original) { return delegate.loadFrontendWindowCaptureRequest(original); }
            @Override public ExactRef frontendWindowCaptureRequestReferenceOf(FrontendWindowCaptureRequest original) { return delegate.frontendWindowCaptureRequestReferenceOf(original); }
            @Override public ExactRef preserveFrontendWindowCaptureOutcome(FrontendWindowCaptureOutcome original) { return delegate.preserveFrontendWindowCaptureOutcome(original); }
            @Override public FrontendWindowCaptureOutcome loadFrontendWindowCaptureOutcome(ExactRef original) { return delegate.loadFrontendWindowCaptureOutcome(original); }
            @Override public ExactRef frontendWindowCaptureOutcomeReferenceOf(FrontendWindowCaptureOutcome original) { return delegate.frontendWindowCaptureOutcomeReferenceOf(original); }
    }

    private static final ActionPorts.HistoricalReadLimits NORMAL_LIMITS =
            new ActionPorts.HistoricalReadLimits(8, 1024 * 1024, 20);

    private static Path payload(ExactRef ref) { return Path.of(ref.path()); }
    private static Path commit(ExactRef ref) { return payload(ref).resolveSibling(ref.sha256() + ".commit.json"); }
    private static java.util.Set<String> inventory(Path root) throws IOException {
        try (var entries = Files.list(root)) {
            return entries.map(p -> p.getFileName().toString()).collect(java.util.stream.Collectors.toUnmodifiableSet());
        }
    }
    private static void unchanged(Fixture f, byte[] snapshot, java.util.Set<String> entries) throws IOException {
        assertArrayEquals(snapshot, Files.readAllBytes(f.layout.snapshot()));
        assertEquals(entries, inventory(f.root.resolve("artifacts")));
    }
    private static ExactRef publish(Fixture f, byte[] value) throws IOException {
        return f.writer.locked(session -> f.archive.inSession(session,
                bound -> bound.preserveMaterial(new RawJson(value))));
    }

    /** Only qualification: GENERIC_WRITE/OPEN_EXISTING never writes a byte. Every actual successful handle closes. */
    private static void writeQualification(Path path, boolean allowed) throws IOException {
        HANDLE handle = Kernel32.INSTANCE.CreateFile(path.toAbsolutePath().toString(), 0x40000000,
                1 | 2 | 4, null, 3, 0x80, null);
        int error = Kernel32.INSTANCE.GetLastError();
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            if (allowed) throw new IOException("owned write qualification unexpectedly failed, Win32=" + error + ": " + path);
            assertEquals(32, error, "custody must specifically deny sharing, not a missing/inaccessible target");
            return;
        }
        boolean closed = Kernel32.INSTANCE.CloseHandle(handle);
        int closeError = Kernel32.INSTANCE.GetLastError();
        if (!closed) throw new IOException("owned qualification CloseHandle failed, Win32=" + closeError);
        assertTrue(allowed, "write qualification unexpectedly succeeded while custody should be held: " + path);
    }
    private static void pairQualification(ExactRef ref, boolean allowed) throws IOException {
        writeQualification(commit(ref), allowed);
        writeQualification(payload(ref), allowed);
    }
    private static byte[] externalOriginal(NativeOutcomeArchive archive, ExactRef ref) throws IOException {
        try {
            var method = NativeOutcomeArchive.class.getDeclaredMethod("verifyRetainedSourceOriginal", ExactRef.class);
            method.setAccessible(true);
            return (byte[]) method.invoke(archive, ref);
        } catch (java.lang.reflect.InvocationTargetException problem) {
            Throwable cause = problem.getCause();
            if (cause instanceof IOException failure) throw failure;
            if (cause instanceof RuntimeException failure) throw failure;
            if (cause instanceof Error failure) throw failure;
            throw new AssertionError("unexpected checked target cause", cause);
        } catch (ReflectiveOperationException infrastructure) {
            throw new AssertionError("external-source witness reflection failed", infrastructure);
        }
    }

    @Test void normalScopeRetainsCompletePairAndReleasesIt() throws IOException {
        Fixture f = fixture("normal");
        byte[] input = bytes("{\"retained\":true}");
        ExactRef ref = publish(f, input);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        f.writer.locked(session -> {
            byte[] result = f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> {
                assertSame(f.store, ((NativeOutcomeArchive) bound).artifactStore());
                LedgerFiles.Document document = f.store.readOriginal(ref, input.length);
                assertEquals(ref, document.pin().reference());
                assertArrayEquals(input, document.bytes());
                byte[] actual = bound.loadMaterial(ref).bytes();
                assertArrayEquals(input, actual);
                actual[0] ^= 1;
                assertFalse(java.util.Arrays.equals(input, actual));
                assertArrayEquals(input, bound.loadMaterial(ref).bytes());
                pairQualification(ref, false);
                return bound.loadMaterial(ref).bytes();
            });
            assertArrayEquals(input, result);
            pairQualification(ref, true);
            return null;
        });
        assertArrayEquals(input, Files.readAllBytes(payload(ref)));
        unchanged(f, snapshot, entries);
    }

    @Test void actualDefaultUsesFullReadersWithoutRetainedCustody() throws IOException {
        Fixture f = fixture("default");
        byte[] input = bytes("{\"default\":true}");
        ExactRef ref = publish(f, input);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        f.writer.locked(session -> {
            ActionPorts.OutcomeArchive adapter = new DefaultArchive(f.archive.withSession(session));
            byte[] actual = adapter.inHistoricalReadScope(session,
                    new ActionPorts.HistoricalReadLimits(1, 1, 4), bound -> {
                        assertSame(adapter, bound);
                        byte[] result = bound.loadMaterial(ref).bytes();
                        assertArrayEquals(input, result);
                        pairQualification(ref, true);
                        return result;
                    });
            assertArrayEquals(input, actual);
            IOException marker = new IOException("owned default checked callback225");
            assertSame(marker, assertThrows(IOException.class, () -> adapter.inHistoricalReadScope(
                    session, NORMAL_LIMITS, bound -> { throw marker; })));
            byte[] changed = input.clone(); changed[0] ^= 1;
            Files.write(payload(ref), changed, StandardOpenOption.TRUNCATE_EXISTING);
            UncheckedIOException refused = assertThrows(UncheckedIOException.class,
                    () -> adapter.inHistoricalReadScope(session, NORMAL_LIMITS,
                            bound -> bound.loadMaterial(ref)));
            assertNotNull(refused.getCause());
            assertArrayEquals(changed, Files.readAllBytes(payload(ref)));
            pairQualification(ref, true);
            return null;
        });
        unchanged(f, snapshot, entries);
    }

    @Test void caughtTrackedFailuresCannotGrantSuccessAndCheckedCallbackReleasesPairs() throws IOException {
        Fixture f = fixture("poison");
        byte[] input = bytes("{\"poison\":false}");
        ExactRef ref = publish(f, input);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        f.writer.locked(session -> {
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> {
                assertArrayEquals(input, f.store.read(ref, input.length));
                pairQualification(ref, false);
                assertThrows(IOException.class, () -> f.store.read(ref, input.length - 1));
                return "caught cap failure must not escape as success";
            }));
            pairQualification(ref, true);
            ExactRef missing = new ExactRef(f.root.resolve("artifacts").resolve("0".repeat(64) + ".bin").toString(),
                    input.length, "0".repeat(64));
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> {
                IOException refused = assertThrows(IOException.class, () -> f.store.read(missing, input.length));
                assertFalse(refused instanceof java.nio.file.NoSuchFileException,
                        "immutable validation absence is not optional absence");
                return "caught missing commit must not grant success";
            }));
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> {
                assertThrows(IOException.class, () -> bound.inHistoricalReadScope(session, NORMAL_LIMITS, inner -> null));
                return "caught nested scope must not grant success";
            }));
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> {
                assertThrows(IOException.class, () -> f.store.publish(bytes("{\"forbidden\":1}"), 1024));
                return "caught write refusal must not grant success";
            }));
            IOException marker = new IOException("owned checked callback225");
            IOException escaped = assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(
                    session, NORMAL_LIMITS, bound -> {
                        assertArrayEquals(input, bound.loadMaterial(ref).bytes());
                        pairQualification(ref, false);
                        throw marker;
                    }));
            assertSame(marker, escaped);
            pairQualification(ref, true);
            assertArrayEquals(input, f.archive.inHistoricalReadScope(session, NORMAL_LIMITS,
                    bound -> bound.loadMaterial(ref).bytes()));
            pairQualification(ref, true);
            return null;
        });
        unchanged(f, snapshot, entries);
    }

    @Test void oneScopeLimitFallsBackToFullReadForSecondPairAndReleasesEverything() throws IOException {
        Fixture f = fixture("limit");
        byte[] first = bytes("{\"first\":true}");
        byte[] second = bytes("{\"second\":true}");
        ExactRef a = publish(f, first), b = publish(f, second);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        f.writer.locked(session -> {
            f.archive.inHistoricalReadScope(session, new ActionPorts.HistoricalReadLimits(1, 1024 * 1024, 4), bound -> {
                assertArrayEquals(first, bound.loadMaterial(a).bytes());
                assertArrayEquals(second, bound.loadMaterial(b).bytes());
                assertArrayEquals(first, bound.loadMaterial(a).bytes());
                pairQualification(a, false);
                pairQualification(b, true);
                return null;
            });
            pairQualification(a, true);
            pairQualification(b, true);
            return null;
        });
        unchanged(f, snapshot, entries);
    }

    @Test void realSessionQualificationAndExternalSourceStayFreshInsideCasScope() throws IOException {
        Fixture f = fixture("qualification");
        byte[] input = bytes("{\"scope\":true}");
        ExactRef ref = publish(f, input);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        AtomicReference<ContinuityStorePort.Session> escaped = new AtomicReference<>();
        f.writer.locked(session -> {
            escaped.set(session);
            CompletionException crossed = assertThrows(CompletionException.class, () -> CompletableFuture.runAsync(() -> {
                try { f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> bound.loadMaterial(ref)); }
                catch (IOException problem) { throw new UncheckedIOException(problem); }
            }).orTimeout(10, TimeUnit.SECONDS).join());
            assertInstanceOf(IllegalArgumentException.class, crossed.getCause());
            return null;
        });
        assertThrows(IllegalArgumentException.class,
                () -> f.archive.inHistoricalReadScope(escaped.get(), NORMAL_LIMITS, bound -> null));
        Fixture foreign = fixture("foreign");
        foreign.writer.locked(session -> {
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, NORMAL_LIMITS, bound -> null));
            return null;
        });
        Path external = f.root.resolve("external-source.bin");
        byte[] source = new byte[] {0, 1, 127, (byte) 128, (byte) 255, 65, 10};
        Files.write(external, source, StandardOpenOption.CREATE_NEW);
        ExactRef externalRef = new ExactRef(external.toString(), source.length, LedgerFiles.sha(source));
        byte[] changed = source.clone(); changed[0] ^= 1;
        assertThrows(IOException.class, () -> f.writer.locked(session -> f.archive.inHistoricalReadScope(
                session, NORMAL_LIMITS, bound -> {
                    assertArrayEquals(input, bound.loadMaterial(ref).bytes());
                    pairQualification(ref, false);
                    assertArrayEquals(source, externalOriginal((NativeOutcomeArchive) bound, externalRef));
                    Files.write(external, changed, StandardOpenOption.TRUNCATE_EXISTING);
                    // Let this actual external failure escape: no claim that an arbitrary caught private call is tracked.
                    return externalOriginal((NativeOutcomeArchive) bound, externalRef);
                })));
        pairQualification(ref, true);
        assertArrayEquals(changed, Files.readAllBytes(external));
        unchanged(f, snapshot, entries);
    }
}
