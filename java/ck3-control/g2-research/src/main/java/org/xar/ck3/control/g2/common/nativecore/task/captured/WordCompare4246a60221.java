package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.word226.WordCompare226Api;
import org.xar.ck3.research.m3.word226.WordCompare4246A60;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213.Memory16;

public final class WordCompare4246a60221 {
    private WordCompare4246a60221() { }

    public static NormalReturn execute(Entry entry, Memory16 memory) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);

        // 1. Construct the algorithm instance and execute it exactly once
        WordCompare4246A60 algorithm = new WordCompare4246A60();
        WordCompare226Api.Memory view = new MemoryView(memory);

        // Inputs: RCX, RDX, R8 from entry volatile bits (full 64-bit)
        long rcx = entry.volatileBits().rcxBits();
        long rdx = entry.volatileBits().rdxBits();
        long r8 = entry.volatileBits().r8Bits();

        WordCompare226Api.Result result = algorithm.execute(view, rcx, rdx, r8);

        // 2. Construct the final VolatileBits based on the result and entry
        VolatileBits v = entry.volatileBits();

        long finalRax;
        long finalRcx;
        long finalRdx;
        long finalR8;

        if (result.finalReadsOccurred()) {
            // Flag true: use result fields
            finalRax = Integer.toUnsignedLong(result.difference32());
            finalRcx = Integer.toUnsignedLong(result.finalRightWord());
            finalRdx = result.finalRightCursor();
            finalR8 = result.remainingR8();
        } else {
            // Flag false: preserve entry RCX/RDX/R8, RAX is diff (0)
            finalRax = Integer.toUnsignedLong(result.difference32()); // Should be 0
            finalRcx = v.rcxBits();
            finalRdx = v.rdxBits();
            finalR8 = v.r8Bits();
        }

        // R9, R10, R11, XMM0..5 remain unchanged from entry
        VolatileBits finalV = new VolatileBits(
            finalRax,
            finalRcx,
            finalRdx,
            finalR8,
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

        // 3. Fresh read of return RIP from stack top (E)
        long e = entry.rspBits();
        long retRip = memory.readQword(e);

        // 4. Construct NormalReturn
        // CallerSP = E + 8 (simulating the pop of the return address)
        // NonvolatileBits are exactly the entry's nonvolatile bits (no changes)
        return new NormalReturn(finalV, retRip, e + 8L, entry.nonvolatileBits());
    }

    private static final class MemoryView implements WordCompare226Api.Memory {
        private final TerminalTailTarget42421c8213.Memory16 memory;

        MemoryView(TerminalTailTarget42421c8213.Memory16 memory) {
            this.memory = Objects.requireNonNull(memory);
        }

        @Override public long readPointer(long address) {
            return memory.readQword(address);
        }

        @Override public int readInt32(long address) {
            return memory.readDword(address);
        }

        @Override public void writeInt32(long address, int value) {
            memory.writeDword(address, value);
        }

        @Override public void writeInt64(long address, long value) {
            memory.writeQword(address, value);
        }

        @Override public int readWord16(long address) {
            return memory.readUnsigned16(address);
        }
    }
}