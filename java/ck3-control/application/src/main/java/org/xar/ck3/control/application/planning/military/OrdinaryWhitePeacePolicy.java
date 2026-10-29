package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The four original native-driver proposal gates. A DATA decision grants no submit or settlement authority. */
public final class OrdinaryWhitePeacePolicy {
    private OrdinaryWhitePeacePolicy() { }
    public enum Variant {
        DEFENDER_DE_JURE("defender_de_jure_white_peace"), DEFENDER_MINOR_RELIGIOUS("defender_minor_religious_white_peace"),
        DE_JURE_NO_SAFE_ROUTE("de_jure_no_safe_route"), CLAIM_CB("claim_cb");
        private final String wire; Variant(String wire) { this.wire = wire; } public String wire() { return wire; }
    }
    public enum Reason {
        SNAPSHOT_NOT_PAUSED, WAR_NOT_ACTIVE, TERMINATION_OPTIONS_MISSING, TERMINATION_TERMS_V1_MISSING,
        TERMINATION_EVIDENCE_NOT_SAME_FRAME, CLAIM_CB_WHITE_PEACE_BASE_GATE_FAILED,
        WHITE_PEACE_RECIPIENT_OR_VALIDATOR_GATE_FAILED, CLAIM_DISPOSITION_V1_GATE_FAILED,
        DE_JURE_WHITE_PEACE_GATE_FAILED, DEFENDER_DE_JURE_WHITE_PEACE_NOT_READY,
        DEFENDER_MINOR_RELIGIOUS_WHITE_PEACE_NOT_READY;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Decision permits Ready, Unavailable { boolean ready(); }
    public record Ready(Variant variant, Obj war, Obj options, Optional<Obj> terms, Obj whitePeace) implements Decision {
        public Ready { Objects.requireNonNull(variant); Objects.requireNonNull(war); Objects.requireNonNull(options); Objects.requireNonNull(terms); Objects.requireNonNull(whitePeace); }
        public boolean ready() { return true; }
        public Obj evidence() {
            var fields = new java.util.LinkedHashMap<String,Value>();
            if (variant != Variant.CLAIM_CB) fields.put("variant", new Text(variant.wire()));
            fields.put("war", war); fields.put("options", options); terms.ifPresent(value -> fields.put("terms", value)); fields.put("white_peace", whitePeace);
            return new Obj(fields);
        }
    }
    public record Unavailable(List<Reason> orderedReasons) implements Decision {
        public Unavailable { orderedReasons = List.copyOf(orderedReasons); StrictJson.require(orderedReasons.size() == 4, "all four ordered original proposal outcomes required"); }
        public boolean ready() { return false; }
        public String reason() { return "defender_de_jure=" + orderedReasons.get(0).wire() + "; defender_minor_religious=" + orderedReasons.get(1).wire()
                + "; de_jure=" + orderedReasons.get(2).wire() + "; claim=" + orderedReasons.get(3).wire(); }
    }
    private record Attempt(Optional<Ready> ready, Reason failure) {
        private Attempt { Objects.requireNonNull(ready); StrictJson.require(ready.isPresent() != (failure != null), "one policy branch result required"); }
        private static Attempt no(Reason reason) { return new Attempt(Optional.empty(), Objects.requireNonNull(reason)); }
        private static Attempt yes(Ready value) { return new Attempt(Optional.of(value), null); }
    }
    public static Decision evaluate(Obj snapshot, int fullWarId) {
        StrictJson.require(fullWarId > 0, "white peace requires the positive complete public WarID"); Objects.requireNonNull(snapshot);
        List<Reason> failures = new ArrayList<>();
        for (int branch = 0; branch < 4; branch++) {
            Attempt choice = switch (branch) { case 0 -> defender(snapshot, fullWarId, false); case 1 -> defender(snapshot, fullWarId, true);
                case 2 -> deJure(snapshot, fullWarId); case 3 -> claim(snapshot, fullWarId); default -> throw new IllegalStateException("finite policy branch"); };
            if (choice.ready().isPresent()) return choice.ready().orElseThrow(); failures.add(choice.failure());
        }
        return new Unavailable(failures);
    }
    /** The actual first-phase claimant gate. It requests terms only after the shared source options/recipient gate. */
    public static boolean needsClaimTerms(Obj snapshot, int fullWarId) {
        StrictJson.require(fullWarId > 0, "claim terms require the positive complete WarID");
        if (!truth(snapshot.get("paused"))) return false;
        Obj war = first(snapshot.get("active_wars"), fullWarId), options = unique(snapshot.get("war_termination_options"), fullWarId);
        return war != null && options != null && sameFrame(snapshot, options) && claimProposerBase(war, options)
                && claimRecipientGate(white(options));
    }
    /** Historical classification only: no same-frame check, fresh lease, Ready decision or submit authority. */
    public static boolean historicalOptionsRequireRefresh(Obj actualWar, Obj historicalOptions) {
        Objects.requireNonNull(actualWar); Objects.requireNonNull(historicalOptions);
        return claimProposerBase(actualWar, historicalOptions) && claimRecipientGate(white(historicalOptions))
                || deJureGate(actualWar, historicalOptions);
    }
    /** Explicit JSON tuple domain for differential regression against the original producer. */
    public static Arr originalTuple(Decision decision) {
        return decision instanceof Ready ready ? new Arr(List.of(new Bool(true), new Text("ready"), ready.evidence()))
                : new Arr(List.of(new Bool(false), new Text(((Unavailable) decision).reason()), new Obj(java.util.Map.of())));
    }
    private static Attempt defender(Obj snapshot, int id, boolean religious) {
        if (!truth(snapshot.get("paused"))) return Attempt.no(Reason.SNAPSHOT_NOT_PAUSED);
        Obj war = first(snapshot.get("active_wars"), id); if (war == null) return Attempt.no(Reason.WAR_NOT_ACTIVE);
        Obj options = unique(snapshot.get("war_termination_options"), id); if (options == null) return Attempt.no(Reason.TERMINATION_OPTIONS_MISSING);
        if (!sameFrame(snapshot, options)) return Attempt.no(Reason.TERMINATION_EVIDENCE_NOT_SAME_FRAME);
        Obj cb = objectOrNull(options.get("active_casus_belli_identity")), white = white(options), acceptance = white == null ? null : objectOrNull(white.get("ai_acceptance"));
        boolean valid = text(war.get("player_side"), "defender") && truth(war.get("player_is_primary_war_leader"))
                && text(options.get("player_side"), "defender") && truth(options.get("player_is_primary_war_leader"))
                && equal(options.get("player_relative_war_score"), war.get("player_relative_war_score"))
                && truth(options.get("active_casus_belli_present")) && cb != null
                && text(cb.get("canonical_key"), religious ? "minor_religious_war" : "individual_county_de_jure_cb")
                && integerEquals(cb.get("database_index"), religious ? 41 : 17) && truth(options.get("cb_allows_white_peace"))
                && legalWhite(white) && truth(white.get("ai_acceptance_observable")) && acceptance != null && positive(acceptance.get("raw"));
        if (!valid) return Attempt.no(religious ? Reason.DEFENDER_MINOR_RELIGIOUS_WHITE_PEACE_NOT_READY : Reason.DEFENDER_DE_JURE_WHITE_PEACE_NOT_READY);
        return Attempt.yes(new Ready(religious ? Variant.DEFENDER_MINOR_RELIGIOUS : Variant.DEFENDER_DE_JURE, war, options, Optional.empty(), white));
    }
    private static Attempt deJure(Obj snapshot, int id) {
        if (!truth(snapshot.get("paused"))) return Attempt.no(Reason.SNAPSHOT_NOT_PAUSED);
        Obj war = first(snapshot.get("active_wars"), id); if (war == null) return Attempt.no(Reason.WAR_NOT_ACTIVE);
        Obj options = unique(snapshot.get("war_termination_options"), id); if (options == null) return Attempt.no(Reason.TERMINATION_OPTIONS_MISSING);
        if (!sameFrame(snapshot, options)) return Attempt.no(Reason.TERMINATION_EVIDENCE_NOT_SAME_FRAME);
        Obj white = white(options);
        return deJureGate(war, options) ? Attempt.yes(new Ready(Variant.DE_JURE_NO_SAFE_ROUTE, war, options, Optional.empty(), white)) : Attempt.no(Reason.DE_JURE_WHITE_PEACE_GATE_FAILED);
    }
    private static boolean deJureGate(Obj war, Obj options) {
        Obj cb = objectOrNull(options.get("active_casus_belli_identity")), white = white(options);
        Obj acceptance = white == null ? null : objectOrNull(white.get("ai_acceptance")), response = white == null ? null : objectOrNull(white.get("recipient_response"));
        Value targets = war.get("targeted_title_ids");
        return attacker(war, options) && between(war.get("player_relative_war_score"), 1, 99) && atLeast(options.get("war_duration_days"), 180)
                && truth(options.get("active_casus_belli_present")) && cb != null && text(cb.get("canonical_key"), "individual_county_de_jure_cb")
                && integerEquals(cb.get("database_index"), 17) && targets instanceof Arr ids && ids.items().size() == 1 && positive(ids.items().getFirst())
                && truth(options.get("cb_allows_white_peace")) && legalWhite(white) && truth(white.get("ai_acceptance_observable"))
                && acceptance != null && positive(acceptance.get("raw")) && response != null && text(response.get("status"), "available") && truth(response.get("would_accept_now"));
    }
    private static Attempt claim(Obj snapshot, int id) {
        if (!truth(snapshot.get("paused"))) return Attempt.no(Reason.SNAPSHOT_NOT_PAUSED);
        Obj war = first(snapshot.get("active_wars"), id); if (war == null) return Attempt.no(Reason.WAR_NOT_ACTIVE);
        Obj options = unique(snapshot.get("war_termination_options"), id); if (options == null) return Attempt.no(Reason.TERMINATION_OPTIONS_MISSING);
        Obj terms = unique(snapshot.get("war_termination_terms"), id); if (terms == null) return Attempt.no(Reason.TERMINATION_TERMS_V1_MISSING);
        if (!sameFrame(snapshot, options) || !sameFrame(snapshot, terms)) return Attempt.no(Reason.TERMINATION_EVIDENCE_NOT_SAME_FRAME);
        Obj cb = objectOrNull(options.get("active_casus_belli_identity")), termsCb = objectOrNull(terms.get("casus_belli"));
        if (!(claimProposerBase(war, options) && cb != null
                && termsCb != null && text(termsCb.get("canonical_key"), "claim_cb") && sameInteger(termsCb.get("database_index"), cb.get("database_index"))
                )) return Attempt.no(Reason.CLAIM_CB_WHITE_PEACE_BASE_GATE_FAILED);
        Obj white = white(options), response = white == null ? null : objectOrNull(white.get("recipient_response"));
        if (!claimRecipientGate(white))
            return Attempt.no(Reason.WHITE_PEACE_RECIPIENT_OR_VALIDATOR_GATE_FAILED);
        Obj readiness = objectOrNull(terms.get("readiness")), player = objectOrNull(snapshot.get("played_character"));
        Value targets = war.get("targeted_title_ids"), claims = terms.get("claims");
        if (!(text(terms.get("status"), "available") && readiness != null && truth(readiness.get("ready"))
                && player != null && sameInteger(terms.get("claimant_character_id"), player.get("character_id")) && targets instanceof Arr titles && !titles.items().isEmpty()
                && equal(terms.get("target_title_ids"), targets) && claims instanceof Arr rows && rows.items().size() == titles.items().size()))
            return Attempt.no(Reason.CLAIM_DISPOSITION_V1_GATE_FAILED);
        for (int i = 0; i < rows.items().size(); i++) {
            Obj row = objectOrNull(rows.items().get(i)); if (row == null || !sameInteger(row.get("title_id"), titles.items().get(i)) || !truth(row.get("present")))
                return Attempt.no(Reason.CLAIM_DISPOSITION_V1_GATE_FAILED);
        }
        return Attempt.yes(new Ready(Variant.CLAIM_CB, war, options, Optional.of(terms), white));
    }
    private static boolean claimProposerBase(Obj war, Obj options) {
        Obj cb = objectOrNull(options.get("active_casus_belli_identity"));
        return attacker(war, options) && between(war.get("player_relative_war_score"), 0, 99) && atLeast(options.get("war_duration_days"), 365)
                && truth(options.get("active_casus_belli_present")) && cb != null && text(cb.get("canonical_key"), "claim_cb")
                && truth(options.get("cb_allows_white_peace"));
    }
    private static boolean claimRecipientGate(Obj white) {
        Obj response = white == null ? null : objectOrNull(white.get("recipient_response"));
        return legalWhite(white) && response != null && text(response.get("status"), "available") && truth(response.get("would_accept_now"));
    }
    private static boolean attacker(Obj war, Obj options) {
        return text(war.get("player_side"), "attacker") && truth(war.get("player_is_primary_war_leader")) && text(options.get("player_side"), "attacker")
                && truth(options.get("player_is_primary_war_leader")) && equal(options.get("player_relative_war_score"), war.get("player_relative_war_score"));
    }
    private static boolean legalWhite(Obj value) {
        return value != null && !(NativeInteractionRoles.fromOption(OpportunityJson.toNode(value)) instanceof NativeInteractionRoles.Unavailable)
                && text(value.get("outcome"), "white_peace") && text(value.get("hostage_variant"), "none")
                && truth(value.get("context_constructed")) && truth(value.get("native_validator_passed")) && truth(value.get("available"));
    }
    private static Obj white(Obj options) { Obj values = objectOrNull(options.get("options")); return values == null ? null : objectOrNull(values.get("white_peace")); }
    private static boolean sameFrame(Obj snapshot, Obj row) {
        Obj diagnostics = objectOrNull(snapshot.get("diagnostics"));
        return equal(row.get("queried_snapshot_id"), snapshot.get("snapshot_id")) && equal(row.get("queried_revision"), snapshot.get("revision"))
                && equal(row.get("queried_native_revision"), snapshot.get("native_revision"))
                && equal(row.get("queried_connection_generation"), diagnostics == null ? null : diagnostics.get("connection_generation"))
                && equal(row.get("episode_run_id"), snapshot.get("episode_run_id"));
    }
    private static Obj first(Value raw, int id) { for (Obj row : rows(raw)) if (integerEquals(row.get("war_id"), id)) return row; return null; }
    private static Obj unique(Value raw, int id) { List<Obj> found = rows(raw).stream().filter(row -> integerEquals(row.get("war_id"), id)).toList(); return found.size() == 1 ? found.getFirst() : null; }
    private static List<Obj> rows(Value value) {
        if (value == null || value == Nil.INSTANCE) return List.of(); StrictJson.require(value instanceof Arr, "actual policy collection must be an array");
        List<Obj> rows = new ArrayList<>(); for (Value row : ((Arr) value).items()) rows.add(OpportunityJson.object(row, "actual policy row")); return List.copyOf(rows);
    }
    private static Obj objectOrNull(Value value) { return value == null || value == Nil.INSTANCE ? null : OpportunityJson.object(value, "actual policy object"); }
    private static boolean equal(Value first, Value second) { return first != null && second != null && first.equals(second); }
    private static boolean truth(Value value) { if (value == null || value == Nil.INSTANCE) return false; return OpportunityJson.bool(value, "actual policy Boolean"); }
    private static boolean text(Value value, String expected) { if (value == null || value == Nil.INSTANCE) return false; return OpportunityJson.text(value, "actual policy text").equals(expected); }
    private static Optional<BigInteger> integer(Value value) { return value == null || value == Nil.INSTANCE ? Optional.empty() : Optional.of(OpportunityJson.integer(value, "actual policy integer")); }
    private static boolean integerEquals(Value value, long expected) { return integer(value).filter(number -> number.equals(BigInteger.valueOf(expected))).isPresent(); }
    private static boolean sameInteger(Value first, Value second) { var left = integer(first); var right = integer(second); return left.isPresent() && left.equals(right); }
    private static boolean positive(Value value) { return integer(value).filter(number -> number.signum() > 0).isPresent(); }
    private static boolean atLeast(Value value, long minimum) { return integer(value).filter(number -> number.compareTo(BigInteger.valueOf(minimum)) >= 0).isPresent(); }
    private static boolean between(Value value, long minimum, long maximum) { return integer(value).filter(number -> number.compareTo(BigInteger.valueOf(minimum)) >= 0 && number.compareTo(BigInteger.valueOf(maximum)) <= 0).isPresent(); }
}
