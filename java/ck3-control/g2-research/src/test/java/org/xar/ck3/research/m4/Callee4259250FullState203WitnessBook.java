package org.xar.ck3.research.m4;

import static org.xar.ck3.research.m4.Free61FullState201WitnessBook.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m4.Callee4259250FullState203WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Literal57B expectations; no candidate execution supplies expected data. */
public final class Callee4259250FullState203WitnessBook implements Callee4259250FullState203WitnessApi.Book {
    private static final long I=0x180000000L, S=0x9008L, PRE=0x8FE0L, SLOT=0x8FD8L;
    static VolatileBits rax(VolatileBits v,long rax) {
        return new VolatileBits(rax,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static Witness nullCase() {
        VolatileBits in=v(0x9000123456789ABCL,0L,31), p1=v(0x7000L,0xAAAABBBBCCCCDDDDL,32);
        VolatileBits p2=v(0xF123456789ABCDEFL,0x1122334455667788L,33);
        NonvolatileBits n=n(0x1122334455667788L,31);
        Map<Long,Integer> seed=new HashMap<>(); q(seed,S,0x1234567876543210L); q(seed,0x7000L,0xDEADBEEF01234567L);
        Map<Long,Integer> b1=new HashMap<>(seed); q(b1,SLOT,I+0x425925EL);
        CallStep s1=new CallStep(new Call(0x4259259L,TargetKind.DIRECT_RVA,0x423B18CL,PRE,in,n),b1,Map.of(),p1);
        Map<Long,Integer> b2=new HashMap<>(b1); d(b2,0x7000L,0x16); q(b2,SLOT,I+0x4259269L);
        Map<Long,Integer> mutation=new HashMap<>(); q(mutation,S,0xFEDCBA9876543210L); mutation.put(0x333L,0xAB);
        CallStep s2=new CallStep(new Call(0x4259264L,TargetKind.DIRECT_RVA,0x4232A50L,PRE,p1,n),b2,mutation,p2);
        Map<Long,Integer> end=new HashMap<>(b2); end.putAll(mutation);
        return new Witness("null-two-calls-dword22-allones-fresh-ret",new Entry(I,S,in,n),seed,List.of(s1,s2),end,
                new NormalReturn(rax(p2,-1L),0xFEDCBA9876543210L,0x9010L,n));
    }
    private static Witness tailCase(String name,long block,long heap,long target,int tag,long portRax) {
        VolatileBits in=v(0xABCD123456789000L+tag,block,tag), post=v(portRax,0xBBCC000000000000L+tag,tag+1);
        NonvolatileBits n=n(0xCCDD000000000000L+tag,tag);
        Map<Long,Integer> seed=new HashMap<>(); q(seed,S,0x1234567876543210L);
        q(seed,I+0x5C5DE30L,heap); q(seed,I+0x43DA7C8L,target);
        Tail tail=new Tail(0x4259282L,TargetKind.INDIRECT_ABSOLUTE,target,
                new Entry(I,S,args(in,heap,0L,block),n));
        long ret=0x5678000000000000L+tag;
        Map<Long,Integer> mutation=new HashMap<>(); q(mutation,S,ret); mutation.put(0x400L+tag,0xE1);
        NormalReturn nr=new NormalReturn(post,ret,0x9010L,n);
        Map<Long,Integer> end=new HashMap<>(seed); end.putAll(mutation);
        return new Witness(name,new Entry(I,S,in,n),seed,List.of(new TailStep(tail,seed,mutation,nr)),end,nr);
    }
    @Override public List<Witness> witnesses() {
        return List.of(nullCase(),
                tailCase("nonnull-actual-restored-stack-tail",0x123456789ABCDEF0L,0x1122334455667788L,0x8877665544332211L,34,0xF0E1D2C3B4A59687L),
                tailCase("nonnull-highbits-tail-allones-port-rax",0x8000000000000001L,0xFEDCBA9876543210L,0x9988776655443322L,36,-1L));
    }
}
