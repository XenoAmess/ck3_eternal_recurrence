package org.xar.ck3.research.m3.manualstack227;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper218Api;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper42420C0;
import org.xar.ck3.research.m3.dispatch218.DispatchHelperBinding218;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle42420F8;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddleBinding219;
import org.xar.ck3.research.m3.stack227.StackContext227Api;
import org.xar.ck3.research.m3.stack227.StackContextFromMiddleBinding227;

/** New context-chain witness only; owner mechanical fixture, source-derived scenarios separate. */
public final class ContextChainValidation227 {
    private ContextChainValidation227() { }
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

    private static final class Mem implements DispatchMiddle219Api.Memory {
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
    private abstract static class TailPorts implements TerminalTailTarget217Api.Ports {
        @Override public long call43da620(TerminalTailTarget217Api.Memory m,long s,long t,int c) { throw unexpected("lookup"); }
        @Override public void call42422d0(TerminalTailTarget217Api.Memory m,long s,int c) { throw unexpected("first"); }
        @Override public long call42420c0(TerminalTailTarget217Api.Memory m,long s,long c,long d,long a,long b) { throw unexpected("helper"); }
        @Override public void call4242284(TerminalTailTarget217Api.Memory m,long s,int c) { throw unexpected("abort"); }
    }
    private abstract static class HelperPorts implements DispatchHelper218Api.Ports {
        @Override public void enter(NativeTaskMemory m,long s,int c) { throw unexpected("enter"); }
        @Override public void call42420f8(NativeTaskMemory m,long s,long c) { throw unexpected("middle"); }
        @Override public long leave(NativeTaskMemory m,long s,int c,long rbx) { throw unexpected("leave"); }
    }
    private abstract static class MiddlePorts implements DispatchMiddle219Api.Ports {
        @Override public void call43dbba8(DispatchMiddle219Api.Memory m,long s,long t,long a,int c,int d,int b) { throw unexpected("iat"); }
        @Override public void call424de88(DispatchMiddle219Api.Memory m,long s,long c) { throw unexpected("context"); }
        @Override public void call424e1ac(DispatchMiddle219Api.Memory m,long s,long c,long d) { throw unexpected("e1ac"); }
    }

    private static void currentChain() {
        final long base=0x10000000L;
        final long[] tops={0x5000L,0x7000L};
        final long[] opaqueLeafReturns={0x8877665544332211L,0xFEDCBA9876543210L};
        final long[] leaveReturns={0x8123456789ABCDEFL,0xF123456789ABCDEFL};
        final Mem mem=new Mem();
        mem.seed(base+0x5C5D2E8L,1,0);
        mem.seed(base+0x5C5D2DCL,4,0);
        final int[] childCalls={0},enters={0},leaves={0},cleanups={0};
        StackContext227Api.Ports child=(m,s,c,d,a,b)->{
            same(m,mem,"current DB74 identity");
            require(childCalls[0]<tops.length,"current DB74 bounded count");
            int index=childCalls[0]++;
            long e=tops[index]-0xC0L;
            eq(s,0x424DEB8L,"current DB74 site");
            eq(c,e+0x10L,"current DB74 RCX");
            eq(d,e+0x20L,"current DB74 RDX");
            eq(a,e-0x18L,"current DB74 R8");
            eq(b,e+0x18L,"current DB74 R9");
            mem.note(p("db74",s,c,d,a,b));
            return opaqueLeafReturns[index];
        };
        DispatchMiddle219Api.Ports passiveMiddle=new MiddlePorts() {
            @Override public void call424e1ac(DispatchMiddle219Api.Memory m,long s,long c,long d) {
                same(m,mem,"current E1AC identity");
                eq(s,0x4242191L,"current mandatory E1AC site");
                eq(c,base+0x441ED78L,"current E1AC RCX");
                eq(d,base+0x441ED80L,"current E1AC RDX");
                cleanups[0]++;
                mem.note(p("e1ac",s,c,d));
            }
        };
        DispatchHelper218Api.Ports passiveHelper=new HelperPorts() {
            @Override public void enter(NativeTaskMemory m,long s,int c) {
                same(m,mem,"current enter identity");
                eq(s,0x42420D7L,"current enter site");
                eq(c,2,"current enter ECX");
                enters[0]++;
                mem.note(p("enter",s,Integer.toUnsignedLong(c)));
            }
            @Override public long leave(NativeTaskMemory m,long s,int c,long rbx) {
                same(m,mem,"current leave identity");
                require(leaves[0]<tops.length,"current leave bounded count");
                int index=leaves[0]++;
                eq(s,0x42420E8L,"current leave site");
                eq(c,2,"current leave ECX");
                eq(rbx,tops[index]-0x34L,"current leave saved original R9");
                mem.note(p("leave",s,Integer.toUnsignedLong(c),rbx));
                return leaveReturns[index];
            }
        };
        // Factories occur once, outside the two current top invocations.
        DispatchMiddle219Api.Ports leafBound=StackContextFromMiddleBinding227.bind(mem,child,passiveMiddle);
        DispatchHelper218Api.Ports middleBound=DispatchMiddleBinding219.bind(mem,base,leafBound,passiveHelper);
        TerminalTailTarget217Api.Ports outerBound=DispatchHelperBinding218.bind(mem,middleBound,new TailPorts() { });
        for(int index=0;index<tops.length;index++) {
            long t=tops[index];
            long e=t-0xC0L;
            mem.seed(e+0x10L,8,0xC1C2C3C4C5C6C7C8L);
            mem.seed(e+0x1CL,4,0xA1B2C3D4L);
            mem.seed(e+0x24L,4,0xE5F60718L);
            TerminalTailTarget217Api.Outcome actual=TerminalTailTarget217.execute(mem,outerBound,
                    new TerminalTailTarget217Api.Input(base,0x13579BDF,1,1,new TerminalTailTarget217Api.Scratch(t)));
            require(actual instanceof TerminalTailTarget217Api.NormalReturn,"current217 ordinary software outcome");
            eq(((TerminalTailTarget217Api.NormalReturn)actual).rawRax(),leaveReturns[index],"current full64 leave return");
            require(leaveReturns[index]!=opaqueLeafReturns[index],"leaf return is distinct from outer leave result");
            mem.expect(List.of(
                    op("W32",t+0x18L,1),op("W32",t+0x10L,1),
                    op("W8",t+0x20L,0),
                    op("W64",t-0x28L,t+0x10L),op("W64",t-0x20L,t+0x18L),op("W64",t-0x18L,t+0x20L),
                    op("W32",t-0x34L,2),op("W32",t-0x30L,2),
                    op("R32",t-0x30L,2),p("enter",0x42420D7L,2),
                    op("R8",base+0x5C5D2E8L,0),"X32@"+h(base+0x5C5D2DCL)+"="+h(index)+">1",
                    op("R64",t-0x28L,t+0x10L),op("R32",t+0x10L,1),
                    op("W64",e+8,base+0x5C5D6B0L),op("W64",e-0x18L,e+8),
                    op("W32",e+0x18L,2),op("W32",e+0x20L,2),
                    p("db74",0x424DEB8L,e+0x10L,e+0x20L,e-0x18L,e+0x18L),
                    op("R64",t-0x28L,t+0x10L),op("R32",t+0x10L,1),
                    p("e1ac",0x4242191L,base+0x441ED78L,base+0x441ED80L),
                    op("R64",t-0x20L,t+0x18L),op("R32",t+0x18L,1),
                    op("R32",t-0x34L,2),p("leave",0x42420E8L,2,t-0x34L),
                    op("R32",t+0x18L,1)
            ),"current T="+h(t)+" complete source trace");
            eq(childCalls[0],index+1L,"one child per current T");
            eq(enters[0],index+1L,"one enter per current T");
            eq(leaves[0],index+1L,"one leave per current T");
            eq(cleanups[0],index+1L,"one mandatory E1AC per current T");
            eq(mem.peek(e+8,8),base+0x5C5D6B0L,"leaf entry RCX home");
            eq(mem.peek(e-0x18L,8),e+8,"leaf address cell");
            eq(mem.peek(e+0x18L,4),2,"leaf R9 DWORD");
            eq(mem.peek(e+0x20L,4),2,"leaf RDX DWORD");
            eq(mem.peek(e+0x10L,8),0xC1C2C3C4C5C6C7C8L,"unknown eight bytes preserved");
            eq(mem.peek(e+0x1CL,4),0xA1B2C3D4L,"first DWORD high canary");
            eq(mem.peek(e+0x24L,4),0xE5F60718L,"second DWORD high canary");
            require(!mem.mapped(e-0x19L)&&!mem.mapped(e-0x10L),"leaf pointer write exact width");
            eq(mem.peek(t+0x20L,1),0,"top final flag remains source zero");
            groups++;
        }
        eq(childCalls[0],2,"same graph observes two distinct current leaf entries");
    }
    private static void legacy() {
        final long base=0x20000000L;
        final Mem mem=new Mem();
        final long pointer=0x9000L,first=0xA000L,second=0xA100L;
        final long enterAddress=0xB000L,leaveAddress=0xB100L;
        final long returned=0xFEDCBA9876543210L;
        mem.seed(base+0x5C5D2E8L,1,0);
        mem.seed(base+0x5C5D2DCL,4,0);
        mem.seed(pointer,8,first);
        mem.seed(pointer+8,8,second);
        mem.seed(first,4,1);
        mem.seed(second,4,1);
        mem.seed(enterAddress,4,2);
        mem.seed(leaveAddress,4,3);
        final Map<Long,Byte> expectedBytes=new HashMap<>(mem.bytes);
        expectedBytes.put(base+0x5C5D2DCL,(byte)1);
        final int[] legacyCalls={0};
        StackContext227Api.Ports forbidden=(m,s,c,d,a,b)->{
            throw unexpected("leaf activated without E");
        };
        DispatchMiddle219Api.Ports passiveMiddle=new MiddlePorts() {
            @Override public void call424de88(DispatchMiddle219Api.Memory m,long s,long c) {
                same(m,mem,"legacy context identity");
                eq(s,0x4242162L,"legacy context site");
                eq(c,base+0x5C5D6B0L,"legacy context receiver");
                legacyCalls[0]++;
                mem.note(p("legacy-context",s,c));
            }
            @Override public void call424e1ac(DispatchMiddle219Api.Memory m,long s,long c,long d) {
                same(m,mem,"legacy E1AC identity");
                eq(s,0x4242191L,"legacy E1AC site");
                eq(c,base+0x441ED78L,"legacy E1AC RCX");
                eq(d,base+0x441ED80L,"legacy E1AC RDX");
                mem.note(p("e1ac",s,c,d));
            }
        };
        DispatchHelper218Api.Ports passiveHelper=new HelperPorts() {
            @Override public void enter(NativeTaskMemory m,long s,int c) {
                same(m,mem,"legacy enter identity");
                eq(s,0x42420D7L,"legacy enter site");
                eq(c,2,"legacy enter ECX");
                mem.note(p("enter",s,Integer.toUnsignedLong(c)));
            }
            @Override public long leave(NativeTaskMemory m,long s,int c,long rbx) {
                same(m,mem,"legacy leave identity");
                eq(s,0x42420E8L,"legacy leave site");
                eq(c,3,"legacy leave ECX");
                eq(rbx,leaveAddress,"legacy leave RBX");
                mem.note(p("leave",s,Integer.toUnsignedLong(c),rbx));
                return returned;
            }
        };
        DispatchMiddle219Api.Ports leafBound=StackContextFromMiddleBinding227.bind(mem,forbidden,passiveMiddle);
        DispatchHelper218Api.Ports middleBound=DispatchMiddleBinding219.bind(mem,base,leafBound,passiveHelper);
        TerminalTailTarget217Api.Ports outerBound=DispatchHelperBinding218.bind(mem,middleBound,new TailPorts() { });
        // The old six-argument callback supplies no entryE. Both old execute methods
        // and the old three-argument DE88 callback must preserve that absence.
        long actual=outerBound.call42420c0(mem,0x4242266L,0xB200L,enterAddress,pointer,leaveAddress);
        eq(actual,returned,"legacy raw leave return");
        mem.expect(List.of(
                op("R32",enterAddress,2),p("enter",0x42420D7L,2),
                op("R8",base+0x5C5D2E8L,0),"X32@"+h(base+0x5C5D2DCL)+"=0>1",
                op("R64",pointer,first),op("R32",first,1),
                p("legacy-context",0x4242162L,base+0x5C5D6B0L),
                op("R64",pointer,first),op("R32",first,1),
                p("e1ac",0x4242191L,base+0x441ED78L,base+0x441ED80L),
                op("R64",pointer+8,second),op("R32",second,1),
                op("R32",leaveAddress,3),p("leave",0x42420E8L,3,leaveAddress)
        ),"legacy absent-E exact complete trace");
        eq(legacyCalls[0],1,"legacy fallback exactly once");
        require(mem.bytes.equals(expectedBytes),"legacy only source exchange changes bytes; no invented temps");
        groups++;
    }
    public static void main(String[] args) {
        currentChain();
        legacy();
        System.out.println("ContextChain227 groups="+groups+" observations="+observations+" mixedChecks="+checks);
    }
}
