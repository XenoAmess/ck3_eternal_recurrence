package org.xar.ck3.research.m3.stack229;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.stack227.StackContext227Api;
import org.xar.ck3.research.m3.stack227.StackContext424DE88;

/** Mechanical byte RAM and assertion vocabulary only. New witness methods are not written here. */
public final class MiddleResult229Witness {
    record Step(String kind, long site, long a, long b, long c, long d) { }

    static Step s(String kind, long site, long a, long b, long c, long d) {
        return new Step(kind, site, a, b, c, d);
    }

    static final class Mem implements NativeTaskMemory {
        final Map<Long, Byte> bytes = new HashMap<>();
        final List<Step> events = new ArrayList<>();

        private long raw(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte cell = bytes.get(address + i);
                if (cell == null) throw new AssertionError("Unseeded byte " + Long.toUnsignedString(address + i, 16));
                value |= (long) Byte.toUnsignedInt(cell) << (8 * i);
            }
            return value;
        }

        private void put(long address, long value, int width) {
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
        }

        void seed32(long address, int value) { put(address, Integer.toUnsignedLong(value), 4); }
        void seed64(long address, long value) { put(address, value, 8); }
        int peek32(long address) { return (int) raw(address, 4); }
        long peek64(long address) { return raw(address, 8); }

        @Override public long readPointer(long address) {
            long value = raw(address, 8);
            events.add(s("R64", 0, address, value, 0, 0));
            return value;
        }
        @Override public int readInt32(long address) {
            int value = (int) raw(address, 4);
            events.add(s("R32", 0, address, Integer.toUnsignedLong(value), 0, 0));
            return value;
        }
        @Override public void writeInt32(long address, int value) {
            put(address, Integer.toUnsignedLong(value), 4);
            events.add(s("W32", 0, address, Integer.toUnsignedLong(value), 0, 0));
        }
        @Override public void writeInt64(long address, long value) {
            put(address, value, 8);
            events.add(s("W64", 0, address, value, 0, 0));
        }
    }

    static void same(Object expected, Object actual, String reason) {
        if (expected != actual) throw new AssertionError(reason);
    }
    static void eq(long expected, long actual, String reason) {
        if (expected != actual) throw new AssertionError(reason + ": expected=" + Long.toUnsignedString(expected, 16)
                + " actual=" + Long.toUnsignedString(actual, 16));
    }
    static void expectEvents(Mem memory, Step... expected) {
        if (!memory.events.equals(Arrays.asList(expected)))
            throw new AssertionError("Expected=" + Arrays.toString(expected) + " actual=" + memory.events);
    }
    static void expectSameFailure(Throwable expected, Runnable action) {
        try { action.run(); }
        catch (Throwable actual) {
            if (actual != expected) throw new AssertionError("Changed exception identity", actual);
            return;
        }
        throw new AssertionError("Expected original exception");
    }
    static void expectThrows(Class<? extends Throwable> expected, Runnable action) {
        try { action.run(); }
        catch (Throwable actual) {
            if (!expected.isInstance(actual)) throw new AssertionError("Wrong failure type", actual);
            return;
        }
        throw new AssertionError("Expected " + expected.getName());
    }

    @Test void direct59FreshReadsAndFailurePrefixes() {
        Step[] normalTrace = new Step[] {
            s("R32", 0, 0x1000L, 0x80000001L, 0, 0),
            s("ENTER", 0x424DB8BL, 0x80000001L, 0, 0, 0),
            s("W32", 0, 0x1000L, 0x7FFFFFFFL, 0, 0),
            s("MIDDLE", 0x424DB94L, 0x2000L, 0xAABBCCDD87654321L, 0, 0),
            s("W32", 0, 0x1000L, 0xFFFFFFFDL, 0, 0),
            s("R32", 0, 0x1000L, 0xFFFFFFFDL, 0, 0),
            s("LEAVE", 0x424DB9DL, 0xFFFFFFFDL, 0x1000L, 0, 0),
            s("W32", 0, 0x1000L, 0x01020304L, 0, 0)
        };

        for (int phase = 0; phase <= 3; phase++) {
            Mem mem = new Mem();
            mem.seed64(0x1000L, 0xA1B2C3D480000001L);
            mem.seed64(0x2000L, 0x1111222233334444L);
            RuntimeException sentinel = new RuntimeException("Sentinel-" + phase);
            final int p = phase;

            StackContext229Api.Ports ports = new StackContext229Api.Ports() {
                @Override public void call4247ffc(NativeTaskMemory m, long site, int ecx) {
                    same(m, mem, "Mem identity");
                    eq(site, 0x424DB8BL, "Site");
                    mem.events.add(s("ENTER", site, Integer.toUnsignedLong(ecx), 0, 0, 0));
                    if (p == 1) throw sentinel;
                    mem.writeInt32(0x1000L, 0x7FFFFFFF);
                }
                @Override public long call424dd60(NativeTaskMemory m, long site, long rcx) {
                    same(m, mem, "Mem identity");
                    eq(site, 0x424DB94L, "Site");
                    eq(rcx, 0x2000L, "RCX");
                    mem.events.add(s("MIDDLE", site, rcx, 0xAABBCCDD87654321L, 0, 0));
                    if (p == 2) throw sentinel;
                    mem.writeInt32(0x1000L, 0xFFFFFFFD);
                    return 0xAABBCCDD87654321L;
                }
                @Override public void call4248050(NativeTaskMemory m, long site, int ecx, long liveRbx) {
                    same(m, mem, "Mem identity");
                    eq(site, 0x424DB9DL, "Site");
                    eq(liveRbx, 0x1000L, "LiveRbx");
                    mem.events.add(s("LEAVE", site, Integer.toUnsignedLong(ecx), liveRbx, 0, 0));
                    if (p == 3) throw sentinel;
                    mem.writeInt32(0x1000L, 0x01020304);
                }
            };

            StackContext229Api.Input input = new StackContext229Api.Input(0x1000L, 0x2000L, 0x1000L);

            if (p == 0) {
                long result = StackContext424DB74.execute(mem, ports, input);
                eq(result, 0x87654321L, "Return value");
                expectEvents(mem, normalTrace[0], normalTrace[1], normalTrace[2], normalTrace[3], normalTrace[4], normalTrace[5], normalTrace[6], normalTrace[7]);
                eq(mem.peek32(0x1000L), 0x01020304, "Final low DWORD");
                eq(mem.peek32(0x1004L), 0xA1B2C3D4, "Preserved high DWORD");
                eq(mem.peek64(0x2000L), 0x1111222233334444L, "Preserved 0x2000");
            } else {
                int prefixLen = (p == 1) ? 2 : (p == 2) ? 4 : 7;
                Step[] expectedPrefix = Arrays.copyOf(normalTrace, prefixLen);

                expectSameFailure(sentinel, () -> StackContext424DB74.execute(mem, ports, input));
                expectEvents(mem, expectedPrefix);

                long expectedLow = (p == 1) ? 0x80000001L : (p == 2) ? 0x7FFFFFFFL : 0xFFFFFFFDL;
                eq(expectedLow, Integer.toUnsignedLong(mem.peek32(0x1000L)), "State at failure");
                eq(mem.peek32(0x1004L), 0xA1B2C3D4, "Preserved high DWORD");
                eq(mem.peek64(0x2000L), 0x1111222233334444L, "Preserved 0x2000");
            }
        }
    }

    @Test void actual227TypedTailsAndBindingContracts() {
        long E = 0x4000L;
        long entryRCX = 0x1122334455667788L;
        long moduleBase = 0x140000000L;

        Mem mem = new Mem();
        mem.seed64(E + 8, 0xABCDEF0000000000L);
        mem.seed64(E - 0x18, 0xFACECAFEBAD00D00L);
        mem.seed64(E + 0x10, 0xCAFEBABE0BADF00DL);
        mem.seed64(E + 0x18, 0x5566778899AABBCCL);
        mem.seed64(E + 0x20, 0x99AABBCCDDEEFF00L);
        mem.seed64(E, 0xF0F0F0F0F0F0F0F0L);

        List<Step> expectedNormal = new ArrayList<>();
        expectedNormal.add(s("W64", 0, E + 8, entryRCX, 0, 0));
        expectedNormal.add(s("W64", 0, E - 0x18, E + 8, 0, 0));
        expectedNormal.add(s("W32", 0, E + 0x18, 2, 0, 0));
        expectedNormal.add(s("W32", 0, E + 0x20, 2, 0, 0));
        expectedNormal.add(s("CHILD", 0x424DEB8, E + 0x10, E + 0x20, E - 0x18, E + 0x18));
        expectedNormal.add(s("R32", 0, E + 0x20, 2, 0, 0));
        expectedNormal.add(s("TAIL500", 0x43DA500, 0x145C5D380L, 0x145C5D330L, 0, 0));
        expectedNormal.add(s("W32", 0, E + 0x18, 0x80000000L, 0, 0));
        expectedNormal.add(s("MIDDLE", 0x424DB94, E - 0x18, 0x11223344F1234567L, 0, 0));
        expectedNormal.add(s("W32", 0, E + 0x18, 0xFFFFFFFDL, 0, 0));
        expectedNormal.add(s("R32", 0, E + 0x18, 0xFFFFFFFDL, 0, 0));
        expectedNormal.add(s("TAIL4F0", 0x43DA4F0, 0x145C5D2B8L, 0x145C5D330L, E + 0x18, 0));
        expectedNormal.add(s("W32", 0, E + 0x18, 0x01020304L, 0, 0));

        StackContext229Api.Tails tails = new StackContext229Api.Tails() {
            @Override public void jump43da500(NativeTaskMemory memory, long knownRcx, long liveRax) {
                same(memory, mem, "Tails500 Memory");
                mem.events.add(s("TAIL500", 0x43DA500, knownRcx, liveRax, 0, 0));
                mem.writeInt32(E + 0x18, 0x80000000);
            }
            @Override public void jump43da4f0(NativeTaskMemory memory, long knownRcx, long liveRax, long liveRbx) {
                same(memory, mem, "Tails4F0 Memory");
                mem.events.add(s("TAIL4F0", 0x43DA4F0, knownRcx, liveRax, liveRbx, 0));
                mem.writeInt32(E + 0x18, 0x01020304);
            }
        };

        StackContext229Api.Ports childFallback = new StackContext229Api.Ports() {
            @Override public void call4247ffc(NativeTaskMemory memory, long siteRva, int ecx) {
                throw new AssertionError("Child enter touched");
            }
            @Override public long call424dd60(NativeTaskMemory memory, long siteRva, long rcx) {
                same(memory, mem, "Middle Memory");
                eq(0x424DB94L, siteRva, "Middle Site");
                mem.events.add(s("MIDDLE", siteRva, rcx, 0x11223344F1234567L, 0, 0));
                mem.writeInt32(E + 0x18, 0xFFFFFFFD);
                return 0x11223344F1234567L;
            }
            @Override public void call4248050(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
                throw new AssertionError("Child leave touched");
            }
        };

        StackContext227Api.Ports parentFallback = new StackContext227Api.Ports() {
            @Override public long call424db74(NativeTaskMemory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
                throw new AssertionError("Parent fallback touched in normal");
            }
        };

        StackContext229Api.Ports boundChild = StackContextIndexedTailBinding229.bind(mem, moduleBase, tails, childFallback);
        StackContext227Api.Ports actualParent = StackContextBinding229.bind(mem, boundChild, parentFallback);

        StackContext227Api.Ports probe = (memory, site, rcx, rdx, r8, r9) -> {
            same(mem, memory, "Actual227 child Memory");
            mem.events.add(s("CHILD", site, rcx, rdx, r8, r9));
            return actualParent.call424db74(memory, site, rcx, rdx, r8, r9);
        };
        long result = StackContext424DE88.execute(mem, probe, new StackContext227Api.Context(E, entryRCX));

        eq(0xF1234567L, result, "Normal return");
        expectEvents(mem, expectedNormal.toArray(new Step[0]));
        eq(0x5566778801020304L, mem.peek64(E + 0x18), "Final complete E+18");
        eq(0xCAFEBABE0BADF00DL, mem.peek64(E + 0x10), "Untouched E+10");
        eq(0xF0F0F0F0F0F0F0F0L, mem.peek64(E), "Untouched E");
        eq(0x99AABBCC00000002L, mem.peek64(E + 0x20), "E+20 value");
        eq(0x4008L, mem.peek64(E - 0x18), "E-18 value");
        eq(0x1122334455667788L, mem.peek64(E + 8), "E+8 value");

        mem.events.clear();

        Mem foreignMem = new Mem();
        foreignMem.seed64(E + 8, 0L);

        expectThrows(IllegalArgumentException.class, () -> {
            actualParent.call424db74(foreignMem, 0x424DEB8L, E + 0x10, E + 0x20, E - 0x18, E + 0x18);
        });
        if (!mem.events.isEmpty()) throw new AssertionError("Mem events after foreign parent");
        if (!foreignMem.events.isEmpty()) throw new AssertionError("Foreign mem events after foreign parent");

        RuntimeException fallbackEx = new RuntimeException("Fallback");
        RuntimeException[] fallbackFailure = {null};
        StackContext227Api.Ports originalFallback = (memory, site, rcx, rdx, r8, r9) -> {
            same(foreignMem, memory, "Unchanged foreign fallback Memory");
            mem.events.add(s("FALLBACK", site, rcx, rdx, r8, r9));
            if (fallbackFailure[0] != null) throw fallbackFailure[0];
            return 0xFEDCBA9876543210L;
        };
        StackContext227Api.Ports delegatingParent = StackContextBinding229.bind(mem, boundChild, originalFallback);
        eq(0xFEDCBA9876543210L, delegatingParent.call424db74(foreignMem, 0x424DEB9L,
                0x1111222233334444L, 0x5555666677778888L, 0x9999AAAABBBBCCCCL, 0xDDDDEEEEFFFF0001L), "Raw foreign fallback return");
        expectEvents(mem, s("FALLBACK", 0x424DEB9L, 0x1111222233334444L,
                0x5555666677778888L, 0x9999AAAABBBBCCCCL, 0xDDDDEEEEFFFF0001L));
        expectEvents(foreignMem);
        mem.events.clear();
        fallbackFailure[0] = fallbackEx;
        expectSameFailure(fallbackEx, () -> delegatingParent.call424db74(foreignMem, 0x424DEB9L,
                0x1111222233334444L, 0x5555666677778888L, 0x9999AAAABBBBCCCCL, 0xDDDDEEEEFFFF0001L));
        expectEvents(mem, s("FALLBACK", 0x424DEB9L, 0x1111222233334444L,
                0x5555666677778888L, 0x9999AAAABBBBCCCCL, 0xDDDDEEEEFFFF0001L));
        expectEvents(foreignMem);
        mem.events.clear();

        expectThrows(IllegalArgumentException.class, () -> {
            boundChild.call4247ffc(mem, 0x424DB8CL, 0);
        });
        if (!mem.events.isEmpty()) throw new AssertionError("Mem events after wrong site enter");
        expectEvents(foreignMem);

        expectThrows(IllegalArgumentException.class, () -> {
            boundChild.call4247ffc(foreignMem, 0x424DB8BL, 0);
        });
        if (!mem.events.isEmpty()) throw new AssertionError("Mem events after foreign enter");
        if (!foreignMem.events.isEmpty()) throw new AssertionError("Foreign mem events after foreign enter");

        expectThrows(IllegalArgumentException.class, () -> {
            boundChild.call4248050(mem, 0x424DB9CL, 0, 0);
        });
        if (!mem.events.isEmpty()) throw new AssertionError("Mem events after wrong site leave");
        expectEvents(foreignMem);

        expectThrows(IllegalArgumentException.class, () -> {
            boundChild.call4248050(foreignMem, 0x424DB9DL, 0, 0);
        });
        if (!mem.events.isEmpty()) throw new AssertionError("Mem events after foreign leave");
        if (!foreignMem.events.isEmpty()) throw new AssertionError("Foreign mem events after foreign leave");

        RuntimeException passiveEx = new RuntimeException("Passive");
        RuntimeException[] passiveFailure = {null};
        StackContext229Api.Ports passiveChild = new StackContext229Api.Ports() {
            @Override public void call4247ffc(NativeTaskMemory memory, long siteRva, int ecx) {
                throw new AssertionError("Passive enter touched");
            }
            @Override public long call424dd60(NativeTaskMemory memory, long siteRva, long rcx) {
                same(foreignMem, memory, "Passive original foreign Memory");
                mem.events.add(s("PASSIVE", siteRva, rcx, 0x8877665544332211L, 0, 0));
                if (passiveFailure[0] != null) throw passiveFailure[0];
                return 0x8877665544332211L;
            }
            @Override public void call4248050(NativeTaskMemory memory, long siteRva, int ecx, long liveRbx) {
                throw new AssertionError("Passive leave touched");
            }
        };
        StackContext229Api.Ports passiveBound = StackContextIndexedTailBinding229.bind(mem, moduleBase, tails, passiveChild);
        eq(0x8877665544332211L, passiveBound.call424dd60(foreignMem, 0x777L, 0x888L), "Passive raw return");
        expectEvents(mem, s("PASSIVE", 0x777L, 0x888L, 0x8877665544332211L, 0, 0));
        expectEvents(foreignMem);
        mem.events.clear();
        passiveFailure[0] = passiveEx;
        expectSameFailure(passiveEx, () -> passiveBound.call424dd60(foreignMem, 0x777L, 0x888L));
        expectEvents(mem, s("PASSIVE", 0x777L, 0x888L, 0x8877665544332211L, 0, 0));
        expectEvents(foreignMem);
    }
}
