package org.xar.ck3.research.m3.handler211;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal207.Terminal4232CF4;

/** Independent finite supplied-storage witness from the original 46B/86B sources. */
public final class HandlerWrapperValidation211 {
    private HandlerWrapperValidation211() { }

    private static final long BASE = 0x10000000L;
    private static final long GLOBAL_BYTE = 0x1542F208L;
    private static final long IAT_POINTER = 0x143DA258L;
    private static int checks;
    private static int memoryEvents;
    private static int portEvents;

    private static void require(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }

    private static void equal(long actual, long expected, String label) {
        require(actual == expected, label + ": actual=" + Long.toHexString(actual)
                + " expected=" + Long.toHexString(expected));
    }

    private static String hx(long value) { return Long.toHexString(value); }
    private static String ix(int value) { return Integer.toUnsignedString(value, 16); }

    private static void port(List<String> events, String value) {
        portEvents++;
        events.add(value);
    }

    private static void exhausted(List<String> actual, String... expected) {
        require(actual.equals(List.of(expected)), "exact complete events: " + actual);
    }

    private static void unchanged(Memory actual, Map<Long, Byte> before, String label) {
        require(actual.bytes.equals(before), label);
    }

    private static void expectIAE(Runnable action, String label) {
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            checks++;
            return;
        }
        throw new AssertionError(label);
    }

    /** Silent fixture seed/peek helpers never turn unmapped production reads into zero. */
    private static final class Memory implements Terminal207Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<String> events;

        private Memory(List<String> events) { this.events = events; }

        private void seed(long address, long value, int width) {
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
        }

        private void seed64(long address, long value) { seed(address, value, 8); }
        private void seed8(long address, int value) { seed(address, value, 1); }

        private long peek(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte part = bytes.get(address + i);
                if (part == null) throw new AssertionError("unmapped byte " + hx(address + i));
                value |= (long) (part & 0xFF) << (8 * i);
            }
            return value;
        }

        private void record(String value) {
            memoryEvents++;
            events.add(value);
        }

        @Override public long readPointer(long address) {
            long value = peek(address, 8);
            record("R64:" + hx(address) + ":" + hx(value));
            return value;
        }

        @Override public int readInt32(long address) {
            int value = (int) peek(address, 4);
            record("R32:" + hx(address) + ":" + ix(value));
            return value;
        }

        @Override public int readUnsigned8(long address) {
            int value = (int) peek(address, 1);
            record("R8:" + hx(address) + ":" + ix(value));
            return value;
        }

        @Override public void writeInt32(long address, int value) {
            seed(address, value, 4);
            record("W32:" + hx(address) + ":" + ix(value));
        }

        @Override public void writeInt64(long address, long value) {
            seed(address, value, 8);
            record("W64:" + hx(address) + ":" + hx(value));
        }
    }

    private static class FailingPorts implements Terminal207Api.Ports {
        @Override public long call4246fb4(Terminal207Api.Memory memory, long site) {
            throw new AssertionError("unexpected old first");
        }
        @Override public long call4246fb4(Terminal207Api.Memory memory, long site, long sourceEntryRsp) {
            throw new AssertionError("unexpected new first");
        }
        @Override public void call4247004(Terminal207Api.Memory memory, long site, int ecx) {
            throw new AssertionError("unexpected handler");
        }
        @Override public int call43da258(Terminal207Api.Memory memory, long site, long code, int ecx) {
            throw new AssertionError("unexpected IAT");
        }
        @Override public void call423283c(Terminal207Api.Memory memory, long site, int ecx, int edx, int r8d) {
            throw new AssertionError("unexpected log");
        }
        @Override public void call4242354(Terminal207Api.Memory memory, long site, int ecx) {
            throw new AssertionError("unexpected last");
        }
    }

    private static final Wrapper4246FB4Api211.Ports NO_CHILD = (memory, site, rcx, rdx, r8, r9) -> {
        throw new AssertionError("unexpected child");
    };

    private static void direct46() {
        List<String> events = new ArrayList<>();
        Memory memory = new Memory(events);
        memory.seed64(0x1008L, 0xFEDCBA9876543210L);
        memory.seed64(0x1010L, 0xA1B2C3D4E5F60718L);
        memory.seed64(0x1018L, 0x1122334455667788L);
        memory.seed64(0x1020L, 0x99AABBCCDDEEFF00L);
        Wrapper4246FB4Api211.Ports child = (m, site, rcx, rdx, r8, r9) -> {
            require(m == memory, "direct child same Memory");
            equal(site, 0x4246FD8L, "direct child site");
            equal(rcx, 0x1008L, "direct RCX");
            equal(rdx, 0x1018L, "direct RDX");
            equal(r8, 0x1008L, "direct R8/RCX alias");
            equal(r9, 0x1010L, "direct R9");
            equal(memory.peek(0x1010L, 8), 0xA1B2C3D400000003L, "direct first exact DWORD");
            equal(memory.peek(0x1018L, 8), 0x1122334400000003L, "direct second exact DWORD");
            equal(memory.peek(0x1008L, 8), 0xFEDCBA9876543210L, "direct untouched S+8");
            port(events, "CHILD:" + hx(site) + ":" + hx(rcx) + ":" + hx(rdx) + ":" + hx(r8) + ":" + hx(r9));
            return 0x80000001FEDCBA98L;
        };
        long result = HandlerWrapper4246FB4.execute(memory, child, 0x1000L);
        equal(result, 0x80000001FEDCBA98L, "direct full64 RAX");
        exhausted(events,
                "W32:1010:3", "W32:1018:3", "CHILD:4246fd8:1008:1018:1008:1010");
        Memory expected = new Memory(new ArrayList<>());
        expected.seed64(0x1008L, 0xFEDCBA9876543210L);
        expected.seed64(0x1010L, 0xA1B2C3D400000003L);
        expected.seed64(0x1018L, 0x1122334400000003L);
        expected.seed64(0x1020L, 0x99AABBCCDDEEFF00L);
        unchanged(memory, expected.bytes, "direct all supplied bytes and no extra bytes");
    }

    private static void contextTrace() {
        List<String> events = new ArrayList<>();
        Memory memory = new Memory(events);
        memory.seed64(0x5FD8L, 0x0123456789ABCDEFL);
        memory.seed64(0x5FE0L, 0x8899AABBCCDDEEFFL);
        memory.seed64(0x5FE8L, 0x1020304050607080L);
        memory.seed8(GLOBAL_BYTE, 1);
        memory.seed64(IAT_POINTER, 0xFEDCBA9876543210L);
        Wrapper4246FB4Api211.Ports child = (m, site, rcx, rdx, r8, r9) -> {
            require(m == memory, "trace child same Memory");
            equal(site, 0x4246FD8L, "trace child site");
            equal(rcx, 0x5FD8L, "trace child S+8");
            equal(rdx, 0x5FE8L, "trace child S+18");
            equal(r8, 0x5FD8L, "trace child RCX/R8 alias");
            equal(r9, 0x5FE0L, "trace child S+10");
            equal(memory.peek(0x5FE0L, 8), 0x8899AABB00000003L, "trace first DWORD before child");
            equal(memory.peek(0x5FE8L, 8), 0x1020304000000003L, "trace second DWORD before child");
            port(events, "CHILD:" + hx(site) + ":" + hx(rcx) + ":" + hx(rdx) + ":" + hx(r8) + ":" + hx(r9));
            return 0x100000000L;
        };
        Terminal207Api.Ports fallback = new FailingPorts() {
            @Override public void call4247004(Terminal207Api.Memory m, long site, int ecx) {
                require(m == memory, "handler same Memory");
                equal(site, 0x4232D07L, "handler site");
                equal(ecx, 0x16, "handler ECX");
                port(events, "HANDLER:" + hx(site) + ":" + ix(ecx));
                memory.seed8(GLOBAL_BYTE, 2);
            }
            @Override public int call43da258(Terminal207Api.Memory m, long site, long code, int ecx) {
                require(m == memory, "IAT same Memory");
                equal(site, 0x4232D1AL, "IAT site");
                equal(code, 0xFEDCBA9876543210L, "IAT code full64");
                equal(ecx, 0x17, "IAT ECX");
                port(events, "IAT:" + hx(site) + ":" + hx(code) + ":" + ix(ecx));
                return 0;
            }
            @Override public void call423283c(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d) {
                require(m == memory, "log same Memory");
                equal(site, 0x4232D3AL, "log site");
                equal(ecx, 3, "log ECX");
                equal(edx, 0x40000015, "log EDX");
                equal(r8d, 1, "log R8D");
                port(events, "LOG:" + hx(site) + ":" + ix(ecx) + ":" + ix(edx) + ":" + ix(r8d));
            }
            @Override public void call4242354(Terminal207Api.Memory m, long site, int ecx) {
                require(m == memory, "last same Memory");
                equal(site, 0x4232D44L, "last site");
                equal(ecx, 3, "last ECX");
                port(events, "LAST:" + hx(site) + ":" + ix(ecx));
            }
        };
        Terminal207Api.Ports bound = TerminalFirstBinding211.bind(memory, child, fallback);
        Terminal207Api.Stop stop = Terminal4232CF4.trace(memory, bound, BASE, 0x6000L);
        require(stop == Terminal207Api.Stop.INT3_4232D49, "trace actual Stop");
        exhausted(events,
                "W32:5fe0:3", "W32:5fe8:3", "CHILD:4246fd8:5fd8:5fe8:5fd8:5fe0",
                "HANDLER:4232d07:16", "R8:1542f208:2", "R64:143da258:fedcba9876543210",
                "IAT:4232d1a:fedcba9876543210:17", "LOG:4232d3a:3:40000015:1", "LAST:4232d44:3");
        Memory expected = new Memory(new ArrayList<>());
        expected.seed64(0x5FD8L, 0x0123456789ABCDEFL);
        expected.seed64(0x5FE0L, 0x8899AABB00000003L);
        expected.seed64(0x5FE8L, 0x1020304000000003L);
        expected.seed8(GLOBAL_BYTE, 2);
        expected.seed64(IAT_POINTER, 0xFEDCBA9876543210L);
        unchanged(memory, expected.bytes, "trace complete final supplied bytes");
    }

    private static void legacyTrace() {
        List<String> events = new ArrayList<>();
        Memory memory = new Memory(events);
        memory.seed8(GLOBAL_BYTE, 1);
        Map<Long, Byte> before = new HashMap<>(memory.bytes);
        Terminal207Api.Ports fallback = new FailingPorts() {
            @Override public long call4246fb4(Terminal207Api.Memory m, long site) {
                require(m == memory, "legacy same Memory");
                equal(site, 0x4232CF8L, "legacy first site");
                port(events, "OLD:" + hx(site));
                return 0;
            }
            @Override public void call4242354(Terminal207Api.Memory m, long site, int ecx) {
                require(m == memory, "legacy last same Memory");
                equal(site, 0x4232D44L, "legacy last site");
                equal(ecx, 3, "legacy last ECX");
                port(events, "LAST:" + hx(site) + ":" + ix(ecx));
            }
        };
        Terminal207Api.Ports bound = TerminalFirstBinding211.bind(memory, NO_CHILD, fallback);
        Terminal207Api.Stop stop = Terminal4232CF4.trace(memory, bound, BASE);
        require(stop == Terminal207Api.Stop.INT3_4232D49, "legacy Stop");
        exhausted(events, "OLD:4232cf8", "R8:1542f208:1", "LAST:4232d44:3");
        unchanged(memory, before, "legacy no invented stack cells or writes");
    }

    private static void firstGuards() {
        List<String> events = new ArrayList<>();
        Memory captured = new Memory(events);
        Memory foreign = new Memory(events);
        captured.seed64(0x7008L, 0x0123456789ABCDEFL);
        foreign.seed64(0x8008L, 0xFEDCBA9876543210L);
        Map<Long, Byte> beforeCaptured = new HashMap<>(captured.bytes);
        Map<Long, Byte> beforeForeign = new HashMap<>(foreign.bytes);
        Terminal207Api.Ports bound = TerminalFirstBinding211.bind(captured, NO_CHILD, new FailingPorts());
        exhausted(events);
        expectIAE(() -> bound.call4246fb4(foreign, 0x4232CF8L, 0x7000L), "foreign first3 must reject");
        exhausted(events);
        unchanged(captured, beforeCaptured, "foreign rejection captured unchanged");
        unchanged(foreign, beforeForeign, "foreign rejection foreign unchanged");
        expectIAE(() -> bound.call4246fb4(captured, 0x4232CF9L, 0x7000L), "wrong-site first3 must reject");
        exhausted(events);
        unchanged(captured, beforeCaptured, "site rejection captured unchanged");
        unchanged(foreign, beforeForeign, "site rejection foreign unchanged");
    }

    private static void exactDelegates() {
        List<String> events = new ArrayList<>();
        Memory captured = new Memory(events);
        Memory callback = new Memory(events);
        captured.seed64(0x9000L, 0x1122334455667788L);
        callback.seed64(0xA000L, 0x8877665544332211L);
        Map<Long, Byte> beforeCaptured = new HashMap<>(captured.bytes);
        Map<Long, Byte> beforeCallback = new HashMap<>(callback.bytes);
        Terminal207Api.Ports fallback = new FailingPorts() {
            @Override public long call4246fb4(Terminal207Api.Memory m, long site) {
                require(m == callback, "delegate oldfirst callback Memory");
                equal(site, 0x76543210L, "delegate oldfirst site");
                port(events, "OLD:" + hx(site));
                return 0xF00DBAAD12345678L;
            }
            @Override public void call4247004(Terminal207Api.Memory m, long site, int ecx) {
                require(m == callback, "delegate handler callback Memory");
                equal(site, 0x10L, "delegate handler site");
                equal(ecx, -7, "delegate handler ECX");
                port(events, "HANDLER:" + hx(site) + ":" + ix(ecx));
            }
            @Override public int call43da258(Terminal207Api.Memory m, long site, long code, int ecx) {
                require(m == callback, "delegate IAT callback Memory");
                equal(site, 0x20L, "delegate IAT site");
                equal(code, 0xFEDCBA9876543210L, "delegate IAT code");
                equal(ecx, 0x89ABCDEF, "delegate IAT ECX");
                port(events, "IAT:" + hx(site) + ":" + hx(code) + ":" + ix(ecx));
                return 0x80000001;
            }
            @Override public void call423283c(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d) {
                require(m == callback, "delegate log callback Memory");
                equal(site, 0x30L, "delegate log site");
                equal(ecx, 0x80000000, "delegate log ECX");
                equal(edx, 0x40000015, "delegate log EDX");
                equal(r8d, -1, "delegate log R8D");
                port(events, "LOG:" + hx(site) + ":" + ix(ecx) + ":" + ix(edx) + ":" + ix(r8d));
            }
            @Override public void call4242354(Terminal207Api.Memory m, long site, int ecx) {
                require(m == callback, "delegate last callback Memory");
                equal(site, 0x40L, "delegate last site");
                equal(ecx, 0x7FFFFFFF, "delegate last ECX");
                port(events, "LAST:" + hx(site) + ":" + ix(ecx));
            }
        };
        Terminal207Api.Ports bound = TerminalFirstBinding211.bind(captured, NO_CHILD, fallback);
        long first = bound.call4246fb4(callback, 0x76543210L);
        equal(first, 0xF00DBAAD12345678L, "delegate oldfirst full64 return");
        bound.call4247004(callback, 0x10L, -7);
        int iat = bound.call43da258(callback, 0x20L, 0xFEDCBA9876543210L, 0x89ABCDEF);
        equal(iat, 0x80000001, "delegate IAT raw32 return");
        bound.call423283c(callback, 0x30L, 0x80000000, 0x40000015, -1);
        bound.call4242354(callback, 0x40L, 0x7FFFFFFF);
        exhausted(events,
                "OLD:76543210", "HANDLER:10:fffffff9", "IAT:20:fedcba9876543210:89abcdef",
                "LOG:30:80000000:40000015:ffffffff", "LAST:40:7fffffff");
        unchanged(captured, beforeCaptured, "delegates captured bytes unchanged");
        unchanged(callback, beforeCallback, "delegates callback bytes unchanged");
    }

    public static void main(String[] args) {
        direct46();
        contextTrace();
        legacyTrace();
        firstGuards();
        exactDelegates();
        equal(memoryEvents, 7, "finite Memory event count");
        equal(portEvents, 13, "finite port event count");
        System.out.println("HandlerWrapperValidation211 groups=5 events=20 memory=7 ports=13 checks="
                + checks + " software_only=true");
    }
}
