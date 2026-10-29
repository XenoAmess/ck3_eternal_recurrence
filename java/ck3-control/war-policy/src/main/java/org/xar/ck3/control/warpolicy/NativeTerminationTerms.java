package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete original claim/Raiktor terms union. A query ACK supplies no material observation. */
public final class NativeTerminationTerms {
    public static final String CLAIM = "claim_cb_claim_disposition";
    public static final String RAIKTOR = "raiktor_claim_cb_attacker_defeat_disposition";
    private static final Set<String> COMMON = Set.of("schema_version", "status", "war_id", "casus_belli",
            "supported_slice", "readiness", "provenance");
    private static final List<String> EFFECTS = List.of("actual_gold_transfer", "actual_prestige_delta",
            "actual_truce_expiry", "actual_prisoner_release_pairs", "conditional_favor_hook_application",
            "targeting_faction_discontent_delta", "glory_hound_vassal_opinion_rows", "antagonistic_clan_vassal_opinion_rows",
            "existing_house_feud_score_delta", "attacker_mandala_piety_experience_delta", "defender_mandala_serenity",
            "defender_accolade_glory", "laamp_actual_settlement_outside_cb_effect", "war_bound_army_losses");
    private NativeTerminationTerms() { }

    public static ObjectNode normalize(JsonNode value, int expectedWarId) {
        require(expectedWarId > 0, "positive expected WarID required");
        ObjectNode root = object(value, "native war_termination_terms");
        String status = text(root.get("status")); String slice = text(root.get("supported_slice"));
        Set<String> fields = new HashSet<>(COMMON); boolean available = status.equals("available");
        if (available && slice.equals(CLAIM)) fields.addAll(Set.of("claimant_character_id", "target_title_ids", "claims", "outcomes"));
        else if (available && slice.equals(RAIKTOR)) {
            fields.addAll(Set.of("claimant_character_id", "target_title_ids", "claims", "attacker_defeat", "gold_reparations",
                    "attacker_fame", "truce", "prisoner_release", "conditional_favor_hook", "attacker_legitimacy_delta",
                    "attacker_influence_delta", "hostages_allowed", "unobserved_dynamic_effects"));
            if (root.has("generic_war_bound_current")) fields.add("generic_war_bound_current");
        } else if (status.equals("unsupported")) fields.add("reason");
        else throw new IllegalArgumentException("native war_termination_terms.status is malformed");
        exact(root, fields, "native war_termination_terms");
        require(number(root.get("schema_version"), 1, 1) == 1, "native war_termination_terms schema differs");
        int warId = positive32(root.get("war_id")); require(warId == expectedWarId, "native war_termination_terms WarID mismatch");
        ObjectNode cb = exact(root.get("casus_belli"), Set.of("database_index", "canonical_key"), "casus_belli");
        int cbIndex = nonnegative32(cb.get("database_index")); String key = text(cb.get("canonical_key"));
        require(Set.of(CLAIM, RAIKTOR).contains(slice), "native war_termination_terms supported slice drifted");
        ObjectNode provenance = provenance(root.get("provenance"), available ? slice : CLAIM);
        ObjectNode normalized = root.deepCopy(); normalized.set("provenance", provenance);
        if (!available) {
            boolean actual4UnsupportedRaiktor = key.equals("raiktor_claim_cb")
                    && text(provenance.get("game_version")).equals("1.20.0.4");
            // Actual .4 C++ only implements claim_cb. Its genuine unsupported Raiktor
            // packet uses the CLAIM slice/provenance; this confers no available terms.
            require(slice.equals(CLAIM) && (!Set.of("claim_cb", "raiktor_claim_cb").contains(key) || actual4UnsupportedRaiktor)
                    && text(root.get("reason")).equals("casus_belli_not_claim_cb"), "native war_termination_terms unsupported branch malformed");
            readiness(root.get("readiness"), Set.of(), Set.of("ready")); return normalized;
        }
        require(key.equals(slice.equals(CLAIM) ? "claim_cb" : "raiktor_claim_cb"), "available terms CB key differs from slice");
        int claimant = positive32(root.get("claimant_character_id"));
        List<Integer> targets = ids(root.get("target_title_ids")); require(!targets.isEmpty(), "target titles must be nonempty");
        ArrayNode claims = array(root.get("claims")); require(claims.size() == targets.size(), "claims must match target titles");
        for (int index = 0; index < claims.size(); index++) {
            ObjectNode claim = object(claims.get(index), "claim"); boolean present = bool(claim.get("present"));
            exact(claim, present ? Set.of("title_id", "present", "strong", "implicit", "state")
                    : Set.of("title_id", "present", "state"), "claim");
            require(positive32(claim.get("title_id")) == targets.get(index), "claim schema/title order differs");
            String expected = present ? (bool(claim.get("strong")) ? "strong_" : "weak_")
                    + (bool(claim.get("implicit")) ? "implicit" : "explicit") : "absent";
            require(text(claim.get("state")).equals(expected), "claim state is inconsistent");
        }
        if (slice.equals(CLAIM)) {
            ObjectNode outcomes = exact(root.get("outcomes"), Set.of("attacker_victory", "white_peace", "attacker_defeat"), "outcomes");
            disposition(outcomes.get("attacker_victory"), "transfer_to_claimant_via_conquest_claim", "resolve_with_add_claim_on_loss");
            disposition(outcomes.get("white_peace"), "unchanged", "retain_and_strengthen_weak");
            disposition(outcomes.get("attacker_defeat"), "unchanged", "remove_declared_target_claims");
            readiness(root.get("readiness"), Set.of("identity_ready", "targets_ready", "claim_rows_ready",
                    "claim_disposition_ready", "ready"), Set.of());
            return normalized;
        }
        ObjectNode gold = gold(root.get("gold_reparations")); ObjectNode fame = fame(root.get("attacker_fame"));
        ObjectNode prisoners = prisoners(root.get("prisoner_release")); ObjectNode favor = favor(root.get("conditional_favor_hook"));
        ObjectNode truce = truce(root.get("truce")); JsonNode generic = root.get("generic_war_bound_current");
        ObjectNode warBound = null;
        if (generic != null && !generic.isNull()) {
            ObjectNode active = object(object(generic, "generic war-bound").get("active_frame"), "generic active frame");
            require(nonnegative32(active.get("active_casus_belli_database_index")) == cbIndex, "generic war-bound CB identity drifted");
            warBound = NativeRaiktorWarBound.normalize(generic, warId, fullId(active.get("primary_attacker_character_id")),
                    fullId(active.get("primary_defender_character_id")), positiveU64(active.get("snapshot_revision")),
                    positiveU64(active.get("native_revision")), signed32(active.get("date_raw")));
        }
        boolean goldReady = bool(gold.get("actual_amount_observable")); boolean fameReady = bool(fame.get("actual_delta_observable"));
        boolean prisonerReady = bool(prisoners.get("actual_pairs_observable")); boolean favorReady = bool(favor.get("actual_applies_observable"));
        boolean truceReady = bool(truce.get("evaluated_days_observable"));
        ObjectNode ready = StrictJson.object();
        for (String field : List.of("identity_ready", "targets_ready", "claim_rows_ready", "attacker_defeat_rule_ready", "static_formula_ready"))
            ready.put(field, true);
        ready.put("finance_ready", goldReady); ready.put("gold_ready", goldReady); ready.put("fame_factor_ready", fameReady);
        ready.put("attacker_prestige_delta_ready", fameReady); ready.put("truce_ready", truceReady);
        ready.put("prisoner_release_ready", prisonerReady); ready.put("favor_hook_ready", favorReady);
        ready.put("war_bound_armies_ready", false); ready.put("same_frame_stable",
                goldReady || fameReady || prisonerReady || favorReady || truceReady || warBound != null);
        for (String field : List.of("dynamic_deltas_ready", "decision_ready", "automatic_surrender_ready", "ready")) ready.put(field, false);
        equal(root.get("readiness"), ready, "Raiktor terms readiness differs");
        ArrayNode unobserved = JsonNodeFactory.instance.arrayNode();
        for (String effect : EFFECTS) {
            boolean observed = switch (effect) {
                case "actual_gold_transfer" -> goldReady;
                case "actual_prestige_delta" -> fameReady;
                case "actual_prisoner_release_pairs" -> prisonerReady;
                case "conditional_favor_hook_application" -> favorReady;
                default -> false;
            };
            if (!observed) unobserved.add(effect);
        }
        equal(root.get("unobserved_dynamic_effects"), unobserved, "Raiktor terms uncertainty set differs");
        disposition(root.get("attacker_defeat"), "unchanged", "remove_declared_target_claims");
        fixed(root.get("attacker_legitimacy_delta")); fixed(root.get("attacker_influence_delta"));
        require(number(root.get("attacker_legitimacy_delta").get("raw"), 0, 0) == 0
                && number(root.get("attacker_influence_delta").get("raw"), 0, 0) == 0
                && !bool(root.get("hostages_allowed")), "Raiktor fixed effects or hostages differ");
        Integer attacker = null; Integer defender = null;
        if (goldReady) {
            attacker = positive32(gold.get("attacker_current_gold").get("character_id"));
            defender = positive32(gold.get("defender_current_gold").get("character_id"));
        }
        if (fameReady) {
            int fameAttacker = positive32(fame.get("attacker_current_prestige").get("character_id"));
            require(attacker == null || attacker == fameAttacker, "attacker identity drifted across resource domains"); attacker = fameAttacker;
        }
        if (prisonerReady) {
            int prisonerAttacker = ids(prisoners.get("attacker_release_candidate_ids")).getFirst();
            int prisonerDefender = ids(prisoners.get("defender_release_candidate_ids")).getFirst();
            require(ids(prisoners.get("attacker_participant_ids")).contains(prisonerAttacker)
                    && ids(prisoners.get("defender_participant_ids")).contains(prisonerDefender)
                    && (attacker == null || attacker == prisonerAttacker) && (defender == null || defender == prisonerDefender),
                    "participant identity drifted across domains");
            attacker = prisonerAttacker; defender = prisonerDefender;
        }
        if (favorReady && attacker != null) require(bool(favor.get("claimant_distinct_from_attacker")) == (claimant != attacker),
                "favor claimant identity drifted");
        if (warBound != null) {
            ObjectNode active = object(warBound.get("active_frame"), "generic active frame");
            require((attacker == null || attacker == fullId(active.get("primary_attacker_character_id")))
                    && (defender == null || defender == fullId(active.get("primary_defender_character_id"))),
                    "war-bound identity drifted across domains");
        }
        normalized.set("gold_reparations", gold); normalized.set("attacker_fame", fame); normalized.set("prisoner_release", prisoners);
        normalized.set("conditional_favor_hook", favor); normalized.set("truce", truce);
        normalized.set("generic_war_bound_current", warBound); normalized.set("readiness", ready);
        return normalized;
    }

    private static ObjectNode gold(JsonNode raw) {
        ObjectNode value = exact(raw, Set.of("direction", "factor", "positive_income_basis", "fallback_condition", "fallback_basis",
                "defender_culture_multiplier", "actual_amount_observable", "attacker_current_gold", "defender_current_gold",
                "attacker_authoritative_monthly_gold_income", "defender_authoritative_monthly_gold_income", "actual_transfer"), "gold_reparations");
        require(text(value.get("direction")).equals("primary_attacker_to_primary_defender") && number(value.get("factor"), 3, 3) == 3
                && text(value.get("positive_income_basis")).equals("primary_attacker_yearly_income")
                && text(value.get("fallback_condition")).equals("landless_adventurer_or_nonpositive_monthly_income")
                && text(value.get("fallback_basis")).equals("primary_attacker_medium_gold_value")
                && text(value.get("defender_culture_multiplier")).equals("2_if_primary_defender_has_more_gold_for_successful_defensive_wars_else_1"),
                "gold reparations authored formula drifted");
        List<String> dynamic = List.of("attacker_current_gold", "defender_current_gold", "attacker_authoritative_monthly_gold_income",
                "defender_authoritative_monthly_gold_income", "actual_transfer");
        if (!bool(value.get("actual_amount_observable"))) { nulls(value, dynamic); return value.deepCopy(); }
        for (String field : dynamic.subList(0, 4)) characterFixed(value.get(field));
        ObjectNode transfer = exact(value.get("actual_transfer"), Set.of("from_character_id", "to_character_id", "value"), "actual_transfer");
        fixed(transfer.get("value"));
        int attacker = positive32(value.get("attacker_current_gold").get("character_id"));
        int defender = positive32(value.get("defender_current_gold").get("character_id"));
        require(attacker != defender && positive32(value.get("attacker_authoritative_monthly_gold_income").get("character_id")) == attacker
                && positive32(value.get("defender_authoritative_monthly_gold_income").get("character_id")) == defender
                && positive32(transfer.get("from_character_id")) == attacker && positive32(transfer.get("to_character_id")) == defender
                && number(transfer.get("value").get("raw"), 0, Long.MAX_VALUE) >= 0, "gold primary identities/direction differ");
        return value.deepCopy();
    }
    private static ObjectNode fame(JsonNode raw) {
        ObjectNode value = exact(raw, Set.of("resource", "base", "scale", "limit_rule", "actual_delta_observable",
                "attacker_current_prestige", "cb_prestige_factor", "attacker_prestige_delta"), "attacker_fame");
        require(text(value.get("resource")).equals("prestige") && text(value.get("base")).equals("cb_prestige_factor")
                && number(value.get("scale"), -10, -10) == -10 && text(value.get("limit_rule")).equals("loss_capped_at_1000"),
                "attacker fame authored formula drifted");
        if (!bool(value.get("actual_delta_observable"))) {
            nulls(value, List.of("attacker_current_prestige", "cb_prestige_factor", "attacker_prestige_delta")); return value.deepCopy();
        }
        characterFixed(value.get("attacker_current_prestige")); characterFixed(value.get("attacker_prestige_delta"));
        fixed(value.get("cb_prestige_factor"));
        BigInteger factor = integer(value.get("cb_prestige_factor").get("raw"));
        BigInteger expected = factor.multiply(BigInteger.valueOf(-10)).max(BigInteger.valueOf(-100_000_000));
        require(factor.signum() >= 0 && positive32(value.get("attacker_current_prestige").get("character_id"))
                == positive32(value.get("attacker_prestige_delta").get("character_id"))
                && integer(value.get("attacker_prestige_delta").get("value").get("raw")).equals(expected),
                "attacker fame factor/delta formula differs");
        return value.deepCopy();
    }
    private static ObjectNode prisoners(JsonNode raw) {
        ObjectNode value = exact(raw, Set.of("rule", "actual_pairs_observable", "attacker_participant_ids", "defender_participant_ids",
                "attacker_release_candidate_ids", "defender_release_candidate_ids", "release_pairs", "full_participant_scan",
                "primary_and_first_three_successors_scanned"), "prisoner_release");
        require(text(value.get("rule")).equals("war_result_primary_and_first_three_heirs"), "prisoner rule drifted");
        if (!bool(value.get("actual_pairs_observable"))) {
            nulls(value, List.of("attacker_participant_ids", "defender_participant_ids", "attacker_release_candidate_ids",
                    "defender_release_candidate_ids", "release_pairs", "full_participant_scan", "primary_and_first_three_successors_scanned"));
            return value.deepCopy();
        }
        List<Integer> attackers = ids(value.get("attacker_participant_ids")); List<Integer> defenders = ids(value.get("defender_participant_ids"));
        List<Integer> attackCandidates = ids(value.get("attacker_release_candidate_ids"));
        List<Integer> defendCandidates = ids(value.get("defender_release_candidate_ids"));
        require(!attackers.isEmpty() && !defenders.isEmpty() && !attackCandidates.isEmpty() && !defendCandidates.isEmpty()
                && java.util.Collections.disjoint(attackers, defenders) && java.util.Collections.disjoint(attackCandidates, defendCandidates)
                && bool(value.get("full_participant_scan")) && bool(value.get("primary_and_first_three_successors_scanned")),
                "prisoner complete-scan identity malformed");
        Set<ReleasePair> seen = new HashSet<>();
        for (JsonNode pairValue : array(value.get("release_pairs"))) {
            ObjectNode pair = exact(pairValue, Set.of("jailer_character_id", "prisoner_character_id", "reason"), "release pair");
            int jailer = positive32(pair.get("jailer_character_id")); int prisoner = positive32(pair.get("prisoner_character_id"));
            require(text(pair.get("reason")).equals("opposite_primary_or_first_three_successors") && seen.add(new ReleasePair(jailer, prisoner))
                    && (defenders.contains(jailer) && attackCandidates.contains(prisoner)
                        || attackers.contains(jailer) && defendCandidates.contains(prisoner)), "prisoner direction/reason differs");
        }
        return value.deepCopy();
    }
    private record ReleasePair(int jailer, int prisoner) { }
    private static ObjectNode favor(JsonNode raw) {
        ObjectNode value = exact(raw, Set.of("rule", "actual_applies_observable", "claimant_distinct_from_attacker",
                "original_visible_root_traversed", "will_apply"), "conditional_favor_hook");
        require(text(value.get("rule")).equals("attacker_on_claimant_if_distinct_and_can_add_favor_hook"), "favor rule drifted");
        if (!bool(value.get("actual_applies_observable"))) {
            nulls(value, List.of("claimant_distinct_from_attacker", "original_visible_root_traversed", "will_apply")); return value.deepCopy();
        }
        boolean distinct = bool(value.get("claimant_distinct_from_attacker")); boolean traversed = bool(value.get("original_visible_root_traversed"));
        boolean applies = bool(value.get("will_apply"));
        require(!(!distinct && (traversed || applies)) && !(distinct && !traversed), "favor authored outer gate malformed");
        return value.deepCopy();
    }
    private static ObjectNode truce(JsonNode raw) {
        ObjectNode value = exact(raw, Set.of("direction", "result", "evaluated_days_observable", "evaluated_days",
                "actual_expiry_observable", "expiry_date_raw"), "truce");
        require(text(value.get("direction")).equals("primary_attacker_toward_primary_defender")
                && text(value.get("result")).equals("defeat"), "truce authored rule drifted");
        boolean observable = bool(value.get("evaluated_days_observable")); JsonNode days = value.get("evaluated_days");
        require(observable == !days.isNull(), "truce evaluated duration gate malformed"); if (!days.isNull()) nonnegative32(days);
        require(!bool(value.get("actual_expiry_observable")) && value.get("expiry_date_raw").isNull(), "truce invented persisted expiry");
        return value.deepCopy();
    }
    private static void characterFixed(JsonNode value) {
        ObjectNode row = exact(value, Set.of("character_id", "value"), "character fixed point"); positive32(row.get("character_id")); fixed(row.get("value"));
    }
    private static void fixed(JsonNode value) {
        ObjectNode row = exact(value, Set.of("raw", "scale"), "fixed point");
        number(row.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE); number(row.get("scale"), 100_000, 100_000);
    }
    private static void disposition(JsonNode raw, String title, String claim) {
        ObjectNode row = exact(raw, Set.of("declared_title_disposition", "claim_disposition"), "outcome disposition");
        require(text(row.get("declared_title_disposition")).equals(title) && text(row.get("claim_disposition")).equals(claim),
                "outcome disposition drifted");
    }
    private static void readiness(JsonNode raw, Set<String> trueFields, Set<String> falseFields) {
        Set<String> all = new HashSet<>(trueFields); all.addAll(falseFields); ObjectNode row = exact(raw, all, "readiness");
        for (String field : trueFields) require(bool(row.get(field)), "readiness differs");
        for (String field : falseFields) require(!bool(row.get(field)), "readiness differs");
    }
    private static ObjectNode provenance(JsonNode raw, String slice) {
        ObjectNode row = object(raw, "terms provenance");
        String version = text(row.get("game_version")); String hash = text(row.get("executable_sha256"));
        String executable = switch (version) {
            case "1.19.0.6" -> "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
            case "1.20.0.2" -> "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
            case "1.20.0.3" -> "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
            case "1.20.0.4" -> "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
            default -> throw new IllegalArgumentException("native terms provenance build unsupported");
        };
        require(hash.equals(executable), "native terms provenance exact build differs");
        ObjectNode expected = StrictJson.object(); expected.put("game_version", version); expected.put("executable_sha256", executable);
        expected.put("native_reader", "CWar+0x270/+0x290;" + (version.equals("1.20.0.4") ? "0x2B9ECB0"
                : version.equals("1.19.0.6") ? "0x28B1AA0" : "0x2B9ECD0"));
        expected.put("present_claim_lifecycle", "present_only_vtable_slot_0_delete_flags_0");
        if (slice.equals(CLAIM)) expected.put("claim_script_sha256", version.equals("1.19.0.6")
                ? "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
                : "887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4");
        else {
            require(slice.equals(RAIKTOR) && version.equals("1.19.0.6"), "native event-war terms are not closed for this build");
            expected.put("event_war_script_sha256", "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707");
            expected.put("casus_belli_effects_script_sha256", "9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C");
            expected.put("war_effects_script_sha256", "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D");
            expected.put("war_interactions_script_sha256", "5C99B8F14893929A9BC2DBB5B258CDD2D4233D5805091952209413DE876EE09F");
            expected.put("bookmark_events_script_sha256", "75CF485E379E522D4AAED9EF889FCC411A0D9DFCC28BCFB250ABDCC93A757EFF");
            expected.put("truce_observer", "ck3-1.19.0.6-native-raiktor-surrender-truce-v1");
        }
        equal(row, expected, "native terms provenance is malformed"); return expected;
    }
    static ObjectNode object(JsonNode value, String name) {
        require(value instanceof ObjectNode, name + " must be an object"); return (ObjectNode) value;
    }
    static ObjectNode exact(JsonNode value, Set<String> fields, String name) {
        ObjectNode row = object(value, name); Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields), name + " schema differs"); return row;
    }
    static ArrayNode array(JsonNode value) { require(value instanceof ArrayNode, "array required"); return (ArrayNode) value; }
    static String text(JsonNode value) { return StrictJson.text(value); }
    static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "strict boolean required"); return value.booleanValue(); }
    static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "strict integer required"); return value.bigIntegerValue(); }
    static long number(JsonNode value, long low, long high) { return StrictJson.integer(value, low, high); }
    static int signed32(JsonNode value) { return Math.toIntExact(number(value, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    static int positive32(JsonNode value) { return Math.toIntExact(number(value, 1, Integer.MAX_VALUE)); }
    static int nonnegative32(JsonNode value) { return Math.toIntExact(number(value, 0, Integer.MAX_VALUE)); }
    static int fullId(JsonNode value) { int id = signed32(value); require(id != -1, "invalid full-generation ID"); return id; }
    static BigInteger positiveU64(JsonNode value) { return positiveU64(integer(value)); }
    static BigInteger positiveU64(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 required"); return value;
    }
    static List<Integer> ids(JsonNode value) {
        List<Integer> result = new ArrayList<>(); Set<Integer> seen = new HashSet<>();
        for (JsonNode item : array(value)) { int id = positive32(item); require(seen.add(id), "duplicate ID"); result.add(id); }
        return List.copyOf(result);
    }
    private static void nulls(ObjectNode row, List<String> fields) {
        for (String field : fields) require(row.get(field).isNull(), "unavailable domain invented dynamic values");
    }
    private static void equal(JsonNode left, JsonNode right, String message) {
        require(StrictJson.canonical(left, StrictJson.EXPLICIT_MAX_BYTES).length <= StrictJson.EXPLICIT_MAX_BYTES, "bounded value required");
        require(java.util.Arrays.equals(StrictJson.canonical(left, StrictJson.EXPLICIT_MAX_BYTES),
                StrictJson.canonical(right, StrictJson.EXPLICIT_MAX_BYTES)), message);
    }
}
