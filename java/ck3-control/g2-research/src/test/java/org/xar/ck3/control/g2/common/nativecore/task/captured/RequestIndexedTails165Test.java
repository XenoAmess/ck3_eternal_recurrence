package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.fail;

import java.util.ArrayList;
import java.util.List;

public final class RequestIndexedTails165Test {

    @Test
    public void testCall4247ffc() {
        long moduleBase = 0x100000000L;
        long expectedRax = 0x105C5D330L;

        long[] expectedRcxTable = {
            0x105C5D330L,
            0x105C5D308L,
            0xFFFFFFED05C5D330L,
            0x1505C5D308L
        };

        int[] entryEcxValues = { 0, -1, Integer.MIN_VALUE, Integer.MAX_VALUE };

        for (int i = 0; i < entryEcxValues.length; i++) {
            int entryEcx = entryEcxValues[i];
            long expectedRcx = expectedRcxTable[i];

            List<String> events = new ArrayList<>();
            List<Long> observedRcx = new ArrayList<>();
            List<Long> observedRax = new ArrayList<>();

            RequestIndexedTails4247ffc.Ports ports = new RequestIndexedTails4247ffc.Ports() {
                @Override
                public void jump43da500(long knownRcx, long liveRax) {
                    events.add("jump43da500");
                    observedRcx.add(knownRcx);
                    observedRax.add(liveRax);
                }
                @Override
                public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                    fail("wrong second tail");
                }
            };

            RequestIndexedTails4247ffc.call4247ffc(moduleBase, entryEcx, ports);

            assertEquals(1, events.size(), "Exactly one callback expected");
            if (!"jump43da500".equals(events.get(0))) {
                fail("Wrong jump slot");
            }
            assertEquals(expectedRcx, observedRcx.get(0), "RCX mismatch");
            assertEquals(expectedRax, observedRax.get(0), "RAX mismatch");
        }
    }

    @Test
    public void testCall4248050() {
        long moduleBase = 0x100000000L;
        long expectedRax = 0x105C5D330L;

        long[] expectedRcxTable = {
            0x105C5D330L,
            0x105C5D308L,
            0xFFFFFFED05C5D330L,
            0x1505C5D308L
        };

        int[] entryEcxValues = { 0, -1, Integer.MIN_VALUE, Integer.MAX_VALUE };

        long[] liveRBXValues = {
            0x1234567890ABCDEFL,
            -0x1234567890ABCDEFL,
            0L,
            -1L
        };

        for (int i = 0; i < entryEcxValues.length; i++) {
            int entryEcx = entryEcxValues[i];
            long expectedRcx = expectedRcxTable[i];
            long liveRBX = liveRBXValues[i];

            List<String> events = new ArrayList<>();
            List<Long> observedRcx = new ArrayList<>();
            List<Long> observedRax = new ArrayList<>();
            List<Long> observedRbx = new ArrayList<>();

            RequestIndexedTails4247ffc.Ports ports = new RequestIndexedTails4247ffc.Ports() {
                @Override
                public void jump43da500(long knownRcx, long liveRax) {
                    fail("wrong first tail");
                }
                @Override
                public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                    events.add("jump43da4f0");
                    observedRcx.add(knownRcx);
                    observedRax.add(liveRax);
                    observedRbx.add(liveRbx);
                }
            };

            RequestIndexedTails4247ffc.call4248050(moduleBase, entryEcx, liveRBX, ports);

            assertEquals(1, events.size(), "Exactly one callback expected");
            if (!"jump43da4f0".equals(events.get(0))) {
                fail("Wrong jump slot");
            }
            assertEquals(expectedRcx, observedRcx.get(0), "RCX mismatch");
            assertEquals(expectedRax, observedRax.get(0), "RAX mismatch");
            assertEquals(liveRBX, observedRbx.get(0), "RBX mismatch");
        }
    }
}
