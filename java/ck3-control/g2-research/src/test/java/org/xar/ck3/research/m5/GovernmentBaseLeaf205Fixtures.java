package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m4.Callee4259250FullState203WitnessApi.Book;
import org.xar.ck3.research.m4.Callee4259250FullState203WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Two new actual203->205->204/Free201 normal integrations, source-only owner oracle. */
public final class GovernmentBaseLeaf205Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L,RET=0x150012345L;
    private static Bits128 x(long a) {return new Bits128(a,~a);}
    private static VolatileBits bits(long seed,long a,long c,long d) {
        return new VolatileBits(a,c,d,seed+8,seed+9,seed+10,seed+11,
                x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60));
    }
    private static VolatileBits values(long a,long c,long d,long r8,VolatileBits v) {
        return new VolatileBits(a,c,d,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits rax(VolatileBits v,long a) {return values(a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v);}
    private static NonvolatileBits n(int tag) {
        long b=0x2222000000000000L+tag*0x1000L;
        return new NonvolatileBits(b+0x101,b+0x102,b+0x103,b+0x104,b+0x112,b+0x113,b+0x114,b+0x115,x(b+0x160));
    }
    private static NonvolatileBits local(NonvolatileBits n,long size,long ptr) {
        return new NonvolatileBits(size,n.rbpBits(),n.rsiBits(),ptr,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static void q(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}
    private static void d(Map<Long,Integer> m,long a,int v) {for(int j=0;j<4;j++)m.put(a+j,(v>>>(j*8))&255);}
    private static Map<Long,Integer> seed(long marker) {
        Map<Long,Integer> m=new LinkedHashMap<>();for(long a=S-0x80;a<S+0x20;a++)m.put(a,0xa5);
        q(m,S,RET);q(m,marker,0x1011121314151617L);return m;
    }
    private static Map<Long,Integer> saved(Map<Long,Integer> initial,NonvolatileBits n,long outerRet) {
        Map<Long,Integer> b=new LinkedHashMap<>(initial);q(b,S+8,n.rbxBits());q(b,S-8,n.rdiBits());
        q(b,S-0x30,outerRet);return b;
    }
    private static Witness f7d() {
        long ptr=0x60002000L,cell=I+0x542f210L;
        VolatileBits in=bits(0x1111000000001000L,0xaaaabbbbccccddddL,ptr,-1L);
        NonvolatileBits nv=n(1),working=local(nv,-1L,ptr);
        Map<Long,Integer> initial=seed(0x900010L);q(initial,cell,0x91929394a5a6a7a8L);
        Map<Long,Integer> before=saved(initial,nv,I+0x4251f82L);q(before,S-0x60,I+0x423b195L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();q(mutation,0x900010L,0x8899aabbccddeeffL);
        VolatileBits post=bits(0x7777000000000000L,0L,0x7777000000000001L,0x7777000000000002L);
        CallStep lower=new CallStep(new Call(0x423b190L,TargetKind.DIRECT_RVA,0x424fc74L,
                S-0x58,in,working),before,mutation,post);
        Map<Long,Integer> after=new LinkedHashMap<>(before);after.putAll(mutation);d(after,cell,12);
        return new Witness("baseF7D-normal-actual204",new Entry(I,S,in,nv),initial,List.of(lower),after,
                new NormalReturn(rax(post,0L),RET,S+8,nv));
    }
    /** Same explicitly owned successful callback vector as the old independent201success data. */
    private static VolatileBits freePost() {
        return new VolatileBits(0xaabbccdd00000001L,0x2233445566778899L,0xcc00000000000003L,
                0x8800000000000003L,0x9900000000000003L,0xaa00000000000003L,0xbb00000000000003L,
                new Bits128(0xa00000000000001eL,0xb00000000000001eL),
                new Bits128(0xa00000000000001fL,0xb00000000000001fL),
                new Bits128(0xa000000000000020L,0xb000000000000020L),
                new Bits128(0xa000000000000021L,0xb000000000000021L),
                new Bits128(0xa000000000000022L,0xb000000000000022L),
                new Bits128(0xa000000000000023L,0xb000000000000023L));
    }
    private static Witness f70() {
        long ptr=0x60001000L,global=0xa0a1a2a3a4a5a6a7L,target=0x1234567812345678L;
        VolatileBits in=bits(0x1111000000002000L,0xbbbbccccddddeeeeL,ptr,0L);
        NonvolatileBits nv=n(2),working=local(nv,0L,ptr);
        Map<Long,Integer> initial=seed(0x900020L);q(initial,I+0x5c5de30L,global);q(initial,I+0x43da748L,target);
        Map<Long,Integer> before=saved(initial,nv,I+0x4251f75L);q(before,S-0x38,0L);q(before,S-0x60,I+0x424e380L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();q(mutation,0x900020L,0x7766554433221100L);
        VolatileBits pre=values(in.raxBits(),global,0L,ptr,in),post=freePost();
        CallStep call=new CallStep(new Call(0x424e37aL,TargetKind.INDIRECT_ABSOLUTE,target,S-0x58,pre,working),
                before,mutation,post);
        Map<Long,Integer> after=new LinkedHashMap<>(before);after.putAll(mutation);
        return new Witness("baseF70-normal-actual-free",new Entry(I,S,in,nv),initial,List.of(call),after,
                new NormalReturn(rax(post,0L),RET,S+8,nv));
    }
    @Override public List<Witness> witnesses() {return List.of(f7d(),f70());}
}
