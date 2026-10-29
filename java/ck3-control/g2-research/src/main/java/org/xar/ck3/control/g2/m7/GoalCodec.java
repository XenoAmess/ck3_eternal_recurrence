package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.GoalPlan;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Priority;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Progress;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Reconciliation;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Succession;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Verdict;

/** One strict JSON representation for persisted goals and their ordinary policy projection. */
public final class GoalCodec {
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private GoalCodec() { }
    public static Goal decodeGoal(byte[] raw) { return parseGoal(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES)); }
    public static byte[] encodeGoal(Goal value) { return StrictJson.canonical(goalJson(value), StrictJson.EXPLICIT_MAX_BYTES); }
    public static GoalPlan decodePlan(byte[] raw) { return parsePlan(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES)); }
    public static GoalPlan parsePlan(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of(
                "policy", "goal_key", "campaign_id", "current_character_id", "progress", "focus", "priorities"));
        List<Priority> priorities = new ArrayList<>(); JsonNode items = row.get("priorities");
        StrictJson.require(items.isArray(), "ordinary goal priorities array required");
        for (JsonNode item : items) {
            ObjectNode priority = StrictJson.object(item, Set.of("priority", "action", "reason"));
            priorities.add(new Priority((int) StrictJson.integer(priority.get("priority"), 0, Integer.MAX_VALUE),
                    text(priority, "action"), text(priority, "reason")));
        }
        var result = new GoalPlan(text(row, "policy"), text(row, "goal_key"), text(row, "campaign_id"),
                characterId(row.get("current_character_id")), progress(row.get("progress")), text(row, "focus"), priorities);
        requireCurrentProgress(result.currentCharacterId(), result.progress());
        var expected = OrdinaryCampaignGoal.plan(new Goal(result.campaignId(), result.currentCharacterId(),
                result.currentCharacterId(), result.progress()));
        StrictJson.require(result.equals(expected), "persisted goal plan must equal the shared ordinary producer");
        return result;
    }
    public static byte[] encodePlan(GoalPlan plan) {
        ObjectNode row = StrictJson.object(); row.put("policy", plan.policy()); row.put("goal_key", plan.goalKey());
        row.put("campaign_id", plan.campaignId()); row.put("current_character_id", plan.currentCharacterId());
        row.set("progress", progressJson(plan.progress())); row.put("focus", plan.focus());
        var priorities = row.putArray("priorities");
        for (Priority priority : plan.priorities()) {
            var item = priorities.addObject(); item.put("priority", priority.priority());
            item.put("action", priority.action()); item.put("reason", priority.reason());
        }
        byte[] raw = StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES);
        decodePlan(raw); return raw;
    }

    /** Consume the actual complete M3 producer DTO, never a six-field compatibility alias. */
    public static Reconciliation decodeReconciliation(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES), Set.of(
                "schema", "status", "predecessor_binding", "successor_binding", "predecessor_character_id",
                "expected_successor_character_id", "actual_successor_character_id", "successor_match",
                "expected_inherited_title_ids", "matched_inherited_title_ids", "missing_expected_inherited_title_ids",
                "unexpected_retained_predecessor_title_ids", "expected_other_heir_title_ids", "expected_without_heir_title_ids",
                "observed_additional_successor_title_ids", "title_distribution_match", "verdict", "unavailable_reason"));
        StrictJson.require(text(row, "schema").equals("xar.ck3.succession-reconciliation/v1")
                && text(row, "status").equals("available") && row.get("unavailable_reason").isNull(),
                "original complete succession reconciliation schema");
        ReconciliationFrame before = binding(row.get("predecessor_binding"), true);
        ReconciliationFrame after = binding(row.get("successor_binding"), false);
        long predecessor = characterId(row.get("predecessor_character_id"));
        long successor = characterId(row.get("actual_successor_character_id"));
        StrictJson.require(characterId(row.get("predecessor_binding").get("episode_character_id")) == predecessor
                && predecessor != successor, "complete reconciliation binds distinct actual predecessor and successor");
        StrictJson.require(after.dateRaw() >= before.dateRaw()
                && after.revision().compareTo(before.revision()) >= 0
                && after.nativeRevision().compareTo(before.nativeRevision()) >= 0,
                "post-transition source frame precedes the original expectation");
        Long expectedSuccessor = row.get("expected_successor_character_id").isNull()
                ? null : characterId(row.get("expected_successor_character_id"));
        StrictJson.require(expectedSuccessor == null || expectedSuccessor != predecessor, "expected successor is the predecessor");
        boolean successorMatch = reconciliationBoolean(row, "successor_match");
        boolean distributionMatch = reconciliationBoolean(row, "title_distribution_match");
        List<Long> expected = reconciliationIds(row.get("expected_inherited_title_ids"));
        List<Long> matched = reconciliationIds(row.get("matched_inherited_title_ids"));
        List<Long> missing = reconciliationIds(row.get("missing_expected_inherited_title_ids"));
        List<Long> unexpected = reconciliationIds(row.get("unexpected_retained_predecessor_title_ids"));
        List<Long> other = reconciliationIds(row.get("expected_other_heir_title_ids"));
        List<Long> without = reconciliationIds(row.get("expected_without_heir_title_ids"));
        List<Long> additional = reconciliationIds(row.get("observed_additional_successor_title_ids"));
        Set<Long> originalTitles = new HashSet<>(expected);
        addDisjoint(originalTitles, other); addDisjoint(originalTitles, without);
        StrictJson.require(!originalTitles.isEmpty() && (expectedSuccessor == null) == expected.isEmpty(),
                "complete original estate and primary-title heir distribution required");
        Set<Long> accounted = new HashSet<>(matched); addDisjoint(accounted, missing);
        StrictJson.require(accounted.equals(new HashSet<>(expected)), "inherited title outcomes must partition the original prediction");
        Set<Long> noninherited = new HashSet<>(other); noninherited.addAll(without);
        StrictJson.require(noninherited.containsAll(unexpected), "unexpected retained titles must belong to the original other/no-heir partition");
        addDisjoint(originalTitles, additional);
        StrictJson.require(successorMatch == (expectedSuccessor != null && expectedSuccessor == successor)
                && distributionMatch == (missing.isEmpty() && unexpected.isEmpty()),
                "actual successor and per-title outcomes disagree with reconciliation flags");
        Verdict verdict = switch (text(row, "verdict")) {
            case "matched" -> Verdict.MATCHED;
            case "unexpected_successor" -> Verdict.UNEXPECTED_SUCCESSOR;
            case "title_distribution_mismatch" -> Verdict.TITLE_DISTRIBUTION_MISMATCH;
            default -> throw new IllegalArgumentException("available complete M3 producer verdict required");
        };
        Verdict derived = !successorMatch ? Verdict.UNEXPECTED_SUCCESSOR
                : distributionMatch ? Verdict.MATCHED : Verdict.TITLE_DISTRIBUTION_MISMATCH;
        StrictJson.require(verdict == derived, "verdict differs from actual successor and per-title outcomes");
        return new Reconciliation(verdict, predecessor, successor, matched, other, without);
    }

    public static Goal parseGoal(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("format_version", "goal_key", "campaign_id",
                "origin_character_id", "current_character_id", "progress"));
        StrictJson.integer(row.get("format_version"), 1, 1);
        StrictJson.require(text(row, "goal_key").equals(OrdinaryCampaignGoal.GOAL_KEY), "ordinary dynasty goal key");
        return requireGoal(new Goal(text(row, "campaign_id"), characterId(row.get("origin_character_id")),
                characterId(row.get("current_character_id")), progress(row.get("progress"))));
    }
    static ObjectNode goalJson(Goal value) {
        requireGoal(value);
        ObjectNode row = StrictJson.object(); row.put("format_version", 1); row.put("goal_key", OrdinaryCampaignGoal.GOAL_KEY);
        row.put("campaign_id", value.campaignId()); row.put("origin_character_id", value.originCharacterId());
        row.put("current_character_id", value.currentCharacterId()); row.set("progress", progressJson(value.progress())); return row;
    }
    private static Progress progress(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("reconciled_successions", "last_succession"));
        Progress result = new Progress(integer(row, "reconciled_successions", 0), row.get("last_succession").isNull()
                ? Optional.empty() : Optional.of(succession(row.get("last_succession"))));
        requireProgress(result); return result;
    }
    private static Succession succession(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("predecessor_character_id", "actual_successor_character_id",
                "matched_inherited_title_ids", "expected_other_heir_title_ids", "expected_without_heir_title_ids"));
        return new Succession(characterId(row.get("predecessor_character_id")), characterId(row.get("actual_successor_character_id")),
                reconciliationIds(row.get("matched_inherited_title_ids")), reconciliationIds(row.get("expected_other_heir_title_ids")),
                reconciliationIds(row.get("expected_without_heir_title_ids")));
    }
    private static ObjectNode progressJson(Progress value) {
        ObjectNode row = StrictJson.object(); row.put("reconciled_successions", value.reconciledSuccessions());
        if (value.lastSuccession().isEmpty()) { row.putNull("last_succession"); }
        else {
            Succession last = value.lastSuccession().orElseThrow(); ObjectNode transition = row.putObject("last_succession");
            transition.put("predecessor_character_id", last.predecessorCharacterId());
            transition.put("actual_successor_character_id", last.actualSuccessorCharacterId());
            addIds(transition, "matched_inherited_title_ids", last.matchedInheritedTitleIds());
            addIds(transition, "expected_other_heir_title_ids", last.expectedOtherHeirTitleIds());
            addIds(transition, "expected_without_heir_title_ids", last.expectedWithoutHeirTitleIds());
        }
        return row;
    }
    private static void addIds(ObjectNode row, String field, List<Long> values) {
        var target = row.putArray(field); values.forEach(target::add);
    }
    private static Goal requireGoal(Goal value) {
        requireCurrentProgress(value.currentCharacterId(), value.progress());
        if (value.progress().lastSuccession().isEmpty()) {
            StrictJson.require(value.originCharacterId() == value.currentCharacterId(),
                    "an unreconciled goal must retain its original actor");
        } else if (value.progress().reconciledSuccessions() == 1) {
            StrictJson.require(value.progress().lastSuccession().orElseThrow().predecessorCharacterId() == value.originCharacterId(),
                    "the first reconciliation must continue the original goal actor");
        }
        return value;
    }
    private static void requireCurrentProgress(long currentCharacterId, Progress value) {
        requireProgress(value);
        value.lastSuccession().ifPresent(last -> StrictJson.require(last.actualSuccessorCharacterId() == currentCharacterId,
                "the retained reconciliation must belong to the current goal actor"));
    }
    private static void requireProgress(Progress value) {
        StrictJson.require((value.reconciledSuccessions() == 0) == value.lastSuccession().isEmpty(),
                "the reconciliation count and last succession must agree");
        value.lastSuccession().ifPresent(last -> {
            StrictJson.require(last.predecessorCharacterId() != last.actualSuccessorCharacterId(),
                    "a retained succession must change the goal actor");
            requireOriginalIds(last.matchedInheritedTitleIds());
            requireOriginalIds(last.expectedOtherHeirTitleIds());
            requireOriginalIds(last.expectedWithoutHeirTitleIds());
            Set<Long> original = new HashSet<>(last.matchedInheritedTitleIds());
            StrictJson.require(!original.isEmpty(), "a matched succession must retain its predicted primary estate");
            addDisjoint(original, last.expectedOtherHeirTitleIds());
            addDisjoint(original, last.expectedWithoutHeirTitleIds());
        });
    }
    private record ReconciliationFrame(BigInteger revision, BigInteger nativeRevision, int dateRaw) { }
    private static ReconciliationFrame binding(JsonNode value, boolean predecessor) {
        ObjectNode row = StrictJson.object(value, predecessor ? Set.of("snapshot_id", "revision", "native_revision",
                "date_raw", "episode_run_id", "episode_character_id") : Set.of("snapshot_id", "revision", "native_revision", "date_raw"));
        text(row, "snapshot_id");
        BigInteger revision = StrictJson.integer(row.get("revision"), BigInteger.ZERO, UINT64_MAX);
        BigInteger nativeRevision = StrictJson.integer(row.get("native_revision"), BigInteger.ZERO, UINT64_MAX);
        int dateRaw = (int) StrictJson.integer(row.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        if (predecessor) { text(row, "episode_run_id"); characterId(row.get("episode_character_id")); }
        return new ReconciliationFrame(revision, nativeRevision, dateRaw);
    }
    private static long reconciliationId(JsonNode value) { return StrictJson.integer(value, 1, Integer.MAX_VALUE); }
    private static long characterId(JsonNode value) { return NativeCharacterId.fromJson(value).value(); }
    private static boolean reconciliationBoolean(ObjectNode row, String field) {
        JsonNode value = row.get(field); StrictJson.require(value.isBoolean(), "exact reconciliation boolean");
        return value.booleanValue();
    }
    private static List<Long> reconciliationIds(JsonNode values) {
        StrictJson.require(values != null && values.isArray(), "explicit original title ID array required");
        List<Long> result = new ArrayList<>(); long previous = 0;
        for (JsonNode value : values) {
            long id = reconciliationId(value);
            StrictJson.require(id > previous, "original M3 title IDs must be unique and sorted");
            result.add(id); previous = id;
        }
        return List.copyOf(result);
    }
    private static void requireOriginalIds(List<Long> values) {
        long previous = 0;
        for (long id : values) {
            StrictJson.require(id > previous && id <= Integer.MAX_VALUE, "retained M3 title IDs must be sorted unique positive int32");
            previous = id;
        }
    }
    private static void addDisjoint(Set<Long> titles, List<Long> added) {
        for (long title : added) { StrictJson.require(titles.add(title), "original title outcome partitions overlap"); }
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static long integer(ObjectNode row, String field, long minimum) { return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER); }
}
