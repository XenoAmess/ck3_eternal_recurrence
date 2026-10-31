package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class RequestCopyConstructComposition154Test {
@org.junit.jupiter.api.Test public void constructCopiesSeventeenBytesThroughConcreteShortCopy() {
    Request140TestMemory memory = new Request140TestMemory();
    Idler79eRegressionHost.Memory backing = memory.bytes();

    long source = 0x100000L;
    long destination = 0x100100L;
    long indirectData = 0x100200L;
    long allocatedQ = 0x100300L;

    backing.map(source, 32);
    backing.map(destination, 32);
    backing.map(indirectData, 17);
    backing.map(allocatedQ, 32);

    for (long i = 0; i < 32; i++) backing.seedByte(source + i, 0xAA);
    for (long i = 0; i < 32; i++) backing.seedByte(destination + i, 0xBB);
    for (long i = 0; i < 32; i++) backing.seedByte(allocatedQ + i, 0xCC);

    long dataPatternLow = 0x0102030405060708L;
    long dataPatternHigh = 0x090A0B0C0D0E0F10L;
    for (int i = 0; i < 8; i++) backing.seedByte(indirectData + i, (int)((dataPatternLow >>> (i * 8)) & 0xFF));
    for (int i = 0; i < 8; i++) backing.seedByte(indirectData + 8 + i, (int)((dataPatternHigh >>> (i * 8)) & 0xFF));
    backing.seedByte(indirectData + 16, 0);

    backing.seedInt64(source, indirectData);
    backing.seedInt64(source + 0x10, 16L);
    backing.seedInt64(source + 0x18, 31L);

    byte[] sourceSnapshot = new byte[32];
    for (int i = 0; i < 32; i++) sourceSnapshot[i] = (byte) backing.peekUnsignedByte(source + i);
    byte[] destSnapshot = new byte[32];
    for (int i = 0; i < 32; i++) destSnapshot[i] = (byte) backing.peekUnsignedByte(destination + i);
    byte[] qSnapshot = new byte[32];
    for (int i = 0; i < 32; i++) qSnapshot[i] = (byte) backing.peekUnsignedByte(allocatedQ + i);
    byte[] dataSnapshot = new byte[17];
    for (int i = 0; i < 17; i++) dataSnapshot[i] = (byte) backing.peekUnsignedByte(indirectData + i);

    long expLow0 = 0L, expHigh0 = 0L, expLow1 = 0L, expHigh1 = 0L;
    for (int i = 0; i < 8; i++) {
        expLow0 |= ((long)(dataSnapshot[i] & 0xFF)) << (i * 8);
        expHigh0 |= ((long)(dataSnapshot[8 + i] & 0xFF)) << (i * 8);
        expLow1 |= ((long)(dataSnapshot[1 + i] & 0xFF)) << (i * 8);
        expHigh1 |= ((long)(dataSnapshot[9 + i] & 0xFF)) << (i * 8);
    }

    java.util.List<String> log = new java.util.ArrayList<>();
    long[] allocArgs = new long[1];
    long[] copyArgs = new long[3];
    int[] fallbackCount = new int[1];
    int[] allocCount = new int[1];
    int[] copyCount = new int[1];

    RequestConstruct855f00.Ports ports = new RequestConstruct855f00.Ports() {
        @Override
        public long call856db0(long rcx) {
            allocArgs[0] = rcx;
            allocCount[0]++;
            log.add("alloc1");
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination + 0x10));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination + 0x18));
            for (int i = 8; i < 16; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(destSnapshot[i],
                        (byte) backing.peekUnsignedByte(destination + i));
            }
            return allocatedQ;
        }
        @Override
        public void call4226860(long rcx, long rdx, long r8) {
            copyArgs[0] = rcx;
            copyArgs[1] = rdx;
            copyArgs[2] = r8;
            copyCount[0]++;
            log.add("copy1");
            org.junit.jupiter.api.Assertions.assertEquals(allocatedQ, backing.peekInt64(destination));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination + 0x10));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination + 0x18));
            org.junit.jupiter.api.Assertions.assertEquals(allocatedQ, rcx);
            org.junit.jupiter.api.Assertions.assertEquals(indirectData, rdx);
            org.junit.jupiter.api.Assertions.assertEquals(17L, r8);

            RequestCopy16To32.Remainder remainder = new RequestCopy16To32.Remainder() {
                @Override
                public void call4226860(long d, long s, long l) {
                    fallbackCount[0]++;
                    throw new AssertionError("Remainder should not be called");
                }
            };
            RequestCopy16To32.copyOrDelegate(rcx, rdx, r8, memory, remainder);

            for (int i = 0; i < 17; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(dataSnapshot[i], (byte) backing.peekUnsignedByte(allocatedQ + i));
            }
            for (int i = 17; i < 32; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(qSnapshot[i], (byte) backing.peekUnsignedByte(allocatedQ + i));
            }
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination + 0x10));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(destination + 0x18));
        }
    };

    long result = RequestConstruct855f00.construct(destination, source, memory, ports);

    org.junit.jupiter.api.Assertions.assertEquals(destination, result);
    org.junit.jupiter.api.Assertions.assertEquals(1, allocCount[0]);
    org.junit.jupiter.api.Assertions.assertEquals(1, copyCount[0]);
    org.junit.jupiter.api.Assertions.assertEquals(0, fallbackCount[0]);
    org.junit.jupiter.api.Assertions.assertEquals(32L, allocArgs[0]);
    org.junit.jupiter.api.Assertions.assertEquals(allocatedQ, copyArgs[0]);
    org.junit.jupiter.api.Assertions.assertEquals(indirectData, copyArgs[1]);
    org.junit.jupiter.api.Assertions.assertEquals(17L, copyArgs[2]);

    java.util.List<Request140TestMemory.Access> expectedTrace = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x18L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, source + 0x18L, 8, 31L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, source + 0x10L, 8, 16L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, source, 8, indirectData, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination, 8, allocatedQ, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, indirectData, 16, expLow0, expHigh0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, indirectData + 1L, 16, expLow1, expHigh1),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, allocatedQ, 16, expLow0, expHigh0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, allocatedQ + 1L, 16, expLow1, expHigh1),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x10L, 8, 16L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x18L, 8, 31L, 0L));
    org.junit.jupiter.api.Assertions.assertEquals(expectedTrace, memory.trace());

    byte[] expectedDestination = destSnapshot.clone();
    java.nio.ByteBuffer.wrap(expectedDestination).order(java.nio.ByteOrder.LITTLE_ENDIAN)
            .putLong(0, allocatedQ).putLong(0x10, 16L).putLong(0x18, 31L);
    for (int i = 0; i < 32; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedDestination[i],
                (byte) backing.peekUnsignedByte(destination + i), "destination byte " + i);
    }

    for (int i = 0; i < 32; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(sourceSnapshot[i], (byte) backing.peekUnsignedByte(source + i));
    }
    org.junit.jupiter.api.Assertions.assertEquals(indirectData, backing.peekInt64(source));
    org.junit.jupiter.api.Assertions.assertEquals(16L, backing.peekInt64(source + 0x10));
    org.junit.jupiter.api.Assertions.assertEquals(31L, backing.peekInt64(source + 0x18));

    for (int i = 0; i < 17; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(dataSnapshot[i], (byte) backing.peekUnsignedByte(indirectData + i));
    }

    for (int i = 0; i < 17; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(dataSnapshot[i], (byte) backing.peekUnsignedByte(allocatedQ + i));
    }
    for (int i = 17; i < 32; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(qSnapshot[i], (byte) backing.peekUnsignedByte(allocatedQ + i));
    }

    org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("alloc1", "copy1"), log);
}


}
