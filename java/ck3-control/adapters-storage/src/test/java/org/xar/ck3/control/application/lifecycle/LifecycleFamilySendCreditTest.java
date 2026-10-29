package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import static org.junit.jupiter.api.Assertions.*;

/** Exercises the actual episode reducer's history consumer; these fixture rows grant no native send authority. */
final class LifecycleFamilySendCreditTest {
    @TempDir Path temporary;

    @Test void sendOnlyHistoryCannotCreateRelationshipAchievementDirectlyOrThroughAutoRunExpansion() throws Exception {
        for (boolean wrapped : List.of(false, true)) {
            Path root = temporary.resolve(wrapped ? "wrapped" : "direct"); java.nio.file.Files.createDirectories(root);
            ObjectNode send = send(); ObjectNode row = wrapped ? wrap(send) : send;
            ObjectNode result = reduce(root, List.of(row));
            var accepted = result.path("cross_run_strategy").path("recorded_episode").path("achievements")
                    .path("danish_betrothal_accepted");
            assertTrue(accepted.isBoolean(), "the actual reducer must retain the explicit achievement field");
            assertFalse(accepted.booleanValue());
            assertTrue(result.path("continue_as_heir_after_death").isBoolean());
            assertFalse(result.path("continue_as_heir_after_death").booleanValue());
            assertTrue(result.path("heir_gameplay_actions").isIntegralNumber());
            assertEquals(0, result.path("heir_gameplay_actions").intValue());
        }
    }

    @Test void explicitRelationshipHistoryRemainsSeparateAndLaterSendCannotEraseIt() throws Exception {
        ObjectNode accepted = LifecycleJson.row().put("command", "arrange-marriage-7-8").put("ok", true);
        accepted.putObject("result").putObject("marriage_result").put("status", "accepted_betrothal")
                .put("source", "native_relationship_snapshot").put("candidate_character_id", 8);
        ObjectNode result = reduce(temporary, List.of(accepted, send()));
        assertTrue(result.path("cross_run_strategy").path("recorded_episode").path("achievements")
                .path("danish_betrothal_accepted").booleanValue());
        LifecycleJson.object(result.get("cross_run_strategy"));
    }

    private static ObjectNode send() {
        ObjectNode row = LifecycleJson.row().put("command", "arrange-marriage-7-8").put("ok", true);
        ObjectNode result = row.putObject("result").put("status", "send_confirmed").put("outcome", "SEND_CONFIRMED")
                .put("outbound_request_effect_observed", true).put("native_pending_full_id", 0)
                .put("subject_full_id", 7).put("candidate_full_id", 8).put("marriage_relation_verified", false)
                .put("alliance_verified", false).put("fees_verified", false).put("native.gameplay_verified", false)
                .put("timeline.advance_verified", false).put("timeline.checkpoint_eligible", false);
        result.putObject("marriage_result").put("status", "outbound_request_observed")
                .put("source", "native_outgoing_request_storage").put("candidate_character_id", 8);
        return row;
    }
    private static ObjectNode wrap(ObjectNode actual) {
        ObjectNode turn = LifecycleJson.row().put("command", "auto-turn").put("ok", true);
        ObjectNode turnResult = turn.putObject("result");
        turnResult.setAll(LifecycleJson.object(actual.get("result")));
        turnResult.putObject("auto_turn").put("selected_step", "arrange-marriage-7-8");
        ObjectNode outer = LifecycleJson.row().put("command", "auto-run 1").put("ok", true);
        outer.putObject("result").putArray("turns").add(turn); return outer;
    }
    private static ObjectNode reduce(Path root, List<ObjectNode> rows) throws Exception {
        var fixture = new LifecycleBusinessFixture(root); var original = fixture.snapshot.facts(); var old = original.driver();
        List<DriverStateSnapshot.HistoryEntry> history = new ArrayList<>();
        for (ObjectNode value : rows) {
            ObjectNode row = value.deepCopy().put("index", history.size() + 1L);
            history.add(new DriverStateSnapshot.HistoryEntry(history.size() + 1L,
                    new DriverStateSnapshot.Value(LifecycleJson.bytes(row))));
        }
        var driver = new DriverStateSnapshot.Complete(old.session(), history, old.lastCheckpoint(), old.rollbackWarFailure(),
                old.managedRestoreTransaction(), old.successionExpectation(), old.successionLifecycle(), old.campaignGoal(), old.rollbackWarFailures());
        var basis = fixture.files.createNew(root.resolve("send-consumer-driver.json"), driver.encode()).reference();
        var stamp = original.stamp();
        var facts = new DriverSnapshotFacts.Known(driver, new DriverSnapshotFacts.Stamp(stamp.driverVersion(), stamp.episodeEpoch(),
                stamp.game(), stamp.episodeRunId(), LifecycleJson.sha(driver.encode())), basis, List.of(), original.auxiliary(), Optional.empty(), Optional.empty());
        var observed = fixture.snapshot;
        var snapshot = new LifecycleObservationPort.Snapshot(observed.actual(), observed.source(), observed.semantic(), facts, observed.originalEvidence());
        var settlement = DeathSettlement.normalize(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(snapshot.semantic().get("one_life_settlement"))).orElseThrow();
        var reduced = LifecycleReducer.death(snapshot, settlement,
                new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD, false, Optional.empty(), List.of()), LifecycleBusinessFixture.AT);
        LifecycleReducer.requireScoredTerminal(reduced.driver());
        return LifecycleJson.parse(reduced.result(), LifecycleProofCodec.MAX_RESULT_BYTES);
    }
}
