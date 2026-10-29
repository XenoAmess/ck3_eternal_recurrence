package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Authored source-shaped policy cases; no Native wire/live qualification is attributed to these vectors. */
final class OrdinaryWhitePeacePolicyTest {
    static ObjectNode frame(OrdinaryWhitePeacePolicy.Variant variant) {
        boolean claim = variant == OrdinaryWhitePeacePolicy.Variant.CLAIM_CB;
        boolean attacker = claim || variant == OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE;
        String side = attacker ? "attacker" : "defender";
        String cb = claim ? "claim_cb" : variant == OrdinaryWhitePeacePolicy.Variant.DEFENDER_MINOR_RELIGIOUS ? "minor_religious_war" : "individual_county_de_jure_cb";
        int index = claim ? 8 : variant == OrdinaryWhitePeacePolicy.Variant.DEFENDER_MINOR_RELIGIOUS ? 41 : 17;
        ObjectNode frame = StrictJson.object().put("paused", true).put("snapshot_id", "source:11").put("revision", 12).put("native_revision", 11).put("date_raw", 1000).put("episode_run_id", "source-episode");
        frame.putObject("diagnostics").put("connection_generation", 5); frame.putObject("played_character").put("character_id", 7);
        ObjectNode war = frame.putArray("active_wars").addObject().put("war_id", 23).put("player_side", side).put("player_is_primary_war_leader", true).put("player_relative_war_score", 7);
        war.putArray("targeted_title_ids").add(101);
        ObjectNode options = frame.putArray("war_termination_options").addObject().put("war_id", 23).put("player_side", side)
                .put("player_is_primary_war_leader", true).put("player_relative_war_score", 7).put("war_duration_days", claim ? 365 : 180)
                .put("active_casus_belli_present", true).put("cb_allows_white_peace", true);
        options.putObject("active_casus_belli_identity").put("canonical_key", cb).put("database_index", index); binding(options);
        ObjectNode white = options.putObject("options").putObject("white_peace").put("outcome", "white_peace").put("hostage_variant", "none")
                .put("context_constructed", true).put("native_validator_passed", true).put("available", true).put("ai_acceptance_observable", true);
        white.putObject("ai_acceptance").put("raw", 1234); white.putObject("recipient_response").put("status", attacker ? "available" : "unavailable").put("would_accept_now", attacker ? true : false);
        if (claim) {
            ObjectNode terms = frame.putArray("war_termination_terms").addObject().put("war_id", 23).put("status", "available").put("claimant_character_id", 7); binding(terms);
            terms.putObject("casus_belli").put("canonical_key", cb).put("database_index", index); terms.putObject("readiness").put("ready", true);
            terms.putArray("target_title_ids").add(101); terms.putArray("claims").addObject().put("title_id", 101).put("present", true);
        } else frame.putArray("war_termination_terms");
        return frame;
    }
    private static void binding(ObjectNode row) { row.put("queried_snapshot_id", "source:11").put("queried_revision", 12).put("queried_native_revision", 11).put("queried_connection_generation", 5).put("episode_run_id", "source-episode"); }
    static Obj obj(JsonNode value) { return DriverJson.object(StrictJson.canonical(value), DriverJson.MAX_NATIVE_BYTES); }
    static ObjectNode options(ObjectNode frame) { return (ObjectNode) frame.get("war_termination_options").get(0); }
    static ObjectNode white(ObjectNode frame) { return (ObjectNode) options(frame).get("options").get("white_peace"); }
    @Test void allFourOriginalBranchesRetainExactEvidenceAndSerde() {
        for (var variant : OrdinaryWhitePeacePolicy.Variant.values()) {
            var input = obj(frame(variant)); var result = OrdinaryWhitePeacePolicy.evaluate(input, 23); assertInstanceOf(OrdinaryWhitePeacePolicy.Ready.class, result);
            var ready = (OrdinaryWhitePeacePolicy.Ready) result; assertEquals(variant, ready.variant());
            var encoded = OpportunityJson.encode(OrdinaryWhitePeacePolicy.originalTuple(result));
            assertEquals(OrdinaryWhitePeacePolicy.originalTuple(result), OpportunityJson.parse(encoded));
            assertEquals(input.get("active_wars") instanceof Arr array ? array.items().getFirst() : null, ready.war());
            assertEquals(variant != OrdinaryWhitePeacePolicy.Variant.CLAIM_CB, ready.evidence().members().containsKey("variant"));
        }
    }
    @Test void defenderQuoteDoesNotBecomeARecipientAnswer() {
        var input = frame(OrdinaryWhitePeacePolicy.Variant.DEFENDER_DE_JURE); ((ObjectNode) white(input).get("recipient_response")).putNull("would_accept_now");
        var ready = assertInstanceOf(OrdinaryWhitePeacePolicy.Ready.class, OrdinaryWhitePeacePolicy.evaluate(obj(input), 23));
        assertEquals(Nil.INSTANCE, ((Obj) ready.whitePeace().get("recipient_response")).get("would_accept_now"));
        for (long raw : List.of(-1L, 0L)) { ((ObjectNode) white(input).get("ai_acceptance")).put("raw", raw); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(input), 23).ready()); }
    }
    @Test void attackerDurationScoreAndClaimsBoundariesAreExact() {
        var deJure = frame(OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE); options(deJure).put("war_duration_days", 179); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(deJure), 23).ready());
        options(deJure).put("war_duration_days", 180); assertTrue(OrdinaryWhitePeacePolicy.evaluate(obj(deJure), 23).ready());
        for (int score : List.of(0, 100)) { ((ObjectNode) deJure.get("active_wars").get(0)).put("player_relative_war_score", score); options(deJure).put("player_relative_war_score", score); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(deJure), 23).ready()); }
        var claim = frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB); options(claim).put("war_duration_days", 364); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(claim), 23).ready());
        options(claim).put("war_duration_days", 365); assertTrue(OrdinaryWhitePeacePolicy.evaluate(obj(claim), 23).ready());
        ((ObjectNode) claim.get("war_termination_terms").get(0).get("claims").get(0)).put("present", false); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(claim), 23).ready());
    }
    @Test void staleDuplicateMissingAndWrongRuntimeTypesCannotAdmit() throws Exception {
        var base = frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB);
        for (String key : List.of("queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_connection_generation", "episode_run_id")) {
            var stale = base.deepCopy(); ((ObjectNode) stale.get("war_termination_options").get(0)).remove(key); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(stale), 23).ready(), key);
        }
        ((com.fasterxml.jackson.databind.node.ArrayNode) base.get("war_termination_options")).add(options(base).deepCopy()); assertFalse(OrdinaryWhitePeacePolicy.evaluate(obj(base), 23).ready());
        for (String invalid : List.of("true", "1.0", "\"7\"", "[]", "{}")) {
            var value = frame(OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE);
            ((ObjectNode) value.get("active_wars").get(0)).set("player_relative_war_score", StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8)));
            options(value).set("player_relative_war_score", value.get("active_wars").get(0).get("player_relative_war_score"));
            // The full input parser preserves decimals; malformed policy integer is then explicitly rejected.
            Obj input = DriverJson.object(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(value), DriverJson.MAX_NATIVE_BYTES);
            assertThrows(IllegalArgumentException.class, () -> OrdinaryWhitePeacePolicy.evaluate(input, 23));
        }
    }
    @Test void cbOneShotAppliesOnlyToItsOriginalWhitePeaceVariantAndEpisode() {
        Obj action = historyAction(23, 1000, "source-episode", "submitted_pending", "individual_county_de_jure_cb", 17);
        Arr history = new Arr(List.of(new Obj(java.util.Map.of("command", new Text("offer-white-peace-23"), "ok", new Bool(true), "result", new Obj(java.util.Map.of("war_termination_result", action))))));
        assertTrue(OrdinaryWarAdmissionRules.whitePeaceFence(history, 23, new Text("source-episode"), OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE).isPresent());
        assertTrue(OrdinaryWarAdmissionRules.whitePeaceFence(history, 23, new Text("other-episode"), OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE).isEmpty());
        assertTrue(OrdinaryWarAdmissionRules.whitePeaceFence(history, 23, new Text("source-episode"), OrdinaryWhitePeacePolicy.Variant.CLAIM_CB).isEmpty());
        assertTrue(OrdinaryWarAdmissionRules.whitePeaceFence(history, 24, new Text("source-episode"), OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE).isEmpty());
    }
    @Test void cooldownPreservesNegativeElapsedAndExactBoundary() {
        var action = historyAction(23, 1000, "source-episode", "submitted_pending", "claim_cb", 8);
        Arr rows = new Arr(List.of(new Obj(java.util.Map.of("command", new Text("offer-white-peace-23"), "ok", new Bool(true), "index", new IntegerValue(BigInteger.ONE), "result", new Obj(java.util.Map.of("war_termination_result", action))))));
        for (int current : List.of(999, 1000, 1719)) assertTrue(OrdinaryWarAdmissionRules.whitePeaceCooldown(rows, 23, new IntegerValue(BigInteger.valueOf(current)), new Text("source-episode")).isPresent());
        assertTrue(OrdinaryWarAdmissionRules.whitePeaceCooldown(rows, 23, new IntegerValue(BigInteger.valueOf(1720)), new Text("source-episode")).isEmpty());
        assertTrue(OrdinaryWarAdmissionRules.whitePeaceCooldown(rows, 23, new Bool(true), new Text("source-episode")).isPresent());
    }
    @Test void declarationOriginalUnknownNeverBecomesAnotherCbAttempt() {
        var input = frame(OrdinaryWhitePeacePolicy.Variant.DEFENDER_DE_JURE);
        for (String status : List.of("submission_unknown", "declaration_submitted")) {
            input.putObject("war_declaration_continuity_v1").put("schema", "war-declaration-continuity-v1").put("status", status).put("native_response", "unknown").put("request_id", "original");
            assertEquals(OrdinaryWarAdmissionRules.Declaration.ORIGINAL_UNRESOLVED, OrdinaryWarAdmissionRules.declaration(obj(input), List.of()));
        }
        for (String terminal : List.of("war_started", "native_rejected", "not_submitted")) {
            ((ObjectNode) input.get("war_declaration_continuity_v1")).put("status", terminal);
            assertEquals(OrdinaryWarAdmissionRules.Declaration.CLEAR, OrdinaryWarAdmissionRules.declaration(obj(input), List.of()));
        }
    }
    static Obj historyAction(int id, int date, String episode, String status, String cb, int databaseIndex) {
        var value = StrictJson.object().put("war_id", id).put("outcome", "white_peace").put("episode_run_id", episode).put("status", status).put("submitted_date_raw", date);
        value.putObject("casus_belli").put("canonical_key", cb).put("database_index", databaseIndex); return obj(value);
    }
}
