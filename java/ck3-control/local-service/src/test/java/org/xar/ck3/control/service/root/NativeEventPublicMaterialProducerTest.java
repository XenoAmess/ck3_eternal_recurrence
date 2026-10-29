package org.xar.ck3.control.service.root;

import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
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
import org.xar.ck3.control.application.planning.events.EventSelectionPublicResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventtraits.*;

/** Actual framed producer -> complete Driver manifest -> event observer -> archive -> same domain replay. */
final class NativeEventPublicMaterialProducerTest {
    static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json",raw.length,DriverJson.sha256(raw)); }
    static GameGeneration game() { return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    static DriverSnapshotFacts.Known known() {
        return DriverFactsRepository.imported(ref(bytes(WIRE)),bytes(WIRE),3,7,game(),new OpportunityJson.Obj(java.util.Map.of()));
    }
    static G2Source source() { return new G2Source("test-machine","2026-10-23T16:00:00Z","test-source",ref(bytes("original-source"))); }
    private static final Instant DEADLINE = Instant.parse("2030-01-01T00:00:00Z");
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":10660101,
         "played_character":{"character_id":73,"alive":true,"stress_points":10},
         "active_event":{"instance_id":17,"option_count":3},"pending_character_interaction":null,
         "one_life_terminal_reason":null,"active_wars":[],"player_armies":[]}
        """;
    private static NativeObservationPort.ObservedFrame frame(long revision, boolean advanced) {
        String state = advanced ? STATE.replace("{\"instance_id\":17,\"option_count\":3}", "null") : STATE;
        byte[] body = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-" + revision + "\",\"revision\":" + revision + ",\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine", game(), BigInteger.valueOf(5), "held-session"),
            "snapshot-" + revision, BigInteger.valueOf(revision), new RawJson(bytes(state)), packet,
            Instant.parse("2026-10-23T16:00:00Z").plusSeconds(advanced?1:0));
    }
    private static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual, Archive archive) {
        var known = known(); RawJson full = new RawJson(known.driver().encode()); ExactRef fullRef = archive.preserveMaterial(full);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, actual.nativeRevision(), 1,
            source(), new OpportunityJson.Obj(Map.of()), fullRef);
        ExactRef reference = archive.preserveMaterial(manifest);
        return DriverObservationEvidenceReader.decode(reference, manifest, full, actual);
    }
    private static ActionCommand command(DriverObservationAssembler.Complete before, boolean poet) {
        var args = StrictJson.object().put("selected_step","select-event-option-1").put("event_instance_id",17)
                .put("option_number",1).put("native_option_index",0).put("rendered_index",0);
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
        return new HeldDriverObservationPort(deadline -> frame(sequence.getAndIncrement() == 0 ? 9007199254740993L : 9007199254740994L, sequence.get() > 1 && advance),
            actual -> new DriverObservationFacts.Known(facts(actual, archive)), archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
    }

    record Produced(ActionReceipt receipt, NativeEffectEvidence.Original material,ActionPorts.OutcomeArchive archive) { }
    /** Actual framed native producer and installed effects/archive replay, before either public codec runs. */
    static Produced produced() throws InterruptedException {
        var archive = new Archive(); var held = held(archive, true); var before = held.observe(DEADLINE);
        var command = command(before, false); var attempt = attempt(command, before);
        var dispatch = new NativeActionPort.Unknown(attempt.requestId(), "unknown original result", new byte[]{1}, Optional.empty());
        var projected = new NativeEventEffects(new NativeEffectSnapshots(held, archive), NO_READS, queries()).observe(command, attempt, dispatch);
        var observed = assertInstanceOf(ActionPorts.EffectObserved.class, projected.result()).observation();
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Settled(attempt, dispatch, new ActionState.Applied(observed)));
        var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        NativeEventEffects.archivedVerifier(command.operation(), ref(new byte[]{1}), loader, queries())
                .verifier().verify(null, receipt, archive);
        archive.preserveReceipt(receipt);
        assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,archive),archive));
        return new Produced(receipt, NativeEffectEvidence.load(receipt, archive, loader),archive);
    }
    @Test void actualProducerAndArchivedReplayReachPublic64AndInverseWithoutChangingOriginals() throws InterruptedException {
        Produced actual=produced();byte[] original=actual.material().compatibleResult().bytes();
        RawJson wire=EventSelectionPublicResult.encode(actual.receipt(),actual.material());
        JsonNode parsed=StrictJson.parse(wire.bytes());JsonNode selection=parsed.get("event_selection");
        assertEquals("xar.event-material-public64/v1",parsed.get("event_material_wire_encoding").textValue());
        assertEquals("9007199254740993",selection.get("starting_revision").textValue());
        assertEquals("9007199254740994",selection.get("ending_revision").textValue());
        assertEquals("5",selection.get("connection_generation").textValue());
        assertTrue(selection.get("selected_option_number").isIntegralNumber());
        assertTrue(selection.get("old_event_instance_id").isIntegralNumber());
        assertTrue(selection.get("starting_played_character_gold").get("gold_raw").isNull());
        assertEquals(StrictJson.parse(original),StrictJson.parse(EventSelectionPublicResult.parse(wire).bytes()));
        assertArrayEquals(original,actual.material().compatibleResult().bytes());
        assertFalse(actual.receipt().eligibleAdvance());
        // The one public response may add safe, separately validated request metadata.
        var wrapped=(com.fasterxml.jackson.databind.node.ObjectNode)parsed;
        wrapped.put("event_instance_id",17).put("option_number",1).put("option_index",0);
        assertDoesNotThrow(()->EventSelectionPublicResult.parse(new RawJson(StrictJson.canonical(wrapped))));
    }
    @Test void differentInstanceChoiceRevisionOrWrongIntegerTokenCannotBecomePublicMaterial() throws InterruptedException {
        Produced actual=produced();
        for(String field:List.of("old_event_instance_id","selected_option_number","starting_revision")) {
            var body=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(actual.material().compatibleResult().bytes());
            ((com.fasterxml.jackson.databind.node.ObjectNode)body.get("event_selection")).put(field,18);
            var changed=new NativeEffectEvidence.Original(actual.material().frames(),actual.material().independentReads(),
                    new RawJson(StrictJson.canonical(body)),actual.material().supportingMaterials(),actual.material().reconciliationGuard());
            assertThrows(IllegalArgumentException.class,()->EventSelectionPublicResult.encode(actual.receipt(),changed));
        }
        RawJson wire=EventSelectionPublicResult.encode(actual.receipt(),actual.material());
        for(JsonNode token:List.of(StrictJson.parse("true".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                StrictJson.parse("9.0".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                StrictJson.parse("\"09007199254740993\"".getBytes(java.nio.charset.StandardCharsets.UTF_8)))) {
            var body=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(wire.bytes());
            ((com.fasterxml.jackson.databind.node.ObjectNode)body.get("event_selection")).set("starting_revision",token);
            assertThrows(IllegalArgumentException.class,()->EventSelectionPublicResult.parse(new RawJson(StrictJson.canonical(body))));
        }
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(wire.bytes());
        ((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("event_selection")).remove("selected_option_number");
        assertThrows(IllegalArgumentException.class,()->EventSelectionPublicResult.parse(new RawJson(StrictJson.canonical(missing))));
    }
    @Test void signedRawFileIdentityAndNullEmptyMissingHaveOneReversiblePublicRepresentation() throws InterruptedException {
        Produced actual=produced();var body=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(actual.material().compatibleResult().bytes());
        var extra=body.putObject("typed_boundary_fixture");
        extra.put("file_id",new BigInteger("18446744073709551615"));
        extra.put("process_birth_filetime",new BigInteger("134000000000000001"));
        extra.put("gold_raw",Long.MIN_VALUE).putNull("fulfillment_raw").put("starting_value",false).put("ending_value",true);extra.putArray("empty");
        var changed=new NativeEffectEvidence.Original(actual.material().frames(),actual.material().independentReads(),
                new RawJson(StrictJson.canonical(body)),actual.material().supportingMaterials(),actual.material().reconciliationGuard());
        RawJson wire=EventSelectionPublicResult.encode(actual.receipt(),changed);JsonNode encoded=StrictJson.parse(wire.bytes());
        assertEquals("18446744073709551615",encoded.path("typed_boundary_fixture").path("file_id").textValue());
        assertEquals("-9223372036854775808",encoded.path("typed_boundary_fixture").path("gold_raw").textValue());
        assertEquals(body,StrictJson.parse(EventSelectionPublicResult.parse(wire).bytes()));
        assertFalse(encoded.path("typed_boundary_fixture").has("missing"));
        assertTrue(encoded.path("typed_boundary_fixture").path("fulfillment_raw").isNull());
        assertTrue(encoded.path("typed_boundary_fixture").path("empty").isArray());
        extra.put("undeclared_identity",new BigInteger("9007199254740993"));
        var unsafe=new NativeEffectEvidence.Original(actual.material().frames(),actual.material().independentReads(),
                new RawJson(StrictJson.canonical(body)),actual.material().supportingMaterials(),actual.material().reconciliationGuard());
        assertThrows(IllegalArgumentException.class,()->EventSelectionPublicResult.encode(actual.receipt(),unsafe));
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> dispatches=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        private final Map<ExactRef, RawJson> materials = new HashMap<>(); private final Map<ExactRef, byte[]> nativeFrames = new HashMap<>();
        private static ExactRef ref(String kind, byte[] raw) { return new ExactRef("memory/" + kind + "/" + DriverJson.sha256(raw), raw.length, DriverJson.sha256(raw)); }
        @Override public ExactRef preserveMaterial(RawJson raw) { var reference = ref("material", raw.bytes()); materials.putIfAbsent(reference, raw); return reference; }
        @Override public RawJson loadMaterial(ExactRef reference) { return java.util.Objects.requireNonNull(materials.get(reference)); }
        @Override public ExactRef materialReferenceOf(RawJson raw) { var reference = ref("material", raw.bytes()); assertEquals(raw, materials.get(reference)); return reference; }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame raw) { var reference = ref("native", raw.originalPacket()); nativeFrames.putIfAbsent(reference, raw.originalPacket()); return reference; }
        @Override public byte[] loadNativeFrame(ExactRef reference) { return java.util.Objects.requireNonNull(nativeFrames.get(reference)).clone(); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw) { var unknown=assertInstanceOf(NativeActionPort.Unknown.class,raw);ExactRef key=ref("dispatch",unknown.originalRequestPacket());dispatches.putIfAbsent(key,raw);return key; }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef reference) { return java.util.Objects.requireNonNull(dispatches.get(reference)); }
        @Override public ExactRef preserveRequest(NativeRequest raw) { var body=StrictJson.object().put("step",raw.step()).put("capability",raw.requiredCapability().orElse(""));body.set("additional",DriverJson.toNode(DriverJson.object(raw.additionalFields().bytes(),RawJson.MAXIMUM_BYTES)));ExactRef key=ref("request",DriverJson.encodeNode(body));requests.putIfAbsent(key,raw);return key; }
        @Override public NativeRequest loadRequest(ExactRef reference) { return java.util.Objects.requireNonNull(requests.get(reference)); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw) { return preserve(raw); }
        @Override public ExactRef requestReferenceOf(NativeRequest raw) { return preserveRequest(raw); }
        @Override public ExactRef preserveRead(PlanningReadReceipt raw) { throw new UnsupportedOperationException(); }
        @Override public PlanningReadReceipt loadRead(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveRecord(ActionRecord raw) { throw new UnsupportedOperationException(); }
        @Override public ActionRecord loadRecord(ExactRef reference) { throw new UnsupportedOperationException(); }
        @Override public ExactRef recordReferenceOf(ActionRecord raw) { throw new UnsupportedOperationException(); }
        @Override public ExactRef preserveReceipt(ActionReceipt raw) { ExactRef key=ref("receipt",ActionReceiptCodec.encodeReceipt(raw,this));receipts.putIfAbsent(key,raw);return key; }
        @Override public ActionReceipt loadReceipt(ExactRef reference) { return java.util.Objects.requireNonNull(receipts.get(reference)); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw) { ExactRef key=ref("receipt",ActionReceiptCodec.encodeReceipt(raw,this));assertEquals(raw,receipts.get(key));return key; }
    }
}
