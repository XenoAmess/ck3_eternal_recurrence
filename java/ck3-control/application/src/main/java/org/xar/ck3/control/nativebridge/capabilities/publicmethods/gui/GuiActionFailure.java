package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.StrictJson;

/** Original rejected action, retaining the canonical receipt and original native false ACK. */
public final class GuiActionFailure extends RuntimeException {
    private static final long serialVersionUID = 1L;
    // In-process domain evidence is consumed directly; Java serialization is not its persistence contract.
    private final transient ActionReceipt receipt;
    // In-process domain evidence is consumed directly; Java serialization is not its persistence contract.
    private final transient NativeActionPort.AckReceived original;
    private final GuiReadFailure.Kind kind;

    private GuiActionFailure(ActionReceipt receipt, NativeActionPort.AckReceived original,
            GuiReadFailure.Kind kind, String message) {
        super(Objects.requireNonNull(message));
        this.receipt = Objects.requireNonNull(receipt);
        this.original = Objects.requireNonNull(original);
        this.kind = Objects.requireNonNull(kind);
    }

    public ActionReceipt receipt() { return receipt; }
    public NativeActionPort.AckReceived original() { return original; }
    public GuiReadFailure.Kind kind() { return kind; }

    /** A missing ACK or Unknown cannot be relabelled a native rejection. */
    public static GuiActionFailure fromRejectedAck(ActionReceipt actual) {
        Objects.requireNonNull(actual);
        NativeActionPort.AckReceived ack = actual.ack().orElseThrow(
                () -> new IllegalArgumentException("actual original rejected GUI ACK required"));
        StrictJson.require(!ack.nativeOk(), "successful native GUI ACK is not a rejection");
        Optional<String> message = GuiReadFailure.refusalMessage(ack);
        return new GuiActionFailure(actual, ack,
                message.isPresent() ? GuiReadFailure.Kind.NATIVE_REFUSAL : GuiReadFailure.Kind.ACK_UNUSABLE,
                message.orElse("actual original rejected GUI ACK has no valid common refusal profile"));
    }
}
