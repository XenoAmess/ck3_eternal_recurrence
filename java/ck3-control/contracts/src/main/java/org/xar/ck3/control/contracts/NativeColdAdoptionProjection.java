package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;

/** Mechanical original-owner state projection. Data parsing never grants Native or original-writer authority. */
public record NativeColdAdoptionProjection(BindingState bindingState, OptionalLong sessionBridgePid,
        Optional<String> restoreKind, Optional<String> rejection, Optional<Candidate> pending, OriginalJson original) {
    public static final String SCHEMA = "xar.native.owner-cold-adoption.v1";
    public static final int MAX_BYTES = StrictJson.EXPLICIT_MAX_BYTES;
    private static final JsonFactory TOKENS = new JsonFactory();

    public enum BindingState {
        UNBOUND("unbound"), PENDING_COLD_CANDIDATE("pending_cold_candidate"), ACTIVE_RESUMED("active_resumed"),
        ACTIVE_NEW("active_new"), ACTIVE_OPERATOR_REBIND("active_operator_rebind"), BINDING_EPISODE_SEED("binding_episode_seed"),
        RELAUNCHING_EPISODE_SEED("relaunching_episode_seed"), ACTIVE_NATURAL_SUCCESSOR("active_natural_successor"), EPISODE_SEED_BLOCKED("episode_seed_blocked");
        private final String wire;
        BindingState(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static BindingState parse(String wire) {
            for (BindingState state : values()) { if (state.wire.equals(wire)) { return state; } }
            throw new IllegalArgumentException("unknown original owner binding state");
        }
    }
    public enum Presence { MISSING, NULL, VALUE }
    public NativeColdAdoptionProjection {
        Objects.requireNonNull(bindingState); Objects.requireNonNull(sessionBridgePid); Objects.requireNonNull(restoreKind);
        Objects.requireNonNull(rejection); Objects.requireNonNull(pending); Objects.requireNonNull(original);
        sessionBridgePid.ifPresent(NativeColdAdoptionProjection::pid);
        restoreKind.ifPresent(StrictJson::text); rejection.ifPresent(StrictJson::text);
        ObjectNode row = StrictJson.object(original.toJson(), Set.of("schema", "binding_state", "session_bridge_pid", "restore_kind", "rejection", "pending"));
        StrictJson.require(sameJson(row, projectionJson(bindingState, sessionBridgePid, restoreKind, rejection, pending)),
                "typed original-owner projection differs from its retained JSON");
    }
    /** Complete original JSON bytes; extra checkpoint fields remain available without exposing an untyped map. */
    public record OriginalJson(byte[] bytes) {
        public OriginalJson { bytes = bytes.clone(); JsonNode parsed = StrictJson.parse(bytes, MAX_BYTES); object(parsed); unicode(parsed); }
        @Override public byte[] bytes() { return bytes.clone(); }
        public ObjectNode toJson() { return object(StrictJson.parse(bytes, MAX_BYTES)).deepCopy(); }
        @Override public boolean equals(Object other) { return other instanceof OriginalJson value && Arrays.equals(bytes, value.bytes); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }
    }
    public record Lifecycle(String lifecycle, Optional<String> xarEnabled, String pactContract,
            String source, Optional<String> environmentSha256) {
        private static final String ORDINARY_VANILLA_PACT = "not_applicable_to_vanilla_configuration";
        private static final String ORDINARY_VANILLA_SOURCE = "ordinary_vanilla_configuration";
        /** Configured vanilla DATA; this does not assert that native mod absence was observed or verified. */
        public static Lifecycle ordinaryVanilla() {
            return new Lifecycle("ordinary_campaign_succession", Optional.empty(), ORDINARY_VANILLA_PACT, ORDINARY_VANILLA_SOURCE, Optional.empty());
        }
        public Lifecycle {
            StrictJson.require(Set.of("rogue_one_life", "ordinary_campaign_succession", "unknown").contains(lifecycle), "known original lifecycle");
            Objects.requireNonNull(xarEnabled); Objects.requireNonNull(environmentSha256); StrictJson.text(pactContract); StrictJson.text(source);
            xarEnabled.ifPresent(value -> StrictJson.require(Set.of("xar_on", "xar_off").contains(value), "original XAR enum"));
            environmentSha256.ifPresent(NativeColdAdoptionProjection::digest);
            boolean verifiedAbsence = lifecycle.equals("ordinary_campaign_succession") && xarEnabled.isEmpty()
                    && pactContract.equals("absent_by_verified_xar_mod_not_loaded") && source.equals("absent_by_verified_xar_mod_not_loaded");
            boolean ordinaryVanilla = lifecycle.equals("ordinary_campaign_succession") && xarEnabled.isEmpty()
                    && pactContract.equals(ORDINARY_VANILLA_PACT) && source.equals(ORDINARY_VANILLA_SOURCE) && environmentSha256.isEmpty();
            boolean expectedProfile = switch (lifecycle) {
                case "rogue_one_life" -> xarEnabled.equals(Optional.of("xar_on")) && pactContract.equals("terminal_settlement_required");
                case "ordinary_campaign_succession" -> xarEnabled.equals(Optional.of("xar_off")) && pactContract.equals("absent_by_fresh_campaign_xar_off_contract");
                case "unknown" -> xarEnabled.isEmpty() && pactContract.equals("unknown");
                default -> false;
            };
            StrictJson.require(expectedProfile || verifiedAbsence || ordinaryVanilla, "original lifecycle support profile is inconsistent");
            if (lifecycle.equals("ordinary_campaign_succession") && !ordinaryVanilla) {
                StrictJson.require(environmentSha256.isPresent(), "ordinary lifecycle requires frozen environment");
            }
        }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object().put("schema", "xar.ck3.succession-lifecycle-binding/v1").put("lifecycle", lifecycle)
                    .put("pact_contract", pactContract).put("source", source);
            if (xarEnabled.isPresent()) { value.put("xar_enabled", xarEnabled.orElseThrow()); } else { value.putNull("xar_enabled"); }
            if (environmentSha256.isPresent()) { value.put("environment_sha256", environmentSha256.orElseThrow()); } else { value.putNull("environment_sha256"); }
            return value;
        }
    }
    public record Checkpoint(String sha256, long size, long dateRaw, OptionalLong historyIndex,
            OptionalLong episodeCharacterId, Optional<String> episodeRunId, OriginalJson original) {
        public Checkpoint {
            digest(sha256); StrictJson.safe(size, 1); StrictJson.safe(dateRaw, 0);
            Objects.requireNonNull(historyIndex); Objects.requireNonNull(episodeCharacterId); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(original);
            historyIndex.ifPresent(value -> StrictJson.safe(value, 1)); episodeCharacterId.ifPresent(value -> StrictJson.safe(value, 0)); episodeRunId.ifPresent(StrictJson::text);
            ObjectNode row = original.toJson();
            StrictJson.require(sha256.equals(StrictJson.text(row.get("sha256")))
                    && size == StrictJson.integer(row.get("size"), 1, StrictJson.MAX_SAFE_INTEGER)
                    && dateRaw == StrictJson.integer(row.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER)
                    && historyIndex.equals(optionalInteger(row, "history_index", 1))
                    && episodeCharacterId.equals(optionalInteger(row, "episode_character_id", 0))
                    && episodeRunId.equals(row.has("episode_run_id") ? nullableText(row.get("episode_run_id")) : Optional.empty()),
                    "typed checkpoint differs from its complete retained JSON");
        }
        public ObjectNode toJson() { return original.toJson(); }
        public Presence historyIndexPresence() { return presence(original.toJson(), "history_index"); }
        public Presence episodeCharacterIdPresence() { return presence(original.toJson(), "episode_character_id"); }
        public Presence episodeRunIdPresence() { return presence(original.toJson(), "episode_run_id"); }
        public boolean sameOriginalIdentity(Checkpoint other) { return sha256.equals(other.sha256) && size == other.size && dateRaw == other.dateRaw; }
    }
    public record Anchor(long index, String command, boolean ok, Checkpoint checkpoint) {
        public Anchor { StrictJson.safe(index, 1); StrictJson.text(command); Objects.requireNonNull(checkpoint); }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object().put("index", index).put("command", command).put("ok", ok);
            value.set("result_checkpoint", checkpoint.toJson()); return value;
        }
    }
    public record Candidate(long formatVersion, long bridgePid, long episodeCharacterId, String episodeRunId,
            Lifecycle lifecycle, Checkpoint checkpoint, long commandHistoryLength, Optional<Anchor> anchor, boolean originalColdReady) {
        public Candidate {
            StrictJson.require(formatVersion == 2, "original full Driver format2"); pid(bridgePid); StrictJson.safe(episodeCharacterId, 0);
            StrictJson.text(episodeRunId); Objects.requireNonNull(lifecycle); Objects.requireNonNull(checkpoint); Objects.requireNonNull(anchor);
            StrictJson.safe(commandHistoryLength, 0);
        }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object().put("format_version", formatVersion).put("bridge_pid", bridgePid)
                    .put("episode_character_id", episodeCharacterId).put("episode_run_id", episodeRunId)
                    .put("command_history_length", commandHistoryLength).put("original_cold_ready", originalColdReady);
            value.set("succession_lifecycle", lifecycle.toJson()); value.set("last_checkpoint", checkpoint.toJson());
            if (anchor.isPresent()) { value.set("checkpoint_anchor", anchor.orElseThrow().toJson()); } else { value.putNull("checkpoint_anchor"); }
            return value;
        }
    }

    public static NativeColdAdoptionProjection parse(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "binding_state", "session_bridge_pid", "restore_kind", "rejection", "pending"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "original owner cold projection schema");
        Optional<Candidate> candidate = value.get("pending").isNull() ? Optional.empty() : Optional.of(candidate(token(raw, "pending")));
        return new NativeColdAdoptionProjection(BindingState.parse(StrictJson.text(value.get("binding_state"))),
                nullableInteger(value.get("session_bridge_pid"), 1, 0xffff_ffffL), nullableText(value.get("restore_kind")),
                nullableText(value.get("rejection")), candidate, new OriginalJson(raw));
    }
    public static NativeColdAdoptionProjection fromJson(JsonNode value) { return parse(value.toString().getBytes(StandardCharsets.UTF_8)); }
    public ObjectNode toJson() { return original.toJson(); }
    private static ObjectNode projectionJson(BindingState state, OptionalLong pid, Optional<String> kind,
            Optional<String> rejection, Optional<Candidate> candidate) {
        ObjectNode value = StrictJson.object().put("schema", SCHEMA).put("binding_state", state.wire());
        if (pid.isPresent()) { value.put("session_bridge_pid", pid.orElseThrow()); } else { value.putNull("session_bridge_pid"); }
        if (kind.isPresent()) { value.put("restore_kind", kind.orElseThrow()); } else { value.putNull("restore_kind"); }
        if (rejection.isPresent()) { value.put("rejection", rejection.orElseThrow()); } else { value.putNull("rejection"); }
        if (candidate.isPresent()) { value.set("pending", candidate.orElseThrow().toJson()); } else { value.putNull("pending"); }
        return value;
    }

    private static Candidate candidate(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("format_version", "bridge_pid", "episode_character_id", "episode_run_id",
                "succession_lifecycle", "last_checkpoint", "command_history_length", "checkpoint_anchor", "original_cold_ready"));
        Optional<Anchor> anchor = value.get("checkpoint_anchor").isNull() ? Optional.empty() : Optional.of(anchor(token(raw, "checkpoint_anchor")));
        return new Candidate(StrictJson.integer(value.get("format_version"), 2, 2), StrictJson.integer(value.get("bridge_pid"), 1, 0xffff_ffffL),
                StrictJson.integer(value.get("episode_character_id"), 0, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(value.get("episode_run_id")),
                lifecycle(value.get("succession_lifecycle")), checkpoint(token(raw, "last_checkpoint")),
                StrictJson.integer(value.get("command_history_length"), 0, StrictJson.MAX_SAFE_INTEGER), anchor, bool(value.get("original_cold_ready")));
    }
    private static Lifecycle lifecycle(JsonNode node) {
        ObjectNode value = StrictJson.object(node, Set.of("schema", "lifecycle", "xar_enabled", "pact_contract", "source", "environment_sha256"));
        StrictJson.require("xar.ck3.succession-lifecycle-binding/v1".equals(StrictJson.text(value.get("schema"))), "original lifecycle schema");
        return new Lifecycle(StrictJson.text(value.get("lifecycle")), nullableText(value.get("xar_enabled")), StrictJson.text(value.get("pact_contract")),
                StrictJson.text(value.get("source")), nullableText(value.get("environment_sha256")));
    }
    private static Checkpoint checkpoint(byte[] raw) {
        ObjectNode value = object(StrictJson.parse(raw, MAX_BYTES));
        // Original anchor results may predate attached episode/history fields; missing is retained in original, not synthesized.
        return new Checkpoint(StrictJson.text(value.get("sha256")), StrictJson.integer(value.get("size"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(value.get("date_raw"), 0, StrictJson.MAX_SAFE_INTEGER), optionalInteger(value, "history_index", 1),
                optionalInteger(value, "episode_character_id", 0), value.has("episode_run_id") ? nullableText(value.get("episode_run_id")) : Optional.empty(), new OriginalJson(raw));
    }
    private static Anchor anchor(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("index", "command", "ok", "result_checkpoint"));
        return new Anchor(StrictJson.integer(value.get("index"), 1, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(value.get("command")),
                bool(value.get("ok")), checkpoint(token(raw, "result_checkpoint")));
    }
    private static OptionalLong optionalInteger(ObjectNode value, String field, long minimum) {
        return value.has(field) ? nullableInteger(value.get(field), minimum, StrictJson.MAX_SAFE_INTEGER) : OptionalLong.empty();
    }
    private static Presence presence(ObjectNode value, String field) {
        return !value.has(field) ? Presence.MISSING : value.get(field).isNull() ? Presence.NULL : Presence.VALUE;
    }
    private static OptionalLong nullableInteger(JsonNode value, long minimum, long maximum) {
        Objects.requireNonNull(value, "required nullable integer field missing");
        return value.isNull() ? OptionalLong.empty() : OptionalLong.of(StrictJson.integer(value, minimum, maximum));
    }
    private static Optional<String> nullableText(JsonNode value) {
        Objects.requireNonNull(value, "required nullable text field missing"); return value.isNull() ? Optional.empty() : Optional.of(StrictJson.text(value));
    }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "exact projection boolean required"); return node.booleanValue(); }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "projection object required"); return (ObjectNode) node; }
    private static void pid(long value) { StrictJson.require(value > 0 && value <= 0xffff_ffffL, "actual uint32 process ID required"); }
    private static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA256 required"); }
    private static boolean sameJson(JsonNode left, JsonNode right) {
        if (left.isIntegralNumber() && right.isIntegralNumber()) { return left.bigIntegerValue().equals(right.bigIntegerValue()); }
        if (left.isObject() && right.isObject()) {
            if (left.size() != right.size()) { return false; }
            var fields = left.fieldNames();
            while (fields.hasNext()) { String field = fields.next(); if (!right.has(field) || !sameJson(left.get(field), right.get(field))) { return false; } }
            return true;
        }
        if (left.isArray() && right.isArray()) {
            if (left.size() != right.size()) { return false; }
            for (int i = 0; i < left.size(); i++) { if (!sameJson(left.get(i), right.get(i))) { return false; } } return true;
        }
        return left.equals(right);
    }
    private static void unicode(JsonNode node) {
        if (node.isTextual()) { unicode(node.textValue()); }
        if (node.isObject()) { node.fieldNames().forEachRemaining(NativeColdAdoptionProjection::unicode); }
        if (node.isContainerNode()) { for (JsonNode child : node) { unicode(child); } }
    }
    private static void unicode(String value) {
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (Character.isHighSurrogate(c)) {
                StrictJson.require(i + 1 < value.length() && Character.isLowSurrogate(value.charAt(i + 1)), "unpaired projection surrogate"); i++;
            } else { StrictJson.require(!Character.isLowSurrogate(c), "unpaired projection surrogate"); }
        }
    }
    private static byte[] token(byte[] raw, String field) {
        try (JsonParser parser = TOKENS.createParser(raw)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "projection source object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken(); long start = parser.currentTokenLocation().getByteOffset();
                parser.skipChildren(); parser.finishToken(); long end = parser.currentLocation().getByteOffset();
                if (name.equals(field)) { return Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end)); }
            }
        } catch (IOException failure) { throw new IllegalArgumentException("invalid original projection token", failure); }
        throw new IllegalArgumentException("required original projection token missing: " + field);
    }
}
