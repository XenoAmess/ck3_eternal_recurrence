package org.xar.ck3.control.wave3.planning.military;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngressCodec;
import org.xar.ck3.control.wave3.military.routereroute.RoutePreviewConsumerCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.*;
import org.xar.ck3.control.wave3.planning.military.OrdinaryMilitaryConsumer.*;

/** Closed receipt format. Reading a saved receipt never installs a frame provider or reservation owner. */
public final class OrdinaryMilitaryResultCodec {
    public static final String SCHEMA = "xar.ordinary-military-contact-result/v1";
    private static final int MAX = 1_048_576;
    private OrdinaryMilitaryResultCodec() { }
    public static byte[] encode(Result result) {
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA); root.put("action_authorized", false);
        root.put("authorizes_command_replay", false); root.put("actual_arrival_observed", false);
        var rejected = root.putArray("route_rejections");
        for (Rejected value : result.routeRejections()) {
            var row = rejected.addObject(); row.put("objective_rank", value.objectiveRank()); row.put("reason", value.reason().name()); row.set("audit", audit(value.audit()));
        }
        var pre = root.putArray("preview_rejections");
        for (RouteReevaluationPlanner.Rejection value : result.previewRejections()) {
            var row = pre.addObject(); row.put("target_province_id", value.targetProvinceId()); row.put("reason", value.reason().name());
        }
        if (result instanceof Unavailable value) { root.put("kind", "UNAVAILABLE"); root.put("gap", value.gap().name()); }
        else if (result instanceof RouteBoundary value) {
            root.put("kind", "ROUTE_BOUNDARY"); root.put("original_rank_offset", value.originalRankOffset()); root.set("boundary", StrictJson.parse(RouteReevaluationCodec.encodeResult(value.boundary()), MAX));
        } else if (result instanceof ReadRequired value) {
            root.put("kind", "READ_REQUIRED"); root.put("read_kind", value.kind().name()); root.put("required_step", value.requiredStep()); root.put("step_advertised", value.stepAdvertised());
            root.put("objective_rank", value.objectiveRank()); preview(root, value.preview()); root.set("audit", audit(value.audit()));
        } else {
            PlanningContinuation value = (PlanningContinuation) result; root.put("kind", "PLANNING_CONTINUATION"); root.put("objective_rank", value.objectiveRank()); root.put("candidate_source", value.source().name());
            preview(root, value.preview()); root.set("audit", audit(value.audit())); root.set("endpoint_contact", StrictJson.parse(IndexedContactIngressCodec.encodeDecision(value.endpointContact())));
        }
        return RoutePreviewConsumerCodec.encodeEnvelope(root);
    }
    public static Result decode(byte[] raw) {
        JsonNode root = StrictJson.parse(raw, MAX); String kind = StrictJson.text(root.get("kind"));
        List<Rejected> rejected = new ArrayList<>();
        for (JsonNode row : array(root.get("route_rejections"))) {
            object(row, "objective_rank", "reason", "audit");
            rejected.add(new Rejected(integer(row.get("objective_rank"), 0), audit(row.get("audit")), token(RejectedReason.class, row.get("reason"))));
        }
        List<RouteReevaluationPlanner.Rejection> previewRejected = new ArrayList<>();
        for (JsonNode row : array(root.get("preview_rejections"))) {
            object(row, "target_province_id", "reason"); previewRejected.add(new RouteReevaluationPlanner.Rejection(integer(row.get("target_province_id"), 1), token(RouteReevaluationPlanner.RejectionReason.class, row.get("reason"))));
        }
        Result result = switch (kind) {
            case "UNAVAILABLE" -> new Unavailable(token(Gap.class, root.get("gap")), rejected, previewRejected);
            case "ROUTE_BOUNDARY" -> new RouteBoundary(RouteReevaluationCodec.decodeResult(RoutePreviewConsumerCodec.encodeEnvelope(root.get("boundary"))), integer(root.get("original_rank_offset"), 0), rejected, previewRejected);
            case "READ_REQUIRED" -> new ReadRequired(token(ReadKind.class, root.get("read_kind")), StrictJson.text(root.get("required_step")), bool(root.get("step_advertised")), integer(root.get("objective_rank"), 0), preview(root), audit(root.get("audit")), rejected, previewRejected);
            case "PLANNING_CONTINUATION" -> new PlanningContinuation(integer(root.get("objective_rank"), 0), token(RouteReevaluationPlanner.CandidateSource.class, root.get("candidate_source")), preview(root), audit(root.get("audit")), IndexedContactIngressCodec.decodeDecision(StrictJson.canonical(root.get("endpoint_contact"))), rejected, previewRejected);
            default -> throw new IllegalArgumentException("unsupported ordinary military result kind");
        };
        // Exact JSON-domain comparison rejects unknown, missing, wrong-type and forged authority fields.
        StrictJson.require(root.equals(StrictJson.parse(encode(result), MAX)), "ordinary military receipt fields/types disagree");
        return result;
    }
    private static ObjectNode audit(Audit audit) {
        var row = StrictJson.object(); row.put("status", audit.status().name()); row.put("target_province_id", audit.targetProvinceId()); row.put("horizon_decision", audit.horizonDecision().name());
        var route = row.putArray("route_province_ids"); audit.routeProvinceIds().forEach(route::add); var conflicts = row.putArray("conflicts");
        for (Conflict conflict : audit.conflicts()) {
            var item = conflicts.addObject(); item.put("kind", conflict.kind().name());
            if (conflict.enemyArmyId() == null) item.putNull("enemy_army_id"); else item.put("enemy_army_id", conflict.enemyArmyId());
            item.put("province_id", conflict.provinceId()); optional(item, "to_province_id", conflict.toProvinceId()); optional(item, "player_hop", conflict.playerHop()); optional(item, "enemy_hop", conflict.enemyHop());
        }
        return row;
    }
    private static Audit audit(JsonNode row) {
        object(row, "status", "target_province_id", "horizon_decision", "route_province_ids", "conflicts");
        List<Integer> route = new ArrayList<>(); for (JsonNode value : array(row.get("route_province_ids"))) route.add(integer(value, 1));
        List<Conflict> conflicts = new ArrayList<>();
        for (JsonNode item : array(row.get("conflicts"))) {
            object(item, "kind", "enemy_army_id", "province_id", "to_province_id", "player_hop", "enemy_hop");
            conflicts.add(new Conflict(token(ConflictKind.class, item.get("kind")), item.get("enemy_army_id").isNull() ? null : integer(item.get("enemy_army_id"), 0), integer(item.get("province_id"), 1), optional(item.get("to_province_id")), optional(item.get("player_hop")), optional(item.get("enemy_hop"))));
        }
        return new Audit(token(Status.class, row.get("status")), integer(row.get("target_province_id"), 1), route, conflicts, token(HorizonDecision.class, row.get("horizon_decision")));
    }
    private static void preview(ObjectNode root, RouteReroutePolicy.Preview preview) { root.set("preview", StrictJson.parse(RoutePreviewConsumerCodec.encode(Optional.of(preview)), MAX)); }
    private static RouteReroutePolicy.Preview preview(JsonNode root) { return RoutePreviewConsumerCodec.decodePreview(RoutePreviewConsumerCodec.encodeEnvelope(root.get("preview"))); }
    private static void optional(ObjectNode row, String key, Optional<Integer> value) { if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key); }
    private static Optional<Integer> optional(JsonNode value) { StrictJson.require(value != null, "required nullable field missing"); return value.isNull() ? Optional.empty() : Optional.of(integer(value, 1)); }
    private static ObjectNode object(JsonNode row, String... fields) { return StrictJson.object(row, Set.of(fields)); }
    private static JsonNode array(JsonNode value) { StrictJson.require(value != null && value.isArray(), "array required"); return value; }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "boolean required"); return value.booleanValue(); }
    private static int integer(JsonNode value, int minimum) { return (int) StrictJson.integer(value, minimum, Integer.MAX_VALUE); }
    private static <E extends Enum<E>> E token(Class<E> type, JsonNode value) { return Enum.valueOf(type, StrictJson.text(value)); }
}
