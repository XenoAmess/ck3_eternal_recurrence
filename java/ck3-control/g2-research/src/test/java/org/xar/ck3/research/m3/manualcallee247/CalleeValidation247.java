package org.xar.ck3.research.m3.manualcallee247;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m3.callee246.Callee42568FC246;
import org.xar.ck3.research.m3.callee246.Callee42568D4247;
import org.xar.ck3.research.m3.callee246.Callee68d4From68fcBinding247;

/** Exact supplied byte effects only, not a CPU or atomic hardware implementation. */
public final class CalleeValidation247 {
    private CalleeValidation247(){ }
    private static int checks,groups,events;
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static String h(long value){return Long.toUnsignedString(value,16);}
    private static String rw(String kind,long a,long value){return kind+":"+h(a)+":"+h(value);}
    private static final class Ram implements Callee68d4Memory246 {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
        int addCalls,xaddCalls;Consumer<Ram> afterXadd;
        private long raw(long a,int width){long value=0;for(int n=0;n<width;n++){Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unmapped "+h(a+n));value|=(b.longValue()&255L)<<(8*n);}return value;}
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
        @Override public void atomicAddInt32(long a,int delta){long before=raw(a,4),after=(before+Integer.toUnsignedLong(delta))&0xFFFFFFFFL;store(a,4,after);addCalls++;trace.add("A32:"+h(a)+":"+h(Integer.toUnsignedLong(delta))+":"+h(before)+":"+h(after));}
        @Override public int exchangeAddInt32(long a,int delta){long before=raw(a,4),after=(before+Integer.toUnsignedLong(delta))&0xFFFFFFFFL;store(a,4,after);xaddCalls++;trace.add("X32:"+h(a)+":"+h(Integer.toUnsignedLong(delta))+":"+h(before)+":"+h(after));if(afterXadd!=null)afterXadd.accept(this);return (int)before;}
    }
    private static void expectedWrite(Map<Long,Byte> m,long a,int width,long value){for(int n=0;n<width;n++)m.put(a+n,(byte)(value>>>(8*n)));}
    private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException actual){check(actual==marker,label);return;}throw new AssertionError("no original exception "+label);}
    private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException actual){checks++;return;}throw new AssertionError("no rejection "+label);}
    private static void complete(Ram m,List<String> expected,String label){check(m.trace.equals(expected),label+" expected="+expected+" actual="+m.trace);groups++;events+=m.trace.size();}
    private static void direct37() {
        // Case 1: Normal path with opaque side effect via afterXadd
        {
            Ram m = new Ram();
            long entryRcx = 0x1000L;
            long moduleBase = 0x2000L;
            long targetAddr = entryRcx + 0x15CL;

            // Seed 64 bytes at targetAddr: low 32 bits = 0, high 32 bits = 0x12345678
            m.seed64(targetAddr, 0x1234567800000000L);

            // Setup opaque side effect: after XADD, write E32 to same cell with value 0x12345678
            m.afterXadd = (Ram r) -> {
                r.effect32(targetAddr, 0x12345678);
            };

            // Expected trace: X32 (old=0, delta=-1, new=FFFFFFFF) then E32 (0x12345678)
            List<String> expectedTrace = new ArrayList<>();
            expectedTrace.add("X32:" + h(targetAddr) + ":" + h(0xFFFFFFFFL) + ":" + h(0L) + ":" + h(0xFFFFFFFFL));
            expectedTrace.add("E32:" + h(targetAddr) + ":" + h(0x12345678L));

            // Expected map state: copy initial, apply X32 low write (FFFFFFFF), then E32 (0x12345678)
            Map<Long, Byte> expectedMap = new HashMap<>(m.snapshot());
            expectedWrite(expectedMap, targetAddr, 4, 0xFFFFFFFFL);
            expectedWrite(expectedMap, targetAddr, 4, 0x12345678L);

            long result = Callee42568D4247.execute(m, moduleBase, entryRcx);

            check(result == 0xFFFFFFFFL, "Case1 result mismatch");
            check(m.xaddCalls == 1, "Case1 xadd count");
            check(m.addCalls == 0, "Case1 add count");
            complete(m, expectedTrace, "R2directcase1");
            check(m.snapshot().equals(expectedMap), "Case1 map mismatch");
        }

        // Case 2: Address wrap to 0
        {
            Ram m = new Ram();
            long entryRcx = 0xFFFFFFFFFFFFFEA4L; // 0x15C wraps to 0
            long moduleBase = 0L;
            long targetAddr = 0L;

            // Seed 64 bytes at 0: low 32 bits = 0x80000000, high 32 bits = 0x11111111
            m.seed64(targetAddr, 0x1111111180000000L);

            // Expected trace: X32 (old=80000000, delta=-1, new=7FFFFFFF)
            List<String> expectedTrace = new ArrayList<>();
            expectedTrace.add("X32:" + h(targetAddr) + ":" + h(0xFFFFFFFFL) + ":" + h(0x80000000L) + ":" + h(0x7FFFFFFFL));

            // Expected map state: copy initial, apply X32 low write (7FFFFFFF)
            Map<Long, Byte> expectedMap = new HashMap<>(m.snapshot());
            expectedWrite(expectedMap, targetAddr, 4, 0x7FFFFFFFL);

            long result = Callee42568D4247.execute(m, moduleBase, entryRcx);

            check(result == 0x7FFFFFFFL, "Case2 result mismatch");
            check(m.xaddCalls == 1, "Case2 xadd count");
            check(m.addCalls == 0, "Case2 add count");
            complete(m, expectedTrace, "R2directcase2");
            check(m.snapshot().equals(expectedMap), "Case2 map mismatch");
        }
            {
            Ram m=new Ram();
            check(Callee42568D4247.execute(null,0L,0L)==0x7FFFFFFFL,"sourceentry0constant/nonullMemoryguard");
            check(Callee42568D4247.execute(m,0xFFFFFFFFF0000000L,0xFFFFFFFFF44271D0L)==0x7FFFFFFFL,"full64highsentinelconstant");
            check(m.trace.isEmpty()&&m.snapshot().isEmpty()&&m.xaddCalls==0&&m.addCalls==0,"bothconstantbrancheszeroRAM");
            m.seed64(0x215CL,0xAABBCCDDFFFFFFFFL);m.seed8(0x215BL,0xA5);m.seed8(0x2164L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x215CL,4,0xFFFFFFFEL);
            long actual=Callee42568D4247.execute(m,0L,0x2000L);
            check(actual==0xFFFFFFFEL,"oldFFFFFFFFDEC32fullpositiveRAX");
            check(m.xaddCalls==1&&m.addCalls==0,"oldFFFFFFFFoneXADD");
            check(m.snapshot().equals(expected),"allbytes/highDWORD/canaryoldFFFFFFFF");
            complete(m,List.of("X32:215c:ffffffff:ffffffff:fffffffe"),"constantbranches+oldFFFFFFFF");
        }
        {
            Ram m=new Ram();RuntimeException marker=new RuntimeException("direct-XADD-original-marker");
            m.seed64(0x315CL,0xDEADC0DE00000001L);m.seed8(0x315BL,0xA5);m.seed8(0x3164L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x315CL,4,0L);
            m.afterXadd=x->{throw marker;};
            sameException(()->Callee42568D4247.execute(m,0L,0x3000L),marker,"originalXADDfailure");
            check(m.xaddCalls==1&&m.addCalls==0,"failedXADDoneevent");
            check(m.snapshot().equals(expected),"failedXADDprefixallbytes");
            complete(m,List.of("X32:315c:ffffffff:1:0"),"directXADDoriginalexception");
        }
    }
    private static void actual246Chain247(){
        {
            Ram m=new Ram();
            m.seed64(0x8010L,0x5566778800000001L);
            m.seed64(0x80E0L,0x0L);
            m.seed64(0x80F0L,0x0L);
            m.seed64(0x80E8L,0x0L);
            m.seed64(0x8100L,0x0L);
            m.seed64(0x8120L,0x9000L);
            m.seed64(0x915CL,0xAABBCCDD00000000L);
            m.seed64(0x8028L,0x10542F498L);
            m.seed64(0x8020L,0x0L);
            m.seed64(0x8048L,0x10542F498L);
            m.seed64(0x8040L,0x0L);
            m.seed64(0x8068L,0x10542F498L);
            m.seed64(0x8060L,0x0L);
            m.seed64(0x8088L,0x10542F498L);
            m.seed64(0x8080L,0x0L);
            m.seed64(0x80A8L,0x10542F498L);
            m.seed64(0x80A0L,0x0L);
            m.seed64(0x80C8L,0x10542F498L);
            m.seed64(0x80C0L,0x0L);
            m.seed8(0x800FL,0xA5);m.seed8(0x8018L,0x5A);m.seed8(0x915BL,0xA5);m.seed8(0x9164L,0x5A);
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());
            expectedWrite(expected,0x8010L,4,0L);expectedWrite(expected,0x915CL,4,0xFFFFFFFFL);
            Callee68fcApi246.Ports bound=Callee68d4From68fcBinding247.bind(0x100000000L,m);
            Callee42568FC246.execute(m,bound,new Callee68fcApi246.Input(0x100000000L,0x8000L));
            check(m.addCalls==1&&m.xaddCalls==1,"actual246oneADDandoneXADD");
            check(m.snapshot().equals(expected),"actual246newedgeexactallbytes");
            complete(m,List.of(
                "A32:8010:ffffffff:1:0",
                "R64:80e0:0",
                "R64:80f0:0",
                "R64:80e8:0",
                "R64:8100:0",
                "R64:8028:10542f498",
                "R64:8020:0",
                "R64:8048:10542f498",
                "R64:8040:0",
                "R64:8068:10542f498",
                "R64:8060:0",
                "R64:8088:10542f498",
                "R64:8080:0",
                "R64:80a8:10542f498",
                "R64:80a0:0",
                "R64:80c8:10542f498",
                "R64:80c0:0",
                "R64:8120:9000",
                "X32:915c:ffffffff:0:ffffffff"
            ),"actual246→newD4binding→37/realresultdiscarded");
        }
        {
            Ram m=new Ram(),foreign=new Ram();
            RuntimeException marker=new RuntimeException("bound-XADD-original-marker");
            m.seed64(0x715CL,0xABCDEF0100000001L);m.seed8(0x715BL,0xA5);m.seed8(0x7164L,0x5A);
            Map<Long,Byte> original=m.snapshot(),foreignOriginal=foreign.snapshot();
            Callee68fcApi246.Ports bound=Callee68d4From68fcBinding247.bind(0L,m);
            rejected(()->Callee68d4From68fcBinding247.bind(0L,null),"factorynullcaptured");
            rejected(()->bound.call42568d4(foreign,0x425699AL,0x7000L,1L,2L,3L,4L),"ownedforeignMemory");
            rejected(()->bound.call42568d4(m,0x4256999L,0x7000L,1L,2L,3L,4L),"ownedwrongsite");
            check(m.trace.isEmpty()&&foreign.trace.isEmpty()&&m.xaddCalls==0&&foreign.xaddCalls==0&&m.addCalls==0&&foreign.addCalls==0,"allguardsbeforeallRAMatomic");
            check(m.snapshot().equals(original)&&foreign.snapshot().equals(foreignOriginal),"guardallbytesunchanged");
            Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x715CL,4,0L);
            m.afterXadd=x->{throw marker;};
            sameException(()->bound.call42568d4(m,0x425699AL,0x7000L,0xFEDCBA9876543210L,0x8123456789ABCDEFL,0xFFFFFFFFFFFFFFFFL,0x8000000000000000L),marker,"boundrealXADDexceptionidentity");
            check(m.xaddCalls==1&&m.addCalls==0,"validboundonesourceXADD");
            check(m.snapshot().equals(expected)&&foreign.snapshot().equals(foreignOriginal)&&foreign.trace.isEmpty(),"validboundfailureexactbyteprefix");
            complete(m,List.of("X32:715c:ffffffff:1:0"),"new247factoryguards+validboundexception");
        }
    }
    public static void main(String[] args){direct37();actual246Chain247();System.out.println("CALLEE247_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");}
}
