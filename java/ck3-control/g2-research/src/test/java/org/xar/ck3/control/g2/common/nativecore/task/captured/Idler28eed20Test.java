package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

public class Idler28eed20Test {

    // Helper to retrieve expected hash from LITERAL-VECTORS01.json for specific inputs
    // This avoids using the production prepare method for expected values.
    private static int getExpectedHash(int rawDword) {
        switch (rawDword) {
            case 0: return 0x4b95f515;
            case 1: return 0xfb69b604;
            case -1: return 0xe3160fb1;
            case 0x12345678: return 0xa3649785;
            case Integer.MIN_VALUE: return 0xcb952b95;
            case 16777216: return 0x4a95f382;
            case 65536: return 0x25937aac;
            case 256: return 0xcaf41ca;
            case 8738: return 0x926d528d;
            case 28672: return 0xf3adfc85;
            default: throw new RuntimeException("No literal vector for " + rawDword);
        }
    }

    @Test
    public void testPrepareHashLogic() {
        // Test 1: Exact 4-byte little-endian 32-bit FNV caller hash from concrete raw DWORD inputs
        // Input: 0x00000000
        int r8d0 = 0;
        var k0 = Idler28eed20.prepare(0L, 0, r8d0);
        assertEquals(getExpectedHash(r8d0), k0.r8d(), "Hash for 0 mismatch");

        assertEquals(0xfb69b604, Idler28eed20.prepare(0L, 0, 1).r8d());

        // Input: 0xFFFFFFFF (-1)
        int r8dm1 = -1;
        var km1 = Idler28eed20.prepare(0L, 0, r8dm1);
        assertEquals(getExpectedHash(r8dm1), km1.r8d(), "Hash for -1 mismatch");

        // Input: 0x12345678 (mixed sign/byte order)
        int r8dmix = 0x12345678;
        var kmix = Idler28eed20.prepare(0L, 0, r8dmix);
        assertEquals(getExpectedHash(r8dmix), kmix.r8d(), "Hash for mixed mismatch");

        // Input: Integer.MIN_VALUE
        int r8dmin = Integer.MIN_VALUE;
        var kmin = Idler28eed20.prepare(0L, 0, r8dmin);
        assertEquals(getExpectedHash(r8dmin), kmin.r8d(), "Hash for INT_MIN mismatch");

        // Input: 16777216 (0x01000000)
        int r8d16m = 16777216;
        var k16m = Idler28eed20.prepare(0L, 0, r8d16m);
        assertEquals(getExpectedHash(r8d16m), k16m.r8d(), "Hash for 16M mismatch");

        // Input: 65536 (0x00010000)
        int r8d65k = 65536;
        var k65k = Idler28eed20.prepare(0L, 0, r8d65k);
        assertEquals(getExpectedHash(r8d65k), k65k.r8d(), "Hash for 65K mismatch");

        // Input: 256 (0x00000100)
        int r8d256 = 256;
        var k256 = Idler28eed20.prepare(0L, 0, r8d256);
        assertEquals(getExpectedHash(r8d256), k256.r8d(), "Hash for 256 mismatch");
    }

    @Test
    public void testPrepareFrameAddressesAndPreservation() {
        // Test 2: All known FrameAddress pointer expressions and preserved raw EDX/R8D saved DWORDs
        long entryRcx = 0x1000L;
        int entryEdx = 0x55AA;
        int entryR8d = 0x11223344;

        var k = Idler28eed20.prepare(entryRcx, entryEdx, entryR8d);

        // RCX + 0x18
        assertEquals(entryRcx + 0x18L, k.rcx(), "RCX offset mismatch");

        assertEquals(Long.MIN_VALUE + 15, Idler28eed20.prepare(Long.MAX_VALUE - 8, -1, Integer.MIN_VALUE).rcx());

        // Symbolic Frame Addresses
        assertEquals(Idler28eed20.FrameAddress.LOCAL_OUT_30, k.rdx(), "RDX address mismatch");
        assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_R8D_60, k.r9(), "R9 address mismatch");
        assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_EDX_58, k.stack28(), "Stack28 address mismatch");

        // Preserved Raw Values
        assertEquals(entryEdx, k.savedEdx58(), "Saved EDX mismatch");
        assertEquals(entryR8d, k.savedR8d60(), "Saved R8D mismatch");
    }

    @Test
    public void testInvokePortReturnsRaw64RAX() {
        // Test 3: Invoke port exactly once returns full raw 64-bit RAX unchanged
        long entryRcx = 0x2000L;
        int entryEdx = 0x1111;
        int entryR8d = 0x2222;
        long expectedReturn = 0xCAFEBABE_DEADBEEFL;

        AtomicReference<Idler28eed20.Known177ed10> capturedKnown = new AtomicReference<>();
        AtomicInteger callCount = new AtomicInteger(0);

        Idler28eed20.Port port = (known) -> {
            callCount.incrementAndGet();
            capturedKnown.set(known);
            return expectedReturn;
        };

        long result = Idler28eed20.invoke(entryRcx, entryEdx, entryR8d, port);

        assertEquals(1, callCount.get(), "Port called exactly once");
        assertEquals(expectedReturn, result, "Return value must be raw 64-bit RAX");

        var k = capturedKnown.get();
        assertNotNull(k);
        assertEquals(entryRcx + 0x18L, k.rcx());
        assertEquals(Idler28eed20.FrameAddress.LOCAL_OUT_30, k.rdx());
        assertEquals(getExpectedHash(entryR8d), k.r8d());
        assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_R8D_60, k.r9());
        assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_EDX_58, k.stack28());
        assertEquals(entryEdx, k.savedEdx58());
        assertEquals(entryR8d, k.savedR8d60());
    }

    @Test
    public void testInvokeOpaqueExceptionPropagation() {
        // Test 4: Invoke opaque exception identity propagates with no catch/retry
        RuntimeException expectedException = new RuntimeException("Opaque Failure");
        AtomicInteger exceptions = new AtomicInteger();

        Idler28eed20.Port port = (known) -> {
            exceptions.incrementAndGet();
            throw expectedException;
        };

        try {
            Idler28eed20.invoke(0L, 0, 0, port);
            fail("Exception should have propagated");
        } catch (RuntimeException e) {
            assertSame(expectedException, e, "Exception identity must be preserved");
            assertEquals(1, exceptions.get());
        }
    }

    @Test
    public void testContinuationPortsForwarding() {
        // Test 5: Actual Idler79eContinuationPorts forwards SAME Known383e320 identity exactly once
        Idler79ePorts.Known383e320 known383 = new Idler79ePorts.Known383e320(
            1L, 2, 3, 4L, 5, 6L, 7, 8L, 9
        );

        AtomicReference<Idler79ePorts.Known383e320> capturedRoot = new AtomicReference<>();
        AtomicInteger rootCallCount = new AtomicInteger(0);

        Idler79eContinuationPorts.RootPort rootPort = (known) -> {
            rootCallCount.incrementAndGet();
            capturedRoot.set(known);
        };

        // Dummy continuation port that does nothing but satisfies interface
        Idler28eed20.Port dummyContinuation = (known) -> 0L;

        Idler79eContinuationPorts ports = new Idler79eContinuationPorts(rootPort, dummyContinuation);

        ports.call383e320(known383);

        assertEquals(1, rootCallCount.get(), "Root port called exactly once");
        assertSame(known383, capturedRoot.get(), "Known383e320 identity must be forwarded");
        RuntimeException expected = new RuntimeException("root");
        AtomicInteger failures = new AtomicInteger();
        AtomicInteger unexpectedContinuations = new AtomicInteger();
        Idler79eContinuationPorts throwing = new Idler79eContinuationPorts(value -> {
            assertSame(known383, value);
            failures.incrementAndGet();
            throw expected;
        }, value -> { unexpectedContinuations.incrementAndGet(); return -1L; });
        assertSame(expected, assertThrows(RuntimeException.class, () -> throwing.call383e320(known383)));
        assertEquals(1, failures.get());
        assertEquals(0, unexpectedContinuations.get());
    }

    @Test
    public void testAdapterCall28eed20Reaches177Port() {
        // Test 6: Actual adapter.call28eed20(header, edx, payload) reaches 177 port once with correctly prepared known frame
        long header = 0x5000L;
        int edx = 0x6000;
        int payload = 0x7000;

        AtomicReference<Idler28eed20.Known177ed10> captured177 = new AtomicReference<>();
        AtomicInteger continuationCallCount = new AtomicInteger(0);

        Idler28eed20.Port continuation = (known) -> {
            continuationCallCount.incrementAndGet();
            captured177.set(known);
            return 0xFEDCBA9876543210L; // Full raw return ignored at the selected79E void callback
        };

        // Root port should NOT be called by call28eed20
        AtomicInteger rootCallCount = new AtomicInteger(0);
        Idler79eContinuationPorts.RootPort rootPort = (known) -> {
            rootCallCount.incrementAndGet();
        };

        Idler79eContinuationPorts ports = new Idler79eContinuationPorts(rootPort, continuation);

        ports.call28eed20(header, edx, payload);

        assertEquals(1, continuationCallCount.get(), "Continuation port called exactly once");
        assertEquals(0, rootCallCount.get(), "Root port must not be called by call28eed20");

        var k = captured177.get();
        assertNotNull(k);

        // Verify prepared frame matches expectations for inputs
        assertEquals(header + 0x18L, k.rcx());
        assertEquals(Idler28eed20.FrameAddress.LOCAL_OUT_30, k.rdx());
        assertEquals(getExpectedHash(payload), k.r8d());
        assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_R8D_60, k.r9());
        assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_EDX_58, k.stack28());
        assertEquals(edx, k.savedEdx58());
        assertEquals(payload, k.savedR8d60());
    }
}
