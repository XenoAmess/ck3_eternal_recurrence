package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentErrorCell204WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentErrorCell204WitnessApi.Dispatch;
import org.xar.ck3.research.m5.GovernmentErrorCell204WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner-independent existing-Java scalar and normal-frame data; no target execution. */
public final class GovernmentErrorCell204Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L;
    private static Bits128 x(long seed) { return new Bits128(seed,~seed); }
    private static VolatileBits v(long seed,long rax) {
        return new VolatileBits(rax,seed+1,seed+2,seed+8,seed+9,seed+10,seed+11,
                x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60));
    }
    private static NonvolatileBits n(long seed) {
        return new NonvolatileBits(seed+0x101,seed+0x102,seed+0x103,seed+0x104,
                seed+0x112,seed+0x113,seed+0x114,seed+0x115,x(seed+0x160));
    }
    private static void q(Map<Long,Integer> bytes,long address,long value) {
        for(int k=0;k<8;k++) bytes.put(address+k,(int)(value >>> (k*8)) & 255);
    }
    private static VolatileBits withRax(VolatileBits p,long rax) {
        return new VolatileBits(rax,p.rcxBits(),p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),p.r11Bits(),
                p.xmm0(),p.xmm1(),p.xmm2(),p.xmm3(),p.xmm4(),p.xmm5());
    }
    private static Witness scene(String name,Dispatch dispatch,int ordinal,long site,
            long entryRip,long lowerRax,long resultRax) {
        long seed=0x1111000000000000L+ordinal*0x1000L;
        VolatileBits incoming=v(seed,seed+0xA0);
        NonvolatileBits nv=n(0x2222000000000000L+ordinal*0x1000L);
        VolatileBits post=v(0x3333000000000000L+ordinal*0x1000L,lowerRax);
        Entry entry=new Entry(I,S,incoming,nv);
        Map<Long,Integer> initial=new LinkedHashMap<>();
        for(long address=S-0x40;address<S+0x20;address++) initial.put(address,0xA5);
        q(initial,S,entryRip);
        long marker=0x900000L+ordinal*0x10L;
        q(initial,marker,0x5A5B5C5D5E5F6061L);
        Map<Long,Integer> before=new LinkedHashMap<>(initial);
        q(before,S-0x30,I+0x423B195L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();
        q(mutation,marker,0x8899AABBCCDDEE00L+ordinal);
        Map<Long,Integer> after=new LinkedHashMap<>(before);after.putAll(mutation);
        Call call=new Call(0x423B190L,TargetKind.DIRECT_RVA,0x424FC74L,S-0x28,incoming,nv);
        NormalReturn expected=new NormalReturn(withRax(post,resultRax),entryRip,S+8,nv);
        return new Witness(name,dispatch,entry,site,initial,
                List.of(new CallStep(call,before,mutation,post)),after,expected);
    }
    @Override public List<Witness> witnesses() {
        return List.of(
                scene("directZero",Dispatch.DIRECT,1,0,0x140123456L,0,0x14542F210L),
                scene("directWrap",Dispatch.DIRECT,2,0,0x140234567L,0xFFFFFFFFFFFFFFE0L,0),
                scene("boundResizeB834",Dispatch.BOUND_CALL,3,0x425B834L,0x14425B839L,0x12345000L,0x12345020L),
                scene("boundFreeE384",Dispatch.BOUND_CALL,4,0x424E384L,0x14424E389L,0x200000000L,0x200000020L));
    }
}
