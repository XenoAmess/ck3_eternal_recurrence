package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.record206.MapRecord86F210206;

public final class MapRecord86f210208 {
    private MapRecord86f210208() {
    }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory) {

        // 1. Construct NativeTaskMemory view delegating to the supplied 185 Memory
        NativeTaskMemory nativeView = new NativeTaskMemoryView(memory);

        // 2. Execute the mature store algorithm exactly once
        //    Input: output = original RCX (from entry.volatileBits().rcxBits())
        //    Input: map = original RDX (from entry.volatileBits().rdxBits())
        //    Effect: writeInt64(originalRCX, originalRDX) -> 185Memory.writeQword
        //    Return: originalRCX
        long originalRcx = entry.volatileBits().rcxBits();
        long originalRdx = entry.volatileBits().rdxBits();

        long storeResult = MapRecord86F210206.store(nativeView, originalRcx, originalRdx);

        // 3. Construct NormalReturn with fresh RET semantics
        //    Physical RET reads return address from stack at entry.rspBits().
        //    Caller SP after RET is entry.rspBits() + 8.
        //    RAX is updated to storeResult (originalRCX).
        //    All other V/NV/XMM preserved from entry.

        long returnRip = memory.readQword(entry.rspBits());
        long callerRsp = entry.rspBits() + 8L;

        GovernmentPrimaryTail155Api.VolatileBits originalV = entry.volatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits originalNV = entry.nonvolatileBits();

        GovernmentPrimaryTail155Api.VolatileBits returnedV = new GovernmentPrimaryTail155Api.VolatileBits(
            storeResult,
            originalV.rcxBits(),
            originalV.rdxBits(),
            originalV.r8Bits(),
            originalV.r9Bits(),
            originalV.r10Bits(),
            originalV.r11Bits(),
            originalV.xmm0(),
            originalV.xmm1(),
            originalV.xmm2(),
            originalV.xmm3(),
            originalV.xmm4(),
            originalV.xmm5()
        );

        return new GovernmentCrtBoundary185Api.NormalReturn(
            returnedV,
            returnRip,
            callerRsp,
            originalNV
        );
    }

    private static final class NativeTaskMemoryView implements NativeTaskMemory {
        private final GovernmentCrtBoundary185Api.Memory delegate;

        NativeTaskMemoryView(GovernmentCrtBoundary185Api.Memory delegate) {
            this.delegate = delegate;
        }

        @Override
        public long readPointer(long address) {
            return delegate.readQword(address);
        }

        @Override
        public int readInt32(long address) {
            return delegate.readDword(address);
        }

        @Override
        public void writeInt32(long address, int value) {
            delegate.writeDword(address, value);
        }

        @Override
        public void writeInt64(long address, long value) {
            delegate.writeQword(address, value);
        }
    }
}