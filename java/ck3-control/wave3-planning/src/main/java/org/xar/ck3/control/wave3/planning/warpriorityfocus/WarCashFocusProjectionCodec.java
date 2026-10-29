package org.xar.ck3.control.wave3.planning.warpriorityfocus;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warbudget.BudgetPoliticalStakesCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegeCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.planning.reinforcementcount.ReinforcementCounts;

/** Strict envelope, immutable owned projections, and unchanged UTF-8 subtrees for shared qualification. */
public final class WarCashFocusProjectionCodec {
    public static final String SCHEMA = "xar.war-cash-focus.request.v1";
    public static final int MAX_BYTES = 65_536;
    private WarCashFocusProjectionCodec() { }

    /** Cannot be constructed from caller-supplied focus, political GREEN, or detached realm instances. */
    public static final class Request {
        private final byte[] original;
        private final List<ObservedWar> wars;
        private final Optional<BigInteger> ownCount;
        private final boolean completeOwnRows;
        private final boolean allOwnRetreating;
        private final int primaryCount;
        private final boolean aggregateDeficit;
        private final RealmSiegePolicy.Snapshot realmSnapshot;
        private final BudgetPoliticalStakesCodec.Context politicalContext;
        private Request(byte[] original, List<ObservedWar> wars, Optional<BigInteger> ownCount,
                        boolean completeOwnRows, boolean allOwnRetreating, int primaryCount,
                        boolean aggregateDeficit, RealmSiegePolicy.Snapshot realmSnapshot,
                        BudgetPoliticalStakesCodec.Context politicalContext) {
            this.original = original.clone(); this.wars = List.copyOf(wars); this.ownCount = ownCount;
            this.completeOwnRows = completeOwnRows; this.allOwnRetreating = allOwnRetreating;
            this.primaryCount = primaryCount; this.aggregateDeficit = aggregateDeficit;
            this.realmSnapshot = realmSnapshot; this.politicalContext = politicalContext;
        }
        List<ObservedWar> wars() { return wars; }
        Optional<BigInteger> ownCount() { return ownCount; }
        boolean completeOwnRows() { return completeOwnRows; }
        boolean allOwnRetreating() { return allOwnRetreating; }
        int primaryCount() { return primaryCount; }
        boolean aggregateDeficit() { return aggregateDeficit; }
        RealmSiegePolicy.Snapshot realmSnapshot() { return realmSnapshot; }
        BudgetPoliticalStakesCodec.Context politicalContext() { return politicalContext; }
    }

    record ObservedWar(int ordinal, BigInteger warId, boolean primary, boolean defender,
                       Optional<BigInteger> score, Optional<BigInteger> enemyCount, boolean completeEnemyRows,
                       boolean primaryTitleTargeted, boolean directHeldTargeted, boolean defensiveTargetsExposed,
                       boolean hostileSiege, boolean hostileObjectiveOccupation, RealmSiegePolicy.War realmWar) { }
    private record CountContext(String snapshotId, BigInteger revision, ReinforcementCounts.CacheStatus status,
                                Optional<String> queriedSnapshotId, Optional<BigInteger> queriedRevision,
                                List<ReinforcementCounts.Strength> strengths) {
        Optional<BigInteger> count(List<JsonNode> rows, String role, Optional<BigInteger> warId) {
            List<ReinforcementCounts.Army> armies = rows.stream().map(row -> new ReinforcementCounts.Army(
                    integer(row.get("army_id")), integer(row.get("soldiers")))).toList();
            return ReinforcementCounts.count(new ReinforcementCounts.CountInput(armies, snapshotId, revision, status,
                    queriedSnapshotId, queriedRevision, strengths, role, warId));
        }
    }

    public static Request decode(byte[] raw) {
        ObjectNode envelope = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "snapshot", "campaign_root"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(envelope.get("schema"))), "unknown cash focus request schema");
        JsonNode snapshot = object(envelope.get("snapshot"));
        JsonNode root = envelope.get("campaign_root");
        StrictJson.require(root.isNull() || root.isObject(), "campaign_root must be object or explicit null");
        List<JsonNode> active = rows(snapshot.get("active_wars"), false);
        List<JsonNode> own = rows(snapshot.get("player_armies"), true);
        boolean ownPresent = snapshot.path("player_armies").isArray();
        CountContext counts = countContext(snapshot);
        Optional<BigInteger> ownCount = ownPresent ? counts.count(own, "player", Optional.empty()) : Optional.empty();
        boolean allRetreating = !own.isEmpty() && own.stream().allMatch(army -> truth(army.get("retreating")));

        ObjectNode realmEnvelope = StrictJson.object(); realmEnvelope.put("schema", RealmSiegePolicy.INPUT_SCHEMA);
        realmEnvelope.set("snapshot", snapshot); realmEnvelope.putArray("detached_wars"); realmEnvelope.putArray("detached_enemies");
        realmEnvelope.putNull("candidate_war_ref"); realmEnvelope.putNull("candidate_enemy_ref");
        RealmSiegePolicy.Snapshot realm = RealmSiegeCodec.decodeNode(realmEnvelope).snapshot();

        BudgetPoliticalStakesCodec.Context political = BudgetPoliticalStakesCodec.parseContext(
                subtree(raw, "snapshot"), subtree(raw, "campaign_root"));
        // This is the actual currentRoot helper result, never a second caller-side qualification.
        JsonNode currentRoot = StrictJson.parse(political.currentRootJsonBytes(), MAX_BYTES);
        Optional<BigInteger> primaryTitle = Optional.empty(); Set<BigInteger> held = new HashSet<>();
        if (!currentRoot.isEmpty()) {
            JsonNode title = currentRoot.get("primary_title");
            if (title != null && !title.isNull()) { primaryTitle = integer(object(title).get("title_id")); }
            for (JsonNode row : rows(currentRoot.get("held_title_partition"), true)) {
                JsonNode heldTitle = row.get("title");
                if (heldTitle != null && !heldTitle.isNull()) { integer(object(heldTitle).get("title_id")).ifPresent(held::add); }
            }
        }
        List<JsonNode> union = new ArrayList<>(); int primaryCount = 0; boolean unionComplete = true;
        for (JsonNode war : active) {
            if (truth(war.get("player_is_primary_war_leader"))) {
                primaryCount++; unionComplete &= war.path("enemy_armies").isArray();
                union.addAll(rows(war.get("enemy_armies"), true));
            }
        }
        Optional<BigInteger> aggregate = primaryCount > 0 && unionComplete
                ? counts.count(union, "active_war_enemy", Optional.empty()) : Optional.empty();
        boolean aggregateDeficit = ownCount.isPresent() && aggregate.isPresent()
                && ownCount.orElseThrow().compareTo(aggregate.orElseThrow()) < 0;
        List<ObservedWar> wars = new ArrayList<>();
        for (int ordinal = 0; ordinal < active.size(); ordinal++) {
            JsonNode war = active.get(ordinal); BigInteger identity = requiredInteger(war.get("war_id"));
            boolean primary = truth(war.get("player_is_primary_war_leader"));
            boolean defender = "defender".equals(optionalText(war.get("player_side")).orElse(""));
            List<BigInteger> targets = integers(war.get("targeted_title_ids"), true).stream().filter(id -> id.signum() >= 0).toList();
            List<JsonNode> enemy = rows(war.get("enemy_armies"), true);
            Optional<BigInteger> enemyCount = war.path("enemy_armies").isArray()
                    ? counts.count(enemy, "active_war_enemy", Optional.of(identity)) : Optional.empty();
            boolean siege = enemy.stream().anyMatch(army -> "sieging".equals(optionalText(army.get("army_state")).orElse(""))
                    && truth(army.get("siege_province_in_player_subrealm")));
            Optional<BigInteger> opponent = integer(war.get("primary_opponent_character_id"));
            boolean occupation = rows(war.get("objective_province_states"), true).stream().anyMatch(state ->
                    truth(state.get("occupation_observable")) && truth(state.get("is_occupied"))
                            && opponent.filter(value -> value.signum() > 0).isPresent()
                            && integer(state.get("occupying_character_id")).equals(opponent));
            wars.add(new ObservedWar(ordinal, identity, primary, defender, integer(war.get("player_relative_war_score")),
                    enemyCount, war.path("enemy_armies").isArray(), primaryTitle.filter(targets::contains).isPresent(),
                    targets.stream().anyMatch(held::contains), primary && defender && !targets.isEmpty(), siege,
                    occupation, realm.activeWars().get(ordinal)));
        }
        return new Request(raw, wars, ownCount, ownPresent, allRetreating, primaryCount, aggregateDeficit, realm, political);
    }

    /** Preserves the original unknown extension values and floating-point token types byte for byte. */
    public static byte[] encodeRequest(Request request) { return request.original.clone(); }

    public static byte[] encode(Optional<WarCashFocusProjection.FocusedWar> value) {
        if (value.isEmpty()) { return new byte[] {'n', 'u', 'l', 'l'}; }
        WarCashFocusProjection.FocusedWar focus = value.orElseThrow(); ObjectNode result = StrictJson.object();
        result.put("war_id", focus.warId()); count(result, "observed_player_raised_soldiers", focus.observedPlayerRaisedSoldiers());
        count(result, "observed_enemy_raised_soldiers", focus.observedEnemyRaisedSoldiers());
        return StrictJson.canonical(result, 4_096);
    }
    public static Optional<WarCashFocusProjection.FocusedWar> decodeResult(byte[] raw) {
        JsonNode result = StrictJson.parse(raw, 4_096); if (result.isNull()) { return Optional.empty(); }
        StrictJson.object(result, Set.of("war_id", "observed_player_raised_soldiers", "observed_enemy_raised_soldiers"));
        return Optional.of(new WarCashFocusProjection.FocusedWar(requiredInteger(result.get("war_id")),
                integer(result.get("observed_player_raised_soldiers")), integer(result.get("observed_enemy_raised_soldiers"))));
    }
    private static CountContext countContext(JsonNode snapshot) {
        String status = optionalText(snapshot.get("army_strengths_status")).orElse("");
        ReinforcementCounts.CacheStatus cache = "available".equals(status) ? ReinforcementCounts.CacheStatus.AVAILABLE
                : "partial".equals(status) ? ReinforcementCounts.CacheStatus.PARTIAL : ReinforcementCounts.CacheStatus.OTHER;
        List<ReinforcementCounts.Strength> strengths = new ArrayList<>();
        for (JsonNode row : rows(snapshot.get("army_strengths"), true)) {
            strengths.add(new ReinforcementCounts.Strength(integer(row.get("army_id")), optionalText(row.get("scope_role")).orElse(""),
                    integers(row.get("war_ids"), true), "available".equals(optionalText(row.get("status")).orElse("")),
                    integer(row.get("current_soldiers"))));
        }
        return new CountContext(StrictJson.text(snapshot.get("snapshot_id")), requiredInteger(snapshot.get("revision")), cache,
                optionalText(snapshot.get("army_strengths_queried_snapshot_id")), integer(snapshot.get("army_strengths_queried_revision")), strengths);
    }
    private static JsonNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "SDK extension container must be an object"); return value;
    }
    private static List<JsonNode> rows(JsonNode value, boolean nullable) {
        if (value == null || value.isNull()) {
            StrictJson.require(nullable, "explicit active_wars array required"); return List.of();
        }
        StrictJson.require(value.isArray(), "SDK row collection must be an array"); List<JsonNode> result = new ArrayList<>();
        for (JsonNode row : value) { result.add(object(row)); } return List.copyOf(result);
    }
    private static List<BigInteger> integers(JsonNode value, boolean nullable) {
        if (value == null || value.isNull()) { StrictJson.require(nullable, "integer array required"); return List.of(); }
        StrictJson.require(value.isArray(), "integer array required"); List<BigInteger> result = new ArrayList<>();
        for (JsonNode item : value) { result.add(requiredInteger(item)); } return List.copyOf(result);
    }
    private static Optional<BigInteger> integer(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        StrictJson.require(value.isIntegralNumber(), "exact integer required; bool/float/string rejected"); return Optional.of(value.bigIntegerValue());
    }
    private static BigInteger requiredInteger(JsonNode value) {
        return integer(value).orElseThrow(() -> new IllegalArgumentException("required integer missing or null"));
    }
    private static Optional<String> optionalText(JsonNode value) {
        if (value == null || value.isNull()) { return Optional.empty(); }
        StrictJson.require(value.isTextual(), "string token required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value); } return Optional.of(value.textValue());
    }
    private static boolean truth(JsonNode value) {
        if (value == null || value.isNull()) { return false; }
        StrictJson.require(value.isBoolean(), "boolean branch requires boolean token"); return value.booleanValue();
    }
    private static void count(ObjectNode node, String field, Optional<BigInteger> value) {
        if (value.isEmpty()) { node.putNull(field); } else { node.put(field, value.orElseThrow()); }
    }
    private static byte[] subtree(byte[] raw, String field) {
        try (JsonParser parser = new JsonFactory().createParser(raw)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "request object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String key = parser.currentName(); parser.nextToken();
                int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset()); parser.skipChildren();
                int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                if (field.equals(key)) { return Arrays.copyOfRange(raw, start, end); }
            }
            throw new IllegalArgumentException("required subtree absent");
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8 request subtree", error); }
    }
}
