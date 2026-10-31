package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.fail;
import java.util.ArrayList;
import java.util.List;

public final class RequestRetryGateComposition160Test {

    @Test
    public void testMethod1() {
        long sizeBits = Long.MIN_VALUE + 39;
        long rawnegative = -123456789L;

        List<String> events = new ArrayList<>();
        List<Long> args = new ArrayList<>();
        List<Long> raxArgs = new ArrayList<>();
        int[] stepCount = new int[1];

        RequestGate424cffc.Ports gate = new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                events.add("gate.call424d02c");
                args.add(knownRcx);
                stepCount[0]++;
                if (stepCount[0] != 2) {
                    fail("Unexpected gate.call424d02c at step " + stepCount[0]);
                }
                return rawnegative;
            }

            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                events.add("gate.callIndirect43dbba8");
                args.add(knownRcx);
                raxArgs.add(liveRax);
                stepCount[0]++;
                if (stepCount[0] != 3) {
                    fail("Unexpected gate.callIndirect43dbba8 at step " + stepCount[0]);
                }
                return -1;
            }
        };

        RequestRetry4223b94.Ports remainder = new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                events.add("remainder.call42420b8");
                args.add(rcx);
                stepCount[0]++;
                if (stepCount[0] == 1) {
                    return 0L;
                } else if (stepCount[0] == 4) {
                    return rawnegative;
                } else {
                    fail("Unexpected remainder.call42420b8 at step " + stepCount[0]);
                    return 0L;
                }
            }

            @Override
            public int call424cffc(long rcx) {
                events.add("remainder.call424cffc");
                args.add(rcx);
                stepCount[0]++;
                fail("remainder.call424cffc must not be called");
                return 0;
            }
        };

        RequestRetry4223b94.Ports composed = RequestRetryGateConsumer.retryPorts(remainder, gate);
        long result = RequestRetry4223b94.execute(sizeBits, composed);

        assertEquals(4, stepCount[0], "Total steps must be 4");
        assertEquals(rawnegative, result, "Result must match second remainder call");

        assertEquals("remainder.call42420b8", events.get(0));
        assertEquals("gate.call424d02c", events.get(1));
        assertEquals("gate.callIndirect43dbba8", events.get(2));
        assertEquals("remainder.call42420b8", events.get(3));

        assertEquals(sizeBits, args.get(0));
        assertEquals(sizeBits, args.get(1));
        assertEquals(sizeBits, args.get(2));
        assertEquals(sizeBits, args.get(3));

        assertEquals(1, raxArgs.size());
        assertEquals(rawnegative, raxArgs.get(0));
    }

    @Test
    public void testMethod2() {
        long sizeBits = -1L;

        List<String> events = new ArrayList<>();
        List<Long> args = new ArrayList<>();
        int[] stepCount = new int[1];

        RequestGate424cffc.Ports gate = new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                events.add("gate.call424d02c");
                args.add(knownRcx);
                stepCount[0]++;
                if (stepCount[0] != 2) {
                    fail("Unexpected gate.call424d02c at step " + stepCount[0]);
                }
                return 0L;
            }

            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                events.add("gate.callIndirect43dbba8");
                args.add(knownRcx);
                stepCount[0]++;
                fail("Indirect call should not happen when gate returns 0");
                return 0;
            }
        };

        RequestRetry4223b94.Ports remainder = new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                events.add("remainder.call42420b8");
                args.add(rcx);
                stepCount[0]++;
                if (stepCount[0] == 1) {
                    return 0L;
                } else {
                    fail("Unexpected remainder.call42420b8 at step " + stepCount[0]);
                    return 0L;
                }
            }

            @Override
            public int call424cffc(long rcx) {
                events.add("remainder.call424cffc");
                args.add(rcx);
                stepCount[0]++;
                fail("remainder.call424cffc must not be called");
                return 0;
            }
        };

        RequestRetry4223b94.Ports composed = RequestRetryGateConsumer.retryPorts(remainder, gate);

        RequestRetry4223b94.UnexecutedSourcePath ex = assertThrows(
            RequestRetry4223b94.UnexecutedSourcePath.class,
            () -> RequestRetry4223b94.execute(sizeBits, composed)
        );

        assertEquals(0x4224a58L, ex.targetRva());
        assertEquals(0x4223bcfL, ex.trapSiteRva());
        assertEquals(-1L, ex.capturedSizeBits());

        assertEquals(2, stepCount[0], "Total steps must be 2");

        assertEquals("remainder.call42420b8", events.get(0));
        assertEquals("gate.call424d02c", events.get(1));

        assertEquals(sizeBits, args.get(0));
        assertEquals(sizeBits, args.get(1));
    }
}
