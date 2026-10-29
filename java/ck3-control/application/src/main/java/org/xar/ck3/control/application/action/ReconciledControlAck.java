package org.xar.ck3.control.application.action;

import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original received result DATA, never a submission permit. The installed domain must replay its native meaning. */
public record ReconciledControlAck(NativeActionPort.AckReceived ack) {
    public ReconciledControlAck {
        Objects.requireNonNull(ack);
        StrictJson.require(ack.nativeOk() && ack.outbound().isPresent() && ack.custody().isPresent(), "actual original successful ACK with outbound and chronology required");
    }
    public void requireMatches(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome original) {
        Objects.requireNonNull(command); Objects.requireNonNull(attempt); Objects.requireNonNull(original);
        StrictJson.require(original instanceof NativeActionPort.Unknown, "late control ACK cannot replace an already retained result");
        var unknown = (NativeActionPort.Unknown) original;
        StrictJson.require(command.operation().equals(attempt.guard().operation()) && command.sessionId().equals(attempt.guard().sessionId())
                && command.source().equals(attempt.guard().source()) && unknown.requestId().equals(attempt.requestId())
                && ack.requestId().equals(attempt.requestId()) && unknown.originalRequestPacket().length > 0
                && Arrays.equals(unknown.originalRequestPacket(), ack.outbound().orElseThrow().originalPacket()),
                "late control ACK changed the canonical original attempt/source/full outgoing packet");
        ack.custody().orElseThrow().verify(ack, attempt.guard());
    }
    /** Existing source artifact only: this lookup must not publish or repair a missing received original. */
    public ExactRef reference(ActionPorts.OutcomeArchive archive) { return archive.referenceOf(ack); }
}
