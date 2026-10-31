package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Memory;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class GovernmentNormalizeFull174Calls {
    private GovernmentNormalizeFull174Calls() { }

    public static Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        return new Bridge(imageBaseBits, memory, fallback);
    }

    private static final class Bridge implements Calls {
        private final long imageBaseBits;
        private final Memory memory;
        private final Calls fallback;

        Bridge(long imageBaseBits, Memory memory, Calls fallback) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public VolatileBits invoke(OpaqueCall call) {
            Objects.requireNonNull(call);
            if (call.targetRva() == 0x30a2cc0L && (call.callSiteRva() == 0x30a3e67L || call.callSiteRva() == 0x30a3ea5L)) {
                return handleNormalizeCall(call);
            }
            return fallback.invoke(call);
        }

        private VolatileBits handleNormalizeCall(OpaqueCall call) {
            long callSiteRva = call.callSiteRva();
            long rspBits = call.rspBits();
            long returnRip = imageBaseBits + callSiteRva + 5L;
            long calleeRsp = rspBits - 8L;

            // Model actual x64 CALL push in shared memory
            memory.writeQword(calleeRsp, returnRip);

            // Construct callee entry with original bits
            GovernmentNormalizeFull174Api.Entry entry = new GovernmentNormalizeFull174Api.Entry(
                imageBaseBits, calleeRsp, call.volatileBits(), call.nonvolatileBits()
            );

            // Create normalized calls port for the core
            GovernmentNormalizeFull174Api.Calls normalizedCalls = new NormalizedCalls(fallback);

            // Execute the independent core
            NormalReturn result = GovernmentNormalizeFull174.execute(entry, memory, normalizedCalls);

            // Validate return RIP
            if (result.returnRipBits() != returnRip) {
                throw new IllegalStateException("Return RIP mismatch: expected " + Long.toHexString(returnRip) + " got " + Long.toHexString(result.returnRipBits()));
            }

            // Validate caller RSP
            if (result.callerRspBits() != rspBits) {
                throw new IllegalStateException("Caller RSP mismatch: expected " + Long.toHexString(rspBits) + " got " + Long.toHexString(result.callerRspBits()));
            }

            // Validate nonvolatile bits preservation
            NonvolatileBits originalNV = call.nonvolatileBits();
            NonvolatileBits resultNV = result.nonvolatileBits();
            if (resultNV.rbxBits() != originalNV.rbxBits() ||
                resultNV.rbpBits() != originalNV.rbpBits() ||
                resultNV.rsiBits() != originalNV.rsiBits() ||
                resultNV.rdiBits() != originalNV.rdiBits() ||
                resultNV.r12Bits() != originalNV.r12Bits() ||
                resultNV.r13Bits() != originalNV.r13Bits() ||
                resultNV.r14Bits() != originalNV.r14Bits() ||
                resultNV.r15Bits() != originalNV.r15Bits() ||
                !resultNV.xmm6().equals(originalNV.xmm6())) {
                throw new IllegalStateException("Nonvolatile bits mismatch");
            }

            return result.volatileBits();
        }
    }

    private static final class NormalizedCalls implements GovernmentNormalizeFull174Api.Calls {
        private final Calls fallback;

        NormalizedCalls(Calls fallback) {
            this.fallback = fallback;
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public VolatileBits invoke(OpaqueCall call) {
            return fallback.invoke(call);
        }
    }
}
