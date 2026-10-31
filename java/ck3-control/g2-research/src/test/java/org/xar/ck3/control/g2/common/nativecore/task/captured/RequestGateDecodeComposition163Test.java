package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.retained.InGameIdlerEventDispatch;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.fail;

import java.util.ArrayList;
import java.util.List;

public final class RequestGateDecodeComposition163Test {

    private static final long BASE = 0x424D02CL;
    private static final long RVA_ENCRYPTED = 0x542F0B8L;
    private static final long RVA_COOKIE = 0x5C5D568L;
    private static final long ADDR_ENCRYPTED = BASE + RVA_ENCRYPTED;
    private static final long ADDR_COOKIE = BASE + RVA_COOKIE;

    @Test
    public void testGateDecodeZeroResult() {
        List<String> trace = new ArrayList<>();
        List<Long> readAddresses = new ArrayList<>();
        List<Long> decoderArgs = new ArrayList<>();
        List<Long> remainderArgs = new ArrayList<>();

        NativeTaskMemory memory = new NativeTaskMemory() {
            @Override
            public long readPointer(long address) {
                readAddresses.add(address);
                if (address == ADDR_ENCRYPTED) {
                    trace.add("readE");
                    return 0L;
                } else if (address == ADDR_COOKIE) {
                    trace.add("readC");
                    return 0L;
                }
                throw new AssertionError("Unexpected read: " + Long.toHexString(address));
            }
            @Override
            public int readInt32(long address) {
                throw new AssertionError("readInt32 not allowed");
            }
            @Override
            public void writeInt32(long address, int value) {
                throw new AssertionError("writeInt32 not allowed");
            }
            @Override
            public void writeInt64(long address, long value) {
                throw new AssertionError("writeInt64 not allowed");
            }
        };

        RequestDecode424d02c.Ports decoder = new RequestDecode424d02c.Ports() {
            @Override
            public void call4247ffc(long knownRcx) {
                trace.add("before0");
                decoderArgs.add(knownRcx);
            }
            @Override
            public void call4248050(long knownRcx, long liveRbx) {
                trace.add("after0");
                decoderArgs.add(knownRcx);
                decoderArgs.add(liveRbx);
            }
        };

        RequestGate424cffc.Ports remainder = new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                throw new AssertionError("remainder.call424d02c should not be called");
            }
            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                throw new AssertionError("remainder.callIndirect43dbba8 should not be called");
            }
        };

        RequestGate424cffc.Ports ports = RequestGateDecodeConsumer.gatePorts(BASE, memory, decoder, remainder);

        int result = RequestGate424cffc.execute(0L, ports);

        assertEquals(0, result);
        assertEquals(List.of("before0", "readE", "readC", "after0"), trace);
        assertEquals(List.of(ADDR_ENCRYPTED, ADDR_COOKIE), readAddresses);
        assertEquals(List.of(0L, 0L, 0L), decoderArgs);
        assertEquals(0, remainderArgs.size());
    }

    @Test
    public void testGateDecodeNonZeroResult() {
        List<String> trace = new ArrayList<>();
        List<Long> readAddresses = new ArrayList<>();
        List<Long> decoderArgs = new ArrayList<>();
        List<Long> remainderArgs = new ArrayList<>();

        long originalSize = Long.MIN_VALUE + 39L;
        long expectedRax = Long.MIN_VALUE;

        NativeTaskMemory memory = new NativeTaskMemory() {
            @Override
            public long readPointer(long address) {
                readAddresses.add(address);
                if (address == ADDR_ENCRYPTED) {
                    trace.add("readE");
                    return 0L;
                } else if (address == ADDR_COOKIE) {
                    trace.add("readC");
                    return Long.MIN_VALUE;
                }
                throw new AssertionError("Unexpected read: " + Long.toHexString(address));
            }
            @Override
            public int readInt32(long address) {
                throw new AssertionError("readInt32 not allowed");
            }
            @Override
            public void writeInt32(long address, int value) {
                throw new AssertionError("writeInt32 not allowed");
            }
            @Override
            public void writeInt64(long address, long value) {
                throw new AssertionError("writeInt64 not allowed");
            }
        };

        RequestDecode424d02c.Ports decoder = new RequestDecode424d02c.Ports() {
            @Override
            public void call4247ffc(long knownRcx) {
                trace.add("before0");
                decoderArgs.add(knownRcx);
            }
            @Override
            public void call4248050(long knownRcx, long liveRbx) {
                trace.add("after0");
                decoderArgs.add(knownRcx);
                decoderArgs.add(liveRbx);
            }
        };

        RequestGate424cffc.Ports remainder = new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                throw new AssertionError("remainder.call424d02c should not be called");
            }
            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                trace.add("indirect");
                remainderArgs.add(knownRcx);
                remainderArgs.add(liveRax);
                return -1;
            }
        };

        RequestGate424cffc.Ports ports = RequestGateDecodeConsumer.gatePorts(BASE, memory, decoder, remainder);

        int result = RequestGate424cffc.execute(originalSize, ports);

        assertEquals(1, result);
        assertEquals(List.of("before0", "readE", "readC", "after0", "indirect"), trace);
        assertEquals(List.of(ADDR_ENCRYPTED, ADDR_COOKIE), readAddresses);
        assertEquals(List.of(0L, 0L, Long.MIN_VALUE), decoderArgs);
        assertEquals(List.of(originalSize, expectedRax), remainderArgs);
    }
}
