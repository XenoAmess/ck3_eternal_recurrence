package org.xar.ck3.control.wave2.military.realmsiege;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Assessment;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Diagnostics;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Enemy;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.EnemyCollection;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.EnemyReference;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.IntegerField;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.PlayedCharacter;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Presence;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Request;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Snapshot;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.War;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.WarCollection;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.WarReference;

/** Only the wrapper is exact; SDK snapshot/war/army extension containers are declared projections. */
public final class RealmSiegeCodec {
    public static final int INPUT_MAX_BYTES = 65_536;
    private RealmSiegeCodec() { }

    public static byte[] evaluate(byte[] raw) { return encodeAssessment(RealmSiegePolicy.assess(decode(raw))); }
    public static Request decode(byte[] raw) { return decodeNode(StrictJson.parse(raw, INPUT_MAX_BYTES)); }

    public static Request decodeNode(JsonNode root) {
        ObjectNode value = StrictJson.object(root, Set.of("schema", "snapshot", "detached_wars", "detached_enemies",
                "candidate_war_ref", "candidate_enemy_ref"));
        StrictJson.require(RealmSiegePolicy.INPUT_SCHEMA.equals(StrictJson.text(value.get("schema"))), "unsupported realm siege schema");
        return new Request(snapshot(value.get("snapshot")), wars(value.get("detached_wars"), false),
                enemies(value.get("detached_enemies"), false), warReference(value.get("candidate_war_ref")),
                enemyReference(value.get("candidate_enemy_ref")));
    }

    private static Snapshot snapshot(JsonNode node) {
        ObjectNode value = projection(node);
        PlayedCharacter played = null;
        if (present(value.get("played_character"))) {
            ObjectNode actor = projection(value.get("played_character"));
            played = new PlayedCharacter(text(actor.get("source")), integer(actor.get("character_id")), bool(actor.get("alive")));
        }
        Diagnostics diagnostics = null;
        if (present(value.get("diagnostics"))) {
            ObjectNode diag = projection(value.get("diagnostics"));
            diagnostics = new Diagnostics(bool(diag.get("connected")), integer(diag.get("bridge_pid")), integer(diag.get("connection_generation")));
        }
        return new Snapshot(text(value.get("source")), integer(value.get("native_revision")), text(value.get("snapshot_id")),
                integer(value.get("revision")), integer(value.get("date_raw")), text(value.get("episode_run_id")),
                bool(value.get("paused")), bool(value.get("map_ready")), presence(value.get("active_event")),
                presence(value.get("pending_character_interaction")), played, diagnostics, wars(value.get("active_wars"), true));
    }

    private static List<War> wars(JsonNode node, boolean nullable) {
        if (nullable && !present(node)) { return null; }
        List<War> result = new ArrayList<>();
        for (JsonNode row : array(node)) {
            ObjectNode value = projection(row);
            result.add(new War(text(value.get("source")), integer(value.get("war_id")), text(value.get("player_side")),
                    bool(value.get("player_is_primary_war_leader")), integer(value.get("player_relative_war_score")),
                    enemies(value.get("enemy_armies"), true)));
        }
        return result;
    }

    private static List<Enemy> enemies(JsonNode node, boolean nullable) {
        if (nullable && !present(node)) { return null; }
        List<Enemy> result = new ArrayList<>();
        for (JsonNode row : array(node)) {
            ObjectNode value = projection(row);
            JsonNode target = value.get("move_target_province_id");
            List<BigInteger> route = null;
            if (present(value.get("route_province_ids"))) {
                route = new ArrayList<>();
                for (JsonNode province : array(value.get("route_province_ids"))) {
                    BigInteger parsed = integer(province);
                    StrictJson.require(parsed != null, "route province cannot be null"); route.add(parsed);
                }
            }
            result.add(new Enemy(text(value.get("source")), integer(value.get("army_id")), integer(value.get("owner_character_id")),
                    bool(value.get("controllable")), text(value.get("army_state")), integer(value.get("army_state_code")),
                    bool(value.get("in_combat")), bool(value.get("retreating")), integer(value.get("current_province_id")),
                    bool(value.get("siege_province_in_player_subrealm")), new IntegerField(presence(target), integer(target)),
                    route, text(value.get("route_read_status"))));
        }
        return result;
    }

    private static WarReference warReference(JsonNode node) {
        if (node.isNull()) { return null; }
        ObjectNode value = StrictJson.object(node, Set.of("collection", "index"));
        String collection = StrictJson.text(value.get("collection"));
        WarCollection kind = switch (collection) {
            case "active_wars" -> WarCollection.ACTIVE_WARS;
            case "detached_wars" -> WarCollection.DETACHED_WARS;
            default -> throw new IllegalArgumentException("war reference must resolve inside this document");
        };
        return new WarReference(kind, index(value.get("index")));
    }
    private static EnemyReference enemyReference(JsonNode node) {
        if (node.isNull()) { return null; }
        ObjectNode value = StrictJson.object(node, Set.of("collection", "index"));
        String collection = StrictJson.text(value.get("collection"));
        EnemyCollection kind = switch (collection) {
            case "candidate_war_enemy_armies" -> EnemyCollection.CANDIDATE_WAR_ENEMIES;
            case "detached_enemies" -> EnemyCollection.DETACHED_ENEMIES;
            default -> throw new IllegalArgumentException("enemy reference must resolve inside this document");
        };
        return new EnemyReference(kind, index(value.get("index")));
    }

    public static byte[] encodeRequest(Request request) {
        ObjectNode result = StrictJson.object(); result.put("schema", RealmSiegePolicy.INPUT_SCHEMA);
        result.set("snapshot", snapshotNode(request.snapshot()));
        result.set("detached_wars", warsNode(request.detachedWars())); result.set("detached_enemies", enemiesNode(request.detachedEnemies()));
        if (request.candidateWarRef() == null) { result.putNull("candidate_war_ref"); }
        else {
            ObjectNode reference = result.putObject("candidate_war_ref");
            reference.put("collection", request.candidateWarRef().collection() == WarCollection.ACTIVE_WARS ? "active_wars" : "detached_wars");
            reference.put("index", request.candidateWarRef().index());
        }
        if (request.candidateEnemyRef() == null) { result.putNull("candidate_enemy_ref"); }
        else {
            ObjectNode reference = result.putObject("candidate_enemy_ref");
            reference.put("collection", request.candidateEnemyRef().collection() == EnemyCollection.CANDIDATE_WAR_ENEMIES
                    ? "candidate_war_enemy_armies" : "detached_enemies"); reference.put("index", request.candidateEnemyRef().index());
        }
        return StrictJson.canonical(result, INPUT_MAX_BYTES);
    }

    private static ObjectNode snapshotNode(Snapshot snapshot) {
        ObjectNode result = StrictJson.object(); result.put("source", snapshot.source()); result.put("native_revision", snapshot.nativeRevision());
        result.put("snapshot_id", snapshot.snapshotId()); result.put("revision", snapshot.revision()); result.put("date_raw", snapshot.dateRaw());
        result.put("episode_run_id", snapshot.episodeRunId()); result.put("paused", snapshot.paused()); result.put("map_ready", snapshot.mapReady());
        presenceNode(result, "active_event", snapshot.activeEvent()); presenceNode(result, "pending_character_interaction", snapshot.pendingCharacterInteraction());
        if (snapshot.playedCharacter() == null) { result.putNull("played_character"); }
        else {
            PlayedCharacter actor = snapshot.playedCharacter(); ObjectNode played = result.putObject("played_character");
            played.put("source", actor.source()); played.put("character_id", actor.characterId()); played.put("alive", actor.alive());
        }
        if (snapshot.diagnostics() == null) { result.putNull("diagnostics"); }
        else {
            Diagnostics diag = snapshot.diagnostics(); ObjectNode diagnostics = result.putObject("diagnostics");
            diagnostics.put("connected", diag.connected()); diagnostics.put("bridge_pid", diag.bridgePid());
            diagnostics.put("connection_generation", diag.connectionGeneration());
        }
        if (snapshot.activeWars() == null) { result.putNull("active_wars"); }
        else { result.set("active_wars", warsNode(snapshot.activeWars())); }
        return result;
    }

    private static ArrayNode warsNode(List<War> wars) {
        ArrayNode result = StrictJson.object().putArray("rows");
        for (War war : wars) {
            ObjectNode value = result.addObject(); value.put("source", war.source()); value.put("war_id", war.warId());
            value.put("player_side", war.playerSide()); value.put("player_is_primary_war_leader", war.playerIsPrimaryWarLeader());
            value.put("player_relative_war_score", war.playerRelativeWarScore());
            if (war.enemyArmies() == null) { value.putNull("enemy_armies"); }
            else { value.set("enemy_armies", enemiesNode(war.enemyArmies())); }
        }
        return result;
    }
    private static ArrayNode enemiesNode(List<Enemy> enemies) {
        ArrayNode result = StrictJson.object().putArray("rows");
        for (Enemy enemy : enemies) {
            ObjectNode value = result.addObject(); value.put("source", enemy.source()); value.put("army_id", enemy.armyId());
            value.put("owner_character_id", enemy.ownerCharacterId()); value.put("controllable", enemy.controllable());
            value.put("army_state", enemy.armyState()); value.put("army_state_code", enemy.armyStateCode());
            value.put("in_combat", enemy.inCombat()); value.put("retreating", enemy.retreating());
            value.put("current_province_id", enemy.currentProvinceId()); value.put("siege_province_in_player_subrealm", enemy.siegeProvinceInPlayerSubrealm());
            switch (enemy.moveTargetProvinceId().presence()) {
                case MISSING -> { }
                case NULL -> value.putNull("move_target_province_id");
                case VALUE -> value.put("move_target_province_id", enemy.moveTargetProvinceId().value());
            }
            if (enemy.routeProvinceIds() == null) { value.putNull("route_province_ids"); }
            else { ArrayNode route = value.putArray("route_province_ids"); enemy.routeProvinceIds().forEach(route::add); }
            value.put("route_read_status", enemy.routeReadStatus());
        }
        return result;
    }

    public static byte[] encodeAssessment(Assessment assessment) {
        ObjectNode result = StrictJson.object(); result.put("schema", RealmSiegePolicy.OUTPUT_SCHEMA);
        result.put("candidate_enemy_scope_observed", assessment.candidateEnemyScopeObserved());
        result.put("candidate_war_scope_observed", assessment.candidateWarScopeObserved());
        ArrayNode wars = result.putArray("current_war_scopes_in_stored_order");
        for (RealmSiegePolicy.WarScope scope : assessment.currentWarScopesInStoredOrder()) {
            ObjectNode row = wars.addObject(); row.put("war_id", scope.warId()); row.put("scope_observed", scope.scopeObserved());
            ArrayNode enemies = row.putArray("enemy_scopes_in_stored_order"); scope.enemyScopesInStoredOrder().forEach(enemies::add);
        }
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }

    private static ObjectNode projection(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "SDK extension container must be an object"); return (ObjectNode) node;
    }
    private static JsonNode array(JsonNode node) { StrictJson.require(node != null && node.isArray(), "array required"); return node; }
    private static boolean present(JsonNode node) { return node != null && !node.isNull(); }
    private static Presence presence(JsonNode node) { return node == null ? Presence.MISSING : node.isNull() ? Presence.NULL : Presence.VALUE; }
    private static BigInteger integer(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isIntegralNumber(), "exact integer required; bool, float and string are rejected"); return node.bigIntegerValue();
    }
    private static Boolean bool(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isBoolean(), "actual boolean required"); return node.booleanValue();
    }
    private static String text(JsonNode node) {
        if (!present(node)) { return null; }
        StrictJson.require(node.isTextual(), "actual string required");
        String value = node.textValue(); if (!value.isEmpty()) { StrictJson.text(value); } return value;
    }
    private static int index(JsonNode node) { return (int) StrictJson.integer(node, 0, Integer.MAX_VALUE); }
    private static void presenceNode(ObjectNode parent, String field, Presence presence) {
        switch (presence) { case MISSING -> { } case NULL -> parent.putNull(field); case VALUE -> parent.putObject(field); }
    }
}
