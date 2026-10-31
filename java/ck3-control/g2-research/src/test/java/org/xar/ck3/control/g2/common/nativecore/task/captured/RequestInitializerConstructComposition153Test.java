package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class RequestInitializerConstructComposition153Test {
@org.junit.jupiter.api.Test
public void initializerUsesConcreteConstructBeforeOutputPublication() {
    final long moduleBase = 0x140000000L;
    final long output = 0x20000L;
    final long descriptor = 0x30000L;
    final long scratch = 0x40000L;
    final long allocatedU = 0x50000L;
    final long destination = allocatedU + 0xB0L;
    final long sentinel = 0x1020304050607080L;
    final long rawLow = 0x1122334455667788L;
    final long rawHigh = 0x99AABBCCDDEEFF00L;
    final int scalar = 0x89ABCDEF;
    final long unsignedScalar = 0x89ABCDEFL;
    final Request140TestMemory memory = new Request140TestMemory();
    memory.bytes().map(output, 8);
    memory.bytes().map(descriptor, 0x29);
    memory.bytes().map(scratch, 0x29);
    memory.bytes().map(allocatedU, 0xE0);
    for (int i = 0; i < 8; i++) memory.bytes().seedByte(output + i, 0xDD);
    for (int i = 0; i < 0x29; i++) {
        memory.bytes().seedByte(descriptor + i, 0xBB);
        memory.bytes().seedByte(scratch + i, 0xCC);
    }
    for (int i = 0; i < 0xE0; i++) memory.bytes().seedByte(allocatedU + i, 0xAA);
    memory.bytes().seedInt64(output, sentinel);
    memory.bytes().seedInt64(descriptor, rawLow);
    memory.bytes().seedInt64(descriptor + 8L, rawHigh);
    memory.bytes().seedInt64(descriptor + 0x10L, 15L);
    memory.bytes().seedInt64(descriptor + 0x18L, 15L);
    memory.bytes().seedInt32(descriptor + 0x20L, scalar);
    memory.bytes().seedByte(descriptor + 0x28L, 1);

    final byte[] initialDescriptor = new byte[0x29];
    final byte[] initialScratch = new byte[0x29];
    final byte[] initialDestination = new byte[0x30];
    for (int i = 0; i < 0x29; i++) {
        initialDescriptor[i] = (byte) memory.bytes().peekUnsignedByte(descriptor + i);
        initialScratch[i] = (byte) memory.bytes().peekUnsignedByte(scratch + i);
    }
    for (int i = 0; i < 0x30; i++) {
        initialDestination[i] = (byte) memory.bytes().peekUnsignedByte(destination + i);
    }
    final byte[] expectedDescriptor = initialDescriptor.clone();
    final byte[] expectedScratch = initialScratch.clone();
    final byte[] expectedDestination = initialDestination.clone();
    java.nio.ByteBuffer.wrap(expectedDescriptor).order(java.nio.ByteOrder.LITTLE_ENDIAN)
            .putLong(0x10, 0L).putLong(0x18, 15L).put(0, (byte) 0);
    System.arraycopy(initialDescriptor, 0, expectedScratch, 0, 0x20);
    java.nio.ByteBuffer.wrap(expectedScratch).order(java.nio.ByteOrder.LITTLE_ENDIAN)
            .putInt(0x20, scalar).put(0x28, (byte) 1);
    java.nio.ByteBuffer.wrap(expectedDestination).order(java.nio.ByteOrder.LITTLE_ENDIAN)
            .putLong(0, rawLow).putLong(8, rawHigh)
            .putLong(0x10, 15L).putLong(0x18, 15L)
            .putInt(0x20, scalar).put(0x28, (byte) 1);

    final java.util.List<Request140TestMemory.Access> expectedDestinationAccesses = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, destination + 0x28L, 1, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x18L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, destination, 16, rawLow, rawHigh),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x10L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, destination + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, destination + 0x20L, 4, unsignedScalar, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, destination + 0x28L, 1, 1L, 0L));
    final java.util.List<Request140TestMemory.Access> expectedRawAccesses = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, descriptor, 16, rawLow, rawHigh),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, scratch, 16, rawLow, rawHigh),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, descriptor + 0x10L, 16, 15L, 15L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, scratch + 0x10L, 16, 15L, 15L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, scratch, 16, rawLow, rawHigh),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, destination, 16, rawLow, rawHigh));
    final java.util.List<Request140TestMemory.Access> expectedDescriptorAccesses = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ8, descriptor + 0x28L, 1, 1L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, descriptor, 16, rawLow, rawHigh),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, descriptor + 0x10L, 16, 15L, 15L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, descriptor + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, descriptor + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, descriptor, 1, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ32, descriptor + 0x20L, 4, unsignedScalar, 0L));
    final java.util.List<Request140TestMemory.Access> expectedScalarAccesses = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ32, descriptor + 0x20L, 4, unsignedScalar, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, scratch + 0x20L, 4, unsignedScalar, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ32, scratch + 0x20L, 4, unsignedScalar, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, destination + 0x20L, 4, unsignedScalar, 0L));
    final java.util.List<Request140TestMemory.Access> expectedConstructOrder = java.util.List.of(
            expectedDestinationAccesses.get(0),
            expectedDestinationAccesses.get(1),
            expectedDestinationAccesses.get(2),
            expectedDestinationAccesses.get(3),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, scratch + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, scratch + 0x10L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ128, scratch, 16, rawLow, rawHigh),
            expectedDestinationAccesses.get(4),
            expectedDestinationAccesses.get(5),
            expectedDestinationAccesses.get(6),
            expectedDestinationAccesses.get(7),
            expectedDestinationAccesses.get(8));
    final java.util.List<String> remainderCalls = new java.util.ArrayList<>();
    final int[] constructCalls = new int[2];
    final RequestConstruct855f00.Ports constructPorts = new RequestConstruct855f00.Ports() {
        @Override
        public long call856db0(long rcx) {
            constructCalls[0]++;
            throw new AssertionError("short Construct must not allocate");
        }
        @Override
        public void call4226860(long rcx, long rdx, long r8) {
            constructCalls[1]++;
            throw new AssertionError("short Construct must not call the opaque copier");
        }
    };
    final RequestStringConsumers.InitializerRemainder remainder =
            new RequestStringConsumers.InitializerRemainder() {
        @Override
        public long call4223b94(int ecx) {
            org.junit.jupiter.api.Assertions.assertEquals(0xE0, ecx);
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(), remainderCalls);
            remainderCalls.add("allocate");
            return allocatedU;
        }
        @Override
        public void call856050(long rcx) {
            org.junit.jupiter.api.Assertions.assertEquals(scratch, rcx);
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("allocate"), remainderCalls);
            remainderCalls.add("cleanup");
            org.junit.jupiter.api.Assertions.assertEquals(sentinel, memory.bytes().peekInt64(output));
            final java.util.List<Request140TestMemory.Access> trace = memory.trace();
            org.junit.jupiter.api.Assertions.assertTrue(trace.stream().noneMatch(a -> a.address() == output));
            org.junit.jupiter.api.Assertions.assertEquals(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ8, scratch + 0x28L, 1, 1L, 0L),
                    trace.get(trace.size() - 1));
            org.junit.jupiter.api.Assertions.assertEquals(expectedDestinationAccesses,
                    trace.stream().filter(a -> a.address() >= destination && a.address() < destination + 0x30L).toList());
            org.junit.jupiter.api.Assertions.assertEquals(expectedRawAccesses,
                    trace.stream().filter(a -> a.op() == Request140TestMemory.Op.READ128
                            || a.op() == Request140TestMemory.Op.WRITE128).toList());
            org.junit.jupiter.api.Assertions.assertEquals(expectedDescriptorAccesses,
                    trace.stream().filter(a -> a.address() >= descriptor && a.address() < descriptor + 0x29L).toList());
            org.junit.jupiter.api.Assertions.assertEquals(expectedScalarAccesses,
                    trace.stream().filter(a -> (a.op() == Request140TestMemory.Op.READ32
                            || a.op() == Request140TestMemory.Op.WRITE32)
                            && (a.address() == descriptor + 0x20L || a.address() == scratch + 0x20L
                            || a.address() == destination + 0x20L)).toList());
            org.junit.jupiter.api.Assertions.assertEquals(expectedConstructOrder,
                    trace.stream().filter(a -> (a.address() >= destination && a.address() < destination + 0x30L)
                            || (a.op() == Request140TestMemory.Op.READ64
                            && (a.address() == scratch + 0x18L || a.address() == scratch + 0x10L))
                            || (a.op() == Request140TestMemory.Op.READ128 && a.address() == scratch)).toList());
            for (int i = 0; i < expectedDescriptor.length; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(expectedDescriptor[i] & 0xFF,
                        memory.bytes().peekUnsignedByte(descriptor + i), "cleanup descriptor byte " + i);
                org.junit.jupiter.api.Assertions.assertEquals(expectedScratch[i] & 0xFF,
                        memory.bytes().peekUnsignedByte(scratch + i), "cleanup scratch byte " + i);
            }
            for (int i = 0; i < expectedDestination.length; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(expectedDestination[i] & 0xFF,
                        memory.bytes().peekUnsignedByte(destination + i), "cleanup destination byte " + i);
            }
        }
    };
    final RequestE92780.Ports adapter =
            RequestStringConsumers.initializerPorts(memory, remainder, constructPorts);
    memory.clearTrace();
    final long result = RequestE92780.initialize(moduleBase, output, descriptor, scratch, memory, adapter);
    org.junit.jupiter.api.Assertions.assertEquals(output, result);
    org.junit.jupiter.api.Assertions.assertEquals(allocatedU, memory.bytes().peekInt64(output));
    org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("allocate", "cleanup"), remainderCalls);
    org.junit.jupiter.api.Assertions.assertArrayEquals(new int[2], constructCalls);
    final java.util.List<Request140TestMemory.Access> finalTrace = memory.trace();
    org.junit.jupiter.api.Assertions.assertEquals(
            java.util.List.of(new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, output, 8, allocatedU, 0L)),
            finalTrace.stream().filter(a -> a.address() == output).toList());
    org.junit.jupiter.api.Assertions.assertEquals(
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, output, 8, allocatedU, 0L),
            finalTrace.get(finalTrace.size() - 1));
    for (int i = 0; i < expectedDescriptor.length; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedDescriptor[i] & 0xFF,
                memory.bytes().peekUnsignedByte(descriptor + i), "final descriptor byte " + i);
        org.junit.jupiter.api.Assertions.assertEquals(expectedScratch[i] & 0xFF,
                memory.bytes().peekUnsignedByte(scratch + i), "final scratch byte " + i);
    }
    for (int i = 0; i < expectedDestination.length; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedDestination[i] & 0xFF,
                memory.bytes().peekUnsignedByte(destination + i), "final destination byte " + i);
    }
}


}
