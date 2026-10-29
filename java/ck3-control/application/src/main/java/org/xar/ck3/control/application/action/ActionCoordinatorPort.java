package org.xar.ck3.control.application.action;

/** All application callers share the same single Game action authority. */
public interface ActionCoordinatorPort {
    default ActionReceipt execute(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command) {
        throw new IllegalStateException("same-writer action submission is not installed");
    }
    default ActionReceipt reconcile(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, String actionId) {
        throw new IllegalStateException("same-writer action reconciliation is not installed");
    }
    default CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token) throws java.io.IOException {
        throw new java.io.IOException("source-owned original composite continuation is unavailable");
    }
    default CompositeContinuationReport continueOriginalComposite(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            CompositeContinuationToken token) throws java.io.IOException {
        throw new java.io.IOException("same-writer original composite continuation is unavailable");
    }
    /** Legacy wrappers forward through their existing same-writer reconcile method; the central source gate remains mandatory. */
    default ActionReceipt reconcileOriginalDirectWindowQuery(DirectFixedWindowQueryContinuation actual) throws java.io.IOException {
        java.util.Objects.requireNonNull(actual);
        return DirectFixedWindowQueryInvocation.forward(null, actual, () -> reconcile(actual.actionId()));
    }
    default ActionReceipt reconcileOriginalDirectWindowQuery(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            DirectFixedWindowQueryContinuation actual) throws java.io.IOException {
        java.util.Objects.requireNonNull(same); java.util.Objects.requireNonNull(actual);
        return DirectFixedWindowQueryInvocation.forward(same, actual, () -> reconcile(same, actual.actionId()));
    }
    ActionReceipt execute(ActionCommand command);
    ActionReceipt reconcile(String actionId);
}
