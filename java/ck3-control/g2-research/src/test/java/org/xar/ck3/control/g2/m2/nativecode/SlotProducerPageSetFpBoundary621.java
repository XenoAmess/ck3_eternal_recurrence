package org.xar.ck3.control.g2.m2.nativecode;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** New upper-entry nested Page/SET prefixes, with literal expected state and one RAM cursor. */
public final class SlotProducerPageSetFpBoundary621 {
    private SlotProducerPageSetFpBoundary621() { }
    private static final long I=0x140000000L,E=0x8500000000008000L,O=0x8500000000002000L,P=O+8,
        T=0x8500000000004000L,CTX=0x8500000000006000L,ARG3=0x8500000000006100L,ARG4=0x8500000000006200L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(0x21,0xE1),P2=new Mxcsr(0x40,0x40);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long bank){return new VolatileBits(
        ax,cx,dx,r8,r9,r10,r11,x(bank,0),x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static final NonvolatileBits N=new NonvolatileBits(11,22,33,44,55,66,77,88,x(0xA0,6));
    private static NonvolatileBits pageN(){return new NonvolatileBits(P,0,33,1,CTX,ARG4,P,0,x(0xA0,6));}
    private static void check(boolean value){if(!value)throw new AssertionError("621 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record Page(KnownPageFp619.CallFrame frame,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private record Tail(KnownPageSetFp620.TailCall frame,Outcome outcome,List<Mem> effects,boolean throwing) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,pageCalls,tails;
        final RuntimeException marker=new IllegalStateException("621 foreign callback marker");
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->event(new Budget(header,guard));
        final KnownPageFp619.Memory memory=(KnownPageFp619.Memory)Proxy.newProxyInstance(KnownPageFp619.Memory.class.getClassLoader(),
            new Class<?>[]{KnownPageFp619.Memory.class},(proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte")||name.equals("write8"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected621Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");
                long value=write?((Number)args[1]).longValue():load(address,width);event(new Mem(write,width,address,mask(width,value)));
                if(write){store(address,width,value);return null;}if(width==1)return Integer.valueOf((int)value&255);
                if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long value=0;for(int k=0;k<width;k++){Byte b=ram.get(address+k);if(b==null)throw new AssertionError("Unseeded621RAM");value|=(b.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("621 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        void addPage(KnownPageFp619.CallFrame frame,Outcome outcome,List<Mem> effects,boolean throwing){steps.add(new Page(frame,outcome,effects,throwing));steps.addAll(effects);}
        void addTail(KnownPageSetFp620.TailCall frame,Outcome outcome,List<Mem> effects,boolean throwing){steps.add(new Tail(frame,outcome,effects,throwing));steps.addAll(effects);}
        void effect(Mem e){check(e.write());if(e.width()==1)memory.writeByte(e.address(),(int)e.value());else if(e.width()==4)memory.writeDword(e.address(),(int)e.value());else memory.writeQword(e.address(),e.value());}
        Outcome page(KnownPageFp619.CallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Page);
            Page expected=(Page)steps.get(cursor++);check(actual.equals(expected.frame())&&actual.preMxcsr()==expected.frame().preMxcsr());pageCalls++;
            for(Mem effect:expected.effects())effect(effect);if(expected.throwing())throw marker;return expected.outcome();}
        Outcome tail(KnownPageSetFp620.TailCall actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Tail);
            Tail expected=(Tail)steps.get(cursor++);check(actual.equals(expected.frame())&&actual.preMxcsr()==expected.frame().preMxcsr());tails++;
            for(Mem effect:expected.effects())effect(effect);if(expected.throwing())throw marker;return expected.outcome();}
        void done(){check(cursor==steps.size());}
    }
    private static SlotProducerGrowthWithFp618.Input input(Script s){var before=v(0xA0,O,CTX,ARG3,ARG4,0xAA,0xAB,0xA0);
        return new SlotProducerGrowthWithFp618.Input(new FullSlotProducer479Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,before,N),true,s.budget),P0);}
    private static Outcome execute(Script s){return SlotProducerKnownPageSetFp621.execute(input(s),s.memory,
        unused->{throw new AssertionError("Unexpected621upperCall");},s::page,
        unused->{throw new AssertionError("Unexpected621reserveCall");},unused->{throw new AssertionError("Unexpected621copyTail");},
        unused->{throw new AssertionError("Unexpected621reserveSetTail");},s::tail);}
    private static Script seeded(long jump){Script s=new Script();s.store(P+0x40,1,0);s.store(P+0x41,1,0);s.store(P+0x38,4,0);
        s.store(P+0xC,4,0);s.store(P,8,T);s.store(I+0x60900F0,4,jump);return s;}
    private static KnownPageFp619.CallFrame tableFrame(){var before=v(0,P,1,ARG3,ARG4,0xAA,0xAB,0xA0);
        var call=new GovernmentCrtBoundary185Api.Call(0x2A32258,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x2A32620,E-0xA8,before,pageN());
        return new KnownPageFp619.CallFrame(new FullPage495Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0xB0,before,pageN()),true,5,I+0x2A3225D),P0);}
    private static Normal tableNormal(long returnRva){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
        v(0xA5,0xA6,0xA7,0xA8,0xA9,0xAA,0xAB,0xB0),I+returnRva,E-0xA8,pageN()),false),P1);}
    private static void prefix(Script s,long tableReturnRva){s.write(8,E+0x10,11);s.write(8,E+0x18,ARG3);
        s.write(8,E-8,22);s.write(8,E-0x10,33);s.write(8,E-0x18,44);s.write(8,E-0x20,55);s.write(8,E-0x28,66);s.write(8,E-0x30,77);s.write(8,E-0x38,88);
        s.read(1,P+0x40,0);s.read(1,P+0x41,0);s.read(4,P+0x38,0);s.read(4,P+0x38,0);s.write(8,E-0x60,I+0x2A327EC);
        s.write(8,E-0x68,77);s.read(1,P+0x40,0);s.write(8,E-0x48,22);s.read(4,P+0xC,0);
        s.write(8,E-0x50,P);s.write(8,E-0x70,33);s.write(8,E-0x78,0);s.write(8,E-0xB0,I+0x2A3225D);
        s.addPage(tableFrame(),tableNormal(tableReturnRva),List.of(new Mem(true,4,P+0xC,0xFFFFFFFFL),new Mem(true,1,P+0x70,123)),false);}
    private static void toSet(Script s,long jump){s.read(4,P+0xC,0xFFFFFFFFL);s.read(8,P,T);s.write(8,E-0xB0,I+0x2A32281);s.read(4,I+0x60900F0,jump);}
    private static KnownPageFp619.CallFrame allocator(){var before=v(T-8,0x172000,0,16,I+0x4227098,0xAA,T-8,0xB0);
        var n=new NonvolatileBits(T,1,0,1,CTX,ARG4,P,0,x(0xA0,6));
        var call=new GovernmentCrtBoundary185Api.Call(0x2A322DB,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4223B94,E-0xA8,before,n);
        return new KnownPageFp619.CallFrame(new FullPage495Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0xB0,before,n),false,5,I+0x2A322E0),P1);}
    private static KnownPageSetFp620.TailCall unknownSet(){var before=v(T-8,T+8,0,16,I+0x1234,0xAA,T-8,0xB0);
        return new KnownPageSetFp620.TailCall(new GovernmentCrtBoundary185Api.Tail(0x422703B,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,I+0x1234,
            new GovernmentCrtBoundary185Api.Entry(I,E-0xB0,before,pageN())),false,P1);}
    private static Stopped stop(GovernmentCrtBoundary185Api.Entry entry,long pc){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(entry,pc,false,P2),0,pc);}
    private static void knownFillThenAllocatorStop(){Script s=seeded(0x4227098);prefix(s,0x2A3225D);toSet(s,0x4227098);
        s.write(8,T-8,0);s.write(8,T,0);s.read(8,E-0xB0,I+0x2A32281);s.write(4,P+0xC,1);
        s.steps.add(new Budget(0x2A322D0,0));s.read(8,P,T);s.write(8,E-0xB0,I+0x2A322E0);
        var f=allocator();var expected=stop(f.original().childEntry(),0x2A322DB);s.addPage(f,expected,List.of(new Mem(true,1,P+0x71,77)),false);
        check(execute(s)==expected);s.done();check(s.pageCalls==2&&s.tails==0&&s.load(T-8,8)==0&&s.load(T,8)==0&&s.load(P+0xC,4)==1&&s.load(P+0x70,1)==123&&s.load(P+0x71,1)==77);
        check(s.load(E-0x60,8)==I+0x2A327EC&&s.load(E-0xB0,8)==I+0x2A322E0&&s.load(E-0x68,8)==77);}
    private static void nestedUnknownSetStop(){Script s=seeded(0x1234);prefix(s,0x2A3225D);toSet(s,0x1234);var f=unknownSet();var expected=stop(f.original().entry(),0x422703B);
        s.addTail(f,expected,List.of(new Mem(true,1,P+0x71,88)),false);check(execute(s)==expected);s.done();
        check(s.pageCalls==1&&s.tails==1&&s.load(P+0xC,4)==0xFFFFFFFFL&&s.load(P+0x71,1)==88&&s.load(E-0xB0,8)==I+0x2A32281);}
    private static void rejectedAndForeignPrefixes(){Script bad=seeded(0x4227098);prefix(bad,0x2A3225E);
        try{execute(bad);throw new AssertionError("Bad621tableNormalaccepted");}catch(IllegalArgumentException expected){bad.done();check(bad.pageCalls==1&&bad.tails==0&&bad.load(P+0xC,4)==0xFFFFFFFFL&&bad.load(P+0x70,1)==123);}
        Script foreign=seeded(0x1234);prefix(foreign,0x2A3225D);toSet(foreign,0x1234);var f=unknownSet();foreign.addTail(f,stop(f.original().entry(),0x422703B),List.of(new Mem(true,1,P+0x71,99)),true);
        try{execute(foreign);throw new AssertionError("Foreign621exceptionswallowed");}catch(RuntimeException actual){check(actual==foreign.marker);foreign.done();check(foreign.pageCalls==1&&foreign.tails==1&&foreign.load(P+0x71,1)==99&&foreign.load(P+0xC,4)==0xFFFFFFFFL);}}
    public static int verify(){knownFillThenAllocatorStop();nestedUnknownSetStop();rejectedAndForeignPrefixes();return 3;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
