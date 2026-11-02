package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Entry;
import org.xar.ck3.research.m5.GovernmentRoot178Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Memory;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Calls;
import org.xar.ck3.research.m4.Retry60NormalFullState284Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Calls;
import org.xar.ck3.research.m5.GovernmentRootRetry209;

/**
 * New unit implementing the seven-input contract for whole Root178 integration.
 * Reuses existing as185 forwarding and 209 delegate without copying algorithms.
 */
public final class GovernmentRootCrtRetry210 {
    private GovernmentRootCrtRetry210() { }

    public static NormalReturn execute(
            Entry entry,
            Memory memory,
            Calls outer,
            GovernmentCrtBoundary185Api.Calls crtPorts,
            GovernmentCrtBoundary185Api.LoopBudget crtBudget,
            GovernmentCrtBoundary185Api.Calls allocationPorts,
            GovernmentCrtBoundary185Api.LoopBudget allocationBudget) {

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(outer);
        Objects.requireNonNull(crtPorts);
        Objects.requireNonNull(crtBudget);
        Objects.requireNonNull(allocationPorts);
        Objects.requireNonNull(allocationBudget);

        // Bind existing GovernmentCrtBoundary185Calls to obtain the real Bridge Calls type.
        // Retry60NormalFullState284Calls.as185 provides a forwarding view over the same Memory object.
        GovernmentCrtBoundary185BridgeApi.Calls boundCRTCalls = GovernmentCrtBoundary185Calls.bind(
                entry.imageBaseBits(),
                Retry60NormalFullState284Calls.as185(memory),
                outer,
                crtPorts,
                crtBudget);

        // Delegate to existing GovernmentRootRetry209.execute exactly once.
        return GovernmentRootRetry209.execute(
                entry,
                memory,
                boundCRTCalls,
                allocationPorts,
                allocationBudget);
    }
}