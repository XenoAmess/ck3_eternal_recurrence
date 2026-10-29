package org.xar.ck3.control.wave2.planning.playerrisk;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Context;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Status;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskConsumers.JournallerStressGate;

final class PlayerRiskContextTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = PlayerRiskContextTest.class.getResourceAsStream("/playerrisk/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("original producer golden required; capture not executed is failure, never skip"); }
            return StrictJson.parse(stream.readAllBytes(), 94_208);
        }
    }
    private static byte[] bytes(JsonNode value) {
        try { return new ObjectMapper().writeValueAsBytes(value); }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static ObjectNode input(JsonNode golden, JsonNode sample) {
        ObjectNode input = golden.get("baseline").deepCopy();
        for (JsonNode edit : sample.get("edits")) {
            JsonNode path = edit.get("path"), parent = input;
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode segment = path.get(index); parent = segment.isIntegralNumber() ? parent.get(segment.intValue()) : parent.get(segment.textValue());
            }
            JsonNode last = path.get(path.size() - 1);
            if (parent instanceof ObjectNode object) {
                if (edit.get("remove").booleanValue()) { object.remove(last.textValue()); }
                else { object.set(last.textValue(), edit.get("value").deepCopy()); }
            } else { ((ArrayNode) parent).set(last.intValue(), edit.get("value").deepCopy()); }
        }
        return input;
    }
    private static ObjectNode baseline() throws IOException { return golden().get("baseline").deepCopy(); }
    private static JsonNode result(JsonNode input) { return jsonDomain(PlayerRiskCodec.encode(PlayerRiskCodec.project(bytes(input)))); }
    private static JsonNode jsonDomain(JsonNode value) { return StrictJson.parse(bytes(value)); }

    @Test
    void actualProducerGoldenAndDriverHistoryMatch() throws IOException {
        JsonNode captured = golden();
        assertEquals("xar.java.player-risk-producer-golden.v1", captured.get("schema").textValue());
        assertTrue(captured.get("sources").size() >= 11); assertTrue(captured.get("machine_id").isTextual());
        assertEquals(0, captured.get("game_rpc_count").intValue()); assertEquals(0, captured.get("canonical_ledger_write_count").intValue());
        assertFalse(captured.get("production_cutover").booleanValue());
        assertEquals(24, captured.get("cases").size());
        for (JsonNode sample : captured.get("cases")) {
            ObjectNode original = input(captured, sample); byte[] before = bytes(original);
            assertEquals(sample.get("expected"), result(original), sample.get("id").textValue());
            assertEquals(new String(before, StandardCharsets.UTF_8), new String(bytes(original), StandardCharsets.UTF_8));
        }
        JsonNode history = captured.get("driver_case");
        assertEquals(history.get("expected"), result(history.get("input")));
        assertFalse(result(history.get("input")).get("current_scope").get("response_connection_generation_observed").booleanValue());
    }

    @Test
    void actualRegisteredServiceAttachmentAndJournallerConsumerRemainNarrow() throws IOException {
        JsonNode captured = golden(), service = captured.get("service_consumer");
        Context risk = PlayerRiskCodec.project(bytes(captured.get("baseline")));
        ObjectNode historyInput = StrictJson.object(); historyInput.set("snapshot", captured.get("baseline").get("snapshot"));
        historyInput.set("history", service.get("history"));
        assertEquals(risk, PlayerRiskConsumers.fromCurrentHistory(bytes(historyInput)));
        ObjectNode attached = PlayerRiskConsumers.attachToPlan(service.get("plan"), risk);
        assertEquals(service.get("expected"), jsonDomain(attached));
        assertFalse(service.get("plan").has("player_risk_context"));
        for (JsonNode sample : captured.get("journaller_consumers")) {
            JournallerStressGate gate = PlayerRiskConsumers.journallerStressGate(PlayerRiskCodec.project(bytes(sample.get("input"))));
            String expected = sample.get("expected_status").textValue();
            assertEquals(switch (expected) {
                case "same_frame_stress_unavailable" -> JournallerStressGate.SAME_FRAME_STRESS_UNAVAILABLE;
                case "below_urgent_stress_threshold" -> JournallerStressGate.BELOW_URGENT_STRESS_THRESHOLD;
                case "required_native_capability_unavailable" -> JournallerStressGate.CONTINUE_NATIVE_GUARDS;
                default -> throw new IllegalArgumentException("unexpected actual journaller boundary: " + expected);
            }, gate, sample.get("id").textValue());
            assertEquals(0, sample.get("action_calls").size());
        }
        attached.withObject("/player_risk_context/health/value").put("raw", 0);
        assertNotEquals(attached.get("player_risk_context"), PlayerRiskCodec.encode(risk));
    }

    @Test
    void currentHistoryUsesActualExecutorWrappersAndNeverFallsBackAfterSelectedMalformedRoot() throws IOException {
        JsonNode captured = golden(); ObjectNode request = StrictJson.object();
        request.set("snapshot", captured.get("baseline").get("snapshot"));
        ArrayNode history = request.putArray("history");
        ObjectNode direct = captured.get("service_consumer").get("history").get(0).deepCopy();
        history.add(direct);
        Context expected = PlayerRiskConsumers.fromCurrentHistory(bytes(request));
        ObjectNode stale = direct.deepCopy();
        ((ObjectNode) stale.get("result")).put("queried_native_revision", 99); history.add(stale);
        assertEquals(expected, PlayerRiskConsumers.fromCurrentHistory(bytes(request)));
        ObjectNode wrapper = StrictJson.object(); wrapper.put("command", "auto-turn"); wrapper.put("ok", true);
        ObjectNode result = wrapper.putObject("result"), automatic = result.putObject("auto_turn");
        automatic.put("selected_step", "query-campaign-root-context-v1"); automatic.set("result", direct.get("result").deepCopy());
        history.add(wrapper);
        assertEquals(expected, PlayerRiskConsumers.fromCurrentHistory(bytes(request)));
        ((ObjectNode) automatic.get("result").get("campaign_root_context").get("player_health")).put("raw", 1.0);
        assertEquals(Status.UNAVAILABLE, PlayerRiskConsumers.fromCurrentHistory(bytes(request)).status());
        history.removeAll();
        assertEquals("same_frame_campaign_root_result_unavailable", PlayerRiskConsumers.fromCurrentHistory(bytes(request)).unavailableReason());
    }

    @Test
    void bothActualQueueOutputBindersConsumeTheSameSerializedRiskFrame() throws IOException {
        JsonNode captured = golden();
        assertEquals(4, captured.get("output_binder_consumers").size());
        for (JsonNode sample : captured.get("output_binder_consumers")) {
            Context risk = PlayerRiskCodec.project(bytes(input(captured, sample)));
            JsonNode goal = sample.get("goal"), initial = sample.get("initial_frame");
            LegacyRiskFrameAdapter.CampaignGoal campaign = new LegacyRiskFrameAdapter.CampaignGoal(goal.get("campaign_id").textValue(), goal.get("current_character_id").intValue());
            LegacyRiskFrameAdapter.InitialCampaign basis = new LegacyRiskFrameAdapter.InitialCampaign(initial.get("actor_character_id").intValue(), initial.get("episode_run_id").textValue());
            assertEquals(2, sample.get("actual_consumers").intValue());
            if (sample.get("expected").get("accepted").booleanValue()) {
                JsonNode adapted = jsonDomain(LegacyRiskFrameAdapter.encode(LegacyRiskFrameAdapter.legacyRiskFallback(risk, campaign, basis)));
                assertEquals(sample.get("expected").get("binding"), adapted, sample.get("id").textValue());
                assertFalse(adapted.has("bridge_pid"), "risk has no Game process source witness");
                assertEquals(adapted, StrictJson.parse(StrictJson.canonical(adapted)));
                assertThrows(ContractViolationException.class, () -> LegacyRiskFrameAdapter.legacyRiskFallback(risk,
                        new LegacyRiskFrameAdapter.CampaignGoal(campaign.campaignId(), campaign.currentCharacterId() + 1), basis));
            } else {
                assertThrows(ContractViolationException.class, () -> LegacyRiskFrameAdapter.legacyRiskFallback(risk, campaign, basis));
            }
        }
    }

    @Test
    void rawNumericTokensCannotAliasFrameIdsSequencesOrScale() throws IOException {
        ObjectNode seed = baseline();
        for (String pointer : List.of("/snapshot/revision", "/snapshot/native_revision", "/snapshot/date_raw",
                "/campaign_root_result/query_sequence", "/campaign_root_result/campaign_root_context/player_character_id",
                "/campaign_root_result/campaign_root_context/player_health/raw", "/campaign_root_result/campaign_root_context/player_health/scale")) {
            for (String token : List.of("true", "1.0", "\"1\"")) {
                ObjectNode altered = seed.deepCopy();
                int slash = pointer.lastIndexOf('/'); ObjectNode parent = (ObjectNode) altered.at(pointer.substring(0, slash));
                parent.set(pointer.substring(slash + 1), new ObjectMapper().readTree(token));
                byte[] raw = bytes(altered);
                assertEquals(Status.UNAVAILABLE, PlayerRiskCodec.project(raw).status(), pointer + " raw=" + token);
            }
        }
    }

    @Test
    void inputGreenCannotCreateSourceAndSdkExtensionsRemainExtensible() throws IOException {
        ObjectNode sample = baseline(); JsonNode expected = result(sample);
        ((ObjectNode) sample.get("snapshot")).put("already_qualified", true);
        ((ObjectNode) sample.get("campaign_root_result")).put("input_green", true);
        ((ObjectNode) sample.get("campaign_root_result").get("campaign_root_context")).putObject("unrelated_sdk_extension").put("ready", true);
        assertEquals(expected, result(sample));
        ((ObjectNode) sample.get("campaign_root_result")).remove("campaign_root_context");
        assertEquals(Status.UNAVAILABLE, PlayerRiskCodec.project(bytes(sample)).status());
        sample = baseline(); sample.put("input_green", true);
        ObjectNode invalid = sample;
        assertThrows(ContractViolationException.class, () -> PlayerRiskCodec.project(bytes(invalid)));
        for (String raw : List.of("{}", "null", "[]", "{} {}", "{\"snapshot\":{},\"snapshot\":{},\"campaign_root_result\":null}")) {
            assertThrows(ContractViolationException.class, () -> PlayerRiskCodec.project(raw.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test
    void uint64SequenceAndHealthInt64RoundtripWithoutDoubleConversion() throws IOException {
        ObjectNode sample = baseline();
        ((ObjectNode) sample.get("campaign_root_result")).put("query_sequence", StrictJson.UINT64_MAX);
        ((ObjectNode) sample.get("campaign_root_result").get("campaign_root_context").get("player_health")).put("raw", Long.MIN_VALUE);
        JsonNode output = result(sample);
        assertEquals(StrictJson.UINT64_MAX, output.get("source").get("query_sequence").bigIntegerValue());
        assertEquals(BigInteger.valueOf(Long.MIN_VALUE), output.get("health").get("value").get("raw").bigIntegerValue());
        assertEquals(output, StrictJson.parse(StrictJson.canonical(output)));
        assertFalse(output.get("readiness").get("legitimacy_protection_ready").booleanValue());
        assertFalse(output.has("selected_step"));
    }
}
