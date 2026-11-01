package org.xar.ck3.research.m3.terminal214;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.research.m3.terminal207.Terminal4232CF4;
import static org.xar.ck3.research.m3.terminal214.Terminal4247004Api214.*;

/** Finite independent observations derived from the held 618B and pure API only. */
public final class TerminalHandlerValidation214 {
    private static final long BASE = 0x1_0000_0000L;
    private static final long H = 0x7000_0000L;
    private static final long B = H - 0x68L;
    private static final long COOKIE = BASE + 0x542F0B8L;
    private static final long CELL = BASE + 0x5C5D318L;
    private static final long SLOT = BASE + 0x43DBBA8L;
    private static int groups;
    private static int fixtures;
    private static int events;
    private static int memoryEvents;
    private static int portEvents;
    private static int finalCells;
    private static int callbackWrites;

    private TerminalHandlerValidation214() { }

    private record Expected(String operation, long[] arguments, long reply, Runnable effect) { }

    private static final class Host implements Memory, Ports {
        private final String label;
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Expected> ordered = new ArrayList<>();
        private int next;

        Host(String label) { this.label = label; }

        void expect(String operation, long... arguments) {
            ordered.add(new Expected(operation, arguments, 0L, null));
        }

        void port(String operation, long reply, Runnable effect, long... arguments) {
            ordered.add(new Expected(operation, arguments, reply, effect));
        }

        long observe(String operation, long... arguments) {
            if (next == ordered.size()) throw new AssertionError(label + ": extra " + operation);
            Expected expected = ordered.get(next++);
            if (!expected.operation().equals(operation) || !Arrays.equals(expected.arguments(), arguments)) {
                throw new AssertionError(label + ": event " + (next - 1) + " expected "
                        + expected.operation() + Arrays.toString(expected.arguments()) + " got "
                        + operation + Arrays.toString(arguments));
            }
            events++;
            if (operation.charAt(0) == 'R' || operation.charAt(0) == 'W') memoryEvents++;
            else portEvents++;
            if (expected.effect() != null) expected.effect().run();
            return expected.reply();
        }

        void seed(long address, int width, long value) {
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
        }

        void callbackWrite(long address, int width, long value) {
            callbackWrites++;
            seed(address, width, value);
        }

        long load(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte part = bytes.get(address + i);
                if (part == null) throw new AssertionError(label + ": missing byte " + Long.toHexString(address + i));
                value |= (part.longValue() & 255L) << (8 * i);
            }
            return value;
        }

        void cell(long address, int width, long expected) {
            long mask = width == 8 ? -1L : (1L << (width * 8)) - 1L;
            if (load(address, width) != (expected & mask)) {
                throw new AssertionError(label + ": final bytes at " + Long.toHexString(address));
            }
            finalCells++;
        }

        void done() {
            if (next != ordered.size()) throw new AssertionError(label + ": unconsumed " + (ordered.size() - next));
            fixtures++;
        }

        private void same(Memory memory) {
            if (memory != this) throw new AssertionError(label + ": child Memory identity");
        }

        @Override public long readPointer(long address) {
            long value = load(address, 8);
            observe("R64", address, value);
            return value;
        }
        @Override public int readInt32(long address) {
            int value = (int) load(address, 4);
            observe("R32", address, Integer.toUnsignedLong(value));
            return value;
        }
        @Override public int readUnsigned8(long address) {
            int value = (int) load(address, 1);
            observe("R8", address, value);
            return value;
        }
        @Override public void writeInt32(long address, int value) {
            observe("W32", address, Integer.toUnsignedLong(value));
            seed(address, 4, Integer.toUnsignedLong(value));
        }
        @Override public void writeInt64(long address, long value) {
            observe("W64", address, value);
            seed(address, 8, value);
        }
        @Override public void write8(long address, int value) {
            observe("W8", address, value & 255L);
            seed(address, 1, value & 255L);
        }

        @Override public long call424fc74(Memory memory, long site, int ecx) {
            same(memory); return observe("pFC74", site, Integer.toUnsignedLong(ecx));
        }
        @Override public long call423b18c(Memory memory, long site) {
            same(memory); return observe("pERROR", site);
        }
        @Override public void call4232a50(Memory memory, long site) {
            same(memory); observe("pERRORDONE", site);
        }
        @Override public void call4247ffc(Memory memory, long site, int ecx) {
            same(memory); observe("pENTER", site, Integer.toUnsignedLong(ecx));
        }
        @Override public long call424faf8(Memory memory, long site) {
            same(memory); return observe("pFAF8", site);
        }
        @Override public void call4248050(Memory memory, long site, int ecx) {
            same(memory); observe("pLEAVE", site, Integer.toUnsignedLong(ecx));
        }
        @Override public void call4242354(Memory memory, long site, int ecx) {
            same(memory); observe("pABORT", site, Integer.toUnsignedLong(ecx));
        }
        @Override public void callIndirectR8(Memory memory, DispatchR8 call) {
            same(memory);
            observe("pR8", call.siteRva(), call.targetSlotAddress(), call.targetBits(),
                    call.handlerBits(), Integer.toUnsignedLong(call.ecxBits()), Integer.toUnsignedLong(call.edxBits()));
        }
        @Override public void callIndirectRdx(Memory memory, DispatchRdx call) {
            same(memory);
            observe("pRDX", call.siteRva(), call.targetSlotAddress(), call.targetBits(),
                    call.handlerBits(), Integer.toUnsignedLong(call.ecxBits()));
        }
    }

    private static final class Fallback implements Terminal207Api.Ports {
        private final Host host;
        Fallback(Host host) { this.host = host; }
        private void same(Terminal207Api.Memory memory) {
            if (memory != host) throw new AssertionError("fallback Memory identity");
        }
        @Override public long call4246fb4(Terminal207Api.Memory memory, long site) {
            same(memory); return host.observe("fFIRST2", site);
        }
        @Override public long call4246fb4(Terminal207Api.Memory memory, long site, long entry) {
            same(memory); return host.observe("fFIRST3", site, entry);
        }
        @Override public void call4247004(Terminal207Api.Memory memory, long site, int ecx) {
            same(memory); host.observe("fHANDLER3", site, Integer.toUnsignedLong(ecx));
        }
        @Override public void call4247004(Terminal207Api.Memory memory, long site, int ecx, long entry) {
            same(memory); host.observe("fHANDLER4", site, Integer.toUnsignedLong(ecx), entry);
        }
        @Override public int call43da258(Terminal207Api.Memory memory, long site, long code, int ecx) {
            same(memory); return (int) host.observe("fIAT", site, code, Integer.toUnsignedLong(ecx));
        }
        @Override public void call423283c(Terminal207Api.Memory memory, long site, int ecx, int edx, int r8d) {
            same(memory); host.observe("fSIGNAL5", site, Integer.toUnsignedLong(ecx),
                    Integer.toUnsignedLong(edx), Integer.toUnsignedLong(r8d));
        }
        @Override public void call423283c(Terminal207Api.Memory memory, long site, int ecx, int edx, int r8d, long entry) {
            same(memory); host.observe("fSIGNAL6", site, Integer.toUnsignedLong(ecx),
                    Integer.toUnsignedLong(edx), Integer.toUnsignedLong(r8d), entry);
        }
        @Override public void call4242354(Terminal207Api.Memory memory, long site, int ecx) {
            same(memory); host.observe("fFINAL", site, Integer.toUnsignedLong(ecx));
        }
    }

    private static void stack(Host host, boolean include80) {
        host.seed(B + 0x70, 8, 0x11223344556677AAL);
        host.seed(B + 0x78, 4, 0xAABBCCDDL);
        host.seed(B + 0x7C, 4, 0x99887766L);
        if (include80) host.seed(B + 0x80, 8, 0x0102030405060708L);
    }

    private static void initial(Host host) {
        host.expect("R32", B + 0x78, 0xAABBCCDDL);
        host.expect("W32", B + 0x78, 0L);
        host.expect("W8", B + 0x70, 1L);
    }

    private static void rmw80(Host host) {
        host.expect("R64", B + 0x80, 0x0102030405060708L);
        host.expect("W64", B + 0x80, 0L);
    }

    private static Host code22(String label, boolean zero, boolean withCaller) {
        Host host = new Host(label);
        stack(host, true);
        host.seed(CELL, 8, zero ? 5L : 0x25L);
        host.seed(COOKIE, 8, 5L);
        if (withCaller) host.port("fFIRST3", 1L, null, 0x4232CF8L, H);
        initial(host);
        rmw80(host);
        host.expect("pENTER", 0x424711FL, 3L);
        host.expect("R64", CELL, zero ? 5L : 0x25L);
        host.expect("R64", COOKIE, 5L);
        host.expect("pLEAVE", zero ? 0x424725DL : 0x42471EDL, 3L);
        if (zero) host.expect("pABORT", 0x4247267L, 3L);
        return host;
    }

    private static void normal(Outcome outcome, long bits) {
        if (!(outcome instanceof NormalReturn result) || result.raxBits() != bits) {
            throw new AssertionError("normal outcome/bits " + outcome);
        }
    }

    private static void basicFinal(Host host, boolean include80, int byte70) {
        host.cell(B + 0x70, 8, 0x1122334455667700L | byte70);
        host.cell(B + 0x78, 4, 0L);
        host.cell(B + 0x7C, 4, 0x99887766L);
        if (include80) host.cell(B + 0x80, 8, 0L);
    }

    private static void groupNormal22() {
        Host direct = code22("22-one-direct", false, false);
        normal(TerminalHandler4247004.execute(direct, direct, new Input(BASE, 22, new Scratch(H))), 0L);
        basicFinal(direct, true, 1);
        direct.cell(CELL, 8, 0x25L);
        direct.cell(COOKIE, 8, 5L);
        direct.done();

        Host bound = code22("22-one-bound", false, false);
        Terminal207Api.Ports ports = TerminalHandlerBinding214.bind(bound, bound, new Fallback(bound), BASE);
        ports.call4247004(bound, 0x4232D07L, 22, H);
        basicFinal(bound, true, 1);
        bound.cell(CELL, 8, 0x25L);
        bound.done();
        groups++;
    }

    private static void groupTrap22() {
        Host direct = code22("22-zero-direct", true, false);
        if (TerminalHandler4247004.execute(direct, direct, new Input(BASE, 22, new Scratch(H)))
                != Trap.INT3_424726D) throw new AssertionError("expected source trap enum");
        basicFinal(direct, true, 1);
        direct.done();

        Host caller = code22("22-zero-actual-caller", true, true);
        Terminal207Api.Ports ports = TerminalHandlerBinding214.bind(caller, caller, new Fallback(caller), BASE);
        try {
            Terminal4232CF4.trace(caller, ports, BASE, H + 0x30L);
            throw new AssertionError("trap binder continued caller");
        } catch (UnsupportedOperationException expected) {
            // No flag/IAT/final continuation has an expected tuple or seeded byte.
        }
        basicFinal(caller, true, 1);
        caller.done();
        groups++;
    }

    private static void groupInvalid() {
        for (int code : new int[] {1, 0x80000007}) {
            Host host = new Host("invalid-" + Integer.toUnsignedString(code));
            stack(host, false);
            long error = 0x88000000L;
            host.seed(error, 8, 0x77889900DEADBEEFL);
            initial(host);
            host.port("pERROR", error, null, 0x42470CAL);
            host.expect("W32", error, 22L);
            host.expect("pERRORDONE", 0x42470D5L);
            normal(TerminalHandler4247004.execute(host, host, new Input(BASE, code, new Scratch(H))), 0xFFFF_FFFFL);
            basicFinal(host, false, 1);
            host.cell(error, 8, 0x7788990000000016L);
            host.done();
        }
        groups++;
    }

    private static void groupCode8() {
        Host host = new Host("code8-two-clear-fresh-restore");
        long header = 0x180001000L, table = 0x180002000L, clear = 0x180003000L;
        long tls1 = 0x190001000L, tls2 = 0x190002000L;
        long tls3 = 0x190003000L, tls4 = 0x190004000L;
        long handler = 0xDEADBEEF00000002L, saved = 0x0102030405060708L;
        long restored = 0x8899AABBCCDDEEFFL, target = 0x2233445566778899L;
        stack(host, true);
        host.seed(header, 8, table);
        host.seed(header + 8, 8, saved);
        host.seed(BASE + 0x44268B0L, 8, 2L);
        host.seed(table + 4, 4, 4L);
        host.seed(table + 0x14, 4, 8L);
        host.seed(table + 0x18, 8, handler);
        host.seed(BASE + 0x44268C0L, 8, 1L);
        host.seed(BASE + 0x44268C8L, 8, 2L);
        host.seed(clear + 0x18, 8, 0xABCDEF0102030405L);
        host.seed(clear + 0x28, 8, 0x1112131415161718L);
        host.seed(tls1 + 0x10, 8, 0x1122334481234567L);
        host.seed(tls2 + 0x10, 8, 0x55667788AABBCCDDL);
        host.seed(tls3 + 0x10, 8, 0xCAFEBABEFEDCBA98L);
        host.seed(tls4 + 0x10, 8, 0x99AABBCC01010101L);
        host.seed(SLOT, 8, 0x1111111122222222L);

        initial(host);
        host.port("pFC74", header, null, 0x424707DL, 8L);
        host.expect("R64", header, table);
        host.expect("R64", BASE + 0x44268B0L, 2L);
        host.expect("R32", table + 4, 4L);
        host.expect("R32", table + 0x14, 8L);
        host.expect("W8", B + 0x70, 0L);
        rmw80(host);
        host.expect("R64", table + 0x18, handler);
        host.expect("R64", header + 8, saved);
        host.expect("W64", B + 0x80, saved);
        host.expect("W64", B + 0x30, saved);
        host.expect("R64", header + 8, saved);
        host.expect("W64", header + 8, 0L);
        host.port("pFAF8", tls1, null, 0x424717EL);
        host.expect("R32", tls1 + 0x10, 0x81234567L);
        host.expect("W32", B + 0x78, 0x81234567L);
        host.expect("W32", B + 0x20, 0x81234567L);
        host.port("pFAF8", tls2, () -> host.callbackWrite(header, 8, clear), 0x424718EL);
        host.expect("W32", tls2 + 0x10, 0x8CL);
        host.expect("R64", BASE + 0x44268C0L, 1L);
        host.expect("R64", header, clear);
        host.expect("R64", BASE + 0x44268C8L, 2L);
        host.expect("W64", B + 0x28, clear + 0x10);
        host.expect("R64", clear + 0x18, 0xABCDEF0102030405L);
        host.expect("W64", clear + 0x18, 0L);
        host.expect("W64", B + 0x28, clear + 0x20);
        host.expect("R64", clear + 0x28, 0x1112131415161718L);
        host.expect("W64", clear + 0x28, 0L);
        host.expect("W64", B + 0x28, clear + 0x30);
        host.port("pFAF8", tls3, () -> host.callbackWrite(SLOT, 8, target), 0x4247204L);
        host.expect("R32", tls3 + 0x10, 0xFEDCBA98L);
        host.expect("R64", SLOT, target);
        host.port("pR8", 0L, () -> {
            host.callbackWrite(B + 0x80, 8, restored);
            host.callbackWrite(B + 0x78, 4, 0x92345678L);
        }, 0x4247218L, SLOT, target, handler, 8L, 0xFEDCBA98L);
        host.expect("R64", B + 0x80, restored);
        host.expect("W64", header + 8, restored);
        host.port("pFAF8", tls4, () -> host.callbackWrite(B + 0x78, 4, 0xA3456789L), 0x4247247L);
        host.expect("R32", B + 0x78, 0xA3456789L);
        host.expect("W32", tls4 + 0x10, 0xA3456789L);

        normal(TerminalHandler4247004.execute(host, host, new Input(BASE, 8, new Scratch(H))), 0L);
        host.cell(B + 0x70, 8, 0x1122334455667700L);
        host.cell(B + 0x78, 4, 0xA3456789L);
        host.cell(B + 0x7C, 4, 0x99887766L);
        host.cell(B + 0x80, 8, restored);
        host.cell(B + 0x30, 8, saved);
        host.cell(B + 0x20, 4, 0x81234567L);
        host.cell(B + 0x28, 8, clear + 0x30);
        host.cell(header, 8, clear);
        host.cell(header + 8, 8, restored);
        host.cell(clear + 0x18, 8, 0L);
        host.cell(clear + 0x28, 8, 0L);
        host.cell(table + 0x18, 8, handler);
        host.cell(tls1 + 0x10, 8, 0x1122334481234567L);
        host.cell(tls2 + 0x10, 8, 0x556677880000008CL);
        host.cell(tls3 + 0x10, 8, 0xCAFEBABEFEDCBA98L);
        host.cell(tls4 + 0x10, 8, 0x99AABBCCA3456789L);
        host.cell(SLOT, 8, target);
        host.done();
        groups++;
    }

    private static void illegalArgument(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) { }
    }

    private static void groupBinding() {
        Host captured = new Host("guard-captured"), foreign = new Host("guard-foreign");
        Terminal207Api.Ports bound = TerminalHandlerBinding214.bind(captured, captured, new Fallback(captured), BASE);
        illegalArgument(() -> bound.call4247004(foreign, 0x4232D07L, 22, H));
        illegalArgument(() -> bound.call4247004(captured, 0x4247004L, 22, H));
        captured.done();
        foreign.done();

        Host host = new Host("all-seven-forwarders");
        long firstBits = 0x8000000000000000L;
        long firstContextBits = 0x1234567800000000L;
        long context = 0xFEDC000011110000L;
        host.port("fFIRST2", firstBits, null, 17L);
        host.port("fFIRST3", firstContextBits, null, 18L, context);
        host.expect("fHANDLER3", 19L, 0x80000007L);
        host.port("fIAT", 0x80000000L, null, 20L, 0x9988776655443322L, 0x89ABCDEFL);
        host.expect("fSIGNAL5", 21L, 3L, 0xFFFFFFFFL, 0x80000000L);
        host.expect("fSIGNAL6", 22L, 0xFFFFFFFDL, 0xFFFFFFFCL, 0xFFFFFFFBL, context);
        host.expect("fFINAL", 23L, 0xFFFFFFFAL);
        RuntimeException marker = new RuntimeException("fallback-marker");
        host.port("fSIGNAL6", 0L, () -> { throw marker; }, 24L, 3L, 4L, 5L, H);
        Terminal207Api.Ports forwarding = TerminalHandlerBinding214.bind(host, host, new Fallback(host), BASE);
        if (forwarding.call4246fb4(host, 17L) != firstBits) throw new AssertionError("first2 bits");
        if (forwarding.call4246fb4(host, 18L, context) != firstContextBits) throw new AssertionError("first3 bits");
        forwarding.call4247004(host, 19L, 0x80000007);
        if (forwarding.call43da258(host, 20L, 0x9988776655443322L, 0x89ABCDEF) != 0x80000000) {
            throw new AssertionError("IAT int return bits");
        }
        forwarding.call423283c(host, 21L, 3, -1, Integer.MIN_VALUE);
        forwarding.call423283c(host, 22L, -3, -4, -5, context);
        forwarding.call4242354(host, 23L, -6);
        try {
            forwarding.call423283c(host, 24L, 3, 4, 5, H);
            throw new AssertionError("fallback exception swallowed");
        } catch (RuntimeException actual) {
            if (actual != marker) throw new AssertionError("fallback exception identity", actual);
        }
        host.done();
        groups++;
    }

    public static void main(String[] args) {
        groupNormal22();
        groupTrap22();
        groupInvalid();
        groupCode8();
        groupBinding();
        if (groups != 5) throw new AssertionError("five finite groups");
        System.out.println("groups=" + groups + " fixtures=" + fixtures + " events=" + events
                + " memoryEvents=" + memoryEvents + " portEvents=" + portEvents
                + " finalCells=" + finalCells + " callbackWrites=" + callbackWrites);
    }
}
