package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatCore.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Complete immutable adapter for the normalized fixed-contact base input. */
public final class CombatInputs {
    private CombatInputs() { }
    public enum Role { ATTACKER, DEFENDER }
    public enum Coalition { PLAYER_OR_ALLIED, ENEMY }
    public record CounterTarget(BigInteger classIndex, BigInteger effectivenessRaw) { }
    public record RegimentCounter(BigInteger classIndex, BigInteger currentChunkRaw, BigInteger stackSizeSoldiers, List<CounterTarget> targets) { public RegimentCounter { targets = List.copyOf(targets); } }
    public record Stats(BigInteger maxSize, BigInteger siegeValueRaw, BigInteger damageRaw, BigInteger toughnessRaw, BigInteger pursuitRaw, BigInteger screenRaw) { }
    public record Regiment(BigInteger regimentId, RegimentKind kind, String maaTypeKey, BigInteger currentSoldiers,
            BigInteger maximumSoldiers, boolean fightsInMainPhase, Stats stats, RegimentCounter counter) {
        public Entry toInitialCombatState() { BigInteger raw = currentSoldiers.multiply(SCALE); return new Entry(regimentId, kind, fightsInMainPhase ? raw : ZERO, fightsInMainPhase ? ZERO : raw, stats.toughnessRaw(), stats.pursuitRaw(), stats.screenRaw(), List.of()); }
    }
    public record Commander(BigInteger characterId, BigInteger genericAdvantagePoints, BigInteger effectiveMinRoll, BigInteger effectiveMaxRoll) { }
    public record Knight(BigInteger characterId, BigInteger sourceRegimentId, BigInteger nativeArmyId, BigInteger prowess,
            BigInteger effectivenessRaw, BigInteger damageRaw, BigInteger toughnessRaw) { }
    public record Army(BigInteger publicArmyId, BigInteger nativeArmyId, Role encounterRole, Coalition coalitionSide,
            String scopeRole, BigInteger ownerCharacterId, BigInteger currentProvinceId, Commander commander, List<Regiment> regiments, List<Knight> knights) {
        public Army { regiments = List.copyOf(regiments); knights = List.copyOf(knights); }
        public BigInteger currentSoldiers() { BigInteger sum = ZERO; for (var r : regiments) sum = sum.add(r.currentSoldiers()); return sum; }
        public BigInteger mainPhaseSoldiers() { BigInteger sum = ZERO; for (var r : regiments) if (r.fightsInMainPhase()) sum = sum.add(r.currentSoldiers()); return sum; }
    }
    public record CounterResolution(Coalition counteredSide, Coalition counteringSide, BigInteger counteredOwnerCharacterId,
            BigInteger counteringOwnerCharacterId, BigInteger contextScaleRaw, List<BigInteger> damageRetentionByClassRaw) { public CounterResolution { damageRetentionByClassRaw = List.copyOf(damageRetentionByClassRaw); } }
    public enum Crossing { NONE, STRAIT, RIVER, LARGE_RIVER }
    public record Encounter(BigInteger targetProvinceId, BigInteger attackerEntryProvinceId, Coalition attackerSide, Coalition defenderSide,
            List<BigInteger> attackerArmyIds, List<BigInteger> defenderArmyIds, String participantPolicy, String terrainKey,
            BigInteger terrainWidthMultiplierRaw, Crossing crossingKind, boolean holdingDefender, BigInteger baseWidth, BigInteger finalWidth) {
        public Encounter { attackerArmyIds = List.copyOf(attackerArmyIds); defenderArmyIds = List.copyOf(defenderArmyIds); }
    }
    public record Capture(ObjectNode source) {
        public Capture { source = source.deepCopy(); JsonNode snapshot = source.get("snapshot_id"); require(absentOrNull(snapshot) || snapshot.isTextual(), "capture.snapshot_id must be string/null");
            for (String key : List.of("revision", "native_revision", "date_raw")) if (source.has(key)) integer(source.get(key), "capture." + key); }
        @Override public ObjectNode source() { return source.deepCopy(); }
        public String snapshotId() { JsonNode value = source.get("snapshot_id"); return absentOrNull(value) ? null : value.textValue(); }
        public BigInteger revision() { return source.has("revision") ? source.get("revision").bigIntegerValue() : null; }
        public BigInteger nativeRevision() { return source.has("native_revision") ? source.get("native_revision").bigIntegerValue() : null; }
        public BigInteger dateRaw() { return source.has("date_raw") ? source.get("date_raw").bigIntegerValue() : null; }
        public static Capture empty() { return new Capture(object()); }
    }
    public record Frozen(String inputSha256, Encounter encounter, List<Army> armies, List<CounterResolution> counterResolutions,
            boolean inputObservationReady, boolean nativeMonteCarloReady, List<String> nativeMissingRequiredDomains, Capture capture) {
        public Frozen { armies = List.copyOf(armies); counterResolutions = List.copyOf(counterResolutions); nativeMissingRequiredDomains = List.copyOf(nativeMissingRequiredDomains); Objects.requireNonNull(capture); }
        public List<Army> armiesForSide(Coalition side) { return armies.stream().filter(a -> a.coalitionSide() == side).toList(); }
        public List<Regiment> regimentsForSide(Coalition side) { return armiesForSide(side).stream().flatMap(a -> a.regiments().stream()).toList(); }
        public List<Entry> initialEntriesForSide(Coalition side) { return regimentsForSide(side).stream().map(Regiment::toInitialCombatState).toList(); }
        private CounterResolution resolution(Coalition side) { return counterResolutions.stream().filter(r -> r.counteredSide() == side).findFirst().orElseThrow(() -> new CombatInputException("no counter resolution for " + side)); }
        public List<BigInteger> dynamicCounterRetentionByClassRaw(Coalition side, List<Entry> own, List<Entry> other) {
            var resolution = resolution(side); var regiments = regimentsForSide(side); var enemies = regimentsForSide(resolution.counteringSide());
            validateEntryCensus(regiments, own); validateEntryCensus(enemies, other); int count = resolution.damageRetentionByClassRaw().size();
            var pressure = new ArrayList<BigInteger>(); var chunks = new ArrayList<BigInteger>(); for (int i = 0; i < count; i++) { pressure.add(ZERO); chunks.add(ZERO); }
            BigInteger context = ZERO.max(resolution.contextScaleRaw());
            for (int i = 0; i < regiments.size(); i++) {
                var r = regiments.get(i); var e = own.get(i); if (r.counter() == null || e.currentRaw().signum() <= 0) continue;
                int index = index(r.counter().classIndex(), count); chunks.set(index, chunks.get(index).add(fixedDiv(e.currentRaw(), r.counter().stackSizeSoldiers().multiply(SCALE))));
            }
            for (int i = 0; i < enemies.size(); i++) {
                var r = enemies.get(i); var e = other.get(i); if (r.counter() == null || e.currentRaw().signum() <= 0) continue;
                BigInteger chunk = fixedDiv(e.currentRaw(), r.counter().stackSizeSoldiers().multiply(SCALE));
                for (var target : r.counter().targets()) { int index = index(target.classIndex(), count); pressure.set(index, pressure.get(index).add(mul(mul(chunk, target.effectivenessRaw()), context))); }
            }
            var retention = new ArrayList<BigInteger>();
            for (int i = 0; i < count; i++) retention.add(chunks.get(i).signum() <= 0 ? SCALE : SCALE.subtract(mul(SCALE.min(fixedDiv(fixedDiv(pressure.get(i), chunks.get(i)), n(200_000))), n(90_000))));
            return List.copyOf(retention);
        }
        public BigInteger counterAdjustedDamageRaw(Coalition side) {
            var retention = resolution(side).damageRetentionByClassRaw(); BigInteger total = ZERO;
            for (var r : regimentsForSide(side)) if (r.fightsInMainPhase()) { BigInteger damage = r.stats().damageRaw(); if (r.counter() != null) damage = mul(damage, retention.get(index(r.counter().classIndex(), retention.size()))); total = total.add(mul(damage, r.currentSoldiers().multiply(SCALE))); }
            return total;
        }
        public BigInteger counterAdjustedCurrentDamageRaw(Coalition side, List<Entry> own, List<Entry> other, Map<BigInteger, BigInteger> effectiveDamage) {
            var regiments = regimentsForSide(side); validateEntryCensus(regiments, own);
            var expected = new HashSet<BigInteger>(); for (var r : regiments) if (r.fightsInMainPhase()) expected.add(r.regimentId());
            require(effectiveDamage.keySet().equals(expected) && effectiveDamage.values().stream().allMatch(v -> v != null && v.signum() >= 0), "current effective-damage census drifted");
            require(own.stream().allMatch(e -> e.currentRaw().signum() >= 0), "current fighting men must be nonnegative");
            var retention = dynamicCounterRetentionByClassRaw(side, own, other); BigInteger total = ZERO;
            for (int i = 0; i < regiments.size(); i++) { var r = regiments.get(i); var e = own.get(i); if (!r.fightsInMainPhase() || e.currentRaw().signum() == 0) continue;
                BigInteger damage = effectiveDamage.get(r.regimentId()); if (r.counter() != null) damage = mul(damage, retention.get(index(r.counter().classIndex(), retention.size()))); total = total.add(mul(damage, e.currentRaw())); }
            return total;
        }
    }
    static int index(BigInteger value, int count) { require(value.signum() >= 0 && value.compareTo(n(count)) < 0, "counter class outside resolution"); return value.intValueExact(); }
    static void validateEntryCensus(List<Regiment> regiments, List<Entry> entries) {
        require(regiments.size() == entries.size(), "entry/input census drifted");
        for (int i = 0; i < regiments.size(); i++) require(regiments.get(i).regimentId().equals(entries.get(i).regimentId()), "entry/input stored order drifted");
    }
    private static Regiment parseRegiment(JsonNode value, BigInteger target, String name) {
        var row = object(value, name); available(row, name); require(yes(row.get("identity_valid")), name + " identity is not valid");
        BigInteger id = positiveInteger(row.get("regiment_id"), name), current = integer(row.get("current_soldiers"), name), maximum = integer(row.get("maximum_soldiers"), name);
        require(current.signum() >= 0 && maximum.signum() >= 0, name + " soldier counts must be nonnegative");
        var kindRow = object(row.get("kind"), name); available(kindRow, name); RegimentKind kind;
        if (is(kindRow.get("value"), "levy")) kind = RegimentKind.LEVY; else if (is(kindRow.get("value"), "men_at_arms")) kind = RegimentKind.MEN_AT_ARMS; else throw new CombatInputException(name + ".kind is unsupported");
        boolean fights = bool(row.get("fights_in_main_phase"), name); var maa = object(row.get("maa_type"), name); String maaKey = null;
        if (is(maa.get("status"), "available")) { maaKey = text(maa.get("key"), name); require(!maaKey.isEmpty(), "invalid maa key"); } else require(is(maa.get("status"), "absent"), "maa unavailable");
        var stats = object(row.get("effective_stats"), name); available(stats, name); scale(stats, name);
        require(positiveInteger(stats.get("source_target_province_id"), name).equals(target), "effective target drifted");
        var typedStats = new Stats(integer(stats.get("max_size"), name), integer(stats.get("siege_value_raw"), name), integer(stats.get("damage_raw"), name), integer(stats.get("toughness_raw"), name), integer(stats.get("pursuit_raw"), name), integer(stats.get("screen_raw"), name));
        var counter = object(row.get("counter"), name); RegimentCounter typedCounter = null;
        if (is(counter.get("status"), "available")) {
            scale(counter, name); BigInteger chunk = positiveInteger(counter.get("current_chunk_raw"), name); require(positive(current), "cannot recover stack from nonpositive current");
            BigInteger[] qr = current.multiply(SCALE).divideAndRemainder(chunk); require(positive(qr[0]) && qr[1].signum() == 0 && fixedDiv(current.multiply(SCALE), qr[0].multiply(SCALE)).equals(chunk), "counter initial chunk is not exactly stack-invertible");
            var targets = new ArrayList<CounterTarget>(); for (var raw : elements(counter.get("targets"), name)) { var t = object(raw, name); targets.add(new CounterTarget(integer(t.get("class_index"), name), integer(t.get("effectiveness_raw"), name))); }
            typedCounter = new RegimentCounter(integer(counter.get("class_index"), name), chunk, qr[0], targets);
        } else require(is(counter.get("status"), "absent"), "counter unavailable");
        return new Regiment(id, kind, maaKey, current, maximum, fights, typedStats, typedCounter);
    }
    private static Role role(JsonNode raw) { if (is(raw, "attacker")) return Role.ATTACKER; if (is(raw, "defender")) return Role.DEFENDER; throw new CombatInputException("invalid encounter role"); }
    static Coalition coalition(JsonNode raw) { if (is(raw, "player_or_allied")) return Coalition.PLAYER_OR_ALLIED; if (is(raw, "enemy")) return Coalition.ENEMY; throw new CombatInputException("invalid coalition"); }
    private static Army parseArmy(JsonNode value, BigInteger target, String name) {
        var row = object(value, name); available(row, name); Role role = role(row.get("encounter_role")); String scopeRole = text(row.get("scope_role"), name);
        Coalition side = scopeRole.equals("active_war_enemy") ? Coalition.ENEMY : Coalition.PLAYER_OR_ALLIED;
        BigInteger nativeId = positiveInteger(row.get("native_carmy_id"), name); var owner = object(row.get("owner"), name); available(owner, name); scale(owner, name);
        var commander = object(row.get("commander"), name); var battle = object(commander.get("battle_context"), name); available(battle, name);
        require(positiveInteger(battle.get("source_target_province_id"), name).equals(target), "commander target drifted");
        BigInteger character = null, advantage = null;
        if (is(commander.get("status"), "available")) { character = characterId(commander.get("character_id"), name); advantage = integer(commander.get("generic_advantage_points"), name); }
        else require(is(commander.get("status"), "absent"), "commander unavailable");
        var typedCommander = new Commander(character, advantage, integer(battle.get("effective_min_roll"), name), integer(battle.get("effective_max_roll"), name));
        var regiments = new ArrayList<Regiment>(); for (var raw : elements(row.get("regiments"), name)) regiments.add(parseRegiment(raw, target, name));
        var regimentIds = new HashSet<BigInteger>(); for (var r : regiments) require(regimentIds.add(r.regimentId()), "repeated RegimentID");
        var knightRow = object(row.get("knights"), name); available(knightRow, name); var knights = new ArrayList<Knight>();
        for (var raw : elements(knightRow.get("members"), name)) { var k = object(raw, name); scale(k, name); require(yes(k.get("eligible")) && yes(k.get("participant_army_membership_verified")), "knight not eligible/membership-safe");
            BigInteger regimentId = positiveInteger(k.get("source_regiment_id"), name); require(regimentIds.contains(regimentId), "knight outside army regiments"); require(positiveInteger(k.get("army_id"), name).equals(nativeId), "knight native army drifted");
            knights.add(new Knight(characterId(k.get("character_id"), name), regimentId, nativeId, integer(k.get("prowess"), name), integer(k.get("knight_effectiveness_raw"), name), integer(k.get("effective_damage_raw"), name), integer(k.get("effective_toughness_raw"), name))); }
        return new Army(publicCunitId(row.get("army_id"), name), nativeId, role, side, scopeRole, characterId(owner.get("character_id"), name), positiveInteger(row.get("current_province_id"), name), typedCommander, regiments, knights);
    }
    public static Frozen freeze(JsonNode payload, Capture capture) {
        var row = object(payload, "combat_simulation_inputs"); String policy = text(row.get("participant_policy"), "participant_policy");
        require(policy.equals("explicit_hypothetical_fixed_at_contact_no_reinforcements"), "participant_policy is not fixed-contact v2");
        BigInteger targetId = positiveInteger(row.get("target_province_id"), "target_province_id"); var scenario = object(row.get("scenario"), "scenario");
        require(is(scenario.get("kind"), "explicit_hypothetical_contact"), "scenario kind is not explicit hypothetical contact");
        BigInteger entry = null; if (absentOrNull(scenario.get("attacker_entry_province_id"))) {
            require(is(scenario.get("contact_geometry_mode"), "native_defender_constructor_zero") && integer(scenario.get("constructor_adjacency_kind_raw"), "constructor_adjacency_kind_raw").signum() == 0
                    && is(scenario.get("attacker_position_policy"), "fixed_at_target_hypothetical") && is(scenario.get("defender_position_policy"), "fixed_at_target_hypothetical"), "null attacker entry requires native defender constructor raw0");
        } else entry = positiveInteger(scenario.get("attacker_entry_province_id"), "attacker entry");
        var attackers = ids(scenario.get("attacker_army_ids"), "attacker_army_ids"); var defenders = ids(scenario.get("defender_army_ids"), "defender_army_ids");
        require(attackers.stream().noneMatch(defenders::contains), "scenario repeats army across sides");
        Coalition attackerSide = coalition(scenario.get("attacker_side")), defenderSide = coalition(scenario.get("defender_side")); require(attackerSide != defenderSide, "invalid coalition orientation");
        require(no(scenario.get("actual_route_dependency")), "fixed-contact scenario unexpectedly depends on route");
        var armies = new ArrayList<Army>(); for (var raw : elements(row.get("armies"), "armies")) armies.add(parseArmy(raw, targetId, "army"));
        var ordered = new ArrayList<>(attackers); ordered.addAll(defenders); require(armies.stream().map(Army::publicArmyId).toList().equals(ordered), "army ordering/partition drifted");
        for (var army : armies) require(army.coalitionSide() == (army.encounterRole() == Role.ATTACKER ? attackerSide : defenderSide), "army role and coalition side disagree");
        var target = object(row.get("target_province"), "target_province"); available(target, "target"); require(positiveInteger(target.get("province_id"), "province_id").equals(targetId), "target ProvinceID drifted");
        var terrain = object(target.get("terrain"), "terrain"); available(terrain, "terrain"); scale(terrain, "terrain"); String terrainKey = text(terrain.get("key"), "terrain key"); require(!terrainKey.isEmpty(), "invalid terrain key");
        var crossing = object(target.get("crossing"), "crossing"); available(crossing, "crossing"); Crossing kind;
        if (is(crossing.get("kind"), "none")) kind = Crossing.NONE; else if (is(crossing.get("kind"), "strait")) kind = Crossing.STRAIT; else if (is(crossing.get("kind"), "river")) kind = Crossing.RIVER; else if (is(crossing.get("kind"), "large_river")) kind = Crossing.LARGE_RIVER; else throw new CombatInputException("invalid crossing kind");
        var defender = object(target.get("defender_context"), "defender_context"); available(defender, "defender_context"); require(is(defender.get("holding_defender_status"), "available"), "holding defender unavailable");
        boolean holding = bool(defender.get("holding_defender"), "holding_defender"); require(coalition(defender.get("defender_side")) == defenderSide, "defender coalition drifted");
        var width = object(target.get("precontact_width"), "width"); available(width, "width"); var resolutions = new ArrayList<CounterResolution>();
        for (var raw : elements(row.get("counter_resolutions"), "counter_resolutions")) { var c = object(raw, "counter resolution"); available(c, "counter resolution"); scale(c, "counter resolution");
            Coalition countered = coalition(c.get("countered_side")), countering = coalition(c.get("countering_side")); require(countered != countering, "invalid counter orientation");
            BigInteger count = integer(c.get("class_count"), "class_count"); var retention = elements(c.get("damage_retention_by_class_raw"), "retention").stream().map(v -> integer(v, "retention")).toList(); require(count.equals(n(retention.size())), "class count disagrees");
            resolutions.add(new CounterResolution(countered, countering, characterId(c.get("countered_modifier_owner_character_id"), "countered owner"), characterId(c.get("countering_modifier_owner_character_id"), "countering owner"), integer(c.get("context_scale_raw"), "context scale"), retention)); }
        require(resolutions.stream().map(CounterResolution::counteredSide).toList().equals(List.of(Coalition.PLAYER_OR_ALLIED, Coalition.ENEMY)), "counter resolutions not canonical side order");
        var completeness = object(row.get("completeness"), "completeness"); boolean inputReady = bool(completeness.get("input_observation_ready"), "input readiness"), mcReady = bool(completeness.get("monte_carlo_ready"), "monte carlo readiness"); require(inputReady, "input observation not ready");
        var missing = elements(completeness.get("missing_required_domains"), "missing domains").stream().map(v -> text(v, "missing domain")).toList();
        var encounter = new Encounter(targetId, entry, attackerSide, defenderSide, attackers, defenders, policy, terrainKey, integer(terrain.get("combat_width_multiplier_raw"), "width multiplier"), kind, holding, positiveInteger(width.get("base"), "base width"), positiveInteger(width.get("final"), "final width"));
        return new Frozen(sha256(canonical(row)), encounter, armies, resolutions, inputReady, mcReady, missing, capture == null ? Capture.empty() : capture);
    }
    /** Exact historical input fixture loader; it grants no current-build runtime qualification. */
    public static Frozen loadLiveCombatFixture(Path path) throws IOException {
        var fixture = object(parse(Files.readAllBytes(path)), "fixture");
        require(is(fixture.get("fixture_kind"), "paused-live-combat-simulation-inputs-v2"), "fixture kind is not paused live combat v2");
        require(is(fixture.get("game_version"), "1.19.0.6") && is(fixture.get("executable_sha256"),
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"), "fixture exact-build provenance mismatch");
        var capture = object(fixture.get("capture"), "fixture.capture"); available(capture, "fixture capture");
        return freeze(fixture.get("combat_simulation_inputs"), new Capture(capture));
    }
    public record EngagementReadiness(boolean inputObservationReady, boolean transitionFidelityGate, boolean plannerUsable,
            boolean activeAttackAllowed, String forecastStatus, int sampleCount, List<String> reasons) { public EngagementReadiness { reasons = List.copyOf(reasons); } }
    public static EngagementReadiness engagementReadiness(Frozen input, Manifest manifest) {
        var reasons = new LinkedHashSet<String>(); if (!input.inputObservationReady()) reasons.add("combat_input_observation_not_ready"); if (!manifest.fidelityGate()) reasons.addAll(manifest.missingRequiredDomains());
        boolean ready = input.inputObservationReady() && manifest.fidelityGate(); if (ready) reasons.add("monte_carlo_experiment_not_run");
        return new EngagementReadiness(input.inputObservationReady(), manifest.fidelityGate(), false, false, ready ? "ready-for-exact-kernel" : "unavailable", 0, List.copyOf(reasons));
    }
}
