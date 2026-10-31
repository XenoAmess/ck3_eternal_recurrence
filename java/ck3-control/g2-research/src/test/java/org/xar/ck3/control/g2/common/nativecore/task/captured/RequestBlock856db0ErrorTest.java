package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public final class RequestBlock856db0ErrorTest {

    @Test
    public void testOverflowErrorPath() {
        // Case 1: sizeBits = -39L (0xFFFFFFFFFFFFFFD9)
        // LEA size+0x27 -> 0. Unsigned 0 <= original -> Error CALL852340+INT3@856E01.
        // Must throw UnexecutedSourcePath before any allocator call or memory effect.

        Request140TestMemory memory = new Request140TestMemory();

        // Ports implementation that fails if called (allocator must not be reached)
        // Use final array for mutable counter to satisfy Java capture rules
        final long[] callCount = new long[]{0L};

        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            @Override
            public long call4223b94(long rcx) {
                callCount[0]++;
                fail("Allocator callback should not be reached for overflow error path");
                return 0L;
            }
        };

        long sizeBits = -39L;

        try {
            RequestBlock856db0.execute(sizeBits, memory, ports);
            fail("Expected UnexecutedSourcePath exception");
        } catch (RequestBlock856db0.UnexecutedSourcePath ex) {
            assertEquals(0x852340L, ex.targetRva(), "Target RVA mismatch");
            assertEquals(0x856E01L, ex.trapSiteRva(), "Trap Site RVA mismatch");
            assertEquals(sizeBits, ex.knownRcx(), "Known RCX mismatch");
        }

        // Verify allocator callback count exactly 0
        assertEquals(0L, callCount[0], "Allocator callback count mismatch");

        // Verify Request140TestMemory.trace() exactly empty
        assertTrue(memory.trace().isEmpty(), "Memory trace should be empty for error path");
    }

    @Test
    public void testNullAllocatorErrorPath() {
        // Case 2: sizeBits = 4096L (0x1000)
        // LEA size+0x27 -> 0x1027 (4135). Unsigned 4135 > 4096 -> Proceed.
        // CALL4223B94(4135). Returns 0.
        // RCX = 0. Null branch -> Error CALL4232A70+INT3@856E07.
        // Must throw UnexecutedSourcePath.

        Request140TestMemory memory = new Request140TestMemory();

        // Ports implementation that returns 0 (simulating allocator failure/null)
        // Use final arrays for mutable observation holders to satisfy Java capture rules
        final long[] callCount = new long[]{0L};
        final long[] observedRcx = new long[]{-1L};

        RequestBlock856db0.Ports ports = new RequestBlock856db0.Ports() {
            @Override
            public long call4223b94(long rcx) {
                callCount[0]++;
                observedRcx[0] = rcx;
                return 0L; // Simulate null return
            }
        };

        long sizeBits = 4096L;

        try {
            RequestBlock856db0.execute(sizeBits, memory, ports);
            fail("Expected UnexecutedSourcePath exception");
        } catch (RequestBlock856db0.UnexecutedSourcePath ex) {
            assertEquals(0x4232A70L, ex.targetRva(), "Target RVA mismatch");
            assertEquals(0x856E07L, ex.trapSiteRva(), "Trap Site RVA mismatch");
            assertEquals(0L, ex.knownRcx(), "Known RCX should be 0 (returned raw)");
        }

        assertEquals(1L, callCount[0], "Allocator callback count mismatch");
        assertEquals(4135L, observedRcx[0], "Allocator callback argument mismatch");

        // Verify ZERO Memory Access
        assertTrue(memory.trace().isEmpty(), "Memory trace should be empty for null allocator error path");
    }
}
