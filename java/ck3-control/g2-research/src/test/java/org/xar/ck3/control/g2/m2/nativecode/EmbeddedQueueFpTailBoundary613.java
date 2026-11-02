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

/** Owner new upper103/partial227 -> actual COPY16..32 compositions and strict prefixes.
 * Mechanical strict RAM/cursor source reused; no old case invoked or target-derived expected trace. */
public final class EmbeddedQueueFpTailBoundary613 {
    private EmbeddedQueueFpTailBoundary613() { }
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
    private record VectorMem(boolean write,long address,Bits128 value) { }
    private record TailEvent(FullCopyWithFp613.TailCall frame) { }
    private record Cas(long address,int expected,int desired,int old) { }
    private record Budget(long header,long guard) { }
    private record Call(AppendCallFrame frame,Normal result) { }
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor;
        final RuntimeException marker=new IllegalStateException("original budget identity");
        boolean failClassifierBudget,failCopyRead,failCopyBudget,throwTail;long copySource;
        FullCopyWithFp613.TailCall expectedTail;Outcome tailOutcome;int tailCount;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            event(new Budget(header,guard));
            if(failClassifierBudget&&header==0x37275B0)throw marker;
            if(failCopyBudget&&header==0x4226CF0)throw marker;
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
                if(name.equals("read128")) {
                    Bits128 value=new Bits128(load(address,8),load(address+8,8));
                    event(new VectorMem(false,address,value));
                    if(failCopyRead&&address==copySource)throw marker;
                    return value;
                }
                if(name.equals("write128")) {
                    Bits128 value=(Bits128)args[1];event(new VectorMem(true,address,value));
                    store(address,8,value.lowBits());store(address+8,8,value.highBits());return null;
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
            Call call=(Call)steps.get(cursor++);check(actual.equals(call.frame()));check(actual.preMxcsr()==call.frame().preMxcsr());return call.result();}
        Outcome tail(FullCopyWithFp613.TailCall actual) {
            check(actual.equals(expectedTail)&&actual.preMxcsr()==expectedTail.preMxcsr());
            event(new TailEvent(actual));check(++tailCount==1);
            if(throwTail)throw marker;return tailOutcome;
        }
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
    private static Outcome execute(Script s,Mxcsr state){return EmbeddedQueueWithKnownFpCopy613.execute(input(s,state),s.memory,s::invoke,s::tail);}
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
    private static void prefix(Script s,int count) {
        classifierPrefix(s);s.read(1,PV+0x44,1);s.read(8,E-0x30,I+0x3727ED4);
        s.read(4,O+0x48,-1);s.steps.add(new Budget(0x3727EE4,LOCK));s.read(4,LOCK,0);
        s.steps.add(new Cas(LOCK,0,1,0));s.write(8,PSTACK,O);s.write(8,E-0x30,I+0x3727F12);
        s.write(8,E-0x20,O);s.write(8,E-0x18,33);s.write(8,E-0x10,44);s.write(8,E-0x38,77);
        s.read(4,H+12,count);s.read(4,H+8,count);s.read(8,H+16,A);s.write(8,E-0x28,22);
    }
    private static void prepareCopy(Script s,int count,int capacity,int mulBits,long old,long destination) {
        prefix(s,count);Mxcsr unknown=UNKNOWN;
        s.read(4,I+0x49F64F0L,0x3FC00000);s.read(8,A,T);s.read(8,T+8,ALLOC);
        s.write(8,E-0x60,I+0x8803A2);
        var alloc=frame(0x88039F,ALLOC,0x8803A2,
            v(T,A,capacity*8L,8,0xA0,new Bits128(mulBits,0)),n(H,capacity,count+1L,44,PSTACK),true,unknown);
        var va=v(destination,0xB1,0xB2,0xB8,0xB0,x(0xB0,0));
        s.steps.add(new Call(alloc,returned(alloc,va,false,P1)));
        s.read(4,H+12,count);s.read(8,PSTACK,O);s.write(8,destination+count*8L,O);
        s.read(4,H+12,count);s.read(8,H,old);s.write(8,E-0x60,I+0x8803CA);
    }
    private static void finish(Script s,int count,int capacity,long old,long destination,VolatileBits afterCopy,boolean df,Mxcsr state) {
        s.read(8,H+16,A);s.read(8,H,old);s.read(8,A,T);s.read(8,T+16,FREE);
        s.write(8,E-0x60,I+0x8803DD);
        var beforeFree=new VolatileBits(T,A,old,8,afterCopy.r9Bits(),afterCopy.r10Bits(),afterCopy.r11Bits(),
            afterCopy.xmm0(),afterCopy.xmm1(),afterCopy.xmm2(),afterCopy.xmm3(),afterCopy.xmm4(),afterCopy.xmm5());
        var free=frame(0x8803DA,FREE,0x8803DD,beforeFree,n(H,capacity,count+1L,destination,PSTACK),df,state);
        var vf=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));
        s.steps.add(new Call(free,returned(free,vf,false,P3)));
        s.write(4,H+8,capacity);s.read(8,E-0x28,22);s.write(8,H,destination);s.write(4,H+12,count+1L);
        s.read(8,E-0x20,O);s.read(8,E-0x18,33);s.read(8,E-0x10,44);s.read(8,E-0x38,77);
        s.read(8,E-0x30,I+0x3727F12);s.write(1,O+0x4E,1);s.write(4,LOCK,0);s.read(8,E-8,11);s.read(8,E,RET);
    }
    private static void checkResult(Script s,Outcome outcome,int count,int capacity,long destination) {
        s.done();var result=(Normal)outcome;check(result.postMxcsr()==P3&&!result.base().postDirectionFlagSet());
        check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(destination+count*8L,count,0xD2,0xD8,0xD0,x(0xD0,0)),RET,E+8,N)));
        check(s.load(H,8)==destination&&s.load(H+8,4)==capacity&&s.load(H+12,4)==count+1L);
        check(s.load(destination+count*8L,8)==O&&s.load(LOCK,4)==0&&s.load(O+0x4E,1)==1);
    }
    private static final Mxcsr UNKNOWN=Mxcsr.unknown();
    private static final long W0=0x1111222233334444L,W1=0x5555666677778888L,
        W2=0x2222333344445555L,W3=0x6666777788889999L,
        W4=0x3333444455556666L,W5=0x777788889999AAAAL,F=0x12345678L;
    private static final Bits128 HEAD=new Bits128(W0,W1),MID=new Bits128(W2,W3),LAST=new Bits128(W4,W5);
    private static Script seeded(){Script s=initial(0);s.store(H+8,4,6);s.store(H+12,4,6);
        s.store(OLD,8,W0);s.store(OLD+8,8,W1);s.store(OLD+16,8,W2);s.store(OLD+24,8,W3);
        s.store(OLD+32,8,W4);s.store(OLD+40,8,W5);s.store(I+0x542F098,4,0);
        s.store(I+0x6090094,4,0x4226DBF);return s;}
    private static VolatileBits sseCurrent(long tableTarget) {
        return new VolatileBits(NEW,NEW,OLD,48,48,I,I+tableTarget,HEAD,
            x(0xB0,1),x(0xB0,2),x(0xB0,3),x(0xB0,4),LAST);
    }
    private static void ssePrefix(Script s,long tableTarget) {
        s.read(4,I+0x542F098,0);s.steps.add(new VectorMem(false,OLD,HEAD));
        s.steps.add(new VectorMem(false,OLD+32,LAST));s.read(4,I+0x6090094,tableTarget);
    }
    private static FullCopyWithFp613.TailCall tail(long pc,long target,long sp,VolatileBits current,
            NonvolatileBits saved,boolean df,Mxcsr state) {
        var transfer=new GovernmentCrtBoundary185Api.Tail(pc,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
            I+target,new GovernmentCrtBoundary185Api.Entry(I,sp,current,saved));
        return new FullCopyWithFp613.TailCall(new FullCopy437Api.TailFrame(transfer,df),state);
    }
    private static void realSse48() {
        Script s=seeded();prepareCopy(s,6,9,0x41100000,OLD,NEW);ssePrefix(s,0x4226DBF);
        s.steps.add(new VectorMem(false,OLD,HEAD));s.steps.add(new VectorMem(true,NEW,HEAD));
        s.steps.add(new VectorMem(false,OLD+16,MID));s.steps.add(new VectorMem(true,NEW+16,MID));
        s.steps.add(new VectorMem(true,NEW+32,LAST));s.steps.add(new VectorMem(true,NEW,HEAD));
        s.read(8,E-0x60,I+0x8803CA);
        var after=new VolatileBits(NEW,NEW,OLD,48,48,I,I+0x4226DBF,HEAD,MID,
            x(0xB0,2),x(0xB0,3),x(0xB0,4),LAST);
        finish(s,6,9,OLD,NEW,after,false,P1);checkResult(s,execute(s,UNKNOWN),6,9,NEW);
        check(s.tailCount==0&&s.load(NEW,8)==W0&&s.load(NEW+8,8)==W1&&s.load(NEW+16,8)==W2);
        check(s.load(NEW+24,8)==W3&&s.load(NEW+32,8)==W4&&s.load(NEW+40,8)==W5);
    }
    private static QueueFp604Api.Input directInput(Script s,long bytes) {
        return new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,
            v(0xA0,NEW,OLD,bytes,0xA0,x(0xA0,0)),N),true,s.budget),UNKNOWN);
    }
    private static Script smallUnknownTail() {
        Script s=initial(0);s.store(I+0x6090014,4,F);s.read(4,I+0x6090014,F);
        var current=new VolatileBits(NEW,NEW,OLD,5,I+F,I,0xAB,x(0xA0,0),x(0xA0,1),
            x(0xA0,2),x(0xA0,3),x(0xA0,4),x(0xA0,5));
        s.expectedTail=tail(0x422688B,F,E,current,N,true,UNKNOWN);
        s.steps.add(new TailEvent(s.expectedTail));return s;
    }
    private static Stopped stopped(FullCopyWithFp613.TailCall frame,long pc) {
        return new Stopped(StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(
            frame.original().transfer().entry(),pc,frame.original().directionFlagSet(),frame.preMxcsr()),0,0x8803C5);
    }
    private static void directTailNormalIdentity() {
        Script s=smallUnknownTail();var expected=new Normal(new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(v(0xB0,0xB1,0xB2,0xB8,0xB0,x(0xB0,0)),RET,E+8,N),false),P2);
        s.tailOutcome=expected;var actual=FullCopyWithFp613.execute(directInput(s,5),s.memory,s::tail);
        check(actual==expected);s.done();check(s.tailCount==1);
    }
    private static void directTailStoppedIdentity() {
        Script s=smallUnknownTail();var expected=stopped(s.expectedTail,0x422688B);s.tailOutcome=expected;
        check(FullCopyWithFp613.execute(directInput(s,5),s.memory,s::tail)==expected);s.done();check(s.tailCount==1);
    }
    private static void upperTailStopBeforeFree() {
        Script s=seeded();s.store(I+0x6090094,4,F);prepareCopy(s,6,9,0x41100000,OLD,NEW);ssePrefix(s,F);
        s.expectedTail=tail(0x4226D76,F,E-0x60,sseCurrent(F),n(H,9,7,NEW,PSTACK),false,P1);
        s.steps.add(new TailEvent(s.expectedTail));var expected=stopped(s.expectedTail,0x4226D76);s.tailOutcome=expected;
        check(execute(s,UNKNOWN)==expected);s.done();check(s.tailCount==1);
        check(s.load(NEW+48,8)==O&&s.load(E-0x60,8)==I+0x8803CA);
        check(s.load(H,8)==OLD&&s.load(H+8,4)==6&&s.load(H+12,4)==6&&s.load(LOCK,4)==1&&s.load(O+0x4E,1)==0);
    }
    private static void foreignTailIdentity() {
        Script s=smallUnknownTail();s.throwTail=true;
        try {FullCopyWithFp613.execute(directInput(s,5),s.memory,s::tail);throw new AssertionError("tail marker must propagate");}
        catch(RuntimeException actual){check(actual==s.marker);s.done();}check(s.tailCount==1);
    }
    private static void originalBudgetPrefixIdentity() {
        Script s=initial(0);s.store(I+0x542F098,4,0);
        s.store(OLD,8,W0);s.store(OLD+8,8,W1);s.store(OLD+241,8,W4);s.store(OLD+249,8,W5);
        s.failCopyBudget=true;s.read(4,I+0x542F098,0);s.steps.add(new VectorMem(false,OLD,HEAD));
        s.steps.add(new VectorMem(false,OLD+241,LAST));s.steps.add(new Budget(0x4226CF0,NEW+16));
        try {FullCopyWithFp613.execute(directInput(s,257),s.memory,s::tail);throw new AssertionError("original budget must propagate");}
        catch(RuntimeException actual){check(actual==s.marker);s.done();}check(s.tailCount==0);
    }
    public static int verify(){realSse48();directTailNormalIdentity();directTailStoppedIdentity();
        upperTailStopBeforeFree();foreignTailIdentity();originalBudgetPrefixIdentity();return 6;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
