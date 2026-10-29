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
}
