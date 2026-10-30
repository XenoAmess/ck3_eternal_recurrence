package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;

/** The copied-source composition boundary formerly owned by the Python Service.
 * No native query, action dispatch or authoritative ledger write occurs here. */
public final class M6TerminalSourceComposition {
    public static final String SCHEMA = "xar.ck3.sway-terminal-source-composition.12004.v1";
    static final String BUILD = "1.20.0.4";
    static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    static final String COMPLETE = "authored_sway_complete_100_source";
    static final List<String> IDS = List.of("actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation");
    static final int MAX = M6SourceProducer.MAX_BYTES;

    private M6TerminalSourceComposition() { }

    /** Empty is an unqueried plane; it is never an available-empty native batch. */
    public record Inputs(Optional<ProjectionJson> completion, Optional<ProjectionJson> execution,
            Optional<ProjectionJson> termination, Optional<ProjectionJson> opinion) {
        public Inputs {
            Objects.requireNonNull(completion); Objects.requireNonNull(execution);
            Objects.requireNonNull(termination); Objects.requireNonNull(opinion);
            for (Optional<ProjectionJson> plane : List.of(completion, execution, termination, opinion)) {
                plane.ifPresent(value -> require(value.isObject(), "M6 copied source plane is an object"));
            }
        }
        public static Inputs unqueried() { return new Inputs(Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()); }
    }
    public enum NativeState { UNKNOWN, CONTINUE, TERMINATED_UNATTRIBUTED }
    public record CurrentInstance(NativeState state, BigInteger revision, int dateRaw, ProjectionJson copied) {
        public CurrentInstance { Objects.requireNonNull(state); Objects.requireNonNull(revision); Objects.requireNonNull(copied); }
    }
    public enum EndSource { RETAINED_WRAPPER_RETURN, COMMON_NATIVE_RETURN }
    public record RetainedEnd(EndSource source, ProjectionJson observation) {
        public RetainedEnd { Objects.requireNonNull(source); Objects.requireNonNull(observation); }
    }
    public record Cause(ProjectionJson observation) {
        public Cause { Objects.requireNonNull(observation); }
        public String key() { return COMPLETE; }
    }
    public record NamedMaterial(G2M6Contracts.NamedValue sway, G2M6Contracts.NamedValue blocker,
            BigInteger revision, int dateRaw, ProjectionJson observation) {
        public NamedMaterial { Objects.requireNonNull(sway); Objects.requireNonNull(blocker); Objects.requireNonNull(revision); Objects.requireNonNull(observation); }
    }
    public record Result(Identity identity, Optional<CurrentInstance> current, Optional<RetainedEnd> wrapperEnd,
            Optional<ProjectionJson> commonFamily, Optional<RetainedEnd> commonEnd, Optional<Cause> cause,
            Optional<NamedMaterial> material, ProjectionJson wire) {
        public Result {
            Objects.requireNonNull(identity); Objects.requireNonNull(current); Objects.requireNonNull(wrapperEnd);
            Objects.requireNonNull(commonFamily); Objects.requireNonNull(commonEnd); Objects.requireNonNull(cause);
            Objects.requireNonNull(material); Objects.requireNonNull(wire);
        }
        public NativeState nativeState() { return current.map(CurrentInstance::state).orElse(NativeState.UNKNOWN); }
        public boolean requestRetried() { return false; }
        public boolean actionAuthorized() { return false; }
        public boolean ledgerCommitted() { return false; }
    }

    /** Live ingress adds strict producer record validation to the historical copied-source compositor. */
    public static void validateInputs(Inputs inputs, Identity identity,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity queried) {
        M6InputValidation.validate(inputs, identity, queried);
    }
    public static ProjectionJson validateExecution(ProjectionJson raw, Identity identity) {
        return validateExecution(raw, Objects.requireNonNull(identity).nativeSubject());
    }
    public static ProjectionJson validateExecution(ProjectionJson raw, NativeSubject subject) {
        return M6InputValidation.journal(raw, Objects.requireNonNull(subject), true);
    }
    public static ProjectionJson validateTermination(ProjectionJson raw, Identity identity) {
        return validateTermination(raw, Objects.requireNonNull(identity).nativeSubject());
    }
    public static ProjectionJson validateTermination(ProjectionJson raw, NativeSubject subject) {
        return M6InputValidation.journal(raw, Objects.requireNonNull(subject), false);
    }

    /** Validate copied native planes before exposing any typed composition to consumers. */
    public static Result compose(G2M6Contracts.Episode episode, Inputs inputs) {
        Objects.requireNonNull(episode); Objects.requireNonNull(inputs);
        JsonNode resolved = parse(episode.originalResolved());
        ObjectNode original = original(resolved, episode.identity());
        JsonNode completion = inputs.completion().map(M6TerminalSourceComposition::parse).orElse(null);
        if (completion != null) {
            actual4(completion); textEquals(completion, "schema", "xar.ck3.sway_completion.v1");
            if (!bool(completion, "available") || !same(completion, original)) completion = null;
            else { u64(completion, "snapshot_revision", 1); signed(completion, "date_raw"); }
        }
        JsonNode execution = inputs.execution().map(value -> journal(parse(value), true)).orElse(null);
        JsonNode termination = inputs.termination().map(value -> journal(parse(value), false)).orElse(null);
        Optional<CurrentInstance> current = Optional.empty();
        JsonNode currentWire = null;
        if (completion != null) {
            currentWire = StrictJson.parse(M6SourceProducer.composeCurrentObservation(
                    StrictJson.canonical(completion, MAX), episode.identity()).bytes(), MAX);
            if (!currentWire.isNull()) {
                current = Optional.of(new CurrentInstance(integer(currentWire, "native_status_raw", 0, 1) == 0
                        ? NativeState.CONTINUE : NativeState.TERMINATED_UNATTRIBUTED,
                        u64(currentWire, "source_snapshot_revision", 1), signed(currentWire, "source_date_raw"), json(completion)));
            }
        }
        JsonNode wrapper = retainedWrapper(termination, original);
        JsonNode common = termination != null && same(termination, original) && termination.has("common_native_end")
                ? M6CommonEndSources.normalize(termination.get("common_native_end"), termination) : null;
        JsonNode commonEnd = M6CommonEndSources.retained(common, termination, original);
        JsonNode pair = null, causal = null;
        if (execution != null && termination != null && same(execution, original) && same(termination, original)) {
            ObjectNode joined = StrictJson.object(); joined.set("execution_read", execution); joined.set("termination_read", termination);
            pair = joined; causal = M6CausalSources.consume(execution, termination);
        }
        JsonNode material = inputs.opinion().isEmpty() ? null : material(parse(inputs.opinion().orElseThrow()), completion, original);
        JsonNode history = resolved.get("material_intervention"), retainedMaterial = null;
        if (history != null && history.isObject() && same(history, original)) {
            ObjectNode retained = StrictJson.object(); retained.put("source_kind", "historical_derived_ledger_summary");
            retained.put("current_native_material_observation", false); retained.put("terminal_cause_input", false);
            retained.set("copied_summary", history); retainedMaterial = retained;
        }
        ObjectNode output = StrictJson.object(); output.put("schema", SCHEMA); output.set("original_instance", original);
        nullable(output, "current_instance_observation", currentWire); nullable(output, "retained_end_observation", wrapper);
        nullable(output, "common_native_end_source", common); nullable(output, "retained_common_end_observation", commonEnd);
        nullable(output, "cause_input_pair", pair); nullable(output, "causal_observation", causal);
        output.put("terminal_cause_observed", causal != null);
        if (causal == null) output.putNull("terminal_cause_key"); else output.put("terminal_cause_key", COMPLETE);
        nullable(output, "named_material_observation", material); nullable(output, "retained_material_context", retainedMaterial);
        output.put("invalidation_notification_terminal_cause_qualified", false);
        output.put("invalidation_missing", "exact_12004_notification_binding_and_dynamic_end_relationship_unavailable");
        Optional<NamedMaterial> typedMaterial = material == null ? Optional.empty() : Optional.of(new NamedMaterial(
                named(material.get("scheme_sway_opinion")), named(material.get("sway_blocker_opinion")),
                u64(material, "source_snapshot_revision", 1), signed(material, "source_date_raw"), json(material)));
        return new Result(episode.identity(), current, end(wrapper, EndSource.RETAINED_WRAPPER_RETURN),
                optionalJson(common), end(commonEnd, EndSource.COMMON_NATIVE_RETURN),
                causal == null ? Optional.empty() : Optional.of(new Cause(json(causal))), typedMaterial, json(output));
    }

    private static ObjectNode original(JsonNode resolved, Identity identity) {
        object(resolved); textEquals(resolved, "status", "applied"); require(bool(resolved, "postcondition_verified"), "original Start was verified");
        textEquals(resolved, "action_id", identity.actionId());
        require(integer(resolved, "actor_character_id", 1, 0xffff_fffeL) == identity.actorCharacterId()
                && integer(resolved, "target_character_id", 1, 0xffff_fffeL) == identity.targetCharacterId(), "original actor/target differ");
        JsonNode receipt = resolved.get("native_receipt");
        boolean recovered = receipt == null || receipt.isNull();
        JsonNode observed = recovered ? resolved.get("recovered_instance_observation") : receipt;
        if (recovered && observed == null) observed = resolved.get("applied_instance_observation");
        object(observed);
        require(integer(observed, "scheme_instance_id", 0, 0xffff_fffeL) == identity.schemeInstanceId()
                && integer(observed, "scheme_instance_generation", 0, 255) == identity.schemeInstanceGeneration(), "original full instance differs");
        if (!recovered) { textEquals(receipt, "schema", "active-scheme-sway-formal-private-v1"); textEquals(receipt, "stage", "applied");
            require(bool(receipt, "postcondition_verified"), "native original verified"); textEquals(receipt, "action_id", identity.actionId()); }
        JsonNode origin = recovered ? observed.get("source_read") : receipt;
        String build = text(origin, "exact_ck3_build"), digest = text(origin, "exe_sha256");
        require((BUILD.equals(build) && EXE.equalsIgnoreCase(digest)) || ("1.20.0.3".equals(build)
                && "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6".equalsIgnoreCase(digest)), "original exact build pair differs");
        ObjectNode result = identityJson(identity); result.put("original_exact_ck3_build", build); result.put("original_exe_sha256", digest);
        if (recovered) { result.put("original_identity_source_kind", "matching_active_readback_recovery");
            result.put("submission_receipt_available", false); result.set("recovered_instance_observation", observed); }
        return result;
    }

    static JsonNode journal(JsonNode input, boolean execution) {
        object(input); String key = execution ? "sway_completion_execution" : "sway_completion_termination";
        ObjectNode read;
        if (input.has("type") && "command_result".equals(text(input, "type"))) {
            require(integer(input, "protocol_version", 1, 1) == 1 && bool(input, "ok"), "native command frame rejected");
            JsonNode result = input.get("result"); object(result);
            require(bool(result, "accepted") && bool(result, "private_build") && bool(result, "read_only"), "native command contract differs");
            actual4(result); object(result.get(key)); read = ((ObjectNode)result.get(key)).deepCopy();
            for (String field : List.of("build_version", "executable_sha256")) {
                require(!read.has(field) || read.get(field).equals(result.get(field)), "journal native envelope differs"); read.set(field, result.get(field));
            }
            require(result.has("snapshot_revision") && result.has("date_raw"), "journal native envelope frame missing");
            read.set("source_snapshot_revision", result.get("snapshot_revision")); read.set("source_date_raw", result.get("date_raw"));
        } else read = ((ObjectNode)input).deepCopy();
        actual4(read); textEquals(read, "schema", execution ? "xar.ck3.sway-completion-execution.v1" : "xar.ck3.sway-completion-termination.v1");
        bool(read, "available"); bool(read, "retention_gap"); array(read.get("records"));
        for (JsonNode row : read.get("records")) object(row);
        for (String field : IDS.subList(0, 3)) {
            if (!execution && !field.equals("scheme_instance_id")) NativeCharacterId.fromJson(read.get(field));
            else integer(read, field, 0, 0xffff_fffeL);
        }
        long generation = integer(read, "scheme_instance_id", 0, 0xffff_fffeL) >> 24;
        if (read.has("scheme_instance_generation")) require(integer(read, "scheme_instance_generation", 0, 255) == generation, "journal generation differs");
        read.put("scheme_instance_generation", generation); return read;
    }

    private static JsonNode retainedWrapper(JsonNode read, JsonNode original) {
        if (read == null || !bool(read, "available") || bool(read, "retention_gap") || !same(read, original)) return null;
        JsonNode records = read.get("records");
        for (int index = records.size() - 1; index >= 0; index--) {
            JsonNode row = records.get(index); if (!same(row, original) || !row.has("native_invocation")) continue;
            JsonNode invocation = M6CausalSources.endInvocation(row.get("native_invocation"), row);
            if (!M6CausalSources.terminalTransition(row, original) || !bool(invocation, "post_frame_observed")) continue;
            ObjectNode result = StrictJson.object(); result.put("native_status_raw", 1); result.put("native_status_key", "terminated_unattributed");
            result.put("native_terminal_state_observed", true); result.put("terminal_cause_observed", false);
            result.put("source_kind", "copied_retained_end_original_return"); result.set("copied_termination_record", row);
            result.set("source_read", sourceRead(read, false)); return result;
        }
        return null;
    }
    private static JsonNode material(JsonNode opinion, JsonNode completion, JsonNode original) {
        actual4(opinion); textEquals(opinion, "schema", "xar.ck3.sway-outcome-opinion-v1");
        if (!bool(opinion, "available") || completion == null) return null;
        for (String field : List.of("actor_character_id", "target_character_id", "date_raw", "snapshot_revision")) {
            JsonNode expected = field.endsWith("character_id") ? original.get(field) : completion.get(field);
            if (!exactIntegerEquals(opinion.get(field), expected)) return null;
        }
        named(opinion.get("scheme_sway_opinion")); named(opinion.get("sway_blocker_opinion"));
        JsonNode sway = opinion.get("scheme_sway_opinion"), blocker = opinion.get("sway_blocker_opinion");
        ObjectNode output = ((ObjectNode) original).deepCopy(); output.put("source_kind", "copied_native_named_opinion_same_completion_frame");
        output.set("source_snapshot_revision", opinion.get("snapshot_revision")); output.set("source_date_raw", opinion.get("date_raw"));
        output.set("scheme_sway_opinion", sway); output.set("sway_blocker_opinion", blocker);
        if (!bool(sway, "observed")) output.putNull("dedicated_benefit_observed");
        else output.put("dedicated_benefit_observed", bool(sway, "present") && signed(sway, "value") > 0);
        if (!bool(blocker, "observed")) output.putNull("dedicated_setback_observed"); else output.put("dedicated_setback_observed", bool(blocker, "present"));
        output.putNull("incremental_named_gain_observed"); output.put("terminal_cause_observed", false); output.set("copied_opinion_read", opinion); return output;
    }

    static G2M6Contracts.NamedValue named(JsonNode value) {
        StrictJson.object(value, Set.of("observed", "present", "value")); boolean observed = bool(value, "observed"), present = bool(value, "present");
        require(!present || observed, "present modifier was not observed");
        Optional<BigInteger> points = present ? Optional.of(BigInteger.valueOf(signed(value, "value"))) : Optional.empty();
        require(present || value.get("value").isNull(), "absent modifier value must be null"); return new G2M6Contracts.NamedValue(observed, present, points);
    }
    static ObjectNode sourceRead(JsonNode read, boolean nullable) {
        ObjectNode source = StrictJson.object(); JsonNode revision = read.has("source_snapshot_revision") ? read.get("source_snapshot_revision") : read.get("snapshot_revision");
        JsonNode date = read.has("source_date_raw") ? read.get("source_date_raw") : read.get("date_raw");
        boolean validRevision = revision != null && revision.isIntegralNumber() && revision.bigIntegerValue().signum() > 0 && revision.bigIntegerValue().compareTo(StrictJson.UINT64_MAX) <= 0;
        boolean validDate = date != null && date.isIntegralNumber() && date.canConvertToInt();
        if (nullable) { nullable(source, "snapshot_revision", validRevision ? revision : null); nullable(source, "date_raw", validDate ? date : null); }
        else { nullable(source, "snapshot_revision", revision); nullable(source, "date_raw", date); }
        source.put("exact_ck3_build", read.has("build_version") ? text(read, "build_version") : text(read, "exact_ck3_build"));
        source.put("exe_sha256", read.has("executable_sha256") ? text(read, "executable_sha256") : text(read, "exe_sha256")); return source;
    }
    static ObjectNode identityJson(Identity identity) {
        ObjectNode value = StrictJson.object(); value.put("action_id", identity.actionId()); value.put("actor_character_id", identity.actorCharacterId());
        value.put("target_character_id", identity.targetCharacterId()); value.put("scheme_instance_id", identity.schemeInstanceId()); value.put("scheme_instance_generation", identity.schemeInstanceGeneration()); return value;
    }
    static boolean same(JsonNode value, JsonNode original) { return value != null && value.isObject() && IDS.stream().allMatch(field -> exactIntegerEquals(value.get(field), original.get(field))); }
    static boolean exactIntegerEquals(JsonNode left, JsonNode right) { return left != null && right != null && left.isIntegralNumber() && right.isIntegralNumber() && left.bigIntegerValue().equals(right.bigIntegerValue()); }
    static void actual4(JsonNode value) {
        object(value); String build = value.has("build_version") ? text(value, "build_version") : text(value, "exact_ck3_build");
        String sha = value.has("executable_sha256") ? text(value, "executable_sha256") : text(value, "exe_sha256");
        require(BUILD.equals(build) && EXE.equalsIgnoreCase(sha), "exact 1.20.0.4 copied source required");
        if (value.has("exact_ck3_build")) textEquals(value, "exact_ck3_build", build);
        if (value.has("exe_sha256")) textEquals(value, "exe_sha256", sha);
    }
    static JsonNode parse(ProjectionJson value) { return StrictJson.parse(value.bytes(), MAX); }
    static ProjectionJson json(JsonNode value) { return ProjectionJson.object(StrictJson.canonical(value, MAX), MAX); }
    static Optional<ProjectionJson> optionalJson(JsonNode value) { return value == null ? Optional.empty() : Optional.of(json(value)); }
    static Optional<RetainedEnd> end(JsonNode value, EndSource source) { return value == null ? Optional.empty() : Optional.of(new RetainedEnd(source, json(value))); }
    static void nullable(ObjectNode value, String field, JsonNode node) { if (node == null || node.isNull()) value.putNull(field); else value.set(field, node); }
    static long integer(JsonNode value, String field, long min, long max) { object(value); return StrictJson.integer(value.get(field), min, max); }
    static BigInteger u64(JsonNode value, String field, long min) { object(value); return StrictJson.integer(value.get(field), BigInteger.valueOf(min), StrictJson.UINT64_MAX); }
    static int signed(JsonNode value, String field) { return Math.toIntExact(integer(value, field, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    static String text(JsonNode value, String field) { object(value); return StrictJson.text(value.get(field)); }
    static void textEquals(JsonNode value, String field, String expected) { require(text(value, field).equals(expected), field + " differs"); }
    static boolean bool(JsonNode value, String field) { object(value); JsonNode node = value.get(field); require(node != null && node.isBoolean(), "exact boolean required: " + field); return node.booleanValue(); }
    static void object(JsonNode value) { require(value != null && value.isObject(), "source object required"); }
    static void array(JsonNode value) { require(value != null && value.isArray() && value.size() <= 4096, "finite source records required"); }
}

