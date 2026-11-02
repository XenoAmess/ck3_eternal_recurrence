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

/** Independent finite source oracle for the new upstream FP carrier; no old suite invoked. */
public final class SlotProducerGrowthFpBoundary618 {
    private SlotProducerGrowthFpBoundary618() { }
    private static final long I=0x140000000L,E=0x8200000000008000L,P=0x8200000000002000L,
        H=P+0x18,OLD=0x8200000000003000L,A=0x8200000000005000L,T=0x8200000000006000L,
        CTX=0x8200000000007000L,ARG4=0x8200000000007100L,ALLOC=0xF000000000000111L,
        RET=0xF100000000000333L,FALL=0xF200000000000444L,REST_BX=0xFACE000000000111L,
        REST_12=0xFACE000000000555L;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(1,1),P2=new Mxcsr(0x21,0xE1);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long bank){return new VolatileBits(
        ax,cx,dx,r8,r9,r10,r11,x(bank,0),x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static NonvolatileBits n(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){
        return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x(0xA0,6));}
    private static final NonvolatileBits N=n(11,22,33,44,55,66,77,88),G=n(P,22,33,44,CTX,ARG4,77,88);
    private static final VolatileBits V=v(0xA0,P-8,CTX,0xA8,ARG4,0xAA,0xAB,0xA0);
    private static void check(boolean condition){if(!condition)throw new AssertionError("618 literal/source mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record Outer(SlotProducerGrowthWithFp618.CallFrame frame,Outcome outcome,List<Mem> effects) { }
    private record Inner(SlotReserveWithFp615.CallFrame frame,Outcome outcome,List<Mem> effects) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,outerCalls,innerCalls;
        final RuntimeException marker=new IllegalStateException("618 foreign callback identity");boolean throwOuter;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->event(new Budget(header,guard));
        final SlotProducerGrowthWithFp618.Memory memory=(SlotProducerGrowthWithFp618.Memory)Proxy.newProxyInstance(
            SlotProducerGrowthWithFp618.Memory.class.getClassLoader(),new Class<?>[]{SlotProducerGrowthWithFp618.Memory.class},
            (proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected618Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");
                long value=write?((Number)args[1]).longValue():load(address,width);
                event(new Mem(write,width,address,mask(width,value)));
                if(write){store(address,width,value);return null;}
                if(width==1)return Integer.valueOf((int)value&255);if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long value=0;for(int k=0;k<width;k++){
            Byte b=ram.get(address+k);if(b==null)throw new AssertionError("Unseeded618RAM "+Long.toHexString(address+k));
            value|=(b.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("618 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        void effects(List<Mem> effects){for(Mem m:effects){check(m.write());if(m.width()==1)memory.writeByte(m.address(),(int)m.value());
            else if(m.width()==8)memory.writeQword(m.address(),m.value());else if(m.width()==4)memory.writeDword(m.address(),(int)m.value());
            else throw new AssertionError("effect width");}}
        Outcome outer(SlotProducerGrowthWithFp618.CallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Outer);
            Outer expected=(Outer)steps.get(cursor++);check(actual.equals(expected.frame())&&actual.preMxcsr()==expected.frame().preMxcsr());
            outerCalls++;effects(expected.effects());if(throwOuter)throw marker;return expected.outcome();}
        Outcome inner(SlotReserveWithFp615.CallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Inner);
            Inner expected=(Inner)steps.get(cursor++);check(actual.equals(expected.frame())&&actual.preMxcsr()==expected.frame().preMxcsr());
            innerCalls++;effects(expected.effects());return expected.outcome();}
        void addOuter(SlotProducerGrowthWithFp618.CallFrame frame,Outcome outcome,List<Mem> effects){steps.add(new Outer(frame,outcome,effects));steps.addAll(effects);}
        void addInner(SlotReserveWithFp615.CallFrame frame,Outcome outcome,List<Mem> effects){steps.add(new Inner(frame,outcome,effects));steps.addAll(effects);}
        void done(){check(cursor==steps.size());}
    }
    private static Script seeded(int head,int capacity){Script s=new Script();s.store(E,8,RET);s.store(P+0x40,1,0);s.store(P+0x41,1,0);
        s.store(P+0x38,4,head);s.store(P+0x24,4,1);s.store(H,8,OLD);s.store(H+8,4,capacity);s.store(H+16,8,A);
        s.store(A,8,T);s.store(T+8,8,ALLOC);s.store(I+0x60900F0,4,0x4227098);s.store(I+0x5D1EC70,8,FALL);return s;}
    private static Outcome execute(Script s){var base=new FullSlotProducer479Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,V,N),true,s.budget);
        return SlotProducerGrowthWithFp618.execute(new SlotProducerGrowthWithFp618.Input(base,P0),s.memory,s::outer,s::inner,
            frame->{throw new AssertionError("618 cases do not reach unknown COPY tail");},
            frame->{throw new AssertionError("618 cases do not reach unknown SET tail");});}
    private static void prologue(Script s){s.write(8,E+0x10,11);s.write(8,E+0x18,0xA8);
        s.write(8,E-8,22);s.write(8,E-0x10,33);s.write(8,E-0x18,44);s.write(8,E-0x20,55);
        s.write(8,E-0x28,66);s.write(8,E-0x30,77);s.write(8,E-0x38,88);s.read(1,P+0x40,0);}
    private static void growPrefix(Script s){prologue(s);s.read(1,P+0x41,0);s.read(4,P+0x38,0xFFFFFF);s.read(4,P+0x24,1);
        s.write(8,E-0x60,I+0x2A327D3);
        s.write(8,E-0x50,P);s.write(8,E-0x48,22);s.write(8,E-0x68,33);s.read(1,P+0x40,0);
        s.read(4,P+0x24,1);s.write(8,E-0x58,44);s.read(4,P+0x24,1);s.write(8,E-0x90,I+0x1ACDFF8);
        s.write(8,E-0x78,1);s.write(8,E-0x98,44);}
    private static SlotReserveWithFp615.CallFrame allocator(Script s){growPrefix(s);s.read(4,H+8,1);s.read(8,H+16,A);
        s.write(8,E-0x88,P);s.write(8,E-0x80,2);s.read(8,A,T);s.read(8,T+8,ALLOC);s.write(8,E-0xC0,I+0x1ACE4E4);
        var before=v(T,A,32,8,ARG4,0xAA,0xAB,0xA0);var saved=n(H,P,2,2,CTX,ARG4,77,88);
        var call=new GovernmentCrtBoundary185Api.Call(0x1ACE4E1,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,ALLOC,E-0xB8,before,saved);
        var original=new PendingSlotCapacityFullState412Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0xC0,before,saved),true,3,I+0x1ACE4E4);
        return new SlotReserveWithFp615.CallFrame(original,P0);}
    private static Stopped innerStopped(SlotReserveWithFp615.CallFrame frame){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(frame.original().childEntry(),0x1ACE4E1,true,P1),0,0x1ACE4E1);}
    private static SlotProducerGrowthWithFp618.CallFrame page(int index,boolean afterGrowth){
        VolatileBits before=afterGrowth?v(OLD|1,P,2,1,OLD,1,0,0xA0):v(0xA0,P,index+1L,0xA8,ARG4,0xAA,0xAB,0xA0);
        NonvolatileBits saved=n(P,22,33,index,CTX,ARG4,77,index);
        var call=new GovernmentCrtBoundary185Api.Call(0x2A327E7,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x2A321F0,E-0x58,before,saved);
        var original=new FullSlotProducer479Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,saved),true,5,I+0x2A327EC);
        return new SlotProducerGrowthWithFp618.CallFrame(original,P0);}
    private static void pagePrefix(Script s,int index){prologue(s);s.read(1,P+0x41,0);s.read(4,P+0x38,index);
        s.read(4,P+0x38,index);s.write(8,E-0x60,I+0x2A327EC);}
    private static void restored(Script s,long bx,long r12){s.read(8,E+0x10,bx);s.read(8,E-0x38,88);s.read(8,E-0x30,77);
        s.read(8,E-0x28,66);s.read(8,E-0x20,r12);s.read(8,E-0x18,44);s.read(8,E-0x10,33);s.read(8,E-8,22);s.read(8,E,RET);}
    private static void actualNestedAllocatorStop(){Script s=seeded(0xFFFFFF,1);var frame=allocator(s);var expected=innerStopped(frame);
        s.addInner(frame,expected,List.of(new Mem(true,1,OLD+63,123)));check(execute(s)==expected);s.done();
        check(s.innerCalls==1&&s.outerCalls==0&&s.load(OLD+63,1)==123&&s.load(P+0x24,4)==1&&s.load(H,8)==OLD);}
    private static void knownSetThenPageStop(){Script s=seeded(0xFFFFFF,2);growPrefix(s);s.read(4,H+8,2);
        s.read(8,E-0x78,1);s.read(8,E-0x98,44);s.read(8,E-0x90,I+0x1ACDFF8);
        s.read(4,P+0x24,1);s.read(8,H,OLD);s.write(8,E-0x90,I+0x1ACE01A);
        s.read(4,I+0x60900F0,0x4227098);s.write(8,OLD+16,0);s.write(8,OLD+24,0);s.read(8,E-0x90,I+0x1ACE01A);
        s.write(4,P+0x24,2);s.steps.add(new Budget(0x1ACE030,1));s.read(8,H,OLD);s.write(4,OLD+20,0xFFFFFF);
        s.read(8,H,OLD);s.write(8,OLD+24,0);s.read(8,H,OLD);s.write(4,OLD+16,0xFFFFFF);
        s.read(4,P+0x38,0xFFFFFF);s.read(8,E-0x58,44);s.write(4,P+0x38,1);
        s.read(8,E-0x50,P);s.read(8,E-0x48,22);s.read(8,E-0x68,33);s.read(8,E-0x60,I+0x2A327D3);
        s.read(4,P+0x38,1);s.write(8,E-0x60,I+0x2A327EC);var frame=page(1,true);
        var expected=new Stopped(StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(frame.original().childEntry(),0x2A327E7,true,P2),0,0x2A327E7);
        s.addOuter(frame,expected,List.of(new Mem(true,1,P+0x42,9)));check(execute(s)==expected);s.done();
        check(s.innerCalls==0&&s.outerCalls==1&&s.load(P+0x24,4)==2&&s.load(P+0x38,4)==1&&s.load(OLD+16,4)==0xFFFFFF&&s.load(OLD+24,8)==0&&s.load(P+0x42,1)==9);}
    private static Normal returned(SlotProducerGrowthWithFp618.CallFrame frame,long rip){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(v(0xC000,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),rip,E-0x58,frame.original().call().nonvolatileBits()),false),P2);}
    private static void opaqueNormalFreshRestore(){Script s=seeded(7,2);pagePrefix(s,7);var frame=page(7,false);
        s.addOuter(frame,returned(frame,I+0x2A327EC),List.of(new Mem(true,8,E+0x10,REST_BX),new Mem(true,8,E-0x20,REST_12)));
        s.read(8,I+0x5D1EC70,FALL);restored(s,REST_BX,REST_12);var actual=(Normal)execute(s);s.done();
        check(actual.postMxcsr()==P2&&!actual.base().postDirectionFlagSet()&&actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(FALL,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),RET,E+8,n(REST_BX,22,33,44,REST_12,66,77,88))));}
    private static void rejectedAndForeignPrefixes(){Script bad=seeded(7,2);pagePrefix(bad,7);var frame=page(7,false);
        bad.addOuter(frame,returned(frame,I+0x2A327ED),List.of(new Mem(true,1,OLD+63,77)));
        try{execute(bad);throw new AssertionError("bad original NR accepted");}catch(IllegalArgumentException expected){bad.done();check(bad.load(OLD+63,1)==77);}
        Script foreign=seeded(7,2);pagePrefix(foreign,7);foreign.addOuter(frame,returned(frame,I+0x2A327EC),List.of(new Mem(true,1,OLD+63,88)));foreign.throwOuter=true;
        try{execute(foreign);throw new AssertionError("foreign exception swallowed");}catch(RuntimeException expected){check(expected==foreign.marker);foreign.done();check(foreign.load(OLD+63,1)==88);}
        Script early=seeded(7,2);early.store(P+0x40,1,1);prologueWithoutFlag(early);early.read(1,P+0x40,1);early.read(8,I+0x5D1EC70,FALL);restored(early,11,55);
        var actual=(Normal)execute(early);early.done();check(actual.postMxcsr()==P0&&actual.base().postDirectionFlagSet()&&early.outerCalls==0&&early.innerCalls==0);
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(FALL,P-8,CTX,0xA8,ARG4,0xAA,0xAB,0xA0),RET,E+8,N)));}
    private static void prologueWithoutFlag(Script s){s.write(8,E+0x10,11);s.write(8,E+0x18,0xA8);s.write(8,E-8,22);s.write(8,E-0x10,33);
        s.write(8,E-0x18,44);s.write(8,E-0x20,55);s.write(8,E-0x28,66);s.write(8,E-0x30,77);s.write(8,E-0x38,88);}
    public static int verify(){actualNestedAllocatorStop();knownSetThenPageStop();opaqueNormalFreshRestore();rejectedAndForeignPrefixes();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
