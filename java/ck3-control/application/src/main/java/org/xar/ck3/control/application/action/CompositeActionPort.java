package org.xar.ck3.control.application.action;

import java.util.List;

/** Registered Java translation of an original composite. Every native mutation is a separately durable child. */
public interface CompositeActionPort {
    String handlerId();
    boolean supports(OperationKey operation);
    /** Original readiness/source/precondition checks, before a durable parent intent. No side effects. */
    void validate(ActionCommand parent);
    /** Synchronous, finite execution on the original writer transaction. UNKNOWN child stops further submission. */
    ActionPorts.PostconditionResult run(ActionCommand parent, Children children) throws InterruptedException;
    /** Reconcile by reading/collecting originals; source-qualified first canonical poststate completion may use the held writer. No native child submitter is supplied. */
    ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained);

    /** The registered source, not a caller-implemented token, revalidates every new child under the same writer. */
    interface OriginalContinuation extends CompositeActionPort {
        void requireContinuation(ActionCommand parent, CompositeExecution retained, CompositeContinuationToken token);
        /** Source-owned finite child proof, including the canonical once reservation and new actor publication. */
        void requireContinuationChild(ActionCommand parent, CompositeExecution retained, CompositeContinuationToken token, ActionCommand child);
        ActionPorts.PostconditionResult continueOriginal(ActionCommand parent, CompositeExecution retained,
                CompositeContinuationToken token, Children children) throws InterruptedException;
    }
    /** Separately qualified prepared control. Every method is entered only through this
     * exact installed source, the same actual writer scope and its private token.
     * Heavy source/original validation and kept dependency leases precede observeLate.
     * The SDK final qualification must use the live scope capability, not replay them. */
    interface PreparedCleanupSource extends OriginalContinuation {
        org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared requirePreparedCleanup(
                ActionCommand child,CompositeContinuationToken token);
        default org.xar.ck3.control.application.advance.PreparedCleanupParentProjection projectPreparedCleanup(
                CompositeContinuationToken token,org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared,
                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.PostAckCaptured captured,org.xar.ck3.control.contracts.ExactRef captureReference){
            throw new IllegalStateException("actual prepared source has no complete captured-frame projection");
        }
        default ActionState.EffectObservation completePreparedCleanupParent(CompositeContinuationToken token,
                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared prepared,ActionReceipt actualChild,
                org.xar.ck3.control.application.advance.PreparedCleanupParentProjection projection){
            throw new IllegalStateException("actual prepared source has no complete five-child parent producer");
        }
        ActionPorts.OutcomeArchive preparedCleanupArchive();
        org.xar.ck3.control.application.advance.LifeAdvanceEvidence.BoundFrameVerifier preparedCleanupFrames();
        <T> T withPreparedCleanupWrite(ActionCommand child,CompositeContinuationToken token,
                org.xar.ck3.control.application.advance.PreparedCleanupEvidence.Prepared actualPrepared,
                PreparedCleanupWork<T> operation) throws java.io.IOException,InterruptedException;
    }
    @FunctionalInterface interface PreparedCleanupWork<T> {
        T run() throws java.io.IOException,InterruptedException;
    }
    interface Children {
        String nextActionId();
        default String nextActionId(OperationKey operation) { return nextActionId(); }
        List<ActionReceipt> completed();
        ActionReceipt submit(ActionCommand child);
        /** A registered lifecycle child commits under the original borrowed writer; it is not another native submission. */
        default org.xar.ck3.control.application.lifecycle.LifecycleCommit lifecycle(org.xar.ck3.control.application.lifecycle.LifecycleChild child) {
            throw new IllegalStateException("actual borrowed lifecycle writer is unavailable");
        }
    }

    /** Opt-in interface for sources that guarantee no gameplay writes before children are reserved. */
    interface ZeroGameplayBeforeChildren extends CompositeActionPort {
        void requireNoGameplayWrite(ActionCommand parent, CompositeExecution retained);
    }

    /** Source-owned opt-in for Life control-prefix interrupted terminal. */
    interface LifeControlPrefixSource extends CompositeActionPort {
        void requireControlPrefixInterruption(ActionCommand parent, CompositeExecution retained, org.xar.ck3.control.application.advance.LifeControlPrefixInterruption observation, java.util.List<ActionReceipt> canonicalChildren);
    }
}
