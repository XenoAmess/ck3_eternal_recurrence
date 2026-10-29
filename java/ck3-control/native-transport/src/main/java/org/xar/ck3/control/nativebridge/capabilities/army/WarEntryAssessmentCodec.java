package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Complete exact-build war-entry request, native power decomposition and same-frame target-scope contract. */
public final class WarEntryAssessmentCodec {
    public static final String CAPABILITY = "game.command.query-war-entry-assessments-v1-N";
    public static final String STEP_PREFIX = "query-war-entry-assessments-v1-";
    public static final String RESERVED_EVENT_SCOPE_CAPABILITY = "game.command.query-war-entry-assessments-raiktor-bookmark-saved-scope-v1";
    private static final List<String> RAW = List.of("distance_raw", "actor_power_base_raw", "actor_network_contribution_raw", "actor_power_total_raw",
            "target_power_base_raw", "target_network_contribution_raw", "target_pre_adjustment_total_raw", "target_adjustment_delta_raw", "target_power_total_raw", "actual_power_ratio_raw");
    private static final Set<String> READY = Set.of("actor_identity_ready", "targets_declarable_ready", "effective_targets_ready", "ai_context_ready", "native_output_ready", "network_decomposition_ready", "same_frame_ready", "ready");
    private WarEntryAssessmentCodec() { }
    public record Expected(List<Integer> targetCharacterIds, BigInteger actorCharacterId, BigInteger nativeRevision, BigInteger dateRaw) {
        public Expected {
            targetCharacterIds = targets(targetCharacterIds); positive32(actorCharacterId); nonnegative64(nativeRevision); signed32(dateRaw);
        }
    }
    public record Assessment(int targetCharacterId, int effectiveTargetCharacterId, long distanceRaw, long actorPowerBaseRaw,
            long actorNetworkContributionRaw, long actorPowerTotalRaw, long targetPowerBaseRaw, long targetNetworkContributionRaw,
            long targetPreAdjustmentTotalRaw, long targetAdjustmentDeltaRaw, long targetPowerTotalRaw, long actualPowerRatioRaw,
            int targetAiContextActorEntryRaw, int actorAiContextTargetEntryRaw, int nativeFlagsRaw) {
        public Assessment {
            require(targetCharacterId > 0 && effectiveTargetCharacterId > 0 && nativeFlagsRaw >= 0 && nativeFlagsRaw <= 255, "war-entry target/uint8 identity differs");
            require(distanceRaw >= 0 && actorPowerBaseRaw >= 0 && actorPowerTotalRaw >= 0 && targetPowerBaseRaw >= 0
                    && targetPreAdjustmentTotalRaw >= 0 && targetPowerTotalRaw >= 0 && actualPowerRatioRaw >= 0, "war-entry nonnegative native power operand differs");
            require(sum(actorPowerBaseRaw, actorNetworkContributionRaw) == actorPowerTotalRaw, "war-entry actor power decomposition differs");
            require(sum(targetPowerBaseRaw, targetNetworkContributionRaw) == targetPreAdjustmentTotalRaw, "war-entry target pre-adjustment decomposition differs");
            require(sum(targetPreAdjustmentTotalRaw, targetAdjustmentDeltaRaw) == targetPowerTotalRaw, "war-entry target adjustment decomposition differs");
        }
        private List<Long> rawValues() { return List.of(distanceRaw, actorPowerBaseRaw, actorNetworkContributionRaw, actorPowerTotalRaw, targetPowerBaseRaw,
                targetNetworkContributionRaw, targetPreAdjustmentTotalRaw, targetAdjustmentDeltaRaw, targetPowerTotalRaw, actualPowerRatioRaw); }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("target_character_id", targetCharacterId).put("effective_target_character_id", effectiveTargetCharacterId);
            List<Long> values = rawValues(); for (int index = 0; index < RAW.size(); index++) wide(n, RAW.get(index), values.get(index), publicV2);
            return n.put("target_ai_context_actor_entry_raw", targetAiContextActorEntryRaw).put("actor_ai_context_target_entry_raw", actorAiContextTargetEntryRaw).put("native_flags_raw", nativeFlagsRaw);
        }
    }
    public record Observed(long snapshotRevision, int dateRaw, int actorCharacterId, List<Integer> requestedTargetCharacterIds,
            List<Assessment> assessments, EventWindowModels.Build build) {
        public Observed {
            require(snapshotRevision >= 0 && actorCharacterId > 0, "war-entry native revision/actor identity differs");
            requestedTargetCharacterIds = targets(requestedTargetCharacterIds); assessments = List.copyOf(assessments); Objects.requireNonNull(build);
            require(assessments.size() == requestedTargetCharacterIds.size() && assessments.getFirst().targetCharacterId() == requestedTargetCharacterIds.getFirst(), "war-entry assessment target order differs");
        }
        public ObjectNode toNativeJson() { return json(false); }
        public ObjectNode toPublicV2Json() { return json(true); }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("schema_version", 1).put("status", "available"); wide(n, "snapshot_revision", snapshotRevision, publicV2);
            n.put("date_raw", dateRaw).put("actor_character_id", actorCharacterId); var targets = n.putArray("requested_target_character_ids"); requestedTargetCharacterIds.forEach(targets::add);
            var rows = n.putArray("assessments"); assessments.forEach(row -> rows.add(row.json(publicV2)));
            var ready = n.putObject("readiness"); READY.stream().sorted().forEach(field -> ready.put(field, true)); n.set("provenance", provenance(build)); return n;
        }
    }
    public enum ScopeSource {
        DECLARABLE_WAR("declarable_war"), ACTIVE_WAR_PRIMARY_OPPONENT("active_war_primary_opponent"), RAIKTOR_BOOKMARK_BYZ_EMPEROR_SAVED_SCOPE("raiktor_bookmark_byz_emperor_saved_scope");
        private final String wire; ScopeSource(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public record TargetScope(int targetCharacterId, List<ScopeSource> sources) {
        public TargetScope { require(targetCharacterId > 0, "positive target required"); sources = List.copyOf(sources); require(!sources.isEmpty() && sources.stream().distinct().count() == sources.size(), "target scope witnesses must be nonempty/distinct"); }
    }
    public record Scopes(List<TargetScope> targets) {
        public Scopes { targets = List.copyOf(targets); require(targets.size() == 1, "exactly one scoped CharacterID required"); }
        public ArrayNode toNativeJson() { var result = empty().arrayNode(); for (TargetScope target : targets) { var row = result.addObject().put("target_character_id", target.targetCharacterId()); var sources = row.putArray("sources"); target.sources().forEach(source -> sources.add(source.wire())); } return result; }
    }
    public static List<Integer> normalizeTargetIds(JsonNode raw) { return targets(array(raw, node -> positive32(integer(node)))); }
    public static String step(List<Integer> targetCharacterIds) { return STEP_PREFIX + "1-" + targets(targetCharacterIds).getFirst(); }
    public static Optional<List<Integer>> parseStep(String value) {
        if (value == null || !value.startsWith(STEP_PREFIX + "1-")) return Optional.empty(); String raw = value.substring((STEP_PREFIX + "1-").length());
        if (!raw.matches("[1-9][0-9]*")) return Optional.empty();
        try { return Optional.of(List.of(positive32(new BigInteger(raw)))); } catch (IllegalArgumentException invalid) { return Optional.empty(); }
    }
    public static Observed normalize(JsonNode raw, Expected expected) {
        Objects.requireNonNull(expected); Observed result = normalize(raw);
        require(result.requestedTargetCharacterIds().equals(expected.targetCharacterIds()) && BigInteger.valueOf(result.actorCharacterId()).equals(expected.actorCharacterId())
                && BigInteger.valueOf(result.snapshotRevision()).equals(expected.nativeRevision()) && BigInteger.valueOf(result.dateRaw()).equals(expected.dateRaw()), "war-entry exact expected actor/targets/native frame differs"); return result;
    }
    public static Observed normalize(JsonNode raw) {
        var n = closed(raw, "schema_version", "status", "snapshot_revision", "date_raw", "actor_character_id", "requested_target_character_ids", "assessments", "readiness", "provenance");
        equal(get(n, "schema_version"), BigInteger.ONE); equal(get(n, "status"), "available"); long revision = nonnegative64(integer(get(n, "snapshot_revision")));
        int date = i32(get(n, "date_raw")), actor = positive32(integer(get(n, "actor_character_id"))); List<Integer> requested = normalizeTargetIds(get(n, "requested_target_character_ids"));
        var rows = array(get(n, "assessments"), WarEntryAssessmentCodec::assessment); require(rows.size() == requested.size(), "war-entry assessment count differs");
        ObjectNode ready = object(get(n, "readiness")); require(names(ready).equals(READY), "war-entry readiness fields differ"); READY.forEach(field -> yes(get(ready, field)));
        var provenance = closed(get(n, "provenance"), "game_version", "executable_sha256", "assessment_rva", "network_collector_rva", "power_leaf", "fixed_point_scale");
        EventWindowModels.Build build = exactBuild(text(get(provenance, "game_version")), text(get(provenance, "executable_sha256")));
        ObjectNode expectedProvenance = provenance(build); for (String field : names(expectedProvenance)) {
            if (field.equals("fixed_point_scale")) equal(get(provenance, field), BigInteger.valueOf(100000)); else equal(get(provenance, field), text(get(expectedProvenance, field)));
        }
        return new Observed(revision, date, actor, requested, rows, build);
    }
    private static Assessment assessment(JsonNode raw) {
        var fields = new HashSet<>(RAW); fields.addAll(Set.of("target_character_id", "effective_target_character_id", "target_ai_context_actor_entry_raw", "actor_ai_context_target_entry_raw", "native_flags_raw"));
        ObjectNode n = object(raw); require(names(n).equals(fields), "war-entry assessment fields differ");
        return new Assessment(positive32(integer(get(n, "target_character_id"))), positive32(integer(get(n, "effective_target_character_id"))),
                i64(get(n, "distance_raw")), i64(get(n, "actor_power_base_raw")), i64(get(n, "actor_network_contribution_raw")), i64(get(n, "actor_power_total_raw")),
                i64(get(n, "target_power_base_raw")), i64(get(n, "target_network_contribution_raw")), i64(get(n, "target_pre_adjustment_total_raw")), i64(get(n, "target_adjustment_delta_raw")),
                i64(get(n, "target_power_total_raw")), i64(get(n, "actual_power_ratio_raw")), i32(get(n, "target_ai_context_actor_entry_raw")), i32(get(n, "actor_ai_context_target_entry_raw")), i32(get(n, "native_flags_raw")));
    }
    public static List<Integer> requireDeclarableTargets(JsonNode snapshot, List<Integer> requested) {
        var targets = targets(requested); Set<Integer> declarable = declarable(object(snapshot)); require(declarable.containsAll(targets), "target is outside current declarable_wars"); return targets;
    }
    public static Scopes targetScopes(JsonNode snapshot, List<Integer> requested) { return targetScopes(snapshot, requested, null); }
    public static Scopes targetScopes(JsonNode snapshot, List<Integer> requested, JsonNode eventContext) {
        var targets = targets(requested); ObjectNode frame = object(snapshot); Set<Integer> declarable = declarable(frame), opponents = new HashSet<>();
        JsonNode wars = frame.get("active_wars"); if (wars != null) for (ObjectNode war : array(wars, ArmyJson::object)) {
            JsonNode raw = war.get("primary_opponent_character_id"); if (raw == null || raw.isNull()) continue;
            int id = i32(raw); if (id == 0) continue; require(id > 0, "active primary opponent must be positive full-generation CharacterID"); opponents.add(id);
        }
        OptionalInt eventTarget = eventContext == null || eventContext.isNull() ? OptionalInt.empty() : raiktorSavedScopeTarget(frame, eventContext);
        List<TargetScope> scopes = new ArrayList<>();
        for (int target : targets) {
            List<ScopeSource> sources = new ArrayList<>(); if (declarable.contains(target)) sources.add(ScopeSource.DECLARABLE_WAR);
            if (opponents.contains(target)) sources.add(ScopeSource.ACTIVE_WAR_PRIMARY_OPPONENT);
            if (eventTarget.isPresent() && eventTarget.getAsInt() == target) sources.add(ScopeSource.RAIKTOR_BOOKMARK_BYZ_EMPEROR_SAVED_SCOPE);
            require(!sources.isEmpty(), "target is outside declarable_wars, active primary opponents and exact Raiktor event saved scope"); scopes.add(new TargetScope(target, sources));
        }
        return new Scopes(scopes);
    }
    /** Existing strict full EventWindow producer is the sole authority for nested scopes, options, indicators and exact-build provenance. */
    public static OptionalInt raiktorSavedScopeTarget(JsonNode snapshot, JsonNode eventContext) {
        ObjectNode frame = object(snapshot); yes(get(frame, "paused")); ObjectNode active = object(get(frame, "active_event")), played = object(get(frame, "played_character"));
        int instance = positive32(integer(get(active, "instance_id"))), player = positive32(integer(get(played, "character_id"))), date = i32(get(frame, "date_raw"));
        BigInteger revision = integer(get(frame, "native_revision")); String backend = text(get(object(get(object(eventContext), "provenance")), "backend_id"));
        EventWindowModels.Build build = java.util.Arrays.stream(EventWindowModels.Build.values()).filter(candidate -> candidate.backend().equals(backend)).findFirst().orElseThrow(() -> new IllegalArgumentException("event context exact build unavailable"));
        var binding = new EventWindowModels.Binding(build, revision, date, instance);
        EventWindowModels.Context normalized = EventWindowCodec.decode(new RawJson(bytes(eventContext)), binding);
        if (!(normalized instanceof EventWindowModels.Available available) || !available.definition().key().equals("bookmark.1071")) return OptionalInt.empty();
        require(i32(get(active, "option_count")) == 3 && available.options().stream().map(EventWindowModels.Option::nativeOptionIndex).collect(java.util.stream.Collectors.toSet()).equals(Set.of(0, 1, 2)), "Raiktor event option projection differs");
        require(available.rootScope().typeKey().equals("character") && available.rootScope().identity() instanceof EventWindowModels.CharacterIdentity character && character.characterId() == player, "Raiktor player root differs");
        Integer byz = null, raiktor = null;
        for (var saved : available.savedScopes()) if (saved.name().equals("byz_emperor") || saved.name().equals("raiktor")) {
            require(saved.scope().typeKey().equals("character") && saved.scope().identity() instanceof EventWindowModels.CharacterIdentity, "Raiktor saved character unavailable");
            int id = ((EventWindowModels.CharacterIdentity) saved.scope().identity()).characterId(); require(id > 0, "Raiktor saved full CharacterID must be positive");
            if (saved.name().equals("byz_emperor")) byz = id; else raiktor = id;
        }
        require(byz != null && raiktor != null && byz != player, "Raiktor Byzantine holder unavailable"); return OptionalInt.of(byz);
    }
    private static Set<Integer> declarable(ObjectNode snapshot) {
        Set<Integer> result = new HashSet<>(); for (ObjectNode row : array(get(snapshot, "declarable_wars"), ArmyJson::object)) result.add(positive32(integer(get(row, "target_character_id")))); return result;
    }
    private static List<Integer> targets(List<Integer> values) { Objects.requireNonNull(values); require(values.size() == 1 && values.getFirst() != null && values.getFirst() > 0, "target_character_ids requires exactly one positive signed32 CharacterID"); return List.copyOf(values); }
    private static int positive32(BigInteger value) { require(value != null && value.signum() > 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "positive signed32 CharacterID required"); return value.intValueExact(); }
    private static long nonnegative64(BigInteger value) { require(value != null && value.signum() >= 0 && value.bitLength() <= 63, "nonnegative signed64 revision required"); return value.longValueExact(); }
    private static int signed32(BigInteger value) { require(value != null && value.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "signed32 date required"); return value.intValueExact(); }
    private static long sum(long first, long second) { try { return Math.addExact(first, second); } catch (ArithmeticException overflow) { throw new IllegalArgumentException("war-entry signed64 power decomposition overflow", overflow); } }
    private static EventWindowModels.Build exactBuild(String version, String sha) {
        return java.util.Arrays.stream(EventWindowModels.Build.values()).filter(build -> build.version().equals(version) && build.sha256().equals(sha)).findFirst().orElseThrow(() -> new IllegalArgumentException("war-entry exact build/SHA provenance differs"));
    }
    private static ObjectNode provenance(EventWindowModels.Build build) {
        boolean old = build == EventWindowModels.Build.TOURS, four = build == EventWindowModels.Build.CROZIER4;
        return empty().put("game_version", build.version()).put("executable_sha256", build.sha256()).put("assessment_rva", old ? "0x1878A00" : four ? "0x1A23220" : "0x1A23240")
                .put("network_collector_rva", old ? "0x1879850" : four ? "0x1A23FF0" : "0x1A24010").put("power_leaf", old ? "CCharacter+0x1B8->+0x308" : "CCharacter+0x1C0->+0x308").put("fixed_point_scale", 100000);
    }
    private static void wide(ObjectNode node, String key, long value, boolean publicV2) { if (publicV2) node.put(key, Long.toString(value)); else node.put(key, value); }
}
