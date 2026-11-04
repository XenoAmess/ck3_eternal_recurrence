package org.xar.ck3.study.m6.posterror256;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;

public final class Error32GenericChildThrow259Test {
    private Error32GenericChildThrow259Test() { }

    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("No args");

        long imageBase = 0x0000000180000000L;
        long rsp = 0x0000000000310008L;
        boolean df = true;
        QueueFp604Api.Mxcsr mxcsr = new QueueFp604Api.Mxcsr(0x8041, 0xA5C5);

        GovernmentPrimaryTail155Api.Bits128 xmm0 = new GovernmentPrimaryTail155Api.Bits128(0x0102030405060708L, 0x1112131415161718L);
        GovernmentPrimaryTail155Api.Bits128 xmm1 = new GovernmentPrimaryTail155Api.Bits128(0x2122232425262728L, 0x3132333435363738L);
        GovernmentPrimaryTail155Api.Bits128 xmm2 = new GovernmentPrimaryTail155Api.Bits128(0x4142434445464748L, 0x5152535455565758L);
        GovernmentPrimaryTail155Api.Bits128 xmm3 = new GovernmentPrimaryTail155Api.Bits128(0x6162636465666768L, 0x7172737475767778L);
        GovernmentPrimaryTail155Api.Bits128 xmm4 = new GovernmentPrimaryTail155Api.Bits128(0x8182838485868788L, 0x9192939495969798L);
        GovernmentPrimaryTail155Api.Bits128 xmm5 = new GovernmentPrimaryTail155Api.Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L);
        GovernmentPrimaryTail155Api.Bits128 xmm6 = new GovernmentPrimaryTail155Api.Bits128(0xC1C2C3C4C5C6C7C8L, 0xD1D2D3D4D5D6D7D8L);

        GovernmentPrimaryTail155Api.VolatileBits v = new GovernmentPrimaryTail155Api.VolatileBits(
                0x9100000000000001L, 0x9200000000000002L, 0x9300000000000003L,
                0x9400000000000004L, 0x9500000000000005L, 0x9600000000000006L, 0x9700000000000007L,
                xmm0, xmm1, xmm2, xmm3, xmm4, xmm5);

        GovernmentPrimaryTail155Api.NonvolatileBits n = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x0B0000000000000BL, 0x0C0000000000000CL, 0x0D0000000000000DL, 0x0E0000000000000EL,
                0xFEDCBA9876543210L, 0x1300000000000013L, 0x1400000000000014L, 0x1500000000000015L, xmm6);

        GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(imageBase, rsp, v, n);
        PostState240Api.Input input = new PostState240Api.Input(entry, df, mxcsr, 0x00ABC259L);

        OwnedMemory mem = new OwnedMemory();
        mem.seed(0x000000000030FFD8L, 0xDEADC0DE13579BDFL);
        mem.seed(0x0000000000310008L, 0x00000001806A5A10L);
        mem.seed(0x0000000000320014L, 0x11223344);

        IllegalStateException sentinel = new IllegalStateException("sentinel");
        int[] callbackCount = new int[1];

        KnownAllocateErrorFp625.ErrorCalls childCalls = new KnownAllocateErrorFp625.ErrorCalls() {
            @Override public QueueFp604Api.Outcome invoke(KnownAllocateErrorFp625.ErrorCall frame) {
                callbackCount[0]++;
                if (callbackCount[0] != 1) throw new AssertionError("Multiple callbacks");

                GovernmentCrtBoundary185Api.Call call = frame.original();
                if (call.callSiteRva() != 0x423B190L) throw new AssertionError("Site");
                if (call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) throw new AssertionError("Kind");
                if (call.targetBits() != 0x424FC74L) throw new AssertionError("Target");
                if (call.rspBits() != 0x000000000030FFE0L) throw new AssertionError("PreSP");
                if (!call.volatileBits().equals(v)) throw new AssertionError("V");
                if (!call.nonvolatileBits().equals(n)) throw new AssertionError("N");

                GovernmentCrtBoundary185Api.Entry ce = frame.childEntry();
                if (ce.imageBaseBits() != imageBase) throw new AssertionError("Image");
                if (ce.rspBits() != 0x000000000030FFD8L) throw new AssertionError("ChildSP");
                if (!ce.volatileBits().equals(v)) throw new AssertionError("CV");
                if (!ce.nonvolatileBits().equals(n)) throw new AssertionError("CN");
                if (frame.returnRipBits() != 0x000000018423B195L) throw new AssertionError("RIP");
                if (!frame.directionFlagSet()) throw new AssertionError("DF");
                if (frame.preMxcsr() != mxcsr) throw new AssertionError("MxRef");
                if (frame.preMxcsr().valueBits() != 0x8041 || frame.preMxcsr().knownMaskBits() != 0xA5C5) throw new AssertionError("MxVal");

                mem.setActor("opaque-child");
                try {
                    long readVal = mem.readQword(0x000000000030FFD8L);
                    if (readVal != 0x000000018423B195L) throw new AssertionError("ReadVal");
                    mem.writeQword(0x0000000000310008L, 0x00000001806B6B20L);
                    mem.writeDword(0x0000000000320014L, 0xA1B2C3D4);
                    throw sentinel;
                } finally {
                    mem.setActor("source");
                }
            }
        };

        Error32PostState256 executor = new Error32PostState256(childCalls);

        try {
            QueueFp604Api.Outcome outcome = executor.execute(input, mem);
            throw new AssertionError("Returned outcome: " + outcome);
        } catch (IllegalStateException e) {
            if (e != sentinel) throw new AssertionError("Wrong exception");
        }

        if (callbackCount[0] != 1) throw new AssertionError("Callback count");

        String[] expectedLog = {
            "source W8 0x000000000030FFD8 0x000000018423B195",
            "opaque-child R8 0x000000000030FFD8 0x000000018423B195",
            "opaque-child W8 0x0000000000310008 0x00000001806B6B20",
            "opaque-child W4 0x0000000000320014 0xA1B2C3D4"
        };
        if (!Arrays.equals(mem.log.toArray(), expectedLog)) throw new AssertionError("Log mismatch");

        Map<Long, Integer> expectedBytes = new HashMap<>();
        for (int i = 0; i < 8; i++) expectedBytes.put(0x000000000030FFD8L + i, (int) ((0x000000018423B195L >>> (i * 8)) & 0xFF));
        for (int i = 0; i < 8; i++) expectedBytes.put(0x0000000000310008L + i, (int) ((0x00000001806B6B20L >>> (i * 8)) & 0xFF));
        for (int i = 0; i < 4; i++) expectedBytes.put(0x0000000000320014L + i, (0xA1B2C3D4 >>> (i * 8)) & 0xFF);

        if (mem.bytes.size() != 20) throw new AssertionError("Byte count");
        if (!expectedBytes.equals(mem.bytes)) throw new AssertionError("Byte mismatch");

        System.out.println("Error32GenericChildThrow259Test: 1 ordinary child exception case");
    }

    private static final class OwnedMemory implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Integer> bytes = new HashMap<>();
        private final java.util.ArrayList<String> log = new java.util.ArrayList<>();
        private String actor = "source";

        private void seed(long addr, long val) {
            for (int i = 0; i < 8; i++) bytes.put(addr + i, (int) ((val >>> (i * 8)) & 0xFF));
        }
        private void seed(long addr, int val) {
            for (int i = 0; i < 4; i++) bytes.put(addr + i, (val >>> (i * 8)) & 0xFF);
        }
        private void setActor(String a) { actor = a; }

        @Override public long readQword(long addr) {
            long val = 0;
            for (int i = 0; i < 8; i++) {
                Integer value = bytes.get(addr + i);
                if (value == null) throw new AssertionError("Unseeded owned byte " + Long.toHexString(addr + i));
                val |= ((long) value) << (i * 8);
            }
            log.add(actor + " R8 0x" + String.format("%016X", addr) + " 0x" + String.format("%016X", val));
            return val;
        }
        @Override public void writeQword(long addr, long val) {
            for (int i = 0; i < 8; i++) bytes.put(addr + i, (int) ((val >>> (i * 8)) & 0xFF));
            log.add(actor + " W8 0x" + String.format("%016X", addr) + " 0x" + String.format("%016X", val));
        }
        @Override public int readDword(long addr) { throw new AssertionError("Unexpected DWORD read"); }
        @Override public void writeDword(long addr, int val) {
            for (int i = 0; i < 4; i++) bytes.put(addr + i, (val >>> (i * 8)) & 0xFF);
            log.add(actor + " W4 0x" + String.format("%016X", addr) + " 0x" + String.format("%08X", val));
        }
        @Override public int readUnsignedByte(long addr) { throw new UnsupportedOperationException(); }
        @Override public void writeByte(long addr, int val) { throw new UnsupportedOperationException(); }
        @Override public int lockedXaddDword(long addr, int val) { throw new UnsupportedOperationException(); }
        @Override public GovernmentPrimaryTail155Api.Bits128 read128(long addr) { throw new UnsupportedOperationException(); }
        @Override public void write128(long addr, GovernmentPrimaryTail155Api.Bits128 val) { throw new UnsupportedOperationException(); }
    }
}