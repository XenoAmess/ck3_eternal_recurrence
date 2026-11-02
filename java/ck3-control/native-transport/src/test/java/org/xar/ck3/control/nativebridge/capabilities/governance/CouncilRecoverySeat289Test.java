package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;
import org.xar.ck3.control.application.action.council.CouncilContinuationReceipt;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Controlled software DATA only; no actual canonical custody, Root permission, query or Game is claimed. */
final class CouncilRecoverySeat289Test {
    private static final Instant T = Instant.parse("2026-11-02T01:00:00Z");
    private static final String VERSION = "1.20.0.2";
    private static final String BUILD = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final String SESSION = "software-council-seat289";
    private static final String ORIGINAL_ID = "controlled-assignment289";
    private static final int OWNER = 16777217, CANDIDATE = 16777232, DATE = 53175816;
    private static final UUID EPOCH = UUID.fromString("f0417bbe-7848-429b-af72-f601669e9289");
    private static final String AVAILABLE_JSON = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"status-available-result\",\"ok\":true,\"result\":{\"schema\":\"xar.ck3.council-application-main/v1\",\"step\":\"query-council-composition-candidates-v1\",\"accepted\":true,\"status\":\"available\",\"query_sequence\":2,\"snapshot_revision\":13,\"council_composition_candidates\":{\"schema\":\"xar.ck3.council-composition-candidates/v1\",\"schema_version\":1,\"capability\":\"game.query.council-composition-candidates-v1\",\"exact_build\":{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\"},\"status\":\"available\",\"unavailable_reason\":null,\"source_unavailable_reason\":null,\"snapshot\":{\"snapshot_id\":\"native:13\",\"public_revision\":13,\"native_revision\":13,\"date_raw\":53175816,\"paused\":true},\"owner_character_id\":16777217,\"position\":{\"position_key\":\"councillor_steward\",\"incumbent_character_id\":16777218,\"incumbent_main_skill\":{\"key\":\"stewardship\",\"value\":9},\"vacant\":false,\"action_route\":\"replace\"},\"candidate_collection_complete\":true,\"candidates\":[{\"character_id\":16777232,\"native_collection_ordinal\":1,\"eligible\":true,\"eligibility_reason\":\"native_candidate_provider_accepted\",\"main_skill\":{\"key\":\"stewardship\",\"value\":22},\"action_route\":\"replace\"},{\"character_id\":16777233,\"native_collection_ordinal\":0,\"eligible\":true,\"eligibility_reason\":\"native_candidate_provider_accepted\",\"main_skill\":{\"key\":\"stewardship\",\"value\":17},\"action_route\":\"replace\"}],\"readiness\":{\"identity_ready\":true,\"candidate_collection_ready\":true,\"incumbent_ready\":true,\"incumbent_main_skill_ready\":true,\"candidate_legality_ready\":true,\"main_skill_ready\":true,\"action_route_ready\":true,\"same_frame_ready\":true,\"ready\":true}},\"backend_id\":\"native-headless\"}}";
    private static final String GATES_JSON = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"wire:council12002\",\"ok\":true,\"result\":{\"schema\":\"xar.ck3.council-application-main/v1\",\"step\":\"private-query-council-final-gates-v1\",\"accepted\":true,\"status\":\"available\",\"query_sequence\":2,\"snapshot_revision\":8,\"private\":true,\"advertised\":false,\"native_helper_invocations_delta\":0,\"council_final_gates\":{\"schema\":\"xar.ck3.private.council-final-gates/v1\",\"status\":\"available\",\"unavailable_reason\":\"none\",\"candidate_count\":2,\"rows\":[{\"character_id\":16777232,\"native_collection_ordinal\":1,\"final_gate_available\":true,\"candidate_already_councillor\":false,\"candidate_is_guest\":false,\"pending_character_interaction\":false,\"incumbent_fireability_evaluated\":true,\"incumbent_can_be_fired\":true},{\"character_id\":16777233,\"native_collection_ordinal\":0,\"final_gate_available\":true,\"candidate_already_councillor\":false,\"candidate_is_guest\":false,\"pending_character_interaction\":false,\"incumbent_fireability_evaluated\":true,\"incumbent_can_be_fired\":true}],\"council_composition_candidates\":{\"schema\":\"xar.ck3.council-composition-candidates/v1\",\"schema_version\":1,\"capability\":\"game.query.council-composition-candidates-v1\",\"exact_build\":{\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\"},\"status\":\"available\",\"unavailable_reason\":null,\"source_unavailable_reason\":null,\"snapshot\":{\"snapshot_id\":\"native:council12002\",\"public_revision\":8,\"native_revision\":7,\"date_raw\":53178264,\"paused\":true},\"owner_character_id\":16777217,\"position\":{\"position_key\":\"councillor_steward\",\"incumbent_character_id\":16777218,\"incumbent_main_skill\":{\"key\":\"stewardship\",\"value\":9},\"vacant\":false,\"action_route\":\"replace\"},\"candidate_collection_complete\":true,\"candidates\":[{\"character_id\":16777232,\"native_collection_ordinal\":1,\"eligible\":true,\"eligibility_reason\":\"native_candidate_provider_accepted\",\"main_skill\":{\"key\":\"stewardship\",\"value\":22},\"action_route\":\"replace\"},{\"character_id\":16777233,\"native_collection_ordinal\":0,\"eligible\":true,\"eligibility_reason\":\"native_candidate_provider_accepted\",\"main_skill\":{\"key\":\"stewardship\",\"value\":17},\"action_route\":\"replace\"}],\"readiness\":{\"identity_ready\":true,\"candidate_collection_ready\":true,\"incumbent_ready\":true,\"incumbent_main_skill_ready\":true,\"candidate_legality_ready\":true,\"main_skill_ready\":true,\"action_route_ready\":true,\"same_frame_ready\":true,\"ready\":true}}},\"backend_id\":\"native-headless\"}}";
    private record Scene(ActionCommand command, ActionState.Attempt attempt, CouncilActionCodec.Receipt applied,
            NativeEffectSnapshots.Pair pair, GuardEvidence observation, PrivateCouncilReads definitions,
            ObjectNode terminal, PlanningReadReceipt pendingRead, PlanningReadReceipt terminalRead) { }
    private static BigInteger n(long value) { return BigInteger.valueOf(value); }
    private static ExactRef ref(String role) {
        return new ExactRef("software-seat289-" + role, 1, ActionCodec.sha256(role.getBytes(StandardCharsets.UTF_8)));
    }
    private static ObjectNode json(String text) { return CouncilCodec.object(StrictJson.parse(text.getBytes(StandardCharsets.UTF_8))); }
    private static OpportunityJson.Obj semantic(ExactRef facts) {
        return new OpportunityJson.Obj(Map.of()).with("java_driver_facts_evidence", OpportunityJson.parse(StrictJson.canonical(facts.toJson())));
    }
    private static ProposalLifecycle.ObservationIdentity frame(G2Source source, long nativeRevision, long publicRevision) {
        return new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(n(OWNER), n(nativeRevision), n(DATE)),
                        "public:" + publicRevision, n(publicRevision), "software-council-seat-episode"), 1);
    }
    private static ObjectNode available(long revision, int incumbent) {
        ObjectNode result = CouncilCodec.object(json(AVAILABLE_JSON).get("result")).deepCopy();
        result.put("snapshot_revision", revision);
        ObjectNode payload = CouncilCodec.object(result.get("council_composition_candidates"));
        CouncilCodec.object(payload.get("snapshot")).put("snapshot_id", "native:" + revision)
                .put("native_revision", revision).put("public_revision", revision);
        CouncilCodec.object(payload.get("position")).put("incumbent_character_id", incumbent);
        return result;
    }
    private static Scene scene(long afterNative) throws Exception {
        var source = new G2Source("software-seat-machine", T.toString(), VERSION, ref("source"));
        var original = frame(source, 110, 80); var current = frame(source, afterNative, 82);
        var available = available(110, 16777218);
        var gates = CouncilCodec.object(CouncilCodec.object(json(GATES_JSON).get("result")).get("council_final_gates")).deepCopy();
        gates.set("council_composition_candidates", available.get("council_composition_candidates"));
        var gateEnvelope = available.deepCopy().put("step", CouncilPrivateCodec.GATES);
        gateEnvelope.remove("council_composition_candidates"); gateEnvelope.set("council_final_gates", gates);
        var gateTerminal = (CouncilPrivateCodec.Terminal) CouncilPrivateCodec.decodeReply(StrictJson.canonical(gateEnvelope), CouncilPrivateCodec.STATUS);
        var normalized = CouncilPrivateCodec.normalize(gateTerminal, CouncilPrivateCodec.GATES,
                new CouncilModels.Frame("native:110", n(110), n(110), DATE, OWNER),
                new CouncilModels.Frame("public:80", n(80), n(110), DATE, OWNER), CouncilModels.Position.STEWARD, VERSION, BUILD);
        var args = new OpportunityJson.Obj(Map.of()).with("position_key", new OpportunityJson.Text("councillor_steward"))
                .with("candidate_character_id", new OpportunityJson.IntegerValue(n(CANDIDATE)))
                .with("original_query", OpportunityJson.parse(normalized.bytes()))
                .with("expected_has_incumbent", new OpportunityJson.Bool(true))
                .with("expected_incumbent_character_id", new OpportunityJson.IntegerValue(n(16777218)));
        var operation = new OperationKey(CouncilActionCodec.PRIVATE_ASSIGN);
        var post = new ProposalLifecycle.ExpectedPostcondition(1, original, source, "software-seat289/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        var command = new ActionCommand("controlled-seat289", original, source, SESSION, operation, args, post,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), T.plusSeconds(60));
        var expected = GovernanceActionPreparation.councilRequest(command, ORIGINAL_ID);
        var prepared = new NativeRequest(operation.value(), Optional.empty(), new RawJson(StrictJson.canonical(CouncilActionCodec.wireFields(expected, true))));
        var oldGuard = new GuardEvidence(original, source, SESSION, n(1), operation, ref("before-native"), ref("before-hello"),
                "controlled-seat-authority", T, T.plusSeconds(60));
        var attempt = new ActionState.Attempt(ORIGINAL_ID, T.plusSeconds(1), oldGuard, prepared);
        var helper = StrictJson.object().put("status", "native_helper_invoked_verification_pending").put("failure", "none")
                .put("action_request_id", ORIGINAL_ID).put("pre_snapshot_id", "native:110").put("pre_public_revision", 110)
                .put("pre_native_revision", 110).put("pre_date_raw", DATE).put("owner_character_id", OWNER)
                .put("position_key", "councillor_steward").put("active_task_id", 6100).put("candidate_character_id", CANDIDATE)
                .put("had_incumbent", true).put("previous_incumbent_character_id", 16777218).put("route", "replace_incumbent")
                .put("native_helper_invoked", true).put("queue_acceptance_observed", false).put("verification_pending", true).put("native_reason_key", "");
        var ack = CouncilActionCodec.decodeAck(StrictJson.canonical(helper), expected);
        var receipt = StrictJson.object().put("status", "applied").put("rejected_action_failure", "none").put("action_request_id", ORIGINAL_ID)
                .put("post_snapshot_id", "native:117").put("post_public_revision", 117).put("post_native_revision", 117)
                .put("post_date_raw", DATE).put("owner_character_id", OWNER).put("position_key", "councillor_steward")
                .put("incumbent_character_id", CANDIDATE).put("incumbent_identity_round_trip", true).put("postcondition_verified", true).put("reason", "");
        var applied = CouncilActionCodec.decodeReceipt(StrictJson.canonical(receipt), ack);
        var before = new Complete(original, source, SESSION, n(1), semantic(ref("before-facts")), oldGuard.nativeEvidence(), T, "a".repeat(64));
        var after = new Complete(current, source, SESSION, n(2), semantic(ref("after-facts")), ref("after-native"), T.plusSeconds(5), "b".repeat(64));
        var pending = new ReconciliationIdentity.Pending(command.actionId(), ActionCodec.bodySha256(command), ORIGINAL_ID, original,
                ref("canonical-pending"), ref("original-driver"));
        var evidence = new ReconciliationIdentity.Evidence(after.originalEvidence(), ref("after-hello"), ref("heartbeat"), ref("after-facts"),
                ref("original-driver"), ref("source-qualification"));
        var identity = new ReconciliationIdentity(current, source, SESSION, n(2), pending, evidence, after.observedAt());
        var observation = new GuardEvidence(new CommandOrigin.Reconciliation(identity), source, SESSION, n(2), operation,
                after.originalEvidence(), evidence.actualHello(), oldGuard.authorityId(), after.observedAt(), T.plusSeconds(60), identity.supportingEvidence());
        var pair = new NativeEffectSnapshots.Pair(before, after, Optional.of(identity));
        var definitions = new PrivateCouncilReads(ref("private-read-source"));
        ObjectNode terminal = available(afterNative, CANDIDATE);
        var pendingResult = StrictJson.object().put("private_council_transport", true).put("advertised", false)
                .put("step", CouncilPrivateCodec.QUERY).put("status", "pending");
        var pendingRead = read(pair, observation, definitions.query(), new OpportunityJson.Obj(Map.of()).with("position_key", new OpportunityJson.Text("councillor_steward")),
                "seat-query289", pendingResult, 10);
        var terminalRead = read(pair, observation, definitions.status(), new OpportunityJson.Obj(Map.of()), "seat-status289", terminal, 20);
        return new Scene(command, attempt, applied, pair, observation, definitions, terminal, pendingRead, terminalRead);
    }
    private static PlanningReadReceipt read(NativeEffectSnapshots.Pair pair, GuardEvidence observation, ReadContract<?> contract,
            OpportunityJson.Obj arguments, String id, ObjectNode result, long order) throws Exception {
        var after = pair.after();
        var request = new PlanningReadRequest(after.identity(), after.source(), after.sessionId(), contract.operation(), arguments, T.plusSeconds(60));
        var prepared = contract.prepare(request, id);
        byte[] outbound = contract.wireProfile() == ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS
                ? NativeWire.executeCouncilMailboxStatus(id, prepared.step(), prepared.additionalFields().bytes())
                : NativeWire.execute(id, prepared.step(), after.identity().frame().identity().nativeRevision(), prepared.additionalFields().bytes());
        var full = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true); full.set("result", result);
        byte[] body = StrictJson.canonical(full), incoming = NativeWire.packet(body);
        var guard = new GuardEvidence(after.identity(), after.source(), after.sessionId(), after.connectionGeneration(), contract.operation(),
                after.originalEvidence(), observation.capabilityEvidence(), "controlled-seat-read-authority", after.observedAt(), T.plusSeconds(60));
        var custody = new NativeRequestChronology(new NativeObservationPort.TransportSession(after.identity().machineId(), after.identity().game(), after.connectionGeneration(), after.sessionId()),
                EPOCH, id, NativeRequestChronology.PacketIdentity.of(outbound), NativeRequestChronology.PacketIdentity.of(incoming),
                new NativeRequestChronology.Event(n(order), T.plusSeconds(6).plusMillis(order)),
                new NativeRequestChronology.Event(n(order + 1), T.plusSeconds(6).plusMillis(order + 1)),
                new NativeRequestChronology.Event(n(order + 2), T.plusSeconds(6).plusMillis(order + 2)));
        var nativeAck = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(StrictJson.canonical(result))), new RawJson(body), incoming,
                Optional.of(new NativeActionPort.OutboundPacket(id, outbound)), Optional.of(custody));
        var bound = new PlanningReadGuard(guard, true, true, true, after.fullBindingSha256());
        return new PlanningReadReceipt(request, contract.contractId(), id, bound, bound, nativeAck);
    }
    private static List<PlanningReadReceipt> changedTerminal(Scene s, Consumer<ObjectNode> mutate) throws Exception {
        var terminal = s.terminal().deepCopy(); mutate.accept(terminal);
        return List.of(s.pendingRead(), read(s.pair(), s.observation(), s.definitions().status(), new OpportunityJson.Obj(Map.of()),
                "seat-status289", terminal, 20));
    }
    private static List<PlanningReadReceipt> terminalThenExtra(Scene s) throws Exception {
        var query = read(s.pair(), s.observation(), s.definitions().query(), s.pendingRead().request().arguments(), "seat-direct-query289", s.terminal(), 10);
        var pending = StrictJson.object().put("private_council_transport", true).put("advertised", false).put("step", CouncilPrivateCodec.STATUS).put("status", "pending");
        var extra = read(s.pair(), s.observation(), s.definitions().status(), new OpportunityJson.Obj(Map.of()), "seat-extra-status289", pending, 20);
        return List.of(query, extra);
    }
    private static CouncilModels.Candidates prove(Scene s, List<PlanningReadReceipt> reads) throws Exception {
        return CouncilRecoverySeatProof.require(s.command(), s.attempt(), s.applied(), s.pair(), s.observation(), reads, s.definitions(), VERSION, BUILD);
    }
    /** Isolated pure old-receipt-frame gate only; this does not claim canonical continuation membership. */
    private static void originalReceiptFrame(Scene s, long queryRevision) throws Exception {
        var scope = new Scope(s.command().actionId(), ActionCodec.bodySha256(s.command()), ORIGINAL_ID);
        var factual = frame(s.command().source(), queryRevision, 81);
        var guard = new GuardEvidence(factual, s.command().source(), SESSION, n(2), new OperationKey(CouncilActionCodec.PRIVATE_RECEIPT),
                ref("original-receipt-native"), ref("after-hello"), "controlled-seat-authority", T.plusSeconds(3), T.plusSeconds(60));
        var request = new Request(scope, "original-receipt-query289", Stage.RECEIPT_QUERY, ref("canonical-pending"), ref("prepared-receipt"), guard,
                T.plusSeconds(3), T.plusSeconds(60), 1, List.of(ref("original-preflight")));
        var item = new CouncilContinuationReceipt(request, Status.ACK, Optional.of(s.terminalRead().original()),
                new IssuedCustody(ref("issued"), ref("issued-domain"), ref("issued-event")), ref("resolved"), ref("result-domain"), ref("result-event"));
        var method = NativeCouncilAssignmentEffects.class.getDeclaredMethod("requireReceiptQueryFrame", List.class, CouncilActionCodec.Receipt.class);
        method.setAccessible(true);
        try { method.invoke(null, List.of(item), s.applied()); }
        catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof Exception actual) throw actual;
            if (failure.getCause() instanceof Error actual) throw actual;
            throw failure;
        }
    }

    @Test void pendingStatusCurrentSeatUsesNativeCounterAndExactPublicProjection() throws Exception {
    for (long nativeCounter : List.of(117L, 118L)) {
        var scene = scene(nativeCounter);
        var actual = prove(scene, List.of(scene.pendingRead(), scene.terminalRead()));
        assertEquals(nativeCounter, actual.frame().nativeRevision().longValueExact());
        assertEquals(nativeCounter, actual.frame().publicRevision().longValueExact());
        assertEquals(OWNER, actual.frame().ownerId());
        assertEquals(CouncilModels.Position.STEWARD, actual.seat().position());
        assertEquals(OptionalInt.of(CANDIDATE), actual.seat().incumbentId());
        assertEquals(BigInteger.valueOf(117), scene.applied().postNativeRevision());
        assertEquals(BigInteger.valueOf(82), scene.pair().after().identity().frame().revision());
    }
}

@Test void foreignSeatAndBrokenTerminalSequencesFailClosed() throws Exception {
    var scene = scene(117);
    assertThrows(IllegalArgumentException.class, () -> prove(scene, changedTerminal(scene, terminal -> CouncilCodec.object(CouncilCodec.object(terminal.get("council_composition_candidates")).get("position")).put("incumbent_character_id", 16777233))));
    assertThrows(IllegalArgumentException.class, () -> prove(scene, changedTerminal(scene, terminal -> CouncilCodec.object(terminal.get("council_composition_candidates")).put("owner_character_id", 16777218))));
    assertThrows(IllegalArgumentException.class, () -> prove(scene, changedTerminal(scene, terminal -> terminal.put("snapshot_revision", 118))));
    assertThrows(IllegalArgumentException.class, () -> prove(scene, List.of(scene.pendingRead())));
    assertThrows(IllegalArgumentException.class, () -> prove(scene, terminalThenExtra(scene)));
}

@Test void originalReceiptFrameStaysBoundTo117() throws Exception {
    var scene = scene(118);
    assertDoesNotThrow(() -> originalReceiptFrame(scene, 117));
    assertThrows(IllegalArgumentException.class, () -> originalReceiptFrame(scene, 116));
    assertThrows(IllegalArgumentException.class, () -> originalReceiptFrame(scene, 118));
}
}
