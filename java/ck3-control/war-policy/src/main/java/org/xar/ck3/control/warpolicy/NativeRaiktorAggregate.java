package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.warpolicy.NativeTerminationTerms.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete or honestly incomplete material aggregate; no source-specific loss or automatic action is inferred. */
public final class NativeRaiktorAggregate {
    public static final String BACKEND = "ck3-1.19.0.6-native-raiktor-surrender-six-domain-v1";
    public static final List<String> ORDER = List.of("claims_base", "gold", "prestige", "prisoner_release",
            "favor_hook", "truce", "generic_war_bound_current");
    private static final Set<String> FRAME_FIELDS = Set.of("snapshot_revision", "native_revision", "date_raw", "paused",
            "war_id", "active_casus_belli_database_index", "active_casus_belli_key", "primary_attacker_character_id",
            "primary_defender_character_id", "claimant_character_id");
    private NativeRaiktorAggregate() { }
    public record Frame(BigInteger snapshotRevision, BigInteger nativeRevision, int dateRaw, int warId,
            int casusBelliIndex, int attacker, int defender, int claimant) {
        public Frame {
            positiveU64(snapshotRevision); positiveU64(nativeRevision);
            require(warId != -1 && attacker != -1 && defender != -1 && claimant != -1
                    && attacker != defender && casusBelliIndex >= 0, "exact paused Raiktor frame required");
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("snapshot_revision", snapshotRevision); row.put("native_revision", nativeRevision);
            row.put("date_raw", dateRaw); row.put("paused", true); row.put("war_id", warId);
            row.put("active_casus_belli_database_index", casusBelliIndex); row.put("active_casus_belli_key", "raiktor_claim_cb");
            row.put("primary_attacker_character_id", attacker); row.put("primary_defender_character_id", defender);
            row.put("claimant_character_id", claimant); return row;
        }
    }
    public static Frame frame(JsonNode value) {
        ObjectNode row = exact(value, FRAME_FIELDS, "aggregate frame");
        require(bool(row.get("paused")) && text(row.get("active_casus_belli_key")).equals("raiktor_claim_cb"),
                "not an exact paused Raiktor frame");
        return new Frame(positiveU64(row.get("snapshot_revision")), positiveU64(row.get("native_revision")),
                signed32(row.get("date_raw")), fullId(row.get("war_id")), nonnegative32(row.get("active_casus_belli_database_index")),
                fullId(row.get("primary_attacker_character_id")), fullId(row.get("primary_defender_character_id")), fullId(row.get("claimant_character_id")));
    }
    public static ObjectNode normalize(JsonNode value, Frame expected) {
        ObjectNode root = exact(value, Set.of("schema_version", "backend_id", "status", "failure", "frame", "claims_base",
                "domains", "missing_domains", "readiness"), "six-domain root");
        require(number(root.get("schema_version"), 1, 1) == 1 && text(root.get("backend_id")).equals(BACKEND)
                && Set.of("complete", "incomplete").contains(text(root.get("status"))) && root.get("failure").isNull(),
                "Raiktor six-domain aggregate unavailable");
        Frame actual = frame(root.get("frame")); require(actual.equals(expected), "Raiktor six-domain root frame disagrees");
        ObjectNode claims = payload(root.get("claims_base"), actual, "claims_base"); if (claims != null) claims(claims);
        ObjectNode domains = exact(root.get("domains"), Set.copyOf(ORDER.subList(1, ORDER.size())), "domains");
        List<String> missing = new ArrayList<>(); if (claims == null) missing.add("claims_base");
        ObjectNode ready = StrictJson.object(); ready.put("claims_base_ready", claims != null);
        boolean sixReady = true; boolean cleanup = false;
        for (String name : ORDER.subList(1, ORDER.size())) {
            ObjectNode payload = payload(domains.get(name), actual, name); boolean available = payload != null;
            ready.put(name + "_ready", available); if (!available) { missing.add(name); sixReady = false; continue; }
            switch (name) {
                case "gold" -> gold(payload, actual);
                case "prestige" -> prestige(payload, actual);
                case "prisoner_release" -> prisoners(payload, actual);
                case "favor_hook" -> favor(payload, actual);
                case "truce" -> NativeRaiktorTruce.normalize(payload, actual);
                case "generic_war_bound_current" -> {
                    NativeRaiktorWarBound.normalize(payload, actual.warId(), actual.attacker(), actual.defender(),
                            actual.snapshotRevision(), actual.nativeRevision(), actual.dateRaw());
                    cleanup = bool(object(payload.get("cleanup"), "cleanup").get("observable"));
                }
                default -> throw new IllegalStateException("domain implementation missing");
            }
        }
        var expectedMissing = JsonNodeFactory.instance.arrayNode(); missing.forEach(expectedMissing::add);
        require(expectedMissing.equals(root.get("missing_domains")), "Raiktor six-domain missing-domain list drifted");
        boolean action = claims != null && sixReady;
        require(text(root.get("status")).equals(action ? "complete" : "incomplete"), "six-domain status differs from readiness");
        ready.put("postwar_cleanup_ready", cleanup); ready.put("source_specific_war_bound_ready", false);
        ready.put("pre_soldiers_ready", false); ready.put("proven_soldier_loss_ready", false);
        ready.put("six_dynamic_domains_ready", sixReady); ready.put("same_frame_stable", action);
        ready.put("action_terms_ready", action); ready.put("automatic_surrender_ready", false);
        require(java.util.Arrays.equals(StrictJson.canonical(ready, StrictJson.EXPLICIT_MAX_BYTES),
                StrictJson.canonical(root.get("readiness"), StrictJson.EXPLICIT_MAX_BYTES)), "six-domain readiness overclaims evidence");
        return root.deepCopy();
    }
    private static ObjectNode payload(JsonNode value, Frame expected, String name) {
        ObjectNode wrapper = object(value, name);
        if (!bool(wrapper.get("available"))) { exact(wrapper, Set.of("available"), name); return null; }
        exact(wrapper, Set.of("available", "frame", "payload"), name);
        require(frame(wrapper.get("frame")).equals(expected), name + " belongs to a different paused frame");
        return object(wrapper.get("payload"), name + ".payload");
    }
    private static void claims(ObjectNode payload) {
        exact(payload, Set.of("target_title_ids", "claims", "attacker_defeat", "target_order_stable", "claim_rows_stable"), "claims payload");
        require(bool(payload.get("target_order_stable")) && bool(payload.get("claim_rows_stable")), "claims stability differs");
        ObjectNode disposition = exact(payload.get("attacker_defeat"), Set.of("declared_title_disposition", "claim_disposition"), "claims disposition");
        require(text(disposition.get("declared_title_disposition")).equals("unchanged")
                && text(disposition.get("claim_disposition")).equals("remove_declared_target_claims"), "claims surrender disposition differs");
        List<Integer> targets = ids(payload.get("target_title_ids")); require(!targets.isEmpty(), "claims target IDs empty");
        var rows = array(payload.get("claims")); require(rows.size() == targets.size(), "claim rows/order differ");
        for (int index = 0; index < rows.size(); index++) {
            ObjectNode row = object(rows.get(index), "claim row"); boolean present = bool(row.get("present"));
            exact(row, present ? Set.of("title_id", "present", "strong", "implicit", "state") : Set.of("title_id", "present", "state"), "claim row");
            require(positive32(row.get("title_id")) == targets.get(index), "claim title order differs");
            String state = present ? (bool(row.get("strong")) ? "strong_" : "weak_") + (bool(row.get("implicit")) ? "implicit" : "explicit") : "absent";
            require(text(row.get("state")).equals(state), "claim state differs");
        }
    }
    private static void gold(ObjectNode payload, Frame frame) {
        exact(payload, Set.of("attacker_current_gold", "defender_current_gold", "attacker_authoritative_monthly_gold_income",
                "defender_authoritative_monthly_gold_income", "actual_transfer", "exact_primary_transfer_observed", "same_frame_stable"), "gold payload");
        character(payload.get("attacker_current_gold"), frame.attacker()); character(payload.get("defender_current_gold"), frame.defender());
        character(payload.get("attacker_authoritative_monthly_gold_income"), frame.attacker());
        character(payload.get("defender_authoritative_monthly_gold_income"), frame.defender());
        ObjectNode transfer = exact(payload.get("actual_transfer"), Set.of("from_character_id", "to_character_id", "value"), "transfer");
        require(fullId(transfer.get("from_character_id")) == frame.attacker() && fullId(transfer.get("to_character_id")) == frame.defender()
                && fixed(transfer.get("value")) >= 0 && bool(payload.get("exact_primary_transfer_observed"))
                && bool(payload.get("same_frame_stable")), "gold domain disagrees");
    }
    private static void prestige(ObjectNode payload, Frame frame) {
        exact(payload, Set.of("attacker_current_prestige", "cb_prestige_factor", "attacker_prestige_delta",
                "exact_factor_and_attacker_delta_observed", "same_frame_stable"), "prestige payload");
        character(payload.get("attacker_current_prestige"), frame.attacker());
        long factor = fixed(payload.get("cb_prestige_factor")); long delta = character(payload.get("attacker_prestige_delta"), frame.attacker());
        require(factor >= 0 && factor <= Long.MAX_VALUE / 10 && delta == -Math.min(factor * 10, 100_000_000L)
                && bool(payload.get("exact_factor_and_attacker_delta_observed")) && bool(payload.get("same_frame_stable")),
                "prestige domain disagrees");
    }
    private static void prisoners(ObjectNode payload, Frame frame) {
        exact(payload, Set.of("attacker_participant_ids", "defender_participant_ids", "attacker_release_candidate_ids",
                "defender_release_candidate_ids", "release_pairs", "full_participant_scan", "primary_and_first_three_successors_scanned",
                "same_frame_stable"), "prisoner payload");
        List<Integer> attackers = fullIds(payload.get("attacker_participant_ids")); List<Integer> defenders = fullIds(payload.get("defender_participant_ids"));
        List<Integer> attackCandidates = fullIds(payload.get("attacker_release_candidate_ids"));
        List<Integer> defendCandidates = fullIds(payload.get("defender_release_candidate_ids"));
        require(!attackers.isEmpty() && !defenders.isEmpty() && !attackCandidates.isEmpty() && !defendCandidates.isEmpty()
                && attackers.contains(frame.attacker()) && defenders.contains(frame.defender())
                && attackCandidates.getFirst() == frame.attacker() && defendCandidates.getFirst() == frame.defender()
                && Collections.disjoint(attackers, defenders) && Collections.disjoint(attackCandidates, defendCandidates)
                && bool(payload.get("full_participant_scan")) && bool(payload.get("primary_and_first_three_successors_scanned"))
                && bool(payload.get("same_frame_stable")), "prisoner domain scan disagrees");
        Set<Pair> seen = new HashSet<>();
        for (JsonNode raw : array(payload.get("release_pairs"))) {
            ObjectNode pair = exact(raw, Set.of("jailer_character_id", "prisoner_character_id", "reason"), "release pair");
            int jailer = fullId(pair.get("jailer_character_id")); int prisoner = fullId(pair.get("prisoner_character_id"));
            boolean forward = attackers.contains(jailer) && defendCandidates.contains(prisoner);
            boolean reverse = defenders.contains(jailer) && attackCandidates.contains(prisoner);
            require(jailer != prisoner && forward != reverse && seen.add(new Pair(jailer, prisoner))
                    && text(pair.get("reason")).equals("opposite_primary_or_first_three_successors"), "release pair disagrees");
        }
    }
    private record Pair(int jailer, int prisoner) { }
    private static void favor(ObjectNode payload, Frame frame) {
        exact(payload, Set.of("claimant_distinct_from_attacker", "original_visible_root_traversed", "will_apply", "same_frame_stable"), "favor payload");
        boolean distinct = bool(payload.get("claimant_distinct_from_attacker")); boolean traversed = bool(payload.get("original_visible_root_traversed"));
        boolean applies = bool(payload.get("will_apply"));
        require(distinct == (frame.claimant() != frame.attacker()) && bool(payload.get("same_frame_stable"))
                && !(distinct && !traversed) && !(!distinct && (traversed || applies)), "favor domain disagrees");
    }
    private static List<Integer> fullIds(JsonNode value) {
        List<Integer> ids = new ArrayList<>(); Set<Integer> seen = new HashSet<>();
        for (JsonNode row : array(value)) { int id = fullId(row); require(seen.add(id), "duplicate generation"); ids.add(id); }
        return List.copyOf(ids);
    }
    private static long character(JsonNode value, int expected) {
        ObjectNode row = exact(value, Set.of("character_id", "value"), "character value");
        require(fullId(row.get("character_id")) == expected, "character value identity differs"); return fixed(row.get("value"));
    }
    private static long fixed(JsonNode value) {
        ObjectNode row = exact(value, Set.of("raw", "scale"), "fixed point"); number(row.get("scale"), 100_000, 100_000);
        return number(row.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE);
    }
}
