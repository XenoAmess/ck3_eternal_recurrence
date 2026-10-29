package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.OrdinaryHistory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.contracts.NativeInteractionRoles;

/** Named projection of the original actual snapshot/query containers; no acceptance inferred from score. */
public final class WarExitEvidence {
    private WarExitEvidence() { }
    public enum Side { ATTACKER, DEFENDER }
    public enum Outcome { ATTACKER_VICTORY, WHITE_PEACE, ATTACKER_DEFEAT }
    public record War(int warId, Side playerSide, boolean primaryLeader, Optional<Integer> score,
                      Optional<Integer> opponent, List<Integer> targetedTitleIds, ObjectNode original) {
        public War {
            require(warId > 0, "positive original planner WarID required"); Objects.requireNonNull(playerSide);
            Objects.requireNonNull(score); Objects.requireNonNull(opponent);
            targetedTitleIds = List.copyOf(targetedTitleIds); original = original.deepCopy();
        }
        @Override public ObjectNode original() { return original.deepCopy(); }
    }
    public sealed interface Response permits FinalResponse, UnknownResponse { }
    public record FinalResponse(int statusRaw, boolean wouldAcceptNow) implements Response {
        public FinalResponse { require(statusRaw >= 0 && statusRaw <= 2 && wouldAcceptNow == (statusRaw != 2),
                "native recipient decision differs from response"); }
    }
    public record UnknownResponse() implements Response { }
    public record Option(Outcome outcome, String hostageVariant, boolean contextConstructed,
                         Optional<Boolean> nativeValidator, boolean available, boolean acceptanceObservable,
                         Optional<Long> acceptanceRaw, boolean autoAcceptObservable, Optional<Boolean> autoAccept,
                         Response response, NativeInteractionRoles recipientContext) {
        public Option {
            Objects.requireNonNull(outcome); Objects.requireNonNull(hostageVariant); Objects.requireNonNull(nativeValidator);
            Objects.requireNonNull(acceptanceRaw); Objects.requireNonNull(autoAccept); Objects.requireNonNull(response);
            Objects.requireNonNull(recipientContext);
            require(acceptanceObservable == acceptanceRaw.isPresent(), "raw acceptance observability differs");
            require(autoAcceptObservable == autoAccept.isPresent(), "autoaccept observability differs");
            require(available == (contextConstructed && nativeValidator.orElse(false)), "native availability differs from validator");
            require(contextConstructed || !(recipientContext instanceof NativeInteractionRoles.Observed), "roles require constructed context");
            require(!(recipientContext instanceof NativeInteractionRoles.Unavailable) || response instanceof UnknownResponse,
                    "unavailable roles cannot bind a final answer");
        }
        public boolean nativeLegal() { return !(recipientContext instanceof NativeInteractionRoles.Unavailable)
                && contextConstructed && nativeValidator.orElse(false) && available; }
        public boolean finalAccepts() { return response instanceof FinalResponse result && result.wouldAcceptNow(); }
        public boolean positiveQuote() { return acceptanceObservable && acceptanceRaw.orElse(0L) > 0; }
    }
    public record Options(int warId, Side playerSide, boolean primaryLeader, int score, Optional<Integer> durationDays,
                          boolean cbPresent, Optional<String> cbKey, Optional<Integer> cbDatabaseIndex,
                          boolean allowsWhitePeace, Option whitePeace, Option surrender, ObjectNode original) {
        public Options {
            require(warId > 0, "positive original planner WarID required"); Objects.requireNonNull(playerSide);
            Objects.requireNonNull(durationDays); Objects.requireNonNull(cbKey); Objects.requireNonNull(cbDatabaseIndex);
            Objects.requireNonNull(whitePeace); Objects.requireNonNull(surrender); original = original.deepCopy();
        }
        @Override public ObjectNode original() { return original.deepCopy(); }
    }

    public static ObjectNode snapshot(PlanningRequest request) {
        return object(OpportunityJson.toNode(request.observations().snapshot()), "actual snapshot");
    }

    public static List<War> wars(ObjectNode snapshot) {
        JsonNode rows = snapshot.get("active_wars"); require(rows != null && rows.isArray(), "actual active_wars required");
        List<War> result = new ArrayList<>(); Set<Integer> ids = new HashSet<>();
        for (JsonNode value : rows) {
            ObjectNode row = object(value, "active war"); int id = positive(row.get("war_id"));
            require(ids.add(id), "duplicate active WarID");
            List<Integer> targets = new ArrayList<>(); JsonNode rawIds = row.get("targeted_title_ids");
            require(rawIds != null && rawIds.isArray() && rawIds.size() <= 4096, "native target IDs required");
            for (JsonNode target : rawIds) { targets.add(int32(target)); }
            require(new HashSet<>(targets).size() == targets.size(), "duplicate native target TitleID");
            result.add(new War(id, side(row.get("player_side")), nullableBool(row.get("player_is_primary_war_leader")).orElse(false),
                    nullableInt(row.get("player_relative_war_score")), nullableInt(row.get("primary_opponent_character_id")), targets, row));
        }
        return List.copyOf(result);
    }

    public static Optional<Options> currentOptions(ObjectNode snapshot, int warId) {
        JsonNode rows = snapshot.get("war_termination_options");
        if (rows == null || rows.isNull()) return Optional.empty();
        require(rows.isArray(), "termination option rows must be an array");
        ObjectNode selected = null;
        for (JsonNode value : rows) {
            ObjectNode row = object(value, "termination option row");
            if (positive(row.get("war_id")) == warId) { require(selected == null, "duplicate termination WarID"); selected = row; }
        }
        if (selected == null || !sameFrame(snapshot, selected, "episode_run_id")) return Optional.empty();
        // Use the existing shared complete packet/cache contract before this named policy projection.
        NativeTerminationOptions.fromCache(selected, warId);
        return Optional.of(projectOptions(selected, warId));
    }

    /** For negative-query classification only; this unbound history projection cannot pass currentOptions. */
    public static Options historicalOptions(ObjectNode value, int warId) {
        ObjectNode packet = value.deepCopy();
        for (String field : List.of("query_sequence", "queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_connection_generation", "episode_run_id")) packet.remove(field);
        return projectOptions(NativeTerminationOptions.normalizeNativePacket(packet, warId).normalized(), warId);
    }

    private static Options projectOptions(ObjectNode selected, int warId) {
        ObjectNode choices = object(selected.get("options"), "termination options");
        JsonNode cbValue = selected.get("active_casus_belli_identity");
        Optional<String> cbKey = Optional.empty(); Optional<Integer> cbIndex = Optional.empty();
        if (cbValue != null && !cbValue.isNull()) {
            ObjectNode cb = object(cbValue, "active CB identity");
            cbKey = Optional.of(StrictJson.text(cb.get("canonical_key"))); cbIndex = Optional.of(int32(cb.get("database_index")));
        }
        return new Options(warId, side(selected.get("player_side")), bool(selected.get("player_is_primary_war_leader")),
                int32(selected.get("player_relative_war_score")), nullableInt(selected.get("war_duration_days")),
                nullableBool(selected.get("active_casus_belli_present")).orElse(false), cbKey, cbIndex,
                nullableBool(selected.get("cb_allows_white_peace")).orElse(false),
                option(choices.get("white_peace")), option(choices.get("surrender")), selected);
    }

    public static boolean sameFrame(ObjectNode snapshot, ObjectNode query, String episodeField) {
        ObjectNode diagnostics = object(snapshot.get("diagnostics"), "native diagnostics");
        return exactText(snapshot.get("snapshot_id"), query.get("queried_snapshot_id"))
                && exactInteger(snapshot.get("revision"), query.get("queried_revision"))
                && exactInteger(snapshot.get("native_revision"), query.get("queried_native_revision"))
                && exactInteger(diagnostics.get("connection_generation"), query.get("queried_connection_generation"))
                && exactText(snapshot.get("episode_run_id"), query.get(episodeField));
    }

    public static List<ObjectNode> historySinceRestore(PlanningRequest request) {
        List<ObjectNode> rows = new ArrayList<>();
        for (OpportunityJson.Obj value : OrdinaryHistory.collect(request.observations().history()).rows()) {
            ObjectNode row = object(OpportunityJson.toNode(value), "original command history");
            if (textIs(row.get("command"), "restore-checkpoint") && OrdinaryHistory.successful(value)) rows.clear(); else rows.add(row);
        }
        return List.copyOf(rows);
    }

    public static List<ObjectNode> effectiveHistorySinceRestore(PlanningRequest request) {
        List<ObjectNode> rows = new ArrayList<>();
        for (OpportunityJson.Obj value : OrdinaryHistory.collect(request.observations().history()).rows()) {
            ObjectNode row = object(OpportunityJson.toNode(value), "original command history").deepCopy();
            Optional<String> command = OrdinaryHistory.effectiveCommand(value);
            if (command.filter("restore-checkpoint"::equals).isPresent() && OrdinaryHistory.successful(value)) { rows.clear(); continue; }
            if (command.isPresent()) row.put("command", command.orElseThrow()); else row.putNull("command");
            Optional<OpportunityJson.Obj> result = OrdinaryHistory.effectiveCommandResult(value);
            if (result.isPresent()) row.set("result", OpportunityJson.toNode(result.orElseThrow())); else row.putNull("result");
            rows.add(row);
        }
        return List.copyOf(rows);
    }

    public static Optional<ObjectNode> currentQuery(List<ObjectNode> history, ObjectNode snapshot, String step, String episodeField) {
        for (int i = history.size() - 1; i >= 0; i--) {
            ObjectNode row = history.get(i); JsonNode result = row.get("result");
            if (textIs(row.get("command"), step) && trueValue(row.get("ok")) && result instanceof ObjectNode query
                    && sameFrame(snapshot, query, episodeField)) return Optional.of(query.deepCopy());
        }
        return Optional.empty();
    }

    public static boolean priorTerminalSubmission(List<ObjectNode> history, int warId) {
        for (ObjectNode row : history) {
            boolean terminal = textIs(row.get("command"), "offer-white-peace-" + warId)
                    || textIs(row.get("command"), "surrender-war-" + warId);
            if (terminal && !falseValue(row.get("ok"))) return true;
        }
        return false;
    }

    public record SurrenderState(boolean sameDayPending, ObjectNode source) {
        public SurrenderState { source = source.deepCopy(); }
        @Override public ObjectNode source() { return source.deepCopy(); }
    }
    public static Optional<SurrenderState> surrenderState(List<ObjectNode> history, ObjectNode snapshot, int warId) {
        int date = int32(snapshot.get("date_raw")); String episode = StrictJson.text(snapshot.get("episode_run_id"));
        for (int i = history.size() - 1; i >= 0; i--) {
            ObjectNode row = history.get(i);
            if (!textIs(row.get("command"), "surrender-war-" + warId) || !trueValue(row.get("ok"))) continue;
            JsonNode result = row.get("result"); JsonNode value = result == null ? null : result.get("war_termination_result");
            if (!(value instanceof ObjectNode action) || !integerIs(action.get("war_id"), warId)
                    || !textIs(action.get("outcome"), "attacker_defeat") || !textIs(action.get("episode_run_id"), episode)
                    || !(textIs(action.get("status"), "submitted_pending") || textIs(action.get("status"), "applied"))) continue;
            JsonNode submittedValue = action.get("submitted_date_raw");
            if (submittedValue == null || !submittedValue.isIntegralNumber()) return Optional.of(new SurrenderState(false, action));
            int submitted = int32(submittedValue);
            return Optional.of(new SurrenderState(date == submitted && textIs(action.get("status"), "submitted_pending"), action));
        }
        return Optional.empty();
    }

    /** Exact original 30-day proposal cooldown; known applied and pending remain distinguishable. */
    public record Cooldown(String status, String actionStatus, Optional<Integer> submittedDateRaw,
                           Optional<Long> elapsedRaw, ObjectNode source) {
        public Cooldown { Objects.requireNonNull(status); Objects.requireNonNull(actionStatus);
            Objects.requireNonNull(submittedDateRaw); Objects.requireNonNull(elapsedRaw); source = source.deepCopy(); }
        @Override public ObjectNode source() { return source.deepCopy(); }
    }
    public static Optional<Cooldown> whitePeaceCooldown(List<ObjectNode> history, ObjectNode snapshot, int warId) {
        int date = int32(snapshot.get("date_raw")); String episode = StrictJson.text(snapshot.get("episode_run_id"));
        for (int i = history.size() - 1; i >= 0; i--) {
            ObjectNode row = history.get(i);
            if (!textIs(row.get("command"), "offer-white-peace-" + warId) || !trueValue(row.get("ok"))) continue;
            JsonNode result = row.get("result"); JsonNode action = result == null ? null : result.get("war_termination_result");
            if (!(action instanceof ObjectNode material) || !integerIs(material.get("war_id"), warId)
                    || !textIs(material.get("outcome"), "white_peace") || !textIs(material.get("episode_run_id"), episode)
                    || !(textIs(material.get("status"), "submitted_pending") || textIs(material.get("status"), "applied"))) continue;
            String status = StrictJson.text(material.get("status"));
            if (material.get("submitted_date_raw") == null || !material.get("submitted_date_raw").isIntegralNumber())
                return Optional.of(new Cooldown("malformed_submission_history", status, Optional.empty(), Optional.empty(), material));
            int submitted = int32(material.get("submitted_date_raw")); long elapsed = (long) date - submitted;
            if (elapsed < 30L * 24) return Optional.of(new Cooldown("cooldown", status, Optional.of(submitted), Optional.of(elapsed), material));
            return Optional.empty();
        }
        return Optional.empty();
    }

    private static Option option(JsonNode value) {
        ObjectNode row = object(value, "native termination option");
        String outcome = StrictJson.text(row.get("outcome"));
        Outcome typed = switch (outcome) {
            case "attacker_victory" -> Outcome.ATTACKER_VICTORY;
            case "white_peace" -> Outcome.WHITE_PEACE;
            case "attacker_defeat" -> Outcome.ATTACKER_DEFEAT;
            default -> throw new IllegalArgumentException("unknown native termination outcome");
        };
        boolean acceptanceObserved = bool(row.get("ai_acceptance_observable")); Optional<Long> raw = Optional.empty();
        JsonNode acceptance = row.get("ai_acceptance");
        if (acceptanceObserved) {
            ObjectNode fixed = object(acceptance, "native acceptance fixed value");
            require(integerIs(fixed.get("scale"), 100_000), "native acceptance scale differs");
            raw = Optional.of(StrictJson.integer(fixed.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE));
        } else { require(acceptance != null && acceptance.isNull(), "unobserved native quote must be null"); }
        ObjectNode response = object(row.get("recipient_response"), "recipient response"); Response typedResponse;
        if (textIs(response.get("status"), "available")) {
            typedResponse = new FinalResponse((int) StrictJson.integer(response.get("decision_status_raw"), 0, 2), bool(response.get("would_accept_now")));
        } else {
            require(textIs(response.get("status"), "unavailable") && response.get("decision_status_raw") != null
                    && response.get("decision_status_raw").isNull() && response.get("would_accept_now") != null
                    && response.get("would_accept_now").isNull(), "unavailable response must retain null fields");
            typedResponse = new UnknownResponse();
        }
        return new Option(typed, StrictJson.text(row.get("hostage_variant")), bool(row.get("context_constructed")),
                nullableBool(row.get("native_validator_passed")), bool(row.get("available")), acceptanceObserved, raw,
                bool(row.get("auto_accept_observable")), nullableBool(row.get("auto_accept")), typedResponse,
                NativeInteractionRoles.fromOption(row));
    }

    static ObjectNode object(JsonNode value, String field) { require(value instanceof ObjectNode, field + " must be object"); return (ObjectNode) value; }
    static boolean trueValue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    static boolean falseValue(JsonNode value) { return value != null && value.isBoolean() && !value.booleanValue(); }
    static boolean textIs(JsonNode value, String text) { return value != null && value.isTextual() && text.equals(value.textValue()); }
    static boolean integerIs(JsonNode value, long integer) { return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(BigInteger.valueOf(integer)); }
    static int int32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    static int positive(JsonNode value) { return (int) StrictJson.integer(value, 1, Integer.MAX_VALUE); }
    static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "exact native boolean required"); return value.booleanValue(); }
    private static Optional<Integer> nullableInt(JsonNode value) { return value == null || value.isNull() ? Optional.empty() : Optional.of(int32(value)); }
    private static Optional<Boolean> nullableBool(JsonNode value) { require(value != null, "explicit nullable native boolean required"); return value.isNull() ? Optional.empty() : Optional.of(bool(value)); }
    private static boolean exactText(JsonNode expected, JsonNode actual) { return expected != null && actual != null && expected.isTextual() && actual.isTextual() && expected.equals(actual); }
    private static boolean exactInteger(JsonNode expected, JsonNode actual) { return expected != null && actual != null && expected.isIntegralNumber() && actual.isIntegralNumber() && expected.bigIntegerValue().equals(actual.bigIntegerValue()); }
    private static Side side(JsonNode value) {
        String key = StrictJson.text(value);
        return switch (key) { case "attacker" -> Side.ATTACKER; case "defender" -> Side.DEFENDER;
            default -> throw new IllegalArgumentException("unknown native player war side"); };
    }
}
