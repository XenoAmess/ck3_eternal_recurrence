package org.xar.ck3.research.m3.manualclear230;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.research.m3.stack229.StackContext229Api;
import org.xar.ck3.research.m3.stack229.StackContext424DB74;
import org.xar.ck3.research.m3.stack229.StackContextIndexedTailBinding229;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api;
import org.xar.ck3.research.m3.clear230.EncodedClear424DD60;
import org.xar.ck3.research.m3.clear230.EncodedClearFromStackBinding230;
import org.xar.ck3.research.m3.clear230.EncodedClearFreeBinding230;

/** Only new230 consumer edges. Owner mechanical fixture, independent new methods separate. */
public final class EncodedClearConsumerValidation230 {
    private EncodedClearConsumerValidation230() { }
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

    private static final class Mem implements Lower61Inputs.Memory {
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
    private abstract static class StackPorts implements StackContext229Api.Ports {
        @Override public void call4247ffc(NativeTaskMemory m,long s,int c) { throw unexpected("stack enter"); }
        @Override public long call424dd60(NativeTaskMemory m,long s,long c) { throw unexpected("stack middle"); }
        @Override public void call4248050(NativeTaskMemory m,long s,int c,long b) { throw unexpected("stack leave"); }
    }
    private abstract static class Tails implements StackContext229Api.Tails {
        @Override public void jump43da500(NativeTaskMemory m,long c,long a) { throw unexpected("tail500"); }
        @Override public void jump43da4f0(NativeTaskMemory m,long c,long a,long b) { throw unexpected("tail4f0"); }
    }
    private abstract static class FreeCalls implements Lower61Inputs.Calls {
        @Override public int callSlot43DA748(Lower61Inputs.FirstCall known) { throw unexpected("heap free"); }
        @Override public long call423B18C() { throw unexpected("failure cell"); }
        @Override public int callSlot43DA738() { throw unexpected("last error"); }
        @Override public int call423B0D4(long c) { throw unexpected("map error"); }
    }
    private static void actual229Caller() {
        groups++;
        long base = 0x100000000L;
        long rdxAddress = 0x100000100L;
        long r8Address = 0x100000200L;
        long r9Address = 0x100000300L;
        long holder = 0x100000400L;

        Mem mem = new Mem();
        // Seed memory
        mem.seed(rdxAddress, 4, 0xFFFFFFFFL); // -1
        mem.seed(r8Address, 8, holder);
        mem.seed(holder, 8, 0L);
        mem.seed(r9Address, 4, 0x12345678L);
        mem.seed(r9Address + 4, 4, 0xCAFEBABEL); // Canary

        // Expected pure literal formula
        long tableBase = base + 0x5C5D330L;
        long enterKnownRCX = tableBase + 40L * (-1L);
        long enterLiveRAX = tableBase;
        long cleanupBits = 0x87654321L;
        long leaveKnownRCX = tableBase + 40L * (long)(int)cleanupBits;
        long leaveLiveRAX = tableBase;

        // Typed tails
        final int[] tailCounts = {0, 0};
        Tails typedTails = new Tails() {
            @Override
            public void jump43da500(NativeTaskMemory m, long c, long a) {
                same(m, mem, "tail500 memory");
                eq(c, enterKnownRCX, "tail500 rcx");
                eq(a, enterLiveRAX, "tail500 rax");
                tailCounts[0]++;
                mem.note(p("jump500", c, a));
                mem.writeInt32(r9Address, (int)cleanupBits);
            }
            @Override
            public void jump43da4f0(NativeTaskMemory m, long c, long a, long b) {
                same(m, mem, "tail4f0 memory");
                eq(c, leaveKnownRCX, "tail4f0 rcx");
                eq(a, leaveLiveRAX, "tail4f0 rax");
                eq(b, r9Address, "tail4f0 rbx");
                tailCounts[1]++;
                mem.note(p("jump4f0", c, a, b));
            }
        };

        // Build actual objects
        StackContext229Api.Ports tailBound = StackContextIndexedTailBinding229.bind(mem, base, typedTails, new StackPorts(){});
        StackContext229Api.Ports outer = EncodedClearFromStackBinding230.bind(base, mem, new ClearPorts(){}, tailBound);

        // Execute mature StackContext424DB74
        long result = StackContext424DB74.execute(mem, outer, new StackContext229Api.Input(rdxAddress, r8Address, r9Address));

        // Verify counts
        require(tailCounts[0] == 1, "tail500 count");
        require(tailCounts[1] == 1, "tail4f0 count");

        // Verify events
        List<String> expectedEvents = new ArrayList<>();
        expectedEvents.add(op("R32", rdxAddress, 0xFFFFFFFFL));
        expectedEvents.add(p("jump500", enterKnownRCX, enterLiveRAX));
        expectedEvents.add(op("W32", r9Address, cleanupBits));
        expectedEvents.add(op("R64", r8Address, holder));
        expectedEvents.add(op("R64", holder, 0L));
        expectedEvents.add(op("R32", r9Address, cleanupBits));
        expectedEvents.add(p("jump4f0", leaveKnownRCX, leaveLiveRAX, r9Address));
        mem.expect(expectedEvents, "actual229Caller");

        // Verify result and canary
        eq(result, 0xFFFFFFFFL, "result");
        eq(mem.peek(r9Address, 4), cleanupBits, "cleanup raw32");
        eq(mem.peek(r9Address + 4, 4), 0xCAFEBABEL, "canary");
    }
    private static void actualMatureFree() {
        groups++;
        long base = 0x100000000L;
        long entryRoot = 0x200000000L;
        long holder = 0x300000000L;
        long descriptor = 0x400000000L;
        long cookieGlobal = base + 0x542F0B8L;
        long heapGlobal = base + 0x5C5DE30L;
        long initialCookie = 0x41L;
        long decodedBegin = 0x9000L;
        long decodedEnd = 0x9000L;
        long rawEncodedBound = Long.rotateLeft(decodedBegin, 1) ^ initialCookie;
        long newCookie = 0xFEDCBA9876543210L;
        long currentH = 0x700000000L;
        long oldH = 0x800000000L;
        long canary = 0x1122334455667788L;

        Mem mem = new Mem();
        mem.seed(entryRoot, 8, holder);
        mem.seed(holder, 8, descriptor);
        mem.seed(descriptor, 8, rawEncodedBound);
        mem.seed(descriptor + 8, 8, rawEncodedBound);
        mem.seed(descriptor + 0x18, 8, canary);
        mem.seed(cookieGlobal, 8, initialCookie);
        mem.seed(heapGlobal, 8, oldH);

        final int[] heapCalls = {0};
        FreeCalls realCalls = new FreeCalls() {
            @Override
            public int callSlot43DA748(Lower61Inputs.FirstCall known) {
                heapCalls[0]++;
                eq(known.rcxRaw(), currentH, "heap fresh full64 H");
                eq(known.rdxRaw(), 0L, "heap flags zero");
                eq(known.r8Raw(), decodedBegin, "heap decoded block");
                mem.note(p("heap", known.rcxRaw(), known.rdxRaw(), known.r8Raw()));
                mem.writeInt64(cookieGlobal, newCookie);
                return Integer.MIN_VALUE;
            }
        };

        EncodedClear230Api.Ports bound = EncodedClearFreeBinding230.bind(base, mem, realCalls, new ClearPorts() {});
        require(mem.events.isEmpty(), "factory IO");

        mem.seed(heapGlobal, 8, currentH);
        long result = EncodedClear424DD60.execute(mem, bound, new EncodedClear230Api.Input(base, entryRoot));

        eq(result, 0L, "return");
        eq(heapCalls[0], 1, "heap counter");
        eq(mem.peek(cookieGlobal, 8), newCookie, "new cookie");
        eq(mem.peek(heapGlobal, 8), currentH, "current H");
        eq(mem.peek(descriptor, 8), newCookie, "cell 0");
        eq(mem.peek(descriptor + 8, 8), newCookie, "cell 8");
        eq(mem.peek(descriptor + 0x10, 8), newCookie, "cell 10");
        eq(mem.peek(descriptor + 0x18, 8), canary, "canary");

        List<String> expected = new ArrayList<>();
        expected.add(op("R64", entryRoot, holder));
        expected.add(op("R64", holder, descriptor));
        expected.add(op("R64", cookieGlobal, initialCookie));
        expected.add(op("R64", descriptor, rawEncodedBound));
        expected.add(op("R64", descriptor + 8, rawEncodedBound));
        expected.add(op("R64", heapGlobal, currentH));
        expected.add(p("heap", currentH, 0L, decodedBegin));
        expected.add(op("W64", cookieGlobal, newCookie));
        expected.add(op("R64", cookieGlobal, newCookie));
        expected.add(op("R64", entryRoot, holder));
        expected.add(op("R64", holder, descriptor));
        expected.add(op("W64", descriptor, newCookie));
        expected.add(op("R64", entryRoot, holder));
        expected.add(op("R64", holder, descriptor));
        expected.add(op("W64", descriptor + 8, newCookie));
        expected.add(op("R64", entryRoot, holder));
        expected.add(op("R64", holder, descriptor));
        expected.add(op("W64", descriptor + 0x10, newCookie));

        mem.expect(expected, "mature free trace");
    }
    private static void compatibility() {
        final long base=0x30000000L;
        final Mem captured=new Mem(),foreign=new Mem();
        final int[] passive={0};
        final RuntimeException leaveSentinel=new RuntimeException("passive stack leave");
        final RuntimeException iatSentinel=new RuntimeException("passive clear IAT");
        StackContext229Api.Ports stackFallback=new StackPorts() {
            @Override public void call4247ffc(NativeTaskMemory m,long s,int c) {
                same(m,foreign,"passive stack enter original Memory");
                eq(s,0xABC001L,"passive stack enter site");
                eq(c,Integer.MIN_VALUE,"passive stack enter ECX bits");
                passive[0]++;
                captured.note(p("passive-enter",s,Integer.toUnsignedLong(c)));
            }
            @Override public void call4248050(NativeTaskMemory m,long s,int c,long b) {
                same(m,foreign,"passive stack leave original Memory");
                eq(s,0xABC002L,"passive stack leave site");
                eq(c,-1,"passive stack leave ECX bits");
                eq(b,0xFEDCBA9876543210L,"passive stack leave RBX");
                passive[0]++;
                captured.note(p("passive-leave",s,Integer.toUnsignedLong(c),b));
                throw leaveSentinel;
            }
        };
        StackContext229Api.Ports stackBound=EncodedClearFromStackBinding230.bind(base,captured,new ClearPorts() { },stackFallback);
        final EncodedClear230Api.IndirectArguments arguments=new EncodedClear230Api.IndirectArguments(
                9,0x8877665544332211L,new EncodedClear230Api.Reloaded(0xF123456789ABCDEFL,0x8123456789ABCDEFL));
        EncodedClear230Api.Ports clearFallback=new ClearPorts() {
            @Override public void call43dbba8(NativeTaskMemory m,long s,long target,long rax,EncodedClear230Api.IndirectArguments a) {
                same(m,foreign,"passive clear IAT original Memory");
                eq(s,0xABC003L,"passive clear IAT site");
                eq(target,0xE23456789ABCDEF0L,"passive clear actual target");
                eq(rax,0xD3456789ABCDEF01L,"passive clear RAX");
                same(a,arguments,"passive clear immutable argument object identity");
                passive[0]++;
                captured.note(p("passive-iat",s,target,rax));
                throw iatSentinel;
            }
        };
        EncodedClear230Api.Ports freeBound=EncodedClearFreeBinding230.bind(base,captured,new FreeCalls() { },clearFallback);
        int rejects=0;
        try {
            stackBound.call424dd60(foreign,0x424DB94L,0x1000L);
            throw new AssertionError("foreign stack active accepted");
        } catch(IllegalArgumentException expected) { rejects++; }
        try {
            stackBound.call424dd60(captured,0x424DB93L,0x1000L);
            throw new AssertionError("wrong stack active site accepted");
        } catch(IllegalArgumentException expected) { rejects++; }
        try {
            freeBound.call424e364(foreign,0x424DE32L,0x2000L);
            throw new AssertionError("foreign free active accepted");
        } catch(IllegalArgumentException expected) { rejects++; }
        try {
            freeBound.call424e364(captured,0x424DE31L,0x2000L);
            throw new AssertionError("wrong free active site accepted");
        } catch(IllegalArgumentException expected) { rejects++; }
        eq(rejects,4,"both bindings reject foreign Memory and wrong site");
        eq(passive[0],0,"invalid active ports never replay fallback");
        require(captured.events.isEmpty()&&foreign.events.isEmpty(),"invalid active calls cause no Memory/port effects");
        require(captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"invalid active calls cause no writes");
        stackBound.call4247ffc(foreign,0xABC001L,Integer.MIN_VALUE);
        boolean leaveThrown=false,iatThrown=false;
        try {
            stackBound.call4248050(foreign,0xABC002L,-1,0xFEDCBA9876543210L);
        } catch(RuntimeException actual) {
            same(actual,leaveSentinel,"passive stack exception object unchanged");
            leaveThrown=true;
        }
        try {
            freeBound.call43dbba8(foreign,0xABC003L,0xE23456789ABCDEF0L,0xD3456789ABCDEF01L,arguments);
        } catch(RuntimeException actual) {
            same(actual,iatSentinel,"passive IAT exception object unchanged");
            iatThrown=true;
        }
        require(leaveThrown&&iatThrown,"passive exceptions propagate");
        captured.expect(List.of(
                p("passive-enter",0xABC001L,0x80000000L),
                p("passive-leave",0xABC002L,0xFFFFFFFFL,0xFEDCBA9876543210L),
                p("passive-iat",0xABC003L,0xE23456789ABCDEF0L,0xD3456789ABCDEF01L)
        ),"both binder passive exact effects");
        eq(passive[0],3,"passive calls exactly once");
        require(captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"passive delegation performs no Memory I/O");
        groups++;
    }
    public static void main(String[] args) {
        actual229Caller();
        actualMatureFree();
        compatibility();
        System.out.println("EncodedClearConsumer230 groups="+groups+" observations="+observations+" mixedChecks="+checks);
    }
}
