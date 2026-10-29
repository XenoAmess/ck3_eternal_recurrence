package org.xar.ck3.control.wave2.finance.feastterminal;

import java.util.Optional;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.Activity;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.CompletionStamp;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampAbsent;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampObserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampUnobserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.TerminalObserved;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.AbsentJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.BooleanObservation;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.JournalField;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Outcome;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.ParsedJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Request;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Status;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.UnknownReason;

/** Existing terminal interpretation, preserving current-row precedence and historical-cut scope. */
public final class FeastTerminalPolicy {
    private FeastTerminalPolicy() { }

    public static Outcome observe(Request request) {
        if (request.post().frameActor().isEmpty() || request.post().frameActor().orElseThrow() != request.actorId()) {
            return unknown(request, UnknownReason.HOST_FRAME_MISMATCH, new StampAbsent(), new AbsentJournal());
        }
        JournalField journal = request.post().journal();
        Optional<Activity> current = request.post().hosted().activities().stream()
                .filter(row -> row.activityId() == request.activityId()).findFirst();
        if (current.isEmpty()) {
            if (journal instanceof ParsedJournal parsed) {
                var records = parsed.value().records();
                for (int index = records.size() - 1; index >= 0; index--) {
                    NativeTerminalJournal.Cut source = records.get(index);
                    if (source.activityFullId() != request.activityId()
                            || source.instanceGeneration() != (request.activityId() >>> 24)
                            || Integer.toUnsignedLong(source.hostCharacterId()) != request.actorId()) continue;
                    BooleanObservation completed = observation(source.completedRaw());
                    BooleanObservation invalidated = observation(source.invalidatedRaw());
                    if (completed != BooleanObservation.TRUE && invalidated != BooleanObservation.TRUE) continue;
                    CompletionStamp stamp = source.completionStampRaw().isPresent()
                            ? new StampObserved(source.completionStampRaw().orElseThrow()) : new StampUnobserved();
                    return new Outcome(request.activityId(), request.actorId(), request.post().revision(), request.post().dateRaw(),
                            status(completed, invalidated), source.completedRaw().isPresent() && source.invalidatedRaw().isPresent(),
                            completed, invalidated, Optional.empty(), stamp, Optional.of(source), journal, request.post().provenance());
                }
            }
            return unknown(request, UnknownReason.ACTIVITY_NOT_OBSERVED, new StampAbsent(), journal);
        }
        Activity row = current.orElseThrow();
        if (row.hostCharacterId() != request.actorId() || !row.activityTypeKey().equals("activity_feast")) {
            return unknown(request, UnknownReason.ACTIVITY_IDENTITY_MISMATCH, new StampAbsent(), journal);
        }
        if (!(row.terminal() instanceof TerminalObserved terminal)) {
            return unknown(request, UnknownReason.TERMINAL_FLAGS_UNOBSERVED, row.completionStamp(), journal);
        }
        BooleanObservation completed = terminal.completed() ? BooleanObservation.TRUE : BooleanObservation.FALSE;
        BooleanObservation invalidated = terminal.invalidated() ? BooleanObservation.TRUE : BooleanObservation.FALSE;
        return new Outcome(request.activityId(), request.actorId(), request.post().revision(), request.post().dateRaw(),
                status(completed, invalidated), true, completed, invalidated, Optional.empty(), row.completionStamp(),
                Optional.empty(), journal, request.post().provenance());
    }

    private static Outcome unknown(Request request, UnknownReason reason, CompletionStamp stamp, JournalField journal) {
        return new Outcome(request.activityId(), request.actorId(), request.post().revision(), request.post().dateRaw(),
                Status.UNKNOWN, false, BooleanObservation.UNKNOWN, BooleanObservation.UNKNOWN, Optional.of(reason), stamp,
                Optional.empty(), journal, request.post().provenance());
    }
    private static BooleanObservation observation(Optional<Integer> value) {
        return value.isEmpty() ? BooleanObservation.UNKNOWN : value.orElseThrow() == 0 ? BooleanObservation.FALSE : BooleanObservation.TRUE;
    }
    private static Status status(BooleanObservation completed, BooleanObservation invalidated) {
        if (completed == BooleanObservation.TRUE && invalidated == BooleanObservation.TRUE) return Status.COMPLETED_AND_INVALIDATED;
        if (completed == BooleanObservation.TRUE) return Status.COMPLETED;
        if (invalidated == BooleanObservation.TRUE) return Status.INVALIDATED;
        return Status.ONGOING;
    }
}
