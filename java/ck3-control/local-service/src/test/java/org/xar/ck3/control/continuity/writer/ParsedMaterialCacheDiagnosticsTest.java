package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;

/** Public Archive software witnesses; no private cache access, Root role or runtime authority. */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
final class ParsedMaterialCacheDiagnosticsTest {
    private static final String PROPERTY = "ck3.dev.archiveParsedMaterialDiagnostics";
    private static final String PREFIX = "ARCHIVE_PARSED_DIAGNOSTICS";
    private static final String MACHINE = "parsed-cache-diagnostics";
    @TempDir Path temp;
    private final String oldProperty = System.getProperty(PROPERTY);
    private final PrintStream oldError = System.err;
    private final List<StorageWriteGuardTestSupport> guards = new ArrayList<>();

    @AfterEach void restore() throws IOException {
        System.setErr(oldError);
        if (oldProperty == null) System.clearProperty(PROPERTY); else System.setProperty(PROPERTY, oldProperty);
        Thread.interrupted(); // Test cleanup only; production must retain the prior flag.
        IOException failure = null;
        for (var guard : guards) try { guard.close(); }
        catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        if (failure != null) throw failure;
    }

    @Test @Order(1) void scopedProfilesLifetimeAndEvictionKeepActualReads() throws IOException {
        System.clearProperty(PROPERTY);
        var f = new Fixture("profiles");
        var references = new ArrayList<ExactRef>();
        for (int i = 0; i < 65; i++) references.add(f.publish(new RawJson(bytes("{\"KEEP_BODY_SECRET\":" + i + "}"))));
        ExactRef firstRef = references.getFirst();
        var output = new ByteArrayOutputStream(); System.setErr(new PrintStream(output, true, StandardCharsets.UTF_8));
        f.writer.locked(session -> f.archive.inSession(session, archive -> {
            assertArrayEquals(bytes("{\"KEEP_BODY_SECRET\":0}"), archive.loadMaterial(firstRef).bytes());
            return null;
        }));
        assertTrue(lines(output).isEmpty(), "default-disabled diagnostics must stay silent");

        System.setProperty(PROPERTY, "true");
        RawJson warm = f.writer.locked(session -> f.archive.inSession(session, archive -> {
            RawJson protocol = archive.loadMaterial(firstRef);
            assertSame(protocol, archive.loadMaterial(firstRef));
            RawJson full = archive.loadFullMaterial(firstRef);
            assertNotSame(protocol, full);
            assertSame(full, archive.loadFullMaterial(firstRef));
            f.archive.inSession(session, nested -> { assertSame(protocol, nested.loadMaterial(firstRef)); return null; });
            return protocol;
        }));
        List<String> first = lines(output); assertEquals(1, first.size(), "nested scope must not report separately");
        String line = first.getFirst();
        assertEquals(2, number(line, "protocol_hits")); assertEquals(1, number(line, "protocol_key_absent"));
        assertEquals(1, number(line, "full_material_hits")); assertEquals(1, number(line, "full_material_key_absent"));
        assertEquals(0, number(line, "protocol_bytes_unequal")); assertEquals(0, number(line, "full_material_bytes_unequal"));
        assertEquals(2, number(line, "final_entries")); assertEquals(2, number(line, "peak_entries"));
        assertEquals(1, number(line, "completed"));
        assertTrue(line.contains("limit_scope=archive_class_generation"));
        assertFalse(line.contains("KEEP_BODY_SECRET")); assertFalse(line.contains(firstRef.path())); assertFalse(line.contains(firstRef.sha256()));
        output.reset();
        RawJson cold = f.writer.locked(session -> f.archive.inSession(session, archive -> archive.loadMaterial(firstRef)));
        assertNotSame(warm, cold); assertEquals(1, number(lines(output).getFirst(), "protocol_key_absent"));
        output.reset();
        f.writer.locked(session -> f.archive.inSession(session, archive -> {
            RawJson oldest = archive.loadMaterial(firstRef);
            for (int i = 1; i < references.size(); i++) assertArrayEquals(bytes("{\"KEEP_BODY_SECRET\":" + i + "}"), archive.loadMaterial(references.get(i)).bytes());
            assertNotSame(oldest, archive.loadMaterial(firstRef));
            return null;
        }));
        line = lines(output).getFirst();
        assertEquals(66, number(line, "protocol_key_absent")); assertEquals(64, number(line, "final_entries"));
        assertEquals(64, number(line, "peak_entries")); assertEquals(2, number(line, "evictions"));
        assertEquals(2, number(line, "entry_evictions")); assertEquals(0, number(line, "byte_evictions"));
        assertEquals(0, number(line, "entry_headroom"));
        assertEquals(64L * 1024 * 1024 - number(line, "final_retained_bytes"), number(line, "byte_headroom"));
    }

    @Test @Order(2) void absentScopeProfilesFreshFailureAndOutletFailurePreserveBusiness() throws IOException {
        System.setProperty(PROPERTY, "true");
        var f = new Fixture("failure");
        RawJson original = new RawJson(bytes("{\"private_marker\":true}"));
        ExactRef ref = f.publish(original);
        var output = new ByteArrayOutputStream(); System.setErr(new PrintStream(output, true, StandardCharsets.UTF_8));
        f.writer.locked(session -> {
            RawJson a = f.archive.loadMaterial(ref), b = f.archive.loadMaterial(ref);
            assertNotSame(a, b); assertEquals(original, a); assertEquals(original, b);
            return null;
        });
        List<String> notices = lines(output); assertEquals(1, notices.size());
        assertTrue(notices.getFirst().contains("no_scope_seen=true count=UNKNOWN"));
        assertTrue(notices.getFirst().contains("limit_scope=archive_class_generation"));
        output.reset();
        ExactRef longNumber = f.publish(RawJson.fullMaterial(bytes("9".repeat(4301))));
        f.writer.locked(session -> f.archive.inSession(session, archive -> {
            assertEquals(4301, archive.loadFullMaterial(longNumber).bytes().length);
            assertThrows(IllegalArgumentException.class, () -> archive.loadMaterial(longNumber));
            return null;
        }));
        assertEquals(1, number(lines(output).getFirst(), "full_material_key_absent"));
        assertEquals(1, number(lines(output).getFirst(), "protocol_key_absent"));
        output.reset();
        Path rawPath = Path.of(ref.path()).toAbsolutePath().normalize();
        assertTrue(rawPath.startsWith(temp.toAbsolutePath().normalize()));
        byte[] changed = original.bytes(); changed[changed.length - 2] = 'x';
        assertThrows(UncheckedIOException.class, () -> f.writer.locked(session -> f.archive.inSession(session, archive -> {
            archive.loadMaterial(ref);
            overwrite(rawPath, changed);
            try { return archive.loadMaterial(ref); }
            finally { overwrite(rawPath, original.bytes()); }
        })));
        assertEquals(0, number(lines(output).getFirst(), "completed"));
        // Restored bytes do not restore the Store's original native pin. Never reuse that original.
        var outlet = new Fixture("outlet");
        ExactRef outletRef = outlet.publish(original);
        outlet.writer.locked(session -> outlet.archive.inSession(session, archive -> { assertEquals(original, archive.loadMaterial(outletRef)); return null; }));
        var callbacks = new AtomicInteger();
        for (boolean error : new boolean[] {false, true}) {
            System.setErr(new FaultOutput(error));
            RuntimeException business = new IllegalStateException("exact business marker");
            assertSame(business, assertThrows(IllegalStateException.class, () -> outlet.writer.locked(session -> outlet.archive.inSession(session, archive -> {
                callbacks.incrementAndGet(); throw business;
            }))));
            Object marker = new Object();
            Object actual = outlet.writer.locked(session -> outlet.archive.inSession(session, archive -> {
                callbacks.incrementAndGet(); Thread.currentThread().interrupt(); return marker;
            }));
            assertSame(marker, actual); assertTrue(Thread.currentThread().isInterrupted());
            Thread.interrupted(); // Reset only in the Test, after checking retained status.
        }
        assertEquals(4, callbacks.get());
        System.setErr(new PrintStream(output, true, StandardCharsets.UTF_8));
        assertEquals(original, outlet.writer.locked(session -> outlet.archive.inSession(session, archive -> archive.loadMaterial(outletRef))));
    }

    @Test @Order(3) void summaryVolumeIsBoundedWithinThisArchiveGeneration() throws IOException {
        System.setProperty(PROPERTY, "true");
        var f = new Fixture("bounded"); var output = new ByteArrayOutputStream();
        System.setErr(new PrintStream(output, true, StandardCharsets.UTF_8));
        for (int i = 0; i < 70; i++) {
            int expected = i;
            assertEquals(expected, f.writer.locked(session -> f.archive.inSession(session, archive -> expected)).intValue());
        }
        List<String> summaries = lines(output).stream().filter(s -> s.contains("scope_summary=true")).toList();
        assertFalse(summaries.isEmpty()); assertTrue(summaries.size() <= 64); assertTrue(summaries.size() < 70);
        for (String line : summaries) {
            assertTrue(number(line, "summary_slot") >= 1 && number(line, "summary_slot") <= 64);
            assertEquals(64, number(line, "summary_limit")); assertEquals(0, number(line, "final_entries"));
        }
        output.reset(); System.setProperty(PROPERTY, "false");
        assertEquals("disabled", f.writer.locked(session -> f.archive.inSession(session, archive -> "disabled")));
        assertTrue(lines(output).isEmpty());
    }

    private static List<String> lines(ByteArrayOutputStream out) {
        return out.toString(StandardCharsets.UTF_8).lines().filter(s -> s.startsWith(PREFIX + " ")).toList();
    }
    private static long number(String line, String key) {
        String prefix = key + "=";
        return line.lines().flatMap(s -> List.of(s.split(" ")).stream()).filter(s -> s.startsWith(prefix))
                .mapToLong(s -> Long.parseLong(s.substring(prefix.length()))).findFirst().orElseThrow();
    }
    private static byte[] bytes(String s) { return s.getBytes(StandardCharsets.UTF_8); }
    private static void overwrite(Path path, byte[] bytes) {
        try { Files.write(path, bytes); } catch (IOException problem) { throw new UncheckedIOException(problem); }
    }
    private static final class FaultOutput extends PrintStream {
        private final boolean error;
        FaultOutput(boolean error) { super(new ByteArrayOutputStream()); this.error = error; }
        @Override public void println(String value) {
            if (value.startsWith(PREFIX)) {
                if (error) throw new AssertionError("diagnostic Error");
                throw new IllegalStateException("diagnostic RuntimeException");
            }
        }
    }
    private final class Fixture {
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(String name) throws IOException {
            Path root = Files.createDirectory(temp.resolve(name));
            assertTrue(root.startsWith(Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize()));
            byte[] state = ContinuityJson.canonical(initial());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite owned software source", StandardOpenOption.CREATE_NEW);
            ExactRef source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            var layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var guard = StorageWriteGuardTestSupport.create(layout); guards.add(guard);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), guard);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no fixture ledger commits"); }
            }, Clock.fixed(Instant.parse("2026-11-03T00:00:00Z"), ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), guard);
            archive = new NativeOutcomeArchive(store, writer);
        }
        ExactRef publish(RawJson value) throws IOException { return writer.locked(session -> archive.preserveMaterial(value)); }
    }
    private static ObjectNode initial() {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE)
                .put("sequence", 0).put("window_id", 1).put("start_date_raw", 1000).put("target_date_raw", 1024)
                .put("target_days", 1).put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
        row.putNull("pending_cycle").putNull("pending_checkpoint"); row.putArray("unknown_requests"); return row;
    }
}
