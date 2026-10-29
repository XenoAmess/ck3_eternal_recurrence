package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Existing original-producer corpus -> shared source/CB projector -> new settlement branch, without native IO. */
public final class M0PoliticalVerification {
    private static int checks;
    private M0PoliticalVerification() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) { throw new IllegalArgumentException("one existing original-producer corpus path required"); }
        Path corpus = Path.of(arguments[0]);
        if (!Files.isRegularFile(corpus) || Files.size(corpus) > 2 * 1024 * 1024) {
            throw new IllegalArgumentException("bounded actual producer corpus required");
        }
        ObjectNode original = null;
        for (String line : Files.readAllLines(corpus, StandardCharsets.UTF_8)) {
            JsonNode vector = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
            if (vector.path("expected").path("profile_id").asText().equals("refused-liege-demand-primary-rebel-political-exposure-v1")) {
                original = (ObjectNode) StrictJson.parse(StrictJson.text(vector.get("input_json")).getBytes(StandardCharsets.UTF_8));
                break;
            }
        }
        if (original == null) { throw new AssertionError("real original political producer vector absent; no substitute or skip"); }
        ObjectNode request = request(original, "white_peace");
        JsonNode white = evaluate(request);
        check(white.path("status").asText().equals("source_reviewed_conditional"), "original source remains conditionally recognized");
        check(white.path("conditional_political_reasons").size() == 2, "white peace has precisely two reviewed reasons");
        check(white.path("conditional_political_reasons").get(0).asText().equals("revoke_title_reason"), "white peace retains revocation risk");
        check(!white.path("conditional_hard_imprisonment_if_not_imprisoned").booleanValue(), "white peace helper has no hard imprisonment call");
        noActionCredit(white);
        JsonNode defeat = evaluate(request(original, "player_defeat"));
        check(defeat.path("conditional_political_reasons").size() == 4, "defeat has four reviewed reasons");
        check(defeat.path("conditional_hard_imprisonment_if_not_imprisoned").booleanValue(), "defeat conditional hard imprisonment preserved");
        noActionCredit(defeat);

        ObjectNode accepted = original.deepCopy();
        ObjectNode query = query(accepted);
        query.put("cb_allows_white_peace", true);
        ObjectNode option = (ObjectNode) query.get("options").get("white_peace");
        option.put("context_constructed", true).put("native_validator_passed", true).put("available", true);
        option.put("ai_acceptance_observable", false).putNull("ai_acceptance");
        option.put("auto_accept_observable", false).putNull("auto_accept");
        option.putObject("recipient_response").put("status", "available").put("decision_status_raw", 0).put("would_accept_now", true);
        JsonNode legalWhite = evaluate(request(accepted, "white_peace"));
        check(legalWhite.path("native_legal_now").booleanValue(), "same-frame native available retained");
        check(legalWhite.path("recipient_accepts_now").booleanValue(), "same-frame recipient acceptance retained");
        check(legalWhite.path("conditional_political_reasons").size() == 2, "legal accepted white peace is not politically harmless");
        noActionCredit(legalWhite);

        ObjectNode stale = original.deepCopy(); query(stale).put("queried_snapshot_id", "native:stale");
        unknown(evaluate(request(stale, "white_peace")), "stale native query");
        ObjectNode sources = original.deepCopy(); ((ObjectNode) sources.get("current_source_sha256"))
                .put("common/scripted_effects/00_war_effects.txt", "0".repeat(64));
        unknown(evaluate(request(sources, "white_peace")), "source SHA drift");
        ObjectNode unrelated = original.deepCopy();
        ((ObjectNode) query(unrelated).get("active_casus_belli_identity")).put("canonical_key", "individual_county_de_jure_cb");
        unknown(evaluate(request(unrelated, "white_peace")), "de-jure CB cannot inherit refused-demand source profile");
        ObjectNode noLiege = original.deepCopy(); ((ObjectNode) noLiege.get("campaign_root")).put("independent", true);
        unknown(evaluate(request(noLiege, "white_peace")), "unobserved defender liege relation");

        for (String raw : List.of("true", "1.0", "null", "\"1\"")) {
            ObjectNode withoutWarId = original.deepCopy(); withoutWarId.remove("war_id");
            String malformed = "{\"operation\":\"" + RefusedDemandSettlementExposure.OPERATION
                    + "\",\"settlement\":\"white_peace\",\"war_outcome_stakes_request\":{\"war_id\":"
                    + raw + "," + withoutWarId.toString().substring(1) + "}";
            rejects(() -> evaluateRaw(malformed), "wrong integer token " + raw);
        }
        ObjectNode missing = request(original, "white_peace"); missing.remove("war_outcome_stakes_request");
        rejects(() -> evaluate(missing), "missing required source request");
        ObjectNode extra = request(original, "white_peace"); extra.put("safe_white_peace", true);
        rejects(() -> evaluate(extra), "caller cannot supply a safety assertion");
        System.out.println("{\"schema\":\"xar.g2-m0-political-verification/v1\",\"checks_passed\":" + checks
                + ",\"failed\":0,\"skipped\":0,\"game_calls\":0,\"scope\":\"original_producer_to_source_conditional_branch\"}");
    }

    private static ObjectNode request(ObjectNode original, String settlement) {
        ObjectNode row = StrictJson.object().put("operation", RefusedDemandSettlementExposure.OPERATION).put("settlement", settlement);
        row.set("war_outcome_stakes_request", original.deepCopy()); return row;
    }
    private static ObjectNode query(ObjectNode original) { return (ObjectNode) original.get("snapshot").get("war_termination_options").get(0); }
    private static JsonNode evaluate(ObjectNode row) {
        return evaluateRaw(row.toString());
    }
    private static JsonNode evaluateRaw(String raw) {
        byte[] output = RefusedDemandSettlementExposure.execute(raw.getBytes(StandardCharsets.UTF_8));
        JsonNode value = StrictJson.parse(output);
        check(java.util.Arrays.equals(output, StrictJson.canonical(value)), "canonical JSON roundtrip");
        return value;
    }
    private static void unknown(JsonNode value, String reason) {
        check(value.path("status").asText().equals("unknown"), reason + " remains unknown");
        check(value.path("conditional_political_reasons").isEmpty(), reason + " supplies no political facts");
        check(value.path("native_legal_now").isNull() && value.path("recipient_accepts_now").isNull(), reason + " cannot mint native legality");
        noActionCredit(value);
    }
    private static void noActionCredit(JsonNode value) {
        check(!value.path("actual_penalty_verified").booleanValue(), "no actual penalty inferred");
        check(!value.path("automatic_title_transfer_verified").booleanValue(), "no automatic title transfer inferred");
        check(!value.path("action_ready").booleanValue() && value.path("selected_action").isNull(), "source knowledge grants no action");
        check(value.path("actual_war_result").isNull() && value.path("continue_legal_war_processing").booleanValue(),
                "actual result remains unknown while legal processing continues");
    }
    private static void rejects(Runnable body, String label) {
        try { body.run(); } catch (IllegalArgumentException expected) { checks++; return; }
        throw new AssertionError(label);
    }
    private static void check(boolean condition, String label) {
        if (!condition) { throw new AssertionError(label); } checks++;
    }
}
