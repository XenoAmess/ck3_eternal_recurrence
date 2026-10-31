package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentRegistry182Calls {
    private GovernmentRegistry182Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(long imageBase, GovernmentSharedManager167Api.Memory memory, GovernmentPrimaryTail155Api.Calls delegate) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);

        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                long callSiteRva = call.callSiteRva();
                long targetRva = call.targetRva();

                if (callSiteRva == 0x3F8A896L && targetRva == 0x4223F24L) {
                    // Manager callback at 3F8A896 has not pushed, so write child CALL return once.
                    long rspBefore = call.rspBits();
                    long rspAfterPush = rspBefore - 8L;
                    long returnAddr = imageBase + callSiteRva + 5L;
                    memory.writeQword(rspAfterPush, returnAddr);

                    // Construct exact callee Entry from actual call-site minus 8
                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                        imageBase,
                        rspAfterPush,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );

                    // Execute actual new method with shared SAME memory and bound Calls
                    GovernmentCallee164Api.NormalReturn ret = GovernmentRegistryStatus182.execute(entry, memory, this);

                    // Check actual return RIP equals base+site+5
                    long expectedRip = imageBase + callSiteRva + 5L;
                    if (ret.returnRipBits() != expectedRip) {
                        throw new UnsupportedOperationException("Return RIP mismatch");
                    }

                    // Returned callerRSP equals call.rspBits
                    if (ret.callerRspBits() != rspBefore) {
                        throw new UnsupportedOperationException("Caller RSP mismatch");
                    }

                    // N equals offered call N
                    GovernmentPrimaryTail155Api.NonvolatileBits expectedN = call.nonvolatileBits();
                    GovernmentPrimaryTail155Api.NonvolatileBits actualN = ret.nonvolatileBits();
                    if (actualN.rbxBits() != expectedN.rbxBits() ||
                        actualN.rbpBits() != expectedN.rbpBits() ||
                        actualN.rsiBits() != expectedN.rsiBits() ||
                        actualN.rdiBits() != expectedN.rdiBits() ||
                        actualN.r12Bits() != expectedN.r12Bits() ||
                        actualN.r13Bits() != expectedN.r13Bits() ||
                        actualN.r14Bits() != expectedN.r14Bits() ||
                        actualN.r15Bits() != expectedN.r15Bits() ||
                        actualN.xmm6().lowBits() != expectedN.xmm6().lowBits() ||
                        actualN.xmm6().highBits() != expectedN.xmm6().highBits()) {
                        throw new UnsupportedOperationException("Nonvolatile bits mismatch");
                    }

                    return ret.volatileBits();
                } else if (callSiteRva == 0x4223F28L && targetRva == 0x4223EE8L) {
                    // Status182 core pushes physical 4223F2D before invokes its 4223F28 opaque callback,
                    // so nested adapter only consumes existing entry, no second same-value memory write.
                    long rspBefore = call.rspBits();
                    long rspAfterPush = rspBefore - 8L;
                    long returnAddr = imageBase + callSiteRva + 5L;

                    // Construct exact callee Entry from actual call-site minus 8
                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                        imageBase,
                        rspAfterPush,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );

                    // Execute actual new method with shared SAME memory and bound Calls
                    GovernmentCallee164Api.NormalReturn ret = GovernmentRegistryEntry183.execute(entry, memory, this);

                    // Check actual return RIP equals base+site+5
                    long expectedRip = imageBase + callSiteRva + 5L;
                    if (ret.returnRipBits() != expectedRip) {
                        throw new UnsupportedOperationException("Return RIP mismatch");
                    }

                    // Returned callerRSP equals call.rspBits
                    if (ret.callerRspBits() != rspBefore) {
                        throw new UnsupportedOperationException("Caller RSP mismatch");
                    }

                    // N equals offered call N
                    GovernmentPrimaryTail155Api.NonvolatileBits expectedN = call.nonvolatileBits();
                    GovernmentPrimaryTail155Api.NonvolatileBits actualN = ret.nonvolatileBits();
                    if (actualN.rbxBits() != expectedN.rbxBits() ||
                        actualN.rbpBits() != expectedN.rbpBits() ||
                        actualN.rsiBits() != expectedN.rsiBits() ||
                        actualN.rdiBits() != expectedN.rdiBits() ||
                        actualN.r12Bits() != expectedN.r12Bits() ||
                        actualN.r13Bits() != expectedN.r13Bits() ||
                        actualN.r14Bits() != expectedN.r14Bits() ||
                        actualN.r15Bits() != expectedN.r15Bits() ||
                        actualN.xmm6().lowBits() != expectedN.xmm6().lowBits() ||
                        actualN.xmm6().highBits() != expectedN.xmm6().highBits()) {
                        throw new UnsupportedOperationException("Nonvolatile bits mismatch");
                    }

                    return ret.volatileBits();
                } else {
                    // All other calls delegate unchanged
                    return delegate.invoke(call);
                }
            }
        };
    }
}