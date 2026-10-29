package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligations.STEP;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligations.*;

/** Exact current serializer plus the two retained original .2 compatibility packets. No world action. */
public final class FamilyObligationsCodec {
    private static final int MAX = 1_048_576;
    private static final String COST_KEYS = "gold prestige piety renown influence herd treasury treasury_or_gold merit barter_goods";
    private static final Set<String> ROOT = keys("schema_version kind game_version executable_sha256 query_status frame native_child_house_preview alliance_obligations betrothal_break_terms step accepted private_build read_only advertised snapshot_revision");
    private static final Set<String> DIAGNOSTICS = keys("native_send_precheck_passed native_send_setup_passed native_send_availability_passed native_send_pair_restriction_blocked native_send_diplomatic_range_passed native_send_already_considering_blocked native_send_answer_status_raw native_send_definition_gate_results native_first_failed_send_stage");
    private static final Set<String> C88 = keys("native_c88_failure_description_status native_c88_failure_description_text");
    private static final Set<String> WAR = keys("war_id caller_character_id recipient_character_id caller_side recipient_side primary_attacker_character_id primary_defender_character_id attacker_character_ids defender_character_ids caller_is_primary_war_leader recipient_was_called native_target_can_be_picked native_target_row_selectable native_complete_can_send send_cost_raw recipient_acceptance_raw recipient_answer_status_raw native_auto_accept");
    private FamilyObligationsCodec() { }

    public static Request decodeRequest(byte[] bytes) { return decodeRequest(StrictJson.parse(bytes)); }
    public static Request decodeRequest(JsonNode node) {
        ObjectNode n = object(node); Set<String> fields = keys("expected_revision");
        for (String key : List.of("subject_character_id", "candidate_character_id", "request_matrilineal_option", "break_recipient_character_id", "ally_character_id", "enumerate_current_allies")) if (n.has(key)) fields.add(key);
        StrictJson.object(n, fields);
        boolean pair = n.has("subject_character_id") || n.has("candidate_character_id");
        Optional<Pair> selectedPair = pair ? Optional.of(new Pair(id(n.get("subject_character_id")), id(n.get("candidate_character_id")))) : Optional.empty();
        return new Request(positive(n.get("expected_revision")), selectedPair,
                n.has("request_matrilineal_option") && bool(n.get("request_matrilineal_option")),
                optionalRequestId(n, "break_recipient_character_id"), optionalRequestId(n, "ally_character_id"),
                n.has("enumerate_current_allies") && bool(n.get("enumerate_current_allies")));
    }
    public static RawJson encodeRequest(Request request) {
        ObjectNode n = wireFields(request); n.put("expected_revision", request.expectedRevision());
        return new RawJson(StrictJson.canonical(n));
    }
    /** Native transport adds the registered expected native revision fields, never the public revision. */
    public static ObjectNode wireFields(Request request) {
        Objects.requireNonNull(request); ObjectNode n = StrictJson.object().put("request_matrilineal_option", request.matrilineal());
        request.pair().ifPresent(pair -> n.put("subject_character_id", pair.subject()).put("candidate_character_id", pair.candidate()));
        request.breakRecipient().ifPresent(value -> n.put("break_recipient_character_id", value));
        request.ally().ifPresent(value -> n.put("ally_character_id", value));
        if (request.enumerateCurrentAllies()) n.put("enumerate_current_allies", true);
        return n;
    }
    public static Observation decodeNative(RawJson original, Binding binding, Request request) {
        Objects.requireNonNull(original); Objects.requireNonNull(binding); Objects.requireNonNull(request);
        StrictJson.require(binding.publicRevision().equals(request.expectedRevision()), "public family request revision changed");
        ObjectNode n = object(StrictJson.parse(original.bytes(), MAX)); Set<String> fields = new HashSet<>(ROOT);
        if (n.has("current_native_allies")) fields.add("current_native_allies");
        StrictJson.object(n, fields); equal(n, "step", STEP); yes(n.get("accepted")); yes(n.get("private_build")); yes(n.get("read_only")); no(n.get("advertised"));
        integer(n.get("schema_version"), 1, 1); equal(n, "kind", "ck3_12002_family_obligations_private_v1");
        equal(n, "game_version", binding.build().version());
        StrictJson.require(StrictJson.text(n.get("executable_sha256")).equalsIgnoreCase(binding.build().sha256()), "exact family version/SHA pair required");
        exact(n.get("snapshot_revision"), binding.nativeRevision());
        ObjectNode frame = StrictJson.object(n.get("frame"), keys("snapshot_revision date_raw played_character_id paused map_ready played_character_alive"));
        exact(frame.get("snapshot_revision"), binding.nativeRevision()); integer(frame.get("date_raw"), binding.dateRaw(), binding.dateRaw()); integer(frame.get("played_character_id"), binding.playedCharacterId(), binding.playedCharacterId());
        yes(frame.get("paused")); yes(frame.get("map_ready")); yes(frame.get("played_character_alive"));
        Lineage lineage = lineage(n.get("native_child_house_preview"), request);
        Alliance alliance = alliance(n.get("alliance_obligations"), request, binding.playedCharacterId());
        Optional<Allies> allies = n.has("current_native_allies") ? Optional.of(allies(n.get("current_native_allies"), request, binding.playedCharacterId())) : Optional.empty();
        StrictJson.require(binding.build() != Build.CURRENT4 || allies.isPresent(), "current serializer must retain current_native_allies group");
        StrictJson.require(!request.enumerateCurrentAllies() || allies.isPresent(), "requested current allies group missing");
        BetrothalBreak betrothal = betrothal(n.get("betrothal_break_terms"), request);
        QueryStatus status = enumValue(QueryStatus.class, n.get("query_status"));
        int requested = request.pair().isPresent() ? 1 : 0;
        int available = lineage.status() == Status.AVAILABLE ? 1 : 0;
        if (request.ally().isPresent()) { requested++; if (alliance.status() == Status.AVAILABLE) available++; }
        if (request.enumerateCurrentAllies()) { requested++; if (allies.orElseThrow().status() == Status.AVAILABLE) available++; }
        if (request.breakRecipient().isPresent()) { requested++; if (betrothal.values().isPresent()) available++; }
        QueryStatus derived = available == requested ? QueryStatus.AVAILABLE : available == 0 ? QueryStatus.UNAVAILABLE : QueryStatus.PARTIAL;
        StrictJson.require(status == derived, "family aggregate availability differs from its actual requested groups");
        return new Observation(binding, request, status, lineage, alliance, allies, betrothal, original);
    }
    /** Roundtrip checks typed content against the immutable original result, including absent versus null fields. */
    public static RawJson encodeNative(Observation observation) {
        Objects.requireNonNull(observation);
        StrictJson.require(observation.equals(decodeNative(observation.originalNativeResult(), observation.binding(), observation.request())), "typed family observation differs from original source");
        return observation.originalNativeResult();
    }
    private static Lineage lineage(JsonNode node, Request request) {
        ObjectNode n = object(node); Status status = enumValue(Status.class, n.get("status"));
        StrictJson.require(status != Status.DEFERRED_BY_OWNER, "lineage deferred status is not authored");
        Set<String> fields = keys("status reason subject_character_id candidate_character_id requested_matrilineal_option");
        if (status == Status.AVAILABLE) fields.addAll(keys("selected_matrilineal_option effective_matrilineal_if_accepted complete_can_send native_selected_parent_character_id house_id dynasty_id"));
        StrictJson.object(n, fields); OptionalLong subject = nullableId(n.get("subject_character_id")), candidate = nullableId(n.get("candidate_character_id"));
        boolean requested = bool(n.get("requested_matrilineal_option"));
        StrictJson.require(subject.equals(request.pair().map(pair -> OptionalLong.of(pair.subject())).orElseGet(OptionalLong::empty))
                && candidate.equals(request.pair().map(pair -> OptionalLong.of(pair.candidate())).orElseGet(OptionalLong::empty)) && requested == request.matrilineal(), "native lineage bound to another pair/option");
        StrictJson.require((status == Status.NOT_REQUESTED) == request.pair().isEmpty(), "native lineage sampling differs from request");
        Optional<LineageTerms> terms = status == Status.AVAILABLE ? Optional.of(new LineageTerms(bool(n.get("selected_matrilineal_option")), bool(n.get("effective_matrilineal_if_accepted")),
                bool(n.get("complete_can_send")), id(n.get("native_selected_parent_character_id")), nullableNonnegativeId(n.get("house_id")), nullableNonnegativeId(n.get("dynasty_id")))) : Optional.empty();
        return new Lineage(status, string(n.get("reason")), subject, candidate, requested, terms);
    }
    private static Alliance alliance(JsonNode node, Request request, long player) {
        ObjectNode n = object(node); Status status = enumValue(Status.class, n.get("status"));
        Set<String> fields = keys("status reason first_character_id second_character_id");
        if (status == Status.AVAILABLE) fields.addAll(keys("first_has_second second_has_first raw_scale send_cost_slot_keys first_wars second_wars"));
        StrictJson.object(n, fields); OptionalLong first = nullableId(n.get("first_character_id")), second = nullableId(n.get("second_character_id"));
        if (request.ally().isEmpty()) StrictJson.require(status == Status.NOT_REQUESTED || status == Status.DEFERRED_BY_OWNER, "unrequested alliance was sampled");
        else StrictJson.require((status == Status.AVAILABLE || status == Status.UNAVAILABLE) && first.equals(OptionalLong.of(player)) && second.equals(request.ally()), "alliance differs from requested player/ally pair");
        Optional<AllianceTerms> terms = Optional.empty();
        if (status == Status.AVAILABLE) {
            integer(n.get("raw_scale"), 100000, 100000); JsonNode slots = array(n.get("send_cost_slot_keys")); String[] names = COST_KEYS.split(" ");
            StrictJson.require(slots.size() == names.length, "all ten source cost names required");
            for (int index = 0; index < names.length; index++) StrictJson.require(names[index].equals(StrictJson.text(slots.get(index))), "source resource slot order changed");
            long ally = request.ally().orElseThrow();
            terms = Optional.of(new AllianceTerms(bool(n.get("first_has_second")), bool(n.get("second_has_first")), wars(n.get("first_wars"), player, ally), wars(n.get("second_wars"), ally, player)));
        }
        return new Alliance(status, string(n.get("reason")), first, second, terms);
    }
    private static List<War> wars(JsonNode node, long caller, long recipient) {
        List<War> result = new ArrayList<>();
        for (JsonNode row : array(node)) {
            ObjectNode n = object(row); Set<String> fields = new HashSet<>(WAR);
            boolean hasSelectedAvailability = n.has("native_selected_target_context_available"); if (hasSelectedAvailability) fields.add("native_selected_target_context_available");
            boolean hasDiagnostics = any(n, DIAGNOSTICS), hasDescription = any(n, C88);
            if (hasDiagnostics) fields.addAll(DIAGNOSTICS); if (hasDescription) fields.addAll(C88); StrictJson.object(n, fields);
            integer(n.get("caller_character_id"), caller, caller); integer(n.get("recipient_character_id"), recipient, recipient);
            Side callerSide = enumValue(Side.class, n.get("caller_side")); StrictJson.require(callerSide != Side.ABSENT, "native caller absent from war");
            Side recipientSide = enumValue(Side.class, n.get("recipient_side"));
            boolean selected = !hasSelectedAvailability || bool(n.get("native_selected_target_context_available"));
            boolean canPick = bool(n.get("native_target_can_be_picked")), rowSelectable = bool(n.get("native_target_row_selectable"));
            Optional<SelectedTerms> terms;
            if (selected) terms = Optional.of(new SelectedTerms(bool(n.get("native_complete_can_send")), costs(n.get("send_cost_raw")), signed(n.get("recipient_acceptance_raw")), answer(n.get("recipient_answer_status_raw")), bool(n.get("native_auto_accept"))));
            else {
                StrictJson.require(!canPick && !rowSelectable, "unselected native war cannot claim selectable terms");
                nil(n, keys("native_complete_can_send send_cost_raw recipient_acceptance_raw recipient_answer_status_raw native_auto_accept")); terms = Optional.empty();
            }
            Optional<Diagnostics> diagnostics = Optional.empty();
            if (hasDiagnostics) {
                if (!selected) { nil(n, DIAGNOSTICS); diagnostics = Optional.of(new Diagnostics(Optional.empty())); }
                else {
                    List<Boolean> gates = new ArrayList<>(); for (JsonNode gate : array(n.get("native_send_definition_gate_results"))) gates.add(bool(gate));
                    DiagnosticValues values = new DiagnosticValues(answer(n.get("native_send_answer_status_raw")), bool(n.get("native_send_precheck_passed")), bool(n.get("native_send_setup_passed")), bool(n.get("native_send_availability_passed")),
                            bool(n.get("native_send_pair_restriction_blocked")), bool(n.get("native_send_diplomatic_range_passed")), bool(n.get("native_send_already_considering_blocked")), gates, enumValue(SendStage.class, n.get("native_first_failed_send_stage")));
                    StrictJson.require(terms.orElseThrow().completeCanSend() == (values.firstFailedStage() == SendStage.NONE), "actual CanSend and failed send stage disagree"); diagnostics = Optional.of(new Diagnostics(Optional.of(values)));
                }
            }
            Optional<Description> description = Optional.empty();
            if (hasDescription) {
                if (!selected) { nil(n, C88); description = Optional.of(new Description(Optional.empty())); }
                else {
                    DescriptionStatus status = enumValue(DescriptionStatus.class, n.get("native_c88_failure_description_status"));
                    Optional<String> text = nullableText(n.get("native_c88_failure_description_text"));
                    boolean failedC88 = diagnostics.flatMap(Diagnostics::values).map(value -> value.firstFailedStage() == SendStage.DEFINITION_C88).orElse(false);
                    StrictJson.require(failedC88 ? status == DescriptionStatus.OBSERVED && text.isPresent() || status == DescriptionStatus.UNAVAILABLE && text.isEmpty()
                            : status == DescriptionStatus.NOT_APPLICABLE && text.isEmpty(), "C88 source description belongs to another stage or has wrong availability");
                    description = Optional.of(new Description(Optional.of(new DescriptionValues(status, text))));
                }
            }
            result.add(new War(integer(n.get("war_id"), 0, 0xffff_ffffL), caller, recipient, callerSide, recipientSide,
                    nullableNonnegativeId(n.get("primary_attacker_character_id")), nullableNonnegativeId(n.get("primary_defender_character_id")), ids(n.get("attacker_character_ids")), ids(n.get("defender_character_ids")),
                    bool(n.get("caller_is_primary_war_leader")), bool(n.get("recipient_was_called")), canPick, rowSelectable,
                    hasSelectedAvailability ? Optional.of(selected) : Optional.empty(), terms, diagnostics, description));
        }
        return List.copyOf(result);
    }
    private static Allies allies(JsonNode node, Request request, long player) {
        ObjectNode n = object(node); Status status = enumValue(Status.class, n.get("status"));
        StrictJson.require(request.enumerateCurrentAllies() ? status == Status.AVAILABLE || status == Status.UNAVAILABLE : status == Status.NOT_REQUESTED, "current ally enumeration differs from request");
        Set<String> fields = keys("status reason played_character_id"); if (status == Status.AVAILABLE) fields.addAll(keys("source_character_ids unresolved_source_character_ids dead_source_character_ids allies")); StrictJson.object(n, fields);
        integer(n.get("played_character_id"), player, player); Optional<AlliesTerms> terms = Optional.empty();
        if (status == Status.AVAILABLE) {
            List<Ally> rows = new ArrayList<>();
            for (JsonNode row : array(n.get("allies"))) {
                StrictJson.object(row, keys("character_id player_has_ally ally_has_player has_realm_data")); long ally = id(row.get("character_id"));
                StrictJson.require(ally != player, "current native ally cannot be the played character"); yes(row.get("player_has_ally")); yes(row.get("ally_has_player")); rows.add(new Ally(ally, true, true, bool(row.get("has_realm_data"))));
            }
            terms = Optional.of(new AlliesTerms(ids(n.get("source_character_ids")), ids(n.get("unresolved_source_character_ids")), ids(n.get("dead_source_character_ids")), rows));
        }
        return new Allies(status, string(n.get("reason")), player, terms);
    }
    private static BetrothalBreak betrothal(JsonNode node, Request request) {
        ObjectNode n = object(node); BreakStatus status = enumValue(BreakStatus.class, n.get("status"));
        Set<String> fields = keys("status reason actor_character_id subject_character_id requested_recipient_character_id"); boolean available = status == BreakStatus.AVAILABLE || status == BreakStatus.NO_BETROTHAL;
        if (available) fields.addAll(keys("betrothed_character_id recipient_character_id secondary_actor_character_id secondary_recipient_character_id intermediary_character_id definition_ordinal definition_stable_hash final_legality_sampled complete_can_send native_send_costs_available native_send_costs_raw outcome_penalty_available outcome_penalty_unavailable_reason outcome_resource_penalty")); StrictJson.object(n, fields);
        OptionalLong subject = nullableId(n.get("subject_character_id")), recipient = nullableId(n.get("requested_recipient_character_id"));
        StrictJson.require(subject.equals(request.pair().map(pair -> OptionalLong.of(pair.subject())).orElseGet(OptionalLong::empty)) && recipient.equals(request.breakRecipient()), "betrothal terms belong to another subject/recipient");
        StrictJson.require((status == BreakStatus.NOT_REQUESTED) == request.breakRecipient().isEmpty(), "unrequested betrothal break was sampled");
        Optional<BreakValues> values = Optional.empty();
        if (available) {
            boolean sampled = bool(n.get("final_legality_sampled")), costsAvailable = bool(n.get("native_send_costs_available"));
            Optional<Boolean> canSend = nullableBool(n.get("complete_can_send")); StrictJson.require(sampled == canSend.isPresent(), "unsampled final legality must remain explicit null");
            Optional<Costs> costs = nullableCosts(n.get("native_send_costs_raw")); StrictJson.require(costsAvailable == costs.isPresent(), "unsampled send costs must remain explicit null");
            Penalty penalty = penalty(n.get("outcome_resource_penalty")); boolean penaltyAvailable = bool(n.get("outcome_penalty_available")); StrictJson.require(penaltyAvailable == penalty.available(), "break penalty availability changed");
            values = Optional.of(new BreakValues(nullableId(n.get("betrothed_character_id")), nullableId(n.get("recipient_character_id")), nullableId(n.get("secondary_actor_character_id")), nullableId(n.get("secondary_recipient_character_id")), nullableId(n.get("intermediary_character_id")),
                    nullableNonnegativeId(n.get("definition_ordinal")), integer(n.get("definition_stable_hash"), 0, 0xffff_ffffL), sampled, canSend, costsAvailable, costs, penaltyAvailable, string(n.get("outcome_penalty_unavailable_reason")), penalty));
        }
        return new BetrothalBreak(status, string(n.get("reason")), nullableId(n.get("actor_character_id")), subject, recipient, values);
    }
    private static Penalty penalty(JsonNode node) {
        ObjectNode n = object(node); boolean available = bool(n.get("resource_penalty_available")); Set<String> fields = keys("resource_penalty_available effects_complete source reason");
        if (available) fields.addAll(keys("proper_reason grand_wedding_promised ordinary_prestige_relevant native_yields_alliance_evaluated yields_alliance rejected_owner_character_id highest_rejected_tier stock_prestige_effect_raw stock_prestige_level_effect")); StrictJson.object(n, fields);
        Optional<PenaltyTerms> terms = available ? Optional.of(new PenaltyTerms(bool(n.get("proper_reason")), bool(n.get("grand_wedding_promised")), bool(n.get("ordinary_prestige_relevant")), bool(n.get("native_yields_alliance_evaluated")), bool(n.get("yields_alliance")), nullableId(n.get("rejected_owner_character_id")),
                (int) integer(n.get("highest_rejected_tier"), Integer.MIN_VALUE, Integer.MAX_VALUE), signed(n.get("stock_prestige_effect_raw")), (int) integer(n.get("stock_prestige_level_effect"), Integer.MIN_VALUE, Integer.MAX_VALUE))) : Optional.empty();
        return new Penalty(available, bool(n.get("effects_complete")), string(n.get("source")), string(n.get("reason")), terms);
    }
    private static OptionalLong optionalRequestId(ObjectNode n, String key) { return n.has(key) ? OptionalLong.of(id(n.get(key))) : OptionalLong.empty(); }
    private static OptionalLong nullableId(JsonNode n) { required(n); return n.isNull() ? OptionalLong.empty() : OptionalLong.of(id(n)); }
    private static OptionalLong nullableNonnegativeId(JsonNode n) { required(n); return n.isNull() ? OptionalLong.empty() : OptionalLong.of(integer(n, 0, 0xffff_ffffL)); }
    private static Optional<Boolean> nullableBool(JsonNode n) { required(n); return n.isNull() ? Optional.empty() : Optional.of(bool(n)); }
    private static Optional<String> nullableText(JsonNode n) { required(n); return n.isNull() ? Optional.empty() : Optional.of(string(n)); }
    private static Optional<Costs> nullableCosts(JsonNode n) { required(n); return n.isNull() ? Optional.empty() : Optional.of(costs(n)); }
    private static Costs costs(JsonNode n) { List<Long> values = new ArrayList<>(); for (JsonNode value : array(n)) values.add(signed(value)); return new Costs(values); }
    private static List<Long> ids(JsonNode n) { List<Long> values = new ArrayList<>(); for (JsonNode value : array(n)) values.add(integer(value, Integer.MIN_VALUE, 0xffff_ffffL)); return List.copyOf(values); }
    private static Answer answer(JsonNode n) { return Answer.values()[(int) integer(n, 0, 2)]; }
    private static long id(JsonNode n) { return integer(n, 1, 0xffff_ffffL); }
    private static long signed(JsonNode n) { return integer(n, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static BigInteger positive(JsonNode n) { return StrictJson.integer(n, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static long integer(JsonNode n, long low, long high) { return StrictJson.integer(n, low, high); }
    private static void exact(JsonNode n, BigInteger value) { StrictJson.integer(n, value, value); }
    private static void required(JsonNode n) { StrictJson.require(n != null, "required native field missing"); }
    private static boolean bool(JsonNode n) { StrictJson.require(n != null && n.isBoolean(), "actual JSON boolean required"); return n.booleanValue(); }
    private static void yes(JsonNode n) { StrictJson.trueValue(n); }
    private static void no(JsonNode n) { StrictJson.require(!bool(n), "actual JSON false required"); }
    private static String string(JsonNode n) { StrictJson.require(n != null && n.isTextual(), "source string required, including legitimate empty output"); String value = n.textValue(); FamilyObligations.reason(value); return value; }
    private static ObjectNode object(JsonNode n) { StrictJson.require(n != null && n.isObject(), "native object required"); return (ObjectNode) n; }
    private static JsonNode array(JsonNode n) { StrictJson.require(n != null && n.isArray(), "native array required"); return n; }
    private static Set<String> keys(String words) { return new HashSet<>(List.of(words.split(" "))); }
    private static boolean any(ObjectNode n, Set<String> fields) { return fields.stream().anyMatch(n::has); }
    private static void nil(ObjectNode n, Set<String> fields) { for (String field : fields) StrictJson.require(n.has(field) && n.get(field).isNull(), "explicit unobserved null required: " + field); }
    private static void equal(ObjectNode n, String field, String value) { StrictJson.require(value.equals(StrictJson.text(n.get(field))), "native family field differs: " + field); }
    private static <E extends Enum<E>> E enumValue(Class<E> type, JsonNode n) {
        String key = StrictJson.text(n); for (E value : type.getEnumConstants()) if (value.name().toLowerCase(Locale.ROOT).equals(key)) return value;
        throw new IllegalArgumentException("unknown authored " + type.getSimpleName() + ": " + key);
    }
}
