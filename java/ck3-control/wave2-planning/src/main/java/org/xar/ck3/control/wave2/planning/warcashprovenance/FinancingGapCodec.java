package org.xar.ck3.control.wave2.planning.warcashprovenance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels.*;

/** Strict request envelope with declared projections of extensible existing native containers. */
public final class FinancingGapCodec {
    public static final String REQUEST_SCHEMA = "xar.war-financing-capability-gap.request.v1";
    public static final String CAPABILITY = "game.command.confirm-ingame-decision-outcome-v1";
    private static final BigInteger SCALE = BigInteger.valueOf(100_000);
    private static final Set<String> REQUEST_FIELDS = Set.of("schema", "snapshot", "priority", "root",
            "construction_ledger", "bridge_capabilities");
    private FinancingGapCodec() { }

    public static Input decode(byte[] payload) {
        ObjectNode request = StrictJson.object(StrictJson.parse(payload), REQUEST_FIELDS);
        StrictJson.require(REQUEST_SCHEMA.equals(StrictJson.text(request.get("schema"))), "unknown financing request schema");
        JsonNode snapshot = request.get("snapshot");
        StrictJson.require(snapshot.isObject(), "snapshot object required");
        JsonNode priority = nullableObject(request.get("priority"), "priority");
        JsonNode root = nullableObject(request.get("root"), "root");
        JsonNode ledger = nullableObject(request.get("construction_ledger"), "construction_ledger");
        ObservedFrame frame = frame(snapshot);
        Set<BigInteger> active = new HashSet<>();
        JsonNode activeRows = snapshot.path("active_wars");
        if (activeRows.isArray()) {
            for (JsonNode row : activeRows) { exactInteger(row.path("war_id")).ifPresent(active::add); }
        }
        List<PriorityWar> wars = new ArrayList<>();
        JsonNode rows = priority.path("wars");
        if (rows.isArray()) {
            for (JsonNode row : rows) {
                Optional<BigInteger> identity = exactInteger(row.path("war_id"));
                if (!row.isObject() || identity.isEmpty()) { continue; }
                wars.add(new PriorityWar(identity.orElseThrow(), isTrue(row.get("primary_player_war")),
                        exactInteger(row.path("player_relative_war_score")), isTrue(row.get("raised_force_deficit")),
                        truthy(row.get("observed_primary_opponent_objective_occupation_province_ids")),
                        truthy(row.get("observed_hostile_siege_in_player_subrealm_army_ids")),
                        isTrue(row.get("all_observed_own_raised_armies_currently_retreating"))));
            }
        }
        Optional<BigInteger> treasury = exactInteger(snapshot.path("played_character_gold").path("scale"))
                .filter(SCALE::equals).flatMap(ignored -> exactInteger(snapshot.path("played_character_gold").path("raw")));
        Optional<BigInteger> maintenance = currentMaintenance(snapshot, root);
        Optional<Boolean> advertised = Optional.empty();
        JsonNode caps = request.get("bridge_capabilities");
        if (!caps.isNull()) {
            StrictJson.require(caps.isArray(), "bridge_capabilities must be null or an explicit string collection");
            Set<String> capabilityNames = new HashSet<>();
            for (JsonNode value : caps) {
                StrictJson.require(capabilityNames.add(StrictJson.text(value)), "duplicate capability identity");
            }
            advertised = Optional.of(capabilityNames.contains(CAPABILITY));
        }
        return new Input(frame, active, wars, treasury, maintenance, ledger.path("pending").isObject(), advertised);
    }

    public static byte[] encode(Optional<Gap> result) {
        if (result.isEmpty()) { return "null".getBytes(StandardCharsets.UTF_8); }
        Gap gap = result.orElseThrow();
        ObjectNode node = StrictJson.object();
        node.put("schema", "xar.war-financing-capability-gap.v1");
        node.set("source_frame", frameNode(gap.sourceFrame()));
        node.put("trigger", "cash_shortfall_or_observed_war_crisis");
        gap.crisisWarIds().forEach(node.putArray("crisis_war_ids")::add);
        putInteger(node, "observed_treasury_raw", gap.observedTreasuryRaw());
        putInteger(node, "ordinary_military_buffer_raw", gap.ordinaryMilitaryBufferRaw());
        node.put("maximum_military_maintenance_status", gap.maximumMilitaryMaintenanceStatus().wire());
        node.put("construction_intent_present", gap.constructionIntentPresent());
        node.put("current_active_project_independently_observed", false);
        ObjectNode cancel = node.putObject("cancel_construction");
        cancel.put("status", "native_interface_missing");
        cancel.put("reason", "stock GUI supports cancellation; current .4 adapter has no final CanCancel/refund quote/native receiver");
        cancel.putNull("refund_quote_raw");
        cancel.put("submit_planned", false);
        ObjectNode debt = node.putObject("legal_debt");
        debt.put("status", "current_build_terms_and_received_funds_unqualified");
        debt.put("reason", "generic selected-decision Confirm exists in source; current .4 full loan terms, typed debt and attributable receipt remain unqualified");
        ObjectNode route = debt.putObject("source_reviewed_confirm_route");
        route.put("public_tool", "ck3_confirm_ingame_decision_outcome_v1");
        route.put("capability", CAPABILITY);
        if (gap.confirmCapabilityAdvertised().isPresent()) {
            route.put("advertised_in_supplied_bridge_capabilities", gap.confirmCapabilityAdvertised().orElseThrow());
        } else { route.putNull("advertised_in_supplied_bridge_capabilities"); }
        route.put("decision_key", "borrow_from_holy_order_decision");
        route.put("expected_outcome", "event_window");
        route.put("expected_event_definition_key", "holy_order.0200");
        route.put("current_selected_legal_decision_verified", false);
        route.put("dispatch_or_expected_event_proves_received_funds", false);
        debt.put("current_build_full_terms_verified", false);
        debt.put("typed_debt_readback_verified", false);
        debt.put("independently_attributed_received_funds_verified", false);
        debt.put("source_reviewed_debt_commit_option", "holy_order.0200.a");
        debt.putNull("principal_quote_raw");
        debt.put("submit_planned", false);
        node.put("unreceived_funding_credited_raw", 0);
        node.putNull("selected_action");
        node.put("future_funding_receipts_must_keep_same_procurement_epoch", true);
        node.put("unknown_submission_must_not_be_replayed", true);
        node.put("continue_existing_war_action", true);
        return StrictJson.canonical(node);
    }

    /** Rejects altered eligibility flags and aliases as well as invalid dynamic fields. */
    public static Optional<Gap> decodeResult(byte[] payload) {
        JsonNode node = StrictJson.parse(payload);
        if (node.isNull()) { return Optional.empty(); }
        StrictJson.require(node.isObject(), "financing result must be null or object");
        JsonNode source = node.get("source_frame");
        StrictJson.object(source, Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id"));
        List<BigInteger> crisis = new ArrayList<>();
        JsonNode rows = node.get("crisis_war_ids");
        StrictJson.require(rows != null && rows.isArray(), "crisis_war_ids must be an explicit collection");
        for (JsonNode identity : rows) { crisis.add(requiredInteger(identity, "crisis WarID")); }
        JsonNode advertised = node.path("legal_debt").path("source_reviewed_confirm_route")
                .get("advertised_in_supplied_bridge_capabilities");
        StrictJson.require(advertised != null && (advertised.isNull() || advertised.isBoolean()), "capability advertisement branch");
        JsonNode intent = node.get("construction_intent_present");
        StrictJson.require(intent != null && intent.isBoolean(), "construction intent must be a boolean");
        String status = StrictJson.text(node.get("maximum_military_maintenance_status"));
        MaintenanceStatus maintenance = switch (status) {
            case "same_frame_observed" -> MaintenanceStatus.SAME_FRAME_OBSERVED;
            case "unobserved" -> MaintenanceStatus.UNOBSERVED;
            default -> throw new IllegalArgumentException("unknown maintenance observation status");
        };
        Gap result = new Gap(frame(source), crisis, requiredNullableInteger(node.get("observed_treasury_raw")),
                requiredNullableInteger(node.get("ordinary_military_buffer_raw")), maintenance,
                intent.booleanValue(), advertised.isNull() ? Optional.empty() : Optional.of(advertised.booleanValue()));
        StrictJson.require(node.equals(StrictJson.parse(encode(Optional.of(result)))), "financing result fields or invariant flags changed");
        return Optional.of(result);
    }

    private static ObservedFrame frame(JsonNode snapshot) {
        JsonNode played = snapshot.get("played_character_id");
        if (played == null || played.isNull()) { played = snapshot.path("played_character").path("character_id"); }
        return new ObservedFrame(requiredInteger(played, "played_character_id"),
                requiredInteger(snapshot.get("native_revision"), "native_revision"),
                requiredInteger(snapshot.get("date_raw"), "date_raw"), StrictJson.text(snapshot.get("snapshot_id")),
                requiredInteger(snapshot.get("revision"), "revision"), StrictJson.text(snapshot.get("episode_run_id")));
    }
    private static Optional<BigInteger> currentMaintenance(JsonNode snapshot, JsonNode root) {
        Optional<BigInteger> actor = exactInteger(snapshot.path("played_character").path("character_id"))
                .filter(value -> value.signum() > 0);
        if (actor.isEmpty() || !"available".equals(root.path("status").textValue())
                || !exactInteger(root.path("player_character_id")).equals(actor)
                || !exactInteger(root.path("snapshot_revision")).equals(exactInteger(snapshot.path("native_revision")))
                || !exactInteger(root.path("date_raw")).equals(exactInteger(snapshot.path("date_raw")))) {
            return Optional.empty();
        }
        JsonNode maximum = root.path("player_max_monthly_gold_maintenance_v1");
        if (!"available".equals(maximum.path("status").textValue())
                || !exactInteger(maximum.path("value").path("scale")).filter(SCALE::equals).isPresent()) {
            return Optional.empty();
        }
        return exactInteger(maximum.path("value").path("raw")).filter(value -> value.signum() >= 0);
    }
    private static JsonNode nullableObject(JsonNode value, String name) {
        StrictJson.require(value != null && (value.isNull() || value.isObject()), name + " must be null or object");
        return value;
    }
    private static Optional<BigInteger> exactInteger(JsonNode value) {
        return value != null && value.isIntegralNumber() ? Optional.of(value.bigIntegerValue()) : Optional.empty();
    }
    private static BigInteger requiredInteger(JsonNode value, String name) {
        return exactInteger(value).orElseThrow(() -> new IllegalArgumentException(name + " needs an exact integer token"));
    }
    private static Optional<BigInteger> requiredNullableInteger(JsonNode value) {
        StrictJson.require(value != null, "missing nullable integer field");
        return value.isNull() ? Optional.empty() : Optional.of(requiredInteger(value, "nullable integer"));
    }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    /** Only this legacy diagnostic predicate uses Python truthiness; no number is coerced into cash or an ID. */
    private static boolean truthy(JsonNode value) {
        if (value == null || value.isNull() || value.isMissingNode()) { return false; }
        if (value.isBoolean()) { return value.booleanValue(); }
        if (value.isIntegralNumber()) { return value.bigIntegerValue().signum() != 0; }
        if (value.isFloatingPointNumber()) { return value.decimalValue().signum() != 0; }
        if (value.isTextual()) { return !value.textValue().isEmpty(); }
        return value.size() != 0;
    }
    private static void putInteger(ObjectNode node, String field, Optional<BigInteger> value) {
        if (value.isPresent()) { node.put(field, value.orElseThrow()); }
        else { node.putNull(field); }
    }
    private static ObjectNode frameNode(ObservedFrame frame) {
        ObjectNode node = StrictJson.object();
        node.put("played_character_id", frame.playedCharacterId());
        node.put("native_revision", frame.nativeRevision());
        node.put("date_raw", frame.dateRaw());
        node.put("snapshot_id", frame.snapshotId());
        node.put("revision", frame.revision());
        node.put("episode_run_id", frame.episodeRunId());
        return node;
    }
}
