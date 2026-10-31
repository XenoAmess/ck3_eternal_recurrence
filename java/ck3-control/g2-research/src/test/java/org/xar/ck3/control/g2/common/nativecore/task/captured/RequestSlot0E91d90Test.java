package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import java.util.List;
public final class RequestSlot0E91d90Test {
    @Test public void normalFlagsPreserveKnownOrderAndReturnedReceiver() {
        Request140TestMemory memory = new Request140TestMemory();
        Idler79eRegressionHost.Memory backing = memory.bytes();

        long moduleBase = backing.allocate(0x1000);
        long receiver = backing.allocate(0x100);
        final long originalVptr = 0x76543210FEDCBA98L;
        final long vptr = moduleBase + 0x44FC298L;
        final long releaseMutation = 0x89ABCDEF01234567L;

        // Seed receiver with poison values to detect unintended overwrites
        for (int i = 0; i < 0x100; i++) {
            backing.seedByte(receiver + i, 0xAA);
        }

        backing.seedInt64(receiver, originalVptr);

        // Case 1: Flag at receiver+0xD8 is 0 (skip first cleanup), rawEdx bit0 clear (skip release)
        backing.seedByte(receiver + 0xD8, 0);
        backing.seedInt64(receiver + 0x70, 0x1111L);
        backing.seedInt64(receiver + 0x48, 0x2222L);
        backing.seedInt64(receiver + 0x28, 0x3333L);

        final long[] capturedRcx = new long[10];
        final int[] capturedEdx = new int[10];
        final int[] callCount = new int[1];

        RequestSlot0E91d90.Ports ports = new RequestSlot0E91d90.Ports() {
            @Override
            public void call856050(long rcx) {
                long expectedAtCallback = (rcx == receiver + 0xB0L || rcx == receiver + 0x70L)
                        ? originalVptr : vptr;
                org.junit.jupiter.api.Assertions.assertEquals(expectedAtCallback, backing.peekInt64(receiver),
                        "Vptr at cleanup callback");
                if (rcx == receiver + 0x28L) backing.seedByte(receiver + 0x17L, 0x4D);
                capturedRcx[callCount[0]] = rcx;
                callCount[0]++;
            }
            @Override
            public void call4223f44(long rcx, int edx) {
                org.junit.jupiter.api.Assertions.assertEquals(vptr, backing.peekInt64(receiver),
                        "Vptr before opaque release effect");
                backing.seedInt64(receiver, releaseMutation);
                capturedRcx[callCount[0]] = rcx;
                capturedEdx[callCount[0]] = edx;
                callCount[0]++;
            }
        };

        final int[] expectedImage1 = new int[0x100];
        for (int i = 0; i < expectedImage1.length; i++) expectedImage1[i] = backing.peekUnsignedByte(receiver + i);
        for (int i = 0; i < 8; i++) expectedImage1[i] = (int) (vptr >>> (8 * i)) & 0xFF;
        expectedImage1[0x17] = 0x4D;
        long result = RequestSlot0E91d90.invoke(moduleBase, receiver, 0x02, memory, ports);
        final java.util.List<Request140TestMemory.Access> trace1 = memory.trace();

        org.junit.jupiter.api.Assertions.assertEquals(receiver, result, "Return must be original receiver");
        org.junit.jupiter.api.Assertions.assertEquals(3, callCount[0], "Expected 3 calls for flag=0, bit0=0");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x70L, capturedRcx[0], "First call856050 rcx (LEA receiver+70)");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x48L, capturedRcx[1], "Second call856050 rcx (LEA receiver+48)");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x28L, capturedRcx[2], "Third call856050 rcx (LEA receiver+28)");

        org.junit.jupiter.api.Assertions.assertEquals(vptr, backing.peekInt64(receiver), "Vptr written to receiver");

        org.junit.jupiter.api.Assertions.assertEquals(2, trace1.size(), "Expected 2 memory ops for Case 1");
        org.junit.jupiter.api.Assertions.assertEquals(Request140TestMemory.Op.READ8, trace1.get(0).op(), "Op0 type");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0xD8L, trace1.get(0).address(), "Op0 address");
        org.junit.jupiter.api.Assertions.assertEquals(1, trace1.get(0).width(), "Op0 width");
        org.junit.jupiter.api.Assertions.assertEquals(0L, trace1.get(0).low(), "Op0 low");
        org.junit.jupiter.api.Assertions.assertEquals(0L, trace1.get(0).high(), "Op0 high");
        org.junit.jupiter.api.Assertions.assertEquals(Request140TestMemory.Op.WRITE64, trace1.get(1).op(), "Op1 type");
        org.junit.jupiter.api.Assertions.assertEquals(receiver, trace1.get(1).address(), "Op1 address");
        org.junit.jupiter.api.Assertions.assertEquals(8, trace1.get(1).width(), "Op1 width");
        org.junit.jupiter.api.Assertions.assertEquals(vptr, trace1.get(1).low(), "Op1 low");
        org.junit.jupiter.api.Assertions.assertEquals(0L, trace1.get(1).high(), "Op1 high");
        for (int i = 0; i < expectedImage1.length; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expectedImage1[i], backing.peekUnsignedByte(receiver + i),
                    "First receiver byte " + i);
        }

        // Case 2: Flag at receiver+0xD8 is 0x80 (nonzero, trigger first cleanup), rawEdx bit0 set (trigger release)
        memory.clearTrace();
        callCount[0] = 0;
        for (int i = 0; i < 0x100; i++) backing.seedByte(receiver + i, 0xAA);
        backing.seedInt64(receiver, originalVptr);

        backing.seedByte(receiver + 0xD8, 0x80);
        backing.seedInt64(receiver + 0x70, 0x1111L);
        backing.seedInt64(receiver + 0x48, 0x2222L);
        backing.seedInt64(receiver + 0x28, 0x3333L);

        final int[] expectedImage2 = new int[0x100];
        for (int i = 0; i < expectedImage2.length; i++) expectedImage2[i] = backing.peekUnsignedByte(receiver + i);
        for (int i = 0; i < 8; i++) expectedImage2[i] = (int) (releaseMutation >>> (8 * i)) & 0xFF;
        expectedImage2[0x17] = 0x4D;
        result = RequestSlot0E91d90.invoke(moduleBase, receiver, 0x03, memory, ports);
        final java.util.List<Request140TestMemory.Access> trace2 = memory.trace();

        org.junit.jupiter.api.Assertions.assertEquals(receiver, result, "Return must be original receiver");
        org.junit.jupiter.api.Assertions.assertEquals(5, callCount[0], "Expected 5 calls for flag!=0, bit0=1");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0xB0L, capturedRcx[0], "First call856050 rcx (receiver+0xB0)");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x70L, capturedRcx[1], "Second call856050 rcx (LEA receiver+70)");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x48L, capturedRcx[2], "Third call856050 rcx (LEA receiver+48)");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x28L, capturedRcx[3], "Fourth call856050 rcx (LEA receiver+28)");
        org.junit.jupiter.api.Assertions.assertEquals(receiver, capturedRcx[4], "call4223f44 rcx (receiver)");
        org.junit.jupiter.api.Assertions.assertEquals(0xE0, capturedEdx[4], "call4223f44 edx (0xE0)");

        org.junit.jupiter.api.Assertions.assertEquals(releaseMutation, backing.peekInt64(receiver),
                "Opaque release storage mutation must survive");

        org.junit.jupiter.api.Assertions.assertEquals(2, trace2.size(), "Expected 2 memory ops for Case 2");
        org.junit.jupiter.api.Assertions.assertEquals(Request140TestMemory.Op.READ8, trace2.get(0).op(), "Op0 type");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0xD8L, trace2.get(0).address(), "Op0 address");
        org.junit.jupiter.api.Assertions.assertEquals(1, trace2.get(0).width(), "Op0 width");
        org.junit.jupiter.api.Assertions.assertEquals(0x80L, trace2.get(0).low(), "Op0 low");
        org.junit.jupiter.api.Assertions.assertEquals(0L, trace2.get(0).high(), "Op0 high");
        org.junit.jupiter.api.Assertions.assertEquals(Request140TestMemory.Op.WRITE64, trace2.get(1).op(), "Op1 type");
        org.junit.jupiter.api.Assertions.assertEquals(receiver, trace2.get(1).address(), "Op1 address");
        org.junit.jupiter.api.Assertions.assertEquals(8, trace2.get(1).width(), "Op1 width");
        org.junit.jupiter.api.Assertions.assertEquals(vptr, trace2.get(1).low(), "Op1 low");
        org.junit.jupiter.api.Assertions.assertEquals(0L, trace2.get(1).high(), "Op1 high");
        for (int i = 0; i < expectedImage2.length; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expectedImage2[i], backing.peekUnsignedByte(receiver + i),
                    "Second receiver byte " + i);
        }
    }
    @Test public void callbackFailureStopsLaterEffectsWithoutImplicitCleanup() {
        long moduleBase = 0x100000L;
        long receiver = 0x100000L;

        Request140TestMemory memory = new Request140TestMemory();
        Idler79eRegressionHost.Memory backing = memory.bytes();

        backing.map(receiver, 0xE0);

        for (int i = 0; i < 0xE0; i++) {
            backing.seedByte(receiver + i, 0xA5);
        }
        backing.seedByte(receiver + 0xD8, 0);

        long vptrTarget = moduleBase + 0x44FC298L;

        RuntimeException expectedException = new RuntimeException("Callback failure at call 2");

        int[] callCount = new int[]{0};
        long[] observedRcx = new long[]{0L, 0L, 0L, 0L};

        RequestSlot0E91d90.Ports ports = new RequestSlot0E91d90.Ports() {
            @Override public void call856050(long rcx) {
                int idx = callCount[0];
                if (idx < observedRcx.length) {
                    observedRcx[idx] = rcx;
                }
                callCount[0]++;
                if (callCount[0] == 1) {
                    backing.seedByte(receiver + 0xD8, 0x80);
                }
                if (callCount[0] == 2) {
                    org.junit.jupiter.api.Assertions.assertEquals(vptrTarget, backing.peekInt64(receiver),
                            "vptr already installed at throwing callback entry");
                    throw expectedException;
                }
            }
            @Override public void call4223f44(long rcx, int edx) {
                callCount[0]++;
                throw new AssertionError("4223f44 should not be reached");
            }
        };

        RuntimeException thrown = org.junit.jupiter.api.Assertions.assertThrows(RuntimeException.class, () -> {
            RequestSlot0E91d90.invoke(moduleBase, receiver, 1, memory, ports);
        });

        org.junit.jupiter.api.Assertions.assertSame(expectedException, thrown, "Exception identity");
        org.junit.jupiter.api.Assertions.assertEquals(2, callCount[0], "Exact callback count");

        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x70L, observedRcx[0], "First call856050 rcx");
        org.junit.jupiter.api.Assertions.assertEquals(receiver + 0x48L, observedRcx[1], "Second call856050 rcx");

        org.junit.jupiter.api.Assertions.assertEquals(List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.READ8,
                        receiver + 0xD8, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64,
                        receiver, 8, vptrTarget, 0)
        ), memory.trace(), "complete source memory effects before callback failure");

        long actualVptr = backing.peekInt64(receiver);
        org.junit.jupiter.api.Assertions.assertEquals(vptrTarget, actualVptr, "vptr installed correctly");

        for (int offset = 8; offset < 0xE0; offset++) {
            int expected = offset == 0xD8 ? 0x80 : 0xA5;
            org.junit.jupiter.api.Assertions.assertEquals(expected, backing.peekUnsignedByte(receiver + offset),
                    "unchanged receiver byte except explicit callback mutation at " + offset);
        }
    }

}
