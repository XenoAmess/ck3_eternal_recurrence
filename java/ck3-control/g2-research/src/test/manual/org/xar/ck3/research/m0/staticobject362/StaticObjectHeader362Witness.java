package org.xar.ck3.research.m0.staticobject362;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m0.staticobject357.StaticObjectB15000FullState;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Three new exact-caller cases; all opaque effects are explicit owned test ports. */
public final class StaticObjectHeader362Witness {
    private static final long IMAGE=0x140000000L,S=0x730008L,RET=0x123456789abcdef0L;
    private static final long GS=0x810000L,TLS=0x920000L,TLS3=0x930000L;
    private static final long GUARD=IMAGE+0x5d1eb08L,OBJECT=IMAGE+0x5d1eaf0L;
    private static final long COUNTER=IMAGE+0x542f090L,INDEX=IMAGE+0x5c5cbc4L;
    private static final long CRITICAL=IMAGE+0x5c5cb18L,ACQUIRE=0x1111222233334444L,RELEASE=0x5555666677778888L;
    private static final NonvolatileBits N=new NonvolatileBits(0x1010101010101010L,2L,3L,4L,
            0xfedcba9876543210L,6L,7L,8L,new Bits128(0x9999L,0xaaaaL));
    private static int checks;
    private StaticObjectHeader362Witness() { }
    public static void main(String[] args) {
        originalSupplierDynamicGuardThenWait();
        nonwaitingFreshTlsAndFullResult();
        exactRoutingAndFailureBoundaries();
        System.out.println("PASS cases=3 checks="+checks+" represented185_only=true Game=false");
    }
    private static void originalSupplierDynamicGuardThenWait() {
        Mem m=base();m.q(S,RET);m.d(GUARD,2);m.d(TLS+16L,1);
        VolatileBits input=v(0x100L),acquired=v(0x200L),waited=v(0x300L),tailV=v(0x400L),footerV=v(0x500L);
        int[] calls={0},gs={0},tails={0},steps={0};
        Calls ports=new Calls(){
            @Override public long readGsQword58(){gs[0]++;return GS;}
            @Override public VolatileBits invoke(Call c){
                calls[0]++;
                if(c.callSiteRva()==0xb15056L){
                    number(0x4223a24L,c.targetBits(),"footer remains residual");equal(TargetKind.DIRECT_RVA,c.kind(),"footer direct role");
                    number(S-0x28L,c.rspBits(),"supplier footer preSP");number(IMAGE+0xb1505bL,m.readQword(S-0x30L),"supplier footer existing continuation");
                    equal(change(tailV,tailV.raxBits(),GUARD,tailV.rdxBits(),tailV.r8Bits(),tailV.r9Bits()),c.volatileBits(),"all tail bits then actual footer RCX");
                    equal(N,c.nonvolatileBits(),"footer current N");return footerV;
                }
                number(S-0x58L,c.rspBits(),"actual header internal preSP");equal(withRbx(N,GUARD),c.nonvolatileBits(),"header actual current RBX");
                if(c.callSiteRva()==0x4223a94L){
                    equal(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"actual acquire target role");number(ACQUIRE,c.targetBits(),"actual IAT value");
                    number(IMAGE+0x4223a9aL,m.readQword(S-0x60L),"six-byte acquire return slot");
                    equal(change(input,1L,CRITICAL,16L,input.r8Bits(),input.r9Bits()),c.volatileBits(),"full actual initial header frame");
                    m.script(1,-1,0,0);return acquired;
                }
                number(0x4223aa9L,c.callSiteRva(),"actual wait site");equal(TargetKind.DIRECT_RVA,c.kind(),"wait direct role");number(0x4223b30L,c.targetBits(),"wait remains opaque");
                number(IMAGE+0x4223aaeL,m.readQword(S-0x60L),"five-byte wait return slot");
                equal(change(acquired,acquired.raxBits(),100L,acquired.rdxBits(),acquired.r8Bits(),acquired.r9Bits()),c.volatileBits(),"wait ECX overwrite and full other V");
                m.q(IMAGE+0x43da4f0L,RELEASE+1L);return waited;
            }
            @Override public NormalReturn tail(Tail t){
                tails[0]++;number(0x4223ae4L,t.jumpSiteRva(),"header exact epilogue tail");equal(TargetKind.INDIRECT_ABSOLUTE,t.kind(),"actual tail target role");
                number(RELEASE+1L,t.targetBits(),"tail target re-read after wait callback");number(S-0x30L,t.entry().rspBits(),"no new tail push or RET");
                equal(change(waited,waited.raxBits(),CRITICAL,waited.rdxBits(),waited.r8Bits(),waited.r9Bits()),t.entry().volatileBits(),"complete waited V at local epilogue");
                equal(N,t.entry().nonvolatileBits(),"saved full N restored before tail");number(-1,m.readDword(GUARD),"zero path fresh OR wrote minus1");
                number(4,m.scriptReads,"both fresh compares and fresh OR sequence consumed");
                return new NormalReturn(tailV,m.readQword(t.entry().rspBits()),t.entry().rspBits()+8L,copyN(N));
            }
        };
        Calls bound=StaticObjectHeader362Calls.bind(IMAGE,m,ports,(header,guard)->{
            number(0x4223a9aL,header,"actual budget header");number(GUARD,guard,"actual budget address");steps[0]++;
        });
        NormalReturn result=StaticObjectB15000FullState.execute(new Entry(IMAGE,S,input,N),m,bound);
        number(2,steps[0],"two actual loop headers, not a fake wait completion");number(3,calls[0],"acquire/wait plus residual footer");
        number(1,tails[0],"real header tail");number(1,gs[0],"only original supplier GS on zero path");
        equal(change(footerV,OBJECT,footerV.rcxBits(),footerV.rdxBits(),footerV.r8Bits(),footerV.r9Bits()),result.volatileBits(),"caller complete final V");
        equal(N,result.nonvolatileBits(),"root full N");number(RET,result.returnRipBits(),"root actual RET");number(S+8L,result.callerRspBits(),"root actual caller SP");
        number(0,m.readUnsignedByte(OBJECT),"actual first object byte");number(255,m.readUnsignedByte(OBJECT+12L),"actual object byte12");
    }
    private static void nonwaitingFreshTlsAndFullResult() {
        Mem m=base();m.q(S-0x30L,IMAGE+0xb15038L);m.d(GUARD,5);m.d(COUNTER,0x80000001);m.d(INDEX,3);m.script(1,5);
        VolatileBits acquired=v(0x600L),tailV=v(0x700L);int[] gs={0},steps={0};
        Calls ports=new Calls(){
            @Override public long readGsQword58(){gs[0]++;return GS;}
            @Override public VolatileBits invoke(Call c){number(0x4223a94L,c.callSiteRva(),"only acquire on nonwaiting branch");return acquired;}
            @Override public NormalReturn tail(Tail t){
                equal(change(acquired,0x80000001L,CRITICAL,TLS3,16L,acquired.r9Bits()),t.entry().volatileBits(),"actual EAX zero-extension and TLS-frame reads");
                number(0x80000001L,Integer.toUnsignedLong(m.readDword(TLS3+16L)),"exact epoch written to indexed TLS");
                number(2,m.scriptReads,"second compare observes5 instead of cached first1");equal(N,t.entry().nonvolatileBits(),"full N at TLS tail");
                return new NormalReturn(tailV,m.readQword(t.entry().rspBits()),t.entry().rspBits()+8L,copyN(N));
            }
        };
        VolatileBits out=StaticObjectHeader362Calls.bind(IMAGE,m,ports,(h,g)->{number(0x4223a9aL,h,"nonwait budget header");number(GUARD,g,"nonwait guard");steps[0]++;}).invoke(matched());
        same(tailV,out,"actual tail result V identity reaches caller");number(1,steps[0],"single nonwaiting step");number(1,gs[0],"one actual header GS read");
    }
    private static void exactRoutingAndFailureBoundaries() {
        Mem never=new Mem();VolatileBits out=v(0x800L);NormalReturn nr=new NormalReturn(out,RET,S+8L,N);Object[] seen={null};
        Calls plain=new BasicPorts(never,0){
            @Override public VolatileBits invoke(Call c){seen[0]=c;return out;}
            @Override public NormalReturn tail(Tail t){seen[0]=t;return nr;}
        };
        Calls bound=StaticObjectHeader362Calls.bind(IMAGE,never,plain,(h,g)->{throw new AssertionError("unmatched call must not use budget");});
        for(Call c:new Call[]{new Call(0xb15032L,TargetKind.DIRECT_RVA,0x4223a84L,S,v(1),N),
                new Call(0xb15033L,TargetKind.DIRECT_RVA,0x4223a24L,S,v(2),N),
                new Call(0xb15033L,TargetKind.INDIRECT_ABSOLUTE,0x4223a84L,S,v(3),N)}){
            same(out,bound.invoke(c),"unmatched V identity");same(c,seen[0],"unmatched Call identity");
        }
        Tail t=new Tail(1L,TargetKind.DIRECT_RVA,2L,new Entry(IMAGE,S,v(4),N));same(nr,bound.tail(t),"forwarded NR identity");same(t,seen[0],"forwarded Tail identity");number(GS,bound.readGsQword58(),"forwarded GS");number(0,never.reads,"unmatched route no memory read");
        Mem wrong=new Mem();wrong.q(S-0x30L,RET);
        expect(IllegalStateException.class,()->StaticObjectHeader362Calls.bind(IMAGE,wrong,new BasicPorts(wrong,0),StaticObjectHeader362Witness::permit).invoke(matched()));
        for(int mode=1;mode<=3;mode++){
            Mem m=base();m.q(S-0x30L,IMAGE+0xb15038L);m.d(GUARD,0);Calls ports=new BasicPorts(m,mode);
            expect(IllegalStateException.class,()->StaticObjectHeader362Calls.bind(IMAGE,m,ports,StaticObjectHeader362Witness::permit).invoke(matched()));
        }
        Mem m=base();m.q(S-0x30L,IMAGE+0xb15038L);RuntimeException stop=new IllegalArgumentException("actual budget stop");
        int[] first={0};Calls ports=new BasicPorts(m,0){@Override public VolatileBits invoke(Call c){first[0]++;number(0x4223a94L,c.callSiteRva(),"budget failure follows acquire");return v(9);}};
        same(stop,expect(RuntimeException.class,()->StaticObjectHeader362Calls.bind(IMAGE,m,ports,(h,g)->{throw stop;}).invoke(matched())),"budget exception identity");number(1,first[0],"actual acquire before budget");
        RuntimeException failure=new IllegalArgumentException("actual IAT callback failure");
        Calls bad=new BasicPorts(m,0){@Override public VolatileBits invoke(Call c){throw failure;}};
        same(failure,expect(RuntimeException.class,()->StaticObjectHeader362Calls.bind(IMAGE,m,bad,(h,g)->{throw new AssertionError("callback failed before budget");}).invoke(matched())),"callback exception identity");
    }
    private static void permit(long h,long g){number(0x4223a9aL,h,"real guarded header");number(GUARD,g,"real guard address");}
    private static Call matched(){return new Call(0xb15033L,TargetKind.DIRECT_RVA,0x4223a84L,S-0x28L,change(v(7),8L,GUARD,9L,10L,11L),N);}
    private static class BasicPorts implements Calls {
        private final Mem memory;private final int mode;
        BasicPorts(Mem memory,int mode){this.memory=memory;this.mode=mode;}
        @Override public VolatileBits invoke(Call c){return v(0x900L);}
        @Override public long readGsQword58(){return GS;}
        @Override public NormalReturn tail(Tail t){
            number(S-0x30L,t.entry().rspBits(),"actual header tail entrySP");equal(N,t.entry().nonvolatileBits(),"actual saved N before bad return injection");
            long rip=memory.readQword(t.entry().rspBits()),sp=t.entry().rspBits()+8L;
            return new NormalReturn(v(0xa00L),mode==1?rip+1L:rip,mode==2?sp+8L:sp,mode==3?withRbx(N,0L):copyN(N));
        }
    }
    private static Mem base(){Mem m=new Mem();m.q(GS,TLS);m.q(GS+24L,TLS3);m.q(IMAGE+0x43da500L,ACQUIRE);m.q(IMAGE+0x43da4f0L,RELEASE);return m;}
    private static VolatileBits v(long s){return new VolatileBits(s+1,s+2,s+3,s+4,s+5,s+6,s+7,new Bits128(s+8,s+9),new Bits128(s+10,s+11),new Bits128(s+12,s+13),new Bits128(s+14,s+15),new Bits128(s+16,s+17),new Bits128(s+18,s+19));}
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8,long r9){return new VolatileBits(a,c,d,r8,r9,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static NonvolatileBits withRbx(NonvolatileBits n,long b){return new NonvolatileBits(b,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static NonvolatileBits copyN(NonvolatileBits n){return withRbx(n,n.rbxBits());}
    private static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
    private static void number(long a,long b,String s){check(a==b,s+" wanted="+a+" actual="+b);}
    private static void equal(Object a,Object b,String s){check(a.equals(b),s+" wanted="+a+" actual="+b);}
    private static void same(Object a,Object b,String s){check(a==b,s);}
    private static RuntimeException expect(Class<? extends RuntimeException> type,Runnable run){try{run.run();}catch(RuntimeException e){check(type.isInstance(e),"actual exception type");return e;}throw new AssertionError("expected "+type.getName());}
    private static final class Mem implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();private final ArrayDeque<Integer> sequence=new ArrayDeque<>();private int reads,scriptReads;
        void script(int...values){for(int value:values)sequence.addLast(value);}
        void q(long p,long v){seed(p,v,8);}void d(long p,int v){seed(p,Integer.toUnsignedLong(v),4);}
        private void seed(long p,long v,int n){for(int i=0;i<n;i++)bytes.put(p+i,(int)(v>>>(8*i))&255);}
        private long raw(long p,int n){reads++;long v=0;for(int i=0;i<n;i++){Integer b=bytes.get(p+i);if(b==null)throw new AssertionError("uninitialized "+Long.toHexString(p+i));v|=(long)b<<(8*i);}return v;}
        @Override public int readDword(long p){if(p==GUARD&&!sequence.isEmpty()){reads++;scriptReads++;return sequence.removeFirst();}return (int)raw(p,4);}
        @Override public long readQword(long p){return raw(p,8);}
        @Override public int readUnsignedByte(long p){return (int)raw(p,1);}
        @Override public void writeDword(long p,int v){d(p,v);}
        @Override public void writeQword(long p,long v){q(p,v);}
        @Override public void writeByte(long p,int v){seed(p,v,1);}
        @Override public int lockedXaddDword(long p,int v){throw new AssertionError("unexpected LOCK");}
        @Override public Bits128 read128(long p){throw new AssertionError("unexpected128 read");}
        @Override public void write128(long p,Bits128 v){throw new AssertionError("unexpected128 write");}
    }
}
