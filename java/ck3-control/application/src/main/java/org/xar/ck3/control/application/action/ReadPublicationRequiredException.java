package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Abort this decision until Root exits the frozen scope and publishes the actual queued READ under this writer.
 * In-process control signal only; Java object serialization is unsupported for its original domain references. */
public final class ReadPublicationRequiredException extends IllegalStateException {
    private static final long serialVersionUID = 1L;
    // These actual same-writer originals remain in memory; the domain JSON codecs own persistence.
    @SuppressWarnings("serial")
    private final ActionCommand command;
    @SuppressWarnings("serial")
    private final Optional<ActionReceipt> zeroDispatchReceipt;
    public ReadPublicationRequiredException(ActionCommand command, Optional<ActionReceipt> zeroDispatchReceipt) {
        super("actual READ publication must complete before this action may submit");
        this.command = Objects.requireNonNull(command); this.zeroDispatchReceipt = Objects.requireNonNull(zeroDispatchReceipt);
        zeroDispatchReceipt.ifPresent(receipt -> {
            StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(receipt.command()))
                    && receipt.outcome() == ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH
                    && receipt.state() instanceof ActionState.RejectedBeforeDispatch, "READ barrier zero-dispatch receipt changed its original command or state");
            var zero = (ActionState.RejectedBeforeDispatch) receipt.state();
            StrictJson.require(zero.dispatch().proof().stage() == NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                    && zero.dispatch().proof().requestBytesWritten() == 0 && zero.attempt().requestId().equals(zero.dispatch().requestId())
                    && zero.attempt().requestId().equals(RequestIds.forCommand(command))
                    && NativeStepDiscriminator.matchesRequest(command.operation(), ExecutableStepBindings.Kind.ACTION, zero.attempt().preparedRequest()), "READ barrier requires the original never-written primitive request");
        });
    }
    public ActionCommand command() { return command; }
    public Optional<ActionReceipt> zeroDispatchReceipt() { return zeroDispatchReceipt; }
}
