package org.xar.ck3.control.wave2.military.commander;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class CommanderQualityTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = CommanderQualityTest.class.getResourceAsStream("/commander/legacy-golden.json")) {
            assertNotNull(stream, "M7 must capture the actual legacy producer golden before accepting this leaf");
            return ArmyCommanderCandidatesCodec.parseJson(stream.readAllBytes());
        }
    }
    @Test void actualLegacyProducerAndFormalConsumersMatch() throws IOException {
        JsonNode golden = golden(); assertEquals(4, golden.get("original_packet_count").intValue()); assertFalse(golden.get("assignment_executed").booleanValue());
        assertTrue(golden.get("source_pins").size() >= 15); assertTrue(golden.get("captured_at_utc").isTextual()); assertTrue(golden.get("machine_id").isTextual());
        int proposals = 0; int plans = 0;
        for (JsonNode row : golden.get("cases")) {
            byte[] input = ArmyCommanderCandidatesCodec.encodeJson(row.get("input"));
            JsonNode result = ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.propose(input));
            assertEquals(row.get("expected"), result, row.get("name").textValue()); proposals++;
            assertFalse(result.get("assignment_executed").booleanValue()); assertFalse(result.get("automatic_consumption").booleanValue());
        }
        for (JsonNode row : golden.get("plans")) {
            // The baseline plan has a real decimal extension outside the integer quality leaf.
            byte[] input = row.get("input").toString().getBytes(StandardCharsets.UTF_8);
            JsonNode result = ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.plan(input));
            assertEquals(row.get("expected"), result, row.get("name").textValue()); plans++;
        }
        assertEquals(15, proposals); assertEquals(13, plans);
    }
    @Test void currentRoleAndNativeLegalityRemainIndependent() throws IOException {
        JsonNode golden = golden(); JsonNode keep = golden.get("cases").get(0).get("expected");
        assertEquals("keep_current", keep.get("status").textValue()); assertEquals(37, keep.get("current_native_ai_base_quality").intValue()); assertEquals(-12, keep.get("quality_gain").intValue());
        for (String name : List.of("legacy-quality-missing", "legacy-quality-null", "unknown-role-not-absent")) {
            JsonNode row = find(golden.get("cases"), name); assertEquals("current_quality_unavailable", row.get("expected").get("status").textValue());
            assertTrue(row.get("expected").get("current_native_ai_base_quality").isNull()); assertTrue(row.get("expected").get("selected_step").isNull());
        }
        assertEquals(4_294_967_295L, find(golden.get("cases"), "gain-exceeds-signed32").get("expected").get("quality_gain").longValue());
        assertEquals("assign_candidate_for_empty_role", find(golden.get("cases"), "absent-role").get("expected").get("status").textValue());
        assertEquals("no_eligible_candidate", find(golden.get("cases"), "absent-no-candidate").get("expected").get("status").textValue());
    }
    @Test void strictTokenAndSourceFailuresAreRejectedBeforeScoring() throws IOException {
        ObjectNode original = (ObjectNode) golden().get("cases").get(0).get("input"); String good = original.toString();
        for (String bad : List.of(good.replace("\"army_id\":83886367", "\"army_id\":true"),
                good.replace("\"army_id\":83886367", "\"army_id\":83886367.0"),
                good.replace("\"query_sequence\":7", "\"query_sequence\":7.0"),
                good.replace("\"native_ai_base_quality\":25", "\"native_ai_base_quality\":25.0"),
                good.replace("\"value\":37", "\"value\":true"),
                good.replace("\"source_character_id\":30000", "\"source_character_id\":30001"),
                good.replace("native_current_assigned_commander_ai_base_quality", "native_total_martial"),
                good.replace("\"can_assign\":true", "\"can_assign\":null"),
                good.replace("\"generic_advantage_points\":7", "\"generic_advantage_points\":7.0"))) {
            assertNotEquals(good, bad, "negative vector must alter the raw token");
            assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.propose(bad.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode missing = original.deepCopy(); ((ObjectNode) missing.get("candidates").get("current_commander").get("current_native_ai_base_quality")).remove("value"); reject(missing);
        ObjectNode unknown = original.deepCopy(); unknown.put("unexpected", true); reject(unknown);
        String duplicate = good.replaceFirst("\\{", "{\"schema\":\"duplicate\","); assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.propose(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.propose((good + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.propose(new byte[] {(byte) 0xc0, (byte) 0x80}));
    }
    @Test void observedQueryAdmissionChecksRealScopeAndDoesNotExecute() throws IOException {
        JsonNode input = golden().get("cases").get(0).get("input"); ObjectNode packet = StrictJson.object(); packet.put("schema", "xar.java.commander-quality-observed-query.v1"); packet.put("army_id", 83886367);
        packet.set("snapshot_before", input.get("snapshot").deepCopy()); packet.set("snapshot_after", input.get("snapshot").deepCopy()); packet.putArray("bridge_capabilities").add(CommanderQuality.QUERY_CAPABILITY); packet.put("expected_revision", 4);
        ObjectNode nativeResult = packet.putObject("native_result"); nativeResult.put("step", "query-army-commander-candidates-v1-for-army-83886367"); nativeResult.put("accepted", true); nativeResult.put("status", "completed"); nativeResult.put("read_only", true); nativeResult.put("query_sequence", 7); nativeResult.put("snapshot_revision", 11); nativeResult.put("date_raw", 53288448); nativeResult.set("army_commander_candidates", input.get("candidates").deepCopy());
        // Compare the persisted JSON domain: parsed golden integers use BigIntegerNode,
        // while the in-memory encoder legitimately uses int/long nodes before serialization.
        JsonNode observed = ArmyCommanderCandidatesCodec.parseJson(ArmyCommanderCandidatesCodec.encodeJson(CommanderQualityCodec.encodeProposal(
                CommanderQualityCodec.admitObservedQuery(ArmyCommanderCandidatesCodec.encodeJson(packet)))));
        assertEquals(golden().get("cases").get(0).get("expected"), observed);
        ObjectNode stale = packet.deepCopy(); ((ObjectNode) stale.get("snapshot_after")).put("revision", 5); rejectObserved(stale);
        ObjectNode unpaused = packet.deepCopy(); ((ObjectNode) unpaused.get("snapshot_after")).put("paused", false); rejectObserved(unpaused);
        ObjectNode wrong = packet.deepCopy(); ((ObjectNode) wrong.get("native_result").get("army_commander_candidates")).put("army_id", 83886368); rejectObserved(wrong);
        ObjectNode ackOnly = packet.deepCopy(); ((ObjectNode) ackOnly.get("native_result")).put("status", "submitted"); rejectObserved(ackOnly);
        ObjectNode capability = packet.deepCopy(); capability.putArray("bridge_capabilities"); rejectObserved(capability);
    }
    @Test void fieldPresenceAndCandidateCollectionDoNotBecomeAssumedFacts() throws IOException {
        JsonNode cases = golden().get("cases"); CommanderQuality.Proposal missing = CommanderQualityCodec.decodeProposalInput(find(cases, "legacy-quality-missing").get("input"));
        CommanderQuality.Proposal explicitNull = CommanderQualityCodec.decodeProposalInput(find(cases, "legacy-quality-null").get("input"));
        assertEquals(CommanderQuality.Presence.MISSING, missing.context().current().quality().presence()); assertEquals(CommanderQuality.Presence.NULL, explicitNull.context().current().quality().presence());
        assertThrows(UnsupportedOperationException.class, () -> missing.context().candidates().clear());
        ObjectNode extension = ((ObjectNode) cases.get(0).get("input")).deepCopy(); ((ObjectNode) extension.get("snapshot")).put("future_sdk_extension", "preserved at original boundary");
        ((ObjectNode) extension.get("candidates")).put("future_native_extension", true);
        assertEquals(cases.get(0).get("expected"), ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.propose(ArmyCommanderCandidatesCodec.encodeJson(extension))));
    }
    private static JsonNode find(JsonNode rows, String name) { for (JsonNode row : rows) { if (name.equals(row.get("name").textValue())) { return row; } } throw new AssertionError("missing golden case: " + name); }
    private static void reject(ObjectNode value) { assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.propose(ArmyCommanderCandidatesCodec.encodeJson(value))); }
    private static void rejectObserved(ObjectNode value) { assertThrows(IllegalArgumentException.class, () -> CommanderQualityCodec.admitObservedQuery(ArmyCommanderCandidatesCodec.encodeJson(value))); }
}
