package org.xar.ck3.control.wave2.military.dejureexitterms;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.Frame;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.MonthlyIncome;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.ObservedPredicate;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.Predicate;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.Resource;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.ResourceBalance;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.StorageCandidate;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.StructuralCandidate;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.TitleHolder;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.TruceInputs;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.UnavailablePredicate;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.UnavailableStorage;

/** Ordinary unadmitted native baseline boundary. The separately verified H2743 stock branch is outside this entry. */
public final class DeJureExitBaselineCodec {
    public static final int MAX_BYTES = 1_048_576;
    private static final Set<String> FIELDS = Set.of("schema", "native_revision", "war_id", "date_raw", "casus_belli_database_index",
            "casus_belli_key", "primary_attacker_character_id", "primary_defender_character_id", "target_title_ids",
            "target_title_holder_prestate", "primary_resource_balances", "primary_monthly_gold_income", "title_vassal_delta",
            "title_vassal_delta_unavailable_reason", "signed_resource_delta", "signed_resource_delta_unavailable_reason",
            "directed_truce", "directed_truce_unavailable_reason", "same_frame_stable", "material_complete");
    private DeJureExitBaselineCodec() { }

    public static String queryStep(int warId) { require(warId > 0, "positive signed native WarID required"); return DeJureExitBaseline.PREFIX + warId; }
    public static OptionalInt parseQueryStep(String step) {
        if (step == null || !step.startsWith(DeJureExitBaseline.PREFIX)) { return OptionalInt.empty(); }
        String suffix = step.substring(DeJureExitBaseline.PREFIX.length());
        if (!suffix.matches("[1-9][0-9]{0,9}")) { return OptionalInt.empty(); }
        long warId = Long.parseLong(suffix);
        return warId <= Integer.MAX_VALUE ? OptionalInt.of((int) warId) : OptionalInt.empty();
    }
    public static DeJureExitBaseline decode(byte[] raw, Frame expectedFrame) { return decodeNode(StrictJson.parse(raw, MAX_BYTES), expectedFrame); }
    public static byte[] normalize(byte[] raw, Frame expectedFrame) { return encodeProjection(decode(raw, expectedFrame)); }

    static DeJureExitBaseline decodeNode(JsonNode raw, Frame expectedFrame) {
        require(expectedFrame != null && raw != null && raw.isObject(), "observed baseline and expected native frame required");
        Set<String> fields = new HashSet<>(FIELDS);
        if (raw.has("truce_inputs_v1")) { fields.add("truce_inputs_v1"); }
        if (raw.has("border_raid_storage_candidate_v1")) {
            require(raw.has("truce_inputs_v1"), "storage scan requires truce input field"); fields.add("border_raid_storage_candidate_v1");
        }
        // An admitted wire cannot cross this ordinary entry without the real Release source-pair verifier.
        ObjectNode root = StrictJson.object(raw, fields);
        literal(root.get("schema"), DeJureExitBaseline.SCHEMA);
        require(nativeInt(root.get("war_id"), true) == expectedFrame.warId()
                && nativeInt(root.get("native_revision"), true) == expectedFrame.nativeRevision()
                && nativeInt(root.get("date_raw"), false) == expectedFrame.dateRaw()
                && nativeInt(root.get("primary_attacker_character_id"), true) == expectedFrame.attackerId()
                && nativeInt(root.get("primary_defender_character_id"), true) == expectedFrame.defenderId(), "baseline frame or parties changed");
        require(nativeInt(root.get("casus_belli_database_index"), false) == 17, "exact de-jure CB index required");
        literal(root.get("casus_belli_key"), "individual_county_de_jure_cb");
        List<Long> titles = ids(root.get("target_title_ids")); require(titles.equals(expectedFrame.targetTitleIds()), "ordered target titles differ");
        List<TitleHolder> holders = new ArrayList<>();
        for (JsonNode value : array(root.get("target_title_holder_prestate"))) {
            ObjectNode row = StrictJson.object(value, Set.of("title_id", "holder_character_id", "holder_immediate_liege_character_id"));
            JsonNode liege = row.get("holder_immediate_liege_character_id");
            holders.add(new TitleHolder(nativeInt(row.get("title_id"), true), nativeInt(row.get("holder_character_id"), true),
                    liege.isNull() ? Optional.empty() : Optional.of(nativeInt(liege, true))));
        }
        StrictJson.trueValue(root.get("same_frame_stable")); falseValue(root.get("material_complete"));
        unavailable(root, "title_vassal_delta", DeJureExitBaseline.TITLE_REASON);
        unavailable(root, "signed_resource_delta", DeJureExitBaseline.RESOURCE_REASON);
        unavailable(root, "directed_truce", DeJureExitBaseline.TRUCE_REASON);
        List<ResourceBalance> balances = new ArrayList<>();
        for (JsonNode value : array(root.get("primary_resource_balances"))) {
            ObjectNode row = StrictJson.object(value, Set.of("character_id", "resource", "value"));
            balances.add(new ResourceBalance(nativeInt(row.get("character_id"), true), Resource.fromWire(StrictJson.text(row.get("resource"))), fixed(row.get("value"))));
        }
        List<MonthlyIncome> income = new ArrayList<>();
        for (JsonNode value : array(root.get("primary_monthly_gold_income"))) {
            ObjectNode row = StrictJson.object(value, Set.of("character_id", "value"));
            income.add(new MonthlyIncome(nativeInt(row.get("character_id"), true), fixed(row.get("value"))));
        }
        return new DeJureExitBaseline(expectedFrame, holders, balances, income,
                root.has("truce_inputs_v1") ? Optional.of(truce(root.get("truce_inputs_v1"))) : Optional.empty(),
                root.has("border_raid_storage_candidate_v1") ? Optional.of(storage(root.get("border_raid_storage_candidate_v1"))) : Optional.empty());
    }

    private static TruceInputs truce(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "attacker_flexible_truces_perk", "attacker_government_is_nomadic",
                "defender_government_is_nomadic", "nomad_both", "short", "long", "border_raid_pair", "evaluated_days", "persisted_expiry_date_raw"));
        literal(row.get("schema"), "xar.ck3.defender-de-jure-truce-inputs.v1");
        nullValue(row.get("evaluated_days")); nullValue(row.get("persisted_expiry_date_raw"));
        return new TruceInputs(predicate(row.get("attacker_flexible_truces_perk")), predicate(row.get("attacker_government_is_nomadic")),
                predicate(row.get("defender_government_is_nomadic")), predicate(row.get("nomad_both")),
                unread(row.get("short")), unread(row.get("long")), unread(row.get("border_raid_pair")));
    }
    private static Predicate predicate(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("status", "value", "unavailable_reason"));
        String status = StrictJson.text(row.get("status"));
        if (status.equals("observed")) { nullValue(row.get("unavailable_reason")); return new ObservedPredicate(bool(row.get("value"))); }
        require(status.equals("unavailable"), "unknown truce predicate status"); nullValue(row.get("value"));
        return new UnavailablePredicate(StrictJson.text(row.get("unavailable_reason")));
    }
    private static UnavailablePredicate unread(JsonNode value) {
        Predicate predicate = predicate(value);
        require(predicate instanceof UnavailablePredicate, "unadmitted stock condition must remain unavailable");
        return (UnavailablePredicate) predicate;
    }
    private static StorageCandidate storage(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("schema", "status", "candidate", "storage_capacity", "active_war_count",
                "matching_war_count", "unavailable_reason", "native_condition_observed"));
        literal(row.get("schema"), "xar.ck3.h2743-border-raid-storage-candidate.v1"); falseValue(row.get("native_condition_observed"));
        long capacity = nativeInt(row.get("storage_capacity"), false), active = nativeInt(row.get("active_war_count"), false), matching = nativeInt(row.get("matching_war_count"), false);
        String status = StrictJson.text(row.get("status"));
        if (status.equals("unavailable")) {
            nullValue(row.get("candidate")); require(capacity == 0 && active == 0 && matching == 0, "unavailable scan cannot invent counts");
            return new UnavailableStorage(StrictJson.text(row.get("unavailable_reason")));
        }
        require(status.equals("structural_candidate_only"), "unknown storage candidate status"); nullValue(row.get("unavailable_reason"));
        StructuralCandidate candidate = new StructuralCandidate(capacity, active, matching);
        require(bool(row.get("candidate")) == candidate.candidate(), "storage candidate disagrees with observed match count"); return candidate;
    }
    private static long fixed(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("raw", "scale")); require(nativeInt(row.get("scale"), false) == 100_000, "fixed scale differs");
        return nativeInt(row.get("raw"), false);
    }

    public static byte[] encodeRaw(DeJureExitBaseline value) {
        ObjectNode root = common(value); root.put("casus_belli_database_index", 17); root.put("casus_belli_key", "individual_county_de_jure_cb");
        root.put("same_frame_stable", true);
        value.truceInputs().ifPresent(inputs -> root.set("truce_inputs_v1", truceNode(inputs)));
        value.borderRaidStorageCandidate().ifPresent(candidate -> root.set("border_raid_storage_candidate_v1", storageNode(candidate)));
        return StrictJson.canonical(root, MAX_BYTES);
    }
    public static byte[] encodeProjection(DeJureExitBaseline value) { return StrictJson.canonical(projectionNode(value), MAX_BYTES); }
    static ObjectNode projectionNode(DeJureExitBaseline value) {
        ObjectNode root = common(value);
        if (value.truceInputs().isPresent()) { root.set("truce_inputs_v1", truceNode(value.truceInputs().orElseThrow())); }
        else { root.putNull("truce_inputs_v1"); }
        if (value.borderRaidStorageCandidate().isPresent()) { root.set("border_raid_storage_candidate_v1", storageNode(value.borderRaidStorageCandidate().orElseThrow())); }
        else { root.putNull("border_raid_storage_candidate_v1"); }
        root.putNull("recommended_outcome"); root.putNull("action_literal"); return root;
    }
    private static ObjectNode common(DeJureExitBaseline value) {
        require(value != null, "typed observed baseline required"); Frame frame = value.expectedFrame();
        ObjectNode root = StrictJson.object(); root.put("schema", DeJureExitBaseline.SCHEMA); root.put("war_id", frame.warId());
        root.put("native_revision", frame.nativeRevision()); root.put("date_raw", frame.dateRaw());
        root.put("primary_attacker_character_id", frame.attackerId()); root.put("primary_defender_character_id", frame.defenderId());
        ArrayNode titles = root.putArray("target_title_ids"); frame.targetTitleIds().forEach(title -> titles.add(title.longValue()));
        ArrayNode holders = root.putArray("target_title_holder_prestate");
        for (TitleHolder holder : value.titleHolderPrestate()) {
            ObjectNode row = holders.addObject(); row.put("title_id", holder.titleId()); row.put("holder_character_id", holder.holderCharacterId());
            if (holder.holderImmediateLiegeCharacterId().isPresent()) { row.put("holder_immediate_liege_character_id", holder.holderImmediateLiegeCharacterId().orElseThrow()); }
            else { row.putNull("holder_immediate_liege_character_id"); }
        }
        ArrayNode balances = root.putArray("primary_resource_balances");
        for (ResourceBalance balance : value.primaryResourceBalances()) {
            ObjectNode row = balances.addObject(); row.put("character_id", balance.characterId()); row.put("resource", balance.resource().wire()); putFixed(row.putObject("value"), balance.raw());
        }
        ArrayNode income = root.putArray("primary_monthly_gold_income");
        for (MonthlyIncome amount : value.primaryMonthlyGoldIncome()) {
            ObjectNode row = income.addObject(); row.put("character_id", amount.characterId()); putFixed(row.putObject("value"), amount.raw());
        }
        root.putNull("title_vassal_delta"); root.put("title_vassal_delta_unavailable_reason", DeJureExitBaseline.TITLE_REASON);
        root.putNull("signed_resource_delta"); root.put("signed_resource_delta_unavailable_reason", DeJureExitBaseline.RESOURCE_REASON);
        root.putNull("directed_truce"); root.put("directed_truce_unavailable_reason", DeJureExitBaseline.TRUCE_REASON); root.put("material_complete", false); return root;
    }
    private static ObjectNode truceNode(TruceInputs value) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.ck3.defender-de-jure-truce-inputs.v1");
        row.set("attacker_flexible_truces_perk", predicateNode(value.attackerFlexibleTrucesPerk()));
        row.set("attacker_government_is_nomadic", predicateNode(value.attackerGovernmentIsNomadic()));
        row.set("defender_government_is_nomadic", predicateNode(value.defenderGovernmentIsNomadic())); row.set("nomad_both", predicateNode(value.nomadBoth()));
        row.set("short", predicateNode(value.shortCondition())); row.set("long", predicateNode(value.longCondition())); row.set("border_raid_pair", predicateNode(value.borderRaidPair()));
        row.putNull("evaluated_days"); row.putNull("persisted_expiry_date_raw"); return row;
    }
    private static ObjectNode predicateNode(Predicate value) {
        ObjectNode row = StrictJson.object();
        if (value instanceof ObservedPredicate observed) { row.put("status", "observed"); row.put("value", observed.value()); row.putNull("unavailable_reason"); }
        else if (value instanceof UnavailablePredicate unavailable) { row.put("status", "unavailable"); row.putNull("value"); row.put("unavailable_reason", unavailable.reason()); }
        return row;
    }
    private static ObjectNode storageNode(StorageCandidate value) {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.ck3.h2743-border-raid-storage-candidate.v1"); row.put("native_condition_observed", false);
        if (value instanceof StructuralCandidate candidate) {
            row.put("status", "structural_candidate_only"); row.put("candidate", candidate.candidate()); row.put("storage_capacity", candidate.storageCapacity());
            row.put("active_war_count", candidate.activeWarCount()); row.put("matching_war_count", candidate.matchingWarCount()); row.putNull("unavailable_reason");
        } else if (value instanceof UnavailableStorage unavailable) {
            row.put("status", "unavailable"); row.putNull("candidate"); row.put("storage_capacity", 0); row.put("active_war_count", 0); row.put("matching_war_count", 0); row.put("unavailable_reason", unavailable.reason());
        }
        return row;
    }
    private static void putFixed(ObjectNode row, long raw) { row.put("raw", raw); row.put("scale", 100_000); }
    static List<Long> ids(JsonNode value) { List<Long> result = new ArrayList<>(); for (JsonNode row : array(value)) { result.add(nativeInt(row, true)); } return List.copyOf(result); }
    static long nativeInt(JsonNode value, boolean positive) { return StrictJson.integer(value, positive ? 1 : Long.MIN_VALUE, Long.MAX_VALUE); }
    static ArrayNode array(JsonNode value) { require(value instanceof ArrayNode, "JSON array required"); return (ArrayNode) value; }
    static void nullValue(JsonNode value) { require(value != null && value.isNull(), "explicit JSON null required"); }
    static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue(); }
    static void falseValue(JsonNode value) { require(!bool(value), "actual JSON false required"); }
    static void literal(JsonNode value, String expected) { require(expected.equals(StrictJson.text(value)), "literal mismatch: " + expected); }
    private static void unavailable(ObjectNode root, String name, String reason) { nullValue(root.get(name)); literal(root.get(name + "_unavailable_reason"), reason); }
}
