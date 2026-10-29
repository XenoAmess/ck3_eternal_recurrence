package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventtraits.*;

/** Actual framed producer -> complete Driver manifest -> event observer -> archive -> same domain replay. */
final class NativeEventEvidenceProducerTest {
    private static final Instant DEADLINE = Instant.parse("2030-01-01T00:00:00Z");
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":10660101,
         "played_character":{"character_id":73,"alive":true,"stress_points":10},
         "active_event":{"instance_id":17,"option_count":3},"pending_character_interaction":null,
         "one_life_terminal_reason":null,"active_wars":[],"player_armies":[]}
        """;
    private static NativeObservationPort.ObservedFrame frame(int revision, boolean advanced) {
        String state = advanced ? STATE.replace("{\"instance_id\":17,\"option_count\":3}", "null") : STATE;
        byte[] body = DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-" + revision + "\",\"revision\":" + revision + ",\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine", DriverStateAssemblerTest.game(), BigInteger.valueOf(5), "held-session"),
            "snapshot-" + revision, BigInteger.valueOf(revision), new RawJson(DriverStateAssemblerTest.bytes(state)), packet,
            Instant.parse("2026-10-23T16:00:00Z").plusSeconds(revision));
    }
    private static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual, Archive archive) {
        var known = DriverStateAssemblerTest.known(); RawJson full = new RawJson(known.driver().encode()); ExactRef fullRef = archive.preserveMaterial(full);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, actual.nativeRevision(), 1,
            DriverStateAssemblerTest.source(), new OpportunityJson.Obj(Map.of()), fullRef);
        ExactRef reference = archive.preserveMaterial(manifest);
        return DriverObservationEvidenceReader.decode(reference, manifest, full, actual);
    }
    private static ActionCommand command(DriverObservationAssembler.Complete before, boolean poet) {
        var args = StrictJson.object();
        if (poet) {
            var original = new PoetTraitOutcome.PublicFrame(before.identity().frame().snapshotId(), before.identity().frame().revision(),
                new EventTraitMembership.Frame(before.identity().frame().identity().nativeRevision(), 10660101, 73));
            args.set("event_material_postcondition", StrictJson.parse(PoetTraitOutcome.encode(new PoetTraitOutcome.Ready(new PoetTraitOutcome.Binding(PoetTraitOutcome.Choice.POET, original)))));
            args.set("event_effect_phase", StrictJson.parse(EventEffectPhase.encode(EventEffectPhase.classify(PoetTraitOutcome.EVENT,
                new EventEffectPhase.SourceBinding("1.20.0.4", EventEffectPhase.EXE, PoetTraitOutcome.SOURCE_PATH, PoetTraitOutcome.SOURCE_SHA256), 0).orElseThrow())));
        }
        var expected = new ExpectedPostcondition(1, before.identity(), before.source(), NativeEventPostconditionPort.EVENT_SCHEMA, List.of(
            new ExpectedInteger(new FieldKey("old_instance_id"), BigInteger.valueOf(17)), new ExpectedBoolean(new FieldKey("old_instance_advanced"), true),
            new ExpectedInteger(new FieldKey("actor_id"), BigInteger.valueOf(73)), new ExpectedText(new FieldKey("connection_generation_decimal"), "5")));
        return new ActionCommand("actual-software-event-consumption", before.identity(), before.source(), before.sessionId(), new OperationKey("select-event-option-1"),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)), "event arguments"), expected,
            new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), DEADLINE);
    }
    private static ActionState.Attempt attempt(ActionCommand command, DriverObservationAssembler.Complete before) {
        var guard = new GuardEvidence(before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), command.operation(),
            before.originalEvidence(), before.originalEvidence(), "actual-software-event-test", before.observedAt(), DEADLINE);
        return new ActionState.Attempt("native-event-request-1", before.observedAt(), guard,
            new NativeRequest(command.operation().value(), Optional.empty(), new RawJson(new byte[]{'{','}'})));
    }
    private static final PlanningReadPort NO_READS = new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            throw new AssertionError("no event material query is installed or required in this fixture");
        }
    };
    private static NativeEventEffects.MaterialQueries queries() { return new NativeEventEffects.MaterialQueries(Optional.empty(), Optional.empty()); }
    private static HeldDriverObservationPort held(Archive archive, boolean advance) {
        var sequence = new AtomicInteger();
        return new HeldDriverObservationPort(deadline -> frame(sequence.getAndIncrement() == 0 ? 9 : 10, sequence.get() > 1 && advance),
            actual -> new DriverObservationFacts.Known(facts(actual, archive)), archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
    }
    private static HeldDriverObservationPort heldPending(Archive archive,boolean advance) {
        return heldPending(archive,advance,false);
    }
    private static HeldDriverObservationPort heldPending(Archive archive,boolean advance,boolean notification) {
        var sequence=new AtomicInteger();
        return new HeldDriverObservationPort(deadline->{
            int position=sequence.getAndIncrement(),revision=position==0?9:10;
            String state=STATE.replace("{\"instance_id\":17,\"option_count\":3}","null")
                    .replace("\"pending_character_interaction\":null",position>0&&advance?"\"pending_character_interaction\":null"
                        :"\"pending_character_interaction\":{\"instance_id\":17,\"sender_character_id\":201,\"auto_accept_notification\":"+notification+"}");
            byte[] body=DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-"+revision+"\",\"revision\":"+revision+",\"state\":"+state+"}");
            byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),BigInteger.valueOf(5),"held-session"),
                    "snapshot-"+revision,BigInteger.valueOf(revision),new RawJson(DriverStateAssemblerTest.bytes(state)),packet,
                    Instant.parse("2026-10-23T16:00:00Z").plusSeconds(revision));
        },actual->new DriverObservationFacts.Known(facts(actual,archive)),archive::preserveNativeFrame,new DriverObservationAssembler(),8);
    }
    private static ActionCommand pendingCommand(DriverObservationAssembler.Complete before,String operation) {
        var event=command(before,false);
        return new ActionCommand("software-pending-"+operation,before.identity(),before.source(),before.sessionId(),new OperationKey(operation),event.arguments(),
                new ExpectedPostcondition(1,before.identity(),before.source(),NativeEventPostconditionPort.PENDING_SCHEMA,event.expected().values()),event.claims(),DEADLINE);
    }
    @Test void allPendingStatusEnvelopesUseActualBeforeAndAfterInsteadOfStaleAckMirrors()throws InterruptedException {
        for(String operation:List.of("reject-pending-character-interaction","accept-pending-character-interaction","acknowledge-pending-character-interaction")) {
            var archive=new Archive();var held=heldPending(archive,true,operation.startsWith("acknowledge-"));var before=held.observe(DEADLINE);
            var command=pendingCommand(before,operation);var attempt=attempt(command,before);
            var token=new RawJson(DriverStateAssemblerTest.bytes("{\"step\":\""+operation+"\",\"accepted\":true,\"snapshot_id\":\"stale\",\"revision\":1,\"paused\":false,\"interaction_result\":{\"status\":\"stale\",\"instance_id\":99,\"sender_character_id\":999},\"remaining_pending_character_interaction\":{\"instance_id\":17}}"));
            var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(token),token,new byte[]{1});
            var deliveries=new AtomicInteger();
            var projected=new NativeEventEffects(new NativeEffectSnapshots(held,archive),NO_READS,queries(),(c,a,p,durable)->{
                assertSame(command,c);assertSame(attempt,a);assertFalse(assertInstanceOf(ActionPorts.EffectObserved.class,durable.result()).observation().supportingEvidence().isEmpty());deliveries.incrementAndGet();
            }).observe(command,attempt,ack);
            JsonNode result=StrictJson.parse(projected.compatibleResult().orElseThrow().bytes());
            String status=operation.startsWith("acknowledge-")?"acknowledged":operation.startsWith("accept-")?"accepted":"rejected";
            assertEquals(status,result.path("interaction_result").path("status").textValue());
            assertEquals(17,result.path("interaction_result").path("instance_id").intValue());assertEquals(201,result.path("interaction_result").path("sender_character_id").intValue());
            assertTrue(result.path("remaining_pending_character_interaction").isNull());assertTrue(result.path("paused").booleanValue());
            assertEquals("snapshot-10",result.path("snapshot_id").textValue());assertEquals(10,result.path("revision").intValue());
            assertEquals("xar.java-native-event-result/v3",result.path("event_result_projection_schema").textValue());assertTrue(result.path("accepted").booleanValue());assertEquals(1,deliveries.get());
            var effect=assertInstanceOf(ActionPorts.EffectObserved.class,projected.result()).observation();
            var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.Applied(effect)));
            assertDoesNotThrow(()->replay(command,receipt,archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler())));
        }
    }
    @Test void unknownPendingIndependentAfterKeepsNoAckAndHistoricalPendingArchiveScope()throws InterruptedException {
        var archive=new Archive();var held=heldPending(archive,true);var before=held.observe(DEADLINE);var command=pendingCommand(before,"reject-pending-character-interaction");var attempt=attempt(command,before);
        var unknown=new NativeActionPort.Unknown(attempt.requestId(),"original pending lost ACK",new byte[]{1},Optional.empty());
        var snapshots=new NativeEffectSnapshots(held,archive);NativeEffectSnapshots.Pair[] pair=new NativeEffectSnapshots.Pair[1];
        var live=new NativeEventEffects(snapshots,NO_READS,queries(),(c,a,p,result)->pair[0]=p).observe(command,attempt,unknown);
        ObjectNode result=(ObjectNode)StrictJson.parse(live.compatibleResult().orElseThrow().bytes());assertFalse(result.has("accepted"));assertTrue(result.get("remaining_pending_character_interaction").isNull());
        ObjectNode legacy=result.deepCopy();for(String field:List.of("interaction_result","remaining_pending_character_interaction","paused","snapshot_id","revision","event_result_projection_schema"))legacy.remove(field);
        RawJson legacyRaw=new RawJson(StrictJson.canonical(legacy,1<<20));ExactRef basis=snapshots.evidence(command,attempt,pair[0],List.of(),legacyRaw,List.of());
        var restored=NativeEffectSnapshots.withEvidence(new NativeEffectRegistry.Projected(live.result(),Optional.of(legacyRaw)),List.of(basis));
        var effect=assertInstanceOf(ActionPorts.EffectObserved.class,restored.result()).observation();
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,unknown,new ActionState.Applied(effect)));
        assertDoesNotThrow(()->replay(command,receipt,archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler())));
    }
    @Test void pendingAckWithOriginalWindowStillPresentDoesNotDeliverAnAfterIncident()throws InterruptedException {
        var archive=new Archive();var held=heldPending(archive,false);var before=held.observe(DEADLINE);var command=pendingCommand(before,"reject-pending-character-interaction");var attempt=attempt(command,before);
        var token=new RawJson(DriverStateAssemblerTest.bytes("{\"step\":\"reject-pending-character-interaction\",\"accepted\":true}"));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(token),token,new byte[]{1});
        var result=new NativeEventEffects(new NativeEffectSnapshots(held,archive),NO_READS,queries(),(c,a,p,r)->fail("ACK cannot stand in for actual pending-window disappearance")).observe(command,attempt,ack);
        assertInstanceOf(ActionPorts.Pending.class,result.result());assertTrue(result.compatibleResult().isEmpty());
    }
    @Test void unknownDispatchCanSettleOnlyAfterIndependentWindowConsumptionAndDurableOriginalReplay() throws InterruptedException {
        var archive = new Archive(); var held = held(archive, true); var before = held.observe(DEADLINE);
        var command = command(before, false); var attempt = attempt(command, before);
        var dispatch = new NativeActionPort.Unknown(attempt.requestId(), "unknown native result", new byte[]{1}, Optional.empty());
        var delivered = new AtomicInteger();
        NativeEventEffects.ObservedAfter journal = (actualCommand, actualAttempt, actualPair, durable) -> {
            assertSame(command, actualCommand); assertSame(attempt, actualAttempt);
            assertEquals(before.identity(), actualPair.before().identity());
            assertNotEquals(before.identity(), actualPair.after().identity());
            var effect = assertInstanceOf(ActionPorts.EffectObserved.class, durable.result()).observation();
            assertEquals(1, effect.supportingEvidence().size());
            assertNotNull(archive.loadMaterial(effect.supportingEvidence().getFirst()));
            assertTrue(StrictJson.parse(durable.compatibleResult().orElseThrow().bytes()).path("event_selection").path("postcondition_verified").booleanValue());
            delivered.incrementAndGet();
        };
        var projected = new NativeEventEffects(new NativeEffectSnapshots(held, archive), NO_READS, queries(), journal).observe(command, attempt, dispatch);
        assertEquals(1, delivered.get());
        var observed = assertInstanceOf(ActionPorts.EffectObserved.class, projected.result()).observation();
        assertInstanceOf(ObservationProvenance.Push.class, observed.provenance()); assertEquals(1, observed.supportingEvidence().size());
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(observed)));
        var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        assertDoesNotThrow(() -> NativeEventEffects.archivedVerifier(command.operation(), DriverStateAssemblerTest.ref(new byte[]{1}), loader, queries()).verifier().verify(null, receipt, archive));
        assertEquals(1, delivered.get(), "archive replay must not invoke the live incident journal again");
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        assertEquals(projected.compatibleResult().orElseThrow(), NativeEffectEvidence.load(receipt, archive, loader).compatibleResult());
        JsonNode result = StrictJson.parse(projected.compatibleResult().orElseThrow().bytes());
        assertTrue(result.get("active_event").isNull());assertTrue(result.get("paused").booleanValue());
        assertEquals("snapshot-10",result.get("snapshot_id").textValue());assertEquals(BigInteger.TEN,result.get("revision").bigIntegerValue());
        assertEquals(17,result.get("event_instance_id").intValue());assertEquals(1,result.get("option_number").intValue());assertEquals(0,result.get("option_index").intValue());
        assertFalse(result.has("accepted"),"an independently observed UNKNOWN does not invent a native ACK");
        archive.nativeFrames.get(observed.originalEvidence())[4] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> NativeEventEvidenceProducerTest.replay(command, receipt, archive, loader));
    }
    private static void replay(ActionCommand command, ActionReceipt receipt, Archive archive, NativeEffectEvidence.FrameLoader loader) {
        NativeEventEffects.archivedVerifier(command.operation(), DriverStateAssemblerTest.ref(new byte[]{1}), loader, queries()).verifier().verify(null, receipt, archive);
    }
    @Test void ackWithUnchangedActualWindowRemainsPendingAndCannotCreateMaterialCredit() throws InterruptedException {
        var archive = new Archive(); var held = held(archive, false); var before = held.observe(DEADLINE);
        var command = command(before, false); var attempt = attempt(command, before);
        var token = new RawJson(DriverStateAssemblerTest.bytes("{\"step\":\"select-event-option-1\",\"accepted\":true}"));
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), true, Optional.of(token), token, new byte[]{1});
        var result = new NativeEventEffects(new NativeEffectSnapshots(held, archive), NO_READS, queries(),
            (ignoredCommand, ignoredAttempt, ignoredPair, ignoredResult) -> fail("unchanged ACK cannot create an incident after")).observe(command, attempt, ack);
        assertInstanceOf(ActionPorts.Pending.class, result.result()); assertTrue(result.compatibleResult().isEmpty());
    }
    @Test void actualAfterFrameReplacesStaleAckMirrorsAndSurvivesCanonicalArchiveReplay() throws InterruptedException {
        var archive = new Archive();var held=held(archive,true);var before=held.observe(DEADLINE);
        var command=command(before,false);var attempt=attempt(command,before);
        var token=new RawJson(DriverStateAssemblerTest.bytes("{\"step\":\"select-event-option-1\",\"accepted\":true,\"snapshot_id\":\"stale-ack\",\"revision\":1,\"paused\":false,\"active_event\":{\"instance_id\":17},\"option_number\":99,\"option_index\":98,\"event_instance_id\":999}"));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(token),token,new byte[]{1});
        var projected=new NativeEventEffects(new NativeEffectSnapshots(held,archive),NO_READS,queries()).observe(command,attempt,ack);
        var observed=assertInstanceOf(ActionPorts.EffectObserved.class,projected.result()).observation();
        JsonNode result=StrictJson.parse(projected.compatibleResult().orElseThrow().bytes());
        assertEquals("snapshot-10",result.get("snapshot_id").textValue());assertEquals(BigInteger.TEN,result.get("revision").bigIntegerValue());
        assertTrue(result.get("paused").booleanValue());assertTrue(result.get("active_event").isNull());assertTrue(result.get("accepted").booleanValue());
        assertEquals(17,result.get("event_instance_id").intValue());assertEquals(1,result.get("option_number").intValue());assertEquals(0,result.get("option_index").intValue());
        assertEquals("snapshot-10",result.path("event_selection").path("ending_snapshot_id").textValue());
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.Applied(observed)));
        var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        assertDoesNotThrow(()->replay(command,receipt,archive,loader));
        assertEquals(projected.compatibleResult().orElseThrow(),NativeEffectEvidence.load(receipt,archive,loader).compatibleResult());
    }
    @Test void historicalProjectionRetainsItsOriginalScopeAndExplicitUnknownVersionIsRejected() throws InterruptedException {
        var archive=new Archive();var held=held(archive,true);var before=held.observe(DEADLINE);
        var command=command(before,false);var attempt=attempt(command,before);var snapshots=new NativeEffectSnapshots(held,archive);
        var unknown=new NativeActionPort.Unknown(attempt.requestId(),"historical software projection fixture",new byte[]{1},Optional.empty());
        NativeEffectSnapshots.Pair[] pair=new NativeEffectSnapshots.Pair[1];
        var live=new NativeEventEffects(snapshots,NO_READS,queries(),(c,a,p,result)->pair[0]=p).observe(command,attempt,unknown);
        ObjectNode legacy=((ObjectNode)StrictJson.parse(live.compatibleResult().orElseThrow().bytes())).deepCopy();
        ObjectNode originalV2=legacy.deepCopy();originalV2.put("event_result_projection_schema","xar.java-native-event-result/v2");
        RawJson v2Raw=new RawJson(StrictJson.canonical(originalV2,1<<20));ExactRef v2Basis=snapshots.evidence(command,attempt,pair[0],List.of(),v2Raw,List.of());
        var v2Projected=NativeEffectSnapshots.withEvidence(new NativeEffectRegistry.Projected(live.result(),Optional.of(v2Raw)),List.of(v2Basis));
        var v2Effect=assertInstanceOf(ActionPorts.EffectObserved.class,v2Projected.result()).observation();
        var v2Receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,unknown,new ActionState.Applied(v2Effect)));
        assertDoesNotThrow(()->replay(command,v2Receipt,archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler())));
        for(String field:List.of("event_result_projection_schema","active_event","paused","snapshot_id","revision","event_instance_id","option_number","option_index"))legacy.remove(field);
        RawJson legacyRaw=new RawJson(StrictJson.canonical(legacy,1<<20));
        ExactRef basis=snapshots.evidence(command,attempt,pair[0],List.of(),legacyRaw,List.of());
        var old=NativeEffectSnapshots.withEvidence(new NativeEffectRegistry.Projected(live.result(),Optional.of(legacyRaw)),List.of(basis));
        var observation=assertInstanceOf(ActionPorts.EffectObserved.class,old.result()).observation();
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,unknown,new ActionState.Applied(observation)));
        var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        assertDoesNotThrow(()->replay(command,receipt,archive,loader));
        legacy.put("event_result_projection_schema","unqualified-event-result-version");RawJson wrongRaw=new RawJson(StrictJson.canonical(legacy,1<<20));
        ExactRef wrongBasis=snapshots.evidence(command,attempt,pair[0],List.of(),wrongRaw,List.of());
        var wrong=NativeEffectSnapshots.withEvidence(new NativeEffectRegistry.Projected(live.result(),Optional.of(wrongRaw)),List.of(wrongBasis));
        var wrongObservation=assertInstanceOf(ActionPorts.EffectObserved.class,wrong.result()).observation();
        var wrongReceipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,unknown,new ActionState.Applied(wrongObservation)));
        assertThrows(IllegalArgumentException.class,()->replay(command,wrongReceipt,archive,loader));
    }
    @Test void missingMaterialObservationDoesNotEraseIndependentlyConsumedModalOrGrantMaterialCredit() throws InterruptedException {
        var archive = new Archive(); var held = held(archive, true); var before = held.observe(DEADLINE);
        var command = command(before, true); var attempt = attempt(command, before);
        var unknown = new NativeActionPort.Unknown(attempt.requestId(), "unknown", new byte[]{1}, Optional.empty());
        var result = new NativeEventEffects(new NativeEffectSnapshots(held, archive), NO_READS, queries()).observe(command, attempt, unknown);
        assertInstanceOf(ActionPorts.EffectObserved.class, result.result());
        JsonNode value = StrictJson.parse(result.compatibleResult().orElseThrow().bytes());
        assertTrue(value.path("event_selection").path("postcondition_verified").booleanValue());
        assertEquals("unavailable", value.path("event_material_postcondition").path("status").textValue());
        assertTrue(value.path("event_material_postcondition").path("material_change_observed").isNull());
    }
    @Test void unknownWithoutIndependentConsumptionDoesNotInvokeTheIncidentJournal() throws InterruptedException {
        var archive = new Archive(); var held = held(archive, false); var before = held.observe(DEADLINE);
        var command = command(before, false); var attempt = attempt(command, before);
        var unknown = new NativeActionPort.Unknown(attempt.requestId(), "unknown unchanged", new byte[]{1}, Optional.empty());
        var output = new NativeEventEffects(new NativeEffectSnapshots(held, archive), NO_READS, queries(),
            (ignoredCommand, ignoredAttempt, ignoredPair, ignoredResult) -> fail("unknown pending cannot create an incident after")).observe(command, attempt, unknown);
        assertInstanceOf(ActionPorts.Pending.class, output.result());
        assertTrue(output.compatibleResult().isEmpty());
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef, RawJson> materials = new HashMap<>(); private final Map<ExactRef, byte[]> nativeFrames = new HashMap<>();
        private static ExactRef ref(String kind, byte[] raw) { return new ExactRef("memory/" + kind + "/" + DriverJson.sha256(raw), raw.length, DriverJson.sha256(raw)); }
        @Override public ExactRef preserveMaterial(RawJson raw) { var reference = ref("material", raw.bytes()); materials.putIfAbsent(reference, raw); return reference; }
        @Override public RawJson loadMaterial(ExactRef reference) { return java.util.Objects.requireNonNull(materials.get(reference)); }
        @Override public ExactRef materialReferenceOf(RawJson raw) { var reference = ref("material", raw.bytes()); assertEquals(raw, materials.get(reference)); return reference; }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame raw) { var reference = ref("native", raw.originalPacket()); nativeFrames.putIfAbsent(reference, raw.originalPacket()); return reference; }
        @Override public byte[] loadNativeFrame(ExactRef reference) { return java.util.Objects.requireNonNull(nativeFrames.get(reference)).clone(); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw) { throw new UnsupportedOperationException(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRequest(NativeRequest raw) { throw new UnsupportedOperationException(); }
        @Override public NativeRequest loadRequest(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef requestReferenceOf(NativeRequest raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt raw) { throw new UnsupportedOperationException(); }
        @Override public PlanningReadReceipt loadRead(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRecord(ActionRecord raw) { throw new UnsupportedOperationException(); }
        @Override public ActionRecord loadRecord(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef recordReferenceOf(ActionRecord raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveReceipt(ActionReceipt raw) { throw new UnsupportedOperationException(); }
        @Override public ActionReceipt loadReceipt(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw) { throw new UnsupportedOperationException(); }
    }
}
