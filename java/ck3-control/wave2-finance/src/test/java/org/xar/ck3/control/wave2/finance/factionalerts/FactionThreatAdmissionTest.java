package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Optional;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatCodec;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionThreatAdmission.*;

/** Uses the unchanged original producer corpus; no synthetic value is called a native capture. */
final class FactionThreatAdmissionTest {
    private record Vector(ObjectNode packet, byte[] activeWars) {
        byte[] bytes() { return StrictJson.canonical(packet, FactionAlertsCodec.MAX_BYTES); }
    }
    private static Vector vector() throws IOException {
        JsonNode golden;
        try (var input = FactionThreatAdmissionTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            assertNotNull(input);
            golden = StrictJson.parse(input.readAllBytes(), FactionAlertsCodec.MAX_BYTES);
        }
        JsonNode selected = null;
        for (JsonNode item : golden.get("cases"))
            if (item.get("name").textValue().equals("exact-build-1.20.0.4")) selected = item;
        assertNotNull(selected);
        ObjectNode frame = (ObjectNode) golden.get("bases").get(selected.get("base").textValue()).deepCopy();
        for (JsonNode operation : selected.get("operations")) {
            String path = operation.get("path").textValue(); int slash = path.lastIndexOf('/');
            ObjectNode parent = slash == 0 ? frame : (ObjectNode) frame.at(path.substring(0, slash));
            if (operation.path("remove").asBoolean(false)) parent.remove(path.substring(slash + 1));
            else parent.set(path.substring(slash + 1), operation.get("value").deepCopy());
        }
        // These eight outer fields follow the actual .4 whole serializer; the nested corpus remains unchanged.
        ObjectNode packet = StrictJson.object().put("step", STEP).put("accepted", true).put("status", frame.get("status").textValue())
                .put("query_sequence", StrictJson.UINT64_MAX).put("snapshot_revision", frame.get("snapshot_revision").bigIntegerValue())
                .put("player_faction_alerts_ready", frame.at("/readiness/alert_ready").booleanValue()).put("backend_id", "native-headless");
        packet.set("player_faction_alerts", frame);
        return new Vector(packet, StrictJson.canonical(selected.get("active_wars")));
    }
    private static Request request(Vector vector, int faction, int recipient) {
        JsonNode frame = vector.packet().get("player_faction_alerts");
        return new Request(new ExpectedFrame(frame.get("date_raw").intValue(),
                frame.get("snapshot_revision").bigIntegerValue(), Optional.of(Build.CK3_12004)),
                frame.get("player_character_id").intValue(), faction, recipient);
    }
    private static Result assess(Vector vector, int faction, int recipient) {
        return fromExistingDriverResult(vector.bytes(), request(vector, faction, recipient), vector.activeWars());
    }
    @Test void actualSharedProducerCorpusPreservesFinalPowerAndOriginalBytes() throws Exception {
        Vector vector = vector(); byte[] raw = vector.bytes();
        Admitted leader = assertInstanceOf(Admitted.class, assess(vector, 771, 33771));
        Admitted member = assertInstanceOf(Admitted.class, assess(vector, 771, 34771));
        assertEquals(leader.faction(), member.faction());
        assertEquals(9_100_000, leader.faction().power().raw());
        assertEquals(8_000_000, leader.faction().powerThreshold().raw());
        var boundary = FactionAlertsBoundary.normalizeExistingDriverResult(raw, leader.request().expected(), vector.activeWars());
        assertArrayEquals(boundary.normalizedAlertJson(), leader.normalizedAlertJson());
        assertEquals(boundary.originalSha256(), leader.originalDriverResultSha256());
        byte[] exposed = leader.normalizedAlertJson(); exposed[0] = 0;
        assertArrayEquals(boundary.normalizedAlertJson(), leader.normalizedAlertJson());
        assertArrayEquals(raw, vector.bytes());
    }
    @Test void exactFactionAndMembershipRemainRequiredWithWarTransferredToWarDomain() throws Exception {
        Vector vector = vector();
        assertEquals(new Missing(MissingReason.SELECTED_FACTION_ABSENT), assess(vector, 999, 33771));
        assertEquals(new Missing(MissingReason.RECIPIENT_NOT_LEADER_OR_MEMBER), assess(vector, 771, 33772));
        assertEquals(new Missing(MissingReason.NOT_CURRENTLY_DANGEROUS), assess(vector, 770, 33770));
        assertEquals(new Missing(MissingReason.EXISTING_FACTION_WAR), assess(vector, 773, 33773));
    }
    @Test void zeroMonthsCannotPromoteEitherUnknownClockOrComponentCacheObservation() throws Exception {
        Vector vector = vector();
        ((ObjectNode) vector.packet().at("/player_faction_alerts/targeting_factions/1"))
                .put("months_until_max_discontent", 0);
        Admitted admitted = assertInstanceOf(Admitted.class, assess(vector, 771, 33771));
        assertEquals(Optional.of(0), admitted.faction().monthsUntilMaxDiscontent());
        assertEquals(ClockCoverage.MONTHS_TO_MAX_DISCONTENT_ONLY_EXACT_DEMAND_CLOCK_UNPUBLISHED, admitted.clockCoverage());
        assertEquals(StrengthCoverage.FINAL_NATIVE_POWER_ONLY_COMPONENT_CACHES_NOT_OBSERVED, admitted.strengthCoverage());
    }
    @Test void strictProducerBoundaryRejectsWrongTokensMissingFieldsAndDifferentNativeFrame() throws Exception {
        Vector vector = vector(); Request request = request(vector, 771, 33771);
        ObjectNode frame = (ObjectNode) vector.packet().get("player_faction_alerts");
        frame.put("snapshot_revision", true);
        assertThrows(IllegalArgumentException.class, () -> fromExistingDriverResult(vector.bytes(), request, vector.activeWars()));
        frame.put("snapshot_revision", 41.0);
        assertThrows(IllegalArgumentException.class, () -> fromExistingDriverResult(vector.bytes(), request, vector.activeWars()));
        frame.remove("snapshot_revision");
        assertThrows(IllegalArgumentException.class, () -> fromExistingDriverResult(vector.bytes(), request, vector.activeWars()));
        Vector valid = vector(); Request bound = request(valid, 771, 33771);
        assertThrows(IllegalArgumentException.class, () -> fromExistingDriverResult(valid.bytes(),
                new Request(new ExpectedFrame(bound.expected().dateRaw(), bound.expected().nativeRevision().add(BigInteger.ONE),
                        Optional.of(Build.CK3_12004)), bound.actorCharacterId(), 771, 33771), valid.activeWars()));
        assertThrows(IllegalArgumentException.class, () -> fromExistingDriverResult(valid.bytes(),
                new Request(bound.expected(), bound.actorCharacterId() + 1, 771, 33771), valid.activeWars()));
        assertThrows(IllegalArgumentException.class, () -> new Request(new ExpectedFrame(bound.expected().dateRaw(),
                bound.expected().nativeRevision(), Optional.of(Build.CK3_11906)), bound.actorCharacterId(), 771, 33771));
    }
    @Test void allCurrentConsumersRequireTheActualOuterNativeResult() throws Exception {
        Vector valid = vector(); Request request = request(valid, 771, 33771);
        var result = FactionAlertsBoundary.normalizeCurrentNativeResult(valid.bytes(), request.expected(), valid.activeWars());
        Admitted admitted = assertInstanceOf(Admitted.class, assess(valid, 771, 33771));
        assertEquals(StrictJson.UINT64_MAX, result.querySequence());
        assertEquals(result.projection().frame(), admitted.nativeFrame());
        assertEquals(result.projection().originalSha256(), admitted.originalDriverResultSha256());
        assertArrayEquals(result.projection().normalizedAlertJson(), admitted.normalizedAlertJson());
        var threat = FactionThreatCodec.decodeExistingObserverResult(FactionAlertsBoundary.forThreatObserver(result.projection()).json());
        assertTrue(threat.available()); assertEquals(request.expected().nativeRevision(), threat.frame().orElseThrow().nativeRevision());
        var outcome = GiftOutcomeCodec.alertResult(FactionAlertsBoundary.forResolvedGiftOutcome(result.projection()).json());
        assertEquals(Optional.of(request.expected().nativeRevision()), outcome.snapshotRevision());
        assertEquals(((Available) admitted.nativeFrame()).targetingFactions().size(), outcome.targetingRows().orElseThrow().size());
        var fields = new java.util.ArrayList<String>(); valid.packet().fieldNames().forEachRemaining(fields::add);
        for (String field : fields) {
            ObjectNode altered = valid.packet().deepCopy(); altered.remove(field);
            rejectCurrent(new Vector(altered, valid.activeWars()), request);
        }
        ObjectNode detached = StrictJson.object(); detached.set("player_faction_alerts", valid.packet().get("player_faction_alerts"));
        rejectCurrent(new Vector(detached, valid.activeWars()), request);
        ObjectNode extra = valid.packet().deepCopy().put("sdk_extension", "not native whole output");
        rejectCurrent(new Vector(extra, valid.activeWars()), request);
    }
    @Test void outerNativeMirrorsCannotAdmitANestedFrameFromAnotherQuery() throws Exception {
        Vector valid = vector(); Request request = request(valid, 771, 33771);
        for (String field : List.of("query_sequence", "snapshot_revision"))
            for (String value : List.of("true", "41.0", "\"41\"", "null", "-1", "0", "18446744073709551616")) {
                ObjectNode altered = valid.packet().deepCopy();
                altered.set(field, StrictJson.parse(("{\"v\":" + value + "}").getBytes(java.nio.charset.StandardCharsets.UTF_8)).get("v"));
                rejectCurrent(new Vector(altered, valid.activeWars()), request);
            }
        for (ObjectNode altered : List.of(valid.packet().deepCopy().put("step", "other-query"),
                valid.packet().deepCopy().put("accepted", false), valid.packet().deepCopy().put("backend_id", "other-backend"),
                valid.packet().deepCopy().put("snapshot_revision", request.expected().nativeRevision().add(BigInteger.ONE)),
                valid.packet().deepCopy().put("status", "unavailable"), valid.packet().deepCopy().put("player_faction_alerts_ready", false)))
            rejectCurrent(new Vector(altered, valid.activeWars()), request);
    }
    private static void rejectCurrent(Vector vector, Request request) {
        assertThrows(IllegalArgumentException.class, () -> FactionAlertsBoundary.normalizeCurrentNativeResult(
                vector.bytes(), request.expected(), vector.activeWars()));
        assertThrows(IllegalArgumentException.class, () -> fromExistingDriverResult(vector.bytes(), request, vector.activeWars()));
    }
}
