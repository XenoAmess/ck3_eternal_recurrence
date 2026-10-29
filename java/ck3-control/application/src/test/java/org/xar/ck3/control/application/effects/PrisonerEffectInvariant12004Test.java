package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.prisoners.PrisonerActionBinding12004;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;

/** Source-level regression cases; no constructed observation claims a real game outcome. */
final class PrisonerEffectInvariant12004Test {
    @Test void currentGoldNeedsObservedPositiveGainWithoutReusingThePausedQuoteAsExactPayment() {
        BigInteger before = BigInteger.valueOf(1000), quoted = BigInteger.valueOf(500);
        assertTrue(NativePrisonerEffects12004.ransomMaterialObserved(false, before, BigInteger.valueOf(1001), quoted, true));
        assertFalse(NativePrisonerEffects12004.ransomMaterialObserved(false, before, BigInteger.valueOf(1001), quoted, false));
        assertTrue(NativePrisonerEffects12004.ransomMaterialObserved(false, before, BigInteger.valueOf(1500), quoted, false));
        assertFalse(NativePrisonerEffects12004.ransomMaterialObserved(true, before, BigInteger.valueOf(2000), quoted, true));
        assertFalse(NativePrisonerEffects12004.ransomMaterialObserved(false, before, before, quoted, true));
        assertThrows(IllegalArgumentException.class, () -> NativePrisonerEffects12004.ransomMaterialObserved(false, before, before, BigInteger.ZERO, true));
    }
    @Test void independentCustodyPreservesFreeTransferAndDeathAsDifferentBranchesAcrossSerialization() {
        var frame = new PrisonerMaterial12004.Frame(BigInteger.valueOf(1015), 53286361, 29829, 0xfffffff0L);
        List<PrisonerMaterial12004.Custody> states = List.of(new PrisonerMaterial12004.Free(frame), new PrisonerMaterial12004.Dead(frame),
                new PrisonerMaterial12004.HeldByOther(frame, 0xfffffffeL), new PrisonerMaterial12004.HeldByPlayer(frame));
        for (var state : states) assertEquals(state, PrisonerMaterial12004.decodeCustody(PrisonerMaterial12004.encode(state), frame));
        ObjectNode wrong = (ObjectNode) StrictJson.parse(PrisonerMaterial12004.encode(new PrisonerMaterial12004.Free(frame)));
        wrong.put("target_alive", 1);
        assertThrows(IllegalArgumentException.class, () -> PrisonerMaterial12004.decodeCustody(wrong, frame));
    }
    @Test void retainedWarProofKeepsTheFullUnsignedGenerationWithoutSignedIntTruncation() {
        var frame = new PrisonerRansomFormalPolicy12004.Frame(BigInteger.valueOf(37), BigInteger.valueOf(1014), 53286360, 29829, List.of(16777231L));
        ObjectNode root = StrictJson.object().put("snapshot_revision", 1014).put("step", "query-war-prisoner-release-pairs-v1-16777231")
                .put("accepted", true).put("status", "available").put("read_only", true).put("backend_id", "native-headless").put("query_sequence", 1);
        ObjectNode proof = root.putObject("war_prisoner_release_pairs_v1").put("war_id", 16777231).put("date_raw", 53286360)
                .put("same_frame_stable", true).put("full_participant_scan", true).put("primary_and_first_three_successors_scanned", true)
                .put("active_casus_belli_key", "individual_county_de_jure_cb").put("active_casus_belli_database_index", 4)
                .put("primary_attacker_character_id", 0x80000001L).put("primary_defender_character_id", 0xfffffffeL);
        proof.putArray("attacker_participant_ids").add(0x80000001L); proof.putArray("defender_participant_ids").add(0xfffffffeL);
        proof.putArray("attacker_release_candidate_ids").add(0x80000001L); proof.putArray("defender_release_candidate_ids").add(0xfffffffeL);
        proof.putArray("release_pairs");
        var read = assertInstanceOf(PrisonerRansomFormalPolicy12004.KnownWarRetention.class,
                PrisonerRansomFormalPolicy12004.readWar(StrictJson.canonical(root), frame, 16777231));
        assertEquals(List.of(0x80000001L, 0xfffffffeL), read.retainedPrisonerIds());
        proof.withArray("attacker_release_candidate_ids").add(0xffffffffL);
        assertThrows(IllegalArgumentException.class, () -> PrisonerRansomFormalPolicy12004.readWar(StrictJson.canonical(root), frame, 16777231));
    }
    @Test void walletRejectsBooleanFloatingMissingAndWrongScaleRatherThanInventingZero() {
        ObjectNode snapshot = StrictJson.object(); snapshot.putObject("played_character_gold").put("raw", Long.MIN_VALUE).put("scale", 100000);
        assertEquals(BigInteger.valueOf(Long.MIN_VALUE), PrisonerActionBinding12004.gold(json(snapshot)));
        ((ObjectNode) snapshot.get("played_character_gold")).put("raw", true);
        assertThrows(IllegalArgumentException.class, () -> PrisonerActionBinding12004.gold(json(snapshot)));
        ((ObjectNode) snapshot.get("played_character_gold")).put("raw", 1.0);
        assertThrows(IllegalArgumentException.class, () -> PrisonerActionBinding12004.gold(json(snapshot)));
        ((ObjectNode) snapshot.get("played_character_gold")).put("raw", 1).put("scale", 1000);
        assertThrows(IllegalArgumentException.class, () -> PrisonerActionBinding12004.gold(json(snapshot)));
    }
    private static org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj json(ObjectNode value) {
        return org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(value)), "synthetic wallet");
    }
}
