package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.StrictJson;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Actual service and original stable joins -> the full shared Java snapshot and public slice. */
final class ArmyStateMigrationTest {
    @Test void actualOriginalWarStateAndJoinsMatchFullSnapshotAcrossActivePostwarAndIdle() throws Exception {
        verifyOriginals();
        ObjectNode request = ArmyJson.empty(); var rows = request.putArray("cases");
        ObjectNode active = snapshot("active");
        ObjectNode explicit = army(0, 11, 101); active.putArray("player_armies").add(explicit).add(explicit.deepCopy());
        ObjectNode war = war(BigInteger.ZERO, BigInteger.valueOf(-37));
        war.putArray("allied_armies").add(army(0, 11, 999)).add(army(2, 11, 202)).add(army(3, 12, 303).put("controllable", false));
        war.putArray("enemy_armies").add(army(4, 12, 404)).add(army(4, 12, 405));
        active.putArray("active_wars").add(war).add(war.deepCopy());
        active.putArray("war_termination_options").add("retained original item").addNull().add(7);
        active.putObject("war_termination_terms").put("not", "a-list");
        active.put("war_termination_exit_terms", "not-a-list");
        active.putArray("army_strengths").addObject().put("unknown_field_retained", true);
        active.putNull("army_strengths_status"); active.put("army_strengths_query_sequence", 88);
        rows.add(active);
        ObjectNode postwar = snapshot("postwar"); postwar.putNull("active_wars"); postwar.putArray("player_armies").add(army(7, 11, 707)); rows.add(postwar);
        ObjectNode idle = snapshot("idle"); idle.putArray("active_wars"); idle.putNull("player_armies"); rows.add(idle);
        ObjectNode wide = snapshot("wide"); BigInteger huge = BigInteger.ONE.shiftLeft(90).add(BigInteger.valueOf(73));
        ObjectNode wideWar = war(huge, huge.negate()); wideWar.put("primary_opponent_character_id", huge);
        wideWar.putArray("targeted_title_ids").add(huge).add(huge);
        ObjectNode wideArmy = army(8, 11, 808).put("owner_character_id", huge).put("soldiers", huge).put("current_province_id", huge);
        wideWar.putArray("allied_armies").add(wideArmy); wide.putArray("active_wars").add(wideWar); rows.add(wide);
        ObjectNode routes = snapshot("routes"); ObjectNode routed = army(9, 11, 909).put("move_target_province_id", 25).put("move_target_observable", true);
        routed.putArray("route_province_ids").add(24).add(25); routed.put("route_read_status", "complete_nonempty").put("route_source_count", 2);
        routed.putNull("siege_days_left"); routed.put("siege_province_holder_character_id", 12).put("siege_province_in_player_subrealm", false);
        routes.putArray("player_armies").add(routed); rows.add(routes);
        ObjectNode original = BattleOriginalOracle.call("""
                import json,sys
                from types import SimpleNamespace
                from xar_autoplayer.bridge.service import GameplayBridgeService
                from xar_autoplayer.bridge.war_contract import normalize_active_wars,player_armies_from_state,enemy_armies_from_wars
                value=json.load(sys.stdin);out=[]
                for snapshot in value['cases']:
                    wars=normalize_active_wars(snapshot.get('active_wars'))
                    result=GameplayBridgeService.war_state(SimpleNamespace(snapshot=lambda:snapshot))
                    out.append({'war_state':result,'players':player_armies_from_state(wars,snapshot.get('player_armies')),
                                'enemies':enemy_armies_from_wars(wars)})
                print(json.dumps({'cases':out},allow_nan=False))
                """, request);
        verifyOriginals();
        for (int i = 0; i < rows.size(); i++) {
            ObjectNode input = (ObjectNode) rows.get(i); JsonNode expected = original.path("cases").get(i);
            var result = ArmySnapshotCodec.state(ArmyJson.bytes(input), input.path("snapshot_id").textValue(), BigInteger.valueOf(3), BigInteger.valueOf(4));
            assertEquals(expected.path("war_state"), ArmyJson.parse(ArmySnapshotCodec.encode(result).bytes()));
            var wars = NativeActiveWarsCodec.normalize(input.get("active_wars"));
            sameJson(expected.path("players"), NativeArmiesCodec.encode(ArmyStateProjection.playerArmiesFromState(wars, input.get("player_armies"))));
            sameJson(expected.path("enemies"), NativeArmiesCodec.encode(ArmyStateProjection.enemyArmiesFromWars(wars)));
            assertEquals(result, ArmySnapshotCodec.state(ArmyJson.bytes(input), result.snapshotId(), result.revision(), result.nativeRevision()));
        }
        assertEquals(101, ArmySnapshotCodec.state(ArmyJson.bytes(active), "active", BigInteger.valueOf(3), BigInteger.valueOf(4))
                .playerArmies().getFirst().soldiers().orElseThrow().intValueExact(), "first original occurrence wins");
    }
    @Test void malformedOriginalDomainsAndCrossedFrameCannotReachFullSnapshotConsumer() {
        ObjectNode raw = snapshot("invalid"); ObjectNode row = army(2, 11, 22); raw.putArray("player_armies").add(row);
        row.put("army_id", true); assertThrows(IllegalArgumentException.class, () -> decode(raw)); row.put("army_id", 2);
        row.put("move_target_observable", true).put("move_target_province_id", 12);
        row.putArray("route_province_ids").add(12); row.put("route_read_status", "complete_nonempty");
        assertThrows(IllegalArgumentException.class, () -> decode(raw), "paired original count cannot be invented");
        row.put("route_source_count", 1); decode(raw);
        raw.put("revision", 4); assertThrows(IllegalArgumentException.class, () -> decode(raw)); raw.put("revision", 3);
        raw.put("native_revision", 5); assertThrows(IllegalArgumentException.class, () -> decode(raw)); raw.put("native_revision", 4);
        ObjectNode war = war(BigInteger.ONE, BigInteger.ZERO); war.put("war_id", 1.0); raw.putArray("active_wars").add(war);
        assertThrows(IllegalArgumentException.class, () -> decode(raw));
    }
    private static ArmyResponses.WarState decode(ObjectNode n) {
        return ArmySnapshotCodec.state(ArmyJson.bytes(n), n.path("snapshot_id").textValue(), BigInteger.valueOf(3), BigInteger.valueOf(4));
    }
    private static ObjectNode snapshot(String id) {
        ObjectNode n = ArmyJson.empty().put("snapshot_id", id).put("revision", 3).put("native_revision", 4).put("date_raw", 77).put("backend_id", "native-original");
        n.putObject("played_character").put("character_id", 11); return n;
    }
    private static ObjectNode army(int id, int owner, int soldiers) {
        return ArmyJson.empty().put("army_id", id).put("owner_character_id", owner).put("soldiers", soldiers).put("controllable", true);
    }
    private static ObjectNode war(BigInteger id, BigInteger score) {
        return ArmyJson.empty().put("war_id", id).put("player_side", "attacker").put("player_relative_war_score", score);
    }
    private static void verifyOriginals() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        if (configured == null || configured.isBlank()) throw new IllegalStateException("required original producer root absent");
        Path root = Path.of(configured).toRealPath();
        String[][] pins = {
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py", "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py", "ae960cc6a928eb9d26f2f9c93f30463a978951c374021558d08860c8f9125b2a"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py", "0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e"}};
        for (String[] pin : pins) {
            Path actual = root.resolve(pin[0]).toRealPath(); assertTrue(actual.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(actual))), "original full snapshot source drift");
        }
    }
    private static void sameJson(JsonNode expected, JsonNode actual) {
        assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8), new String(StrictJson.canonical(actual), StandardCharsets.UTF_8));
    }
}
