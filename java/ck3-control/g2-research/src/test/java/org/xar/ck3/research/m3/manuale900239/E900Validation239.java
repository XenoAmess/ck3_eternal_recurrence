package org.xar.ck3.research.m3.manuale900239;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.e900239.E900Api239;
import org.xar.ck3.research.m3.e900239.E900Target424E900;
import org.xar.ck3.research.m3.e900239.E900FromFc74Binding239;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;

/** Finite supplied-storage witness; no Native or Game execution. */
public final class E900Validation239 {
    private E900Validation239() { }
    private static int checks,groups,events;
    private static void check(boolean value,String label) {
        checks++;if(!value)throw new AssertionError(label);
    }
    private static long u(int value) { return Integer.toUnsignedLong(value); }
    private record Step(String op,long value,long[] args,Runnable after) { }
    private static Step row(String op,long value,long... args) { return new Step(op,value,args.clone(),null); }
    private static Step rowAfter(String op,long value,Runnable after,long... args) { return new Step(op,value,args.clone(),after); }
    private static final class Ram implements NativeTaskMemory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final Deque<Step> pending=new ArrayDeque<>();
        private int consumed;
        void expect(Step... steps) { pending.addAll(Arrays.asList(steps)); }
        Step take(String op,long... args) {
            Step s=pending.pollFirst();check(s!=null,"unexpected "+op);
            check(s.op().equals(op)&&Arrays.equals(s.args(),args),"expected "+s.op()+Arrays.toString(s.args())+" actual "+op+Arrays.toString(args));
            consumed++;return s;
        }
        private long rawRead(long address,int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Byte part=bytes.get(address+i);
                if(part==null)throw new AssertionError("unseeded byte "+Long.toUnsignedString(address+i,16));
                value|=(long)(part&255)<<(i*8);
            }
            return value;
        }
        private void rawWrite(long address,long value,int width) {
            for(int i=0;i<width;i++)bytes.put(address+i,(byte)(value>>>(i*8)));
        }
        void seed8(long address,int value) { rawWrite(address,value,1); }
        void seed32(long address,int value) { rawWrite(address,u(value),4); }
        void seed64(long address,long value) { rawWrite(address,value,8); }
        int peek8(long address) { return (int)rawRead(address,1); }
        long peek64(long address) { return rawRead(address,8); }
        Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
        void effect64(long address,long value) {
            Step s=take("E64",address);check(s.value()==value,"opaque write value");rawWrite(address,value,8);
        }
        @Override public long readPointer(long address) {
            Step s=take("R64",address);long value=rawRead(address,8);check(value==s.value(),"R64 value");return value;
        }
        @Override public int readInt32(long address) {
            Step s=take("R32",address);int value=(int)rawRead(address,4);check(u(value)==s.value(),"R32 value");return value;
        }
        @Override public void writeInt32(long address,int value) {
            Step s=take("W32",address);check(u(value)==s.value(),"W32 value");rawWrite(address,u(value),4);
        }
        @Override public void writeInt64(long address,long value) {
            Step s=take("W64",address);check(value==s.value(),"W64 value");rawWrite(address,value,8);
        }
        void finish(String label) { check(pending.isEmpty(),label+" unused events="+pending.size());groups++;events+=consumed; }
    }
    private static final class Child implements E900Api239.Ports {
        private final Ram ram;
        Child(Ram ram) { this.ram=ram; }
        private long call(NativeTaskMemory memory,String op,long... args) {
            check(memory==ram,"child identical Memory");Step s=ram.take(op,args);
            if(s.after()!=null)s.after().run();return s.value();
        }
        @Override public long call424e448(NativeTaskMemory memory,long site,int ecx,long rdx,long r8,long r9) {
            return call(memory,"E448",site,u(ecx),rdx,r8,r9);
        }
        @Override public long tail43dbba8(NativeTaskMemory memory,long site,long target,long rax,int ecx) {
            return call(memory,"TBB",site,target,rax,u(ecx));
        }
        @Override public long tail43da460(NativeTaskMemory memory,long site,long target,long rax,int ecx) {
            return call(memory,"T460",site,target,rax,u(ecx));
        }
    }
    private static final class Fallback implements Fc74Api238.Ports {
        private final Ram trace;
        private final NativeTaskMemory expectedMemory;
        Fallback(Ram trace,NativeTaskMemory expectedMemory) { this.trace=trace;this.expectedMemory=expectedMemory; }
        private long call(NativeTaskMemory memory,String op,long... args) {
            check(memory==expectedMemory,"fallback original Memory");Step s=trace.take(op,args);
            if(s.after()!=null)s.after().run();return s.value();
        }
        @Override public long call424e900(NativeTaskMemory memory,long site,int ecx) { throw new AssertionError("active E900 delegated"); }
        @Override public int callIat43da738(NativeTaskMemory memory,long site,long target,int ecx) { return (int)call(memory,"FIRST",site,target,u(ecx)); }
        @Override public int call424e948(NativeTaskMemory memory,long site,int ecx,long rdx) { return (int)call(memory,"E948",site,u(ecx),rdx); }
        @Override public long call424e2ec(NativeTaskMemory memory,long site,long rcx,long rdx) { return call(memory,"ALLOC",site,rcx,rdx); }
        @Override public void call424e364(NativeTaskMemory memory,long site,long rcx) { call(memory,"FREE",site,rcx); }
        @Override public void call424f8a8(NativeTaskMemory memory,long site,long rcx) { call(memory,"INIT",site,rcx); }
        @Override public void callIat43da420(NativeTaskMemory memory,long site,long target,int ecx) { call(memory,"LAST",site,target,u(ecx)); }
    }
    private static void sameException(Runnable action,RuntimeException expected,String label) {
        try { action.run(); } catch(RuntimeException actual) { check(actual==expected,label);return; }
        throw new AssertionError(label+" no exception");
    }
    private static void rejected(Runnable action,String label) {
        try { action.run(); } catch(RuntimeException expected) { checks++;return; }
        throw new AssertionError(label+" no RuntimeException");
    }

    private static void e900Producer239() {
        {
            Ram ram = new Ram();
            Child child = new Child(ram);
            long base = 0x144000000L;
            int entryEcxBits = 0x80000000; // High bit set, low32 non-zero
            long rdx = base + 0x4420C50L;
            long r8 = base + 0x4426F28L;
            long r9 = base + 0x4426F30L;
            long firstRax = 0x100000000L; // Full 64-bit non-zero, low 32 bits zero
            long initialSlot = 0x1111111111111111L;
            long mutatedSlot = 0x2222222222222222L;
            long tailReturn = 0x3333333333333333L;

            ram.seed64(base + 0x43DBBA8L, initialSlot);
            ram.seed8(base + 0x43DBBA8L - 1L, 0xA5);
            ram.seed64(base + 0x43DBBA8L + 8L, 0xDEADBEEFDEADBEEFL);

            ram.expect(
                rowAfter("E448", firstRax, () -> { ram.effect64(base + 0x43DBBA8L, mutatedSlot); }, 0x424E922L, u(5), rdx, r8, r9),
                row("E64", mutatedSlot, base + 0x43DBBA8L),
                row("R64", mutatedSlot, base + 0x43DBBA8L),
                row("TBB", tailReturn, 0x424E933L, mutatedSlot, firstRax, u(entryEcxBits))
            );

            long result = E900Target424E900.execute(ram, child, new E900Api239.Input(base, entryEcxBits));
            check(result == tailReturn, "Scene1 tail return");
            check(ram.peek64(base + 0x43DBBA8L) == mutatedSlot, "Scene1 slot mutation");
            check(ram.peek8(base + 0x43DBBA8L - 1L)==0xA5,"left boundary unchanged");
            check(ram.peek64(base + 0x43DBBA8L + 8L) == 0xDEADBEEFDEADBEEFL, "Scene1 neighbor canary");
            ram.finish("Scene1");
        }

        {
            Ram ram = new Ram();
            Child child = new Child(ram);
            long base = 0x144000000L;
            int entryEcxBits = 0x12345678;
            long rdx = base + 0x4420C50L;
            long r8 = base + 0x4426F28L;
            long r9 = base + 0x4426F30L;
            long firstRax = 0L;
            long initialSlot = 0x4444444444444444L;
            long mutatedSlot = 0x5555555555555555L;
            long tailReturn = 0x6666666666666666L;

            ram.seed64(base + 0x43DA460L, initialSlot);
            ram.seed8(base + 0x43DA460L - 1L, 0xA5);
            ram.seed64(base + 0x43DA460L + 8L, 0xCAFECAFECAFECAFEL);

            ram.expect(
                rowAfter("E448", firstRax, () -> { ram.effect64(base + 0x43DA460L, mutatedSlot); }, 0x424E922L, u(5), rdx, r8, r9),
                row("E64", mutatedSlot, base + 0x43DA460L),
                row("R64", mutatedSlot, base + 0x43DA460L),
                row("T460", tailReturn, 0x424E93FL, mutatedSlot, firstRax, u(entryEcxBits))
            );

            long result = E900Target424E900.execute(ram, child, new E900Api239.Input(base, entryEcxBits));
            check(result == tailReturn, "Scene2 tail return");
            check(ram.peek64(base + 0x43DA460L) == mutatedSlot, "Scene2 slot mutation");
            check(ram.peek8(base + 0x43DA460L - 1L)==0xA5,"left boundary unchanged");
            check(ram.peek64(base + 0x43DA460L + 8L) == 0xCAFECAFECAFECAFEL, "Scene2 neighbor canary");
            ram.finish("Scene2");
        }

        {
            Ram ram = new Ram();
            Child child = new Child(ram);
            long base = 0x144000000L;
            int entryEcxBits = 0x11111111;
            long rdx = base + 0x4420C50L;
            long r8 = base + 0x4426F28L;
            long r9 = base + 0x4426F30L;
            RuntimeException ex = new RuntimeException("E448 fail");
            Map<Long,Byte> before=ram.snapshot();

            ram.expect(
                rowAfter("E448", 0L, () -> { throw ex; }, 0x424E922L, u(5), rdx, r8, r9)
            );

            sameException(() -> E900Target424E900.execute(ram, child, new E900Api239.Input(base, entryEcxBits)), ex, "Scene3 first call throw");
            check(ram.snapshot().equals(before),"firstthrow no Memory effect");
            ram.finish("Scene3");
        }

        {
            Ram ram = new Ram();
            Child child = new Child(ram);
            long base = 0x144000000L;
            int entryEcxBits = 0x22222222;
            long rdx = base + 0x4420C50L;
            long r8 = base + 0x4426F28L;
            long r9 = base + 0x4426F30L;
            long firstRax = 0x9999999999999999L;
            long slotTarget = 0xAAAAAAAAAAAAAAAAL;
            RuntimeException ex = new RuntimeException("TBB fail");

            ram.seed64(base + 0x43DBBA8L, slotTarget);
            Map<Long,Byte> before=ram.snapshot();

            ram.expect(
                row("E448", firstRax, 0x424E922L, u(5), rdx, r8, r9),
                row("R64", slotTarget, base + 0x43DBBA8L),
                rowAfter("TBB", 0L, () -> { throw ex; }, 0x424E933L, slotTarget, firstRax, u(entryEcxBits))
            );

            sameException(() -> E900Target424E900.execute(ram, child, new E900Api239.Input(base, entryEcxBits)), ex, "Scene4 tail throw");
            check(ram.snapshot().equals(before),"tailthrow no Memory effect");
            ram.finish("Scene4");
        }
    }

    private static void fc74ChainProtocol239() {
        {
            Ram ram=new Ram();
            long base=0x20000000L;
            long first=base+0x43DA738L,bb=base+0x43DBBA8L,last=base+0x43DA420L;
            long index=base+0x542F328L;
            ram.seed64(first,0x11223344ABCDEF00L);
            ram.seed64(index,0xBEEFCAFE89ABCDEFL);
            ram.seed64(bb,0x2222333344445555L);
            ram.seed64(last,0x3333444455556666L);
            ram.seed8(bb-1,0xA5);ram.seed8(bb+8,0x5A);
            ram.seed8(last-1,0x69);ram.seed8(last+8,0x96);
            Child child=new Child(ram);
            Fallback fallback=new Fallback(ram,ram);
            Fc74Api238.Ports bound=E900FromFc74Binding239.bind(base,ram,child,fallback);
            ram.expect(
                row("R64",0x11223344ABCDEF00L,first),
                row("FIRST",0xDEADBEEFL,0x424FC83L,0x11223344ABCDEF00L,u(0x80000005)),
                row("R32",0x89ABCDEFL,index),
                rowAfter("E448",0x100000000L,()->{
                    ram.effect64(bb,0xB111222233334444L);
                    ram.effect64(last,0xC111222233334444L);
                },0x424E922L,5L,base+0x4420C50L,base+0x4426F28L,base+0x4426F30L),
                row("E64",0xB111222233334444L,bb),
                row("E64",0xC111222233334444L,last),
                row("R64",0xB111222233334444L,bb),
                row("TBB",0x8123456789ABC000L,0x424E933L,0xB111222233334444L,0x100000000L,u(0x89ABCDEF)),
                row("R64",0xC111222233334444L,last),
                row("LAST",0L,0x424FD21L,0xC111222233334444L,u(0xDEADBEEF))
            );
            long result=Fc74Target424FC74.execute(ram,bound,new Fc74Api238.Input(base,0x80000005));
            check(result==0x8123456789ABC000L,"real FC74 retains rawlong tailresult");
            check(ram.peek64(bb)==0xB111222233334444L&&ram.peek64(last)==0xC111222233334444L,"both callback slot writes visible");
            check(ram.peek8(bb-1)==0xA5&&ram.peek8(bb+8)==0x5A,"BB exactQWORD boundaries");
            check(ram.peek8(last-1)==0x69&&ram.peek8(last+8)==0x96,"last exactQWORD boundaries");
            check(ram.peek64(first)==0x11223344ABCDEF00L,"firstIAT unchanged");
            check(ram.peek64(index)==0xBEEFCAFE89ABCDEFL,"DWORD index read preserves upperhalf");
            ram.finish("actualFC74-E900newedge");
        }
        {
            Ram cap=new Ram(),foreign=new Ram();
            long base=0x30000000L;
            cap.seed64(0x6000L,0xA1A2A3A4A5A6A7A8L);
            foreign.seed64(0x7000L,0xB1B2B3B4B5B6B7B8L);
            Map<Long,Byte> capBefore=cap.snapshot(),foreignBefore=foreign.snapshot();
            Child child=new Child(cap);
            Fallback fallback=new Fallback(cap,foreign);
            Fc74Api238.Ports bound=E900FromFc74Binding239.bind(base,cap,child,fallback);
            rejected(()->bound.call424e900(foreign,0x424FC96L,0x80000001),"active foreignMemory pre-effect rejection");
            rejected(()->bound.call424e900(cap,0x424FC97L,0x80000002),"active wrongsite pre-effect rejection");
            check(cap.consumed==0&&foreign.consumed==0&&cap.pending.isEmpty()&&foreign.pending.isEmpty(),"both guards zero effects");
            check(cap.snapshot().equals(capBefore)&&foreign.snapshot().equals(foreignBefore),"both guard snapshots unchanged");
            cap.expect(row("FIRST",0x89ABCDEFL,0x1111222233334400L,0xD111222233334444L,u(0x80000003)));
            check(bound.callIat43da738(foreign,0x1111222233334400L,0xD111222233334444L,0x80000003)==0x89ABCDEF,"passive int FIRST bits");
            cap.expect(row("E948",0xFEDCBA98L,0x1111222233334401L,u(0xFFFFFFFF),0x8123456789ABCDEFL));
            check(bound.call424e948(foreign,0x1111222233334401L,0xFFFFFFFF,0x8123456789ABCDEFL)==0xFEDCBA98,"passive int E948 bits");
            cap.expect(row("ALLOC",0xFEDCBA9876543210L,0x1111222233334402L,0x8123456789ABCDEFL,0xFFEEDDCCBBAA0099L));
            check(bound.call424e2ec(foreign,0x1111222233334402L,0x8123456789ABCDEFL,0xFFEEDDCCBBAA0099L)==0xFEDCBA9876543210L,"passive ALLOC rawlong");
            cap.expect(row("FREE",0L,0x1111222233334403L,0xFFFFFFFF00001111L));
            bound.call424e364(foreign,0x1111222233334403L,0xFFFFFFFF00001111L);
            cap.expect(row("INIT",0L,0x1111222233334404L,0x8123456789ABC001L));
            bound.call424f8a8(foreign,0x1111222233334404L,0x8123456789ABC001L);
            cap.expect(row("LAST",0L,0x1111222233334405L,0xA555222233334444L,u(0x80000004)));
            bound.callIat43da420(foreign,0x1111222233334405L,0xA555222233334444L,0x80000004);
            RuntimeException ex=new RuntimeException("passive exactexception");
            cap.expect(rowAfter("FIRST",0L,()->{throw ex;},0x1111222233334400L,0xD111222233334444L,u(0x80000003)));
            sameException(()->bound.callIat43da738(foreign,0x1111222233334400L,0xD111222233334444L,0x80000003),ex,"FIRST exception");
            cap.expect(rowAfter("E948",0L,()->{throw ex;},0x1111222233334401L,u(0xFFFFFFFF),0x8123456789ABCDEFL));
            sameException(()->bound.call424e948(foreign,0x1111222233334401L,0xFFFFFFFF,0x8123456789ABCDEFL),ex,"E948 exception");
            cap.expect(rowAfter("ALLOC",0L,()->{throw ex;},0x1111222233334402L,0x8123456789ABCDEFL,0xFFEEDDCCBBAA0099L));
            sameException(()->bound.call424e2ec(foreign,0x1111222233334402L,0x8123456789ABCDEFL,0xFFEEDDCCBBAA0099L),ex,"ALLOC exception");
            cap.expect(rowAfter("FREE",0L,()->{throw ex;},0x1111222233334403L,0xFFFFFFFF00001111L));
            sameException(()->bound.call424e364(foreign,0x1111222233334403L,0xFFFFFFFF00001111L),ex,"FREE exception");
            cap.expect(rowAfter("INIT",0L,()->{throw ex;},0x1111222233334404L,0x8123456789ABC001L));
            sameException(()->bound.call424f8a8(foreign,0x1111222233334404L,0x8123456789ABC001L),ex,"INIT exception");
            cap.expect(rowAfter("LAST",0L,()->{throw ex;},0x1111222233334405L,0xA555222233334444L,u(0x80000004)));
            sameException(()->bound.callIat43da420(foreign,0x1111222233334405L,0xA555222233334444L,0x80000004),ex,"LAST exception");
            check(cap.snapshot().equals(capBefore)&&foreign.snapshot().equals(foreignBefore),"passives preserve both memories");
            check(foreign.consumed==0&&foreign.pending.isEmpty(),"foreign original object no Memorytouch");
            cap.finish("E900binding-sixpassives-guards");
        }
    }

    public static void main(String[] args) {
        e900Producer239();fc74ChainProtocol239();
        System.out.println("E900239_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" Native=0 Game=0");
    }
}
