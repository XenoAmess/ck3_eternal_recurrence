package org.xar.ck3.research.m3.cookie215;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;
import org.xar.ck3.research.m3.handler211.HandlerWrapper4246FB4;
import org.xar.ck3.research.m3.handler211.Wrapper4246FB4Api211;

/** Owner fixture and independent finite source-derived business witness. */
public final class CookieHelperValidation215 {
    private CookieHelperValidation215() { }
    private static int checks;
    private static int memoryEvents;
    private static int portEvents;

    private static String h(long value) { return Long.toHexString(value); }
    private static String i(int value) { return Integer.toUnsignedString(value, 16); }
    private static void check(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }
    private static void equal(long actual, long expected, String label) {
        check(actual == expected, label + ": " + h(actual) + " != " + h(expected));
    }
    private static void events(List<String> actual, String... expected) {
        check(actual.equals(List.of(expected)), "exact complete events " + actual);
    }
    private static void port(List<String> events, String value) { portEvents++; events.add(value); }
    private static void sameBytes(Mem actual, Map<Long, Byte> expected, String label) {
        check(actual.bytes.equals(expected), label);
    }
    private static void expectIAE(Runnable action, String label) {
        try { action.run(); }
        catch (IllegalArgumentException expected) { checks++; return; }
        throw new AssertionError(label);
    }

    private static final class Mem implements NativeTaskMemory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<String> events;
        private Mem(List<String> events) { this.events = events; }
        private void seed(long address, long value, int width) {
            for (int n = 0; n < width; n++) bytes.put(address + n, (byte) (value >>> (8 * n)));
        }
        private void seed32(long address, int value) { seed(address, value, 4); }
        private void seed64(long address, long value) { seed(address, value, 8); }
        private Map<Long, Byte> snapshot() { return new HashMap<>(bytes); }
        private long peek(long address, int width) {
            long value = 0;
            for (int n = 0; n < width; n++) {
                Byte part = bytes.get(address + n);
                if (part == null) throw new AssertionError("unmapped byte " + h(address + n));
                value |= (long) (part & 0xFF) << (8 * n);
            }
            return value;
        }
        @Override public long readPointer(long address) {
            long value = peek(address, 8);
            memoryEvents++;
            events.add("R64:" + h(address) + ":" + h(value));
            return value;
        }
        @Override public int readInt32(long address) {
            int value = (int) peek(address, 4);
            memoryEvents++;
            events.add("R32:" + h(address) + ":" + i(value));
            return value;
        }
        @Override public void writeInt32(long address, int value) {
            seed(address, value, 4);
            memoryEvents++;
            events.add("W32:" + h(address) + ":" + i(value));
        }
        @Override public void writeInt64(long address, long value) {
            seed(address, value, 8);
            memoryEvents++;
            events.add("W64:" + h(address) + ":" + h(value));
        }
    }

    private static class CookiePorts implements CookieHelper215Api.Ports {
        @Override public void enter(NativeTaskMemory memory, long site, int ecx) { throw new AssertionError("unexpected enter"); }
        @Override public void leave(NativeTaskMemory memory, long site, int ecx, long liveRbx) { throw new AssertionError("unexpected leave"); }
    }
    private static class TailPorts implements RequestIndexedTails4247ffc.Ports {
        @Override public void jump43da500(long knownRcx, long liveRax) { throw new AssertionError("unexpected enter tail"); }
        @Override public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) { throw new AssertionError("unexpected leave tail"); }
    }

    private static void directDistinct() {
        List<String> ev = new ArrayList<>();
        Mem m = new Mem(ev);
        m.seed64(0x2000L, 0xAABBCCDD89ABCDEFL);
        m.seed64(0x3000L, 0x1122334455667788L);
        m.seed64(0x10542F0B8L, 0x1111111111111111L);
        m.seed64(0x105C5D318L, 0x2222222222222222L);
        Map<Long, Byte> before = m.snapshot();
        CookiePorts cp = new CookiePorts() {
            @Override public void enter(NativeTaskMemory memory, long site, int ecx) {
                check(memory == m, "distinct enter Memory");
                equal(site, 0x4246EB0L, "distinct enter site");
                equal(ecx, 0x89ABCDEF, "distinct original entry DWORD");
                port(ev, "ENTER:" + h(site) + ":" + i(ecx));
                m.seed64(0x10542F0B8L, 0x800000000000003FL);
                m.seed64(0x105C5D318L, 0x0123456789ABCDEFL);
                m.seed32(0x3000L, 0xFEDCBA98);
            }
            @Override public void leave(NativeTaskMemory memory, long site, int ecx, long liveRbx) {
                check(memory == m, "distinct leave Memory");
                equal(site, 0x4246ECEL, "distinct leave site");
                equal(ecx, 0xFEDCBA98, "distinct fresh R9 DWORD");
                equal(liveRbx, 0x02468ACF13579BA1L, "distinct rotated full64 RBX");
                port(ev, "LEAVE:" + h(site) + ":" + i(ecx) + ":" + h(liveRbx));
                m.seed64(0x10542F0B8L, 0xCAFEBABEDEADBEEFL);
                m.seed64(0x105C5D318L, 0x1111222233334444L);
                m.seed32(0x3000L, 0x76543210);
            }
        };
        long value = CookieHelper4246E9C.execute(new CookieHelper215Api.Input(0x100000000L, 0x2000L, 0x3000L), m, cp);
        equal(value, 0x02468ACF13579BA1L, "distinct return retains decoded value after leave effects");
        events(ev, "R32:2000:89abcdef", "ENTER:4246eb0:89abcdef",
                "R64:10542f0b8:800000000000003f", "R64:105c5d318:123456789abcdef",
                "R32:3000:fedcba98", "LEAVE:4246ece:fedcba98:2468acf13579ba1");
        Mem expected = new Mem(new ArrayList<>());
        expected.bytes.putAll(before);
        expected.seed64(0x10542F0B8L, 0xCAFEBABEDEADBEEFL);
        expected.seed64(0x105C5D318L, 0x1111222233334444L);
        expected.seed64(0x3000L, 0x1122334476543210L);
        sameBytes(m, expected.bytes, "distinct full final bytes and high DWORD canaries");
    }
    private static void directAlias() {
        List<String> ev = new ArrayList<>();
        Mem m = new Mem(ev);
        m.seed64(0x4000L, 0x1122334480000000L);
        m.seed64(0x10542F0B8L, 0x3333333333333333L);
        m.seed64(0x105C5D318L, 0x4444444444444444L);
        Map<Long, Byte> before = m.snapshot();
        CookiePorts cp = new CookiePorts() {
            @Override public void enter(NativeTaskMemory memory, long site, int ecx) {
                check(memory == m, "alias enter Memory"); equal(site, 0x4246EB0L, "alias enter site");
                equal(ecx, 0x80000000, "alias first DWORD");
                port(ev, "ENTER:" + h(site) + ":" + i(ecx));
                m.seed32(0x4000L, 0x7FFFFFFF);
                m.seed64(0x10542F0B8L, 0xF000000000000040L);
                m.seed64(0x105C5D318L, 0x0F0E0D0C0B0A0908L);
            }
            @Override public void leave(NativeTaskMemory memory, long site, int ecx, long liveRbx) {
                check(memory == m, "alias leave Memory"); equal(site, 0x4246ECEL, "alias leave site");
                equal(ecx, 0x7FFFFFFF, "alias second fresh DWORD");
                equal(liveRbx, 0xFF0E0D0C0B0A0948L, "alias low6zero full64");
                port(ev, "LEAVE:" + h(site) + ":" + i(ecx) + ":" + h(liveRbx));
            }
        };
        long value = CookieHelper4246E9C.execute(new CookieHelper215Api.Input(0x100000000L, 0x4000L, 0x4000L), m, cp);
        equal(value, 0xFF0E0D0C0B0A0948L, "alias raw64 return");
        events(ev, "R32:4000:80000000", "ENTER:4246eb0:80000000",
                "R64:10542f0b8:f000000000000040", "R64:105c5d318:f0e0d0c0b0a0908",
                "R32:4000:7fffffff", "LEAVE:4246ece:7fffffff:ff0e0d0c0b0a0948");
        Mem expected = new Mem(new ArrayList<>());
        expected.bytes.putAll(before);
        expected.seed64(0x4000L, 0x112233447FFFFFFFL);
        expected.seed64(0x10542F0B8L, 0xF000000000000040L);
        expected.seed64(0x105C5D318L, 0x0F0E0D0C0B0A0908L);
        sameBytes(m, expected.bytes, "alias complete final bytes and neighbor preservation");
    }
    private static void caller211() {
        List<String> ev = new ArrayList<>();
        Mem m = new Mem(ev);
        m.seed64(0x5008L, 0xDEADBEEF01234567L);
        m.seed64(0x5010L, 0xA1B2C3D4E5F60718L);
        m.seed64(0x5018L, 0x1020304050607080L);
        m.seed64(0x10542F0B8L, 0x5555555555555555L);
        m.seed64(0x105C5D318L, 0x6666666666666666L);
        Map<Long, Byte> before = m.snapshot();
        CookiePorts cp = new CookiePorts() {
            @Override public void enter(NativeTaskMemory memory, long site, int ecx) {
                check(memory == m, "caller enter Memory"); equal(site, 0x4246EB0L, "caller enter site");
                equal(ecx, 3, "caller RDX=S+18 contains3");
                equal(m.peek(0x5010L, 8), 0xA1B2C3D400000003L, "caller first exact DWORD before enter");
                equal(m.peek(0x5018L, 8), 0x1020304000000003L, "caller second exact DWORD before enter");
                equal(m.peek(0x5008L, 8), 0xDEADBEEF01234567L, "unconsumed RCX/R8 canary untouched");
                port(ev, "ENTER:" + h(site) + ":" + i(ecx));
                m.seed32(0x5010L, 0x80000001);
                m.seed64(0x10542F0B8L, 0x8000000000000001L);
                m.seed64(0x105C5D318L, 0);
            }
            @Override public void leave(NativeTaskMemory memory, long site, int ecx, long liveRbx) {
                check(memory == m, "caller leave Memory"); equal(site, 0x4246ECEL, "caller leave site");
                equal(ecx, 0x80000001, "caller fresh R9=S+10 after enter");
                equal(liveRbx, 0xC000000000000000L, "caller rotate1 full64");
                port(ev, "LEAVE:" + h(site) + ":" + i(ecx) + ":" + h(liveRbx));
            }
        };
        Wrapper4246FB4Api211.Ports wrapper = CookieWrapperBinding215.bind(0x100000000L, m, cp);
        events(ev);
        long value = HandlerWrapper4246FB4.execute(m, wrapper, 0x5000L);
        equal(value, 0xC000000000000000L, "actual211 full64 consumer result");
        events(ev, "W32:5010:3", "W32:5018:3", "R32:5018:3", "ENTER:4246eb0:3",
                "R64:10542f0b8:8000000000000001", "R64:105c5d318:0",
                "R32:5010:80000001", "LEAVE:4246ece:80000001:c000000000000000");
        Mem expected = new Mem(new ArrayList<>());
        expected.bytes.putAll(before);
        expected.seed64(0x5010L, 0xA1B2C3D480000001L);
        expected.seed64(0x5018L, 0x1020304000000003L);
        expected.seed64(0x10542F0B8L, 0x8000000000000001L);
        expected.seed64(0x105C5D318L, 0);
        sameBytes(m, expected.bytes, "actual211 complete bytes and no extra ABI/home writes");
    }
    private static void wrapperQualification() {
        List<String> ev = new ArrayList<>();
        Mem m = new Mem(ev);
        Mem foreign = new Mem(ev);
        m.seed64(0x6000L, 0xAABBCCDDFFFF0001L);
        m.seed64(0x7000L, 0xDEADBEEF13579BDFL);
        m.seed64(0x10542F0B8L, 0x7777777777777777L);
        m.seed64(0x105C5D318L, 0x8888888888888888L);
        foreign.seed64(0x9000L, 0x1234567890ABCDEFL);
        Map<Long, Byte> before = m.snapshot();
        Map<Long, Byte> foreignBefore = foreign.snapshot();
        CookiePorts cp = new CookiePorts() {
            @Override public void enter(NativeTaskMemory memory, long site, int ecx) {
                check(memory == m, "qualified enter Memory"); equal(site, 0x4246EB0L, "qualified enter site");
                equal(ecx, 0xFFFF0001, "qualified original RDX DWORD");
                port(ev, "ENTER:" + h(site) + ":" + i(ecx));
                m.seed64(0x10542F0B8L, 0x40L);
                m.seed64(0x105C5D318L, 0xFEDCBA9876543250L);
                m.seed32(0x7000L, 0x2468ACE0);
            }
            @Override public void leave(NativeTaskMemory memory, long site, int ecx, long liveRbx) {
                check(memory == m, "qualified leave Memory"); equal(site, 0x4246ECEL, "qualified leave site");
                equal(ecx, 0x2468ACE0, "qualified fresh R9 DWORD");
                equal(liveRbx, 0xFEDCBA9876543210L, "qualified full64 result");
                port(ev, "LEAVE:" + h(site) + ":" + i(ecx) + ":" + h(liveRbx));
            }
        };
        Wrapper4246FB4Api211.Ports wrapper = CookieWrapperBinding215.bind(0x100000000L, m, cp);
        events(ev);
        expectIAE(() -> wrapper.call4246e9c(foreign, 0x4246FD8L, 1, 0x6000L, 2, 0x7000L), "wrapper foreign before effects");
        events(ev);
        sameBytes(m, before, "wrapper foreign captured bytes"); sameBytes(foreign, foreignBefore, "wrapper foreign bytes");
        expectIAE(() -> wrapper.call4246e9c(m, 0x4246FD9L, 1, 0x6000L, 2, 0x7000L), "wrapper site before effects");
        events(ev);
        sameBytes(m, before, "wrapper site captured bytes"); sameBytes(foreign, foreignBefore, "wrapper site foreign bytes");
        long value = wrapper.call4246e9c(m, 0x4246FD8L, 0x1111111111111111L, 0x6000L, 0xFEDCBA9876543210L, 0x7000L);
        equal(value, 0xFEDCBA9876543210L, "wrapper ignores arbitrary unequal RCX/R8");
        events(ev, "R32:6000:ffff0001", "ENTER:4246eb0:ffff0001",
                "R64:10542f0b8:40", "R64:105c5d318:fedcba9876543250",
                "R32:7000:2468ace0", "LEAVE:4246ece:2468ace0:fedcba9876543210");
        Mem expected = new Mem(new ArrayList<>());
        expected.bytes.putAll(before);
        expected.seed64(0x10542F0B8L, 0x40L);
        expected.seed64(0x105C5D318L, 0xFEDCBA9876543250L);
        expected.seed64(0x7000L, 0xDEADBEEF2468ACE0L);
        sameBytes(m, expected.bytes, "qualified complete final bytes");
        sameBytes(foreign, foreignBefore, "qualified callback leaves foreign object untouched");
    }
    private static void indexedTails() {
        List<String> ev = new ArrayList<>();
        Mem m = new Mem(ev);
        Mem foreign = new Mem(ev);
        m.seed64(0xA000L, 0x1020304050607080L);
        foreign.seed64(0xB000L, 0x8877665544332211L);
        Map<Long, Byte> before = m.snapshot();
        Map<Long, Byte> foreignBefore = foreign.snapshot();
        TailPorts tails = new TailPorts() {
            @Override public void jump43da500(long knownRcx, long liveRax) {
                equal(knownRcx, 0x105C5D308L, "enter signedECX=-1 known RCX");
                equal(liveRax, 0x105C5D330L, "enter full64 table RAX");
                port(ev, "T500:" + h(knownRcx) + ":" + h(liveRax));
            }
            @Override public void jump43da4f0(long knownRcx, long liveRax, long liveRbx) {
                equal(knownRcx, 0xFFFFFFED05C5D330L, "leave signedECX=MIN known RCX");
                equal(liveRax, 0x105C5D330L, "leave full64 table RAX");
                equal(liveRbx, 0xF123456789ABCDEFL, "leave full64 decoded RBX preserved");
                port(ev, "T4F0:" + h(knownRcx) + ":" + h(liveRax) + ":" + h(liveRbx));
            }
        };
        CookieHelper215Api.Ports bound = CookieIndexedTailBinding215.bind(0x100000000L, m, tails);
        events(ev);
        expectIAE(() -> bound.enter(foreign, 0x4246EB0L, -1), "tail enter foreign");
        events(ev); sameBytes(m, before, "tail enter foreign captured"); sameBytes(foreign, foreignBefore, "tail enter foreign bytes");
        expectIAE(() -> bound.enter(m, 0x4246EB1L, -1), "tail enter site");
        events(ev); sameBytes(m, before, "tail enter site captured"); sameBytes(foreign, foreignBefore, "tail enter site foreign");
        expectIAE(() -> bound.leave(foreign, 0x4246ECEL, 0x80000000, 0xF123456789ABCDEFL), "tail leave foreign");
        events(ev); sameBytes(m, before, "tail leave foreign captured"); sameBytes(foreign, foreignBefore, "tail leave foreign bytes");
        expectIAE(() -> bound.leave(m, 0x4246ECFL, 0x80000000, 0xF123456789ABCDEFL), "tail leave site");
        events(ev); sameBytes(m, before, "tail leave site captured"); sameBytes(foreign, foreignBefore, "tail leave site foreign");
        bound.enter(m, 0x4246EB0L, -1);
        bound.leave(m, 0x4246ECEL, 0x80000000, 0xF123456789ABCDEFL);
        events(ev, "T500:105c5d308:105c5d330", "T4F0:ffffffed05c5d330:105c5d330:f123456789abcdef");
        sameBytes(m, before, "qualified M7 tails perform no invented Memory access");
        sameBytes(foreign, foreignBefore, "qualified M7 foreign bytes untouched");
    }

    public static void main(String[] args) {
        directDistinct();
        directAlias();
        caller211();
        wrapperQualification();
        indexedTails();
        equal(memoryEvents, 18, "finite Memory count");
        equal(portEvents, 10, "finite port count");
        System.out.println("CookieHelperValidation215 groups=5 events=" + (memoryEvents + portEvents)
                + " memory=" + memoryEvents + " ports=" + portEvents + " checks=" + checks + " software_only=true");
    }
}
