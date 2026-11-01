package org.xar.ck3.research.m3.manualf8a8242;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.allocator241.Allocator241Api;
import org.xar.ck3.research.m3.allocator241.AllocatorFromFc74Binding241;
import org.xar.ck3.research.m3.e900239.E900Api239;
import org.xar.ck3.research.m3.e900239.E900FromFc74Binding239;
import org.xar.ck3.research.m3.e948240.E948Api240;
import org.xar.ck3.research.m3.e948240.E948FromFc74Binding240;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f8a8242.F8a8Target424F8A8;
import org.xar.ck3.research.m3.f8a8242.F8a8FromFc74Binding242;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214;
import org.xar.ck3.research.m3.terminal214.TerminalHandler4247004;
import org.xar.ck3.research.m3.fc74238.Fc74FromHandlerBinding238;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;

/** One finite source-derived manual Test; callback scripts only, no native or CPU model. */
public final class F8a8Validation242 {
    private F8a8Validation242() { }
    private static int checks,groups,events;
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static String h(long value){return Long.toUnsignedString(value,16);}
    private static long u32(int value){return Integer.toUnsignedLong(value);}
    private static String rw(String role,long address,long value){return role+":"+h(address)+":"+h(value);}
    private static String ev(String role,NativeTaskMemory memory,long... arguments){
        StringBuilder text=new StringBuilder("C:").append(role).append(':').append(((Ram)memory).name);
        for(long value:arguments)text.append(':').append(h(value));return text.toString();
    }
    private static final class Ram implements NativeTaskMemory,F8a8Api242.Memory,Terminal4247004Api214.Memory {
        final String name;final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
        Ram(String name){this.name=name;}
        private long raw(long address,int width){long value=0;for(int index=0;index<width;index++){Byte b=bytes.get(address+index);if(b==null)throw new AssertionError("unmapped "+name+":"+h(address+index));value|=(b.longValue()&255L)<<(index*8);}return value;}
        private void store(long address,int width,long value){for(int index=0;index<width;index++)bytes.put(address+index,(byte)(value>>>(index*8)));}
        void seed8(long address,int value){check((value&~255)==0,"seed8 range");store(address,1,value);}
        void seed32(long address,int value){store(address,4,u32(value));}
        void seed64(long address,long value){store(address,8,value);}
        void effect32(long address,int value){trace.add(rw("E32",address,u32(value)));store(address,4,u32(value));}
        void effect64(long address,long value){trace.add(rw("E64",address,value));store(address,8,value);}
        long peek64(long address){return raw(address,8);}
        int peek32(long address){return (int)raw(address,4);}
        int peek8(long address){return (int)raw(address,1);}
        Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
        @Override public int readUnsigned8(long address){int v=(int)raw(address,1);trace.add(rw("R8",address,v));return v;}
        @Override public void write8(long address,int value){trace.add(rw("W8",address,value&255L));store(address,1,value);}
        @Override public void writeInt16(long address,int value){trace.add(rw("W16",address,value&65535L));store(address,2,value);}
        @Override public long readPointer(long address){long value=raw(address,8);trace.add(rw("R64",address,value));return value;}
        @Override public int readInt32(long address){long value=raw(address,4);trace.add(rw("R32",address,value));return (int)value;}
        @Override public void writeInt64(long address,long value){trace.add(rw("W64",address,value));store(address,8,value);}
        @Override public void writeInt32(long address,int value){trace.add(rw("W32",address,u32(value)));store(address,4,u32(value));}
    }
    /** Expected callback fields only; ordered RAM effects remain in the same recorder trace. */
    private record Call(String role,NativeTaskMemory memory,long[] arguments,long returned,Consumer<Ram> effect,RuntimeException failure){ }
    private static Call c(String role,NativeTaskMemory memory,long[] arguments,long returned,Consumer<Ram> effect,RuntimeException failure){return new Call(role,memory,arguments,returned,effect,failure);}
    private static final class Plan {
        final Ram recorder;final List<Call> calls;int cursor;
        Plan(Ram recorder,List<Call> calls){this.recorder=recorder;this.calls=List.copyOf(calls);}
        long invoke(String role,NativeTaskMemory memory,long... arguments){
            check(cursor<calls.size(),"unexpected callback "+role);Call expected=calls.get(cursor++);
            check(expected.role().equals(role),"exact callback role");check(expected.memory()==memory,"exact callback Memory object");
            check(Arrays.equals(expected.arguments(),arguments),"exact callback arguments "+role);
            recorder.trace.add(ev(role,memory,arguments));
            if(expected.effect()!=null)expected.effect().accept(recorder);
            if(expected.failure()!=null)throw expected.failure();return expected.returned();
        }
        void exhausted(){check(cursor==calls.size(),"all planned callbacks consumed");}
    }
    private static final class LeafPorts implements F8a8Api242.Ports {
        final Plan plan;LeafPorts(Plan plan){this.plan=plan;}
        @Override public void call424f780(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9){plan.invoke("F780",m,site,rcx,rdx,r8,r9);}
        @Override public void call424f800(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9){plan.invoke("F800",m,site,rcx,rdx,r8,r9);}
    }
    private static final class FcPorts implements Fc74Api238.Ports {
        final Plan plan;FcPorts(Plan plan){this.plan=plan;}
        @Override public int callIat43da738(NativeTaskMemory m,long site,long target,int ecx){return (int)plan.invoke("FIRST",m,site,target,u32(ecx));}
        @Override public long call424e900(NativeTaskMemory m,long site,int ecx){return plan.invoke("E900",m,site,u32(ecx));}
        @Override public int call424e948(NativeTaskMemory m,long site,int ecx,long rdx){return (int)plan.invoke("E948",m,site,u32(ecx),rdx);}
        @Override public long call424e2ec(NativeTaskMemory m,long site,long rcx,long rdx){return plan.invoke("ALLOC",m,site,rcx,rdx);}
        @Override public void call424e364(NativeTaskMemory m,long site,long rcx){plan.invoke("FREE",m,site,rcx);}
        @Override public void call424f8a8(NativeTaskMemory m,long site,long rcx){plan.invoke("INIT_OLD",m,site,rcx);}
        @Override public void callIat43da420(NativeTaskMemory m,long site,long target,int ecx){plan.invoke("LAST",m,site,target,u32(ecx));}
    }
    private static final class HandlerPorts implements Terminal4247004Api214.Ports {
        final Plan plan;HandlerPorts(Plan plan){this.plan=plan;}
        @Override public long call424fc74(Terminal4247004Api214.Memory m,long site,int ecx){return plan.invoke("H_FC74_OLD",m,site,u32(ecx));}
        @Override public long call423b18c(Terminal4247004Api214.Memory m,long site){return plan.invoke("H_CELL",m,site);}
        @Override public void call4232a50(Terminal4247004Api214.Memory m,long site){plan.invoke("H_ERROR",m,site);}
        @Override public void call4247ffc(Terminal4247004Api214.Memory m,long site,int ecx){plan.invoke("H_ENTER",m,site,u32(ecx));}
        @Override public long call424faf8(Terminal4247004Api214.Memory m,long site){return plan.invoke("H_OBJECT",m,site);}
        @Override public void call4248050(Terminal4247004Api214.Memory m,long site,int ecx){plan.invoke("H_LEAVE",m,site,u32(ecx));}
        @Override public void call4242354(Terminal4247004Api214.Memory m,long site,int ecx){plan.invoke("H_ABORT",m,site,u32(ecx));}
        @Override public void callIndirectR8(Terminal4247004Api214.Memory m,Terminal4247004Api214.DispatchR8 d){plan.invoke("H_R8",m,d.siteRva(),d.targetSlotAddress(),d.targetBits(),d.handlerBits(),u32(d.ecxBits()),u32(d.edxBits()));}
        @Override public void callIndirectRdx(Terminal4247004Api214.Memory m,Terminal4247004Api214.DispatchRdx d){plan.invoke("H_RDX",m,d.siteRva(),d.targetSlotAddress(),d.targetBits(),d.handlerBits(),u32(d.ecxBits()));}
    }
    /** Actual three new4 forwarding edges; their unrelated active algorithms must remain uncalled. */
    private static Fc74Api238.Ports forwardingPath(long base,Ram m,F8a8Api242.Ports leaf,Fc74Api238.Ports fallback){
        E900Api239.Ports no900=new E900Api239.Ports(){
            @Override public long call424e448(NativeTaskMemory x,long s,int c,long d,long r8,long r9){throw new AssertionError("unplanned E900 algorithm");}
            @Override public long tail43dbba8(NativeTaskMemory x,long s,long t,long a,int c){throw new AssertionError("unplanned E900 tail");}
            @Override public long tail43da460(NativeTaskMemory x,long s,long t,long a,int c){throw new AssertionError("unplanned E900 tail");}
        };
        E948Api240.Ports no948=new E948Api240.Ports(){
            @Override public long call424e448(NativeTaskMemory x,long s,int c,long d,long r8,long r9){throw new AssertionError("unplanned E948 algorithm");}
            @Override public long callIat43dbba8(NativeTaskMemory x,long s,long t,long a,int c,long d){throw new AssertionError("unplanned E948 IAT");}
            @Override public long callIat43da470(NativeTaskMemory x,long s,long t,long a,int c,long d){throw new AssertionError("unplanned E948 IAT");}
        };
        Allocator241Api.Ports noAlloc=new Allocator241Api.Ports(){
            @Override public long allocateImported(NativeTaskMemory x,long s,long t,long h,int f,long b){throw new AssertionError("unplanned allocator algorithm");}
            @Override public int retryGate(NativeTaskMemory x,long s){throw new AssertionError("unplanned allocator gate");}
            @Override public int retryCall(NativeTaskMemory x,long s,long b){throw new AssertionError("unplanned allocator retry");}
            @Override public long failureCellAddress(NativeTaskMemory x,long s){throw new AssertionError("unplanned allocator cell");}
        };
        Fc74Api238.Ports path=F8a8FromFc74Binding242.bind(base,m,leaf,fallback);
        path=AllocatorFromFc74Binding241.bind(base,m,noAlloc,path);
        path=E948FromFc74Binding240.bind(base,m,no948,path);
        return E900FromFc74Binding239.bind(base,m,no900,path);
    }
    /** Script the seven unrelated old calls; route only new4 through the actual forwardingPath. */
    private static Fc74Api238.Ports contextOnly(Fc74Api238.Ports scripted,Fc74Api238.Ports path){
        return new Fc74Api238.Ports(){
            @Override public int callIat43da738(NativeTaskMemory m,long s,long t,int c){return scripted.callIat43da738(m,s,t,c);}
            @Override public long call424e900(NativeTaskMemory m,long s,int c){return scripted.call424e900(m,s,c);}
            @Override public int call424e948(NativeTaskMemory m,long s,int c,long d){return scripted.call424e948(m,s,c,d);}
            @Override public long call424e2ec(NativeTaskMemory m,long s,long c,long d){return scripted.call424e2ec(m,s,c,d);}
            @Override public void call424e364(NativeTaskMemory m,long s,long c){scripted.call424e364(m,s,c);}
            @Override public void call424f8a8(NativeTaskMemory m,long s,long c){scripted.call424f8a8(m,s,c);}
            @Override public void callIat43da420(NativeTaskMemory m,long s,long t,int c){scripted.callIat43da420(m,s,t,c);}
            @Override public void call424f8a8(NativeTaskMemory m,long s,long c,long e){path.call424f8a8(m,s,c,e);}
        };
    }
    private static void rejectedRuntime(Runnable work,String label){try{work.run();}catch(RuntimeException expected){checks++;return;}throw new AssertionError("no RuntimeException rejection: "+label);}
    private static void sameException(Runnable work,RuntimeException expected,String label){try{work.run();}catch(RuntimeException actual){check(actual==expected,label);return;}throw new AssertionError("no original exception: "+label);}
    private static void complete(Ram memory,List<String> expected,String label,Plan... plans){
        check(memory.trace.equals(expected),label+" fulltrace\nexpected="+expected+"\nactual="+memory.trace);
        for(Plan plan:plans)plan.exhausted();groups++;events+=memory.trace.size();
    }
    private static void producer205() {
        String[] names={"normalMutation","homeAlias","firstThrow"};
        long[] bases={0x100000000L,0x200000000L,0x300000000L};
        long[] entries={0x5000L,0x100005000L,0x7000L};
        long[] blocks={0x9000L,0x100004FA8L,0xB000L};
        long[] freshHomes={0x9000L,0x100000001L,0xB000L};
        long[] oldRmw={0x1122334455667788L,0x8877665544332211L,0xAABBCCDD11223344L};
        List<List<String>> expectedAll=List.of(
            List.of(
                "W64:4fd0:9000",
                "W64:4fe0:4fd0",
                "W32:5018:5",
                "W32:5020:5",
                "W64:4fe8:4fd0",
                "W64:4ff0:4fd8",
                "W32:4fc8:4",
                "W32:4fcc:4",
                "W64:4fd8:105c5dcd8",
                "W32:9028:1",
                "R64:4fd0:9000",
                "W64:9000:1044267f0",
                "R64:4fd0:9000",
                "W32:93a8:1",
                "R64:4fd0:9000",
                "W64:9088:10542f770",
                "R64:4fd0:9000",
                "W16:90bc:43",
                "R64:4fd0:9000",
                "W16:91c2:43",
                "R64:4fd0:9000",
                "R64:93a0:1122334455667788",
                "W64:93a0:0",
                "C:F780:normalMutation:424f955:5010:5020:4fe0:5018",
                "E32:4fc8:80000001",
                "E64:4fe8:a1a2a3a4a5a6a7a8",
                "C:F800:normalMutation:424f96a:5010:4fcc:4fe8:4fc8"
            ),
            List.of(
                "W64:100004fd0:100004fa8",
                "W64:100004fe0:100004fd0",
                "W32:100005018:5",
                "W32:100005020:5",
                "W64:100004fe8:100004fd0",
                "W64:100004ff0:100004fd8",
                "W32:100004fc8:4",
                "W32:100004fcc:4",
                "W64:100004fd8:205c5dcd8",
                "W32:100004fd0:1",
                "R64:100004fd0:100000001",
                "W64:100000001:2044267f0",
                "R64:100004fd0:100000001",
                "W32:1000003a9:1",
                "R64:100004fd0:100000001",
                "W64:100000089:20542f770",
                "R64:100004fd0:100000001",
                "W16:1000000bd:43",
                "R64:100004fd0:100000001",
                "W16:1000001c3:43",
                "R64:100004fd0:100000001",
                "R64:1000003a1:8877665544332211",
                "W64:1000003a1:0",
                "C:F780:homeAlias:424f955:100005010:100005020:100004fe0:100005018",
                "C:F800:homeAlias:424f96a:100005010:100004fcc:100004fe8:100004fc8"
            ),
            List.of(
                "W64:6fd0:b000",
                "W64:6fe0:6fd0",
                "W32:7018:5",
                "W32:7020:5",
                "W64:6fe8:6fd0",
                "W64:6ff0:6fd8",
                "W32:6fc8:4",
                "W32:6fcc:4",
                "W64:6fd8:305c5dcd8",
                "W32:b028:1",
                "R64:6fd0:b000",
                "W64:b000:3044267f0",
                "R64:6fd0:b000",
                "W32:b3a8:1",
                "R64:6fd0:b000",
                "W64:b088:30542f770",
                "R64:6fd0:b000",
                "W16:b0bc:43",
                "R64:6fd0:b000",
                "W16:b1c2:43",
                "R64:6fd0:b000",
                "R64:b3a0:aabbccdd11223344",
                "W64:b3a0:0",
                "C:F780:firstThrow:424f955:7010:7020:6fe0:7018"
            ));
        for(int scene=0;scene<names.length;scene++) {
            long base=bases[scene],E=entries[scene],B=E-8,block=blocks[scene],fresh=freshHomes[scene];
            Ram m=new Ram(names[scene]);m.seed64(fresh+0x3A0,oldRmw[scene]);
            m.seed8(fresh+0xBB,0xA5);m.seed8(fresh+0xBE,0x5A);m.seed8(fresh+0x1C1,0xC3);m.seed8(fresh+0x1C4,0x3C);
            Ram expectedRam=new Ram("literalExpected");expectedRam.bytes.putAll(m.snapshot());
            switch(scene) {
                case 0 -> {
                    expectedRam.store(0x4FD0L,8,0x9000L);
                    expectedRam.store(0x4FE0L,8,0x4FD0L);
                    expectedRam.store(0x5018L,4,0x5L);
                    expectedRam.store(0x5020L,4,0x5L);
                    expectedRam.store(0x4FE8L,8,0x4FD0L);
                    expectedRam.store(0x4FF0L,8,0x4FD8L);
                    expectedRam.store(0x4FC8L,4,0x4L);
                    expectedRam.store(0x4FCCL,4,0x4L);
                    expectedRam.store(0x4FD8L,8,0x105C5DCD8L);
                    expectedRam.store(0x9028L,4,0x1L);
                    expectedRam.store(0x9000L,8,0x1044267F0L);
                    expectedRam.store(0x93A8L,4,0x1L);
                    expectedRam.store(0x9088L,8,0x10542F770L);
                    expectedRam.store(0x90BCL,2,0x43L);
                    expectedRam.store(0x91C2L,2,0x43L);
                    expectedRam.store(0x93A0L,8,0x0L);
                    expectedRam.store(0x4FC8L,4,0x80000001L);
                    expectedRam.store(0x4FE8L,8,0xA1A2A3A4A5A6A7A8L);
                }
                case 1 -> {
                    expectedRam.store(0x100004FD0L,8,0x100004FA8L);
                    expectedRam.store(0x100004FE0L,8,0x100004FD0L);
                    expectedRam.store(0x100005018L,4,0x5L);
                    expectedRam.store(0x100005020L,4,0x5L);
                    expectedRam.store(0x100004FE8L,8,0x100004FD0L);
                    expectedRam.store(0x100004FF0L,8,0x100004FD8L);
                    expectedRam.store(0x100004FC8L,4,0x4L);
                    expectedRam.store(0x100004FCCL,4,0x4L);
                    expectedRam.store(0x100004FD8L,8,0x205C5DCD8L);
                    expectedRam.store(0x100004FD0L,4,0x1L);
                    expectedRam.store(0x100000001L,8,0x2044267F0L);
                    expectedRam.store(0x1000003A9L,4,0x1L);
                    expectedRam.store(0x100000089L,8,0x20542F770L);
                    expectedRam.store(0x1000000BDL,2,0x43L);
                    expectedRam.store(0x1000001C3L,2,0x43L);
                    expectedRam.store(0x1000003A1L,8,0x0L);
                }
                case 2 -> {
                    expectedRam.store(0x6FD0L,8,0xB000L);
                    expectedRam.store(0x6FE0L,8,0x6FD0L);
                    expectedRam.store(0x7018L,4,0x5L);
                    expectedRam.store(0x7020L,4,0x5L);
                    expectedRam.store(0x6FE8L,8,0x6FD0L);
                    expectedRam.store(0x6FF0L,8,0x6FD8L);
                    expectedRam.store(0x6FC8L,4,0x4L);
                    expectedRam.store(0x6FCCL,4,0x4L);
                    expectedRam.store(0x6FD8L,8,0x305C5DCD8L);
                    expectedRam.store(0xB028L,4,0x1L);
                    expectedRam.store(0xB000L,8,0x3044267F0L);
                    expectedRam.store(0xB3A8L,4,0x1L);
                    expectedRam.store(0xB088L,8,0x30542F770L);
                    expectedRam.store(0xB0BCL,2,0x43L);
                    expectedRam.store(0xB1C2L,2,0x43L);
                    expectedRam.store(0xB3A0L,8,0x0L);
                }
                default -> throw new AssertionError("finite literal scene");
            }
            Map<Long,Byte> finalBytes=expectedRam.snapshot();
            RuntimeException marker=new RuntimeException("original F780 marker");
            Consumer<Ram> firstEffect=scene==0?r->{r.effect32(B-0x30,0x80000001);r.effect64(B-0x10,0xA1A2A3A4A5A6A7A8L);}:null;
            Consumer<Ram> secondObservation=scene==0?r->{check(r.peek32(B-0x30)==0x80000001,"second callback sees modified DWORD local");check(r.peek64(B-0x10)==0xA1A2A3A4A5A6A7A8L,"second callback sees modified pointer local");}:null;
            List<Call> calls=new ArrayList<>();
            calls.add(c("F780",m,new long[]{0x424F955L,B+0x18,B+0x28,B-0x18,B+0x20},0,firstEffect,scene==2?marker:null));
            if(scene!=2)calls.add(c("F800",m,new long[]{0x424F96AL,B+0x18,B-0x2C,B-0x10,B-0x30},0,secondObservation,null));
            Plan plan=new Plan(m,calls);F8a8Api242.Input input=new F8a8Api242.Input(base,block,new F8a8Api242.Scratch(E));
            if(scene==2)sameException(()->F8a8Target424F8A8.execute(m,new LeafPorts(plan),input),marker,"F780 original exception object");
            else F8a8Target424F8A8.execute(m,new LeafPorts(plan),input);
            check(m.snapshot().equals(finalBytes),"producer exact final bytes and WORD neighbors "+names[scene]);
            complete(m,expectedAll.get(scene),"source205 "+names[scene],plan);
        }
    }
    private static void actualContextChain242() {
        {
            long base=0x400000000L,block=0x300000L,first=base+0x43DA738,last=base+0x43DA420,index=base+0x542F328;
            long firstTarget=0x123456789ABCDEF0L,lastTarget=0xFEDCBA9876543210L,table=base+0x44267F0;
            long[] handlerEntries={0x10000L,0x20000L};
            Ram m=new Ram("actualChain");m.seed64(first,firstTarget);m.seed64(last,lastTarget);m.seed32(index,-1);
            m.seed64(base+0x44268B0,1);m.seed32(table+4,4);m.seed64(table+8,1);
            m.seed64(block+0x3A0,0x1122334455667788L);
            m.seed8(block+0xBB,0xA5);m.seed8(block+0xBE,0x5A);m.seed8(block+0x1C1,0xC3);m.seed8(block+0x1C4,0x3C);
            for(long H:handlerEntries){long D=H-0x68;m.seed32(D+0x78,0xA1B2C3D4);m.seed64(D+0x80,0x8877665544332211L);m.seed8(D+0x6F,0xE6);m.seed8(D+0x71,0x6E);}
            List<Call> leafCalls=new ArrayList<>(),fcCalls=new ArrayList<>();
            for(long H:handlerEntries) {
                long E=H-0xA0,B=E-8;
                leafCalls.add(c("F780",m,new long[]{0x424F955L,B+0x18,B+0x28,B-0x18,B+0x20},0,null,null));
                leafCalls.add(c("F800",m,new long[]{0x424F96AL,B+0x18,B-0x2C,B-0x10,B-0x30},0,null,null));
                fcCalls.add(c("FIRST",m,new long[]{0x424FC83L,firstTarget,4},0x81234567L,null,null));
                fcCalls.add(c("E948",m,new long[]{0x424FCB9L,0xFFFFFFFFL,-1L},1,null,null));
                fcCalls.add(c("ALLOC",m,new long[]{0x424FCCCL,1,0x3C8},block,null,null));
                fcCalls.add(c("E948",m,new long[]{0x424FCF2L,0xFFFFFFFFL,block},1,null,null));
                fcCalls.add(c("FREE",m,new long[]{0x424FD17L,0},0,null,null));
                fcCalls.add(c("LAST",m,new long[]{0x424FD21L,lastTarget,0x81234567L},0,null,null));
            }
            Plan lp=new Plan(m,leafCalls),fp=new Plan(m,fcCalls),hp=new Plan(m,List.of());
            FcPorts script=new FcPorts(fp);Fc74Api238.Ports path=forwardingPath(base,m,new LeafPorts(lp),script);
            Fc74Api238.Ports routed=contextOnly(script,path);
            Terminal4247004Api214.Ports bound=Fc74FromHandlerBinding238.bind(base,m,routed,new HandlerPorts(hp));
            List<List<String>> expectedAll=List.of(
                List.of(
                    "R32:10010:a1b2c3d4",
                    "W32:10010:0",
                    "W8:10008:1",
                    "R64:4043da738:123456789abcdef0",
                    "C:FIRST:actualChain:424fc83:123456789abcdef0:4",
                    "R32:40542f328:ffffffff",
                    "C:E948:actualChain:424fcb9:ffffffff:ffffffffffffffff",
                    "C:ALLOC:actualChain:424fccc:1:3c8",
                    "R32:40542f328:ffffffff",
                    "C:E948:actualChain:424fcf2:ffffffff:300000",
                    "W64:ff30:300000",
                    "W64:ff40:ff30",
                    "W32:ff78:5",
                    "W32:ff80:5",
                    "W64:ff48:ff30",
                    "W64:ff50:ff38",
                    "W32:ff28:4",
                    "W32:ff2c:4",
                    "W64:ff38:405c5dcd8",
                    "W32:300028:1",
                    "R64:ff30:300000",
                    "W64:300000:4044267f0",
                    "R64:ff30:300000",
                    "W32:3003a8:1",
                    "R64:ff30:300000",
                    "W64:300088:40542f770",
                    "R64:ff30:300000",
                    "W16:3000bc:43",
                    "R64:ff30:300000",
                    "W16:3001c2:43",
                    "R64:ff30:300000",
                    "R64:3003a0:1122334455667788",
                    "W64:3003a0:0",
                    "C:F780:actualChain:424f955:ff70:ff80:ff40:ff78",
                    "C:F800:actualChain:424f96a:ff70:ff2c:ff48:ff28",
                    "C:FREE:actualChain:424fd17:0",
                    "R64:4043da420:fedcba9876543210",
                    "C:LAST:actualChain:424fd21:fedcba9876543210:81234567",
                    "R64:300000:4044267f0",
                    "R64:4044268b0:1",
                    "R32:4044267f4:4",
                    "W8:10008:0",
                    "R64:10018:8877665544332211",
                    "W64:10018:0",
                    "R64:4044267f8:1"
                ),
                List.of(
                    "R32:20010:a1b2c3d4",
                    "W32:20010:0",
                    "W8:20008:1",
                    "R64:4043da738:123456789abcdef0",
                    "C:FIRST:actualChain:424fc83:123456789abcdef0:4",
                    "R32:40542f328:ffffffff",
                    "C:E948:actualChain:424fcb9:ffffffff:ffffffffffffffff",
                    "C:ALLOC:actualChain:424fccc:1:3c8",
                    "R32:40542f328:ffffffff",
                    "C:E948:actualChain:424fcf2:ffffffff:300000",
                    "W64:1ff30:300000",
                    "W64:1ff40:1ff30",
                    "W32:1ff78:5",
                    "W32:1ff80:5",
                    "W64:1ff48:1ff30",
                    "W64:1ff50:1ff38",
                    "W32:1ff28:4",
                    "W32:1ff2c:4",
                    "W64:1ff38:405c5dcd8",
                    "W32:300028:1",
                    "R64:1ff30:300000",
                    "W64:300000:4044267f0",
                    "R64:1ff30:300000",
                    "W32:3003a8:1",
                    "R64:1ff30:300000",
                    "W64:300088:40542f770",
                    "R64:1ff30:300000",
                    "W16:3000bc:43",
                    "R64:1ff30:300000",
                    "W16:3001c2:43",
                    "R64:1ff30:300000",
                    "R64:3003a0:0",
                    "W64:3003a0:0",
                    "C:F780:actualChain:424f955:1ff70:1ff80:1ff40:1ff78",
                    "C:F800:actualChain:424f96a:1ff70:1ff2c:1ff48:1ff28",
                    "C:FREE:actualChain:424fd17:0",
                    "R64:4043da420:fedcba9876543210",
                    "C:LAST:actualChain:424fd21:fedcba9876543210:81234567",
                    "R64:300000:4044267f0",
                    "R64:4044268b0:1",
                    "R32:4044267f4:4",
                    "W8:20008:0",
                    "R64:20018:8877665544332211",
                    "W64:20018:0",
                    "R64:4044267f8:1"
                ));
            Ram expectedRam=new Ram("literalExpected");expectedRam.bytes.putAll(m.snapshot());
            for(int round=0;round<handlerEntries.length;round++) {
                switch(round) {
                    case 0 -> {
                        expectedRam.store(0x10010L,4,0x0L);
                        expectedRam.store(0x10008L,1,0x1L);
                        expectedRam.store(0xFF30L,8,0x300000L);
                        expectedRam.store(0xFF40L,8,0xFF30L);
                        expectedRam.store(0xFF78L,4,0x5L);
                        expectedRam.store(0xFF80L,4,0x5L);
                        expectedRam.store(0xFF48L,8,0xFF30L);
                        expectedRam.store(0xFF50L,8,0xFF38L);
                        expectedRam.store(0xFF28L,4,0x4L);
                        expectedRam.store(0xFF2CL,4,0x4L);
                        expectedRam.store(0xFF38L,8,0x405C5DCD8L);
                        expectedRam.store(0x300028L,4,0x1L);
                        expectedRam.store(0x300000L,8,0x4044267F0L);
                        expectedRam.store(0x3003A8L,4,0x1L);
                        expectedRam.store(0x300088L,8,0x40542F770L);
                        expectedRam.store(0x3000BCL,2,0x43L);
                        expectedRam.store(0x3001C2L,2,0x43L);
                        expectedRam.store(0x3003A0L,8,0x0L);
                        expectedRam.store(0x10008L,1,0x0L);
                        expectedRam.store(0x10018L,8,0x0L);
                    }
                    case 1 -> {
                        expectedRam.store(0x20010L,4,0x0L);
                        expectedRam.store(0x20008L,1,0x1L);
                        expectedRam.store(0x1FF30L,8,0x300000L);
                        expectedRam.store(0x1FF40L,8,0x1FF30L);
                        expectedRam.store(0x1FF78L,4,0x5L);
                        expectedRam.store(0x1FF80L,4,0x5L);
                        expectedRam.store(0x1FF48L,8,0x1FF30L);
                        expectedRam.store(0x1FF50L,8,0x1FF38L);
                        expectedRam.store(0x1FF28L,4,0x4L);
                        expectedRam.store(0x1FF2CL,4,0x4L);
                        expectedRam.store(0x1FF38L,8,0x405C5DCD8L);
                        expectedRam.store(0x300028L,4,0x1L);
                        expectedRam.store(0x300000L,8,0x4044267F0L);
                        expectedRam.store(0x3003A8L,4,0x1L);
                        expectedRam.store(0x300088L,8,0x40542F770L);
                        expectedRam.store(0x3000BCL,2,0x43L);
                        expectedRam.store(0x3001C2L,2,0x43L);
                        expectedRam.store(0x3003A0L,8,0x0L);
                        expectedRam.store(0x20008L,1,0x0L);
                        expectedRam.store(0x20018L,8,0x0L);
                    }
                    default -> throw new AssertionError("finite current-H round");
                }
                Map<Long,Byte> finalBytes=expectedRam.snapshot();
                Terminal4247004Api214.Outcome result=TerminalHandler4247004.execute(m,bound,new Terminal4247004Api214.Input(base,4,new Terminal4247004Api214.Scratch(handlerEntries[round])));
                check(result instanceof Terminal4247004Api214.NormalReturn,"actual context chain normal outcome");
                check(((Terminal4247004Api214.NormalReturn)result).raxBits()==0,"actual214 handler sentinel result zero");
                check(m.snapshot().equals(finalBytes),"current H exact source writes and WORD canaries");
                check(m.trace.equals(expectedAll.get(round)),"complete actual214/FC74/205 trace round "+round+" expected="+expectedAll.get(round)+" actual="+m.trace);
                groups++;events+=m.trace.size();m.trace.clear();
            }
            lp.exhausted();fp.exhausted();hp.exhausted();
        }
        {
            long base=0x500000000L,E=0x9000L,block=0xE000L,B=E-8;
            Ram m=new Ram("protocolCaptured"),foreign=new Ram("protocolForeign");
            m.seed64(block+0x3A0,0x1020304050607080L);m.seed8(block+0xBB,0xD5);m.seed8(block+0xBE,0x5D);m.seed8(block+0x1C1,0xE7);m.seed8(block+0x1C4,0x7E);
            foreign.seed64(0x880,0x13579BDF2468ACE0L);
            Map<Long,Byte> initial=m.snapshot(),foreignInitial=foreign.snapshot();
            RuntimeException marker=new RuntimeException("original protocol marker");
            Plan lp=new Plan(m,List.of(c("F780",m,new long[]{0x424F955L,B+0x18,B+0x28,B-0x18,B+0x20},0,null,marker)));
            Plan fp=new Plan(m,List.of(
                c("INIT_OLD",foreign,new long[]{0x901,0x123456789ABCDEF0L},0,null,null),
                c("INIT_OLD",foreign,new long[]{0x902,0xFEDCBA9876543210L},0,null,marker),
                c("INIT_OLD",foreign,new long[]{0x903,0x8000000000000001L},0,null,null),
                c("FIRST",foreign,new long[]{0x904,0xABCDEF0123456789L,0xFFFFFFFFL},0x80000001L,null,null),
                c("FIRST",foreign,new long[]{0x905,0x0123456789ABCDEFL,0x80000000L},0,null,marker)));
            Plan hp=new Plan(m,List.of(c("H_FC74_OLD",foreign,new long[]{0x906,0x81234567L},0xAABBCCDDEEFF0011L,null,null)));
            LeafPorts leaf=new LeafPorts(lp);FcPorts fallback=new FcPorts(fp);
            Fc74Api238.Ports path=forwardingPath(base,m,leaf,fallback);
            List<String> expected=List.of(
                "C:INIT_OLD:protocolForeign:901:123456789abcdef0",
                "C:INIT_OLD:protocolForeign:902:fedcba9876543210",
                "C:INIT_OLD:protocolForeign:903:8000000000000001",
                "C:FIRST:protocolForeign:904:abcdef0123456789:ffffffff",
                "C:FIRST:protocolForeign:905:123456789abcdef:80000000",
                "C:H_FC74_OLD:protocolForeign:906:81234567",
                "W64:8fd0:e000",
                "W64:8fe0:8fd0",
                "W32:9018:5",
                "W32:9020:5",
                "W64:8fe8:8fd0",
                "W64:8ff0:8fd8",
                "W32:8fc8:4",
                "W32:8fcc:4",
                "W64:8fd8:505c5dcd8",
                "W32:e028:1",
                "R64:8fd0:e000",
                "W64:e000:5044267f0",
                "R64:8fd0:e000",
                "W32:e3a8:1",
                "R64:8fd0:e000",
                "W64:e088:50542f770",
                "R64:8fd0:e000",
                "W16:e0bc:43",
                "R64:8fd0:e000",
                "W16:e1c2:43",
                "R64:8fd0:e000",
                "R64:e3a0:1020304050607080",
                "W64:e3a0:0",
                "C:F780:protocolCaptured:424f955:9010:9020:8fe0:9018"
            );
            Ram expectedRam=new Ram("literalExpected");expectedRam.bytes.putAll(initial);
            expectedRam.store(0x8FD0L,8,0xE000L);
            expectedRam.store(0x8FE0L,8,0x8FD0L);
            expectedRam.store(0x9018L,4,0x5L);
            expectedRam.store(0x9020L,4,0x5L);
            expectedRam.store(0x8FE8L,8,0x8FD0L);
            expectedRam.store(0x8FF0L,8,0x8FD8L);
            expectedRam.store(0x8FC8L,4,0x4L);
            expectedRam.store(0x8FCCL,4,0x4L);
            expectedRam.store(0x8FD8L,8,0x505C5DCD8L);
            expectedRam.store(0xE028L,4,0x1L);
            expectedRam.store(0xE000L,8,0x5044267F0L);
            expectedRam.store(0xE3A8L,4,0x1L);
            expectedRam.store(0xE088L,8,0x50542F770L);
            expectedRam.store(0xE0BCL,2,0x43L);
            expectedRam.store(0xE1C2L,2,0x43L);
            expectedRam.store(0xE3A0L,8,0x0L);
            Map<Long,Byte> finalBytes=expectedRam.snapshot();
            rejectedRuntime(()->path.call424f8a8(foreign,0x424FD10L,block,E),"new4 foreign Memory before effects");
            rejectedRuntime(()->path.call424f8a8(m,0x424FD11L,block,E),"new4 wrong site before effects");
            rejectedRuntime(()->F8a8FromFc74Binding242.bind(base,null,leaf,fallback),"factory null Memory");
            rejectedRuntime(()->F8a8FromFc74Binding242.bind(base,m,null,fallback),"factory null child");
            rejectedRuntime(()->F8a8FromFc74Binding242.bind(base,m,leaf,null),"factory null fallback");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty(),"guard zero RAM or callback observations");
            check(lp.cursor==0&&fp.cursor==0&&hp.cursor==0,"guard zero planned-call consumption");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"guard exact byte snapshots");
            path.call424f8a8(foreign,0x901,0x123456789ABCDEF0L);
            sameException(()->path.call424f8a8(foreign,0x902,0xFEDCBA9876543210L),marker,"legacy old3 exception exact");
            fallback.call424f8a8(foreign,0x903,0x8000000000000001L,0xDEADBEEF01234567L);
            check(path.callIat43da738(foreign,0x904,0xABCDEF0123456789L,-1)==0x80000001,"passive FIRST original intbits");
            sameException(()->path.callIat43da738(foreign,0x905,0x0123456789ABCDEFL,0x80000000),marker,"passive FIRST exact exception");
            check(new HandlerPorts(hp).call424fc74(foreign,0x906,0x81234567,0xFEDCBA9876543210L)==0xAABBCCDDEEFF0011L,"214 newdefault exact old3 full64 return");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"legacy/default/passive no extra Memory IO");
            sameException(()->path.call424f8a8(m,0x424FD10L,block,E),marker,"new4 through three forwarders original F780 exception");
            check(m.snapshot().equals(finalBytes),"binding exception prefix exact source byte writes");
            check(foreign.snapshot().equals(foreignInitial)&&foreign.trace.isEmpty(),"legacy foreign Memory untouched");
            complete(m,expected,"legacy defaults guards passive and new4 exception",lp,fp,hp);
        }
    }
    public static void main(String[] ignored){producer205();actualContextChain242();System.out.println("F8A8242_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
