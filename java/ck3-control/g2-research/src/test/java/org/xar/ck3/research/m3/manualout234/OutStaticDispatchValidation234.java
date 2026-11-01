package org.xar.ck3.research.m3.manualout234;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.out224.OutHelper224Api;
import org.xar.ck3.research.m3.out224.OutHelper424E620;
import org.xar.ck3.research.m3.out234.OutStaticDispatch234Api;
import org.xar.ck3.research.m3.out234.OutStaticDispatchBinding234;

/** Finite new binding witness with exact supplied-storage effects; no native execution. */
public final class OutStaticDispatchValidation234 {
    private OutStaticDispatchValidation234() { }
    private static int checks;
    private static int groups;
    private static int events;
    private static void check(boolean condition, String label) {
        checks++; if (!condition) throw new AssertionError(label);
    }
    private static String h(long bits) { return Long.toUnsignedString(bits, 16); }
    private static String memoryName(NativeTaskMemory memory) {
        if (memory instanceof Ram ram) return ram.name;
        throw new AssertionError("unlabelled supplied Memory");
    }
    private static String r(long address, long value) { return "R64:" + h(address) + ":" + h(value); }
    private static String e(long address, long value) { return "E64:" + h(address) + ":" + h(value); }
    private static String d(NativeTaskMemory memory, long site, int ecx, long rdx, long r8, long r9) {
        return "D:" + memoryName(memory) + ":" + h(site) + ":" + Integer.toUnsignedString(ecx, 16)
                + ":" + h(rdx) + ":" + h(r8) + ":" + h(r9);
    }
    private static String f(NativeTaskMemory memory, long site, long target, long liveRax, long rcx, long rdx) {
        return "F:" + memoryName(memory) + ":" + h(site) + ":" + h(target) + ":" + h(liveRax) + ":" + h(rcx) + ":" + h(rdx);
    }
    private static String t(NativeTaskMemory memory, long site, long target, long rcx, long rdx) {
        return "T:" + memoryName(memory) + ":" + h(site) + ":" + h(target) + ":" + h(rcx) + ":" + h(rdx);
    }
    private static final class Ram implements NativeTaskMemory {
        final String name;
        final List<String> trace = new ArrayList<>();
        final Map<Long, Byte> bytes = new HashMap<>();
        Ram(String name) { this.name = name; }
        private long raw(long address, int width) {
            long result = 0L;
            for (int index = 0; index < width; index++) {
                Byte value = bytes.get(address + index);
                if (value == null) throw new AssertionError("unmapped " + name + ":" + h(address + index));
                result |= (value.longValue() & 255L) << (index * 8);
            }
            return result;
        }
        private void store(long address, int width, long value) {
            for (int index = 0; index < width; index++) bytes.put(address + index, (byte) (value >>> (index * 8)));
        }
        void seed64(long address, long value) { store(address, 8, value); }
        void seed8(long address, int value) { check((value & ~255) == 0, "initial BYTE range"); store(address, 1, value); }
        void effect64(long address, long value) { trace.add(e(address, value)); store(address, 8, value); }
        long peek64(long address) { return raw(address, 8); }
        int peek8(long address) { return (int) raw(address, 1); }
        Map<Long, Byte> snapshot() { return Map.copyOf(bytes); }
        @Override public long readPointer(long address) { long value=raw(address,8); trace.add(r(address,value)); return value; }
        @Override public int readInt32(long address) { long value=raw(address,4); trace.add("R32:"+h(address)+":"+h(value)); return (int)value; }
        @Override public void writeInt32(long address,int value) { trace.add("W32:"+h(address)+":"+Integer.toUnsignedString(value,16)); store(address,4,Integer.toUnsignedLong(value)); }
        @Override public void writeInt64(long address,long value) { trace.add("W64:"+h(address)+":"+h(value)); store(address,8,value); }
    }
    @FunctionalInterface private interface DirectHook {
        long call(NativeTaskMemory memory,long site,int ecx,long rdx,long r8,long r9);
    }
    @FunctionalInterface private interface FallbackTailHook {
        long call(NativeTaskMemory memory,long site,long target,long liveRax,long rcx,long rdx);
    }
    @FunctionalInterface private interface JumpHook {
        long call(NativeTaskMemory memory,long site,long target,long rcx,long rdx);
    }
    private static final class Fallback implements OutHelper224Api.Ports {
        final Ram recorder;
        final DirectHook direct;
        final FallbackTailHook tail;
        int directCalls;
        int tailCalls;
        Fallback(Ram recorder,DirectHook direct,FallbackTailHook tail) {
            this.recorder=recorder; this.direct=direct; this.tail=tail;
        }
        @Override public long call424e448(NativeTaskMemory memory,long site,int ecx,long rdx,long r8,long r9) {
            directCalls++; recorder.trace.add(d(memory,site,ecx,rdx,r8,r9));
            return direct.call(memory,site,ecx,rdx,r8,r9);
        }
        @Override public long tail43dbba8(NativeTaskMemory memory,long site,long target,long liveRax,long rcx,long rdx) {
            tailCalls++; recorder.trace.add(f(memory,site,target,liveRax,rcx,rdx));
            return tail.call(memory,site,target,liveRax,rcx,rdx);
        }
    }
    private static final class Target implements OutStaticDispatch234Api.TailPort {
        final Ram recorder;
        final JumpHook hook;
        int calls;
        Target(Ram recorder,JumpHook hook) { this.recorder=recorder; this.hook=hook; }
        @Override public long jumpRax(NativeTaskMemory memory,long site,long target,long rcx,long rdx) {
            calls++; recorder.trace.add(t(memory,site,target,rcx,rdx));
            return hook.call(memory,site,target,rcx,rdx);
        }
    }
    private static void rejected(Runnable work,String label) {
        try { work.run(); } catch (IllegalArgumentException expected) { checks++; return; }
        throw new AssertionError("missing active rejection: "+label);
    }
    private static void sameException(Runnable work,RuntimeException expected,String label) {
        try { work.run(); } catch (RuntimeException actual) { check(actual==expected,label); return; }
        throw new AssertionError("missing exact exception: "+label);
    }
    private static void complete(Ram memory,List<String> expected,String label) {
        check(memory.trace.equals(expected),label+" full ordered trace\nexpected="+expected+"\nactual="+memory.trace);
        groups++; events+=memory.trace.size();
    }
    private static void directProtocol() {
        long base = 0xFFFFFFFFFE000000L;
        long active = base + 0x4267630L;
        long other = active ^ 0x10L;
        long site = 0x424E65CL;
        Ram memory = new Ram("C");
        Ram foreign = new Ram("F");
        long effectAddress = 0x6000L;
        long firstEffect = 0x1122334455667788L;
        long nestedEffect = 0x2233445566778899L;
        long outerEffect = 0x33445566778899AAL;
        long live0 = 0x1234567887654321L;
        long liveOuter = 0xFEDCBA9876543210L;
        long liveNested = 0x8123456789ABCDEFL;
        long liveThrow = 0xAABBCCDDEEFF0011L;
        long rcx0 = -6L;
        long rdx0 = 0xCAFEBABE12345678L;
        long rcxOuter = 0x8000000000000101L;
        long rdxOuter = 0x7FFFFFFFFFFFFF02L;
        long rcxNested = 0x1122334455667703L;
        long rdxNested = 0x8877665544332204L;
        long outerReturn = 0xFEDCBA9887654321L;
        long nestedReturn = 0x8123456701234567L;
        long passiveSite = 0x13579BDFL;
        long passiveLive = 0xF0E1D2C3B4A59687L;
        long passiveRcx = 0xA1A2A3A4A5A6A7A8L;
        long passiveRdx = 0xB1B2B3B4B5B6B7B8L;
        long passiveReturn = 0x7ABCDEF012345678L;
        int directEcx = -123;
        long directRdx = 0xC1C2C3C4C5C6C7C8L;
        long directR8 = 0xD1D2D3D4D5D6D7D8L;
        long directR9 = 0xE1E2E3E4E5E6E7E8L;
        long directReturn = 0x80000000000000FEL;
        RuntimeException activeFailure = new IllegalStateException("active234");
        RuntimeException tailFailure = new IllegalStateException("passive-tail234");
        RuntimeException directFailure = new IllegalStateException("passive-direct234");
        memory.seed8(effectAddress - 1L, 0xA5);
        memory.seed8(effectAddress + 8L, 0x5A);
        List<String> expected = List.of(
                t(memory, site, live0, rcx0, rdx0), e(effectAddress, firstEffect),
                t(memory, site, liveOuter, rcxOuter, rdxOuter),
                t(memory, site, liveNested, rcxNested, rdxNested), e(effectAddress, nestedEffect),
                e(effectAddress, outerEffect), t(memory, site, liveThrow, rcx0, rdx0),
                f(foreign, passiveSite, other, passiveLive, passiveRcx, passiveRdx),
                f(foreign, passiveSite, other, passiveLive, passiveRcx, passiveRdx),
                d(foreign, passiveSite, directEcx, directRdx, directR8, directR9),
                d(foreign, passiveSite, directEcx, directRdx, directR8, directR9));
        final int[] targetOrdinal = {0};
        final int[] fallbackTailOrdinal = {0};
        final int[] fallbackDirectOrdinal = {0};
        final OutHelper224Api.Ports[] bound = {null};
        Target target = new Target(memory, (m, callSite, targetRax, rcx, rdx) -> {
            check(m == memory && callSite == site, "direct active exact Memory/site");
            int ordinal = ++targetOrdinal[0];
            if (ordinal == 1) {
                check(targetRax == live0 && rcx == rcx0 && rdx == rdx0, "active zero-result original full args");
                memory.effect64(effectAddress, firstEffect);
                return 0L;
            }
            if (ordinal == 2) {
                check(targetRax == liveOuter && rcx == rcxOuter && rdx == rdxOuter, "outer active original full args");
                long returned = bound[0].tail43dbba8(memory, site, active, liveNested, rcxNested, rdxNested);
                check(returned == nestedReturn, "reentrant inner normal full64 result");
                memory.effect64(effectAddress, outerEffect);
                return outerReturn;
            }
            if (ordinal == 3) {
                check(targetRax == liveNested && rcx == rcxNested && rdx == rdxNested, "nested active original full args");
                memory.effect64(effectAddress, nestedEffect);
                return nestedReturn;
            }
            check(ordinal == 4 && targetRax == liveThrow && rcx == rcx0 && rdx == rdx0,
                    "throwing active original full args");
            throw activeFailure;
        });
        Fallback fallback = new Fallback(memory,
                (m, callSite, ecx, rdx, r8, r9) -> {
                    check(m == foreign && callSite == passiveSite && ecx == directEcx,
                            "passive direct Memory/site/signed int exact");
                    check(rdx == directRdx && r8 == directR8 && r9 == directR9,
                            "passive direct all full64 arguments");
                    int ordinal = ++fallbackDirectOrdinal[0];
                    if (ordinal == 1) return directReturn;
                    check(ordinal == 2, "only two passive direct calls");
                    throw directFailure;
                },
                (m, callSite, actualTarget, liveRax, rcx, rdx) -> {
                    check(m == foreign && callSite == passiveSite && actualTarget == other,
                            "different target bypasses active Memory/site guards");
                    check(liveRax == passiveLive && rcx == passiveRcx && rdx == passiveRdx,
                            "passive tail all original full64 arguments");
                    int ordinal = ++fallbackTailOrdinal[0];
                    if (ordinal == 1) return passiveReturn;
                    check(ordinal == 2, "only two passive tail calls");
                    throw tailFailure;
                });
        bound[0] = OutStaticDispatchBinding234.bind(base, memory, target, fallback);
        check(bound[0].tail43dbba8(memory, site, active, live0, rcx0, rdx0) == 0L,
                "real active normal zero is preserved");
        check(bound[0].tail43dbba8(memory, site, active, liveOuter, rcxOuter, rdxOuter) == outerReturn,
                "outer reentrant normal result independent from nested result");
        Map<Long, Byte> beforeGuard = memory.snapshot();
        Map<Long, Byte> foreignBefore = foreign.snapshot();
        int traceBeforeGuard = memory.trace.size();
        rejected(() -> bound[0].tail43dbba8(foreign, site, active, live0, rcx0, rdx0), "active foreign Memory");
        rejected(() -> bound[0].tail43dbba8(memory, site + 1L, active, live0, rcx0, rdx0), "active wrong site");
        check(target.calls == 3 && fallback.directCalls == 0 && fallback.tailCalls == 0,
                "guards before every callback");
        check(memory.trace.size() == traceBeforeGuard && memory.snapshot().equals(beforeGuard)
                && foreign.snapshot().equals(foreignBefore), "guards before all RAM and trace effects");
        sameException(() -> bound[0].tail43dbba8(memory, site, active, liveThrow, rcx0, rdx0), activeFailure,
                "active exception identity and no replay");
        check(bound[0].tail43dbba8(foreign, passiveSite, other, passiveLive, passiveRcx, passiveRdx) == passiveReturn,
                "foreign different-target full64 fallback result");
        sameException(() -> bound[0].tail43dbba8(foreign, passiveSite, other, passiveLive, passiveRcx, passiveRdx),
                tailFailure, "passive tail exception identity");
        check(bound[0].call424e448(foreign, passiveSite, directEcx, directRdx, directR8, directR9) == directReturn,
                "passive direct full64 fallback result");
        sameException(() -> bound[0].call424e448(foreign, passiveSite, directEcx, directRdx, directR8, directR9),
                directFailure, "passive direct exception identity");
        check(target.calls == 4 && fallback.tailCalls == 2 && fallback.directCalls == 2,
                "all actual callbacks counted exactly once");
        check(memory.peek64(effectAddress) == outerEffect && memory.peek8(effectAddress - 1L) == 0xA5
                && memory.peek8(effectAddress + 8L) == 0x5A, "reentrant final word and adjacent BYTE canaries");
        check(foreign.snapshot().equals(foreignBefore) && foreign.trace.isEmpty(), "passive foreign Memory unchanged");
        complete(memory, expected, "directProtocol");
    }
    private static void actualCaller() {
        Ram memory = new Ram("R");
        long base = 0x2345678900000000L;
        long entry = 0xFEDCBA9876543210L;
        long iat = base + 0x43DBBA8L;
        long active = base + 0x4267630L;
        long oldTarget = 0x1111222233334444L;
        long directA = 0xF123456789ABCDEFL;
        long directB = 0x8000000000000042L;
        long finalA = 0xCAFEBEEF87654321L;
        long effectAddress = 0x8000L;
        long effectA = 0x777788889999AAAAL;
        long effectB = 0x88889999AAAABBBBL;
        long argumentRdx = base + 0x4427010L;
        long argumentR8 = base + 0x442700CL;
        memory.seed64(iat, oldTarget);
        memory.seed8(iat - 1L, 0xA1);
        memory.seed8(iat + 8L, 0xB2);
        memory.seed8(effectAddress - 1L, 0xC3);
        memory.seed8(effectAddress + 8L, 0xD4);
        List<String> expected = List.of(
                d(memory, 0x424E643L, 0x1C, argumentRdx, argumentR8, argumentRdx),
                d(memory, 0x424E643L, 0x1C, argumentRdx, argumentR8, argumentRdx),
                e(iat, active), r(iat, active), t(memory, 0x424E65CL, directA, -6L, entry), e(effectAddress, effectA),
                d(memory, 0x424E643L, 0x1C, argumentRdx, argumentR8, argumentRdx),
                e(iat, active), r(iat, active), t(memory, 0x424E65CL, directB, -6L, entry), e(effectAddress, effectB));
        final int[] directOrdinal = {0};
        final int[] targetOrdinal = {0};
        Fallback fallback = new Fallback(memory,
                (m, site, ecx, rdx, r8, r9) -> {
                    check(m == memory && site == 0x424E643L && ecx == 0x1C, "actual78 direct Memory/site/ECX");
                    check(rdx == argumentRdx && r9 == argumentRdx && r8 == argumentR8,
                            "actual78 true RDX/R9 alias and R8 address");
                    int ordinal = ++directOrdinal[0];
                    if (ordinal == 1) return 0L;
                    check(ordinal == 2 || ordinal == 3, "only three real producer executions");
                    memory.effect64(iat, active);
                    return ordinal == 2 ? directA : directB;
                },
                (m, site, target, liveRax, rcx, rdx) -> { throw new AssertionError("qualifying actual224 call reached fallback tail"); });
        Target target = new Target(memory, (m, site, targetRax, rcx, rdx) -> {
            check(m == memory && site == 0x424E65CL && rcx == -6L && rdx == entry,
                    "actual78 known tail Memory/site/RCX/RDX");
            int ordinal = ++targetOrdinal[0];
            if (ordinal == 1) {
                check(targetRax == directA, "first actual downstream full liveRAX independent from IAT target");
                memory.effect64(effectAddress, effectA);
                return finalA;
            }
            check(ordinal == 2 && targetRax == directB, "second actual downstream full liveRAX");
            memory.effect64(effectAddress, effectB);
            return 0L;
        });
        OutHelper224Api.Ports bound = OutStaticDispatchBinding234.bind(base, memory, target, fallback);
        OutHelper224Api.Input input = new OutHelper224Api.Input(base, entry);
        check(OutHelper424E620.execute(memory, bound, input) == 0x00000000C0000225L,
                "actual78 direct-zero normal zero-extended C0000225");
        check(memory.trace.size() == 1 && target.calls == 0 && fallback.tailCalls == 0,
                "direct-zero reaches no IAT read or tail");
        check(memory.peek64(iat) == oldTarget, "direct-zero leaves preexisting IAT untouched");
        check(OutHelper424E620.execute(memory, bound, input) == finalA,
                "new actual edge preserves complete high32 and low32 normal tail return");
        check(memory.peek64(effectAddress) == effectA, "first real active callback effect");
        check(OutHelper424E620.execute(memory, bound, input) == 0L,
                "same bound graph real normal zero does not leak prior long return");
        check(fallback.directCalls == 3 && fallback.tailCalls == 0 && target.calls == 2,
                "three actual producer direct calls and two new active tails");
        check(memory.peek64(iat) == active && memory.peek64(effectAddress) == effectB,
                "fresh supplied IAT and final downstream opaque word");
        check(memory.peek8(iat - 1L) == 0xA1 && memory.peek8(iat + 8L) == 0xB2
                && memory.peek8(effectAddress - 1L) == 0xC3 && memory.peek8(effectAddress + 8L) == 0xD4,
                "exact-width IAT and downstream effects preserve BYTE canaries");
        complete(memory, expected, "actualCaller");
    }
    public static void main(String[] args) {
        directProtocol(); actualCaller();
        System.out.println("OUT_STATIC234_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");
    }
}
