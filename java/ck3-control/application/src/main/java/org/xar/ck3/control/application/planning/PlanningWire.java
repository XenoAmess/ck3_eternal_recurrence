package org.xar.ck3.control.application.planning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionFactCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Closed ordinary application wire, using the sole existing action/frame/source/domain contracts. */
public final class PlanningWire {
    public static final String REQUEST_SCHEMA = "xar.java-ordinary-plan-request/v2";
    public static final String RESULT_SCHEMA = "xar.java-ordinary-plan-result/v1";
    /** Full frozen snapshot plus surviving history; individual snapshot remains bounded at 64 MiB. */
    public static final int MAX_BYTES = 256 * 1024 * 1024;
    private PlanningWire() { }

    public static byte[] encodeRequest(PlanningRequest request) {
        ObjectNode root = StrictJson.object(); root.put("schema", REQUEST_SCHEMA);
        root.set("before", ProposalLifecycleCodec.observation(request.before()));
        root.set("source", ProposalLifecycleCodec.source(request.source())); root.put("session_id", request.sessionId());
        root.put("deadline", request.deadline().toString());
        PlanningObservation observation = request.observations(); ObjectNode row = root.putObject("observations");
        row.set("snapshot", DriverJson.toNode(observation.snapshot()));
        ArrayNode history = row.putArray("history"); observation.history().forEach(value -> history.add(DriverJson.toNode(value)));
        ArrayNode actions = row.putArray("action_steps"); observation.actionSteps().stream().map(OperationKey::value).sorted().forEach(actions::add);
        ArrayNode capabilities = row.putArray("bridge_capabilities"); observation.bridgeCapabilities().stream().sorted().forEach(capabilities::add);
        row.set("battle_speed_readiness", observation.battleSpeedReadiness().<JsonNode>map(DriverJson::toNode).orElseGet(() -> row.nullNode()));
        ArrayNode facts = row.putArray("action_facts"); observation.actionFacts().forEach(fact -> facts.add(ActionFactCodec.toJson(fact)));
        row.set("campaign_goal", observation.campaignGoal().<JsonNode>map(goal -> parse(GoalCodec.encodeGoal(goal))).orElseGet(() -> row.nullNode()));
        row.set("cross_run_plan", observation.crossRunPlan().<JsonNode>map(DriverJson::toNode).orElseGet(() -> row.nullNode()));
        row.put("initial_lifestyle_focus_required", observation.initialLifestyleFocusRequired());
        return encode(root);
    }

    public static PlanningRequest decodeRequest(byte[] raw) {
        ObjectNode root = StrictJson.object(parse(raw), Set.of("schema", "before", "source", "session_id", "deadline", "observations"));
        require(REQUEST_SCHEMA.equals(text(root, "schema")), "exact ordinary request schema required");
        ObjectNode row = StrictJson.object(root.get("observations"), Set.of("snapshot", "history", "action_steps", "bridge_capabilities",
                "battle_speed_readiness", "action_facts", "campaign_goal", "cross_run_plan", "initial_lifestyle_focus_required"));
        List<OpportunityJson.Obj> history = new ArrayList<>();
        for (JsonNode value : array(row.get("history"))) history.add(objectValue(value));
        Set<OperationKey> actions = new HashSet<>();
        for (JsonNode value : array(row.get("action_steps"))) require(actions.add(new OperationKey(StrictJson.text(value))), "duplicate action step");
        Set<String> capabilities = new HashSet<>();
        for (JsonNode value : array(row.get("bridge_capabilities"))) require(capabilities.add(StrictJson.text(value)), "duplicate bridge capability");
        var facts = new ArrayList<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact>();
        for (JsonNode value : array(row.get("action_facts"))) facts.add(ActionFactCodec.fromJson(value));
        PlanningObservation observation = new PlanningObservation(objectValue(row.get("snapshot")), history, actions, capabilities,
                optionalObject(row.get("battle_speed_readiness")), facts,
                row.get("campaign_goal").isNull() ? Optional.empty() : Optional.of(GoalCodec.parseGoal(row.get("campaign_goal"))),
                optionalObject(row.get("cross_run_plan")), bool(row.get("initial_lifestyle_focus_required")));
        String deadline = text(root, "deadline"); StrictJson.utc(deadline);
        return new PlanningRequest(ProposalLifecycleCodec.decodeObservation(root.get("before")), G2Wire.source(root.get("source")),
                text(root, "session_id"), Instant.parse(deadline), observation);
    }

    public static byte[] encodeResult(PlanningResult result) {
        ObjectNode root = StrictJson.object(); root.put("schema", RESULT_SCHEMA); root.set("trace", trace(result.trace()));
        switch (result) {
            case PlanningResult.ActionSelected selected -> {
                root.put("status", "ACTION_SELECTED"); root.set("command", parse(ActionCodec.encodeCommand(selected.command())));
            }
            case PlanningResult.ReadOnlyWait wait -> {
                root.put("status", "READ_ONLY_WAIT"); root.set("before", ProposalLifecycleCodec.observation(wait.before())); root.put("reason", wait.reason());
            }
            case PlanningResult.RefreshRequired refresh -> {
                root.put("status", "REFRESH_REQUIRED"); root.set("before", ProposalLifecycleCodec.observation(refresh.before())); root.put("reason", refresh.reason());
            }
            case PlanningResult.Stopped stopped -> {
                root.put("status", "STOPPED"); root.set("before", ProposalLifecycleCodec.observation(stopped.before()));
                root.put("stop_reason", stopped.reason().name()); root.put("detail", stopped.detail());
            }
            case PlanningResult.IncompleteMigration incomplete -> {
                root.put("status", "INCOMPLETE_MIGRATION"); root.set("before", ProposalLifecycleCodec.observation(incomplete.before()));
                ArrayNode stages = root.putArray("missing_stages"); incomplete.missingStages().forEach(stage -> stages.add(stage.name()));
            }
            case PlanningResult.ExistingActionReconciliation reconcile -> {
                root.put("status", "RECONCILE_EXISTING"); root.put("action_id", reconcile.actionId());
                root.set("before", ProposalLifecycleCodec.observation(reconcile.before())); root.set("detail", DriverJson.toNode(reconcile.detail()));
            }
        }
        return encode(root);
    }

    public static PlanningResult decodeResult(byte[] raw) {
        JsonNode parsed = parse(raw); require(parsed.isObject(), "ordinary result object required");
        ObjectNode root = (ObjectNode) parsed; require(RESULT_SCHEMA.equals(text(root, "schema")), "exact ordinary result schema required");
        PlanTrace trace = readTrace(root.get("trace"));
        return switch (text(root, "status")) {
            case "ACTION_SELECTED" -> {
                fields(root, "command"); yield new PlanningResult.ActionSelected(ActionCodec.decodeCommand(encode(root.get("command"))), trace);
            }
            case "READ_ONLY_WAIT" -> {
                fields(root, "before", "reason"); yield new PlanningResult.ReadOnlyWait(ProposalLifecycleCodec.decodeObservation(root.get("before")), text(root, "reason"), trace);
            }
            case "REFRESH_REQUIRED" -> {
                fields(root, "before", "reason"); yield new PlanningResult.RefreshRequired(ProposalLifecycleCodec.decodeObservation(root.get("before")), text(root, "reason"), trace);
            }
            case "STOPPED" -> {
                fields(root, "before", "stop_reason", "detail"); yield new PlanningResult.Stopped(ProposalLifecycleCodec.decodeObservation(root.get("before")),
                        PlanningResult.StopReason.valueOf(text(root, "stop_reason")), text(root, "detail"), trace);
            }
            case "INCOMPLETE_MIGRATION" -> {
                fields(root, "before", "missing_stages"); List<PlanningStage> stages = new ArrayList<>();
                for (JsonNode value : array(root.get("missing_stages"))) require(!stages.contains(PlanningStage.valueOf(StrictJson.text(value)))
                        && stages.add(PlanningStage.valueOf(StrictJson.text(value))), "duplicate missing stage");
                yield new PlanningResult.IncompleteMigration(ProposalLifecycleCodec.decodeObservation(root.get("before")), stages, trace);
            }
            case "RECONCILE_EXISTING" -> {
                fields(root, "action_id", "before", "detail"); yield new PlanningResult.ExistingActionReconciliation(text(root, "action_id"),
                        ProposalLifecycleCodec.decodeObservation(root.get("before")), objectValue(root.get("detail")), trace);
            }
            default -> throw new IllegalArgumentException("unsupported ordinary result status");
        };
    }

    public static ObjectNode trace(PlanTrace trace) {
        ObjectNode row = StrictJson.object(); row.set("before", ProposalLifecycleCodec.observation(trace.before()));
        ArrayNode visits = row.putArray("visits");
        for (PlanTrace.StageVisit visit : trace.visits()) {
            ObjectNode value = visits.addObject(); value.put("stage", visit.stage().name()); value.put("outcome", visit.outcome().name()); value.put("reason", visit.reason());
            value.set("source", visit.source().<JsonNode>map(ExactRef::toJson).orElseGet(() -> value.nullNode()));
            value.set("evidence", visit.evidence().<JsonNode>map(DriverJson::toNode).orElseGet(() -> value.nullNode()));
        }
        row.set("final_plan", trace.finalPlan().<JsonNode>map(PlanningWire::draft).orElseGet(() -> row.nullNode())); return row;
    }

    private static PlanTrace readTrace(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("before", "visits", "final_plan")); List<PlanTrace.StageVisit> visits = new ArrayList<>();
        for (JsonNode entry : array(row.get("visits"))) {
            ObjectNode visit = StrictJson.object(entry, Set.of("stage", "outcome", "reason", "source", "evidence"));
            visits.add(new PlanTrace.StageVisit(PlanningStage.valueOf(text(visit, "stage")), PlanTrace.Outcome.valueOf(text(visit, "outcome")), text(visit, "reason"),
                    visit.get("source").isNull() ? Optional.empty() : Optional.of(ExactRef.fromJson(visit.get("source"))), optionalObject(visit.get("evidence"))));
        }
        return new PlanTrace(ProposalLifecycleCodec.decodeObservation(row.get("before")), visits,
                row.get("final_plan").isNull() ? Optional.empty() : Optional.of(readDraft(row.get("final_plan"))));
    }

    private static ObjectNode draft(OrdinaryPolicy.Draft draft) {
        ObjectNode row = StrictJson.object(); row.put("policy", draft.policy()); row.put("phase", draft.phase()); row.put("reason", draft.reason());
        row.put("kind", draft.kind().name()); row.put("purpose", draft.purpose().name());
        row.set("command", draft.command().<JsonNode>map(command -> parse(ActionCodec.encodeCommand(command))).orElseGet(() -> row.nullNode()));
        if (draft.domain().isPresent()) row.put("domain", draft.domain().orElseThrow().name()); else row.putNull("domain");
        row.set("detail", DriverJson.toNode(draft.detail())); return row;
    }
    private static OrdinaryPolicy.Draft readDraft(JsonNode node) {
        ObjectNode row = StrictJson.object(node, Set.of("policy", "phase", "reason", "kind", "purpose", "command", "domain", "detail"));
        return new OrdinaryPolicy.Draft(text(row, "policy"), text(row, "phase"), text(row, "reason"), OrdinaryPolicy.Kind.valueOf(text(row, "kind")),
                row.get("command").isNull() ? Optional.empty() : Optional.of(ActionCodec.decodeCommand(encode(row.get("command")))),
                OrdinaryPolicy.Purpose.valueOf(text(row, "purpose")), row.get("domain").isNull() ? Optional.empty() : Optional.of(Domain.valueOf(text(row, "domain"))), objectValue(row.get("detail")));
    }

    private static Optional<OpportunityJson.Obj> optionalObject(JsonNode node) { require(node != null, "required nullable field is missing"); return node.isNull() ? Optional.empty() : Optional.of(objectValue(node)); }
    private static OpportunityJson.Obj objectValue(JsonNode node) {
        require(node != null && node.isObject(), "immutable JSON object required"); return (OpportunityJson.Obj) value(node);
    }
    /** The shared JSON domain's sole tree conversion here retains absent members, explicit null and arrays. */
    private static OpportunityJson.Value value(JsonNode node) {
        require(node != null, "missing JSON cannot become explicit null");
        if (node.isObject()) {
            var fields = new LinkedHashMap<String, OpportunityJson.Value>(); node.properties().forEach(field -> fields.put(field.getKey(), value(field.getValue())));
            return new OpportunityJson.Obj(fields);
        }
        if (node.isArray()) { List<OpportunityJson.Value> values = new ArrayList<>(); node.forEach(item -> values.add(value(item))); return new OpportunityJson.Arr(values); }
        if (node.isTextual()) return new OpportunityJson.Text(node.textValue());
        if (node.isIntegralNumber()) return new OpportunityJson.IntegerValue(node.bigIntegerValue());
        if (node.isFloatingPointNumber()) {
            require(node instanceof DecimalTokenNode, "ordinary JSON decimal must retain its original token");
            return new OpportunityJson.DecimalValue(((DecimalTokenNode) node).originalToken());
        }
        if (node.isBoolean()) return new OpportunityJson.Bool(node.booleanValue());
        require(node.isNull(), "unsupported JSON node"); return OpportunityJson.Nil.INSTANCE;
    }
    private static JsonNode parse(byte[] raw) { return FullJsonTree.parse(raw, MAX_BYTES); }
    private static byte[] encode(JsonNode value) {
        byte[] raw = PublicDataJson.encodeTypedBytes(value(value), MAX_BYTES);
        require(raw.length <= MAX_BYTES, "ordinary full wire exceeds the frozen Driver byte budget");
        return raw;
    }
    private static ArrayNode array(JsonNode node) { require(node instanceof ArrayNode, "exact JSON array required"); return (ArrayNode) node; }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue(); }
    private static void fields(ObjectNode row, String... specific) {
        Set<String> expected = new HashSet<>(List.of("schema", "status", "trace")); expected.addAll(List.of(specific)); StrictJson.object(row, expected);
    }
    private static void require(boolean condition, String reason) { StrictJson.require(condition, reason); }
}
