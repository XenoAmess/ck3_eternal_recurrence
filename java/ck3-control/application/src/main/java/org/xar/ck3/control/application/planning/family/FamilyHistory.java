package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Persistent ordinary history; a plan wrapper is never substituted for factual results. */
public final class FamilyHistory {
    private FamilyHistory() { }
    static String command(Obj row) {
        String command = string(row.get("command"));
        if (!"auto-turn".equals(command)) return command;
        if (!(row.get("result") instanceof Obj result) || !(result.get("auto_turn") instanceof Obj turn)) return null;
        return string(turn.get("selected_step"));
    }
    static Optional<Obj> result(Obj row) {
        if (!(row.get("result") instanceof Obj result)) return Optional.empty();
        if (!"auto-turn".equals(string(row.get("command")))) return Optional.of(result);
        for (String key : List.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after"))
            if (result.get(key) instanceof Obj) return Optional.of(result);
        if (result.get("auto_turn") instanceof Obj turn && turn.get("result") instanceof Obj nested) return Optional.of(nested);
        return Optional.of(result);
    }
    static BigInteger index(Obj row, int position) {
        return row.get("index") instanceof IntegerValue i ? i.value() : BigInteger.valueOf(position + 1L);
    }
    static boolean advance(String step) { return "life-advance".equals(step) || step != null && step.startsWith("life-advance-"); }
    static BigInteger latest(List<Obj> rows, String step, boolean successful) {
        for (int i = rows.size() - 1; i >= 0; i--)
            if (step.equals(command(rows.get(i))) && (!successful || yes(rows.get(i).get("ok")))) return index(rows.get(i), i);
        return BigInteger.ZERO;
    }
    static BigInteger latestAdvance(List<Obj> rows) {
        for (int i = rows.size() - 1; i >= 0; i--)
            if (advance(command(rows.get(i))) && yes(rows.get(i).get("ok"))) return index(rows.get(i), i);
        return BigInteger.ZERO;
    }
    static Optional<Obj> rulerAttempt(List<Obj> rows, Obj snapshot) {
        Value currentActor = object(snapshot.get("played_character")).get("character_id"); positive(currentActor);
        for (int i = rows.size() - 1; i >= 0; i--) {
            Obj history = rows.get(i); String step = command(history);
            if (step == null || !step.matches("arrange-marriage-[0-9]+-[0-9]+")) continue;
            String[] parts = step.substring("arrange-marriage-".length()).split("-");
            Value played = new IntegerValue(new BigInteger(parts[0])), candidate = new IntegerValue(new BigInteger(parts[1]));
            positive(played); positive(candidate);
            if (!eq(played, currentActor)) continue;
            Value attempt = new IntegerValue(index(history, i));
            Obj output = obj("played_character_id", played, "candidate_character_id", candidate, "attempt_index", attempt, "retry_index", attempt);
            String currentRelation = relationship(snapshot.get("played_character"), played, candidate);
            if (currentRelation != null) return Optional.of(output.with("status", t("completed")).with("relationship_status", t(currentRelation)));
            // A failed command wrapper or a missing ACK cannot prove no native send.
            // Historical rows do not carry an intrinsic episode/source qualification.
            if (!yes(history.get("ok"))) return Optional.of(output.with("status", t("pending")).with("reason", t("submission_outcome_unknown_no_replay")));
            // Original ruler intent is stored in the actual executor root, separately from auto_turn's plan.
            if (!(history.get("result") instanceof Obj result) || !(result.get("marriage_action") instanceof Obj action))
                return Optional.of(output.with("status", t("pending")).with("reason", t("submission_result_missing_no_replay")));
            if (!eq(action.get("played_character_id"), played) || !eq(action.get("candidate_character_id"), candidate))
                throw new IllegalArgumentException("ruler marriage result changed its original command pair");
            if (!"proposal_submitted".equals(string(action.get("status"))))
                return Optional.of(output.with("status", t("pending")).with("reason", t("submission_disposition_not_independently_qualified")));
            BigInteger days = null;
            if (action.get("submitted_date_raw") instanceof IntegerValue submitted && snapshot.get("date_raw") instanceof IntegerValue current
                    && current.value().compareTo(submitted.value()) >= 0) days = current.value().subtract(submitted.value()).divide(BigInteger.valueOf(24));
            long advances = rows.subList(i + 1, rows.size()).stream().filter(row -> yes(row.get("ok")) && advance(command(row))).count();
            boolean timeout = advances >= 7 || days != null && days.compareTo(BigInteger.valueOf(30)) >= 0;
            return Optional.of(output.with("status", t("pending")).with("reason", t(timeout ? "proposal_timeout_unknown_no_replay" : "awaiting_relationship"))
                    .with("native_pending_status", t("unknown_without_current_outbound_query"))
                    .with("submitted_date_raw", nil(action.get("submitted_date_raw"))).with("elapsed_days", days == null ? Nil.INSTANCE : new IntegerValue(days))
                    .with("life_advances", n(advances)).with("timeout_days", n(30)).with("max_life_advances", n(7)));
        }
        return Optional.empty();
    }
    private static String relationship(Value raw, Value played, Value candidate) {
        if (!(raw instanceof Obj actual) || !eq(actual.get("character_id"), played)) return null;
        if (eq(actual.get("betrothed_id"), candidate)) return "accepted_betrothal";
        if (actual.get("spouse_ids") instanceof Arr spouses && spouses.items().contains(candidate)) return "accepted_marriage";
        return null;
    }
    public static Optional<Obj> focusPending(List<Obj> rows, Obj snapshot) {
        Set<Value> closed = new HashSet<>();
        int controller = NativeCharacterId.of(integer(object(snapshot.get("played_character")).get("character_id"))).value();
        BigInteger unsignedController = BigInteger.valueOf(controller & 0xffff_ffffL);
        for (int i = rows.size() - 1; i >= 0; i--) {
            String step = command(rows.get(i)); Optional<Obj> value = result(rows.get(i)); if (value.isEmpty()) continue;
            Obj result = value.get();
            if ("private-query-child-education-focus-receipt-v1".equals(step)) {
                if ("observed_applied".equals(string(result.get("status"))) && yes(result.get("observed_applied")) && result.get("submission") instanceof Obj submission)
                    closed.add(submission.get("action_request_id"));
                continue;
            }
            if (!"private-select-child-education-focus-v1".equals(step)) continue;
            Value action = result.get("action_request_id"); if (closed.contains(action)) continue;
            if ("rejected_before_submit".equals(string(result.get("status")))) { closed.add(action); continue; }
            if (!oneOf(result.get("status"), "action_state_unknown", "submit_unknown", "submitted_verification_pending")) continue;
            Obj pre = object(result.get("pre_frame"));
            if (sameEpisode(pre, snapshot) && integer(pre.get("controller_full_id")).equals(unsignedController)) return Optional.of(result);
        }
        return Optional.empty();
    }
}
