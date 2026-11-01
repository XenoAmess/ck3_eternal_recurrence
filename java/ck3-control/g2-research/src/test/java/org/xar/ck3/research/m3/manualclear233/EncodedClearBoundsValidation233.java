package org.xar.ck3.research.m3.manualclear233;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api;
import org.xar.ck3.research.m3.clear230.EncodedClear230BoundsPorts;
import org.xar.ck3.research.m3.clear230.EncodedClear424DD60;

/** Finite supplied-storage compatibility witness; source-derived software checks only. */
public final class EncodedClearBoundsValidation233 {
    private EncodedClearBoundsValidation233() { }
    private static int checks;
    private static int groups;
    private static int events;
    private static void check(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }
    private static String h(long value) { return Long.toUnsignedString(value, 16); }
    private static String r(long address, long value) { return "R64:" + h(address) + ":" + h(value); }
    private static String w(long address, long value) { return "W64:" + h(address) + ":" + h(value); }
    private static String e(long address, long value) { return "E64:" + h(address) + ":" + h(value); }
    private static String argumentState(EncodedClear230Api.RdxR9 state) {
        if (state == EncodedClear230Api.EntryUnknown.UNKNOWN) return "entry-unknown";
        if (state instanceof EncodedClear230Api.Reloaded value) return "reloaded:" + h(value.rdx()) + ":" + h(value.r9());
        throw new AssertionError("unknown RdxR9 variant");
    }
    private static String i(String dispatch, long site, long target, long rax, int ecx,
            long cookie, String argumentState, String bounds) {
        return "I:" + dispatch + ":" + h(site) + ":" + h(target) + ":" + h(rax) + ":"
                + ecx + ":" + h(cookie) + ":" + argumentState + ":" + bounds;
    }
    private static String f(String dispatch, long site, long rcx, String bounds) {
        return "F:" + dispatch + ":" + h(site) + ":" + h(rcx) + ":" + bounds;
    }
    private static String bounds(EncodedClear230BoundsPorts.DecodedBounds value) {
        return value == null ? "none" : h(value.beginBits()) + ":" + h(value.endBits());
    }
    private static final class Ram implements NativeTaskMemory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<String> trace = new ArrayList<>();
        private long raw(long address, int width) {
            long value = 0;
            for (int index = 0; index < width; index++) {
                Byte part = bytes.get(address + index);
                if (part == null) throw new AssertionError("unmapped byte " + h(address + index));
                value |= (part.longValue() & 255L) << (index * 8);
            }
            return value;
        }
        private void store(long address, int width, long value) {
            for (int index = 0; index < width; index++) bytes.put(address + index, (byte) (value >>> (index * 8)));
        }
        void seed64(long address, long value) { store(address, 8, value); }
        void seed8(long address, int value) { check((value & ~255) == 0, "seed BYTE range"); store(address, 1, value); }
        void effect64(long address, long value) { trace.add(e(address, value)); store(address, 8, value); }
        long peek64(long address) { return raw(address, 8); }
        int peek8(long address) { return (int) raw(address, 1); }
        Map<Long, Byte> snapshot() { return Map.copyOf(bytes); }
        @Override public long readPointer(long address) { long value = raw(address, 8); trace.add(r(address, value)); return value; }
        @Override public int readInt32(long address) { long value = raw(address, 4); trace.add("R32:" + h(address) + ":" + h(value)); return (int) value; }
        @Override public void writeInt32(long address, int value) { trace.add("W32:" + h(address) + ":" + Integer.toUnsignedString(value, 16)); store(address, 4, Integer.toUnsignedLong(value)); }
        @Override public void writeInt64(long address, long value) { trace.add(w(address, value)); store(address, 8, value); }
    }
    @FunctionalInterface private interface IndirectHook {
        void call(Ram memory, long site, long target, long rax,
                EncodedClear230Api.IndirectArguments arguments,
                EncodedClear230BoundsPorts.DecodedBounds bounds);
    }
    @FunctionalInterface private interface FreeHook {
        void call(Ram memory, long site, long rcx, EncodedClear230BoundsPorts.DecodedBounds bounds);
    }
    private static class LegacyPorts implements EncodedClear230Api.Ports {
        final Ram captured;
        final IndirectHook indirect;
        final FreeHook free;
        int legacyIndirect;
        int legacyFree;
        int boundsIndirect;
        int boundsFree;
        LegacyPorts(Ram captured, IndirectHook indirect, FreeHook free) {
            this.captured = captured; this.indirect = indirect; this.free = free;
        }
        @Override public void call43dbba8(NativeTaskMemory memory, long site, long target,
                long rax, EncodedClear230Api.IndirectArguments arguments) {
            check(memory == captured, "legacy indirect same memory"); legacyIndirect++;
            captured.trace.add(i("legacy", site, target, rax, arguments.ecx(), arguments.r8(), argumentState(arguments.rdxR9()), "none"));
            indirect.call(captured, site, target, rax, arguments, null);
        }
        @Override public void call424e364(NativeTaskMemory memory, long site, long rcx) {
            check(memory == captured, "legacy free same memory"); legacyFree++;
            captured.trace.add(f("legacy", site, rcx, "none")); free.call(captured, site, rcx, null);
        }
    }
    private static final class BoundsPorts extends LegacyPorts implements EncodedClear230BoundsPorts {
        BoundsPorts(Ram captured, IndirectHook indirect, FreeHook free) { super(captured, indirect, free); }
        @Override public void call43dbba8WithBounds(NativeTaskMemory memory, long site, long target,
                long rax, EncodedClear230Api.IndirectArguments arguments, DecodedBounds cachedBounds) {
            check(memory == captured, "bounds indirect same memory"); boundsIndirect++;
            captured.trace.add(i("bounds", site, target, rax, arguments.ecx(), arguments.r8(), argumentState(arguments.rdxR9()), bounds(cachedBounds)));
            indirect.call(captured, site, target, rax, arguments, cachedBounds);
        }
        @Override public void call424e364WithBounds(NativeTaskMemory memory, long site, long rcx,
                DecodedBounds cachedBounds) {
            check(memory == captured, "bounds free same memory"); boundsFree++;
            captured.trace.add(f("bounds", site, rcx, bounds(cachedBounds)));
            free.call(captured, site, rcx, cachedBounds);
        }
    }
    private static void complete(Ram memory, List<String> expected, String label) {
        check(memory.trace.equals(expected), label + " complete ordered memory/port/effect trace\nexpected=" + expected + "\nactual=" + memory.trace);
        groups++; events += memory.trace.size();
    }
    private static void legacyCompatibility() {
        Ram ram = new Ram();
        long base = 0x10000000L;
        long entry = base + 0x100L;
        long outer = base + 0x200L;
        long descriptor = base + 0x300L;
        long begin = 0x5000L;
        long end = 0x5008L;
        long cookieAddress = base + 0x542F0B8L;
        long iatAddress = base + 0x43DBBA8L;
        long initialCookie = 0x123456789ABCDEF1L;
        long refreshedCookie = 0x8877665544332202L;
        long finalCookie = 0xF0E1D2C3B4A59687L;
        long payload = 0x8123456789ABCDEFL;
        long target = 0xFEDCBA9876543210L;
        int rotate = (int) (initialCookie & 63L);
        int nextRotate = (int) (refreshedCookie & 63L);
        long encodedBegin = Long.rotateLeft(begin, rotate) ^ initialCookie;
        long encodedEnd = Long.rotateLeft(end, rotate) ^ initialCookie;
        long nextEncodedBegin = Long.rotateLeft(begin, nextRotate) ^ refreshedCookie;
        long nextEncodedEnd = Long.rotateLeft(end, nextRotate) ^ refreshedCookie;
        long encodedCell = Long.rotateLeft(payload, rotate) ^ initialCookie;
        ram.seed64(entry, outer);
        ram.seed64(outer, descriptor);
        ram.seed64(descriptor, encodedBegin);
        ram.seed64(descriptor + 8L, encodedEnd);
        ram.seed64(cookieAddress, initialCookie);
        ram.seed64(iatAddress, target);
        ram.seed64(begin, encodedCell);
        ram.seed8(descriptor - 1L, 0xA1);
        ram.seed8(descriptor + 24L, 0xB2);
        ram.seed8(begin - 1L, 0xC3);
        ram.seed8(end, 0xD4);

        List<String> expected = List.of(
                r(entry, outer), r(outer, descriptor), r(cookieAddress, initialCookie),
                r(descriptor, encodedBegin), r(descriptor + 8L, encodedEnd),
                r(begin, encodedCell), w(begin, initialCookie), r(iatAddress, target),
                i("legacy", 0x424DDE5L, target, payload, rotate, initialCookie, "entry-unknown", "none"),
                e(cookieAddress, refreshedCookie), e(descriptor, nextEncodedBegin), e(descriptor + 8L, nextEncodedEnd),
                r(cookieAddress, refreshedCookie), r(entry, outer), r(outer, descriptor),
                r(descriptor, nextEncodedBegin), r(descriptor + 8L, nextEncodedEnd),
                f("legacy", 0x424DE32L, begin, "none"), e(cookieAddress, finalCookie),
                r(cookieAddress, finalCookie),
                r(entry, outer), r(outer, descriptor), w(descriptor, finalCookie),
                r(entry, outer), r(outer, descriptor), w(descriptor + 8L, finalCookie),
                r(entry, outer), r(outer, descriptor), w(descriptor + 16L, finalCookie));
        LegacyPorts ports = new LegacyPorts(ram,
                (m, site, actualTarget, rax, arguments, suppliedBounds) -> {
                    check(suppliedBounds == null, "legacy indirect has no bounds metadata");
                    check(site == 0x424DDE5L && actualTarget == target, "legacy exact indirect site/target");
                    check(rax == payload && arguments.ecx() == rotate && arguments.r8() == initialCookie,
                            "legacy actual full64 RAX/cookie and low6 ECX");
                    check(arguments.rdxR9() == EncodedClear230Api.EntryUnknown.UNKNOWN, "legacy initial unknown RDX/R9");
                    m.effect64(cookieAddress, refreshedCookie);
                    m.effect64(descriptor, nextEncodedBegin);
                    m.effect64(descriptor + 8L, nextEncodedEnd);
                },
                (m, site, rcx, suppliedBounds) -> {
                    check(suppliedBounds == null, "legacy free has no bounds metadata");
                    check(site == 0x424DE32L && rcx == begin, "legacy exact free site/RCX");
                    m.effect64(cookieAddress, finalCookie);
                });
        long returned = EncodedClear424DD60.execute(ram, ports, new EncodedClear230Api.Input(base, entry));
        check(returned == 0L, "legacy zero-extended normal return");
        check(ports.legacyIndirect == 1 && ports.legacyFree == 1, "one actual old callback of each kind");
        check(ports.boundsIndirect == 0 && ports.boundsFree == 0, "legacy does not receive opt-in callback");
        check(ram.peek64(begin) == initialCookie, "legacy cell marker retains initial cookie");
        check(ram.peek64(descriptor) == finalCookie && ram.peek64(descriptor + 8L) == finalCookie
                && ram.peek64(descriptor + 16L) == finalCookie, "legacy final three exact-width stores use fresh cookie");
        check(ram.peek64(cookieAddress) == finalCookie, "legacy explicit free effect remains");
        check(ram.peek8(descriptor - 1L) == 0xA1 && ram.peek8(descriptor + 24L) == 0xB2
                && ram.peek8(begin - 1L) == 0xC3 && ram.peek8(end) == 0xD4,
                "legacy descriptor/cell adjacent byte canaries unchanged");
        complete(ram, expected, "legacyCompatibility");
    }
    private static void boundsOptIn() {
        Ram ram = new Ram();
        long base = 0x10000000L;
        long entryRcx = base + 0x100L;
        long outer = base + 0x200L;
        long descriptor = base + 0x300L;
        long cookieAddr = base + 0x542F0B8L;
        long iatAddr = base + 0x43DBBA8L;

        long initialCookie = 0x1122334455667788L;
        long newCookie = 0x9988776655443322L;
        long finalCookie = 0x123456789ABCDEF0L;
        long iatTarget = 0x43DBBA80L;

        long begin1 = 0x400L;
        long end1 = 0x410L;
        long cell1 = end1 - 8L;
        long liveRax1 = 0x1111111111111111L;

        long begin2 = 0x420L;
        long end2 = 0x428L;
        long cell2 = end2 - 8L;
        long liveRax2 = 0x2222222222222222L;

        int rot1 = (int) (initialCookie & 0x3FL);
        int rot2 = (int) (newCookie & 0x3FL);

        long encBegin1 = Long.rotateLeft(begin1, rot1) ^ initialCookie;
        long encEnd1 = Long.rotateLeft(end1, rot1) ^ initialCookie;

        long encBegin2 = Long.rotateLeft(begin2, rot2) ^ newCookie;
        long encEnd2 = Long.rotateLeft(end2, rot2) ^ newCookie;

        long cellVal1 = Long.rotateLeft(liveRax1, rot1) ^ initialCookie;
        long cellVal2 = Long.rotateLeft(liveRax2, rot2) ^ newCookie;

        ram.seed64(entryRcx, outer);
        ram.seed64(outer, descriptor);
        ram.seed64(descriptor, encBegin1);
        ram.seed64(descriptor + 8L, encEnd1);
        ram.seed64(cookieAddr, initialCookie);
        ram.seed64(iatAddr, iatTarget);
        ram.seed64(cell1, cellVal1);
        ram.seed64(cell2, cellVal2);

        long canaryAddr = base + 0x900L;
        ram.seed64(canaryAddr, 0xDEADBEEFCAFEBABEL);
        ram.seed8(descriptor - 1L, 0xA5);
        ram.seed8(descriptor + 24L, 0x5A);
        ram.seed8(cell1 - 1L, 0xC1);
        ram.seed8(cell1 + 8L, 0xD1);
        ram.seed8(cell2 - 1L, 0xC2);
        ram.seed8(cell2 + 8L, 0xD2);

        final int[] callbackOrdinal = {0};

        IndirectHook indirect = (Ram m, long site, long target, long rax, EncodedClear230Api.IndirectArguments args, EncodedClear230BoundsPorts.DecodedBounds bounds) -> {
            callbackOrdinal[0]++;
            if (callbackOrdinal[0] == 1) {
                check(bounds != null, "bounds present on first indirect");
                check(bounds.beginBits() == begin1, "first bounds begin");
                check(bounds.endBits() == end1, "first bounds end");
                check(args.rdxR9() == EncodedClear230Api.EntryUnknown.UNKNOWN, "first args entry-unknown");
                check(args.ecx() == rot1, "first args ecx");
                check(args.r8() == initialCookie, "first args cookie");
                check(rax == liveRax1, "first liveRax");
                check(site == 0x424DDE5L, "first site");
                check(target == iatTarget, "first target");

                m.effect64(cookieAddr, newCookie);
                m.effect64(descriptor, encBegin2);
                m.effect64(descriptor + 8L, encEnd2);
            } else if (callbackOrdinal[0] == 2) {
                check(bounds != null, "bounds present on second indirect");
                check(bounds.beginBits() == begin2, "second bounds begin");
                check(bounds.endBits() == end2, "second bounds end");
                check(args.rdxR9() instanceof EncodedClear230Api.Reloaded, "second args reloaded");
                EncodedClear230Api.Reloaded reloaded = (EncodedClear230Api.Reloaded) args.rdxR9();
                check(reloaded.rdx() == descriptor, "second reloaded rdx");
                check(reloaded.r9() == begin2, "second reloaded r9");
                check(args.ecx() == rot2, "second args ecx");
                check(args.r8() == newCookie, "second args cookie");
                check(rax == liveRax2, "second liveRax");
                check(site == 0x424DDE5L, "second site");
                check(target == iatTarget, "second target");
            } else {
                throw new AssertionError("unexpected indirect ordinal " + callbackOrdinal[0]);
            }
        };

        FreeHook free = (Ram m, long site, long rcx, EncodedClear230BoundsPorts.DecodedBounds bounds) -> {
            check(bounds != null, "bounds present on free");
            check(bounds.beginBits() == begin2, "free bounds begin");
            check(bounds.endBits() == end2, "free bounds end");
            check(rcx == begin2, "free rcx");
            check(site == 0x424DE32L, "free site");
            m.effect64(cookieAddr, finalCookie);
        };

        List<String> expected = new ArrayList<>();

        expected.add(r(entryRcx, outer));
        expected.add(r(outer, descriptor));

        expected.add(r(cookieAddr, initialCookie));

        expected.add(r(descriptor, encBegin1));
        expected.add(r(descriptor + 8L, encEnd1));

        expected.add(r(cell1, cellVal1));
        expected.add(w(cell1, initialCookie));
        expected.add(r(iatAddr, iatTarget));
        expected.add(i("bounds", 0x424DDE5L, iatTarget, liveRax1, rot1, initialCookie, "entry-unknown", h(begin1) + ":" + h(end1)));
        expected.add(e(cookieAddr, newCookie));
        expected.add(e(descriptor, encBegin2));
        expected.add(e(descriptor + 8L, encEnd2));

        expected.add(r(cookieAddr, newCookie));
        expected.add(r(entryRcx, outer));
        expected.add(r(outer, descriptor));
        expected.add(r(descriptor, encBegin2));
        expected.add(r(descriptor + 8L, encEnd2));

        expected.add(r(cell2, cellVal2));
        expected.add(w(cell2, initialCookie));
        expected.add(r(iatAddr, iatTarget));
        expected.add(i("bounds", 0x424DDE5L, iatTarget, liveRax2, rot2, newCookie, "reloaded:" + h(descriptor) + ":" + h(begin2), h(begin2) + ":" + h(end2)));

        expected.add(r(cookieAddr, newCookie));
        expected.add(r(entryRcx, outer));
        expected.add(r(outer, descriptor));
        expected.add(r(descriptor, encBegin2));
        expected.add(r(descriptor + 8L, encEnd2));


        expected.add(f("bounds", 0x424DE32L, begin2, h(begin2) + ":" + h(end2)));
        expected.add(e(cookieAddr, finalCookie));

        expected.add(r(cookieAddr, finalCookie));

        expected.add(r(entryRcx, outer));
        expected.add(r(outer, descriptor));
        expected.add(w(descriptor, finalCookie));

        expected.add(r(entryRcx, outer));
        expected.add(r(outer, descriptor));
        expected.add(w(descriptor + 8L, finalCookie));

        expected.add(r(entryRcx, outer));
        expected.add(r(outer, descriptor));
        expected.add(w(descriptor + 16L, finalCookie));

        BoundsPorts ports = new BoundsPorts(ram, indirect, free);
        EncodedClear230Api.Input input = new EncodedClear230Api.Input(base, entryRcx);

        long result = EncodedClear424DD60.execute(ram, ports, input);

        check(result == 0L, "boundsOptIn return 0");
        check(ports.boundsIndirect == 2, "boundsOptIn two bounds indirect");
        check(ports.boundsFree == 1, "boundsOptIn one bounds free");
        check(ports.legacyIndirect == 0, "boundsOptIn zero legacy indirect");
        check(ports.legacyFree == 0, "boundsOptIn zero legacy free");

        check(ram.peek64(canaryAddr) == 0xDEADBEEFCAFEBABEL, "canary unchanged");

        check(callbackOrdinal[0] == 2, "two explicit opaque indirect effects");
        check(ram.peek64(cell1) == initialCookie && ram.peek64(cell2) == initialCookie,
                "both reverse-cell markers retain INITIAL cookie");
        check(ram.peek64(descriptor) == finalCookie && ram.peek64(descriptor + 8L) == finalCookie
                && ram.peek64(descriptor + 16L) == finalCookie,
                "opt-in final three stores use post-free fresh cookie");
        check(ram.peek64(cookieAddr) == finalCookie, "opt-in final explicit cookie effect");
        check(ram.peek8(descriptor - 1L) == 0xA5 && ram.peek8(descriptor + 24L) == 0x5A
                && ram.peek8(cell1 - 1L) == 0xC1 && ram.peek8(cell1 + 8L) == 0xD1
                && ram.peek8(cell2 - 1L) == 0xC2 && ram.peek8(cell2 + 8L) == 0xD2,
                "opt-in descriptor and both cell adjacent BYTE canaries");
        complete(ram, expected, "boundsOptIn");
    }
    public static void main(String[] args) {
        legacyCompatibility(); boundsOptIn();
        System.out.println("CLEAR_BOUNDS233_PASS groups=" + groups + " orderedEvents=" + events + " mixedChecks=" + checks + " Game=0 Native=0");
    }
}
