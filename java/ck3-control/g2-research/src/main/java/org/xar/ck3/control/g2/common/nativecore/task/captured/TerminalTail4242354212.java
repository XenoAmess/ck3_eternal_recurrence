package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m3.tail212.Tail4242354;
import org.xar.ck3.research.m3.tail212.TerminalTail212Api;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class TerminalTail4242354212 {
    private TerminalTail4242354212() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {

        Terminal207Api.Memory memView = new MemoryView(memory);

        // Capture the NormalReturn object from the tail call inside the callback
        GovernmentCrtBoundary185Api.NormalReturn[] captured = new GovernmentCrtBoundary185Api.NormalReturn[1];

        TerminalTail212Api.Ports ports = new TerminalTail212Api.Ports() {
            @Override
            public long tail42421c8(Terminal207Api.Memory m, long siteRva, long rcx, int edx, int r8d) {
                // Construct actual 155 VolatileBits from original incoming V
                GovernmentPrimaryTail155Api.VolatileBits originalV = entry.volatileBits();

                GovernmentPrimaryTail155Api.VolatileBits actualV = new GovernmentPrimaryTail155Api.VolatileBits(
                    originalV.raxBits(),
                    rcx,
                    Integer.toUnsignedLong(edx),
                    Integer.toUnsignedLong(r8d),
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

                // Construct Tail Entry preserving original image, SP, NV and carrying actual pre-tail fullV
                GovernmentCrtBoundary185Api.Entry tailEntry = new GovernmentCrtBoundary185Api.Entry(
                    entry.imageBaseBits(),
                    entry.rspBits(),
                    actualV,
                    entry.nonvolatileBits()
                );

                // Call calls.tail with the actual opaque fullV tail edge
                GovernmentCrtBoundary185Api.NormalReturn nr = calls.tail(new GovernmentCrtBoundary185Api.Tail(
                    siteRva,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x42421C8L,
                    tailEntry
                ));

                // Save the exact actual NormalReturn object
                captured[0] = nr;

                // Return actual NR RAX to satisfy old business long API
                return nr.volatileBits().raxBits();
            }
        };

        // Reuse actual Tail4242354.execute exactly ONCE
        Tail4242354.execute(memView, ports, entry.volatileBits().rcxBits());

        // Return the exact captured whole 185 NormalReturn OBJECT
        return captured[0];
    }

    private static final class MemoryView implements Terminal207Api.Memory {
        private final GovernmentCrtBoundary185Api.Memory delegate;

        MemoryView(GovernmentCrtBoundary185Api.Memory delegate) {
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

        @Override
        public int readUnsigned8(long address) {
            return delegate.readUnsignedByte(address);
        }
    }
}