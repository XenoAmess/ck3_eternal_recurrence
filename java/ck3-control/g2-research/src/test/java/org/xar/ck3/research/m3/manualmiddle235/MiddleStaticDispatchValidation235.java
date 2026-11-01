package org.xar.ck3.research.m3.manualmiddle235;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle42420F8;
import org.xar.ck3.research.m3.middle235.MiddleStaticDispatch235Api;
import org.xar.ck3.research.m3.middle235.MiddleStaticDispatchBinding235;

public final class MiddleStaticDispatchValidation235 {
    private MiddleStaticDispatchValidation235() { }
    private static int checks,groups,events;
    private static void check(boolean value,String label) { checks++; if(!value) throw new AssertionError(label); }
    private static String h(long value) { return Long.toUnsignedString(value,16); }
    private static long u(int value) { return Integer.toUnsignedLong(value); }
    private static String mem(DispatchMiddle219Api.Memory memory) {
        if(memory instanceof Ram ram) return ram.name;
        throw new AssertionError("unlabelled Memory");
    }
    private static String rw(String kind,long address,long value) { return kind+":"+h(address)+":"+h(value); }
    private static String p(String kind,DispatchMiddle219Api.Memory memory,long... args) {
        StringBuilder text=new StringBuilder(kind+":"+mem(memory));
        for(long value:args) text.append(':').append(h(value));
        return text.toString();
    }
    private static final class Ram implements DispatchMiddle219Api.Memory {
        final String name;
        final List<String> trace=new ArrayList<>();
        final Map<Long,Byte> bytes=new HashMap<>();
        Ram(String name) { this.name=name; }
        private long raw(long address,int width) {
            long result=0;
            for(int i=0;i<width;i++) { Byte value=bytes.get(address+i); if(value==null) throw new AssertionError("unmapped "+name+":"+h(address+i)); result|=(value.longValue()&255L)<<(8*i); }
            return result;
        }
        private void store(long address,int width,long value) { for(int i=0;i<width;i++) bytes.put(address+i,(byte)(value>>>(8*i))); }
        void seed8(long address,int value) { check((value&~255)==0,"seed8 range"); store(address,1,value); }
        void seed32(long address,int value) { store(address,4,u(value)); }
        void seed64(long address,long value) { store(address,8,value); }
        void effect8(long address,int value) { check((value&~255)==0,"effect8 range"); trace.add(rw("E8",address,value)); store(address,1,value); }
        void effect32(long address,int value) { trace.add(rw("E32",address,u(value))); store(address,4,u(value)); }
        void effect64(long address,long value) { trace.add(rw("E64",address,value)); store(address,8,value); }
        long peek64(long address) { return raw(address,8); }
        int peek32(long address) { return (int)raw(address,4); }
        int peek8(long address) { return (int)raw(address,1); }
        Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
        @Override public long readPointer(long address) { long value=raw(address,8); trace.add(rw("R64",address,value)); return value; }
        @Override public int readInt32(long address) { long value=raw(address,4); trace.add(rw("R32",address,value)); return (int)value; }
        @Override public int readUnsigned8(long address) { int value=(int)raw(address,1); trace.add(rw("R8",address,value)); return value; }
        @Override public int readUnsigned16(long address) { int value=(int)raw(address,2); trace.add(rw("R16",address,value)); return value; }
        @Override public void write8(long address,int value) { check((value&~255)==0,"write8 range"); trace.add(rw("W8",address,value)); store(address,1,value); }
        @Override public void writeInt32(long address,int value) { trace.add(rw("W32",address,u(value))); store(address,4,u(value)); }
        @Override public void writeInt64(long address,long value) { trace.add(rw("W64",address,value)); store(address,8,value); }
        @Override public void exchangeInt32(long address,int value) { trace.add(rw("X32",address,u(value))); store(address,4,u(value)); }
    }
    @FunctionalInterface private interface IndirectHook { void call(DispatchMiddle219Api.Memory m,long site,long target,long rax,int ecx,int edx,int r8d); }
    @FunctionalInterface private interface De3Hook { void call(DispatchMiddle219Api.Memory m,long site,long rcx); }
    @FunctionalInterface private interface De4Hook { void call(DispatchMiddle219Api.Memory m,long site,long rcx,long entry); }
    @FunctionalInterface private interface SpanHook { void call(DispatchMiddle219Api.Memory m,long site,long rcx,long rdx); }
    @FunctionalInterface private interface JumpHook { int call(DispatchMiddle219Api.Memory m,long site,long rax,long rcx,int edx,int r8d); }
    private static final class Fallback implements DispatchMiddle219Api.Ports {
        final Ram recorder;
        final IndirectHook indirect;
        final De3Hook de3;
        final De4Hook de4;
        final SpanHook span;
        int indirectCalls,de3Calls,de4Calls,spanCalls;
        Fallback(Ram recorder,IndirectHook indirect,De3Hook de3,De4Hook de4,SpanHook span) { this.recorder=recorder;this.indirect=indirect;this.de3=de3;this.de4=de4;this.span=span; }
        @Override public void call43dbba8(DispatchMiddle219Api.Memory m,long site,long target,long rax,int ecx,int edx,int r8d) {
            indirectCalls++;recorder.trace.add(p("I",m,site,target,rax,u(ecx),u(edx),u(r8d)));indirect.call(m,site,target,rax,ecx,edx,r8d);
        }
        @Override public void call424de88(DispatchMiddle219Api.Memory m,long site,long rcx) { de3Calls++;recorder.trace.add(p("D3",m,site,rcx));de3.call(m,site,rcx); }
        @Override public void call424de88(DispatchMiddle219Api.Memory m,long site,long rcx,long entry) { de4Calls++;recorder.trace.add(p("D4",m,site,rcx,entry));de4.call(m,site,rcx,entry); }
        @Override public void call424e1ac(DispatchMiddle219Api.Memory m,long site,long rcx,long rdx) { spanCalls++;recorder.trace.add(p("S",m,site,rcx,rdx));span.call(m,site,rcx,rdx); }
    }
    private static final class Target implements MiddleStaticDispatch235Api.TailPort {
        final Ram recorder;
        final JumpHook hook;
        final List<Integer> normalResults=new ArrayList<>();
        int calls;
        Target(Ram recorder,JumpHook hook) { this.recorder=recorder;this.hook=hook; }
        @Override public int jumpRax(DispatchMiddle219Api.Memory m,long site,long rax,long rcx,int edx,int r8d) {
            calls++;recorder.trace.add(p("T",m,site,rax,rcx,u(edx),u(r8d)));int result=hook.call(m,site,rax,rcx,edx,r8d);normalResults.add(result);return result;
        }
    }
    private static void rejected(Runnable work,String label) { try { work.run(); } catch(IllegalArgumentException expected) { checks++;return; } throw new AssertionError("not rejected "+label); }
    private static void sameException(Runnable work,RuntimeException expected,String label) { try { work.run(); } catch(RuntimeException actual) { check(actual==expected,label);return; } throw new AssertionError("no exception "+label); }
    private static void complete(Ram memory,List<String> expected,String label) { check(memory.trace.equals(expected),label+" full trace\nexpected="+expected+"\nactual="+memory.trace);groups++;events+=memory.trace.size(); }
    private static void directProtocol() {
        Ram memory=new Ram("D");
        Ram foreign=new Ram("F");
        long base=0xFFFFFFFFFE000000L;
        long active=base+0x4267630L;
        long other=active^0x10L;
        long site=0x4242147L;
        long valueA=0xFEDCBA9876543210L,valueB=0x8123456789ABCDEFL;
        int ecxA=0x80000001,edxA=0xFEDCBA98,r8A=0x89ABCDEF;
        int ecxB=0xFFFFFFFF,edxB=0x80000000,r8B=0xFFFFFFFF;
        long knownA=0x80000001L,knownB=0xFFFFFFFFL;
        long word=0x6000L,effectA=0x123456789ABCDEF0L,effectB=0x8877665544332211L;
        long passiveSite=0x12345678L,passiveRax=0xAABBCCDDEEFF0011L;
        int passiveEcx=0x76543210,passiveEdx=0xFEDCBA90,passiveR8=0x80000002;
        long deRcx=0xCAFEBABE12345678L,entry=0xFEDCBA9876543210L;
        long spanRcx=0xABCDABCDABCDABCDL,spanRdx=0xDCBADCBA98765432L;
        RuntimeException activeFailure=new IllegalStateException("active235");
        RuntimeException indirectFailure=new IllegalStateException("indirect235");
        RuntimeException de3Failure=new IllegalStateException("oldDE235");
        RuntimeException de4Failure=new IllegalStateException("newDE235");
        RuntimeException spanFailure=new IllegalStateException("span235");
        memory.seed8(word-1L,0xA5);memory.seed8(word+8L,0x5A);
        List<String> expected=List.of(
                p("T",memory,site,valueA,knownA,u(edxA),u(r8A)),rw("E64",word,effectA),
                p("T",memory,site,valueB,knownB,u(edxB),u(r8B)),rw("E64",word,effectB),
                p("T",memory,site,valueB,knownB,u(edxB),u(r8B)),
                p("I",foreign,passiveSite,other,passiveRax,u(passiveEcx),u(passiveEdx),u(passiveR8)),
                p("I",foreign,passiveSite,other,passiveRax,u(passiveEcx),u(passiveEdx),u(passiveR8)),
                p("D3",foreign,passiveSite,deRcx),p("D3",foreign,passiveSite,deRcx),
                p("D4",foreign,passiveSite,deRcx,entry),p("D4",foreign,passiveSite,deRcx,entry),
                p("S",foreign,passiveSite,spanRcx,spanRdx),p("S",foreign,passiveSite,spanRcx,spanRdx));
        final int[] targetOrdinal={0},indirectOrdinal={0},de3Ordinal={0},de4Ordinal={0},spanOrdinal={0};
        Target target=new Target(memory,(m,s,rax,rcx,edx,r8d)->{
            check(m==memory&&s==site,"active original Memory/site");
            int ordinal=++targetOrdinal[0];
            if(ordinal==1) {
                check(rax==valueA&&rcx==knownA&&edx==edxA&&r8d==r8A,"first fullRAX unsignedECX rawEDX/R8D");
                memory.effect64(word,effectA);return 0;
            }
            check((ordinal==2||ordinal==3)&&rax==valueB&&rcx==knownB&&edx==edxB&&r8d==r8B,
                    "second fullRAX unsignedECX rawEDX/R8D");
            if(ordinal==2) { memory.effect64(word,effectB);return 0x80000001; }
            throw activeFailure;
        });
        Fallback fallback=new Fallback(memory,
                (m,s,t,rax,ecx,edx,r8d)->{
                    check(m==foreign&&s==passiveSite&&t==other,"different target before active Memory/site guard");
                    check(rax==passiveRax&&ecx==passiveEcx&&edx==passiveEdx&&r8d==passiveR8,"passive indirect original full fields");
                    int ordinal=++indirectOrdinal[0];check(ordinal==1||ordinal==2,"two passive indirect callbacks");
                    if(ordinal==2) throw indirectFailure;
                },
                (m,s,rcx)->{
                    check(m==foreign&&s==passiveSite&&rcx==deRcx,"old3 exact passive fields");
                    int ordinal=++de3Ordinal[0];check(ordinal==1||ordinal==2,"two old3 callbacks");
                    if(ordinal==2) throw de3Failure;
                },
                (m,s,rcx,e)->{
                    check(m==foreign&&s==passiveSite&&rcx==deRcx&&e==entry,"new4 exact context without shift/default collapse");
                    int ordinal=++de4Ordinal[0];check(ordinal==1||ordinal==2,"two new4 callbacks");
                    if(ordinal==2) throw de4Failure;
                },
                (m,s,rcx,rdx)->{
                    check(m==foreign&&s==passiveSite&&rcx==spanRcx&&rdx==spanRdx,"span exact passive fields");
                    int ordinal=++spanOrdinal[0];check(ordinal==1||ordinal==2,"two span callbacks");
                    if(ordinal==2) throw spanFailure;
                });
        DispatchMiddle219Api.Ports bound=MiddleStaticDispatchBinding235.bind(base,memory,target,fallback);
        bound.call43dbba8(memory,site,active,valueA,ecxA,edxA,r8A);
        bound.call43dbba8(memory,site,active,valueB,ecxB,edxB,r8B);
        check(target.normalResults.equals(List.of(0,0x80000001)),"two real normal int results recorded, no fabricated RAX");
        int beforeTrace=memory.trace.size();Map<Long,Byte> before=memory.snapshot(),foreignBefore=foreign.snapshot();
        rejected(()->bound.call43dbba8(foreign,site,active,valueA,ecxA,edxA,r8A),"active foreign");
        rejected(()->bound.call43dbba8(memory,site+1L,active,valueA,ecxA,edxA,r8A),"active site");
        check(target.calls==2&&fallback.indirectCalls==0&&fallback.de3Calls==0&&fallback.de4Calls==0&&fallback.spanCalls==0,
                "active rejection before all callbacks");
        check(memory.trace.size()==beforeTrace&&memory.snapshot().equals(before)&&foreign.snapshot().equals(foreignBefore),
                "active rejection before RAM and global trace effects");
        sameException(()->bound.call43dbba8(memory,site,active,valueB,ecxB,edxB,r8B),activeFailure,"active exact exception");
        bound.call43dbba8(foreign,passiveSite,other,passiveRax,passiveEcx,passiveEdx,passiveR8);
        sameException(()->bound.call43dbba8(foreign,passiveSite,other,passiveRax,passiveEcx,passiveEdx,passiveR8),indirectFailure,"indirect exact exception");
        bound.call424de88(foreign,passiveSite,deRcx);
        sameException(()->bound.call424de88(foreign,passiveSite,deRcx),de3Failure,"old3 exact exception");
        bound.call424de88(foreign,passiveSite,deRcx,entry);
        sameException(()->bound.call424de88(foreign,passiveSite,deRcx,entry),de4Failure,"new4 exact exception");
        bound.call424e1ac(foreign,passiveSite,spanRcx,spanRdx);
        sameException(()->bound.call424e1ac(foreign,passiveSite,spanRcx,spanRdx),spanFailure,"span exact exception");
        check(target.calls==3&&target.normalResults.size()==2&&fallback.indirectCalls==2&&fallback.de3Calls==2
                &&fallback.de4Calls==2&&fallback.spanCalls==2,"all actual callbacks once, no normal result after throw");
        check(memory.peek64(word)==effectB&&memory.peek8(word-1L)==0xA5&&memory.peek8(word+8L)==0x5A,
                "last explicit supplier word and adjacent canaries");
        check(foreign.snapshot().equals(foreignBefore)&&foreign.trace.isEmpty(),"passive foreign storage untouched");
        complete(memory,expected,"directProtocol");
    }
    private static void actualCaller() {
        Ram memory=new Ram("R");
        long base=0x10000000L,p=0x1000L,entry=0x8000L;
        long flag=base+0x5C5D2E8L,gate=base+0x5C5D2DCL;
        long cookieAddress=base+0x542F0B8L,encodedAddress=base+0x5C5D2E0L,iat=base+0x43DBBA8L;
        long cookie=5L,decoded=0x8123456789ABCDEFL;
        long encoded=Long.rotateLeft(decoded,5)^cookie;
        long active=base+0x4267630L;
        memory.seed8(flag,0);memory.seed32(gate,0x89ABCDEF);
        memory.seed64(p,0x2000L);memory.seed32(0x2000L,0);
        memory.seed64(p+8L,0x3000L);memory.seed64(p+16L,0x4000L);
        memory.seed32(0x2020L,0);memory.seed32(0x3010L,0);memory.seed8(0x5000L,0);
        memory.seed64(cookieAddress,cookie);memory.seed64(encodedAddress,encoded);memory.seed64(iat,active);
        int flagBefore=(int)(encoded>>>56)&255,gateAfter=(int)encoded&255;
        memory.seed8(flag-1L,flagBefore);memory.seed8(flag+1L,0x92);
        memory.seed8(gate-1L,0x93);memory.seed8(gate+4L,gateAfter);
        memory.seed8(0x4FFFL,0x95);memory.seed8(0x5001L,0x96);
        List<String> expected=List.of(
                rw("R8",flag,0),rw("X32",gate,1),rw("R64",p,0x2000L),rw("R32",0x2000L,0),
                rw("R64",cookieAddress,cookie),rw("R64",encodedAddress,encoded),rw("R64",iat,active),
                p("T",memory,0x4242147L,decoded,0,0,0),rw("E64",p+8L,0x3010L),
                p("D4",memory,0x4242162L,base+0x5C5D698L,entry-0x30L),rw("E64",p,0x2020L),
                rw("R64",p,0x2020L),rw("R32",0x2020L,0),
                p("S",memory,0x424217EL,base+0x441ED48L,base+0x441ED70L),
                p("S",memory,0x4242191L,base+0x441ED78L,base+0x441ED80L),rw("E64",p+16L,0x5000L),
                rw("R64",p+8L,0x3010L),rw("R32",0x3010L,0),rw("W8",flag,1),rw("R64",p+16L,0x5000L),rw("W8",0x5000L,1));
        final int[] spans={0};
        Fallback fallback=new Fallback(memory,
                (m,s,t,rax,ecx,edx,r8d)->{throw new AssertionError("actual qualifying IAT reached passive fallback");},
                (m,s,rcx)->{throw new AssertionError("newexecute4 lost current DE88 context to old3");},
                (m,s,rcx,e)->{
                    check(m==memory&&s==0x4242162L&&rcx==base+0x5C5D698L,"actual DE88 Memory/site/receiver");
                    check(e==entry-0x30L,"actual DE88 per-call entryRsp minus30 exactly once");
                    memory.effect64(p,0x2020L);
                },
                (m,s,rcx,rdx)->{
                    check(m==memory,"actual span same Memory");
                    int ordinal=++spans[0];
                    if(ordinal==1) {
                        check(s==0x424217EL&&rcx==base+0x441ED48L&&rdx==base+0x441ED70L,"conditional first actual span");
                    } else {
                        check(ordinal==2&&s==0x4242191L&&rcx==base+0x441ED78L&&rdx==base+0x441ED80L,"unconditional second actual span");
                        memory.effect64(p+16L,0x5000L);
                    }
                });
        Target target=new Target(memory,(m,s,rax,rcx,edx,r8d)->{
            check(m==memory&&s==0x4242147L&&rax==decoded,"actual XOR/ROR full64 target and known site/Memory");
            check(rcx==0L&&edx==0&&r8d==0,"actual source establishes ECX/EDX/R8D zero at this call only");
            memory.effect64(p+8L,0x3010L);return 0x80000001;
        });
        DispatchMiddle219Api.Ports bound=MiddleStaticDispatchBinding235.bind(base,memory,target,fallback);
        DispatchMiddle42420F8.execute(memory,bound,new DispatchMiddle219Api.Input(base,p),entry);
        check(target.calls==1&&target.normalResults.equals(List.of(0x80000001)),"one real synchronous int callback, outer producer remains void");
        check(fallback.indirectCalls==0&&fallback.de3Calls==0&&fallback.de4Calls==1&&fallback.spanCalls==2&&spans[0]==2,
                "actual new active path and exact context/span callback counts");
        check(memory.peek64(p)==0x2020L&&memory.peek64(p+8L)==0x3010L&&memory.peek64(p+16L)==0x5000L,
                "three explicitly mutated future pointers retained");
        check(memory.peek32(gate)==1&&memory.peek8(flag)==1&&memory.peek8(0x5000L)==1,
                "actual XCHG DWORD and final two BYTE writes");
        check(memory.peek8(flag-1L)==flagBefore&&memory.peek8(flag+1L)==0x92&&memory.peek8(gate-1L)==0x93
                &&memory.peek8(gate+4L)==gateAfter&&memory.peek8(0x4FFFL)==0x95&&memory.peek8(0x5001L)==0x96,
                "DWORD/BYTE operations preserve exact adjacent byte canaries");
        complete(memory,expected,"actualCaller");
    }
    public static void main(String[] args) { directProtocol();actualCaller();System.out.println("MIDDLE_STATIC235_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0"); }
}
