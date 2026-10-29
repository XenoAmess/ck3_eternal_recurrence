package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit complete query branches used by the actual partial FULL. Unknown actions remain rejected. */
public final class SettledQueryClassifier {
    public static final String CONTRACT = "xar.closed-partial-settled-query-classifier/v1";
    private SettledQueryClassifier() { }
    public static ObjectNode classify(ObjectNode body, SavedFrame frame) {
        equal(body, "status", "executed"); ObjectNode result = object(body.get("result"));
        String step = text(body, "selected_step");
        ObjectNode observation = base(step, text(result, "status"));
        if (step.equals("query-war-results-window-v1")) { return warResults(body, result, frame); }
        if (step.equals("query-campaign-root-context-v1")) { return existingFocus(body, result, frame, observation); }
        StrictJson.trueValue(result.get("accepted"));
        if (step.equals("query-observed-first-heir-marriage-result-v1-private")) {
            equal(result, "schema", "xar.ck3.observed-first-heir-marriage-private-action.v1");
            StrictJson.integer(result.get("schema_version"), 1, 1); equal(result, "step", step);
            StrictJson.trueValue(result.get("private_build")); falseValue(result.get("advertised"));
            StrictJson.trueValue(result.get("cold_recovery"));
            String status = text(result, "status"); StrictJson.require(Set.of("marriage", "betrothal", "pending").contains(status), "formal relation readback");
            booleanValue(result.get("material_result"), !status.equals("pending"));
            StrictJson.integer(result.get("pre_native_revision"), 0, 0);
            StrictJson.integer(result.get("post_native_revision"), frame.nativeRevision(), frame.nativeRevision());
            uint32(result.get("heir_character_id")); uint32(result.get("candidate_character_id"));
        } else if (step.equals("query-army-strengths-v1")) {
            equal(result, "status", "available"); JsonNode armies = result.get("armies");
            StrictJson.require(armies != null && armies.isArray() && !armies.isEmpty(), "actual army observations");
            for (JsonNode army : armies) { uint32(object(army).get("army_id")); }
        } else {
            equal(result, "step", step); equal(result, "backend_id", "native-headless");
            StrictJson.integer(result.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
            if (step.equals("query-player-mercenary-context-v1")) {
                equal(result, "status", "completed"); StrictJson.trueValue(result.get("read_only"));
                StrictJson.integer(result.get("snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
                StrictJson.integer(result.get("date_raw"), frame.dateRaw(), frame.dateRaw());
                StrictJson.require(!object(result.get("player_mercenary_context")).isEmpty(), "mercenary read, no hire");
            } else if (step.matches("query-war-termination-options-[1-9][0-9]*")) {
                long war = decimal(step.substring(step.lastIndexOf('-') + 1), false); equal(result, "status", "available");
                StrictJson.integer(object(result.get("war_termination_options")).get("war_id"), war, war);
            } else if (step.matches("query-route-contact-horizon-v1-(0|[1-9][0-9]*)-to-[1-9][0-9]*-h-[1-9][0-9]*(?:-[1-9][0-9]*)+")) {
                routeIds(step); equal(result, "status", "available");
                StrictJson.integer(result.get("snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
                StrictJson.require(!object(result.get("route_contact_horizon")).isEmpty(), "typed route read, no movement");
            } else { throw new org.xar.ck3.control.contracts.ContractViolationException("unmigrated/unsupported settled read operation"); }
        }
        observation.put("category", "primitive_accepted"); observation.put("primitive_accepted", true); return observation;
    }
    private static void routeIds(String step) {
        String tail = step.substring("query-route-contact-horizon-v1-".length());
        String[] halves = tail.split("-to-", -1); long actorArmy = decimal(halves[0], true);
        StrictJson.require(actorArmy <= Integer.MAX_VALUE, "route moving CUnit width");
        String[] second = halves[1].split("-h-", -1);
        StrictJson.require(decimal(second[0], false) <= Integer.MAX_VALUE, "route target province width");
        String[] targets = second[1].split("-", -1); long count = decimal(targets[0], false);
        StrictJson.require(count <= 64 && targets.length == count + 1, "original bounded hostile count");
        Set<Long> unique = new java.util.HashSet<>();
        long previous = -1;
        for (int i = 1; i < targets.length; i++) {
            long id = decimal(targets[i], false);
            StrictJson.require(id <= Integer.MAX_VALUE && unique.add(id) && id > previous && id != actorArmy,
                    "sorted unique hostile CUnit ids exclude the moving army"); previous = id;
        }
    }
    private static long decimal(String value, boolean zero) {
        BigInteger parsed = new BigInteger(value);
        StrictJson.require(parsed.compareTo(zero ? BigInteger.ZERO : BigInteger.ONE) >= 0
                && parsed.compareTo(BigInteger.valueOf(4_294_967_295L)) <= 0, "native route integer domain");
        return parsed.longValueExact();
    }
    private static ObjectNode existingFocus(ObjectNode body, ObjectNode result, SavedFrame frame, ObjectNode observation) {
        ObjectNode plan = object(body.get("plan")), existing = object(plan.get("initial_lifestyle_focus_existing"));
        equal(plan, "selected_step", "query-campaign-root-context-v1"); equal(existing, "status", "verified_existing");
        ObjectNode gate = object(body.get("initial_lifestyle_focus_gate")), source = object(existing.get("source_frame"));
        StrictJson.integer(source.get("revision"), 1, StrictJson.MAX_SAFE_INTEGER);
        long revision = number(source, "native_revision", 1); equal(source, "snapshot_id", "native:" + revision);
        StrictJson.integer(source.get("player_character_id"), frame.actorCharacterId(), frame.actorCharacterId());
        StrictJson.integer(source.get("date_raw"), frame.dateRaw(), frame.dateRaw()); equal(gate, "episode_run_id", frame.episodeRunId());
        StrictJson.trueValue(result.get("accepted")); equal(result, "step", "query-campaign-root-context-v1");
        for (String key : Set.of("snapshot_id", "revision", "native_revision")) {
            StrictJson.require(java.util.Objects.equals(result.get("queried_" + key), source.get(key)), "independent focus root source frame");
        }
        StrictJson.integer(result.get("date_raw"), frame.dateRaw(), frame.dateRaw());
        StrictJson.integer(result.get("player_character_id"), frame.actorCharacterId(), frame.actorCharacterId());
        ObjectNode focus = object(existing.get("current_focus")), progress = object(existing.get("current_lifestyle_progress"));
        equal(focus, "presence", "present"); String focusKey = text(focus, "key"), lifestyle = text(focus, "lifestyle_key");
        equal(progress, "presence", "present"); equal(progress, "lifestyle_key", lifestyle);
        for (String key : Set.of("xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points")) {
            number(progress, key, key.equals("xp_per_level") ? 1 : 0);
        }
        String readback = text(existing, "readback_source");
        StrictJson.require(readback.equals("native_current_state_only") || (readback.equals("native_formal_and_stock")
                && existing.get("stock_focus_native_legal") != null && existing.get("stock_focus_native_legal").isBoolean()), "independent existing focus readback");
        equal(gate, "stage", "complete"); equal(gate, "existing_focus", focusKey);
        StrictJson.integer(gate.get("date_raw"), frame.dateRaw(), frame.dateRaw());
        observation.put("category", "lifestyle_existing_focus_verified"); observation.put("existing_focus_verified", true);
        observation.put("target_key", focusKey); observation.put("episode_run_id", frame.episodeRunId()); return observation;
    }
    private static ObjectNode warResults(ObjectNode body, ObjectNode result, SavedFrame frame) {
        ObjectNode plan = object(body.get("plan")); equal(plan, "policy", "ordinary-war-results-window-v1");
        equal(plan, "selected_step", "query-war-results-window-v1"); equal(result, "schema", "ck3-war-results-window-v1");
        equal(result, "sdk_validation_schema", "war-results-window-source-v1"); equal(result, "backend_id", "native-headless");
        equal(result, "step", "query-war-results-window-v1"); equal(result, "operation", "query"); equal(result, "window_name", "war_results");
        for (String flag : Set.of("root_observed", "post_observed", "scope_unchanged", "application_owner_thread_verified", "available", "accepted")) {
            StrictJson.trueValue(result.get(flag));
        }
        StrictJson.integer(result.get("played_character_id"), frame.actorCharacterId(), frame.actorCharacterId());
        StrictJson.integer(result.get("queried_actor_character_id"), frame.actorCharacterId(), frame.actorCharacterId());
        equal(result, "queried_episode_run_id", frame.episodeRunId());
        StrictJson.require(java.util.Objects.equals(result.get("queried_date_raw"), result.get("date_raw")), "war results query date binding");
        equal(result, "native_request_id", text(result, "request_id"));
        ObjectNode owner = object(object(result.get("native_command_result")).get("war_results_window_owner_receipt"));
        equal(owner, "request_id", text(result, "request_id"));
        for (String key : Set.of("ticket_sequence", "pump_epoch", "thread_id", "date_raw", "connection_generation")) {
            number(owner, key, 1); StrictJson.require(owner.get(key).equals(result.get(key)), "independent native owner result");
        }
        StrictJson.require(owner.get("ticket_sequence").equals(owner.get("executor_started_sequence"))
                && owner.get("ticket_sequence").equals(owner.get("completed_sequence")), "actual owner completion, not submission ACK");
        String status = text(result, "status"); StrictJson.require(Set.of("absent", "hidden", "visible").contains(status), "actual window query state");
        if (status.equals("visible")) { StrictJson.trueValue(result.get("post_effective_visible")); }
        ObjectNode observation = base("query-war-results-window-v1", status); observation.put("category", "war_results_window_observed");
        observation.put("war_results_window_closed_verified", false); observation.put("source_native_request_id", text(result, "native_request_id"));
        observation.set("source_native_owner_receipt", owner.deepCopy()); observation.put("typed_nonmaterial_observation", true);
        for (String flag : Set.of("existing_typed_material_verified", "council_material_verified", "construction_material_verified",
                "construction_start_verified", "construction_completion_verified", "crown_material_verified", "crown_receipt_nonmaterial", "date_advance_observed")) {
            observation.put(flag, false);
        }
        return observation;
    }
    private static ObjectNode base(String step, String status) {
        ObjectNode row = StrictJson.object(); row.put("schema", "g2.queue.ordinary-result-credit/v1"); row.put("selected_step", step);
        row.put("service_status", "executed"); row.put("result_status", status);
        for (String flag : Set.of("submitted_pending", "lifestyle_material_verified", "existing_focus_verified", "primitive_accepted",
                "business_success_inferred", "replay_allowed")) { row.put(flag, false); }
        return row;
    }
    static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "required object; absent/null are distinct"); return (ObjectNode) value;
    }
    static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    static long number(ObjectNode row, String field, long min) { return StrictJson.integer(row.get(field), min, StrictJson.MAX_SAFE_INTEGER); }
    static void equal(ObjectNode row, String field, String expected) { StrictJson.require(text(row, field).equals(expected), "exact " + field); }
    static void falseValue(JsonNode node) { booleanValue(node, false); }
    static void booleanValue(JsonNode node, boolean expected) {
        StrictJson.require(node != null && node.isBoolean() && node.booleanValue() == expected, "exact boolean field");
    }
    private static void uint32(JsonNode node) { StrictJson.integer(node, 1, 4_294_967_295L); }
}
