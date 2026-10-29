package org.xar.ck3.control.wave2.planning.swaymaterial;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete pure material stage/refresh/first-gain reducer and once-only following projection. */
public final class SwayMaterialReducer {
    private static final String BUILD = "1.20.0.4";
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final ObjectMapper WRITER = new ObjectMapper();
    private SwayMaterialReducer() { }
    public enum Transition { NEW_MATERIAL, REFRESHED, UNCHANGED }
    public enum Decision { RETAIN_EXISTING_SWAY, CONSUME_RETAINED_TERMINATION, OBSERVE_TRACKED_INSTANCE_END }
    public static final class Snapshot {
        private final byte[] raw;
        private Snapshot(JsonNode value) {
            require(value != null && value.isObject(), "snapshot object required");
            try {
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                try (JsonGenerator generator = WRITER.getFactory().createGenerator(output)) { token(value, generator); }
                raw = output.toByteArray();
            } catch (IOException error) { throw new ContractViolationException("JSON domain copy failed", error); }
            require(raw.length <= StrictJson.INPUT_MAX_BYTES, "snapshot exceeds finite byte budget");
        }
        public byte[] toJson() { return raw.clone(); }
    }
    public record StageResult(Transition transition, Snapshot material, Optional<Snapshot> updatedResolved,
            boolean firstNamedGainCreated) {
        public StageResult {
            Objects.requireNonNull(transition); Objects.requireNonNull(material); Objects.requireNonNull(updatedResolved);
            require((transition == Transition.UNCHANGED) == updatedResolved.isEmpty(), "write plan does not match actual change");
            require(!firstNamedGainCreated || transition == Transition.NEW_MATERIAL, "refresh must not replace the first named gain");
        }
        public boolean ledgerCommitted() { return false; }
        public boolean submissionAuthorized() { return false; }
    }
    private record Identity(String action, long actor, long target, long instance, int generation) { }
    private record NamedMeasurement(ObjectNode raw, BigInteger points) { }
    private record Opinion(ObjectNode raw, BigInteger revision, BigInteger date, String build, String sha,
            BigInteger totalOpinion, NamedMeasurement sway, NamedMeasurement blocker) { }
    private record Activity(boolean trackedActive, boolean currentTerminalObserved) { }

    /** Source is a census read or the original stored exact-instance completion; never a free GREEN flag. */
    public static StageResult stage(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("resolved", "opinion_read", "source"));
        ObjectNode resolved = object(input.get("resolved"));
        require(flag(resolved.get("postcondition_verified")), "original result is not verified");
        Identity identity = identity(resolved);
        Opinion opinion = opinion(input.get("opinion_read"), identity);
        ObjectNode source = object(input.get("source"));
        String kind = StrictJson.text(source.get("kind"));
        Activity activity;
        ObjectNode terminal = null;
        if (kind.equals("census")) {
            StrictJson.object(source, Set.of("kind", "sway_read"));
            ObjectNode census = object(source.get("sway_read"));
            text(census.get("schema"), "active-scheme-sway-private-read-v1");
            samePair(census, opinion, identity, "date_raw");
            JsonNode rows = census.get("active_sway_instances"); require(rows != null && rows.isArray(), "actual instance census required");
            boolean tracked = false;
            for (JsonNode row : rows) {
                if (!row.isObject()) { continue; }
                long instance = StrictJson.integer(row.get("scheme_instance_id"), 0, 0xffff_fffeL);
                long generation = StrictJson.integer(row.get("scheme_instance_generation"), 0, 255);
                long target = id(row.get("target_character_id"));
                tracked |= instance == identity.instance && generation == identity.generation && target == identity.target;
            }
            activity = new Activity(tracked, false);
        } else {
            require(kind.equals("completion"), "known material source kind required"); StrictJson.object(source, Set.of("kind"));
            ObjectNode completion = object(resolved.get("latest_instance_observation"));
            samePair(completion, opinion, identity, "source_date_raw");
            ObjectNode nativeObservation = object(completion.get("native_observation"));
            text(nativeObservation.get("schema"), "xar.ck3.sway_completion.v1"); require(flag(nativeObservation.get("available")), "completion source unavailable");
            samePair(nativeObservation, opinion, identity, "date_raw");
            require(StrictJson.integer(nativeObservation.get("scheme_instance_id"), 0, 0xffff_fffeL) == identity.instance
                    && StrictJson.integer(nativeObservation.get("scheme_instance_generation"), 0, 255) == identity.generation,
                    "completion original instance differs");
            boolean statusObserved = flag(nativeObservation.get("native_status_observed"));
            boolean tracked = flag(nativeObservation.get("exact_instance_join_ready"))
                    && flag(nativeObservation.get("owner_matches_actor")) && statusObserved
                    && integer(nativeObservation.get("native_status_raw")).equals(BigInteger.ZERO);
            boolean currentTerminal = flag(nativeObservation.get("native_terminal_state_observed"));
            require(flag(completion.get("tracked_instance_active")) == tracked
                    && flag(completion.get("instance_terminal_outcome_observed")) == currentTerminal,
                    "stored completion differs from its actual native projection");
            activity = new Activity(tracked, currentTerminal);
            JsonNode storedTerminal = resolved.get("terminal_intervention");
            if (storedTerminal != null && !storedTerminal.isNull()) { terminal = object(storedTerminal); }
        }
        return reduce(resolved, identity, opinion, activity, terminal);
    }

    private static StageResult reduce(ObjectNode resolved, Identity identity, Opinion opinion, Activity activity, ObjectNode terminal) {
        boolean ended = terminal != null && flag(terminal.get("instance_terminal_outcome_observed"));
        JsonNode previousValue = resolved.get("material_intervention");
        ObjectNode previous = previousValue != null && previousValue.isObject() ? (ObjectNode) previousValue : null;
        if (previous != null) {
            flag(previous.get("tracked_instance_active")); flag(previous.get("instance_terminal_outcome_observed"));
            flag(previous.get("next_turn_consumed")); integer(previous.get("source_native_revision")); integer(previous.get("source_date_raw"));
        }
        ObjectNode oldSway = previous != null && previous.path("scheme_sway_opinion").isObject()
                ? (ObjectNode) previous.get("scheme_sway_opinion") : null;
        Optional<BigInteger> oldPoints = optionalPoints(oldSway);
        boolean gain = previous != null && oldPoints.isPresent() && (activity.trackedActive || activity.currentTerminalObserved)
                && isTrue(previous.get("tracked_instance_active"))
                && opinion.date.compareTo(integer(previous.get("source_date_raw"))) > 0
                && opinion.sway.points.compareTo(oldPoints.orElseThrow()) > 0;
        boolean sameMaterial = previous != null && isBoolean(previous.get("tracked_instance_active"), activity.trackedActive)
                && isBoolean(previous.get("instance_terminal_outcome_observed"), ended)
                && opinion.sway.raw.equals(previous.get("scheme_sway_opinion"))
                && opinion.blocker.raw.equals(previous.get("sway_blocker_opinion"))
                && opinion.totalOpinion.equals(integer(previous.get("target_opinion_of_actor")));
        if (sameMaterial) {
            ObjectNode refreshed = previous.deepCopy(); provenance(refreshed, opinion);
            if (!opinion.revision.equals(integer(previous.get("source_native_revision")))
                    || !opinion.date.equals(integer(previous.get("source_date_raw")))) {
                refreshed.put("incremental_named_gain_observed", gain); refreshed.set("previous_scheme_sway_opinion", oldSway.deepCopy());
            }
            terminalMetadata(refreshed, terminal);
            if (refreshed.equals(previous)) { return new StageResult(Transition.UNCHANGED, new Snapshot(refreshed), Optional.empty(), false); }
            ObjectNode updated = resolved.deepCopy(); updated.set("material_intervention", refreshed);
            return new StageResult(Transition.REFRESHED, new Snapshot(refreshed), Optional.of(new Snapshot(updated)), false);
        }
        ObjectNode material = StrictJson.object();
        material.put("action_id", identity.action); material.put("actor_character_id", identity.actor); material.put("target_character_id", identity.target);
        material.put("scheme_instance_id", identity.instance); material.put("scheme_instance_generation", identity.generation); provenance(material, opinion);
        material.put("target_opinion_of_actor", opinion.totalOpinion); material.set("scheme_sway_opinion", opinion.sway.raw.deepCopy());
        material.set("sway_blocker_opinion", opinion.blocker.raw.deepCopy()); material.put("tracked_instance_active", activity.trackedActive);
        material.put("dedicated_benefit_observed", opinion.sway.points.signum() > 0);
        material.put("dedicated_setback_observed", opinion.blocker.points.signum() < 0); material.put("incremental_named_gain_observed", gain);
        if (oldSway == null) { material.putNull("previous_scheme_sway_opinion"); } else { material.set("previous_scheme_sway_opinion", oldSway.deepCopy()); }
        Decision decision = activity.trackedActive ? Decision.RETAIN_EXISTING_SWAY
                : ended ? Decision.CONSUME_RETAINED_TERMINATION : Decision.OBSERVE_TRACKED_INSTANCE_END;
        material.put("decision", decision.name().toLowerCase(Locale.ROOT)); material.put("instance_terminal_outcome_observed", ended);
        material.put("next_turn_consumed", false); terminalMetadata(material, terminal);
        ObjectNode updated = resolved.deepCopy(); updated.set("material_intervention", material);
        boolean firstGainCreated = gain && !resolved.has("first_named_gain_intervention");
        if (firstGainCreated) {
            ObjectNode first = material.deepCopy(); first.set("baseline_source_native_revision", previous.get("source_native_revision"));
            first.set("baseline_source_date_raw", previous.get("source_date_raw")); updated.set("first_named_gain_intervention", first);
        }
        return new StageResult(Transition.NEW_MATERIAL, new Snapshot(material), Optional.of(new Snapshot(updated)), firstGainCreated);
    }

    /** No read and no write: one eligible later real turn gets the original immutable material projection once. */
    public static Optional<Snapshot> following(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), Set.of("material", "actor_character_id", "native_revision", "date_raw"));
        JsonNode value = input.get("material");
        if (!value.isObject()) { return Optional.empty(); }
        ObjectNode material = (ObjectNode) value;
        long actor = id(input.get("actor_character_id")); BigInteger revision = integer(input.get("native_revision")), date = integer(input.get("date_raw"));
        if (flag(material.get("next_turn_consumed")) || id(material.get("actor_character_id")) != actor
                || (revision.compareTo(integer(material.get("source_native_revision"))) <= 0
                && date.compareTo(integer(material.get("source_date_raw"))) <= 0)) { return Optional.empty(); }
        ObjectNode consumed = material.deepCopy(); consumed.put("next_turn_consumed", true);
        consumed.put("following_native_revision", revision); consumed.put("following_date_raw", date); return Optional.of(new Snapshot(consumed));
    }

    private static Opinion opinion(JsonNode value, Identity identity) {
        ObjectNode row = object(value); text(row.get("schema"), "xar.ck3.sway-outcome-opinion-v1"); require(flag(row.get("available")), "opinion unavailable");
        require(id(row.get("actor_character_id")) == identity.actor && id(row.get("target_character_id")) == identity.target, "opinion original player pair differs");
        return new Opinion(row, integer(row.get("snapshot_revision")), integer(row.get("date_raw")), StrictJson.text(row.get("exact_ck3_build")),
                StrictJson.text(row.get("exe_sha256")), integer(row.get("target_opinion_of_actor")), measurement(row.get("scheme_sway_opinion")), measurement(row.get("sway_blocker_opinion")));
    }
    private static NamedMeasurement measurement(JsonNode value) {
        ObjectNode row = object(value); return new NamedMeasurement(row, optionalPoints(row).orElseThrow(() -> new ContractViolationException("named modifier not observed")));
    }
    private static Optional<BigInteger> optionalPoints(ObjectNode row) {
        if (row == null || !isTrue(row.get("observed"))) { return Optional.empty(); }
        JsonNode points = row.get("value");
        if (isBoolean(row.get("present"), false) && (points == null || points.isNull())) { return Optional.of(BigInteger.ZERO); }
        return isTrue(row.get("present")) && points != null && points.isIntegralNumber() ? Optional.of(points.bigIntegerValue()) : Optional.empty();
    }
    private static void samePair(ObjectNode row, Opinion opinion, Identity identity, String dateField) {
        require(id(row.get("actor_character_id")) == identity.actor && id(row.get("target_character_id")) == identity.target
                && integer(row.get(dateField)).equals(opinion.date), "material native read pair differs");
        text(row.get("exact_ck3_build"), opinion.build); text(row.get("exe_sha256"), opinion.sha);
    }
    private static Identity identity(ObjectNode resolved) {
        String action = StrictJson.text(resolved.get("action_id")); long actor = id(resolved.get("actor_character_id")), target = id(resolved.get("target_character_id"));
        require(actor != target, "original actor and target must differ");
        JsonNode receipt = resolved.get("native_receipt"), identity;
        if (receipt != null && receipt.isObject()) {
            identity = receipt;
            if (isText(receipt.get("exact_ck3_build"), BUILD) && !receipt.has("actor_character_id") && !receipt.has("target_character_id")) {
                text(resolved.get("status"), "applied"); text(receipt.get("schema"), "active-scheme-sway-formal-private-v1"); text(receipt.get("stage"), "applied");
                require(flag(receipt.get("postcondition_verified")), "receipt is unverified"); text(receipt.get("action_id"), action);
                require(StrictJson.text(receipt.get("exe_sha256")).toUpperCase(Locale.ROOT).equals(SHA), "projected receipt executable differs");
                BigInteger before = integer(resolved.get("pre_capture_epoch")), copied = integer(receipt.get("post_capture_epoch")), after = integer(resolved.get("post_capture_epoch"));
                require(before.signum() > 0 && before.compareTo(copied) < 0 && copied.compareTo(after) <= 0, "receipt epoch chain differs");
                BigInteger date = integer(receipt.get("post_date_raw")); require(date.signum() > 0 && date.equals(integer(resolved.get("post_date_raw"))), "receipt date differs");
                require(StrictJson.integer(receipt.get("scheme_instance_id"), 1, 0xffff_fffeL) > 0, "projected instance must be positive");
            }
        } else {
            require(receipt == null || receipt.isNull(), "malformed receipt cannot use recovered fallback"); identity = resolved.get("recovered_instance_observation"); object(identity);
            text(identity.get("schema"), "xar.ck3.sway-recovered-instance-observation.v1"); text(identity.get("source_kind"), "matching_active_readback_recovery");
            require(!flag(identity.get("submission_receipt_available")), "recovery must preserve absent original receipt"); text(identity.get("action_id"), action);
            require(id(identity.get("actor_character_id")) == actor && id(identity.get("target_character_id")) == target, "recovered pair differs");
            ObjectNode active = object(identity.get("active_instance")), source = object(identity.get("source_read"));
            require(integer(active.get("scheme_instance_id")).equals(integer(identity.get("scheme_instance_id")))
                    && integer(active.get("scheme_instance_generation")).equals(integer(identity.get("scheme_instance_generation")))
                    && id(active.get("target_character_id")) == target, "recovered active row differs");
            text(source.get("schema"), "active-scheme-sway-private-read-v1");
            for (String key : Set.of("exact_ck3_build", "exe_sha256", "queried_snapshot_id", "queried_revision", "queried_native_revision", "snapshot_revision", "date_raw", "capture_epoch", "container_generation", "post_snapshot_id")) {
                require(source.has(key), "recovered source field absent: " + key);
            }
        }
        long instance = StrictJson.integer(identity.get("scheme_instance_id"), 0, 0xffff_fffeL); int generation = Math.toIntExact(StrictJson.integer(identity.get("scheme_instance_generation"), 0, 255));
        require(generation == instance >> 24, "original full instance generation differs"); return new Identity(action, actor, target, instance, generation);
    }
    private static void provenance(ObjectNode row, Opinion opinion) {
        row.put("exact_ck3_build", opinion.build); row.put("exe_sha256", opinion.sha); row.put("source_native_revision", opinion.revision); row.put("source_date_raw", opinion.date);
    }
    private static void terminalMetadata(ObjectNode material, ObjectNode terminal) {
        if (terminal == null) { return; }
        material.put("completion_source_native_revision", integer(terminal.get("source_native_revision")));
        material.put("native_status_key", StrictJson.text(terminal.get("native_status_key")));
        material.put("terminal_cause_observed", flag(terminal.get("terminal_cause_observed")));
        material.put("terminal_cause", StrictJson.text(terminal.get("terminal_cause")));
    }
    private static void token(JsonNode value, JsonGenerator writer) throws IOException {
        if (value.isObject()) {
            writer.writeStartObject(); for (var field : value.properties()) { writer.writeFieldName(field.getKey()); token(field.getValue(), writer); } writer.writeEndObject();
        } else if (value.isArray()) {
            writer.writeStartArray(); for (JsonNode child : value) { token(child, writer); } writer.writeEndArray();
        } else if (value.isFloatingPointNumber()) {
            String raw = value.decimalValue().toString(); if (!raw.contains(".") && !raw.contains("E") && !raw.contains("e")) { raw += ".0"; } writer.writeNumber(raw);
        } else { writer.writeTree(value); }
    }
    private static ObjectNode object(JsonNode node) { require(node != null && node.isObject(), "actual object required"); return (ObjectNode) node; }
    private static long id(JsonNode node) { return StrictJson.integer(node, 1, 0xffff_ffffL); }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "actual integer token required"); return node.bigIntegerValue(); }
    private static boolean flag(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue(); }
    private static boolean isTrue(JsonNode node) { return isBoolean(node, true); }
    private static boolean isBoolean(JsonNode node, boolean value) { return node != null && node.isBoolean() && node.booleanValue() == value; }
    private static boolean isText(JsonNode node, String value) { return node != null && node.isTextual() && value.equals(node.textValue()); }
    private static void text(JsonNode node, String value) { require(isText(node, value), "source text differs"); }
    private static void require(boolean value, String reason) { StrictJson.require(value, reason); }
}
