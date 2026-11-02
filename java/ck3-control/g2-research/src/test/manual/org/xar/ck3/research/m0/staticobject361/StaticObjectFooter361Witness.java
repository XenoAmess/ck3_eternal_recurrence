package org.xar.ck3.research.m0.staticobject361;

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

/** New consumer cases; opaque calls are explicit test ports, never actual CRT or Game. */
public final class StaticObjectFooter361Witness {
    private static final long IMAGE=0x140000000L,S=0x730008L,RET=0x123456789abcdef0L;
    private static final long GS=0x810000L,TLS=0x920000L,TLS3=0x930000L;
    private static final long GUARD=IMAGE+0x5d1eb08L,OBJECT=IMAGE+0x5d1eaf0L;
    private static final long COUNTER=IMAGE+0x542f090L,INDEX=IMAGE+0x5c5cbc4L;
    private static final long CRITICAL=IMAGE+0x5c5cb18L,ACQUIRE=0x1111222233334444L,RELEASE=0x5555666677778888L;
    private static final NonvolatileBits N=new NonvolatileBits(0x1010101010101010L,2L,3L,4L,
            0xfedcba9876543210L,6L,7L,8L,new Bits128(0x9999L,0xaaaaL));
    private static int checks;
    private StaticObjectFooter361Witness() { }
    public static void main(String[] args) {
        originalSupplierReachesActualFooter();
        exactFilterAndIdentityForwarding();
        existingSlotAndReturnedBoundaryFailures();
        System.out.println("PASS cases=3 checks="+checks+" represented185_only=true Game=false");
    }
    private static void originalSupplierReachesActualFooter() {
        Mem m=base();m.q(S,RET);m.d(GUARD,2);m.d(TLS+16L,1);m.d(COUNTER,-1);m.d(INDEX,3);
        VolatileBits input=v(0x100L),header=v(0x200L),acquired=v(0x300L),released=v(0x400L),tailV=v(0x500L);
        int[] calls={0},gs={0},tails={0};
        Calls ports=new Calls(){
            @Override public long readGsQword58(){gs[0]++;return GS;}
            @Override public VolatileBits invoke(Call c){
                calls[0]++;
                if(c.callSiteRva()==0xb15033L){
                    equal(TargetKind.DIRECT_RVA,c.kind(),"header direct role");number(0x4223a84L,c.targetBits(),"header remains opaque");
                    number(S-0x28L,c.rspBits(),"supplier actual preSP");number(IMAGE+0xb15038L,m.readQword(S-0x30L),"header existing push");
                    number(GUARD,c.volatileBits().rcxBits(),"header guard argument");equal(N,c.nonvolatileBits(),"header incoming N");
                    m.d(GUARD,-1);return header;
                }
                number(S-0x58L,c.rspBits(),"footer actual internal preSP");
                equal(withRbx(N,GUARD),c.nonvolatileBits(),"footer current RBX holds guard");
                equal(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"actual IAT target role");
                if(c.callSiteRva()==0x4223a34L){
                    number(ACQUIRE,c.targetBits(),"fresh acquire IAT value");number(IMAGE+0x4223a3aL,m.readQword(S-0x60L),"six-byte acquire continuation");
                    equal(change(header,header.raxBits(),CRITICAL,header.rdxBits(),header.r8Bits(),header.r9Bits()),c.volatileBits(),"full acquire frame");
                    return acquired;
                }
                number(0x4223a74L,c.callSiteRva(),"second actual IAT site");number(RELEASE,c.targetBits(),"fresh release IAT value");
                number(IMAGE+0x4223a7aL,m.readQword(S-0x60L),"six-byte release continuation");
                equal(change(acquired,0L,CRITICAL,3L,TLS3,16L),c.volatileBits(),"full release frame including EAX wrap and TLS");
                number(0,m.readDword(COUNTER),"global counter wrapped at32bits");number(0,m.readDword(GUARD),"guard gets new epoch");
                number(0,m.readDword(TLS3+16L),"actual indexed TLS write");return released;
            }
            @Override public NormalReturn tail(Tail t){
                tails[0]++;number(0x4223a7fL,t.jumpSiteRva(),"actual local epilogue tail site");
                equal(TargetKind.DIRECT_RVA,t.kind(),"opaque direct tail role");number(0x4223aecL,t.targetBits(),"unexpanded tail target");
                number(S-0x30L,t.entry().rspBits(),"tail owns no push or RET");number(IMAGE,t.entry().imageBaseBits(),"actual image");
                equal(released,t.entry().volatileBits(),"all volatile release bits reach tail");equal(N,t.entry().nonvolatileBits(),"saved RBX restored before tail");
                return new NormalReturn(tailV,m.readQword(t.entry().rspBits()),t.entry().rspBits()+8L,copyN(N));
            }
        };
        NormalReturn result=StaticObjectB15000FullState.execute(new Entry(IMAGE,S,input,N),m,
                StaticObjectFooter361Calls.bind(IMAGE,m,ports));
        equal(change(tailV,OBJECT,tailV.rcxBits(),tailV.rdxBits(),tailV.r8Bits(),tailV.r9Bits()),result.volatileBits(),"supplier final RAX and complete tail V");
        equal(N,result.nonvolatileBits(),"root represented N preserved");number(RET,result.returnRipBits(),"root actual RET");number(S+8L,result.callerRspBits(),"root actual SP");
        number(3,calls[0],"header plus two actual footer IAT calls");number(2,gs[0],"two real GS consumers");number(1,tails[0],"one real opaque tail");
        number(0,m.readUnsignedByte(OBJECT),"supplier actual first byte");number(255,m.readUnsignedByte(OBJECT+12L),"supplier actual twelfth byte");
        number(IMAGE+0xb1505bL,m.readQword(S-0x30L),"caller push not overwritten by binder");
    }
    private static void exactFilterAndIdentityForwarding() {
        Mem neverRead=new Mem();VolatileBits out=v(0x600L);NormalReturn nr=new NormalReturn(out,RET,S+8L,N);
        Object[] seen={null};int[] gs={0};
        Calls ports=new Calls(){
            @Override public VolatileBits invoke(Call c){seen[0]=c;return out;}
            @Override public NormalReturn tail(Tail t){seen[0]=t;return nr;}
            @Override public long readGsQword58(){gs[0]++;return GS;}
        };
        Calls bound=StaticObjectFooter361Calls.bind(IMAGE,neverRead,ports);
        for(Call c:new Call[]{new Call(0xb15055L,TargetKind.DIRECT_RVA,0x4223a24L,S,v(1),N),
                new Call(0xb15056L,TargetKind.DIRECT_RVA,0x4223a84L,S,v(2),N),
                new Call(0xb15056L,TargetKind.INDIRECT_ABSOLUTE,0x4223a24L,S,v(3),N)}){
            same(out,bound.invoke(c),"unmatched result identity");same(c,seen[0],"unmatched Call identity");
        }
        Tail tail=new Tail(0x42L,TargetKind.DIRECT_RVA,0x43L,new Entry(IMAGE,S,v(4),N));
        same(nr,bound.tail(tail),"forwarded NormalReturn identity");same(tail,seen[0],"forwarded Tail identity");
        number(GS,bound.readGsQword58(),"delegated GS value");number(1,gs[0],"delegated GS count");number(0,neverRead.reads,"unmatched route has no memory access");
    }
    private static void existingSlotAndReturnedBoundaryFailures() {
        Mem wrong=new Mem();wrong.q(S-0x30L,RET);
        Calls fail=new BasicPorts(wrong,0){@Override public VolatileBits invoke(Call c){throw new AssertionError("bad caller slot must stop before CRT");}};
        expect(IllegalStateException.class,()->StaticObjectFooter361Calls.bind(IMAGE,wrong,fail).invoke(matched()));
        for(int mode=1;mode<=3;mode++){
            Mem m=base();m.q(S-0x30L,IMAGE+0xb1505bL);m.d(COUNTER,4);m.d(INDEX,3);
            Calls ports=new BasicPorts(m,mode);
            expect(IllegalStateException.class,()->StaticObjectFooter361Calls.bind(IMAGE,m,ports).invoke(matched()));
        }
        Mem m=base();m.q(S-0x30L,IMAGE+0xb1505bL);
        RuntimeException marker=new IllegalArgumentException("owned opaque IAT failure");
        Calls ports=new BasicPorts(m,0){@Override public VolatileBits invoke(Call c){number(0x4223a34L,c.callSiteRva(),"failure actual first IAT");throw marker;}};
        same(marker,expect(RuntimeException.class,()->StaticObjectFooter361Calls.bind(IMAGE,m,ports).invoke(matched())),"callback failure identity");
    }
    private static Call matched(){return new Call(0xb15056L,TargetKind.DIRECT_RVA,0x4223a24L,S-0x28L,change(v(7),8L,GUARD,9L,10L,11L),N);}
    private static class BasicPorts implements Calls {
        private final Mem memory;private final int mode;
        BasicPorts(Mem memory,int mode){this.memory=memory;this.mode=mode;}
        @Override public VolatileBits invoke(Call call){return v(0x700L);}
        @Override public long readGsQword58(){return GS;}
        @Override public NormalReturn tail(Tail t){
            number(S-0x30L,t.entry().rspBits(),"bad-return witness reached actual tail");equal(N,t.entry().nonvolatileBits(),"local epilogue restores N before injected bad return");
            long rip=memory.readQword(t.entry().rspBits()),sp=t.entry().rspBits()+8L;
            return new NormalReturn(v(0x800L),mode==1?rip+1L:rip,mode==2?sp+8L:sp,mode==3?withRbx(N,0L):copyN(N));
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
        private final Map<Long,Integer> bytes=new HashMap<>();private int reads;
        void q(long p,long v){seed(p,v,8);}void d(long p,int v){seed(p,Integer.toUnsignedLong(v),4);}
        private void seed(long p,long v,int n){for(int i=0;i<n;i++)bytes.put(p+i,(int)(v>>>(8*i))&255);}
        private long raw(long p,int n){reads++;long v=0;for(int i=0;i<n;i++){Integer b=bytes.get(p+i);if(b==null)throw new AssertionError("uninitialized "+Long.toHexString(p+i));v|=(long)b<<(8*i);}return v;}
        @Override public int readDword(long p){return (int)raw(p,4);}
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
