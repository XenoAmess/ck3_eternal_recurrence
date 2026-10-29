package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcement;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcementCodec;
import org.xar.ck3.control.wave2.military.holyhirecontract.HolyHireCodec;

/** Two typed pure ports in the one existing host. Original owners retain transport and Game authority. */
public final class HolyConsumerPorts {
    private HolyConsumerPorts() { }
    /** Root supplies the two canonical central enum values; this leaf creates no enum aliases or dispatcher. */
    public record Operations(ProjectionOperation reinforcement, ProjectionOperation hire) {
        public Operations { Objects.requireNonNull(reinforcement); Objects.requireNonNull(hire);
            StrictJson.require(reinforcement != hire, "two distinct central operations required"); }
    }
    public enum ReinfOperation { CHOOSE, PLAN, POSTCONDITION }
    public enum HireOperation { REQUEST, ACK, QUERY }
    public enum PlanStage { PREPARE, FOLD }
    public enum PostStage { VALIDATE, PREPARE, FOLD }
    public enum QueryStage { CONTEXT, ENVELOPE }
    public sealed interface ReinfInput permits Choose, Plan, Post { HolySdkJson.Source source(); }
    public record Choose(HolySdkJson.Source source) implements ReinfInput { }
    public record Plan(PlanStage stage, HolySdkJson.Source source) implements ReinfInput { }
    public record Post(PostStage stage, HolySdkJson.Source source) implements ReinfInput { }
    public sealed interface HireInput permits Request, Ack, Query { HolySdkJson.Source source(); }
    public record Request(HolySdkJson.Source source) implements HireInput { }
    public record Ack(HolySdkJson.Source source) implements HireInput { }
    public record Query(QueryStage stage, HolySdkJson.Source source) implements HireInput { }
    public record Reply(byte[] value) {
        public Reply { value = ProjectionJson.value(value, HolySdkJson.LIMIT).bytes(); }
        @Override public byte[] value() { return value.clone(); }
    }
    public static List<RegisteredProjection> registrations(Operations operations) {
        return List.of(RegisteredProjection.of(new ReinforcementPort(operations.reinforcement())),
                RegisteredProjection.of(new HirePort(operations.hire())));
    }
    private static <E extends Enum<E>> E exactEnum(JsonNode value, Class<E> type) {
        String wire = StrictJson.text(value);
        for (E item : type.getEnumConstants()) {
            if (wire.equals(item.name().toLowerCase(java.util.Locale.ROOT))) { return item; }
        }
        throw new IllegalArgumentException("unknown exact operation or stage");
    }
    private static HolySdkJson.Source request(HolySdkJson.Source outer, boolean staged) {
        StrictJson.object(outer.tree(), staged ? Set.of("operation", "stage", "request") : Set.of("operation", "request"));
        return outer.select("/request");
    }
    public static final class ReinforcementPort implements ProjectionPort<ReinfInput, Reply> {
        private final ProjectionOperation operation;
        public ReinforcementPort(ProjectionOperation operation) { this.operation = Objects.requireNonNull(operation); }
        @Override public ProjectionOperation operation() { return operation; }
        @Override public int inputMaximumBytes() { return HolySdkJson.LIMIT; }
        @Override public int outputMaximumBytes() { return HolySdkJson.LIMIT; }
        @Override public ReinfInput decode(byte[] raw) {
            HolySdkJson.Source outer = new HolySdkJson.Source(raw); JsonNode node = outer.tree();
            return switch (exactEnum(node.get("operation"), ReinfOperation.class)) {
                case CHOOSE -> new Choose(request(outer, false));
                case PLAN -> new Plan(exactEnum(node.get("stage"), PlanStage.class), request(outer, true));
                case POSTCONDITION -> new Post(exactEnum(node.get("stage"), PostStage.class), request(outer, true));
            };
        }
        @Override public Reply project(ReinfInput input) {
            HolySdkJson.Source source = input.source(); byte[] raw = source.bytes();
            return switch (input) {
                case Choose ignored -> new Reply(StrictJson.canonical(HolyReinforcementCodec.chooseNode(raw), HolySdkJson.LIMIT));
                case Plan plan -> plan.stage() == PlanStage.PREPARE ? planDirective(source)
                        : new Reply(source.merge(HolyReinforcementCodec.planNode(raw), "/planned",
                                Map.of("/plan/deferred_siege_plan", "/planned/plan")));
                case Post post -> switch (post.stage()) {
                    case VALIDATE -> {
                        ObjectNode req = HolyInputValidation.object(source.tree(), Set.of("schema", "proposal"));
                        HolyInputValidation.require("xar.ck3.holy-reinforcement-proposal-input.v1".equals(HolyInputValidation.text(req.get("schema"))), "proposal schema required");
                        var proposal = HolyReinforcementCodec.selectedProposal(req.get("proposal"));
                        yield new Reply(StrictJson.canonical(StrictJson.object().put("holy_order_id", proposal.selection().holyOrderId())));
                    }
                    case PREPARE -> new Reply(StrictJson.canonical(HolyReinforcementCodec.selectedPostReadDirective(raw), HolySdkJson.LIMIT));
                    case FOLD -> {
                        JsonNode result = HolyReinforcementCodec.selectedPostNode(raw);
                        yield new Reply(source.merge(result, "/ack", postAliases(source, result)));
                    }
                };
            };
        }
        @Override public byte[] encode(Reply result) { return result.value(); }
    }
    private static Reply planDirective(HolySdkJson.Source source) {
        ObjectNode req = HolyInputValidation.object(source.tree(), Set.of("schema", "snapshot", "planned", "bridge_capabilities", "query_available", "holy_context", "query_error"));
        HolyInputValidation.require(HolyReinforcementCodec.PLAN_SCHEMA.equals(HolyInputValidation.text(req.get("schema"))), "planner schema required");
        JsonNode planned = req.get("planned"); HolyInputValidation.require(planned.isObject(), "planner container required");
        JsonNode plan = planned.get("plan"); JsonNode available = req.get("query_available");
        HolyInputValidation.require(available.isBoolean() && req.get("bridge_capabilities").isArray(), "actual transport availability required");
        boolean capability = false;
        for (JsonNode item : req.get("bridge_capabilities")) { capability |= HolyReinforcement.CAPABILITY.equals(HolyInputValidation.text(item)); }
        boolean query = plan != null && plan.isObject()
                && HolyReinforcement.siegeNeed(HolyReinforcementCodec.snapshot(req.get("snapshot")), HolyReinforcementCodec.plan(plan)) != null
                && capability && available.booleanValue();
        ObjectNode out = StrictJson.object().put("query_current_terms", query);
        out.set("expected_revision", planned.has("revision") ? planned.get("revision") : out.nullNode());
        out.set("result", query ? out.nullNode() : planned);
        return new Reply(source.merge(out, "/absent", Map.of("/result", "/planned")));
    }
    private static Map<String, String> postAliases(HolySdkJson.Source source, JsonNode result) {
        String expense = "/holy_order_reinforcement_postcondition/actor_expenses";
        JsonNode id = result.path("holy_order_reinforcement_postcondition").path("holy_order_id");
        JsonNode rows = source.tree().path("after_context").path("rows");
        for (int i = 0; i < rows.size(); i++) {
            JsonNode sampled = rows.get(i).path("holy_order_id");
            if (sampled.isIntegralNumber() && id.isIntegralNumber()
                    && sampled.bigIntegerValue().equals(id.bigIntegerValue())
                    && rows.get(i).path("military_terms").has("troop_association")) {
                return Map.of(expense, "/actor_expenses",
                        "/holy_order_reinforcement_postcondition/troop_association",
                        "/after_context/rows/" + i + "/military_terms/troop_association");
            }
        }
        return Map.of(expense, "/actor_expenses");
    }
    public static final class HirePort implements ProjectionPort<HireInput, Reply> {
        private final ProjectionOperation operation;
        public HirePort(ProjectionOperation operation) { this.operation = Objects.requireNonNull(operation); }
        @Override public ProjectionOperation operation() { return operation; }
        @Override public int inputMaximumBytes() { return HolySdkJson.LIMIT; }
        @Override public int outputMaximumBytes() { return HolySdkJson.LIMIT; }
        @Override public HireInput decode(byte[] raw) {
            HolySdkJson.Source outer = new HolySdkJson.Source(raw); JsonNode node = outer.tree();
            return switch (exactEnum(node.get("operation"), HireOperation.class)) {
                case REQUEST -> new Request(request(outer, false));
                case ACK -> new Ack(request(outer, false));
                case QUERY -> new Query(exactEnum(node.get("stage"), QueryStage.class), request(outer, true));
            };
        }
        @Override public Reply project(HireInput input) {
            HolySdkJson.Source source = input.source(); byte[] raw = source.bytes();
            return switch (input) {
                case Request ignored -> { HolyHireCodec.request(raw); yield new Reply("null".getBytes(StandardCharsets.US_ASCII)); }
                case Ack ignored -> new Reply(source.merge(HolyHireCodec.acknowledgeNode(raw), "/ack", Map.of()));
                case Query query -> {
                    if (query.stage() == QueryStage.CONTEXT) {
                        ObjectNode req = HolyInputValidation.object(source.tree(), Set.of("schema", "value", "snapshot"));
                        HolyInputValidation.require("xar.ck3.holy-context-normalize-input.v1".equals(HolyInputValidation.text(req.get("schema"))), "context schema required");
                        HolyReinforcementCodec.context(req.get("value"), HolyReinforcementCodec.snapshot(req.get("snapshot")));
                        yield new Reply(source.token("/value"));
                    }
                    yield new Reply(source.merge(HolyHireCodec.queryNode(raw), "/packet/result/player_holy_order_context", Map.of()));
                }
            };
        }
        @Override public byte[] encode(Reply result) { return result.value(); }
    }
}
