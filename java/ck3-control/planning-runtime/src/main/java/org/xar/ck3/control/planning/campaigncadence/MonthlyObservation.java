package org.xar.ck3.control.planning.campaigncadence;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Incomplete exact-slot projection, with no reads, query instructions or persistence. */
public record MonthlyObservation(String machineId, String observedAtUtc, int monthIndex,
        CampaignCalendar.Boundary current, CampaignAnchor campaignAnchor,
        CampaignCalendar.Boundary baseline, CampaignCalendar.Boundary endpoint,
        Frame frame, String observedGold, List<WarRow> observedPlayerWars) {
    private static final String UNKNOWN_REASON = "当前普通帧未提供同口径、同范围的该评分输入。";
    private static final BigInteger UINT32_MAX = new BigInteger("4294967295");

    public enum Metric {
        Q_REALM("Q_realm", "quality_county_equivalent"), K_DYNASTY("K_dynasty", "quality_county_equivalent"),
        LEGACY_RANKS("legacy_ranks", "rank"), CONTROL_AVERAGE("control_average", "fraction"),
        REBEL_SHARE("rebel_share", "fraction"), GOLD("gold", "gold"), GROSS_INCOME("gross_income", "gold/month"),
        TOTAL_EXPENSES("total_expenses", "gold/month"), MILITARY_CURRENT("military_current", "gold/month"),
        MILITARY_ALL_RAISED("military_all_raised", "gold/month"), DUE_COMMITMENTS("due_commitments", "gold"),
        P_QUALITY("P_quality", "standard_soldier_equivalent"), CONTINUATION_LEGAL("continuation_legal", "boolean"),
        BACKUP_HEIRS("backup_heirs", "person"), U_DISCRETIONARY("u_discretionary", "gold/month"),
        REALM_COUNTY_COUNT("realm_county_count", "county"), DYNASTY_COUNTY_COUNT("dynasty_county_count", "county"),
        HOUSE_ANCHOR_ID("house_anchor_id", "id"), DYNASTY_ANCHOR_ID("dynasty_anchor_id", "id"),
        ACTIVE_FAMILY_BRANCHES("active_family_branches", "house");
        private final String wire;
        private final String unit;
        Metric(String wire, String unit) { this.wire = wire; this.unit = unit; }
        public String wire() { return wire; }
        public String unit() { return unit; }
    }

    public record CampaignAnchor(String campaignId, BigInteger founderCharacterId,
            BigInteger foundingHouseId, BigInteger foundingDynastyId) {
        public CampaignAnchor {
            StrictJson.text(campaignId);
            NativeCharacterId.of(founderCharacterId);
            if (foundingHouseId != null) { positiveId(foundingHouseId); }
            if (foundingDynastyId != null) { positiveId(foundingDynastyId); }
        }

        public ObjectNode toJson() {
            ObjectNode node = StrictJson.object();
            node.put("campaign_id", campaignId);
            node.put("founder_character_id", founderCharacterId);
            nullable(node, "founding_house_id", foundingHouseId);
            nullable(node, "founding_dynasty_id", foundingDynastyId);
            return node;
        }
    }

    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, int dateRaw,
            String episodeRunId, BigInteger episodeCharacterId, Boolean oneLifeTerminal,
            String oneLifeTerminalReason, BigInteger actorCharacterId, Boolean actorAlive) {
        public Frame {
            StrictJson.text(snapshotId);
            uint64(revision); uint64(nativeRevision);
            CampaignCalendar.rawToDate(dateRaw);
            if (episodeRunId != null) { StrictJson.text(episodeRunId); }
            if (episodeCharacterId != null) { NativeCharacterId.of(episodeCharacterId); }
            if (actorCharacterId != null) { NativeCharacterId.of(actorCharacterId); }
        }

        public ObjectNode toJson() {
            ObjectNode node = StrictJson.object();
            node.put("snapshot_id", snapshotId);
            node.put("revision", revision); node.put("native_revision", nativeRevision); node.put("date_raw", dateRaw);
            nullable(node, "episode_run_id", episodeRunId);
            nullable(node, "episode_character_id", episodeCharacterId);
            nullable(node, "one_life_terminal", oneLifeTerminal);
            nullable(node, "one_life_terminal_reason", oneLifeTerminalReason);
            nullable(node, "actor_character_id", actorCharacterId);
            nullable(node, "actor_alive", actorAlive);
            node.put("paused", true);
            return node;
        }
    }

    public record WarRow(BigInteger warId, String playerSide, BigInteger primaryOpponentCharacterId,
            Integer playerRelativeWarScore) {
        public WarRow {
            if (warId != null) { positiveId(warId); }
            if (primaryOpponentCharacterId != null) { NativeCharacterId.of(primaryOpponentCharacterId); }
            if (playerSide != null) { require(playerSide.equals("attacker") || playerSide.equals("defender"), "invalid player side"); }
            if (playerRelativeWarScore != null) { require(playerRelativeWarScore >= -100 && playerRelativeWarScore <= 100, "war score outside -100..100"); }
        }

        public ObjectNode toJson() {
            ObjectNode node = StrictJson.object();
            nullable(node, "war_id", warId); nullable(node, "player_side", playerSide);
            nullable(node, "primary_opponent_character_id", primaryOpponentCharacterId);
            if (playerRelativeWarScore == null) { node.putNull("player_relative_war_score"); }
            else { node.put("player_relative_war_score", playerRelativeWarScore); }
            return node;
        }
    }

    public MonthlyObservation {
        StrictJson.text(machineId); StrictJson.text(observedAtUtc);
        require(current != null && campaignAnchor != null && baseline != null && endpoint != null && frame != null,
                "complete observation bindings required");
        require(monthIndex >= 0 && monthIndex <= 360 && current.raw() == frame.dateRaw()
                && baseline.raw() <= current.raw() && current.raw() <= endpoint.raw(), "inconsistent exact slot");
        if (observedGold != null) { require(observedGold.matches("-?[0-9]+(\\.[0-9]+)?"), "decimal gold string required"); }
        if (observedPlayerWars != null) {
            require(observedPlayerWars.size() <= 128, "bounded player wars required");
            observedPlayerWars = List.copyOf(observedPlayerWars);
        }
    }

    /** Snapshot is an extensible upstream DTO; only fields actually projected are consumed. */
    public static Optional<MonthlyObservation> fromExistingFrame(ObjectNode snapshot, String startDate,
            String machineId, String observedAtUtc, ObjectNode anchor, int months) {
        require(snapshot != null && anchor != null, "sample inputs must be objects");
        List<CampaignCalendar.Boundary> rows = CampaignCalendar.monthBoundaries(startDate, months);
        int raw = signedInt(snapshot.get("date_raw"));
        int slot = 0;
        while (slot < rows.size() && rows.get(slot).raw() < raw) { slot++; }
        if (slot == rows.size() || rows.get(slot).raw() != raw) { return Optional.empty(); }
        StrictJson.trueValue(snapshot.get("paused"));
        CampaignAnchor campaignAnchor = new CampaignAnchor(StrictJson.text(anchor.get("campaign_id")),
                characterIdentity(anchor.get("founder_character_id")), optionalId(anchor.get("founding_house_id")),
                optionalId(anchor.get("founding_dynasty_id")));
        ObjectNode player = snapshot.get("played_character") instanceof ObjectNode object ? object : StrictJson.object();
        Frame frame = new Frame(StrictJson.text(snapshot.get("snapshot_id")),
                StrictJson.integer(snapshot.get("revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                StrictJson.integer(snapshot.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX), raw,
                optionalText(snapshot.get("episode_run_id")), optionalCharacterId(snapshot.get("episode_character_id")),
                optionalBoolean(snapshot.get("one_life_terminal")), optionalText(snapshot.get("one_life_terminal_reason")),
                optionalCharacterId(player.get("character_id")), optionalBoolean(player.get("alive")));
        String gold = null;
        if (snapshot.get("played_character_gold") instanceof ObjectNode wallet
                && wallet.get("raw") != null && wallet.get("raw").isIntegralNumber()
                && wallet.get("scale") != null && wallet.get("scale").isIntegralNumber()
                && wallet.get("scale").bigIntegerValue().equals(BigInteger.valueOf(100_000))) {
            // Python Decimal division uses its default precision 28 / HALF_EVEN in this pure leaf.
            gold = new BigDecimal(wallet.get("raw").bigIntegerValue()).divide(BigDecimal.valueOf(100_000),
                    new MathContext(28, RoundingMode.HALF_EVEN)).toPlainString();
        }
        List<WarRow> wars = null;
        if (snapshot.get("active_wars") instanceof ArrayNode values && values.size() <= 128) {
            boolean objects = true;
            for (JsonNode value : values) { objects &= value.isObject(); }
            if (objects) {
                wars = new ArrayList<>();
                for (JsonNode value : values) {
                    wars.add(new WarRow(optionalId(value.get("war_id")), optionalText(value.get("player_side")),
                            optionalCharacterId(value.get("primary_opponent_character_id")),
                            absent(value.get("player_relative_war_score")) ? null : signedInt(value.get("player_relative_war_score"))));
                }
            }
        }
        return Optional.of(new MonthlyObservation(machineId, observedAtUtc, slot, rows.get(slot), campaignAnchor,
                rows.getFirst(), rows.getLast(), frame, gold, wars));
    }

    public ObjectNode toJson() {
        ObjectNode result = StrictJson.object();
        result.put("schema", "xar.ck3.campaign-score-month-observation/v1");
        result.put("calendar_profile", CampaignCalendar.PROFILE);
        result.put("machine_id", machineId); result.put("observed_at_utc", observedAtUtc);
        result.put("month_index", monthIndex); result.put("date", current.date()); result.put("date_raw", current.raw());
        result.set("campaign_anchor", campaignAnchor.toJson());
        result.put("baseline_date", baseline.date()); result.put("baseline_date_raw", baseline.raw());
        result.put("endpoint_date", endpoint.date()); result.put("endpoint_date_raw", endpoint.raw());
        result.set("frame", frame.toJson());
        ObjectNode metrics = result.putObject("raw_metrics");
        for (Metric metric : Metric.values()) {
            ObjectNode row = metrics.putObject(metric.wire());
            boolean observed = metric == Metric.GOLD && observedGold != null;
            if (observed) { row.put("value", observedGold); } else { row.putNull("value"); }
            row.put("unit", metric.unit()); row.put("availability", observed ? "observed" : "unknown");
            row.put("source_ref", "ordinary_frame");
            if (!observed) { row.put("reason_zh", UNKNOWN_REASON); }
        }
        if (observedPlayerWars == null) { result.putNull("observed_player_wars"); }
        else {
            ArrayNode wars = result.putArray("observed_player_wars");
            observedPlayerWars.forEach(row -> wars.add(row.toJson()));
        }
        ObjectNode source = result.putArray("sources").addObject();
        source.put("id", "ordinary_frame"); source.put("kind", "existing_ordinary_semantic_snapshot");
        source.set("binding", frame.toJson());
        result.put("status", "OBSERVED_EXACT_SLOT_INCOMPLETE_SCORING_INPUT");
        result.put("source_response_binding_pending", true);
        result.put("new_RPC_calls", 0); result.put("new_SAVE_exports", 0);
        result.put("historic_slots_reconstructed", false); result.put("score_or_complete_history_claimed", false);
        return result;
    }

    private static void positiveId(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(UINT32_MAX) <= 0, "positive uint32 identity required");
    }
    private static void uint64(BigInteger value) {
        require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 revision required");
    }
    private static BigInteger identity(JsonNode value) { return StrictJson.integer(value, BigInteger.ONE, UINT32_MAX); }
    private static BigInteger optionalId(JsonNode value) { return absent(value) ? null : identity(value); }
    private static BigInteger characterIdentity(JsonNode value) { return NativeCharacterId.fromJson(value).asBigInteger(); }
    private static BigInteger optionalCharacterId(JsonNode value) { return absent(value) ? null : characterIdentity(value); }
    private static int signedInt(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static boolean absent(JsonNode value) { return value == null || value.isNull(); }
    private static String optionalText(JsonNode value) { return absent(value) ? null : StrictJson.text(value); }
    private static Boolean optionalBoolean(JsonNode value) {
        if (absent(value)) { return null; }
        require(value.isBoolean(), "JSON boolean required");
        return value.booleanValue();
    }
    private static void nullable(ObjectNode object, String key, BigInteger value) {
        if (value == null) { object.putNull(key); } else { object.put(key, value); }
    }
    private static void nullable(ObjectNode object, String key, String value) {
        if (value == null) { object.putNull(key); } else { object.put(key, value); }
    }
    private static void nullable(ObjectNode object, String key, Boolean value) {
        if (value == null) { object.putNull(key); } else { object.put(key, value); }
    }
}
