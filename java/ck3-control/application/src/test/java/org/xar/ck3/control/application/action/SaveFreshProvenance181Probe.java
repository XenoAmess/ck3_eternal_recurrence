package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;

public final class SaveFreshProvenance181Probe {
    private static int checks = 0;

    private static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }

    private static void expectFailure(Runnable runnable, String message) {
        checks++;
        try {
            runnable.run();
            throw new AssertionError(message + " (expected failure but passed)");
        } catch (IllegalArgumentException | IllegalStateException e) {
            // Expected
        }
    }

    // --- Fixtures ---
    private static final Instant NOW = Instant.parse("2026-10-23T18:00:00Z");
    private static final ExactRef REF = new ExactRef("D:/contract-vectors/source.json", 1, "a".repeat(64));
    private static final ExactRef AFTER = new ExactRef("D:/contract-vectors/after.json", 1, "b".repeat(64));
    private static final ExactRef BASIS = new ExactRef("D:/contract-vectors/basis.json", 1, "c".repeat(64));
    private static final ExactRef COLD_REF = new ExactRef("D:/contract-vectors/cold.json", 1, "d".repeat(64));
    private static final ExactRef READ_ACK = new ExactRef("D:/contract-vectors/read-ack.json", 1, "e".repeat(64));
    private static final ExactRef LIVE_SETTER = new ExactRef("D:/contract-vectors/live-setter.json", 1, "f".repeat(64));
    private static final ExactRef WATCH_PARENT = new ExactRef("D:/contract-vectors/watch-parent.json", 1, "7".repeat(64));
    private static final ExactRef WATCH_RESUME = new ExactRef("D:/contract-vectors/watch-resume.json", 1, "8".repeat(64));

    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    private static final JointBudgetSelector.Claims CLAIMS = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of());

    private static ProposalLifecycle.ObservationIdentity frame(int revision, String snapshotId) {
        return new ProposalLifecycle.ObservationIdentity(
                SOURCE.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(revision + 10), BigInteger.valueOf(100)),
                        snapshotId,
                        BigInteger.valueOf(revision + 10),
                        "episode-1"),
                1);
    }

    private static ActionCommand saveCommand(String id, int revision, String snapshotId) {
        var before = frame(revision, snapshotId);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, SOURCE, CheckpointRequestFactory.OBSERVER_SCHEMA,
                List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("date_raw"), before.frame().identity().dateRaw()),
                        new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("played_character_id"), before.frame().identity().player()),
                        new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("checkpoint_pair_verified"), true)));
        return new ActionCommand(id, before, SOURCE, "session-1", new OperationKey("save-checkpoint"),
                new OpportunityJson.Obj(Map.of()), expected, CLAIMS, NOW.plusSeconds(30));
    }

    private static ActionCommand ordinaryCommand(String id, int revision, String snapshotId) {
        var before = frame(revision, snapshotId);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, SOURCE, "paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, SOURCE, "session-1", new OperationKey("pause-map"),
                new OpportunityJson.Obj(Map.of()), expected, CLAIMS, NOW.plusSeconds(30));
    }

    private static GuardEvidence guard(ActionCommand command, Instant at) {
        return new GuardEvidence(command.before(), SOURCE, command.sessionId(), BigInteger.ONE, command.operation(), REF, BASIS, "authority-1", at, NOW.plusSeconds(20));
    }

    private static ActionState.Attempt attempt(ActionCommand command, String request) {
        return new ActionState.Attempt(request, NOW, guard(command, NOW), new NativeRequest(command.operation().value(), "timeline-control", new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
    }

    private static ObservationProvenance.FreshSnapshotQuery coldFresh(String requestId, Instant observedAt) {
        var event = new NativeRequestChronology.Event(BigInteger.ONE, observedAt);
        return new ObservationProvenance.FreshSnapshotQuery(requestId, READ_ACK, event, new ObservationProvenance.ColdAfterAcknowledgement(COLD_REF));
    }

    private static ObservationProvenance.FreshSnapshotQuery liveFresh(String requestId, Instant observedAt) {
        var event = new NativeRequestChronology.Event(BigInteger.ONE, observedAt);
        return new ObservationProvenance.FreshSnapshotQuery(requestId, READ_ACK, event, new ObservationProvenance.LiveAfterSetter(LIVE_SETTER));
    }

    private static ObservationProvenance.FreshSnapshotQuery watchFresh(String requestId, Instant observedAt) {
        var event = new NativeRequestChronology.Event(BigInteger.ONE, observedAt);
        return new ObservationProvenance.FreshSnapshotQuery(requestId, READ_ACK, event, new ObservationProvenance.SameGameWatch(WATCH_PARENT, WATCH_RESUME));
    }

    private static ActionState.EffectObservation effectWithProvenance(ActionCommand command, int afterRevision, String afterSnapshotId, ObservationProvenance provenance, Instant observedAt) {
        var after = frame(afterRevision, afterSnapshotId);
        return new ActionState.EffectObservation(after, SOURCE, command.sessionId(), command.expected().observerSchema(),
                command.expected().values(), provenance, observedAt, AFTER, List.of(BASIS));
    }

    private static ActionState.EffectObservation effectWithQuery(ActionCommand command, int afterRevision, String afterSnapshotId, String readRequestId, Instant observedAt) {
        var after = frame(afterRevision, afterSnapshotId);
        return new ActionState.EffectObservation(after, SOURCE, command.sessionId(), command.expected().observerSchema(),
                command.expected().values(), readRequestId, observedAt, AFTER, List.of(BASIS));
    }

    public static void main(String[] args) {
        // (1) FreshSnapshotQuery ColdAfterAcknowledgement roundtrip
        var cold = new ObservationProvenance.FreshSnapshotQuery("req-1", READ_ACK, new NativeRequestChronology.Event(BigInteger.ONE, NOW), new ObservationProvenance.ColdAfterAcknowledgement(COLD_REF));
        var encoded = ObservationProvenanceCodec.encode(cold);
        var decoded = ObservationProvenanceCodec.decode(encoded);
        check(decoded instanceof ObservationProvenance.FreshSnapshotQuery, "Cold roundtrip kind");
        var decodedFresh = (ObservationProvenance.FreshSnapshotQuery) decoded;
        check(decodedFresh.basis() instanceof ObservationProvenance.ColdAfterAcknowledgement, "Cold roundtrip basis kind");
        check(((ObservationProvenance.ColdAfterAcknowledgement) decodedFresh.basis()).originalReceipt().equals(COLD_REF), "Cold roundtrip exact originalReceipt");

        // Exact closed-key schema, with no filesystem or deep-authenticity claims.
        expectFailure(() -> {
            var obj = ObservationProvenanceCodec.encode(cold);
            ((com.fasterxml.jackson.databind.node.ObjectNode) obj.get("basis")).remove("original_receipt");
            ObservationProvenanceCodec.decode(obj);
        }, "missing original_receipt rejected");
        expectFailure(() -> {
            var obj = ObservationProvenanceCodec.encode(cold);
            ((com.fasterxml.jackson.databind.node.ObjectNode) obj.get("basis")).put("unrecognized", true);
            ObservationProvenanceCodec.decode(obj);
        }, "extra basis key rejected");
        expectFailure(() -> {
            var obj = ObservationProvenanceCodec.encode(cold);
            ((com.fasterxml.jackson.databind.node.ObjectNode) obj.get("basis")).put("kind", "unrecognized");
            ObservationProvenanceCodec.decode(obj);
        }, "unknown basis kind rejected");
        check(encoded.get("basis").get("kind").textValue().equals("cold_after_acknowledgement"), "exact cold JSON kind");

        // Reject zero-byte cold ref
        expectFailure(() -> new ObservationProvenance.ColdAfterAcknowledgement(new ExactRef("D:/zero.json", 0, "0".repeat(64))), "Zero-byte cold ref rejected");

        // Legacy Live and Watch preserved exact kinds
        var live = new ObservationProvenance.FreshSnapshotQuery("req-2", READ_ACK, new NativeRequestChronology.Event(BigInteger.ONE, NOW), new ObservationProvenance.LiveAfterSetter(LIVE_SETTER));
        var liveEncoded = ObservationProvenanceCodec.encode(live);
        check(liveEncoded.get("basis").get("kind").textValue().equals("live_after_setter"), "exact legacy live JSON kind");
        var liveDecoded = ObservationProvenanceCodec.decode(liveEncoded);
        check(liveDecoded instanceof ObservationProvenance.FreshSnapshotQuery, "Live roundtrip kind");
        check(((ObservationProvenance.FreshSnapshotQuery) liveDecoded).basis() instanceof ObservationProvenance.LiveAfterSetter, "Live roundtrip basis kind");

        var watch = new ObservationProvenance.FreshSnapshotQuery("req-3", READ_ACK, new NativeRequestChronology.Event(BigInteger.ONE, NOW), new ObservationProvenance.SameGameWatch(WATCH_PARENT, WATCH_RESUME));
        var watchEncoded = ObservationProvenanceCodec.encode(watch);
        check(watchEncoded.get("basis").get("kind").textValue().equals("same_game_watch"), "exact legacy watch JSON kind");
        var watchDecoded = ObservationProvenanceCodec.decode(watchEncoded);
        check(watchDecoded instanceof ObservationProvenance.FreshSnapshotQuery, "Watch roundtrip kind");
        check(((ObservationProvenance.FreshSnapshotQuery) watchDecoded).basis() instanceof ObservationProvenance.SameGameWatch, "Watch roundtrip basis kind");

        // (2) Structural ActionEffects.validate checks

        // Case A: Same before/after nativeRevision and same snapshotID: exact save-checkpoint and CheckpointRequestFactory.OBSERVER_SCHEMA with Cold Fresh passes structural ActionEffects.validate
        var saveCmd = saveCommand("save-a", 1, "native-1");
        var saveAttempt = attempt(saveCmd, "write-req");
        var coldProvenance = coldFresh("read-req", NOW.plusSeconds(3));
        var effectA = effectWithProvenance(saveCmd, 1, "native-1", coldProvenance, NOW.plusSeconds(3));
        var settlementA = new ActionState.Applied(effectA);
        ActionEffects.validate(saveCmd, saveAttempt, settlementA);
        check(true, "Case A passed");

        // Case B: Same before/after nativeRevision and same snapshotID: exact save-checkpoint and CheckpointRequestFactory.OBSERVER_SCHEMA with Live Fresh passes
        var liveProvenance = liveFresh("read-req", NOW.plusSeconds(3));
        var effectB = effectWithProvenance(saveCmd, 1, "native-1", liveProvenance, NOW.plusSeconds(3));
        var settlementB = new ActionState.Applied(effectB);
        ActionEffects.validate(saveCmd, saveAttempt, settlementB);
        check(true, "Case B passed");

        // Case C: Different snapshotID and greater nativeRevision with Cold passes too
        var effectC = effectWithProvenance(saveCmd, 2, "native-2", coldProvenance, NOW.plusSeconds(3));
        var settlementC = new ActionState.Applied(effectC);
        ActionEffects.validate(saveCmd, saveAttempt, settlementC);
        check(true, "Case C passed");

        // Case D: Lower nativeRevision cold SAVE rejects
        var effectD = effectWithProvenance(saveCmd, 0, "native-0", coldProvenance, NOW.plusSeconds(3));
        var settlementD = new ActionState.Applied(effectD);
        expectFailure(() -> ActionEffects.validate(saveCmd, saveAttempt, settlementD), "Case D lower revision rejected");

        // Case E: Same-revision ordinary world action with Cold Fresh rejects
        var ordinaryCmd = ordinaryCommand("pause-e", 1, "native-1");
        var ordinaryAttempt = attempt(ordinaryCmd, "write-req");
        var effectE = effectWithProvenance(ordinaryCmd, 1, "native-1", coldProvenance, NOW.plusSeconds(3));
        var settlementE = new ActionState.Applied(effectE);
        expectFailure(() -> ActionEffects.validate(ordinaryCmd, ordinaryAttempt, settlementE), "Case E ordinary same revision rejected");

        // Case F: SAVE with Query or SameGameWatch same frame rejects
        var effectFQuery = effectWithQuery(saveCmd, 1, "native-1", "read-req", NOW.plusSeconds(3));
        var settlementFQuery = new ActionState.Applied(effectFQuery);
        expectFailure(() -> ActionEffects.validate(saveCmd, saveAttempt, settlementFQuery), "Case F Query same frame rejected");

        var effectFWatch = effectWithProvenance(saveCmd, 1, "native-1", watchFresh("read-req", NOW.plusSeconds(3)), NOW.plusSeconds(3));
        var settlementFWatch = new ActionState.Applied(effectFWatch);
        expectFailure(() -> ActionEffects.validate(saveCmd, saveAttempt, settlementFWatch), "Case F Watch same frame rejected");

        // Case G: Wrong schema same frame rejects
        var wrongSchemaCmd = new ActionCommand("save-g", saveCmd.before(), SOURCE, "session-1", new OperationKey("save-checkpoint"),
                new OpportunityJson.Obj(Map.of()), new ProposalLifecycle.ExpectedPostcondition(1, saveCmd.before(), SOURCE, "wrong/v1", saveCmd.expected().values()), CLAIMS, NOW.plusSeconds(30));
        var wrongSchemaAttempt = attempt(wrongSchemaCmd, "write-req");
        var effectG = effectWithProvenance(wrongSchemaCmd, 1, "native-1", coldProvenance, NOW.plusSeconds(3));
        var settlementG = new ActionState.Applied(effectG);
        expectFailure(() -> ActionEffects.validate(wrongSchemaCmd, wrongSchemaAttempt, settlementG), "Case G wrong schema rejected");

        // Case H: Same READ request as write rejects even SAVE
        var effectH = effectWithProvenance(saveCmd, 1, "native-1", coldFresh("write-req", NOW.plusSeconds(3)), NOW.plusSeconds(3));
        var settlementH = new ActionState.Applied(effectH);
        expectFailure(() -> ActionEffects.validate(saveCmd, saveAttempt, settlementH), "Case H same read request rejected");

        // Case I: Older observedAt rejects
        var effectI = effectWithProvenance(saveCmd, 1, "native-1", coldProvenance, NOW.minusSeconds(1));
        var settlementI = new ActionState.Applied(effectI);
        expectFailure(() -> ActionEffects.validate(saveCmd, saveAttempt, settlementI), "Case I older observedAt rejected");

        // (3) ActionEffects.supportingEvidence(Applied) includes cold.originalReceipt plus readAcknowledgement
        var evidence = ActionEffects.supportingEvidence(settlementA);
        check(evidence.contains(COLD_REF), "Supporting evidence includes cold originalReceipt");
        check(evidence.contains(READ_ACK), "Supporting evidence includes readAcknowledgement");

        System.out.println("Checks passed: " + checks);
    }
}