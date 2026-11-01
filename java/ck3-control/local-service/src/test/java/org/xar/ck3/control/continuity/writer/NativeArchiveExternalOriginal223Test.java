package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real Windows physical archive and writer fixtures. No Game, native submission or production ledger. */
final class NativeArchiveExternalOriginal223Test {
    private static final String MACHINE = "archive-external-223";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final Set<StorageWriteGuardTestSupport> storageScopes = new java.util.LinkedHashSet<>();

    @AfterEach void closeStorageScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : storageScopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root, boolean reopen) throws IOException {
            this.root = root;
            if (!reopen) {
                Files.createDirectory(root);
                byte[] initial = ContinuityJson.canonical(state());
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
                Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
                Files.createDirectory(root.resolve("artifacts"));
                Files.writeString(root.resolve("source.txt"), "actual reviewed fixture source", StandardOpenOption.CREATE_NEW);
            }
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = reopen ? StorageWriteGuardTestSupport.forLayout(layout) : StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            assertSame(storage, store.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("archive fixture must not commit"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object();
            row.put("schema", "root.ck3.continuity-window/v1");
            row.put("machine_id", MACHINE);
            row.put("sequence", 0);
            row.put("window_id", 1);
            row.put("status", "running");
            row.put("target_days", 10958);
            row.put("target_years", 30);
            row.put("calendar_year_days", 365.25);
            row.put("start_date_raw", 1000);
            row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000);
            row.put("last_settled_cycles", 1);
            row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0);
            row.put("binding_lineage_count", 0);
            row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z");
            row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558);
            row.put("NEXT", 11559);
            return row;
        }
    }

    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name), false); }

    private static long leaves(Path root) throws IOException { try (var values = Files.list(root)) { return values.count(); } }

    private static Method getVerifyRetainedSourceOriginal() throws NoSuchMethodException {
        Method method = NativeOutcomeArchive.class.getDeclaredMethod("verifyRetainedSourceOriginal", ExactRef.class);
        method.setAccessible(true);
        return method;
    }

    private static byte[] invokeVerifyRetainedSourceOriginal(NativeOutcomeArchive archive, ExactRef ref) throws IOException {
        try {
            Method method = getVerifyRetainedSourceOriginal();
            return (byte[]) method.invoke(archive, ref);
        } catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof IOException) throw (IOException) cause;
            if (cause instanceof RuntimeException) throw (RuntimeException) cause;
            if (cause instanceof Error) throw (Error) cause;
            throw new AssertionError("unexpected target checked exception", cause);
        } catch (ReflectiveOperationException infrastructure) {
            throw new AssertionError("test reflection setup/invoke failed", infrastructure);
        }
    }

    @Test void knownNonemptyExternalFileOutsideCasRootButInsideOwnedFixture() throws IOException {
        Fixture f = fixture("external-known");
        Path external = f.root.resolve("external-known.txt");
        byte[] content = new byte[] {0, 1, 127, (byte)128, (byte)255, 65, 66, 67, 10};
        Files.write(external, content, StandardOpenOption.CREATE_NEW);
        ExactRef ref = new ExactRef(external.toString(), content.length, LedgerFiles.sha(content));

        long casLeavesBefore = leaves(f.store.identity().root());
        byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot());

        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            byte[] result = invokeVerifyRetainedSourceOriginal(bound, ref);
            assertArrayEquals(content, result);
            // Mutate the returned array; it must be detached.
            result[0] ^= 1;
            assertFalse(java.util.Arrays.equals(content, result));
            assertArrayEquals(content, Files.readAllBytes(external));
            byte[] second = invokeVerifyRetainedSourceOriginal(bound, ref);
            assertArrayEquals(content, second);
            return null;
        });

        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot()));
        assertEquals(casLeavesBefore, leaves(f.store.identity().root()));
    }

    @Test void missingCorruptZeroLengthAndOversizedRefsRejectWithoutRepair() throws IOException {
        Fixture f = fixture("external-reject");
        byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot());
        long casLeavesBefore = leaves(f.root.resolve("artifacts"));
        Path external = f.root.resolve("external-reject.txt");
        byte[] content = new byte[] {0, 1, 127, (byte)128, (byte)255, 65, 66, 67, 10};
        Files.write(external, content, StandardOpenOption.CREATE_NEW);

        // Missing file
        ExactRef missing = new ExactRef(f.root.resolve("missing.txt").toString(), 10, "0".repeat(64));
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(bound, missing));
            return null;
        });

        // Corrupt/wrong SHA
        ExactRef corrupt = new ExactRef(external.toString(), content.length, "0".repeat(64));
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(bound, corrupt));
            return null;
        });

        // Zero length ref
        ExactRef zero = new ExactRef(external.toString(), 0, LedgerFiles.sha(new byte[0]));
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(bound, zero));
            return null;
        });

        // Oversized ref
        ExactRef oversized = new ExactRef(external.toString(), MAX_PIN_BYTES + 1, LedgerFiles.sha(content));
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(bound, oversized));
            return null;
        });

        assertArrayEquals(content, Files.readAllBytes(external));
        ExactRef good = new ExactRef(external.toString(), content.length, LedgerFiles.sha(content));
        byte[] changed = content.clone(); changed[0] ^= 1;
        Files.write(external, changed, StandardOpenOption.TRUNCATE_EXISTING);
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(bound, good));
            return null;
        });
        // The independently supplied corrupted input stays corrupted; no repair/publication.
        assertArrayEquals(changed, Files.readAllBytes(external));
        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot()));
        assertEquals(casLeavesBefore, leaves(f.root.resolve("artifacts")));
    }

    @Test void realNoActiveForeignWriterWrongThreadAndEscapedSessionBoundaries() throws IOException {
        Fixture f = fixture("external-scope");
        Path external = f.root.resolve("external-scope.txt");
        byte[] content = new byte[] {0, 1, 127, (byte)128, (byte)255, 65, 66, 67, 10};
        Files.write(external, content, StandardOpenOption.CREATE_NEW);
        ExactRef ref = new ExactRef(external.toString(), content.length, LedgerFiles.sha(content));

        byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot());
        long casLeavesBefore = leaves(f.root.resolve("artifacts"));
        // No active session
        assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(f.archive, ref));

        // Foreign writer
        Fixture foreign = fixture("external-foreign");
        foreign.writer.locked(session -> {
            assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(f.archive, ref));
            return null;
        });

        // Wrong thread
        AtomicReference<NativeOutcomeArchive> escaped = new AtomicReference<>();
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            escaped.set(bound);
            CompletionException crossed = assertThrows(CompletionException.class, () -> CompletableFuture.runAsync(() -> {
                try { invokeVerifyRetainedSourceOriginal(bound, ref); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }).orTimeout(10, java.util.concurrent.TimeUnit.SECONDS).join());
            assertInstanceOf(IllegalArgumentException.class, crossed.getCause());
            return null;
        });

        // Invoke the actual previously borrowed view after its owning Session closed.
        assertThrows(IllegalArgumentException.class, () -> invokeVerifyRetainedSourceOriginal(escaped.get(), ref));
        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot()));
        assertEquals(casLeavesBefore, leaves(f.root.resolve("artifacts")));
    }

    @Test void readOriginalCaptureRejectsNewFileIdAtSameNameWithSameBytesAndMtime() throws Exception {
        Fixture f = fixture("external-capture");
        Path external = f.root.resolve("external-capture.txt");
        byte[] content = new byte[] {0, 1, 127, (byte)128, (byte)255, 65, 66, 67, 10};
        Files.write(external, content, StandardOpenOption.CREATE_NEW);
        ExactRef ref = new ExactRef(external.toString(), content.length, LedgerFiles.sha(content));

        byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot());
        long casLeavesBefore = leaves(f.root.resolve("artifacts"));
        // Get the private ThreadLocal field
        Field captureField = NativeOutcomeArchive.class.getDeclaredField("readOriginalCapture");
        captureField.setAccessible(true);
        @SuppressWarnings("unchecked") ThreadLocal<Object> captureHolder = (ThreadLocal<Object>) captureField.get(f.archive);

        // Get the private ReadOriginalCapture class and constructor
        Class<?> captureClass = Class.forName(NativeOutcomeArchive.class.getName() + "$ReadOriginalCapture");
        Constructor<?> captureConstructor = captureClass.getDeclaredConstructor(ContinuityStorePort.Session.class, List.class);
        captureConstructor.setAccessible(true);

        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            assertNull(captureHolder.get(), "test must own an otherwise absent capture scope");
            Object capture;
            try { capture = captureConstructor.newInstance(session, List.of()); }
            catch (ReflectiveOperationException infrastructure) {
                throw new AssertionError("test capture constructor failed", infrastructure);
            }
            captureHolder.set(capture);
            try {
                // First read
                byte[] first = invokeVerifyRetainedSourceOriginal(bound, ref);
                assertArrayEquals(content, first);

                Pin independentlyObserved = LedgerFiles.read(external, content.length).pin();
                try {
                    Field pins = captureClass.getDeclaredField("pins");
                    pins.setAccessible(true);
                    assertEquals(Map.of(ref, independentlyObserved), pins.get(capture),
                            "capture must contain the actual first external Pin");
                } catch (ReflectiveOperationException infrastructure) {
                    throw new AssertionError("test capture observation failed", infrastructure);
                }
                // Record original mtime before moving old file aside
                var originalAttrs = Files.readAttributes(external, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                var originalMtime = originalAttrs.lastModifiedTime();

                // Rename old, create new with same bytes and mtime but new FileID
                Path retained = external.resolveSibling("retained-original.txt");
                Files.move(external, retained);
                Files.write(external, content, StandardOpenOption.CREATE_NEW);
                Files.setLastModifiedTime(external, originalMtime);
                assertArrayEquals(content, Files.readAllBytes(external));
                assertEquals(originalMtime, Files.getLastModifiedTime(external));
                assertNotEquals(LedgerFiles.identity(retained).fileIdDecimal(),
                        LedgerFiles.identity(external).fileIdDecimal(), "retained old object proves new FileID");

                // Second read must reject because remember sees the new actual Pin
                assertThrows(IOException.class, () -> invokeVerifyRetainedSourceOriginal(bound, ref));
            } finally {
                captureHolder.remove();
            }
            return null;
        });
        assertNull(captureHolder.get());
        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot()));
        assertEquals(casLeavesBefore, leaves(f.root.resolve("artifacts")));
    }
}