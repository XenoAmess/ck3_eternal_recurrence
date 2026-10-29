package org.xar.ck3.control.wave2.military.commander;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.military.commander.CommanderQuality.*;

/** Strict raw-token entry. SDK containers remain extensible declared projections. */
public final class CommanderQualityCodec {
    public static final String INPUT_SCHEMA = "xar.java.commander-quality-input.v1";
    public static final String PLAN_SCHEMA = "xar.java.commander-quality-plan-input.v1";
    public static final int MAX_BYTES = ArmyCommanderCandidatesCodec.MAX_BYTES;
    private static final BigInteger INT32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private CommanderQualityCodec() { }

    public static byte[] propose(byte[] raw) { return ArmyCommanderCandidatesCodec.encodeJson(encodeProposal(decodeProposalInput(ArmyCommanderCandidatesCodec.parseJson(raw)))); }
    public static byte[] proposeTarget(byte[] raw, int expectedTargetProvince) {
        return ArmyCommanderCandidatesCodec.encodeJson(encodeProposal(decodeTargetProposalInput(ArmyCommanderCandidatesCodec.parseJson(raw), expectedTargetProvince)));
    }
    public static Proposal decodeProposalInput(JsonNode value) {
        ObjectNode root = closedObject(value, Set.of("schema", "snapshot", "query_sequence", "candidates"));
        equal(root.get("schema"), INPUT_SCHEMA); Frame frame = frame(object(root.get("snapshot")), positive(root.get("query_sequence")));
        Candidates candidates = candidates(root.get("candidates"), frame);
        return CommanderQuality.propose(candidates, frame);
    }

    private static Candidates candidates(JsonNode raw, Frame frame) {
        ObjectNode payload = object(raw); NativeId army = id(payload.get("army_id"));
        JsonNode province = payload.get("target_province_id");
        // Pure proposal DTOs retain normalized target context; native reads admit a separate requested target below.
        java.util.Optional<ArmyCommanderCandidatesCodec.Province> target = province == null || province.isNull()
                ? java.util.Optional.empty() : java.util.Optional.of(new ArmyCommanderCandidatesCodec.Province(
                        boundedInteger(province, BigInteger.ONE, INT32_MAX).intValueExact()));
        return ArmyCommanderCandidatesCodec.normalize(raw, new ArmyCommanderCandidatesCodec.Expected(army,
                frame.nativeRevision(), frame.dateRaw(), target)).qualityInput();
    }

    public static Proposal decodeTargetProposalInput(JsonNode value, int expectedTargetProvince) {
        ObjectNode root = closedObject(value, Set.of("schema", "snapshot", "query_sequence", "candidates"));
        equal(root.get("schema"), INPUT_SCHEMA); Frame frame = frame(object(root.get("snapshot")), positive(root.get("query_sequence")));
        var target = new ArmyCommanderCandidatesCodec.Province(expectedTargetProvince); NativeId army = id(object(root.get("candidates")).get("army_id"));
        var normalized = ArmyCommanderCandidatesCodec.normalize(root.get("candidates"), new ArmyCommanderCandidatesCodec.Expected(army,
                frame.nativeRevision(), frame.dateRaw(), java.util.Optional.of(target)));
        return ArmyCommanderCandidatesCodec.propose(normalized, frame);
    }

    /** Validate an already observed query against before/after scope; this performs no native read. */
    public static Proposal admitObservedQuery(byte[] raw) {
        return admitObservedObservation(raw).proposal();
    }
    public static Proposal admitObservedTargetQuery(byte[] raw, int expectedTargetProvince) {
        return admitObservedTargetObservation(raw, expectedTargetProvince).proposal();
    }
    public static ArmyCommanderCandidatesCodec.ObservedQuery admitObservedObservation(byte[] raw) {
        return admitObserved(raw, java.util.Optional.empty());
    }
    public static ArmyCommanderCandidatesCodec.ObservedQuery admitObservedTargetObservation(byte[] raw, int expectedTargetProvince) {
        return admitObserved(raw, java.util.Optional.of(new ArmyCommanderCandidatesCodec.Province(expectedTargetProvince)));
    }
    private static ArmyCommanderCandidatesCodec.ObservedQuery admitObserved(byte[] raw, java.util.Optional<ArmyCommanderCandidatesCodec.Province> target) {
        ObjectNode root = closedObject(ArmyCommanderCandidatesCodec.parseJson(raw), Set.of("schema", "army_id", "snapshot_before", "snapshot_after", "bridge_capabilities", "expected_revision", "native_result"));
        equal(root.get("schema"), "xar.java.commander-quality-observed-query.v1"); NativeId army = id(root.get("army_id"));
        ObjectNode before = object(root.get("snapshot_before")); ObjectNode after = object(root.get("snapshot_after"));
        require(bool(before.get("paused")) && bool(after.get("paused")), "commander query requires paused before/after snapshots");
        for (String key : Set.of("snapshot_id", "revision", "native_revision", "date_raw")) { require(Objects.equals(before.get(key), after.get(key)), "commander query crossed a paused frame"); }
        if (!root.get("expected_revision").isNull()) { require(nonnegative(root.get("expected_revision")).equals(nonnegative(before.get("revision"))), "commander public revision mismatch"); }
        var request = new ArmyCommanderCandidatesCodec.QueryStep(army, target);
        require(strings(root.get("bridge_capabilities")).contains(request.capability()), "requested commander query capability unavailable");
        JsonNode armies = before.get("player_armies"); require(armies != null && armies.isArray(), "current player armies unavailable"); int matching = 0;
        for (JsonNode row : armies) { if (row.isObject() && row.hasNonNull("army_id") && row.get("army_id").isIntegralNumber() && row.get("army_id").bigIntegerValue().equals(BigInteger.valueOf(army.value())) && row.path("controllable").isBoolean() && row.path("controllable").booleanValue()) { matching++; } }
        require(matching == 1, "army outside unique controllable player scope");
        ObjectNode result = object(root.get("native_result"));
        equal(result.get("step"), request.step()); equal(result.get("status"), "completed");
        require(bool(result.get("accepted")), "actual accepted true required"); require(bool(result.get("read_only")), "actual read_only true required");
        Frame frame = frame(before, positive(result.get("query_sequence")));
        require(integer(result.get("snapshot_revision")).equals(frame.nativeRevision()) && integer(result.get("date_raw")).equals(frame.dateRaw()), "native query envelope frame mismatch");
        var normalized = ArmyCommanderCandidatesCodec.normalize(result.get("army_commander_candidates"), new ArmyCommanderCandidatesCodec.Expected(army,
                frame.nativeRevision(), frame.dateRaw(), target));
        return new ArmyCommanderCandidatesCodec.ObservedQuery(normalized, frame, ArmyCommanderCandidatesCodec.propose(normalized, frame));
    }

    /** Offline wire adapter for the actual formal consumer. Query entries are captured observations, not actions. */
    public static byte[] plan(byte[] raw) {
        return ArmyCommanderCandidatesCodec.encodePreserving(raw, planNode(raw, false), "/planned",
                List.of(new ArmyCommanderCandidatesCodec.OriginalAlias("/plan/deferred_commander_baseline_plan", "/planned/plan")));
    }
    /** Continue the same formal plan only until its existing query port needs another actual observation. */
    public static byte[] continuePlan(byte[] raw) {
        ObjectNode reply = StrictJson.object(); reply.put("schema", "xar.java.commander-quality-plan-continuation.v1");
        try { reply.put("status", "completed"); reply.set("planned", planNode(raw, true)); }
        catch (NextQuery query) { reply.put("status", "query"); reply.put("army_id", query.armyId); reply.put("expected_revision", query.revision); }
        return ArmyCommanderCandidatesCodec.encodePreserving(raw, reply, "",
                List.of(new ArmyCommanderCandidatesCodec.OriginalAlias("/planned/plan/deferred_commander_baseline_plan", "/planned/plan")));
    }
    private static final class NextQuery extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final int armyId;
        private final BigInteger revision;
        private NextQuery(NativeId army, BigInteger revision) { super(null, null, false, false); this.armyId = army.value(); this.revision = revision; }
    }
    private static ObjectNode planNode(byte[] raw, boolean continuation) {
        ObjectNode root = closedObject(ArmyCommanderCandidatesCodec.parseJson(raw), Set.of("schema", "planned", "snapshot", "bridge_capabilities", "queries")); equal(root.get("schema"), PLAN_SCHEMA);
        ObjectNode planned = object(root.get("planned")); ObjectNode snapshot = object(root.get("snapshot")); JsonNode rawPlan = planned.get("plan");
        ObjectNode base = rawPlan != null && rawPlan.isObject() ? object(rawPlan) : null;
        Field<NativeId> pursuit = Field.missing();
        if (base != null && base.path("pursuit").isObject()) { pursuit = base.get("pursuit").hasNonNull("army_id") ? Field.of(id(base.get("pursuit").get("army_id"))) : Field.nullValue(); }
        List<Army> armies = new ArrayList<>(); JsonNode rawArmies = snapshot.get("player_armies");
        if (rawArmies != null && rawArmies.isArray()) { for (JsonNode army : rawArmies) {
            if (army.isObject() && army.path("controllable").isBoolean() && army.path("controllable").booleanValue() && army.hasNonNull("army_id")) { armies.add(new Army(id(army.get("army_id")), true)); }
        } }
        PlanContext context = new PlanContext(base != null && rawArmies != null && rawArmies.isArray(), base == null ? null : nullableText(base.get("phase")),
                base == null ? Field.missing() : stringField(base, "selected_step"), pursuit, planned.has("revision") ? nonnegative(planned.get("revision")) : null, armies, strings(root.get("bridge_capabilities")));
        JsonNode queries = root.get("queries"); require(queries != null && queries.isArray(), "query observation array required"); int[] cursor = {0};
        Decision decision = CommanderQuality.plan(context, (army, revision) -> {
            if (continuation && cursor[0] == queries.size()) { throw new NextQuery(army, revision); }
            require(cursor[0] < queries.size(), "missing consumed query observation");
            ObjectNode query = closedObject(queries.get(cursor[0]++), Set.of("army_id", "proposal_input", "unavailable_reason"));
            require(id(query.get("army_id")).equals(army), "query observation scan order mismatch");
            if (!query.get("unavailable_reason").isNull()) { require(query.get("proposal_input").isNull(), "query unavailable/input conflict"); return new InputUnavailable(text(query.get("unavailable_reason"))); }
            Proposal proposal = decodeProposalInput(query.get("proposal_input"));
            require(proposal.context().armyId().equals(army) && proposal.frame().revision().equals(revision), "formal query army/revision mismatch");
            for (String key : Set.of("snapshot_id", "revision", "native_revision", "date_raw")) { require(Objects.equals(query.get("proposal_input").get("snapshot").get(key), snapshot.get(key)), "formal query snapshot mismatch"); }
            return new Queried(proposal);
        });
        require(cursor[0] == queries.size(), "unused query observation; actual consumer would not query it");
        ObjectNode output = planned.deepCopy();
        if (decision.selection() != null) {
            ObjectNode plan = Objects.requireNonNull(base).deepCopy(); plan.set("commander_quality_selection", encodeSelection(decision.selection(), base.get("selected_step")));
            if (decision.actionable()) {
                Proposal proposal = ((Queried) decision.selection().outcome()).proposal(); plan.remove("required_step"); plan.put("phase", "native_commander_quality_assignment"); plan.put("selected_step", proposal.selectedStep());
                plan.put("reason", proposal.status() == ProposalStatus.ASSIGN_BETTER ? "a native-eligible commander improves the observed current native quality" : "a native-eligible commander fills the observed empty commander role");
                plan.set("deferred_commander_baseline_plan", base.deepCopy());
            }
            output.set("plan", plan);
        }
        return output;
    }

    public static ObjectNode encodeProposal(Proposal value) {
        ObjectNode node = StrictJson.object(); node.put("schema", "xar.ck3.commander-quality-proposal.v1"); node.put("policy", "native_base_quality_current_baseline_v1"); node.put("status", value.status().wire());
        node.put("read_only", true); node.put("scope", "existing_mcp_queried_proposal"); node.put("automatic_consumption", false); node.put("assignment_executed", false); node.put("source", "native_ai_base_quality");
        node.put("army_id", value.context().armyId().value()); putId(node, "native_carmy_id", value.context().nativeArmyId()); putId(node, "owner_character_id", value.context().ownerCharacterId());
        ObjectNode frame = node.putObject("frame"); frame.put("snapshot_id", value.frame().snapshotId()); frame.put("revision", value.frame().revision()); frame.put("native_revision", value.frame().nativeRevision()); frame.put("date_raw", value.frame().dateRaw()); frame.put("query_sequence", value.frame().querySequence());
        putId(node, "current_commander_character_id", value.context().current().characterId()); putInteger(node, "current_native_ai_base_quality", value.currentQuality());
        putId(node, "best_eligible_candidate_character_id", value.bestCandidate() == null ? null : value.bestCandidate().characterId()); putInteger(node, "best_eligible_candidate_native_ai_base_quality", value.bestCandidate() == null ? null : value.bestCandidate().nativeQuality());
        if (value.qualityGain() == null) { node.putNull("quality_gain"); } else { node.put("quality_gain", value.qualityGain()); }
        putId(node, "proposed_commander_character_id", value.proposedCharacterId()); putText(node, "selected_step", value.selectedStep()); putText(node, "unavailable_reason", value.unavailableReason()); return node;
    }
    public static ObjectNode encodePublicV2Proposal(Proposal value) {
        ObjectNode node = encodeProposal(value); ObjectNode frame = (ObjectNode) node.get("frame");
        for (String key : Set.of("revision", "native_revision", "date_raw", "query_sequence")) frame.put(key, frame.get(key).bigIntegerValue().toString());
        return node;
    }
    private static ObjectNode encodeSelection(Selection value, JsonNode baseline) {
        ObjectNode node = StrictJson.object(); node.put("schema", "xar.ck3.commander-quality-formal-consumer.v1"); node.put("assignment_executed", false); node.set("baseline_selected_step", baseline == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : baseline.deepCopy());
        if (value.outcome() instanceof InputUnavailable unavailable) { node.put("status", "input_unavailable"); node.put("formal_action_ready", false); node.putNull("selected_step"); node.put("reason", unavailable.reason());
        } else { Proposal proposal = ((Queried) value.outcome()).proposal(); node.put("status", proposal.status().wire()); node.put("automatic_consumption", true); node.put("formal_action_ready", proposal.selectedStep() != null); putText(node, "selected_step", proposal.selectedStep()); node.set("proposal", encodeProposal(proposal)); }
        if (!value.unavailableInputs().isEmpty()) { ArrayNode inputs = node.putArray("unavailable_inputs"); for (UnavailableInput unavailable : value.unavailableInputs()) { ObjectNode entry = inputs.addObject(); entry.put("army_id", unavailable.armyId().value()); entry.put("reason", unavailable.reason()); } }
        return node;
    }

    private static Frame frame(ObjectNode snapshot, BigInteger sequence) { return new Frame(text(snapshot.get("snapshot_id")), nonnegative(snapshot.get("revision")), positive(snapshot.get("native_revision")), integer(snapshot.get("date_raw")), sequence); }
    private static ObjectNode object(JsonNode value) { require(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value; }
    private static String text(JsonNode value) { require(value != null && value.isTextual(), "exact JSON string required"); String result = value.textValue(); if (!result.isEmpty()) { boundedText(result); } return result; }
    private static String nullableText(JsonNode value) { return value == null || value.isNull() ? null : text(value); }
    private static void equal(JsonNode value, String expected) { require(expected.equals(text(value)), "unexpected schema/source/step: " + expected); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "exact JSON boolean required"); return value.booleanValue(); }
    private static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "exact integer token required; no bool/float/string"); return value.bigIntegerValue(); }
    private static BigInteger nonnegative(JsonNode value) { BigInteger result = integer(value); require(result.signum() >= 0, "nonnegative integer required"); return result; }
    private static BigInteger positive(JsonNode value) { BigInteger result = integer(value); require(result.signum() > 0, "positive integer required"); return result; }
    private static NativeId id(JsonNode value) { return new NativeId(boundedInteger(value, BigInteger.ZERO, INT32_MAX).intValueExact()); }
    private static Set<String> strings(JsonNode value) { require(value != null && value.isArray(), "string array required"); Set<String> result = new HashSet<>(); for (JsonNode entry : value) { result.add(text(entry)); } return Set.copyOf(result); }
    private static Field<String> stringField(ObjectNode node, String key) { return !node.has(key) ? Field.missing() : node.get(key).isNull() ? Field.nullValue() : Field.of(text(node.get(key))); }
    private static void putId(ObjectNode node, String name, NativeId value) { if (value == null) { node.putNull(name); } else { node.put(name, value.value()); } }
    private static void putInteger(ObjectNode node, String name, Integer value) { if (value == null) { node.putNull(name); } else { node.put(name, value); } }
    private static void putText(ObjectNode node, String name, String value) { if (value == null) { node.putNull(name); } else { node.put(name, value); } }
    private static void require(boolean valid, String message) { if (!valid) throw new ProjectionDomainRejection(message); }
    private static ObjectNode closedObject(JsonNode value, Set<String> fields) {
        try { return StrictJson.object(value, fields); } catch (ContractViolationException error) { throw new ProjectionDomainRejection(error.getMessage()); }
    }
    private static BigInteger boundedInteger(JsonNode value, BigInteger minimum, BigInteger maximum) {
        try { return StrictJson.integer(value, minimum, maximum); } catch (ContractViolationException error) { throw new ProjectionDomainRejection(error.getMessage()); }
    }
    private static void boundedText(String value) {
        try { StrictJson.text(value); } catch (ContractViolationException error) { throw new ProjectionDomainRejection(error.getMessage()); }
    }
}
