package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Retained original R20 row161, including its legal zero SiegeID, follows the actual shared Java decoder. */
final class ArmyWarOccupationCodecTest {
    private static final String ORIGINAL = "{\"siege_id\":0,\"besieging_army_id\":8,\"player_army_besieging\":false,\"progress_fraction\":{\"raw\":0,\"scale\":100000},\"current_work\":{\"raw\":0,\"scale\":100000},\"total_work\":{\"raw\":32500000,\"scale\":100000},\"remaining_work\":{\"raw\":32500000,\"scale\":100000},\"days_left\":170,\"ordinary_daily_progress\":{\"raw\":192000,\"scale\":100000},\"eligible_regiment_siege_work\":{\"raw\":80000,\"scale\":100000},\"highest_eligible_siege_tier\":1,\"province_unit_occurrences\":[{\"occurrence_index\":0,\"public_unit_id\":8,\"native_carmy_id\":8,\"eligible\":true,\"qualified_regiment_ids\":[8,9,10,11]},{\"occurrence_index\":1,\"public_unit_id\":9,\"native_carmy_id\":9,\"eligible\":true,\"qualified_regiment_ids\":[12,13,14,15]},{\"occurrence_index\":2,\"public_unit_id\":10,\"native_carmy_id\":10,\"eligible\":true,\"qualified_regiment_ids\":[16,17,18,19]},{\"occurrence_index\":3,\"public_unit_id\":11,\"native_carmy_id\":11,\"eligible\":true,\"qualified_regiment_ids\":[20,21,22,23]}],\"current_phase_length\":{\"raw\":2000000,\"scale\":100000},\"prepared_phase_length\":{\"raw\":0,\"scale\":100000},\"phase_counter\":0,\"can_advance\":true,\"phase_event_state\":{\"breach_level\":0,\"starvation_level\":0,\"disease_level\":0,\"desertion_count\":0,\"stalemate_count\":0},\"prepared_selected_phase_event_enum\":5,\"assault_observable\":true,\"breach_level\":0,\"walls_breached\":false,\"assault_in_progress\":false,\"can_start_assault\":false,\"can_stop_assault\":false,\"assault_daily_progress\":{\"raw\":0,\"scale\":100000},\"assault_daily_casualties\":0}";
    @Test void actualZeroSiegeKeepsAllMaterialAndRoundTripsThePublicWireAndColdDecoder() {
        ObjectNode original = ArmyJson.parse(ORIGINAL.getBytes(StandardCharsets.UTF_8));
        var siege = ArmyWarOccupationCodec.siege(original);
        assertEquals(0, siege.id()); assertFalse(siege.playerBesieging()); assertTrue(siege.assaultObservable());
        assertFalse(siege.assault().orElseThrow().canStart()); assertEquals(32500000, siege.total().raw());
        assertEquals(original, OpportunityJson.toNode(siege.normalized()));
        assertEquals(siege, ArmyWarOccupationCodec.siege(OpportunityJson.toNode(siege.normalized())));
        Context context = context();
        RawJson publicWire = ArmyPublicWire.encode(siege.normalized(), context);
        assertEquals(siege.normalized(), ArmyPublicWire.decode(publicWire, context));
        assertEquals(siege, ArmyWarOccupationCodec.siege(OpportunityJson.toNode(ArmyPublicWire.decode(publicWire, context))));
        assertEquals(ORIGINAL, new String(ORIGINAL.getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8));
    }
    @Test void wrongTypesAndUnknownAssaultCannotBecomeAnActionOrEraseNativeOccurrenceOrder() {
        ObjectNode original = ArmyJson.parse(ORIGINAL.getBytes(StandardCharsets.UTF_8));
        for (var invalid : List.of(ArmyJson.empty().booleanNode(false), ArmyJson.empty().numberNode(-1),
                ArmyJson.empty().numberNode(2147483648L), ArmyJson.empty().nullNode())) {
            ObjectNode changed = original.deepCopy(); changed.set("siege_id", invalid);
            assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.siege(changed));
        }
        ObjectNode unknown = original.deepCopy().put("assault_observable", false);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.siege(unknown));
        ObjectNode order = original.deepCopy(); ((ObjectNode) order.path("province_unit_occurrences").get(1)).put("occurrence_index", 0);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.siege(order));
        ObjectNode repeated = original.deepCopy();
        ObjectNode first = (ObjectNode) repeated.path("province_unit_occurrences").get(0), second = (ObjectNode) repeated.path("province_unit_occurrences").get(1);
        second.put("public_unit_id", first.path("public_unit_id").intValue()); second.put("native_carmy_id", first.path("native_carmy_id").intValue());
        var normalized = ArmyWarOccupationCodec.siege(repeated);
        assertEquals(4, normalized.normalized().get("province_unit_occurrences") instanceof OpportunityJson.Arr a ? a.items().size() : -1);
        assertEquals(repeated.get("province_unit_occurrences"), OpportunityJson.toNode(normalized.normalized()).get("province_unit_occurrences"));
        ObjectNode unresolved = original.deepCopy(); ObjectNode occurrence = (ObjectNode) unresolved.path("province_unit_occurrences").get(0);
        occurrence.putNull("eligible");
        assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.siege(unresolved));
    }
    @Test void completeOccupationCannotBorrowAnotherFrameOrPublishUnknownHoldingsAsComplete() {
        Context source = context(); ObjectNode n = ArmyJson.empty().put("schema", "xar.ck3.war-occupation-targets.v1")
                .put("schema_version", 1).put("available", true).put("collection_complete", true).put("status", "available")
                .put("snapshot_revision", 7).put("date_raw", 456).put("war_id", 17).put("actor_character_id", 29829)
                .put("primary_attacker_character_id", 29829).put("primary_defender_character_id", 17116).put("player_side", "attacker")
                .put("game_version", "1.20.0.4").put("executable_sha256", "A".repeat(64)).putNull("unavailable_reason");
        var counts = n.putArray("side_counts");
        for (String side : List.of("attacker", "defender")) counts.addObject().put("territory_side", side).put("eligible", 1).put("occupied", 0).put("native_candidate_count", 1).put("collection_complete", true);
        var row = n.putArray("rows").addObject().put("holding_title_id", 0).put("province_id", 0).put("legal_holder_character_id", 0)
                .put("territory_side", "defender").put("occupation_observable", true).put("occupier_side", "none")
                .put("is_occupied", false).putNull("occupying_character_id").put("counted_occupied_by_opposing_side", false).put("siege_observable", true);
        row.set("active_siege", ArmyJson.parse(ORIGINAL.getBytes(StandardCharsets.UTF_8)));
        var value = ArmyWarOccupationCodec.normalize(n, source, 17, Side.ATTACKER);
        assertEquals(0, value.holdings().getFirst().siege().orElseThrow().id());
        assertEquals(value, ArmyWarOccupationCodec.normalize(ArmyWarOccupationCodec.normalizedNode(value), source, 17, Side.ATTACKER));
        ObjectNode wrongFrame = n.deepCopy().put("snapshot_revision", 8);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.normalize(wrongFrame, source, 17, Side.ATTACKER));
        ObjectNode wrongWar = n.deepCopy().put("war_id", 18);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.normalize(wrongWar, source, 17, Side.ATTACKER));
        ObjectNode unknown = n.deepCopy(); ((ObjectNode) unknown.path("rows").get(0)).put("occupation_observable", false);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarOccupationCodec.normalize(unknown, source, 17, Side.ATTACKER));
    }
    private static Context context() {
        var ref = new ExactRef("retained-original-fixture-source", 1, "a".repeat(64));
        var source = new G2Source("source-shaped-test-machine", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(7), BigInteger.valueOf(456)), "fixture:7", BigInteger.valueOf(9), "fixture-episode");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "fixture-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
}

