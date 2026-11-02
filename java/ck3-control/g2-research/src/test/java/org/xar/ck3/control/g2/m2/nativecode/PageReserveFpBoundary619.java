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

/** Owner assembly of the private pre-POST oracle; no old suite or target-generated expected values. */
public final class PageReserveFpBoundary619 {
    private PageReserveFpBoundary619() { }
    private static final long I=0x140000000L,S=0x8300000000008000L,P=0x8300000000002000L,
        BAD=0xFACE000000000777L,RET=I+0x2A327EC;
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(1,1),P2=new Mxcsr(0x21,0xE1);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,long bank){return new VolatileBits(
        ax,cx,dx,r8,r9,r10,r11,x(bank,0),x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static NonvolatileBits n(long r14){return new NonvolatileBits(11,22,33,44,55,66,r14,88,x(0xA0,6));}
    private static final NonvolatileBits N=n(77);
    private static void check(boolean value){if(!value)throw new AssertionError("619 pre-POST literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Budget(long header,long guard) { }
    private record Invoke(KnownPageFp619.CallFrame frame,Outcome result,List<Mem> effects) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls;
        final RuntimeException marker=new IllegalStateException("619 foreign diagnostic exception");boolean throwCallback;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->event(new Budget(header,guard));
        final KnownPageFp619.Memory memory=(KnownPageFp619.Memory)Proxy.newProxyInstance(
            KnownPageFp619.Memory.class.getClassLoader(),new Class<?>[]{KnownPageFp619.Memory.class},(proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte")||name.equals("write8"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected619Memory "+name);
                long address=((Long)args[0]).longValue();boolean write=name.startsWith("write");
                long value=write?((Number)args[1]).longValue():load(address,width);
                event(new Mem(write,width,address,mask(width,value)));if(write){store(address,width,value);return null;}
                if(width==1)return Integer.valueOf((int)value&255);if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long value=0;for(int k=0;k<width;k++){
            Byte b=ram.get(address+k);if(b==null)throw new AssertionError("Unseeded619RAM "+Long.toHexString(address+k));value|=(b.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("619 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        void add(KnownPageFp619.CallFrame frame,Outcome outcome,List<Mem> effects){steps.add(new Invoke(frame,outcome,effects));steps.addAll(effects);}
        Outcome invoke(KnownPageFp619.CallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Invoke);
            Invoke expected=(Invoke)steps.get(cursor++);check(actual.equals(expected.frame())&&actual.preMxcsr()==expected.frame().preMxcsr());calls++;
            for(Mem effect:expected.effects()){check(effect.write());if(effect.width()==1)memory.writeByte(effect.address(),(int)effect.value());
                else if(effect.width()==8)memory.writeQword(effect.address(),effect.value());else throw new AssertionError("effect width");}
            if(throwCallback)throw marker;return expected.result();}
        void done(){check(cursor==steps.size());}
    }
    private static Script seeded(){Script s=new Script();s.store(S,8,RET);s.store(P+0x40,1,0);s.store(P+0xC,4,2);return s;}
    private static SlotProducerGrowthWithFp618.CallFrame frame(long request,long site,long target,long ret){
        VolatileBits before=v(0xA0,P,request,0xA8,0xA9,0xAA,0xAB,0xA0);
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,S+8,before,N);
        var original=new FullSlotProducer479Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,S,before,N),true,5,I+ret);
        return new SlotProducerGrowthWithFp618.CallFrame(original,P0);}
    private static SlotProducerGrowthWithFp618.CallFrame page(long request){return frame(request,0x2A327E7,0x2A321F0,0x2A327EC);}
    private static Outcome execute(Script s,long request){return KnownPageFp619.bind(s.memory,s.budget,s::invoke,
        original->{throw new AssertionError("Unexpected619foreign");}).invoke(page(request));}
    private static KnownPageFp619.CallFrame diagnostic(Script s){s.write(8,S-8,77);s.read(1,P+0x40,0);
        s.write(8,S-0x28,I+0x5D1DAD9);s.write(8,S-0x50,I+0x2A3221F);
        var before=v(I+0x5D1DAD9,I+0x45B64C8,0xFFFFFF,0xA8,0xA9,0xAA,0xAB,0xA0);
        var call=new GovernmentCrtBoundary185Api.Call(0x2A3221A,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x3F7AA40,S-0x48,before,n(P));
        var original=new FullPage495Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,S-0x50,before,n(P)),true,5,I+0x2A3221F);
        return new KnownPageFp619.CallFrame(original,P0);}
    private static VolatileBits callbackV(){return v(0xCDEF,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0);}
    private static Normal returned(){return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
        callbackV(),I+0x2A3221F,S-0x48,n(P)),false),P2);}
    private static void fastNormalSameUnknownState(){Script s=seeded();s.write(8,S-8,77);s.read(1,P+0x40,0);s.write(8,S+0x18,22);
        s.read(4,P+0xC,2);s.read(8,S+0x18,22);s.read(8,S-8,77);s.read(8,S,RET);
        var actual=(Normal)execute(s,2);s.done();check(s.calls==0&&actual.postMxcsr()==P0&&actual.base().postDirectionFlagSet());
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(0x801,P,2,0xA8,0xA9,0xAA,0xAB,0xA0),RET,S+8,N)));}
    private static void diagnosticStoppedPrefix(){Script s=seeded();var expectedFrame=diagnostic(s);
        var expected=new Stopped(StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(expectedFrame.original().childEntry(),0x2A3221A,true,P1),0,0x2A3221A);
        s.add(expectedFrame,expected,List.of(new Mem(true,1,P+0x70,123)));check(execute(s,0xFFFFFF)==expected);s.done();
        check(s.calls==1&&s.load(P+0x70,1)==123&&s.load(S-8,8)==77);}
    private static void diagnosticNormalPostState(){Script s=seeded();var expectedFrame=diagnostic(s);
        s.add(expectedFrame,returned(),List.of(new Mem(true,1,P+0x70,123)));s.read(8,S-8,77);s.read(8,S,RET);
        var actual=(Normal)execute(s,0xFFFFFF);s.done();check(s.calls==1&&actual.postMxcsr()==P2&&!actual.base().postDirectionFlagSet()&&s.load(P+0x70,1)==123);
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(0xCD00,0xC1,0xC2,0xC8,0xC9,0xCA,0xCB,0xC0),RET,S+8,N)));}
    private static void aliasGuardForeignAndDelegate(){Script alias=seeded();var f=diagnostic(alias);alias.add(f,returned(),List.of(new Mem(true,8,S-8,BAD)));
        alias.read(8,S-8,BAD);alias.read(8,S,RET);try{execute(alias,0xFFFFFF);throw new AssertionError("outer NR alias accepted");}
        catch(IllegalArgumentException expected){alias.done();check(alias.load(S-8,8)==BAD);}
        Script foreign=seeded();var ff=diagnostic(foreign);foreign.add(ff,returned(),List.of(new Mem(true,1,P+0x70,88)));foreign.throwCallback=true;
        try{execute(foreign,0xFFFFFF);throw new AssertionError("foreign exception swallowed");}
        catch(RuntimeException expected){check(expected==foreign.marker);foreign.done();check(foreign.load(P+0x70,1)==88);}
        Script delegated=seeded();var original=frame(2,0x2A328C4,0x3076B60,0x2A328C9);
        var expected=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            callbackV(),I+0x2A328C9,S+8,N),false),P2);
        var actual=KnownPageFp619.bind(delegated.memory,delegated.budget,unused->{throw new AssertionError("nonmatch page execution");},
            offered->{check(offered==original);return expected;}).invoke(original);
        check(actual==expected&&delegated.calls==0);delegated.done();}
    public static int verify(){fastNormalSameUnknownState();diagnosticStoppedPrefix();diagnosticNormalPostState();aliasGuardForeignAndDelegate();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
