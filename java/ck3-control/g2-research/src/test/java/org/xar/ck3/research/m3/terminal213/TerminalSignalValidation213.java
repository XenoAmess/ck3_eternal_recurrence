package org.xar.ck3.research.m3.terminal213;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;

/** Finite independent business-memory witness; no Native CPU/EH/Game execution. */
public final class TerminalSignalValidation213 {
    private TerminalSignalValidation213() { }

    private static final long BASE = 0x10000000L;
    private static final long COOKIE = 0xC0FFEE123456789AL;
    private static final long R14 = 0xFEDCBA9876543210L;
    private static final long CODE418 = 0x8122334455667788L;
    private static final long CODE2A0 = 0x9233445566778899L;
    private static final long CODE2A8 = 0xA3445566778899AAL;
    private static final long CODE6A0 = 0xB45566778899AABBL;
    private static final long CODE770 = 0xC566778899AABBCCL;
    private static final long CODE2B0 = 0xD6778899AABBCCDDL;
    private static int checks;
    private static int memoryEvents;
    private static int portEvents;

    private static void require(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }

    private static void equal(long actual, long expected, String label) {
        require(actual == expected, label + ": " + Long.toHexString(actual) + " != " + Long.toHexString(expected));
    }

    private static String hx(long value) { return Long.toHexString(value); }
    private static String ix(int value) { return Integer.toUnsignedString(value, 16); }

    private static void port(List<String> events, String value) {
        portEvents++;
        events.add(value);
    }

    private static void exhausted(List<String> actual, String... expected) {
        require(actual.equals(List.of(expected)), "complete chronological events " + actual);
    }

    private static void expectIAE(Runnable action) {
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            checks++;
            return;
        }
        throw new AssertionError("expected IllegalArgumentException");
    }

    /** Only source API calls record events; fixture seed/peek/copy operations are silent. */
    private static final class Memory implements Terminal207Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<String> events;

        private Memory(List<String> events) { this.events = events; }

        private void seed(long address, long value, int width) {
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
        }

        private void seed64(long address, long value) { seed(address, value, 8); }

        private long peek(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte part = bytes.get(address + i);
                if (part == null) throw new AssertionError("unmapped byte " + hx(address + i));
                value |= (long) (part & 0xFF) << (8 * i);
            }
            return value;
        }

        private void record(String value) { memoryEvents++; events.add(value); }

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

    private static class FailingLeaf implements TerminalSignal213Api.Ports {
        @Override public void call4224800Initial(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d) { throw new AssertionError("initial"); }
        @Override public void call4226f10(Terminal207Api.Memory m, long site, long rcx, int edx, int r8d) { throw new AssertionError("fill"); }
        @Override public void call43da418(Terminal207Api.Memory m, long site, long code, long rcx) { throw new AssertionError("418"); }
        @Override public long call43da2a0(Terminal207Api.Memory m, long site, long code, long rcx, long rdx, int r8d) { throw new AssertionError("2a0"); }
        @Override public void call43da2a8(Terminal207Api.Memory m, long site, long code, long rcx, long rdx, long r8, long r9, long body) { throw new AssertionError("2a8"); }
        @Override public int call43da6a0(Terminal207Api.Memory m, long site, long code) { throw new AssertionError("6a0"); }
        @Override public void call43da770(Terminal207Api.Memory m, long site, long code, int ecx) { throw new AssertionError("770"); }
        @Override public int call43da2b0(Terminal207Api.Memory m, long site, long code, long rcx) { throw new AssertionError("2b0"); }
        @Override public void call4224800Repeat(Terminal207Api.Memory m, long site, int ecx) { throw new AssertionError("repeat"); }
        @Override public void call4224700(Terminal207Api.Memory m, long site, long rcx) { throw new AssertionError("cookie"); }
    }

    private static class FailingTerminal implements Terminal207Api.Ports {
        @Override public long call4246fb4(Terminal207Api.Memory m, long site) { throw new AssertionError("first2"); }
        @Override public long call4246fb4(Terminal207Api.Memory m, long site, long entry) { throw new AssertionError("first3"); }
        @Override public void call4247004(Terminal207Api.Memory m, long site, int ecx) { throw new AssertionError("handler3"); }
        @Override public void call4247004(Terminal207Api.Memory m, long site, int ecx, long entry) { throw new AssertionError("handler4"); }
        @Override public int call43da258(Terminal207Api.Memory m, long site, long code, int ecx) { throw new AssertionError("IAT"); }
        @Override public void call423283c(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d) { throw new AssertionError("signal5"); }
        @Override public void call423283c(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d, long entry) { throw new AssertionError("signal6"); }
        @Override public void call4242354(Terminal207Api.Memory m, long site, int ecx) { throw new AssertionError("last"); }
    }

    /** Typed opaque callbacks for exactly the two finite scenes, never a leaf interpreter. */
    private static final class Leaf extends FailingLeaf {
        private final Memory memory;
        private final boolean full;
        private final long entry;
        private final long body;

        private Leaf(Memory memory, boolean full, long entry) {
            this.memory = memory;
            this.full = full;
            this.entry = entry;
            this.body = entry - 0x608L;
        }

        private void same(Terminal207Api.Memory actual) { require(actual == memory, "leaf callback Memory identity"); }

        @Override public void call4224800Initial(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d) {
            same(m);
            require(full, "direct ECX=-1 skips initial");
            equal(site, 0x4232876L, "initial site");
            equal(ecx, 3, "initial ECX"); equal(edx, 0x40000015, "initial EDX"); equal(r8d, 1, "initial R8D");
            port(memory.events, "INIT:" + hx(site) + ":" + ix(ecx) + ":" + ix(edx) + ":" + ix(r8d));
        }

        @Override public void call4226f10(Terminal207Api.Memory m, long site, long rcx, int edx, int r8d) {
            same(m);
            equal(edx, 0, "fill EDX");
            if (site == 0x4232888L) {
                equal(rcx, body + 0x70L, "first fill address"); equal(r8d, 0x98, "first fill count");
            } else {
                equal(site, 0x4232899L, "second fill site");
                equal(rcx, body + 0x110L, "second fill address"); equal(r8d, 0x4D0, "second fill count");
                // Explicit supplied effects; no library-name memset assumption.
                memory.seed64(body + 0x208L, R14);
                memory.seed64(0x143DA418L, CODE418);
            }
            port(memory.events, "FILL:" + hx(site) + ":" + hx(rcx) + ":" + ix(edx) + ":" + ix(r8d));
        }

        @Override public void call43da418(Terminal207Api.Memory m, long site, long code, long rcx) {
            same(m); equal(site, 0x42328B5L, "418 site"); equal(code, CODE418, "418 fresh code");
            equal(rcx, body + 0x110L, "418 RCX");
            port(memory.events, "SETUP:" + hx(site) + ":" + hx(code) + ":" + hx(rcx));
            memory.seed64(0x143DA2A0L, CODE2A0);
        }

        @Override public long call43da2a0(Terminal207Api.Memory m, long site, long code, long rcx, long rdx, int r8d) {
            same(m); equal(site, 0x42328CDL, "lookup site"); equal(code, CODE2A0, "lookup fresh code");
            equal(rcx, R14, "captured full64 R14"); equal(rdx, body + 0x40L, "lookup RDX address"); equal(r8d, 0, "lookup R8D");
            long result = full ? 0x100000000L : 0L;
            port(memory.events, "LOOKUP:" + hx(site) + ":" + hx(code) + ":" + hx(rcx) + ":" + hx(rdx) + ":" + ix(r8d) + ":" + hx(result));
            if (full) {
                memory.seed64(body + 0x38L, 0xABCDEF0123456789L);
                memory.seed64(body + 0x40L, 0xF1E2D3C4B5A69788L);
                memory.seed64(body + 0x208L, 0x0101010101010101L);
                memory.seed64(0x143DA2A8L, CODE2A8);
            } else {
                memory.seed64(0x143DA6A0L, CODE6A0);
            }
            return result;
        }

        @Override public void call43da2a8(Terminal207Api.Memory m, long site, long code, long rcx, long rdx, long r8, long r9, long callerBodyRsp) {
            same(m); require(full, "null lookup skips detail");
            equal(site, 0x4232908L, "detail site"); equal(code, CODE2A8, "detail fresh code"); equal(rcx, 0, "detail RCX");
            equal(rdx, 0xF1E2D3C4B5A69788L, "detail fresh RDX"); equal(r8, R14, "detail captured R14 survives callback mutation");
            equal(r9, 0x100000000L, "lookup full64 high-only RAX"); equal(callerBodyRsp, body, "detail body context");
            equal(memory.peek(body + 0x38L, 8), 0, "outgoing eighth slot");
            equal(memory.peek(body + 0x30L, 8), 0x2FFFFA50L, "outgoing seventh slot");
            equal(memory.peek(body + 0x28L, 8), 0x2FFFFA58L, "outgoing sixth slot");
            equal(memory.peek(body + 0x20L, 8), 0x2FFFFB08L, "outgoing fifth slot");
            equal(memory.peek(entry, 8), 0x14232D3FL, "actual binding return-slot push before opaque change");
            port(memory.events, "DETAIL:" + hx(site) + ":" + hx(code) + ":" + hx(rcx) + ":" + hx(rdx) + ":" + hx(r8) + ":" + hx(r9) + ":" + hx(callerBodyRsp));
            memory.seed64(entry, 0x8877665544332211L);
            memory.seed64(0x143DA6A0L, CODE6A0);
        }

        @Override public int call43da6a0(Terminal207Api.Memory m, long site, long code) {
            same(m); equal(site, 0x4232941L, "6a0 site"); equal(code, CODE6A0, "6a0 fresh code");
            int result = full ? 0 : 0x80000000;
            port(memory.events, "STATUS6:" + hx(site) + ":" + hx(code) + ":" + ix(result));
            memory.seed64(0x143DA770L, CODE770);
            return result;
        }

        @Override public void call43da770(Terminal207Api.Memory m, long site, long code, int ecx) {
            same(m); equal(site, 0x423294BL, "770 site"); equal(code, CODE770, "770 fresh code"); equal(ecx, 0, "770 ECX");
            port(memory.events, "CLEAR:" + hx(site) + ":" + hx(code) + ":" + ix(ecx));
            memory.seed64(0x143DA2B0L, CODE2B0);
        }

        @Override public int call43da2b0(Terminal207Api.Memory m, long site, long code, long rcx) {
            same(m); equal(site, 0x4232956L, "2b0 site"); equal(code, CODE2B0, "2b0 fresh code"); equal(rcx, body + 0x48L, "2b0 address RCX");
            port(memory.events, "STATUS2:" + hx(site) + ":" + hx(code) + ":" + hx(rcx) + ":0");
            if (!full) memory.seed64(body + 0x5E0L, 0x0102030405060708L);
            return 0;
        }

        @Override public void call4224800Repeat(Terminal207Api.Memory m, long site, int ecx) {
            same(m); require(full, "direct repeat skipped"); equal(site, 0x423296BL, "repeat site"); equal(ecx, 3, "repeat sole known ECX");
            port(memory.events, "REPEAT:" + hx(site) + ":" + ix(ecx));
            memory.seed64(body + 0x5E0L, 0x1122334455667788L);
        }

        @Override public void call4224700(Terminal207Api.Memory m, long site, long rcx) {
            same(m); equal(site, 0x423297AL, "cookie site");
            equal(rcx, full ? 0x112233447A998E70L : 0x010203041AF9FEF0L, "fresh final cookie XOR body");
            port(memory.events, "COOKIE:" + hx(site) + ":" + hx(rcx));
        }
    }

    private static void seedInputs(Memory memory, long body) {
        memory.seed64(0x1542F0B8L, COOKIE);
        memory.seed64(0x143DA418L, 0x1111111111111111L);
        memory.seed64(0x143DA2A0L, 0x2222222222222222L);
        memory.seed64(0x143DA2A8L, 0x3333333333333333L);
        memory.seed64(0x143DA6A0L, 0x4444444444444444L);
        memory.seed64(0x143DA770L, 0x5555555555555555L);
        memory.seed64(0x143DA2B0L, 0x6666666666666666L);
        memory.seed64(body + 0x70L, 0x0102030405060708L);
        memory.seed64(body + 0x78L, 0xBADDCAFE10203040L);
    }

    private static Memory expectedFrom(Map<Long, Byte> before) {
        Memory expected = new Memory(new ArrayList<>());
        expected.bytes.putAll(before);
        expected.seed64(0x143DA418L, CODE418);
        expected.seed64(0x143DA2A0L, CODE2A0);
        expected.seed64(0x143DA6A0L, CODE6A0);
        expected.seed64(0x143DA770L, CODE770);
        expected.seed64(0x143DA2B0L, CODE2B0);
        return expected;
    }

    private static void directNull() {
        List<String> events = new ArrayList<>();
        Memory memory = new Memory(events);
        seedInputs(memory, 0x1FFFF9F8L);
        memory.seed64(0x20000000L, 0x1122334455667788L);
        Map<Long, Byte> before = new HashMap<>(memory.bytes);
        TerminalSignal423283C.execute(memory, new Leaf(memory, false, 0x20000000L),
                new TerminalSignal213Api.Input(BASE, 0x20000000L, -1, 0x89ABCDEF, 0xFEDCBA98));
        exhausted(events,
                "R64:1542f0b8:c0ffee123456789a", "W64:1fffffd8:c0ffee122ba98162",
                "FILL:4232888:1ffffa68:0:98", "FILL:4232899:1ffffb08:0:4d0",
                "W64:1ffffa40:1ffffa68", "W64:1ffffa48:1ffffb08",
                "R64:143da418:8122334455667788", "SETUP:42328b5:8122334455667788:1ffffb08",
                "R64:1ffffc00:fedcba9876543210", "R64:143da2a0:9233445566778899",
                "LOOKUP:42328cd:9233445566778899:fedcba9876543210:1ffffa38:0:0",
                "R64:20000000:1122334455667788", "W64:1ffffc00:1122334455667788",
                "W32:1ffffa68:89abcdef", "W64:1ffffba0:20000008",
                "R64:20000000:1122334455667788", "W64:1ffffa78:1122334455667788", "W32:1ffffa6c:fedcba98",
                "R64:143da6a0:b45566778899aabb", "STATUS6:4232941:b45566778899aabb:80000000",
                "R64:143da770:c566778899aabbcc", "CLEAR:423294b:c566778899aabbcc:0",
                "R64:143da2b0:d6778899aabbccdd", "STATUS2:4232956:d6778899aabbccdd:1ffffa40:0",
                "R64:1fffffd8:102030405060708", "COOKIE:423297a:10203041af9fef0");
        Memory expected = expectedFrom(before);
        expected.seed64(0x1FFFFFD8L, 0x0102030405060708L);
        expected.seed64(0x1FFFFA40L, 0x1FFFFA68L);
        expected.seed64(0x1FFFFA48L, 0x1FFFFB08L);
        expected.seed64(0x1FFFFC00L, 0x1122334455667788L);
        expected.seed64(0x1FFFFA68L, 0xFEDCBA9889ABCDEFL);
        expected.seed64(0x1FFFFBA0L, 0x20000008L);
        expected.seed64(0x1FFFFA78L, 0x1122334455667788L);
        require(memory.bytes.equals(expected.bytes), "direct complete final bytes including neighboring canary");
    }

    private static void boundFull() {
        List<String> events = new ArrayList<>();
        Memory memory = new Memory(events);
        seedInputs(memory, 0x2FFFF9F8L);
        require(!memory.bytes.containsKey(0x30000000L), "bound E not preseeded");
        Map<Long, Byte> before = new HashMap<>(memory.bytes);
        Terminal207Api.Ports bound = TerminalSignalBinding213.bind(memory, new Leaf(memory, true, 0x30000000L), new FailingTerminal(), BASE);
        exhausted(events);
        bound.call423283c(memory, 0x4232D3AL, 3, 0x40000015, 1, 0x30000000L);
        exhausted(events,
                "W64:30000000:14232d3f", "R64:1542f0b8:c0ffee123456789a", "W64:2fffffd8:c0ffee121ba98162",
                "INIT:4232876:3:40000015:1", "FILL:4232888:2ffffa68:0:98", "FILL:4232899:2ffffb08:0:4d0",
                "W64:2ffffa40:2ffffa68", "W64:2ffffa48:2ffffb08",
                "R64:143da418:8122334455667788", "SETUP:42328b5:8122334455667788:2ffffb08",
                "R64:2ffffc00:fedcba9876543210", "R64:143da2a0:9233445566778899",
                "LOOKUP:42328cd:9233445566778899:fedcba9876543210:2ffffa38:0:100000000",
                "R64:2ffffa30:abcdef0123456789", "W64:2ffffa30:0", "R64:2ffffa38:f1e2d3c4b5a69788",
                "W64:2ffffa28:2ffffa50", "W64:2ffffa20:2ffffa58", "W64:2ffffa18:2ffffb08",
                "R64:143da2a8:a3445566778899aa",
                "DETAIL:4232908:a3445566778899aa:0:f1e2d3c4b5a69788:fedcba9876543210:100000000:2ffff9f8",
                "R64:30000000:8877665544332211", "W64:2ffffc00:8877665544332211",
                "W32:2ffffa68:40000015", "W64:2ffffba0:30000008",
                "R64:30000000:8877665544332211", "W64:2ffffa78:8877665544332211", "W32:2ffffa6c:1",
                "R64:143da6a0:b45566778899aabb", "STATUS6:4232941:b45566778899aabb:0",
                "R64:143da770:c566778899aabbcc", "CLEAR:423294b:c566778899aabbcc:0",
                "R64:143da2b0:d6778899aabbccdd", "STATUS2:4232956:d6778899aabbccdd:2ffffa40:0",
                "REPEAT:423296b:3", "R64:2fffffd8:1122334455667788", "COOKIE:423297a:112233447a998e70");
        Memory expected = expectedFrom(before);
        expected.seed64(0x143DA2A8L, CODE2A8);
        expected.seed64(0x30000000L, 0x8877665544332211L);
        expected.seed64(0x2FFFFFD8L, 0x1122334455667788L);
        expected.seed64(0x2FFFFA40L, 0x2FFFFA68L);
        expected.seed64(0x2FFFFA48L, 0x2FFFFB08L);
        expected.seed64(0x2FFFFC00L, 0x8877665544332211L);
        expected.seed64(0x2FFFFA30L, 0);
        expected.seed64(0x2FFFFA38L, 0xF1E2D3C4B5A69788L);
        expected.seed64(0x2FFFFA28L, 0x2FFFFA50L);
        expected.seed64(0x2FFFFA20L, 0x2FFFFA58L);
        expected.seed64(0x2FFFFA18L, 0x2FFFFB08L);
        expected.seed64(0x2FFFFA68L, 0x0000000140000015L);
        expected.seed64(0x2FFFFBA0L, 0x30000008L);
        expected.seed64(0x2FFFFA78L, 0x8877665544332211L);
        require(memory.bytes.equals(expected.bytes), "bound complete final bytes and no second push/unclaimed cells");
    }

    private static void qualificationAndCompatibility() {
        List<String> events = new ArrayList<>();
        Memory captured = new Memory(events);
        Memory foreign = new Memory(events);
        captured.seed64(0x45000008L, 0x0123456789ABCDEFL);
        foreign.seed64(0x55000008L, 0xFEDCBA9876543210L);
        Map<Long, Byte> beforeCaptured = new HashMap<>(captured.bytes);
        Map<Long, Byte> beforeForeign = new HashMap<>(foreign.bytes);
        Terminal207Api.Ports fallback = new FailingTerminal() {
            @Override public void call423283c(Terminal207Api.Memory m, long site, int ecx, int edx, int r8d) {
                require(m == foreign, "legacy signal callback object"); equal(site, 0x76543210L, "legacy signal site");
                equal(ecx, -7, "legacy ECX"); equal(edx, 0x80000000, "legacy EDX"); equal(r8d, 0x89ABCDEF, "legacy R8D");
                port(events, "OLD_SIGNAL:" + hx(site) + ":" + ix(ecx) + ":" + ix(edx) + ":" + ix(r8d));
            }
            @Override public void call4247004(Terminal207Api.Memory m, long site, int ecx, long entry) {
                require(m == foreign, "new handler callback object"); equal(site, 0x6543210L, "new handler site");
                equal(ecx, 0x80000000, "new handler ECX"); equal(entry, 0xF123456789ABCDEFL, "new handler full64 context");
                port(events, "NEW_HANDLER:" + hx(site) + ":" + ix(ecx) + ":" + hx(entry));
            }
        };
        Terminal207Api.Ports bound = TerminalSignalBinding213.bind(captured, new FailingLeaf(), fallback, BASE);
        exhausted(events);
        expectIAE(() -> bound.call423283c(foreign, 0x4232D3AL, 3, 0x40000015, 1, 0x50000000L));
        exhausted(events);
        require(captured.bytes.equals(beforeCaptured) && foreign.bytes.equals(beforeForeign), "foreign rejection before all effects");
        expectIAE(() -> bound.call423283c(captured, 0x4232D3BL, 3, 0x40000015, 1, 0x50000000L));
        exhausted(events);
        require(captured.bytes.equals(beforeCaptured) && foreign.bytes.equals(beforeForeign), "site rejection before all effects");
        bound.call423283c(foreign, 0x76543210L, -7, 0x80000000, 0x89ABCDEF);
        bound.call4247004(foreign, 0x6543210L, 0x80000000, 0xF123456789ABCDEFL);
        exhausted(events, "OLD_SIGNAL:76543210:fffffff9:80000000:89abcdef", "NEW_HANDLER:6543210:80000000:f123456789abcdef");
        require(captured.bytes.equals(beforeCaptured) && foreign.bytes.equals(beforeForeign), "compatibility has zero Memory/leaf effect");
    }

    public static void main(String[] args) {
        directNull();
        boundFull();
        qualificationAndCompatibility();
        equal(memoryEvents, 44, "finite Memory events");
        equal(portEvents, 21, "finite port events");
        System.out.println("TerminalSignalValidation213 groups=3 events=65 memory=44 ports=21 checks="
                + checks + " software_only=true");
    }
}
