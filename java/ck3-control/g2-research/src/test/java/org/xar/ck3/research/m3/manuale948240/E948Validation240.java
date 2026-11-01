package org.xar.ck3.research.m3.manuale948240;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.e948240.E948Api240;
import org.xar.ck3.research.m3.e948240.E948Target424E948;
import org.xar.ck3.research.m3.e948240.E948FromFc74Binding240;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;

/** One finite source-derived manual Test; callback scripts only, no native or CPU model. */
public final class E948Validation240 {
    private E948Validation240() { }
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
    private static final class LeafPorts implements E948Api240.Ports {
        final Plan plan;LeafPorts(Plan plan){this.plan=plan;}
        @Override public long call424e448(NativeTaskMemory m,long site,int ecx,long rdx,long r8,long r9){return plan.invoke("LOOKUP",m,site,u32(ecx),rdx,r8,r9);}
        @Override public long callIat43dbba8(NativeTaskMemory m,long site,long target,long rax,int ecx,long rdx){return plan.invoke("NONZERO",m,site,target,rax,u32(ecx),rdx);}
        @Override public long callIat43da470(NativeTaskMemory m,long site,long target,long rax,int ecx,long rdx){return plan.invoke("ZERO",m,site,target,rax,u32(ecx),rdx);}
    }
    private static final class FcPorts implements Fc74Api238.Ports {
        final Plan plan;FcPorts(Plan plan){this.plan=plan;}
        @Override public int callIat43da738(NativeTaskMemory m,long site,long target,int ecx){return (int)plan.invoke("FIRST",m,site,target,u32(ecx));}
        @Override public long call424e900(NativeTaskMemory m,long site,int ecx){return plan.invoke("E900",m,site,u32(ecx));}
        @Override public int call424e948(NativeTaskMemory m,long site,int ecx,long rdx){return (int)plan.invoke("E948_FALLBACK",m,site,u32(ecx),rdx);}
        @Override public long call424e2ec(NativeTaskMemory m,long site,long rcx,long rdx){return plan.invoke("ALLOC",m,site,rcx,rdx);}
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
    private static void producer240() {
        {
            long base=0x100000000L,slot=base+0x43DBBA8L;
            int ecx=0x80000001;long rdx=0xDEADBEEF01234567L;
            long lookup=0x100000000L,target=0xFEDCBA9876543210L,post=0x8877665500000000L;
            Ram m=new Ram("pNonzero");m.seed64(slot,0x12345678L);
            m.seed64(slot-8,0x1020304050607080L);m.seed64(slot+8,0x8877665544332211L);
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<8;i++)finalBytes.put(slot+i,(byte)(target>>>(8*i)));
            Plan p=new Plan(m,List.of(
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},lookup,r->r.effect64(slot,target),null),
                c("NONZERO",m,new long[]{0x424E980L,target,lookup,u32(ecx),rdx},post,null,null)));
            List<String> expected=List.of(
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("E64",slot,target),rw("R64",slot,target),
                ev("NONZERO",m,0x424E980L,target,lookup,u32(ecx),rdx));
            long result=E948Target424E948.execute(m,new LeafPorts(p),new E948Api240.Input(base,ecx,rdx));
            check(result==post,"nonzero full64 selected postRAX");
            check(m.snapshot().equals(finalBytes),"nonzero exact final bytes and canaries");
            complete(m,expected,"nonzero fresh selected IAT",p);
        }
        {
            long base=0x200000000L,slot=base+0x43DA470L;
            long target=0x8000000012345678L,post=0x76543210FEDCBA98L;
            Ram m=new Ram("pZero");m.seed64(slot,target);
            m.seed64(slot-8,0x1122334455667788L);m.seed64(slot+8,0xFF00112233445566L);
            Map<Long,Byte> initial=m.snapshot();
            Plan p=new Plan(m,List.of(
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},0,null,null),
                c("ZERO",m,new long[]{0x424E988L,target,0,0xFFFFFFFFL,-1L},post,null,null)));
            List<String> expected=List.of(
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("R64",slot,target),ev("ZERO",m,0x424E988L,target,0,0xFFFFFFFFL,-1L));
            long result=E948Target424E948.execute(m,new LeafPorts(p),new E948Api240.Input(base,-1,-1L));
            check(result==post,"zero path full64 selected postRAX");
            check(m.snapshot().equals(initial),"zero unchanged exact mapped bytes");
            complete(m,expected,"zero chosen slot only",p);
        }
        {
            long base=0x100000000L;Ram m=new Ram("pFirstThrow");
            RuntimeException marker=new RuntimeException("opaque first marker");
            Plan p=new Plan(m,List.of(c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},0,null,marker)));
            List<String> expected=List.of(ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L));
            sameException(()->E948Target424E948.execute(m,new LeafPorts(p),new E948Api240.Input(base,7,0x8765432101234567L)),marker,"first original exception object");
            check(m.snapshot().isEmpty(),"first exception no RAM effects");
            complete(m,expected,"first throw before any RAM read",p);
        }
        {
            long base=0x200000000L,slot=base+0x43DBBA8L,target=0x123456789ABCDEF0L;
            long rdx=0xFEDCBA9876543210L;Ram m=new Ram("pSelectedThrow");
            m.seed64(slot,target);m.seed64(slot-8,0x0807060504030201L);m.seed64(slot+8,0x0102030405060708L);
            Map<Long,Byte> initial=m.snapshot();
            RuntimeException marker=new RuntimeException("opaque selected marker");
            Plan p=new Plan(m,List.of(
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},-1L,null,null),
                c("NONZERO",m,new long[]{0x424E980L,target,-1L,3,rdx},0,null,marker)));
            List<String> expected=List.of(
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("R64",slot,target),ev("NONZERO",m,0x424E980L,target,-1L,3,rdx));
            sameException(()->E948Target424E948.execute(m,new LeafPorts(p),new E948Api240.Input(base,3,rdx)),marker,"selected original exception object");
            check(m.snapshot().equals(initial),"selected exception no extra writes");
            complete(m,expected,"selected throw after fresh IAT",p);
        }
    }
    private static void fc74ChainProtocol240() {
        {
            long base=0x300000000L,first=base+0x43DA738L,last=base+0x43DA420L,index=base+0x542F328L;
            long nonzero=base+0x43DBBA8L,zero=base+0x43DA470L;
            long firstTarget=0x123456789ABCDEF0L,lastTarget=0x76543210FEDCBA98L;
            long newTarget=0xFEDCBA9801234567L,zeroTarget=0x9988776655443322L;
            int entry=0x81234567,saved=0x80000005;
            Ram m=new Ram("allocFail");
            m.seed64(first,firstTarget);m.seed64(last,lastTarget);m.seed32(index,-1);
            m.seed64(nonzero,0x13579BDFL);m.seed64(zero,zeroTarget);
            m.seed8(index-1,0xA5);m.seed8(index+4,0x5A);
            m.seed8(nonzero-1,0xC3);m.seed8(nonzero+8,0x3C);
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<4;i++)finalBytes.put(index+i,(byte)(5>>>(8*i)));
            for(int i=0;i<8;i++)finalBytes.put(nonzero+i,(byte)(newTarget>>>(8*i)));
            Plan p=new Plan(m,List.of(
                c("FIRST",m,new long[]{0x424FC83L,firstTarget,u32(entry)},u32(saved),null,null),
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},0x100000000L,r->r.effect64(nonzero,newTarget),null),
                c("NONZERO",m,new long[]{0x424E980L,newTarget,0x100000000L,0xFFFFFFFFL,-1L},0x1111111100000001L,null,null),
                c("ALLOC",m,new long[]{0x424FCCCL,1,0x3C8},0,r->r.effect32(index,5),null),
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},0,null,null),
                c("ZERO",m,new long[]{0x424E988L,zeroTarget,0,5,0},0xDEADBEEF00000001L,null,null),
                c("FREE",m,new long[]{0x424FCE8L,0},0,null,null),
                c("LAST",m,new long[]{0x424FD21L,lastTarget,u32(saved)},0,null,null)));
            List<String> expected=List.of(
                rw("R64",first,firstTarget),ev("FIRST",m,0x424FC83L,firstTarget,u32(entry)),rw("R32",index,0xFFFFFFFFL),
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("E64",nonzero,newTarget),rw("R64",nonzero,newTarget),
                ev("NONZERO",m,0x424E980L,newTarget,0x100000000L,0xFFFFFFFFL,-1L),
                ev("ALLOC",m,0x424FCCCL,1,0x3C8),rw("E32",index,5),rw("R32",index,5),
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("R64",zero,zeroTarget),ev("ZERO",m,0x424E988L,zeroTarget,0,5,0),
                ev("FREE",m,0x424FCE8L,0),rw("R64",last,lastTarget),ev("LAST",m,0x424FD21L,lastTarget,u32(saved)));
            Fc74Api238.Ports bound=E948FromFc74Binding240.bind(base,m,new LeafPorts(p),new FcPorts(p));
            long result=Fc74Target424FC74.execute(m,bound,new Fc74Api238.Input(base,entry));
            check(result==0,"allocation failure caller final return");
            check(m.snapshot().equals(finalBytes),"allocation failure exact bytes and canaries");
            complete(m,expected,"actual B9 then E1 allocation failure",p);
        }
        {
            long base=0x400000000L,first=base+0x43DA738L,last=base+0x43DA420L,index=base+0x542F328L;
            long nonzero=base+0x43DBBA8L,zero=base+0x43DA470L;
            long firstTarget=0x1122334455667788L,lastTarget=0x8877665544332211L;
            long nonzeroTarget=0x76543210FEDCBA98L,zeroTarget=0xDEADBEEF00000001L,block=0xFEDCBA9876543210L;
            int entry=0xF1234567,saved=0x12345678;
            Ram m=new Ram("associationFail");
            m.seed64(first,firstTarget);m.seed64(last,lastTarget);m.seed32(index,1);
            m.seed64(nonzero,nonzeroTarget);m.seed64(zero,zeroTarget);
            m.seed8(index-1,0x6D);m.seed8(index+4,0xD6);
            m.seed8(zero-1,0x7E);m.seed8(zero+8,0xE7);
            Map<Long,Byte> finalBytes=new HashMap<>(m.snapshot());
            for(int i=0;i<4;i++)finalBytes.put(index+i,(byte)(8>>>(8*i)));
            Plan p=new Plan(m,List.of(
                c("FIRST",m,new long[]{0x424FC83L,firstTarget,u32(entry)},u32(saved),null,null),
                c("E900",m,new long[]{0x424FC96L,1},0,r->r.effect32(index,6),null),
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},0,null,null),
                c("ZERO",m,new long[]{0x424E988L,zeroTarget,0,6,-1L},0xAAAAAAAA00000001L,null,null),
                c("ALLOC",m,new long[]{0x424FCCCL,1,0x3C8},block,r->r.effect32(index,7),null),
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},Long.MIN_VALUE,null,null),
                c("NONZERO",m,new long[]{0x424E980L,nonzeroTarget,Long.MIN_VALUE,7,block},0xBBBBBBBB00000000L,r->r.effect32(index,8),null),
                c("LOOKUP",m,new long[]{0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L},0,null,null),
                c("ZERO",m,new long[]{0x424E988L,zeroTarget,0,8,0},0xCCCCCCCCFFFFFFFFL,null,null),
                c("FREE",m,new long[]{0x424FCE8L,block},0,null,null),
                c("LAST",m,new long[]{0x424FD21L,lastTarget,u32(saved)},0,null,null)));
            List<String> expected=List.of(
                rw("R64",first,firstTarget),ev("FIRST",m,0x424FC83L,firstTarget,u32(entry)),rw("R32",index,1),
                ev("E900",m,0x424FC96L,1),rw("E32",index,6),rw("R32",index,6),
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("R64",zero,zeroTarget),ev("ZERO",m,0x424E988L,zeroTarget,0,6,-1L),
                ev("ALLOC",m,0x424FCCCL,1,0x3C8),rw("E32",index,7),rw("R32",index,7),
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("R64",nonzero,nonzeroTarget),ev("NONZERO",m,0x424E980L,nonzeroTarget,Long.MIN_VALUE,7,block),
                rw("E32",index,8),rw("R32",index,8),
                ev("LOOKUP",m,0x424E971L,6,base+0x4420C60L,base+0x4426F30L,base+0x4426F38L),
                rw("R64",zero,zeroTarget),ev("ZERO",m,0x424E988L,zeroTarget,0,8,0),
                ev("FREE",m,0x424FCE8L,block),rw("R64",last,lastTarget),ev("LAST",m,0x424FD21L,lastTarget,u32(saved)));
            Fc74Api238.Ports bound=E948FromFc74Binding240.bind(base,m,new LeafPorts(p),new FcPorts(p));
            long result=Fc74Target424FC74.execute(m,bound,new Fc74Api238.Input(base,entry));
            check(result==0,"association failure caller final return");
            check(m.snapshot().equals(finalBytes),"association failure exact bytes and canaries");
            complete(m,expected,"actual B9 F2 D03 association failure",p);
        }
        {
            Ram m=new Ram("guardCaptured"),foreign=new Ram("foreignPassive");
            m.seed64(0xABC0,0x1234567890ABCDEFL);foreign.seed64(0xDEF0,0xFEDCBA0987654321L);
            Map<Long,Byte> initial=m.snapshot(),foreignInitial=foreign.snapshot();
            Plan childPlan=new Plan(m,List.of());
            RuntimeException marker=new RuntimeException("passive original marker");
            String[] roles={"FIRST","E900","ALLOC","FREE","INIT","LAST"};
            long[][] args={{0x901,0xF0E0D0C0B0A09080L,0xFFFFFFFFL},{0x902,0x80000000L},
                {0x903,0xFEDCBA9876543210L,0x8000000000000001L},{0x904,0x123456789ABCDEF0L},
                {0x905,0x876543210FEDCBA9L},{0x906,0x8123456789ABCDEFL,0x81234567L}};
            long[] returns={0x80000001L,0xFEDCBA9876543210L,0x8877665544332211L,0,0,0};
            List<Call> calls=new ArrayList<>();List<String> expected=new ArrayList<>();
            for(int i=0;i<roles.length;i++){
                calls.add(c(roles[i],foreign,args[i],returns[i],null,null));
                calls.add(c(roles[i],foreign,args[i],0,null,marker));
                expected.add(ev(roles[i],foreign,args[i]));expected.add(ev(roles[i],foreign,args[i]));
            }
            Plan fallbackPlan=new Plan(m,calls);LeafPorts child=new LeafPorts(childPlan);FcPorts fallback=new FcPorts(fallbackPlan);
            Fc74Api238.Ports bound=E948FromFc74Binding240.bind(0x500000000L,m,child,fallback);
            rejectedRuntime(()->bound.call424e948(foreign,0x424FCB9L,9,-1L),"active foreign Memory");
            rejectedRuntime(()->bound.call424e948(m,0x424FCBAL,9,-1L),"active wrong site");
            rejectedRuntime(()->E948FromFc74Binding240.bind(0,m,null,fallback),"factory null child");
            rejectedRuntime(()->E948FromFc74Binding240.bind(0,null,child,fallback),"factory null Memory");
            rejectedRuntime(()->E948FromFc74Binding240.bind(0,m,child,null),"factory null fallback");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty(),"guard zero Memory or port effects");
            check(childPlan.cursor==0&&fallbackPlan.cursor==0,"guard zero child/fallback consumption");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"guard exact bytes");
            check(bound.callIat43da738(foreign,0x901,0xF0E0D0C0B0A09080L,-1)==0x80000001,"passive FIRST exact intbits");
            sameException(()->bound.callIat43da738(foreign,0x901,0xF0E0D0C0B0A09080L,-1),marker,"FIRST exception identity");
            check(bound.call424e900(foreign,0x902,0x80000000)==0xFEDCBA9876543210L,"passive E900 full64");
            sameException(()->bound.call424e900(foreign,0x902,0x80000000),marker,"E900 exception identity");
            check(bound.call424e2ec(foreign,0x903,0xFEDCBA9876543210L,0x8000000000000001L)==0x8877665544332211L,"passive ALLOC full64");
            sameException(()->bound.call424e2ec(foreign,0x903,0xFEDCBA9876543210L,0x8000000000000001L),marker,"ALLOC exception identity");
            bound.call424e364(foreign,0x904,0x123456789ABCDEF0L);
            sameException(()->bound.call424e364(foreign,0x904,0x123456789ABCDEF0L),marker,"FREE exception identity");
            bound.call424f8a8(foreign,0x905,0x876543210FEDCBA9L);
            sameException(()->bound.call424f8a8(foreign,0x905,0x876543210FEDCBA9L),marker,"INIT exception identity");
            bound.callIat43da420(foreign,0x906,0x8123456789ABCDEFL,0x81234567);
            sameException(()->bound.callIat43da420(foreign,0x906,0x8123456789ABCDEFL,0x81234567),marker,"LAST exception identity");
            check(m.snapshot().equals(initial)&&foreign.snapshot().equals(foreignInitial),"passive all bytes unchanged");
            check(foreign.trace.isEmpty(),"passive no Memory reads or writes");
            complete(m,expected,"guards and six passive normal/exception delegates",childPlan,fallbackPlan);
        }
    }
    public static void main(String[] ignored){producer240();fc74ChainProtocol240();System.out.println("E948240_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
