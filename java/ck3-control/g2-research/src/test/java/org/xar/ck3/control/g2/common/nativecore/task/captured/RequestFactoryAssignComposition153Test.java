package org.xar.ck3.control.g2.common.nativecore.task.captured;
public final class RequestFactoryAssignComposition153Test {
@org.junit.jupiter.api.Test public void createUsesFactoryAssignAndFreshPostLookupState() {
    // 1. Setup Memory and Backing
    org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory memory = new org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory();
    org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79eRegressionHost.Memory backing = memory.bytes();

    // 2. Allocate Regions for Fixtures (Non-overlapping)
    // U: 0xE0 bytes
    long uAddr = backing.allocate(0xE0);
    // Descriptor: 0x30 bytes (covers 0x28 flag)
    long descAddr = backing.allocate(0x30);
    // SourceString: 0x20 bytes
    long srcStrAddr = backing.allocate(0x20);
    // P: 0x180 bytes (covers 0x140, 0x170)
    long pAddr = backing.allocate(0x180);
    // P2: 0x180 bytes (covers 0x170, vptr)
    long p2Addr = backing.allocate(0x180);
    // Global Slot: 0x8 bytes
    long globalSlotAddr = backing.allocate(0x8);
    // Receiver (Application): 0x200 bytes (covers 0x1C0)
    long receiverAddr = backing.allocate(0x200);
    // Owner: 0x90 bytes (covers 0x50, 0x70)
    long ownerAddr = backing.allocate(0x90);
    // Output Holder: 0x8 bytes
    long outputHolderAddr = backing.allocate(0x8);
    // Vtable: 0x8 bytes
    long vtableAddr = backing.allocate(0x8);

    // Scratch Addresses (Independent 8-byte holders)
    long initializerHolderAddr = backing.allocate(0x8);
    long lookupHolderAddr = backing.allocate(0x8);
    long view70Addr = backing.allocate(0x10); // 13 bytes needed, allocate 16
    long view50Addr = backing.allocate(0x10);
    long viewCAddr = backing.allocate(0x10);
    long initializerScratchAddr = backing.allocate(0x30); // Covers 0x28

    // 3. Seed Initial State
    // Descriptor: flag at 0x28 is 0
    backing.seedByte(descAddr + 0x28, 0);
    // SourceString: length at 0x10 is 4, cap at 0x18 is 15 (inline)
    backing.seedInt64(srcStrAddr + 0x10, 4L);
    backing.seedInt64(srcStrAddr + 0x18, 15L);
    // SourceString data (inline at 0x0)
    backing.seedByte(srcStrAddr, 'W');
    backing.seedByte(srcStrAddr + 1, 'X');
    backing.seedByte(srcStrAddr + 2, 'Y');
    backing.seedByte(srcStrAddr + 3, 'Z');

    // Global Slot points to Receiver
    backing.seedInt64(globalSlotAddr, receiverAddr);
    // Receiver: slot at 0x1C0 points to Owner
    backing.seedInt64(receiverAddr + 0x1C0, ownerAddr);

    // Owner: inline descriptors for views
    // View 70 (rcx+0x70): length 2, cap 15
    backing.seedInt32(ownerAddr + 0x70 + 0x10, 2);
    backing.seedInt64(ownerAddr + 0x70 + 0x18, 15L);
    // View 50 (rcx+0x50): length 3, cap 15
    backing.seedInt32(ownerAddr + 0x50 + 0x10, 3);
    backing.seedInt64(ownerAddr + 0x50 + 0x18, 15L);

    // P: inline data at 0x140 (length 4, cap 15)
    backing.seedInt64(pAddr + 0x140 + 0x10, 4L);
    backing.seedInt64(pAddr + 0x140 + 0x18, 15L);
    backing.seedByte(pAddr + 0x140, 'A');
    backing.seedByte(pAddr + 0x140 + 1, 'B');
    backing.seedByte(pAddr + 0x140 + 2, 'C');
    backing.seedByte(pAddr + 0x140 + 3, 'D');
    // P: flag at 0x170 is 0
    backing.seedByte(pAddr + 0x170, 0);

    // P2: flag at 0x170 is 2 (nonzero, not 1)
    backing.seedByte(p2Addr + 0x170, 2);
    // P2 vptr points to the separately mapped slot0
    backing.seedInt64(p2Addr, vtableAddr);
    backing.seedInt64(vtableAddr, 0x12345678L); // Virtual target

    // 4. Prepare Scratch for Request26769e0.create
    // Note: The record Scratch takes addresses, not contents.
    org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.Scratch scratch = new org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.Scratch(
        initializerHolderAddr,
        lookupHolderAddr,
        view70Addr,
        view50Addr,
        viewCAddr,
        initializerScratchAddr
    );

    // 5. Define Callbacks and Capture State
    final java.util.List<String> callSequence = new java.util.ArrayList<>();
    final java.util.List<org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.Known3852500> capturedKnown = new java.util.ArrayList<>();
    final java.util.List<long[]> capturedAssignArgs = new java.util.ArrayList<>();
    final java.util.List<long[]> capturedVirtualArgs = new java.util.ArrayList<>();
    final java.util.List<Long> capturedCleanupArgs = new java.util.ArrayList<>(); // Boxed Long

    // RequestStringConsumers.FactoryRemainder
    final org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStringConsumers.FactoryRemainder remainder = new org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStringConsumers.FactoryRemainder() {
        @Override
        public void call3852500(org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.Known3852500 known) {
            callSequence.add("lookup");
            capturedKnown.add(known);

            // Verify Known fields against supplied addresses
            // rcx is ownerAddr (loaded from receiver+0x1C0)
            if (known.rcx() != ownerAddr) throw new AssertionError("Bad rcx");
            if (known.rdx() != lookupHolderAddr) throw new AssertionError("Bad rdx");
            if (known.r8() != viewCAddr) throw new AssertionError("Bad r8");
            if (known.r9() != view50Addr) throw new AssertionError("Bad r9");
            if (known.stack20() != view70Addr) throw new AssertionError("Bad stack20");

            org.junit.jupiter.api.Assertions.assertEquals(srcStrAddr, backing.peekInt64(viewCAddr));
            org.junit.jupiter.api.Assertions.assertEquals(4, backing.peekInt32(viewCAddr + 0x8));
            org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(viewCAddr + 0xC));
            org.junit.jupiter.api.Assertions.assertEquals(ownerAddr + 0x70, backing.peekInt64(view70Addr));
            org.junit.jupiter.api.Assertions.assertEquals(2, backing.peekInt32(view70Addr + 0x8));
            org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(view70Addr + 0xC));
            org.junit.jupiter.api.Assertions.assertEquals(ownerAddr + 0x50, backing.peekInt64(view50Addr));
            org.junit.jupiter.api.Assertions.assertEquals(3, backing.peekInt32(view50Addr + 0x8));
            org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(view50Addr + 0xC));
            org.junit.jupiter.api.Assertions.assertEquals(15L, backing.peekInt64(uAddr + 0x88));
            org.junit.jupiter.api.Assertions.assertEquals(0L, backing.peekInt64(uAddr + 0x80));
            org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(descAddr + 0x28));

            // Publish INITIAL P to actual lookupHolder
            backing.seedInt64(lookupHolderAddr, pAddr);

            // Clear trace to start recording from post-lookup
            memory.clearTrace();
        }
        @Override
        public void callVirtual0(long target, long rcx, int edx) {
            callSequence.add("virtual0");
            capturedVirtualArgs.add(new long[]{target, rcx, edx});

            // Verify U and U+0x90
            org.junit.jupiter.api.Assertions.assertEquals(13, memory.trace().size());
            long u = backing.peekInt64(outputHolderAddr);
            int u90 = backing.peekInt32(u + 0x90);
            org.junit.jupiter.api.Assertions.assertEquals(0x12345678L, target);
            org.junit.jupiter.api.Assertions.assertEquals(p2Addr, rcx);
            org.junit.jupiter.api.Assertions.assertEquals(1, edx);
            if (u != uAddr) throw new AssertionError("Virtual0 U mismatch");
            if (u90 != 1) throw new AssertionError("Virtual0 U90 mismatch");

            // Change descriptor flag to 1
            backing.seedByte(descAddr + 0x28, 1);
        }
        @Override
        public void call856050(long rcx) {
            callSequence.add("cleanup");
            org.junit.jupiter.api.Assertions.assertEquals(descAddr, rcx);
            org.junit.jupiter.api.Assertions.assertEquals(14, memory.trace().size());
            capturedCleanupArgs.add(rcx);
        }
    };

    // RequestAssign855db0.Ports
    final org.xar.ck3.control.g2.common.nativecore.task.captured.RequestAssign855db0.Ports assignPorts = new org.xar.ck3.control.g2.common.nativecore.task.captured.RequestAssign855db0.Ports() {
        @Override
        public long call856db0(long rcx) {
            throw new AssertionError("Unexpected allocation");
        }
        @Override
        public void call4226860(long rcx, long rdx, long r8) {
            callSequence.add("assignCopy");
            capturedAssignArgs.add(new long[]{rcx, rdx, r8});

            // Verify pre-copy state
            // dest = U+0x70, source = P+0x140, count = 4
            if (rcx != uAddr + 0x70) throw new AssertionError("Bad dest");
            if (rdx != pAddr + 0x140) throw new AssertionError("Bad source");
            if (r8 != 4L) throw new AssertionError("Bad count");

            // Check U+0x80 length is already 4 (set by Assign before copy)
            org.junit.jupiter.api.Assertions.assertEquals(5, memory.trace().size());
            long len = backing.peekInt64(uAddr + 0x80);
            if (len != 4L) throw new AssertionError("Bad pre-copy length");

            // Check U+0x88 cap15 is retained from the real initializer
            long cap = backing.peekInt64(uAddr + 0x88);
            if (cap != 15L) throw new AssertionError("Bad pre-copy cap");

            // Seed 4 bytes at destination
            backing.seedByte(rcx, 'A');
            backing.seedByte(rcx + 1, 'B');
            backing.seedByte(rcx + 2, 'C');
            backing.seedByte(rcx + 3, 'D');

            // Change lookupHolder to P2 (Freshness)
            backing.seedInt64(lookupHolderAddr, p2Addr);
        }
        @Override
        public void call4223f44(long rcx, long rdx, java.util.OptionalLong knownR8) {
            throw new AssertionError("Unexpected free");
        }
    };

    // RequestE92780.Ports (Initializer Ports)
    final org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780.Ports initializerPorts = new org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780.Ports() {
        @Override
        public long call4223b94(int ecx) {
            callSequence.add("allocU");
            if (ecx != 0xE0) throw new AssertionError("Bad ECX");
            return uAddr;
        }
        @Override
        public void call855f00(long rcx, long rdx) {
            throw new AssertionError("Unexpected initializer copy");
        }
        @Override
        public void call856050(long rcx) {
            throw new AssertionError("Unexpected initializer cleanup");
        }
    };

    // 6. Execute Composition using actual factoryPorts
    // moduleBase must be such that moduleBase + 0x5CB87F8 == globalSlotAddr
    long moduleBase = globalSlotAddr - 0x5CB87F8L;

    org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.Ports factoryPorts =
        org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStringConsumers.factoryPorts(memory, remainder, assignPorts);

    long result = org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.create(
        moduleBase,
        outputHolderAddr,
        descAddr,
        srcStrAddr,
        scratch,
        memory,
        initializerPorts,
        factoryPorts
    );

    // 7. Assertions
    org.junit.jupiter.api.Assertions.assertEquals(outputHolderAddr, result);
    org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("allocU", "lookup", "assignCopy", "virtual0", "cleanup"), callSequence);
    org.junit.jupiter.api.Assertions.assertEquals("allocU", callSequence.get(0));
    org.junit.jupiter.api.Assertions.assertEquals("lookup", callSequence.get(1));
    org.junit.jupiter.api.Assertions.assertEquals("assignCopy", callSequence.get(2));
    org.junit.jupiter.api.Assertions.assertEquals("virtual0", callSequence.get(3));
    org.junit.jupiter.api.Assertions.assertEquals("cleanup", callSequence.get(4));

    // Check Known3852500
    org.xar.ck3.control.g2.common.nativecore.task.captured.Request26769e0.Known3852500 known = capturedKnown.get(0);
    org.junit.jupiter.api.Assertions.assertEquals(ownerAddr, known.rcx());
    org.junit.jupiter.api.Assertions.assertEquals(lookupHolderAddr, known.rdx());
    org.junit.jupiter.api.Assertions.assertEquals(viewCAddr, known.r8());
    org.junit.jupiter.api.Assertions.assertEquals(view50Addr, known.r9());
    org.junit.jupiter.api.Assertions.assertEquals(view70Addr, known.stack20());

    // Check Assign Args
    long[] assignArgs = capturedAssignArgs.get(0);
    org.junit.jupiter.api.Assertions.assertEquals(uAddr + 0x70, assignArgs[0]); // dest
    org.junit.jupiter.api.Assertions.assertEquals(pAddr + 0x140, assignArgs[1]); // source
    org.junit.jupiter.api.Assertions.assertEquals(4L, assignArgs[2]); // length

    // Check Virtual Args
    long[] virtualArgs = capturedVirtualArgs.get(0);
    org.junit.jupiter.api.Assertions.assertEquals(0x12345678L, virtualArgs[0]); // target
    org.junit.jupiter.api.Assertions.assertEquals(p2Addr, virtualArgs[1]); // rcx
    org.junit.jupiter.api.Assertions.assertEquals(1, virtualArgs[2]); // edx

    // Check Cleanup Args
    org.junit.jupiter.api.Assertions.assertEquals(descAddr, capturedCleanupArgs.get(0).longValue());

    // Check Memory Effects
    // U+0x70 content
    org.junit.jupiter.api.Assertions.assertEquals('A', backing.peekUnsignedByte(uAddr + 0x70));
    org.junit.jupiter.api.Assertions.assertEquals('B', backing.peekUnsignedByte(uAddr + 0x71));
    org.junit.jupiter.api.Assertions.assertEquals('C', backing.peekUnsignedByte(uAddr + 0x72));
    org.junit.jupiter.api.Assertions.assertEquals('D', backing.peekUnsignedByte(uAddr + 0x73));
    org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(uAddr + 0x74)); // NUL
    // U+0x80 length
    org.junit.jupiter.api.Assertions.assertEquals(4L, backing.peekInt64(uAddr + 0x80));
    // U+0x88 cap
    org.junit.jupiter.api.Assertions.assertEquals(15L, backing.peekInt64(uAddr + 0x88));
    // U+0x90 flag
    org.junit.jupiter.api.Assertions.assertEquals(1, backing.peekInt32(uAddr + 0x90));
    // Descriptor flag
    org.junit.jupiter.api.Assertions.assertEquals(1, backing.peekUnsignedByte(descAddr + 0x28));

    org.junit.jupiter.api.Assertions.assertEquals(uAddr, backing.peekInt64(outputHolderAddr));
    org.junit.jupiter.api.Assertions.assertEquals(uAddr, backing.peekInt64(initializerHolderAddr));
    org.junit.jupiter.api.Assertions.assertEquals(p2Addr, backing.peekInt64(lookupHolderAddr));
    org.junit.jupiter.api.Assertions.assertEquals(0, backing.peekUnsignedByte(pAddr + 0x170));
    org.junit.jupiter.api.Assertions.assertEquals(2, backing.peekUnsignedByte(p2Addr + 0x170));

    // Boundary: lookup checked the three views, seeded INITIAL P, then cleared
    // Request trace. Callback backing seed/peek operations add no Request Access.
    // Every source operation after that boundary is asserted, including Assign.
    org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, lookupHolderAddr, 8, pAddr, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, pAddr + 0x150, 8, 4L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, pAddr + 0x158, 8, 15L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, uAddr + 0x88, 8, 15L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, uAddr + 0x80, 8, 4L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, uAddr + 0x74, 1, 0L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, lookupHolderAddr, 8, p2Addr, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ8, p2Addr + 0x170, 1, 2L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, uAddr + 0x90, 4, 1L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, outputHolderAddr, 8, uAddr, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, lookupHolderAddr, 8, p2Addr, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, p2Addr, 8, vtableAddr, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ64, vtableAddr, 8, 0x12345678L, 0L),
        new Request140TestMemory.Access(Request140TestMemory.Op.READ8, descAddr + 0x28, 1, 1L, 0L)
    ), memory.trace());
}

}
