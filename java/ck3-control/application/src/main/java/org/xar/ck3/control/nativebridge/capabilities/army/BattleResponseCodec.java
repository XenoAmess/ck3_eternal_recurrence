package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import java.util.ArrayList;
import java.util.HashSet;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleResponses.*;

/** Raw native result -> exact identity-bound battle values. This decoder does not run a simulator or grant action permission. */
public final class BattleResponseCodec {
    private BattleResponseCodec() { }
    static ObjectNode result(PlanningReadReceipt receipt) {
        require(receipt.original().nativeOk(), "native rejected this exact read");
        return parse(receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("successful native read lacks its original result token")).bytes());
    }
    static Frame frame(ObjectNode result, Context source) {
        equal(get(result, "snapshot_revision"), source.nativeRevision());
        if (result.has("date_raw")) equal(result.get("date_raw"), source.dateRaw());
        return new Frame(positive(get(result, "snapshot_revision")), source.dateRaw().longValueExact(), new Present<>(positive(get(result, "query_sequence"))));
    }
    public static Control control(byte[] raw, Context source, ArmyRequests.Unit request) {
        ObjectNode root = parse(raw); equal(get(root, "step"), "query-battle-control-snapshot-v1-" + request.unit().value()); yes(get(root, "accepted"));
        return controlNode(object(get(root, "battle_control_snapshot")), source, request, frame(root, source));
    }
    /** Native semantic snapshots already contain the frame, without a query ACK or query sequence. */
    public static Control controlFrame(byte[] rawFrame, Context source, ArmyRequests.Unit request) {
        return controlNode(parse(rawFrame), source, request, new Frame(UInt64.positive(source.nativeRevision()), source.dateRaw().longValueExact(), new Missing<>()));
    }
    /** Shared history/direct-frame boundary, with independent public and native revisions. */
    public static Obj normalizeControl(Obj input, int subject, BigInteger nativeRevision, long dateRaw) {
        ObjectNode node = parse(DriverJson.encode(input));
        Control result = controlNode(node, nativeRevision, dateRaw, new ArmyRequests.Unit(new PublicUnitId(subject)),
                new Frame(UInt64.positive(nativeRevision), dateRaw, new Missing<>()));
        return result.originalFrame();
    }
    private static Control controlNode(ObjectNode n, Context source, ArmyRequests.Unit request, Frame frame) {
        return controlNode(n, source.nativeRevision(), source.dateRaw().longValueExact(), request, frame);
    }
    private static Control controlNode(ObjectNode n, BigInteger nativeRevision, long dateRaw, ArmyRequests.Unit request, Frame frame) {
        required(n, "schema_version", "contract_stage", "status", "battle_control_ready", "snapshot_revision", "observed_date_raw", "subject_public_cunit_id", "subject_native_carmy_id", "combat_id", "province_id", "selected_public_cunit_id", "selected_native_carmy_id", "selected_owner_character_id", "combat_province_id", "side_index", "side_scope", "affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order", "side_flags", "legality", "phase", "phase_raw", "phase_day", "winner_side", "winner_raw", "forced_winner_side", "forced_winner_raw", "finalized", "battle_result_id", "base_combat_width", "final_combat_width", "roll_cadence_counter", "base_advantage_raw", "resolved_advantage_raw", "attacker", "defender");
        require(i32(n.get("schema_version")) == 1, "battle schema version"); equal(n.get("contract_stage"), "production_exact_ongoing_combat"); equal(n.get("status"), "available"); yes(n.get("battle_control_ready"));
        equal(n.get("snapshot_revision"), nativeRevision); equal(n.get("observed_date_raw"), BigInteger.valueOf(dateRaw));
        PublicUnitId subject = unit(n.get("subject_public_cunit_id")); require(subject.equals(request.unit()), "battle subject mismatch"); FullId combat = full(n.get("combat_id"));
        Side side = side(n.get("side_index")); Scope scope = scope(n.get("side_scope")); Phase phase = phase(n.get("phase_raw"), n.get("phase"));
        CombatSide attacker = combatSide(n.get("attacker"), Side.ATTACKER, combat), defender = combatSide(n.get("defender"), Side.DEFENDER, combat);
        List<PublicUnitId> attackerIds = attacker.orderedArmies().stream().map(Army::publicId).toList(), defenderIds = defender.orderedArmies().stream().map(Army::publicId).toList();
        require(attackerIds.stream().noneMatch(defenderIds::contains), "opposing public CUnit identities overlap");
        require(attacker.orderedArmies().stream().map(Army::nativeArmy).noneMatch(value -> defender.orderedArmies().stream().anyMatch(row -> row.nativeArmy().equals(value))), "opposing native CArmy identities overlap");
        require(attackerIds.contains(subject) != defenderIds.contains(subject), "subject must appear in exactly one combat side");
        require((side == Side.ATTACKER ? attackerIds : defenderIds).contains(subject), "subject side mapping mismatch");
        List<PublicUnitId> affected = units(n.get("affected_public_cunit_ids_in_stored_order")), unaffected = units(n.get("unaffected_same_side_public_cunit_ids_in_stored_order"));
        require(affected.contains(subject) && affected.stream().noneMatch(unaffected::contains), "retreat affected scope overlaps or omits selected subject");
        List<PublicUnitId> sameSide = side == Side.ATTACKER ? attackerIds : defenderIds;
        require(affected.size() + unaffected.size() == sameSide.size() && sameSide.containsAll(affected) && sameSide.containsAll(unaffected), "retreat scope is not a partition of the actual side");
        if (scope == Scope.FULL_SIDE) require(affected.equals(sameSide) && unaffected.isEmpty(), "full-side retreat scope mismatch");
        ObjectNode flags = closed(n.get("side_flags"), "disallow_retreat", "allow_early_retreat", "skip_pursuit");
        SideFlags sideFlags = new SideFlags(bool(flags.get("disallow_retreat")), bool(flags.get("allow_early_retreat")), bool(flags.get("skip_pursuit")));
        RetreatLegality legality = legality(n.get("legality"), phase, dateRaw, sideFlags);
        PublicUnitId selected = unit(n.get("selected_public_cunit_id")); PositiveId selectedNative = id(n.get("selected_native_carmy_id")), selectedOwner = id(n.get("selected_owner_character_id"));
        Army selectedArmy = (side == Side.ATTACKER ? attacker : defender).orderedArmies().stream().filter(a -> a.publicId().equals(selected)).findFirst().orElseThrow(() -> new IllegalArgumentException("selected retreat army absent from actual side"));
        require(selected.equals(subject) && selectedArmy.nativeArmy().equals(selectedNative) && selectedArmy.owner().equals(selectedOwner) && id(n.get("subject_native_carmy_id")).equals(selectedNative), "selected public/native/owner identity differs from actual combat row");
        List<Army> ownArmies = (side == Side.ATTACKER ? attacker : defender).orderedArmies();
        List<PublicUnitId> expectedAffected = ownArmies.stream().filter(army -> army.owner().equals(selectedOwner)).map(Army::publicId).toList();
        List<PublicUnitId> expectedUnaffected = ownArmies.stream().filter(army -> !army.owner().equals(selectedOwner)).map(Army::publicId).toList();
        require(affected.equals(expectedAffected) && unaffected.equals(expectedUnaffected)
                && scope == (expectedUnaffected.isEmpty() ? Scope.FULL_SIDE : Scope.OWNER_SUBSET), "retreat owner subset/stored order differs");
        require(id(n.get("province_id")).equals(id(n.get("combat_province_id"))), "actual combat Province differs");
        Set<String> core = Set.of("schema_version", "contract_stage", "status", "battle_control_ready", "snapshot_revision", "observed_date_raw", "subject_public_cunit_id", "subject_native_carmy_id", "combat_id", "province_id", "selected_public_cunit_id", "selected_native_carmy_id", "selected_owner_character_id", "combat_province_id", "side_index", "side_scope", "affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order", "side_flags", "legality", "phase", "phase_raw", "phase_day", "winner_side", "winner_raw", "forced_winner_side", "forced_winner_raw", "finalized", "battle_result_id", "base_combat_width", "final_combat_width", "roll_cadence_counter", "base_advantage_raw", "resolved_advantage_raw", "attacker", "defender");
        require(names(n).stream().allMatch(key -> core.contains(key) || BattleControlExtensionCodec.OPTIONAL_FIELDS.contains(key)), "invented battle control field");
        n = BattleControlExtensionCodec.normalize(n);
        return new Control(frame, subject, id(n.get("subject_native_carmy_id")), combat, id(n.get("province_id")), selected, selectedNative, selectedOwner, id(n.get("combat_province_id")), side, scope, affected, unaffected, sideFlags, legality, phase, i32(n.get("phase_day")), winner(n.get("winner_raw"), n.get("winner_side")), winner(n.get("forced_winner_raw"), n.get("forced_winner_side")), bool(n.get("finalized")), nullable(n, "battle_result_id", ArmyJson::full), i32(n.get("base_combat_width")), i32(n.get("final_combat_width")), i32(n.get("roll_cadence_counter")), i64(n.get("base_advantage_raw")), i64(n.get("resolved_advantage_raw")), attacker, defender, List.of(), freeze(n));
    }
    private static RetreatLegality legality(JsonNode raw, Phase phase, long date, SideFlags flags) {
        ObjectNode n = closed(raw, "status", "native_boolean", "phase_raw", "phase", "retreat_elapsed_baseline_date_raw", "elapsed_whole_days", "minimum_elapsed_whole_days_exclusive", "landless_gate_allows_retreat", "legal_now", "reason_codes_in_native_order", "native_reason_keys_in_native_order", "earliest_day_gate_date_raw");
        Availability status = availability(n.get("status")); require(phase(n.get("phase_raw"), n.get("phase")) == phase, "retreat phase differs from combat");
        require(status == Availability.AVAILABLE, "current native retreat legality unavailable");
        boolean nativeBoolean = bool(n.get("native_boolean")), legal = bool(n.get("legal_now")), landless = bool(n.get("landless_gate_allows_retreat"));
        long baseline = i32(n.get("retreat_elapsed_baseline_date_raw")), elapsed = i64(n.get("elapsed_whole_days")); int minimum = i32(n.get("minimum_elapsed_whole_days_exclusive"));
        long baselineDay = (baseline - 0x029C55C0L) / 24, actualDay = Math.subtractExact(date, 0x029C55C0L) / 24;
        require(elapsed == Math.subtractExact(actualDay, baselineDay), "retreat elapsed native day indices differ");
        List<String> reasons = new ArrayList<>(), keys = new ArrayList<>();
        if (flags.disallowRetreat()) { reasons.add("disallowed"); keys.add("COMBAT_NO_RETREAT_DISALLOWED"); }
        if (!flags.allowEarlyRetreat() && elapsed <= minimum) { reasons.add("too_early"); keys.add("COMBAT_NO_RETREAT_TOO_EARLY"); }
        if (phase == Phase.PURSUIT || phase == Phase.DONE) { reasons.add("pursuit_or_done"); keys.add("COMBAT_NO_RETREAT_PURSUIT"); }
        if (!landless) { reasons.add("landless"); keys.add("COMBAT_NO_RETREAT_LANDLESS"); }
        require(reasons.equals(array(n.get("reason_codes_in_native_order"), ArmyJson::text)) && keys.equals(array(n.get("native_reason_keys_in_native_order"), ArmyJson::text))
                && nativeBoolean == reasons.isEmpty() && legal == reasons.isEmpty(), "native retreat gate values/order differ");
        long earliest = i64(n.get("earliest_day_gate_date_raw"));
        require(earliest == Math.addExact(0x029C55C0L, Math.multiplyExact(Math.addExact(Math.addExact(baselineDay, minimum), 1), 24)), "retreat earliest day gate differs");
        return new RetreatLegality(status, new Present<>(nativeBoolean), i32(n.get("phase_raw")), phase, new Present<>(baseline), new Present<>(elapsed), new Present<>(minimum), new Present<>(landless), legal, reasons, keys, new Present<>(earliest));
    }
    private static CombatSide combatSide(JsonNode raw, Side expected, FullId combat) {
        ObjectNode n = exactOptional(raw, Set.of("side_index", "role", "primary_participant_character_id", "selected_commander_character_id", "current_roll_points", "ordered_armies", "levy_entries", "men_at_arms_entries", "stored_current_fighting_raw", "stored_levy_current_fighting_raw", "stored_current_matches_derived", "stored_levy_current_matches_derived", "derived_current_fighting_raw", "derived_soft_casualties_raw", "derived_main_fighting_entry_hard_casualties_raw", "non_main_start_minus_current_minus_soft_raw", "participant_hard_ledger", "participant_hard_total_raw", "side_strength_raw", "side_strength_scale"), Set.of("stored_terminal_loss_baseline_raw"));
        require(side(get(n, "side_index")) == expected, "combat side index mismatch"); equal(get(n, "role"), expected == Side.ATTACKER ? "attacker" : "defender");
        List<Army> armies = array(get(n, "ordered_armies"), row -> { ObjectNode a = closed(row, "native_carmy_id", "public_cunit_id", "owner_character_id", "combat_backlink_id"); Army value = new Army(unit(a.get("public_cunit_id")), id(a.get("native_carmy_id")), id(a.get("owner_character_id")), full(a.get("combat_backlink_id"))); require(value.combatBacklink().equals(combat), "army backlink does not bind full CombatID"); return value; });
        require(!armies.isEmpty() && armies.stream().map(Army::publicId).distinct().count() == armies.size() && armies.stream().map(Army::nativeArmy).distinct().count() == armies.size(), "combat armies missing or duplicated");
        List<Entry> levies = array(get(n, "levy_entries"), BattleResponseCodec::entry), maa = array(get(n, "men_at_arms_entries"), BattleResponseCodec::entry);
        for (int i = 0; i < levies.size(); i++) require(levies.get(i).bucket().equals("levy") && levies.get(i).bucketIndex() == i, "levy bucket order differs");
        for (int i = 0; i < maa.size(); i++) require(maa.get(i).bucket().equals("men_at_arms") && maa.get(i).bucketIndex() == i, "MAA bucket order differs");
        List<Entry> entries = java.util.stream.Stream.concat(levies.stream(), maa.stream()).toList();
        require(entries.stream().map(Entry::regiment).distinct().count() == entries.size(), "duplicate retained RegimentID");
        for (Entry entry : java.util.stream.Stream.concat(levies.stream(), maa.stream()).toList()) require(armies.stream().anyMatch(a -> a.publicId().equals(entry.publicId()) && a.nativeArmy().equals(entry.nativeArmy()) && a.owner().equals(entry.owner())), "entry/army generation mapping mismatch");
        List<HardLedger> ledger = array(get(n, "participant_hard_ledger"), row -> { ObjectNode a = exactOptional(row, Set.of("row_index", "participant_character_id", "hard_casualties_raw"), Set.of("resource_share_weight_signed32")); if(a.has("resource_share_weight_signed32") && !a.get("resource_share_weight_signed32").isNull()) i32(a.get("resource_share_weight_signed32")); return new HardLedger(nonnegative(a.get("row_index")), id(a.get("participant_character_id")), i64(a.get("hard_casualties_raw"))); });
        for (int i = 0; i < ledger.size(); i++) require(ledger.get(i).rowIndex() == i, "participant hard ledger order differs");
        long derivedCurrent = i64(get(n, "derived_current_fighting_raw")), derivedSoft = i64(get(n, "derived_soft_casualties_raw")), hardTotal = i64(get(n, "participant_hard_total_raw"));
        require(java.util.stream.Stream.concat(levies.stream(), maa.stream()).mapToLong(Entry::currentFightingRaw).reduce(0, Math::addExact) == derivedCurrent, "battle derived current total differs from entries");
        require(java.util.stream.Stream.concat(levies.stream(), maa.stream()).mapToLong(Entry::softCasualtiesRaw).reduce(0, Math::addExact) == derivedSoft, "battle derived soft total differs from entries");
        require(ledger.stream().mapToLong(HardLedger::hardCasualtiesRaw).reduce(0, Math::addExact) == hardTotal, "battle participant hard ledger total mismatch");
        long levyCurrent = levies.stream().mapToLong(Entry::currentFightingRaw).reduce(0, Math::addExact);
        long mainHard = 0, nonMain = 0;
        for (Entry entry : entries) if (entry.hardRaw() instanceof Present<Long> hard) mainHard = Math.addExact(mainHard, hard.value());
            else nonMain = Math.addExact(nonMain, Math.subtractExact(Math.subtractExact(entry.startingRaw(), entry.currentFightingRaw()), entry.softCasualtiesRaw()));
        require(bool(n.get("stored_current_matches_derived")) == (i64(n.get("stored_current_fighting_raw")) == derivedCurrent)
                && bool(n.get("stored_levy_current_matches_derived")) == (i64(n.get("stored_levy_current_fighting_raw")) == levyCurrent)
                && i64(n.get("derived_main_fighting_entry_hard_casualties_raw")) == mainHard
                && i64(n.get("non_main_start_minus_current_minus_soft_raw")) == nonMain && i32(n.get("side_strength_scale")) == 100000, "battle retained ledger/cache flags differ");
        if (n.has("stored_terminal_loss_baseline_raw")) i64(n.get("stored_terminal_loss_baseline_raw"));
        return new CombatSide(expected, id(get(n, "primary_participant_character_id")), nullable(n, "selected_commander_character_id", ArmyJson::id), i32(get(n, "current_roll_points")), armies, levies, maa, i64(get(n, "stored_current_fighting_raw")), i64(get(n, "stored_levy_current_fighting_raw")), bool(get(n, "stored_current_matches_derived")), bool(get(n, "stored_levy_current_matches_derived")), derivedCurrent, derivedSoft, i64(get(n, "derived_main_fighting_entry_hard_casualties_raw")), i64(get(n, "non_main_start_minus_current_minus_soft_raw")), ledger, hardTotal, i32(get(n, "side_strength_raw")), 100000, field(n, "stored_terminal_loss_baseline_raw", ArmyJson::i64));
    }
    private static Entry entry(JsonNode raw) {
        ObjectNode n = exactOptional(raw, Set.of("bucket", "bucket_index", "regiment_id", "native_carmy_id", "public_cunit_id", "owner_character_id", "starting_raw", "current_fighting_raw", "soft_casualties_raw", "fights_in_main_phase", "hard_casualties_status", "hard_casualties_raw", "hard_casualties_source", "hard_casualties_unavailable_reason", "effective_max_size", "effective_siege_raw", "effective_damage_raw", "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw", "entry_strength_raw"), Set.of("physical_entry_identity", "knight_character_id_raw", "accolade_source")); boolean fights = bool(get(n, "fights_in_main_phase"));
        if (n.has("knight_character_id_raw") || n.has("accolade_source")) equal(n.get("bucket"), "men_at_arms");
        if (n.has("knight_character_id_raw")) i32(n.get("knight_character_id_raw"));
        if (n.has("physical_entry_identity")) require(!n.get("physical_entry_identity").isNull(), "present physical identity cannot be null");
        if (n.has("accolade_source")) require(!n.get("accolade_source").isNull(), "present accolade source cannot be null");
        long starting = i64(get(n, "starting_raw")), current = i64(get(n, "current_fighting_raw")), soft = i64(get(n, "soft_casualties_raw"));
        long difference = Math.subtractExact(Math.subtractExact(starting, current), soft);
        Field<Long> hard = nullable(n, "hard_casualties_raw", ArmyJson::i64); Field<String> source = nullable(n, "hard_casualties_source", ArmyJson::text), reason = nullable(n, "hard_casualties_unavailable_reason", ArmyJson::text);
        String hardStatus = text(get(n, "hard_casualties_status"));
        if (fights) require(hardStatus.equals("available") && hard.equals(new Present<>(difference)) && source.equals(new Present<>("derived_starting_minus_current_minus_soft")) && reason instanceof NullValue<?>, "main entry hard casualty derivation mismatch");
        else require(hardStatus.equals("unavailable") && hard instanceof NullValue<?> && source instanceof NullValue<?> && reason.equals(new Present<>("non_main_reserve_not_distinguishable_from_hard")), "nonmain reserve cannot establish hard casualties");
        Field<UInt64> physical = field(n, "physical_entry_identity", value -> {
            if (value.isTextual()) { String token = text(value); require(token.matches("0x[0-9a-fA-F]+"), "physical identity must retain the original native uint64 hex token"); return UInt64.positive(new BigInteger(token.substring(2), 16)); }
            return positive(value);
        });
        Field<Integer> knight = field(n, "knight_character_id_raw", ArmyJson::i32);
        Field<AccoladeSource> accolade = field(n, "accolade_source", value -> {
            ObjectNode a = closed(value, "link_status", "accolade_id_raw", "rows_status", "rows", "source_gate_status"); require(knight instanceof Present<?>, "accolade source lacks observed knight slot");
            int knightId = ((Present<Integer>) knight).value(); String link = text(a.get("link_status")); Field<Integer> accoladeId = nullable(a, "accolade_id_raw", ArmyJson::i32);
            require((knightId == -1) == link.equals("not_applicable_empty_knight_slot"), "empty knight slot accolade source mismatch");
            require(link.equals("observed") ? knightId != -1 && accoladeId instanceof Present<?> : Set.of("not_applicable_empty_knight_slot", "unavailable_character_generation", "unavailable_link_changed").contains(link) && accoladeId instanceof NullValue<?>, "accolade link status/value mismatch");
            String expected = knightId == -1 ? "not_applicable_empty_knight_slot" : link.equals("observed") && accoladeId.equals(new Present<>(-1)) ? "not_applicable_no_accolade" : "unknown_not_observed";
            equal(a.get("rows_status"), expected); require(a.get("rows").isNull(), "accolade rows are not observed"); equal(a.get("source_gate_status"), expected.equals("unknown_not_observed") ? "unknown_original_call_not_observed" : expected);
            return new AccoladeSource(link, accoladeId, expected, text(a.get("source_gate_status")));
        });
        return new Entry(nonempty(get(n, "bucket")), nonnegative(get(n, "bucket_index")), full(get(n, "regiment_id")), id(get(n, "native_carmy_id")), unit(get(n, "public_cunit_id")), id(get(n, "owner_character_id")), starting, current, soft, fights, hardStatus, hard, source, reason, i32(get(n, "effective_max_size")), i64(get(n, "effective_siege_raw")), i64(get(n, "effective_damage_raw")), i64(get(n, "effective_toughness_raw")), i64(get(n, "effective_pursuit_raw")), i64(get(n, "effective_screen_raw")), i32(get(n, "entry_strength_raw")), physical, knight, accolade);
    }
    public static Transition transition(byte[] raw, Context source, ArmyRequests.Combat request) {
        ObjectNode root = parse(raw); equal(get(root, "step"), "query-battle-transition-v1-" + request.combat().value()); yes(get(root, "accepted")); Frame frame = frame(root, source);
        return transitionNode(object(get(root, "battle_transition_snapshot")), source.nativeRevision(), source.dateRaw().longValueExact(), request, frame);
    }
    public static Obj normalizeTransition(Obj input, int combat, BigInteger nativeRevision, long dateRaw) {
        return transitionNode(parse(DriverJson.encode(input)), nativeRevision, dateRaw,
                new ArmyRequests.Combat(new FullId(combat)), new Frame(UInt64.positive(nativeRevision), dateRaw, new Missing<>())).originalFrame();
    }
    private static Transition transitionNode(ObjectNode n, BigInteger nativeRevision, long dateRaw, ArmyRequests.Combat request, Frame frame) {
        exactOptional(n, Set.of("schema_version", "contract_stage", "status", "battle_transition_ready", "snapshot_revision", "observed_date_raw", "combat_id", "province_id", "phase", "phase_raw", "phase_day", "winner_side", "winner_raw", "forced_winner_side", "forced_winner_raw", "finalized", "battle_result_id", "attacker_public_cunit_ids_in_stored_order", "defender_public_cunit_ids_in_stored_order"), Set.of("current_observation", "native_owner_recall_inputs_v1", "actual_geography_v1"));
        require(i32(get(n, "schema_version")) == 1, "transition schema version"); equal(get(n, "contract_stage"), "production_exact_combat_lifecycle"); equal(get(n, "snapshot_revision"), nativeRevision); equal(get(n, "observed_date_raw"), BigInteger.valueOf(dateRaw)); require(full(get(n, "combat_id")).equals(request.combat()), "transition CombatID changed");
        TransitionStatus status = switch (text(get(n, "status"))) { case "available" -> TransitionStatus.AVAILABLE; case "combat_not_found" -> TransitionStatus.COMBAT_NOT_FOUND; case "state_changed" -> TransitionStatus.STATE_CHANGED; case "unavailable" -> TransitionStatus.UNAVAILABLE; default -> throw new IllegalArgumentException("unknown transition status"); };
        boolean ready = bool(get(n, "battle_transition_ready")); require(ready == (status == TransitionStatus.AVAILABLE || status == TransitionStatus.COMBAT_NOT_FOUND), "transition readiness mismatch");
        List<PublicUnitId> attackers = units(get(n, "attacker_public_cunit_ids_in_stored_order")), defenders = units(get(n, "defender_public_cunit_ids_in_stored_order")); require(attackers.stream().noneMatch(defenders::contains), "transition sides overlap");
        Field<Lifecycle> lifecycle;
        if (status == TransitionStatus.AVAILABLE) lifecycle = new Present<>(new Lifecycle(id(get(n, "province_id")), phase(get(n, "phase_raw"), get(n, "phase")), nonnegative(get(n, "phase_day")), winner(get(n, "winner_raw"), get(n, "winner_side")), winner(get(n, "forced_winner_raw"), get(n, "forced_winner_side")), bool(get(n, "finalized")), nullable(n, "battle_result_id", ArmyJson::full)));
        else { for (String key : List.of("province_id", "phase", "phase_raw", "phase_day", "winner_side", "winner_raw", "forced_winner_side", "forced_winner_raw", "finalized", "battle_result_id")) require(get(n, key).isNull(), "nonavailable transition invented lifecycle state"); require(attackers.isEmpty() && defenders.isEmpty(), "nonavailable transition invented side state"); lifecycle = new NullValue<>(); }
        if (n.has("current_observation") && !n.get("current_observation").isNull()) require(status == TransitionStatus.AVAILABLE, "current observations require available lifecycle");
        if (n.has("actual_geography_v1")) {
            JsonNode geography = BattleControlExtensionCodec.normalizeGeography(n.get("actual_geography_v1"), "battle_transition_snapshot.actual_geography_v1");
            require(status == TransitionStatus.AVAILABLE || geography.isNull(), "unavailable lifecycle invented actual geography"); n.set("actual_geography_v1", geography);
        }
        if (n.has("native_owner_recall_inputs_v1")) n.set("native_owner_recall_inputs_v1", BattleOwnerRecallCodec.normalize(n.get("native_owner_recall_inputs_v1"), status == TransitionStatus.AVAILABLE));
        return new Transition(frame, request.combat(), status, ready, lifecycle, attackers, defenders, field(n, "current_observation", BattleResponseCodec::currentObservation), List.of(), freeze(n));
    }
    private static CurrentObservation currentObservation(JsonNode raw) {
        ObjectNode n = closed(raw, "status", "unavailable_reason", "scale", "base_combat_width", "final_combat_width", "base_advantage_raw", "resolved_advantage_raw", "attacker", "defender");
        Availability status = availability(n.get("status")); require(status == Availability.AVAILABLE || status == Availability.UNAVAILABLE, "current observation status invalid");
        require(i64(n.get("scale")) == 100000, "current observation scale differs");
        if (status == Availability.AVAILABLE) {
            require(n.get("unavailable_reason").isNull(), "available current observation has reason");
            nonnegative(n.get("base_combat_width")); nonnegative(n.get("final_combat_width")); i64(n.get("base_advantage_raw")); i64(n.get("resolved_advantage_raw")); object(n.get("attacker")); object(n.get("defender"));
        } else {
            nonempty(n.get("unavailable_reason"));
            for (String key : List.of("base_combat_width", "final_combat_width", "base_advantage_raw", "resolved_advantage_raw", "attacker", "defender")) require(n.get(key).isNull(), "unavailable current observation invented value");
        }
        return new CurrentObservation(availability(n.get("status")), nullable(n, "unavailable_reason", ArmyJson::text), i64(n.get("scale")), nullable(n, "base_combat_width", ArmyJson::i32), nullable(n, "final_combat_width", ArmyJson::i32), nullable(n, "base_advantage_raw", ArmyJson::i64), nullable(n, "resolved_advantage_raw", ArmyJson::i64), nullable(n, "attacker", BattleResponseCodec::currentSide), nullable(n, "defender", BattleResponseCodec::currentSide));
    }
    private static CurrentSide currentSide(JsonNode raw) {
        ObjectNode n = closed(raw, "derived_current_fighting_raw", "derived_soft_casualties_raw", "derived_main_fighting_entry_hard_casualties_raw", "non_main_start_minus_current_minus_soft_raw", "participant_hard_total_raw", "participant_hard_ledger");
        for (String key : List.of("derived_current_fighting_raw", "derived_soft_casualties_raw", "derived_main_fighting_entry_hard_casualties_raw", "non_main_start_minus_current_minus_soft_raw", "participant_hard_total_raw")) require(i64(n.get(key)) >= 0, "current ledger quantities must be nonnegative");
        List<HardLedger> ledger = new ArrayList<>();
        for (JsonNode rawRow : n.get("participant_hard_ledger")) {
            ObjectNode row = closed(rawRow, "participant_character_id", "hard_casualties_raw"); long hard = i64(row.get("hard_casualties_raw")); require(hard >= 0, "current participant hard loss must be nonnegative"); ledger.add(new HardLedger(ledger.size(), id(row.get("participant_character_id")), hard));
        }
        require(n.get("participant_hard_ledger").isArray() && ledger.stream().mapToLong(HardLedger::hardCasualtiesRaw).reduce(0, Math::addExact) == i64(n.get("participant_hard_total_raw")), "current participant hard ledger sum differs");
        return new CurrentSide(i64(n.get("derived_current_fighting_raw")), i64(n.get("derived_soft_casualties_raw")), i64(n.get("derived_main_fighting_entry_hard_casualties_raw")), i64(n.get("non_main_start_minus_current_minus_soft_raw")), i64(n.get("participant_hard_total_raw")), ledger);
    }
    public static Reinforcement reinforcement(byte[] raw, Context source, ArmyRequests.Unit request) {
        return ArmyReinforcementCodec.decode(raw, source, request);
    }
    public static Knight knight(byte[] raw, Context source, ArmyRequests.Knight request) {
        ObjectNode root = parse(raw); equal(get(root, "step"), "query-current-battle-knight-v1-" + request.subject().value() + "-" + request.character().value() + "-" + request.regiment().value()); equal(get(root, "status"), "available"); yes(get(root, "accepted")); Frame frame = frame(root, source);
        ObjectNode n = closed(get(root, "current_battle_knight"), "observed_date_raw", "combat_id", "province_id", "subject_public_cunit_id", "native_carmy_id", "character_id", "regiment_id", "schema", "current_effective_prowess", "knight_effectiveness_raw", "province_evaluated_damage_raw", "province_evaluated_toughness_raw", "stored_combat_entry_damage_raw", "stored_combat_entry_toughness_raw", "scale", "paired_generation_ids_verified", "double_sample_stable", "province_evaluation_fresh");
        equal(n.get("schema"), "current-battle-knight-v1"); yes(n.get("paired_generation_ids_verified")); yes(n.get("double_sample_stable")); yes(n.get("province_evaluation_fresh"));
        require(i64(n.get("observed_date_raw")) == request.dateRaw() && id(n.get("combat_id")).equals(request.combat()) && id(n.get("province_id")).equals(request.province()) && unit(n.get("subject_public_cunit_id")).equals(request.subject()) && id(n.get("native_carmy_id")).equals(request.nativeArmy()) && id(n.get("character_id")).equals(request.character()) && id(n.get("regiment_id")).equals(request.regiment()) && i64(n.get("scale")) == 100000, "knight generation/frame binding mismatch");
        return new Knight(frame, request.dateRaw(), request.combat(), request.province(), request.subject(), request.nativeArmy(), request.character(), request.regiment(), i32(n.get("current_effective_prowess")), i64(n.get("knight_effectiveness_raw")), i64(n.get("province_evaluated_damage_raw")), i64(n.get("province_evaluated_toughness_raw")), i64(n.get("stored_combat_entry_damage_raw")), i64(n.get("stored_combat_entry_toughness_raw")), 100000);
    }
    static Side side(JsonNode raw) { return switch (i32(raw)) { case 0 -> Side.ATTACKER; case 1 -> Side.DEFENDER; default -> throw new IllegalArgumentException("native side must be 0 or 1"); }; }
    static Scope scope(JsonNode raw) { return switch (text(raw)) { case "full_side" -> Scope.FULL_SIDE; case "owner_subset" -> Scope.OWNER_SUBSET; default -> throw new IllegalArgumentException("unknown retreat scope"); }; }
    static Phase phase(JsonNode raw, JsonNode name) { Phase phase = switch (i32(raw)) { case 0 -> Phase.MANEUVER; case 1 -> Phase.MAIN; case 2 -> Phase.PURSUIT; case 3 -> Phase.DONE; default -> throw new IllegalArgumentException("unknown native combat phase"); }; equal(name, phase.name().toLowerCase(java.util.Locale.ROOT)); return phase; }
    static Winner winner(JsonNode raw, JsonNode name) { Winner winner = switch (i32(raw)) { case -1 -> Winner.NONE; case 0 -> Winner.ATTACKER; case 1 -> Winner.DEFENDER; default -> throw new IllegalArgumentException("unknown native winner"); }; equal(name, winner.name().toLowerCase(java.util.Locale.ROOT)); return winner; }
    static ObjectNode exactOptional(JsonNode raw, Set<String> required, Set<String> optional) {
        ObjectNode value = object(raw); Set<String> names = names(value); require(names.containsAll(required) && names.stream().allMatch(key -> required.contains(key) || optional.contains(key)), "native object has missing or invented fields"); return value;
    }
    static Obj freeze(ObjectNode value) { return DriverJson.object(bytes(value), RawJson.MAXIMUM_BYTES); }
}
