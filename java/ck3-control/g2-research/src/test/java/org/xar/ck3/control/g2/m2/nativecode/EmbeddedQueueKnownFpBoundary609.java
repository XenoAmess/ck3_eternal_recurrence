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
public final class EmbeddedQueueKnownFpBoundary609 {
    private EmbeddedQueueKnownFpBoundary609() { }
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
    private static final Mxcsr PRE=Mxcsr.exact(0x1F80),P1=Mxcsr.exact(0x1F81),P2=new Mxcsr(0x1F80,0xFFC0);
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
    private static Outcome execute(Script s,Mxcsr state){return EmbeddedQueueWithKnownFp609.execute(input(s,state),s.memory,s::invoke);}
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
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
            target,E-0x58,before,saved);
        var child=new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,saved);
        return new AppendCallFrame(new QueueAppend597Api.CallFrame(call,child,df,3,I+ret),pre);
    }
    private static Normal returned(AppendCallFrame frame,VolatileBits after,boolean df,Mxcsr post){
        return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            after,frame.base().returnRipBits(),E-0x58,frame.base().call().nonvolatileBits()),df),post);}
    private static void normalComposition(){
        Script s=initial(0);appendPrefix(s);s.read(4,I+0x49F64F0L,0x3FC00000);
        s.read(8,A,T);s.read(8,T+8,ALLOC);s.write(8,E-0x60,I+0x8803A2);
        var alloc=frame(0x88039F,ALLOC,0x8803A2,v(T,A,8,8,0xA0,new Bits128(0,0)),n(H,1,1,44,PSTACK),true,PRE);
        var va=v(NEW,0xB1,0xB2,0xB8,0xB0,x(0xB0,0));s.steps.add(new Call(alloc,returned(alloc,va,false,P1)));
        s.read(4,H+12,0);s.read(8,PSTACK,O);s.write(8,NEW,O);s.read(4,H+12,0);
        s.read(8,H+16,A);s.read(8,H,OLD);s.read(8,A,T);s.read(8,T+16,FREE);s.write(8,E-0x60,I+0x8803DD);
        var free=frame(0x8803DA,FREE,0x8803DD,v(T,A,OLD,8,0xB0,x(0xB0,0)),n(H,1,1,NEW,PSTACK),false,P1);
        var vf=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));s.steps.add(new Call(free,returned(free,vf,true,P2)));
        s.write(4,H+8,1);s.read(8,E-0x28,22);s.write(8,H,NEW);s.write(4,H+12,1);
        s.read(8,E-0x20,O);s.read(8,E-0x18,33);s.read(8,E-0x10,44);s.read(8,E-0x38,77);
        s.read(8,E-0x30,I+0x3727F12);s.write(1,O+0x4E,1);s.write(4,LOCK,0);
        s.read(8,E-8,11);s.read(8,E,RET);
        Outcome result=execute(s,PRE);s.done();check(result instanceof Normal);
        var normal=(Normal)result;check(normal.postMxcsr()==P2&&normal.base().postDirectionFlagSet());
        check(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(NEW,0,0xD2,0xD8,0xD0,x(0xD0,0)),RET,E+8,N)));
        check(s.load(H,8)==NEW&&s.load(H+8,4)==1&&s.load(H+12,4)==1&&s.load(NEW,8)==O);
        check(s.load(LOCK,4)==0&&s.load(O+0x4E,1)==1);
    }
    private static void partialStateStopWhileLocked(){
        Script s=initial(0);appendPrefix(s);Mxcsr unknown=Mxcsr.unknown();Outcome result=execute(s,unknown);s.done();
        check(result instanceof Stopped);var stopped=(Stopped)result;
        check(stopped.reason()==StopReason.MISSING_FP_INPUT&&stopped.raisedConditionBits()==0);
        check(stopped.originCallSiteRva()==0x3727F0D&&stopped.snapshot().instructionRva()==0x880385);
        check(stopped.snapshot().directionFlagSet()&&stopped.snapshot().mxcsr()==unknown);
        check(stopped.snapshot().currentState().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x58,
            v(0,A,PSTACK,8,0xA0,new Bits128(0,0)),n(H,1,1,44,PSTACK))));
        check(s.load(LOCK,4)==1&&s.load(O+0x4E,1)==0&&s.load(H,8)==OLD&&s.load(H+12,4)==0);
        check(s.load(E-0x30,8)==I+0x3727F12&&s.load(E-8,8)==11); // no fake unwind
    }
    private static void originalBudgetFailure(){
        Script s=initial(0);classifierPrefix(s);s.failClassifierBudget=true;
        try{execute(s,PRE);throw new AssertionError("Expected original budget failure");}
        catch(RuntimeException actual){check(actual==s.marker);}
        s.done();check(s.load(LOCK,4)==0&&s.load(O+0x4E,1)==0&&s.load(H,8)==OLD);
    }
    private static void alreadyFlaggedUnknown(){
        Script s=initial(1);s.write(8,E-8,11);s.read(1,O+0x4E,1);s.read(8,E-8,11);s.read(8,E,RET);
        Mxcsr unknown=Mxcsr.unknown();var normal=(Normal)execute(s,unknown);s.done();
        check(normal.postMxcsr()==unknown&&normal.base().postDirectionFlagSet());
        check(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(V,RET,E+8,N)));
    }
    public static int verify(){normalComposition();partialStateStopWhileLocked();originalBudgetFailure();alreadyFlaggedUnknown();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
