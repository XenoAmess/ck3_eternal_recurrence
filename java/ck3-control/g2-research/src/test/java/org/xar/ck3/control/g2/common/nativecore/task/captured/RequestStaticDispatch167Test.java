package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.fail;

import java.util.ArrayList;
import java.util.List;

public final class RequestStaticDispatch167Test {

    @Test
    public void staticTailForwardsFullKnownRegistersAndRawEax() {
        final List<Long> observedTargetRax = new ArrayList<>();
        final List<Long> observedKnownRcx = new ArrayList<>();
        final List<Integer> observedEax = new ArrayList<>();

        final RequestStaticDispatch4267630.TailTarget target = new RequestStaticDispatch4267630.TailTarget() {
            @Override
            public int jumpRax(long targetRax, long knownRcx) {
                observedTargetRax.add(targetRax);
                observedKnownRcx.add(knownRcx);
                if (observedEax.size() == 0) {
                    return 0;
                } else if (observedEax.size() == 1) {
                    return -12345;
                } else {
                    return 67890;
                }
            }
        };

        long rcx1 = 0L;
        long rax1 = 0L;
        int res1 = RequestStaticDispatch4267630.execute(rcx1, rax1, target);
        observedEax.add(res1);
        assertEquals(0, res1, "Raw EAX 0 expected");
        assertEquals(1, observedTargetRax.size(), "One callback expected");
        assertEquals(rax1, observedTargetRax.get(0), "Target RAX forwarded exactly");
        assertEquals(rcx1, observedKnownRcx.get(0), "Known RCX forwarded exactly");

        long rcx2 = -1L;
        long rax2 = Long.MIN_VALUE;
        int res2 = RequestStaticDispatch4267630.execute(rcx2, rax2, target);
        observedEax.add(res2);
        assertEquals(-12345, res2, "Raw negative EAX expected");
        assertEquals(2, observedTargetRax.size(), "Two callbacks expected");
        assertEquals(rax2, observedTargetRax.get(1), "Target RAX forwarded exactly (negative)");
        assertEquals(rcx2, observedKnownRcx.get(1), "Known RCX forwarded exactly (negative)");

        long rcx3 = 0x1234567890ABCDEFL;
        long rax3 = 0x7FFFFFFFFFFFFFFFL;
        int res3 = RequestStaticDispatch4267630.execute(rcx3, rax3, target);
        observedEax.add(res3);
        assertEquals(67890, res3, "Raw positive EAX expected");
        assertEquals(3, observedTargetRax.size(), "Three callbacks expected");
        assertEquals(rax3, observedTargetRax.get(2), "Target RAX forwarded exactly (positive)");
        assertEquals(rcx3, observedKnownRcx.get(2), "Known RCX forwarded exactly (positive)");
    }

    @Test
    public void targetFailureRetainsIdentityAndSingleTransfer() {
        final RuntimeException expectedException = new RuntimeException("Dispatch failure marker");

        final List<Long> observedTargetRax = new ArrayList<>();
        final List<Long> observedKnownRcx = new ArrayList<>();

        final RequestStaticDispatch4267630.TailTarget target = new RequestStaticDispatch4267630.TailTarget() {
            @Override
            public int jumpRax(long targetRax, long knownRcx) {
                observedTargetRax.add(targetRax);
                observedKnownRcx.add(knownRcx);
                throw expectedException;
            }
        };

        long rcx = 0xCAFEBABEL;
        long rax = 0xDEADBEEFL;

        RuntimeException caught = null;
        try {
            RequestStaticDispatch4267630.execute(rcx, rax, target);
            fail("Expected RuntimeException to be thrown");
        } catch (RuntimeException e) {
            caught = e;
        }

        assertNotNull(caught, "Exception must be caught");
        assertSame(expectedException, caught, "Exception identity must be retained");

        assertEquals(1, observedTargetRax.size(), "Exactly one callback expected");
        assertEquals(rax, observedTargetRax.get(0), "Target RAX forwarded exactly");
        assertEquals(rcx, observedKnownRcx.get(0), "Known RCX forwarded exactly");
    }
}
