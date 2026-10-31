package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.fail;

import java.util.ArrayList;
import java.util.List;

/**
 * Verifies the frozen RequestCriticalSectionImportBinding.toTails adapter.
 * Ensures that the returned Ports correctly map jump43da500 to EnterCriticalSection
 * and jump43da4f0 to LeaveCriticalSection, passing only the exact RCX bits.
 */
public final class RequestCriticalSectionImportBinding166Test {

    private static final long MODULE_BASE = 0x140000000L;

    @Test
    public void namedImportsReceiveOnlyTheExactFullRcxBits() {
        // 1. Setup recording ports
        List<String> calls = new ArrayList<>();
        List<Long> args = new ArrayList<>();

        RequestCriticalSectionImportBinding.WindowsApiPorts recorder = new RequestCriticalSectionImportBinding.WindowsApiPorts() {
            @Override
            public void enterCriticalSection(long criticalSectionPtr) {
                calls.add("Enter");
                args.add(criticalSectionPtr);
            }

            @Override
            public void leaveCriticalSection(long criticalSectionPtr) {
                calls.add("Leave");
                args.add(criticalSectionPtr);
            }
        };

        // 2. Get the adapter
        RequestIndexedTails4247ffc.Ports tails = RequestCriticalSectionImportBinding.toTails(recorder);

        // 3. Invoke jump43da500 (Enter) with distinct arbitrary full64 values
        long rcx1 = 0xFFFFFFFFFFFFFFFFL; // -1
        long rcx2 = 0x8000000000000000L; // Long.MIN_VALUE

        tails.jump43da500(rcx1, 0xDEADBEEFL); // liveRax is poison/unrelated
        tails.jump43da500(rcx2, 0xCAFEBABEL); // liveRax is poison/unrelated

        // 4. Invoke jump43da4f0 (Leave) with distinct arbitrary full64 values
        long rcx3 = 0x0000000000000001L; // 1
        long rcx4 = 0x7FFFFFFFFFFFFFFFL; // Long.MAX_VALUE

        tails.jump43da4f0(rcx3, 0x12345678L, 0x9ABCDEF0L); // liveRax, liveRbx are poison/unrelated
        tails.jump43da4f0(rcx4, 0x0L, 0x0L); // liveRax, liveRbx are poison/unrelated

        // 5. Assert exact chronological Enter/Leave target and exact raw64 RCX
        assertEquals(4, calls.size());
        assertEquals("Enter", calls.get(0));
        assertEquals("Enter", calls.get(1));
        assertEquals("Leave", calls.get(2));
        assertEquals("Leave", calls.get(3));

        assertEquals(rcx1, args.get(0));
        assertEquals(rcx2, args.get(1));
        assertEquals(rcx3, args.get(2));
        assertEquals(rcx4, args.get(3));
    }

    @Test
    public void portFailuresPropagateByIdentityWithoutOtherCalls() {
        // 1. Setup throwing ports with shared event/counter log
        RuntimeException enterEx = new RuntimeException("EnterFailed");
        RuntimeException leaveEx = new RuntimeException("LeaveFailed");
        List<String> events = new ArrayList<>();

        RequestCriticalSectionImportBinding.WindowsApiPorts thrower = new RequestCriticalSectionImportBinding.WindowsApiPorts() {
            @Override
            public void enterCriticalSection(long criticalSectionPtr) {
                events.add("Enter");
                throw enterEx;
            }

            @Override
            public void leaveCriticalSection(long criticalSectionPtr) {
                events.add("Leave");
                throw leaveEx;
            }
        };

        // 2. Get the adapter
        RequestIndexedTails4247ffc.Ports tails = RequestCriticalSectionImportBinding.toTails(thrower);

        // 3. Test jump43da500 (Enter) throws identity and only Enter was called
        long rcx = 0x123456789ABCDEF0L;
        long rax = 0x0L;
        long rbx = 0x0L;

        try {
            tails.jump43da500(rcx, rax);
            fail("Expected exception from jump43da500");
        } catch (RuntimeException e) {
            assertSame(enterEx, e);
        }
        assertEquals(1, events.size());
        assertEquals("Enter", events.get(0));

        // 4. Test jump43da4f0 (Leave) throws identity and only Leave was called
        events.clear();
        try {
            tails.jump43da4f0(rcx, rax, rbx);
            fail("Expected exception from jump43da4f0");
        } catch (RuntimeException e) {
            assertSame(leaveEx, e);
        }
        assertEquals(1, events.size());
        assertEquals("Leave", events.get(0));
    }
}
