package org.xar.ck3.control.wave3.military.routereroute;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner.*;

/** Strict JSON entrance and persistence for the ordinary route planner stage. No body field installs a provider. */
public final class RouteReevaluationCodec {
    public static final String REQUEST_SCHEMA = "xar.ordinary-route-reevaluation-request/v1";
    public static final String RESULT_SCHEMA = "xar.ordinary-route-reevaluation-result/v1";
    private RouteReevaluationCodec() { }
    public record Request(byte[] lookupPacket, Context context, List<Objective> orderedObjectives, List<String> availableSteps) {
        public Request {
            lookupPacket = lookupPacket.clone(); RoutePreviewConsumerCodec.decode(lookupPacket);
            java.util.Objects.requireNonNull(context); orderedObjectives = List.copyOf(orderedObjectives);
            availableSteps = List.copyOf(availableSteps); availableSteps.forEach(StrictJson::text);
        }
        @Override public byte[] lookupPacket() { return lookupPacket.clone(); }
    }
    public static Request decodeRequest(byte[] raw) {
        ObjectNode root = object(StrictJson.parse(raw, RoutePreviewConsumerCodec.MAXIMUM_BYTES), "schema", "lookup", "context", "ordered_objectives", "available_steps");
        requireSchema(root, REQUEST_SCHEMA);
        ObjectNode context = object(root.get("context"), "stationary_threatened", "refuge_lifecycle_active", "active_route_unsafe", "exact_siege_rejected");
        List<Objective> objectives = new ArrayList<>();
        for (JsonNode row : array(root.get("ordered_objectives"))) {
            ObjectNode goal = object(row, "target_province_id", "source", "blocked");
            objectives.add(new Objective(integer(goal.get("target_province_id"), 1),
                    enumValue(CandidateSource.class, goal.get("source")), bool(goal.get("blocked"))));
        }
        List<String> steps = new ArrayList<>(); for (JsonNode row : array(root.get("available_steps"))) { steps.add(StrictJson.text(row)); }
        return new Request(RoutePreviewConsumerCodec.encodeEnvelope(root.get("lookup")),
                new Context(bool(context.get("stationary_threatened")), bool(context.get("refuge_lifecycle_active")),
                        bool(context.get("active_route_unsafe")), bool(context.get("exact_siege_rejected"))), objectives, steps);
    }
    public static byte[] encodeRequest(Request request) {
        ObjectNode root = StrictJson.object(); root.put("schema", REQUEST_SCHEMA);
        root.set("lookup", StrictJson.parse(request.lookupPacket(), RoutePreviewConsumerCodec.MAXIMUM_BYTES));
        Context context = request.context(); ObjectNode row = root.putObject("context");
        row.put("stationary_threatened", context.stationaryThreatened()); row.put("refuge_lifecycle_active", context.refugeLifecycleActive());
        row.put("active_route_unsafe", context.activeRouteUnsafe()); row.put("exact_siege_rejected", context.exactSiegeRejected());
        var objectives = root.putArray("ordered_objectives");
        for (Objective goal : request.orderedObjectives()) {
            ObjectNode goalRow = objectives.addObject(); goalRow.put("target_province_id", goal.targetProvinceId());
            goalRow.put("source", goal.source().name()); goalRow.put("blocked", goal.blocked());
        }
        var steps = root.putArray("available_steps"); request.availableSteps().forEach(steps::add);
        return RoutePreviewConsumerCodec.encodeEnvelope(root);
    }
    public static byte[] project(byte[] raw) {
        Request request = decodeRequest(raw);
        return encodeResult(RoutePlanningConsumer.planOrdinary(request.lookupPacket(), request.context(), request.orderedObjectives(), request.availableSteps()));
    }
    public static byte[] encodeResult(Result result) {
        ObjectNode root = StrictJson.object(); root.put("schema", RESULT_SCHEMA); root.put("action_authorized", false);
        var rejected = root.putArray("rejections");
        for (Rejection value : result.rejections()) {
            ObjectNode row = rejected.addObject(); row.put("target_province_id", value.targetProvinceId()); row.put("reason", value.reason().name());
        }
        if (result instanceof PreviewQuery query) {
            root.put("type", "PREVIEW_QUERY"); root.put("army_id", query.armyId()); root.put("origin_province_id", query.originProvinceId());
            root.put("target_province_id", query.targetProvinceId()); root.put("required_step", query.requiredStep()); root.put("step_available", query.stepAvailable());
        } else if (result instanceof ReadinessRequired value) {
            root.put("type", "READINESS_REQUIRED"); root.put("target_province_id", value.targetProvinceId()); preview(root, value.preview());
        } else if (result instanceof ExistingDateBoundary value) {
            root.put("type", "EXISTING_DATE_BOUNDARY"); root.put("target_province_id", value.targetProvinceId());
            if (value.existingCandidateStep().isPresent()) { root.put("existing_candidate_step", value.existingCandidateStep().orElseThrow()); }
            else { root.putNull("existing_candidate_step"); } preview(root, value.preview());
        } else if (result instanceof AuditContinuation value) {
            root.put("type", "AUDIT_CONTINUATION"); root.put("target_province_id", value.targetProvinceId()); root.put("objective_rank", value.objectiveRank());
            root.put("source", value.source().name()); preview(root, value.preview());
        } else if (result instanceof StationaryContinuation value) {
            root.put("type", "STATIONARY_CONTINUATION"); root.put("target_province_id", value.targetProvinceId()); root.put("objective_rank", value.objectiveRank());
        } else if (result instanceof Arrived value) {
            root.put("type", "ARRIVED"); root.put("target_province_id", value.targetProvinceId()); root.put("objective_rank", value.objectiveRank());
        } else if (result instanceof Exhausted) { root.put("type", "EXHAUSTED"); }
        else if (result instanceof Unavailable value) { root.put("type", "UNAVAILABLE"); root.put("missing", value.missing().name()); }
        else { throw new IllegalArgumentException("unknown route planner result"); }
        return RoutePreviewConsumerCodec.encodeEnvelope(root);
    }
    public static Result decodeResult(byte[] raw) {
        JsonNode parsed = StrictJson.parse(raw, RoutePreviewConsumerCodec.MAXIMUM_BYTES);
        String type = StrictJson.text(parsed.get("type"));
        Set<String> common = Set.of("schema", "type", "action_authorized", "rejections");
        Set<String> extra = switch (type) {
            case "PREVIEW_QUERY" -> Set.of("army_id", "origin_province_id", "target_province_id", "required_step", "step_available");
            case "READINESS_REQUIRED" -> Set.of("target_province_id", "preview");
            case "EXISTING_DATE_BOUNDARY" -> Set.of("target_province_id", "preview", "existing_candidate_step");
            case "AUDIT_CONTINUATION" -> Set.of("target_province_id", "objective_rank", "source", "preview");
            case "STATIONARY_CONTINUATION", "ARRIVED" -> Set.of("target_province_id", "objective_rank");
            case "EXHAUSTED" -> Set.of(); case "UNAVAILABLE" -> Set.of("missing");
            default -> throw new IllegalArgumentException("unknown route planner result type");
        };
        java.util.HashSet<String> fields = new java.util.HashSet<>(common); fields.addAll(extra);
        ObjectNode root = StrictJson.object(parsed, Set.copyOf(fields)); requireSchema(root, RESULT_SCHEMA);
        StrictJson.require(!bool(root.get("action_authorized")), "planner result cannot grant action authority");
        List<Rejection> rejected = new ArrayList<>();
        for (JsonNode row : array(root.get("rejections"))) {
            ObjectNode rejection = object(row, "target_province_id", "reason");
            rejected.add(new Rejection(integer(rejection.get("target_province_id"), 1), enumValue(RejectionReason.class, rejection.get("reason"))));
        }
        if (type.equals("EXHAUSTED")) { return new Exhausted(rejected); }
        if (type.equals("UNAVAILABLE")) { return new Unavailable(enumValue(MissingInput.class, root.get("missing")), rejected); }
        int target = integer(root.get("target_province_id"), 1);
        return switch (type) {
            case "PREVIEW_QUERY" -> new PreviewQuery(integer(root.get("army_id"), 0), integer(root.get("origin_province_id"), 1), target,
                    StrictJson.text(root.get("required_step")), bool(root.get("step_available")), rejected);
            case "READINESS_REQUIRED" -> new ReadinessRequired(target, preview(root), rejected);
            case "EXISTING_DATE_BOUNDARY" -> new ExistingDateBoundary(target,
                    root.get("existing_candidate_step").isNull() ? Optional.empty() : Optional.of(StrictJson.text(root.get("existing_candidate_step"))), preview(root), rejected);
            case "AUDIT_CONTINUATION" -> new AuditContinuation(target, integer(root.get("objective_rank"), 0),
                    enumValue(CandidateSource.class, root.get("source")), preview(root), rejected);
            case "STATIONARY_CONTINUATION" -> new StationaryContinuation(target, integer(root.get("objective_rank"), 0), rejected);
            case "ARRIVED" -> new Arrived(target, integer(root.get("objective_rank"), 0), rejected);
            default -> throw new IllegalArgumentException("unknown result");
        };
    }
    private static void preview(ObjectNode root, RouteReroutePolicy.Preview value) {
        root.set("preview", StrictJson.parse(RoutePreviewConsumerCodec.encode(Optional.of(value)), RoutePreviewConsumerCodec.MAXIMUM_BYTES));
    }
    private static RouteReroutePolicy.Preview preview(ObjectNode root) {
        return RoutePreviewConsumerCodec.decodePreview(RoutePreviewConsumerCodec.encodeEnvelope(root.get("preview")));
    }
    private static ObjectNode object(JsonNode value, String... keys) { return StrictJson.object(value, Set.of(keys)); }
    private static JsonNode array(JsonNode value) { StrictJson.require(value != null && value.isArray(), "array required"); return value; }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "boolean token required"); return value.booleanValue(); }
    private static int integer(JsonNode value, int minimum) { return (int) StrictJson.integer(value, minimum, Integer.MAX_VALUE); }
    private static <E extends Enum<E>> E enumValue(Class<E> type, JsonNode value) { return Enum.valueOf(type, StrictJson.text(value)); }
    private static void requireSchema(ObjectNode root, String schema) { StrictJson.require(StrictJson.text(root.get("schema")).equals(schema), "schema mismatch"); }
}
