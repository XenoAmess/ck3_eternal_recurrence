package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeReadEvidence;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;

/** Sole transport parser plus actual receive custody for the five installed EXECUTE_STEP Army reads.
 * This verifies originals. It issues no read permit, store claim, current frame or Native submission.
 */
public final class RootArmyReadPacketVerifier {
    private RootArmyReadPacketVerifier() { }
    public static void require(ArmyTypes.Context actual, OperationKey operation,
            RawJson expectedNativeArguments, PlanningReadReceipt receipt) {
        requirePackets(actual, operation, expectedNativeArguments, receipt);
        receipt.original().custody().orElseThrow(() -> new IllegalArgumentException("actual original Army receive custody is unavailable"))
                .verify(receipt);
        // Live PlanningReadCoordinator decodes before preserveRead. Archive membership is checked
        // by the installed replayArchived consumer after the actual receipt has been preserved.
    }
    /** Packet DATA validation seam for tests; success never substitutes for require's retained chronology. */
    static void requirePackets(ArmyTypes.Context actual, OperationKey operation,
            RawJson expectedNativeArguments, PlanningReadReceipt receipt) {
        Objects.requireNonNull(actual); Objects.requireNonNull(operation);
        Objects.requireNonNull(expectedNativeArguments); Objects.requireNonNull(receipt);
        ArmyNativeReadEvidence.verifyContext(actual, receipt);
        StrictJson.require(receipt.request().operation().equals(operation), "Army original read operation changed");
        try {
            var ack = receipt.original();
            var original = NativeWire.decode(ack.originalPacket());
            StrictJson.require(original instanceof NativeWire.CommandResult, "complete original Army command_result packet required");
            var result = (NativeWire.CommandResult) original;
            StrictJson.require(result.requestId().equals(receipt.requestId()) && ack.requestId().equals(receipt.requestId())
                    && result.nativeOk() && ack.nativeOk()
                    && Arrays.equals(result.payload().value(), ack.originalFrame().bytes())
                    && result.result().presence() == NativeWire.Presence.VALUE
                    && Arrays.equals(result.result().token().orElseThrow().value(), ack.originalResultToken().orElseThrow().bytes()),
                    "original Army packet, payload, request or result token changed");
            var outbound = ack.outbound().orElseThrow(() -> new IllegalArgumentException("actual original Army outbound packet is unavailable"));
            var request = NativeWire.decodeExecuteRequest(outbound.originalPacket());
            StrictJson.require(outbound.requestId().equals(receipt.requestId()) && request.requestId().equals(receipt.requestId())
                    && request.step().equals(operation.value())
                    && request.expectedRevision().equals(Optional.of(actual.nativeRevision()))
                    && request.expectedSnapshotRevision().isEmpty(),
                    "original Army EXECUTE_STEP outbound step, request or native revision changed");
            StrictJson.require(NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()))
                    .equals(NativeWire.object(NativeWire.parse(expectedNativeArguments.bytes()))),
                    "original Army native argument fields changed");
        } catch (IOException unavailable) {
            throw new UncheckedIOException("original Army packet is invalid or unavailable", unavailable);
        }
    }
}
