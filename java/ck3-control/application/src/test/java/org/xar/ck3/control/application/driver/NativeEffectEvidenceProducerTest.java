package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual native-frame producer -> full Driver evidence -> observer -> archive -> original domain replay. */
final class NativeEffectEvidenceProducerTest {
    private static final Instant DEADLINE = Instant.parse("2030-01-01T00:00:00Z");
    private static final String BASE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":10660101,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,"active_wars":[],
         "player_armies":[{"army_id":1,"owner_character_id":73,"controllable":true,"in_combat":false,
          "retreating":false,"army_state":"regular","army_state_code":1,"current_province_id":2,
          "move_target_province_id":null,"route_province_ids":[]}]}
        """;
    private static NativeObservationPort.ObservedFrame frame(int revision, boolean moving) {
        String state = moving ? BASE.replace("\"move_target_province_id\":null", "\"move_target_province_id\":3").replace("\"route_province_ids\":[]", "\"route_province_ids\":[2,3]") : BASE;
        byte[] body = DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-" + revision + "\",\"revision\":" + revision + ",\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine", DriverStateAssemblerTest.game(), BigInteger.valueOf(5), "held-session"),
                "snapshot-" + revision, BigInteger.valueOf(revision), new RawJson(DriverStateAssemblerTest.bytes(state)), packet, Instant.parse("2026-10-23T16:00:00Z").plusSeconds(revision));
    }
    private static DriverObservationFacts actualFacts(NativeObservationPort.ObservedFrame actual, FixtureArchive archive) {
        var known = DriverStateAssemblerTest.known();
        RawJson full = new RawJson(known.driver().encode()); ExactRef fullRef = archive.preserveMaterial(full);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, actual.nativeRevision(), 1,
                DriverStateAssemblerTest.source(), new OpportunityJson.Obj(Map.of()), fullRef);
        ExactRef manifestRef = archive.preserveMaterial(manifest);
        return DriverObservationEvidenceReader.decode(manifestRef, manifest, full, actual);
    }
    private static ActionCommand command(DriverObservationAssembler.Complete before) {
        var operation = new OperationKey("move-army-1-to-3");
        return new ActionCommand("real-software-wire-move", before.identity(), before.source(), before.sessionId(), operation,
                new OpportunityJson.Obj(Map.of()), NativeArmyMoveEffects.expected(before.identity(), before.source(), operation),
                new JointBudgetSelector.Claims(Set.of(BigInteger.ONE), Set.of(), Set.of(), Set.of()), DEADLINE);
    }
    private static ActionState.Attempt attempt(ActionCommand command, DriverObservationAssembler.Complete before) {
        var guard = new GuardEvidence(before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), command.operation(),
                before.originalEvidence(), before.originalEvidence(), "software-domain-test", before.observedAt(), DEADLINE);
        return new ActionState.Attempt("native-request-1", before.observedAt(), guard, new NativeRequest(command.operation().value(), Optional.empty(), new RawJson(new byte[]{'{','}'})));
    }
    @Test void actualNativeAndCompleteDriverRebuildTheObservedMovementAfterArchiveRoundTrip() throws InterruptedException {
        var archive = new FixtureArchive(); var sequence = new AtomicInteger();
        var held = new HeldDriverObservationPort(deadline -> frame(sequence.getAndIncrement() == 0 ? 9 : 10, sequence.get() > 1),
                actual -> new DriverObservationFacts.Known(actualFacts(actual, archive)), archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
        var before = held.observe(DEADLINE); var command = command(before); var attempt = attempt(command, before);
        var observer = new NativeArmyMoveEffects(new NativeEffectSnapshots(held, archive));
        // An unknown dispatch does not prevent a later independent material observation; it never authorizes replay.
        var originalDispatch = new NativeActionPort.Unknown(attempt.requestId(), "actual unknown native return", new byte[]{1}, Optional.empty());
        var projected = observer.observe(command, attempt, originalDispatch);
        var effect = assertInstanceOf(ActionPorts.EffectObserved.class, projected.result());
        assertEquals(1, effect.observation().supportingEvidence().size());
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, originalDispatch, new ActionState.Applied(effect.observation())));
        var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var original = NativeEffectEvidence.load(receipt, archive, loader);
        assertEquals(original.independentReads(),NativeEffectEvidence.archivedReads(receipt,archive));
        assertEquals(before.semantic(), original.frames().before().semantic());
        assertEquals(projected.compatibleResult().orElseThrow(), original.compatibleResult());
        assertDoesNotThrow(() -> NativeArmyMoveEffects.archivedVerifier(command.operation(), DriverStateAssemblerTest.ref(new byte[]{1}), loader).verifier().verify(null, receipt, archive));
        assertTrue(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        ExactRef nativeAfter = effect.observation().originalEvidence(); archive.nativeFrames.get(nativeAfter)[4] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeEffectEvidence.archivedReads(receipt, archive));
        assertThrows(IllegalArgumentException.class, () -> NativeEffectEvidence.load(receipt, archive, loader));
    }
    @Test void successfulAckWithUnchangedActualArmyDoesNotProduceEffectOrDurableBasis() throws InterruptedException {
        var archive = new FixtureArchive(); var sequence = new AtomicInteger();
        var held = new HeldDriverObservationPort(deadline -> frame(sequence.getAndIncrement() == 0 ? 9 : 10, false),
                actual -> new DriverObservationFacts.Known(actualFacts(actual, archive)), archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
        var before = held.observe(DEADLINE); var command = command(before); var attempt = attempt(command, before);
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), true, Optional.of(new RawJson(new byte[]{'{','}'})), new RawJson(new byte[]{'{','}'}), new byte[]{1});
        var result = new NativeArmyMoveEffects(new NativeEffectSnapshots(held, archive)).observe(command, attempt, ack);
        assertInstanceOf(ActionPorts.Pending.class, result.result()); assertTrue(result.compatibleResult().isEmpty());
    }
    @Test void nativeFrameCannotSubstituteForFullDriverManifest() {
        var reference = DriverStateAssemblerTest.ref(new byte[]{1});
        assertThrows(IllegalArgumentException.class, () -> new NativeEffectEvidence.FrameBasis(reference, reference));
    }
    @Test void explicitPreviewMaterialIsPartOfTheReceiptClosureAndCannotDisappear() throws InterruptedException {
        var archive = new FixtureArchive(); var sequence = new AtomicInteger();
        var held = new HeldDriverObservationPort(deadline -> frame(sequence.getAndIncrement() == 0 ? 9 : 10, sequence.get() > 1),
                actual -> new DriverObservationFacts.Known(actualFacts(actual, archive)), archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
        var before = held.observe(DEADLINE); var command = command(before); var attempt = attempt(command, before);
        var snapshots = new NativeEffectSnapshots(held, archive); var dispatch = new NativeActionPort.Unknown(attempt.requestId(), "original return unknown", new byte[0], Optional.empty());
        var projected = new NativeArmyMoveEffects(snapshots).observe(command, attempt, dispatch);
        var initial = assertInstanceOf(ActionPorts.EffectObserved.class, projected.result()).observation();
        var initialReceipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(initial)));
        var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler()); var original = NativeEffectEvidence.load(initialReceipt, archive, loader);
        var preview = archive.preserveMaterial(new RawJson("{\"original_domain_material\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var basis = NativeEffectEvidence.preserve(command, attempt, original.frames(), original.independentReads(), original.compatibleResult(), List.of(preview), archive);
        var withClosure = NativeEffectSnapshots.withEvidence(projected, List.of(basis, preview));
        var observed = assertInstanceOf(ActionPorts.EffectObserved.class, withClosure.result()).observation();
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(observed)));
        assertEquals(List.of(preview), NativeEffectEvidence.load(receipt, archive, loader).supportingMaterials());
        assertEquals(original.independentReads(),NativeEffectEvidence.archivedReads(receipt,archive));
        var incomplete = NativeEffectSnapshots.withEvidence(projected, List.of(basis));
        var incompleteEffect = assertInstanceOf(ActionPorts.EffectObserved.class, incomplete.result()).observation();
        var missing = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(incompleteEffect)));
        assertThrows(IllegalArgumentException.class, () -> NativeEffectEvidence.load(missing, archive, loader));
        assertThrows(IllegalArgumentException.class, () -> NativeEffectEvidence.archivedReads(missing, archive));
        archive.materials.remove(preview);
        assertThrows(RuntimeException.class, () -> NativeEffectEvidence.archivedReads(receipt, archive));
        assertThrows(RuntimeException.class, () -> NativeEffectEvidence.load(receipt, archive, loader));
    }
    private static final class FixtureArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef, RawJson> materials = new HashMap<>();
        private final Map<ExactRef, byte[]> nativeFrames = new HashMap<>();
        private static ExactRef ref(String kind, byte[] bytes) { return new ExactRef("memory/" + kind + "/" + DriverJson.sha256(bytes), bytes.length, DriverJson.sha256(bytes)); }
        @Override public ExactRef preserveMaterial(RawJson original) { var ref = ref("material", original.bytes()); materials.putIfAbsent(ref, original); return ref; }
        @Override public RawJson loadMaterial(ExactRef original) { return java.util.Objects.requireNonNull(materials.get(original), "original fixture material missing"); }
        @Override public ExactRef materialReferenceOf(RawJson original) { var ref = ref("material", original.bytes()); assertEquals(original, materials.get(ref)); return ref; }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { var ref = ref("native", original.originalPacket()); nativeFrames.putIfAbsent(ref, original.originalPacket()); return ref; }
        @Override public byte[] loadNativeFrame(ExactRef original) { return java.util.Objects.requireNonNull(nativeFrames.get(original), "original fixture native missing").clone(); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { throw new UnsupportedOperationException(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRequest(NativeRequest original) { throw new UnsupportedOperationException(); }
        @Override public NativeRequest loadRequest(ExactRef original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { throw new UnsupportedOperationException(); }
        @Override public PlanningReadReceipt loadRead(ExactRef original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRecord(ActionRecord original) { throw new UnsupportedOperationException(); }
        @Override public ActionRecord loadRecord(ExactRef original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef recordReferenceOf(ActionRecord original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveReceipt(ActionReceipt original) { throw new UnsupportedOperationException(); }
        @Override public ActionReceipt loadReceipt(ExactRef original) { throw new UnsupportedOperationException(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt original) { throw new UnsupportedOperationException(); }
    }
}
