package org.xar.ck3.control.g2.common.nativecore.task.captured;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.StorageCleanupFree83Consumer.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestSlot0CleanupConsumer.UnsupportedCleanupPath;
public final class RequestCleanupComposition144Test {
@org.junit.jupiter.api.Test
public void slot0FreshReadsFeedExistingCleanup() {
    final long u = 0x20000L;
    final long base = 0x140000000L;
    final long heap = 0x90000L;
    final long initialVptr = 0x2222L;
    final long installedVptr = base + 0x44FC298L;
    final Request140TestMemory memory = new Request140TestMemory();
    final Idler79eRegressionHost.Memory bytes = memory.bytes();
    bytes.map(u, 0x100);
    bytes.map(0x50000L, 0x100);
    bytes.map(0x60000L, 0x100);
    bytes.map(0x70000L, 0x100);
    for (int i = 0; i < 0x100; i++) bytes.seedByte(u + i, 0xA5);
    bytes.seedInt64(u, initialVptr);
    bytes.seedByte(u + 0xD8L, 0x80);
    bytes.seedInt64(u + 0xC8L, 15);
    bytes.seedInt64(u + 0x88L, 16);
    bytes.seedInt64(u + 0x70L, 0x50000L);
    bytes.seedInt64(u + 0x60L, 4095);
    bytes.seedInt64(u + 0x48L, 0x60010L);
    bytes.seedInt64(0x60008L, 0x60000L);
    bytes.seedInt64(u + 0x40L, -1L);
    bytes.seedInt64(u + 0x28L, 0);
    final int[] seededImage = new int[0x100];
    for (int i = 0; i < seededImage.length; i++) seededImage[i] = bytes.peekUnsignedByte(u + i);
    final java.util.List<Request140TestMemory.Access> expectedTrace = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ8, u + 0xD8L, 1, 0x80, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0xC8L, 8, 15, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0xC0L, 8, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0xC8L, 8, 15, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0xB0L, 1, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0x88L, 8, 16, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0x70L, 8, 0x50000L, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x80L, 8, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x88L, 8, 15, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x70L, 1, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u, 8, installedVptr, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0x60L, 8, 4095, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0x48L, 8, 0x70018L, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, 0x70010L, 8, 0x70000L, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x58L, 8, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x60L, 8, 15, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x48L, 1, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0x40L, 8, -1L, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, u + 0x28L, 8, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x38L, 8, 0, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x40L, 8, 15, 0),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x28L, 1, 0, 0)
    );
    final java.util.List<String> events = new java.util.ArrayList<>();
    final int[] heapCount = {0};
    final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32 capturedCell =
            new org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32(0x13579BDF);
    final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls calls =
            new org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls() {
        @Override public int heapFree(long heapHandleRaw, int flagsRaw32, long blockRaw) {
            org.junit.jupiter.api.Assertions.assertEquals(heap, heapHandleRaw);
            org.junit.jupiter.api.Assertions.assertEquals(0, flagsRaw32);
            final int call = heapCount[0]++;
            if (call == 0) {
                org.junit.jupiter.api.Assertions.assertEquals(0x50000L, blockRaw);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(), events);
                org.junit.jupiter.api.Assertions.assertEquals(expectedTrace.subList(0, 7), memory.trace());
                org.junit.jupiter.api.Assertions.assertEquals(initialVptr, bytes.peekInt64(u));
                org.junit.jupiter.api.Assertions.assertEquals(0, bytes.peekInt64(u + 0xC0L));
                org.junit.jupiter.api.Assertions.assertEquals(15, bytes.peekInt64(u + 0xC8L));
                org.junit.jupiter.api.Assertions.assertEquals(0xA5A5A5A5A5A5A500L, bytes.peekInt64(u + 0xB0L));
                org.junit.jupiter.api.Assertions.assertEquals(0xA5A5A5A5A5A5A5A5L, bytes.peekInt64(u + 0x80L));
                org.junit.jupiter.api.Assertions.assertEquals(16, bytes.peekInt64(u + 0x88L));
                org.junit.jupiter.api.Assertions.assertEquals(0x50000L, bytes.peekInt64(u + 0x70L));
                events.add("heap50000");
                bytes.seedInt64(u + 0x48L, 0x70018L);
                bytes.seedInt64(0x70010L, 0x70000L);
                bytes.seedByte(u + 0xA1L, 0x3C);
                return 0;
            }
            if (call == 1) {
                org.junit.jupiter.api.Assertions.assertEquals(0x70000L, blockRaw);
                org.junit.jupiter.api.Assertions.assertEquals(
                        java.util.List.of("heap50000", "cell", "error", "map"), events);
                org.junit.jupiter.api.Assertions.assertEquals(expectedTrace.subList(0, 14), memory.trace());
                org.junit.jupiter.api.Assertions.assertEquals(0xABCD, capturedCell.value);
                org.junit.jupiter.api.Assertions.assertEquals(installedVptr, bytes.peekInt64(u));
                org.junit.jupiter.api.Assertions.assertEquals(0, bytes.peekInt64(u + 0x80L));
                org.junit.jupiter.api.Assertions.assertEquals(15, bytes.peekInt64(u + 0x88L));
                org.junit.jupiter.api.Assertions.assertEquals(0x50000L, bytes.peekInt64(u + 0x70L));
                org.junit.jupiter.api.Assertions.assertEquals(0x70018L, bytes.peekInt64(u + 0x48L));
                org.junit.jupiter.api.Assertions.assertEquals(4095, bytes.peekInt64(u + 0x60L));
                org.junit.jupiter.api.Assertions.assertEquals(0xA5A5A5A5A5A5A5A5L, bytes.peekInt64(u + 0x58L));
                events.add("heap70000");
                return 1;
            }
            if (call == 2) {
                org.junit.jupiter.api.Assertions.assertEquals(u, blockRaw);
                org.junit.jupiter.api.Assertions.assertEquals(
                        java.util.List.of("heap50000", "cell", "error", "map", "heap70000"), events);
                org.junit.jupiter.api.Assertions.assertEquals(expectedTrace, memory.trace());
                org.junit.jupiter.api.Assertions.assertEquals(installedVptr, bytes.peekInt64(u));
                org.junit.jupiter.api.Assertions.assertEquals(0xABCD, capturedCell.value);
                org.junit.jupiter.api.Assertions.assertEquals(0, bytes.peekInt64(u + 0x58L));
                org.junit.jupiter.api.Assertions.assertEquals(15, bytes.peekInt64(u + 0x60L));
                org.junit.jupiter.api.Assertions.assertEquals(0x70000L, bytes.peekInt64(u + 0x48L));
                org.junit.jupiter.api.Assertions.assertEquals(0, bytes.peekInt64(u + 0x38L));
                org.junit.jupiter.api.Assertions.assertEquals(15, bytes.peekInt64(u + 0x40L));
                org.junit.jupiter.api.Assertions.assertEquals(0, bytes.peekInt64(u + 0x28L));
                events.add("heapU");
                bytes.seedInt64(u, 0x3333L);
                return 1;
            }
            throw new AssertionError("Unexpected extra heap callback " + call);
        }
        @Override public org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32 failureCell() {
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("heap50000"), events);
            org.junit.jupiter.api.Assertions.assertEquals(expectedTrace.subList(0, 7), memory.trace());
            org.junit.jupiter.api.Assertions.assertEquals(0x13579BDF, capturedCell.value);
            events.add("cell");
            return capturedCell;
        }
        @Override public int lastErrorBits() {
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("heap50000", "cell"), events);
            org.junit.jupiter.api.Assertions.assertEquals(expectedTrace.subList(0, 7), memory.trace());
            org.junit.jupiter.api.Assertions.assertEquals(0x13579BDF, capturedCell.value);
            events.add("error");
            return 0x80000001;
        }
        @Override public int mapCode(long zeroExtendedError32) {
            org.junit.jupiter.api.Assertions.assertEquals(2147483649L, zeroExtendedError32);
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("heap50000", "cell", "error"), events);
            org.junit.jupiter.api.Assertions.assertEquals(expectedTrace.subList(0, 7), memory.trace());
            org.junit.jupiter.api.Assertions.assertEquals(0x13579BDF, capturedCell.value);
            events.add("map");
            return 0xABCD;
        }
    };
    final long returned = RequestSlot0CleanupConsumer.invoke(base, u, 3, heap, memory, calls);
    final java.util.List<Request140TestMemory.Access> actualTrace = memory.trace();
    org.junit.jupiter.api.Assertions.assertEquals(u, returned);
    org.junit.jupiter.api.Assertions.assertEquals(22, actualTrace.size());
    org.junit.jupiter.api.Assertions.assertEquals(expectedTrace, actualTrace);
    org.junit.jupiter.api.Assertions.assertEquals(3, heapCount[0]);
    org.junit.jupiter.api.Assertions.assertEquals(
            java.util.List.of("heap50000", "cell", "error", "map", "heap70000", "heapU"), events);
    org.junit.jupiter.api.Assertions.assertEquals(0xABCD, capturedCell.value);
    org.junit.jupiter.api.Assertions.assertEquals(0x3333L, bytes.peekInt64(u));
    org.junit.jupiter.api.Assertions.assertEquals(0x60000L, bytes.peekInt64(0x60008L));
    org.junit.jupiter.api.Assertions.assertEquals(0x70000L, bytes.peekInt64(0x70010L));
    final int[] expectedImage = seededImage.clone();
    final long[][] literalWritesAndCallbackMutations = {
            {0xC0, 8, 0}, {0xC8, 8, 15}, {0xB0, 1, 0},
            {0x48, 8, 0x70018L}, {0xA1, 1, 0x3C},
            {0x80, 8, 0}, {0x88, 8, 15}, {0x70, 1, 0},
            {0, 8, installedVptr},
            {0x58, 8, 0}, {0x60, 8, 15}, {0x48, 1, 0},
            {0x38, 8, 0}, {0x40, 8, 15}, {0x28, 1, 0},
            {0, 8, 0x3333L}
    };
    for (long[] store : literalWritesAndCallbackMutations) {
        for (int i = 0; i < (int) store[1]; i++) {
            expectedImage[(int) store[0] + i] = (int) (store[2] >>> (8 * i)) & 0xFF;
        }
    }
    for (int i = 0; i < expectedImage.length; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedImage[i], bytes.peekUnsignedByte(u + i),
                "Receiver byte " + i);
    }
}


    @org.junit.jupiter.api.Test
    public void rejectedAndThrowingCallsStopSlot0WithoutReset() {
        final long moduleBase = 0x140000000L;
        final int rawEdx = 3;
        final long receiverA = 0x20000L;
        final long heapA = 0x1122334455667788L;
        final Request140TestMemory memA = new Request140TestMemory();
        final Idler79eRegressionHost.Memory bytesA = memA.bytes();
        bytesA.map(receiverA, 0x100);
        bytesA.map(0x30000L, 0x100);
        for (int index = 0; index < 0x100; index++) {
            bytesA.seedByte(receiverA + index, 0xAA);
            bytesA.seedByte(0x30000L + index, 0xBB);
        }
        bytesA.seedInt64(receiverA, 0x2222L);
        bytesA.seedByte(receiverA + 0xD8, 0x80);
        bytesA.seedInt64(receiverA + 0xC8, 15L);
        bytesA.seedInt64(receiverA + 0x88, 4095L);
        bytesA.seedInt64(receiverA + 0x70, 0x30028L);
        bytesA.seedInt64(0x30020L, 0x30000L);
        final byte[] initialA = new byte[0x100];
        final byte[] headerA = new byte[0x100];
        for (int index = 0; index < 0x100; index++) {
            initialA[index] = (byte) bytesA.peekUnsignedByte(receiverA + index);
            headerA[index] = (byte) bytesA.peekUnsignedByte(0x30000L + index);
        }
        final byte[] expectedA = initialA.clone();
        for (int index = 0; index < 8; index++) {
            expectedA[0xC0 + index] = 0;
            expectedA[0xC8 + index] = (byte) (15L >>> (index * 8));
        }
        expectedA[0xB0] = 0;
        final int[] callsA = {0, 0, 0, 0};
        final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls portsA =
                new org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls() {
            @Override public int heapFree(long heap, int flags, long block) {
                callsA[0]++;
                throw new AssertionError("Rejected-header route invoked heapFree");
            }
            @Override public org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32 failureCell() {
                callsA[1]++;
                throw new AssertionError("Rejected-header route selected failure cell");
            }
            @Override public int lastErrorBits() {
                callsA[2]++;
                throw new AssertionError("Rejected-header route read error");
            }
            @Override public int mapCode(long bits) {
                callsA[3]++;
                throw new AssertionError("Rejected-header route mapped error");
            }
        };
        memA.clearTrace();
        final RequestSlot0CleanupConsumer.UnsupportedCleanupPath rejected =
                org.junit.jupiter.api.Assertions.assertThrows(
                        RequestSlot0CleanupConsumer.UnsupportedCleanupPath.class,
                        () -> RequestSlot0CleanupConsumer.invoke(moduleBase, receiverA, rawEdx,
                                heapA, memA, portsA));
        org.junit.jupiter.api.Assertions.assertEquals(
                org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.StorageCleanupFree83Consumer.Completion.REJECTED_HEADER_UNEXECUTED,
                rejected.outcome().completion());
        final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.Plan planA = rejected.outcome().plan();
        org.junit.jupiter.api.Assertions.assertEquals(
                org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.Path.REJECTED_HEADER, planA.path());
        org.junit.jupiter.api.Assertions.assertEquals(
                org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.Target.RVA_4232A70, planA.target());
        org.junit.jupiter.api.Assertions.assertEquals(java.util.OptionalLong.of(40L), planA.rcxBits());
        org.junit.jupiter.api.Assertions.assertEquals(java.util.OptionalLong.of(4135L), planA.rdxBits());
        org.junit.jupiter.api.Assertions.assertEquals(java.util.OptionalLong.of(0x30000L), planA.r8Bits());
        org.junit.jupiter.api.Assertions.assertEquals(
                java.util.OptionalLong.of(0x30020L), planA.backReferenceReadAddress());
        org.junit.jupiter.api.Assertions.assertEquals(
                org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.ResetTiming.NONE_AFTER_TRAP,
                planA.resetTiming());
        org.junit.jupiter.api.Assertions.assertArrayEquals(new int[]{0, 0, 0, 0}, callsA);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.READ8, receiverA + 0xD8, 1, 0x80, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, receiverA + 0xC8, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, receiverA + 0xC0, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, receiverA + 0xC8, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, receiverA + 0xB0, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, receiverA + 0x88, 8, 4095, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, receiverA + 0x70, 8, 0x30028, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, 0x30020, 8, 0x30000, 0)
        ), memA.trace());
        org.junit.jupiter.api.Assertions.assertEquals(0x2222L, bytesA.peekInt64(receiverA));
        for (int index = 0; index < 0x100; index++) {
            org.junit.jupiter.api.Assertions.assertEquals(expectedA[index] & 0xFF,
                    bytesA.peekUnsignedByte(receiverA + index), "rejected receiver byte " + index);
            org.junit.jupiter.api.Assertions.assertEquals(headerA[index] & 0xFF,
                    bytesA.peekUnsignedByte(0x30000L + index), "rejected header byte " + index);
        }

        final long receiverB = 0x40000L;
        final long heapB = 0xFEDCBA9876543210L;
        final long installedVptr = moduleBase + 0x44FC298L;
        final Request140TestMemory memB = new Request140TestMemory();
        final Idler79eRegressionHost.Memory bytesB = memB.bytes();
        bytesB.map(receiverB, 0x100);
        bytesB.map(0x60000L, 0x100);
        for (int index = 0; index < 0x100; index++) {
            bytesB.seedByte(receiverB + index, 0xCC);
            bytesB.seedByte(0x60000L + index, 0xDD);
        }
        bytesB.seedInt64(receiverB, 0x1111L);
        bytesB.seedByte(receiverB + 0xD8, 0);
        bytesB.seedInt64(receiverB + 0x88, 15L);
        bytesB.seedInt64(receiverB + 0x60, 16L);
        bytesB.seedInt64(receiverB + 0x48, 0x60000L);
        bytesB.seedInt64(receiverB + 0x40, 15L);
        final byte[] initialB = new byte[0x100];
        final byte[] blockB = new byte[0x100];
        for (int index = 0; index < 0x100; index++) {
            initialB[index] = (byte) bytesB.peekUnsignedByte(receiverB + index);
            blockB[index] = (byte) bytesB.peekUnsignedByte(0x60000L + index);
        }
        final byte[] expectedB = initialB.clone();
        for (int index = 0; index < 8; index++) {
            expectedB[0x80 + index] = 0;
            expectedB[0x88 + index] = (byte) (15L >>> (index * 8));
            expectedB[index] = (byte) (installedVptr >>> (index * 8));
        }
        expectedB[0x70] = 0;
        final java.util.List<Request140TestMemory.Access> expectedTraceB = java.util.List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.READ8, receiverB + 0xD8, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, receiverB + 0x88, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, receiverB + 0x80, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, receiverB + 0x88, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, receiverB + 0x70, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, receiverB, 8, installedVptr, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, receiverB + 0x60, 8, 16, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, receiverB + 0x48, 8, 0x60000, 0)
        );
        final RuntimeException sentinel = new RuntimeException("controlled-U48-heap-callback");
        final int[] callsB = {0, 0, 0, 0};
        final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls portsB =
                new org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls() {
            @Override public int heapFree(long heap, int flags, long block) {
                callsB[0]++;
                org.junit.jupiter.api.Assertions.assertEquals(1, callsB[0]);
                org.junit.jupiter.api.Assertions.assertEquals(heapB, heap);
                org.junit.jupiter.api.Assertions.assertEquals(0, flags);
                org.junit.jupiter.api.Assertions.assertEquals(0x60000L, block);
                org.junit.jupiter.api.Assertions.assertEquals(installedVptr, bytesB.peekInt64(receiverB));
                org.junit.jupiter.api.Assertions.assertEquals(expectedTraceB, memB.trace());
                for (int index = 0; index < 0x100; index++) {
                    org.junit.jupiter.api.Assertions.assertEquals(expectedB[index] & 0xFF,
                            bytesB.peekUnsignedByte(receiverB + index), "heap entry receiver byte " + index);
                }
                throw sentinel;
            }
            @Override public org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32 failureCell() {
                callsB[1]++;
                throw new AssertionError("Throwing heap callback selected failure cell");
            }
            @Override public int lastErrorBits() {
                callsB[2]++;
                throw new AssertionError("Throwing heap callback read error");
            }
            @Override public int mapCode(long bits) {
                callsB[3]++;
                throw new AssertionError("Throwing heap callback mapped error");
            }
        };
        memB.clearTrace();
        org.junit.jupiter.api.Assertions.assertSame(sentinel,
                org.junit.jupiter.api.Assertions.assertThrows(RuntimeException.class,
                        () -> RequestSlot0CleanupConsumer.invoke(moduleBase, receiverB, rawEdx,
                                heapB, memB, portsB)));
        org.junit.jupiter.api.Assertions.assertArrayEquals(new int[]{1, 0, 0, 0}, callsB);
        org.junit.jupiter.api.Assertions.assertEquals(expectedTraceB, memB.trace());
        org.junit.jupiter.api.Assertions.assertEquals(installedVptr, bytesB.peekInt64(receiverB));
        for (int index = 0; index < 0x100; index++) {
            org.junit.jupiter.api.Assertions.assertEquals(expectedB[index] & 0xFF,
                    bytesB.peekUnsignedByte(receiverB + index), "throwing receiver byte " + index);
            org.junit.jupiter.api.Assertions.assertEquals(blockB[index] & 0xFF,
                    bytesB.peekUnsignedByte(0x60000L + index), "controlled block byte " + index);
        }
    }

}
