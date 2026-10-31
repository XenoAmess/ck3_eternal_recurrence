package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtRegistry195WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentCrtRegistry195WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New185 bridge consumption data, independently derived from raw59B and frozen
 * scripts. Both model rounds rejected; target Java neither read nor run. */
public final class GovernmentCrtRegistry195Fixtures implements Book {
    private static final long I=0x140000000L,S=0x900008L,W=0x8fffe0L,SLOT=0x8fffd8L;
    @Override public List<Witness> witnesses() {
        VolatileBits entry=v(0xaaaa000011112222L,0xbbbb000033334444L,0x620020L,0x620030L,
                0x620040L,0xaaaa555566667777L,0xbbbb666677778888L,0xb000L);
        NonvolatileBits original=n(0x1111222233334444L,0x4444555566667777L);
        Call request=new Call(0x424df29L,TargetKind.DIRECT_RVA,0x424db38L,S+8,entry,original);
        Map<Long,Integer> seed=new LinkedHashMap<>();for(long a=0x8fff88L;a<0x900088L;a++)seed.put(a,0xa5);
        qword(seed,S,I+0x424df2eL);dword(seed,0x620020L,0xf1234567);dword(seed,0x620040L,0x10203040);

        Map<Long,Integer> before1=new LinkedHashMap<>(seed);
        qword(before1,S+8,original.rbxBits());qword(before1,S+0x20,0x620040L);qword(before1,S-8,original.rdiBits());
        qword(before1,SLOT,I+0x424db54L);
        NonvolatileBits work=n(0x620040L,0x620030L);
        VolatileBits post1=post(0x1111111100000000L,0x1111111100000001L,0xd000L);
        CallStep first=new CallStep(new Call(0x424db4fL,TargetKind.DIRECT_RVA,0x4247ffcL,W,
                change(entry,entry.raxBits(),0xf1234567L),work),before1,Map.of(),post1);

        Map<Long,Integer> before2=new LinkedHashMap<>(before1);qword(before2,SLOT,I+0x424db5dL);
        Map<Long,Integer> mutation=new LinkedHashMap<>();dword(mutation,0x620040L,0x89abcdef);
        VolatileBits post2=post(0x2222222200000000L,0xfedcba9880000001L,0xe000L);
        CallStep second=new CallStep(new Call(0x424db58L,TargetKind.DIRECT_RVA,0x424dbb0L,W,
                change(post1,post1.raxBits(),0x620030L),work),before2,mutation,post2);

        Map<Long,Integer> before3=new LinkedHashMap<>(before2);before3.putAll(mutation);qword(before3,SLOT,I+0x424db66L);
        VolatileBits post3=post(0x3333333300000000L,0x123456789abcdef0L,0xf000L);
        CallStep third=new CallStep(new Call(0x424db61L,TargetKind.DIRECT_RVA,0x4248050L,W,
                change(post2,post2.raxBits(),0x89abcdefL),n(0x620040L,0x80000001L)),before3,Map.of(),post3);
        return List.of(new Witness("registry195-new185-three-call-shared-byteimage",I,request,seed,
                List.of(first,second,third),before3,change(post3,0x80000001L,post3.rcxBits())));
    }
    private static NonvolatileBits n(long bx,long di) {
        return new NonvolatileBits(bx,0x2222333344445555L,0x3333444455556666L,di,0x5555666677778888L,
                0x6666777788889999L,0x777788889999aaaaL,0x88889999aaaabbbbL,new Bits128(0xb100L,0xb101L));
    }
    private static VolatileBits post(long h,long a,long x) {return v(a,h+2,h+3,h+4,h+5,h+6,h+7,x);}
    private static VolatileBits change(VolatileBits p,long a,long c) {
        return new VolatileBits(a,c,p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),p.r11Bits(),
                p.xmm0(),p.xmm1(),p.xmm2(),p.xmm3(),p.xmm4(),p.xmm5());
    }
    private static VolatileBits v(long a,long c,long d,long r8,long r9,long r10,long r11,long x) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,new Bits128(x,x+1),new Bits128(x+2,x+3),new Bits128(x+4,x+5),
                new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static void qword(Map<Long,Integer> m,long a,long value) {for(int j=0;j<8;j++)m.put(a+j,(int)(value>>>(j*8))&255);}
    private static void dword(Map<Long,Integer> m,long a,int value) {for(int j=0;j<4;j++)m.put(a+j,(value>>>(j*8))&255);}
}
