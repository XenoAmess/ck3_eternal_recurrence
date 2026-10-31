package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m1.GovernmentLookup167Api.Entry;
import org.xar.ck3.research.m1.GovernmentLookup167Api.Result;
import org.xar.ck3.research.m1.GovernmentLookup167Api.Target;
import org.xar.ck3.research.m1.GovernmentLookup167Api.SpinBudget;

public final class GovernmentLookup167Adapter implements Calls {
    private final long imageBaseBits;
    private final Memory memory;
    private final Calls fallback;
    private final Target target;
    private final SpinBudget spinBudget;

    public GovernmentLookup167Adapter(long imageBaseBits, Memory memory, Calls fallback, Target target, SpinBudget spinBudget) {
        this.imageBaseBits = imageBaseBits;
        this.memory = Objects.requireNonNull(memory);
        this.fallback = Objects.requireNonNull(fallback);
        this.target = Objects.requireNonNull(target);
        this.spinBudget = Objects.requireNonNull(spinBudget);
    }

    @Override
    public long readGsQword58() {
        return fallback.readGsQword58();
    }

    @Override
    public VolatileBits invoke(OpaqueCall call) {
        Objects.requireNonNull(call);
        if (call.targetRva() != 0x3F8A6D0L) {
            return fallback.invoke(call);
        }

        long siteRSP = call.rspBits();
        long callSiteRva = call.callSiteRva();
        long returnAddr = imageBaseBits + callSiteRva + 5L;
        long stackSlot = siteRSP - 8L;
        memory.writeQword(stackSlot, returnAddr);

        Entry entry = new Entry(
            imageBaseBits,
            stackSlot,
            call.volatileBits(),
            call.nonvolatileBits()
        );

        Result result = target.execute(entry, memory, fallback, spinBudget);

        if (result.returnRipBits() != returnAddr) {
            throw new UnsupportedOperationException("Boundary mismatch: returnRipBits(" + result.returnRipBits() + ") != returnAddr(" + returnAddr + ")");
        }
        if (result.callerRspBits() != siteRSP) {
            throw new UnsupportedOperationException("Boundary mismatch: callerRspBits(" + result.callerRspBits() + ") != siteRSP(" + siteRSP + ")");
        }
        if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
            throw new UnsupportedOperationException("Boundary mismatch: returnedNonvolatile differs from input nonvolatile");
        }

        return result.volatileBits();
    }
}