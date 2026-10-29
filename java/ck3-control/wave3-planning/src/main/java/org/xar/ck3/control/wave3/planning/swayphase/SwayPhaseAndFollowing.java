package org.xar.ck3.control.wave3.planning.swayphase;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Hidden-phase staging and original-episode following readiness; no writer, source replay or submitter. */
public final class SwayPhaseAndFollowing {
    private static final String SHA4 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final ObjectMapper WRITER = new ObjectMapper();
    private SwayPhaseAndFollowing() { }
    public enum StageTransition { NEW_PHASE, RETAINED_SAME_SOURCE }
    public enum PendingKind { ORIGINAL_START, FIRST_NAMED_GAIN, HIDDEN_PHASE, NAMED_MATERIAL, TERMINAL, VERIFIED_STOP }
    public enum Consumption { MISSING, NULL, UNCONSUMED, CONSUMED }
    public enum Branch { HIDDEN_PHASE_SUCCESS_SOURCE, HIDDEN_PHASE_FAILURE_SOURCE }
    public static final class Snapshot {
        private final byte[] raw;
        private Snapshot(JsonNode node) {
            require(node != null && node.isObject(), "immutable state object required");
            try {
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                try (JsonGenerator writer = WRITER.getFactory().createGenerator(output)) { token(node, writer); }
                raw = output.toByteArray();
            } catch (IOException error) { throw new ContractViolationException("state JSON copy failed", error); }
            require(raw.length <= StrictJson.INPUT_MAX_BYTES, "bounded state snapshot required");
        }
        public byte[] toJson() { return raw.clone(); }
    }
    public record StageResult(StageTransition transition, Snapshot phase, Optional<Snapshot> updatedResolved) {
        public StageResult {
            Objects.requireNonNull(transition); Objects.requireNonNull(phase); Objects.requireNonNull(updatedResolved);
            require(updatedResolved.isPresent() == (transition == StageTransition.NEW_PHASE), "phase write plan differs from transition");
        }
        public boolean writerCommitted() { return false; }
        public boolean materialEffectGranted() { return false; }
        public boolean terminalOutcomeGranted() { return false; }
    }
    public record PendingWork(int episodeIndex, PendingKind kind, Consumption consumption) {
        public PendingWork {
            require(episodeIndex >= 0, "episode index is nonnegative"); Objects.requireNonNull(kind); Objects.requireNonNull(consumption);
            require(consumption != Consumption.CONSUMED, "consumed work cannot be pending");
        }
    }
    public record PendingAssessment(List<PendingWork> work) {
        public PendingAssessment { work = List.copyOf(work); }
        public boolean pending() { return !work.isEmpty(); }
        public boolean snapshotTaken() { return false; }
        public boolean submissionAuthorized() { return false; }
    }
    private record Identity(String action, long actor, long target, long instance, int generation) { }
    private record Phase(Branch branch, BigInteger sequence, BigInteger date, JsonNode stockEvent, String outcome) { }

    /** Declared projection of the complete normalized execution read; last exact hidden phase wins. */
    public static Optional<StageResult> stage(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("resolved", "execution_read"));
        JsonNode readValue = input.get("execution_read"), resolvedValue = input.get("resolved");
        if (!readValue.isObject() || !resolvedValue.isObject()) { return Optional.empty(); }
        ObjectNode read = (ObjectNode) readValue, resolved = (ObjectNode) resolvedValue;
        if (!isText(read.get("schema"), "xar.ck3.sway-completion-execution.v1") || !isTrue(read.get("available"))) { return Optional.empty(); }
        JsonNode records = read.get("records"); require(records != null && records.isArray(), "execution records array required");
        if (records.isEmpty() || !isTrue(resolved.get("postcondition_verified"))) { return Optional.empty(); }
        Identity original = identity(resolved);
        if (id(read.get("actor_character_id")) != original.actor || id(read.get("target_character_id")) != original.target
                || StrictJson.integer(read.get("scheme_instance_id"), 0, 0xffff_fffeL) != original.instance) { return Optional.empty(); }
        Phase phase = null; BigInteger previousSequence = null;
        for (JsonNode row : records) {
            object(row);
            require(StrictJson.integer(row.get("scheme_instance_id"), 0, 0xffff_fffeL) == original.instance
                    && id(row.get("actor_character_id")) == original.actor && id(row.get("target_character_id")) == original.target,
                    "execution record is not the requested original instance");
            int generation = Math.toIntExact(StrictJson.integer(row.get("scheme_instance_generation"), 0, 255));
            if (generation != original.generation) { return Optional.empty(); }
            BigInteger sequence = uint64(row.get("sequence"));
            require(previousSequence == null || sequence.compareTo(previousSequence) > 0, "record sequence must preserve native order");
            previousSequence = sequence;
            Branch branch = switch (StrictJson.text(row.get("source_branch"))) {
                case "hidden_phase_success_source" -> Branch.HIDDEN_PHASE_SUCCESS_SOURCE;
                case "hidden_phase_failure_source" -> Branch.HIDDEN_PHASE_FAILURE_SOURCE;
                default -> throw new ContractViolationException("Service must filter the hidden-phase source before staging");
            };
            String outcome = StrictJson.text(row.get("phase_result"));
            require(outcome.equals(branch == Branch.HIDDEN_PHASE_SUCCESS_SOURCE ? "success" : "failure"), "phase outcome differs from source branch");
            require(flag(row.get("executing_input_observed")) && flag(row.get("exact_scope_join_ready"))
                    && !flag(row.get("material_effect_observed")) && !flag(row.get("native_terminal_state_observed")),
                    "hidden execution does not prove material or terminal effects");
            JsonNode event = row.get("stock_event"); require(event != null && (event.isNull() || event.isTextual()), "required nullable event string");
            phase = new Phase(branch, sequence, signedDate(row.get("date_raw")), event, outcome);
        }
        Phase observed = Objects.requireNonNull(phase);
        JsonNode previous = resolved.get("phase_intervention");
        if (previous != null && previous.isObject() && integer(previous.get("source_sequence")).equals(observed.sequence)
                && integer(previous.get("execution_date_raw")).equals(observed.date)
                && isText(previous.get("source_branch"), observed.branch.name().toLowerCase(Locale.ROOT))) {
            return Optional.of(new StageResult(StageTransition.RETAINED_SAME_SOURCE, new Snapshot(previous), Optional.empty()));
        }
        ObjectNode observation = StrictJson.object();
        observation.put("action_id", original.action); observation.put("actor_character_id", original.actor); observation.put("target_character_id", original.target);
        observation.put("scheme_instance_id", original.instance); observation.put("scheme_instance_generation", original.generation);
        observation.put("exact_ck3_build", StrictJson.text(read.get("exact_ck3_build"))); observation.put("exe_sha256", StrictJson.text(read.get("exe_sha256")));
        observation.put("source_native_revision", uint64(read.get("snapshot_revision"))); observation.put("source_date_raw", signedDate(read.get("date_raw")));
        observation.put("source_sequence", observed.sequence); observation.put("execution_date_raw", observed.date);
        observation.put("source_branch", observed.branch.name().toLowerCase(Locale.ROOT)); observation.set("stock_event", observed.stockEvent.deepCopy());
        observation.put("phase_result", observed.outcome); observation.put("executing_input_observed", true);
        observation.put("material_effect_observed", false); observation.put("native_terminal_state_observed", false);
        observation.set("native_observation", read.deepCopy()); observation.put("next_turn_consumed", false);
        ObjectNode updated = resolved.deepCopy(); updated.set("phase_intervention", observation);
        return Optional.of(new StageResult(StageTransition.NEW_PHASE, new Snapshot(observation), Optional.of(new Snapshot(updated))));
    }

    /** Pure replacement for the ledger fast gate. This schedules no snapshot, read or action. */
    public static PendingAssessment pending(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("resolved")); JsonNode value = input.get("resolved");
        if (value.isNull()) { return new PendingAssessment(List.of()); }
        ObjectNode resolved = object(value); List<ObjectNode> episodes = new ArrayList<>(); episodes.add(resolved);
        JsonNode history = resolved.get("previous_interventions");
        if (history != null) { require(history.isArray(), "episode history array required"); for (JsonNode episode : history) { episodes.add(object(episode)); } }
        List<PendingWork> work = new ArrayList<>();
        for (int index = 0; index < episodes.size(); index++) {
            ObjectNode episode = episodes.get(index);
            add(work, index, PendingKind.ORIGINAL_START, consumption(episode));
            JsonNode gain = episode.get("first_named_gain_intervention");
            if (gain != null && gain.isObject() && isTrue(gain.get("incremental_named_gain_observed"))) {
                Identity original = identity(episode);
                if (isText(gain.get("action_id"), original.action) && id(gain.get("actor_character_id")) == original.actor
                        && id(gain.get("target_character_id")) == original.target
                        && StrictJson.integer(gain.get("scheme_instance_id"), 0, 0xffff_fffeL) == original.instance
                        && StrictJson.integer(gain.get("scheme_instance_generation"), 0, 255) == original.generation) {
                    add(work, index, PendingKind.FIRST_NAMED_GAIN, consumption(gain));
                }
            }
            for (PendingKind kind : List.of(PendingKind.HIDDEN_PHASE, PendingKind.NAMED_MATERIAL, PendingKind.TERMINAL, PendingKind.VERIFIED_STOP)) {
                String key = switch (kind) { case HIDDEN_PHASE -> "phase_intervention"; case NAMED_MATERIAL -> "material_intervention";
                    case TERMINAL -> "terminal_intervention"; case VERIFIED_STOP -> "stop_intervention";
                    default -> throw new IllegalStateException("not an intervention kind"); };
                JsonNode row = episode.get(key);
                if (row != null && row.isObject() && (kind != PendingKind.VERIFIED_STOP || isTrue(row.get("postcondition_verified")))) {
                    add(work, index, kind, consumption(row));
                }
            }
        }
        return new PendingAssessment(work);
    }
    private static void add(List<PendingWork> work, int index, PendingKind kind, Consumption state) {
        if (state != Consumption.CONSUMED) { work.add(new PendingWork(index, kind, state)); }
    }
    private static Consumption consumption(JsonNode row) {
        JsonNode state = row.get("next_turn_consumed");
        if (state == null) { return Consumption.MISSING; } if (state.isNull()) { return Consumption.NULL; }
        return flag(state) ? Consumption.CONSUMED : Consumption.UNCONSUMED;
    }

    private static Identity identity(ObjectNode resolved) {
        String action = StrictJson.text(resolved.get("action_id")); long actor = id(resolved.get("actor_character_id")), target = id(resolved.get("target_character_id"));
        require(actor != target, "original actor and target differ"); JsonNode receipt = resolved.get("native_receipt"), identity;
        if (receipt != null && receipt.isObject()) {
            identity = receipt;
            if (isText(receipt.get("exact_ck3_build"), "1.20.0.4") && !receipt.has("actor_character_id") && !receipt.has("target_character_id")) {
                require(isTrue(resolved.get("postcondition_verified")) && isTrue(receipt.get("postcondition_verified")), "projected applied receipt must be verified");
                text(resolved.get("status"), "applied"); text(receipt.get("schema"), "active-scheme-sway-formal-private-v1"); text(receipt.get("stage"), "applied"); text(receipt.get("action_id"), action);
                require(StrictJson.text(receipt.get("exe_sha256")).toUpperCase(Locale.ROOT).equals(SHA4), "projected exact executable differs");
                BigInteger before = integer(resolved.get("pre_capture_epoch")), copied = integer(receipt.get("post_capture_epoch")), after = integer(resolved.get("post_capture_epoch"));
                require(before.signum() > 0 && before.compareTo(copied) < 0 && copied.compareTo(after) <= 0, "projected receipt epoch chain differs");
                BigInteger date = integer(receipt.get("post_date_raw")); require(date.signum() > 0 && date.equals(integer(resolved.get("post_date_raw"))), "projected receipt date differs");
                require(StrictJson.integer(receipt.get("scheme_instance_id"), 1, 0xffff_fffeL) > 0, "projected native receipt instance must be positive");
            }
        } else {
            require(receipt == null || receipt.isNull(), "malformed receipt cannot use recovery fallback"); identity = resolved.get("recovered_instance_observation"); object(identity);
            text(identity.get("schema"), "xar.ck3.sway-recovered-instance-observation.v1"); text(identity.get("source_kind"), "matching_active_readback_recovery");
            require(!flag(identity.get("submission_receipt_available")), "recovered observation must preserve unavailable receipt"); text(identity.get("action_id"), action);
            require(id(identity.get("actor_character_id")) == actor && id(identity.get("target_character_id")) == target, "recovered action pair differs");
            ObjectNode active = object(identity.get("active_instance")), source = object(identity.get("source_read"));
            require(integer(active.get("scheme_instance_id")).equals(integer(identity.get("scheme_instance_id")))
                    && integer(active.get("scheme_instance_generation")).equals(integer(identity.get("scheme_instance_generation"))) && id(active.get("target_character_id")) == target,
                    "recovered active row identity differs"); text(source.get("schema"), "active-scheme-sway-private-read-v1");
            for (String key : Set.of("exact_ck3_build", "exe_sha256", "queried_snapshot_id", "queried_revision", "queried_native_revision", "snapshot_revision", "date_raw", "capture_epoch", "container_generation", "post_snapshot_id")) {
                require(source.has(key), "recovered source field missing: " + key);
            }
        }
        long instance = StrictJson.integer(identity.get("scheme_instance_id"), 0, 0xffff_fffeL); int generation = Math.toIntExact(StrictJson.integer(identity.get("scheme_instance_generation"), 0, 255));
        require(generation == instance >> 24, "full instance generation differs"); return new Identity(action, actor, target, instance, generation);
    }
    private static void token(JsonNode node, JsonGenerator writer) throws IOException {
        if (node.isObject()) { writer.writeStartObject(); for (var field : node.properties()) { writer.writeFieldName(field.getKey()); token(field.getValue(), writer); } writer.writeEndObject(); }
        else if (node.isArray()) { writer.writeStartArray(); for (JsonNode child : node) { token(child, writer); } writer.writeEndArray(); }
        else if (node.isFloatingPointNumber()) {
            String raw = node.decimalValue().toString(); if (!raw.contains(".") && !raw.contains("E") && !raw.contains("e")) { raw += ".0"; } writer.writeNumber(raw);
        } else { writer.writeTree(node); }
    }
    private static BigInteger uint64(JsonNode node) { return StrictJson.integer(node, BigInteger.ZERO, StrictJson.UINT64_MAX); }
    private static BigInteger signedDate(JsonNode node) { return BigInteger.valueOf(StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "actual integer token required"); return node.bigIntegerValue(); }
    private static ObjectNode object(JsonNode node) { require(node != null && node.isObject(), "actual object required"); return (ObjectNode) node; }
    private static long id(JsonNode node) { return StrictJson.integer(node, 1, 0xffff_ffffL); }
    private static boolean flag(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue(); }
    private static boolean isTrue(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static boolean isText(JsonNode node, String value) { return node != null && node.isTextual() && value.equals(node.textValue()); }
    private static void text(JsonNode node, String value) { require(isText(node, value), "source text differs"); }
    private static void require(boolean value, String reason) { StrictJson.require(value, reason); }
}
