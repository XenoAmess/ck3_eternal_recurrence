package org.xar.ck3.research.m3.manualallocator241;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.allocator241.Allocator241Api;
import org.xar.ck3.research.m3.allocator241.AllocatorReuse424E2EC241;
import org.xar.ck3.research.m3.allocator241.AllocatorFromFc74Binding241;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;

/** One finite source-derived manual Test; callback scripts only, no native or CPU model. */
public final class AllocatorReuseValidation241 {
    private AllocatorReuseValidation241() { }
    private static int checks,groups,events;
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static String h(long value){return Long.toUnsignedString(value,16);}
    private static long u32(int value){return Integer.toUnsignedLong(value);}
    private static String rw(String role,long address,long value){return role+":"+h(address)+":"+h(value);}
    private static String ev(String role,NativeTaskMemory memory,long... arguments){
        StringBuilder text=new StringBuilder("C:").append(role).append(':').append(((Ram)memory).name);
        for(long value:arguments)text.append(':').append(h(value));return text.toString();
    }
    private static final class Ram implements NativeTaskMemory {
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
    private static final class AllocPorts implements Allocator241Api.Ports {
        final Plan plan;AllocPorts(Plan plan){this.plan=plan;}
        @Override public long allocateImported(NativeTaskMemory m,long site,long target,long heap,int flags,long bytes){return plan.invoke("ALLOC",m,site,target,heap,u32(flags),bytes);}
        @Override public int retryGate(NativeTaskMemory m,long site){return (int)plan.invoke("GATE",m,site);}
        @Override public int retryCall(NativeTaskMemory m,long site,long bytes){return (int)plan.invoke("RETRY",m,site,bytes);}
        @Override public long failureCellAddress(NativeTaskMemory m,long site){return plan.invoke("CELL",m,site);}
    }
    private static final class FcPorts implements Fc74Api238.Ports {
        final Plan plan;FcPorts(Plan plan){this.plan=plan;}
        @Override public int callIat43da738(NativeTaskMemory m,long site,long target,int ecx){return (int)plan.invoke("FIRST",m,site,target,u32(ecx));}
        @Override public long call424e900(NativeTaskMemory m,long site,int ecx){return plan.invoke("E900",m,site,u32(ecx));}
        @Override public int call424e948(NativeTaskMemory m,long site,int ecx,long rdx){return (int)plan.invoke("E948",m,site,u32(ecx),rdx);}
        @Override public long call424e2ec(NativeTaskMemory m,long site,long rcx,long rdx){return plan.invoke("ALLOC_FALLBACK",m,site,rcx,rdx);}
        @Override public void call424e364(NativeTaskMemory m,long site,long rcx){plan.invoke("FREE",m,site,rcx);}
        @Override public void call424f8a8(NativeTaskMemory m,long site,long rcx){plan.invoke("INIT",m,site,rcx);}
        @Override public void callIat43da420(NativeTaskMemory m,long site,long target,int ecx){plan.invoke("LAST",m,site,target,u32(ecx));}
    }
    private static void rejectedRuntime(Runnable work,String label){try{work.run();}catch(RuntimeException expected){checks++;return;}throw new AssertionError("no RuntimeException rejection: "+label);}
    private static void sameException(Runnable work,RuntimeException expected,String label){try{work.run();}catch(RuntimeException actual){check(actual==expected,label);return;}throw new AssertionError("no original exception: "+label);}
    private static void complete(Ram memory,List<String> expected,String label,Plan... plans){
        check(memory.trace.equals(expected),label+" fulltrace\nexpected="+expected+"\nactual="+memory.trace);
        for(Plan plan:plans)plan.exhausted();groups++;events+=memory.trace.size();
    }
    private static void producerReuse241() {
        long base=0x100000000L,heap=base+0x5C5DE30L,slot=base+0x43DA768L;
        long heap1=0x123456789ABCDEF0L,target1=0x1122334455667788L;
        {
            Ram m=new Ram("zeroCount");m.seed64(heap,heap1);m.seed64(slot,target1);
            m.seed8(heap-1,0xA5);m.seed8(heap+8,0x5A);
            Map<Long,Byte> initial=m.snapshot();long resultBits=0xFEDCBA9876543210L;
            Plan p=new Plan(m,List.of(c("ALLOC",m,new long[]{0x424E341L,target1,heap1,8,1},resultBits,null,null)));
            List<String> expected=List.of(rw("R64",heap,heap1),rw("R64",slot,target1),ev("ALLOC",m,0x424E341L,target1,heap1,8,1));
            long result=AllocatorReuse424E2EC241.execute(m,new AllocPorts(p),new Allocator241Api.Input(base,0,Long.MIN_VALUE));
            check(result==resultBits,"count zero allocates one byte and preserves full64 result");
            check(m.snapshot().equals(initial),"zero count no RAM writes");
            complete(m,expected,"zero count bytes one",p);
        }
        {
            Ram m=new Ram("overflowZeroCell");m.seed64(0,0xAABBCCDD11223344L);m.seed8(-1L,0x6D);m.seed8(8,0xD6);
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<4;i++)finalBytes.put((long)i,(byte)(12>>>(8*i)));
            Plan p=new Plan(m,List.of(c("CELL",m,new long[]{0x424E34EL},0,null,null)));
            List<String> expected=List.of(ev("CELL",m,0x424E34EL),rw("W32",0,12));
            long result=AllocatorReuse424E2EC241.execute(m,new AllocPorts(p),new Allocator241Api.Input(base,-1L,1));
            check(result==0,"unsigned overflow returns zero");
            check(m.snapshot().equals(finalBytes),"failure pointer zero single DWORD preserves high DWORD and canaries");
            complete(m,expected,"overflow no heap or IAT read",p);
        }
        {
            Ram m=new Ram("retryFresh");m.seed64(heap,heap1);m.seed64(slot,target1);
            m.seed8(heap-1,0xC3);m.seed8(heap+8,0x3C);m.seed8(slot-1,0x5E);m.seed8(slot+8,0xE5);
            long target2=0xFEDCBA9801234567L;
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<8;i++){finalBytes.put(heap+i,(byte)0);finalBytes.put(slot+i,(byte)(target2>>>(8*i)));}
            Plan p=new Plan(m,List.of(
                c("ALLOC",m,new long[]{0x424E341L,target1,heap1,8,15},0,r->{r.effect64(heap,0);r.effect64(slot,target2);},null),
                c("GATE",m,new long[]{0x424E31DL},0x80000000L,null,null),
                c("RETRY",m,new long[]{0x424E329L,15},0xFFFFFFFFL,null,null),
                c("ALLOC",m,new long[]{0x424E341L,target2,0,8,15},-1L,null,null)));
            List<String> expected=List.of(
                rw("R64",heap,heap1),rw("R64",slot,target1),ev("ALLOC",m,0x424E341L,target1,heap1,8,15),
                rw("E64",heap,0),rw("E64",slot,target2),ev("GATE",m,0x424E31DL),ev("RETRY",m,0x424E329L,15),
                rw("R64",heap,0),rw("R64",slot,target2),ev("ALLOC",m,0x424E341L,target2,0,8,15));
            long result=AllocatorReuse424E2EC241.execute(m,new AllocPorts(p),new Allocator241Api.Input(base,3,5));
            check(result==-1L,"retry success preserves raw all-ones result");
            check(m.snapshot().equals(finalBytes),"retry exact opaque mutations and canaries");
            complete(m,expected,"fresh actual heap and IAT every attempt",p);
        }
        for(int scenario=0;scenario<2;scenario++) {
            boolean retryZero=scenario==1;long actualHeap=retryZero?7:3,actualTarget=retryZero?8:4;
            long bytes=retryZero?8:4,cell=retryZero?0x9000:0x8000;
            Ram m=new Ram(retryZero?"retryZero":"gateZero");m.seed64(heap,actualHeap);m.seed64(slot,actualTarget);
            m.seed64(cell,0x8877665544332211L);m.seed8(cell-1,0xA6);m.seed8(cell+8,0x6A);
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<4;i++)finalBytes.put(cell+i,(byte)(12>>>(8*i)));
            List<Call> calls=new ArrayList<>();
            calls.add(c("ALLOC",m,new long[]{0x424E341L,actualTarget,actualHeap,8,bytes},0,null,null));
            calls.add(c("GATE",m,new long[]{0x424E31DL},retryZero?1:0,null,null));
            if(retryZero)calls.add(c("RETRY",m,new long[]{0x424E329L,bytes},0,null,null));
            calls.add(c("CELL",m,new long[]{0x424E34EL},cell,null,null));
            Plan p=new Plan(m,calls);
            List<String> expected=new ArrayList<>(List.of(
                rw("R64",heap,actualHeap),rw("R64",slot,actualTarget),ev("ALLOC",m,0x424E341L,actualTarget,actualHeap,8,bytes),ev("GATE",m,0x424E31DL)));
            if(retryZero)expected.add(ev("RETRY",m,0x424E329L,bytes));
            expected.add(ev("CELL",m,0x424E34EL));expected.add(rw("W32",cell,12));
            long result=AllocatorReuse424E2EC241.execute(m,new AllocPorts(p),new Allocator241Api.Input(base,retryZero?2:1,4));
            check(result==0,"terminal retry role returns zero");
            check(m.snapshot().equals(finalBytes),"terminal failure exact DWORD width and final bytes");
            complete(m,expected,retryZero?"retry zero failure":"gate zero failure",p);
        }
        {
            Ram m=new Ram("gateThrow");m.seed64(heap,9);m.seed64(slot,10);m.seed8(heap-1,0xD7);m.seed8(heap+8,0x7D);
            Map<Long,Byte> initial=m.snapshot();RuntimeException marker=new RuntimeException("opaque gate marker");
            Plan p=new Plan(m,List.of(
                c("ALLOC",m,new long[]{0x424E341L,10,9,8,1},0,null,null),
                c("GATE",m,new long[]{0x424E31DL},0,null,marker)));
            List<String> expected=List.of(rw("R64",heap,9),rw("R64",slot,10),ev("ALLOC",m,0x424E341L,10,9,8,1),ev("GATE",m,0x424E31DL));
            sameException(()->AllocatorReuse424E2EC241.execute(m,new AllocPorts(p),new Allocator241Api.Input(base,1,0)),marker,"gate original exception identity");
            check(m.snapshot().equals(initial),"opaque exception prefix has no failure flush");
            complete(m,expected,"gate throw no retry cell write or replay",p);
        }
    }
    private static void actualFc74Protocol241() {
        {
            long base=0x200000000L,heap=base+0x5C5DE30L,slot=base+0x43DA768L,index=base+0x542F328L;
            long first=base+0x43DA738L,last=base+0x43DA420L;
            long firstTarget=0x1020304050607080L,lastTarget=0x8877665544332211L;
            long heap1=0x123456789ABCDEF0L,heap2=0xFEDCBA9876543210L;
            long target1=0x1122334455667788L,target2=0x9988776655443322L,block=0x8765432100000011L;
            int entry=0x81234567,saved=0xCAFE8001;
            Ram m=new Ram("actualFc74");m.seed64(heap,heap1);m.seed64(slot,target1);m.seed32(index,-1);
            m.seed64(first,firstTarget);m.seed64(last,lastTarget);
            m.seed8(index-1,0x8A);m.seed8(index+4,0xA8);m.seed8(heap-1,0x9B);m.seed8(heap+8,0xB9);
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<8;i++){finalBytes.put(heap+i,(byte)(heap2>>>(8*i)));finalBytes.put(slot+i,(byte)(target2>>>(8*i)));}
            for(int i=0;i<4;i++)finalBytes.put(index+i,(byte)(9>>>(8*i)));
            Plan childPlan=new Plan(m,List.of(
                c("ALLOC",m,new long[]{0x424E341L,target1,heap1,8,0x3C8},0,r->{r.effect64(heap,heap2);r.effect64(slot,target2);},null),
                c("GATE",m,new long[]{0x424E31DL},0xFFFFFFFFL,null,null),
                c("RETRY",m,new long[]{0x424E329L,0x3C8},0x80000000L,null,null),
                c("ALLOC",m,new long[]{0x424E341L,target2,heap2,8,0x3C8},block,r->r.effect32(index,9),null)));
            Plan fallbackPlan=new Plan(m,List.of(
                c("FIRST",m,new long[]{0x424FC83L,firstTarget,u32(entry)},u32(saved),null,null),
                c("E948",m,new long[]{0x424FCB9L,0xFFFFFFFFL,-1L},1,null,null),
                c("E948",m,new long[]{0x424FCF2L,9,block},1,null,null),
                c("INIT",m,new long[]{0x424FD10L,block},0,null,null),
                c("FREE",m,new long[]{0x424FD17L,0},0,null,null),
                c("LAST",m,new long[]{0x424FD21L,lastTarget,u32(saved)},0,null,null)));
            List<String> expected=List.of(
                rw("R64",first,firstTarget),ev("FIRST",m,0x424FC83L,firstTarget,u32(entry)),rw("R32",index,0xFFFFFFFFL),
                ev("E948",m,0x424FCB9L,0xFFFFFFFFL,-1L),
                rw("R64",heap,heap1),rw("R64",slot,target1),ev("ALLOC",m,0x424E341L,target1,heap1,8,0x3C8),
                rw("E64",heap,heap2),rw("E64",slot,target2),ev("GATE",m,0x424E31DL),ev("RETRY",m,0x424E329L,0x3C8),
                rw("R64",heap,heap2),rw("R64",slot,target2),ev("ALLOC",m,0x424E341L,target2,heap2,8,0x3C8),
                rw("E32",index,9),rw("R32",index,9),ev("E948",m,0x424FCF2L,9,block),
                ev("INIT",m,0x424FD10L,block),ev("FREE",m,0x424FD17L,0),rw("R64",last,lastTarget),ev("LAST",m,0x424FD21L,lastTarget,u32(saved)));
            Fc74Api238.Ports bound=AllocatorFromFc74Binding241.bind(base,m,new AllocPorts(childPlan),new FcPorts(fallbackPlan));
            long result=Fc74Target424FC74.execute(m,bound,new Fc74Api238.Input(base,entry));
            check(result==block,"actual caller allocated full64 block survives final result");
            check(m.snapshot().equals(finalBytes),"actual caller exact opaque effects and byte canaries");
            complete(m,expected,"real FCCC edge and fresh caller index",childPlan,fallbackPlan);
        }
        {
            Ram m=new Ram("protocolCaptured"),foreign=new Ram("protocolForeign");
            m.seed64(0xAB00,0x0123456789ABCDEFL);foreign.seed64(0xCD00,0xFEDCBA9876543210L);
            Map<Long,Byte> initial=m.snapshot(),foreignInitial=foreign.snapshot();
            Plan childPlan=new Plan(m,List.of());RuntimeException marker=new RuntimeException("passive original marker");
            String[] roles={"FIRST","E900","E948","FREE","INIT","LAST"};
            long[][] args={{0x901,0x8877665544332211L,0xFFFFFFFFL},{0x902,0x80000000L},
                {0x903,0xFEDCBA98L,0x876543210FEDCBA9L},{0x904,0xFEDCBA9876543210L},
                {0x905,0x123456789ABCDEF0L},{0x906,0x8123456789ABCDEFL,0x81234567L}};
            long[] returned={0x80000001L,0x9988776655443322L,0xFEDCBA98L,0,0,0};
            List<Call> calls=new ArrayList<>();List<String> expected=new ArrayList<>();
            for(int i=0;i<roles.length;i++){
                calls.add(c(roles[i],foreign,args[i],returned[i],null,null));calls.add(c(roles[i],foreign,args[i],0,null,marker));
                expected.add(ev(roles[i],foreign,args[i]));expected.add(ev(roles[i],foreign,args[i]));
            }
            Plan fallbackPlan=new Plan(m,calls);AllocPorts child=new AllocPorts(childPlan);FcPorts fallback=new FcPorts(fallbackPlan);
            Fc74Api238.Ports bound=AllocatorFromFc74Binding241.bind(0x300000000L,m,child,fallback);
            rejectedRuntime(()->bound.call424e2ec(foreign,0x424FCCCL,1,0x3C8),"active foreign Memory");
            rejectedRuntime(()->bound.call424e2ec(m,0x424FCCDL,1,0x3C8),"active wrong site");
            rejectedRuntime(()->AllocatorFromFc74Binding241.bind(0,null,child,fallback),"null captured Memory");
            rejectedRuntime(()->AllocatorFromFc74Binding241.bind(0,m,null,fallback),"null child");
            rejectedRuntime(()->AllocatorFromFc74Binding241.bind(0,m,child,null),"null fallback");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty(),"guards zero Memory and callback events");
            check(childPlan.cursor==0&&fallbackPlan.cursor==0,"guards zero child and fallback calls");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"guards exact bytes");
            check(bound.callIat43da738(foreign,0x901,0x8877665544332211L,-1)==0x80000001,"passive FIRST intbits");
            sameException(()->bound.callIat43da738(foreign,0x901,0x8877665544332211L,-1),marker,"FIRST exact exception");
            check(bound.call424e900(foreign,0x902,0x80000000)==0x9988776655443322L,"passive E900 full64");
            sameException(()->bound.call424e900(foreign,0x902,0x80000000),marker,"E900 exact exception");
            check(bound.call424e948(foreign,0x903,0xFEDCBA98,0x876543210FEDCBA9L)==0xFEDCBA98,"passive E948 intbits");
            sameException(()->bound.call424e948(foreign,0x903,0xFEDCBA98,0x876543210FEDCBA9L),marker,"E948 exact exception");
            bound.call424e364(foreign,0x904,0xFEDCBA9876543210L);
            sameException(()->bound.call424e364(foreign,0x904,0xFEDCBA9876543210L),marker,"FREE exact exception");
            bound.call424f8a8(foreign,0x905,0x123456789ABCDEF0L);
            sameException(()->bound.call424f8a8(foreign,0x905,0x123456789ABCDEF0L),marker,"INIT exact exception");
            bound.callIat43da420(foreign,0x906,0x8123456789ABCDEFL,0x81234567);
            sameException(()->bound.callIat43da420(foreign,0x906,0x8123456789ABCDEFL,0x81234567),marker,"LAST exact exception");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"passive exact bytes unchanged");
            check(foreign.trace.isEmpty(),"passive no extra Memory access");
            complete(m,expected,"active guards and six exact passive methods",childPlan,fallbackPlan);
        }
    }
    public static void main(String[] ignored){producerReuse241();actualFc74Protocol241();System.out.println("ALLOCATOR241_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
