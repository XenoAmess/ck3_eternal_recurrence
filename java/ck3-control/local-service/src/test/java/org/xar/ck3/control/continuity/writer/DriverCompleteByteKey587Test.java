package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts.Layout;
import org.xar.ck3.control.continuity.writer.WriterContracts.Request;
import org.xar.ck3.control.continuity.writer.WriterContracts.TransitionAuthority;

/**
 * One scoped DATA witness; software validation is recorded separately.
 * Reuses the pinned mature storage helper binary, not its source or the old333 tests.
 */
final class DriverCompleteByteKey587Test {
    private static final String MACHINE = "driver-bytekey587";
    private static final Instant NOW = Instant.parse("2026-11-02T00:00:00Z");
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software587","bridge_pid":123,"episode_character_id":73,"episode_run_id":"episode587",
         "last_checkpoint":null,"command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"goal587"},"rollback_war_failures":null}
        """;

    @TempDir Path temporary;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var storage : storageScopes) {
            try {
                storage.close();
            } catch (IOException problem) {
                if (failure == null) failure = problem;
                else failure.addSuppressed(problem);
            }
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    @Test void collidingFullBytesStaySeparateThroughCallerMutationAndLru() throws IOException {
        byte[] a = driver("aA");
        byte[] b = driver("BB");
        assertFalse(Arrays.equals(a, b), "different complete JSON originals");
        assertEquals(a.length, b.length, "same-array replacement preserves length");
        assertEquals(ByteBuffer.wrap(a).hashCode(), ByteBuffer.wrap(b).hashCode(),
                "actual public ByteBuffer collision precondition");
        var fixture = new Fixture();

        fixture.writer.locked(session -> fixture.archive.inSession(session, bound -> {
            byte[] caller = a.clone();
            var firstA = fixture.loader.decodeCompleteDriverBytes(caller);
            var firstB = fixture.loader.decodeCompleteDriverBytes(b);
            assertNotSame(firstA, firstB, "same hash does not identify complete bytes");
            assertNotEquals(firstA.campaignGoal(), firstB.campaignGoal(), "actual Driver DATA differs");
            assertSame(firstA, fixture.loader.decodeCompleteDriverBytes(a.clone()));

            assertSame(firstA, fixture.loader.decodeCompleteDriverBytes(caller));
            System.arraycopy(b, 0, caller, 0, b.length);
            assertSame(firstB, fixture.loader.decodeCompleteDriverBytes(caller),
                    "same caller array now holds the other legal complete JSON");
            assertSame(firstA, fixture.loader.decodeCompleteDriverBytes(a.clone()),
                    "retained private A key survives caller mutation");

            fixture.loader.decodeCompleteDriverBytes(driver("CC"));
            fixture.loader.decodeCompleteDriverBytes(driver("DD"));
            assertSame(firstA, fixture.loader.decodeCompleteDriverBytes(a.clone()), "refresh A at four entries");
            fixture.loader.decodeCompleteDriverBytes(driver("EE"));
            assertSame(firstA, fixture.loader.decodeCompleteDriverBytes(a.clone()), "recent A survives fifth entry");

            var rebuiltB = fixture.loader.decodeCompleteDriverBytes(b.clone());
            assertNotSame(firstB, rebuiltB, "least-recent colliding B was evicted");
            assertEquals(firstB.campaignGoal(), rebuiltB.campaignGoal(), "rebuild retains original B DATA");
            assertSame(rebuiltB, fixture.loader.decodeCompleteDriverBytes(caller), "rebuilt exact B hits independently");
            assertSame(firstA, fixture.loader.decodeCompleteDriverBytes(a.clone()), "A remains independently keyed");
            return null;
        }));
    }

    private final class Fixture {
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;

        Fixture() throws IOException {
            Path root = Files.createDirectory(temporary.resolve("scoped-collision"));
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite software source587", StandardOpenOption.CREATE_NEW);
            var source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            var layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(
                    root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) {
                    return ContinuityJson.digest(request.detailsObject());
                }
                @Override public ContinuityState reduce(ContinuityState before, Request request) {
                    throw new IllegalStateException("no fixture ledger commits");
                }
            }, Clock.fixed(NOW, ZoneOffset.UTC),
                    new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer, loader);
        }
    }

    private static ObjectNode state() {
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

    private static byte[] driver(String goal) {
        byte[] original = DRIVER.replace("goal587", goal).getBytes(StandardCharsets.UTF_8);
        assertTrue(original.length < 1024, "small original; no large budget payload");
        return original;
    }
}
