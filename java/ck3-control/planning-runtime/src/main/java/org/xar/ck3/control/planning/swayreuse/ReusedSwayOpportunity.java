package org.xar.ck3.control.planning.swayreuse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure source-bound storage reuse observation. It never authorizes a submission. */
public final class ReusedSwayOpportunity {
    public static final String CK3_BUILD = "1.20.0.4";
    public static final String EXE_SHA256 =
            "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final BigInteger ZERO = BigInteger.ZERO;
    private static final BigInteger FULL_ID_MAX = BigInteger.valueOf(0xffff_fffeL);

    private ReusedSwayOpportunity() { }

    public enum TerminalCause { UNKNOWN }

    /** The old instance remains UNKNOWN. A new episode earns none of its old gain. */
    public record ObservationGap(String actionId, long actorCharacterId, long targetCharacterId,
            long schemeInstanceId, int schemeInstanceGeneration,
            BigInteger sourceNativeRevision, BigInteger sourceDateRaw, TerminalCause terminalCause) {
        public ObservationGap {
            StrictJson.text(actionId);
            requireFullId(actorCharacterId);
            requireFullId(targetCharacterId);
            requireFullId(schemeInstanceId);
            require(actorCharacterId != targetCharacterId, "actor and target must differ");
            require(schemeInstanceGeneration == schemeInstanceId >> 24, "generation differs from full instance");
            Objects.requireNonNull(sourceNativeRevision, "sourceNativeRevision");
            Objects.requireNonNull(sourceDateRaw, "sourceDateRaw");
            require(sourceNativeRevision.signum() > 0, "positive native revision required");
            require(terminalCause == TerminalCause.UNKNOWN, "reuse cannot invent terminal outcome");
        }

        public boolean storageSlotReused() { return true; }
        public boolean instanceTerminalOutcomeObserved() { return false; }
        public boolean submissionAuthorized() { return false; }
        public boolean previousGainCredited() { return false; }
    }

    private record InstanceIdentity(long fullId, int generation) { }

    /**
     * Outer request has exactly resolved, actor_character_id, date_raw. Existing
     * ledger/native containers remain extensible; only consumed fields are projected.
     * A malformed or unavailable legacy observation returns empty, matching None.
     */
    public static Optional<ObservationGap> decodeObservationGap(byte[] raw) {
        ObjectNode request = StrictJson.object(StrictJson.parse(raw),
                Set.of("resolved", "actor_character_id", "date_raw"));
        return observationGap(request.get("resolved"), request.get("actor_character_id"), request.get("date_raw"));
    }

    /**
     * Called only after the unchanged formal consumer's current frame join. The
     * result does not replace session/custody/material checks, should_submit_sway,
     * pending recovery, durable intent, a new UUID or independent postcondition.
     */
    public static Optional<ObservationGap> decodeFreshEmptySlot(byte[] raw) {
        ObjectNode request = StrictJson.object(StrictJson.parse(raw), Set.of("resolved", "readback"));
        JsonNode readback = request.get("readback");
        if (readback == null || !readback.isObject()) { return Optional.empty(); }
        Optional<ObservationGap> result = observationGap(request.get("resolved"),
                readback.get("actor_character_id"), readback.get("date_raw"));
        if (result.isEmpty()) { return result; }
        try {
            ObservationGap gap = result.orElseThrow();
            textEquals(readback.get("schema"), "active-scheme-sway-private-read-v1");
            require(exactInteger(readback.get("target_character_id")).equals(BigInteger.valueOf(gap.targetCharacterId())),
                    "fresh target differs from old target");
            require(exactInteger(readback.get("active_scheme_count")).equals(ZERO), "fresh slot must be empty");
            JsonNode instances = readback.get("active_sway_instances");
            require(instances != null && instances.isArray() && instances.isEmpty(), "actual empty instance list required");
            flag(readback.get("matching_sway_active"), false);
            flag(readback.get("native_complete_can_send"), true);
            flag(readback.get("native_legal_now"), true);
            exactBuild(readback);
            return result;
        } catch (ContractViolationException rejected) {
            return Optional.empty();
        }
    }

    /** Original flat Python JSON result domain; absence is encoded as JSON null. */
    public static byte[] encode(Optional<ObservationGap> value) {
        Objects.requireNonNull(value, "value");
        if (value.isEmpty()) { return new byte[] {'n', 'u', 'l', 'l'}; }
        ObservationGap gap = value.orElseThrow();
        ObjectNode row = StrictJson.object();
        row.put("action_id", gap.actionId());
        row.put("actor_character_id", gap.actorCharacterId());
        row.put("target_character_id", gap.targetCharacterId());
        row.put("scheme_instance_id", gap.schemeInstanceId());
        row.put("scheme_instance_generation", gap.schemeInstanceGeneration());
        row.put("source_native_revision", gap.sourceNativeRevision());
        row.put("source_date_raw", gap.sourceDateRaw());
        row.put("storage_slot_reused", true);
        row.put("instance_terminal_outcome_observed", false);
        row.put("terminal_cause", "unknown");
        return StrictJson.canonical(row);
    }

    /** Decode a persisted result, with no truthy defaults or hidden aliases. */
    public static Optional<ObservationGap> decodeResult(byte[] raw) {
        JsonNode parsed = StrictJson.parse(raw);
        if (parsed.isNull()) { return Optional.empty(); }
        ObjectNode row = StrictJson.object(parsed, Set.of("action_id", "actor_character_id",
                "target_character_id", "scheme_instance_id", "scheme_instance_generation",
                "source_native_revision", "source_date_raw", "storage_slot_reused",
                "instance_terminal_outcome_observed", "terminal_cause"));
        flag(row.get("storage_slot_reused"), true);
        flag(row.get("instance_terminal_outcome_observed"), false);
        textEquals(row.get("terminal_cause"), "unknown");
        return Optional.of(new ObservationGap(StrictJson.text(row.get("action_id")),
                fullId(row.get("actor_character_id")), fullId(row.get("target_character_id")),
                fullId(row.get("scheme_instance_id")),
                Math.toIntExact(StrictJson.integer(row.get("scheme_instance_generation"), 0, 255)),
                exactInteger(row.get("source_native_revision")), exactInteger(row.get("source_date_raw")),
                TerminalCause.UNKNOWN));
    }

    private static Optional<ObservationGap> observationGap(JsonNode resolved, JsonNode requestedActor, JsonNode requestedDate) {
        try {
            object(resolved);
            textEquals(resolved.get("status"), "applied");
            flag(resolved.get("postcondition_verified"), true);
            BigInteger actorInput = exactInteger(requestedActor);
            require(actorInput.equals(exactInteger(resolved.get("actor_character_id"))), "requested actor differs");
            BigInteger dateInput = exactInteger(requestedDate);
            JsonNode terminal = resolved.get("terminal_intervention");
            require(terminal == null || !terminal.isObject()
                    || !isBoolean(terminal.get("instance_terminal_outcome_observed"), true), "terminal already observed");
            InstanceIdentity identity = resolvedIdentity(resolved);
            String action = StrictJson.text(resolved.get("action_id"));
            long actor = fullId(resolved.get("actor_character_id"));
            long target = fullId(resolved.get("target_character_id"));
            require(actor != target, "actor and target must differ");
            JsonNode observation = resolved.get("latest_instance_observation");
            object(observation);
            BigInteger revision = exactInteger(observation.get("source_native_revision"));
            BigInteger date = exactInteger(observation.get("source_date_raw"));
            require(revision.signum() > 0 && date.compareTo(dateInput) <= 0, "observation is unavailable or in future");
            sameIdentity(observation, action, actor, target, identity, true);
            flag(observation.get("tracked_instance_active"), false);
            flag(observation.get("instance_terminal_outcome_observed"), false);
            JsonNode nativeObservation = observation.get("native_observation");
            object(nativeObservation);
            textEquals(nativeObservation.get("schema"), "xar.ck3.sway_completion.v1");
            flag(nativeObservation.get("available"), true);
            sameIdentity(nativeObservation, action, actor, target, identity, false);
            require(exactInteger(nativeObservation.get("snapshot_revision")).equals(revision), "native revision differs");
            require(exactInteger(nativeObservation.get("date_raw")).equals(date), "native date differs");
            flag(nativeObservation.get("instance_source_observed"), true);
            flag(nativeObservation.get("instance_present"), false);
            flag(nativeObservation.get("storage_slot_reused"), true);
            flag(nativeObservation.get("exact_instance_join_ready"), false);
            flag(nativeObservation.get("native_status_observed"), false);
            flag(nativeObservation.get("native_terminal_state_observed"), false);
            // Original get(None) accepts both missing and explicit null. No status
            // value is synthesized for either representation.
            JsonNode status = nativeObservation.get("native_status_raw");
            require(status == null || status.isNull(), "native status must remain unobserved");
            exactBuild(nativeObservation);
            exactBuild(observation);
            return Optional.of(new ObservationGap(action, actor, target, identity.fullId(), identity.generation(),
                    revision, date, TerminalCause.UNKNOWN));
        } catch (ContractViolationException rejected) {
            return Optional.empty();
        }
    }

    private static InstanceIdentity resolvedIdentity(JsonNode resolved) {
        JsonNode receipt = resolved.get("native_receipt");
        if (receipt != null && receipt.isObject()) {
            long instance = fullId(receipt.get("scheme_instance_id"));
            int generation = Math.toIntExact(StrictJson.integer(receipt.get("scheme_instance_generation"), 0, 255));
            require(generation == instance >> 24, "receipt generation differs");
            if (isText(receipt.get("exact_ck3_build"), CK3_BUILD)
                    && !receipt.has("actor_character_id") && !receipt.has("target_character_id")) {
                exactBuild(receipt);
                textEquals(receipt.get("schema"), "active-scheme-sway-formal-private-v1");
                textEquals(receipt.get("stage"), "applied");
                flag(receipt.get("postcondition_verified"), true);
                textEquals(receipt.get("action_id"), StrictJson.text(resolved.get("action_id")));
                BigInteger before = exactInteger(resolved.get("pre_capture_epoch"));
                BigInteger receiptPost = exactInteger(receipt.get("post_capture_epoch"));
                BigInteger post = exactInteger(resolved.get("post_capture_epoch"));
                require(before.signum() > 0 && before.compareTo(receiptPost) < 0
                        && receiptPost.compareTo(post) <= 0, "applied receipt epochs differ");
                BigInteger receiptDate = exactInteger(receipt.get("post_date_raw"));
                require(receiptDate.signum() > 0 && receiptDate.equals(exactInteger(resolved.get("post_date_raw"))),
                        "applied receipt date differs");
            }
            return new InstanceIdentity(instance, generation);
        }
        require(receipt == null || receipt.isNull(), "malformed native receipt cannot fall back to recovered identity");
        JsonNode recovered = resolved.get("recovered_instance_observation");
        object(recovered);
        textEquals(recovered.get("schema"), "xar.ck3.sway-recovered-instance-observation.v1");
        textEquals(recovered.get("source_kind"), "matching_active_readback_recovery");
        flag(recovered.get("submission_receipt_available"), false);
        String action = StrictJson.text(resolved.get("action_id"));
        long actor = fullId(resolved.get("actor_character_id"));
        long target = fullId(resolved.get("target_character_id"));
        long instance = fullId(recovered.get("scheme_instance_id"));
        int generation = Math.toIntExact(StrictJson.integer(recovered.get("scheme_instance_generation"), 0, 255));
        require(generation == instance >> 24, "recovered generation differs");
        InstanceIdentity identity = new InstanceIdentity(instance, generation);
        sameIdentity(recovered, action, actor, target, identity, true);
        JsonNode active = recovered.get("active_instance");
        object(active);
        require(fullId(active.get("scheme_instance_id")) == instance
                && StrictJson.integer(active.get("scheme_instance_generation"), 0, 255) == generation
                && fullId(active.get("target_character_id")) == target, "recovered active instance differs");
        JsonNode source = recovered.get("source_read");
        object(source);
        textEquals(source.get("schema"), "active-scheme-sway-private-read-v1");
        for (String field : Set.of("exact_ck3_build", "exe_sha256", "queried_snapshot_id", "queried_revision",
                "queried_native_revision", "snapshot_revision", "date_raw", "capture_epoch",
                "container_generation", "post_snapshot_id")) {
            require(source.has(field), "recovery read lacks " + field);
        }
        return identity;
    }

    private static void sameIdentity(JsonNode row, String action, long actor, long target,
            InstanceIdentity identity, boolean includeAction) {
        if (includeAction) { textEquals(row.get("action_id"), action); }
        require(fullId(row.get("actor_character_id")) == actor
                && fullId(row.get("target_character_id")) == target
                && fullId(row.get("scheme_instance_id")) == identity.fullId()
                && StrictJson.integer(row.get("scheme_instance_generation"), 0, 255) == identity.generation(),
                "source-bound identity differs");
    }

    private static void exactBuild(JsonNode row) {
        textEquals(row.get("exact_ck3_build"), CK3_BUILD);
        require(StrictJson.text(row.get("exe_sha256")).toUpperCase(Locale.ROOT).equals(EXE_SHA256), "exact native executable differs");
    }

    private static BigInteger exactInteger(JsonNode node) {
        require(node != null && node.isIntegralNumber(), "actual JSON integer required");
        return node.bigIntegerValue();
    }

    private static long fullId(JsonNode node) {
        return StrictJson.integer(node, BigInteger.ONE, FULL_ID_MAX).longValueExact();
    }

    private static void requireFullId(long value) {
        require(value > 0 && value <= 0xffff_fffeL, "full ID outside storage reuse domain");
    }

    private static void object(JsonNode row) { require(row != null && row.isObject(), "actual object required"); }
    private static boolean isText(JsonNode node, String text) { return node != null && node.isTextual() && text.equals(node.textValue()); }
    private static void textEquals(JsonNode node, String text) { require(isText(node, text), "source text differs"); }
    private static boolean isBoolean(JsonNode node, boolean value) { return node != null && node.isBoolean() && node.booleanValue() == value; }
    private static void flag(JsonNode node, boolean value) { require(isBoolean(node, value), "actual source boolean differs"); }
    private static void require(boolean condition, String reason) { StrictJson.require(condition, reason); }
}
