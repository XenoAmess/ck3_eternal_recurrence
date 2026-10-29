package org.xar.ck3.control.wave3.planning.participatingwar;

import static org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.StrictJson;

/** Deterministic default regressions plus an explicit original-module differential run. */
public final class ParticipatingWarThreatsRegression {
    private ParticipatingWarThreatsRegression() { }
    private record Case(String name, ObjectNode snapshot) { }
    private static int checks;
    private static final String ORIGINAL = """
            import sys,json
            from pathlib import Path
            sys.path.insert(0,str(Path(sys.argv[1])/'ck3_autonomous_player/src'))
            from xar_autoplayer.participating_war_threat_observation_v1 import observe_participating_war_threats_v1
            cases=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
            print(json.dumps([{'name':row['name'],'result':observe_participating_war_threats_v1(row['snapshot'])} for row in cases],sort_keys=True,separators=(',',':'),allow_nan=False))
            """;

    public static int verify() {
        int before = checks; List<Case> cases = cases();
        for (Case item : cases) {
            byte[] original = raw(item.snapshot()); Observation observation = ParticipatingWarThreatsCodec.observeSnapshot(original);
            equal(observation, ParticipatingWarThreatsCodec.decode(ParticipatingWarThreatsCodec.encode(observation)), item.name() + " typed JSON roundtrip");
            equal(new String(original, StandardCharsets.UTF_8), new String(raw(item.snapshot()), StandardCharsets.UTF_8), item.name() + " input unchanged");
            check(!observation.actionAuthorized() && observation.nonParticipantLiegeScope() == NonParticipantLiegeScope.UNASSESSED_NONPARTICIPANT_LIEGE_WARS, "no authority or unpublished-liege coverage");
        }
        Observed base = observed(base()); equal(List.of(10, 20), base.participatingWarIds(), "all wars"); equal(List.of(11, 12), base.uniqueEnemyArmyIds(), "enemy union");
        equal(List.of(10, 20), base.enemyArmyMemberships().getFirst().warIds(), "enemy membership retains both wars"); equal(new Known(BigInteger.valueOf(1000)), base.strength(), "unique counts");
        ObjectNode missing = base(); army(missing, 0, 0).remove("soldiers"); ObjectNode explicitNull = base(); army(explicitNull, 0, 0).putNull("soldiers");
        equal(new Unknown(Presence.MISSING), observed(missing).strength(), "missing soldiers"); equal(new Unknown(Presence.EXPLICIT_NULL), observed(explicitNull).strength(), "null soldiers");
        ObjectNode conflict = base(); army(conflict, 1, 0).put("soldiers", 301); equal(new Conflict(11), observed(conflict).strength(), "duplicate conflict");
        ObjectNode absentWars = base(); absentWars.remove("active_wars"); ObjectNode nullWars = base(); nullWars.putNull("active_wars"); ObjectNode emptyWars = base(); emptyWars.putArray("active_wars");
        equal(Presence.MISSING, ((Unavailable) projection(absentWars)).sourcePresence(), "missing array"); equal(Presence.EXPLICIT_NULL, ((Unavailable) projection(nullWars)).sourcePresence(), "null array");
        equal(new Known(BigInteger.ZERO), observed(emptyWars).strength(), "observed empty is zero");
        ObjectNode zeroArmy = base(); army(zeroArmy, 0, 0).put("army_id", 0); army(zeroArmy, 1, 0).put("army_id", 0); check(observed(zeroArmy).uniqueEnemyArmyIds().contains(0), "ArmyID zero retained");
        ObjectNode zeroWar = base(); war(zeroWar, 0).put("war_id", 0); check(projection(zeroWar) instanceof Unavailable, "raw WarID zero conservatively unassessed");
        ObjectNode large = base(); large.put("revision", StrictJson.UINT64_MAX); large.put("native_revision", StrictJson.UINT64_MAX); large.put("played_character_id", StrictJson.UINT64_MAX);
        JsonNode wire = StrictJson.parse(ParticipatingWarThreatsCodec.encode(projection(large))); equal(StrictJson.UINT64_MAX.toString(), wire.path("source_frame").path("revision").textValue(), "uint64 exact decimal string");
        for (String token : List.of("true", "1.0", "1e0", "\"1\"")) {
            ObjectNode parsed = (ObjectNode) StrictJson.parse(raw(base())); String text = new String(raw(parsed), StandardCharsets.UTF_8);
            byte[] invalid = text.replace("\"revision\":9", "\"revision\":" + token).getBytes(StandardCharsets.UTF_8);
            check(ParticipatingWarThreatsCodec.observeSnapshot(invalid) instanceof Unavailable, "native revision exact integer token " + token);
        }
        ObjectNode valid = (ObjectNode) StrictJson.parse(ParticipatingWarThreatsCodec.encode(base));
        ObjectNode extra = valid.deepCopy(); extra.put("approved", true); rejects(raw(extra), "extra observation field");
        ObjectNode missingField = valid.deepCopy(); missingField.remove("strength"); rejects(raw(missingField), "missing observation field");
        ObjectNode wrongType = valid.deepCopy(); ((ObjectNode) wrongType.get("source_frame")).put("revision", 9); rejects(raw(wrongType), "new uint64 wire rejects numeric alias");
        ObjectNode padded = valid.deepCopy(); ((ObjectNode) padded.get("source_frame")).put("revision", "09"); rejects(raw(padded), "canonical decimal spelling");
        ObjectNode forged = valid.deepCopy(); forged.put("action_authorized", true); rejects(raw(forged), "cannot forge authority");
        ObjectNode floatCount = valid.deepCopy(); ((ObjectNode) floatCount.get("strength")).put("soldiers", 1000.0); rejects(floatCount.toString().getBytes(StandardCharsets.UTF_8), "integer count not float");
        String duplicate = new String(raw(valid), StandardCharsets.UTF_8).replace("\"action_authorized\":false", "\"action_authorized\":false,\"action_authorized\":false"); rejects(duplicate.getBytes(StandardCharsets.UTF_8), "duplicate field");
        return checks - before;
    }

    /** Default CI consumes the actual accepted original bytes; absent resources are a failure. */
    public static void verifyCommittedOriginalGolden() throws IOException {
        try (var resource = ParticipatingWarThreatsRegression.class.getResourceAsStream("/participatingwar/original-producer-golden.json")) {
            if (resource == null) throw new IOException("committed actual original participant-war golden required");
            byte[] bytes = resource.readNBytes(262_145); if (bytes.length > 262_144) throw new IOException("committed original golden cap");
            compareOriginal(bytes);
        }
    }

    /** Explicit invocation only; default verification never starts Python or generates goldens. */
    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("repository existing-python new-scratch-directory root-verified-machine-id");
        StrictJson.text(args[3]); Path repository = Path.of(args[0]).toRealPath(); ArrayNode sourceBefore = sourceBindings(repository);
        int verified = verify(); Path scratch = Path.of(args[2]).toAbsolutePath(); if (Files.exists(scratch)) throw new IOException("new scratch required"); Files.createDirectories(scratch);
        ArrayNode inputs = StrictJson.object().putArray("cases"); List<Case> cases = cases();
        for (Case item : cases) { ObjectNode row = StrictJson.object(); row.put("name", item.name()); row.set("snapshot", item.snapshot()); inputs.add(row); }
        byte[] inputBytes = raw(inputs); if (inputBytes.length > ParticipatingWarThreatsCodec.MAX_BYTES) throw new IOException("original input cap");
        Path input = scratch.resolve("original-input.json"); Files.write(input, inputBytes, StandardOpenOption.CREATE_NEW);
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-", args[0], input.toString()); builder.directory(Path.of(args[0]).toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectError(scratch.resolve("original.stderr.txt").toFile()); Process process = builder.start();
        byte[] oracle;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var output = readers.submit(() -> process.getInputStream().readNBytes(262_145));
            try (var stdin = process.getOutputStream()) { stdin.write(ORIGINAL.getBytes(StandardCharsets.UTF_8)); }
            if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original oracle timeout"); }
            oracle = output.get(5, TimeUnit.SECONDS); if (process.exitValue() != 0) throw new IOException("original oracle exit " + process.exitValue());
            if (oracle.length > 262_144) throw new IOException("original oracle output cap");
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); } }
        Files.write(scratch.resolve("original-output.json"), oracle, StandardOpenOption.CREATE_NEW); compareOriginal(oracle);
        ArrayNode sourceAfter = sourceBindings(repository); equal(sourceBefore, sourceAfter, "actual original sources unchanged");
        ObjectNode receipt = StrictJson.object(); receipt.put("schema", "xar.g2.m5-participant-producer-regression.v1"); receipt.put("machine_id", args[3]); receipt.put("observed_at_utc", Instant.now().toString());
        receipt.put("status", "PASS"); receipt.put("default_assertions", verified); receipt.put("original_cases", cases.size()); receipt.put("total_assertions", checks); receipt.put("native_rpc_count", 0); receipt.put("game_days", 0);
        receipt.set("source_before", sourceBefore); receipt.set("source_after", sourceAfter); receipt.put("source_match", true);
        Files.write(scratch.resolve("ACTUAL.json"), StrictJson.canonical(receipt), StandardOpenOption.CREATE_NEW);
        System.out.println(new String(StrictJson.canonical(receipt), StandardCharsets.UTF_8));
    }

    private static void compareOriginal(byte[] original) {
        JsonNode expected = StrictJson.parse(original, ParticipatingWarThreatsCodec.MAX_BYTES); List<Case> cases = cases();
        equal(cases.size(), expected.size(), "all original cases returned");
        for (int index = 0; index < cases.size(); index++) {
            Case item = cases.get(index); equal(item.name(), expected.get(index).get("name").textValue(), "original case order");
            equal(expected.get(index).get("result"), originalView(projection(item.snapshot())), item.name() + " actual original producer differential");
        }
    }

    private static ArrayNode sourceBindings(Path repository) throws Exception {
        ArrayNode result = StrictJson.object().putArray("sources");
        for (String relative : List.of("ck3_autonomous_player/src/xar_autoplayer/participating_war_threat_observation_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py",
                "ck3_autonomous_player/native_bridge/src/ck3_12002_world.cpp",
                "ck3_autonomous_player/native_bridge/src/ck3_12004_world.cpp")) {
            byte[] bytes = Files.readAllBytes(repository.resolve(relative)); ObjectNode ref = StrictJson.object(); ref.put("path", repository.resolve(relative).toString()); ref.put("bytes", bytes.length);
            ref.put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); result.add(ref);
        }
        return result;
    }

    private static List<Case> cases() {
        List<Case> result = new ArrayList<>(); result.add(new Case("primary_and_nonprimary", base()));
        ObjectNode v = base(); v.putArray("active_wars"); result.add(new Case("observed_empty", v));
        v = base(); v.remove("active_wars"); result.add(new Case("missing_wars", v));
        v = base(); v.putNull("active_wars"); result.add(new Case("null_wars", v));
        v = base(); war(v, 1).putNull("enemy_armies"); result.add(new Case("null_enemy_array", v));
        v = base(); war(v, 1).remove("enemy_armies"); result.add(new Case("missing_enemy_array", v));
        v = base(); war(v, 1).put("war_id", 10); result.add(new Case("duplicate_war", v));
        v = base(); war(v, 0).put("war_id", 0); result.add(new Case("raw_zero_war_unassessed", v));
        v = base(); army(v, 0, 0).put("army_id", 0); army(v, 1, 0).put("army_id", 0); result.add(new Case("public_zero_army", v));
        v = base(); war(v, 1).putNull("player_is_primary_war_leader"); result.add(new Case("null_leadership", v));
        v = base(); war(v, 1).remove("player_is_primary_war_leader"); result.add(new Case("missing_leadership", v));
        v = base(); army(v, 1, 0).put("soldiers", 301); result.add(new Case("conflicting_duplicate", v));
        v = base(); army(v, 0, 0).remove("soldiers"); result.add(new Case("missing_soldiers", v));
        v = base(); army(v, 0, 0).putNull("soldiers"); result.add(new Case("null_soldiers", v));
        v = base(); army(v, 0, 0).put("soldiers", 300.0); result.add(new Case("floating_soldiers_unknown", v));
        v = base(); v.put("unconsumed_native_extension", 0.0); result.add(new Case("unconsumed_float_extension", v));
        v = base(); army(v, 0, 0).put("army_id", true); result.add(new Case("boolean_army_identity", v));
        v = base(); war(v, 0).put("war_id", 10.0); result.add(new Case("floating_war_identity", v));
        v = base(); v.putNull("episode_run_id"); result.add(new Case("missing_frame_identity", v));
        v = base(); v.put("paused", false); result.add(new Case("unpaused", v));
        v = base(); cache(v, true); result.add(new Case("fresh_strength_cache", v));
        v = base(); cache(v, false); result.add(new Case("stale_strength_cache_unknown", v));
        v = base(); cache(v, true); ((ArrayNode) v.get("army_strengths")).add(StrictJson.parse("{\"army_id\":true,\"scope_role\":null,\"status\":\"available\",\"current_soldiers\":999}".getBytes(StandardCharsets.UTF_8))); result.add(new Case("unrelated_malformed_cache_row", v));
        v = base(); cache(v, true); ((ArrayNode) v.get("army_strengths")).add(StrictJson.parse("{\"army_id\":true,\"scope_role\":\"active_war_enemy\",\"status\":\"available\",\"current_soldiers\":999}".getBytes(StandardCharsets.UTF_8))); result.add(new Case("unrelated_malformed_enemy_cache_identity", v));
        v = base(); cache(v, true); ((ArrayNode) v.get("army_strengths")).add(v.get("army_strengths").get(0).deepCopy()); result.add(new Case("duplicate_cache_uses_missing_fallback", v));
        v = base(); cache(v, true); ((ObjectNode) v.get("army_strengths").get(0)).put("scope_role", "player"); result.add(new Case("enemy_membership_survives_other_cache_role", v));
        v = base(); cache(v, true); v.putArray("active_wars"); ((ArrayNode) v.get("army_strengths")).add(StrictJson.parse("{\"army_id\":true,\"scope_role\":\"active_war_enemy\",\"status\":\"available\",\"current_soldiers\":999}".getBytes(StandardCharsets.UTF_8))); result.add(new Case("empty_scope_ignores_cache", v));
        v = base(); army(v, 0, 0).put("soldiers", BigInteger.TEN.pow(110)); army(v, 1, 0).put("soldiers", BigInteger.TEN.pow(110)); result.add(new Case("unbounded_soldier_integer", v));
        v = base(); v.put("revision", StrictJson.UINT64_MAX); v.put("native_revision", StrictJson.UINT64_MAX); result.add(new Case("uint64_frame", v));
        return List.copyOf(result);
    }
    private static void cache(ObjectNode root, boolean current) {
        for (JsonNode war : root.get("active_wars")) for (JsonNode army : war.get("enemy_armies")) ((ObjectNode) army).putNull("soldiers");
        root.put("army_strengths_status", "available"); root.put("army_strengths_queried_snapshot_id", "native:7"); root.put("army_strengths_queried_revision", current ? 9 : 8);
        root.set("army_strengths", StrictJson.parse("[{\"army_id\":11,\"scope_role\":\"active_war_enemy\",\"war_ids\":[10,20],\"status\":\"available\",\"current_soldiers\":300},{\"army_id\":12,\"scope_role\":\"active_war_enemy\",\"war_ids\":[20],\"status\":\"available\",\"current_soldiers\":700}]".getBytes(StandardCharsets.UTF_8)));
    }
    private static ObjectNode base() { return (ObjectNode) StrictJson.parse("""
            {"snapshot_id":"native:7","revision":9,"native_revision":7,"date_raw":53144328,"episode_run_id":"synthetic-participating-scope","paused":true,"map_ready":true,"played_character":{"character_id":31254,"alive":true},"player_armies":[],"active_wars":[{"war_id":10,"source":"native","player_side":"defender","player_is_primary_war_leader":true,"player_relative_war_score":-30,"targeted_title_ids":[2230],"enemy_armies":[{"army_id":11,"soldiers":300}]},{"war_id":20,"source":"native","player_side":"defender","player_is_primary_war_leader":false,"player_relative_war_score":-80,"enemy_armies":[{"army_id":11,"soldiers":300},{"army_id":12,"soldiers":700}]}]}
            """.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode war(ObjectNode root, int index) { return (ObjectNode) root.get("active_wars").get(index); }
    private static ObjectNode army(ObjectNode root, int war, int index) { return (ObjectNode) war(root, war).get("enemy_armies").get(index); }
    private static Observation projection(ObjectNode value) { return ParticipatingWarThreatsCodec.observeSnapshot(raw(value)); }
    private static Observed observed(ObjectNode value) { return (Observed) projection(value); }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static void rejects(byte[] value, String name) { boolean rejected = false; try { ParticipatingWarThreatsCodec.decode(value); } catch (IllegalArgumentException expected) { rejected = true; } check(rejected, name); }
    private static void check(boolean condition, String name) { checks++; if (!condition) throw new AssertionError(name); }
    private static void equal(Object expected, Object actual, String name) { checks++; if (!java.util.Objects.equals(expected, actual)) throw new AssertionError(name + " expected=" + expected + " actual=" + actual); }

    /** Test-only explicit projection to the legacy numeric JSON domain for differential comparison. */
    private static ObjectNode originalView(Observation observation) {
        ObjectNode root = StrictJson.object(); root.put("schema", "xar.participating-war-threat-observation.v1"); root.put("read_only", true); root.put("scope", "opposing armies in published player-participant wars only");
        root.put("unraised_or_future_enemy_reserves_bounded", false); root.put("unpublished_liege_wars_covered", false); root.put("defeat_title_transfer_verified", false); root.putNull("battle_win_probability"); root.put("action_authorized", false);
        ObjectNode encoded = (ObjectNode) StrictJson.parse(ParticipatingWarThreatsCodec.encode(observation)); JsonNode frame = encoded.get("source_frame").deepCopy();
        if (!frame.isNull()) for (String field : List.of("played_character_id", "native_revision", "date_raw", "revision")) ((ObjectNode) frame).put(field, new BigInteger(frame.get(field).textValue()));
        root.set("source_frame", frame); root.set("status", encoded.get("status"));
        for (String field : List.of("participating_war_ids", "primary_war_ids", "non_primary_war_ids", "leadership_unknown_war_ids", "enemy_army_memberships", "unique_enemy_army_ids")) root.set(field, encoded.get(field));
        if (observation instanceof Observed value) {
            root.put("reason", "published_participating_war_scope_aggregated"); root.put("leadership_scope_complete", value.leadershipScopeComplete());
            if (value.strength() instanceof Known known) root.put("observed_enemy_raised_soldiers", known.soldiers()); else root.putNull("observed_enemy_raised_soldiers");
            root.put("strength_status", value.strength() instanceof Known ? "available" : "unavailable_or_conflicting");
        } else { root.set("reason", encoded.get("reason")); root.putNull("observed_enemy_raised_soldiers"); }
        return root;
    }
}
