package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionculture.FactionCultureCodec;
import org.xar.ck3.control.wave2.finance.factionculture.FactionCultureModel.CultureRelation;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;

/** Whole v1 normalizer and same-frame war handoff validator, with exact source field sets. */
public final class FactionAlertsCodec {
    public static final int MAX_BYTES = 1_048_576;
    private static final Set<String> FRAME_FIELDS = Set.of("schema_version", "status", "snapshot_revision", "date_raw", "player_character_id", "targeting_faction_count", "targeting_factions", "county_exposures", "planner_projection", "readiness", "component_unavailable_reasons", "unavailable_reason", "provenance");
    private static final Set<String> TARGET_FIELDS = Set.of("faction_id", "faction_type_key", "target_character_id", "leader_character_id", "leader_is_human", "special_character_id", "special_title_id", "faction_at_war", "faction_war_id", "power", "power_threshold", "discontent", "discontent_per_month", "months_until_max_discontent", "character_member_ids", "county_member_title_ids", "dangerous_by_stock_rule", "danger_reason");
    private static final Set<String> COUNTY_FIELDS = Set.of("county_title_id", "capital_province_id", "holder_character_id", "county_opinion", "native_county_join_score", "can_add_county", "removal_queued", "native_leave_score_threshold", "opinion_status", "native_final_status");
    private FactionAlertsCodec() { }

    /** The normalized wire remains the old schema, beside the validated immutable model. */
    public static final class Normalized {
        private final Frame frame; private final byte[] json;
        private Normalized(Frame frame, byte[] json) { this.frame = frame; this.json = json.clone(); }
        public Frame frame() { return frame; }
        public byte[] json() { return json.clone(); }
    }
    public static Normalized normalize(byte[] raw, ExpectedFrame expected) {
        ObjectNode root = object(StrictJson.parse(raw, MAX_BYTES), FRAME_FIELDS, Set.of(COUNTY_COMPONENT));
        StrictJson.require(number(root.get("schema_version"), 1, 1) == 1, "schema_version must be integer 1");
        BigInteger revision = uint64(root.get("snapshot_revision"));
        StrictJson.require(revision.equals(expected.nativeRevision()), "snapshot_revision does not match paused frame");
        Build provenance = provenance(root.get("provenance"));
        StrictJson.require(expected.connectedBuild().filter(value -> value != provenance).isEmpty(), "faction source does not match the connected exact build");
        Readiness readiness = readiness(root.get("readiness")); Reasons reasons = reasons(root.get("component_unavailable_reasons"));
        Planner planner = planner(root.get("planner_projection")); List<JsonNode> rawTargets = array(root.get("targeting_factions"));
        List<JsonNode> rawExposures = array(root.get("county_exposures")); Status status = status(root.get("status"));
        Frame frame;
        if (status == Status.UNAVAILABLE) {
            StrictJson.require(!root.has(COUNTY_COMPONENT), "unavailable faction frame cannot expose county component");
            Optional<Integer> date = optionalInt(root.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            StrictJson.require(date.filter(value -> value != expected.dateRaw()).isEmpty(), "unavailable frame date mismatch");
            StrictJson.require(root.get("player_character_id").isNull() && root.get("targeting_faction_count").isNull()
                    && rawTargets.isEmpty() && rawExposures.isEmpty(), "unavailable frame cannot expose partial observations");
            frame = new Unavailable(revision, date, unavailableReason(root.get("unavailable_reason")), readiness, planner, reasons, provenance);
        } else {
            StrictJson.require(root.get("unavailable_reason").isNull(), "available frame unavailable reason");
            int date = (int) number(root.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            StrictJson.require(date == expected.dateRaw(), "date_raw does not match paused frame");
            StrictJson.require(readiness.identityReady() && readiness.targetingCountReady() && readiness.sameFrameReady(), "available frame requires same-frame identity and count");
            int actor = character(root.get("player_character_id")); int count = (int) number(root.get("targeting_faction_count"), 0, Integer.MAX_VALUE);
            List<TargetingFaction> targets = new ArrayList<>();
            if (readiness.targetingRowsReady()) for (JsonNode row : rawTargets) targets.add(target(row));
            else StrictJson.require(rawTargets.isEmpty() && reasons.targetingRows().filter(value -> value.value().equals(ROWS_UNAVAILABLE)).isPresent(), "unready targeting rows must be empty and explain why");
            List<CountyExposure> exposures = new ArrayList<>();
            if (readiness.countyExposureReady()) for (JsonNode row : rawExposures) exposures.add(exposure(row));
            else StrictJson.require(rawExposures.isEmpty() && reasons.countyExposure().filter(value -> value.value().equals(COUNTY_UNAVAILABLE)).isPresent(), "unready county exposure must be empty and explain why");
            Optional<SubrealmCounties> counties = root.has(COUNTY_COMPONENT)
                    ? Optional.of(subrealm(root.get(COUNTY_COMPONENT), actor, expected)) : Optional.empty();
            Available available = new Available(revision, date, actor, count, targets, exposures, planner, readiness, reasons, provenance, counties);
            validate(available); frame = available;
        }
        ObjectNode normalized = root.deepCopy(); ObjectNode source = (ObjectNode) normalized.get("provenance");
        source.put("game_version", provenance.version()); source.put("executable_sha256", provenance.sha256()); source.put("backend_id", provenance.backendId());
        return new Normalized(frame, StrictJson.canonical(normalized, MAX_BYTES));
    }
    public static ExpectedFrame expected(byte[] raw) {
        ObjectNode root = object(StrictJson.parse(raw, MAX_BYTES), Set.of("expected_date_raw", "expected_snapshot_revision"), Set.of("expected_game_version", "expected_executable_sha256"));
        Optional<String> version = optionalText(root.get("expected_game_version")); Optional<String> sha = optionalText(root.get("expected_executable_sha256"));
        Optional<Build> build = Optional.empty();
        if (version.isPresent() || sha.isPresent()) {
            StrictJson.require(version.isPresent() && sha.isPresent(), "connected build requires both version and SHA");
            build = Optional.of(Build.exact(version.orElseThrow(), sha.orElseThrow()));
        }
        return new ExpectedFrame((int) number(root.get("expected_date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE), uint64(root.get("expected_snapshot_revision")), build);
    }
    public static void validateWarHandoffs(Frame frame, byte[] activeWarsJson) {
        if (!(frame instanceof Available available)) return;
        Set<Integer> referenced = new TreeSet<>(); for (TargetingFaction row : available.targetingFactions()) row.factionWarId().ifPresent(referenced::add);
        if (referenced.isEmpty()) return;
        List<JsonNode> wars = array(StrictJson.parse(activeWarsJson, MAX_BYTES)); Set<Integer> observed = new HashSet<>();
        for (JsonNode row : wars) {
            JsonNode value = row.isObject() ? row.get("war_id") : null;
            if (value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() > 0
                    && value.bigIntegerValue().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0) observed.add(value.intValue());
        }
        StrictJson.require(observed.containsAll(referenced), "faction war handoff identities are absent from active_wars");
    }
    private static void validate(Available frame) {
        Readiness ready = frame.readiness(); Reasons reasons = frame.reasons();
        if (ready.targetingRowsReady()) {
            StrictJson.require(reasons.targetingRows().isEmpty(), "ready targeting rows cannot carry reason");
            ids(frame.targetingFactions().stream().map(TargetingFaction::factionId).toList());
            StrictJson.require(frame.targetingFactions().size() == frame.targetingFactionCount(), "targeting rows do not match count");
            for (TargetingFaction row : frame.targetingFactions()) StrictJson.require(row.targetCharacterId() == frame.playerCharacterId(), "target must be played character");
        }
        if (ready.countyExposureReady()) {
            StrictJson.require(reasons.countyExposure().isEmpty(), "ready county exposure cannot carry reason");
            ids(frame.countyExposures().stream().map(CountyExposure::countyTitleId).toList());
            for (CountyExposure row : frame.countyExposures()) StrictJson.require(row.targetCharacterId() != frame.playerCharacterId(), "county exposure target must not be player");
        }
        StrictJson.require(ready.alertReady() == (ready.targetingRowsReady() && ready.countyExposureReady() && ready.stockDangerousReady() && ready.sameFrameReady()), "alert readiness must derive from components");
        StrictJson.require(ready.stockDangerousReady() == ready.targetingRowsReady(), "stock predicate readiness must match targeting rows");
        if (ready.alertReady()) {
            List<Integer> dangerous = frame.targetingFactions().stream().filter(row -> row.dangerous() && !row.factionAtWar()).map(TargetingFaction::factionId).toList();
            List<Integer> watch = frame.targetingFactions().stream().filter(row -> !row.dangerous() && !row.factionAtWar()).map(TargetingFaction::factionId).toList();
            List<Integer> war = frame.targetingFactions().stream().filter(TargetingFaction::factionAtWar).map(TargetingFaction::factionId).toList();
            List<Integer> exposed = frame.countyExposures().stream().filter(CountyExposure::dangerous).map(CountyExposure::countyTitleId).toList();
            Planner derived = new AvailablePlanner(!frame.targetingFactions().isEmpty() || !frame.countyExposures().isEmpty(), !dangerous.isEmpty() || !exposed.isEmpty(), dangerous, watch, war, exposed);
            StrictJson.require(frame.planner().equals(derived), "planner projection is not derived from ready rows");
        } else StrictJson.require(frame.planner() instanceof UnavailablePlanner, "unready components require unavailable planner");
    }
    private static Build provenance(JsonNode node) {
        ObjectNode root = exact(node, "game_version", "executable_sha256", "backend_id");
        Build build = Build.exact(text(root.get("game_version")), text(root.get("executable_sha256")));
        StrictJson.require(text(root.get("backend_id")).equals(build.backendId()), "native backend does not match frozen build"); return build;
    }
    private static Readiness readiness(JsonNode node) {
        ObjectNode root = exact(node, "targeting_count_ready", "identity_ready", "targeting_rows_ready", "county_exposure_ready", "stock_dangerous_predicate_ready", "same_frame_ready", "alert_ready", "exact_ultimatum_timing_ready");
        StrictJson.require(!bool(root.get("exact_ultimatum_timing_ready")), "exact ultimatum timing is not ready in v1");
        return new Readiness(bool(root.get("targeting_count_ready")), bool(root.get("identity_ready")), bool(root.get("targeting_rows_ready")), bool(root.get("county_exposure_ready")), bool(root.get("stock_dangerous_predicate_ready")), bool(root.get("same_frame_ready")), bool(root.get("alert_ready")));
    }
    private static Reasons reasons(JsonNode node) {
        ObjectNode root = exact(node, "targeting_rows", "county_exposure"); return new Reasons(optionalKey(root.get("targeting_rows")), optionalKey(root.get("county_exposure")));
    }
    private static Planner planner(JsonNode node) {
        ObjectNode root = exact(node, "status", "present", "dangerous", "dangerous_faction_ids", "watch_faction_ids", "war_handoff_faction_ids", "exposed_county_title_ids", "exact_ultimatum_timing_ready");
        Status status = status(root.get("status")); Optional<Boolean> present = optionalBool(root.get("present")); Optional<Boolean> danger = optionalBool(root.get("dangerous"));
        List<Integer> dangerous = idList(root.get("dangerous_faction_ids")); List<Integer> watch = idList(root.get("watch_faction_ids"));
        List<Integer> war = idList(root.get("war_handoff_faction_ids")); List<Integer> exposed = idList(root.get("exposed_county_title_ids"));
        StrictJson.require(!bool(root.get("exact_ultimatum_timing_ready")), "planner cannot claim exact ultimatum timing");
        if (status == Status.UNAVAILABLE) {
            StrictJson.require(present.isEmpty() && danger.isEmpty() && dangerous.isEmpty() && watch.isEmpty() && war.isEmpty() && exposed.isEmpty(), "unavailable planner must not guess alerts");
            return new UnavailablePlanner();
        }
        StrictJson.require(present.isPresent() && danger.isPresent(), "available planner requires boolean summary");
        return new AvailablePlanner(present.orElseThrow(), danger.orElseThrow(), dangerous, watch, war, exposed);
    }
    private static TargetingFaction target(JsonNode node) {
        ObjectNode root = object(node, TARGET_FIELDS, Set.of("county_member_observations", "surrender_impact"));
        int factionId = positive(root.get("faction_id")); StableKey type = key(root.get("faction_type_key")); int actor = character(root.get("target_character_id"));
        Optional<Integer> leader = optionalCharacter(root.get("leader_character_id")); boolean human = bool(root.get("leader_is_human"));
        boolean atWar = bool(root.get("faction_at_war")); Optional<Integer> war = optionalPositive(root.get("faction_war_id"));
        FixedPoint monthly = fixed(root.get("discontent_per_month"), SCALE, 64, false);
        Optional<Integer> months = optionalInt(root.get("months_until_max_discontent"), 0, Integer.MAX_VALUE);
        boolean danger = bool(root.get("dangerous_by_stock_rule")); StableKey reason = key(root.get("danger_reason"));
        String expectedReason = human ? "human_faction_leader" : type.value().equals("peasant_faction")
                ? months.filter(value -> value <= 12).isPresent() ? "peasant_ultimatum_within_12_months" : "peasant_ultimatum_not_within_12_months"
                : monthly.raw() > 0 ? "non_peasant_discontent_increasing" : "non_peasant_discontent_not_increasing";
        boolean expectedDanger = human || (type.value().equals("peasant_faction") ? months.filter(value -> value <= 12).isPresent() : monthly.raw() > 0);
        StrictJson.require(danger == expectedDanger && reason.value().equals(expectedReason), "stock dangerous result is inconsistent");
        List<Integer> counties = idList(root.get("county_member_title_ids")); Optional<List<CountyMember>> observations = Optional.empty();
        if (root.has("county_member_observations")) {
            List<CountyMember> members = new ArrayList<>(); for (JsonNode row : array(root.get("county_member_observations"))) members.add(county(row));
            List<Integer> observedIds = ids(members.stream().map(CountyMember::countyTitleId).toList());
            StrictJson.require(counties.containsAll(observedIds), "county observations must follow member title IDs"); observations = Optional.of(List.copyOf(members));
        }
        return new TargetingFaction(factionId, type, actor, leader, human, optionalCharacter(root.get("special_character_id")), optionalPositive(root.get("special_title_id")), atWar, war,
                fixed(root.get("power"), SCALE, 64, true), fixed(root.get("power_threshold"), SCALE, 64, true), fixed(root.get("discontent"), SCALE, 64, true), monthly,
                months, characterList(root.get("character_member_ids")), counties, danger, reason, observations,
                root.has("surrender_impact") ? Optional.of(impact(root.get("surrender_impact"))) : Optional.empty());
    }
    private static CountyExposure exposure(JsonNode node) {
        ObjectNode root = exact(node, "county_title_id", "faction_id", "faction_type_key", "target_character_id", "power", "power_threshold", "dangerous_by_stock_rule", "danger_reason");
        StableKey type = key(root.get("faction_type_key")); FixedPoint power = fixed(root.get("power"), SCALE, 64, true);
        FixedPoint threshold = fixed(root.get("power_threshold"), SCALE, 64, true); boolean danger = bool(root.get("dangerous_by_stock_rule"));
        Optional<StableKey> reason = optionalKey(root.get("danger_reason"));
        StrictJson.require(type.value().equals("populist_faction") && power.raw() > threshold.raw() && danger
                && reason.filter(value -> value.value().equals("player_county_in_powerful_liege_targeting_populist_faction")).isPresent(), "not a stock dangerous county exposure");
        return new CountyExposure(positive(root.get("county_title_id")), positive(root.get("faction_id")), type, character(root.get("target_character_id")), power, threshold, danger, reason.orElseThrow());
    }
    private static CountyMember county(JsonNode node) {
        ObjectNode root = object(node, COUNTY_FIELDS, FactionCultureCodec.CULTURE_FIELDS);
        Optional<CultureRelation> culture = FactionCultureCodec.normalizeRelation(StrictJson.canonical(root, MAX_BYTES), "county_member_observation");
        return new CountyMember(positive(root.get("county_title_id")), optionalPositive(root.get("capital_province_id")), optionalCharacter(root.get("holder_character_id")),
                optionalFixed(root.get("county_opinion"), 1, 32), optionalFixed(root.get("native_county_join_score"), SCALE, 64),
                optionalBool(root.get("can_add_county")), optionalBool(root.get("removal_queued")), optionalFixed(root.get("native_leave_score_threshold"), 1, 32),
                materialStatus(root.get("opinion_status")), materialStatus(root.get("native_final_status")), culture);
    }
    private static SurrenderImpact impact(JsonNode node) {
        ObjectNode root = exact(node, "status", "unavailable_reason", "ordinary_branch_title_sets_ready", "county_loss_complete", "kingdom_outcome_complete", "government_allows_state_faith", "leader_at_war_with_target", "player_subrealm_county_title_ids", "player_direct_title_loss_ids", "player_remaining_direct_county_title_ids", "member_counties", "seized_counties", "seized_duchies", "kingdoms", "unresolved_branches");
        List<KingdomImpact> kingdoms = new ArrayList<>();
        for (JsonNode row : array(root.get("kingdoms"))) {
            ObjectNode kingdom = exact(row, "title", "de_jure_county_title_ids", "seized_county_title_ids", "strict_majority_from_seized_counties");
            kingdoms.add(new KingdomImpact(title(kingdom.get("title")), idList(kingdom.get("de_jure_county_title_ids")), idList(kingdom.get("seized_county_title_ids")), bool(kingdom.get("strict_majority_from_seized_counties"))));
        }
        List<StableKey> branches = new ArrayList<>(); for (JsonNode value : array(root.get("unresolved_branches"))) branches.add(key(value));
        return new SurrenderImpact(status(root.get("status")), optionalKey(root.get("unavailable_reason")), bool(root.get("ordinary_branch_title_sets_ready")), bool(root.get("county_loss_complete")), bool(root.get("kingdom_outcome_complete")),
                optionalBool(root.get("government_allows_state_faith")), optionalBool(root.get("leader_at_war_with_target")), idList(root.get("player_subrealm_county_title_ids")), idList(root.get("player_direct_title_loss_ids")), idList(root.get("player_remaining_direct_county_title_ids")),
                titles(root.get("member_counties")), titles(root.get("seized_counties")), titles(root.get("seized_duchies")), kingdoms, branches);
    }
    private static List<SurrenderTitle> titles(JsonNode node) {
        List<SurrenderTitle> result = new ArrayList<>(); for (JsonNode value : array(node)) result.add(title(value)); return List.copyOf(result);
    }
    private static SurrenderTitle title(JsonNode node) {
        ObjectNode root = exact(node, "title_id", "tier_raw", "de_jure_parent_title_id", "duchy_title_id", "kingdom_title_id", "holder_character_id", "top_liege_character_id");
        return new SurrenderTitle(positive(root.get("title_id")), (int) number(root.get("tier_raw"), 1, 5), optionalPositive(root.get("de_jure_parent_title_id")), optionalPositive(root.get("duchy_title_id")), optionalPositive(root.get("kingdom_title_id")), optionalCharacter(root.get("holder_character_id")), optionalCharacter(root.get("top_liege_character_id")));
    }
    private static SubrealmCounties subrealm(JsonNode node, int actor, ExpectedFrame expected) {
        return FactionSubrealmCodec.parse(node, actor, expected.nativeRevision(), expected.dateRaw());
    }
    private static ObjectNode exact(JsonNode node, String... fields) { return StrictJson.object(node, Set.of(fields)); }
    private static ObjectNode object(JsonNode node, Set<String> required, Set<String> optional) {
        StrictJson.require(node != null && node.isObject(), "JSON object required"); ObjectNode root = (ObjectNode) node;
        Set<String> actual = new HashSet<>(); root.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.containsAll(required), "missing required contract fields"); actual.removeAll(required);
        StrictJson.require(optional.containsAll(actual), "unknown contract fields"); return root;
    }
    private static List<JsonNode> array(JsonNode node) {
        StrictJson.require(node != null && node.isArray(), "JSON array required"); List<JsonNode> result = new ArrayList<>(); node.forEach(result::add); return result;
    }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static Optional<String> optionalText(JsonNode node) { return node == null || node.isNull() ? Optional.empty() : Optional.of(text(node)); }
    private static StableKey key(JsonNode node) { return new StableKey(text(node)); }
    private static Optional<StableKey> optionalKey(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(key(node)); }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "boolean token required"); return node.booleanValue(); }
    private static Optional<Boolean> optionalBool(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(bool(node)); }
    private static long number(JsonNode node, long min, long max) { return StrictJson.integer(node, min, max); }
    private static int character(JsonNode node) { return NativeCharacterId.fromJson(node).value(); }
    private static Optional<Integer> optionalCharacter(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(character(node)); }
    private static List<Integer> characterList(JsonNode node) {
        List<Integer> result = new ArrayList<>(); for (JsonNode value : array(node)) result.add(character(value)); return characterIds(result);
    }
    private static int positive(JsonNode node) { return (int) number(node, 1, Integer.MAX_VALUE); }
    private static Optional<Integer> optionalInt(JsonNode node, int min, int max) { return node.isNull() ? Optional.empty() : Optional.of((int) number(node, min, max)); }
    private static Optional<Integer> optionalPositive(JsonNode node) { return optionalInt(node, 1, Integer.MAX_VALUE); }
    private static BigInteger uint64(JsonNode node) { return StrictJson.integer(node, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static List<Integer> idList(JsonNode node) {
        List<Integer> result = new ArrayList<>(); for (JsonNode value : array(node)) result.add(positive(value)); return ids(result);
    }
    private static FixedPoint fixed(JsonNode node, int scale, int bits, boolean nonnegative) {
        ObjectNode root = exact(node, "raw", "scale"); long value = number(root.get("raw"), bits == 32 ? Integer.MIN_VALUE : Long.MIN_VALUE, bits == 32 ? Integer.MAX_VALUE : Long.MAX_VALUE);
        StrictJson.require(number(root.get("scale"), scale, scale) == scale, "fixed point scale mismatch");
        StrictJson.require(!nonnegative || value >= 0, "fixed point must be nonnegative"); return new FixedPoint(value, scale);
    }
    private static Optional<FixedPoint> optionalFixed(JsonNode node, int scale, int bits) { return node.isNull() ? Optional.empty() : Optional.of(fixed(node, scale, bits, false)); }
    private static Status status(JsonNode node) {
        String value = text(node); for (Status status : Status.values()) if (status.wire().equals(value)) return status;
        throw new ContractViolationException("unsupported availability status");
    }
    private static MaterialStatus materialStatus(JsonNode node) {
        String value = text(node); for (MaterialStatus status : MaterialStatus.values()) if (status.wire().equals(value)) return status;
        throw new ContractViolationException("unsupported county observation status");
    }
    private static UnavailableReason unavailableReason(JsonNode node) {
        String value = text(node); for (UnavailableReason reason : UnavailableReason.values()) if (reason.wire().equals(value)) return reason;
        throw new ContractViolationException("unsupported unavailable reason");
    }
}
