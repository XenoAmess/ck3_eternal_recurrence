package org.xar.ck3.research.m3.manualf780243;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.f780243.F780Api243;
import org.xar.ck3.research.m3.f780243.F780Target424F780;
import org.xar.ck3.research.m3.f780243.F780FromF8Binding243;
import org.xar.ck3.research.m3.f780243.F780IndexedTailBinding243;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f8a8242.F8a8Target424F8A8;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;

/** One finite source-derived manual Test; callback scripts only, no native or CPU model. */
public final class F780Validation243 {
    private F780Validation243() { }
    private static int checks,groups,events;
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static String h(long value){return Long.toUnsignedString(value,16);}
    private static long u32(int value){return Integer.toUnsignedLong(value);}
    private static String rw(String role,long address,long value){return role+":"+h(address)+":"+h(value);}
    private static String ev(String role,NativeTaskMemory memory,long... arguments){
        StringBuilder text=new StringBuilder("C:").append(role).append(':').append(((Ram)memory).name);
        for(long value:arguments)text.append(':').append(h(value));return text.toString();
    }
    private static final class Ram implements F780Api243.Memory {
        final String name;final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
        int atomicCalls;Consumer<Ram> atomicEffect;
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
        @Override public void writeInt16(long address,int value){trace.add(rw("W16",address,value&65535L));store(address,2,value);}
        @Override public void atomicIncrementInt32(long address){long before=raw(address,4),after=(before+1)&0xFFFFFFFFL;store(address,4,after);atomicCalls++;trace.add("A32:"+h(address)+":"+h(before)+":"+h(after));if(atomicEffect!=null)atomicEffect.accept(this);}
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
    private static final class LeafPorts implements F780Api243.Ports {
        final Plan plan;LeafPorts(Plan plan){this.plan=plan;}
        @Override public void call4247ffc(F780Api243.Memory m,long site,int ecx){plan.invoke("ENTER",m,site,u32(ecx));}
        @Override public void call4248050(F780Api243.Memory m,long site,int ecx,long rbx){plan.invoke("LEAVE",m,site,u32(ecx),rbx);}
    }
    private static final class OldF8Ports implements F8a8Api242.Ports {
        final Plan plan;OldF8Ports(Plan plan){this.plan=plan;}
        @Override public void call424f780(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9){plan.invoke("F780_OLD",m,site,rcx,rdx,r8,r9);}
        @Override public void call424f800(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9){plan.invoke("F800_OLD",m,site,rcx,rdx,r8,r9);}
    }
    /** Existing mature tail API has no Memory argument; fixture captures its recorder explicitly. */
    private static final class TailPorts implements RequestIndexedTails4247ffc.Ports {
        final Plan plan;TailPorts(Plan plan){this.plan=plan;}
        @Override public void jump43da500(long rcx,long rax){plan.invoke("TAIL500",plan.recorder,rcx,rax);}
        @Override public void jump43da4f0(long rcx,long rax,long rbx){plan.invoke("TAIL4F0",plan.recorder,rcx,rax,rbx);}
    }
    private static void rejectedRuntime(Runnable work,String label){try{work.run();}catch(RuntimeException expected){checks++;return;}throw new AssertionError("no RuntimeException rejection: "+label);}
    private static void sameException(Runnable work,RuntimeException expected,String label){try{work.run();}catch(RuntimeException actual){check(actual==expected,label);return;}throw new AssertionError("no original exception: "+label);}
    private static void complete(Ram memory,List<String> expected,String label,Plan... plans){
        check(memory.trace.equals(expected),label+" fulltrace\nexpected="+expected+"\nactual="+memory.trace);
        for(Plan plan:plans)plan.exhausted();groups++;events+=memory.trace.size();
    }
    private static void direct63() {
        String[] names={"homeRdxFresh","homeR8Alias","enterThrow"};
        long[] entries={0x1000L,0x2000L,0x3000L},rdx={0x1020L,0x3000L,0x4000L},r8={0x2000L,0x2020L,0x9000L},r9={0x5000L,0x6000L,0xA000L};
        List<List<String>> expectedAll=List.of(
            List.of(
                "W64:1020:5000",
                "R32:1020:5000",
                "C:ENTER:homeRdxFresh:424f797:5000",
                "E64:2000:2100",
                "R64:2000:2100",
                "R64:2100:2200",
                "R64:2288:2300",
                "A32:2300:ffffffff:0",
                "E32:5000:80000001",
                "R32:5000:80000001",
                "C:LEAVE:homeRdxFresh:424f7af:80000001:5000"
            ),
            List.of(
                "W64:2020:6000",
                "R32:3000:ffffffff",
                "C:ENTER:homeR8Alias:424f797:ffffffff",
                "R64:2020:6000",
                "R64:6000:7000",
                "R64:7088:8000",
                "A32:8000:7fffffff:80000000",
                "R32:6000:7000",
                "C:LEAVE:homeR8Alias:424f7af:7000:6000"
            ),
            List.of(
                "W64:3020:a000",
                "R32:4000:f1234567",
                "C:ENTER:enterThrow:424f797:f1234567"
            ));
        for(int scene=0;scene<names.length;scene++) {
            Ram m=new Ram(names[scene]);long E=entries[scene],home=E+0x20;
            m.seed8(home-1,0xA5);m.seed8(home+8,0x5A);
            switch(scene) {
                case 0 -> {m.seed64(0x1020,0xAABBCCDD12345678L);m.seed64(0x2000,0xDEADDEADDEADDEADL);m.seed64(0x2100,0x2200);m.seed64(0x2288,0x2300);m.seed64(0x2300,0xAABBCCDDFFFFFFFFL);m.seed64(0x5000,0x1122334455667788L);}
                case 1 -> {m.seed64(0x2020,0xAABBCCDDEEFF0011L);m.seed32(0x3000,-1);m.seed64(0x6000,0x7000);m.seed64(0x7088,0x8000);m.seed64(0x8000,0xC3D4E5F67FFFFFFFL);}
                case 2 -> m.seed32(0x4000,0xF1234567);
                default -> throw new AssertionError("finite literal scene");
            }
            Ram expectedRam=new Ram("literalExpected");expectedRam.bytes.putAll(m.snapshot());
            switch(scene) {
                case 0 -> {
                    expectedRam.store(0x1020L,8,0x5000L);
                    expectedRam.store(0x2000L,8,0x2100L);
                    expectedRam.store(0x2300L,4,0x0L);
                    expectedRam.store(0x5000L,4,0x80000001L);
                }
                case 1 -> {
                    expectedRam.store(0x2020L,8,0x6000L);
                    expectedRam.store(0x8000L,4,0x80000000L);
                }
                case 2 -> {
                    expectedRam.store(0x3020L,8,0xA000L);
                }
                default -> throw new AssertionError("finite literal expected bytes");
            }
            Map<Long,Byte> finalBytes=expectedRam.snapshot();
            RuntimeException marker=new RuntimeException("original ENTER marker");
            List<Call> calls=new ArrayList<>();
            calls.add(c("ENTER",m,new long[]{0x424F797L,scene==0?0x5000L:scene==1?0xFFFFFFFFL:0xF1234567L},0,scene==0?x->x.effect64(0x2000,0x2100):null,scene==2?marker:null));
            if(scene!=2)calls.add(c("LEAVE",m,new long[]{0x424F7AFL,scene==0?0x80000001L:0x7000L,r9[scene]},0,null,null));
            if(scene==0)m.atomicEffect=x->x.effect32(0x5000,0x80000001);
            Plan plan=new Plan(m,calls);F780Api243.Input input=new F780Api243.Input(rdx[scene],r8[scene],r9[scene],new F780Api243.Scratch(E));
            if(scene==2)sameException(()->F780Target424F780.execute(m,new LeafPorts(plan),input),marker,"original ENTER exception object");
            else F780Target424F780.execute(m,new LeafPorts(plan),input);
            check(m.snapshot().equals(finalBytes),"direct exact final bytes and atomic high DWORD "+names[scene]);
            check(m.atomicCalls==(scene==2?0:1),"one atomic capability only after normal enter");
            complete(m,expectedAll.get(scene),"literal direct63 "+names[scene],plan);
        }
    }
    private static void actual205Chain243() {
        {
            long base=0x100000000L,P=0x10000L,B=P-8,block=0x200000L,counter=base+0x542F770L,tailBase=base+0x5C5D330L;
            Ram m=new Ram("actual205");m.seed64(block+0x3A0,0x1122334455667788L);m.seed64(counter,0xABCDEF01FFFFFFFFL);
            m.seed8(block+0xBB,0xA5);m.seed8(block+0xBE,0x5A);m.seed8(block+0x1C1,0xC3);m.seed8(block+0x1C4,0x3C);
            m.seed8(counter-1,0xD6);m.seed8(counter+8,0x6D);
            Plan tp=new Plan(m,List.of(
                c("TAIL500",m,new long[]{tailBase+0xC8,tailBase},0,x->x.effect32(B+0x20,9),null),
                c("TAIL4F0",m,new long[]{tailBase+0x168,tailBase,B+0x20},0,null,null)));
            Plan fp=new Plan(m,List.of(c("F800_OLD",m,new long[]{0x424F96AL,B+0x18,B-0x2C,B-0x10,B-0x30},0,null,null)));
            F780Api243.Ports child=F780IndexedTailBinding243.bind(base,m,new TailPorts(tp));
            F8a8Api242.Ports bound=F780FromF8Binding243.bind(m,child,new OldF8Ports(fp));
            List<String> expected=List.of(
                "W64:ffd0:200000",
                "W64:ffe0:ffd0",
                "W32:10018:5",
                "W32:10020:5",
                "W64:ffe8:ffd0",
                "W64:fff0:ffd8",
                "W32:ffc8:4",
                "W32:ffcc:4",
                "W64:ffd8:105c5dcd8",
                "W32:200028:1",
                "R64:ffd0:200000",
                "W64:200000:1044267f0",
                "R64:ffd0:200000",
                "W32:2003a8:1",
                "R64:ffd0:200000",
                "W64:200088:10542f770",
                "R64:ffd0:200000",
                "W16:2000bc:43",
                "R64:ffd0:200000",
                "W16:2001c2:43",
                "R64:ffd0:200000",
                "R64:2003a0:1122334455667788",
                "W64:2003a0:0",
                "W64:ffc0:10018",
                "R32:10020:5",
                "C:TAIL500:actual205:105c5d3f8:105c5d330",
                "E32:10018:9",
                "R64:ffe0:ffd0",
                "R64:ffd0:200000",
                "R64:200088:10542f770",
                "A32:10542f770:ffffffff:0",
                "R32:10018:9",
                "C:TAIL4F0:actual205:105c5d498:105c5d330:10018",
                "C:F800_OLD:actual205:424f96a:10010:ffcc:ffe8:ffc8"
            );
            Ram expectedRam=new Ram("literalExpected");expectedRam.bytes.putAll(m.snapshot());
            expectedRam.store(0xFFD0L,8,0x200000L);
            expectedRam.store(0xFFE0L,8,0xFFD0L);
            expectedRam.store(0x10018L,4,0x5L);
            expectedRam.store(0x10020L,4,0x5L);
            expectedRam.store(0xFFE8L,8,0xFFD0L);
            expectedRam.store(0xFFF0L,8,0xFFD8L);
            expectedRam.store(0xFFC8L,4,0x4L);
            expectedRam.store(0xFFCCL,4,0x4L);
            expectedRam.store(0xFFD8L,8,0x105C5DCD8L);
            expectedRam.store(0x200028L,4,0x1L);
            expectedRam.store(0x200000L,8,0x1044267F0L);
            expectedRam.store(0x2003A8L,4,0x1L);
            expectedRam.store(0x200088L,8,0x10542F770L);
            expectedRam.store(0x2000BCL,2,0x43L);
            expectedRam.store(0x2001C2L,2,0x43L);
            expectedRam.store(0x2003A0L,8,0x0L);
            expectedRam.store(0xFFC0L,8,0x10018L);
            expectedRam.store(0x10018L,4,0x9L);
            expectedRam.store(0x10542F770L,4,0x0L);
            Map<Long,Byte> finalBytes=expectedRam.snapshot();
            F8a8Target424F8A8.execute(m,bound,new F8a8Api242.Input(base,block,new F8a8Api242.Scratch(P)));
            check(m.snapshot().equals(finalBytes),"actual205 exact source writes and atomic high DWORD");
            check(m.atomicCalls==1,"actual205 only one atomic DWORD operation");
            complete(m,expected,"real205 new7 current E and both actual mature helpers",tp,fp);
        }
        {
            long base=0x200000000L,tailBase=base+0x5C5D330L,E=0xA000L;
            Ram m=new Ram("protocol"),foreign=new Ram("foreign");m.seed32(0x6000,-1);m.seed8(E+0x1F,0xE7);m.seed8(E+0x28,0x7E);
            foreign.seed64(0xB000,0x13579BDF2468ACE0L);
            Map<Long,Byte> initial=m.snapshot(),foreignInitial=foreign.snapshot();
            RuntimeException marker=new RuntimeException("original tail or fallback marker");
            Plan tp=new Plan(m,List.of(c("TAIL500",m,new long[]{tailBase-0x28,tailBase},0,null,marker)));
            Plan fp=new Plan(m,List.of(
                c("F780_OLD",foreign,new long[]{0x901,0x123456789ABCDEF0L,0x8000000000000001L,0xFEDCBA9876543210L,0x8877665544332211L},0,null,null),
                c("F780_OLD",foreign,new long[]{0x902,1,2,3,4},0,null,marker),
                c("F800_OLD",foreign,new long[]{0x903,-1L,0x8123456789ABCDEFL,0x123456789ABCDEF0L,Long.MIN_VALUE},0,null,null),
                c("F800_OLD",foreign,new long[]{0x904,5,6,7,8},0,null,marker),
                c("F780_OLD",foreign,new long[]{0x905,9,10,11,12},0,null,null)));
            TailPorts tails=new TailPorts(tp);F780Api243.Ports child=F780IndexedTailBinding243.bind(base,m,tails);OldF8Ports fallback=new OldF8Ports(fp);
            F8a8Api242.Ports bound=F780FromF8Binding243.bind(m,child,fallback);
            List<String> expected=List.of(
                "C:F780_OLD:foreign:901:123456789abcdef0:8000000000000001:fedcba9876543210:8877665544332211",
                "C:F780_OLD:foreign:902:1:2:3:4",
                "C:F800_OLD:foreign:903:ffffffffffffffff:8123456789abcdef:123456789abcdef0:8000000000000000",
                "C:F800_OLD:foreign:904:5:6:7:8",
                "C:F780_OLD:foreign:905:9:a:b:c",
                "W64:a020:7000",
                "R32:6000:ffffffff",
                "C:TAIL500:protocol:205c5d308:205c5d330"
            );
            Ram expectedRam=new Ram("literalExpected");expectedRam.bytes.putAll(initial);
            expectedRam.store(0xA020L,8,0x7000L);
            Map<Long,Byte> finalBytes=expectedRam.snapshot();
            rejectedRuntime(()->bound.call424f780(foreign,0x424F955L,0,0x6000,0xDEAD0000L,0x7000,E),"new7 foreign Memory");
            rejectedRuntime(()->bound.call424f780(m,0x424F956L,0,0x6000,0xDEAD0000L,0x7000,E),"new7 wrong site");
            rejectedRuntime(()->child.call4247ffc(foreign,0x424F797L,1),"enter tail foreign Memory");
            rejectedRuntime(()->child.call4247ffc(m,0x424F798L,1),"enter tail wrong site");
            rejectedRuntime(()->child.call4248050(foreign,0x424F7AFL,2,0x1234),"leave tail foreign Memory");
            rejectedRuntime(()->child.call4248050(m,0x424F7B0L,2,0x1234),"leave tail wrong site");
            rejectedRuntime(()->F780FromF8Binding243.bind(null,child,fallback),"null binding Memory");
            rejectedRuntime(()->F780FromF8Binding243.bind(m,null,fallback),"null binding child");
            rejectedRuntime(()->F780FromF8Binding243.bind(m,child,null),"null binding fallback");
            rejectedRuntime(()->F780IndexedTailBinding243.bind(0,null,tails),"null tail Memory");
            rejectedRuntime(()->F780IndexedTailBinding243.bind(0,m,null),"null tail capability");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty(),"guards before home write or tail effect");
            check(tp.cursor==0&&fp.cursor==0&&m.atomicCalls==0&&foreign.atomicCalls==0,"guard no child fallback atomic consumption");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"guards exact byte snapshots");
            bound.call424f780(foreign,0x901,0x123456789ABCDEF0L,0x8000000000000001L,0xFEDCBA9876543210L,0x8877665544332211L);
            sameException(()->bound.call424f780(foreign,0x902,1,2,3,4),marker,"old6 original fallback exception");
            bound.call424f800(foreign,0x903,-1L,0x8123456789ABCDEFL,0x123456789ABCDEF0L,Long.MIN_VALUE);
            sameException(()->bound.call424f800(foreign,0x904,5,6,7,8),marker,"F800 original fallback exception");
            fallback.call424f780(foreign,0x905,9,10,11,12,0xFEDCBA9876543210L);
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"legacy/default no home write");
            sameException(()->bound.call424f780(m,0x424F955L,0x123456789ABCDEF0L,0x6000,0xDEAD0000L,0x7000,E),marker,"new7 actual mature tail original exception");
            check(m.snapshot().equals(finalBytes)&&foreign.snapshot().equals(foreignInitial),"binding tail exception exact prefix bytes");
            check(m.atomicCalls==0&&foreign.atomicCalls==0&&foreign.trace.isEmpty(),"tail throw stops before pointer chain and atomic");
            complete(m,expected,"legacy default F800 guards and actual tail exception",tp,fp);
        }
    }
    public static void main(String[] ignored){direct63();actual205Chain243();System.out.println("F780243_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
