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

/** New normal203-null ->205leaf ->existing204 scene; owner-independent data. */
public final class GovernmentSizeLeaf205Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L,CELL=0xa00020L;
    private static Bits128 x(long a) {return new Bits128(a,~a);}
    private static VolatileBits bits(long seed,long a,long c) {
        return new VolatileBits(a,c,seed+2,seed+8,seed+9,seed+10,seed+11,
                x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60));
    }
    private static VolatileBits rax(VolatileBits v,long a) {
        return new VolatileBits(a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static void q(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}
    private static void d(Map<Long,Integer> m,long a,int v) {for(int j=0;j<4;j++)m.put(a+j,(v>>>(j*8))&255);}
    @Override public List<Witness> witnesses() {
        VolatileBits incoming=bits(0x1111000000000000L,0xaaaabbbbccccddddL,0L);
        NonvolatileBits n=new NonvolatileBits(0x2222000000000101L,0x2222000000000102L,
                0x2222000000000103L,0x2222000000000104L,0x2222000000000112L,
                0x2222000000000113L,0x2222000000000114L,0x2222000000000115L,x(0x2222000000000160L));
        Entry entry=new Entry(I,S,incoming,n);
        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(long a=S-0x80;a<S+0x20;a++)seed.put(a,0xa5);
        q(seed,S,0x150012345L);q(seed,CELL,0x91929394a5a6a7a8L);
        q(seed,0x900000L,0x1011121314151617L);q(seed,0x900010L,0x2021222324252627L);
        Map<Long,Integer> before1=new LinkedHashMap<>(seed);
        q(before1,S-0x30,I+0x425925eL);q(before1,S-0x60,I+0x423b195L);
        Map<Long,Integer> mutation1=new LinkedHashMap<>();q(mutation1,0x900000L,0x8899aabbccddeeffL);
        VolatileBits post1=bits(0x3333000000000000L,0xa00000L,0x3333000000000001L);
        CallStep lower=new CallStep(new Call(0x423b190L,TargetKind.DIRECT_RVA,0x424fc74L,
                S-0x58,incoming,n),before1,mutation1,post1);
        Map<Long,Integer> before2=new LinkedHashMap<>(before1);before2.putAll(mutation1);
        d(before2,CELL,0x16);q(before2,S-0x30,I+0x4259269L);
        Map<Long,Integer> mutation2=new LinkedHashMap<>();q(mutation2,0x900010L,0x7766554433221100L);
        VolatileBits post2=bits(0x4444000000000000L,0x7123456789abcdefL,0x4444000000000001L);
        CallStep second=new CallStep(new Call(0x4259264L,TargetKind.DIRECT_RVA,0x4232a50L,
                S-0x28,rax(post1,CELL),n),before2,mutation2,post2);
        Map<Long,Integer> expected=new LinkedHashMap<>(before2);expected.putAll(mutation2);
        NormalReturn result=new NormalReturn(rax(post2,-1L),0x150012345L,S+8,n);
        return List.of(new Witness("size-null205-actual-error204",entry,seed,List.of(lower,second),expected,result));
    }
}
