package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Public, finite software Writer admission only; no application or Root permission issuer. */
final class WriterPhaseDiagnosticsTest {
    private static final String FLAG = "ck3.dev.writerPhaseDiagnostics";
    private static final String MACHINE = "writer-phase-software";
    private static final String KIND = "writer_phase_test";
    @TempDir Path temporary;

    @Test void defaultAndEnabledNormalDuplicateAndNoChangePreservePublicWriterResults() throws Exception {
        try (Diagnostics d = new Diagnostics(false, null);
                Fixture f = new Fixture(temporary.resolve("disabled"))) {
            f.writer.locked(session -> {
                Request request = request("disabled", false);
                Receipt result = session.commit(session.preview(request));
                assertLiteralCommit(f, request, result);
                assertEquals(List.of("revalidate:disabled", "reduce:disabled",
                        "revalidate:disabled", "reduce:disabled"), f.authority.trace);
                return null;
            });
            assertEquals(0, d.outlet.attempts);
        }
        try (Diagnostics d = new Diagnostics(true, null);
                Fixture f = new Fixture(temporary.resolve("enabled"))) {
            f.writer.locked(session -> {
                Request request = request("enabled", false);
                Prepared prepared = session.preview(request);
                Receipt result = session.commit(prepared);
                assertLiteralCommit(f, request, result);
                assertEquals(2, f.authority.revalidations);
                assertEquals(2, f.authority.reductions);
                byte[] persisted = Files.readAllBytes(f.layout.snapshot());

                Receipt duplicate = session.commit(prepared);
                assertEquals(Disposition.ALREADY_COMMITTED, duplicate.disposition());
                assertEquals(0, duplicate.writes());
                assertArrayEquals(result.head().canonicalBytes(), duplicate.head().canonicalBytes());
                Prepared duplicatePreview = session.preview(request);
                assertArrayEquals(result.head().canonicalBytes(), duplicatePreview.reduced().canonicalBytes());
                assertEquals(2, f.authority.revalidations);
                assertEquals(2, f.authority.reductions);

                Request same = request("same", true);
                Receipt quiet = session.commit(session.preview(same));
                assertEquals(Disposition.NO_CHANGE, quiet.disposition());
                assertEquals(0, quiet.writes());
                assertArrayEquals(persisted, Files.readAllBytes(f.layout.snapshot()));
                assertFalse(Files.exists(f.layout.event(2)));
                assertFalse(Files.exists(f.layout.sourceIndex(same.sourceKey())));
                assertEquals(4, f.authority.revalidations);
                assertEquals(4, f.authority.reductions);
                return null;
            });
            List<String> lines = d.outlet.lines();
            assertEquals(6, lines.size(), "one optional summary per instrumented public path");
            Map<String, String> preview = summary(lines.get(0), true);
            assertEquals("true", preview.get("returned"));
            assertTrue(number(preview, "revalidate_ns") >= 0);
            assertTrue(number(preview, "reduce_ns") >= 0);
            Map<String, String> commit = summary(lines.get(1), false);
            assertEquals("true", commit.get("returned"));
            assertTrue(number(commit, "write_ns") >= 0);
            Map<String, String> recovery = summary(lines.get(2), false);
            assertEquals("true", recovery.get("returned"));
            assertTrue(number(recovery, "duplicate_recovery_ns") >= 0);
            assertEquals(-1, number(recovery, "revalidate_ns"));
            assertEquals(-1, number(recovery, "write_ns"));
            Map<String, String> duplicate = summary(lines.get(3), true);
            assertEquals("true", duplicate.get("duplicate_path"));
            assertTrue(number(duplicate, "duplicate_validation_ns") >= 0);
            assertEquals(-1, number(duplicate, "revalidate_ns"));
            assertEquals(-1, number(duplicate, "reduce_ns"));
            summary(lines.get(4), true);
            Map<String, String> quiet = summary(lines.get(5), false);
            assertEquals("true", quiet.get("returned"));
            assertEquals(-1, number(quiet, "write_ns"));
        }
    }

    @Test void originalAuthorityAndFreshSourceFailuresAreNotReplacedByDiagnosticFaults() throws Exception {
        RuntimeException previewFailure = new IllegalStateException("original preview marker");
        try (Diagnostics d = new Diagnostics(true, new IllegalArgumentException("outlet runtime"));
                Fixture f = new Fixture(temporary.resolve("preview-failure"))) {
            f.authority.failure = previewFailure;
            f.authority.failRevalidateAt = 1;
            Request request = request("preview-failure", false);
            f.writer.locked(session -> {
                assertSame(previewFailure, assertThrows(IllegalStateException.class, () -> session.preview(request)));
                assertEquals(1, f.authority.revalidations);
                assertEquals(0, f.authority.reductions);
                assertUnpublished(f, request);
                return null;
            });
            assertEquals(1, d.outlet.attempts);
        }
        RuntimeException commitFailure = new IllegalStateException("original commit marker");
        try (Diagnostics d = new Diagnostics(true, new AssertionError("outlet error"));
                Fixture f = new Fixture(temporary.resolve("commit-failure"))) {
            f.authority.failure = commitFailure;
            f.authority.failReduceAt = 2;
            Request request = request("commit-failure", false);
            f.writer.locked(session -> {
                Prepared prepared = session.preview(request);
                assertSame(commitFailure, assertThrows(IllegalStateException.class, () -> session.commit(prepared)));
                assertEquals(2, f.authority.revalidations);
                assertEquals(2, f.authority.reductions);
                assertUnpublished(f, request);
                return null;
            });
            assertEquals(2, d.outlet.attempts);
        }
        try (Diagnostics d = new Diagnostics(true, new IllegalStateException("outlet runtime"));
                Fixture f = new Fixture(temporary.resolve("fresh-source-failure"))) {
            f.authority.changeSourceOnCommit = true;
            Request request = request("fresh-source-failure", false);
            f.writer.locked(session -> {
                Prepared prepared = session.preview(request);
                IOException rejected = assertThrows(IOException.class, () -> session.commit(prepared));
                assertFalse(rejected instanceof CommitUncertainException);
                assertTrue(rejected.getMessage().contains("named source bytes/SHA/path changed"));
                assertUnpublished(f, request);
                return null;
            });
            assertEquals(2, d.outlet.attempts);
        }
        // Independent new storage/ref: restoring bytes would not restore the native Pin's identity.
        try (Diagnostics d = new Diagnostics(true, new AssertionError("outlet error"));
                Fixture f = new Fixture(temporary.resolve("successful-faulting-outlet"))) {
            f.writer.locked(session -> {
                Request request = request("successful-faulting-outlet", false);
                assertLiteralCommit(f, request, session.commit(session.preview(request)));
                return null;
            });
            assertEquals(2, d.outlet.attempts);
        }
    }

    @Test void alreadyInterruptedExitSkipsOptionalOutputAndKeepsFlag() throws Exception {
        assertFalse(Thread.currentThread().isInterrupted());
        RuntimeException marker = new IllegalStateException("interrupt boundary marker");
        try (Diagnostics d = new Diagnostics(true, new AssertionError("must not print"));
                Fixture f = new Fixture(temporary.resolve("interrupted"))) {
            f.authority.failure = marker;
            f.authority.failRevalidateAt = 1;
            f.authority.interruptAtFailure = true;
            Request request = request("interrupted", false);
            try {
                f.writer.locked(session -> {
                    assertSame(marker, assertThrows(IllegalStateException.class, () -> session.preview(request)));
                    assertTrue(Thread.currentThread().isInterrupted(), "diagnostic path must not clear the flag");
                    assertEquals(0, d.outlet.attempts);
                    assertEquals(1, f.authority.revalidations);
                    assertEquals(0, f.authority.reductions);
                    // Clear only this test's interruption after checking it, before further physical file IO.
                    assertTrue(Thread.interrupted());
                    assertUnpublished(f, request);
                    f.authority.failRevalidateAt = 0;
                    f.authority.interruptAtFailure = false;
                    Request later = request("later", false);
                    assertLiteralCommit(f, later, session.commit(session.preview(later)));
                    return null;
                });
            } finally {
                Thread.interrupted();
            }
            assertEquals(2, d.outlet.attempts, "only the later normal paths attempted output");
        }
    }

    private static void assertLiteralCommit(Fixture f, Request request, Receipt result) throws IOException {
        assertEquals(Disposition.COMMITTED, result.disposition());
        assertEquals(3, result.writes());
        ObjectNode expected = initial();
        expected.putObject("payload").put("text", "kept-\u00c5-\u4e2d").putNull("optional");
        expected.put("sequence", 1).put("last_event_identity", request.identity());
        byte[] raw = ContinuityJson.canonical(expected);
        assertArrayEquals(raw, result.head().canonicalBytes());
        assertArrayEquals(withNewline(raw), Files.readAllBytes(f.layout.snapshot()));
        assertTrue(Files.isRegularFile(f.layout.event(1)));
        assertTrue(Files.isRegularFile(f.layout.sourceIndex(request.sourceKey())));
    }

    private static void assertUnpublished(Fixture f, Request request) throws IOException {
        assertArrayEquals(f.initialBytes, Files.readAllBytes(f.layout.snapshot()));
        assertFalse(Files.exists(f.layout.event(1)));
        assertFalse(Files.exists(f.layout.sourceIndex(request.sourceKey())));
        assertEquals(0, f.storage.successfulBatches());
        assertFalse(f.storage.hasUnknownWrite());
    }

    private static Map<String, String> summary(String line, boolean preview) {
        assertTrue(line.length() < 2000, "bounded primitive-only summary");
        String[] parts = line.split(" ");
        assertEquals(preview ? "WRITER_PREVIEW_INTERNAL" : "WRITER_COMMIT_PREPARED", parts[0]);
        Map<String, String> values = new LinkedHashMap<>();
        for (int i = 1; i < parts.length; i++) {
            String[] pair = parts[i].split("=", -1);
            assertEquals(2, pair.length);
            assertNull(values.put(pair[0], pair[1]), "duplicate metadata key");
        }
        Set<String> keys = preview
                ? Set.of("phase", "thread", "event_ns", "elapsed_ns", "head_ns", "sources_ns", "evidence_ns",
                        "duplicate_ns", "revalidate_ns", "reduce_ns", "validate_ns", "duplicate_path",
                        "duplicate_validation_ns", "returned")
                : Set.of("phase", "thread", "event_ns", "elapsed_ns", "source_ns", "evidence_ns", "closure_ns",
                        "head_ns", "duplicate_ns", "predecessor_ns", "revalidate_ns", "reduce_ns", "validate_ns",
                        "fresh_source_ns", "fresh_evidence_ns", "document_ns", "absence_ns", "plan_ns", "write_ns",
                        "duplicate_recovery_ns", "returned");
        assertEquals(keys, values.keySet(), "no path, identity, body, digest or exception text fields");
        for (Map.Entry<String, String> row : values.entrySet()) {
            if (row.getKey().equals("returned") || row.getKey().equals("duplicate_path")) {
                assertTrue(row.getValue().equals("true") || row.getValue().equals("false"));
            } else {
                long value = Long.parseLong(row.getValue());
                if (row.getKey().endsWith("_ns") && !row.getKey().equals("event_ns")) assertTrue(value >= -1);
            }
        }
        assertTrue(number(values, "thread") > 0);
        assertTrue(number(values, "elapsed_ns") >= 0);
        return values;
    }

    private static long number(Map<String, String> values, String field) { return Long.parseLong(values.get(field)); }

    private static Request request(String id, boolean same) {
        ObjectNode details = StrictJson.object().put("evidence_id", id).put("source", "owned-software-input")
                .put("mode", same ? "same" : "replace");
        if (!same) details.putObject("next_payload").put("text", "kept-\u00c5-\u4e2d").putNull("optional");
        return new Request(KIND, ContinuityJson.canonical(details), List.of());
    }

    private static ObjectNode initial() {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1")
                .put("machine_id", MACHINE).put("sequence", 0).put("window_id", 1)
                .put("start_date_raw", 1000).put("target_date_raw", 1024).put("target_days", 1)
                .put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
        row.putObject("pending_cycle").put("stage", "UNKNOWN").putNull("optional");
        row.putArray("unknown_requests").add("keep-this-exact");
        return row.put("NEXT", 73).putNull("pending_checkpoint");
    }

    private static byte[] withNewline(byte[] raw) {
        byte[] result = Arrays.copyOf(raw, raw.length + 1);
        result[raw.length] = '\n';
        return result;
    }

    private static ExactRef reference(Path path) throws Exception {
        byte[] raw = Files.readAllBytes(path);
        return new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }

    private static final class ProbeAuthority implements TransitionAuthority {
        private final Path source;
        private final List<String> trace = new ArrayList<>();
        private int revalidations, reductions, failRevalidateAt, failReduceAt;
        private boolean changeSourceOnCommit, interruptAtFailure;
        private RuntimeException failure;
        private ProbeAuthority(Path source) { this.source = source; }
        @Override public String revalidate(ContinuityState ignored, Request request) {
            throw new AssertionError("actual Writer must use its Head-aware authority contract");
        }
        @Override public String revalidate(Head actual, Request request) {
            assertEquals(MACHINE, actual.state().machineId());
            revalidations++;
            trace.add("revalidate:" + request.detailsObject().get("evidence_id").textValue());
            if (revalidations == failRevalidateAt) {
                if (interruptAtFailure) Thread.currentThread().interrupt();
                throw failure;
            }
            return ContinuityJson.digest(request.detailsObject());
        }
        @Override public ContinuityState reduce(ContinuityState before, Request request) throws IOException {
            reductions++;
            trace.add("reduce:" + request.detailsObject().get("evidence_id").textValue());
            if (reductions == failReduceAt) throw failure;
            if (changeSourceOnCommit && reductions == 2) Files.writeString(source, "changed owned source");
            ObjectNode details = request.detailsObject();
            if (details.get("mode").textValue().equals("same")) return before;
            ObjectNode row = before.toJson();
            row.set("payload", details.get("next_payload"));
            return ContinuityState.fromJson(row, MACHINE);
        }
    }

    private static final class Diagnostics implements AutoCloseable {
        private final String oldFlag = System.getProperty(FLAG);
        private final PrintStream oldError = System.err;
        private final Outlet outlet;
        private Diagnostics(boolean enabled, Throwable failure) {
            if (enabled) System.setProperty(FLAG, "true"); else System.clearProperty(FLAG);
            outlet = new Outlet(oldError, failure);
            System.setErr(outlet);
        }
        @Override public void close() {
            System.setErr(oldError);
            if (oldFlag == null) System.clearProperty(FLAG); else System.setProperty(FLAG, oldFlag);
            outlet.close();
        }
    }

    private static final class Outlet extends PrintStream {
        private final PrintStream original;
        private final Throwable failure;
        private final ByteArrayOutputStream captured = new ByteArrayOutputStream();
        private int attempts;
        private Outlet(PrintStream original, Throwable failure) {
            super(original, true, StandardCharsets.UTF_8);
            this.original = original;
            this.failure = failure;
        }
        @Override public void println(String line) {
            if (line != null && (line.startsWith("WRITER_PREVIEW_INTERNAL ") || line.startsWith("WRITER_COMMIT_PREPARED "))) {
                attempts++;
                if (failure instanceof RuntimeException runtime) throw runtime;
                if (failure instanceof Error error) throw error;
                byte[] raw = (line + "\n").getBytes(StandardCharsets.UTF_8);
                captured.writeBytes(raw);
            } else {
                original.println(line);
            }
        }
        @Override public void close() { flush(); } // Never close the original process stderr.
        private List<String> lines() { return captured.toString(StandardCharsets.UTF_8).lines().toList(); }
    }

    private static final class Fixture implements AutoCloseable {
        private final Layout layout;
        private final ContinuityWriter writer;
        private final StorageWriteGuardTestSupport storage;
        private final ProbeAuthority authority;
        private final byte[] initialBytes;
        private Fixture(Path directory) throws Exception {
            Path root = directory.toAbsolutePath().normalize();
            Path ownedTemporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
            assertTrue(root.startsWith(ownedTemporary), "all fixture storage must belong to this runner's temporary directory");
            Files.createDirectory(root);
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
            initialBytes = ContinuityJson.canonical(initial());
            Files.write(snapshot, initialBytes);
            Files.write(anchor, initialBytes);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path source = root.resolve("source.txt");
            Files.writeString(source, "original owned source");
            layout = new Layout(snapshot, reference(anchor), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            authority = new ProbeAuthority(source);
            writer = new ContinuityWriter(layout, List.of(reference(source)), authority,
                    Clock.fixed(Instant.parse("2023-01-01T00:00:00Z"), ZoneOffset.UTC), storage);
        }
        @Override public void close() throws IOException { storage.close(); }
    }
}
