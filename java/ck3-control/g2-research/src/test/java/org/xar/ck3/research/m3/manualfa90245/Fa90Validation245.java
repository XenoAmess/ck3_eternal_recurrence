package org.xar.ck3.research.m3.manualfa90245;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f800244.F800Api244;
import org.xar.ck3.research.m3.f800244.F800Target424F800;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;
import org.xar.ck3.research.m3.fa90245.Fa90FromF800Binding245;

/** Finite source-only manual witness: byte RAM, scripted opaque calls, no CPU or Native execution. */
public final class Fa90Validation245 {
    private Fa90Validation245(){ }
    private static int checks,groups,events;
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static String h(long value){return Long.toUnsignedString(value,16);}
    private static String rw(String kind,long address,long value){return kind+":"+h(address)+":"+h(value);}
    private static String ev(String role,F8a8Api242.Memory m,Object... arguments){
        StringBuilder s=new StringBuilder("C:").append(role).append(':').append(((Ram)m).name);
        for(Object a:arguments){s.append(':');if(a instanceof Long bits)s.append(h(bits));
            else if(a instanceof OptionalLong known)s.append(known.isPresent()?"k"+h(known.getAsLong()):"?");
            else throw new AssertionError("fixture unknown argument type");}return s.toString();
    }
    private static final class Ram implements F8a8Api242.Memory {
        final String name;final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
        Ram(String name){this.name=name;}
        private long raw(long a,int width){long value=0;for(int n=0;n<width;n++){Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unmapped "+name+":"+h(a+n));value|=(b.longValue()&255L)<<(8*n);}return value;}
        private void store(long a,int width,long value){for(int n=0;n<width;n++)bytes.put(a+n,(byte)(value>>>(8*n)));}
        void seed8(long a,int value){check((value&~255)==0,"seed8width");store(a,1,value);}
        void seed32(long a,int value){store(a,4,Integer.toUnsignedLong(value));}
        void seed64(long a,long value){store(a,8,value);}
        void effect32(long a,int value){trace.add(rw("E32",a,Integer.toUnsignedLong(value)));store(a,4,Integer.toUnsignedLong(value));}
        void effect64(long a,long value){trace.add(rw("E64",a,value));store(a,8,value);}
        Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
        @Override public long readPointer(long a){long value=raw(a,8);trace.add(rw("R64",a,value));return value;}
        @Override public int readInt32(long a){long value=raw(a,4);trace.add(rw("R32",a,value));return (int)value;}
        @Override public void writeInt64(long a,long value){trace.add(rw("W64",a,value));store(a,8,value);}
        @Override public void writeInt32(long a,int value){trace.add(rw("W32",a,Integer.toUnsignedLong(value)));store(a,4,Integer.toUnsignedLong(value));}
        @Override public void writeInt16(long a,int value){trace.add(rw("W16",a,value&65535L));store(a,2,value);}
    }
    private record Call(String role,F8a8Api242.Memory memory,Object[] arguments,Consumer<Ram> effect,RuntimeException failure){ }
    private static Call c(String role,F8a8Api242.Memory m,Object[] arguments,Consumer<Ram> effect,RuntimeException failure){return new Call(role,m,arguments,effect,failure);}
    private static final class Plan {
        final Ram recorder;final List<Call> calls;int cursor;
        Plan(Ram recorder,List<Call> calls){this.recorder=recorder;this.calls=List.copyOf(calls);}
        void invoke(String role,F8a8Api242.Memory memory,Object... args){
            check(cursor<calls.size(),"unexpected opaque "+role);Call call=calls.get(cursor++);
            check(call.role().equals(role),"opaque role");check(call.memory()==memory,"same actual Memory");
            check(Arrays.equals(call.arguments(),args),"all actual typed arguments including OptionalLong knownness");
            recorder.trace.add(ev(role,memory,args));if(call.effect()!=null)call.effect().accept(recorder);
            if(call.failure()!=null)throw call.failure();
        }
        void exhausted(){check(cursor==calls.size(),"opaque script exhausted");}
    }
    private static final class LeafPorts implements Fa90Api245.Ports {
        final Plan plan;LeafPorts(Plan plan){this.plan=plan;}
        @Override public void call42568fc(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){plan.invoke("FIRST",m,site,rcx,rdx,rax);}
        @Override public void call42566fc(F8a8Api242.Memory m,long site,long rcx,long rax){plan.invoke("SECOND",m,site,rcx,rax);}
        @Override public void call4256670(F8a8Api242.Memory m,long site,long rcx,OptionalLong rdx,OptionalLong rax){
            check(rdx!=null&&rax!=null,"nonnull knownness");plan.invoke("THIRD",m,site,rcx,rdx,rax);
        }
    }
    private static final class F800Ports implements F800Api244.Ports {
        final Plan plan;F800Ports(Plan plan){this.plan=plan;}
        @Override public void call4247ffc(F8a8Api242.Memory m,long site,int ecx){plan.invoke("ENTER800",m,site,Integer.toUnsignedLong(ecx));}
        @Override public void call4248050(F8a8Api242.Memory m,long site,int ecx,long rbx){plan.invoke("LEAVE800",m,site,Integer.toUnsignedLong(ecx),rbx);}
        @Override public void call424fa90(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){plan.invoke("FA90_PASSIVE",m,site,rcx,rdx,rax);}
    }
    private static void expectedWrite(Map<Long,Byte> bytes,long a,int width,long value){for(int n=0;n<width;n++)bytes.put(a+n,(byte)(value>>>(8*n)));}
    private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException actual){check(actual==marker,label);return;}throw new AssertionError("missing exception "+label);}
    private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException actual){checks++;return;}throw new AssertionError("missing RuntimeException "+label);}
    private static void complete(Ram m,List<String> trace,String label,Plan... plans){check(m.trace.equals(trace),label+" fulltrace expected="+trace+" actual="+m.trace);for(Plan plan:plans)plan.exhausted();groups++;events+=m.trace.size();}
    private static void direct103(){
        {
            Ram m=new Ram("A");
            m.seed64(0x2090L,0x0L);
            m.seed8(0x208FL,0xA5);m.seed8(0x2098L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x2090L,8,0x9000L);
            Plan plan=new Plan(m,List.of(c("THIRD",m,new Object[]{0x424FAE7L,0x9000L,OptionalLong.of(0x9000L),OptionalLong.of(0L)},null,null)));
            Fa90Target424FA90.execute(m,new LeafPorts(plan),new Fa90Api245.Input(0x100000000L,0x2000L,0x9000L,0x0L));
            check(m.snapshot().equals(expected),"exactallbytes includingcanaries directA");
            complete(m,List.of(
                "R64:2090:0",
                "W64:2090:9000",
                "C:THIRD:A:424fae7:9000:k9000:k0"
            ),"source103 directA",plan);
        }
        {
            Ram m=new Ram("B");
            m.seed64(0x2090L,0x5000L);
            m.seed64(0x105C5DCD8L,0x7000L);
            m.seed32(0x10L,(int)0x0L);
            m.seed8(0x208FL,0xA5);m.seed8(0x2098L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x2090L,8,0x0L);
            expectedWrite(expected,0x105C5DCD8L,8,0x6000L);
            expectedWrite(expected,0x2090L,8,0xDEADL);
            expectedWrite(expected,0x2090L,8,0x9000L);
            Plan plan=new Plan(m,List.of(
                c("FIRST",m,new Object[]{0x424FAACL,0x5000L,0x9000L,0xFEDCBA9876543210L},x->{x.effect64(0x2090L,0L);x.effect64(0x105C5DCD8L,0x6000L);},null),
                c("SECOND",m,new Object[]{0x424FAD3L,0L,0x10542F330L},x->x.effect64(0x2090L,0xDEADL),null),
                c("THIRD",m,new Object[]{0x424FAE7L,0x9000L,OptionalLong.empty(),OptionalLong.empty()},null,null)));
            Fa90Target424FA90.execute(m,new LeafPorts(plan),new Fa90Api245.Input(0x100000000L,0x2000L,0x9000L,0xFEDCBA9876543210L));
            check(m.snapshot().equals(expected),"exactallbytes includingcanaries directB");
            complete(m,List.of(
                "R64:2090:5000",
                "C:FIRST:B:424faac:5000:9000:fedcba9876543210",
                "E64:2090:0",
                "E64:105c5dcd8:6000",
                "R64:2090:0",
                "R64:105c5dcd8:6000",
                "R32:10:0",
                "C:SECOND:B:424fad3:0:10542f330",
                "E64:2090:dead",
                "W64:2090:9000",
                "C:THIRD:B:424fae7:9000:?:?"
            ),"source103 directB",plan);
        }
        {
            Ram m=new Ram("C");
            m.seed64(0x2090L,0x5000L);
            m.seed64(0x105C5DCD8L,0x7000L);
            m.seed8(0x208FL,0xA5);m.seed8(0x2098L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x2090L,8,0x6000L);
            expectedWrite(expected,0x105C5DCD8L,8,0x6000L);
            expectedWrite(expected,0x2090L,8,0x9000L);
            Plan plan=new Plan(m,List.of(
                c("FIRST",m,new Object[]{0x424FAACL,0x5000L,0x9000L,0x8123456789ABCDEFL},x->{x.effect64(0x2090L,0x6000L);x.effect64(0x105C5DCD8L,0x6000L);},null),
                c("THIRD",m,new Object[]{0x424FAE7L,0x9000L,OptionalLong.empty(),OptionalLong.empty()},null,null)));
            Fa90Target424FA90.execute(m,new LeafPorts(plan),new Fa90Api245.Input(0x100000000L,0x2000L,0x9000L,0x8123456789ABCDEFL));
            check(m.snapshot().equals(expected),"exactallbytes includingcanaries directC");
            complete(m,List.of(
                "R64:2090:5000",
                "C:FIRST:C:424faac:5000:9000:8123456789abcdef",
                "E64:2090:6000",
                "E64:105c5dcd8:6000",
                "R64:2090:6000",
                "R64:105c5dcd8:6000",
                "W64:2090:9000",
                "C:THIRD:C:424fae7:9000:?:?"
            ),"source103 directC",plan);
        }
        {
            Ram m=new Ram("D");
            m.seed64(0x2090L,0x5000L);
            m.seed64(0x105C5DCD8L,0x7000L);
            m.seed8(0x208FL,0xA5);m.seed8(0x2098L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x2090L,8,0x10542F330L);
            expectedWrite(expected,0x2090L,8,0x9000L);
            Plan plan=new Plan(m,List.of(
                c("FIRST",m,new Object[]{0x424FAACL,0x5000L,0x9000L,0xFEDCBA9876543210L},x->x.effect64(0x2090L,0x10542F330L),null),
                c("THIRD",m,new Object[]{0x424FAE7L,0x9000L,OptionalLong.empty(),OptionalLong.of(0x10542F330L)},null,null)));
            Fa90Target424FA90.execute(m,new LeafPorts(plan),new Fa90Api245.Input(0x100000000L,0x2000L,0x9000L,0xFEDCBA9876543210L));
            check(m.snapshot().equals(expected),"exactallbytes includingcanaries directD");
            complete(m,List.of(
                "R64:2090:5000",
                "C:FIRST:D:424faac:5000:9000:fedcba9876543210",
                "E64:2090:10542f330",
                "R64:2090:10542f330",
                "R64:105c5dcd8:7000",
                "W64:2090:9000",
                "C:THIRD:D:424fae7:9000:?:k10542f330"
            ),"source103 directD",plan);
        }
        {
            Ram m=new Ram("E");
            m.seed64(0x2090L,0x5000L);
            m.seed8(0x208FL,0xA5);m.seed8(0x2098L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            RuntimeException marker=new RuntimeException("first-original-marker");
            Plan plan=new Plan(m,List.of(c("FIRST",m,new Object[]{0x424FAACL,0x5000L,0x9000L,0xFEDCBA9876543210L},null,marker)));
            sameException(()->Fa90Target424FA90.execute(m,new LeafPorts(plan),new Fa90Api245.Input(0x100000000L,0x2000L,0x9000L,0xFEDCBA9876543210L)),marker,"firstoriginalprefix");
            check(m.snapshot().equals(expected),"exactallbytes includingcanaries directE");
            complete(m,List.of(
                "R64:2090:5000",
                "C:FIRST:E:424faac:5000:9000:fedcba9876543210"
            ),"source103 directE",plan);
        }
    }
    private static void actual69Chain245(){
        {
            Ram m=new Ram("CHAIN");
            m.seed64(0x6008L,0x8000L);
            m.seed64(0x8000L,0x9000L);
            m.seed64(0x6000L,0x7000L);
            m.seed64(0x9000L,0xB000L);
            m.seed64(0x7000L,0xA000L);
            m.seed64(0xA090L,0xC000L);
            m.seed64(0x105C5DCD8L,0xE000L);
            m.seed64(0x4000L,0xAAAABBBB00000004L);
            m.seed32(0x5000L,(int)0x3L);
            m.seed32(0xD010L,(int)0x1L);
            m.seed8(0x101FL,0xA5);m.seed8(0x1028L,0x5A);m.seed8(0xA08FL,0xA5);m.seed8(0xA098L,0x5A);
            m.seed8(0xD00FL,0xA5);m.seed8(0xD014L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x1020L,8,0x4000L);
            expectedWrite(expected,0xA090L,8,0xD000L);
            expectedWrite(expected,0xA090L,8,0xB000L);
            expectedWrite(expected,0x4000L,4,0x80000002L);
            Plan plan=new Plan(m,List.of(
                c("ENTER800",m,new Object[]{0x424F817L,3L},null,null),
                c("FIRST",m,new Object[]{0x424FAACL,0xC000L,0xB000L,0x8000L},x->x.effect64(0xA090L,0xD000L),null),
                c("THIRD",m,new Object[]{0x424FAE7L,0xB000L,OptionalLong.empty(),OptionalLong.of(0x10542F330L)},x->x.effect32(0x4000L,0x80000002),null),
                c("LEAVE800",m,new Object[]{0x424F835L,0x80000002L,0x4000L},null,null)));
            F800Api244.Ports bound=Fa90FromF800Binding245.bind(0x100000000L,m,new LeafPorts(plan),new F800Ports(plan));
            F800Target424F800.execute(m,bound,new F800Api244.Input(0x5000L,0x6000L,0x4000L,new F800Api244.Scratch(0x1000L)));
            check(m.snapshot().equals(expected),"actual69+new103exactallbytes/R9upperDWORD/canaries");
            complete(m,List.of(
                "W64:1020:4000",
                "R32:5000:3",
                "C:ENTER800:CHAIN:424f817:3",
                "R64:6008:8000",
                "R64:8000:9000",
                "R64:6000:7000",
                "R64:9000:b000",
                "R64:7000:a000",
                "R64:a090:c000",
                "C:FIRST:CHAIN:424faac:c000:b000:8000",
                "E64:a090:d000",
                "R64:a090:d000",
                "R64:105c5dcd8:e000",
                "R32:d010:1",
                "W64:a090:b000",
                "C:THIRD:CHAIN:424fae7:b000:?:k10542f330",
                "E32:4000:80000002",
                "R32:4000:80000002",
                "C:LEAVE800:CHAIN:424f835:80000002:4000"
            ),"actual69bindingknownRAX/freshfield/freshleave",plan);
        }
        {
            Ram m=new Ram("PROTO"),foreign=new Ram("FOREIGN");
            RuntimeException marker=new RuntimeException("passive-enter-original");
            Plan child=new Plan(m,List.of());
            Plan fallback=new Plan(m,List.of(
                c("ENTER800",foreign,new Object[]{0x501L,0xFFFFFFFFL},null,null),
                c("LEAVE800",foreign,new Object[]{0x502L,0x80000000L,0xFEDCBA9876543210L},null,null),
                c("ENTER800",foreign,new Object[]{0x503L,0L},null,marker)));
            LeafPorts leaf=new LeafPorts(child);F800Ports old=new F800Ports(fallback);
            F800Api244.Ports bound=Fa90FromF800Binding245.bind(0L,m,leaf,old);
            Map<Long,Byte> original=m.snapshot(),foreignOriginal=foreign.snapshot();
            rejected(()->bound.call424fa90(foreign,0x424F82DL,0xA000L,0xB000L,0xFEDCBA9876543210L),"ownedforeign");
            rejected(()->bound.call424fa90(m,0x424F82CL,0xA000L,0xB000L,0xFEDCBA9876543210L),"ownedsite");
            rejected(()->Fa90FromF800Binding245.bind(0L,null,leaf,old),"factorycapturednull");
            rejected(()->Fa90FromF800Binding245.bind(0L,m,null,old),"factorychildnull");
            rejected(()->Fa90FromF800Binding245.bind(0L,m,leaf,null),"factoryfallbacknull");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty()&&child.cursor==0&&fallback.cursor==0,"allrejectionsbeforealleffects");
            bound.call4247ffc(foreign,0x501L,-1);
            bound.call4248050(foreign,0x502L,Integer.MIN_VALUE,0xFEDCBA9876543210L);
            sameException(()->bound.call4247ffc(foreign,0x503L,0),marker,"passiveexceptionidentity");
            check(m.snapshot().equals(original)&&foreign.snapshot().equals(foreignOriginal)&&foreign.trace.isEmpty(),"allpassiveRAMunchanged");
            complete(m,List.of("C:ENTER800:FOREIGN:501:ffffffff","C:LEAVE800:FOREIGN:502:80000000:fedcba9876543210","C:ENTER800:FOREIGN:503:0"),"new245guardsandtwoexactpassives",child,fallback);
        }
    }
    public static void main(String[] args){direct103();actual69Chain245();System.out.println("FA90245_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
