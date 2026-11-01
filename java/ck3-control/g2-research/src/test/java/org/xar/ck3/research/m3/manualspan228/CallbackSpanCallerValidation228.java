package org.xar.ck3.research.m3.manualspan228;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle42420F8;
import org.xar.ck3.research.m3.span228.CallbackSpan228Api;
import org.xar.ck3.research.m3.span228.CallbackSpanBinding228;

/** New actual219 two-span consumer only; owner mechanical byte fixture. */
public final class CallbackSpanCallerValidation228 {
    private CallbackSpanCallerValidation228() { }
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

    private static String span(long site,long target,long rax,CallbackSpan228Api.Arguments args) {
        if(args instanceof CallbackSpan228Api.EntryArguments entry) {
            return p("span",site,target,rax)+":ENTRY:"+h(entry.rcx())+":"+h(entry.rdx());
        }
        if(args==CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN) return p("span",site,target,rax)+":UNKNOWN";
        throw new AssertionError("unknown arguments variant");
    }
    private static final class Mem implements CallbackSpan228Api.Memory {
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
        @Override public int readUnsigned8(long address) {
            long value=raw(address,1); note(op("R8",address,value)); return (int)value;
        }
        @Override public int readUnsigned16(long address) {
            long value=raw(address,2); note(op("R16",address,value)); return (int)value;
        }
        @Override public void writeInt64(long address,long value) {
            put(address,8,value); note(op("W64",address,value));
        }
        @Override public void writeInt32(long address,int value) {
            put(address,4,Integer.toUnsignedLong(value)); note(op("W32",address,Integer.toUnsignedLong(value)));
        }
        @Override public void write8(long address,int value) {
            put(address,1,value&255L); note(op("W8",address,value&255L));
        }
        @Override public void exchangeInt32(long address,int value) {
            long old=raw(address,4); put(address,4,Integer.toUnsignedLong(value));
            note("X32@"+h(address)+"="+h(old)+">"+h(Integer.toUnsignedLong(value)));
        }
    }
    private abstract static class MiddlePorts implements DispatchMiddle219Api.Ports {
        @Override public void call43dbba8(DispatchMiddle219Api.Memory m,long s,long t,long a,int c,int d,int b) { throw unexpected("iat"); }
        @Override public void call424de88(DispatchMiddle219Api.Memory m,long s,long c) { throw unexpected("context"); }
        @Override public void call424e1ac(DispatchMiddle219Api.Memory m,long s,long c,long d) { throw unexpected("e1ac"); }
    }

    private static void actualCaller() {
        groups++;
        long base = 0x100000000L;
        long parentP = 0x200000000L;
        long current219EntryRsp = 0x300000000L;
        long firstStart = base + 0x441ED48L;
        long firstEnd = base + 0x441ED70L;
        long secondStart = base + 0x441ED78L;
        long secondEnd = base + 0x441ED80L;
        long iatSlot = base + 0x43DBBA8L;

        // Parent globals and cookies
        long cookieA = 0xAAAAAAAAAAAAAAAAL;
        long cookieB = 0xAAAAAAAAAAAAAAAAL;

        // First span elements (5 slots: 0, A, 0, B, 0)
        long elem0 = 0L;
        long elemA = 0x1111111111111111L;
        long elem2 = 0L;
        long elemB_initial = 0L; // Will be overwritten by child 1
        long elem4 = 0L;

        // Second span element (1 slot: C)
        long elemC_initial = 0L; // Will be overwritten by child 2

        // IAT targets
        long iatTarget1 = 0x6666666666666666L;
        long iatTarget2 = 0x7777777777777777L;
        long iatTarget3 = 0x8888888888888888L;

        // Objects
        long firstObj = 0x400000000L;
        long secondObj = 0x500000000L;

        // Values written by children
        long elemB_new = 0x2222222222222222L;
        long elemC_new = 0x3333333333333333L;

        Mem mem = new Mem();

        // Seed parent state
        mem.seed(base + 0x5C5D2E8L, 1, 0L); // flag 0
        mem.seed(base + 0x5C5D2DCL, 4, 0L); // exchange target
        mem.seed(parentP, 8, firstObj);
        mem.seed(firstObj, 4, 0L); // firstObj DWORD 0
        mem.seed(base + 0x542F0B8L, 8, cookieA);
        mem.seed(base + 0x5C5D2E0L, 8, cookieB);
        mem.seed(iatSlot, 8, iatTarget1);

        // Seed first span
        mem.seed(firstStart, 8, elem0);
        mem.seed(firstStart + 8L, 8, elemA);
        mem.seed(firstStart + 16L, 8, elem2);
        mem.seed(firstStart + 24L, 8, elemB_initial);
        mem.seed(firstStart + 32L, 8, elem4);

        // Seed second span
        mem.seed(secondStart, 8, elemC_initial);

        // Seed parentP+8 for final check (will be mutated by child 3)
        mem.seed(parentP + 8L, 8, 0L); // Initial value, child 3 will write secondObj
        mem.seed(secondObj, 4, 1L); // secondObj DWORD 1

        // Canaries to ensure no out-of-bounds reads
        mem.seed(firstEnd, 8, 0xDEADBEEFDEADBEEFL);
        mem.seed(secondEnd, 8, 0xCAFECAFECACECAFEL);

        int[] childIndex = {0};

        CallbackSpan228Api.Ports childSpanPorts = new CallbackSpan228Api.Ports() {
            @Override public void call43dbba8(CallbackSpan228Api.Memory m, long site, long target, long rax, CallbackSpan228Api.Arguments args) {
                if (m != mem) throw new AssertionError("wrong memory in child");
                if (site != 0x424E1E9L) throw new AssertionError("wrong site in child");

                childIndex[0]++;

                if (childIndex[0] == 1) {
                    // First successful callback: elemA at offset 8
                    if (!(args instanceof CallbackSpan228Api.EntryArguments)) throw new AssertionError("expected EntryArguments 1");
                    CallbackSpan228Api.EntryArguments ea = (CallbackSpan228Api.EntryArguments) args;
                    if (ea.rcx() != firstStart || ea.rdx() != firstEnd) throw new AssertionError("bad entry args 1");
                    if (target != iatTarget1 || rax != elemA) throw new AssertionError("bad target/rax 1");

                    // Log event
                    mem.note(span(site, target, rax, args));

                    // Effects: Write elemB_new to future offset 24, update IAT to target2
                    mem.writeInt64(firstStart + 24L, elemB_new);
                    mem.writeInt64(iatSlot, iatTarget2);
                } else if (childIndex[0] == 2) {
                    // Second successful callback: elemB_new at offset 24
                    if (args != CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN) throw new AssertionError("expected UNKNOWN 2");
                    if (target != iatTarget2 || rax != elemB_new) throw new AssertionError("bad target/rax 2");

                    // Log event
                    mem.note(span(site, target, rax, args));

                    // Effects: Write elemC_new to second span, update IAT to target3
                    mem.writeInt64(secondStart, elemC_new);
                    mem.writeInt64(iatSlot, iatTarget3);
                } else if (childIndex[0] == 3) {
                    // Third successful callback: elemC_new in second span
                    if (!(args instanceof CallbackSpan228Api.EntryArguments)) throw new AssertionError("expected EntryArguments 3");
                    CallbackSpan228Api.EntryArguments ea = (CallbackSpan228Api.EntryArguments) args;
                    if (ea.rcx() != secondStart || ea.rdx() != secondEnd) throw new AssertionError("bad entry args 3");
                    if (target != iatTarget3 || rax != elemC_new) throw new AssertionError("bad target/rax 3");

                    // Log event
                    mem.note(span(site, target, rax, args));

                    // Effects: Write secondObj to parentP+8
                    mem.writeInt64(parentP + 8L, secondObj);
                } else {
                    throw new AssertionError("unexpected child call");
                }
            }
        };

        DispatchMiddle219Api.Ports parentFallback = new DispatchMiddle219Api.Ports() {
            @Override public void call43dbba8(DispatchMiddle219Api.Memory m, long s, long t, long a, int c, int d, int b) { throw new AssertionError("unexpected parent iat"); }
            @Override public void call424de88(DispatchMiddle219Api.Memory m, long s, long c) { throw new AssertionError("unexpected old de88"); }
            @Override public void call424de88(DispatchMiddle219Api.Memory m, long s, long c, long e) {
                if (m != mem) throw new AssertionError("wrong memory in de88");
                if (s != 0x4242162L) throw new AssertionError("wrong site in de88");
                if (c != base + 0x5C5D698L) throw new AssertionError("wrong rcx in de88");
                if (e != current219EntryRsp - 0x30L) throw new AssertionError("wrong entryRsp in de88");
                mem.note(p("de88", s, c, e));
            }
            @Override public void call424e1ac(DispatchMiddle219Api.Memory m, long s, long c, long d) { throw new AssertionError("unexpected parent e1ac"); }
        };

        DispatchMiddle219Api.Ports boundPorts = CallbackSpanBinding228.bind(base, mem, childSpanPorts, parentFallback);
        DispatchMiddle219Api.Input input = new DispatchMiddle219Api.Input(base, parentP);
        DispatchMiddle42420F8.execute(mem, boundPorts, input, current219EntryRsp);

        List<String> expected = new ArrayList<>();

        // 1. Parent entry checks
        expected.add(op("R8", base + 0x5C5D2E8L, 0L));
        expected.add("X32@" + h(base + 0x5C5D2DCL) + "=" + h(0L) + ">" + h(1L));
        expected.add(op("R64", parentP, firstObj));
        expected.add(op("R32", firstObj, 0L));

        // 2. Parent cookie check (equal, so skip IAT callback)
        expected.add(op("R64", base + 0x542F0B8L, cookieA));
        expected.add(op("R64", base + 0x5C5D2E0L, cookieB));

        // 3. Parent DE88 call
        expected.add(p("de88", 0x4242162L, base + 0x5C5D698L, current219EntryRsp - 0x30L));

        // 4. Parent second check (fresh read)
        expected.add(op("R64", parentP, firstObj));
        expected.add(op("R32", firstObj, 0L));

        // 5. First Span Execution (5 slots)
        // Slot 0: elem0 = 0 -> Skip IAT/Call
        expected.add(op("R64", firstStart, elem0));

        // Slot 1: elemA != 0 -> Read IAT, Call
        expected.add(op("R64", firstStart + 8L, elemA));
        expected.add(op("R64", iatSlot, iatTarget1));
        expected.add(span(0x424E1E9L, iatTarget1, elemA, new CallbackSpan228Api.EntryArguments(firstStart, firstEnd)));

        // Child 1 Effects
        expected.add(op("W64", firstStart + 24L, elemB_new));
        expected.add(op("W64", iatSlot, iatTarget2));

        // Slot 2: elem2 = 0 -> Skip IAT/Call
        expected.add(op("R64", firstStart + 16L, elem2));

        // Slot 3: elemB_new != 0 -> Read IAT, Call
        expected.add(op("R64", firstStart + 24L, elemB_new));
        expected.add(op("R64", iatSlot, iatTarget2));
        expected.add(span(0x424E1E9L, iatTarget2, elemB_new, CallbackSpan228Api.AfterOpaqueReturn.UNKNOWN));

        // Child 2 Effects
        expected.add(op("W64", secondStart, elemC_new));
        expected.add(op("W64", iatSlot, iatTarget3));

        // Slot 4: elem4 = 0 -> Skip IAT/Call
        expected.add(op("R64", firstStart + 32L, elem4));

        // 6. Second Span Execution (1 slot)
        // Slot 0: elemC_new != 0 -> Read IAT, Call
        expected.add(op("R64", secondStart, elemC_new));
        expected.add(op("R64", iatSlot, iatTarget3));
        expected.add(span(0x424E1E9L, iatTarget3, elemC_new, new CallbackSpan228Api.EntryArguments(secondStart, secondEnd)));

        // Child 3 Effects
        expected.add(op("W64", parentP + 8L, secondObj));

        // 7. Parent final checks
        // Fresh read parentP+8
        expected.add(op("R64", parentP + 8L, secondObj));
        // Fresh read DWORD of secondObj
        expected.add(op("R32", secondObj, 1L));
        // DWORD != 0, so return. No W8, no third pointer read.

        mem.expect(expected, "actualCaller");

        // Silent peeks for final state verification
        require(mem.peek(firstStart + 24L, 8) == elemB_new, "mutated elem3");
        require(mem.peek(secondStart, 8) == elemC_new, "mutated elem5");
        require(mem.peek(iatSlot, 8) == iatTarget3, "mutated iat");
        require(mem.peek(parentP + 8L, 8) == secondObj, "mutated parentP+8");
        require(mem.peek(firstEnd, 8) == 0xDEADBEEFDEADBEEFL, "canary firstEnd");
        require(mem.peek(secondEnd, 8) == 0xCAFECAFECACECAFEL, "canary secondEnd");
    }
    private static void exceptionPrefix() {
        final long base=0x50000000L,parentP=0xA000L,object=0xB000L,entry=0xC000L;
        final long start=base+0x441ED48L,end=base+0x441ED70L;
        final long element=0xF123456789ABCDEFL,target=0xE23456789ABCDEF0L;
        final long cookie=0xD3456789ABCDEF01L;
        final Mem mem=new Mem();
        mem.seed(base+0x5C5D2E8L,1,0);
        mem.seed(base+0x5C5D2DCL,4,0);
        mem.seed(parentP,8,object);
        mem.seed(object,4,0);
        mem.seed(base+0x542F0B8L,8,cookie);
        mem.seed(base+0x5C5D2E0L,8,cookie);
        mem.seed(start,8,element);
        mem.seed(base+0x43DBBA8L,8,target);
        final Map<Long,Byte> expectedBytes=new HashMap<>(mem.bytes);
        expectedBytes.put(base+0x5C5D2DCL,(byte)1);
        final RuntimeException sentinel=new RuntimeException("opaque span exception");
        final int[] childCalls={0};
        CallbackSpan228Api.Ports child=(m,s,t,a,args)->{
            same(m,mem,"exception child same Memory");
            eq(s,0x424E1E9L,"exception child site");
            eq(t,target,"exception child actual target");
            eq(a,element,"exception child full64 element");
            require(args instanceof CallbackSpan228Api.EntryArguments,"exception first successful call entry state");
            CallbackSpan228Api.EntryArguments known=(CallbackSpan228Api.EntryArguments)args;
            eq(known.rcx(),start,"exception entry RCX");
            eq(known.rdx(),end,"exception entry RDX");
            childCalls[0]++;
            mem.note(span(s,t,a,args));
            throw sentinel;
        };
        DispatchMiddle219Api.Ports fallback=new MiddlePorts() {
            @Override public void call424de88(DispatchMiddle219Api.Memory m,long s,long c,long e) {
                same(m,mem,"exception current DE88 same Memory");
                eq(s,0x4242162L,"exception current DE88 site");
                eq(c,base+0x5C5D698L,"exception current DE88 RCX");
                eq(e,entry-0x30L,"exception current DE88 E");
                mem.note(p("de88",s,c,e));
            }
        };
        DispatchMiddle219Api.Ports bound=CallbackSpanBinding228.bind(base,mem,child,fallback);
        boolean thrown=false;
        try {
            DispatchMiddle42420F8.execute(mem,bound,new DispatchMiddle219Api.Input(base,parentP),entry);
        } catch(RuntimeException actual) {
            same(actual,sentinel,"exception object passed through binding and actual219");
            thrown=true;
        }
        require(thrown,"actual219 caller propagates first-span exception");
        mem.expect(List.of(
                op("R8",base+0x5C5D2E8L,0),"X32@"+h(base+0x5C5D2DCL)+"=0>1",
                op("R64",parentP,object),op("R32",object,0),
                op("R64",base+0x542F0B8L,cookie),op("R64",base+0x5C5D2E0L,cookie),
                p("de88",0x4242162L,base+0x5C5D698L,entry-0x30L),
                op("R64",parentP,object),op("R32",object,0),
                op("R64",start,element),op("R64",base+0x43DBBA8L,target),
                span(0x424E1E9L,target,element,new CallbackSpan228Api.EntryArguments(start,end))
        ),"actual caller exception exact prefix; no next element or second span");
        eq(childCalls[0],1,"exception callback once");
        require(mem.bytes.equals(expectedBytes),"exception only source X32 effect; no later writes");
        require(!mem.mapped(start+8)&&!mem.mapped(parentP+8),"unreached later reads intentionally unmapped");
        groups++;
    }

    private static void compatibility() {
        final Mem captured=new Mem(),foreign=new Mem();
        final long base=0x30000000L;
        final int[] childCalls={0},passiveCalls={0};
        CallbackSpan228Api.Ports forbidden=(m,s,t,a,args)->{
            childCalls[0]++;
            throw unexpected("guarded child");
        };
        DispatchMiddle219Api.Ports fallback=new MiddlePorts() {
            @Override public void call43dbba8(DispatchMiddle219Api.Memory m,long s,long target,long rax,int c,int d,int a) {
                same(m,foreign,"passive IAT original memory");
                eq(s,0xABCD1001L,"passive IAT original site");
                eq(target,0xFEDCBA9876543210L,"passive IAT target");
                eq(rax,0x8123456789ABCDEFL,"passive IAT RAX");
                eq(c,-1,"passive IAT ECX bits");
                eq(d,Integer.MIN_VALUE,"passive IAT EDX bits");
                eq(a,0x76543210,"passive IAT R8D bits");
                passiveCalls[0]++;
                captured.note(p("passive-iat",s,target,rax,Integer.toUnsignedLong(c),Integer.toUnsignedLong(d),Integer.toUnsignedLong(a)));
            }
            @Override public void call424de88(DispatchMiddle219Api.Memory m,long s,long c) {
                same(m,foreign,"passive old DE88 memory");
                eq(s,0xABCD1002L,"passive old DE88 site");
                eq(c,0xFFEEDDCCBBAA9988L,"passive old DE88 RCX");
                passiveCalls[0]++;
                captured.note(p("passive-de88-old",s,c));
            }
            @Override public void call424de88(DispatchMiddle219Api.Memory m,long s,long c,long e) {
                same(m,foreign,"passive new DE88 memory");
                eq(s,0xABCD1003L,"passive new DE88 site");
                eq(c,0xF0E1D2C3B4A59687L,"passive new DE88 RCX");
                eq(e,0x8877665544332211L,"passive new DE88 entryE");
                passiveCalls[0]++;
                captured.note(p("passive-de88-new",s,c,e));
            }
        };
        DispatchMiddle219Api.Ports bound=CallbackSpanBinding228.bind(base,captured,forbidden,fallback);
        int rejects=0;
        try {
            bound.call424e1ac(foreign,0x424217EL,base+0x441ED48L,base+0x441ED70L);
            throw new AssertionError("foreign active callback accepted");
        } catch(IllegalArgumentException expected) { rejects++; }
        try {
            bound.call424e1ac(captured,0x4242190L,base+0x441ED78L,base+0x441ED80L);
            throw new AssertionError("wrong active site accepted");
        } catch(IllegalArgumentException expected) { rejects++; }
        eq(rejects,2,"active guards reject both invalid inputs");
        eq(childCalls[0],0,"guards call no child");
        eq(passiveCalls[0],0,"guards call no fallback");
        require(captured.events.isEmpty()&&foreign.events.isEmpty(),"guard zero Memory and port observations");
        require(captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"guard zero writes");
        bound.call43dbba8(foreign,0xABCD1001L,0xFEDCBA9876543210L,0x8123456789ABCDEFL,-1,Integer.MIN_VALUE,0x76543210);
        bound.call424de88(foreign,0xABCD1002L,0xFFEEDDCCBBAA9988L);
        bound.call424de88(foreign,0xABCD1003L,0xF0E1D2C3B4A59687L,0x8877665544332211L);
        captured.expect(List.of(
                p("passive-iat",0xABCD1001L,0xFEDCBA9876543210L,0x8123456789ABCDEFL,0xFFFFFFFFL,0x80000000L,0x76543210L),
                p("passive-de88-old",0xABCD1002L,0xFFEEDDCCBBAA9988L),
                p("passive-de88-new",0xABCD1003L,0xF0E1D2C3B4A59687L,0x8877665544332211L)
        ),"passive callbacks exact full argument trace");
        eq(passiveCalls[0],3,"each passive callback once");
        eq(childCalls[0],0,"passive methods call no span child");
        require(captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"passive callback delegation performs no Memory I/O");
        groups++;
    }
    public static void main(String[] args) {
        actualCaller();
        exceptionPrefix();
        compatibility();
        System.out.println("CallbackSpanCaller228 groups="+groups+" observations="+observations+" mixedChecks="+checks);
    }
}
