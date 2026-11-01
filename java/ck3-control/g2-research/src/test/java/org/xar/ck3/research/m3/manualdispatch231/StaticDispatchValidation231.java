package org.xar.ck3.research.m3.manualdispatch231;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api;
import org.xar.ck3.research.m3.clear230.EncodedClear424DD60;
import org.xar.ck3.research.m3.clear230.StaticDispatch231Api;
import org.xar.ck3.research.m3.clear230.EncodedClearStaticDispatchBinding231;

/** New231 target-qualified binding edges only; owner mechanical memory fixture. */
public final class StaticDispatchValidation231 {
    private StaticDispatchValidation231() { }
    private static int checks;
    private static int groups;
    private static int observations;
    private static String h(long value) { return Long.toUnsignedString(value,16); }
    private static String op(String kind,long address,long value) {
        return kind+"@"+h(address)+"="+h(value);
    }
    private static String p(String role,long... args) {
        StringBuilder s=new StringBuilder("P:"+role);
        for (long a:args) s.append(':').append(h(a));
        return s.toString();
    }
    private static void require(boolean value,String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    private static void eq(long actual,long expected,String message) {
        require(actual==expected,message+": "+h(actual)+" != "+h(expected));
    }
    private static void same(Object actual,Object expected,String message) {
        require(actual==expected,message);
    }
    private static AssertionError unexpected(String role) { return new AssertionError("unexpected "+role); }

    private static final class Mem implements NativeTaskMemory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final List<String> events=new ArrayList<>();
        private long raw(long address,int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Byte b=bytes.get(address+i);
                if(b==null) throw new AssertionError("unmapped "+h(address+i));
                value|=(long)(b&255)<<(8*i);
            }
            return value;
        }
        private void put(long address,int width,long value) {
            for(int i=0;i<width;i++) bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        void seed(long address,int width,long value) { put(address,width,value); }
        long peek(long address,int width) { return raw(address,width); }
        boolean mapped(long address) { return bytes.containsKey(address); }
        void note(String event) { events.add(event); }
        void expect(List<String> expected,String label) {
            require(events.equals(expected),label+" events\nactual="+events+"\nexpected="+expected);
            observations+=events.size();
            events.clear();
        }
        @Override public long readPointer(long address) {
            long value=raw(address,8); note(op("R64",address,value)); return value;
        }
        @Override public int readInt32(long address) {
            long value=raw(address,4); note(op("R32",address,value)); return (int)value;
        }
        @Override public void writeInt64(long address,long value) {
            put(address,8,value); note(op("W64",address,value));
        }
        @Override public void writeInt32(long address,int value) {
            put(address,4,Integer.toUnsignedLong(value)); note(op("W32",address,Integer.toUnsignedLong(value)));
        }
    }
    private abstract static class ClearPorts implements EncodedClear230Api.Ports {
        @Override public void call43dbba8(NativeTaskMemory m,long s,long t,long a,EncodedClear230Api.IndirectArguments args) { throw unexpected("clear IAT"); }
        @Override public void call424e364(NativeTaskMemory m,long s,long c) { throw unexpected("clear free"); }
    }
    private static void directGate() {
        // 1. Setup Memory and Ports
        Mem capturedMem = new Mem();
        Mem foreignMem = new Mem();

        // 2. Setup Arguments
        // args1: ecx=-1 (0xFFFFFFFF), r8=0x123456789ABCDEF0L, EntryUnknown.UNKNOWN
        EncodedClear230Api.IndirectArguments args1 = new EncodedClear230Api.IndirectArguments(-1, 0x123456789ABCDEF0L, EncodedClear230Api.EntryUnknown.UNKNOWN);
        // args2: ecx=Integer.MIN_VALUE (0x80000000), r8=0xFEDCBA9876543210L, Reloaded(0x1111111111111111L, 0x2222222222222222L)
        EncodedClear230Api.IndirectArguments args2 = new EncodedClear230Api.IndirectArguments(Integer.MIN_VALUE, 0xFEDCBA9876543210L, new EncodedClear230Api.Reloaded(0x1111111111111111L, 0x2222222222222222L));

        // 3. Setup Sentinel Exceptions
        RuntimeException sentinelActive = new RuntimeException("active-sentinel");
        RuntimeException sentinelPassiveIAT = new RuntimeException("passive-iat-sentinel");
        RuntimeException sentinelPassiveFree = new RuntimeException("passive-free-sentinel");

        // 4. Setup Fallback Ports (frozenClearPorts style)
        EncodedClear230Api.Ports fallback = new EncodedClear230Api.Ports() {
            @Override
            public void call43dbba8(NativeTaskMemory m, long s, long t, long a, EncodedClear230Api.IndirectArguments args) {
                // Passive IAT: Check original args
                same(m, foreignMem, "passive-iat-memory");
                eq(s, 0x424DDE6L, "passive-iat-site");
                eq(t, 0x9999999999999999L, "passive-iat-target");
                eq(a, 0xAAAAAAAAAAAAAAAAL, "passive-iat-rax");
                same(args, args2, "passive-iat-args");
                capturedMem.note(p("P:passive-iat", s, t, a));
                throw sentinelPassiveIAT;
            }
            @Override
            public void call424e364(NativeTaskMemory m, long s, long c) {
                // Passive Free: Check original args
                same(m, foreignMem, "passive-free-memory");
                eq(s, 0xABCD003L, "passive-free-site");
                eq(c, 0xBBBBBBBBBBBBBBBBL, "passive-free-rcx");
                capturedMem.note(p("P:passive-free", s, c));
                throw sentinelPassiveFree;
            }
        };

        // 5. Setup TailPort for Active Calls
        // We need to track counts and verify identities for the 3 active calls
        int[] activeCounts = new int[3];

        StaticDispatch231Api.TailPort target = new StaticDispatch231Api.TailPort() {
            @Override
            public int jumpRax(NativeTaskMemory m, long s, long t, long c, EncodedClear230Api.IndirectArguments args) {
                // Verify same capturedMem and site
                same(m, capturedMem, "active-memory");
                eq(s, 0x424DDE5L, "active-site");

                // Determine which call this is based on args identity
                if (args == args1) {
                    // Call 1 or Call 3
                    if (activeCounts[0] == 0) {
                        // Call 1: decodedRAX 0
                        eq(t, 0L, "active-1-rax");
                        eq(c, Integer.toUnsignedLong(-1), "active-1-rcx");
                        capturedMem.note(p("P:active-1", s, t, c));
                        activeCounts[0]++;
                        return 0;
                    } else if (activeCounts[2] == 0) {
                        // Call 3: different raw decodedRAX
                        eq(t, 0xCCCCCCCCCCCCCCCL, "active-3-rax");
                        eq(c, Integer.toUnsignedLong(-1), "active-3-rcx");
                        capturedMem.note(p("P:active-3", s, t, c));
                        activeCounts[2]++;
                        throw sentinelActive;
                    }
                } else if (args == args2) {
                    // Call 2
                    if (activeCounts[1] == 0) {
                        // Call 2: decodedRAX highbit
                        eq(t, 0x8000000000000000L, "active-2-rax");
                        eq(c, Integer.toUnsignedLong(Integer.MIN_VALUE), "active-2-rcx");
                        capturedMem.note(p("P:active-2", s, t, c));
                        activeCounts[1]++;
                        return Integer.MIN_VALUE;
                    }
                }
                throw new AssertionError("unexpected active call");
            }
        };

        // 6. Bind Factory
        EncodedClear230Api.Ports bound = EncodedClearStaticDispatchBinding231.bind(0x100000000L, capturedMem, target, fallback);

        // 7. Execute Tests

        // Test 1: Invalid Input (Foreign Memory, Valid Site) -> IAE before effect
        try {
            bound.call43dbba8(foreignMem, 0x424DDE5L, 0x100000000L + 0x4267630L, 0L, args1);
            throw new AssertionError("expected IAE");
        } catch (IllegalArgumentException e) {
            // Expected
        }
        require(capturedMem.events.isEmpty(), "capturedMem empty after invalid 1");
        require(foreignMem.events.isEmpty(), "foreignMem empty after invalid 1");

        // Test 2: Invalid Input (Captured Memory, Wrong Site) -> IAE before effect
        try {
            bound.call43dbba8(capturedMem, 0x424DDE6L, 0x100000000L + 0x4267630L, 0L, args1);
            throw new AssertionError("expected IAE");
        } catch (IllegalArgumentException e) {
            // Expected
        }
        require(capturedMem.events.isEmpty(), "capturedMem empty after invalid 2");
        require(foreignMem.events.isEmpty(), "foreignMem empty after invalid 2");

        // Test 3: Passive IAT (Different Target, Foreign Memory, Wrong Site) -> Fallback
        try {
            bound.call43dbba8(foreignMem, 0x424DDE6L, 0x9999999999999999L, 0xAAAAAAAAAAAAAAAAL, args2);
            throw new AssertionError("expected sentinelPassiveIAT");
        } catch (RuntimeException e) {
            same(e, sentinelPassiveIAT, "passive-iat-sentinel");
        }

        // Test 4: Passive Free (Existing E364 with foreignMem/arbitrary site) -> Fallback
        try {
            bound.call424e364(foreignMem, 0xABCD003L, 0xBBBBBBBBBBBBBBBBL);
            throw new AssertionError("expected sentinelPassiveFree");
        } catch (RuntimeException e) {
            same(e, sentinelPassiveFree, "passive-free-sentinel");
        }

        // Test 5: Active Call 1 (Equal Target, Captured Memory, Valid Site, args1, RAX=0)
        // Returns int 0, ignored at void boundary.
        bound.call43dbba8(capturedMem, 0x424DDE5L, 0x100000000L + 0x4267630L, 0L, args1);

        // Test 6: Active Call 2 (Equal Target, Captured Memory, Valid Site, args2, RAX=HighBit)
        // Returns Integer.MIN_VALUE, ignored at void boundary.
        bound.call43dbba8(capturedMem, 0x424DDE5L, 0x100000000L + 0x4267630L, 0x8000000000000000L, args2);

        // Test 7: Active Call 3 (Equal Target, Captured Memory, Valid Site, args1, RAX=Different)
        // Throws sentinelActive.
        try {
            bound.call43dbba8(capturedMem, 0x424DDE5L, 0x100000000L + 0x4267630L, 0xCCCCCCCCCCCCCCCL, args1);
            throw new AssertionError("expected sentinelActive");
        } catch (RuntimeException e) {
            same(e, sentinelActive, "active-sentinel");
        }

        // Verify Counts
        eq(activeCounts[0], 1, "active-1-count");
        eq(activeCounts[1], 1, "active-2-count");
        eq(activeCounts[2], 1, "active-3-count");
        capturedMem.expect(List.of(
                p("P:passive-iat",0x424DDE6L,0x9999999999999999L,0xAAAAAAAAAAAAAAAAL),
                p("P:passive-free",0xABCD003L,0xBBBBBBBBBBBBBBBBL),
                p("P:active-1",0x424DDE5L,0L,0xFFFFFFFFL),
                p("P:active-2",0x424DDE5L,0x8000000000000000L,0x80000000L),
                p("P:active-3",0x424DDE5L,0xCCCCCCCCCCCCCCCL,0xFFFFFFFFL)
        ),"direct complete five opaque events");
        foreignMem.expect(List.of(),"direct foreign Memory zero IO");
        require(capturedMem.bytes.isEmpty()&&foreignMem.bytes.isEmpty(),"direct no storage writes");
        groups++;
    }
    private static void actual230Chain() {
        groups++;
        long base = 0x100000000L;
        long entryRoot = 0x200000000L;
        long outer = 0x300000000L;
        long descriptor = 0x400000000L;
        long begin = 0x9000L;
        long end = 0x9010L;
        long cookie = 0x41L;
        int ecx = 1;
        long firstDecoded = 0x8877665544332211L;
        long secondDecoded = 0x1122334455667788L;
        long rawBegin = Long.rotateLeft(begin, ecx) ^ cookie;
        long rawEnd = Long.rotateLeft(end, ecx) ^ cookie;
        long rawFirst = Long.rotateLeft(firstDecoded, ecx) ^ cookie;
        long rawSecond = Long.rotateLeft(secondDecoded, ecx) ^ cookie;
        long iatSlot = base + 0x43DBBA8L;
        long cookieAddr = base + 0x542F0B8L;
        long staticTarget = base + 0x4267630L;
        long otherTarget = base + 0x4267631L;
        long canaryEnd = 0x1234567890ABCDEFL;
        long canaryDesc = 0x2234567890ABCDEFL;

        Mem mem = new Mem();
        mem.seed(entryRoot, 8, outer);
        mem.seed(outer, 8, descriptor);
        mem.seed(descriptor, 8, rawBegin);
        mem.seed(descriptor + 8, 8, rawEnd);
        mem.seed(cookieAddr, 8, cookie);
        mem.seed(iatSlot, 8, staticTarget);
        mem.seed(begin, 8, rawSecond);
        mem.seed(begin + 8, 8, rawFirst);
        mem.seed(end, 8, canaryEnd);
        mem.seed(descriptor + 0x18, 8, canaryDesc);

        int[] tailCount = new int[]{0};
        int[] fallbackCount = new int[]{0};
        int[] freeCount = new int[]{0};

        StaticDispatch231Api.TailPort tailPort = new StaticDispatch231Api.TailPort() {
            @Override
            public int jumpRax(NativeTaskMemory memory, long siteRva, long targetRax, long knownRcx, EncodedClear230Api.IndirectArguments arguments) {
                tailCount[0]++;
                same(memory, mem, "tail memory");
                eq(siteRva, 0x424DDE5L, "tail site");
                eq(targetRax, firstDecoded, "tail targetRax");
                eq(knownRcx, 1L, "tail knownRcx");
                eq(arguments.ecx(), 1, "tail args.ecx");
                eq(arguments.r8(), cookie, "tail args.r8");
                require(arguments.rdxR9() == EncodedClear230Api.EntryUnknown.UNKNOWN, "tail args.rdxR9");
                mem.note(p("tail", siteRva, targetRax, knownRcx, arguments.ecx(), arguments.r8()));
                memory.writeInt64(iatSlot, otherTarget);
                return 0x80000001;
            }
        };

        EncodedClear230Api.Ports fallback = new EncodedClear230Api.Ports() {
            @Override
            public void call43dbba8(NativeTaskMemory memory, long siteRva, long actualTarget, long liveRax, EncodedClear230Api.IndirectArguments arguments) {
                fallbackCount[0]++;
                same(memory, mem, "fallback memory");
                eq(siteRva, 0x424DDE5L, "fallback site");
                eq(actualTarget, otherTarget, "fallback actualTarget");
                eq(liveRax, secondDecoded, "fallback liveRax");
                eq(arguments.ecx(), 1, "fallback args.ecx");
                eq(arguments.r8(), cookie, "fallback args.r8");
                require(arguments.rdxR9() instanceof EncodedClear230Api.Reloaded, "fallback args.rdxR9 type");
                EncodedClear230Api.Reloaded reloaded = (EncodedClear230Api.Reloaded) arguments.rdxR9();
                eq(reloaded.rdx(), descriptor, "fallback reloaded.rdx");
                eq(reloaded.r9(), begin, "fallback reloaded.r9");
                mem.note(p("fallback", siteRva, actualTarget, liveRax, arguments.ecx(), arguments.r8()));
            }
            @Override
            public void call424e364(NativeTaskMemory memory, long siteRva, long rcx) {
                freeCount[0]++;
                same(memory, mem, "free memory");
                eq(siteRva, 0x424DE32L, "free site");
                eq(rcx, begin, "free rcx");
                mem.note(p("free", siteRva, rcx));
            }
        };

        EncodedClear230Api.Ports ports = EncodedClearStaticDispatchBinding231.bind(base, mem, tailPort, fallback);
        EncodedClear230Api.Input input = new EncodedClear230Api.Input(base, entryRoot);
        long result = EncodedClear424DD60.execute(mem, ports, input);

        eq(result, 0L, "execute result");
        eq(tailCount[0], 1, "tail count");
        eq(fallbackCount[0], 1, "fallback count");
        eq(freeCount[0], 1, "free count");

        List<String> expected = new ArrayList<>();
        expected.add(op("R64", entryRoot, outer));
        expected.add(op("R64", outer, descriptor));
        expected.add(op("R64", cookieAddr, cookie));
        expected.add(op("R64", descriptor, rawBegin));
        expected.add(op("R64", descriptor + 8, rawEnd));
        expected.add(op("R64", begin + 8, rawFirst));
        expected.add(op("W64", begin + 8, cookie));
        expected.add(op("R64", iatSlot, staticTarget));
        expected.add(p("tail", 0x424DDE5L, firstDecoded, 1L, 1L, cookie));
        expected.add(op("W64", iatSlot, otherTarget));
        expected.add(op("R64", cookieAddr, cookie));
        expected.add(op("R64", entryRoot, outer));
        expected.add(op("R64", outer, descriptor));
        expected.add(op("R64", descriptor, rawBegin));
        expected.add(op("R64", descriptor + 8, rawEnd));
        expected.add(op("R64", begin, rawSecond));
        expected.add(op("W64", begin, cookie));
        expected.add(op("R64", iatSlot, otherTarget));
        expected.add(p("fallback", 0x424DDE5L, otherTarget, secondDecoded, 1L, cookie));
        expected.add(op("R64", cookieAddr, cookie));
        expected.add(op("R64", entryRoot, outer));
        expected.add(op("R64", outer, descriptor));
        expected.add(op("R64", descriptor, rawBegin));
        expected.add(op("R64", descriptor + 8, rawEnd));
        expected.add(p("free", 0x424DE32L, begin));
        expected.add(op("R64", cookieAddr, cookie));
        expected.add(op("R64", entryRoot, outer));
        expected.add(op("R64", outer, descriptor));
        expected.add(op("W64", descriptor, cookie));
        expected.add(op("R64", entryRoot, outer));
        expected.add(op("R64", outer, descriptor));
        expected.add(op("W64", descriptor + 8, cookie));
        expected.add(op("R64", entryRoot, outer));
        expected.add(op("R64", outer, descriptor));
        expected.add(op("W64", descriptor + 0x10, cookie));

        mem.expect(expected, "actual230Chain");

        eq(mem.peek(descriptor, 8), cookie, "header0");
        eq(mem.peek(descriptor + 8, 8), cookie, "header8");
        eq(mem.peek(descriptor + 0x10, 8), cookie, "header10");
        eq(mem.peek(begin, 8), cookie, "cellBegin");
        eq(mem.peek(begin + 8, 8), cookie, "cellBegin8");
        eq(mem.peek(end, 8), canaryEnd, "canaryEnd");
        eq(mem.peek(descriptor + 0x18, 8), canaryDesc, "canaryDesc");
        eq(mem.peek(iatSlot, 8), otherTarget, "iatOther");
    }
    public static void main(String[] args) {
        directGate();
        actual230Chain();
        System.out.println("StaticDispatch231 groups="+groups+" observations="+observations+" mixedChecks="+checks);
    }
}
