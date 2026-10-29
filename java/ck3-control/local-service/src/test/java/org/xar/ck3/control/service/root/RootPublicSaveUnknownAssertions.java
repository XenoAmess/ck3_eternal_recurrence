package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;

/** Test-only assertions around an actual Root SAVE. This helper constructs no Root, request command or qualification. */
public final class RootPublicSaveUnknownAssertions {
    private RootPublicSaveUnknownAssertions() { }

    /** A real fixture must arrange the delayed native poststate before invoking this production entry. */
    public static Retained captureUnknown(RootApplicationSession actualRoot,
            RootCheckpointPublicCalls.Request originalPublicRequest, Instant originalDeadline)
            throws IOException, InterruptedException {
        Objects.requireNonNull(actualRoot);Objects.requireNonNull(originalPublicRequest);Objects.requireNonNull(originalDeadline);
        RootCheckpointPublicCalls.SaveCall actual=actualRoot.saveCheckpointPublic(originalPublicRequest,originalDeadline);
        require(actual.actual() instanceof CheckpointResult.Unknown,
                "actual delayed SAVE must return UNKNOWN, not a fabricated before-submit result or an already confirmed SAVE");
        var unknown=(CheckpointResult.Unknown)actual.actual();
        ActionReceipt original=unknown.action().orElseThrow(()->new AssertionError("MISSING_ACTUAL_SAVE_ATTEMPT: before-submit UNKNOWN cannot cover late SAVE queries"));
        require(!original.settled(),"delayed-poststate fixture must retain an actually unresolved original SAVE action");
        require(unknown.actionId().equals(original.command().actionId()),"UNKNOWN must retain its actual original SAVE action ID");
        ActionState.Attempt attempt=attempt(original);
        require(attempt.submittedAt().isBefore(original.command().deadline())||attempt.submittedAt().equals(original.command().deadline()),
                "the original SAVE attempt must already have entered before its original deadline");
        verifyArchived(actualRoot,actual,original);
        return new Retained(actualRoot,originalPublicRequest,actualRoot.identity(),original,attempt,actual);
    }

    /** Private construction records only observations returned by the real production entry; it grants no action permission. */
    public static final class Retained {
        private final RootApplicationSession root;
        private final RootCheckpointPublicCalls.Request request;
        private final SessionIdentity owner;
        private final ActionReceipt original;
        private final ActionState.Attempt attempt;
        private final List<RootCheckpointPublicCalls.SaveCall> observed=new ArrayList<>();
        private RootCheckpointPublicCalls.SaveCall latest;
        private Retained(RootApplicationSession root,RootCheckpointPublicCalls.Request request,SessionIdentity owner,
                ActionReceipt original,ActionState.Attempt attempt,RootCheckpointPublicCalls.SaveCall initial) {
            this.root=root;this.request=request;this.owner=owner;this.original=original;this.attempt=attempt;
            this.latest=initial;observed.add(initial);
        }

        /** One public call means exactly one same-attempt query; fixture scheduling stays outside this helper. */
        public synchronized RootCheckpointPublicCalls.SaveCall query(Instant freshDeadline)
                throws IOException,InterruptedException {
            Objects.requireNonNull(freshDeadline);
            require(latest.actual() instanceof CheckpointResult.Unknown,"do not issue a new SAVE after the retained attempt has settled");
            require(freshDeadline.isAfter(original.command().deadline()),"late-query regression must cross the original SAVE deadline");
            require(root.identity().equals(owner),"query cannot move the retained SAVE to another physical Root");
            require(observed.size()<9,"actual SAVE query assertion fixture is bounded to eight queries");
            RootCheckpointPublicCalls.SaveCall actual=root.saveCheckpointPublic(request,freshDeadline);
            ActionReceipt receipt=RootCheckpointPublicCalls.action(actual.actual())
                    .orElseThrow(()->new AssertionError("actual retained SAVE query lost its original canonical receipt"));
            require(receipt.command().equals(original.command())&&receipt.bodySha256().equals(original.bodySha256()),
                    "query changed the original SAVE command, source, expected frame, deadline or canonical body");
            require(attempt(receipt).equals(attempt),"query allocated another SAVE attempt, request ID, guard or prepared native request");
            if(original.ack().isPresent())require(receipt.ack().equals(original.ack()),"query replaced the original native SAVE ACK");
            if(actual.actual() instanceof CheckpointResult.Unknown unknown)
                require(unknown.actionId().equals(original.command().actionId()),"UNKNOWN query changed its original action identity");
            if(actual.actual() instanceof CheckpointResult.Rejected rejected)
                require(rejected.actionId().equals(original.command().actionId()),"rejection changed its original action identity");
            verifyArchived(root,actual,receipt);
            latest=actual;observed.add(actual);return actual;
        }

        public synchronized List<RootCheckpointPublicCalls.SaveCall> observations(){return List.copyOf(observed);}

        /** Call only once the real fixture has supplied the original late physical pair and native poststate. */
        public synchronized CheckpointResult.Confirmed requireConfirmed() {
            require(latest.actual() instanceof CheckpointResult.Confirmed,
                    "MISSING_ACTUAL_SAVE_POSTSTATE: repeated UNKNOWN is not a passed confirmation regression");
            var confirmed=(CheckpointResult.Confirmed)latest.actual();
            require(latest.savedDriver().isPresent()&&latest.canonicalReceipt().isPresent(),
                    "confirmed query must expose its verified physical saved Driver and canonical receipt");
            require(confirmed.action().command().equals(original.command())&&attempt(confirmed.action()).equals(attempt),
                    "confirmed SAVE must be the same original action and physical attempt");
            return confirmed;
        }

        /** Missing ACK/poststate remains UNKNOWN with no saved-Driver or completion credit. */
        public synchronized void requireUnknown() {
            require(latest.actual() instanceof CheckpointResult.Unknown&&latest.savedDriver().isEmpty(),
                    "unconfirmed original SAVE acquired a saved Driver or false completion");
        }
    }

    private static void verifyArchived(RootApplicationSession root,RootCheckpointPublicCalls.SaveCall actual,
            ActionReceipt receipt)throws IOException {
        var ref=actual.canonicalReceipt().orElseThrow(()->new AssertionError("actual SAVE requires its original archived receipt"));
        // Historical receipt readback uses the original writer, not the already expired SAVE observation deadline.
        root.writer().locked(same->{
            require(root.archive().withSession(same).loadReceipt(ref).equals(receipt),
                    "public SAVE result is not its actual canonical archived receipt");
            return null;
        });
    }

    private static ActionState.Attempt attempt(ActionReceipt receipt) {
        if(receipt.state() instanceof ActionState.Submitting value)return value.attempt();
        if(receipt.state() instanceof ActionState.AckReceived value)return value.attempt();
        if(receipt.state() instanceof ActionState.Unknown value)
            return value.attempt().orElseThrow(()->new AssertionError("real SAVE UNKNOWN must retain its submitted attempt"));
        if(receipt.state() instanceof ActionState.Settled value)return value.attempt();
        if(receipt.state() instanceof ActionState.RejectedBeforeDispatch value)return value.attempt();
        throw new AssertionError("SAVE query regression requires its actual primitive attempt");
    }
    private static void require(boolean actual,String message){if(!actual)throw new AssertionError(message);}
}
