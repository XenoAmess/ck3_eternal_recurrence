package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.fail;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import java.util.ArrayList;
import java.util.List;

public final class RequestDecodeTailComposition165Test {

    private static final long BASE = 0x100000000L;
    private static final long ADDR_E = BASE + 0x542f0b8L;
    private static final long ADDR_C = BASE + 0x5c5d568L;
    private static final long TAIL_RAX = BASE + 0x5c5d330L;

    private static final RuntimeException EXC = new RuntimeException("boom");

    private static final List<String> trace = new ArrayList<>();

    private static long encoded;
    private static long cookie;

    private static NativeTaskMemory fakeMemory() {
        return new NativeTaskMemory() {
            @Override
            public long readPointer(long address) {
                if (address == ADDR_E) {
                    trace.add("readE");
                    return encoded;
                }
                if (address == ADDR_C) {
                    trace.add("readC");
                    return cookie;
                }
                fail("unexpected read " + Long.toHexString(address));
                return 0L;
            }
            @Override
            public int readInt32(long address) { fail("unexpected readInt32"); return 0; }
            @Override
            public void writeInt32(long address, int value) { fail("unexpected writeInt32"); }
            @Override
            public void writeInt64(long address, long value) { fail("unexpected writeInt64"); }
        };
    }

    @Test
    public void testNormalFlow() {
        trace.clear();
        encoded = 0x1234567890abcdefL;
        cookie = 0x0000000000000000L;

        RequestIndexedTails4247ffc.Ports tails = new RequestIndexedTails4247ffc.Ports() {
            @Override
            public void jump43da500(long knownRcx, long liveRax) {
                trace.add("jump500");
                assertEquals(TAIL_RAX, knownRcx);
                assertEquals(TAIL_RAX, liveRax);
                encoded = 1L;
                cookie = 2L;
            }
            @Override
            public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                trace.add("jump4f0");
                assertEquals(TAIL_RAX, knownRcx);
                assertEquals(TAIL_RAX, liveRax);
                assertEquals(0x8000000000000001L, liveRbx);
                encoded = 0x3333333333333333L;
                cookie = 0x4444444444444444L;
            }
        };

        RequestDecode424d02c.Ports ports = RequestDecodeTailConsumer.ports(BASE, tails);
        long result = RequestDecode424d02c.execute(BASE, fakeMemory(), ports);

        assertEquals(0x8000000000000001L, result);
        assertEquals(List.of("jump500", "readE", "readC", "jump4f0"), trace);
    }

    @Test
    public void testExceptionFlow() {
        trace.clear();
        encoded = 0L;
        cookie = Long.MIN_VALUE;

        RequestIndexedTails4247ffc.Ports tails = new RequestIndexedTails4247ffc.Ports() {
            @Override
            public void jump43da500(long knownRcx, long liveRax) {
                trace.add("jump500");
                assertEquals(TAIL_RAX, knownRcx);
                assertEquals(TAIL_RAX, liveRax);
            }
            @Override
            public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                trace.add("jump4f0");
                assertEquals(TAIL_RAX, knownRcx);
                assertEquals(TAIL_RAX, liveRax);
                assertEquals(Long.MIN_VALUE, liveRbx);
                throw EXC;
            }
        };

        RequestDecode424d02c.Ports ports = RequestDecodeTailConsumer.ports(BASE, tails);
        RuntimeException thrown = assertThrows(RuntimeException.class, () -> {
            RequestDecode424d02c.execute(BASE, fakeMemory(), ports);
        });

        assertSame(EXC, thrown);
        assertEquals(List.of("jump500", "readE", "readC", "jump4f0"), trace);
    }
}
