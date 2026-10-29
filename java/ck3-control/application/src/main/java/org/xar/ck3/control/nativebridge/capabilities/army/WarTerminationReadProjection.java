package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Comparator;
import java.util.List;
import org.xar.ck3.control.g2.m0.RaiktorSurrenderAggregateProducer;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original readonly query producer projections after the sole packet codecs and actual outer receipt guard. No additional native query or action authority. */
public final class WarTerminationReadProjection {
    private WarTerminationReadProjection() { }
    public static ObjectNode options(Context context, Obj actualSnapshot, NativeTerminationOptions.NativePacket packet,
            UInt64 sequence, ObjectNode originalResult) {
        ObjectNode snapshot = snapshot(context, actualSnapshot); positiveSequence(sequence);
        List<NativeActiveWarsCodec.War> wars = NativeActiveWarsCodec.normalize(get(snapshot, "active_wars"));
        ObjectNode selected = selected(wars, packet.warId()), options = packet.normalized();
        for (String field : List.of("war_id", "player_side", "player_is_primary_war_leader", "player_relative_war_score"))
            require(java.util.Arrays.equals(org.xar.ck3.control.contracts.StrictJson.canonical(get(options, field)),
                    org.xar.ck3.control.contracts.StrictJson.canonical(get(selected, field))), "termination query differs from actual active war: " + field);
        ObjectNode result = originalResult.deepCopy(); equal(get(result, "status"), "available");
        result.set("war_termination_options", options); result.put("query_sequence", sequence.value()); bindings(result, snapshot, true);
        ObjectNode query = empty().put("schema_version", 1); query.set("queried_date_raw", get(snapshot, "date_raw"));
        query.set("queried_connection_generation", get(object(get(snapshot, "diagnostics")), "connection_generation"));
        query.set("queried_episode_run_id", get(snapshot, "episode_run_id"));
        query.set("queried_character_id", get(object(get(snapshot, "played_character")), "character_id"));
        query.set("active_war_signature", activeWarSignature(wars)); query.set("negative_decision_signature", negativeSignature(packet));
        query.set("queried_war_duration_days", get(options, "war_duration_days")); result.set("termination_query_context", query); return result;
    }
    public static ObjectNode terms(Context context, Obj actualSnapshot, ObjectNode terms, UInt64 sequence, ObjectNode originalResult) {
        ObjectNode snapshot = snapshot(context, actualSnapshot); positiveSequence(sequence);
        selected(NativeActiveWarsCodec.normalize(get(snapshot, "active_wars")), i32(get(terms, "war_id")));
        ObjectNode result = originalResult.deepCopy(); equal(get(result, "status"), text(get(terms, "status")));
        ObjectNode provenance = object(get(terms, "provenance")), hello = object(get(object(get(snapshot, "diagnostics")), "hello"));
        equal(get(provenance, "game_version"), text(get(hello, "expected_ck3_version")));
        require(text(get(provenance, "executable_sha256")).equalsIgnoreCase(text(get(hello, "expected_ck3_sha256"))), "terms belong to another exact native build");
        result.set("war_termination_terms", terms); result.put("query_sequence", sequence.value()); bindings(result, snapshot, false);
        // The original projection emits an unavailable session when dynamic terms are absent. No passive truce or source-specific loss is invented.
        return RaiktorSurrenderAggregateProducer.attachSession(snapshot, result, null);
    }
    /** Stable six-field signature consumes the already complete shared War model; daily armies, duration and tactical state are excluded by the original contract. */
    public static ArrayNode activeWarSignature(List<NativeActiveWarsCodec.War> wars) {
        ArrayNode result = empty().arrayNode();
        for (var war : List.copyOf(wars).stream().sorted(Comparator.comparing(NativeActiveWarsCodec.War::warId)).toList()) {
            require(war.warId().signum() > 0, "negative-query signature requires positive active WarIDs");
            ObjectNode row = NativeActiveWarsCodec.encodeWar(war), projected = empty();
            for (String field : List.of("war_id", "player_side", "player_is_primary_war_leader", "primary_opponent_character_id", "player_relative_war_score", "targeted_title_ids")) projected.set(field, get(row, field));
            result.add(projected);
        }
        return result;
    }
    public static ObjectNode negativeSignature(NativeTerminationOptions.NativePacket packet) {
        ObjectNode options = packet.normalized(), result = empty();
        for (String field : List.of("war_id", "player_side", "player_is_primary_war_leader", "player_relative_war_score", "absolute_war_scores_observable", "attacker_war_score", "defender_war_score", "war_score_breakdown", "active_casus_belli_present", "active_casus_belli_identity", "cb_allows_white_peace")) result.set(field, get(options, field));
        ObjectNode signature = empty(), rows = object(get(options, "options"));
        for (String name : List.of("surrender", "white_peace", "victory")) {
            ObjectNode option = object(get(rows, name)), projected = empty();
            for (String field : List.of("outcome", "hostage_variant", "context_constructed", "native_validator_passed", "available")) projected.set(field, get(option, field));
            ObjectNode response = object(get(option, "recipient_response")), selected = empty();
            for (String field : List.of("status", "decision_status_raw", "would_accept_now")) selected.set(field, get(response, field));
            projected.set("recipient_response", selected);
            NativeInteractionRoles.putOption(projected, NativeInteractionRoles.fromOption(option));
            signature.set(name, projected);
        }
        result.set("options", signature); return result;
    }
    private static ObjectNode snapshot(Context context, Obj actual) {
        ObjectNode snapshot = object(OpportunityJson.toNode(actual));
        equal(get(snapshot, "snapshot_id"), context.before().frame().snapshotId()); equal(get(snapshot, "revision"), context.before().frame().revision());
        equal(get(snapshot, "native_revision"), context.nativeRevision()); equal(get(snapshot, "date_raw"), context.dateRaw());
        equal(get(snapshot, "episode_run_id"), context.before().frame().episodeRunId());
        equal(get(object(get(snapshot, "played_character")), "character_id"), context.playerId()); yes(get(snapshot, "paused")); return snapshot;
    }
    private static ObjectNode selected(List<NativeActiveWarsCodec.War> wars, int id) {
        var rows = wars.stream().filter(war -> war.warId().equals(BigInteger.valueOf(id))).toList();
        require(rows.size() == 1, "termination query requires exactly one actual active WarID"); return NativeActiveWarsCodec.encodeWar(rows.getFirst());
    }
    private static void positiveSequence(UInt64 sequence) { require(sequence != null && sequence.value().signum() > 0, "actual positive termination query sequence required"); }
    private static void bindings(ObjectNode result, ObjectNode snapshot, boolean options) {
        if (!result.has("backend_id")) result.put("backend_id", "native-headless");
        for (String field : List.of("snapshot_id", "revision", "native_revision")) result.set("queried_" + field, get(snapshot, field));
        result.set("queried_connection_generation", get(object(get(snapshot, "diagnostics")), "connection_generation"));
        result.set(options ? "queried_episode_run_id" : "episode_run_id", get(snapshot, "episode_run_id"));
    }
}
