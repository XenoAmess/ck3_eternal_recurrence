package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponseCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleTerminalCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual ordinary battle gate. History and current snapshots use the same strict native decoders. */
public final class BattleControlTurnState {
    private BattleControlTurnState() { }
    static final String PENDING = "active_combat_identity_subject_combat_id_invalid";
    private static final String CONTROL = "query-battle-control-snapshot-v1-";
    private static final String TERMINAL = "query-battle-terminal-transition-v1-";
    private static final Pattern TERMINAL_REQUEST = Pattern.compile("(-?(?:0|[1-9][0-9]*))-(0|[1-9][0-9]*)-(0|[1-9][0-9]*)(?::characters:([0-9,]+))?");
    public record ControlRecord(int position, int subject, String snapshotId, BigInteger publicRevision,
            BigInteger nativeRevision, BigInteger querySequence, Obj frame) { }
    public record TerminalRequest(int combat, int subject, Optional<BigInteger> cursor, List<Integer> characters) {
        public TerminalRequest { cursor = Objects.requireNonNull(cursor); characters = List.copyOf(characters); }
        public String step() { return TERMINAL + combat + "-" + subject + "-" + cursor.orElse(BigInteger.ZERO)
                + (characters.isEmpty() ? "" : ":characters:" + String.join(",", characters.stream().map(String::valueOf).toList())); }
    }
    private record TerminalRecord(int position, TerminalRequest request, String snapshotId,
            BigInteger publicRevision, BigInteger nativeRevision, Obj frame) { }
    public record CursorSelection(Optional<Obj> currentCursor, boolean currentQueryAttempted) {
        public CursorSelection { Objects.requireNonNull(currentCursor); }
    }

    /** The ordinary terminal-cruise caller freezes a real gap-free cursor from this exact frame. */
    public static CursorSelection terminalCursor(PlanningRequest request, int combat, int subject) {
        require(combat != -1 && subject >= 0, "original full CombatID and public CUnit required");
        Obj snapshot = request.observations().snapshot(); Optional<Obj> cursor = Optional.empty(); boolean attempted = false;
        for (TerminalRecord record : terminalRecords(afterRestore(request.observations().history()))) {
            if (record.request().combat() != combat || record.request().subject() != subject || record.request().cursor().isPresent()
                    || !Objects.equals(new Text(record.snapshotId()), snapshot.get("snapshot_id"))
                    || !Objects.equals(new IntegerValue(record.publicRevision()), snapshot.get("revision"))
                    || !Objects.equals(new IntegerValue(record.nativeRevision()), snapshot.get("native_revision"))) continue;
            attempted = true;
            Obj frame = record.frame(), journal = child(frame, "terminal_journal"), prior = child(frame, "prior");
            if (!named(frame, "status", "available") || !yes(frame.get("battle_terminal_transition_ready"))
                    || !Objects.equals(frame.get("observed_date_raw"), snapshot.get("date_raw")) || journal == null || prior == null
                    || journal.get("requested_after_sequence") != Nil.INSTANCE || !named(journal, "event_status", "not_observed")
                    || journal.get("event_sequence") != Nil.INSTANCE || !named(prior, "terminal_kind", "active_not_terminal")) continue;
            BigInteger latest = n(journal, "latest_sequence");
            if (latest.signum() < 0 || latest.signum() == 0 && !equal(journal, "oldest_available_sequence", 0)) continue;
            cursor = Optional.of(obj(f("position", number(record.position())), f("combat_id", number(combat)), f("subject_army_id", number(subject)),
                    f("after_terminal_sequence", latest.signum() > 0 ? number(latest) : Nil.INSTANCE), f("empty_journal_before_arm", new Bool(latest.signum() == 0))));
        }
        return new CursorSelection(cursor, attempted);
    }

    /** Keeps original statuses for the sole BATTLE_CONTROL_PRELUDE caller; no action is submitted here. */
    public static Obj collect(PlanningRequest request) {
        Objects.requireNonNull(request);
        Obj snapshot = request.observations().snapshot();
        List<Obj> rows = request.observations().history(), scoped = afterRestore(rows);
        int scopeOffset = rows.size() - scoped.size(), latest = 0, previous = 0;
        for (int i = scoped.size(); i > 0; i--) if (yes(scoped.get(i - 1).get("ok"))
                && WarHistorySteps.isLifeAdvance(command(scoped.get(i - 1)))) {
            if (latest != 0) { previous = i; break; } latest = i;
        }
        Obj advance = latest == 0 ? null : result(scoped.get(latest - 1));
        Optional<BattleHistoryAdvance.Validation> sentinel = BattleHistoryAdvance.validate(advance);
        if (sentinel.isPresent() && !sentinel.orElseThrow().valid())
            return invalid(obj(f("status", text("invalid")), f("reason", text("native_sentinel_reconciliation_failed")),
                    f("sentinel_validation", sentinel.orElseThrow().evidence())), null);
        List<ControlRecord> records = controlRecords(scoped.subList(previous, scoped.size()), previous);
        Map<Integer, ControlRecord> current = currentFrames(snapshot, records);
        Map<Integer, ControlRecord> before = new TreeMap<>();
        if (latest != 0) for (ControlRecord record : records)
            if (previous < record.position() && record.position() < latest) before.put(record.subject(), record);
        Map<Integer, Army> observed = new HashMap<>();
        for (Obj raw : rows(snapshot.get("player_armies"))) { Army army = army(raw); observed.put(army.id(), army); }
        List<Integer> active = armies(request).stream().filter(Army::controllable)
                .filter(army -> "combat".equals(army.tacticalState())).map(Army::id).distinct().sorted().toList();
        List<Obj> recognized = new ArrayList<>(); Set<Integer> removed = new HashSet<>();
        for (ControlRecord record : before.values()) {
            int subject = record.subject(); if (active.contains(subject)) continue;
            if (terminalCruise(advance)) {
                Obj terminal = terminalTransition(scoped, previous, latest, record, snapshot, advance);
                if (named(terminal, "status", "query_required")) return put(terminal, "status", text("terminal_query_required"));
                if (named(terminal, "status", "invalid")) return invalid(terminal, record.frame());
                recognized.add(terminal);
            } else {
                Army army = observed.get(subject); String state = army == null ? null : army.tacticalState();
                recognized.add(obj(f("status", text("left_combat")), f("subject_army_id", number(subject)),
                        f("before_combat_id", record.frame().get("combat_id")),
                        f("before_snapshot_revision", record.frame().get("snapshot_revision")),
                        f("before_phase", record.frame().get("phase")), f("before_phase_day", record.frame().get("phase_day")),
                        f("observed_army_state", text(state == null ? "absent" : state)),
                        f("reason", text("semantic_subject_left_active_combat_no_winner_inferred"))));
            }
            removed.add(subject);
        }
        if (!recognized.isEmpty()) return recognized(rows, scoped, scopeOffset, previous, latest, recognized, removed);
        if (active.isEmpty()) return obj(f("status", text("not_in_combat")), f("evidence", objects(List.of())));
        if (!yes(snapshot.get("paused"))) return obj(f("status", text("wait_for_pause")), f("subject_army_ids", numbers(active)));
        Optional<Obj> watch = BattleReaderWatch.select(snapshot, scoped); if (watch.isPresent()) return watch.orElseThrow();
        for (int subject : active) {
            Optional<Obj> pending = identityPending(snapshot, subject); if (pending.isEmpty()) continue;
            Optional<Obj> prior = priorMaterialization(scoped, snapshot, subject);
            return obj(f("status", text(prior.isPresent() ? "identity_pending_after_materialization" : "identity_pending")),
                    f("subject_army_id", number(subject)), f("identity_pending", pending.orElseThrow()),
                    f("prior_materialization", prior.<Value>map(value -> value).orElse(Nil.INSTANCE)));
        }
        for (int subject : active) if (!current.containsKey(subject))
            return obj(f("status", text("query_required")), f("subject_army_id", number(subject)), f("step", text(CONTROL + subject)));
        List<Obj> transitions = new ArrayList<>();
        for (int subject : active) {
            Obj frame = current.get(subject).frame(); ControlRecord pre = before.get(subject);
            if (yes(frame.get("finalized")) || named(frame, "phase", "done")) {
                if (terminalCruise(advance)) {
                    if (pre == null) return invalid(problem("finalized_terminal_cruise_lacks_pre_arm_combat"), frame);
                    Obj terminal = terminalTransition(scoped, previous, latest, pre, snapshot, advance);
                    if (named(terminal, "status", "query_required")) return put(terminal, "status", text("terminal_query_required"));
                    if (named(terminal, "status", "invalid")) return invalid(terminal, frame);
                    return obj(f("status", text("terminal_observed")), f("subject_army_id", number(subject)),
                            f("transition", terminal), f("frame", summary(frame)));
                }
                return obj(f("status", text("terminal_observed")), f("subject_army_id", number(subject)), f("frame", summary(frame)));
            }
            if (pre == null) continue;
            Obj transition = transition(pre.frame(), frame, advance);
            if (named(transition, "status", "invalid")) return invalid(transition, frame);
            if (named(transition, "status", "combat_replaced")) {
                if (terminalCruise(advance)) {
                    Obj terminal = terminalTransition(scoped, previous, latest, pre, snapshot, advance);
                    if (named(terminal, "status", "query_required")) return put(terminal, "status", text("terminal_query_required"));
                    if (named(terminal, "status", "invalid")) return invalid(terminal, frame);
                    recognized.add(terminal);
                } else recognized.add(transition);
                removed.add(subject);
            } else transitions.add(transition);
        }
        if (!recognized.isEmpty()) return recognized(rows, scoped, scopeOffset, previous, latest, recognized, removed);
        List<Obj> frames = active.stream().map(subject -> current.get(subject).frame()).toList();
        return obj(f("status", text("ready")), f("evidence", objects(frames.stream().map(BattleControlTurnState::summary).toList())),
                f("full_frames", objects(frames)), f("transitions", objects(transitions)));
    }

    public static List<ControlRecord> controlRecords(List<Obj> history, int positionOffset) {
        List<ControlRecord> records = new ArrayList<>();
        for (int i = 0; i < history.size(); i++) {
            Obj row = history.get(i); Optional<Integer> subject = controlSubject(command(row));
            if (subject.isEmpty() || !yes(row.get("ok"))) continue;
            Obj out = result(row); if (out == null) continue;
            try {
                BigInteger revision = n(out, "queried_revision"), nativeRevision = n(out, "queried_native_revision"), sequence = n(out, "query_sequence");
                String snapshotId = OpportunityJson.text(out.get("queried_snapshot_id"), "queried_snapshot_id");
                require(revision.signum() >= 0 && nativeRevision.signum() > 0 && sequence.signum() > 0
                        && named(out, "step", command(row)) && yes(out.get("accepted")) && named(out, "status", "available")
                        && n(out, "snapshot_revision").equals(nativeRevision), "battle history binding differs");
                Obj frame = object(out.get("battle_control_snapshot"), "battle_control_snapshot");
                frame = BattleResponseCodec.normalizeControl(frame, subject.orElseThrow(), nativeRevision, n(frame, "observed_date_raw").longValueExact());
                records.add(new ControlRecord(positionOffset + i + 1, subject.orElseThrow(), snapshotId, revision, nativeRevision, sequence, frame));
            } catch (IllegalArgumentException | ArithmeticException invalid) { /* An invalid query cannot become evidence. */ }
        }
        return List.copyOf(records);
    }
    private static Map<Integer, ControlRecord> currentFrames(Obj snapshot, List<ControlRecord> records) {
        Map<Integer, ControlRecord> current = new HashMap<>(); if (!yes(snapshot.get("paused"))) return current;
        for (ControlRecord record : records) if (sameFrame(record.snapshotId(), record.publicRevision(), record.nativeRevision(), record.frame(), snapshot)) current.put(record.subject(), record);
        try {
            int subject = id(snapshot.get("battle_control_snapshot_v1_subject_army_id"));
            BigInteger sequence = n(snapshot, "battle_control_snapshot_v1_query_sequence");
            require(named(snapshot, "battle_control_snapshot_v1_status", "available") && sequence.signum() > 0
                    && Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_snapshot_id"), snapshot.get("snapshot_id"))
                    && Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_revision"), snapshot.get("revision")), "direct battle source differs");
            BigInteger nativeRevision = n(snapshot, "native_revision");
            if (snapshot.members().containsKey("battle_control_snapshot_v1_queried_native_revision"))
                require(Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_native_revision"), new IntegerValue(nativeRevision)), "direct native query provenance differs");
            Obj frame = BattleResponseCodec.normalizeControl(object(snapshot.get("battle_control_snapshot_v1"), "direct battle frame"), subject, nativeRevision, n(snapshot, "date_raw").longValueExact());
            int position = records.stream().filter(record -> record.subject() == subject && record.querySequence().equals(sequence)
                    && sameFrame(record.snapshotId(), record.publicRevision(), record.nativeRevision(), record.frame(), snapshot)).mapToInt(ControlRecord::position).max().orElse(0);
            current.put(subject, new ControlRecord(position, subject, OpportunityJson.text(snapshot.get("snapshot_id"), "snapshot_id"), n(snapshot, "revision"), nativeRevision, sequence, frame));
        } catch (IllegalArgumentException | ArithmeticException unavailable) { /* Missing direct frame requires a real query. */ }
        return current;
    }
    private static List<TerminalRecord> terminalRecords(List<Obj> rows) {
        List<TerminalRecord> records = new ArrayList<>();
        for (int i = 0; i < rows.size(); i++) {
            Obj row = rows.get(i); Optional<TerminalRequest> request = parseTerminal(command(row)); Obj out = result(row);
            if (request.isEmpty() || !yes(row.get("ok")) || out == null) continue;
            try {
                BigInteger revision = n(out, "queried_revision"), nativeRevision = n(out, "queried_native_revision");
                require(revision.signum() >= 0 && nativeRevision.signum() > 0 && n(out, "query_sequence").signum() > 0
                        && named(out, "step", command(row)) && yes(out.get("accepted"))
                        && Set.of("available", "unavailable").contains(OpportunityJson.text(out.get("status"), "status"))
                        && n(out, "snapshot_revision").equals(nativeRevision), "terminal history binding differs");
                Obj frame = object(out.get("battle_terminal_transition"), "battle_terminal_transition"); TerminalRequest q = request.orElseThrow();
                frame = BattleTerminalCodec.normalizeTerminal(frame, q.combat(), q.subject(), q.cursor(), q.characters(), nativeRevision, n(frame, "observed_date_raw").longValueExact());
                require(Objects.equals(frame.get("status"), out.get("status")), "terminal envelope status differs");
                records.add(new TerminalRecord(i + 1, q, OpportunityJson.text(out.get("queried_snapshot_id"), "queried_snapshot_id"), revision, nativeRevision, frame));
            } catch (IllegalArgumentException | ArithmeticException unavailable) { /* Retain raw history; never promote malformed material. */ }
        }
        return List.copyOf(records);
    }
    private static Obj terminalTransition(List<Obj> rows, int previous, int latest, ControlRecord before, Obj snapshot, Obj advance) {
        var validation = BattleHistoryAdvance.validate(advance);
        if (validation.isEmpty() || !validation.orElseThrow().valid() || !validation.orElseThrow().terminalObserved() || !terminalCruise(advance))
            return problem("terminal_cruise_lacks_complete_native_terminal_sentinel");
        int combat = int32(before.frame().get("combat_id"));
        List<TerminalRecord> records = terminalRecords(rows), cursors = new ArrayList<>();
        for (TerminalRecord record : records) {
            Obj frame = record.frame(), journal = child(frame, "terminal_journal"), prior = child(frame, "prior");
            if (previous < record.position() && record.position() < latest && record.request().combat() == combat
                    && record.request().cursor().isEmpty() && record.snapshotId().equals(before.snapshotId())
                    && record.publicRevision().equals(before.publicRevision()) && record.nativeRevision().equals(before.nativeRevision())
                    && named(frame, "status", "available") && Objects.equals(frame.get("observed_date_raw"), before.frame().get("observed_date_raw"))
                    && journal != null && journal.get("requested_after_sequence") == Nil.INSTANCE && named(journal, "event_status", "not_observed")
                    && journal.get("event_sequence") == Nil.INSTANCE && numberOrNull(journal.get("latest_sequence")) != null
                    && n(journal, "latest_sequence").signum() >= 0 && (n(journal, "latest_sequence").signum() > 0 || equal(journal, "oldest_available_sequence", 0))
                    && prior != null && equal(prior, "combat_id", combat) && named(prior, "terminal_kind", "active_not_terminal")) cursors.add(record);
        }
        if (cursors.isEmpty()) return problem("terminal_cruise_lacks_gap_free_pre_arm_cursor");
        TerminalRecord cursorRecord = cursors.stream().min(Comparator.comparingInt((TerminalRecord record) -> record.request().subject()).thenComparing(Comparator.comparingInt(TerminalRecord::position).reversed())).orElseThrow();
        BigInteger cursor = n(child(cursorRecord.frame(), "terminal_journal"), "latest_sequence");
        TerminalRequest query = new TerminalRequest(combat, cursorRecord.request().subject(), cursor.signum() == 0 ? Optional.empty() : Optional.of(cursor), List.of());
        Optional<TerminalRecord> matching = records.stream().filter(record -> record.position() > latest && record.request().combat() == combat
                && record.request().subject() == query.subject() && record.request().cursor().equals(query.cursor())
                && sameFrame(record.snapshotId(), record.publicRevision(), record.nativeRevision(), record.frame(), snapshot)).reduce((a, b) -> b);
        if (matching.isEmpty()) {
            boolean attempted = rows.subList(latest, rows.size()).stream().anyMatch(row -> query.step().equals(command(row)));
            return obj(f("status", text(attempted ? "invalid" : "query_required")), f("reason", text(attempted ? "cursor_bound_terminal_query_invalid" : "query_terminal_journal_after_native_stop")),
                    f("step", text(query.step())), f("combat_id", number(combat)), f("subject_army_id", number(query.subject())),
                    f("transition_subject_army_id", number(before.subject())), f("after_terminal_sequence", cursorValue(query.cursor())));
        }
        Obj terminal = matching.orElseThrow().frame(), journal = child(terminal, "terminal_journal"), prior = child(terminal, "prior");
        if (!named(terminal, "status", "available") || !yes(terminal.get("battle_terminal_transition_ready")) || journal == null || prior == null
                || !named(journal, "event_status", "observed") || numberOrNull(journal.get("event_sequence")) == null
                || n(journal, "event_sequence").compareTo(cursor) <= 0 || cursor.signum() == 0 && !equal(journal, "oldest_available_sequence", 1)
                || !Objects.equals(prior.get("terminal_date_raw"), advance.get("ending_date_raw"))
                || !(named(prior, "terminal_kind", "normal_result") && Set.of(BigInteger.ZERO, BigInteger.ONE).contains(numberOrNull(prior.get("winner_raw")))
                    || named(prior, "terminal_kind", "no_normal_result") && Set.of(BigInteger.valueOf(-1), BigInteger.ZERO, BigInteger.ONE).contains(numberOrNull(prior.get("winner_raw")))))
            return problem("post_stop_journal_does_not_prove_original_combat_cursor_date_winner");
        int winner = n(prior, "winner_raw").intValueExact();
        return obj(f("status", text("terminal_journal_observed")), f("subject_army_id", number(before.subject())), f("journal_subject_army_id", number(query.subject())),
                f("before_combat_id", number(combat)), f("terminal_date_raw", prior.get("terminal_date_raw")), f("terminal_journal_sequence", journal.get("event_sequence")),
                f("after_terminal_sequence", cursorValue(query.cursor())), f("outcome", obj(f("terminal_kind", prior.get("terminal_kind")),
                    f("winner_side", named(prior, "terminal_kind", "normal_result") ? text(winner == 0 ? "attacker" : "defender") : Nil.INSTANCE),
                    f("winner_raw", prior.get("winner_raw")), f("battle_result_id", prior.get("battle_result_id")), f("wipe", prior.get("wipe_raw")))),
                f("successor", terminal.get("successor")), f("removal", terminal.get("removal")), f("reason", text("cursor_bound_native_terminal_event_observed")));
    }

    /** Original phase/ledger acceptance, preserving the reinforcement reopen and terminal skip distinctions. */
    public static Obj transition(Obj before, Obj after, Obj advance) {
        long start = n(before, "observed_date_raw").longValueExact(), end = n(after, "observed_date_raw").longValueExact(), delta = Math.subtractExact(end, start);
        int beforeCombat = int32(before.get("combat_id")), afterCombat = int32(after.get("combat_id"));
        Obj common = obj(f("subject_army_id", after.get("subject_public_cunit_id")), f("before_combat_id", number(beforeCombat)), f("after_combat_id", number(afterCombat)),
                f("before_snapshot_revision", before.get("snapshot_revision")), f("after_snapshot_revision", after.get("snapshot_revision")),
                f("before_date_raw", number(start)), f("after_date_raw", number(end)), f("observed_date_delta_raw", number(delta)),
                f("advance_starting_date_raw", value(advance, "starting_date_raw")), f("advance_ending_date_raw", value(advance, "ending_date_raw")), f("advance_elapsed_days", value(advance, "elapsed_days")),
                f("before_phase", before.get("phase")), f("before_phase_day", before.get("phase_day")), f("after_phase", after.get("phase")), f("after_phase_day", after.get("phase_day")));
        if (beforeCombat != afterCombat) return classified(common, "combat_replaced", "original_combat_left_subject_and_different_active_combat_observed");
        if (!Objects.equals(before.get("subject_native_carmy_id"), after.get("subject_native_carmy_id")) || !Objects.equals(before.get("province_id"), after.get("province_id")))
            return classified(common, "invalid", "same_combat_subject_identity_or_province_changed");
        if (n(after, "snapshot_revision").compareTo(n(before, "snapshot_revision")) <= 0) return classified(common, "invalid", "native_revision_did_not_increase");
        Optional<BattleHistoryAdvance.Validation> sentinel = BattleHistoryAdvance.validate(advance);
        if (advance == null || !named(advance, "step", "life-advance") && sentinel.isEmpty()
                || numberOrNull(value(advance, "starting_date_raw")) == null || numberOrNull(value(advance, "ending_date_raw")) == null || numberOrNull(value(advance, "elapsed_days")) == null)
            return classified(common, "invalid", "bounded_advance_lacks_exact_start_end_elapsed");
        if (sentinel.isPresent() && !sentinel.orElseThrow().valid()) return classified(common, "invalid", "native_sentinel_reconciliation_failed");
        if (!equal(advance, "starting_date_raw", start) || !equal(advance, "ending_date_raw", end) || delta <= 0 || delta % 24 != 0)
            return classified(common, "invalid", "advance_dates_do_not_match_positive_whole_observed_days");
        long elapsed = delta / 24; common = put(common, "actual_elapsed_days", number(elapsed));
        if (!equal(advance, "elapsed_days", elapsed) || sentinel.isEmpty() && elapsed != 1 && elapsed != 2)
            return classified(common, "invalid", "advance_elapsed_or_two_day_envelope_differs");
        int bp = int32(before.get("phase_raw")), ap = int32(after.get("phase_raw")), bd = int32(before.get("phase_day")), ad = int32(after.get("phase_day"));
        boolean strictAdded = strictReinforcement(before, after), noWinner = named(after, "winner_side", "none") && named(after, "forced_winner_side", "none");
        boolean mainReopen = bp == 1 && ap == 1 && ad < bd && sentinel.isPresent() && 0 <= ad && ad <= elapsed && noWinner && strictAdded;
        boolean pursuitReopen = bp == 2 && ap == 1 && noWinner && 0 <= ad && ad <= (long) bd + elapsed;
        boolean terminalSkip = sentinel.isPresent() && bp < 2 && ap == 2 && ap - bp <= elapsed && ad >= 0 && ad <= elapsed
                && (named(after, "winner_side", "attacker") && equal(child(after, "defender"), "derived_current_fighting_raw", 0)
                    || named(after, "winner_side", "defender") && equal(child(after, "attacker"), "derived_current_fighting_raw", 0));
        boolean legal = mainReopen || ap == bp && bd <= ad && ad <= (long) bd + elapsed
                || ap == bp + 1 && ad >= 0 && ad <= elapsed || pursuitReopen || terminalSkip;
        if (!legal) return classified(common, "invalid", "phase_day_path_regressed_or_skipped");
        boolean phaseChanged = bp != ap || bd != ad, ledgerChanged = !ledgerFingerprint(before).equals(ledgerFingerprint(after));
        if (!phaseChanged && !ledgerChanged) return merge(classified(common, "invalid", "ack_date_revision_without_phase_or_casualty_ledger_transition"), obj(f("phase_day_changed", new Bool(false)), f("ledger_changed", new Bool(false))));
        return merge(classified(common, mainReopen || pursuitReopen ? "same_combat_reopened" : "same_combat_advanced",
                mainReopen ? "strict_reinforcement_restarted_main_counter" : pursuitReopen ? "pursuit_reopened_main_with_winner_reset" : terminalSkip ? "reconciled_sentinel_reached_terminal_pursuit" : "legal_bounded_phase_or_exact_ledger_transition"),
                obj(f("phase_day_changed", new Bool(phaseChanged)), f("ledger_changed", new Bool(ledgerChanged)), f("pursuit_reopened_to_main", new Bool(pursuitReopen)),
                    f("main_reopened_by_reinforcement", new Bool(mainReopen)), f("reinforcement_strictly_added", new Bool(strictAdded)), f("terminal_pursuit_skip", new Bool(terminalSkip))));
    }
    private static List<Value> ledgerFingerprint(Obj frame) {
        List<Value> output = new ArrayList<>();
        for (String sideName : List.of("attacker", "defender")) {
            Obj side = object(frame.get(sideName), sideName);
            output.add(side.get("ordered_armies"));
            for (String bucket : List.of("levy_entries", "men_at_arms_entries")) for (Obj row : rows(side.get(bucket))) {
                List<Value> fields = new ArrayList<>();
                for (String field : List.of("bucket", "bucket_index", "regiment_id", "native_carmy_id", "public_cunit_id", "owner_character_id", "starting_raw", "current_fighting_raw", "soft_casualties_raw", "fights_in_main_phase", "hard_casualties_status", "hard_casualties_raw")) fields.add(row.get(field));
                output.add(new Arr(fields));
            }
            output.add(side.get("participant_hard_ledger"));
            for (String field : List.of("derived_current_fighting_raw", "derived_soft_casualties_raw", "derived_main_fighting_entry_hard_casualties_raw", "non_main_start_minus_current_minus_soft_raw", "participant_hard_total_raw")) output.add(side.get(field));
        }
        return List.copyOf(output);
    }
    private static boolean strictReinforcement(Obj before, Obj after) {
        boolean added = false;
        for (String side : List.of("attacker", "defender")) {
            Set<Integer> a = sideIds(before, side), b = sideIds(after, side); if (!b.containsAll(a)) return false; added |= !a.equals(b);
        }
        return added;
    }
    private static Set<Integer> sideIds(Obj frame, String side) {
        Set<Integer> ids = new HashSet<>(); for (Obj army : rows(object(frame.get(side), side).get("ordered_armies"))) ids.add(id(army.get("public_cunit_id"))); return Set.copyOf(ids);
    }
    public static Obj summary(Obj frame) {
        List<Field> fields = new ArrayList<>();
        for (String field : List.of("combat_id", "snapshot_revision", "observed_date_raw", "phase", "phase_day", "winner_side", "finalized")) fields.add(f(field, frame.get(field)));
        fields.add(f("subject_army_id", frame.get("subject_public_cunit_id")));
        for (String side : List.of("attacker", "defender")) {
            Obj value = object(frame.get(side), side);
            fields.add(f(side + "_current_raw", value.get("derived_current_fighting_raw"))); fields.add(f(side + "_soft_raw", value.get("derived_soft_casualties_raw"))); fields.add(f(side + "_hard_raw", value.get("participant_hard_total_raw")));
        }
        return obj(fields.toArray(Field[]::new));
    }
    private static Optional<Obj> identityPending(Obj snapshot, int subject) {
        Optional<Obj> army = rows(snapshot.get("player_armies")).stream().filter(row -> equal(row, "army_id", subject)).findFirst();
        if (!yes(snapshot.get("paused")) || !named(snapshot, "battle_control_snapshot_v1_status", "identity_pending")
                || !named(snapshot, "battle_control_snapshot_v1_diagnostic_reason", PENDING) || !named(snapshot, "battle_control_snapshot_v1_native_query_status", "state_changed")
                || !equal(snapshot, "battle_control_snapshot_v1_query_attempts", 3) || snapshot.get("battle_control_snapshot_v1") != Nil.INSTANCE
                || !equal(snapshot, "battle_control_snapshot_v1_subject_army_id", subject)
                || !Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_snapshot_id"), snapshot.get("snapshot_id"))
                || !Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_revision"), snapshot.get("revision"))
                || !Objects.equals(snapshot.get("battle_control_snapshot_v1_queried_native_revision"), snapshot.get("native_revision"))
                || army.isEmpty() || !yes(army.orElseThrow().get("controllable")) || !yes(army.orElseThrow().get("in_combat"))) return Optional.empty();
        return Optional.of(obj(f("status", text("identity_pending")), f("diagnostic_reason", text(PENDING)), f("subject_army_id", number(subject)),
                f("snapshot_id", snapshot.get("snapshot_id")), f("revision", snapshot.get("revision")), f("native_revision", snapshot.get("native_revision")), f("date_raw", snapshot.get("date_raw"))));
    }
    private static Optional<Obj> priorMaterialization(List<Obj> rows, Obj snapshot, int subject) {
        for (int i = rows.size() - 1; i >= 0; i--) {
            Obj row = rows.get(i), result = result(row), material = child(result, "battle_identity_materialization");
            if (!yes(row.get("ok")) || !"life-advance".equals(command(row)) || result == null || material == null) continue;
            try {
                if (equal(material, "schema_version", 1) && named(material, "status", "one_day_advanced") && named(material, "proof_kind", "battle_identity_materialization")
                        && named(material, "diagnostic_reason", PENDING) && equal(material, "subject_public_cunit_id", subject) && named(material, "next_revision_requirement", "full_combat_id")
                        && n(material, "ending_date_raw").equals(n(material, "starting_date_raw").add(BigInteger.valueOf(24))) && equal(material, "elapsed_days", 1)
                        && n(material, "ending_revision").compareTo(n(material, "starting_revision")) > 0 && n(material, "starting_native_revision").signum() > 0
                        && n(material, "ending_native_revision").compareTo(n(material, "starting_native_revision")) > 0
                        && Objects.equals(material.get("ending_snapshot_id"), snapshot.get("snapshot_id")) && Objects.equals(material.get("ending_revision"), snapshot.get("revision"))
                        && Objects.equals(material.get("ending_native_revision"), snapshot.get("native_revision")) && Objects.equals(material.get("ending_date_raw"), snapshot.get("date_raw"))
                        && yes(result.get("paused")) && equal(result, "timeline_speed", 1) && named(result, "timeline_policy", "exact_one_day_battle_identity_materialization")) return Optional.of(material);
            } catch (IllegalArgumentException invalid) { /* Malformed history is not a prior materialization. */ }
        }
        return Optional.empty();
    }
    public static Optional<Integer> controlSubject(String step) {
        if (step == null || !step.startsWith(CONTROL)) return Optional.empty(); String value = step.substring(CONTROL.length());
        if (!value.matches("0|[1-9][0-9]*")) return Optional.empty();
        try { return Optional.of(id(new IntegerValue(new BigInteger(value)))); } catch (IllegalArgumentException | ArithmeticException invalid) { return Optional.empty(); }
    }
    public static Optional<TerminalRequest> parseTerminal(String step) {
        if (step == null || !step.startsWith(TERMINAL)) return Optional.empty(); var matcher = TERMINAL_REQUEST.matcher(step.substring(TERMINAL.length())); if (!matcher.matches()) return Optional.empty();
        try {
            int combat = new BigInteger(matcher.group(1)).intValueExact(), subject = new BigInteger(matcher.group(2)).intValueExact(); BigInteger cursor = new BigInteger(matcher.group(3));
            require(combat != -1 && subject >= 0 && cursor.signum() >= 0 && cursor.bitLength() <= 64, "terminal request bounds");
            require(Integer.toString(combat).equals(matcher.group(1)), "canonical signed full CombatID required");
            List<Integer> characters = new ArrayList<>(); if (matcher.group(4) != null) for (String id : matcher.group(4).split(",", -1)) {
                require(id.matches("[1-9][0-9]*"), "canonical CharacterID"); int character = new BigInteger(id).intValueExact(); require(character > 0, "positive CharacterID"); if (!characters.contains(character)) characters.add(character);
            }
            return Optional.of(new TerminalRequest(combat, subject, cursor.signum() == 0 ? Optional.empty() : Optional.of(cursor), characters));
        } catch (IllegalArgumentException | ArithmeticException invalid) { return Optional.empty(); }
    }
    private static Obj recognized(List<Obj> original, List<Obj> scoped, int offset, int previous, int latest, List<Obj> transitions, Set<Integer> subjects) {
        Set<Integer> remove = new HashSet<>();
        for (int i = 1; i <= scoped.size(); i++) if (previous < i && i < latest && controlSubject(command(scoped.get(i - 1))).filter(subjects::contains).isPresent()) remove.add(offset + i);
        List<Obj> remaining = new ArrayList<>(); for (int i = 1; i <= original.size(); i++) if (!remove.contains(i)) remaining.add(original.get(i - 1));
        return obj(f("status", text("transition_recognized")), f("transitions", objects(transitions)), f("remaining_rows", objects(remaining)));
    }
    private static boolean sameFrame(String id, BigInteger revision, BigInteger nativeRevision, Obj frame, Obj snapshot) {
        return Objects.equals(new Text(id), snapshot.get("snapshot_id")) && Objects.equals(new IntegerValue(revision), snapshot.get("revision"))
                && Objects.equals(new IntegerValue(nativeRevision), snapshot.get("native_revision")) && Objects.equals(frame.get("observed_date_raw"), snapshot.get("date_raw"));
    }
    private static Obj invalid(Obj transition, Obj frame) { return obj(f("status", text("transition_invalid")), f("transition", transition), f("frame", frame == null ? Nil.INSTANCE : summary(frame))); }
    private static Obj problem(String reason) { return obj(f("status", text("invalid")), f("reason", text(reason))); }
    private static Obj classified(Obj common, String status, String reason) { return merge(common, obj(f("status", text(status)), f("reason", text(reason)))); }
    private static boolean terminalCruise(Obj result) { return named(result, "step", "battle-terminal-cruise"); }
    private static Value cursorValue(Optional<BigInteger> cursor) { return cursor.<Value>map(IntegerValue::new).orElse(Nil.INSTANCE); }
    static Obj child(Obj value, String key) { return value != null && value.get(key) instanceof Obj obj ? obj : null; }
    static Value value(Obj value, String key) { return value == null || value.get(key) == null ? Nil.INSTANCE : value.get(key); }
    static boolean named(Obj value, String key, String name) { return value != null && name != null && new Text(name).equals(value.get(key)); }
    static BigInteger numberOrNull(Value value) { return value instanceof IntegerValue integer ? integer.value() : null; }
    static BigInteger n(Obj value, String key) { return integer(value.get(key), key); }
    static boolean equal(Obj value, String key, long number) { return value != null && BigInteger.valueOf(number).equals(numberOrNull(value.get(key))); }
    private static void require(boolean condition, String reason) { org.xar.ck3.control.contracts.StrictJson.require(condition, reason); }
}
