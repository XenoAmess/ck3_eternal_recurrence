package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Single actual pending query producer. The native parser requires the signed full ID on the wire. */
public final class PendingInteractionContracts {
    private PendingInteractionContracts() { }
    public static ReadContract<PendingContext> pending(ExactRef source) {
        return new ReadContract<>("interactions:pending-context",new OperationKey(PendingContextCodec.STEP),
                Optional.of(PendingContextCodec.CAPABILITY),PendingContextCodec.CAPABILITY,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                (request,requestId)-> {
                    var context=InteractionArguments.context(request);
                    var pending=context.controls().pending();
                    need(pending!=null,"current exact pending instance required");
                    var args=InteractionArguments.parseApp(request.arguments());
                    int requested=integer(args,"pending_id",Integer.MIN_VALUE,Integer.MAX_VALUE);
                    need(requested==pending.instance().value(),"query full signed pending identity changed");
                    return new NativeRequest(PendingContextCodec.STEP,PendingContextCodec.CAPABILITY,
                            encode(F.objectNode().put("pending_interaction_id",requested)));
                },
                PendingInteractionContracts::decodeOriginal,PendingInteractionContracts::decodeOriginal);
    }
    private static PendingContext decodeOriginal(org.xar.ck3.control.application.action.PlanningReadReceipt receipt) {
        var context=InteractionArguments.context(receipt.request());
                    var args=InteractionArguments.parseApp(receipt.request().arguments());
                    var id=new InteractionModels.PendingId(integer(args,"pending_id",Integer.MIN_VALUE,Integer.MAX_VALUE));
                    return PendingContextCodec.decodeNative(receipt.original().originalResultToken().orElseThrow(),context,id);
    }
}
