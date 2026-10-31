package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.fail;

public final class RequestRetry4223b94ErrorTest {

    private static final long SIZE_ZERO = 0L;
    private static final long SIZE_ALL_ONES = -1L;

    private static final long TARGET_42207D8 = 0x42207D8L;
    private static final long TRAP_4223BC9 = 0x4223BC9L;

    private static final long TARGET_4224A58 = 0x4224A58L;
    private static final long TRAP_4223BCF = 0x4223BCFL;

    @Test
    public void testRefusalZeroSize() {
        assertRefusal(SIZE_ZERO, TARGET_42207D8, TRAP_4223BC9);
    }

    @Test
    public void testRefusalAllOnesSize() {
        assertRefusal(SIZE_ALL_ONES, TARGET_4224A58, TRAP_4223BCF);
    }

    private static void assertRefusal(long sizeBits, long expectedTarget, long expectedTrap) {
        // Shared finite sequence state: step 0 = call42420b8, step 1 = call424cffc, step 2+ = fail
        final int[] step = new int[]{0};
        final long[] lastRcx = new long[2];

        RequestRetry4223b94.Ports ports = new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                if (step[0] != 0) {
                    fail("Unexpected call42420b8 at step " + step[0]);
                }
                step[0] = 1;
                lastRcx[0] = rcx;
                return 0L;
            }

            @Override
            public int call424cffc(long rcx) {
                if (step[0] != 1) {
                    fail("Unexpected call424cffc at step " + step[0]);
                }
                step[0] = 2;
                lastRcx[1] = rcx;
                return 0;
            }
        };

        RequestRetry4223b94.UnexecutedSourcePath ex = assertThrows(
            RequestRetry4223b94.UnexecutedSourcePath.class,
            () -> {
                RequestRetry4223b94.execute(sizeBits, ports);
            }
        );

        assertNotNull(ex);
        assertEquals(2, step[0], "Expected exactly two callback steps");
        assertEquals(sizeBits, lastRcx[0], "call42420b8 received wrong RCX");
        assertEquals(sizeBits, lastRcx[1], "call424cffc received wrong RCX");
        assertEquals(expectedTarget, ex.targetRva(), "Wrong targetRva");
        assertEquals(expectedTrap, ex.trapSiteRva(), "Wrong trapSiteRva");
        assertEquals(sizeBits, ex.capturedSizeBits(), "Wrong capturedSizeBits");
    }
}
