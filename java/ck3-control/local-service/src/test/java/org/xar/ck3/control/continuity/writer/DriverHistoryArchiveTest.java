package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.history.DriverHistoryImport;
import org.xar.ck3.control.application.history.DriverHistoryProjection;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.history.RouteContactHistoryAdapter;
import org.xar.ck3.control.application.routecontact.RouteContactProofs;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Real physical archive/writer sessions and the full Driver decoder; no archive or history test double. */
class DriverHistoryArchiveTest {
    @TempDir Path temporary;

    @Test void committedCompleteDriverRoundtripRetainsTheLatestFailedQueryTombstone() throws Exception {
        NativeOutcomeArchive archive = archive(temporary.resolve("writer"));
        byte[] original = Vectors.driver(List.of(
                Vectors.row(1, Vectors.QUERY, true, Vectors.queryResult()),
                Vectors.row(2, Vectors.QUERY, false, null))).encode();
        var ref = archive.preserveMaterial(new RawJson(original));
        assertArrayEquals(original, archive.loadMaterial(ref).bytes());
        var imported = DriverHistoryImport.archivedOriginalV2(archive, ref, 3, 1, Vectors.game(), new Obj(Map.of()));
        assertEquals(ref, imported.facts().originalHistoryBasis());
        var queries = RouteContactHistoryAdapter.queries(imported.completeSurvivingBranch(), Vectors.frame());
        assertTrue(queries.getFirst().valid().isPresent()); assertTrue(queries.getLast().valid().isEmpty());
        assertTrue(RouteContactProofs.oneDayEntries(Vectors.frame(), queries, List.of()).isEmpty());
    }

    @Test void physicalRestoreBranchArchivePreservesStrictFailureAndDiscardsAbandonedGameplay() throws Exception {
        NativeOutcomeArchive archive = archive(temporary.resolve("writer"));
        var checkpoint = Vectors.checkpoint(2);
        var original = List.of(
                Vectors.row(1, Vectors.ADVANCE, false, Vectors.strictFailure()), Vectors.anchor(2),
                Vectors.row(3, "move-army-1-to-99", true, "{\"war_action\":{\"status\":\"moving\"}}"),
                Vectors.row(4, "restore-checkpoint", true, Vectors.result(checkpoint, "native-session-cold-start", 7, 9)));
        var completed = Vectors.row(5, "restore-checkpoint", true,
                Vectors.result(checkpoint, "native-session-lifecycle-queue", 7, 9));
        var restored = assertInstanceOf(DriverHistoryProjection.Available.class,
                DriverHistoryProjection.completedRestore(checkpoint, original, completed));
        assertEquals(3, restored.rows().size()); assertEquals(1, restored.retainedPhysicalRestarts());
        var branch = new ArrayList<>(restored.rows());
        branch.add(Vectors.row(4, Vectors.QUERY, true, Vectors.queryResult()));
        var ref = archive.preserveMaterial(new RawJson(Vectors.driver(branch).encode()));
        var imported = DriverHistoryImport.archivedOriginalV2(archive, ref, 4, 2, Vectors.game(), new Obj(Map.of()));
        var rows = imported.completeSurvivingBranch();
        assertEquals(1, DriverSurvivingHistory.afterLatestRestore(rows).size());
        assertFalse(rows.stream().anyMatch(row -> row.command().equals("move-army-1-to-99")));
        assertTrue(RouteContactProofs.oneDayEntries(Vectors.frame(),
                RouteContactHistoryAdapter.queries(DriverSurvivingHistory.afterLatestRestore(rows), Vectors.frame()),
                RouteContactHistoryAdapter.timeline(rows)).isEmpty(), "surviving strict failure must prohibit a third day");
    }

    @Test void sameBytesReplacementAndMissingLookupCannotBecomeAnEmptySuccessfulHistory() throws Exception {
        NativeOutcomeArchive archive = archive(temporary.resolve("writer"));
        byte[] original = Vectors.driver(List.of(Vectors.row(1, "query", false, "null"))).encode();
        assertThrows(UncheckedIOException.class, () -> archive.materialReferenceOf(new RawJson(original)));
        var ref = archive.preserveMaterial(new RawJson(original));
        Path replacement = temporary.resolve("same-bytes-replacement.bin"); Files.write(replacement, original);
        Files.move(replacement, Path.of(ref.path()), StandardCopyOption.REPLACE_EXISTING);
        assertThrows(UncheckedIOException.class, () -> DriverHistoryImport.archivedOriginalV2(
                archive, ref, 1, 1, Vectors.game(), new Obj(Map.of())));
    }

    private static NativeOutcomeArchive archive(Path root) throws IOException {
        Files.createDirectory(root);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        byte[] state = ContinuityJson.canonical(state()); Files.write(snapshot, state); Files.write(anchor, state);
        Path lock = root.resolve("ROOT-CONTINUITY-WINDOW.lock"); Files.createFile(lock);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path source = root.resolve("reviewed-source.txt"); Files.writeString(source, "synthetic history archive fixture source");
        Layout layout = new Layout(snapshot, LedgerFiles.read(anchor, 65_536).pin().reference(), "xenoamess-full-tower-eb9d2c1186");
        Path artifactsRoot = root.resolve("artifacts"); Files.createDirectory(artifactsRoot);
        var storage = StorageWriteGuardTestSupport.create(layout); ImmutableArtifactStore artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactsRoot, lock, 1_048_576), storage);
        ContinuityWriter writer = new ContinuityWriter(layout, List.of(LedgerFiles.read(source, 65_536).pin().reference()), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor, Request request) { return ContinuityJson.digest(request.detailsObject()); }
            @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { return OriginalWindowReducer.reduce(predecessor, request); }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
        return new NativeOutcomeArchive(artifacts, writer);
    }

    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1");
        row.put("machine_id", "xenoamess-full-tower-eb9d2c1186"); row.put("sequence", 0); row.put("window_id", 1);
        row.put("status", "running"); row.put("target_days", 10_958); row.put("target_years", 30); row.put("calendar_year_days", 365.25);
        row.put("start_date_raw", 1000); row.put("target_date_raw", 1000 + 10_958 * 24); row.put("last_settled_date_raw", 1000);
        row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1); row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        ObjectNode game = row.putObject("game_binding"); game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z");
        row.putNull("latest_binding"); ObjectNode pending = row.putObject("pending_cycle"); pending.put("stage", "auto_unsettled");
        pending.put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }

    /** Local-service test vectors; no dependency on application test artifacts. */
    private static final class Vectors {
        private static final String QUERY = "query-route-contact-horizon-v1-1-to-10-h-1-2";
        private static final String ADVANCE = "advance-route-contact-horizon-v1-1-to-10-h-1-2";
        private static Obj json(String value) {
            return org.xar.ck3.control.application.driver.DriverJson.object(value.getBytes(java.nio.charset.StandardCharsets.UTF_8), 1_048_576);
        }
        private static Obj row(int index, String command, boolean ok, String result) {
            return json("{\"index\":" + index + ",\"command\":\"" + command + "\",\"ok\":" + ok
                    + (result == null ? "" : ",\"result\":" + result) + "}");
        }
        private static String encoded(Obj value) {
            return new String(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(value), java.nio.charset.StandardCharsets.UTF_8);
        }
        private static Obj checkpoint(int index) {
            return json("{\"history_index\":" + index + ",\"sha256\":\"" + "a".repeat(64) + "\",\"size\":4096,\"date_raw\":100}");
        }
        private static Obj anchor(int index) { return row(index, "save-checkpoint", true, "{\"checkpoint\":" + encoded(checkpoint(index)) + "}"); }
        private static String result(Obj checkpoint, String source, int previous, int pid) {
            return "{\"step\":\"restore-checkpoint\",\"accepted\":true,\"status\":\"restored\",\"backend_id\":\"native-headless\",\"source\":\""
                    + source + "\",\"restored_date_raw\":100,\"map_ready\":true,\"checkpoint\":" + encoded(checkpoint)
                    + ",\"lifecycle\":{\"previous_pid\":" + previous + ",\"pid\":" + pid + "}}";
        }
        private static org.xar.ck3.control.contracts.GameGeneration game() {
            return new org.xar.ck3.control.contracts.GameGeneration(9,
                    new org.xar.ck3.control.contracts.PythonOnlyUInt64(new java.math.BigInteger("134373229053165471")));
        }
        private static org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete driver(List<Obj> rows) {
            return org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(
                    ("{\"format_version\":2,\"pipe_name\":\"pipe\",\"bridge_pid\":9,\"episode_character_id\":1,\"episode_run_id\":\"ep\","
                    + "\"command_history\":[" + rows.stream().map(Vectors::encoded).collect(java.util.stream.Collectors.joining(",")) + "],"
                    + "\"last_checkpoint\":null,\"rollback_war_failure\":null,\"managed_restore_transaction\":null,"
                    + "\"succession_expectation\":null,\"campaign_goal\":null}").getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        private static org.xar.ck3.control.application.routecontact.RouteContactModel.Frame frame() {
            var owner = new org.xar.ck3.control.application.routecontact.RouteContactModel.Owner(
                    "machine", game(), "session", java.math.BigInteger.ONE, 9, "ep", 1, 0);
            var own = new org.xar.ck3.control.application.routecontact.RouteContactModel.Army(
                    1, true, 10, Optional.empty(), List.of(), Optional.of("regular"), Optional.of(1), false, false);
            var hostile = new org.xar.ck3.control.application.routecontact.RouteContactModel.Army(
                    2, false, 20, Optional.of(10), List.of(10), Optional.of("moving"), Optional.of(4), false, false);
            return new org.xar.ck3.control.application.routecontact.RouteContactModel.Frame(owner, "snap",
                    java.math.BigInteger.valueOf(3), java.math.BigInteger.valueOf(7), 100, true, true, 1, false, true,
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE, List.of(4), List.of(own), List.of(hostile));
        }
        private static String queryResult() {
            return """
                    {"queried_snapshot_id":"snap","queried_revision":3,"queried_native_revision":7,"queried_connection_generation":1,"queried_episode_run_id":"ep",
                     "route_contact_horizon":{"status":"available","date_raw":100,"snapshot_revision":7,"subject_army_id":1,"target_province_id":10,
                      "hostile_army_ids":[2],"horizon_start_date_raw":100,"horizon_end_date_raw":124,"one_day_contact_free":false,
                      "subject_route":{"timeline_observable":true,"army_id":1,"current_province_id":10,"effective_origin_province_id":10,"route_province_ids":[],"arrival_date_raws":[]},
                      "hostile_routes":[{"timeline_observable":true,"army_id":2,"current_province_id":20,"effective_origin_province_id":20,"route_province_ids":[10],"arrival_date_raws":[100]}],
                      "conflicts":[{"kind":"same_province","hostile_army_id":2,"province_id":10,"overlap_start_date_raw":100,"overlap_end_date_raw":124}]}}
                    """;
        }
        private static String strictFailure() {
            return """
                    {"ending_date_raw":100,"contact_followup":{"status":"exhausted_without_strong_transition","episode_run_id":"ep",
                     "subject_army_id":1,"contact_province_id":10,"starting_date_raw":76,"ending_date_raw":100}}
                    """;
        }
    }
}
