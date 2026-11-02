package org.xar.ck3.control.g2.m2.nativecode;

import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner literal new103->actual81+FP-aware227 composition. Mechanical strictRAM/cursor
 * foundation adapted from owner608 fixture; no old Test/execute-generated oracle. */
public final class EmbeddedQueuePartialFpBoundary611 {
    private EmbeddedQueuePartialFpBoundary611() { }
    private static final long I=0x140000000L,E=0x8100000000008000L,O=0x8100000000001000L,
        PV=0x8100000000002000L,OLD=0x8100000000003000L,NEW=0x8100000000004000L,
        A=0x8100000000005000L,T=0x8100000000006000L,H=I+0x5468A68L,
        LOCK=I+0x5C9FF68L,ALLOC=0xF000000000000111L,FREE=0xF000000000000222L,
        RET=0xF100000000000333L,PSTACK=E+0x10;
    private static Bits128 x(long bank,int lane) {return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long bank,Bits128 x0) {
        return new VolatileBits(ax,cx,dx,r8,bank+9,bank+10,bank+11,x0,
            x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));
    }
    private static NonvolatileBits n(long bx,long bp,long si,long di,long r14) {
        return new NonvolatileBits(bx,bp,si,di,55,66,r14,88,x(0xA0,6));
    }
    private static final VolatileBits V=v(0xA0,O,0xA2,0xA8,0xA0,x(0xA0,0));
    private static final NonvolatileBits N=n(11,22,33,44,77);
    private static final Mxcsr P1=new Mxcsr(1,1),P2=new Mxcsr(0x21,0x21),P3=new Mxcsr(0x21,0xE1);
    private static void check(boolean ok){if(!ok)throw new AssertionError("609 source literal mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record Cas(long address,int expected,int desired,int old) { }
    private record Budget(long header,long guard) { }
    private record Call(AppendCallFrame frame,Normal result) { }
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor;
        final RuntimeException marker=new IllegalStateException("original budget identity");
        boolean failClassifierBudget;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            event(new Budget(header,guard));
            if(failClassifierBudget&&header==0x37275B0)throw marker;
        };
        final EmbeddedQueueFp609Api.Memory memory=(EmbeddedQueueFp609Api.Memory)Proxy.newProxyInstance(
            EmbeddedQueueFp609Api.Memory.class.getClassLoader(),new Class<?>[]{EmbeddedQueueFp609Api.Memory.class},
            (proxy,method,args)->{
                String name=method.getName();long address=((Long)args[0]).longValue();
                if(name.equals("compareExchangeDword")) {
                    int expected=((Integer)args[1]).intValue(),desired=((Integer)args[2]).intValue();
                    int old=(int)load(address,4);event(new Cas(address,expected,desired,old));
                    if(old==expected)store(address,4,desired);return Integer.valueOf(old);
                }
                int width;
                if(name.equals("readUnsignedByte")||name.equals("writeByte"))width=1;
                else if(name.equals("readDword")||name.equals("writeDword"))width=4;
                else if(name.equals("readQword")||name.equals("writeQword"))width=8;
                else throw new AssertionError("Unexpected Memory port "+name);
                boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);
                event(new Mem(write,width,address,mask(width,value)));
                if(write){store(address,width,value);return null;}
                if(width==1)return Integer.valueOf((int)value&255);
                if(width==4)return Integer.valueOf((int)value);
                return Long.valueOf(value);
            });
        void store(long address,int width,long value){for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long address,int width){long result=0;for(int k=0;k<width;k++){
            Byte b=ram.get(address+k);if(b==null)throw new AssertionError("Unseeded609RAM "+Long.toHexString(address+k));
            result|=(b.byteValue()&255L)<<(8*k);}return result;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))
            throw new AssertionError("609 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long address,long value){steps.add(new Mem(false,width,address,mask(width,value)));}
        void write(int width,long address,long value){steps.add(new Mem(true,width,address,mask(width,value)));}
        Outcome invoke(AppendCallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Call);
            Call call=(Call)steps.get(cursor++);check(actual.equals(call.frame()));return call.result();}
        void done(){check(cursor==steps.size());}
    }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static Script initial(int flag){Script s=new Script();s.store(E,8,RET);s.store(O+0x4E,1,flag);
        s.store(O+0x1C,4,0);s.store(O+0x30,8,PV);s.store(O+0x3C,4,1);s.store(PV+0x44,1,1);
        s.store(O+0x48,4,-1);s.store(LOCK,4,0);s.store(H,8,OLD);s.store(H+8,4,0);s.store(H+12,4,0);
        s.store(H+16,8,A);s.store(A,8,T);s.store(T+8,8,ALLOC);s.store(T+16,8,FREE);
        s.store(I+0x49F64F0L,4,0x3FC00000);return s;}
    private static QueueFp604Api.Input input(Script s,Mxcsr state){return new QueueFp604Api.Input(
        new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,V,N),true,s.budget),state);}
    private static Outcome execute(Script s,Mxcsr state){return EmbeddedQueueWithPartialFp611.execute(input(s,state),s.memory,s::invoke);}
    private static void classifierPrefix(Script s){
        s.write(8,E-8,11);s.read(1,O+0x4E,0);s.write(8,E-0x30,I+0x3727ED4);
        s.read(4,O+0x1C,0);s.read(8,O+0x30,PV);s.read(4,O+0x3C,1);
        s.steps.add(new Budget(0x37275B0,PV));
    }
    private static void appendPrefix(Script s){
        classifierPrefix(s);s.read(1,PV+0x44,1);s.read(8,E-0x30,I+0x3727ED4);
        s.read(4,O+0x48,-1);s.steps.add(new Budget(0x3727EE4,LOCK));s.read(4,LOCK,0);
        s.steps.add(new Cas(LOCK,0,1,0));s.write(8,PSTACK,O);s.write(8,E-0x30,I+0x3727F12);
        s.write(8,E-0x20,O);s.write(8,E-0x18,33);s.write(8,E-0x10,44);s.write(8,E-0x38,77);
        s.read(4,H+12,0);s.read(4,H+8,0);s.read(8,H+16,A);s.write(8,E-0x28,22);
    }
    private static AppendCallFrame frame(long site,long target,long ret,VolatileBits before,NonvolatileBits saved,boolean df,Mxcsr pre){
        var call=new GovernmentCrtBoundary185Api.Call(site,site==0x8803C5?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
            target,E-0x58,before,saved);
        var child=new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,saved);
        return new AppendCallFrame(new QueueAppend597Api.CallFrame(call,child,df,site==0x8803C5?5:3,I+ret),pre);
    }
    private static Normal returned(AppendCallFrame frame,VolatileBits after,boolean df,Mxcsr post){
        return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            after,frame.base().returnRipBits(),E-0x58,frame.base().call().nonvolatileBits()),df),post);}
    private static Script seeded(int count,int factor){
        Script s=initial(0);s.store(H+8,4,count);s.store(H+12,4,count);s.store(I+0x49F64F0L,4,factor);return s;
    }
    private static void partialPrefix(Script s,int count){
        classifierPrefix(s);s.read(1,PV+0x44,1);s.read(8,E-0x30,I+0x3727ED4);
        s.read(4,O+0x48,-1);s.steps.add(new Budget(0x3727EE4,LOCK));s.read(4,LOCK,0);
        s.steps.add(new Cas(LOCK,0,1,0));s.write(8,PSTACK,O);s.write(8,E-0x30,I+0x3727F12);
        s.write(8,E-0x20,O);s.write(8,E-0x18,33);s.write(8,E-0x10,44);s.write(8,E-0x38,77);
        s.read(4,H+12,count);s.read(4,H+8,count);s.read(8,H+16,A);s.write(8,E-0x28,22);
    }
    private static void positiveUnknownAllThree(){
        Script s=seeded(2,0x3FC00000);partialPrefix(s,2);Mxcsr unknown=Mxcsr.unknown();
        s.read(4,I+0x49F64F0L,0x3FC00000);s.read(8,A,T);s.read(8,T+8,ALLOC);s.write(8,E-0x60,I+0x8803A2);
        var alloc=frame(0x88039F,ALLOC,0x8803A2,v(T,A,24,8,0xA0,new Bits128(0x40400000,0)),n(H,3,3,44,PSTACK),true,unknown);
        var va=v(NEW,0xB1,0xB2,0xB8,0xB0,x(0xB0,0));s.steps.add(new Call(alloc,returned(alloc,va,false,P1)));
        s.read(4,H+12,2);s.read(8,PSTACK,O);s.write(8,NEW+16,O);s.read(4,H+12,2);s.read(8,H,OLD);
        s.write(8,E-0x60,I+0x8803CA);
        var copy=frame(0x8803C5,0x4226860,0x8803CA,v(2,NEW,OLD,16,0xB0,x(0xB0,0)),n(H,3,3,NEW,PSTACK),false,P1);
        var vc=v(0xC0,0xC1,0xC2,0xC8,0xC0,x(0xC0,0));s.steps.add(new Call(copy,returned(copy,vc,true,P2)));
        s.read(8,H+16,A);s.read(8,H,OLD);s.read(8,A,T);s.read(8,T+16,FREE);s.write(8,E-0x60,I+0x8803DD);
        var free=frame(0x8803DA,FREE,0x8803DD,v(T,A,OLD,8,0xC0,x(0xC0,0)),n(H,3,3,NEW,PSTACK),true,P2);
        var vf=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));s.steps.add(new Call(free,returned(free,vf,false,P3)));
        s.write(4,H+8,3);s.read(8,E-0x28,22);s.write(8,H,NEW);s.write(4,H+12,3);
        s.read(8,E-0x20,O);s.read(8,E-0x18,33);s.read(8,E-0x10,44);s.read(8,E-0x38,77);
        s.read(8,E-0x30,I+0x3727F12);s.write(1,O+0x4E,1);s.write(4,LOCK,0);s.read(8,E-8,11);s.read(8,E,RET);
        var result=(Normal)execute(s,unknown);s.done();check(result.postMxcsr()==P3&&!result.base().postDirectionFlagSet());
        check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(NEW+16,2,0xD2,0xD8,0xD0,x(0xD0,0)),RET,E+8,N)));
        check(s.load(H,8)==NEW&&s.load(H+8,4)==3&&s.load(H+12,4)==3&&s.load(NEW+16,8)==O);
        check(s.load(O+0x4E,1)==1&&s.load(LOCK,4)==0);
    }
    private static void unsupported(int count,int factor,int cvtBits){
        Script s=seeded(count,factor);partialPrefix(s,count);s.read(4,I+0x49F64F0L,factor);
        Mxcsr unknown=Mxcsr.unknown();var result=(Stopped)execute(s,unknown);s.done();
        check(result.reason()==StopReason.UNSUPPORTED_FP_DOMAIN&&result.raisedConditionBits()==0);
        check(result.originCallSiteRva()==0x3727F0D&&result.snapshot().instructionRva()==0x880385);
        check(result.snapshot().directionFlagSet()&&result.snapshot().mxcsr()==unknown);
        long next=Integer.toUnsignedLong(count+1);
        check(result.snapshot().currentState().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x58,
            v(count,A,PSTACK,8,0xA0,new Bits128(Integer.toUnsignedLong(cvtBits),0)),n(H,next,next,44,PSTACK))));
        check(s.load(LOCK,4)==1&&s.load(O+0x4E,1)==0&&s.load(H,8)==OLD&&s.load(H+12,4)==Integer.toUnsignedLong(count));
    }
    private static void encoded(boolean negative,long coefficient,int exponent,int expected){
        var actual=QueueExactNormalProduct611.encode(new QueueFiniteProduct606.Product(negative,coefficient,exponent));
        check(actual.isPresent()&&actual.getAsInt()==expected);
    }
    private static void empty(long coefficient,int exponent){
        check(QueueExactNormalProduct611.encode(new QueueFiniteProduct606.Product(false,coefficient,exponent)).isEmpty());
    }
    private static void predicateLiterals(){
        encoded(false,0,-149,0);encoded(true,0,104,0x80000000);
        encoded(false,0x1800000,-23,0x40400000);encoded(true,0x1800000,-23,0xC0400000);
        encoded(false,1,-126,0x00800000);empty(1,-127);
        encoded(false,0xFFFFFF,104,0x7F7FFFFF);empty(0x1000000,104); // prePOSToracleerratum validProduct
        empty(0x1000001,0);encoded(false,0x1000000,0,0x4B800000);
    }
    private static void stickyAndReadFailure(){
        for(int mode:new int[]{0,1}){
            var v0=v(0xA0,O,0xA2,0xA8,0xA0,new Bits128(0x40000000,0));
            var r=org.xar.ck3.research.m5.GovernmentCallee164Api.registers(
                new org.xar.ck3.research.m5.GovernmentCallee164Api.Entry(I,E,v0,N));
            int[] reads={0};RuntimeException marker=new IllegalStateException("freshfactor identity");
            final int which=mode;
            var memory=(QueueAppend597Api.Memory)Proxy.newProxyInstance(QueueAppend597Api.Memory.class.getClassLoader(),
                new Class<?>[]{QueueAppend597Api.Memory.class},(proxy,method,args)->{
                    check(method.getName().equals("readDword")&&((Long)args[0]).longValue()==I+0x49F64F0L);
                    check(++reads[0]==1&&r.volatileBits().equals(v0)&&r.nonvolatileBits().equals(N)&&r.rsp==E);
                    if(which==1)throw marker;return Integer.valueOf(0x3FC00000);
                });
            Mxcsr state=new Mxcsr(0x21,0xA1); // oldIE/PE, IM known0, remainingcontrolsunknown
            try{
                var result=QueueGrowthPartialMulss611.execute(I,r,true,state,0x3727F0D,memory);
                check(mode==0&&result instanceof QueueGrowthMulss606.Completed);
                check(((QueueGrowthMulss606.Completed)result).mxcsr()==state);
                check(r.volatileBits().equals(v(0xA0,O,0xA2,0xA8,0xA0,new Bits128(0x40400000,0))));
            }catch(RuntimeException actual){check(mode==1&&actual==marker&&r.volatileBits().equals(v0));}
            check(reads[0]==1&&r.nonvolatileBits().equals(N)&&r.rsp==E);
        }
    }
    public static int verify(){predicateLiterals();positiveUnknownAllThree();
        unsupported(16777215,0x3FC00000,0x4B7FFFFF);unsupported(2,1,0x40000000);
        stickyAndReadFailure();return 5;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
