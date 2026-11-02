package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Entry;
import org.xar.ck3.research.m5.GovernmentRoot178Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Memory;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Calls;
import org.xar.ck3.research.m4.Retry60NormalFullState284Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

public final class GovernmentRootRetry209 {
    private GovernmentRootRetry209() { }

    public static NormalReturn execute(
            Entry entry,
            Memory memory,
            Calls outer,
            GovernmentCrtBoundary185Api.Calls lower,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(outer);
        Objects.requireNonNull(lower);
        Objects.requireNonNull(budget);

        GovernmentRoot178Api.Calls bound = Retry60NormalFullState284Calls.bindRoot(
                entry.imageBaseBits(),
                memory,
                outer,
                lower,
                budget);

        return GovernmentRoot178.execute(entry, memory, bound);
    }
}