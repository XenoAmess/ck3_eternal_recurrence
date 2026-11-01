package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic pure DATA only: no private Admission, filesystem, Game or native authorization. */
public final class SavedContinuityBootstrap249Test {
    private static final String MACHINE = "test-machine";
    private static final long DATE = 2656; // original1000 +69days*24
    private static final String SHA = "a".repeat(64);
    private record Fixture(ContinuityState before, SavedContinuityBootstrap.Input input) { }
    private static ExactRef ref(String path, long bytes) { return new ExactRef(path, bytes, SHA); }
    private static ExactRef stateRef(String path, ContinuityState state) {
        return new ExactRef(path, state.canonicalBytes().length, ContinuityJson.digest(state.toJson()));
    }
    private static GameGeneration game(long pid, String birth) {
        var row = StrictJson.object(); row.put("pid", pid); row.put("creation_filetime", birth);
        return GameGeneration.fromJson(row);
    }
    private static GameGeneration oldGame() { return game(100, "100000000000000000"); }
    private static GameGeneration newGame() { return game(200, "200000000000000000"); }
    private static ObjectNode observation(GameGeneration game, long date, int player, String episode) {
        var row = StrictJson.object(); row.put("machine_id", MACHINE); row.set("game", game.toJson()); row.put("observation_version", 1);
        var frame = row.putObject("frame"); frame.put("played_character_id", Integer.toString(player));
        frame.put("native_revision", "3"); frame.put("date_raw", Long.toString(date)); frame.put("snapshot_id", "snapshot-new");
        frame.put("revision", "7"); frame.put("episode_run_id", episode); return row;
    }
    private static ObjectNode binding(long date, String episode) {
        var row = StrictJson.object(); row.put("date_raw", date); row.put("actor_character_id", 31254);
        row.put("native_revision", 3); row.put("revision", 7); row.put("snapshot_id", "snapshot-new"); row.put("episode_run_id", episode); return row;
    }
    private static ObjectNode witness(String path) {
        var row = StrictJson.object(); row.set("ref", ref(path, 100).toJson()); row.put("identity_schema", FileStatIdentity.SCHEMA);
        var identity = row.putObject("identity"); identity.put("bytes", 100); identity.put("file_id", "123"); identity.put("mtime_ns", "1234567890"); return row;
    }
    private static ObjectNode pair() {
        var row = StrictJson.object(); row.put("schema", "xar.java-checkpoint-pair/v1");
        row.set("save", witness("saved-game")); row.set("driver", witness("saved-driver"));
        row.set("frame", observation(oldGame(), DATE, 31254, "old-episode"));
        row.put("lineage_id", "lineage"); row.put("history_index", 12); row.put("save_action_id", "original-save");
        row.set("native_ack_ref", ref("original-ack", 32).toJson()); row.put("observed_at_utc", "2026-11-01T00:00:00Z"); return row;
    }
    private static Fixture fixture() {
        var saved = StrictJson.object(); saved.put("schema", "root.ck3.continuity-window/v1"); saved.put("machine_id", MACHINE);
        saved.put("sequence", 788); saved.put("window_id", 1); saved.put("status", "running");
        saved.put("start_date_raw", 1000); saved.put("target_date_raw", 3400); saved.put("target_days", 100);
        saved.put("last_settled_cycles", 12); saved.put("last_settled_date_raw", DATE);
        saved.put("manual_repair_count", 0); saved.put("automatic_recovery_count", 0); saved.put("binding_lineage_count", 0);
        saved.set("game_binding", oldGame().toJson()); saved.set("latest_binding", binding(DATE, "old-episode"));
        var cycle = saved.putObject(WriterContracts.ORDINARY_CYCLE_FIELD); cycle.put("completed_cycles", 12);
        cycle.putNull("pending_receipt"); cycle.set("head", ref("original-cycle", 32).toJson());
        var slot = saved.putObject(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD); slot.set("pair", pair()); slot.set("state", cycle.deepCopy());
        var savedState = ContinuityState.fromJson(saved, MACHINE);
        var head = saved.deepCopy(); head.put("sequence", 843); head.put("status", "repair_required");
        ((ObjectNode)head.get(WriterContracts.ORDINARY_CYCLE_FIELD)).put("completed_cycles", 13);
        head.set("latest_binding", binding(2944, "old-episode")); head.put("old_action_never_import", "already-applied");
        var headState = ContinuityState.fromJson(head, MACHINE);
        var session = StrictJson.object(); session.put("machine_id", MACHINE); session.set("game", newGame().toJson()); session.put("session_id", "new-session");
        var input = new SavedContinuityBootstrap.Input(savedState, stateRef("archived-saved-state", savedState), ref("original-confirmation", 32),
                headState, stateRef("archived-source-head", headState), ContinuityJson.canonical(pair()), ContinuityJson.canonical(session),
                ContinuityJson.canonical(observation(newGame(), DATE, 31254, "new-episode")), ref("new-driver", 100), ref("new-facts", 100), 0, 0);
        var before = FreshContinuityGenesis.initial(new FreshContinuityGenesis.Plan(MACHINE, 1, 100), ref("fresh-plan", 100));
        return new Fixture(before, input);
    }
    private static WriterContracts.Request request(Fixture fixture) {
        return SavedContinuityBootstrap.request(fixture.input(), "saved-entry", StrictJson.object().put("source", "pure-test"));
    }
    private static SavedContinuityBootstrap.Input copy(SavedContinuityBootstrap.Input value, ExactRef savedRef,
            ContinuityState head, ExactRef headRef, byte[] pair, byte[] session, byte[] opening) {
        return new SavedContinuityBootstrap.Input(value.savedState(), savedRef, value.confirmationReference(), head, headRef,
                pair, session, opening, value.fullDriver(), value.driverFacts(), value.driverVersion(), value.episodeEpoch());
    }
    private static ObjectNode expected(Fixture f, WriterContracts.Request request) {
        var next = f.before().toJson(); next.put("schema", "root.ck3.continuity-window/v1"); next.put("window_id", 1);
        next.put("status", "running"); next.put("start_date_raw", 1000); next.put("target_date_raw", 3400); next.put("target_days", 100);
        next.put("last_settled_cycles", 12); next.put("last_settled_date_raw", DATE); next.set("game_binding", newGame().toJson());
        next.set("latest_binding", binding(DATE, "new-episode")); next.set(SavedContinuityBootstrap.FIELD, request.detailsObject());
        next.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD, f.input().fullDriver().toJson()); return next;
    }
    private static void rejected(Runnable action) { assertThrows(ContractViolationException.class, action::run); }

    @Test void importsSavedBasisWithoutDirtyBranchOrNewCredit() {
        var f = fixture(); var request = request(f); var after = SavedContinuityBootstrap.reduce(f.before(), request);
        assertTrue(ContinuityJson.same(expected(f, request), after.toJson()));
        assertEquals(12, after.settledCycles()); assertEquals(DATE, after.settledDateRaw()); assertEquals(0, after.sequence());
        assertEquals(1000, after.origin().startDateRaw()); assertEquals(3400, after.origin().targetDateRaw());
        assertEquals(0, request.detailsObject().get("driver_version").longValue()); assertEquals(0, request.detailsObject().get("episode_epoch").longValue());
        assertEquals(List.of(f.input().savedStateReference(), f.input().confirmationReference(), f.input().sourceHeadReference(),
                f.input().fullDriver(), f.input().driverFacts()), request.evidence());
        for (String key : List.of(WriterContracts.ORDINARY_CYCLE_FIELD, WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,
                WriterContracts.GAMEPLAY_ENTRY_FIELD, WriterContracts.DRIVER_ACTION_HISTORY_FIELD, "origin_frame", "old_action_never_import"))
            assertFalse(after.toJson().has(key), key);
    }
    @Test void callerAndAccessorArraysCannotChangeInput() {
        var original = fixture().input(); byte[] pair = original.checkpointPair(), session = original.session(), opening = original.opening();
        var input = copy(original, original.savedStateReference(), original.sourceHead(), original.sourceHeadReference(), pair, session, opening);
        pair[0] = '!'; session[0] = '!'; opening[0] = '!';
        byte[] a = input.checkpointPair(), b = input.session(), c = input.opening(); a[0] = '?'; b[0] = '?'; c[0] = '?';
        assertArrayEquals(original.checkpointPair(), input.checkpointPair()); assertArrayEquals(original.session(), input.session());
        assertArrayEquals(original.opening(), input.opening());
    }
    @Test void fullSourceHashesAndSurvivingSavedSlotAreBound() {
        var f = fixture(); var input = f.input();
        rejected(() -> SavedContinuityBootstrap.request(copy(input, ref("wrong-saved", 1), input.sourceHead(), input.sourceHeadReference(),
                input.checkpointPair(), input.session(), input.opening()), "test", StrictJson.object().put("source", "test")));
        rejected(() -> SavedContinuityBootstrap.request(copy(input, input.savedStateReference(), input.sourceHead(), ref("wrong-head", 1),
                input.checkpointPair(), input.session(), input.opening()), "test", StrictJson.object().put("source", "test")));
        var changed = input.sourceHead().toJson();
        ((ObjectNode)changed.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD).get("pair")).put("lineage_id", "foreign-lineage");
        var head = ContinuityState.fromJson(changed, MACHINE);
        rejected(() -> SavedContinuityBootstrap.request(copy(input, input.savedStateReference(), head, stateRef("changed-head", head),
                input.checkpointPair(), input.session(), input.opening()), "test", StrictJson.object().put("source", "test")));
    }
    @Test void openingRejectsOldBirthForeignMachineActorAndDate() {
        var details = request(fixture()).detailsObject();
        for (String fault : List.of("birth", "machine", "actor", "date")) {
            var changed = details.deepCopy(); var opening = (ObjectNode)changed.get("opening"); var frame = (ObjectNode)opening.get("frame");
            switch (fault) {
                case "birth" -> { opening.set("game", oldGame().toJson()); ((ObjectNode)changed.get("session")).set("game", oldGame().toJson()); }
                case "machine" -> { opening.put("machine_id", "foreign"); ((ObjectNode)changed.get("session")).put("machine_id", "foreign"); }
                case "actor" -> frame.put("played_character_id", "31255");
                case "date" -> frame.put("date_raw", "2680");
                default -> throw new AssertionError(fault);
            }
            rejected(() -> SavedContinuityBootstrap.request(changed));
        }
    }
    @Test void onlyExactFreshPredecessorAndPolicyCanInitialize() {
        var f = fixture(); var request = request(f); var hidden = f.before().toJson(); hidden.put("hidden_action", "unresolved");
        var hiddenState = ContinuityState.fromJson(hidden, MACHINE);
        rejected(() -> SavedContinuityBootstrap.reduce(hiddenState, request));
        var initialized = SavedContinuityBootstrap.reduce(f.before(), request);
        rejected(() -> SavedContinuityBootstrap.reduce(initialized, request));
        rejected(() -> SavedContinuityBootstrap.requireSavedAdmissionReduction(initialized, initialized, request, false));
        for (var plan : List.of(new FreshContinuityGenesis.Plan(MACHINE, 2, 100), new FreshContinuityGenesis.Plan(MACHINE, 1, 101))) {
            var mismatch = FreshContinuityGenesis.initial(plan, ref("other-plan", 100));
            rejected(() -> SavedContinuityBootstrap.reduce(mismatch, request));
        }
    }
    @Test void finiteDetailsClosedFieldsAndEvidenceCannotBeBypassed() {
        var f = fixture(); var request = request(f); var unknown = request.detailsObject(); unknown.put("unknown", 1);
        rejected(() -> SavedContinuityBootstrap.request(unknown));
        var badDecimal = request.detailsObject(); ((ObjectNode)badDecimal.get("opening").get("frame")).put("date_raw", "02656");
        rejected(() -> SavedContinuityBootstrap.request(badDecimal));
        var oversized = StrictJson.object(); oversized.put("one", "x".repeat(30000)); oversized.put("two", "x".repeat(30000)); oversized.put("three", "x".repeat(30000));
        rejected(() -> SavedContinuityBootstrap.request(f.input(), "test", oversized));
        var reordered = new ArrayList<>(request.evidence()); Collections.reverse(reordered);
        var wrong = new WriterContracts.Request(request.kind(), request.details(), reordered);
        rejected(() -> SavedContinuityBootstrap.reduce(f.before(), wrong));
        var extra = new ArrayList<>(request.evidence()); extra.add(ref("unrelated", 1));
        var unrelated = new WriterContracts.Request(request.kind(), request.details(), extra);
        rejected(() -> SavedContinuityBootstrap.reduce(f.before(), unrelated));
    }
    @Test void entireUnsequencedAndSequencedDerivedStateIsRequired() {
        var f = fixture(); var request = request(f); var literal = expected(f, request);
        SavedContinuityBootstrap.requireSavedAdmissionReduction(f.before(), ContinuityState.fromJson(literal, MACHINE), request, false);
        literal.put("sequence", 1); literal.put("last_event_identity", request.identity());
        SavedContinuityBootstrap.requireSavedAdmissionReduction(f.before(), ContinuityState.fromJson(literal, MACHINE), request, true);
        for (String fault : List.of("sequence", "counter", "action")) {
            var changed = literal.deepCopy();
            switch (fault) { case "sequence" -> changed.put("sequence", 2); case "counter" -> changed.put("manual_repair_count", 1);
                case "action" -> changed.put("old_action_never_import", "applied"); default -> throw new AssertionError(fault); }
            var after = ContinuityState.fromJson(changed, MACHINE);
            rejected(() -> SavedContinuityBootstrap.requireSavedAdmissionReduction(f.before(), after, request, true));
        }
    }
    @Test void historicalEventUsesSameStrictReductionWithoutLiveAuthority() {
        var f = fixture(); var request = request(f); var literal = expected(f, request); literal.put("sequence", 1); literal.put("last_event_identity", request.identity());
        var after = ContinuityState.fromJson(literal, MACHINE);
        var event = new ContinuityEvent(1, "2026-11-01T00:00:00Z", SavedContinuityBootstrap.KIND, request.details(), request.identity(),
                ContinuityJson.digest(f.before().toJson()), after);
        var restored = ContinuityEvent.fromJson(event.toJson(), f.before());
        assertTrue(ContinuityJson.same(literal, restored.after().toJson()));
        var changed = event.toJson(); ((ObjectNode)changed.get("after")).put("old_action_never_import", "applied");
        rejected(() -> ContinuityEvent.fromJson(changed, f.before()));
        var wrongPredecessor = f.input().sourceHead();
        rejected(() -> ContinuityEvent.fromJson(event.toJson(), wrongPredecessor));
    }
}
