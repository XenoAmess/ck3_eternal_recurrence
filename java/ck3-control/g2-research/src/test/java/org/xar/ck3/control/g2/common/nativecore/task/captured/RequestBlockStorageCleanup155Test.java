package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class RequestBlockStorageCleanup155Test {
@org.junit.jupiter.api.Test public void alignedStorageAllocationComposesWithExistingCleanup() {
    final long SOURCE_ADDR = 0x10000L;
    final long DEST_ADDR = 0x20000L;
    final long HEADER_START = 0x30000L;
    final long DATA_START = 0x40000L;
    final int DATA_SIZE = 16;
    final long SYNTH_H = 0x30003L;
    final long SYNTH_P = 0x30020L;
    final long HEAP_HANDLE = 0x99999999L;

    final org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory memory = new org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory();
    final org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79eRegressionHost.Memory backing = memory.bytes();

    backing.map(SOURCE_ADDR, 32);
    backing.map(DEST_ADDR, 32);
    backing.map(HEADER_START, 64);
    backing.map(DATA_START, DATA_SIZE);

    for (int i = 0; i < 32; i++) backing.seedByte(SOURCE_ADDR + i, 0xAA);
    for (int i = 0; i < 32; i++) backing.seedByte(DEST_ADDR + i, 0xBB);
    for (int i = 0; i < 64; i++) backing.seedByte(HEADER_START + i, 0xCC);
    for (int i = 0; i < DATA_SIZE; i++) backing.seedByte(DATA_START + i, 0xDD);

    backing.seedInt64(SOURCE_ADDR + 0x10L, 4095L);
    backing.seedInt64(SOURCE_ADDR + 0x18L, 4095L);
    backing.seedInt64(SOURCE_ADDR, DATA_START);

    final long[] initialSource = new long[32];
    final long[] initialDest = new long[32];
    final long[] initialHeader = new long[64];
    final long[] initialData = new long[DATA_SIZE];
    for (int i = 0; i < 32; i++) initialSource[i] = backing.peekUnsignedByte(SOURCE_ADDR + i);
    for (int i = 0; i < 32; i++) initialDest[i] = backing.peekUnsignedByte(DEST_ADDR + i);
    for (int i = 0; i < 64; i++) initialHeader[i] = backing.peekUnsignedByte(HEADER_START + i);
    for (int i = 0; i < DATA_SIZE; i++) initialData[i] = backing.peekUnsignedByte(DATA_START + i);

    final long[] expectedConstructedDest = initialDest.clone();
    final long[] expectedHeader = initialHeader.clone();
    for (int i = 0; i < 8; i++) {
        expectedConstructedDest[i] = (SYNTH_P >>> (i * 8)) & 0xFFL;
        expectedConstructedDest[0x10 + i] = (4095L >>> (i * 8)) & 0xFFL;
        expectedConstructedDest[0x18 + i] = (4095L >>> (i * 8)) & 0xFFL;
        expectedHeader[0x18 + i] = (SYNTH_H >>> (i * 8)) & 0xFFL;
    }
    final long[] expectedResetDest = expectedConstructedDest.clone();
    for (int i = 0; i < 8; i++) {
        expectedResetDest[0x10 + i] = 0L;
        expectedResetDest[0x18 + i] = (15L >>> (i * 8)) & 0xFFL;
    }
    expectedResetDest[0] = 0L;
    final java.util.List<String> callbacks = new java.util.ArrayList<>();
    final int[] rejectedCalls = new int[4];

    final org.xar.ck3.control.g2.common.nativecore.task.captured.RequestBlock856db0.Ports blockPorts = new org.xar.ck3.control.g2.common.nativecore.task.captured.RequestBlock856db0.Ports() {
        @Override public long call4223b94(long rcx) {
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(), callbacks);
            callbacks.add("blockalloc");
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(DEST_ADDR));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(DEST_ADDR + 0x10L));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(DEST_ADDR + 0x18L));
            for (int i = 8; i < 16; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(initialDest[i], backing.peekUnsignedByte(DEST_ADDR + i));
            }
            org.junit.jupiter.api.Assertions.assertEquals(4135L, rcx, "Block allocator RCX mismatch");
            return SYNTH_H;
        }
    };

    final org.xar.ck3.control.g2.common.nativecore.task.captured.RequestConstruct855f00.Ports constructRemainder = new org.xar.ck3.control.g2.common.nativecore.task.captured.RequestConstruct855f00.Ports() {
        @Override public long call856db0(long rcx) {
            rejectedCalls[0]++;
            throw new AssertionError("Fallback allocator called");
        }
        @Override public void call4226860(long rcx, long rdx, long r8) {
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("blockalloc"), callbacks);
            callbacks.add("copy");
            org.junit.jupiter.api.Assertions.assertEquals(SYNTH_P, rcx, "Copy dest mismatch");
            org.junit.jupiter.api.Assertions.assertEquals(DATA_START, rdx, "Copy src mismatch");
            org.junit.jupiter.api.Assertions.assertEquals(4096L, r8, "Copy len mismatch");
            org.junit.jupiter.api.Assertions.assertEquals(SYNTH_P, backing.peekInt64(DEST_ADDR), "D pointer not P during copy");
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(DEST_ADDR + 0x10L), "D len not 0 during copy");
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(DEST_ADDR + 0x18L), "D cap not 0 during copy");
            org.junit.jupiter.api.Assertions.assertEquals(SYNTH_H, backing.peekInt64(SYNTH_P - 8L), "Backref not H during copy");
        }
    };

    final org.xar.ck3.control.g2.common.nativecore.task.captured.RequestConstruct855f00.Ports constructPorts = org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStringStorageConsumers.constructPorts(memory, blockPorts, constructRemainder);

    final long resultDest = org.xar.ck3.control.g2.common.nativecore.task.captured.RequestConstruct855f00.construct(DEST_ADDR, SOURCE_ADDR, memory, constructPorts);
    org.junit.jupiter.api.Assertions.assertEquals(DEST_ADDR, resultDest, "Construct return mismatch");

    org.junit.jupiter.api.Assertions.assertEquals(SYNTH_P, backing.peekInt64(DEST_ADDR), "D pointer post-construct");
    org.junit.jupiter.api.Assertions.assertEquals(4095L, backing.peekInt64(DEST_ADDR + 0x10L), "D len post-construct");
    org.junit.jupiter.api.Assertions.assertEquals(4095L, backing.peekInt64(DEST_ADDR + 0x18L), "D cap post-construct");
    org.junit.jupiter.api.Assertions.assertEquals(SYNTH_H, backing.peekInt64(SYNTH_P - 8L), "Backref post-construct");

    for (int i = 0; i < 32; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedConstructedDest[i],
                backing.peekUnsignedByte(DEST_ADDR + i), "constructed destination byte " + i);
    }
    for (int i = 0; i < 64; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedHeader[i],
                backing.peekUnsignedByte(HEADER_START + i), "constructed header byte " + i);
    }

    for (int i = 0; i < 32; i++) org.junit.jupiter.api.Assertions.assertEquals(initialSource[i], backing.peekUnsignedByte(SOURCE_ADDR + i), "Source changed");
    for (int i = 0; i < DATA_SIZE; i++) org.junit.jupiter.api.Assertions.assertEquals(initialData[i], backing.peekUnsignedByte(DATA_START + i), "Data changed");

    final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls cleanupCalls = new org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls() {
        @Override public int heapFree(long heapHandleRaw, int flagsRaw32, long blockRaw) {
            org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("blockalloc", "copy"), callbacks);
            callbacks.add("heapFree");
            for (int i = 0; i < 32; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(expectedConstructedDest[i],
                        backing.peekUnsignedByte(DEST_ADDR + i), "heap callback destination byte " + i);
            }
            for (int i = 0; i < 64; i++) {
                org.junit.jupiter.api.Assertions.assertEquals(expectedHeader[i],
                        backing.peekUnsignedByte(HEADER_START + i), "heap callback header byte " + i);
            }
            org.junit.jupiter.api.Assertions.assertEquals(HEAP_HANDLE, heapHandleRaw, "Heap handle mismatch");
            org.junit.jupiter.api.Assertions.assertEquals(0, flagsRaw32, "Flags mismatch");
            org.junit.jupiter.api.Assertions.assertEquals(SYNTH_H, blockRaw, "Block raw mismatch");
            org.junit.jupiter.api.Assertions.assertEquals(SYNTH_P, backing.peekInt64(DEST_ADDR), "D pointer pre-reset");
            org.junit.jupiter.api.Assertions.assertEquals(4095L, backing.peekInt64(DEST_ADDR + 0x10L), "D len pre-reset");
            org.junit.jupiter.api.Assertions.assertEquals(4095L, backing.peekInt64(DEST_ADDR + 0x18L), "D cap pre-reset");
            org.junit.jupiter.api.Assertions.assertEquals(SYNTH_H, backing.peekInt64(SYNTH_P - 8L), "Backref pre-reset");
            return 1;
        }
        @Override public org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32 failureCell() {
            rejectedCalls[1]++;
            throw new AssertionError("failureCell called");
        }
        @Override public int lastErrorBits() {
            rejectedCalls[2]++;
            throw new AssertionError("lastErrorBits called");
        }
        @Override public int mapCode(long zeroExtendedError32) {
            rejectedCalls[3]++;
            throw new AssertionError("mapCode called");
        }
    };

    final org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.StorageCleanupFree83Consumer.Outcome outcome = org.xar.ck3.control.g2.common.nativecore.task.captured.RequestCleanup856050.cleanup(DEST_ADDR, HEAP_HANDLE, memory, cleanupCalls);

    org.junit.jupiter.api.Assertions.assertEquals(org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.StorageCleanupFree83Consumer.Completion.RESET_AFTER_CALLEE_RETURN, outcome.completion(), "Completion mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.Path.ADJUSTED_CALL, outcome.plan().path(), "Plan path mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.Target.RVA_4223F44, outcome.plan().target(), "Plan target mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(SYNTH_H, outcome.plan().rcxBits().getAsLong(), "Plan rcx mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(4135L, outcome.plan().rdxBits().getAsLong(), "Plan rdx mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(SYNTH_H, outcome.plan().r8Bits().getAsLong(), "Plan r8 mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(SYNTH_P - 8L, outcome.plan().backReferenceReadAddress().getAsLong(), "Plan readAddr mismatch");
    org.junit.jupiter.api.Assertions.assertEquals(org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan.ResetTiming.AFTER_NORMAL_CALL_RETURN, outcome.plan().resetTiming(), "Plan resetTiming mismatch");

    org.junit.jupiter.api.Assertions.assertEquals(0x30000L, backing.peekInt64(DEST_ADDR), "D pointer post-reset");
    org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(DEST_ADDR + 0x10L), "D len post-reset");
    org.junit.jupiter.api.Assertions.assertEquals(15L, backing.peekInt64(DEST_ADDR + 0x18L), "D cap post-reset");
    org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(DEST_ADDR), "D byte0 post-reset");

    for (int i = 0; i < 32; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedResetDest[i],
                backing.peekUnsignedByte(DEST_ADDR + i), "reset destination byte " + i);
        org.junit.jupiter.api.Assertions.assertEquals(initialSource[i],
                backing.peekUnsignedByte(SOURCE_ADDR + i), "final source byte " + i);
    }
    for (int i = 0; i < 64; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(expectedHeader[i],
                backing.peekUnsignedByte(HEADER_START + i), "final header byte " + i);
    }
    for (int i = 0; i < DATA_SIZE; i++) {
        org.junit.jupiter.api.Assertions.assertEquals(initialData[i],
                backing.peekUnsignedByte(DATA_START + i), "final data byte " + i);
    }
    org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("blockalloc", "copy", "heapFree"), callbacks);
    org.junit.jupiter.api.Assertions.assertArrayEquals(new int[4], rejectedCalls);

    final java.util.List<Request140TestMemory.Access> expectedTrace = java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR + 0x18L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, SOURCE_ADDR + 0x18L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, SOURCE_ADDR + 0x10L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, SOURCE_ADDR, 8, DATA_START, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, SYNTH_P - 8L, 8, SYNTH_H, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR, 8, SYNTH_P, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR + 0x10L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR + 0x18L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, DEST_ADDR + 0x18L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, DEST_ADDR, 8, SYNTH_P, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, SYNTH_P - 8L, 8, SYNTH_H, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, DEST_ADDR + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, DEST_ADDR, 1, 0L, 0L));
    org.junit.jupiter.api.Assertions.assertEquals(expectedTrace, memory.trace());
}


}
