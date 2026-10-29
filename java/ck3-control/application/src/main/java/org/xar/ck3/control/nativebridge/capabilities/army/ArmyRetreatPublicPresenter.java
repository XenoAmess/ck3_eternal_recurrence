package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original public order ACK. Independent lifecycle success stays in the original private action/domain, never in ACK credit. */
public final class ArmyRetreatPublicPresenter {
    /** Historical schema discriminator, not a runtime/implementation provenance statement. */
    public static final String PUBLIC_CONTRACT_STAGE = "python_production_composition";
    private ArmyRetreatPublicPresenter() { }
    public static Obj preview(Obj originalJavaPreview) {
        ObjectNode result = object(OpportunityJson.toNode(originalJavaPreview)).deepCopy();
        equal(get(result, "contract_stage"), ArmyRetreatTokens.STAGE); result.put("contract_stage", PUBLIC_CONTRACT_STAGE);
        return DriverJson.object(bytes(result), DriverJson.MAX_NATIVE_BYTES);
    }
    public static Obj order(ActiveRetreatProposal.Order original, OperationKey originalOperation, Obj actualNativeSubmission,
            Optional<ArmyPublicSnapshot> actualAfter) {
        ObjectNode submission = object(OpportunityJson.toNode(actualNativeSubmission)); boolean accepted = bool(get(submission, "accepted"));
        if (accepted) require(text(get(submission, "status")).equals("submitted")
                && text(get(submission, "step")).equals("move-army-" + original.arguments().selectedPublicCunitId() + "-to-" + original.arguments().targetProvinceId()), "public retreat requires its actual submitted Native ACK for the same subject/target");
        else require(text(get(submission, "status")).equals("rejected") && !text(get(submission, "rejection_reason")).isEmpty(), "public retreat rejection must be definitive");
        var request = original.arguments(); ObjectNode result = empty().put("schema_version", 1).put("contract_stage", PUBLIC_CONTRACT_STAGE).put("step", originalOperation.value())
                .put("accepted", accepted).put("status", accepted ? "accepted_verification_pending" : "rejected").put("verification_pending", accepted).put("token_consumed", true)
                .put("selected_public_cunit_id", request.selectedPublicCunitId()).put("expected_snapshot_revision", request.expectedRevision())
                .put("expected_combat_id", request.expectedCombatId()).put("expected_side_index", request.expectedSideIndex()).put("expected_scope", request.expectedScope().wire())
                .put("target_province_id", request.targetProvinceId()).put("backend_id", "native-headless");
        if (accepted) result.putNull("rejection_reason"); else result.set("rejection_reason", get(submission, "rejection_reason").deepCopy());
        ArrayNode affected = result.putArray("affected_public_cunit_ids_in_stored_order"); original.affectedInStoredOrder().forEach(affected::add);
        ArrayNode unaffected = result.putArray("unaffected_same_side_public_cunit_ids_in_stored_order"); original.unaffectedInStoredOrder().forEach(unaffected::add);
        if (accepted) result.set("underlying_move_result", submission.deepCopy()); else result.putNull("underlying_move_result");
        result.set("semantic_postcondition", accepted ? actualAfter.map(frame -> semantic(original, frame)).orElseGet(() -> emptyPost("observation_pending")) : emptyPost("not_observed"));
        return DriverJson.object(bytes(result), DriverJson.MAX_NATIVE_BYTES);
    }
    private static ObjectNode semantic(ActiveRetreatProposal.Order order, ArmyPublicSnapshot actual) {
        ObjectNode snapshot = object(OpportunityJson.toNode(actual.semantic()));
        // A complete original paused episode binding is mandatory; an absent binding produces no partial claims.
        try {
            var current = ActiveRetreatProposal.SourceFrame.read(actual.semantic());
            if (!current.episodeRunId().equals(order.source().episodeRunId())) return emptyPost("observation_pending");
        } catch (IllegalArgumentException unavailable) { return emptyPost("observation_pending"); }
        ObjectNode post = emptyPost("observed_partial"); post.set("observation_snapshot_id", get(snapshot, "snapshot_id").deepCopy()); post.set("observation_revision", get(snapshot, "revision").deepCopy());
        post.set("observation_native_revision", get(snapshot, "native_revision").deepCopy()); post.set("observation_date_raw", get(snapshot, "date_raw").deepCopy());
        ArrayNode observations = post.putArray("affected_armies_in_stored_order"); boolean retreating = !order.affectedInStoredOrder().isEmpty(), target = retreating, route = retreating;
        JsonNode armies = snapshot.get("player_armies");
        for (int id : order.affectedInStoredOrder()) {
            ObjectNode army = null;
            if (armies != null && armies.isArray()) for (JsonNode candidate : armies) if (candidate.isObject() && candidate.path("army_id").isIntegralNumber() && candidate.path("army_id").bigIntegerValue().equals(java.math.BigInteger.valueOf(id))) { army = (ObjectNode) candidate; break; }
            ObjectNode row = empty().put("public_cunit_id", id).put("present", army != null);
            Boolean retreated = null, matched = null, reached = null; JsonNode destination = null; ArrayNode remaining = null;
            if (army != null) {
                boolean observable = false; for (String field : List.of("retreating", "in_combat", "army_state", "army_state_code")) observable |= army.has(field);
                if (observable) retreated = army.path("retreating").isBoolean() && army.path("retreating").booleanValue()
                        || army.path("army_state").isTextual() && army.path("army_state").textValue().equalsIgnoreCase("retreating")
                        || army.path("army_state_code").isIntegralNumber() && army.path("army_state_code").bigIntegerValue().equals(java.math.BigInteger.valueOf(6));
                boolean targetObservable = !army.path("move_target_observable").isBoolean() || army.path("move_target_observable").booleanValue();
                if (targetObservable) {
                    JsonNode value = army.get("move_target_province_id"); if (value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() > 0) destination = value;
                    matched = destination != null && destination.bigIntegerValue().equals(java.math.BigInteger.valueOf(order.arguments().targetProvinceId()));
                }
                JsonNode storedRoute = army.get("route_province_ids");
                if (storedRoute != null && storedRoute.isArray()) {
                    remaining = empty().arrayNode(); boolean valid = true; int ordinal = 0;
                    for (JsonNode province : storedRoute) {
                        if (!province.isIntegralNumber() || province.bigIntegerValue().signum() <= 0) { valid = false; break; }
                        if (ordinal++ == 0 && army.path("current_province_id").isIntegralNumber() && province.bigIntegerValue().equals(army.get("current_province_id").bigIntegerValue())) continue;
                        remaining.add(province.deepCopy());
                    }
                    if (!valid) remaining = null;
                    if (remaining != null) reached = !remaining.isEmpty() && remaining.get(remaining.size() - 1).bigIntegerValue().equals(java.math.BigInteger.valueOf(order.arguments().targetProvinceId()));
                }
            }
            boxed(row, "retreating", retreated); ArmyPublicSnapshot.copyNullable(row, "move_target_province_id", destination); boxed(row, "target_matches", matched);
            ArmyPublicSnapshot.copyNullable(row, "route_province_ids", remaining); boxed(row, "route_reaches_target", reached); observations.add(row);
            retreating &= army != null && Boolean.TRUE.equals(retreated); target &= army != null && Boolean.TRUE.equals(matched); route &= army != null && Boolean.TRUE.equals(reached);
        }
        return post.put("all_affected_retreating_observed", retreating).put("all_affected_target_observed", target).put("all_affected_route_observed", route);
    }
    private static ObjectNode emptyPost(String status) {
        ObjectNode result = empty().put("status", status); for (String field : List.of("observation_snapshot_id", "observation_revision", "observation_native_revision", "observation_date_raw", "all_affected_retreating_observed", "all_affected_target_observed", "all_affected_route_observed")) result.putNull(field);
        result.putArray("affected_armies_in_stored_order"); return result.put("combat_id_post_query_performed", false).put("winner_verified", false).put("phase_verified", false).put("full_postcondition_verified", false);
    }
    private static void boxed(ObjectNode n, String field, Boolean value) { if (value == null) n.putNull(field); else n.put(field, value); }
}
