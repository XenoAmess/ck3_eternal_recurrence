package org.xar.ck3.control.wave2.events.occurrence;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Counts factual selections. PreparedHistory indexes the complete supplied immutable lineage once. */
public final class EventOccurrence {
    public static final String QUERY_STEP = "query-current-event-window-context-v1";
    private EventOccurrence() { }
    public enum Status { AVAILABLE, UNAVAILABLE }
    public enum Reason {
        EVENT_HISTORY_UNAVAILABLE, CONFLICTING_EVENT_QUERY_IDENTITY, UNVERIFIED_HISTORICAL_EVENT_SELECTION,
        HISTORICAL_SELECTION_FRAME_UNAVAILABLE, HISTORICAL_SELECTION_EVENT_IDENTITY_UNAVAILABLE;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface HistoryItem permits IgnoredItem, CommandRow { }
    public record IgnoredItem() implements HistoryItem { }
    public record TypedCharacter(String status, String typeKey, String identityStatus, String identityKind,
                                  BigInteger characterId) {
        public BigInteger availableCharacterId() {
            return "available".equals(status) && "character".equals(typeKey)
                && "available".equals(identityStatus) && "character".equals(identityKind)
                && positive(characterId) ? characterId : null;
        }
    }
    public record EventContext(String status, BigInteger currentEventInstanceId, BigInteger snapshotRevision,
                                BigInteger dateRaw, String eventDefinitionKey, TypedCharacter rootScope) { }
    public record EventSelection(String status, Boolean postconditionVerified, BigInteger selectedOptionNumber,
                                  BigInteger selectedNativeOptionIndex, BigInteger newEventInstanceId,
                                  BigInteger oldEventInstanceId, String startingSnapshotId, BigInteger startingRevision) { }
    public record CommandResult(String step, Boolean accepted, EventContext context,
                                 BigInteger currentEventInstanceId, BigInteger queriedNativeRevision,
                                 BigInteger snapshotRevision, BigInteger dateRaw, BigInteger queriedRevision,
                                 String queriedSnapshotId, EventSelection eventSelection) { }
    public record CommandRow(String command, Boolean ok, CommandResult result) implements HistoryItem { }
    public record Request(String eventDefinitionKey, BigInteger playedCharacterId, Optional<List<HistoryItem>> commands) {
        public Request {
            StrictJson.text(eventDefinitionKey);
            Objects.requireNonNull(playedCharacterId, "playedCharacterId");
            StrictJson.require(playedCharacterId.signum() > 0, "played character identity must be positive");
            Objects.requireNonNull(commands, "commands");
            commands = commands.map(List::copyOf);
        }
    }
    public record Result(String eventDefinitionKey, BigInteger playedCharacterId, Status status, Integer count, Reason reason) {
        public Result {
            StrictJson.text(eventDefinitionKey);
            Objects.requireNonNull(playedCharacterId, "playedCharacterId");
            StrictJson.require(playedCharacterId.signum() > 0, "played character identity must be positive");
            Objects.requireNonNull(status, "status");
            StrictJson.require(status == Status.AVAILABLE ? count != null && count >= 0 && reason == null : count == null && reason != null,
                "occurrence result branch");
        }
        public boolean actionAuthorized() { return false; }
    }
    private record Frame(BigInteger instance, String snapshotId, BigInteger publicRevision) { }
    private record Identity(String eventKey, BigInteger actor) { }

    /**
     * No cache or authority is created here. A caller retaining this value must retain the complete
     * parsed source and enforce its existing source/frame/writer token before and after each read.
     * All rows remain available, including rows unrelated to a particular lookup.
     */
    public static final class PreparedHistory {
        private final Optional<List<HistoryItem>> retained;
        private final Map<Identity,Integer> counts;
        private final Reason refusal;
        private PreparedHistory(Optional<List<HistoryItem>> retained, Map<Identity,Integer> counts, Reason refusal) {
            this.retained = retained; this.counts = Map.copyOf(counts); this.refusal = refusal;
        }
        public Optional<List<HistoryItem>> retainedCommands() { return retained; }
        public Result count(String eventDefinitionKey, BigInteger playedCharacterId) {
            Request request = new Request(eventDefinitionKey, playedCharacterId, retained);
            if (refusal != null) return unavailable(request, refusal);
            return new Result(eventDefinitionKey, playedCharacterId, Status.AVAILABLE,
                    counts.getOrDefault(new Identity(eventDefinitionKey, playedCharacterId), 0), null);
        }
    }

    /** Existing single-request entry now consumes the same sole reducer used by prepared reads. */
    public static Result count(Request request) {
        Objects.requireNonNull(request, "request");
        return prepare(request.commands()).count(request.eventDefinitionKey(), request.playedCharacterId());
    }

    /** Original two passes, in their original failure order, covering the entire history. */
    public static PreparedHistory prepare(Optional<List<HistoryItem>> commands) {
        Objects.requireNonNull(commands, "commands");
        Optional<List<HistoryItem>> retained = commands.map(List::copyOf);
        if (retained.isEmpty()) return refused(retained, Reason.EVENT_HISTORY_UNAVAILABLE);
        List<HistoryItem> history = retained.orElseThrow();
        Map<Frame,Identity> queries = new HashMap<>();
        for (HistoryItem item : history) {
            if (!(item instanceof CommandRow row) || !Boolean.TRUE.equals(row.ok()) || row.result() == null) continue;
            CommandResult result = row.result(); EventContext context = result.context();
            if (!QUERY_STEP.equals(result.step()) || !Boolean.TRUE.equals(result.accepted()) || context == null
                    || !"available".equals(context.status())) continue;
            BigInteger actor = context.rootScope() == null ? null : context.rootScope().availableCharacterId();
            if (!positive(context.currentEventInstanceId()) || !positive(context.snapshotRevision())
                    || result.queriedRevision() == null || result.queriedRevision().signum() < 0
                    || result.queriedSnapshotId() == null || result.queriedSnapshotId().isEmpty()
                    || context.eventDefinitionKey() == null || context.eventDefinitionKey().isEmpty() || actor == null
                    || !Objects.equals(result.currentEventInstanceId(), context.currentEventInstanceId())
                    || !Objects.equals(result.queriedNativeRevision(), context.snapshotRevision())
                    || !Objects.equals(result.snapshotRevision(), context.snapshotRevision())
                    || !Objects.equals(result.dateRaw(), context.dateRaw())) continue;
            Frame frame = new Frame(context.currentEventInstanceId(), result.queriedSnapshotId(), result.queriedRevision());
            Identity identity = new Identity(context.eventDefinitionKey(), actor);
            Identity previous = queries.putIfAbsent(frame, identity);
            if (previous != null && !previous.equals(identity)) return refused(retained, Reason.CONFLICTING_EVENT_QUERY_IDENTITY);
        }
        HashSet<Frame> observed = new HashSet<>(); Map<Identity,Integer> counts = new HashMap<>();
        for (HistoryItem item : history) {
            if (!(item instanceof CommandRow row)) continue;
            Optional<BigInteger> optionNumber = parseOptionStep(row.command());
            if (optionNumber.isEmpty()) continue;
            CommandResult result = row.result(); EventSelection selected = result == null ? null : result.eventSelection();
            if (!Boolean.TRUE.equals(row.ok()) || result == null || !Boolean.TRUE.equals(result.accepted()) || selected == null
                    || !"event_instance_advanced".equals(selected.status()) || !Boolean.TRUE.equals(selected.postconditionVerified())
                    || !optionNumber.orElseThrow().equals(selected.selectedOptionNumber())
                    || !optionNumber.orElseThrow().subtract(BigInteger.ONE).equals(selected.selectedNativeOptionIndex())
                    || Objects.equals(selected.newEventInstanceId(), selected.oldEventInstanceId()))
                return refused(retained, Reason.UNVERIFIED_HISTORICAL_EVENT_SELECTION);
            if (!positive(selected.oldEventInstanceId()) || selected.startingSnapshotId() == null || selected.startingRevision() == null)
                return refused(retained, Reason.HISTORICAL_SELECTION_FRAME_UNAVAILABLE);
            Frame frame = new Frame(selected.oldEventInstanceId(), selected.startingSnapshotId(), selected.startingRevision());
            Identity identity = queries.get(frame);
            if (identity == null) return refused(retained, Reason.HISTORICAL_SELECTION_EVENT_IDENTITY_UNAVAILABLE);
            if (observed.add(frame)) counts.merge(identity, 1, Math::addExact);
        }
        return new PreparedHistory(retained, counts, null);
    }
    private static PreparedHistory refused(Optional<List<HistoryItem>> retained, Reason reason) {
        return new PreparedHistory(retained, Map.of(), reason);
    }
    public static Optional<BigInteger> parseOptionStep(String command) {
        String prefix = "select-event-option-";
        if (command == null || !command.startsWith(prefix)) return Optional.empty();
        String suffix = command.substring(prefix.length());
        if (suffix.isEmpty()) return Optional.empty();
        for (int index = 0; index < suffix.length(); index++) if (suffix.charAt(index) < '0' || suffix.charAt(index) > '9') return Optional.empty();
        BigInteger value = new BigInteger(suffix); return value.signum() > 0 ? Optional.of(value) : Optional.empty();
    }
    private static Result unavailable(Request request, Reason reason) {
        return new Result(request.eventDefinitionKey(), request.playedCharacterId(), Status.UNAVAILABLE, null, reason);
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
}
