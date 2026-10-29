package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Same-packet software producer-to-consumer regression; constructed receipt DATA grants no Root, writer or gameplay qualification. */
final class GuiDecisionNativeCampaignTest {
    private static final Instant NOW = Instant.parse("2026-10-24T23:00:00Z");
    private static final String KEY = "ervc_courtier_creator_decision";
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"fixture-pipe","bridge_pid":42,"episode_character_id":311,"episode_run_id":"private-stage-episode",
         "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,
         "succession_expectation":null,"succession_lifecycle":null,"campaign_goal":{"original":"retained"},"rollback_war_failures":[]}
        """;
    private record Original(GuiModels.Context context, RawJson snapshot, RawJson beforeSource) { }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String name, byte[] wire) { return new ExactRef("D:/software-data/" + name, wire.length, DriverJson.sha256(wire)); }
    private static ExactRef ref(String name) { return ref(name, bytes(name)); }
    private static RawJson raw(ObjectNode value) { return PublicDataJson.encode(value); }

    private static Original original(String episodeFields, int nativeRevision, int publicRevision) {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var auxiliary = new OpportunityJson.Obj(Map.of("episode_projection", new OpportunityJson.Text("native_campaign")));
        var before = DriverFactsRepository.imported(ref("driver", bytes(DRIVER)), bytes(DRIVER), 7, 3, game, auxiliary);
        String id = "native-gui-profile4-" + nativeRevision;
        String state = "{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":53144328,"
                + "\"played_character\":{\"character_id\":922,\"alive\":true},\"active_event\":null,"
                + "\"pending_character_interaction\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{}" + episodeFields + "}";
        byte[] body = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"" + id
                + "\",\"revision\":" + nativeRevision + ",\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("fixture-machine", game, BigInteger.valueOf(5), "fixture-session"),
                id, BigInteger.valueOf(nativeRevision), new RawJson(bytes(state)), packet, NOW);
        var projected = InitialDriverState.fixtureActorProjection(before, actual, before.auxiliary());
        var source = new G2Source("fixture-machine", NOW.toString(), "software original fixture source", ref("sources"));
        var manifest = DriverObservationEvidenceReader.encode(projected, actual, BigInteger.valueOf(publicRevision),
                DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION, source, projected.auxiliary(), ref("full-driver", projected.driver().encode()));
        var restored = DriverObservationEvidenceReader.nativeFrame(ref("manifest", manifest.bytes()), manifest, packet);
        var facts = DriverObservationEvidenceReader.decode(ref("manifest", manifest.bytes()), manifest, RawJson.fullMaterial(projected.driver().encode()), restored);
        var assembled = new DriverObservationAssembler().assemble(restored, facts, ref("native", packet));
        var complete = assertInstanceOf(DriverObservationAssembler.Complete.class, assembled);
        var publicContext = DriverPublicContext.from(complete);
        var context = new GuiModels.Context(complete.identity(), complete.source(), complete.sessionId(), complete.connectionGeneration(), GuiModels.Build.CROZIER3, NOW.plusSeconds(60));
        return new Original(context, publicContext.snapshot(), GuiPublicMetadata.beforeSource(publicContext.snapshot(), publicContext.diagnostics()));
    }

    private static OpportunityJson.Obj arguments(Request request, GuiModels.Context context) {
        ObjectNode fields = GuiCodec.encodeRequest(request); fields.remove("expected_revision");
        if (request.method() == Method.CONFIRM_OUTCOME) fields.put("expected_event_definition_key", "");
        fields.put("_gui_build", context.build().name()).put("_gui_generation", context.connectionGeneration());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)), "software decision arguments");
    }
    private static GuardEvidence guard(GuiModels.Context context, String operation) {
        return new GuardEvidence(context.before(), context.source(), context.sessionId(), context.connectionGeneration(), new OperationKey(operation),
                ref("guard-native"), ref("guard-capability"), "software-data-only", NOW, NOW.plusSeconds(60));
    }
    private static NativeActionPort.AckReceived ack(String id, RawJson token) {
        byte[] packet = StrictJson.canonical(StrictJson.object().put("request_id", id).put("ok", true));
        return new NativeActionPort.AckReceived(id, true, Optional.of(token), raw(StrictJson.object().put("software_data", true)), packet);
    }
    private static PlanningReadReceipt read(GuiModels.Context context, String operation, OpportunityJson.Obj fields, RawJson token) {
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(), new OperationKey(operation), fields, context.deadline());
        var guard = new PlanningReadGuard(guard(context, operation), true, true, true, "a".repeat(64));
        return new PlanningReadReceipt(request, "software-data:" + operation, "software-read", guard, guard, ack("software-read", token));
    }

    @Test void actualProfileFourReadWrapperPublishesOriginalMissingNullOrValueWithoutInventingEpisode() {
        for (String fields : List.of("", ",\"episode_run_id\":null", ",\"episode_run_id\":\"original-native-episode\"")) {
            var original = original(fields, 9, 12); var context = original.context();
            assertEquals("private-stage-episode", context.before().frame().episodeRunId());
            var request = new Request(Method.QUERY_DECISION, new Decision(new GuiModels.DecisionKey(KEY)), new PublicUnsigned64.Value(context.before().frame().revision()));
            var token = raw(StrictJson.object().put("schema", "ck3-ingame-decision-item-v1").put("decision_key", KEY));
            var receipt = read(context, "query-ingame-decision-item-v1", arguments(request, context), token);
            var reply = new ReadReply(receipt, ref("read"), Optional.of(original.beforeSource()), Optional.empty());
            ObjectNode output = PublicDataJson.object(GuiDecisionPublicFormatter.read(request, reply, Optional.of(context)));
            var actual = PublicDataJson.object(original.snapshot()).get("episode_run_id");
            assertEquals(actual == null ? com.fasterxml.jackson.databind.node.NullNode.instance : actual, output.get("episode_run_id"));
            assertTrue(output.has("episode_run_id"));
            assertEquals(!fields.isEmpty(), PublicDataJson.object(original.snapshot()).has("episode_run_id"));
        }
    }

    @Test void actualProfileFourOutcomeUsesIndependentProducerAndRejectsWrongEpisodeOrMarker() {
        for (String fields : List.of("", ",\"episode_run_id\":null", ",\"episode_run_id\":\"original-native-episode\"")) {
            var original = original(fields, 9, 12); var context = original.context();
            String afterFields = fields.isEmpty() ? ",\"episode_run_id\":null" : fields.equals(",\"episode_run_id\":null") ? "" : fields;
            var after = original(afterFields, 10, 13);
            var request = new Request(Method.CONFIRM_OUTCOME, new ConfirmOutcome(new GuiModels.DecisionKey(KEY), GuiModels.Outcome.DECISION_CLOSED, new Absent<>()), new PublicUnsigned64.Value(context.before().frame().revision()));
            var expected = new ExpectedPostcondition(1, context.before(), context.source(), "software.gui-observer/v1", List.of(new ExpectedBoolean(new FieldKey("gui.actual"), true)));
            String operation = "confirm-ingame-decision-outcome-v1";
            var command = new ActionCommand("software-profile4-action", context.before(), context.source(), context.sessionId(), new OperationKey(operation), arguments(request, context), expected,
                    new JointBudgetSelector.Claims(java.util.Set.of(), java.util.Set.of(), java.util.Set.of(), java.util.Set.of()), context.deadline());
            var attempt = new ActionState.Attempt("software-native", NOW, guard(context, operation), new NativeRequest(operation, "game.command." + operation, raw(StrictJson.object())));
            var acknowledgement = ack("software-native", raw(StrictJson.object().put("schema", "ck3-ingame-decision-outcome-confirm-v1")));
            ObjectNode tree = StrictJson.object().put("schema", "ck3-native-gui-window-tree-inspection-v1").put("window_kind", "decision_detail").put("root_available", false).put("truncated", false); tree.putArray("widgets");
            RawJson later = raw(tree);
            var settlement = new ActionState.ControlApplied(read(context, "inspect-gui-window-tree-v1", new OpportunityJson.Obj(Map.of("window_kind", new OpportunityJson.Text("decision_detail"))), later), "software.gui-observer/v1", expected.values());
            var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, acknowledgement, settlement));
            byte[] data = ActionCodec.encodeCommand(command);
            var reply = new ActionReply(receipt, data, ref("canonical-data", data), Optional.of(original.beforeSource()), Optional.empty());
            ObjectNode output = PublicDataJson.object(GuiDecisionPublicFormatter.action(request, reply, context, Optional.of(later), Optional.of(after.snapshot())));
            assertEquals(GuiPublicMetadata.episodeRunId(context, original.beforeSource()), output.get("episode_run_id"));
            assertFalse(output.get("business_effects_verified").booleanValue()); assertFalse(output.get("full_product_acceptance_credit").booleanValue());
            ObjectNode noMarker = PublicDataJson.object(after.snapshot()); noMarker.remove("xar_java_snapshot_projection");
            assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, context, Optional.of(later), Optional.of(PublicDataJson.encodeFullMaterial(noMarker))));
            ObjectNode wrongMarker = PublicDataJson.object(after.snapshot()); ((ObjectNode) wrongMarker.get("xar_java_snapshot_projection")).put("observation_version", 3);
            assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, context, Optional.of(later), Optional.of(PublicDataJson.encodeFullMaterial(wrongMarker))));
            var wrongEpisode = original(",\"episode_run_id\":\"changed-native-episode\"", 10, 13);
            assertThrows(IllegalArgumentException.class, () -> GuiDecisionPublicFormatter.action(request, reply, context, Optional.of(later), Optional.of(wrongEpisode.snapshot())));
        }
    }
}
