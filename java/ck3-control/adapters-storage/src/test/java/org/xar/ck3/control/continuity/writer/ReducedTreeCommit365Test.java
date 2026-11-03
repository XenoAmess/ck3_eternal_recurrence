package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Public Writer behavior under finite software-only storage admission, never Root or Game authority. */
final class ReducedTreeCommit365Test {
    private static final String MACHINE = "writer-reduced-tree365-software";
    private static final String KIND = "software_reduced_tree365";
    @TempDir Path temporary;

    @Test void changedAndNoChangeKeepReducedStateDetached() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("changed"))) {
            Request changed = request("changed", false);
            f.writer.locked(session -> {
                Prepared prepared = session.preview(changed);
                byte[] originalReduction = prepared.reduced().canonicalBytes();
                Receipt actual = session.commit(prepared);
                assertEquals(Disposition.COMMITTED, actual.disposition());
                assertEquals(3, actual.writes());
                assertEquals(2, f.authority.revalidations);
                assertEquals(2, f.authority.reductions);
                ObjectNode expected = initial();
                expected.set("payload", literalPayload());
                expected.put("sequence", 1);
                expected.put("last_event_identity", changed.identity());
                byte[] expectedState = ContinuityJson.canonical(expected);
                assertArrayEquals(expectedState, actual.head().canonicalBytes());
                assertArrayEquals(withNewline(expectedState), Files.readAllBytes(f.layout.snapshot()));
                assertArrayEquals(originalReduction, prepared.reduced().canonicalBytes());
                assertArrayEquals(originalReduction, f.authority.lastReduced.canonicalBytes());
                assertEquals(0, prepared.reduced().sequence());
                assertFalse(prepared.reduced().toJson().has("last_event_identity"));
                assertTrue(Files.isRegularFile(f.layout.event(1)));
                assertTrue(Files.isRegularFile(f.layout.sourceIndex(changed.sourceKey())));

                byte[] persisted = Files.readAllBytes(f.layout.snapshot());
                Request same = request("unchanged", true);
                Prepared noChange = session.preview(same);
                byte[] originalNoChange = noChange.reduced().canonicalBytes();
                Receipt quiet = session.commit(noChange);
                assertEquals(Disposition.NO_CHANGE, quiet.disposition());
                assertEquals(0, quiet.writes());
                assertEquals(4, f.authority.revalidations);
                assertEquals(4, f.authority.reductions);
                assertArrayEquals(expectedState, quiet.head().canonicalBytes());
                assertArrayEquals(originalNoChange, noChange.reduced().canonicalBytes());
                assertArrayEquals(originalNoChange, f.authority.lastReduced.canonicalBytes());
                assertArrayEquals(persisted, Files.readAllBytes(f.layout.snapshot()));
                assertFalse(Files.exists(f.layout.event(2)));
                assertFalse(Files.exists(f.layout.sourceIndex(same.sourceKey())));
                return null;
            });
        }
    }

    @Test void callbackDriftStillRejectsBeforePublication() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("changed-reducer"))) {
            f.authority.driftOnCommit = true;
            Request request = request("reducer-drift", false);
            f.writer.locked(session -> {
                Prepared prepared = session.preview(request);
                ContractViolationException rejected = assertThrows(ContractViolationException.class,
                        () -> session.commit(prepared));
                assertTrue(rejected.getMessage().contains("same reducer result changed after preview"));
                assertEquals(2, f.authority.revalidations);
                assertEquals(2, f.authority.reductions);
                assertUnpublished(f, request);
                return null;
            });
        }
        try (Fixture f = new Fixture(temporary.resolve("changed-source"))) {
            f.authority.changeSourceOnCommit = true;
            Request request = request("source-drift", false);
            f.writer.locked(session -> {
                Prepared prepared = session.preview(request);
                IOException rejected = assertThrows(IOException.class, () -> session.commit(prepared));
                assertFalse(rejected instanceof CommitUncertainException);
                assertTrue(rejected.getMessage().contains("named source bytes/SHA/path changed"));
                assertEquals(2, f.authority.revalidations);
                assertEquals(2, f.authority.reductions);
                assertUnpublished(f, request);
                return null;
            });
        }
    }

    private static void assertUnpublished(Fixture f, Request request) throws IOException {
        assertArrayEquals(f.initialBytes, Files.readAllBytes(f.layout.snapshot()));
        assertFalse(Files.exists(f.layout.event(1)));
        assertFalse(Files.exists(f.layout.sourceIndex(request.sourceKey())));
        assertEquals(0, f.storage.successfulBatches());
        assertFalse(f.storage.hasUnknownWrite());
    }

    private static Request request(String id, boolean unchanged) {
        ObjectNode details = StrictJson.object().put("evidence_id", id).put("source", "owned-software-input")
                .put("mode", unchanged ? "same" : "replace");
        if (!unchanged) {
            ObjectNode payload = details.putObject("next_payload");
            payload.put("text", "A\u00c5\u4e2d\uD83C\uDF0B").put("negative_zero", -0.0d).putNull("optional");
            payload.putArray("nested").add(7).add(true).addNull().addObject().put("key", "value");
        }
        return new Request(KIND, ContinuityJson.canonical(details), List.of());
    }

    private static ObjectNode literalPayload() {
        return ContinuityJson.parseObject(("{\"text\":\"A\u00c5\u4e2d\uD83C\uDF0B\",\"negative_zero\":-0.0,\"optional\":null,"
                + "\"nested\":[7,true,null,{\"key\":\"value\"}]}").getBytes(StandardCharsets.UTF_8), 4096);
    }

    private static ObjectNode initial() {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1")
                .put("machine_id", MACHINE).put("sequence", 0).put("window_id", 1)
                .put("start_date_raw", 1000).put("target_date_raw", 1024).put("target_days", 1)
                .put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
        row.putObject("pending_cycle").put("stage", "UNKNOWN").putNull("optional");
        row.putArray("unknown_requests").add("keep-this-exact");
        row.put("NEXT", 73).putNull("pending_checkpoint");
        return row;
    }

    private static byte[] withNewline(byte[] canonical) {
        byte[] result = Arrays.copyOf(canonical, canonical.length + 1);
        result[result.length - 1] = '\n';
        return result;
    }

    private static ExactRef reference(Path path) throws Exception {
        byte[] raw = Files.readAllBytes(path);
        return new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }

    private static final class ProbeAuthority implements TransitionAuthority {
        private final Path source;
        private int revalidations, reductions;
        private boolean driftOnCommit, changeSourceOnCommit;
        private ContinuityState lastReduced;
        private ProbeAuthority(Path source) { this.source = source; }
        @Override public String revalidate(ContinuityState ignored, Request request) {
            throw new AssertionError("Writer must preserve its actual Head-aware authority call");
        }
        @Override public String revalidate(Head actual, Request request) {
            assertEquals(MACHINE, actual.state().machineId());
            revalidations++;
            return ContinuityJson.digest(request.detailsObject());
        }
        @Override public ContinuityState reduce(ContinuityState before, Request request) throws IOException {
            reductions++;
            if (changeSourceOnCommit && reductions == 2) Files.writeString(source, "deliberately changed owned source");
            ObjectNode details = request.detailsObject();
            if (details.get("mode").textValue().equals("same")) {
                lastReduced = before;
            } else {
                ObjectNode row = before.toJson();
                row.set("payload", details.get("next_payload"));
                if (driftOnCommit && reductions == 2) ((ObjectNode) row.get("payload")).put("unexpected", true);
                lastReduced = ContinuityState.fromJson(row, MACHINE);
            }
            return lastReduced;
        }
    }

    private static final class Fixture implements AutoCloseable {
        private final Layout layout;
        private final ContinuityWriter writer;
        private final StorageWriteGuardTestSupport storage;
        private final ProbeAuthority authority;
        private final byte[] initialBytes;
        private Fixture(Path directory) throws Exception {
            Path root = directory.toAbsolutePath().normalize();
            Path temp = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
            assertTrue(root.startsWith(temp), "Native runner must place all fixture storage under owned java.io.tmpdir");
            Files.createDirectory(root);
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
            initialBytes = ContinuityJson.canonical(initial());
            Files.write(snapshot, initialBytes); Files.write(anchor, initialBytes);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path source = root.resolve("source.txt"); Files.writeString(source, "original owned source");
            layout = new Layout(snapshot, reference(anchor), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            authority = new ProbeAuthority(source);
            writer = new ContinuityWriter(layout, List.of(reference(source)), authority,
                    Clock.fixed(Instant.parse("2023-01-01T00:00:00Z"), ZoneOffset.UTC), storage);
        }
        @Override public void close() throws IOException { storage.close(); }
    }
}
