package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Central bounded raw-token boundary. SDK containers are projected, not exact-key rewritten. */
public final class SuccessionCodec {
    public static final int MAX_BYTES = 131_072;
    private static final ObjectMapper JSON = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private static final Set<String> EXPECTATION_KEYS = Set.of("schema", "status", "binding", "expectation_state", "predecessor_character_id", "expected_successor_character_id", "title_expectations", "risk_state", "unavailable_reason");
    private static final Set<String> FRAME_KEYS = Set.of("snapshot_id", "revision", "native_revision", "date_raw");
    private static final Set<String> BINDING_KEYS = Set.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "episode_character_id");
    private SuccessionCodec() { }

    public static Expectation decodeExpectation(byte[] body) { return expectation(parse(body)); }
    public static byte[] encodeExpectation(Expectation expectation) { return encode(expectationNode(expectation)); }
    public static byte[] normalize(byte[] body) { return encodeExpectation(decodeExpectation(body)); }
    public static byte[] freeze(byte[] bundle, String episodeRunId, int episodeCharacterId) {
        return encodeExpectation(SuccessionPolicy.freeze(turnBundle(parse(bundle), true), episodeRunId, episodeCharacterId));
    }
    public static byte[] reconcile(byte[] expectation, byte[] postSnapshot, byte[] postBundle) {
        return encodeReconciliation(SuccessionPolicy.reconcile(decodeExpectation(expectation), snapshot(parse(postSnapshot)), turnBundle(parse(postBundle), false)));
    }
    public static byte[] operating(byte[] currentSnapshot, byte[] previousExpectation) {
        JsonNode source = parse(currentSnapshot); Snapshot snapshot = snapshot(source);
        Expectation current = forgivingExpectation(source.isObject() ? source.get("succession_expectation") : null);
        JsonNode previousSource = previousExpectation == null ? null : parse(previousExpectation);
        Expectation previous = forgivingExpectation(previousSource);
        return encodeOperating(SuccessionPolicy.operating(snapshot, current, previous, previousSource != null && !previousSource.isNull()));
    }
    static JsonNode parse(byte[] bytes) {
        check(bytes != null && bytes.length > 0 && bytes.length <= MAX_BYTES, "bounded nonempty succession JSON required");
        JsonNode value = FullJsonTree.parse(bytes, MAX_BYTES);
        unicode(value);
        return value;
    }
    static byte[] encode(JsonNode value) {
        unicode(value);
        try { byte[] bytes = JSON.writeValueAsBytes(value); check(bytes.length <= MAX_BYTES, "succession byte budget exceeded"); return bytes; }
        catch (IOException error) { throw new IllegalArgumentException("succession JSON encoding failed", error); }
    }
    static Expectation expectation(JsonNode value) {
        exact(value, EXPECTATION_KEYS); check(text(field(value, "schema")).equals(EXPECTATION_SCHEMA), "expectation schema changed");
        check(text(field(value, "status")).equals("available") && field(value, "unavailable_reason").isNull(), "available expectation required");
        Binding binding = binding(field(value, "binding")); List<TitleRow> rows = new ArrayList<>();
        for (JsonNode row : array(field(value, "title_expectations"))) { rows.add(row(row, false)); }
        return new Expectation(binding, state(field(value, "expectation_state")), character(field(value, "predecessor_character_id")),
                nullableCharacter(field(value, "expected_successor_character_id")), rows, risk(field(value, "risk_state")));
    }
    private static Expectation forgivingExpectation(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        try { return expectation(value); } catch (IllegalArgumentException error) { return null; }
    }
    static TurnBundle turnBundle(JsonNode value, boolean forFreeze) {
        object(value); check(text(field(value, "schema")).equals("xar.ck3.turn-bundle/v1"), "turn bundle schema changed");
        String status = text(field(value, "status")); check(status.equals("available") || status.equals("partial"), "turn bundle unavailable");
        Frame frame = frame(field(value, "binding"), false);
        JsonNode succession = available(field(value, "succession_state")); object(succession);
        JsonNode partition = available(field(succession, "partition")); object(partition);
        List<TitleRow> rows = new ArrayList<>(); Set<Integer> seen = new HashSet<>(); int primaries = 0;
        for (JsonNode raw : array(field(partition, "title_heirs"))) {
            TitleRow row = row(raw, true); check(seen.add(row.title().titleId()), "duplicate title"); rows.add(row); if (row.primary()) { primaries++; }
        }
        check(primaries == 1, "exactly one primary required");
        Actor ruler = actor(available(field(value, "ruler_state"))); Integer heir = null; RiskState risk = null;
        if (forFreeze) {
            JsonNode component = field(succession, "primary_title_heir_character_id"); object(component);
            String heirStatus = text(field(component, "status"));
            if (heirStatus.equals("available")) { heir = character(field(component, "value")); }
            else { check(heirStatus.equals("not_applicable") && field(component, "value").isNull()
                    && field(component, "unavailable_reason").isTextual(), "primary heir component malformed"); }
            risk = risk(field(partition, "risk_state"));
        }
        return new TurnBundle(frame, ruler, rows, heir, risk);
    }
    static TitleRow row(JsonNode value, boolean bundle) {
        Set<String> legacy = Set.of("title", "first_heir_character_id", "primary");
        Set<String> current = Set.of("title", "first_heir_character_id", "primary", "capital_province_id");
        Set<String> family = Set.of("title", "first_heir_character_id", "primary", "capital_province_id", "capital_province_kind", "title_key");
        if (bundle && keys(value).equals(family)) {
            JsonNode title = field(value, "title");
            exact(title, Set.of("title_id", "tier_raw", "tier_key"));
            positive(field(title, "title_id"));
            check(integer(field(title, "tier_raw"), 2, 2) == 2 && "county".equals(text(field(title, "tier_key"))), "family title must be county");
            String titleKey = text(field(value, "title_key"));
            check(titleKey.length() >= 3 && titleKey.length() <= 1024 && titleKey.matches("c_[A-Za-z0-9][A-Za-z0-9_]*")
                    && field(value, "capital_province_id").isNull()
                    && "landless_noble_family_no_province".equals(text(field(value, "capital_province_kind"))), "explicit native family no-province row required");
        }
        else if (bundle && keys(value).equals(current)) {
            try { nullablePositive(field(value, "capital_province_id")); }
            catch (IllegalArgumentException error) {
                throw new IllegalArgumentException("succession capital province is malformed", error);
            }
        }
        else { exact(value, legacy); }
        JsonNode title = field(value, "title"); object(title); int id = positive(field(title, "title_id"));
        JsonNode tier = title.get("tier_raw"); BigInteger integerTier = tier != null && tier.isIntegralNumber() ? tier.bigIntegerValue() : null;
        return new TitleRow(new Title(id, integerTier, new WireObject(encode(title))), nullableCharacter(field(value, "first_heir_character_id")), bool(field(value, "primary")));
    }
    static Snapshot snapshot(JsonNode source) {
        if (!source.isObject()) { return null; }
        Frame frame = null;
        if (FRAME_KEYS.stream().allMatch(source::has)) { frame = frame(source, false); }
        JsonNode actorWire = source.get("played_character"); Actor played = actorWire != null && actorWire.isObject() && actorWire.has("character_id") ? actor(actorWire) : null;
        JsonNode lifecycleWire = source.path("succession_lifecycle").path("lifecycle"); Lifecycle lifecycle = null;
        if (lifecycleWire.isTextual()) {
            lifecycle = switch (lifecycleWire.textValue()) { case "ordinary_campaign_succession" -> Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION;
                case "rogue_one_life" -> Lifecycle.ROGUE_ONE_LIFE; case "unknown" -> Lifecycle.UNKNOWN; default -> null; };
        }
        return new Snapshot(frame, optionalText(source, "episode_run_id"), optionalCharacter(source, "episode_character_id"), optionalBool(source, "paused"), optionalBool(source, "map_ready"),
                optionalBool(source, "one_life_terminal"), optionalText(source, "one_life_terminal_reason"), played,
                nonnull(source.get("active_event")), nonnull(source.get("pending_character_interaction")), lifecycle);
    }
    private static boolean nonnull(JsonNode value) { return value != null && !value.isNull(); }
    private static Actor actor(JsonNode value) { object(value); return new Actor(character(field(value, "character_id")), Boolean.TRUE.equals(optionalBool(value, "alive"))); }
    static Binding binding(JsonNode value) { exact(value, BINDING_KEYS); return new Binding(frame(value, false), text(field(value, "episode_run_id")), character(field(value, "episode_character_id"))); }
    static Frame frame(JsonNode value, boolean exact) {
        if (exact) { exact(value, FRAME_KEYS); } else { object(value); }
        return new Frame(text(field(value, "snapshot_id")), uint64(field(value, "revision")), uint64(field(value, "native_revision")), integer(field(value, "date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
    static ObjectNode expectationNode(Expectation value) {
        ObjectNode out = objectNode(); out.put("schema", EXPECTATION_SCHEMA).put("status", "available"); out.set("binding", bindingNode(value.binding()));
        out.put("expectation_state", wire(value.state())); out.put("predecessor_character_id", value.predecessorCharacterId()); nullableId(out, "expected_successor_character_id", value.expectedSuccessorCharacterId());
        out.set("title_expectations", rowsNode(value.titleExpectations())); out.put("risk_state", wire(value.riskState())).putNull("unavailable_reason"); return out;
    }
    private static ArrayNode rowsNode(List<TitleRow> rows) {
        ArrayNode out = JSON.createArrayNode(); for (TitleRow row : rows) { ObjectNode item = objectNode(); JsonNode title = parse(row.title().original().bytes());
            check(positive(field(title, "title_id")) == row.title().titleId(), "title metadata identity changed");
            JsonNode tier = title.get("tier_raw"); BigInteger integerTier = tier != null && tier.isIntegralNumber() ? tier.bigIntegerValue() : null;
            check(java.util.Objects.equals(integerTier, row.title().integerTier()), "title metadata rank changed"); item.set("title", title);
            nullableId(item, "first_heir_character_id", row.firstHeirCharacterId()); item.put("primary", row.primary()); out.add(item); } return out;
    }
    private static ObjectNode frameNode(Frame frame) { ObjectNode out = objectNode(); out.put("snapshot_id", frame.snapshotId()).put("revision", frame.revision()).put("native_revision", frame.nativeRevision()).put("date_raw", frame.dateRaw()); return out; }
    private static ObjectNode bindingNode(Binding binding) { ObjectNode out = frameNode(binding.frame()); out.put("episode_run_id", binding.episodeRunId()).put("episode_character_id", binding.episodeCharacterId()); return out; }
    public static byte[] encodeReconciliation(Reconciliation value) {
        ObjectNode out = objectNode(); out.put("schema", RECONCILIATION_SCHEMA).put("status", "available"); out.set("predecessor_binding", bindingNode(value.predecessorBinding())); out.set("successor_binding", frameNode(value.successorBinding()));
        out.put("predecessor_character_id", value.predecessorCharacterId()); nullableId(out, "expected_successor_character_id", value.expectedSuccessorCharacterId()); out.put("actual_successor_character_id", value.actualSuccessorCharacterId()).put("successor_match", value.successorMatch());
        ids(out, "expected_inherited_title_ids", value.expectedInheritedTitleIds()); ids(out, "matched_inherited_title_ids", value.matchedInheritedTitleIds()); ids(out, "missing_expected_inherited_title_ids", value.missingExpectedInheritedTitleIds());
        ids(out, "unexpected_retained_predecessor_title_ids", value.unexpectedRetainedPredecessorTitleIds()); ids(out, "expected_other_heir_title_ids", value.expectedOtherHeirTitleIds()); ids(out, "expected_without_heir_title_ids", value.expectedWithoutHeirTitleIds());
        ids(out, "observed_additional_successor_title_ids", value.observedAdditionalSuccessorTitleIds()); out.put("title_distribution_match", value.titleDistributionMatch()).put("verdict", wire(value.verdict())).putNull("unavailable_reason"); return encode(out);
    }
    public static byte[] encodeOperating(OperatingResult value) {
        ObjectNode out = objectNode(); out.put("schema", OPERATING_SCHEMA); out.putArray("action_candidates"); out.put("queries_performed", 0).put("ordinary_priority_override", false).put("submission_authorized", false);
        if (value instanceof UnavailableOperating unavailable) {
            out.put("status", unavailable.playerDecisionPending() ? "deferred_player_decision" : "unavailable"); out.putNull("source_binding").putNull("estate"); out.putArray("issues"); out.putNull("observed_changes").put("unavailable_reason", unavailable.reason()); return encode(out);
        }
        AvailableOperating available = (AvailableOperating) value; out.put("status", "available"); out.set("source_binding", bindingNode(available.sourceBinding()));
        out.put("source_kind", "original_complete_expectation_on_same_published_frame").put("published_frame_is_not_an_estate_or_law_epoch", true);
        Estate estate = available.estate(); ObjectNode estateWire = out.putObject("estate"); estateWire.put("primary_title_id", estate.primaryTitleId()); nullableId(estateWire, "primary_title_heir_character_id", estate.primaryTitleHeirCharacterId());
        estateWire.put("risk_state", wire(estate.riskState())); estateWire.set("title_expectations", rowsNode(estate.titleExpectations()));
        ids(estateWire, "personal_estate_titles_to_primary_title_heir", estate.primaryHeirTitles()); ids(estateWire, "personal_estate_titles_to_other_heirs", estate.otherHeirTitles()); ids(estateWire, "titles_without_observed_heir", estate.withoutHeirTitles());
        ids(estateWire, "equal_or_higher_rank_titles_to_other_heirs", estate.equalOrHigherOtherHeirTitles()); ids(estateWire, "other_heir_title_rank_unavailable", estate.unknownRankOtherHeirTitles());
        ArrayNode issues = out.putArray("issues"); for (Issue issue : available.issues()) { ObjectNode row = issues.addObject(); row.put("kind", wire(issue.kind())); ids(row, "title_ids", issue.titleIds()); if (issue.kind() == IssueKind.OTHER_HEIR_RECEIVES_EQUAL_OR_HIGHER_RANK_TITLE) { row.put("actual_realm_exit_proven", false); } }
        Changes changes = available.changes(); if (changes == null) { out.putNull("observed_changes"); } else { ObjectNode changed = out.putObject("observed_changes"); changed.set("source_binding", bindingNode(changes.sourceBinding()));
            ids(changed, "added_held_title_ids", changes.addedTitles()); ids(changed, "removed_held_title_ids", changes.removedTitles()); ids(changed, "changed_first_heir_title_ids", changes.changedFirstHeirTitles());
            changed.put("primary_title_changed", changes.primaryTitleChanged()).put("primary_title_heir_changed", changes.primaryTitleHeirChanged()); }
        if (available.previousComparisonUnavailableReason() == null) { out.putNull("previous_comparison_unavailable_reason"); } else { out.put("previous_comparison_unavailable_reason", available.previousComparisonUnavailableReason()); }
        ArrayNode missing = out.putArray("missing_operating_inputs"); for (String item : List.of("same_published_frame_estate_or_law_change_witness", "independently_qualified_current_legal_player_heir_and_dynasty", "current_realm_and_title_succession_laws", "candidate_action_final_permission_cost_and_political_consequences", "native_counterfactual_distribution_for_a_supported_action", "actual_post_partition_realm_relationships")) { missing.add(item); }
        out.put("law_change_inferred_from_title_distribution", false).put("actual_land_loss_or_realm_exit_inferred", false).putNull("unavailable_reason"); return encode(out);
    }
    private static void ids(ObjectNode out, String key, List<Integer> values) { ArrayNode array = out.putArray(key); values.forEach(array::add); }
    private static void nullableId(ObjectNode out, String key, Integer id) { if (id == null) { out.putNull(key); } else { out.put(key, id); } }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static ExpectationState state(JsonNode value) { return switch (text(value)) { case "successor_expected" -> ExpectationState.SUCCESSOR_EXPECTED; case "no_primary_heir" -> ExpectationState.NO_PRIMARY_HEIR; default -> throw new IllegalArgumentException("invalid expectation state"); }; }
    private static RiskState risk(JsonNode value) { return switch (text(value)) { case "single_successor" -> RiskState.SINGLE_SUCCESSOR; case "split_successors" -> RiskState.SPLIT_SUCCESSORS; case "no_primary_heir" -> RiskState.NO_PRIMARY_HEIR; default -> throw new IllegalArgumentException("invalid succession risk"); }; }
    private static JsonNode available(JsonNode value) { object(value); check(text(field(value, "status")).equals("available") && (!value.has("unavailable_reason") || value.get("unavailable_reason").isNull()), "available component required"); return field(value, "value"); }
    static ObjectNode objectNode() { return JSON.createObjectNode(); }
    static JsonNode field(JsonNode value, String name) { object(value); check(value.has(name), "missing succession field: " + name); return value.get(name); }
    private static void object(JsonNode value) { check(value != null && value.isObject(), "succession object required"); }
    private static Set<String> keys(JsonNode value) { object(value); Set<String> result = new HashSet<>(); value.fieldNames().forEachRemaining(result::add); return result; }
    static void exact(JsonNode value, Set<String> expected) { check(keys(value).equals(expected), "succession fields changed"); }
    private static List<JsonNode> array(JsonNode value) { check(value.isArray() && value.size() <= 4096, "bounded succession array required"); List<JsonNode> values = new ArrayList<>(); value.forEach(values::add); return values; }
    static String text(JsonNode value) { check(value != null && value.isTextual() && !value.textValue().isEmpty(), "nonempty succession string required"); return value.textValue(); }
    private static int character(JsonNode value) { return NativeCharacterId.fromJson(value).value(); }
    private static Integer nullableCharacter(JsonNode value) { return value.isNull() ? null : character(value); }
    private static int positive(JsonNode value) { return integer(value, 1, Integer.MAX_VALUE); }
    private static Integer nullablePositive(JsonNode value) { return value.isNull() ? null : positive(value); }
    private static int integer(JsonNode value, int low, int high) { check(value != null && value.isIntegralNumber() && value.bigIntegerValue().compareTo(BigInteger.valueOf(low)) >= 0 && value.bigIntegerValue().compareTo(BigInteger.valueOf(high)) <= 0, "exact int32 required"); return value.intValue(); }
    private static BigInteger uint64(JsonNode value) { check(value != null && value.isIntegralNumber(), "exact uint64 integer token required"); BigInteger result = value.bigIntegerValue(); SuccessionModel.uint64(result); return result; }
    private static boolean bool(JsonNode value) { check(value != null && value.isBoolean(), "exact boolean required"); return value.booleanValue(); }
    private static Boolean optionalBool(JsonNode value, String key) { JsonNode item = value.get(key); return item == null || item.isNull() ? null : bool(item); }
    private static String optionalText(JsonNode value, String key) { JsonNode item = value.get(key); if (item == null || item.isNull()) { return null; } check(item.isTextual(), "string/null required"); return item.textValue(); }
    private static Integer optionalCharacter(JsonNode value, String key) { JsonNode item = value.get(key); return item == null || item.isNull() ? null : character(item); }
    private static void unicode(JsonNode value) {
        if (value.isTextual()) { validUnicode(value.textValue()); }
        if (value.isObject()) { value.fieldNames().forEachRemaining(SuccessionCodec::validUnicode); }
        if (value.isContainerNode()) { value.forEach(SuccessionCodec::unicode); }
    }
    private static void validUnicode(String text) { for (int i = 0; i < text.length(); i++) { char ch = text.charAt(i); if (Character.isHighSurrogate(ch)) { check(i + 1 < text.length() && Character.isLowSurrogate(text.charAt(++i)), "unpaired JSON surrogate"); } else { check(!Character.isLowSurrogate(ch), "unpaired JSON surrogate"); } } }
}
