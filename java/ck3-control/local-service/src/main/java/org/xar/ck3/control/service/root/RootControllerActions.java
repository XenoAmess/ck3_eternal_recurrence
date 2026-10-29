package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Controller routing only. The identical installed coordinator remains the sole Game submitter. */
final class RootControllerActions implements ActionCoordinatorPort {
    private final RootApplicationAssembly.Core core;
    private final SessionIdentity identity;
    private final ActionCoordinatorPort original;
    private volatile RootApplicationSession root;

    RootControllerActions(RootApplicationAssembly.Core core, SessionIdentity identity, ActionCoordinatorPort original) {
        this.core = Objects.requireNonNull(core);
        this.identity = Objects.requireNonNull(identity);
        this.original = Objects.requireNonNull(original);
    }
    /** The circular Controller/Session graph closes once before publication or any turn. */
    synchronized void bind(RootApplicationSession actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(root == null && actual.ownedBy(core) && actual.writer() == core.writer()
                && actual.archive() == core.archive() && actual.identity().equals(identity),
                "Controller actions must bind their identical actual Root session once");
        root = actual;
    }
    private RootApplicationSession required() {
        RootApplicationSession actual = root;
        StrictJson.require(actual != null, "Controller actions are unavailable before the actual Root session binds");
        return actual;
    }
    private static boolean checkpoint(ActionCommand command) {
        return Objects.requireNonNull(command).operation().value().equals("save-checkpoint");
    }
    @Override public ActionReceipt execute(ActionCommand command) {
        RootApplicationSession actual = required();
        // A planned SAVE consumes the Root's private Prepared, paired files and material/Controller adoption.
        return checkpoint(command) ? actual.execute(command) : original.execute(command);
    }
    @Override public ActionReceipt execute(ContinuityStorePort.Session same, ActionCommand command) {
        RootApplicationSession actual = required();
        return checkpoint(command) ? actual.execute(same, command) : original.execute(same, command);
    }
    @Override public ActionReceipt reconcile(String actionId) {
        // Session recognizes its retained SAVE; other originals still use the identical coordinator.
        return required().reconcile(actionId);
    }
    @Override public ActionReceipt reconcile(ContinuityStorePort.Session same, String actionId) {
        return required().reconcile(same, actionId);
    }
    @Override public CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token) throws IOException {
        required(); return original.continueOriginalComposite(token);
    }
    @Override public CompositeContinuationReport continueOriginalComposite(ContinuityStorePort.Session same,
            CompositeContinuationToken token) throws IOException {
        required(); return original.continueOriginalComposite(same, token);
    }
    @Override public ActionReceipt reconcileOriginalDirectWindowQuery(DirectFixedWindowQueryContinuation actual) throws IOException {
        required(); return original.reconcileOriginalDirectWindowQuery(actual);
    }
    @Override public ActionReceipt reconcileOriginalDirectWindowQuery(ContinuityStorePort.Session same,
            DirectFixedWindowQueryContinuation actual) throws IOException {
        required(); return original.reconcileOriginalDirectWindowQuery(same, actual);
    }
}
