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

/** Owner source oracle for the new known SET FP factory and actual parent composition. */
public final class SlotCapacityKnownSetFpBoundary617 {
    private SlotCapacityKnownSetFpBoundary617() { }
    private static final long I=0x140000000L,E=0x8100000000008000L,H=0x8100000000002000L,
        OLD=0x8100000000003000L,NEW=0x8100000000004000L,A=0x8100000000005000L,
        A2=0x8100000000005100L,T=0x8100000000006000L,T2=0x8100000000006100L,
        ALLOC=0xF000000000000111L,FREE=0xF000000000000222L,RET=0xF100000000000333L,
        REST_BP=0xFACE000000000222L,REP=0x4226840L,F=0x12345678L;
    private static final long P=H-0x18;
    private static final long W0=0x1111222233334444L,W1=0x5555666677778888L,W2=0x2222333344445555L,
        W3=0x6666777788889999L,W4=0x3333444455556666L,W5=0x777788889999AAAAL;
    private static final Bits128 HEAD=new Bits128(W0,W1),MID=new Bits128(W2,W3),LAST=new Bits128(W4,W5);
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(1,1),P2=new Mxcsr(0x21,0xE1),P3=new Mxcsr(0x40,0xC0);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long bank,Bits128 x0){return new VolatileBits(
        ax,cx,dx,r8,bank+9,bank+10,bank+11,x0,x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static NonvolatileBits n(long bx,long bp,long si,long di){return new NonvolatileBits(bx,bp,si,di,55,66,77,88,x(0xA0,6));}
    private static final NonvolatileBits N=n(11,22,33,44);
    private static final VolatileBits VA=v(NEW,0xB1,0xB2,0xB8,0xB0,x(0xB0,0)),VF=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));
    private static final VolatileBits VS=v(0xE0,0xE1,0xE2,0xE8,0xE0,x(0xE0,0));
    private static void check(boolean ok){if(!ok)throw new AssertionError("617 literal/source mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record VectorMem(boolean write,long address,Bits128 value) { }
    private record Budget(long header,long guard) { }
    private record Call(SlotReserveWithFp615.CallFrame frame,Outcome result,List<Mem> effects) { }
    private record Tail(FullCopyWithFp613.TailCall frame,Outcome result) { }
    private record SetTail(KnownSetFp617.TailCall frame,Outcome result,List<Mem> effects) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls,tails,setTails;
        final RuntimeException marker=new IllegalStateException("617 original callback/budget identity");
        long throwSite;boolean failParentBudget,failSetRepBudget,throwSetTail;SlotReserveWithFp615.CallFrame expectedIdentity;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            event(new Budget(header,guard));if((failParentBudget&&header==0x1ACE030)||(failSetRepBudget&&header==0x4226EF9))throw marker;
        };
        final SlotReserveWithFp615.Memory memory=(SlotReserveWithFp615.Memory)Proxy.newProxyInstance(
            SlotReserveWithFp615.Memory.class.getClassLoader(),new Class<?>[]{SlotReserveWithFp615.Memory.class},
            (proxy,method,args)->{
                String name=method.getName();long address=((Long)args[0]).longValue();
                if(name.equals("read128")){Bits128 value=new Bits128(load(address,8),load(address+8,8));event(new VectorMem(false,address,value));return value;}
                if(name.equals("write128")){Bits128 value=(Bits128)args[1];event(new VectorMem(true,address,value));store(address,8,value.lowBits());store(address+8,8,value.highBits());return null;}
                int width;
                if(name.equals("readUnsignedByte")||name.equals("read8")||name.equals("writeByte"))width=1;
                else if(name.equals("readDword")||name.equals("read32")||name.equals("writeDword")||name.equals("write32"))width=4;
                else if(name.equals("readQword")||name.equals("read64")||name.equals("writeQword")||name.equals("write64"))width=8;
                else throw new AssertionError("Unexpected617Memory "+name);
                boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);
                event(new Mem(write,width,address,mask(width,value)));if(write){store(address,width,value);return null;}
                if(width==1)return Integer.valueOf((int)value&255);if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long a,int width,long value){for(int k=0;k<width;k++)ram.put(a+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long a,int width){long value=0;for(int k=0;k<width;k++){Byte b=ram.get(a+k);if(b==null)throw new AssertionError("Unseeded617RAM "+Long.toHexString(a+k));value|=(b.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("617 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long a,long value){steps.add(new Mem(false,width,a,mask(width,value)));}
        void write(int width,long a,long value){steps.add(new Mem(true,width,a,mask(width,value)));}
        Outcome invoke(SlotReserveWithFp615.CallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Call);
            Call call=(Call)steps.get(cursor++);if(expectedIdentity!=null)check(actual==expectedIdentity);check(actual.equals(call.frame())&&actual.preMxcsr()==call.frame().preMxcsr());calls++;
            for(Mem effect:call.effects()){
                check(effect.write());if(effect.width()==8)memory.writeQword(effect.address(),effect.value());
                else if(effect.width()==4)memory.writeDword(effect.address(),(int)effect.value());
                else if(effect.width()==1)memory.writeByte(effect.address(),(int)effect.value());else throw new AssertionError("effectwidth");
            }
            if(actual.original().call().callSiteRva()==throwSite)throw marker;return call.result();
        }
        Outcome tail(FullCopyWithFp613.TailCall actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Tail);
            Tail tail=(Tail)steps.get(cursor++);check(actual.equals(tail.frame())&&actual.preMxcsr()==tail.frame().preMxcsr());tails++;return tail.result();}
        Outcome setTail(KnownSetFp617.TailCall actual){check(cursor<steps.size()&&steps.get(cursor) instanceof SetTail);
            SetTail tail=(SetTail)steps.get(cursor++);check(actual.equals(tail.frame())&&actual.preMxcsr()==tail.frame().preMxcsr());setTails++;
            for(Mem effect:tail.effects()){check(effect.write());if(effect.width()==1)memory.writeByte(effect.address(),(int)effect.value());
                else if(effect.width()==8)memory.writeQword(effect.address(),effect.value());else throw new AssertionError("set effectwidth");}
            if(throwSetTail)throw marker;return tail.result();}
        void done(){check(cursor==steps.size());}
    }
    private static Script seeded(){Script s=new Script();s.store(E,8,RET);s.store(H,8,OLD);s.store(H+8,4,3);s.store(H+12,4,3);
        s.store(H+16,8,A);s.store(A,8,T);s.store(T+8,8,ALLOC);s.store(A2,8,T2);s.store(T2+16,8,FREE);
        s.store(OLD,8,W0);s.store(OLD+8,8,W1);s.store(OLD+16,8,W2);s.store(OLD+24,8,W3);s.store(OLD+32,8,W4);s.store(OLD+40,8,W5);
        s.store(I+0x542F098,4,0);s.store(I+0x6090094,4,0x4226DBF);s.store(P+0x38,4,0xFFFFFF);s.store(P+0x40,1,0);s.store(I+0x60900F0,4,0x4227098);return s;}
    private static Outcome execute(Script s,long requested,Mxcsr state){var base=new PendingSlotCapacityFullState412Api.Input(
        new GovernmentCrtBoundary185Api.Entry(I,E,v(0xA0,P,requested,0xA8,0xA0,x(0xA0,0)),N),true,s.budget);
        return SlotCapacityWithFp616.execute(new SlotReserveWithFp615.Input(base,state),s.memory,KnownSetFp617.bind(s.memory,s.budget,s::setTail,s::invoke),
            KnownRepFpTail614.bind(s.memory,s.budget,s::tail));}
    private static SlotReserveWithFp615.CallFrame frame(long site,long target,long ret,VolatileBits before,NonvolatileBits saved,boolean df,Mxcsr state){
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,E-0x58,before,saved);
        var base=new PendingSlotCapacityFullState412Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x60,before,saved),df,3,I+ret);
        return new SlotReserveWithFp615.CallFrame(base,state);}
    private static Normal returned(SlotReserveWithFp615.CallFrame frame,VolatileBits after,boolean df,Mxcsr state){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(after,frame.original().returnRipBits(),frame.original().call().rspBits(),frame.original().call().nonvolatileBits()),df),state);}
    private static Stopped stopped(SlotReserveWithFp615.CallFrame frame,Mxcsr state){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(frame.original().childEntry(),frame.original().call().callSiteRva(),frame.original().directionFlagSet(),state),0,frame.original().call().callSiteRva());}
    private static List<Mem> allocateEffects(){return List.of(new Mem(true,8,H+16,A2));}
    private static List<Mem> freeEffects(){return List.of(new Mem(true,4,H+12,99),new Mem(true,1,NEW+60,77),new Mem(true,1,P+0x40,9));}
    private static void addCall(Script s,SlotReserveWithFp615.CallFrame frame,Outcome outcome,List<Mem> effects){s.steps.add(new Call(frame,outcome,effects));s.steps.addAll(effects);}
    private static SlotReserveWithFp615.CallFrame allocationPrefix(Script s){
        s.write(8,E+0x10,11);s.write(8,E+0x18,22);s.write(8,E-8,33);s.read(1,P+0x40,0);s.read(4,P+0x24,3);
        s.write(8,E+8,44);s.read(4,P+0x24,3);s.write(8,E-0x30,I+0x1ACDFF8);
        s.write(8,E-0x18,3);s.write(8,E-0x38,44);s.read(4,H+8,3);s.read(8,H+16,A);
        s.write(8,E-0x28,P);s.write(8,E-0x20,4);s.read(8,A,T);s.read(8,T+8,ALLOC);s.write(8,E-0x60,I+0x1ACE4E4);
        return frame(0x1ACE4E1,ALLOC,0x1ACE4E4,v(T,A,64,8,0xA0,x(0xA0,0)),n(H,P,4,4),true,P0);
    }
    private static void allocatedCopyPrefix(Script s){var alloc=allocationPrefix(s);addCall(s,alloc,returned(alloc,VA,false,P1),allocateEffects());
        s.read(4,H+12,3);s.read(8,H,OLD);s.write(8,E-0x60,I+0x1ACE501);}
    private static void sseReads(Script s,long table){s.read(4,I+0x542F098,0);s.steps.add(new VectorMem(false,OLD,HEAD));
        s.steps.add(new VectorMem(false,OLD+32,LAST));s.read(4,I+0x6090094,table);}
    private static VolatileBits copyCurrent(long table,boolean copied){return new VolatileBits(NEW,NEW,OLD,48,48,I,I+table,HEAD,
        copied?MID:x(0xB0,1),x(0xB0,2),x(0xB0,3),x(0xB0,4),LAST);}
    private static void copiedSse(Script s){sseReads(s,0x4226DBF);s.steps.add(new VectorMem(false,OLD,HEAD));s.steps.add(new VectorMem(true,NEW,HEAD));
        s.steps.add(new VectorMem(false,OLD+16,MID));s.steps.add(new VectorMem(true,NEW+16,MID));
        s.steps.add(new VectorMem(true,NEW+32,LAST));s.steps.add(new VectorMem(true,NEW,HEAD));s.read(8,E-0x60,I+0x1ACE501);}
    private static SlotReserveWithFp615.CallFrame freePrefix(Script s,long table,boolean copied){
        s.read(4,H+12,3);s.read(8,H+16,A2);s.read(8,H,OLD);s.read(8,A2,T2);s.read(8,T2+16,FREE);s.write(8,E-0x60,I+0x1ACE517);
        VolatileBits current=copyCurrent(table,copied);return frame(0x1ACE514,FREE,0x1ACE517,
            new VolatileBits(T2,A2,OLD,8,current.r9Bits(),current.r10Bits(),current.r11Bits(),current.xmm0(),current.xmm1(),current.xmm2(),current.xmm3(),current.xmm4(),current.xmm5()),
            n(H,NEW,3,4),false,P1);}
    private static void childFinish(Script s,long restoredBp){s.write(8,H,NEW);s.read(8,E-0x28,restoredBp);s.write(4,H+12,3);
        s.read(8,E-0x20,4);s.write(4,H+8,4);s.read(8,E-0x18,3);s.read(8,E-0x38,44);s.read(8,E-0x30,I+0x1ACDFF8);}
    private static void checkUnpublished(Script s,int count){check(s.load(H,8)==OLD&&s.load(H+8,4)==3&&s.load(H+12,4)==count);}
    private static SlotReserveWithFp615.CallFrame setPrefix(Script s){s.read(4,P+0x24,3);s.read(8,P+0x18,NEW);s.write(8,E-0x30,I+0x1ACE01A);
        var before=new VolatileBits(1,NEW+48,0,16,VF.r9Bits(),VF.r10Bits(),VF.r11Bits(),VF.xmm0(),VF.xmm1(),VF.xmm2(),VF.xmm3(),VF.xmm4(),VF.xmm5());
        var call=new GovernmentCrtBoundary185Api.Call(0x1ACE015,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226F10,E-0x28,before,n(3,P,4,44));
        return new SlotReserveWithFp615.CallFrame(new PendingSlotCapacityFullState412Api.CallFrame(call,
            new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,call.nonvolatileBits()),true,5,I+0x1ACE01A),P2);}
    private static void completedChild(Script s){allocatedCopyPrefix(s);copiedSse(s);var free=freePrefix(s,0x4226DBF,true);
        addCall(s,free,returned(free,VF,true,P2),freeEffects());childFinish(s,P);}
    private static List<Mem> setEffects(){return List.of(new Mem(true,8,NEW+48,0),new Mem(true,8,NEW+56,0));}
    private static void afterSetBudget(Script s){s.write(4,P+0x24,4);s.steps.add(new Budget(0x1ACE030,3));}
    private static void parentFinish(Script s){s.read(8,P+0x18,NEW);s.write(4,NEW+52,0xFFFFFF);s.read(8,P+0x18,NEW);
        s.write(8,NEW+56,0);s.read(8,P+0x18,NEW);s.write(4,NEW+48,0xFFFFFF);s.read(4,P+0x38,0xFFFFFF);
        s.read(8,E+8,44);s.write(4,P+0x38,3);s.read(8,E+0x10,11);s.read(8,E+0x18,22);s.read(8,E-8,33);s.read(8,E,RET);}
    private static void knownSet16(Script s){s.read(4,I+0x60900F0,0x4227098);s.write(8,NEW+48,0);s.write(8,NEW+56,0);s.read(8,E-0x30,I+0x1ACE01A);}
    private static KnownSetFp617.TailCall setTransfer(long table){
        var current=new VolatileBits(NEW+48,NEW+64,0,16,I+table,0xDA,NEW+48,VF.xmm0(),VF.xmm1(),VF.xmm2(),VF.xmm3(),VF.xmm4(),VF.xmm5());
        var entry=new GovernmentCrtBoundary185Api.Entry(I,E-0x30,current,n(3,P,4,44));
        return new KnownSetFp617.TailCall(new PendingSlotCapacityFullState412Api.TailFrame(new GovernmentCrtBoundary185Api.Tail(
            0x422703B,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,I+table,entry),true),P2);}
    private static SlotReserveWithFp615.CallFrame directSet(long count,long fill,Mxcsr state){
        var before=v(0xD0,NEW+48,fill,count,0xD0,x(0xD0,0));var saved=n(3,P,4,44);
        var call=new GovernmentCrtBoundary185Api.Call(0x1ACE015,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226F10,E-0x28,before,saved);
        return new SlotReserveWithFp615.CallFrame(new PendingSlotCapacityFullState412Api.CallFrame(call,
            new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,saved),true,5,I+0x1ACE01A),state);}
    private static Outcome directInvoke(Script s,SlotReserveWithFp615.CallFrame fp){return KnownSetFp617.bind(s.memory,s.budget,s::setTail,s::invoke).invoke(fp);}
    private static void wholeKnownSetNormal(){Script s=seeded();completedChild(s);setPrefix(s);knownSet16(s);afterSetBudget(s);parentFinish(s);
        var actual=(Normal)execute(s,4,P0);s.done();var finalV=new VolatileBits((NEW&~255L)|1,2,6,3,NEW,3,0,VF.xmm0(),VF.xmm1(),VF.xmm2(),VF.xmm3(),VF.xmm4(),VF.xmm5());
        check(actual.postMxcsr()==P2&&actual.base().postDirectionFlagSet()&&actual.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(finalV,RET,E+8,N)));
        check(s.calls==2&&s.setTails==0&&s.tails==0&&s.load(P+0x24,4)==4&&s.load(P+0x20,4)==4&&s.load(P+0x38,4)==3);
        check(s.load(P+0x18,8)==NEW&&s.load(P+0x28,8)==A2&&s.load(P+0x40,1)==9&&s.load(NEW+48,4)==0xFFFFFF&&s.load(NEW+52,4)==0xFFFFFF&&s.load(NEW+56,8)==0);
        check(s.load(NEW,8)==W0&&s.load(NEW+8,8)==W1&&s.load(NEW+16,8)==W2&&s.load(NEW+24,8)==W3&&s.load(NEW+32,8)==W4&&s.load(NEW+40,8)==W5);}
    private static void wholeUnknownSetStopped(){Script s=seeded();s.store(I+0x60900F0,4,F);completedChild(s);var fp=setPrefix(s);s.read(4,I+0x60900F0,F);
        var tail=setTransfer(F);Stopped expected=new Stopped(StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(tail.original().transfer().entry(),0x422703B,true,P3),0,0x1ACE015);
        var effects=List.of(new Mem(true,1,NEW+63,123));s.steps.add(new SetTail(tail,expected,effects));s.steps.addAll(effects);
        check(execute(s,4,P0)==expected);s.done();check(s.calls==2&&s.setTails==1&&s.load(P+0x18,8)==NEW&&s.load(P+0x20,4)==4&&s.load(P+0x24,4)==3);
        check(s.load(P+0x38,4)==0xFFFFFF&&s.load(NEW+60,1)==77&&s.load(NEW+63,1)==123);}
    private static void originalSetRepBudgetFailure(){Script s=seeded();s.store(I+0x5C5CBB0,1,2);s.store(E-0x30,8,I+0x1ACE01A);var fp=directSet(129,0xAB,P0);
        s.read(1,I+0x5C5CBB0,2);s.write(8,E-0x38,44);s.steps.add(new Budget(0x4226EF9,NEW+48));s.failSetRepBudget=true;
        try{directInvoke(s,fp);throw new AssertionError("original SET REP budget must propagate");}catch(RuntimeException thrown){check(thrown==s.marker);s.done();}
        check(s.calls==0&&s.setTails==0&&s.load(E-0x38,8)==44);}
    private static void unknownAndForeignPrefixes(){
        Script bad=seeded();bad.store(I+0x60900F0,4,F);var frame=directSet(16,0,P2);bad.read(4,I+0x60900F0,F);var bt=setTransfer(F);
        var invalid=new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(VF,I+0x1ACE01B,E-0x28,frame.original().call().nonvolatileBits()),false),P3);
        var be=List.of(new Mem(true,1,NEW+48,238));bad.steps.add(new SetTail(bt,invalid,be));bad.steps.addAll(be);
        try{directInvoke(bad,frame);throw new AssertionError("original CALL NR must reject");}catch(IllegalArgumentException expected){bad.done();}
        check(bad.setTails==1&&bad.load(NEW+48,1)==238);
        Script f=seeded();f.store(I+0x60900F0,4,F);var ff=directSet(16,0,P2);f.read(4,I+0x60900F0,F);var ft=setTransfer(F);
        var fe=List.of(new Mem(true,1,NEW+49,239));f.steps.add(new SetTail(ft,returned(ff,VF,false,P3),fe));f.steps.addAll(fe);f.throwSetTail=true;
        try{directInvoke(f,ff);throw new AssertionError("unknown SET tail exception must propagate");}catch(RuntimeException thrown){check(thrown==f.marker);f.done();}
        check(f.setTails==1&&f.load(NEW+49,1)==239);
        Script foreign=seeded();var af=frame(0x1ACE4E1,ALLOC,0x1ACE4E4,v(T,A,64,8,0xA0,x(0xA0,0)),n(H,P,4,4),true,P0);
        Stopped expected=stopped(af,P0);addCall(foreign,af,expected,List.of());foreign.expectedIdentity=af;
        check(directInvoke(foreign,af)==expected);foreign.done();check(foreign.calls==1&&foreign.setTails==0);}
    public static int verify(){wholeKnownSetNormal();wholeUnknownSetStopped();originalSetRepBudgetFailure();unknownAndForeignPrefixes();return 4;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
