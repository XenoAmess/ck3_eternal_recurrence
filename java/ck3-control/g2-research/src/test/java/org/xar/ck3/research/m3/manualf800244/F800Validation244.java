package org.xar.ck3.research.m3.manualf800244;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.f780243.F780Api243;
import org.xar.ck3.research.m3.f800244.F800Api244;
import org.xar.ck3.research.m3.f800244.F800Target424F800;
import org.xar.ck3.research.m3.f800244.F800FromF8Binding244;
import org.xar.ck3.research.m3.f800244.F800IndexedTailBinding244;
import org.xar.ck3.research.m3.f780243.F780Target424F780;
import org.xar.ck3.research.m3.f780243.F780FromF8Binding243;
import org.xar.ck3.research.m3.f780243.F780IndexedTailBinding243;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f8a8242.F8a8Target424F8A8;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;

/** One finite source-derived manual Test; callback scripts only, no native or CPU model. */
public final class F800Validation244 {
    private F800Validation244() { }
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
    private static final class F780Ports implements F780Api243.Ports {
        final Plan plan;F780Ports(Plan plan){this.plan=plan;}
        @Override public void call4247ffc(F780Api243.Memory m,long site,int ecx){plan.invoke("ENTER",m,site,u32(ecx));}
        @Override public void call4248050(F780Api243.Memory m,long site,int ecx,long rbx){plan.invoke("LEAVE",m,site,u32(ecx),rbx);}
    }
    private static final class LeafPorts implements F800Api244.Ports {
        final Plan plan;LeafPorts(Plan plan){this.plan=plan;}
        @Override public void call4247ffc(F8a8Api242.Memory m,long site,int ecx){plan.invoke("ENTER800",m,site,u32(ecx));}
        @Override public void call4248050(F8a8Api242.Memory m,long site,int ecx,long rbx){plan.invoke("LEAVE800",m,site,u32(ecx),rbx);}
        @Override public void call424fa90(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){plan.invoke("MIDDLE800",m,site,rcx,rdx,rax);}
    }
    private static final class ExtendedF8Ports implements F8a8Api242.Ports {
        final Plan plan;ExtendedF8Ports(Plan plan){this.plan=plan;}
        @Override public void call424f780(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9){plan.invoke("F780_OLD",m,site,rcx,rdx,r8,r9);}
        @Override public void call424f800(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9){plan.invoke("F800_OLD",m,site,rcx,rdx,r8,r9);}
        @Override public void call424f780(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9,long entry){plan.invoke("F780_NEW",m,site,rcx,rdx,r8,r9,entry);}
        @Override public void call424f800(F8a8Api242.Memory m,long site,long rcx,long rdx,long r8,long r9,long entry){plan.invoke("F800_NEW",m,site,rcx,rdx,r8,r9,entry);}
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
    private static void expectedWrite(Map<Long,Byte> bytes,long address,int width,long value){
        for(int index=0;index<width;index++)bytes.put(address+index,(byte)(value>>>(index*8)));
    }
    private static void direct69(){
        {
            Ram m=new Ram("D1");
            m.seed64(0x1020L,0xAABBCCDDEEFF0011L);
            m.seed64(0x3000L,0x7000L);
            m.seed64(0x3008L,0x10000L);
            m.seed64(0x5000L,0x6000L);
            m.seed64(0x6000L,0xFEDCBA9876543210L);
            m.seed64(0x7000L,0x8123456789ABCDEFL);
            m.seed64(0x4000L,0xAAAABBBB11223344L);
            m.seed8(0x101FL,0xA5);m.seed8(0x1030L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x1020L,8,0x4000L);
            expectedWrite(expected,0x3008L,8,0x5000L);
            expectedWrite(expected,0x4000L,4,0x80000001L);
            Plan plan=new Plan(m,List.of(
                c("ENTER800",m,new long[]{0x424F817L,0x4000L},0L,x->x.effect64(0x3008L,0x5000L),null),
                c("MIDDLE800",m,new long[]{0x424F82DL,0x8123456789ABCDEFL,0xFEDCBA9876543210L,0x5000L},0L,x->x.effect32(0x4000L,0x80000001),null),
                c("LEAVE800",m,new long[]{0x424F835L,0x80000001L,0x4000L},0L,null,null)));
            F800Target424F800.execute(m,new LeafPorts(plan),new F800Api244.Input(0x1020L,0x3000L,0x4000L,new F800Api244.Scratch(0x1000L)));
            check(m.snapshot().equals(expected),"exact finalallbytes direct1");
            check(m.atomicCalls==0,"new69doesnotinvokeatomic");
            complete(m,List.of(
                "W64:1020:4000",
                "R32:1020:4000",
                "C:ENTER800:D1:424f817:4000",
                "E64:3008:5000",
                "R64:3008:5000",
                "R64:5000:6000",
                "R64:3000:7000",
                "R64:6000:fedcba9876543210",
                "R64:7000:8123456789abcdef",
                "C:MIDDLE800:D1:424f82d:8123456789abcdef:fedcba9876543210:5000",
                "E32:4000:80000001",
                "R32:4000:80000001",
                "C:LEAVE800:D1:424f835:80000001:4000"
            ),"independent source direct1",plan);
        }
        {
            Ram m=new Ram("D2");
            m.seed64(0x2020L,0xDEADDEADDEADDEADL);
            m.seed64(0x2028L,0x6000L);
            m.seed64(0x6000L,0x7000L);
            m.seed64(0x7000L,0x1122334455667788L);
            m.seed64(0x5000L,0x8877665544332211L);
            m.seed32(0x3000L,(int)0xFFFFFFFFL);
            m.seed8(0x201FL,0xA5);m.seed8(0x2030L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x2020L,8,0x5000L);
            Plan plan=new Plan(m,List.of(
                c("ENTER800",m,new long[]{0x424F817L,0xFFFFFFFFL},0L,null,null),
                c("MIDDLE800",m,new long[]{0x424F82DL,0x8877665544332211L,0x1122334455667788L,0x6000L},0L,null,null),
                c("LEAVE800",m,new long[]{0x424F835L,0x44332211L,0x5000L},0L,null,null)));
            F800Target424F800.execute(m,new LeafPorts(plan),new F800Api244.Input(0x3000L,0x2020L,0x5000L,new F800Api244.Scratch(0x2000L)));
            check(m.snapshot().equals(expected),"exact finalallbytes direct2");
            check(m.atomicCalls==0,"new69doesnotinvokeatomic");
            complete(m,List.of(
                "W64:2020:5000",
                "R32:3000:ffffffff",
                "C:ENTER800:D2:424f817:ffffffff",
                "R64:2028:6000",
                "R64:6000:7000",
                "R64:2020:5000",
                "R64:7000:1122334455667788",
                "R64:5000:8877665544332211",
                "C:MIDDLE800:D2:424f82d:8877665544332211:1122334455667788:6000",
                "R32:5000:44332211",
                "C:LEAVE800:D2:424f835:44332211:5000"
            ),"independent source direct2",plan);
        }
        {
            Ram m=new Ram("D3");
            m.seed64(0x5000L,0x9000L);
            m.seed64(0x5008L,0x7000L);
            m.seed64(0x7000L,0x8000L);
            m.seed64(0x8000L,0xABCDEF0011223344L);
            m.seed64(0x9000L,0xFEDCBA9876543210L);
            m.seed32(0x4000L,(int)0x7L);
            m.seed8(0x301FL,0xA5);m.seed8(0x3030L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x3020L,8,0x6000L);
            RuntimeException marker=new RuntimeException("opaque-middle-original");
            Plan plan=new Plan(m,List.of(
                c("ENTER800",m,new long[]{0x424F817L,7L},0L,null,null),
                c("MIDDLE800",m,new long[]{0x424F82DL,0xFEDCBA9876543210L,0xABCDEF0011223344L,0x7000L},0L,null,marker)));
            sameException(()->F800Target424F800.execute(m,new LeafPorts(plan),new F800Api244.Input(0x4000L,0x5000L,0x6000L,new F800Api244.Scratch(0x3000L))),marker,"originalmiddle/noaftereffects");
            check(m.snapshot().equals(expected),"exact finalallbytes direct3");
            check(m.atomicCalls==0,"new69doesnotinvokeatomic");
            complete(m,List.of(
                "W64:3020:6000",
                "R32:4000:7",
                "C:ENTER800:D3:424f817:7",
                "R64:5008:7000",
                "R64:7000:8000",
                "R64:5000:9000",
                "R64:8000:abcdef0011223344",
                "R64:9000:fedcba9876543210",
                "C:MIDDLE800:D3:424f82d:fedcba9876543210:abcdef0011223344:7000"
            ),"independent source direct3",plan);
        }
    }
    private static void actual205Protocol244(){
        {
            Ram m=new Ram("CHAIN");
            m.seed64(0x2003A0L,0x1122334455667788L);
            m.seed64(0x10542F770L,0xABCDEF01FFFFFFFFL);
            m.seed64(0x105C5DCD8L,0xFEDCBA9876543210L);
            m.seed8(0x2000BBL,0xA5);
            m.seed8(0x2000BEL,0xA5);
            m.seed8(0x2001C1L,0xA5);
            m.seed8(0x2001C4L,0xA5);
            m.seed8(0x10542F76FL,0xA5);
            m.seed8(0x10542F778L,0xA5);
            m.seed8(0xFFBFL,0xA5);
            m.seed8(0xFFC7L,0xA5);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0xFFD0L,8,0x200000L);
            expectedWrite(expected,0xFFE0L,8,0xFFD0L);
            expectedWrite(expected,0x10018L,4,0x5L);
            expectedWrite(expected,0x10020L,4,0x5L);
            expectedWrite(expected,0xFFE8L,8,0xFFD0L);
            expectedWrite(expected,0xFFF0L,8,0xFFD8L);
            expectedWrite(expected,0xFFC8L,4,0x4L);
            expectedWrite(expected,0xFFCCL,4,0x4L);
            expectedWrite(expected,0xFFD8L,8,0x105C5DCD8L);
            expectedWrite(expected,0x200028L,4,0x1L);
            expectedWrite(expected,0x200000L,8,0x1044267F0L);
            expectedWrite(expected,0x2003A8L,4,0x1L);
            expectedWrite(expected,0x200088L,8,0x10542F770L);
            expectedWrite(expected,0x2000BCL,2,0x43L);
            expectedWrite(expected,0x2001C2L,2,0x43L);
            expectedWrite(expected,0x2003A0L,8,0x0L);
            expectedWrite(expected,0xFFC0L,8,0x10018L);
            expectedWrite(expected,0x10542F770L,4,0x0L);
            expectedWrite(expected,0xFFC0L,8,0xFFC8L);
            expectedWrite(expected,0xFFC8L,4,0xFFFFFFFEL);
            Plan f780=new Plan(m,List.of(
                c("ENTER",m,new long[]{0x424F797L,5L},0L,null,null),
                c("LEAVE",m,new long[]{0x424F7AFL,5L,0x10018L},0L,null,null)));
            Plan middle=new Plan(m,List.of(c("MIDDLE800",m,new long[]{0x424F82DL,0x200000L,0xFEDCBA9876543210L,0xFFD8L},0L,x->x.effect32(0xFFC8L,0xFFFFFFFE),null)));
            Plan tails=new Plan(m,List.of(
                c("TAIL500",m,new long[]{0x105C5D3D0L,0x105C5D330L},0L,null,null),
                c("TAIL4F0",m,new long[]{0x105C5D2E0L,0x105C5D330L,0xFFC8L},0L,null,null)));
            Plan fallback=new Plan(m,List.of());
            F800Api244.Ports child=F800IndexedTailBinding244.bind(0x100000000L,m,new TailPorts(tails),new LeafPorts(middle));
            F8a8Api242.Ports inner=F800FromF8Binding244.bind(m,child,new ExtendedF8Ports(fallback));
            F8a8Api242.Ports outer=F780FromF8Binding243.bind(m,new F780Ports(f780),inner);
            F8a8Target424F8A8.execute(m,outer,new F8a8Api242.Input(0x100000000L,0x200000L,new F8a8Api242.Scratch(0x10000L)));
            check(m.snapshot().equals(expected),"exact205+63+69allbytes/canaries");
            check(m.atomicCalls==1,"onlyincidentalexisting63atomic");
            complete(m,List.of(
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
                "C:ENTER:CHAIN:424f797:5",
                "R64:ffe0:ffd0",
                "R64:ffd0:200000",
                "R64:200088:10542f770",
                "A32:10542f770:ffffffff:0",
                "R32:10018:5",
                "C:LEAVE:CHAIN:424f7af:5:10018",
                "W64:ffc0:ffc8",
                "R32:ffcc:4",
                "C:TAIL500:CHAIN:105c5d3d0:105c5d330",
                "R64:fff0:ffd8",
                "R64:ffd8:105c5dcd8",
                "R64:ffe8:ffd0",
                "R64:105c5dcd8:fedcba9876543210",
                "R64:ffd0:200000",
                "C:MIDDLE800:CHAIN:424f82d:200000:fedcba9876543210:ffd8",
                "E32:ffc8:fffffffe",
                "R32:ffc8:fffffffe",
                "C:TAIL4F0:CHAIN:105c5d2e0:105c5d330:ffc8"
            ),"actual205 nestednewF800currentE",f780,middle,tails,fallback);
        }
        {
            Ram m=new Ram("PROTO"),foreign=new Ram("FOREIGN");
            RuntimeException middleFailure=new RuntimeException("passive-middle-marker");
            Plan passive=new Plan(m,List.of(
                c("F780_OLD",foreign,new long[]{0x501L,0xFEDCBA9876543210L,1L,2L,3L},0L,null,null),
                c("F800_OLD",foreign,new long[]{0x502L,4L,5L,6L,7L},0L,null,null),
                c("F780_NEW",foreign,new long[]{0x503L,8L,9L,10L,11L,0xFFFFFFFFFFFFFF00L},0L,null,null),
                c("F800_NEW",foreign,new long[]{0x504L,12L,13L,14L,15L,0x8000000000001234L},0L,null,null)));
            Plan legacy=new Plan(m,List.of(c("F800_OLD",foreign,new long[]{0x505L,16L,17L,18L,19L},0L,null,null)));
            Plan middle=new Plan(m,List.of(
                c("MIDDLE800",foreign,new long[]{0x506L,0xFEDCBA9876543210L,0x8123456789ABCDEFL,0x8000000000000001L},0L,null,null),
                c("MIDDLE800",foreign,new long[]{0x507L,20L,21L,0xFFFFFFFFFFFFFFFFL},0L,null,middleFailure)));
            Plan unused=new Plan(m,List.of());
            F800Api244.Ports tails=F800IndexedTailBinding244.bind(0x200000000L,m,new TailPorts(unused),new LeafPorts(middle));
            F8a8Api242.Ports active=F800FromF8Binding244.bind(m,tails,new ExtendedF8Ports(passive));
            F8a8Api242.Ports oldWrapper=F780FromF8Binding243.bind(m,new F780Ports(unused),new ExtendedF8Ports(passive));
            Map<Long,Byte> original=m.snapshot(),foreignOriginal=foreign.snapshot();
            rejectedRuntime(()->active.call424f800(foreign,0x424F96AL,0L,0L,0L,0L,0L),"activeforeign");
            rejectedRuntime(()->active.call424f800(m,0x424F969L,0L,0L,0L,0L,0L),"activesite");
            rejectedRuntime(()->tails.call4247ffc(foreign,0x424F817L,7),"tailenterforeign");
            rejectedRuntime(()->tails.call4247ffc(m,0x424F816L,7),"tailentersite");
            rejectedRuntime(()->tails.call4248050(foreign,0x424F835L,7,0xDEADL),"tailleaveforeign");
            rejectedRuntime(()->tails.call4248050(m,0x424F834L,7,0xDEADL),"tailleavesite");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty()&&passive.cursor==0&&middle.cursor==0&&unused.cursor==0,"allguardsbeforeallobservations");
            active.call424f780(foreign,0x501L,0xFEDCBA9876543210L,1L,2L,3L);
            active.call424f800(foreign,0x502L,4L,5L,6L,7L);
            active.call424f780(foreign,0x503L,8L,9L,10L,11L,0xFFFFFFFFFFFFFF00L);
            oldWrapper.call424f800(foreign,0x504L,12L,13L,14L,15L,0x8000000000001234L);
            new OldF8Ports(legacy).call424f800(foreign,0x505L,16L,17L,18L,19L,0xDEADL);
            tails.call424fa90(foreign,0x506L,0xFEDCBA9876543210L,0x8123456789ABCDEFL,0x8000000000000001L);
            sameException(()->tails.call424fa90(foreign,0x507L,20L,21L,0xFFFFFFFFFFFFFFFFL),middleFailure,"middlepassiveexactexception");
            check(m.snapshot().equals(original)&&foreign.snapshot().equals(foreignOriginal)&&foreign.trace.isEmpty(),"allpassiveguardsnoRAM");
            complete(m,List.of(
                "C:F780_OLD:FOREIGN:501:fedcba9876543210:1:2:3",
                "C:F800_OLD:FOREIGN:502:4:5:6:7",
                "C:F780_NEW:FOREIGN:503:8:9:a:b:ffffffffffffff00",
                "C:F800_NEW:FOREIGN:504:c:d:e:f:8000000000001234",
                "C:F800_OLD:FOREIGN:505:10:11:12:13",
                "C:MIDDLE800:FOREIGN:506:fedcba9876543210:8123456789abcdef:8000000000000001",
                "C:MIDDLE800:FOREIGN:507:14:15:ffffffffffffffff"
            ),"new244protocollegacyguardsfullbits",passive,legacy,middle,unused);
        }
    }
    public static void main(String[] ignored){direct69();actual205Protocol244();System.out.println("F800244_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
