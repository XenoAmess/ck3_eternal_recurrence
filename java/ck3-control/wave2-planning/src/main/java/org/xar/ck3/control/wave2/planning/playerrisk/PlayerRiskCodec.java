package org.xar.ck3.control.wave2.planning.playerrisk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import java.util.Objects;
import org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.*;

/** Strict JSON entry and declared projection of the extensible legacy SDK containers. */
public final class PlayerRiskCodec {
    private static final BigInteger ZERO = BigInteger.ZERO;
    private static final BigInteger ONE = BigInteger.ONE;
    private static final Set<String> PARTITION = Set.of("title", "first_heir_character_id", "capital_province_id", "primary");
    private static final Set<String> FAMILY = Set.of("title", "first_heir_character_id", "capital_province_id", "primary", "capital_province_kind", "title_key");
    private PlayerRiskCodec() { }

    public static Context project(byte[] request) {
        JsonNode input = StrictJson.parse(request);
        StrictJson.object(input, Set.of("snapshot", "campaign_root_result"));
        return projectObserved(input.get("snapshot"), input.get("campaign_root_result"));
    }

    /** Existing same-frame projection on the already-decoded complete source; no second small JSON parser. */
    public static Context projectObserved(JsonNode snapshot, JsonNode result) {
        if (nil(result)) { return PlayerRiskContext.unavailable(PlayerRiskContext.MISSING); }
        try { return PlayerRiskContext.project(decode(snapshot, result)); }
        catch (ContractViolationException error) { return PlayerRiskContext.unavailable(PlayerRiskContext.INVALID); }
    }

    private static Input decode(JsonNode snapshot, JsonNode result) {
        object(snapshot); object(result);
        JsonNode root = object(result.get("campaign_root_context"));
        String snapshotId = text(snapshot.get("snapshot_id"));
        BigInteger revision = integer(snapshot.get("revision"), ZERO, StrictJson.UINT64_MAX);
        BigInteger nativeRevision = integer(snapshot.get("native_revision"), ONE, StrictJson.UINT64_MAX);
        int date = int32(snapshot.get("date_raw"));
        StrictJson.trueValue(snapshot.get("paused"));
        compareIfPresent(result, "queried_snapshot_id", snapshot.get("snapshot_id"));
        compareIfPresent(result, "queried_revision", snapshot.get("revision"));
        compareIfPresent(result, "queried_native_revision", snapshot.get("native_revision"));
        JsonNode diagnostics = snapshot.get("diagnostics");
        BigInteger generation = diagnostics != null && diagnostics.isObject() ? positiveOrNull(diagnostics.get("connection_generation")) : null;
        boolean witness = result.has("queried_connection_generation");
        if (witness) {
            BigInteger observed = positiveOrNull(result.get("queried_connection_generation"));
            require(observed != null && observed.equals(generation), "response generation differs");
        }
        JsonNode binding = result.get("binding");
        if (binding != null && binding.isObject()) {
            require(text(binding.get("snapshot_id")).equals(snapshotId), "snapshot differs");
            require(integer(binding.get("revision"), ZERO, StrictJson.UINT64_MAX).equals(revision), "revision differs");
            require(integer(binding.get("native_revision"), ONE, StrictJson.UINT64_MAX).equals(nativeRevision), "native revision differs");
            require(int32(binding.get("date_raw")) == date, "binding date differs");
        } else {
            require(result.has("queried_snapshot_id") && result.has("queried_revision") && result.has("queried_native_revision"), "missing observed binding");
        }
        require(integer(root.get("snapshot_revision"), ONE, StrictJson.UINT64_MAX).equals(nativeRevision), "root revision differs");
        require(int32(root.get("date_raw")) == date, "root date differs");
        BigInteger sequence = integer(result.get("query_sequence"), ONE, StrictJson.UINT64_MAX);
        String status = text(root.get("status"));
        require(text(result.get("status")).equals(status), "root status differs");
        if (status.equals("unavailable")) { return new RootUnavailable(text(root.get("unavailable_reason"))); }
        require(status.equals("available"), "root status invalid");
        int actor = id(root.get("player_character_id"));
        boolean alive = bool(root.get("player_character_alive"));
        JsonNode played = snapshot.get("played_character");
        if (!nil(played)) {
            object(played); require(id(played.get("character_id")) == actor && bool(played.get("alive")) == alive, "played character differs");
        }
        Component<Stress> stress = stress(played != null && played.isObject() ? played.get("stress_points") : null);
        fixed(root.get("player_monthly_gold_income"));
        long health = fixed(root.get("player_health"));
        JsonNode gold = snapshot.get("played_character_gold");
        if (gold != null && gold.isObject()) { fixed(gold); }
        optionalId(root.get("capital_province_id"));
        incidentalRootChecks(root);
        JsonNode primary = root.get("primary_title");
        Integer tier = nil(primary) ? null : title(primary);
        ArrayNode successorsNode = array(root.get("primary_title_succession_character_ids"));
        List<Integer> successors = new ArrayList<>();
        successorsNode.forEach(value -> successors.add(id(value)));
        require(tier != null || successors.isEmpty(), "landless successors");
        Integer first = successors.isEmpty() ? null : successors.getFirst();
        ArrayNode partition = array(root.get("held_title_partition"));
        List<HeldTitle> held = new ArrayList<>();
        if (tier == null || tier == 1) { require(partition.isEmpty(), "inapplicable partition"); }
        else {
            int primaryCount = 0;
            for (JsonNode row : partition) {
                object(row);
                boolean family = row.has("capital_province_kind") || row.has("title_key");
                StrictJson.object(row, family ? FAMILY : PARTITION);
                int rowTier = title(row.get("title"));
                int titleId = id(row.get("title").get("title_id"));
                Integer rowHeir = optionalId(row.get("first_heir_character_id"));
                Integer capital = optionalId(row.get("capital_province_id"));
                boolean isPrimary = bool(row.get("primary"));
                if (isPrimary) { primaryCount++; require(java.util.Objects.equals(first, rowHeir), "primary heir differs"); }
                if (family) {
                    require(rowTier == 2 && capital == null && isText(row.get("capital_province_kind"), "landless_noble_family_no_province"), "invalid family geography");
                    String key = text(row.get("title_key"));
                    require(key.length() <= 1024 && key.matches("c_[a-zA-Z0-9][a-zA-Z0-9_]*"), "invalid family title key");
                }
                held.add(new HeldTitle(titleId, rowTier, rowHeir, capital, isPrimary, family));
            }
            require(primaryCount == 1, "one primary partition row required");
        }
        incidentalSnapshotChecks(snapshot);
        String backend = nil(snapshot.get("backend_id")) ? null : text(snapshot.get("backend_id"));
        return new Observation(new Binding(snapshotId, revision, nativeRevision, date, actor), new Source(sequence, backend),
                new CurrentScope(generation, witness), health, stress, tier, successors, held);
    }

    /** Preserve the original aggregate's rejection boundary without constructing unrelated domain output. */
    private static void incidentalRootChecks(JsonNode root) {
        array(root.get("direct_landed_vassal_character_ids"));
        ArrayNode adjacent = array(root.get("adjacent_external_province_holder_character_ids"));
        ArrayNode related = array(root.get("related_character_contexts"));
        HashMap<Integer, JsonNode> byId = new HashMap<>();
        for (JsonNode row : related) { object(row); require(byId.put(id(row.get("character_id")), row) == null, "duplicate related character"); }
        for (JsonNode holder : adjacent) {
            JsonNode row = byId.get(id(holder)); require(row != null, "adjacent character missing"); id(row.get("top_liege_character_id"));
        }
        StrictJson.integer(root.get("player_domain_size"), 0, Integer.MAX_VALUE);
        id(root.get("player_domain_limit"));
        StrictJson.integer(root.get("player_targeting_faction_count"), 0, Integer.MAX_VALUE);
        JsonNode council = object(root.get("council"));
        String status = text(council.get("status"));
        require(status.equals("available") || status.equals("unavailable"), "invalid council status");
        if (status.equals("unavailable")) { text(council.get("unavailable_reason")); }
        optionalId(root.get("immediate_liege_character_id")); id(root.get("top_liege_character_id")); bool(root.get("independent"));
    }

    private static void incidentalSnapshotChecks(JsonNode snapshot) {
        if (snapshot.has("active_event") && snapshot.has("pending_character_interaction")) {
            for (String key : List.of("active_event", "pending_character_interaction")) {
                if (!nil(snapshot.get(key))) { object(snapshot.get(key)); }
            }
        }
        JsonNode wars = snapshot.get("active_wars");
        if (wars == null || !wars.isArray()) { return; }
        Set<Integer> seen = new HashSet<>();
        for (JsonNode war : wars) {
            object(war); require(seen.add(id(war.get("war_id"))), "duplicate war");
            require(isText(war.get("player_side"), "attacker") || isText(war.get("player_side"), "defender"), "invalid war side");
            require(war.get("player_relative_war_score") != null && war.get("player_relative_war_score").isIntegralNumber(), "integer war score required");
            optionalId(war.get("primary_opponent_character_id"));
        }
    }

    private static Component<Stress> stress(JsonNode node) {
        if (node != null && node.isIntegralNumber() && node.bigIntegerValue().signum() >= 0
                && node.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0) {
            int value = node.intValue(); return new Known<>(new Stress(value, value >= 100));
        }
        return new Unknown<>("played_character_stress_unavailable");
    }
    private static int title(JsonNode node) {
        StrictJson.object(node, Set.of("title_id", "tier_raw", "tier_key")); id(node.get("title_id"));
        int tier = (int) StrictJson.integer(node.get("tier_raw"), 1, 6);
        require(text(node.get("tier_key")).equals(List.of("barony", "county", "duchy", "kingdom", "empire", "hegemony").get(tier - 1)), "title tier pair differs");
        return tier;
    }
    private static long fixed(JsonNode node) {
        StrictJson.object(node, Set.of("raw", "scale"));
        require(StrictJson.integer(node.get("scale"), 100_000, 100_000) == 100_000, "fixed scale differs");
        return StrictJson.integer(node.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE);
    }
    private static void compareIfPresent(JsonNode row, String key, JsonNode expected) {
        if (row.has(key)) { require(row.get(key).equals(expected), "observed frame differs: " + key); }
    }
    private static BigInteger positiveOrNull(JsonNode value) {
        return value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() > 0 ? value.bigIntegerValue() : null;
    }
    private static JsonNode object(JsonNode node) { require(node != null && node.isObject(), "object required"); return node; }
    private static ArrayNode array(JsonNode node) { require(node instanceof ArrayNode, "array required"); return (ArrayNode) node; }
    private static boolean nil(JsonNode node) { return node == null || node.isNull(); }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static boolean isText(JsonNode node, String text) { return node != null && node.isTextual() && node.textValue().equals(text); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean required"); return node.booleanValue(); }
    private static int id(JsonNode node) { return (int) StrictJson.integer(node, 1, Integer.MAX_VALUE); }
    private static Integer optionalId(JsonNode node) { return nil(node) ? null : id(node); }
    private static int int32(JsonNode node) { return (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static BigInteger integer(JsonNode node, BigInteger min, BigInteger max) { return StrictJson.integer(node, min, max); }
    private static void require(boolean value, String reason) { StrictJson.require(value, reason); }

    public static ObjectNode encode(Context context) {
        ObjectNode node = StrictJson.object(); node.put("schema", PlayerRiskContext.SCHEMA);
        node.put("status", context.status() == Status.PARTIAL ? "partial" : "unavailable");
        if (context.binding() == null) { node.putNull("binding"); node.putNull("source"); node.putNull("current_scope"); }
        else {
            Binding value = context.binding(); ObjectNode binding = node.putObject("binding");
            binding.put("snapshot_id", value.snapshotId()); binding.put("revision", value.revision());
            binding.put("native_revision", value.nativeRevision()); binding.put("date_raw", value.dateRaw()); binding.put("character_id", value.characterId());
            ObjectNode source = node.putObject("source"); source.put("capability", "game.command.query-campaign-root-context-v1");
            source.put("query_sequence", context.source().querySequence()); source.put("backend_id", context.source().backendId());
            ObjectNode scope = node.putObject("current_scope"); scope.put("connection_generation", context.currentScope().connectionGeneration());
            scope.put("source", "current_snapshot_diagnostics"); scope.put("response_connection_generation_observed", context.currentScope().responseGenerationObserved());
        }
        node.set("health", component(context.health())); node.set("stress", component(context.stress()));
        ObjectNode alerts = node.putObject("alerts"); alerts.set("ruler_health_below_fine", component(context.alerts().belowFine()));
        alerts.set("ruler_stress_at_or_above_100", component(context.alerts().highStress()));
        alerts.set("no_primary_title_heir", component(context.alerts().noHeir())); alerts.set("succession_partition_split", component(context.alerts().partitionSplit()));
        ObjectNode signals = node.putObject("planner_signals"); signals.set("succession_preparation_priority", component(context.signals().successionPriority()));
        signals.set("avoid_discretionary_stress_gain", component(context.signals().avoidStressGain())); signals.set("protect_legitimacy_floor", component(context.signals().protectLegitimacyFloor()));
        ObjectNode readiness = node.putObject("readiness"); readiness.put("health_ready", context.readiness().healthReady()); readiness.put("stress_ready", context.readiness().stressReady());
        readiness.put("succession_priority_ready", context.readiness().successionPriorityReady()); readiness.put("legitimacy_protection_ready", context.readiness().legitimacyProtectionReady());
        node.put("unavailable_reason", context.unavailableReason()); return node;
    }

    /** Public representation of this typed risk schema only; the internal encoder and consumers retain their numeric domain. */
    public static ObjectNode encodePublic(Context actual) {
        Objects.requireNonNull(actual);
        ObjectNode result = encode(actual);
        if (actual.binding() != null) {
            ObjectNode binding = (ObjectNode) result.get("binding");
            binding.put("revision", PublicUnsigned64.canonical(actual.binding().revision(), PublicUnsigned64.Minimum.ZERO));
            binding.put("native_revision", PublicUnsigned64.canonical(actual.binding().nativeRevision(), PublicUnsigned64.Minimum.ONE));
            ((ObjectNode) result.get("source")).put("query_sequence",
                    PublicUnsigned64.canonical(actual.source().querySequence(), PublicUnsigned64.Minimum.ONE));
            ObjectNode scope = (ObjectNode) result.get("current_scope");
            if (actual.currentScope().connectionGeneration() == null) scope.putNull("connection_generation");
            else scope.put("connection_generation", PublicUnsigned64.canonical(
                    actual.currentScope().connectionGeneration(), PublicUnsigned64.Minimum.ONE));
        }
        return result;
    }

    private static ObjectNode component(Component<?> component) {
        ObjectNode result = StrictJson.object();
        if (component instanceof Unknown<?> unknown) { result.put("status", "unavailable"); result.putNull("value"); result.put("unavailable_reason", unknown.reason()); }
        else if (component instanceof NotApplicable<?> absent) { result.put("status", "not_applicable"); result.putNull("value"); result.put("unavailable_reason", absent.reason()); }
        else {
            result.put("status", "available"); result.putNull("unavailable_reason"); Object value = ((Known<?>) component).value();
            if (value instanceof Boolean flag) { result.put("value", flag); }
            else if (value instanceof Priority priority) { result.put("value", priority.name().toLowerCase(java.util.Locale.ROOT)); }
            else if (value instanceof Health health) {
                ObjectNode payload = result.putObject("value"); payload.put("raw", health.raw()); payload.put("scale", 100_000);
                payload.put("band", health.band().name().toLowerCase(java.util.Locale.ROOT)); payload.put("below_fine", health.belowFine());
                payload.put("at_or_below_death_chance_dying", health.dyingOrWorse());
            } else if (value instanceof Stress stress) {
                ObjectNode payload = result.putObject("value"); payload.put("points", stress.points()); payload.put("at_or_above_first_break_threshold", stress.firstBreakThreshold());
            } else { throw new IllegalArgumentException("unsupported risk component"); }
        }
        return result;
    }
}
