package org.xar.ck3.research.m3.tail6874fp272;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m3.tail250.Tail4256874250;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Explicit proposal implementation for Tail6874FullState272.
 * Reuses existing Tail4256874250.execute exactly once with a private sameRAM adapter.
 * No binder, no test, no old algorithm delta.
 */
public final class Tail6874FullState272 {
    private Tail6874FullState272() { }

    public static QueueFp604Api.Normal execute(QueueFp604Api.Input input, FullCopy437Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        GovernmentCrtBoundary185Api.Entry entry = input.base().entry();
        long imageBase = entry.imageBaseBits();
        long rspBits = entry.rspBits();

        // Extract entry registers from volatile bits
        GovernmentPrimaryTail155Api.VolatileBits v = entry.volatileBits();
        long entryRcx = v.rcxBits();

        // Create the private sameRAM adapter implementing Callee68d4Memory246
        Callee68d4Memory246 adapter = new SameRamAdapter(memory);

        // Execute the old business logic exactly once
        long resultScalar = Tail4256874250.execute(adapter, imageBase, entryRcx);

        // Construct the NormalReturn with updated RAX and fresh RIP read
        // RAX is replaced by the zero-extended scalar result
        GovernmentPrimaryTail155Api.VolatileBits updatedV = new GovernmentPrimaryTail155Api.VolatileBits(
            resultScalar, // raxBits
            v.rcxBits(),
            v.rdxBits(),
            v.r8Bits(),
            v.r9Bits(),
            v.r10Bits(),
            v.r11Bits(),
            v.xmm0(),
            v.xmm1(),
            v.xmm2(),
            v.xmm3(),
            v.xmm4(),
            v.xmm5()
        );

        // Fresh memory read for return RIP after core execution
        long freshRip = memory.readQword(rspBits);

        // Construct 185.NormalReturn
        GovernmentCrtBoundary185Api.NormalReturn normalReturn = new GovernmentCrtBoundary185Api.NormalReturn(
            updatedV,
            freshRip,
            rspBits + 8L,
            entry.nonvolatileBits()
        );

        // Construct 437.CallResult with preserved DF
        FullCopy437Api.CallResult callResult = new FullCopy437Api.CallResult(
            normalReturn,
            input.base().directionFlagSet()
        );

        // Construct 604.Normal with SAME FP object
        return new QueueFp604Api.Normal(callResult, input.mxcsr());
    }

    /**
     * Private sameRAM adapter implementing Callee68d4Memory246.
     * Delegates all inherited memory members to the provided FullCopy437Api.Memory.
     */
    private static final class SameRamAdapter implements Callee68d4Memory246 {
        private final FullCopy437Api.Memory delegate;

        SameRamAdapter(FullCopy437Api.Memory delegate) {
            this.delegate = delegate;
        }

        @Override
        public long readPointer(long addressBits) {
            return delegate.readQword(addressBits);
        }

        @Override
        public int readInt32(long addressBits) {
            return delegate.readDword(addressBits);
        }

        @Override
        public void writeInt32(long addressBits, int valueBits) {
            delegate.writeDword(addressBits, valueBits);
        }

        @Override
        public void writeInt64(long addressBits, long valueBits) {
            delegate.writeQword(addressBits, valueBits);
        }

        @Override
        public void writeInt16(long addressBits, int valueBits) {
            delegate.writeWord(addressBits, valueBits);
        }

        @Override
        public void atomicAddInt32(long addressBits, int deltaBits) {
            delegate.lockedXaddDword(addressBits, deltaBits);
        }

        @Override
        public int exchangeAddInt32(long addressBits, int deltaBits) {
            return delegate.lockedXaddDword(addressBits, deltaBits);
        }


    }
}