package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m4.StackProbe78FullState290;
import java.util.Objects;

public final class StackProbe78Initial162Calls290 {
    private StackProbe78Initial162Calls290() { }

    public static GovernmentInitialFrame162Api.Calls bind(long imageBase, GovernmentInitialFrame162Api.Memory memory, GovernmentInitialFrame162Api.Calls outerFallback, StackProbe78FullState290.Gs10 gs10, GovernmentCrtBoundary185Api.LoopBudget budget) {
        GovernmentCrtBoundary185Api.Memory m185 = Retry60NormalFullState284Calls.as185(memory);

        return new GovernmentInitialFrame162Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x30A2F2AL && call.targetRva() == 0x42247B0L) {
                    // Exact owned callback: push return address once before child entry
                    long preSP = call.rspBits();
                    long childRSP = preSP - 8L;

                    // Write return address to the slot that will be popped by RET
                    m185.writeQword(childRSP, imageBase + 0x30A2F2FL);

                    // Construct child entry with correct pre-push state
                    GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                            imageBase,
                            childRSP,
                            call.volatileBits(),
                            call.nonvolatileBits()
                    );

                    // Execute StackProbe78FullState290
                    GovernmentCrtBoundary185Api.NormalReturn childReturn = StackProbe78FullState290.execute(
                            childEntry,
                            m185,
                            gs10,
                            budget
                    );

                    // Validate return RIP and SP
                    long expectedRip = imageBase + 0x30A2F2FL;
                    if (childReturn.returnRipBits() != expectedRip) {
                        throw new UnsupportedOperationException("Invalid child return RIP");
                    }
                    if (childReturn.callerRspBits() != preSP) {
                        throw new UnsupportedOperationException("Invalid child return SP");
                    }

                    // Validate nonvolatile preservation
                    if (!childReturn.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Nonvolatile continuation mismatch");
                    }

                    // Return actual volatile bits from child
                    return childReturn.volatileBits();
                }

                // Delegate all other calls to outerFallback
                return outerFallback.invoke(call);
            }

            @Override
            public long readGsQword58() {
                return outerFallback.readGsQword58();
            }
        };
    }
}