package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

import java.util.Objects;

/**
 * Consumer for the actual BD7CF0 integration targets at 0xBD7DD2 and 0xBD7E5F.
 * Matches exact call sites and targets, delegates unchanged for all other calls/tails/GS.
 */
public final class LoadRowReference34ef710195Calls {

    private static final long TARGET_RVA = 0x34EF710L;

    // Call site 1: BD7DD2, next instruction BD7DD7 (return RIP)
    private static final long SITE1 = 0xBD7DD2L;
    private static final long RET1 = 0xBD7DD7L;

    // Call site 2: BD7E5F, next instruction BD7E64 (return RIP)
    private static final long SITE2 = 0xBD7E5FL;
    private static final long RET2 = 0xBD7E64L;

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        return new Consumer(imageBaseBits, memory, delegate);
    }

    private static final class Consumer implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBase;
        private final GovernmentCrtBoundary185Api.Memory mem;
        private final GovernmentCrtBoundary185Api.Calls del;

        Consumer(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate) {
            this.imageBase = imageBaseBits;
            this.mem = memory;
            this.del = delegate;
        }

        @Override
        public VolatileBits invoke(Call call) {
            // Check if this is one of the two specific integration targets
            if (call.kind() == TargetKind.DIRECT_RVA && call.targetBits() == TARGET_RVA) {
                if (call.callSiteRva() == SITE1) {
                    return handleIntegration(call, RET1);
                } else if (call.callSiteRva() == SITE2) {
                    return handleIntegration(call, RET2);
                }
            }
            // Delegate unchanged for all other calls
            return del.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            // Delegate unchanged for all tails
            return del.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            // Delegate unchanged for GS read
            return del.readGsQword58();
        }

        private VolatileBits handleIntegration(Call call, long expectedReturnRip) {
            // Construct the child entry for the production execute
            // childEntry uses call.rspBits-8 (return slot already owned by caller)
            long childRsp = call.rspBits() - 8L;

            // Create Entry with same image, shared memory, all V and NV bits
            Entry childEntry = new Entry(
                imageBase,
                childRsp,
                call.volatileBits(),
                call.nonvolatileBits()
            );

            // Invoke the production execute
            NormalReturn result = LoadRowReference34ef710195.execute(childEntry, mem, del);

            // Verify exact return RIP matches expected (imageBase + actual next RVA)
            long expectedRip = imageBase + expectedReturnRip;
            if (result.returnRipBits() != expectedRip) {
                throw new IllegalStateException("Return RIP mismatch: expected " + Long.toHexString(expectedRip) + " got " + Long.toHexString(result.returnRipBits()));
            }

            // Verify caller RSP equality
            if (result.callerRspBits() != call.rspBits()) {
                throw new IllegalStateException("Caller RSP mismatch: expected " + Long.toHexString(call.rspBits()) + " got " + Long.toHexString(result.callerRspBits()));
            }

            // Verify nonvolatile equality to original call
            NonvolatileBits originalNv = call.nonvolatileBits();
            NonvolatileBits restoredNv = result.nonvolatileBits();

            if (originalNv.rbxBits() != restoredNv.rbxBits() ||
                originalNv.rbpBits() != restoredNv.rbpBits() ||
                originalNv.rsiBits() != restoredNv.rsiBits() ||
                originalNv.rdiBits() != restoredNv.rdiBits() ||
                originalNv.r12Bits() != restoredNv.r12Bits() ||
                originalNv.r13Bits() != restoredNv.r13Bits() ||
                originalNv.r14Bits() != restoredNv.r14Bits() ||
                originalNv.r15Bits() != restoredNv.r15Bits() ||
                !bitsEqual(originalNv.xmm6(), restoredNv.xmm6())) {
                throw new IllegalStateException("Nonvolatile register mismatch");
            }

            // Return complete volatile tuple
            return result.volatileBits();
        }

        private static boolean bitsEqual(Bits128 a, Bits128 b) {
            return a.lowBits() == b.lowBits() && a.highBits() == b.highBits();
        }
    }
}