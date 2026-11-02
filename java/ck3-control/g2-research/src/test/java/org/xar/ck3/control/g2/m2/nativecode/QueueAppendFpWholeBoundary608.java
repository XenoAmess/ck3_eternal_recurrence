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
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner source-literal new FP-aware whole-entry checks. One strict RAM and global
 * Memory/CALL cursor; no execution-generated expectations or callee algorithm. */
public final class QueueAppendFpWholeBoundary608 {
    private QueueAppendFpWholeBoundary608() { }
    private static final long I=0x140000000L,E=0x8100000000008000L,H=0x8100000000001000L,
        S=0x8100000000002000L,OLD=0x8100000000003000L,NEW=0x8100000000004000L,
        A=0x8100000000005000L,T=0x8100000000006000L,A2=0x8100000000007000L,
        T2=0x8100000000009000L,OLD2=OLD+0x100,ALLOC=0xF000000000000111L,
        FREE=0xF000000000000222L,RET=0xF100000000000333L,RET2=RET+1,VALUE=0xAABBCCDD11223344L;
    private static final long ORIGIN=0x3727F0D;
    private static final NonvolatileBits N=n(11,22,33,44,77);
    private static final Mxcsr PRE=Mxcsr.exact(0x1F80),P1=Mxcsr.exact(0x1F81),
        P2=new Mxcsr(0x1F80,0xFFC0),P3=new Mxcsr(0x1FA0,0xFFE0);
    private static Bits128 x(long bank,int lane) {
        return new Bits128(bank+lane,0xD000000000000000L+bank+lane);
    }
    private static VolatileBits v(long ax,long cx,long dx,long r8,long bank,Bits128 x0) {
        return new VolatileBits(ax,cx,dx,r8,bank+9,bank+10,bank+11,x0,
            x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));
    }
    private static final VolatileBits V=v(0xA0,H,S,0xA8,0xA0,x(0xA0,0));
    private static NonvolatileBits n(long bx,long bp,long si,long di,long r14) {
        return new NonvolatileBits(bx,bp,si,di,55,66,r14,88,x(0xA0,6));
    }
    private static void check(boolean ok) { if(!ok)throw new AssertionError("608 source literal mismatch"); }
    private record Mem(boolean write,int width,long address,long value) { }
    private record Call(AppendCallFrame frame,Outcome result,RuntimeException failure,List<Mem> effects) { }
    private static final class Script {
        final List<Object> steps=new ArrayList<>();
        final Map<Long,Byte> ram=new HashMap<>();
        int cursor;
        final QueueAppend597Api.Memory memory=(QueueAppend597Api.Memory)Proxy.newProxyInstance(
            QueueAppend597Api.Memory.class.getClassLoader(),new Class<?>[]{QueueAppend597Api.Memory.class},
            (proxy,method,args)->{
                String name=method.getName();int width;
                if(name.equals("readDword")||name.equals("writeDword"))width=4;
                else if(name.equals("readQword")||name.equals("writeQword"))width=8;
                else throw new AssertionError("Unexpected Memory port "+name);
                boolean write=name.startsWith("write");long address=((Long)args[0]).longValue();
                long value=write?((Number)args[1]).longValue():load(address,width);
                event(new Mem(write,width,address,width==4?value&0xFFFFFFFFL:value));
                if(write){store(address,width,value);return null;}
                if(width==4)return Integer.valueOf((int)value);
                return Long.valueOf(value);
            });
        void store(long address,int width,long value) {
            for(int k=0;k<width;k++)ram.put(address+k,Byte.valueOf((byte)(value>>>(8*k))));
        }
        long load(long address,int width) {
            long value=0;
            for(int k=0;k<width;k++) {
                Byte b=ram.get(address+k);if(b==null)throw new AssertionError("Unseeded RAM "+Long.toHexString(address+k));
                value|=(b.byteValue()&255L)<<(8*k);
            }
            return value;
        }
        void event(Object actual) {
            if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))
                throw new AssertionError("608 global event "+(cursor-1)+" actual="+actual);
        }
        void read(int width,long address,long value) {steps.add(new Mem(false,width,address,width==4?value&0xFFFFFFFFL:value));}
        void write(int width,long address,long value) {steps.add(new Mem(true,width,address,width==4?value&0xFFFFFFFFL:value));}
        void call(AppendCallFrame frame,Outcome result,RuntimeException failure,Mem...effects) {
            steps.add(new Call(frame,result,failure,List.of(effects)));
            steps.addAll(List.of(effects));
        }
        Outcome invoke(AppendCallFrame actual) {
            check(cursor<steps.size()&&steps.get(cursor) instanceof Call);
            Call call=(Call)steps.get(cursor++);check(actual.equals(call.frame()));
            if(call.failure()!=null)throw call.failure();
            for(Mem effect:call.effects()) {
                if(effect.width()==4)memory.writeDword(effect.address(),(int)effect.value());
                else memory.writeQword(effect.address(),effect.value());
            }
            return call.result();
        }
        void done(){check(cursor==steps.size());}
    }
    private static QueueFp604Api.Input input(Mxcsr state) {
        return new QueueFp604Api.Input(new FullCopy437Api.Input(
            new GovernmentCrtBoundary185Api.Entry(I,E,V,N),true,(site,header)->{
                throw new AssertionError("227 has no own budget loop");
            }),state);
    }
    private static AppendCallFrame frame(long site,long target,int length,long ret,
            VolatileBits before,NonvolatileBits saved,boolean df,Mxcsr pre) {
        var kind=site==0x8803C5?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
        var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,E-0x28,before,saved);
        var child=new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,saved);
        return new AppendCallFrame(new QueueAppend597Api.CallFrame(call,child,df,length,I+ret),pre);
    }
    private static Normal returned(AppendCallFrame frame,VolatileBits after,boolean df,Mxcsr post) {
        return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            after,frame.base().returnRipBits(),E-0x28,frame.base().call().nonvolatileBits()),df),post);
    }
    private static Script initial(int count,int capacity,int factor) {
        Script s=new Script();s.store(H,8,OLD);s.store(H+8,4,capacity);s.store(H+12,4,count);
        s.store(H+16,8,A);s.store(A,8,T);s.store(T+8,8,ALLOC);s.store(T+16,8,FREE);
        s.store(S,8,0x1234);s.store(E,8,RET);s.store(I+0x49F64F0L,4,factor);
        s.write(8,E+0x10,11);s.write(8,E+0x18,33);s.write(8,E+0x20,44);s.write(8,E-8,77);
        s.read(4,H+12,count);s.read(4,H+8,capacity);
        return s;
    }
    private static VolatileBits beforeAlloc(long bytes,int floatBits) {
        return v(T,A,bytes,8,0xA0,new Bits128(Integer.toUnsignedLong(floatBits),0));
    }
    private static void fpPrefix(Script s,int factor) {
        s.read(8,H+16,A);s.write(8,E+8,22);s.read(4,I+0x49F64F0L,factor);
        s.read(8,A,T);s.read(8,T+8,ALLOC);s.write(8,E-0x30,I+0x8803A2);
    }
    private static Outcome execute(Script s,Mxcsr pre) {
        return QueueAppendFpWhole608.execute(input(pre),s.memory,s::invoke,ORIGIN);
    }
    private static void wholePositiveAlias() {
        Script s=initial(2,2,0x3FC00000);s.store(A2,8,T2);s.store(T2+16,8,FREE+1);fpPrefix(s,0x3FC00000);
        var alloc=frame(0x88039F,ALLOC,3,0x8803A2,beforeAlloc(24,0x40400000),n(H,3,3,44,S),true,PRE);
        var va=v(NEW,0xB1,0xB2,0xB8,0xB0,x(0xB0,0));
        s.call(alloc,returned(alloc,va,false,P1),null,new Mem(true,4,H+12,1),new Mem(true,8,S,VALUE));
        s.read(4,H+12,1);s.read(8,S,VALUE);s.write(8,NEW+8,VALUE);s.read(4,H+12,1);s.read(8,H,OLD);
        s.write(8,E-0x30,I+0x8803CA);
        var copy=frame(0x8803C5,0x4226860,5,0x8803CA,
            v(1,NEW,OLD,8,0xB0,x(0xB0,0)),n(H,3,3,NEW,S),false,P1);
        var vc=v(0xC0,0xC1,0xC2,0xC8,0xC0,x(0xC0,0));
        s.call(copy,returned(copy,vc,true,P2),null,new Mem(true,8,H+16,A2),
            new Mem(true,8,H,OLD2),new Mem(true,8,E+8,222),new Mem(true,8,E,RET2));
        s.read(8,H+16,A2);s.read(8,H,OLD2);s.read(8,A2,T2);s.read(8,T2+16,FREE+1);
        s.write(8,E-0x30,I+0x8803DD);
        var free=frame(0x8803DA,FREE+1,3,0x8803DD,
            v(T2,A2,OLD2,8,0xC0,x(0xC0,0)),n(H,3,3,NEW,S),true,P2);
        var vf=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));
        s.call(free,returned(free,vf,false,P3),null,new Mem(true,8,E+0x10,111));
        s.write(4,H+8,3);s.read(8,E+8,222);s.write(8,H,NEW);s.write(4,H+12,3);
        s.read(8,E+0x10,111);s.read(8,E+0x18,33);s.read(8,E+0x20,44);s.read(8,E-8,77);s.read(8,E,RET2);
        Outcome actual=execute(s,PRE);s.done();check(actual instanceof Normal);
        var normal=(Normal)actual;check(normal.postMxcsr()==P3&&!normal.base().postDirectionFlagSet());
        check(normal.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(NEW+16,2,0xD2,0xD8,0xD0,x(0xD0,0)),RET2,E+8,n(111,222,33,44,77))));
        check(s.load(NEW+8,8)==VALUE&&s.load(H,8)==NEW&&s.load(H+8,4)==3&&s.load(H+12,4)==3);
        check(s.load(E-0x30,8)==I+0x8803DD); // one physical slot per CALL, final contents fresh
    }
    private static void wholeZeroNoCopy() {
        Script s=initial(0,0,0x3FC00000);fpPrefix(s,0x3FC00000);
        var alloc=frame(0x88039F,ALLOC,3,0x8803A2,beforeAlloc(8,0),n(H,1,1,44,S),true,PRE);
        var va=v(NEW,0xB1,0xB2,0xB8,0xB0,x(0xB0,0));s.call(alloc,returned(alloc,va,false,P1),null);
        s.read(4,H+12,0);s.read(8,S,0x1234);s.write(8,NEW,0x1234);s.read(4,H+12,0);
        s.read(8,H+16,A);s.read(8,H,OLD);s.read(8,A,T);s.read(8,T+16,FREE);s.write(8,E-0x30,I+0x8803DD);
        var free=frame(0x8803DA,FREE,3,0x8803DD,v(T,A,OLD,8,0xB0,x(0xB0,0)),n(H,1,1,NEW,S),false,P1);
        var vf=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));s.call(free,returned(free,vf,true,P2),null);
        s.write(4,H+8,1);s.read(8,E+8,22);s.write(8,H,NEW);s.write(4,H+12,1);
        s.read(8,E+0x10,11);s.read(8,E+0x18,33);s.read(8,E+0x20,44);s.read(8,E-8,77);s.read(8,E,RET);
        var actual=(Normal)execute(s,PRE);s.done();check(actual.postMxcsr()==P2&&actual.base().postDirectionFlagSet());
        check(actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(NEW,0,0xD2,0xD8,0xD0,x(0xD0,0)),RET,E+8,N)));
    }
    private static void largeRoundUpStoppedChild() {
        Script s=initial(16777217,16777217,0x3FC00000);fpPrefix(s,0x3FC00000);
        var pre=Mxcsr.exact(0x5F80);var post=Mxcsr.exact(0x5FA0);
        var f=frame(0x88039F,ALLOC,3,0x8803A2,beforeAlloc(201326624,0x4BC00002),
            n(H,25165828,16777218,44,S),true,post);
        var childStop=new Stopped(StopReason.MISSING_POST_STATE,
            new Snapshot(f.base().childEntry(),0x855870,true,Mxcsr.unknown()),0,0x88039F);
        s.call(f,childStop,null);check(execute(s,pre)==childStop);s.done();
        check(s.load(H,8)==OLD&&s.load(H+12,4)==16777217&&s.load(E-0x30,8)==I+0x8803A2);
    }
    private static void fpFault(int count,int factor,int controls,long pc,int sourceBits,int flags,boolean spilled) {
        Script s=initial(count,count,factor);s.read(8,H+16,A);
        if(spilled){s.write(8,E+8,22);s.read(4,I+0x49F64F0L,factor);}
        var actual=execute(s,Mxcsr.exact(controls));s.done();check(actual instanceof Stopped);
        var stop=(Stopped)actual;check(stop.reason()==StopReason.ARCHITECTURAL_FP_CONDITION);
        check(stop.raisedConditionBits()==flags&&stop.originCallSiteRva()==ORIGIN);
        check(stop.snapshot().instructionRva()==pc&&stop.snapshot().directionFlagSet());
        check(stop.snapshot().mxcsr().equals(Mxcsr.exact(controls|flags)));
        long esi=Integer.toUnsignedLong(count+1);
        var expected=new GovernmentCrtBoundary185Api.Entry(I,E-0x28,
            v(count,A,S,8,0xA0,new Bits128(Integer.toUnsignedLong(sourceBits),0)),n(H,spilled?esi:22,esi,44,S));
        check(stop.snapshot().currentState().equals(expected));
        check(s.ram.containsKey(E+8)==spilled);check(s.load(E,8)==RET&&s.load(H,8)==OLD);
    }
    private static void callbackFailures() {
        for(int mode:new int[]{0,1}) {
            Script s=initial(2,2,0x3FC00000);fpPrefix(s,0x3FC00000);
            var f=frame(0x88039F,ALLOC,3,0x8803A2,beforeAlloc(24,0x40400000),n(H,3,3,44,S),true,PRE);
            RuntimeException marker=new IllegalStateException("foreign callback identity");
            Normal bad=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                V,f.base().returnRipBits()+1,E-0x28,f.base().call().nonvolatileBits()),false),P1);
            s.call(f,bad,mode==0?marker:null);
            try{execute(s,PRE);throw new AssertionError("Expected callback failure");}
            catch(RuntimeException actual){if(mode==0)check(actual==marker);else check(actual instanceof IllegalArgumentException);}
            s.done();check(s.load(H,8)==OLD&&s.load(H+12,4)==2&&s.load(E,8)==RET);
        }
    }
    private static void nonGrowthUnknown() {
        Script s=initial(0,1,0x7F812345); // factor must never be touched in this new entry branch
        s.read(8,H,OLD);s.read(8,S,0x1234);s.write(8,OLD,0x1234);s.read(4,H+12,0);s.write(4,H+12,1);
        s.read(4,H+12,1);s.read(8,H,OLD);s.read(8,E+0x10,11);s.read(8,E+0x18,33);
        s.read(8,E+0x20,44);s.read(8,E-8,77);s.read(8,E,RET);
        Mxcsr unknown=Mxcsr.unknown();var result=(Normal)execute(s,unknown);s.done();
        check(result.postMxcsr()==unknown&&result.base().postDirectionFlagSet());
        check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(
            v(OLD,0,0,0xA8,0xA0,x(0xA0,0)),RET,E+8,N)));
    }
    public static int verify() {
        wholePositiveAlias();wholeZeroNoCopy();largeRoundUpStoppedChild();
        fpFault(16777217,0x3FC00000,0x0F80,0x88037B,16777217,0x20,false);
        fpFault(2,0x7F812345,0x1F00,0x880385,0x40000000,1,true);
        fpFault(2,0x7F800000,0x1F00,0x88038D,0x7F800000,1,true);
        callbackFailures();nonGrowthUnknown();return 8;
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("No args");
        System.out.println(verify());
    }
}
