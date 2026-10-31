package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class RequestBlock856db0NormalTest {
@org.junit.jupiter.api.Test public void normalPathsPreserveRawSizeAndHeader() {
    {
        long size = 0L;
        int[] callCount = new int[]{0};
        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            public long call4223b94(long rcx) {
                callCount[0]++;
                return 0L;
            }
        };
        Request140TestMemory m = new Request140TestMemory();
        long result = RequestBlock856db0.execute(size, m, ports);
        java.util.List<Request140TestMemory.Access> trace = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(0L, result);
        org.junit.jupiter.api.Assertions.assertEquals(0, callCount[0]);
        org.junit.jupiter.api.Assertions.assertEquals(0, trace.size());
    }
    {
        long size = 1L;
        int[] callCount = new int[]{0};
        long[] cbArg = new long[1];
        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            public long call4223b94(long rcx) {
                callCount[0]++;
                cbArg[0] = rcx;
                return 0L;
            }
        };
        Request140TestMemory m = new Request140TestMemory();
        long result = RequestBlock856db0.execute(size, m, ports);
        java.util.List<Request140TestMemory.Access> trace = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(1, callCount[0]);
        org.junit.jupiter.api.Assertions.assertEquals(1L, cbArg[0]);
        org.junit.jupiter.api.Assertions.assertEquals(0L, result);
        org.junit.jupiter.api.Assertions.assertEquals(0, trace.size());
    }
    {
        long size = 4095L;
        long expectedRet = 0x1234567890ABCDEFL;
        int[] callCount = new int[]{0};
        long[] cbArg = new long[1];
        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            public long call4223b94(long rcx) {
                callCount[0]++;
                cbArg[0] = rcx;
                return expectedRet;
            }
        };
        Request140TestMemory m = new Request140TestMemory();
        long result = RequestBlock856db0.execute(size, m, ports);
        java.util.List<Request140TestMemory.Access> trace = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(1, callCount[0]);
        org.junit.jupiter.api.Assertions.assertEquals(4095L, cbArg[0]);
        org.junit.jupiter.api.Assertions.assertEquals(expectedRet, result);
        org.junit.jupiter.api.Assertions.assertEquals(0, trace.size());
    }
    {
        long size = 4096L;
        long adjusted = 4135L;
        long H = 0x100010L;
        long expectedResult = 0x100020L;
        long headerAddr = 0x100018L;
        Request140TestMemory m = new Request140TestMemory();
        m.bytes().map(0x100000L, 64);
        for (long i = 0x100000L; i < 0x100040L; i++) {
            m.bytes().seedByte(i, 0xAA);
        }
        final byte[] expectedImage = new byte[64];
        for (int j = 0; j < 64; j++) expectedImage[j] = (byte) m.bytes().peekUnsignedByte(0x100000L + j);
        int[] callCount = new int[]{0};
        long[] cbArg = new long[1];
        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            public long call4223b94(long rcx) {
                callCount[0]++;
                cbArg[0] = rcx;
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(), m.trace());
                for (int j = 0; j < 64; j++) org.junit.jupiter.api.Assertions.assertEquals(expectedImage[j] & 255, m.bytes().peekUnsignedByte(0x100000L + j), "callback before headerstore " + j);
                return H;
            }
        };
        long result = RequestBlock856db0.execute(size, m, ports);
        java.util.List<Request140TestMemory.Access> trace = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(1, callCount[0]);
        org.junit.jupiter.api.Assertions.assertEquals(adjusted, cbArg[0]);
        org.junit.jupiter.api.Assertions.assertEquals(expectedResult, result);
        org.junit.jupiter.api.Assertions.assertEquals(1, trace.size());
        Request140TestMemory.Access acc = trace.get(0);
        org.junit.jupiter.api.Assertions.assertEquals(Request140TestMemory.Op.WRITE64, acc.op());
        org.junit.jupiter.api.Assertions.assertEquals(headerAddr, acc.address());
        org.junit.jupiter.api.Assertions.assertEquals(8, acc.width());
        org.junit.jupiter.api.Assertions.assertEquals(H, acc.low());
        org.junit.jupiter.api.Assertions.assertEquals(0L, acc.high());
        org.junit.jupiter.api.Assertions.assertEquals(H, m.bytes().peekInt64(headerAddr));
        for (int j = 0; j < 8; j++) expectedImage[(int) (headerAddr - 0x100000L) + j] = (byte) (H >>> (8 * j));
        for (int j = 0; j < 64; j++) org.junit.jupiter.api.Assertions.assertEquals(expectedImage[j] & 255, m.bytes().peekUnsignedByte(0x100000L + j), "whole headerimage " + j);
    }
    {
        long size = Long.MAX_VALUE;
        long adjusted = 0x8000000000000026L;
        long H = 0x100020L;
        long expectedResult = 0x100040L;
        long headerAddr = 0x100038L;
        Request140TestMemory m = new Request140TestMemory();
        m.bytes().map(0x100000L, 64);
        for (long i = 0x100000L; i < 0x100040L; i++) {
            m.bytes().seedByte(i, 0xBB);
        }
        final byte[] expectedImage = new byte[64];
        for (int j = 0; j < 64; j++) expectedImage[j] = (byte) m.bytes().peekUnsignedByte(0x100000L + j);
        int[] callCount = new int[]{0};
        long[] cbArg = new long[1];
        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            public long call4223b94(long rcx) {
                callCount[0]++;
                cbArg[0] = rcx;
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(), m.trace());
                for (int j = 0; j < 64; j++) org.junit.jupiter.api.Assertions.assertEquals(expectedImage[j] & 255, m.bytes().peekUnsignedByte(0x100000L + j), "callback before headerstore " + j);
                return H;
            }
        };
        long result = RequestBlock856db0.execute(size, m, ports);
        java.util.List<Request140TestMemory.Access> trace = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(1, callCount[0]);
        org.junit.jupiter.api.Assertions.assertEquals(adjusted, cbArg[0]);
        org.junit.jupiter.api.Assertions.assertEquals(expectedResult, result);
        org.junit.jupiter.api.Assertions.assertEquals(1, trace.size());
        Request140TestMemory.Access acc = trace.get(0);
        org.junit.jupiter.api.Assertions.assertEquals(Request140TestMemory.Op.WRITE64, acc.op());
        org.junit.jupiter.api.Assertions.assertEquals(headerAddr, acc.address());
        org.junit.jupiter.api.Assertions.assertEquals(8, acc.width());
        org.junit.jupiter.api.Assertions.assertEquals(H, acc.low());
        org.junit.jupiter.api.Assertions.assertEquals(0L, acc.high());
        org.junit.jupiter.api.Assertions.assertEquals(H, m.bytes().peekInt64(headerAddr));
        for (int j = 0; j < 8; j++) expectedImage[(int) (headerAddr - 0x100000L) + j] = (byte) (H >>> (8 * j));
        for (int j = 0; j < 64; j++) org.junit.jupiter.api.Assertions.assertEquals(expectedImage[j] & 255, m.bytes().peekUnsignedByte(0x100000L + j), "whole headerimage " + j);
    }
}

}
