package org.xar.ck3.control.wave3.planning.swaystop;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Selected relation Finish policy and pending-only reconciliation; no UUID, writer or submitter. */
public final class SelectedSwayStop {
    private static final String BUILD = "1.20.0.4";
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final ObjectMapper WRITER = new ObjectMapper();
    private SelectedSwayStop() { }
    public enum Operation { START_PENDING_RECOVERY, OTHER_ACTOR_OR_TARGET, ALREADY_TERMINAL_OBSERVED,
        OBSERVE_ORIGINAL_STOP, RETAIN_EXISTING_SWAY, REQUIRE_NATIVE_STOP_ENTRY, PROPOSE_SELECTED_STOP }
    public enum NativeEntry { UNAVAILABLE, PRESENT_REQUIRES_ORIGINAL_QUALIFICATION }
    public record Episode(String originalActionId, long actor, long target, long instance, int generation) {
        public Episode {
            StrictJson.text(originalActionId); characterId(actor); characterId(target); require(actor != target, "actor and target differ");
            require(instance > 0 && instance < 0xffff_ffffL && generation == instance >> 24, "original instance/generation mismatch");
        }
    }
    public static final class Snapshot {
        private final byte[] raw;
        private Snapshot(JsonNode value) {
            require(value != null && value.isObject(), "state snapshot object required");
            try {
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                try (JsonGenerator writer = WRITER.getFactory().createGenerator(output)) { token(value, writer); }
                raw = output.toByteArray();
            } catch (IOException error) { throw new ContractViolationException("snapshot serialization failed", error); }
            require(raw.length <= StrictJson.INPUT_MAX_BYTES, "state snapshot exceeds finite budget");
        }
        public byte[] toJson() { return raw.clone(); }
    }
    public record Plan(Operation operation, Episode original, Optional<Snapshot> retainedStop) {
        public Plan {
            Objects.requireNonNull(operation); Objects.requireNonNull(original); Objects.requireNonNull(retainedStop);
            require(retainedStop.isPresent() == (operation == Operation.ALREADY_TERMINAL_OBSERVED || operation == Operation.OBSERVE_ORIGINAL_STOP),
                    "original Stop identity must be preserved on observation-only routes");
        }
        public boolean submissionAuthorized() { return false; }
        public boolean requestRetried() { return false; }
        public boolean newActionIdGenerated() { return false; }
    }
    public record PostconditionProjection(Snapshot stop, boolean originalInstanceTerminalObserved) {
        public PostconditionProjection { Objects.requireNonNull(stop); }
        public boolean nativeQualificationGranted() { return false; }
        public boolean writerCommitted() { return false; }
        public boolean submissionAuthorized() { return false; }
    }
    private record Frame(long actor, BigInteger revision, BigInteger nativeRevision, BigInteger date) { }
    private record TargetRead(boolean matching, BigInteger targetOpinion) { }

    /** Original relation objective only; this does not grant native Stop legality or permission. */
    public static boolean shouldFinish(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("snapshot", "readback", "resolved", "target_character_id", "opinion_read"));
        long target = id(input.get("target_character_id"));
        return shouldFinish(object(input.get("snapshot")), object(input.get("readback")), object(input.get("resolved")), target, input.get("opinion_read"));
    }

    private static boolean shouldFinish(ObjectNode snapshot, ObjectNode readback, ObjectNode resolved, long target, JsonNode opinion) {
        Frame frame = frame(snapshot, target); TargetRead read = read(readback, frame, target);
        if (!isTrue(resolved.get("postcondition_verified")) || id(resolved.get("actor_character_id")) != frame.actor
                || id(resolved.get("target_character_id")) != target) { return false; }
        JsonNode receipt = resolved.get("native_receipt"), instance = resolved.get("latest_instance_observation"), material = resolved.get("material_intervention");
        if (receipt == null || !receipt.isObject() || instance == null || !instance.isObject() || material == null || !material.isObject()) { return false; }
        long originalInstance = StrictJson.integer(receipt.get("scheme_instance_id"), 1, 0xffff_fffeL);
        long originalGeneration = StrictJson.integer(receipt.get("scheme_instance_generation"), 0, 255);
        require(originalGeneration == originalInstance >> 24, "original full instance generation differs");
        boolean currentPositive;
        if (opinion == null || opinion.isNull()) {
            currentPositive = integer(material.get("source_date_raw")).equals(frame.date) && isTrue(material.get("dedicated_benefit_observed"));
        } else {
            ObjectNode sample = object(opinion); JsonNode modifier = sample.get("scheme_sway_opinion");
            currentPositive = isTrue(sample.get("available")) && id(sample.get("actor_character_id")) == frame.actor
                    && id(sample.get("target_character_id")) == target && integer(sample.get("snapshot_revision")).equals(frame.nativeRevision)
                    && integer(sample.get("date_raw")).equals(frame.date) && integer(sample.get("target_opinion_of_actor")).equals(read.targetOpinion)
                    && modifier != null && modifier.isObject() && isTrue(modifier.get("observed")) && isTrue(modifier.get("present"))
                    && integer(modifier.get("value")).signum() > 0;
        }
        JsonNode nativeObservation = instance.get("native_observation");
        if (nativeObservation == null || !nativeObservation.isObject()) { return false; }
        return StrictJson.integer(instance.get("scheme_instance_id"), 1, 0xffff_fffeL) == originalInstance
                && StrictJson.integer(instance.get("scheme_instance_generation"), 0, 255) == originalGeneration
                && integer(instance.get("source_date_raw")).equals(frame.date)
                && isTrue(nativeObservation.get("exact_instance_join_ready")) && isTrue(nativeObservation.get("owner_matches_actor"))
                && id(nativeObservation.get("native_owner_raw")) == frame.actor && isTrue(nativeObservation.get("native_status_observed"))
                && integer(nativeObservation.get("native_status_raw")).equals(BigInteger.ZERO)
                && read.matching && read.targetOpinion.compareTo(BigInteger.valueOf(50)) > 0 && currentPositive;
    }

    /** Selected request routing. Existing start/Stop UNKNOWN is always recovery/observation only. */
    public static Plan plan(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("ledger", "snapshot", "selected_request", "readback", "opinion_read", "native_stop_entry"));
        ObjectNode ledger = StrictJson.object(input.get("ledger"), Set.of("schema", "pending", "resolved"));
        text(ledger.get("schema"), "xar.ck3.active-scheme-sway-formal-private.v1");
        ObjectNode request = StrictJson.object(input.get("selected_request"), Set.of("expected_revision", "target_character_id", "scheme_instance_id", "scheme_instance_generation"));
        long target = id(request.get("target_character_id")); ObjectNode snapshot = object(input.get("snapshot")); Frame frame = frame(snapshot, target);
        require(frame.revision.equals(integer(request.get("expected_revision"))), "selected request public revision is stale");
        ObjectNode resolved = object(ledger.get("resolved")), receipt = object(resolved.get("native_receipt"));
        long instance = StrictJson.integer(receipt.get("scheme_instance_id"), 1, 0xffff_fffeL);
        int generation = Math.toIntExact(StrictJson.integer(receipt.get("scheme_instance_generation"), 0, 255));
        require(instance == StrictJson.integer(request.get("scheme_instance_id"), 1, 0xffff_fffeL)
                && generation == StrictJson.integer(request.get("scheme_instance_generation"), 0, 255), "selected request differs from original episode");
        Episode episode = new Episode(StrictJson.text(resolved.get("action_id")), id(resolved.get("actor_character_id")),
                id(resolved.get("target_character_id")), instance, generation);
        JsonNode pending = ledger.get("pending");
        require(pending.isNull() || pending.isObject(), "pending must preserve null/object contract");
        if (!pending.isNull()) { return new Plan(Operation.START_PENDING_RECOVERY, episode, Optional.empty()); }
        if (episode.actor != frame.actor || episode.target != target) { return new Plan(Operation.OTHER_ACTOR_OR_TARGET, episode, Optional.empty()); }
        JsonNode previous = resolved.get("stop_intervention");
        if (previous != null && previous.isObject()) {
            return new Plan(isTrue(previous.get("postcondition_verified")) ? Operation.ALREADY_TERMINAL_OBSERVED : Operation.OBSERVE_ORIGINAL_STOP,
                    episode, Optional.of(new Snapshot(previous)));
        }
        if (!shouldFinish(snapshot, object(input.get("readback")), resolved, target, input.get("opinion_read"))) {
            return new Plan(Operation.RETAIN_EXISTING_SWAY, episode, Optional.empty());
        }
        NativeEntry entry = switch (StrictJson.text(input.get("native_stop_entry"))) {
            case "unavailable" -> NativeEntry.UNAVAILABLE;
            case "present_requires_original_qualification" -> NativeEntry.PRESENT_REQUIRES_ORIGINAL_QUALIFICATION;
            default -> throw new ContractViolationException("known native entry state required");
        };
        return new Plan(entry == NativeEntry.UNAVAILABLE ? Operation.REQUIRE_NATIVE_STOP_ENTRY : Operation.PROPOSE_SELECTED_STOP, episode, Optional.empty());
    }

    /** Projection of the independent original-instance read; ACK/disappearance never supplies terminal success. */
    public static PostconditionProjection reconcile(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("resolved", "stop", "snapshot", "completion_read"));
        ObjectNode resolved = object(input.get("resolved")), stop = object(input.get("stop")), completion = object(input.get("completion_read"));
        long target = id(resolved.get("target_character_id")); Frame frame = frame(object(input.get("snapshot")), target);
        require(frame.actor == id(resolved.get("actor_character_id")), "independent stop read belongs to another actor");
        ObjectNode receipt = object(resolved.get("native_receipt"));
        long instance = StrictJson.integer(receipt.get("scheme_instance_id"), 1, 0xffff_fffeL);
        long generation = StrictJson.integer(receipt.get("scheme_instance_generation"), 0, 255);
        StrictJson.text(stop.get("action_id")); text(stop.get("original_action_id"), StrictJson.text(resolved.get("action_id")));
        require(id(stop.get("actor_character_id")) == frame.actor && id(stop.get("target_character_id")) == target
                && StrictJson.integer(stop.get("scheme_instance_id"), 1, 0xffff_fffeL) == instance
                && StrictJson.integer(stop.get("scheme_instance_generation"), 0, 255) == generation, "independent read cannot settle another Stop intent");
        text(completion.get("schema"), "xar.ck3.sway_completion.v1");
        text(completion.get("exact_ck3_build"), BUILD);
        require(StrictJson.text(completion.get("exe_sha256")).equalsIgnoreCase(SHA), "independent Stop read exact executable differs");
        require(flag(completion.get("available")), "independent completion read unavailable");
        require(id(completion.get("actor_character_id")) == frame.actor && id(completion.get("target_character_id")) == target
                && StrictJson.integer(completion.get("scheme_instance_id"), 1, 0xffff_fffeL) == instance
                && StrictJson.integer(completion.get("scheme_instance_generation"), 0, 255) == generation
                && integer(completion.get("snapshot_revision")).equals(frame.nativeRevision)
                && integer(completion.get("date_raw")).equals(frame.date), "independent read source/identity drifted");
        boolean terminal = flag(completion.get("native_terminal_state_observed"));
        if (terminal) {
            require(flag(completion.get("instance_present")) && !flag(completion.get("storage_slot_reused"))
                    && flag(completion.get("exact_instance_join_ready")) && flag(completion.get("native_status_observed"))
                    && integer(completion.get("native_status_raw")).equals(BigInteger.ONE), "terminal flag lacks an exact retained status1 observation");
            long owner = id(completion.get("native_owner_raw"));
            require(owner == frame.actor || owner == 0xffff_ffffL, "terminal instance owner differs");
        }
        ObjectNode result = stop.deepCopy();
        result.put("status", terminal ? "terminal_observed_after_stop_request" : "stop_postcondition_pending");
        result.put("postcondition_verified", terminal); result.set("independent_instance_observation", completion.deepCopy());
        if (terminal) {
            result.set("source_native_revision", completion.get("snapshot_revision")); result.set("source_date_raw", completion.get("date_raw"));
            result.put("terminal_cause_observed", flag(completion.get("terminal_cause_observed")));
            result.put("terminal_cause", StrictJson.text(completion.get("terminal_cause"))); result.put("next_turn_consumed", false);
        }
        return new PostconditionProjection(new Snapshot(result), terminal);
    }

    private static Frame frame(ObjectNode snapshot, long target) {
        JsonNode played = snapshot.get("played_character"); long actor; boolean alive;
        if (played != null && played.isObject()) {
            actor = id(played.get("character_id")); alive = flag(played.get("alive"));
            if (snapshot.has("played_character_id")) { require(id(snapshot.get("played_character_id")) == actor, "player identity differs across frame views"); }
            if (snapshot.has("played_character_alive")) { require(flag(snapshot.get("played_character_alive")) == alive, "player alive differs across frame views"); }
        } else {
            require(played == null || played.isNull(), "played character has malformed shape");
            actor = id(snapshot.get("played_character_id")); alive = flag(snapshot.get("played_character_alive"));
        }
        BigInteger revision = integer(snapshot.get("revision")), nativeRevision = integer(snapshot.get("native_revision"));
        require(flag(snapshot.get("paused")) && flag(snapshot.get("map_ready")) && alive && actor != target
                && revision.signum() > 0 && nativeRevision.signum() > 0, "living player and paused map frame required");
        return new Frame(actor, revision, nativeRevision, integer(snapshot.get("date_raw")));
    }
    private static TargetRead read(ObjectNode readback, Frame frame, long target) {
        text(readback.get("schema"), "active-scheme-sway-private-read-v1");
        require(integer(readback.get("queried_revision")).equals(frame.revision)
                && integer(readback.get("queried_native_revision")).equals(frame.nativeRevision)
                && integer(readback.get("snapshot_revision")).equals(frame.nativeRevision)
                && integer(readback.get("date_raw")).equals(frame.date)
                && id(readback.get("actor_character_id")) == frame.actor && id(readback.get("target_character_id")) == target
                && integer(readback.get("capture_epoch")).signum() > 0 && integer(readback.get("container_generation")).signum() > 0,
                "target read differs from paused source frame");
        BigInteger opinion = BigInteger.valueOf(StrictJson.integer(readback.get("target_opinion_of_actor"), -100, 100));
        StrictJson.integer(readback.get("active_scheme_count"), 0, 32); flag(readback.get("native_legal_now"));
        return new TargetRead(flag(readback.get("matching_sway_active")), opinion);
    }
    private static void token(JsonNode node, JsonGenerator writer) throws IOException {
        if (node.isObject()) { writer.writeStartObject(); for (var field : node.properties()) { writer.writeFieldName(field.getKey()); token(field.getValue(), writer); } writer.writeEndObject(); }
        else if (node.isArray()) { writer.writeStartArray(); for (JsonNode item : node) { token(item, writer); } writer.writeEndArray(); }
        else if (node.isFloatingPointNumber()) {
            String value = node.decimalValue().toString(); if (!value.contains(".") && !value.contains("E") && !value.contains("e")) { value += ".0"; } writer.writeNumber(value);
        } else { writer.writeTree(node); }
    }
    private static ObjectNode object(JsonNode node) { require(node != null && node.isObject(), "actual object required"); return (ObjectNode) node; }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "actual integer token required"); return node.bigIntegerValue(); }
    private static long id(JsonNode node) { return StrictJson.integer(node, 1, 0xffff_ffffL); }
    private static void characterId(long value) { require(value > 0 && value <= 0xffff_ffffL, "full character ID required"); }
    private static boolean flag(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue(); }
    private static boolean isTrue(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static void text(JsonNode node, String value) { require(node != null && node.isTextual() && value.equals(node.textValue()), "source text differs"); }
    private static void require(boolean value, String reason) { StrictJson.require(value, reason); }
}
