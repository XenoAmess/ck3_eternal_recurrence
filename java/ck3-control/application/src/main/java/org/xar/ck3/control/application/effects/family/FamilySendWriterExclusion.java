package org.xar.ck3.control.application.effects.family;

import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** One conservative original-writer exclusion check shared by both family-send domains. */
public final class FamilySendWriterExclusion {
    private FamilySendWriterExclusion() { }

    public static boolean exclusive(WriterContracts.Head actualHead, ActionCommand command, ActionState.Attempt attempt,
            PlanningReadReceipt before, PlanningReadReceipt after, FamilySendObservation.OriginalFrames frames,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actualHead); Objects.requireNonNull(command); Objects.requireNonNull(attempt);
        Objects.requireNonNull(frames); Objects.requireNonNull(archive);
        var first=before.original().custody().orElseThrow(); var last=after.original().custody().orElseThrow();
        first.verify(before); last.verify(after); boolean found=false;
        for (var receipt : ContinuityActionJournal.receipts(actualHead.state(), archive)) {
            if (receipt.command().actionId().equals(command.actionId())) {
                found=receipt.command().equals(command) && receipt.bodySha256().equals(ActionCodec.bodySha256(command))
                        && ActionTransitions.attempt(receipt.state()).filter(attempt::equals).isPresent();
                continue;
            }
            if (!receipt.command().origin().game().equals(command.origin().game())) continue;
            var originalAttempt=ActionTransitions.attempt(receipt.state()); if (originalAttempt.isEmpty()) continue;
            var other=originalAttempt.orElseThrow();
            if (!receipt.settled()) return false;
            if (!other.submittedAt().isBefore(first.responseReceived().observedAt())
                    && !other.submittedAt().isAfter(last.responseReceived().observedAt())) return false;
            if (other.guard().origin() instanceof CommandOrigin.Gameplay game
                    && game.before().frame().identity().nativeRevision().compareTo(frames.before().identity().frame().identity().nativeRevision())>0
                    && game.before().frame().identity().nativeRevision().compareTo(frames.after().identity().frame().identity().nativeRevision())<=0) return false;
            var originalDispatch=ActionTransitions.dispatch(receipt.state());
            if (originalDispatch.orElse(null) instanceof NativeActionPort.AckReceived ack && ack.custody().isPresent()) {
                var custody=ack.custody().orElseThrow(); custody.verify(ack,other.guard());
                if (custody.session().equals(first.session()) && custody.custodyEpoch().equals(first.custodyEpoch())
                        && custody.writeEntered().order().compareTo(first.responseReceived().order())>=0
                        && custody.writeEntered().order().compareTo(last.responseReceived().order())<=0) return false;
            }
        }
        return found;
    }
}
