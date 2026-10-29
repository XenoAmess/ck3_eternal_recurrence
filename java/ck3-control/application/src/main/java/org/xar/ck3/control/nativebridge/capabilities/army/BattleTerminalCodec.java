package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Set;
import java.util.ArrayList;
import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.application.driver.DriverJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleResponses.*;

/** Terminal journal, strict object resolution and independently sampled successor state. No removal-to-win inference. */
public final class BattleTerminalCodec {
    private BattleTerminalCodec() { }
    public static Terminal terminal(byte[] raw, Context source, ArmyRequests.Terminal request) {
        return terminal(raw,source,request,new org.xar.ck3.control.application.action.OperationKey(ArmySteps.terminal(request)));
    }
    /** Original EXECUTE literal is explicit custody, validated against the same typed terminal request. */
    public static Terminal terminal(byte[] raw,Context source,ArmyRequests.Terminal request,
            org.xar.ck3.control.application.action.OperationKey originalLiteral) {
        ArmySteps.requireTerminalLiteral(originalLiteral,request);
        ObjectNode root=parse(raw);equal(get(root,"step"),originalLiteral.value());yes(get(root,"accepted"));Frame frame=BattleResponseCodec.frame(root,source);
        return terminalNode(object(get(root, "battle_terminal_transition")), source.nativeRevision(), source.dateRaw().longValueExact(), request, frame);
    }
    public static Obj normalizeTerminal(Obj input, int combat, int subject, Optional<BigInteger> cursor, List<Integer> characters, BigInteger nativeRevision, long dateRaw) {
        require(characters.stream().allMatch(character -> character > 0), "requested terminal CharacterID must be positive");
        ArmyRequests.Terminal request = new ArmyRequests.Terminal(combat == -1 ? Optional.empty() : Optional.of(new FullId(combat)), subject == -1 ? Optional.empty() : Optional.of(new PublicUnitId(subject)), cursor.map(UInt64::positive), characters.stream().map(FullId::new).toList());
        return terminalNode(parse(DriverJson.encode(input)), nativeRevision, dateRaw, request,
                new Frame(UInt64.positive(nativeRevision), dateRaw, new Missing<>())).originalFrame();
    }
    private static Terminal terminalNode(ObjectNode n, BigInteger nativeRevision, long dateRaw, ArmyRequests.Terminal request, Frame frame) {
        BattleResponseCodec.exactOptional(n, Set.of("schema_version", "contract_stage", "status", "unavailable_reason", "battle_terminal_transition_ready", "snapshot_revision", "observed_date_raw", "prior_combat_id", "subject_public_cunit_id", "terminal_journal", "prior", "removal", "subject", "successor"), Set.of("character_observations", "pending_death_queue"));
        require(i32(get(n, "schema_version")) == 1, "terminal version"); equal(get(n, "contract_stage"), "production_exact_battle_terminal_transition"); equal(get(n, "snapshot_revision"), nativeRevision); equal(get(n, "observed_date_raw"), BigInteger.valueOf(dateRaw)); i32(n.get("observed_date_raw"));
        require(i32(get(n, "prior_combat_id")) == request.priorCombat().map(FullId::value).orElse(-1) && i32(get(n, "subject_public_cunit_id")) == request.subject().map(PublicUnitId::value).orElse(-1), "terminal selected full IDs changed");
        Availability status = availability(get(n, "status")); require(status == Availability.AVAILABLE || status == Availability.UNAVAILABLE, "terminal availability"); boolean ready = bool(get(n, "battle_terminal_transition_ready")); require(ready == (status == Availability.AVAILABLE && request.priorCombat().isPresent()), "terminal readiness mismatch");
        List<Integer> observedCharacters = new ArrayList<>();
        if (n.has("character_observations")) {
            JsonNode observed = BattleTerminalPersonCodec.normalizeCustody(n.get("character_observations"), "character_observations", true); n.set("character_observations", observed);
            if (!observed.isNull()) for (JsonNode row : observed) observedCharacters.add(id(get(object(row), "character_id")).value());
        }
        require(observedCharacters.equals(request.characters().stream().map(FullId::value).toList()), "terminal character request order differs");
        if (n.has("pending_death_queue")) n.set("pending_death_queue", BattleTerminalPersonCodec.normalizePendingDeathQueue(n.get("pending_death_queue")));
        Journal journal = journal(get(n, "terminal_journal"), request); Field<TerminalState> state = new NullValue<>();
        if (status == Availability.UNAVAILABLE) {
            require(Set.of("unsupported_build", "requires_paused", "invalid_request", "journal_gap", "identity_unavailable", "state_changed", "bounds_exceeded").contains(text(n.get("unavailable_reason"))), "terminal unavailable reason invalid");
            for (String key : List.of("prior", "removal", "subject", "successor")) require(get(n, key).isNull(), "unavailable terminal invented native state");
            require(journal.eventSequence() instanceof NullValue<?>, "unavailable terminal invented event");
        } else if (request.priorCombat().isPresent()) {
            require(n.get("unavailable_reason").isNull(), "available terminal invented reason");
            Prior prior = prior(get(n, "prior"), request, journal); Removal removal = removal(get(n, "removal")); Subject subject = subject(get(n, "subject")); Successor successor = successor(get(n, "successor"), prior, subject);
            require(!prior.terminalKind().equals("active_not_terminal") || removal.combatResolves(), "active terminal must strictly resolve"); require(!prior.terminalKind().equals("unavailable_after_removal") || !removal.combatResolves(), "removed terminal unexpectedly resolves"); state = new Present<>(new TerminalState(prior, removal, subject, successor));
        } else {
            require(n.get("unavailable_reason").isNull() && !observedCharacters.isEmpty() && journal.requestedAfter() instanceof NullValue<?> && journal.eventSequence() instanceof NullValue<?> && journal.eventStatus().equals("not_observed"), "character-only terminal invented battle event");
            for (String key : List.of("prior", "removal", "subject", "successor")) require(n.get(key).isNull(), "character-only terminal invented battle context");
        }
        return new Terminal(frame, request.priorCombat().<Field<FullId>>map(Present::new).orElseGet(NullValue::new), request.subject().<Field<PublicUnitId>>map(Present::new).orElseGet(NullValue::new), status, ready, nullable(n, "unavailable_reason", ArmyJson::text), journal, state, List.of(), BattleResponseCodec.freeze(n));
    }
    private static Journal journal(JsonNode raw, ArmyRequests.Terminal request) {
        ObjectNode n = closed(raw, "requested_after_sequence", "oldest_available_sequence", "latest_sequence", "event_sequence", "event_status");
        Field<UInt64> requested = nullable(n, "requested_after_sequence", ArmyJson::positive), event = nullable(n, "event_sequence", ArmyJson::positive); UInt64 oldest = u64(n.get("oldest_available_sequence")), latest = u64(n.get("latest_sequence"));
        require(requested.equals(request.afterSequence().<Field<UInt64>>map(Present::new).orElseGet(NullValue::new)), "journal cursor changed"); require((oldest.value().signum() == 0) == (latest.value().signum() == 0) && oldest.value().compareTo(latest.value()) <= 0, "journal ring bounds disagree"); String status = text(n.get("event_status"));
        require(Set.of("observed", "not_observed").contains(status), "journal event status");
        if (event instanceof Present<UInt64> value) { require(status.equals("observed") && value.value().value().compareTo(oldest.value()) >= 0 && value.value().value().compareTo(latest.value()) <= 0, "event outside native ring"); request.afterSequence().ifPresent(after -> require(value.value().value().compareTo(after.value()) > 0, "event does not follow requested cursor")); }
        else require(status.equals("not_observed"), "observed event lacks sequence");
        return new Journal(requested, oldest, latest, event, status);
    }
    private static Prior prior(JsonNode raw, ArmyRequests.Terminal request, Journal journal) {
        ObjectNode n = BattleResponseCodec.exactOptional(raw, Set.of("combat_id", "terminal_kind", "terminal_date_raw", "suppress_normal_result_envelopes", "phase_raw", "phase_day", "winner_raw", "finalized_before", "daily_guard_raw", "province_id", "battle_result_id", "wipe_raw", "attacker_primary_participant_character_id", "defender_primary_participant_character_id", "attacker_public_cunit_ids_in_stored_order", "defender_public_cunit_ids_in_stored_order", "battle_warscore"), Set.of("hard_loss_inputs", "side_loss_inputs_in_native_order", "side_final_results_in_native_order", "character_result_rows_in_native_order", "character_custody_in_observed_order"));
        FullId combat = full(get(n, "combat_id")); require(request.priorCombat().orElseThrow().equals(combat), "prior full CombatID mismatch");
        String kind = nonempty(get(n, "terminal_kind")); require(Set.of("active_not_terminal", "normal_result", "no_normal_result", "unavailable_after_removal").contains(kind), "prior terminal kind invalid");
        Field<List<PublicUnitId>> attackers = nullable(n, "attacker_public_cunit_ids_in_stored_order", ArmyJson::units), defenders = nullable(n, "defender_public_cunit_ids_in_stored_order", ArmyJson::units);
        if (attackers instanceof Present<List<PublicUnitId>> a && defenders instanceof Present<List<PublicUnitId>> d) require(a.value().stream().noneMatch(d.value()::contains), "terminal prior sides overlap");
        if (!n.get("terminal_date_raw").isNull()) nonnegative(n.get("terminal_date_raw"));
        if (!n.get("phase_day").isNull()) nonnegative(n.get("phase_day"));
        if (!n.get("winner_raw").isNull()) { int winner = i32(n.get("winner_raw")); require(winner >= -1 && winner <= 1, "terminal winner invalid"); }
        if (!n.get("daily_guard_raw").isNull()) { int guard = i32(n.get("daily_guard_raw")); require(guard >= 0 && guard <= 255, "terminal daily guard invalid"); }
        WarScore score = warScore(get(n, "battle_warscore"));
        List<String> canonical = List.of("terminal_date_raw", "suppress_normal_result_envelopes", "phase_raw", "phase_day", "winner_raw", "finalized_before", "daily_guard_raw", "province_id", "attacker_primary_participant_character_id", "defender_primary_participant_character_id", "attacker_public_cunit_ids_in_stored_order", "defender_public_cunit_ids_in_stored_order");
        if (journal.eventStatus().equals("observed")) {
            require(kind.equals("normal_result") || kind.equals("no_normal_result"), "observed event is not terminal"); for (String key : canonical) require(!n.get(key).isNull(), "observed terminal omitted canonical state");
            require(bool(n.get("suppress_normal_result_envelopes")) == kind.equals("no_normal_result"), "terminal suppress flag differs from kind");
            require(!kind.equals("no_normal_result") || score.status().equals("not_recorded_by_native"), "no-normal result invented warscore");
        } else if (kind.equals("active_not_terminal")) {
            require(n.get("terminal_date_raw").isNull() && n.get("suppress_normal_result_envelopes").isNull(), "active combat invented terminal date/suppress");
            for (String key : canonical) if (!Set.of("terminal_date_raw", "suppress_normal_result_envelopes").contains(key)) require(!n.get(key).isNull(), "active combat omitted current canonical state");
            require(!bool(n.get("finalized_before")) && i32(n.get("daily_guard_raw")) == 0 && (!n.get("battle_result_id").isNull() || n.get("wipe_raw").isNull()) && score.status().equals("unavailable"), "active combat invented terminal result");
        } else {
            require(kind.equals("unavailable_after_removal") && score.status().equals("unavailable"), "unobserved removal invented terminal kind/warscore");
            for (String key : canonical) require(n.get(key).isNull(), "unobserved removal invented prior state");
            require(n.get("battle_result_id").isNull() && n.get("wipe_raw").isNull(), "unobserved removal invented result");
        }
        priorExtensions(n, kind);
        return new Prior(combat, kind, nullable(n, "terminal_date_raw", ArmyJson::i64), nullable(n, "suppress_normal_result_envelopes", ArmyJson::bool), nullable(n, "phase_raw", ArmyJson::i32), nullable(n, "phase_day", ArmyJson::i32), nullable(n, "winner_raw", ArmyJson::i32), nullable(n, "finalized_before", ArmyJson::bool), nullable(n, "daily_guard_raw", ArmyJson::i32), nullable(n, "province_id", ArmyJson::id), nullable(n, "battle_result_id", ArmyJson::full), nullable(n, "wipe_raw", ArmyJson::bool), nullable(n, "attacker_primary_participant_character_id", ArmyJson::id), nullable(n, "defender_primary_participant_character_id", ArmyJson::id), attackers, defenders, score, List.of());
    }
    private static Removal removal(JsonNode raw) {
        ObjectNode n = closed(raw, "prior_combat_strictly_resolves", "prior_province_strictly_resolves", "prior_province_contains_prior_combat_id", "result_strictly_resolves", "result_relevant_player_count");
        Removal value = new Removal(bool(n.get("prior_combat_strictly_resolves")), nullable(n, "prior_province_strictly_resolves", ArmyJson::bool), nullable(n, "prior_province_contains_prior_combat_id", ArmyJson::bool), nullable(n, "result_strictly_resolves", ArmyJson::bool), nullable(n, "result_relevant_player_count", ArmyJson::nonnegative));
        require(value.provinceResolves().equals(new Present<>(true)) || value.provinceContainsCombat() instanceof NullValue<?>, "unresolved province invented combat membership"); require(value.resultResolves().equals(new Present<>(true)) || value.resultRelevantPlayerCount() instanceof NullValue<?>, "unresolved result invented player count"); return value;
    }
    private static Subject subject(JsonNode raw) {
        ObjectNode n = closed(raw, "exists", "current_province_id", "native_carmy_id", "combat_backlink_id", "active_combat_id", "movement_or_retreat_state_raw", "move_target_province_id", "route_province_ids_in_stored_order", "ai_membership_status", "coordinator_id", "unit_stack_stored_index", "subunit_stored_index", "blocked_by_active_combat"); boolean exists = bool(n.get("exists")); String membership = text(n.get("ai_membership_status")); require(Set.of("none", "observed", "unavailable").contains(membership), "subject AI membership status");
        if (!exists) { for (String key : names(n)) if (!Set.of("exists", "ai_membership_status").contains(key)) require(n.get(key).isNull(), "absent subject invented native state"); require(membership.equals("none"), "absent subject has AI membership"); }
        Subject subject = new Subject(exists, nullable(n, "current_province_id", ArmyJson::id), nullable(n, "native_carmy_id", ArmyJson::id), nullable(n, "combat_backlink_id", ArmyJson::full), nullable(n, "active_combat_id", ArmyJson::full), nullable(n, "movement_or_retreat_state_raw", ArmyJson::i32), nullable(n, "move_target_province_id", ArmyJson::id), nullable(n, "route_province_ids_in_stored_order", row -> array(row, ArmyJson::id)), membership, nullable(n, "coordinator_id", ArmyJson::full), nullable(n, "unit_stack_stored_index", ArmyJson::nonnegative), nullable(n, "subunit_stored_index", ArmyJson::nonnegative), nullable(n, "blocked_by_active_combat", ArmyJson::bool));
        require(!subject.blockedByCombat().equals(new Present<>(true)) || subject.activeCombat() instanceof Present<?>, "active combat blocker lacks full CombatID");
        if (!n.get("coordinator_id").isNull()) id(n.get("coordinator_id"));
        require(membership.equals("observed") ? subject.coordinator() instanceof Present<?> && subject.stackIndex() instanceof Present<?> && subject.subunitIndex() instanceof Present<?> : subject.coordinator() instanceof NullValue<?> && subject.stackIndex() instanceof NullValue<?> && subject.subunitIndex() instanceof NullValue<?>, "AI membership identity/readiness mismatch"); return subject;
    }
    private static Successor successor(JsonNode raw, Prior prior, Subject subject) {
        ObjectNode n = closed(raw, "state", "matching_combat_ids_in_native_order", "selected_successor_combat_id", "participant_overlap_public_cunit_ids_in_prior_order"); String state = text(n.get("state")); List<FullId> matches = distinct(array(n.get("matching_combat_ids_in_native_order"), ArmyJson::full), 0, 65536, "successor combats"); Field<FullId> selected = nullable(n, "selected_successor_combat_id", ArmyJson::full); List<PublicUnitId> overlap = units(n.get("participant_overlap_public_cunit_ids_in_prior_order"));
        require(Set.of("residual_new_combat", "subject_missing", "subject_retreating", "subject_assignment_reopened", "no_successor", "unavailable").contains(state), "unknown successor state");
        if (prior.attackers() instanceof Present<List<PublicUnitId>> a && prior.defenders() instanceof Present<List<PublicUnitId>> d) {
            List<PublicUnitId> priorOrder = java.util.stream.Stream.concat(a.value().stream(), d.value().stream()).toList(); int last = -1;
            for (PublicUnitId id : overlap) { int index = priorOrder.indexOf(id); require(index > last, "successor overlap not in prior stored order"); last = index; }
        }
        if (selected instanceof Present<FullId> value) require(matches.contains(value.value()), "selected successor absent from matches");
        if (state.equals("residual_new_combat")) require(selected instanceof Present<?> && !matches.isEmpty() && !overlap.isEmpty() && subject.exists() && subject.activeCombat().equals(selected) && subject.blockedByCombat().equals(new Present<>(true)), "residual successor lacks exact native identity overlap");
        else require(selected instanceof NullValue<?> && overlap.isEmpty(), "nonresidual successor invented selected combat");
        int movement = subject.movementState() instanceof Present<Integer> value ? value.value() : 0;
        if (state.equals("subject_missing")) require(!subject.exists() && matches.isEmpty(), "subject missing mismatch");
        if (state.equals("subject_retreating")) require(subject.exists() && subject.activeCombat() instanceof NullValue<?> && subject.blockedByCombat().equals(new Present<>(false)) && movement > 0, "retreating successor lacks independent movement state");
        if (state.equals("subject_assignment_reopened")) require(subject.exists() && subject.activeCombat() instanceof NullValue<?> && subject.blockedByCombat().equals(new Present<>(false)) && movement <= 0 && subject.aiMembershipStatus().equals("observed") && matches.isEmpty(), "assignment reopened lacks observed AI membership");
        if (state.equals("no_successor")) require(subject.exists() && subject.aiMembershipStatus().equals("none") && subject.activeCombat() instanceof NullValue<?> && !subject.blockedByCombat().equals(new Present<>(true)) && movement <= 0 && matches.isEmpty(), "no-successor lacks complete negative evidence");
        return new Successor(state, matches, selected, overlap);
    }
    private static WarScore warScore(JsonNode raw) {
        ObjectNode n = BattleResponseCodec.exactOptional(raw, Set.of("status", "war_id", "war_battle_row_index", "value_raw_q100000", "winner_is_war_attacker", "combat_side0_is_war_attacker", "attacker_relative_delta_raw_q100000"), Set.of("denominator_inputs", "selected_cb_battle_scale_raw_q100000"));
        String status = text(n.get("status")); require(Set.of("recorded", "not_recorded_by_native", "unavailable").contains(status), "warscore status invalid");
        if (!status.equals("recorded")) {
            for (String key : names(n)) if (!key.equals("status")) require(n.get(key).isNull(), "nonrecorded warscore invented value");
        } else {
            id(n.get("war_id")); nonnegative(n.get("war_battle_row_index")); long value = i64(n.get("value_raw_q100000")); require(value >= 0, "battle warscore must be nonnegative");
            boolean winnerAttacker = bool(n.get("winner_is_war_attacker")); bool(n.get("combat_side0_is_war_attacker"));
            require(i64(n.get("attacker_relative_delta_raw_q100000")) == (winnerAttacker ? value : -value), "warscore attacker-relative sign differs");
            if (n.has("selected_cb_battle_scale_raw_q100000") && !n.get("selected_cb_battle_scale_raw_q100000").isNull()) require(i64(n.get("selected_cb_battle_scale_raw_q100000")) >= 0, "CB scale negative");
            if (n.has("denominator_inputs") && !n.get("denominator_inputs").isNull()) {
                ObjectNode denominator = closed(n.get("denominator_inputs"), "sum_int32", "after_minimum_int32", "participants");
                List<ObjectNode> participants = array(denominator.get("participants"), row -> closed(row, "character_id", "buckets_native_add_order_int32")); require(!participants.isEmpty() && participants.size() <= 32, "denominator participant count");
                int total = 0;
                for (ObjectNode participant : participants) {
                    id(participant.get("character_id")); List<Integer> buckets = array(participant.get("buckets_native_add_order_int32"), ArmyJson::nonnegative); require(buckets.size() == 8, "denominator eight native buckets required");
                    for (int bucket : buckets) total += bucket;
                }
                require(i32(denominator.get("sum_int32")) == total && i32(denominator.get("after_minimum_int32")) == Math.max(1, total), "native wrapping denominator arithmetic differs");
            }
        }
        return new WarScore(status, nullable(n, "war_id", ArmyJson::full), nullable(n, "war_battle_row_index", ArmyJson::nonnegative), nullable(n, "value_raw_q100000", ArmyJson::i64), nullable(n, "winner_is_war_attacker", ArmyJson::bool), nullable(n, "combat_side0_is_war_attacker", ArmyJson::bool), nullable(n, "attacker_relative_delta_raw_q100000", ArmyJson::i64));
    }
    private static void priorExtensions(ObjectNode prior, String kind) {
        if (prior.has("hard_loss_inputs") && !prior.get("hard_loss_inputs").isNull()) {
            ObjectNode n = closed(prior.get("hard_loss_inputs"), "losing_side_index", "baseline_raw", "stored_current_raw", "levy_soft_raw", "men_at_arms_soft_raw", "hard_loss_raw");
            int winner = i32(prior.get("winner_raw")), loser = i32(n.get("losing_side_index"));
            require(kind.equals("normal_result") && (winner == 0 || winner == 1) && loser == 1 - winner, "terminal hard-loss side differs");
            hardLoss(n, "baseline_raw", "stored_current_raw", "levy_soft_raw", "men_at_arms_soft_raw", "hard_loss_raw");
        }
        if (prior.has("side_loss_inputs_in_native_order") && !prior.get("side_loss_inputs_in_native_order").isNull()) {
            List<ObjectNode> rows = array(prior.get("side_loss_inputs_in_native_order"), row -> closed(row, "side_index", "baseline_raw_q100000", "stored_current_fighting_raw_q100000", "levy_soft_raw_q100000", "men_at_arms_soft_raw_q100000", "hard_loss_raw_q100000"));
            require(kind.equals("normal_result") && rows.size() == 2, "side-loss rows require two normal-result sides");
            for (int i = 0; i < rows.size(); i++) { ObjectNode row = rows.get(i); require(i32(row.get("side_index")) == i, "side-loss native order differs"); hardLoss(row, "baseline_raw_q100000", "stored_current_fighting_raw_q100000", "levy_soft_raw_q100000", "men_at_arms_soft_raw_q100000", "hard_loss_raw_q100000"); }
        }
        if (prior.has("side_final_results_in_native_order") && !prior.get("side_final_results_in_native_order").isNull()) {
            List<ObjectNode> rows = array(prior.get("side_final_results_in_native_order"), row -> closed(row, "side_index", "selected_commander_character_id", "baseline_raw_q100000", "survivors_raw_q100000"));
            require(kind.equals("normal_result") && rows.size() == 2, "final-side rows require two normal-result sides");
            for (int i = 0; i < rows.size(); i++) { ObjectNode row = rows.get(i); require(i32(row.get("side_index")) == i && i32(row.get("selected_commander_character_id")) >= -1 && i64(row.get("baseline_raw_q100000")) >= 0 && i64(row.get("survivors_raw_q100000")) >= 0, "final-side native order/quantities differ"); }
        }
        if (prior.has("character_result_rows_in_native_order") && !prior.get("character_result_rows_in_native_order").isNull()) {
            require(kind.equals("normal_result"), "character results require normal result"); List<ObjectNode> rows = array(prior.get("character_result_rows_in_native_order"), row -> closed(row, "native_row_index", "left_character_id", "right_character_id", "key", "type_raw", "side0", "target_right"));
            for (int i = 0; i < rows.size(); i++) { ObjectNode row = rows.get(i); require(i32(row.get("native_row_index")) == i && i32(row.get("left_character_id")) >= -1 && i32(row.get("right_character_id")) >= -1, "character result native order/IDs differ"); if (!row.get("key").isNull()) text(row.get("key")); i32(row.get("type_raw")); bool(row.get("side0")); bool(row.get("target_right")); }
        }
        if (prior.has("character_custody_in_observed_order")) {
            require(prior.get("character_custody_in_observed_order").isNull() || kind.equals("normal_result"), "custody requires normal result");
            prior.set("character_custody_in_observed_order", BattleTerminalPersonCodec.normalizeCustody(prior.get("character_custody_in_observed_order"), "terminal character custody", false));
        }
    }
    private static void hardLoss(ObjectNode n, String baseline, String current, String levySoft, String maaSoft, String hard) {
        for (String key : List.of(baseline, current, levySoft, maaSoft, hard)) require(i64(n.get(key)) >= 0, "terminal loss operands must be nonnegative");
        BigInteger expected = BigInteger.valueOf(i64(n.get(baseline))).subtract(BigInteger.valueOf(i64(n.get(current)))).subtract(BigInteger.valueOf(i64(n.get(levySoft)))).subtract(BigInteger.valueOf(i64(n.get(maaSoft)))).max(BigInteger.ZERO);
        require(expected.equals(BigInteger.valueOf(i64(n.get(hard)))), "terminal hard-loss formula differs");
    }
}
