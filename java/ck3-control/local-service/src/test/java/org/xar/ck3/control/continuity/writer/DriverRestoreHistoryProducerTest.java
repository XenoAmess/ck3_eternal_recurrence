package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverHistoryImport;
import org.xar.ck3.control.application.history.DriverRestoreHistoryProducer;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Exercises real archive lookup/identity failures and the production completed Driver producer. */
class DriverRestoreHistoryProducerTest {
    @TempDir Path temporary;
    private static final String REQUEST = "restore-source-bound-request";

    @Test void actualArchiveCompletionFeedsFullDriverImportAndRetainsEverySavedUnknownField() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var saved = saved();
        var staged = staged(List.of(unknown(), anchor(), cold(3, 6, 7), abandoned(4), cold(5, 7, 9)), "ep", 1);
        ExactRef stagedRef = preserve(archive, staged.encode());
        ExactRef completedRef = preserve(archive, OpportunityJson.encode(completed(6, REQUEST, 7, 9)));
        var candidate = DriverRestoreHistoryProducer.prepare(archive, saved, stagedRef, completedRef, binding());
        assertEquals(stagedRef, candidate.stagedDriverEvidence()); assertEquals(completedRef, candidate.completedRowEvidence());
        assertEquals(binding(), candidate.binding());
        var rows = DriverSurvivingHistory.rows(candidate.driver());
        assertEquals(4, rows.size()); assertEquals(unknown(), rows.getFirst());
        assertEquals(7, OpportunityJson.integer(OpportunityJson.object(OpportunityJson.object(rows.get(2).get("result"), "result").get("lifecycle"), "lifecycle").get("pid"), "pid").intValueExact());
        assertFalse(rows.stream().anyMatch(row -> OpportunityJson.text(row.get("command"), "command").equals("move-army-1-to-99")));
        assertEquals(REQUEST, OpportunityJson.text(OpportunityJson.object(OpportunityJson.object(rows.getLast().get("result"), "result").get("lifecycle"), "lifecycle").get("request_id"), "request"));
        assertInstanceOf(DriverStateSnapshot.NullValue.class, candidate.driver().managedRestoreTransaction());
        assertTrue(DriverJson.same(staged.rollbackWarFailure(), candidate.driver().rollbackWarFailure()));
        assertTrue(DriverJson.same(staged.rollbackWarFailures(), candidate.driver().rollbackWarFailures()));
        assertTrue(DriverJson.same(staged.campaignGoal(), candidate.driver().campaignGoal()));
        assertInstanceOf(DriverStateSnapshot.Missing.class, candidate.driver().successionLifecycle());
        var imported = DriverHistoryImport.archivedOriginalV2(archive, candidate.driverEvidence(), 5, 2, newGame(), new Obj(java.util.Map.of()));
        assertArrayEquals(candidate.driver().encode(), imported.facts().driver().encode());
        assertTrue(DriverSurvivingHistory.afterLatestRestore(imported.completeSurvivingBranch()).isEmpty());
    }

    @Test void publicationRecoveryWithTheSameArchivedCompletionDoesNotAppendAnotherRestart() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var stagedRef = preserve(archive, staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "ep", 1).encode());
        var completedRef = preserve(archive, OpportunityJson.encode(completed(4, REQUEST, 7, 9)));
        var first = DriverRestoreHistoryProducer.prepare(archive, saved(), stagedRef, completedRef, binding());
        var recovered = DriverRestoreHistoryProducer.prepare(archive, saved(), first.driverEvidence(), completedRef, binding());
        assertEquals(first.driverEvidence(), recovered.driverEvidence());
        assertArrayEquals(first.driver().encode(), recovered.driver().encode());
        assertEquals(3, recovered.driver().commandHistory().size());
    }

    @Test void missingOrSameBytesReplacedCompletionCannotProduceAFullAdoptionCandidate() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var stagedRef = preserve(archive, staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "ep", 1).encode());
        byte[] completion = OpportunityJson.encode(completed(4, REQUEST, 7, 9));
        assertThrows(UncheckedIOException.class, () -> archive.materialReferenceOf(new RawJson(completion)));
        var completedRef = preserve(archive, completion);
        Path replacement = temporary.resolve("replacement-completion.bin"); Files.write(replacement, completion);
        Files.move(replacement, Path.of(completedRef.path()), StandardCopyOption.REPLACE_EXISTING);
        assertThrows(UncheckedIOException.class, () -> DriverRestoreHistoryProducer.prepare(archive, saved(), stagedRef, completedRef, binding()));
    }

    @Test void changedSavedPrefixAndInventedEpisodeOrActorAreRejectedBeforeFinalPublication() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var completedRef = preserve(archive, OpportunityJson.encode(completed(4, REQUEST, 7, 9)));
        for (var staged : List.of(
                staged(List.of(json("{\"index\":1,\"command\":\"unknown-original\",\"ok\":false,\"result\":{},\"error\":\"real failure\"}"), anchor(), cold(3, 7, 9)), "ep", 1),
                staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "invented-episode", 1),
                staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "ep", 2))) {
            var stagedRef = preserve(archive, staged.encode());
            assertThrows(IllegalArgumentException.class, () -> DriverRestoreHistoryProducer.prepare(archive, saved(), stagedRef, completedRef, binding()));
        }
        var valid = preserve(archive, staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "ep", 1).encode());
        var wrongDate = new DriverRestoreHistoryProducer.Binding(REQUEST, oldGame(), newGame(), session(), BigInteger.valueOf(124));
        assertThrows(IllegalArgumentException.class, () -> DriverRestoreHistoryProducer.prepare(archive, saved(), valid, completedRef, wrongDate));
    }

    @Test void wrongRequestOrPhysicalProcessAndBooleanPidNeverBecomeActualCompletion() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var stagedRef = preserve(archive, staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "ep", 1).encode());
        for (Obj row : List.of(completed(4, "other-request", 7, 9), completed(4, REQUEST, 6, 9), cold(4, 7, 9),
                json(encoded(completed(4, REQUEST, 7, 9)).replace("\"paused\":true", "\"paused\":false")),
                json(encoded(completed(4, REQUEST, 7, 9)).replace("\"episode_character_id\":1", "\"episode_character_id\":2")),
                json(encoded(completed(4, REQUEST, 7, 9)).replace("\"previous_pid\":7", "\"previous_pid\":true")))) {
            var rowRef = preserve(archive, OpportunityJson.encode(row));
            assertThrows(IllegalArgumentException.class, () -> DriverRestoreHistoryProducer.prepare(archive, saved(), stagedRef, rowRef, binding()));
        }
        assertThrows(IllegalArgumentException.class, () -> new DriverRestoreHistoryProducer.Binding(REQUEST, oldGame(), oldGame(), session(), BigInteger.valueOf(100)));
    }

    @Test void conflictingCompletionForTheSamePhysicalReplacementCannotBeSilentlyReplaced() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var stagedRef = preserve(archive, staged(List.of(unknown(), anchor(), completed(3, REQUEST, 7, 9)), "ep", 1).encode());
        var changed = json(encoded(completed(4, REQUEST, 7, 9)).replace("\"native-extra\":null", "\"native-extra\":[]"));
        var completion = preserve(archive, OpportunityJson.encode(changed));
        assertThrows(IllegalArgumentException.class, () -> DriverRestoreHistoryProducer.prepare(archive, saved(), stagedRef, completion, binding()));
    }

    @Test void goalSerializationOrderDoesNotHideMissingNullOrChangedContent() throws Exception {
        var archive = archive(temporary.resolve("writer"));
        var staged = staged(List.of(unknown(), anchor(), cold(3, 7, 9)), "ep", 1);
        var completion = preserve(archive, OpportunityJson.encode(completed(4, REQUEST, 7, 9)));
        for (String value : List.of("{\"calendar\":[],\"goal\":null}", "{\"goal\":[],\"calendar\":[]}")) {
            var encodedGoal = new DriverStateSnapshot.Value(value.getBytes(StandardCharsets.UTF_8));
            var altered = new DriverStateSnapshot.Complete(staged.session(), staged.commandHistory(), staged.lastCheckpoint(), staged.rollbackWarFailure(),
                    staged.managedRestoreTransaction(), staged.successionExpectation(), staged.successionLifecycle(),
                    encodedGoal, staged.rollbackWarFailures());
            var ref = preserve(archive, altered.encode());
            if (value.contains("\"goal\":null")) {
                var result = DriverRestoreHistoryProducer.prepare(archive, saved(), ref, completion, binding());
                assertEquals(OpportunityJson.parse(encodedGoal.json()),
                        OpportunityJson.parse(assertInstanceOf(DriverStateSnapshot.Value.class, result.driver().campaignGoal()).json()));
            } else assertThrows(IllegalArgumentException.class, () -> DriverRestoreHistoryProducer.prepare(archive, saved(), ref, completion, binding()));
        }
    }

    private static NativeOutcomeArchive archive(Path root) throws IOException {
        Files.createDirectory(root);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        byte[] state = ContinuityJson.canonical(state()); Files.write(snapshot, state); Files.write(anchor, state);
        Path lock = root.resolve("ROOT-CONTINUITY-WINDOW.lock"); Files.createFile(lock);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path source = root.resolve("reviewed-source.txt"); Files.writeString(source, "synthetic source-bound restore regression fixture");
        Layout layout = new Layout(snapshot, LedgerFiles.read(anchor, 65_536).pin().reference(), "xenoamess-full-tower-eb9d2c1186");
        Path artifactsRoot = root.resolve("artifacts"); Files.createDirectory(artifactsRoot);
        var storage = StorageWriteGuardTestSupport.create(layout); ImmutableArtifactStore artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactsRoot, lock, 1_048_576), storage);
        var writer = new ContinuityWriter(layout, List.of(LedgerFiles.read(source, 65_536).pin().reference()), new TransitionAuthority() {
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
    private static ExactRef preserve(NativeOutcomeArchive archive, byte[] bytes) { return archive.preserveMaterial(new RawJson(bytes)); }
    private static Obj json(String raw) { return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES); }
    private static String encoded(Obj row) { return new String(OpportunityJson.encode(row), StandardCharsets.UTF_8); }
    private static Obj unknown() { return json("{\"index\":1,\"command\":\"unknown-original\",\"ok\":false,\"result\":null,\"error\":\"real failure\",\"unmigrated_extension\":[null,[],{}]}"); }
    private static Obj checkpoint() { return json("{\"history_index\":2,\"sha256\":\"" + "a".repeat(64) + "\",\"size\":4096,\"date_raw\":100,\"episode_character_id\":1,\"episode_run_id\":\"ep\"}"); }
    private static Obj anchor() { return json("{\"index\":2,\"command\":\"save-checkpoint\",\"ok\":true,\"result\":{\"checkpoint\":" + encoded(checkpoint()) + "}}"); }
    private static Obj abandoned(int index) { return json("{\"index\":" + index + ",\"command\":\"move-army-1-to-99\",\"ok\":true,\"result\":{}}"); }
    private static Obj cold(int index, long previous, long pid) { return restore(index, "native-session-cold-start", "provisional", previous, pid); }
    private static Obj completed(int index, String request, long previous, long pid) { return restore(index, "native-session-lifecycle-queue", request, previous, pid); }
    private static Obj restore(int index, String source, String request, long previous, long pid) {
        return json("{\"index\":" + index + ",\"command\":\"restore-checkpoint\",\"ok\":true,\"result\":{\"step\":\"restore-checkpoint\",\"accepted\":true,\"status\":\"restored\",\"backend_id\":\"native-headless\",\"source\":\"" + source
                + "\",\"restored_date_raw\":100,\"map_ready\":true,\"paused\":true,\"native-extra\":null,\"checkpoint\":" + encoded(checkpoint())
                + ",\"lifecycle\":{\"request_id\":\"" + request + "\",\"previous_pid\":" + previous + ",\"pid\":" + pid + "}}}");
    }
    private static DriverStateSnapshot.Complete saved() {
        return driver(new DriverStateSnapshot.Session("old-pipe", 7, BigInteger.ONE, "ep"), List.of(unknown(), anchor()), new DriverStateSnapshot.NullValue());
    }
    private static DriverStateSnapshot.Complete staged(List<Obj> rows, String episode, long actor) {
        return driver(new DriverStateSnapshot.Session("replacement-pipe", 9, BigInteger.valueOf(actor), episode), rows,
                new DriverStateSnapshot.Value("{\"request_id\":\"restore-source-bound-request\",\"status\":\"pending\"}".getBytes(StandardCharsets.UTF_8)));
    }
    private static DriverStateSnapshot.Complete driver(DriverStateSnapshot.Session session, List<Obj> rows, DriverStateSnapshot.Slot managed) {
        var history = rows.stream().map(row -> new DriverStateSnapshot.HistoryEntry(OpportunityJson.integer(row.get("index"), "index").longValueExact(), new DriverStateSnapshot.Value(OpportunityJson.encode(row)))).toList();
        return new DriverStateSnapshot.Complete(session, history, new DriverStateSnapshot.Value(OpportunityJson.encode(checkpoint())),
                new DriverStateSnapshot.NullValue(), managed, new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.Missing(),
                new DriverStateSnapshot.Value("{\"goal\":null,\"calendar\":[]}".getBytes(StandardCharsets.UTF_8)), new DriverStateSnapshot.Value("[]".getBytes(StandardCharsets.UTF_8)));
    }
    private static DriverStateSnapshot.Session session() { return new DriverStateSnapshot.Session("replacement-pipe", 9, BigInteger.ONE, "ep"); }
    private static GameGeneration oldGame() { return new GameGeneration(7, new PythonOnlyUInt64(new BigInteger("134373229053165471"))); }
    private static GameGeneration newGame() { return new GameGeneration(9, new PythonOnlyUInt64(new BigInteger("134373229053165472"))); }
    private static DriverRestoreHistoryProducer.Binding binding() { return new DriverRestoreHistoryProducer.Binding(REQUEST, oldGame(), newGame(), session(), BigInteger.valueOf(100)); }
}
