package org.xar.ck3.control.wave3.planning.participatingwar;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats.*;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Synthetic detached snapshots exercise the real producer and strict durable risk boundary. */
final class ParticipatingWarNonPrimaryRiskTest {
    private static ObjectNode snapshot() {
        return (ObjectNode) StrictJson.parse("""
                {"played_character_id":29829,"native_revision":17,"date_raw":53202168,
                 "snapshot_id":"risk-fixture","revision":23,"episode_run_id":"risk-fixture-episode",
                 "paused":true,"map_ready":true,"played_character":{"character_id":29829,"alive":true},
                 "active_wars":[]}
                """.getBytes(StandardCharsets.UTF_8), ParticipatingWarThreatsCodec.MAX_BYTES);
    }
    private static ObjectNode war(int id, Boolean primary, int armyId, Integer soldiers) {
        ObjectNode war = StrictJson.object(); war.put("war_id", id); war.put("source", "native");
        war.put("player_side", "defender");
        if (primary != null) war.put("player_is_primary_war_leader", primary);
        ObjectNode army = StrictJson.object(); army.put("army_id", armyId);
        if (soldiers != null) army.put("soldiers", soldiers);
        war.putArray("enemy_armies").add(army); return war;
    }
    private static Observation observe(ObjectNode snapshot) {
        return ParticipatingWarThreatsCodec.observeSnapshot(StrictJson.canonical(snapshot, ParticipatingWarThreatsCodec.MAX_BYTES));
    }
    private static ObjectNode riskJson(NonPrimaryRisk risk) {
        return (ObjectNode) StrictJson.parse(ParticipatingWarThreatsCodec.encodeNonPrimaryRisk(risk),
                ParticipatingWarThreatsCodec.MAX_BYTES);
    }

    @Test void knownDeduplicatedStrengthDoesNotAssessNonleadingOrUnknownLeadershipConsequences() {
        ObjectNode snapshot = snapshot(); ArrayNode wars = (ArrayNode) snapshot.get("active_wars");
        wars.add(war(11, true, 55, 400)); wars.add(war(12, false, 55, 400));
        wars.add(war(13, null, 56, 500));
        Observed observation = assertInstanceOf(Observed.class, observe(snapshot));
        assertEquals(new Known(BigInteger.valueOf(900)), observation.strength());
        ObservedNonPrimaryRisk risk = assertInstanceOf(ObservedNonPrimaryRisk.class, nonPrimaryRisk(observation));
        assertEquals(List.of(12), risk.nonPrimaryWarIds());
        assertEquals(List.of(13), risk.leadershipUnknownWarIds());
        assertEquals(NonPrimaryRiskStatus.UNASSESSED, risk.status());
        assertFalse(risk.politicalAndTerritorialConsequencesAssessed());
        assertFalse(risk.unraisedReservesBounded()); assertFalse(risk.actionAuthorized());
        assertEquals(NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS, risk.nonParticipantLiegeScope());
        byte[] saved = ParticipatingWarThreatsCodec.encodeNonPrimaryRisk(risk);
        assertEquals(risk, ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(saved));
        assertArrayEquals(saved, ParticipatingWarThreatsCodec.encodeNonPrimaryRisk(
                ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(saved)));
        assertEquals(observation, ParticipatingWarThreatsCodec.decode(ParticipatingWarThreatsCodec.encode(observation)),
                "the existing participant observation wire remains independent and unchanged");
    }

    @Test void unavailableAndObservedEmptyScopeRemainDifferentAndNeitherAssertsSafetyOutsidePublishedScope() {
        ObjectNode empty = snapshot(); NonPrimaryRisk emptyRisk = nonPrimaryRisk(observe(empty));
        ObservedNonPrimaryRisk observed = assertInstanceOf(ObservedNonPrimaryRisk.class, emptyRisk);
        assertEquals(NonPrimaryRiskStatus.NO_OBSERVED_NON_PRIMARY_OR_UNRESOLVED_LEADERSHIP_WARS, observed.status());
        ObjectNode missing = empty.deepCopy(); missing.remove("active_wars");
        NonPrimaryRisk unavailable = nonPrimaryRisk(observe(missing));
        assertInstanceOf(UnavailableNonPrimaryRisk.class, unavailable);
        ObjectNode absent = riskJson(unavailable), present = riskJson(emptyRisk);
        assertTrue(absent.get("non_primary_war_ids").isNull());
        assertTrue(present.get("non_primary_war_ids").isArray());
        assertEquals(0, present.get("non_primary_war_ids").size());
        assertFalse(unavailable.politicalAndTerritorialConsequencesAssessed());
        assertEquals(unavailable, ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(
                ParticipatingWarThreatsCodec.encodeNonPrimaryRisk(unavailable)));
    }

    @Test void unknownSoldiersDoNotEraseObservedNonleadingWarsOrCreateKnownRisk() {
        ObjectNode snapshot = snapshot();
        ((ArrayNode) snapshot.get("active_wars")).add(war(12, false, 55, null));
        Observed observation = assertInstanceOf(Observed.class, observe(snapshot));
        assertInstanceOf(Unknown.class, observation.strength());
        ObservedNonPrimaryRisk risk = assertInstanceOf(ObservedNonPrimaryRisk.class, nonPrimaryRisk(observation));
        assertEquals(List.of(12), risk.nonPrimaryWarIds()); assertEquals(NonPrimaryRiskStatus.UNASSESSED, risk.status());
    }

    @Test void strictRiskDecoderRejectsWrongFieldsTypesAndUnsupportedAssessmentOrAuthority() {
        ObjectNode snapshot = snapshot();
        ((ArrayNode) snapshot.get("active_wars")).add(war(12, false, 55, 400));
        ObjectNode saved = riskJson(nonPrimaryRisk(observe(snapshot)));
        for (String field : List.of("source_frame", "non_primary_war_ids", "risk_assessment_status")) {
            ObjectNode wrong = saved.deepCopy(); wrong.remove(field); rejects(wrong);
        }
        ObjectNode extra = saved.deepCopy(); extra.put("safer", true); rejects(extra);
        for (String field : List.of("political_and_territorial_consequences_assessed", "unraised_reserves_bounded", "action_authorized")) {
            ObjectNode wrong = saved.deepCopy(); wrong.put(field, true); rejects(wrong);
        }
        ObjectNode identity = saved.deepCopy(); ((ArrayNode) identity.get("non_primary_war_ids")).set(0, com.fasterxml.jackson.databind.node.BooleanNode.TRUE); rejects(identity);
        ObjectNode alias = saved.deepCopy(); alias.put("risk_assessment_status", "no_observed_non_primary_or_unresolved_leadership_wars"); rejects(alias);
        ObjectNode duplicate = saved.deepCopy(); ((ArrayNode) duplicate.get("leadership_unknown_war_ids")).add(12); rejects(duplicate);
        ObjectNode unavailable = riskJson(new UnavailableNonPrimaryRisk(java.util.Optional.empty(),
                Reason.PUBLISHED_ACTIVE_WAR_ARRAY_UNAVAILABLE, Presence.MISSING));
        unavailable.putArray("non_primary_war_ids"); rejects(unavailable);
    }

    @Test void uint64FrameIdentitySurvivesAsCanonicalDecimalString() {
        ObjectNode snapshot = snapshot();
        snapshot.put("native_revision", StrictJson.UINT64_MAX); snapshot.put("revision", StrictJson.UINT64_MAX);
        NonPrimaryRisk risk = nonPrimaryRisk(observe(snapshot));
        ObjectNode encoded = riskJson(risk);
        assertEquals("18446744073709551615", encoded.get("source_frame").get("revision").textValue());
        assertEquals(risk, ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(
                StrictJson.canonical(encoded, ParticipatingWarThreatsCodec.MAX_BYTES)));
    }

    private static void rejects(ObjectNode value) {
        byte[] bytes = StrictJson.canonical(value, ParticipatingWarThreatsCodec.MAX_BYTES);
        assertThrows(IllegalArgumentException.class, () -> ParticipatingWarThreatsCodec.decodeNonPrimaryRisk(bytes));
    }
}

