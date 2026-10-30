package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Exact current native producers. Raw uint64 native numbers stay BigInteger until explicit JSON encoding. */
public final class SwayNativeWire {
    public static final String BUILD = "1.20.0.4";
    public static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final String TARGET = "query-active-scheme-sway-target-v1-private-";
    public static final String START = "submit-active-scheme-sway-v1-private-";
    public static final String RECEIPT = "receipt-active-scheme-sway-v1-private-";
    public static final String STOP = "stop-active-scheme-sway-v1-private";
    public static final int MAX = 1_048_576;
    private static final Set<String> TARGET_FIELDS = Set.of("schema", "snapshot_revision", "capture_epoch", "container_generation",
            "date_raw", "actor_character_id", "target_character_id", "target_opinion_of_actor", "active_scheme_count",
            "matching_sway_active", "native_complete_can_send", "native_legal_now", "native_failure_classification", "active_sway_instances");
    private SwayNativeWire() { }

    /** Created only from the root's admitted full read/action guard. Construction is not qualification. */
    public record Binding(ObservationIdentity before, String sessionId, BigInteger connectionGeneration,
            String authorityId, String exactBuild, String exeSha256) {
        public Binding {
            Objects.requireNonNull(before); StrictJson.text(sessionId); StrictJson.text(authorityId);
            u64(connectionGeneration, 1); require(BUILD.equals(exactBuild) && EXE.equalsIgnoreCase(exeSha256), "current admitted Sway build pair required");
        }
        public long actor() { return before.frame().identity().player().longValueExact(); }
        public int date() { return before.frame().identity().dateRaw().intValueExact(); }
        public BigInteger revision() { return before.frame().identity().nativeRevision(); }
        public boolean sameEpisode(Binding other) {
            return before.machineId().equals(other.before.machineId())
                    && before.frame().episodeRunId().equals(other.before.frame().episodeRunId()) && actor() == other.actor()
                    && exactBuild.equals(other.exactBuild) && exeSha256.equalsIgnoreCase(other.exeSha256);
        }
        public boolean sameSession(Binding other) {
            return sameEpisode(other) && before.game().equals(other.before.game()) && sessionId.equals(other.sessionId)
                    && connectionGeneration.equals(other.connectionGeneration) && authorityId.equals(other.authorityId);
        }
    }
    public record Instance(long fullId, int generation, long target, int progress, int progressGoal, boolean exposed, boolean frozen) {
        public Instance {
            instance(fullId, generation); actionCharacter(target); require(progress >= 0 && progressGoal > 0 && progress <= progressGoal, "Sway progress interval");
        }
    }
    public record TargetRead(Binding binding, BigInteger captureEpoch, BigInteger containerGeneration, long target,
            int targetOpinion, int activeCount, boolean matching, boolean canSend, boolean legal, String failure,
            List<Instance> instances, ProjectionJson body) {
        public TargetRead {
            Objects.requireNonNull(binding); u64(captureEpoch, 1); u64(containerGeneration, 1); actionCharacter(target);
            require(binding.actor() != target, "Sway actor differs from target"); require(targetOpinion >= -100 && targetOpinion <= 100, "Sway opinion range");
            require(activeCount >= 0 && activeCount <= 32, "native scheme count range"); instances = List.copyOf(instances);
            require(instances.size() <= activeCount && matching == instances.stream().anyMatch(row -> row.target() == target), "matching Sway rows differ");
            require(!legal || !matching && canSend, "legal Sway requires complete validator and no matching row");
            require(failure.equals("") || failure.equals("native_complete_validator_rejected"), "native failure classification"); Objects.requireNonNull(body);
        }
        public boolean startable(boolean clearMandatoryContext) { return clearMandatoryContext && targetOpinion <= 50 && activeCount == 0 && !matching && canSend && legal; }
        @Override public boolean equals(Object other) { return other instanceof TargetRead row && binding.equals(row.binding) && captureEpoch.equals(row.captureEpoch) && containerGeneration.equals(row.containerGeneration) && target == row.target && targetOpinion == row.targetOpinion && activeCount == row.activeCount && matching == row.matching && canSend == row.canSend && legal == row.legal && failure.equals(row.failure) && instances.equals(row.instances) && java.util.Arrays.equals(body.bytes(), row.body.bytes()); }
        @Override public int hashCode() { return Objects.hash(binding, captureEpoch, containerGeneration, target, targetOpinion, activeCount, matching, canSend, legal, failure, instances, java.util.Arrays.hashCode(body.bytes())); }
    }
    public record StartAck(String actionId, long actor, long target, BigInteger preCaptureEpoch,
            BigInteger preContainerGeneration, int preDateRaw, ProjectionJson body) {
        public StartAck { action(actionId, false); actionCharacter(actor); actionCharacter(target); u64(preCaptureEpoch, 1); u64(preContainerGeneration, 1); Objects.requireNonNull(body); }
        public boolean applied() { return false; }
        @Override public boolean equals(Object other) { return other instanceof StartAck row && actionId.equals(row.actionId) && actor == row.actor && target == row.target && preCaptureEpoch.equals(row.preCaptureEpoch) && preContainerGeneration.equals(row.preContainerGeneration) && preDateRaw == row.preDateRaw && java.util.Arrays.equals(body.bytes(), row.body.bytes()); }
        @Override public int hashCode() { return Objects.hash(actionId, actor, target, preCaptureEpoch, preContainerGeneration, preDateRaw, java.util.Arrays.hashCode(body.bytes())); }
    }
    public record AppliedReceipt(Binding binding, String actionId, BigInteger postCaptureEpoch,
            BigInteger postContainerGeneration, int postDateRaw, long fullId, int generation, ProjectionJson body) {
        public AppliedReceipt {
            Objects.requireNonNull(binding); action(actionId, false); u64(postCaptureEpoch, 1); u64(postContainerGeneration, 1);
            instance(fullId, generation); Objects.requireNonNull(body);
        }
        @Override public boolean equals(Object other) { return other instanceof AppliedReceipt row && binding.equals(row.binding) && actionId.equals(row.actionId) && postCaptureEpoch.equals(row.postCaptureEpoch) && postContainerGeneration.equals(row.postContainerGeneration) && postDateRaw == row.postDateRaw && fullId == row.fullId && generation == row.generation && java.util.Arrays.equals(body.bytes(), row.body.bytes()); }
        @Override public int hashCode() { return Objects.hash(binding, actionId, postCaptureEpoch, postContainerGeneration, postDateRaw, fullId, generation, java.util.Arrays.hashCode(body.bytes())); }
    }
    public record StopAck(String actionId, long actor, long target, long fullId, int generation, ProjectionJson body) {
        public StopAck { action(actionId, true); currentCharacter(actor); currentCharacter(target); instance(fullId, generation); Objects.requireNonNull(body); }
        public boolean terminalObserved() { return false; }
        @Override public boolean equals(Object other) { return other instanceof StopAck row && actionId.equals(row.actionId) && actor == row.actor && target == row.target && fullId == row.fullId && generation == row.generation && java.util.Arrays.equals(body.bytes(), row.body.bytes()); }
        @Override public int hashCode() { return Objects.hash(actionId, actor, target, fullId, generation, java.util.Arrays.hashCode(body.bytes())); }
    }

    public static TargetRead target(byte[] rawFrame, String requestId, Binding binding, long target) {
        actionCharacter(target); ObjectNode row = envelope(rawFrame, requestId, TARGET + target, "available", "active_scheme_sway", true, false);
        StrictJson.object(row, TARGET_FIELDS); equals(row, "schema", "active-scheme-sway-private-read-v1"); frame(row, binding, target);
        JsonNode entries = row.get("active_sway_instances"); require(entries.isArray() && entries.size() <= 32, "bounded active Sway rows");
        List<Instance> instances = new ArrayList<>(); Set<Long> identities = new HashSet<>();
        for (JsonNode value : entries) {
            StrictJson.object(value, Set.of("scheme_instance_id", "scheme_instance_generation", "target_character_id", "progress", "progress_goal", "is_exposed", "is_frozen"));
            long id = integer(value, "scheme_instance_id", 0, 0xffff_fffeL); require(identities.add(id), "duplicate full Sway instance");
            instances.add(new Instance(id, Math.toIntExact(integer(value, "scheme_instance_generation", 0, 255)), actionCharacter(value, "target_character_id"),
                    Math.toIntExact(integer(value, "progress", 0, Integer.MAX_VALUE)), Math.toIntExact(integer(value, "progress_goal", 1, Integer.MAX_VALUE)), bool(value, "is_exposed"), bool(value, "is_frozen")));
        }
        return new TargetRead(binding, wide(row, "capture_epoch", 1), wide(row, "container_generation", 1), target,
                Math.toIntExact(integer(row, "target_opinion_of_actor", -100, 100)), Math.toIntExact(integer(row, "active_scheme_count", 0, 32)),
                bool(row, "matching_sway_active"), bool(row, "native_complete_can_send"), bool(row, "native_legal_now"), string(row, "native_failure_classification"), instances, json(row));
    }
    public static StartAck startAck(byte[] rawFrame, String requestId, String actionId, TargetRead before) {
        ObjectNode row = envelope(rawFrame, requestId, START + before.target(), "submitted_verification_pending", "active_scheme_sway_formal", false, false);
        StrictJson.object(row, Set.of("schema", "stage", "action_id", "actor_character_id", "target_character_id", "pre_capture_epoch", "pre_container_generation", "pre_date_raw", "submit_call_count", "receipt_pending"));
        equals(row, "schema", "active-scheme-sway-formal-private-v1"); equals(row, "stage", "submitted_verification_pending"); equals(row, "action_id", actionId);
        require(actionCharacter(row, "actor_character_id") == before.binding().actor() && actionCharacter(row, "target_character_id") == before.target(), "Sway Start ACK actor/target drift");
        BigInteger epoch = wide(row, "pre_capture_epoch", 1), generation = wide(row, "pre_container_generation", 1);
        require(epoch.compareTo(before.captureEpoch()) > 0 && generation.equals(before.containerGeneration()) && signed(row, "pre_date_raw") == before.binding().date(), "Sway Start ACK lost source read");
        require(integer(row, "submit_call_count", 1, 1) == 1 && bool(row, "receipt_pending"), "Sway Start ACK is pending once");
        return new StartAck(actionId, before.binding().actor(), before.target(), epoch, generation, before.binding().date(), json(row));
    }
    public static AppliedReceipt receipt(byte[] rawFrame, String requestId, Binding binding, String actionId, long target, BigInteger preCaptureEpoch) {
        ObjectNode row = envelope(rawFrame, requestId, RECEIPT + target, "applied", "active_scheme_sway_formal", false, false);
        StrictJson.object(row, Set.of("schema", "stage", "action_id", "post_capture_epoch", "post_container_generation", "post_date_raw", "scheme_instance_id", "scheme_instance_generation", "postcondition_verified"));
        equals(row, "schema", "active-scheme-sway-formal-private-v1"); equals(row, "stage", "applied"); equals(row, "action_id", actionId);
        require(bool(row, "postcondition_verified") && wide(row, "post_capture_epoch", 1).compareTo(preCaptureEpoch) > 0, "Sway receipt independent native epoch");
        require(signed(row, "post_date_raw") == binding.date(), "Sway receipt paused date changed");
        return new AppliedReceipt(binding, actionId, wide(row, "post_capture_epoch", 1), wide(row, "post_container_generation", 1), signed(row, "post_date_raw"),
                integer(row, "scheme_instance_id", 0, 0xffff_fffeL), Math.toIntExact(integer(row, "scheme_instance_generation", 0, 255)), json(row));
    }
    public static StopAck stopAck(byte[] rawFrame, String requestId, Binding binding, String actionId, long target, long fullId, int generation) {
        currentCharacter(binding.actor()); currentCharacter(target); instance(fullId, generation);
        ObjectNode row = envelope(rawFrame, requestId, STOP, "submitted_verification_pending", "sway_stop", false, true);
        StrictJson.object(row, Set.of("schema", "action_id", "status", "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation", "snapshot_revision", "date_raw", "exact_ck3_build", "exe_sha256", "submit_call_count", "postcondition_verified", "terminal_observed", "terminal_cause_observed", "terminal_cause"));
        equals(row, "schema", "xar.ck3.selected-sway-stop.v1"); equals(row, "action_id", actionId); equals(row, "status", "submitted_verification_pending");
        frame(row, binding, target); require(integer(row, "scheme_instance_id", 0, 0xffff_fffeL) == fullId && integer(row, "scheme_instance_generation", 0, 255) == generation, "Sway Stop exact instance drift");
        equals(row, "exact_ck3_build", BUILD); require(EXE.equalsIgnoreCase(string(row, "exe_sha256")), "Sway Stop executable drift");
        require(integer(row, "submit_call_count", 1, 1) == 1 && !bool(row, "postcondition_verified") && !bool(row, "terminal_observed") && !bool(row, "terminal_cause_observed"), "Sway Stop ACK cannot grant terminal");
        equals(row, "terminal_cause", "unknown"); return new StopAck(actionId, binding.actor(), target, fullId, generation, json(row));
    }

    static ObjectNode envelope(byte[] raw, String requestId, String step, String status, String payload, boolean readOnly, boolean stop) {
        ObjectNode packet = StrictJson.object(StrictJson.parse(raw, MAX), stop ? Set.of("type", "protocol_version", "request_id", "ok", "error", "result") : Set.of("type", "protocol_version", "request_id", "ok", "result"));
        equals(packet, "type", "command_result"); equals(packet, "request_id", requestId); integer(packet, "protocol_version", 1, 1); require(bool(packet, "ok"), "native Sway command RED");
        if (stop) require(string(packet, "error").isEmpty(), "native Stop ACK retained error");
        Set<String> fields = new HashSet<>(Set.of("step", "accepted", "status", "private_build", "advertised", "backend_id", payload));
        if (readOnly || stop) fields.add("read_only"); ObjectNode result = StrictJson.object(packet.get("result"), fields);
        equals(result, "step", step); equals(result, "status", status); equals(result, "backend_id", "native-headless");
        require(bool(result, "accepted") && bool(result, "private_build") && !bool(result, "advertised"), "private Sway envelope flags");
        if (readOnly || stop) require(bool(result, "read_only") == readOnly, "Sway read/write envelope differs");
        require(result.get(payload).isObject(), "Sway payload object required"); return (ObjectNode) result.get(payload);
    }
    static void frame(JsonNode row, Binding binding, long target) {
        require(wide(row, "snapshot_revision", 1).equals(binding.revision()) && signed(row, "date_raw") == binding.date()
                && actionCharacter(row, "actor_character_id") == binding.actor() && actionCharacter(row, "target_character_id") == target, "Sway native payload crossed complete actor/date/revision frame");
    }
    public static ObjectNode bindingJson(Binding value) {
        ObjectNode row = StrictJson.object(); row.set("before", ProposalLifecycleCodec.observation(value.before())); row.put("session_id", value.sessionId());
        row.put("connection_generation", value.connectionGeneration().toString()); row.put("authority_id", value.authorityId()); row.put("exact_build", value.exactBuild()); row.put("exe_sha256", value.exeSha256()); return row;
    }
    public static Binding binding(JsonNode value) {
        StrictJson.object(value, Set.of("before", "session_id", "connection_generation", "authority_id", "exact_build", "exe_sha256"));
        String generation = string(value, "connection_generation"); require(generation.matches("[1-9][0-9]*"), "canonical decimal connection generation");
        return new Binding(ProposalLifecycleCodec.decodeObservation(value.get("before")), string(value, "session_id"), new BigInteger(generation), string(value, "authority_id"), string(value, "exact_build"), string(value, "exe_sha256"));
    }
    static void instance(long fullId, int generation) { require(fullId >= 0 && fullId < 0xffff_ffffL && generation >= 0 && generation <= 255 && generation == fullId >>> 24, "full Sway instance/generation mismatch"); }
    static void actionCharacter(long value) { org.xar.ck3.control.contracts.NativeCharacterId.of(value); }
    static int actionCharacter(JsonNode row, String name) { return org.xar.ck3.control.contracts.NativeCharacterId.fromJson(row.get(name)).value(); }
    static void character(long value) { require(value > 0 && value <= 0xffff_ffffL, "full uint32 Sway character required"); }
    static void currentCharacter(long value) { require(value > 0 && value <= Integer.MAX_VALUE, "current native Sway entry requires positive int32 character"); }
    static void action(String value, boolean stop) { org.xar.ck3.control.contracts.NativeSwayActionId.require(value, stop ? org.xar.ck3.control.contracts.NativeSwayActionId.Kind.SELECTED_STOP : org.xar.ck3.control.contracts.NativeSwayActionId.Kind.START); }
    static void u64(BigInteger value, long min) { require(value != null && value.compareTo(BigInteger.valueOf(min)) >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "exact native uint64 range"); }
    static BigInteger wide(JsonNode row, String name, long min) { return StrictJson.integer(row.get(name), BigInteger.valueOf(min), StrictJson.UINT64_MAX); }
    static long integer(JsonNode row, String name, long min, long max) { return StrictJson.integer(row.get(name), min, max); }
    static int signed(JsonNode row, String name) { return Math.toIntExact(integer(row, name, Integer.MIN_VALUE, Integer.MAX_VALUE)); }
    static String string(JsonNode row, String name) { JsonNode value = row.get(name); require(value != null && value.isTextual(), "native string required: " + name); return value.textValue(); }
    static boolean bool(JsonNode row, String name) { JsonNode value = row.get(name); require(value != null && value.isBoolean(), "native boolean required: " + name); return value.booleanValue(); }
    static void equals(JsonNode row, String name, String expected) { require(string(row, name).equals(expected), "native field differs: " + name); }
    static ProjectionJson json(JsonNode value) { return ProjectionJson.object(StrictJson.canonical(value, MAX), MAX); }
}
