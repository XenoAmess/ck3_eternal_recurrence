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

/** Owner fixed-source oracle for the new scoped133 FP carrier; no old suite invoked. */
public final class SlotReserveFpBoundary615 {
    private SlotReserveFpBoundary615() { }
    private static final long I=0x140000000L,E=0x8100000000008000L,H=0x8100000000002000L,
        OLD=0x8100000000003000L,NEW=0x8100000000004000L,A=0x8100000000005000L,
        A2=0x8100000000005100L,T=0x8100000000006000L,T2=0x8100000000006100L,
        ALLOC=0xF000000000000111L,FREE=0xF000000000000222L,RET=0xF100000000000333L,
        REST_BP=0xFACE000000000222L,REP=0x4226840L,F=0x12345678L;
    private static final long W0=0x1111222233334444L,W1=0x5555666677778888L,W2=0x2222333344445555L,
        W3=0x6666777788889999L,W4=0x3333444455556666L,W5=0x777788889999AAAAL;
    private static final Bits128 HEAD=new Bits128(W0,W1),MID=new Bits128(W2,W3),LAST=new Bits128(W4,W5);
    private static final Mxcsr P0=Mxcsr.unknown(),P1=new Mxcsr(1,1),P2=new Mxcsr(0x21,0xE1);
    private static Bits128 x(long bank,int lane){return new Bits128(bank+lane,0xD000000000000000L+bank+lane);}
    private static VolatileBits v(long ax,long cx,long dx,long r8,long bank,Bits128 x0){return new VolatileBits(
        ax,cx,dx,r8,bank+9,bank+10,bank+11,x0,x(bank,1),x(bank,2),x(bank,3),x(bank,4),x(bank,5));}
    private static NonvolatileBits n(long bx,long bp,long si,long di){return new NonvolatileBits(bx,bp,si,di,55,66,77,88,x(0xA0,6));}
    private static final NonvolatileBits N=n(11,22,33,44);
    private static final VolatileBits VA=v(NEW,0xB1,0xB2,0xB8,0xB0,x(0xB0,0)),VF=v(0xD0,0xD1,0xD2,0xD8,0xD0,x(0xD0,0));
    private static void check(boolean ok){if(!ok)throw new AssertionError("615 literal/source mismatch");}
    private record Mem(boolean write,int width,long address,long value) { }
    private record VectorMem(boolean write,long address,Bits128 value) { }
    private record Budget(long header,long guard) { }
    private record Call(SlotReserveWithFp615.CallFrame frame,Outcome result,List<Mem> effects) { }
    private record Tail(FullCopyWithFp613.TailCall frame,Outcome result) { }
    private static long mask(int width,long value){return width==1?value&255:width==4?value&0xFFFFFFFFL:value;}
    private static final class Script {
        final List<Object> steps=new ArrayList<>();final Map<Long,Byte> ram=new HashMap<>();int cursor,calls,tails;
        final RuntimeException marker=new IllegalStateException("615 original callback/budget identity");
        long throwSite;boolean failRepBudget;
        final GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            event(new Budget(header,guard));if(failRepBudget&&header==0x422684B)throw marker;
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
                else throw new AssertionError("Unexpected615Memory "+name);
                boolean write=name.startsWith("write");long value=write?((Number)args[1]).longValue():load(address,width);
                event(new Mem(write,width,address,mask(width,value)));if(write){store(address,width,value);return null;}
                if(width==1)return Integer.valueOf((int)value&255);if(width==4)return Integer.valueOf((int)value);return Long.valueOf(value);
            });
        void store(long a,int width,long value){for(int k=0;k<width;k++)ram.put(a+k,Byte.valueOf((byte)(value>>>(8*k))));}
        long load(long a,int width){long value=0;for(int k=0;k<width;k++){Byte b=ram.get(a+k);if(b==null)throw new AssertionError("Unseeded615RAM "+Long.toHexString(a+k));value|=(b.byteValue()&255L)<<(8*k);}return value;}
        void event(Object actual){if(cursor>=steps.size()||!steps.get(cursor++).equals(actual))throw new AssertionError("615 cursor "+(cursor-1)+" actual="+actual);}
        void read(int width,long a,long value){steps.add(new Mem(false,width,a,mask(width,value)));}
        void write(int width,long a,long value){steps.add(new Mem(true,width,a,mask(width,value)));}
        Outcome invoke(SlotReserveWithFp615.CallFrame actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Call);
            Call call=(Call)steps.get(cursor++);check(actual.equals(call.frame())&&actual.preMxcsr()==call.frame().preMxcsr());calls++;
            for(Mem effect:call.effects()){
                check(effect.write());if(effect.width()==8)memory.writeQword(effect.address(),effect.value());
                else if(effect.width()==4)memory.writeDword(effect.address(),(int)effect.value());
                else if(effect.width()==1)memory.writeByte(effect.address(),(int)effect.value());else throw new AssertionError("effectwidth");
            }
            if(actual.original().call().callSiteRva()==throwSite)throw marker;return call.result();
        }
        Outcome tail(FullCopyWithFp613.TailCall actual){check(cursor<steps.size()&&steps.get(cursor) instanceof Tail);
            Tail tail=(Tail)steps.get(cursor++);check(actual.equals(tail.frame())&&actual.preMxcsr()==tail.frame().preMxcsr());tails++;return tail.result();}
        void done(){check(cursor==steps.size());}
    }
    private static Script seeded(){Script s=new Script();s.store(E,8,RET);s.store(H,8,OLD);s.store(H+8,4,3);s.store(H+12,4,3);
        s.store(H+16,8,A);s.store(A,8,T);s.store(T+8,8,ALLOC);s.store(A2,8,T2);s.store(T2+16,8,FREE);
        s.store(OLD,8,W0);s.store(OLD+8,8,W1);s.store(OLD+16,8,W2);s.store(OLD+24,8,W3);s.store(OLD+32,8,W4);s.store(OLD+40,8,W5);
        s.store(I+0x542F098,4,0);s.store(I+0x6090094,4,0x4226DBF);return s;}
    private static Outcome execute(Script s,long requested,Mxcsr state){var base=new PendingSlotCapacityFullState412Api.Input(
        new GovernmentCrtBoundary185Api.Entry(I,E,v(0xA0,H,requested,0xA8,0xA0,x(0xA0,0)),N),true,s.budget);
        return SlotReserveWithFp615.execute(new SlotReserveWithFp615.Input(base,state),s.memory,s::invoke,
            KnownRepFpTail614.bind(s.memory,s.budget,s::tail));}
    private static SlotReserveWithFp615.CallFrame frame(long site,long target,long ret,VolatileBits before,NonvolatileBits saved,boolean df,Mxcsr state){
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,E-0x28,before,saved);
        var base=new PendingSlotCapacityFullState412Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,saved),df,3,I+ret);
        return new SlotReserveWithFp615.CallFrame(base,state);}
    private static Normal returned(SlotReserveWithFp615.CallFrame frame,VolatileBits after,boolean df,Mxcsr state){return new Normal(new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(after,frame.original().returnRipBits(),E-0x28,frame.original().call().nonvolatileBits()),df),state);}
    private static Stopped stopped(SlotReserveWithFp615.CallFrame frame,Mxcsr state){return new Stopped(StopReason.MISSING_POST_STATE,
        new QueueFp604Api.Snapshot(frame.original().childEntry(),frame.original().call().callSiteRva(),frame.original().directionFlagSet(),state),0,frame.original().call().callSiteRva());}
    private static List<Mem> allocateEffects(){return List.of(new Mem(true,8,H+16,A2));}
    private static List<Mem> freeEffects(){return List.of(new Mem(true,4,H+12,99),new Mem(true,1,NEW+60,77),new Mem(true,8,E+8,REST_BP));}
    private static void addCall(Script s,SlotReserveWithFp615.CallFrame frame,Outcome outcome,List<Mem> effects){s.steps.add(new Call(frame,outcome,effects));s.steps.addAll(effects);}
    private static SlotReserveWithFp615.CallFrame allocationPrefix(Script s){
        s.write(8,E+0x18,11);s.write(8,E-8,44);s.read(4,H+8,3);s.read(8,H+16,A);
        s.write(8,E+8,22);s.write(8,E+0x10,33);s.read(8,A,T);s.read(8,T+8,ALLOC);s.write(8,E-0x30,I+0x1ACE4E4);
        return frame(0x1ACE4E1,ALLOC,0x1ACE4E4,v(T,A,64,8,0xA0,x(0xA0,0)),n(H,22,33,4),true,P0);
    }
    private static void allocatedCopyPrefix(Script s){var alloc=allocationPrefix(s);addCall(s,alloc,returned(alloc,VA,false,P1),allocateEffects());
        s.read(4,H+12,3);s.read(8,H,OLD);s.write(8,E-0x30,I+0x1ACE501);}
    private static void sseReads(Script s,long table){s.read(4,I+0x542F098,0);s.steps.add(new VectorMem(false,OLD,HEAD));
        s.steps.add(new VectorMem(false,OLD+32,LAST));s.read(4,I+0x6090094,table);}
    private static VolatileBits copyCurrent(long table,boolean copied){return new VolatileBits(NEW,NEW,OLD,48,48,I,I+table,HEAD,
        copied?MID:x(0xB0,1),x(0xB0,2),x(0xB0,3),x(0xB0,4),LAST);}
    private static void copiedSse(Script s){sseReads(s,0x4226DBF);s.steps.add(new VectorMem(false,OLD,HEAD));s.steps.add(new VectorMem(true,NEW,HEAD));
        s.steps.add(new VectorMem(false,OLD+16,MID));s.steps.add(new VectorMem(true,NEW+16,MID));
        s.steps.add(new VectorMem(true,NEW+32,LAST));s.steps.add(new VectorMem(true,NEW,HEAD));s.read(8,E-0x30,I+0x1ACE501);}
    private static SlotReserveWithFp615.CallFrame freePrefix(Script s,long table,boolean copied){
        s.read(4,H+12,3);s.read(8,H+16,A2);s.read(8,H,OLD);s.read(8,A2,T2);s.read(8,T2+16,FREE);s.write(8,E-0x30,I+0x1ACE517);
        VolatileBits current=copyCurrent(table,copied);return frame(0x1ACE514,FREE,0x1ACE517,
            new VolatileBits(T2,A2,OLD,8,current.r9Bits(),current.r10Bits(),current.r11Bits(),current.xmm0(),current.xmm1(),current.xmm2(),current.xmm3(),current.xmm4(),current.xmm5()),
            n(H,NEW,3,4),false,P1);}
    private static void finish(Script s){s.write(8,H,NEW);s.read(8,E+8,REST_BP);s.write(4,H+12,3);s.read(8,E+0x10,33);s.write(4,H+8,4);
        s.read(8,E+0x18,11);s.read(8,E-8,44);s.read(8,E,RET);}
    private static void checkUnpublished(Script s,int count){check(s.load(H,8)==OLD&&s.load(H+8,4)==3&&s.load(H+12,4)==count);}
    private static void signedNoGrowthPreservesKnowledge(){Script s=seeded();long requested=0x12340000FFFFFFFFL;
        s.write(8,E+0x18,11);s.write(8,E-8,44);s.read(4,H+8,3);s.read(8,E+0x18,11);s.read(8,E-8,44);s.read(8,E,RET);
        var result=(Normal)execute(s,requested,P2);s.done();check(result.postMxcsr()==P2&&result.base().postDirectionFlagSet()&&s.calls==0&&s.tails==0);
        check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(v(0xA0,H,requested,0xA8,0xA0,x(0xA0,0)),RET,E+8,N)));checkUnpublished(s,3);}
    private static void normalThreeCallStateFlow(){Script s=seeded();allocatedCopyPrefix(s);copiedSse(s);var free=freePrefix(s,0x4226DBF,true);
        addCall(s,free,returned(free,VF,true,P2),freeEffects());finish(s);var result=(Normal)execute(s,4,P0);s.done();
        check(result.postMxcsr()==P2&&result.base().postDirectionFlagSet()&&s.calls==2&&s.tails==0);
        check(result.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(VF,RET,E+8,n(11,REST_BP,33,44))));
        check(s.load(H,8)==NEW&&s.load(H+8,4)==4&&s.load(H+12,4)==3&&s.load(H+16,8)==A2&&s.load(NEW+60,1)==77);
        check(s.load(NEW,8)==W0&&s.load(NEW+8,8)==W1&&s.load(NEW+16,8)==W2&&s.load(NEW+24,8)==W3&&s.load(NEW+32,8)==W4&&s.load(NEW+40,8)==W5);}
    private static void allocatorStoppedIdentity(){Script s=seeded();var alloc=allocationPrefix(s);Stopped expected=stopped(alloc,P0);
        addCall(s,alloc,expected,allocateEffects());check(execute(s,4,P0)==expected);s.done();checkUnpublished(s,3);check(s.calls==1&&s.tails==0&&s.load(H+16,8)==A2);}
    private static void copyTailStoppedIdentity(){Script s=seeded();s.store(I+0x6090094,4,F);allocatedCopyPrefix(s);sseReads(s,F);
        var transfer=new GovernmentCrtBoundary185Api.Tail(0x4226D76,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,I+F,
            new GovernmentCrtBoundary185Api.Entry(I,E-0x30,copyCurrent(F,false),n(H,NEW,3,4)));
        var frame=new FullCopyWithFp613.TailCall(new FullCopy437Api.TailFrame(transfer,false),P1);
        Stopped expected=new Stopped(StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(transfer.entry(),0x4226D76,false,P1),0,0x1ACE4FC);
        s.steps.add(new Tail(frame,expected));check(execute(s,4,P0)==expected);s.done();checkUnpublished(s,3);check(s.calls==1&&s.tails==1);}
    private static void rep48(Script s,boolean fail){sseReads(s,REP);s.write(8,E-0x38,4);s.write(8,E-0x40,3);
        s.steps.add(new Budget(0x422684B,NEW));if(fail)return;
        s.read(1,OLD+0,68);s.write(1,NEW+0,68);
        s.steps.add(new Budget(0x422684B,NEW+1));
        s.read(1,OLD+1,68);s.write(1,NEW+1,68);
        s.steps.add(new Budget(0x422684B,NEW+2));
        s.read(1,OLD+2,51);s.write(1,NEW+2,51);
        s.steps.add(new Budget(0x422684B,NEW+3));
        s.read(1,OLD+3,51);s.write(1,NEW+3,51);
        s.steps.add(new Budget(0x422684B,NEW+4));
        s.read(1,OLD+4,34);s.write(1,NEW+4,34);
        s.steps.add(new Budget(0x422684B,NEW+5));
        s.read(1,OLD+5,34);s.write(1,NEW+5,34);
        s.steps.add(new Budget(0x422684B,NEW+6));
        s.read(1,OLD+6,17);s.write(1,NEW+6,17);
        s.steps.add(new Budget(0x422684B,NEW+7));
        s.read(1,OLD+7,17);s.write(1,NEW+7,17);
        s.steps.add(new Budget(0x422684B,NEW+8));
        s.read(1,OLD+8,136);s.write(1,NEW+8,136);
        s.steps.add(new Budget(0x422684B,NEW+9));
        s.read(1,OLD+9,136);s.write(1,NEW+9,136);
        s.steps.add(new Budget(0x422684B,NEW+10));
        s.read(1,OLD+10,119);s.write(1,NEW+10,119);
        s.steps.add(new Budget(0x422684B,NEW+11));
        s.read(1,OLD+11,119);s.write(1,NEW+11,119);
        s.steps.add(new Budget(0x422684B,NEW+12));
        s.read(1,OLD+12,102);s.write(1,NEW+12,102);
        s.steps.add(new Budget(0x422684B,NEW+13));
        s.read(1,OLD+13,102);s.write(1,NEW+13,102);
        s.steps.add(new Budget(0x422684B,NEW+14));
        s.read(1,OLD+14,85);s.write(1,NEW+14,85);
        s.steps.add(new Budget(0x422684B,NEW+15));
        s.read(1,OLD+15,85);s.write(1,NEW+15,85);
        s.steps.add(new Budget(0x422684B,NEW+16));
        s.read(1,OLD+16,85);s.write(1,NEW+16,85);
        s.steps.add(new Budget(0x422684B,NEW+17));
        s.read(1,OLD+17,85);s.write(1,NEW+17,85);
        s.steps.add(new Budget(0x422684B,NEW+18));
        s.read(1,OLD+18,68);s.write(1,NEW+18,68);
        s.steps.add(new Budget(0x422684B,NEW+19));
        s.read(1,OLD+19,68);s.write(1,NEW+19,68);
        s.steps.add(new Budget(0x422684B,NEW+20));
        s.read(1,OLD+20,51);s.write(1,NEW+20,51);
        s.steps.add(new Budget(0x422684B,NEW+21));
        s.read(1,OLD+21,51);s.write(1,NEW+21,51);
        s.steps.add(new Budget(0x422684B,NEW+22));
        s.read(1,OLD+22,34);s.write(1,NEW+22,34);
        s.steps.add(new Budget(0x422684B,NEW+23));
        s.read(1,OLD+23,34);s.write(1,NEW+23,34);
        s.steps.add(new Budget(0x422684B,NEW+24));
        s.read(1,OLD+24,153);s.write(1,NEW+24,153);
        s.steps.add(new Budget(0x422684B,NEW+25));
        s.read(1,OLD+25,153);s.write(1,NEW+25,153);
        s.steps.add(new Budget(0x422684B,NEW+26));
        s.read(1,OLD+26,136);s.write(1,NEW+26,136);
        s.steps.add(new Budget(0x422684B,NEW+27));
        s.read(1,OLD+27,136);s.write(1,NEW+27,136);
        s.steps.add(new Budget(0x422684B,NEW+28));
        s.read(1,OLD+28,119);s.write(1,NEW+28,119);
        s.steps.add(new Budget(0x422684B,NEW+29));
        s.read(1,OLD+29,119);s.write(1,NEW+29,119);
        s.steps.add(new Budget(0x422684B,NEW+30));
        s.read(1,OLD+30,102);s.write(1,NEW+30,102);
        s.steps.add(new Budget(0x422684B,NEW+31));
        s.read(1,OLD+31,102);s.write(1,NEW+31,102);
        s.steps.add(new Budget(0x422684B,NEW+32));
        s.read(1,OLD+32,102);s.write(1,NEW+32,102);
        s.steps.add(new Budget(0x422684B,NEW+33));
        s.read(1,OLD+33,102);s.write(1,NEW+33,102);
        s.steps.add(new Budget(0x422684B,NEW+34));
        s.read(1,OLD+34,85);s.write(1,NEW+34,85);
        s.steps.add(new Budget(0x422684B,NEW+35));
        s.read(1,OLD+35,85);s.write(1,NEW+35,85);
        s.steps.add(new Budget(0x422684B,NEW+36));
        s.read(1,OLD+36,68);s.write(1,NEW+36,68);
        s.steps.add(new Budget(0x422684B,NEW+37));
        s.read(1,OLD+37,68);s.write(1,NEW+37,68);
        s.steps.add(new Budget(0x422684B,NEW+38));
        s.read(1,OLD+38,51);s.write(1,NEW+38,51);
        s.steps.add(new Budget(0x422684B,NEW+39));
        s.read(1,OLD+39,51);s.write(1,NEW+39,51);
        s.steps.add(new Budget(0x422684B,NEW+40));
        s.read(1,OLD+40,170);s.write(1,NEW+40,170);
        s.steps.add(new Budget(0x422684B,NEW+41));
        s.read(1,OLD+41,170);s.write(1,NEW+41,170);
        s.steps.add(new Budget(0x422684B,NEW+42));
        s.read(1,OLD+42,153);s.write(1,NEW+42,153);
        s.steps.add(new Budget(0x422684B,NEW+43));
        s.read(1,OLD+43,153);s.write(1,NEW+43,153);
        s.steps.add(new Budget(0x422684B,NEW+44));
        s.read(1,OLD+44,136);s.write(1,NEW+44,136);
        s.steps.add(new Budget(0x422684B,NEW+45));
        s.read(1,OLD+45,136);s.write(1,NEW+45,136);
        s.steps.add(new Budget(0x422684B,NEW+46));
        s.read(1,OLD+46,119);s.write(1,NEW+46,119);
        s.steps.add(new Budget(0x422684B,NEW+47));
        s.read(1,OLD+47,119);s.write(1,NEW+47,119);
        s.read(8,E-0x40,3);s.read(8,E-0x38,4);s.read(8,E-0x30,I+0x1ACE501);
    }
    private static void freeStoppedAfterActualRep(){Script s=seeded();s.store(I+0x6090094,4,REP);allocatedCopyPrefix(s);rep48(s,false);
        var free=freePrefix(s,REP,false);Stopped expected=stopped(free,P2);addCall(s,free,expected,freeEffects());
        check(execute(s,4,P0)==expected);s.done();checkUnpublished(s,99);check(s.calls==2&&s.tails==0&&s.load(E+8,8)==REST_BP);
        check(s.load(NEW,8)==W0&&s.load(NEW+8,8)==W1&&s.load(NEW+16,8)==W2&&s.load(NEW+24,8)==W3&&s.load(NEW+32,8)==W4&&s.load(NEW+40,8)==W5);}
    private static void exceptionAndGuardPrefixes(){
        Script a=seeded();var alloc=allocationPrefix(a);addCall(a,alloc,returned(alloc,VA,false,P1),allocateEffects());a.throwSite=0x1ACE4E1;
        try {execute(a,4,P0);throw new AssertionError("allocator marker must propagate");}catch(RuntimeException actual){check(actual==a.marker);a.done();}
        checkUnpublished(a,3);check(a.calls==1&&a.load(H+16,8)==A2);
        Script f=seeded();allocatedCopyPrefix(f);copiedSse(f);var free=freePrefix(f,0x4226DBF,true);
        addCall(f,free,returned(free,VF,true,P2),freeEffects());f.throwSite=0x1ACE514;
        try {execute(f,4,P0);throw new AssertionError("free marker must propagate");}catch(RuntimeException actual){check(actual==f.marker);f.done();}
        checkUnpublished(f,99);check(f.calls==2&&f.load(E+8,8)==REST_BP);
        Script b=seeded();b.store(I+0x6090094,4,REP);allocatedCopyPrefix(b);rep48(b,true);b.failRepBudget=true;
        try {execute(b,4,P0);throw new AssertionError("original REP budget must propagate");}catch(RuntimeException actual){check(actual==b.marker);b.done();}
        checkUnpublished(b,3);check(b.calls==1&&b.tails==0&&b.load(E-0x38,8)==4&&b.load(E-0x40,8)==3);
        Script bad=seeded();var original=allocationPrefix(bad);var invalid=new Normal(new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(VA,I+0x1ACE4E5,E-0x28,original.original().call().nonvolatileBits()),false),P1);
        addCall(bad,original,invalid,allocateEffects());
        try {execute(bad,4,P0);throw new AssertionError("original412NR guard must reject");}catch(IllegalArgumentException expected){bad.done();}
        checkUnpublished(bad,3);check(bad.calls==1&&bad.tails==0);
    }
    public static int verify(){signedNoGrowthPreservesKnowledge();normalThreeCallStateFlow();allocatorStoppedIdentity();copyTailStoppedIdentity();freeStoppedAfterActualRep();exceptionAndGuardPrefixes();return 6;}
    public static void main(String[] args){if(args.length!=0)throw new IllegalArgumentException("No args");System.out.println(verify());}
}
