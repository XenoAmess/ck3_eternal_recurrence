package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original generic execute_step emergency predicates. This DATA result grants no action authority. */
public final class OrdinaryAutomaticSurrenderPolicy {
    private OrdinaryAutomaticSurrenderPolicy() { }
    public enum Variant {
        DE_JURE_NO_SAFE_ROUTE("de_jure_no_safe_route"), RAIKTOR_TERMINAL_CONTROL("raiktor_terminal_control"),
        RAIKTOR_LONG_WAR_UTILITY("raiktor_long_war_utility"), TERMINAL_SCORE_DEFEAT("terminal_score_defeat");
        private final String wire;
        Variant(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Variant exact(String wire) {
            for (Variant variant : values()) if (variant.wire.equals(wire)) return variant;
            throw new IllegalArgumentException("unknown automatic surrender variant");
        }
    }
    public enum Reason {
        SNAPSHOT_NOT_PAUSED, WAR_NOT_ACTIVE, TERMINATION_OPTIONS_MISSING, TERMINATION_EVIDENCE_NOT_SAME_FRAME,
        DE_JURE_EMERGENCY_SURRENDER_GATE_FAILED, RAIKTOR_TERMINAL_CONTROL_SURRENDER_GATE_FAILED,
        RAIKTOR_LONG_WAR_SURRENDER_GATE_FAILED, TERMINAL_SCORE_SURRENDER_GATE_FAILED;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Decision permits Ready, Unavailable { boolean ready(); }
    public record Ready(Variant variant, Obj war, Obj options, Obj surrender) implements Decision {
        public Ready { Objects.requireNonNull(variant); Objects.requireNonNull(war); Objects.requireNonNull(options); Objects.requireNonNull(surrender); }
        public boolean ready() { return true; }
        public Obj evidence() { return new Obj(Map.of("variant", new Text(variant.wire()), "war", war, "options", options, "surrender", surrender)); }
    }
    public record Unavailable(List<Reason> orderedReasons) implements Decision {
        public Unavailable { orderedReasons = List.copyOf(orderedReasons); StrictJson.require(orderedReasons.size() == 4, "four ordered original emergency branches required"); }
        public boolean ready() { return false; }
        public String reason() {
            return "de_jure=" + orderedReasons.get(0).wire() + "; raiktor=" + orderedReasons.get(1).wire()
                    + "; raiktor_long_war=" + orderedReasons.get(2).wire() + "; terminal=" + orderedReasons.get(3).wire();
        }
    }
    private record Attempt(Ready ready, Reason reason) {
        private Attempt { StrictJson.require((ready == null) != (reason == null), "exactly one branch result required"); }
    }
    public static Decision evaluate(Obj actualSnapshot, int fullWarId) {
        Objects.requireNonNull(actualSnapshot); StrictJson.require(fullWarId > 0, "positive complete int31 surrender WarID required");
        List<Reason> reasons = new ArrayList<>();
        for (Variant variant : Variant.values()) {
            Attempt attempt = branch(actualSnapshot, fullWarId, variant);
            if (attempt.ready() != null) return attempt.ready(); reasons.add(attempt.reason());
        }
        return new Unavailable(reasons);
    }
    public static Arr originalTuple(Decision decision) {
        return decision instanceof Ready ready ? new Arr(List.of(new Bool(true), new Text("ready"), ready.evidence()))
                : new Arr(List.of(new Bool(false), new Text(((Unavailable) decision).reason()), new Obj(Map.of())));
    }
    private static Attempt branch(Obj snapshot, int id, Variant variant) {
        if (!truth(snapshot.get("paused"))) return new Attempt(null, Reason.SNAPSHOT_NOT_PAUSED);
        Obj war = first(snapshot.get("active_wars"), id); if (war == null) return new Attempt(null, Reason.WAR_NOT_ACTIVE);
        Obj options = unique(snapshot.get("war_termination_options"), id); if (options == null) return new Attempt(null, Reason.TERMINATION_OPTIONS_MISSING);
        if (!sameFrame(snapshot, options)) return new Attempt(null, Reason.TERMINATION_EVIDENCE_NOT_SAME_FRAME);
        Obj choices = object(options.get("options")), surrender = choices == null ? null : object(choices.get("surrender"));
        Obj response = surrender == null ? null : object(surrender.get("recipient_response"));
        Obj cb = object(options.get("active_casus_belli_identity"));
        Value score = war.get("player_relative_war_score");
        boolean base = text(war.get("player_side"), "attacker") && truth(war.get("player_is_primary_war_leader"))
                && text(options.get("player_side"), "attacker") && truth(options.get("player_is_primary_war_leader"))
                && integer(score) != null && equal(options.get("player_relative_war_score"), score)
                && truth(options.get("active_casus_belli_present")) && cb != null && legal(surrender)
                && response != null && text(response.get("status"), "available") && truth(response.get("would_accept_now"));
        boolean valid = base && switch (variant) {
            case DE_JURE_NO_SAFE_ROUTE -> atMost(score, -1) && atLeast(options.get("war_duration_days"), 180)
                    && text(cb.get("canonical_key"), "individual_county_de_jure_cb");
            case RAIKTOR_TERMINAL_CONTROL -> is(score, -100) && absolute(options, score)
                    && text(cb.get("canonical_key"), "raiktor_claim_cb");
            case RAIKTOR_LONG_WAR_UTILITY -> atMost(score, -1) && absolute(options, score)
                    && atLeast(options.get("war_duration_days"), 730) && text(cb.get("canonical_key"), "raiktor_claim_cb");
            case TERMINAL_SCORE_DEFEAT -> is(score, -100) && absolute(options, score);
        };
        Reason failure = switch (variant) {
            case DE_JURE_NO_SAFE_ROUTE -> Reason.DE_JURE_EMERGENCY_SURRENDER_GATE_FAILED;
            case RAIKTOR_TERMINAL_CONTROL -> Reason.RAIKTOR_TERMINAL_CONTROL_SURRENDER_GATE_FAILED;
            case RAIKTOR_LONG_WAR_UTILITY -> Reason.RAIKTOR_LONG_WAR_SURRENDER_GATE_FAILED;
            case TERMINAL_SCORE_DEFEAT -> Reason.TERMINAL_SCORE_SURRENDER_GATE_FAILED;
        };
        return valid ? new Attempt(new Ready(variant, war, options, surrender), null) : new Attempt(null, failure);
    }
    /** Original same-episode successful submission history is a fence, not a settlement observation. */
    public static java.util.Optional<Obj> previousSubmission(Arr history, int fullWarId, Value episode) {
        Objects.requireNonNull(history); Objects.requireNonNull(episode);
        for (int i = history.items().size() - 1; i >= 0; i--) {
            Obj row = object(history.items().get(i));
            if (row == null || !text(row.get("command"), "surrender-war-" + fullWarId) || !truth(row.get("ok"))) continue;
            Obj result = object(row.get("result")), action = result == null ? null : object(result.get("war_termination_result"));
            if (action != null && is(action.get("war_id"), fullWarId) && equal(action.get("episode_run_id"), episode)
                    && (text(action.get("outcome"), "attacker_defeat") || text(action.get("outcome"), "attacker_victory"))
                    && (text(action.get("status"), "submitted_pending") || text(action.get("status"), "applied"))) return java.util.Optional.of(action);
        }
        return java.util.Optional.empty();
    }
    private static boolean legal(Obj surrender) {
        return surrender != null && text(surrender.get("outcome"), "attacker_defeat") && text(surrender.get("hostage_variant"), "none")
                && truth(surrender.get("context_constructed")) && truth(surrender.get("native_validator_passed"))
                && truth(surrender.get("available")) && truth(surrender.get("auto_accept_observable")) && truth(surrender.get("auto_accept"));
    }
    private static boolean absolute(Obj options, Value score) {
        BigInteger value = integer(score), defender = integer(options.get("defender_war_score"));
        return truth(options.get("absolute_war_scores_observable")) && equal(options.get("attacker_war_score"), score)
                && value != null && defender != null && defender.equals(value.negate());
    }
    private static boolean sameFrame(Obj snapshot, Obj row) {
        Obj diagnostics = object(snapshot.get("diagnostics"));
        return equal(row.get("queried_snapshot_id"), snapshot.get("snapshot_id")) && equal(row.get("queried_revision"), snapshot.get("revision"))
                && equal(row.get("queried_native_revision"), snapshot.get("native_revision"))
                && equal(row.get("queried_connection_generation"), diagnostics == null ? null : diagnostics.get("connection_generation"))
                && equal(row.get("episode_run_id"), snapshot.get("episode_run_id"));
    }
    private static Obj first(Value raw, int id) { for (Obj row : rows(raw)) if (is(row.get("war_id"), id)) return row; return null; }
    private static Obj unique(Value raw, int id) { List<Obj> rows = rows(raw).stream().filter(row -> is(row.get("war_id"), id)).toList(); return rows.size() == 1 ? rows.getFirst() : null; }
    private static List<Obj> rows(Value raw) {
        if (raw == null || raw == Nil.INSTANCE) return List.of();
        List<Obj> rows = new ArrayList<>(); for (Value value : OpportunityJson.array(raw, "actual complete surrender rows")) rows.add(OpportunityJson.object(value, "actual surrender row")); return List.copyOf(rows);
    }
    private static Obj object(Value value) { return value == null || value == Nil.INSTANCE ? null : OpportunityJson.object(value, "actual surrender object"); }
    private static boolean equal(Value a, Value b) { return a != null && b != null && a.equals(b); }
    private static boolean truth(Value value) { return value != null && value != Nil.INSTANCE && OpportunityJson.bool(value, "actual surrender Boolean"); }
    private static boolean text(Value value, String expected) { return value != null && value != Nil.INSTANCE && OpportunityJson.text(value, "actual surrender text").equals(expected); }
    private static BigInteger integer(Value value) { return value == null || value == Nil.INSTANCE ? null : OpportunityJson.integer(value, "actual surrender integer"); }
    private static boolean is(Value value, long expected) { BigInteger integer = integer(value); return integer != null && integer.equals(BigInteger.valueOf(expected)); }
    private static boolean atLeast(Value value, long bound) { BigInteger integer = integer(value); return integer != null && integer.compareTo(BigInteger.valueOf(bound)) >= 0; }
    private static boolean atMost(Value value, long bound) { BigInteger integer = integer(value); return integer != null && integer.compareTo(BigInteger.valueOf(bound)) <= 0; }
}
