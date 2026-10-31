package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure software DTO projection; no canonical writer, Native or Game qualification. */
final class DriverAppliedLifeHistory206Test {
    static final String WIRE = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"life-advance","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}""";

    static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw)); }
    static GameGeneration game() { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    static G2Source source() { return new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref(bytes("original-source"))); }

    static ProposalLifecycle.ObservationIdentity identity(BigInteger date, BigInteger revision, String snapshotId) {
        return new ProposalLifecycle.ObservationIdentity("test-machine", game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73), revision, date), snapshotId, BigInteger.valueOf(2), "episode-real-1"), 1);
    }

    static ActionCommand parentCommand() {
        var before = identity(BigInteger.valueOf(53144328), BigInteger.valueOf(9), "snapshot-9");
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source(), "test-effect/v1", List.of(
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true)));
        return new ActionCommand("parent-action", before, source(), "held-session", new OperationKey("life-advance"),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.parse("2030-01-01T00:00:00Z"));
    }

    static ActionCommand childCommand() {
        var before = identity(BigInteger.valueOf(53144328), BigInteger.valueOf(9), "snapshot-9");
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source(), "test-effect/v1", List.of(
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.resume_observed"), true)));
        return new ActionCommand("child-action", before, source(), "held-session", new OperationKey("resume-map"),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.parse("2030-01-01T00:00:00Z"));
    }

    static ActionState.Attempt attempt(ActionCommand command) {
        var guard = new GuardEvidence(new CommandOrigin.Gameplay(command.before()), command.source(), command.sessionId(),
                BigInteger.valueOf(1), command.operation(), ref(bytes("guard-native")), ref(bytes("guard-capability")),
                "authority-1", Instant.parse("2026-10-23T16:00:00Z"), Instant.parse("2030-01-01T00:00:00Z"));
        var prepared = new NativeRequest(command.operation().value(), Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        return new ActionState.Attempt("req-1", Instant.parse("2026-10-23T16:00:00Z"), guard, prepared);
    }

    static ActionState.Settled settledChild(ActionCommand command) {
        var before = command.before();
        var after = identity(BigInteger.valueOf(53144329), BigInteger.valueOf(10), "snapshot-10");
        var effect = new ActionState.EffectObservation(after, command.source(), command.sessionId(), "test-effect/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.resume_observed"), true)),
                new ObservationProvenance.Query("req-3"), Instant.parse("2026-10-23T16:00:01Z"), ref(bytes("child-effect-native")));
        var dispatch = new NativeActionPort.AckReceived("req-1", true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), bytes("ack-packet"));
        return new ActionState.Settled(attempt(command), dispatch, new ActionState.Applied(effect));
    }

    static CompositeExecution execution(ActionCommand parent, ActionCommand child) {
        var guard = new GuardEvidence(new CommandOrigin.Gameplay(parent.before()), parent.source(), parent.sessionId(),
                BigInteger.valueOf(1), parent.operation(), ref(bytes("guard-native")), ref(bytes("guard-capability")),
                "authority-1", Instant.parse("2026-10-23T16:00:00Z"), Instant.parse("2030-01-01T00:00:00Z"));
        return new CompositeExecution(LifeAdvanceComposite.HANDLER, Instant.parse("2026-10-23T16:00:00Z"), guard,
                List.of(new CompositeExecution.Child(child.actionId(), ActionCodec.bodySha256(child))));
    }

    static ActionState.CompositeSettled compositeSettled(ActionCommand parent, ActionCommand child) {
        var before = parent.before();
        var after = identity(BigInteger.valueOf(53144352), BigInteger.valueOf(11), "snapshot-11");
        var effect = new ActionState.EffectObservation(after, parent.source(), parent.sessionId(), "test-effect/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true)),
                new ObservationProvenance.Query("req-2"), Instant.parse("2026-10-23T16:00:02Z"), ref(bytes("effect-native")));
        return new ActionState.CompositeSettled(execution(parent, child), new ActionState.Applied(effect));
    }

    static ActionReceipt parentReceipt(ActionCommand parent, ActionCommand child) {
        return new ActionReceipt(1, 10, parent, ActionCodec.bodySha256(parent), compositeSettled(parent, child));
    }

    static ActionReceipt childReceipt(ActionCommand child) {
        return new ActionReceipt(1, 9, child, ActionCodec.bodySha256(child), settledChild(child));
    }

    static DriverSnapshotFacts.Known knownWithParentCoverage(ActionCommand parent, String originalWire) {
        var imported = DriverFactsRepository.imported(ref(bytes(originalWire)), bytes(originalWire), 3, 7, game(), new OpportunityJson.Obj(Map.of()));
        var parentRow = new DriverSnapshotFacts.ActionRow(parent.actionId(), ActionCodec.bodySha256(parent), 10L, 1L, ref(imported.driver().commandHistory().getFirst().originalRow().json()));
        return new DriverSnapshotFacts.Known(imported.driver(), imported.stamp(), imported.originalHistoryBasis(),
                List.of(parentRow), imported.auxiliary(), imported.loop(), imported.observation());
    }

    static ActionJournal.Snapshot snapshot(DriverSnapshotFacts.Known known, List<ActionReceipt> actions) {
        return new ActionJournal.Snapshot(10, "a".repeat(64), actions, new ActionJournal.BoundHistoryBasis(known.originalHistoryBasis()));
    }

    @Test void appliedLifeParentWithCanonicalChildrenLacksSecondRecorderRow() {
        var parent = parentCommand();
        var child = childCommand();
        var known = knownWithParentCoverage(parent, WIRE);
        var parentReceipt = parentReceipt(parent, child);
        var childReceipt = childReceipt(child);
        var settled = (ActionState.CompositeSettled) parentReceipt.state();
        ActionEffects.validateComposite(parent, settled.execution(), settled.settlement());
        ActionEffects.validateCompositeChildren(parent, settled.execution(), settled.settlement(), List.of(childReceipt));
        AdvanceClockArchivedReplay.verifyChildBindings(parent, List.of(childReceipt));
        var primitive = (ActionState.Settled) childReceipt.state();
        ActionEffects.validate(child, primitive.attempt(), primitive.dispatch(), primitive.settlement());

        assertInstanceOf(ActionState.Applied.class, settled.settlement());
        assertEquals(LifeAdvanceComposite.HANDLER, settled.execution().handlerId());
        assertEquals(1, known.actionRows().size());
        assertEquals(parent.actionId(), known.actionRows().getFirst().actionId());
        assertTrue(known.actionRows().stream().noneMatch(row -> row.actionId().equals(child.actionId())));
        var actual = assertInstanceOf(DriverStateSnapshot.Complete.class,
                DriverStateAssembler.project(known, snapshot(known, List.of(childReceipt, parentReceipt)), Optional.empty()));
        assertArrayEquals(known.driver().encode(), actual.encode());
        assertEquals(1, actual.commandHistory().size());
    }

    @Test void existingConflictsAndMissingParentOrCanonicalChildCannotUseTheAbsentRowException() {
        var parent = parentCommand();
        var child = childCommand();
        var known = knownWithParentCoverage(parent, WIRE);
        var parentReceipt = parentReceipt(parent, child);
        var childReceipt = childReceipt(child);
        var actions = List.of(childReceipt, parentReceipt);
        var parentRow = known.actionRows().getFirst();

        // Canonical-only is an existing public coverage variant. Its valid counterpart must work
        // before changing just one identity field; these records grant no original-source authority.
        var canonicalSource = new DriverSnapshotFacts.CanonicalOnly(ref(ActionCodec.encodeCommand(child)));
        var correctChild = new DriverSnapshotFacts.ActionRow(child.actionId(), childReceipt.bodySha256(), childReceipt.sequence(), canonicalSource);
        var bothCovered = withCoverage(known, List.of(parentRow, correctChild));
        assertInstanceOf(DriverStateSnapshot.Complete.class,
                DriverStateAssembler.project(bothCovered, snapshot(bothCovered, actions), Optional.empty()));
        var wrongBody = new DriverSnapshotFacts.ActionRow(child.actionId(), "f".repeat(64), childReceipt.sequence(), canonicalSource);
        assertMissing(withCoverage(known, List.of(parentRow, wrongBody)), actions,
                "original_history_row_unavailable:" + child.actionId());
        var futureSequence = new DriverSnapshotFacts.ActionRow(child.actionId(), childReceipt.bodySha256(), childReceipt.sequence() + 1, canonicalSource);
        assertMissing(withCoverage(known, List.of(parentRow, futureSequence)), actions,
                "original_history_row_unavailable:" + child.actionId());

        assertMissing(withCoverage(known, List.of()), actions, "original_history_row_unavailable:" + parent.actionId());
        String wrongSlot = WIRE.replace("\"command\":\"life-advance\"", "\"command\":\"other-history-command\"");
        assertNotEquals(WIRE, wrongSlot);
        assertMissing(knownWithParentCoverage(parent, wrongSlot), actions,
                "original_history_result_disagrees:" + parent.actionId());

        var missingChild = assertThrows(IllegalArgumentException.class, () -> DriverStateAssembler.project(
                known, snapshot(known, List.of(parentReceipt)), Optional.empty()));
        assertEquals("settled Life control child is absent from canonical Driver actions", missingChild.getMessage());
        var settled = (ActionState.CompositeSettled) parentReceipt.state();
        var conflict = new CompositeExecution(LifeAdvanceComposite.HANDLER, settled.execution().startedAt(),
                settled.execution().guard(), List.of(new CompositeExecution.Child(child.actionId(), "0".repeat(64))));
        var wrongParent = new ActionReceipt(1, parentReceipt.sequence(), parent, parentReceipt.bodySha256(),
                new ActionState.CompositeSettled(conflict, settled.settlement()));
        var conflictingChild = assertThrows(IllegalArgumentException.class, () -> DriverStateAssembler.project(
                known, snapshot(known, List.of(childReceipt, wrongParent)), Optional.empty()));
        assertEquals("composite cannot settle over a missing, conflicting or unresolved child", conflictingChild.getMessage());
        var foreignExecution = new CompositeExecution("foreign-life-handler", settled.execution().startedAt(),
                settled.execution().guard(), settled.execution().children());
        var foreignParent = new ActionReceipt(1, parentReceipt.sequence(), parent, parentReceipt.bodySha256(),
                new ActionState.CompositeSettled(foreignExecution, settled.settlement()));
        assertMissing(known, List.of(childReceipt, foreignParent), "original_history_row_unavailable:" + child.actionId());
    }

    static DriverSnapshotFacts.Known withCoverage(DriverSnapshotFacts.Known known, List<DriverSnapshotFacts.ActionRow> rows) {
        return new DriverSnapshotFacts.Known(known.driver(), known.stamp(), known.originalHistoryBasis(),
                rows, known.auxiliary(), known.loop(), known.observation());
    }
    static void assertMissing(DriverSnapshotFacts.Known known, List<ActionReceipt> actions, String field) {
        var actual = assertInstanceOf(DriverStateSnapshot.Incomplete.class,
                DriverStateAssembler.project(known, snapshot(known, actions), Optional.empty()));
        assertTrue(actual.missingOrUnreconciledFields().contains(field), actual.missingOrUnreconciledFields().toString());
    }
}
