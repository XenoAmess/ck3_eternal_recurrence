package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** One original receipt boundary shared by the finite Army read producers. */
public final class ArmyNativeReadEvidence {
    private ArmyNativeReadEvidence() { }
    /** Rebind only the real invocation's transport budget. Native/Driver/episode/source identity must remain exact. */
    public static Context contextForRequest(Context selected, PlanningReadRequest request) {
        require(request.before().equals(selected.before()) && request.source().equals(selected.source())
                && request.sessionId().equals(selected.sessionId()), "Army read request crossed selected native/Driver source identity");
        return new Context(selected.before(), selected.source(), selected.sessionId(), request.deadline());
    }
    /** These strict decoders consume typed arguments and Context only. The publisher additionally proves current raw native/source/capability evidence. */
    public static void requireCanonicalEquivalent(PlanningReadReceipt original, PlanningReadRequest current) {
        var old=original.request();
        require(old.before().equals(current.before()) && old.source().equals(current.source())
                && old.sessionId().equals(current.sessionId()) && old.operation().equals(current.operation())
                && old.arguments().equals(current.arguments()), "Army canonical read crossed an observed source or typed selection");
    }
    public static void verifyContext(Context context, PlanningReadReceipt receipt) {
        contextForRequest(context, receipt.request());
        for (var guard : List.of(receipt.before(), receipt.after()))
            require(guard.binding().observed().equals(context.before()) && guard.binding().source().equals(context.source())
                    && guard.binding().sessionId().equals(context.sessionId()) && guard.paused() && guard.mapReady() && guard.playerAlive(), "Army read requires the same actual living paused map");
        require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "Army semantic/modal binding changed");
    }
    public static ObjectNode result(Context context, PlanningReadReceipt receipt) {
        verifyContext(context, receipt);
        ObjectNode frame = closed(parse(receipt.original().originalFrame().bytes()), "type", "protocol_version", "request_id", "ok", "result");
        equal(frame.get("type"), "command_result"); require(i32(frame.get("protocol_version")) == 1, "Native protocol version");
        equal(frame.get("request_id"), receipt.requestId()); yes(frame.get("ok")); ObjectNode result = object(frame.get("result"));
        require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent()
                && parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(result), "Army token differs from its full original Native result");
        equal(get(result, "step"), receipt.request().operation().value()); return result;
    }
}

