package org.xar.ck3.control.application.session;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.contracts.StrictJson;

/** Root emits this only after its original pending-read barrier and same-Session actual READ commit. No action retry or effect is granted. */
public final class ReadPublicationRefreshException extends RuntimeException {
    private static final long serialVersionUID=1L;
    // These same-process control-flow facts are retained by their original typed owners, not exception serialization.
    private final transient ActionCommand interrupted;
    private final transient Optional<ActionReceipt> zeroDispatch;
    private final transient OrdinaryPlanCompletion.Published actual;
    private final transient Optional<String> unresolvedParent;
    public ReadPublicationRefreshException(ActionCommand interrupted,Optional<ActionReceipt> actualZeroDispatch,
            OrdinaryPlanCompletion.Published actualReadPublication,Optional<String> actualUnresolvedParentId) {
        super("actual read publication requires a fresh complete observation and plan before dispatch");
        this.interrupted=Objects.requireNonNull(interrupted);zeroDispatch=Objects.requireNonNull(actualZeroDispatch);actual=Objects.requireNonNull(actualReadPublication);
        unresolvedParent=Objects.requireNonNull(actualUnresolvedParentId);
        unresolvedParent.ifPresent(id->StrictJson.require(id.equals(interrupted.actionId())&&zeroDispatch.isEmpty(),"original unresolved parent refresh cannot impersonate a child zero-dispatch receipt"));
        StrictJson.require(actual.predecessor().state().machineId().equals(interrupted.origin().machineId()),"read refresh crossed actual original machine");
        zeroDispatch.ifPresent(receipt->{
            StrictJson.require(receipt.command().equals(interrupted)&&receipt.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH
                    &&receipt.state() instanceof ActionState.RejectedBeforeDispatch,"read refresh needs its exact independently retained zero-dispatch receipt");
            var rejected=(ActionState.RejectedBeforeDispatch)receipt.state();
            StrictJson.require(rejected.dispatch().proof().requestBytesWritten()==0
                    &&rejected.attempt().requestId().equals(rejected.dispatch().requestId()),"read refresh cannot conceal any original native write or request drift");
        });
    }
    public ActionCommand command(){return interrupted;}
    public Optional<ActionReceipt> zeroDispatchReceipt(){return zeroDispatch;}
    public OrdinaryPlanCompletion.Published publication(){return actual;}
    public Optional<String> unresolvedParentId(){return unresolvedParent;}
}
