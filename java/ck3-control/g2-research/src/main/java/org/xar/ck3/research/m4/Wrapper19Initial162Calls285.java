package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m4.Retry60NormalFullState284Calls;
import org.xar.ck3.research.m4.Wrapper19NormalFullState285;
import java.util.Objects;

public final class Wrapper19Initial162Calls285 {
    private Wrapper19Initial162Calls285() { }

    public static GovernmentInitialFrame162Api.Calls bind(long imageBase, GovernmentInitialFrame162Api.Memory memory, GovernmentInitialFrame162Api.Calls outerFallback, GovernmentCrtBoundary185Api.Calls lower, GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(outerFallback);
        Objects.requireNonNull(lower);
        Objects.requireNonNull(budget);

        GovernmentCrtBoundary185Api.Memory m185 = Retry60NormalFullState284Calls.as185(memory);
        GovernmentCrtBoundary185Api.Calls children = Retry60NormalFullState284Calls.normalChildren(imageBase, m185, lower, budget);

        return new GovernmentInitialFrame162Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x30A304FL && call.targetRva() == 0x42242CCL) {
                    long preSP = call.rspBits();
                    long childRsp = preSP - 8L;
                    long retAddr = imageBase + 0x30A3054L;

                    // Owned callback push: write return address to stack before child execution
                    m185.writeQword(childRsp, retAddr);

                    GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                            imageBase,
                            childRsp,
                            call.volatileBits(),
                            call.nonvolatileBits());

                    GovernmentCrtBoundary185Api.NormalReturn childReturn = Wrapper19NormalFullState285.execute(
                            childEntry, m185, children, budget);

                    // Validate actual normal return state
                    if (childReturn.returnRipBits() != retAddr) {
                        throw new UnsupportedOperationException("Invalid child return RIP");
                    }
                    if (childReturn.callerRspBits() != preSP) {
                        throw new UnsupportedOperationException("Invalid child return SP");
                    }
                    if (!childReturn.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Nonvolatile continuation mismatch");
                    }

                    return childReturn.volatileBits();
                }

                // Delegate other calls to outerFallback
                return outerFallback.invoke(call);
            }

            @Override
            public long readGsQword58() {
                return outerFallback.readGsQword58();
            }
        };
    }
}