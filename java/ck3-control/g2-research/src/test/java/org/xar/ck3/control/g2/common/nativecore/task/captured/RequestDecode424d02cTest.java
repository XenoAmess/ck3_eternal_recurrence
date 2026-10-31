package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.retained.InGameIdlerEventDispatch;

import java.util.ArrayList;
import java.util.List;

public final class RequestDecode424d02cTest {

    private static final long MODULE_BASE = 0x424D02CL;
    private static final long ENCODED_ADDR = MODULE_BASE + 0x542F0B8L;
    private static final long COOKIE_ADDR = MODULE_BASE + 0x5C5D568L;

    private static NativeTaskMemory createFakeMemory(List<String> events, long[] encodedVal, long[] cookieVal) {
        return new NativeTaskMemory() {
            @Override
            public long readPointer(long address) {
                if (address == ENCODED_ADDR) {
                    events.add("READ:" + address);
                    return encodedVal[0];
                } else if (address == COOKIE_ADDR) {
                    events.add("READ:" + address);
                    return cookieVal[0];
                } else {
                    throw new AssertionError("Unexpected readPointer at " + address);
                }
            }

            @Override
            public int readInt32(long address) {
                throw new AssertionError("Unexpected readInt32 at " + address);
            }

            @Override
            public void writeInt32(long address, int value) {
                throw new AssertionError("Unexpected writeInt32 at " + address);
            }

            @Override
            public void writeInt64(long address, long value) {
                throw new AssertionError("Unexpected writeInt64 at " + address);
            }
        };
    }

    @Test
    public void testFiniteLiteralCases() {
        runCase(-64L, 1L, -63L);
        runCase(1L, 2L, 0x8000000000000001L);
        runCase(31L, 1L, 0x0000003C00000000L);
        runCase(32L, 1L, 0x0000002100000000L);
        runCase(63L, 1L, 0x000000000000007CL);
    }

    private void runCase(long encoded, long cookie, long expected) {
        List<String> events = new ArrayList<>();
        long[] encVal = {encoded};
        long[] cookieVal = {cookie};
        NativeTaskMemory memory = createFakeMemory(events, encVal, cookieVal);

        RequestDecode424d02c.Ports ports = new RequestDecode424d02c.Ports() {
            @Override
            public void call4247ffc(long knownRcx) {
                events.add("CALL4247FFC:" + knownRcx);
            }
            @Override
            public void call4248050(long knownRcx, long liveRbx) {
                events.add("CALL4248050:" + knownRcx + "," + liveRbx);
            }
        };

        long result = RequestDecode424d02c.execute(MODULE_BASE, memory, ports);

        assertEquals("CALL4247FFC:0", events.get(0));
        assertEquals("READ:" + ENCODED_ADDR, events.get(1));
        assertEquals("READ:" + COOKIE_ADDR, events.get(2));
        assertEquals("CALL4248050:0," + expected, events.get(3));
        assertEquals(expected, result);
        assertEquals(4, events.size());
    }

    @Test
    public void testFreshnessCapturedReturn() {
        List<String> events = new ArrayList<>();

        long[] encVal = {63L};
        long[] cookieVal = {1L};

        NativeTaskMemory memory = createFakeMemory(events, encVal, cookieVal);

        long newEncoded = 1L;
        long newCookie = 2L;
        long expected = 0x8000000000000001L;

        RequestDecode424d02c.Ports ports = new RequestDecode424d02c.Ports() {
            @Override
            public void call4247ffc(long knownRcx) {
                events.add("CALL4247FFC:" + knownRcx);
                encVal[0] = newEncoded;
                cookieVal[0] = newCookie;
            }
            @Override
            public void call4248050(long knownRcx, long liveRbx) {
                events.add("CALL4248050:" + knownRcx + "," + liveRbx);
                assertEquals(0L, knownRcx);
                assertEquals(expected, liveRbx);
                encVal[0] = 0L;
                cookieVal[0] = 0L;
            }
        };

        long result = RequestDecode424d02c.execute(MODULE_BASE, memory, ports);

        assertEquals("CALL4247FFC:0", events.get(0));
        assertEquals("READ:" + ENCODED_ADDR, events.get(1));
        assertEquals("READ:" + COOKIE_ADDR, events.get(2));
        assertEquals("CALL4248050:0," + expected, events.get(3));
        assertEquals(expected, result);
        assertEquals(4, events.size());
    }
}
