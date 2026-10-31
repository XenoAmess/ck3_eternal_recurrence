package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;
import java.util.ArrayList;
import java.util.List;

public final class RequestGate424cffcTruthTest {

    @Test
    public void testDirectZeroOnly() {
        long size = Long.MIN_VALUE + 39;
        List<String> events = new ArrayList<>();
        List<Long> directArgs = new ArrayList<>();
        List<Long> indirectArgs = new ArrayList<>();

        RequestGate424cffc.Ports ports = new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                events.add("direct");
                directArgs.add(knownRcx);
                return 0L;
            }
            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                events.add("indirect");
                indirectArgs.add(knownRcx);
                throw new AssertionError("indirect must not be invoked when direct returns 0");
            }
        };

        int result = RequestGate424cffc.execute(size, ports);

        Assertions.assertEquals(0, result);
        Assertions.assertEquals(List.of("direct"), events);
        Assertions.assertEquals(1, directArgs.size());
        Assertions.assertEquals(size, directArgs.get(0));
        Assertions.assertTrue(indirectArgs.isEmpty());
    }

    @Test
    public void testNonzeroGateIndirectSequence() {
        long size = 0x1234567800000027L;

        // Case 1: direct returns Long.MIN_VALUE (nonzero), indirect returns 0 -> result 0
        {
            List<String> events = new ArrayList<>();
            List<Long> directArgs = new ArrayList<>();
            List<Long> indirectArgs = new ArrayList<>();
            List<Long> indirectRaxArgs = new ArrayList<>();

            RequestGate424cffc.Ports ports = new RequestGate424cffc.Ports() {
                @Override
                public long call424d02c(long knownRcx) {
                    events.add("direct");
                    directArgs.add(knownRcx);
                    return Long.MIN_VALUE;
                }
                @Override
                public int callIndirect43dbba8(long knownRcx, long liveRax) {
                    events.add("indirect");
                    indirectArgs.add(knownRcx);
                    indirectRaxArgs.add(liveRax);
                    return 0;
                }
            };

            int result = RequestGate424cffc.execute(size, ports);
            Assertions.assertEquals(0, result);
            Assertions.assertEquals(List.of("direct", "indirect"), events);
            Assertions.assertEquals(1, directArgs.size());
            Assertions.assertEquals(size, directArgs.get(0));
            Assertions.assertEquals(1, indirectArgs.size());
            Assertions.assertEquals(size, indirectArgs.get(0));
            Assertions.assertEquals(1, indirectRaxArgs.size());
            Assertions.assertEquals(Long.MIN_VALUE, indirectRaxArgs.get(0));
        }

        // Case 2: direct returns Long.MIN_VALUE (nonzero), indirect returns -1 -> result 1
        {
            List<String> events = new ArrayList<>();
            List<Long> directArgs = new ArrayList<>();
            List<Long> indirectArgs = new ArrayList<>();
            List<Long> indirectRaxArgs = new ArrayList<>();

            RequestGate424cffc.Ports ports = new RequestGate424cffc.Ports() {
                @Override
                public long call424d02c(long knownRcx) {
                    events.add("direct");
                    directArgs.add(knownRcx);
                    return Long.MIN_VALUE;
                }
                @Override
                public int callIndirect43dbba8(long knownRcx, long liveRax) {
                    events.add("indirect");
                    indirectArgs.add(knownRcx);
                    indirectRaxArgs.add(liveRax);
                    return -1;
                }
            };

            int result = RequestGate424cffc.execute(size, ports);
            Assertions.assertEquals(1, result);
            Assertions.assertEquals(List.of("direct", "indirect"), events);
            Assertions.assertEquals(1, directArgs.size());
            Assertions.assertEquals(size, directArgs.get(0));
            Assertions.assertEquals(1, indirectArgs.size());
            Assertions.assertEquals(size, indirectArgs.get(0));
            Assertions.assertEquals(1, indirectRaxArgs.size());
            Assertions.assertEquals(Long.MIN_VALUE, indirectRaxArgs.get(0));
        }
    }
}
