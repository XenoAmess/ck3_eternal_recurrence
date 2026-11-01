package org.xar.ck3.research.m3.manualcallee246;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.callee246.Callee42568FC246;
import org.xar.ck3.research.m3.callee246.Callee68fcFromFa90Binding246;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;

/** Finite source-only manual witness: byte RAM, scripted opaque calls, no CPU or Native execution. */
public final class CalleeValidation246 {
    private CalleeValidation246(){ }
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
    private static final class Ram implements Callee68fcApi246.Memory {
        final String name;final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
        int atomicCalls;final Map<Integer,Consumer<Ram>> afterAtomic=new HashMap<>();
        Ram(String name){this.name=name;}
        private long raw(long a,int width){long value=0;for(int n=0;n<width;n++){Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unmapped "+name+":"+h(a+n));value|=(b.longValue()&255L)<<(8*n);}return value;}
        private void store(long a,int width,long value){for(int n=0;n<width;n++)bytes.put(a+n,(byte)(value>>>(8*n)));}
        void seed8(long a,int value){check((value&~255)==0,"seed8width");store(a,1,value);}
        void seed32(long a,int value){store(a,4,Integer.toUnsignedLong(value));}
        void seed64(long a,long value){store(a,8,value);}
        void effect32(long a,int value){trace.add(rw("E32",a,Integer.toUnsignedLong(value)));store(a,4,Integer.toUnsignedLong(value));}
        void effect64(long a,long value){trace.add(rw("E64",a,value));store(a,8,value);}
        Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
        @Override public void atomicAddInt32(long a,int delta){
            long before=raw(a,4),after=(before+Integer.toUnsignedLong(delta))&0xFFFFFFFFL;
            store(a,4,after);atomicCalls++;trace.add("A32:"+h(a)+":"+h(Integer.toUnsignedLong(delta))+":"+h(before)+":"+h(after));
            Consumer<Ram> effect=afterAtomic.get(atomicCalls);if(effect!=null)effect.accept(this);
        }
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
    private static final class Fa90Ports implements Fa90Api245.Ports {
        final Plan plan;boolean requireOptionalIdentity;OptionalLong expectedRdxObject,expectedRaxObject;
        Fa90Ports(Plan plan){this.plan=plan;}
        @Override public void call42568fc(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){plan.invoke("FIRST",m,site,rcx,rdx,rax);}
        @Override public void call42566fc(F8a8Api242.Memory m,long site,long rcx,long rax){plan.invoke("SECOND",m,site,rcx,rax);}
        @Override public void call4256670(F8a8Api242.Memory m,long site,long rcx,OptionalLong rdx,OptionalLong rax){
            if(requireOptionalIdentity)check(rdx==expectedRdxObject&&rax==expectedRaxObject,"same passive OptionalLong argument objects");
            plan.invoke("THIRD",m,site,rcx,rdx,rax);
        }
    }
    private static final class TerminalPorts implements Callee68fcApi246.Ports {
        final Plan plan;TerminalPorts(Plan plan){this.plan=plan;}
        @Override public void call42568d4(Callee68fcApi246.Memory m,long site,long rcx,long rdx,long rax,long r8,long r9){plan.invoke("TERMINAL",m,site,rcx,rdx,rax,r8,r9);}
    }
    private static void expectedWrite(Map<Long,Byte> bytes,long a,int width,long value){for(int n=0;n<width;n++)bytes.put(a+n,(byte)(value>>>(8*n)));}
    private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException actual){check(actual==marker,label);return;}throw new AssertionError("missing exception "+label);}
    private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException actual){checks++;return;}throw new AssertionError("missing RuntimeException "+label);}
    private static void complete(Ram m,List<String> trace,String label,Plan... plans){check(m.trace.equals(trace),label+" fulltrace expected="+trace+" actual="+m.trace);for(Plan plan:plans)plan.exhausted();groups++;events+=m.trace.size();}
    private static void direct168(){
        {
            Ram m=new Ram("ZERO");
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            Plan plan=new Plan(m,List.of());
            Callee42568FC246.execute(m,new TerminalPorts(plan),new Callee68fcApi246.Input(0x0L,0x0L));
            check(m.atomicCalls==0,"sourceexactatomiccount ZERO");
            check(m.snapshot().equals(expected),"sourceexactallbytes/upperDWORD/canaries ZERO");
            complete(m,List.of(),"source168 ZERO",plan);
        }
        {
            Ram m=new Ram("MIX");
            m.seed64(0x1010L,0xAABBCCDD00000000L);
            m.seed64(0x10E0L,0xDEADL);
            m.seed64(0x10F0L,0x3000L);
            m.seed64(0x10E8L,0x0L);
            m.seed64(0x1100L,0x4000L);
            m.seed64(0x2000L,0x1122334400000000L);
            m.seed64(0x3000L,0x5566778800000001L);
            m.seed64(0x4000L,0x99AABBCC80000000L);
            m.seed64(0x6000L,0xDEADBEEF00000002L);
            m.seed64(0x7000L,0xCAFEBABE00000001L);
            m.seed64(0x8000L,0xA1A2A3A400000000L);
            m.seed64(0x1028L,0x1111L);
            m.seed64(0x1038L,0x6000L);
            m.seed64(0x1020L,0x0L);
            m.seed64(0x1030L,0x7000L);
            m.seed64(0x1048L,0x10542F498L);
            m.seed64(0x1040L,0x1L);
            m.seed64(0x1050L,0x0L);
            m.seed64(0x1068L,0x0L);
            m.seed64(0x1078L,0x0L);
            m.seed64(0x1060L,0x0L);
            m.seed64(0x1088L,0x10542F498L);
            m.seed64(0x1080L,0x0L);
            m.seed64(0x10A8L,0x0L);
            m.seed64(0x10B8L,0x8000L);
            m.seed64(0x10A0L,0x0L);
            m.seed64(0x10C8L,0x0L);
            m.seed64(0x10D8L,0x0L);
            m.seed64(0x10C0L,0x0L);
            m.seed64(0x1120L,0xFEDCBA9876543210L);
            m.seed8(0x100FL,0xA5);m.seed8(0x1018L,0x5A);
            m.seed8(0x1FFFL,0xA5);m.seed8(0x2008L,0x5A);
            m.seed8(0x2FFFL,0xA5);m.seed8(0x3008L,0x5A);
            m.seed8(0x3FFFL,0xA5);m.seed8(0x4008L,0x5A);
            m.seed8(0x5FFFL,0xA5);m.seed8(0x6008L,0x5A);
            m.seed8(0x6FFFL,0xA5);m.seed8(0x7008L,0x5A);
            m.seed8(0x7FFFL,0xA5);m.seed8(0x8008L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x1010L,4,0xFFFFFFFFL);
            expectedWrite(expected,0x10E0L,8,0x2000L);
            expectedWrite(expected,0x2000L,4,0xFFFFFFFFL);
            expectedWrite(expected,0x10E8L,8,0x4000L);
            expectedWrite(expected,0x3000L,4,0x0L);
            expectedWrite(expected,0x4000L,4,0x7FFFFFFFL);
            expectedWrite(expected,0x4000L,4,0x7FFFFFFEL);
            expectedWrite(expected,0x6000L,4,0x1L);
            expectedWrite(expected,0x1020L,8,0x1L);
            expectedWrite(expected,0x7000L,4,0x0L);
            expectedWrite(expected,0x8000L,4,0xFFFFFFFFL);
            expectedWrite(expected,0x1120L,8,0x0L);
            m.afterAtomic.put(1,x->{x.effect64(0x10E0L,0x2000L);});
            m.afterAtomic.put(2,x->{x.effect64(0x10E8L,0x4000L);});
            m.afterAtomic.put(6,x->{x.effect64(0x1020L,0x1L);});
            m.afterAtomic.put(8,x->{x.effect64(0x1120L,0x0L);});
            Plan plan=new Plan(m,List.of(c("TERMINAL",m,new Object[]{0x425699AL,0x0L,0x0L,0x10F8L,0x0L,0xFFFFFFFFL},null,null)));
            Callee42568FC246.execute(m,new TerminalPorts(plan),new Callee68fcApi246.Input(0x100000000L,0x1000L));
            check(m.atomicCalls==8,"sourceexactatomiccount MIX");
            check(m.snapshot().equals(expected),"sourceexactallbytes/upperDWORD/canaries MIX");
            complete(m,List.of(
                "A32:1010:ffffffff:0:ffffffff",
                "E64:10e0:2000",
                "R64:10e0:2000",
                "A32:2000:ffffffff:0:ffffffff",
                "E64:10e8:4000",
                "R64:10f0:3000",
                "A32:3000:ffffffff:1:0",
                "R64:10e8:4000",
                "A32:4000:ffffffff:80000000:7fffffff",
                "R64:1100:4000",
                "A32:4000:ffffffff:7fffffff:7ffffffe",
                "R64:1028:1111",
                "R64:1038:6000",
                "A32:6000:ffffffff:2:1",
                "E64:1020:1",
                "R64:1020:1",
                "R64:1030:7000",
                "A32:7000:ffffffff:1:0",
                "R64:1048:10542f498",
                "R64:1040:1",
                "R64:1050:0",
                "R64:1068:0",
                "R64:1078:0",
                "R64:1060:0",
                "R64:1088:10542f498",
                "R64:1080:0",
                "R64:10a8:0",
                "R64:10b8:8000",
                "A32:8000:ffffffff:0:ffffffff",
                "E64:1120:0",
                "R64:10a0:0",
                "R64:10c8:0",
                "R64:10d8:0",
                "R64:10c0:0",
                "R64:1120:0",
                "C:TERMINAL:MIX:425699a:0:0:10f8:0:ffffffff"
            ),"source168 MIX",plan);
        }
        {
            Ram m=new Ram("SKIP");
            m.seed64(0x2010L,0x1122334400000001L);
            m.seed64(0x20E0L,0x0L);
            m.seed64(0x20F0L,0x0L);
            m.seed64(0x20E8L,0x0L);
            m.seed64(0x2100L,0x0L);
            m.seed64(0x2120L,0x0L);
            m.seed64(0x2028L,0x10542F498L);
            m.seed64(0x2020L,0x0L);
            m.seed64(0x2048L,0x10542F498L);
            m.seed64(0x2040L,0x0L);
            m.seed64(0x2068L,0x10542F498L);
            m.seed64(0x2060L,0x0L);
            m.seed64(0x2088L,0x10542F498L);
            m.seed64(0x2080L,0x0L);
            m.seed64(0x20A8L,0x10542F498L);
            m.seed64(0x20A0L,0x0L);
            m.seed64(0x20C8L,0x10542F498L);
            m.seed64(0x20C0L,0x0L);
            m.seed8(0x200FL,0xA5);m.seed8(0x2018L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x2010L,4,0x0L);
            Plan plan=new Plan(m,List.of(c("TERMINAL",m,new Object[]{0x425699AL,0x0L,0x10542F498L,0x20F8L,0x0L,0xFFFFFFFFL},null,null)));
            Callee42568FC246.execute(m,new TerminalPorts(plan),new Callee68fcApi246.Input(0x100000000L,0x2000L));
            check(m.atomicCalls==1,"sourceexactatomiccount SKIP");
            check(m.snapshot().equals(expected),"sourceexactallbytes/upperDWORD/canaries SKIP");
            complete(m,List.of(
                "A32:2010:ffffffff:1:0",
                "R64:20e0:0",
                "R64:20f0:0",
                "R64:20e8:0",
                "R64:2100:0",
                "R64:2028:10542f498",
                "R64:2020:0",
                "R64:2048:10542f498",
                "R64:2040:0",
                "R64:2068:10542f498",
                "R64:2060:0",
                "R64:2088:10542f498",
                "R64:2080:0",
                "R64:20a8:10542f498",
                "R64:20a0:0",
                "R64:20c8:10542f498",
                "R64:20c0:0",
                "R64:2120:0",
                "C:TERMINAL:SKIP:425699a:0:10542f498:20f8:0:ffffffff"
            ),"source168 SKIP",plan);
        }
        {
            Ram m=new Ram("FAIL");
            m.seed64(0x3010L,0xAABBCCDD00000000L);
            m.seed8(0x300FL,0xA5);m.seed8(0x3018L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x3010L,4,0xFFFFFFFFL);
            RuntimeException marker=new RuntimeException("atomic-original-marker");
            m.afterAtomic.put(1,x->{throw marker;});
            Plan plan=new Plan(m,List.of());
            sameException(()->Callee42568FC246.execute(m,new TerminalPorts(plan),new Callee68fcApi246.Input(0x100000000L,0x3000L)),marker,"atomic original exactprefix");
            check(m.atomicCalls==1,"sourceexactatomiccount FAIL");
            check(m.snapshot().equals(expected),"sourceexactallbytes/upperDWORD/canaries FAIL");
            complete(m,List.of(
                "A32:3010:ffffffff:0:ffffffff"
            ),"source168 FAIL",plan);
        }
    }
    private static void actual245Chain246(){
        {
            Ram m=new Ram("CHAIN");
            m.seed64(0x3010L,0x1122334400000001L);
            m.seed64(0x30E0L,0x0L);
            m.seed64(0x30F0L,0x0L);
            m.seed64(0x30E8L,0x0L);
            m.seed64(0x3100L,0x0L);
            m.seed64(0x3120L,0x0L);
            m.seed64(0x3028L,0x10542F498L);
            m.seed64(0x3020L,0x0L);
            m.seed64(0x3048L,0x10542F498L);
            m.seed64(0x3040L,0x0L);
            m.seed64(0x3068L,0x10542F498L);
            m.seed64(0x3060L,0x0L);
            m.seed64(0x3088L,0x10542F498L);
            m.seed64(0x3080L,0x0L);
            m.seed64(0x30A8L,0x10542F498L);
            m.seed64(0x30A0L,0x0L);
            m.seed64(0x30C8L,0x10542F498L);
            m.seed64(0x30C0L,0x0L);
            m.seed64(0x2090L,0x3000L);
            m.seed64(0x105C5DCD8L,0x7777L);
            m.seed8(0x300FL,0xA5);m.seed8(0x3018L,0x5A);m.seed8(0x208FL,0xA5);m.seed8(0x2098L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x3010L,4,0x0L);
            expectedWrite(expected,0x2090L,8,0x7777L);
            expectedWrite(expected,0x2090L,8,0x9000L);
            Plan plan=new Plan(m,List.of(
                c("TERMINAL",m,new Object[]{0x425699AL,0L,0x10542F498L,0x30F8L,0L,0xFFFFFFFFL},x->x.effect64(0x2090L,0x7777L),null),
                c("THIRD",m,new Object[]{0x424FAE7L,0x9000L,OptionalLong.empty(),OptionalLong.empty()},null,null)));
            Fa90Api245.Ports bound=Callee68fcFromFa90Binding246.bind(0x100000000L,m,new TerminalPorts(plan),new Fa90Ports(plan));
            Fa90Target424FA90.execute(m,bound,new Fa90Api245.Input(0x100000000L,0x2000L,0x9000L,0xFEDCBA9876543210L));
            check(m.atomicCalls==1,"actual245 newedge oneleafmainatomic");
            check(m.snapshot().equals(expected),"actual245+168 exactallbytes/parentfield/freshglobal");
            complete(m,List.of(
                "R64:2090:3000",
                "A32:3010:ffffffff:1:0",
                "R64:30e0:0",
                "R64:30f0:0",
                "R64:30e8:0",
                "R64:3100:0",
                "R64:3028:10542f498",
                "R64:3020:0",
                "R64:3048:10542f498",
                "R64:3040:0",
                "R64:3068:10542f498",
                "R64:3060:0",
                "R64:3088:10542f498",
                "R64:3080:0",
                "R64:30a8:10542f498",
                "R64:30a0:0",
                "R64:30c8:10542f498",
                "R64:30c0:0",
                "R64:3120:0",
                "C:TERMINAL:CHAIN:425699a:0:10542f498:30f8:0:ffffffff",
                "E64:2090:7777",
                "R64:2090:7777",
                "R64:105c5dcd8:7777",
                "W64:2090:9000",
                "C:THIRD:CHAIN:424fae7:9000:?:?"
            ),"actual245→newbinder→168/sourceunknownafterfirst",plan);
        }
        {
            Ram m=new Ram("PROTO"),foreign=new Ram("FOREIGN");
            RuntimeException marker=new RuntimeException("passive-second-marker");
            OptionalLong knownZero=OptionalLong.of(0L),unknown=OptionalLong.empty();
            Plan child=new Plan(m,List.of());
            Plan passive=new Plan(m,List.of(
                c("SECOND",foreign,new Object[]{0x501L,0xFEDCBA9876543210L,0x8123456789ABCDEFL},null,null),
                c("THIRD",foreign,new Object[]{0x502L,0x8000000000001234L,knownZero,unknown},null,null),
                c("SECOND",foreign,new Object[]{0x503L,1L,2L},null,marker)));
            TerminalPorts leaf=new TerminalPorts(child);Fa90Ports fallback=new Fa90Ports(passive);
            fallback.requireOptionalIdentity=true;fallback.expectedRdxObject=knownZero;fallback.expectedRaxObject=unknown;
            Fa90Api245.Ports bound=Callee68fcFromFa90Binding246.bind(0L,m,leaf,fallback);
            Map<Long,Byte> original=m.snapshot(),foreignOriginal=foreign.snapshot();
            rejected(()->bound.call42568fc(foreign,0x424FAACL,0L,0x8000000000000001L,0xFEDCBA9876543210L),"ownedwrongMemory");
            rejected(()->bound.call42568fc(m,0x424FAABL,0L,0x8000000000000001L,0xFEDCBA9876543210L),"ownedwrongsite");
            rejected(()->Callee68fcFromFa90Binding246.bind(0L,null,leaf,fallback),"factorycapturednull");
            rejected(()->Callee68fcFromFa90Binding246.bind(0L,m,null,fallback),"factorychildnull");
            rejected(()->Callee68fcFromFa90Binding246.bind(0L,m,leaf,null),"factoryfallbacknull");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty()&&m.atomicCalls==0&&foreign.atomicCalls==0&&child.cursor==0&&passive.cursor==0,"allrejectionsbeforeallRAMatomicports");
            bound.call42566fc(foreign,0x501L,0xFEDCBA9876543210L,0x8123456789ABCDEFL);
            bound.call4256670(foreign,0x502L,0x8000000000001234L,knownZero,unknown);
            sameException(()->bound.call42566fc(foreign,0x503L,1L,2L),marker,"passive original exception");
            check(m.snapshot().equals(original)&&foreign.snapshot().equals(foreignOriginal)&&foreign.trace.isEmpty(),"passivebothMemoryunchanged");
            complete(m,List.of("C:SECOND:FOREIGN:501:fedcba9876543210:8123456789abcdef","C:THIRD:FOREIGN:502:8000000000001234:k0:?","C:SECOND:FOREIGN:503:1:2"),"passiveexactOptionalobjects/guards",child,passive);
        }
    }
    public static void main(String[] args){direct168();actual245Chain246();System.out.println("CALLEE246_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
