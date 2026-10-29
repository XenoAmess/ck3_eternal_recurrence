package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionModel;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/** Actual serializers and pure consumers; this does not manufacture a Root lease or writer commit. */
final class SuccessionFullSemanticProducerTest {
    @Test void actualDriverJsonToM3AndPreclockProjectionRetainsCompleteHistoryAndSlotSemantics() {
        OpportunityJson.Obj history = history();
        byte[] semantic = fullSemantic(11, 2, false, history);
        var before = driver(history);
        byte[] originalDriver = before.encode();
        assertTrue(semantic.length > SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
        var estate = SuccessionNativeEstate12004.freeze(root(11, 2, false), semantic);
        var replacement = DriverPreclockExpectationProducer.replace(before, estate);
        assertArrayEquals(semantic, estate.originalSemantic());
        assertEquals(DriverJson.sha256(semantic), estate.originalSemanticSha256());
        assertArrayEquals(originalDriver, before.encode());
        assertEquals(before.session(), replacement.session());
        assertEquals(before.commandHistory(), replacement.commandHistory());
        assertSame(before.lastCheckpoint(), replacement.lastCheckpoint());
        assertSame(before.rollbackWarFailure(), replacement.rollbackWarFailure());
        assertSame(before.managedRestoreTransaction(), replacement.managedRestoreTransaction());
        assertSame(before.campaignGoal(), replacement.campaignGoal());
        assertSame(before.successionLifecycle(), replacement.successionLifecycle());
        assertSame(before.rollbackWarFailures(), replacement.rollbackWarFailures());
        var decoded = DriverStateSnapshot.decodeComplete(replacement.encode());
        assertArrayEquals(replacement.encode(), decoded.encode());
        assertArrayEquals(before.commandHistory().getFirst().originalRow().json(), decoded.commandHistory().getFirst().originalRow().json());
        assertArrayEquals(estate.wire(), assertInstanceOf(DriverStateSnapshot.Value.class, decoded.successionExpectation()).json());
        assertArrayEquals(estate.wire(), SuccessionCodec.encodeExpectation(SuccessionCodec.decodeExpectation(estate.wire())));
        assertInstanceOf(DriverStateSnapshot.Missing.class, decoded.successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.Missing.class, decoded.rollbackWarFailures());
        assertInstanceOf(DriverStateSnapshot.NullValue.class, decoded.rollbackWarFailure());
        JsonNode retained = FullJsonTree.parse(estate.originalSemantic(), FullJsonTree.MAXIMUM_BYTES).get("command_history").get(0);
        assertEquals(SuccessionNativeEstate12004.MAX_SOURCE_BYTES + 32, retained.get("raw_history").textValue().length());
        assertEquals(new BigInteger("90071992547409931234567890"), retained.get("raw_identity").bigIntegerValue());
        assertTrue(retained.get("ratio").isFloatingPointNumber()); assertFalse(retained.get("ratio").isIntegralNumber());
        assertEquals("1.0", retained.get("ratio").asText()); assertEquals(1.0, retained.get("ratio").doubleValue());
        assertEquals("-0.0", retained.get("negative_zero").asText());
        assertEquals(Double.doubleToRawLongBits(-0.0), Double.doubleToRawLongBits(retained.get("negative_zero").doubleValue()));
        assertTrue(retained.get("nullable").isNull()); assertFalse(retained.has("missing"));
    }

    @Test void actualLargeBeforeAndAfterMaterialsProduceTheCompleteGoalAndDriverReconciliationWire() {
        var history = history(); byte[] before = fullSemantic(11, 2, false, history), after = fullSemantic(13, 3, true, history);
        var retained = SuccessionNativeEstate12004.freeze(root(11, 2, false), before);
        var comparison = SuccessionNativeEstate12004.reconcile(retained, root(13, 3, true), after);
        assertEquals(SuccessionModel.Verdict.MATCHED, comparison.comparison().verdict());
        assertArrayEquals(before, comparison.predecessor().originalSemantic()); assertArrayEquals(after, comparison.originalSemantic());
        assertEquals(DriverJson.sha256(after), comparison.originalSemanticSha256());
        assertNotNull(GoalCodec.decodeReconciliation(comparison.wire())); // Also the LifecycleReducer DTO decoder.
        var originalWire = DriverJson.object(comparison.wire(), DriverJson.MAX_NATIVE_BYTES);
        assertEquals(originalWire, DriverJson.object(DriverJson.encode(originalWire), DriverJson.MAX_NATIVE_BYTES));
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(13)), originalWire.get("successor_binding") instanceof OpportunityJson.Obj binding
                ? binding.get("native_revision") : null);
        assertFalse(FullJsonTree.parse(after, FullJsonTree.MAXIMUM_BYTES).has("one_life_terminal"));
    }

    @Test void actualDriverSerializerCannotConvertFloatOrBooleanConsumedRevisionIntoAnInteger() {
        var typed = DriverJson.object(fullSemantic(11, 2, false, history()), DriverJson.MAX_NATIVE_BYTES);
        for (OpportunityJson.Value wrong : List.<OpportunityJson.Value>of(new OpportunityJson.DecimalValue("11.0"),
                new OpportunityJson.Bool(true), OpportunityJson.Nil.INSTANCE, new OpportunityJson.Text("11"))) {
            byte[] original = DriverJson.encode(typed.with("native_revision", wrong));
            assertTrue(original.length > SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
            assertThrows(IllegalArgumentException.class, () -> SuccessionNativeEstate12004.freeze(root(11, 2, false), original));
        }
    }

    private static OpportunityJson.Obj history() {
        byte[] raw = ("{\"index\":1,\"command\":\"retained-original\",\"raw_identity\":90071992547409931234567890,"
                + "\"ratio\":1.0,\"negative_zero\":-0.0,\"nullable\":null}").getBytes(StandardCharsets.UTF_8);
        return DriverJson.object(raw, DriverJson.MAX_NATIVE_BYTES).with("raw_history",
                new OpportunityJson.Text("x".repeat(SuccessionNativeEstate12004.MAX_SOURCE_BYTES + 32)));
    }
    private static DriverStateSnapshot.Complete driver(OpportunityJson.Obj history) {
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-original-pipe", 7, BigInteger.TWO, "old-episode"),
                List.of(new DriverStateSnapshot.HistoryEntry(1, new DriverStateSnapshot.Value(DriverJson.encode(history)))),
                value("{\"original_checkpoint\":true}"), new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.Missing(), value("{\"original_goal\":90071992547409931234567890}"),
                new DriverStateSnapshot.Missing());
    }
    private static DriverStateSnapshot.Value value(String json) { return new DriverStateSnapshot.Value(json.getBytes(StandardCharsets.UTF_8)); }
    private static byte[] fullSemantic(int revision, int actor, boolean changed, OpportunityJson.Obj history) {
        var semantic = StrictJson.object().put("snapshot_id", "actual-" + revision).put("revision", revision + 100)
                .put("native_revision", revision).put("date_raw", 100).put("episode_run_id", "old-episode")
                .put("episode_character_id", 2).put("paused", true).put("map_ready", true)
                .putNull("active_event").putNull("pending_character_interaction");
        if (changed) semantic.put("one_life_terminal_reason", "played_character_changed"); else semantic.putNull("one_life_terminal_reason");
        semantic.putObject("played_character").put("character_id", actor).put("alive", true);
        semantic.putObject("succession_lifecycle").put("lifecycle", "ordinary_campaign_succession");
        var complete = DriverJson.object(StrictJson.canonical(semantic), DriverJson.MAX_NATIVE_BYTES)
                .with("command_history", new OpportunityJson.Arr(List.of(history)));
        return DriverJson.encode(complete);
    }
    private static byte[] root(int revision, int actor, boolean after) {
        var result = StrictJson.object().put("step", "query-campaign-root-context-v1").put("accepted", true).put("status", "available")
                .put("query_sequence", revision).put("snapshot_revision", revision).put("backend_id", "native-headless");
        var root = result.putObject("campaign_root_context").put("schema_version", 1).put("status", "available")
                .put("snapshot_revision", revision).put("date_raw", 100).put("player_character_id", actor)
                .put("player_character_alive", true).putNull("unavailable_reason");
        root.set("primary_title", title(10)); root.putArray("primary_title_succession_character_ids").add(after ? 6 : 3);
        root.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", SuccessionNativeEstate12004.EXECUTABLE_SHA256)
                .put("backend_id", "ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset", "0x1E0").put("primary_title_rva", "0x289DA10");
        var readiness = root.putObject("readiness");
        for (String key : List.of("player_identity_ready", "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready", "same_frame_ready")) readiness.put(key, true);
        var rows = root.putArray("held_title_partition"); rows.add(row(10, after ? 6 : 3, true)); if (!after) rows.add(row(20, 4, false));
        return StrictJson.canonical(result, SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode title(int id) {
        return StrictJson.object().put("title_id", id).put("tier_raw", 2).put("tier_key", "county");
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode row(int id, int heir, boolean primary) {
        var row = StrictJson.object().put("first_heir_character_id", heir).put("primary", primary).put("capital_province_id", id + 1);
        row.set("title", title(id)); return row;
    }
}
