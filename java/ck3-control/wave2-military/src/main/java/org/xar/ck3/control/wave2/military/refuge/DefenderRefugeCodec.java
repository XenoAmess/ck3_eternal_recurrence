package org.xar.ck3.control.wave2.military.refuge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Army;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Assessment;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.CacheBinding;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.CachedQuery;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.CampaignRoot;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Diagnostics;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Enemy;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.HeldTitle;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Presence;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Readiness;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.RefugeScope;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.RelatedContext;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Request;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Snapshot;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.Title;
import org.xar.ck3.control.wave2.military.refuge.DefenderRefugePolicy.War;

/** Strict scalar types around declared native DTO projections; no file, query or authority side effects. */
public final class DefenderRefugeCodec {
    public static final int INPUT_MAX_BYTES = 65_536;
    private DefenderRefugeCodec() { }

    public static byte[] evaluate(byte[] raw) { return encodeAssessment(DefenderRefugePolicy.assess(decode(raw))); }
    public static Request decode(byte[] raw) { return decodeNode(StrictJson.parse(raw, INPUT_MAX_BYTES)); }
    public static Request decodeNode(JsonNode node) {
        ObjectNode value = StrictJson.object(node, Set.of("schema", "snapshot", "root", "cached_query"));
        StrictJson.require(DefenderRefugePolicy.INPUT_SCHEMA.equals(StrictJson.text(value.get("schema"))), "unsupported refuge schema");
        return new Request(snapshot(value.get("snapshot")), root(value.get("root")), cached(value.get("cached_query")));
    }

    private static Snapshot snapshot(JsonNode node) {
        if (!present(node)) { return null; }
        ObjectNode value = object(node); BigInteger played = null; Diagnostics diagnostics = null;
        if (present(value.get("played_character"))) { played = integer(object(value.get("played_character")).get("character_id")); }
        if (present(value.get("diagnostics"))) {
            ObjectNode diag = object(value.get("diagnostics")); diagnostics = new Diagnostics(integer(diag.get("bridge_pid")), integer(diag.get("connection_generation")));
        }
        List<War> wars = null;
        if (present(value.get("active_wars"))) {
            wars = new ArrayList<>();
            for (JsonNode row : array(value.get("active_wars"))) {
                ObjectNode war = object(row); List<Enemy> enemies = null;
                if (present(war.get("enemy_armies"))) {
                    enemies = new ArrayList<>();
                    for (JsonNode enemyNode : array(war.get("enemy_armies"))) {
                        ObjectNode enemy = object(enemyNode); enemies.add(new Enemy(integer(enemy.get("army_id")), bool(enemy.get("retreating"))));
                    }
                }
                wars.add(new War(text(war.get("player_side")), bool(war.get("player_is_primary_war_leader")), integers(war.get("war_objective_province_ids")), enemies));
            }
        }
        List<Army> armies = null;
        if (present(value.get("player_armies"))) {
            armies = new ArrayList<>();
            for (JsonNode row : array(value.get("player_armies"))) {
                ObjectNode army = object(row);
                armies.add(new Army(integer(army.get("army_id")), integer(army.get("current_province_id")), integer(army.get("owner_character_id")),
                        bool(army.get("controllable")), text(army.get("army_state")), bool(army.get("in_combat")), bool(army.get("retreating")),
                        integers(army.get("route_province_ids")), integer(army.get("move_target_province_id"))));
            }
        }
        return new Snapshot(bool(value.get("paused")), bool(value.get("map_ready")), presence(value.get("active_event")),
                presence(value.get("pending_character_interaction")), integer(value.get("actor_character_id")), played,
                text(value.get("snapshot_id")), integer(value.get("revision")), integer(value.get("native_revision")),
                integer(value.get("date_raw")), diagnostics, wars, armies);
    }

    private static CampaignRoot root(JsonNode node) {
        if (!present(node)) { return null; }
        ObjectNode value = object(node); Readiness readiness = null;
        if (present(value.get("readiness"))) {
            ObjectNode ready = object(value.get("readiness"));
            readiness = new Readiness(bool(ready.get("direct_landed_vassals_ready")), bool(ready.get("related_character_contexts_ready")));
        }
        List<RelatedContext> contexts = null;
        if (present(value.get("related_character_contexts"))) {
            contexts = new ArrayList<>();
            for (JsonNode row : array(value.get("related_character_contexts"))) {
                ObjectNode context = object(row);
                contexts.add(new RelatedContext(text(context.get("relationship_role")), integer(context.get("character_id")),
                        integer(context.get("immediate_liege_character_id")), integer(context.get("top_liege_character_id")),
                        title(context.get("primary_title")), integer(context.get("capital_province_id"))));
            }
        }
        List<HeldTitle> partition = null;
        if (present(value.get("held_title_partition"))) {
            partition = new ArrayList<>();
            for (JsonNode row : array(value.get("held_title_partition"))) {
                ObjectNode held = object(row); partition.add(new HeldTitle(title(held.get("title")), integer(held.get("capital_province_id"))));
            }
        }
        return new CampaignRoot(text(value.get("status")), integer(value.get("player_character_id")), integer(value.get("top_liege_character_id")), readiness,
                integers(value.get("direct_landed_vassal_character_ids")), contexts, integer(value.get("snapshot_revision")), integer(value.get("date_raw")), partition);
    }
    private static Title title(JsonNode node) {
        if (!present(node)) { return null; }
        ObjectNode value = object(node); return new Title(integer(value.get("title_id")), integer(value.get("tier_raw")));
    }
    private static CachedQuery cached(JsonNode node) {
        if (!present(node)) { return null; }
        ObjectNode value = object(node); CacheBinding binding = null;
        if (present(value.get("cache_binding"))) {
            ObjectNode frame = object(value.get("cache_binding"));
            String snapshotId = text(frame.get("snapshot_id"));
            StrictJson.require(snapshotId != null, "complete cache binding snapshot_id required");
            binding = new CacheBinding(snapshotId, requiredInteger(frame.get("revision")), requiredInteger(frame.get("native_revision")),
                    requiredInteger(frame.get("date_raw")), requiredInteger(frame.get("actor_character_id")),
                    requiredInteger(frame.get("bridge_pid")), requiredInteger(frame.get("connection_generation")));
        }
        return new CachedQuery(binding, root(value.get("campaign_root_context")));
    }

    public static byte[] encodeRequest(Request request) {
        ObjectNode result = StrictJson.object(); result.put("schema", DefenderRefugePolicy.INPUT_SCHEMA);
        if (request.snapshot() == null) { result.putNull("snapshot"); } else { result.set("snapshot", snapshotNode(request.snapshot())); }
        if (request.root() == null) { result.putNull("root"); } else { result.set("root", rootNode(request.root())); }
        if (request.cachedQuery() == null) { result.putNull("cached_query"); }
        else {
            CachedQuery cached = request.cachedQuery(); ObjectNode query = result.putObject("cached_query");
            if (cached.cacheBinding() == null) { query.putNull("cache_binding"); }
            else {
                CacheBinding frame = cached.cacheBinding(); ObjectNode binding = query.putObject("cache_binding");
                binding.put("snapshot_id", frame.snapshotId()); binding.put("revision", frame.revision()); binding.put("native_revision", frame.nativeRevision());
                binding.put("date_raw", frame.dateRaw()); binding.put("actor_character_id", frame.actorCharacterId());
                binding.put("bridge_pid", frame.bridgePid()); binding.put("connection_generation", frame.connectionGeneration());
            }
            if (cached.campaignRootContext() == null) { query.putNull("campaign_root_context"); }
            else { query.set("campaign_root_context", rootNode(cached.campaignRootContext())); }
        }
        return StrictJson.canonical(result, INPUT_MAX_BYTES);
    }

    private static ObjectNode snapshotNode(Snapshot snapshot) {
        ObjectNode result = StrictJson.object(); result.put("paused", snapshot.paused()); result.put("map_ready", snapshot.mapReady());
        presenceNode(result, "active_event", snapshot.activeEvent()); presenceNode(result, "pending_character_interaction", snapshot.pendingCharacterInteraction());
        result.put("actor_character_id", snapshot.actorCharacterId()); result.putObject("played_character").put("character_id", snapshot.playedCharacterId());
        result.put("snapshot_id", snapshot.snapshotId()); result.put("revision", snapshot.revision()); result.put("native_revision", snapshot.nativeRevision());
        result.put("date_raw", snapshot.dateRaw());
        if (snapshot.diagnostics() == null) { result.putNull("diagnostics"); }
        else {
            ObjectNode diag = result.putObject("diagnostics"); diag.put("bridge_pid", snapshot.diagnostics().bridgePid());
            diag.put("connection_generation", snapshot.diagnostics().connectionGeneration());
        }
        if (snapshot.activeWars() == null) { result.putNull("active_wars"); }
        else {
            ArrayNode wars = result.putArray("active_wars");
            for (War war : snapshot.activeWars()) {
                ObjectNode value = wars.addObject(); value.put("player_side", war.playerSide()); value.put("player_is_primary_war_leader", war.playerIsPrimaryWarLeader());
                integersNode(value, "war_objective_province_ids", war.warObjectiveProvinceIds());
                if (war.enemyArmies() == null) { value.putNull("enemy_armies"); }
                else {
                    ArrayNode enemies = value.putArray("enemy_armies");
                    for (Enemy enemy : war.enemyArmies()) { ObjectNode row = enemies.addObject(); row.put("army_id", enemy.armyId()); row.put("retreating", enemy.retreating()); }
                }
            }
        }
        if (snapshot.playerArmies() == null) { result.putNull("player_armies"); }
        else {
            ArrayNode armies = result.putArray("player_armies");
            for (Army army : snapshot.playerArmies()) {
                ObjectNode row = armies.addObject(); row.put("army_id", army.armyId()); row.put("current_province_id", army.currentProvinceId());
                row.put("owner_character_id", army.ownerCharacterId()); row.put("controllable", army.controllable()); row.put("army_state", army.armyState());
                row.put("in_combat", army.inCombat()); row.put("retreating", army.retreating()); integersNode(row, "route_province_ids", army.routeProvinceIds());
                row.put("move_target_province_id", army.moveTargetProvinceId());
            }
        }
        return result;
    }
    private static ObjectNode rootNode(CampaignRoot root) {
        ObjectNode result = StrictJson.object(); result.put("status", root.status()); result.put("player_character_id", root.playerCharacterId());
        result.put("top_liege_character_id", root.topLiegeCharacterId()); result.put("snapshot_revision", root.snapshotRevision()); result.put("date_raw", root.dateRaw());
        if (root.readiness() == null) { result.putNull("readiness"); }
        else {
            ObjectNode ready = result.putObject("readiness"); ready.put("direct_landed_vassals_ready", root.readiness().directLandedVassalsReady());
            ready.put("related_character_contexts_ready", root.readiness().relatedCharacterContextsReady());
        }
        integersNode(result, "direct_landed_vassal_character_ids", root.directLandedVassalCharacterIds());
        if (root.relatedCharacterContexts() == null) { result.putNull("related_character_contexts"); }
        else {
            ArrayNode contexts = result.putArray("related_character_contexts");
            for (RelatedContext context : root.relatedCharacterContexts()) {
                ObjectNode row = contexts.addObject(); row.put("relationship_role", context.relationshipRole()); row.put("character_id", context.characterId());
                row.put("immediate_liege_character_id", context.immediateLiegeCharacterId()); row.put("top_liege_character_id", context.topLiegeCharacterId());
                titleNode(row, "primary_title", context.primaryTitle()); row.put("capital_province_id", context.capitalProvinceId());
            }
        }
        if (root.heldTitlePartition() == null) { result.putNull("held_title_partition"); }
        else {
            ArrayNode partition = result.putArray("held_title_partition");
            for (HeldTitle held : root.heldTitlePartition()) {
                ObjectNode row = partition.addObject(); titleNode(row, "title", held.title()); row.put("capital_province_id", held.capitalProvinceId());
            }
        }
        return result;
    }

    public static byte[] encodeAssessment(Assessment assessment) {
        ObjectNode result = StrictJson.object(); result.put("schema", DefenderRefugePolicy.OUTPUT_SCHEMA);
        if (assessment.directVassalCapitalProvinceIds() == null) { result.putNull("direct_vassal_capital_province_ids"); }
        else { ArrayNode capitals = result.putArray("direct_vassal_capital_province_ids"); assessment.directVassalCapitalProvinceIds().forEach(capitals::add); }
        scopeNode(result, "lifecycle_scope", assessment.lifecycleScope()); scopeNode(result, "same_frame_cached_scope", assessment.sameFrameCachedScope());
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }
    private static void scopeNode(ObjectNode parent, String key, RefugeScope scope) {
        if (scope == null) { parent.putNull(key); return; }
        ObjectNode result = parent.putObject(key); result.put("army_id", scope.armyId()); result.put("current_province_id", scope.currentProvinceId());
        result.put("own_capital_province_id", scope.ownCapitalProvinceId()); result.put("current_kind", scope.currentKind().wire());
        ArrayNode candidates = result.putArray("candidate_province_ids"); scope.candidateProvinceIds().forEach(candidates::add);
        ArrayNode hostiles = result.putArray("hostile_army_ids"); scope.hostileArmyIds().forEach(hostiles::add);
    }
    private static void titleNode(ObjectNode parent, String key, Title title) {
        if (title == null) { parent.putNull(key); }
        else { ObjectNode value = parent.putObject(key); value.put("title_id", title.titleId()); value.put("tier_raw", title.tierRaw()); }
    }
    private static void integersNode(ObjectNode parent, String key, List<BigInteger> values) {
        if (values == null) { parent.putNull(key); }
        else { ArrayNode array = parent.putArray(key); values.forEach(array::add); }
    }
    private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "native DTO projection object required"); return (ObjectNode) node; }
    private static JsonNode array(JsonNode node) { StrictJson.require(node != null && node.isArray(), "array required"); return node; }
    private static boolean present(JsonNode node) { return node != null && !node.isNull(); }
    private static Presence presence(JsonNode node) { return node == null ? Presence.MISSING : node.isNull() ? Presence.NULL : Presence.VALUE; }
    private static BigInteger integer(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isIntegralNumber(), "exact JSON integer required"); return node.bigIntegerValue();
    }
    private static BigInteger requiredInteger(JsonNode node) {
        BigInteger value = integer(node); StrictJson.require(value != null, "complete cache binding integer required"); return value;
    }
    private static List<BigInteger> integers(JsonNode node) {
        if (!present(node)) { return null; }
        List<BigInteger> result = new ArrayList<>();
        for (JsonNode value : array(node)) { BigInteger parsed = integer(value); StrictJson.require(parsed != null, "integer array member cannot be null"); result.add(parsed); }
        return result;
    }
    private static Boolean bool(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isBoolean(), "actual JSON boolean required"); return node.booleanValue();
    }
    private static String text(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isTextual(), "actual JSON string required"); String value = node.textValue();
        if (!value.isEmpty()) { StrictJson.text(value); } return value;
    }
    private static void presenceNode(ObjectNode parent, String key, Presence presence) {
        switch (presence) { case MISSING -> { } case NULL -> parent.putNull(key); case VALUE -> parent.putObject(key); }
    }
}
