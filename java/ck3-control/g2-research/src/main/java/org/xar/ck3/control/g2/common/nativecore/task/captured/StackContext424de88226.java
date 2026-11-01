package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.stack227.StackContext227Api;
import org.xar.ck3.research.m3.stack227.StackContext424DE88;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class StackContext424de88226 {
    private StackContext424de88226() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        long e = entry.rspBits();
        long image = entry.imageBaseBits();
        long w = e - 0x38L;
        VolatileBits entryV = entry.volatileBits();
        NonvolatileBits entryNV = entry.nonvolatileBits();

        // Mutable carrier for the actual whole VolatileBits reply from the opaque child
        VolatileBits[] replyCarrier = new VolatileBits[1];

        // Native4 view forwarding to same provided 185 memory
        NativeTaskMemory nativeView = new Native4View(memory);

        // Ports implementation that prepares actual V, writes physical CALL return,
        // invokes 185 Call, stores whole reply in carrier, returns only RAX to old M3
        StackContext227Api.Ports ports = new PortsImpl(image, w, entryV, entryNV, calls, replyCarrier, memory);

        // Context for old M3 execute
        StackContext227Api.Context context = new StackContext227Api.Context(e, entryV.rcxBits());

        // Run old M3 business exactly once
        StackContext424DE88.execute(nativeView, ports, context);

        // After old execute returns normally: source only ADD SP 0x38 and RET
        // Fresh read of return address at [E]
        long actualRetRip = memory.readQword(e);

        // NormalReturn with actual whole callback reply, actual RET, caller SP = E+8, entry NV
        return new GovernmentCrtBoundary185Api.NormalReturn(
            replyCarrier[0],
            actualRetRip,
            e + 8L,
            entryNV
        );
    }

    private static final class Native4View implements NativeTaskMemory {
        private final GovernmentCrtBoundary185Api.Memory mem;
        Native4View(GovernmentCrtBoundary185Api.Memory mem) {
            this.mem = Objects.requireNonNull(mem);
        }
        @Override public long readPointer(long address) { return mem.readQword(address); }
        @Override public int readInt32(long address) { return mem.readDword(address); }
        @Override public void writeInt32(long address, int value) { mem.writeDword(address, value); }
        @Override public void writeInt64(long address, long value) { mem.writeQword(address, value); }
    }

    private static final class PortsImpl implements StackContext227Api.Ports {
        private final long image;
        private final long w;
        private final VolatileBits entryV;
        private final NonvolatileBits entryNV;
        private final GovernmentCrtBoundary185Api.Calls calls;
        private final VolatileBits[] replyCarrier;
        private final GovernmentCrtBoundary185Api.Memory mem;

        PortsImpl(long image, long w, VolatileBits entryV, NonvolatileBits entryNV,
                  GovernmentCrtBoundary185Api.Calls calls, VolatileBits[] replyCarrier,
                  GovernmentCrtBoundary185Api.Memory mem) {
            this.image = image;
            this.w = w;
            this.entryV = entryV;
            this.entryNV = entryNV;
            this.calls = calls;
            this.replyCarrier = replyCarrier;
            this.mem = mem;
        }

        @Override public long call424db74(NativeTaskMemory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
            // Prepare actual full V for the child call
            // RAX=2L, RCX=passed, RDX=passed, R8=passed, R9=passed, R10=entryV.r10Bits(), R11=E (w+0x38), XMM0..5 exact entryV
            long e = w + 0x38L;
            VolatileBits actualV = new VolatileBits(
                2L,
                rcx,
                rdx,
                r8,
                r9,
                entryV.r10Bits(),
                e,
                entryV.xmm0(),
                entryV.xmm1(),
                entryV.xmm2(),
                entryV.xmm3(),
                entryV.xmm4(),
                entryV.xmm5()
            );

            long pushAddr = w - 8L;
            long retAddr = image + 0x424DEBDL;
            mem.writeQword(pushAddr, retAddr);

            // Invoke 185 Call
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                0x424DEB8L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x424DB74L,
                w,
                actualV,
                entryNV
            );

            VolatileBits reply = calls.invoke(call);
            Objects.requireNonNull(reply);

            // Store whole reply in carrier
            replyCarrier[0] = reply;

            // Return only actual RAX to old M3 Port
            return reply.raxBits();
        }
    }
}