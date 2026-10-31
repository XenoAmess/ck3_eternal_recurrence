package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** Owner independent Resize149/Free61-null CPU and byte transcript. Model only builds overlay. */
public final class GovernmentWholeResizeFree202Fixtures implements Book {
    private static final long I=0x140000000L,S=0xbfecd0L,T=S-0x1a8L,W=S-0x1d0L,SLOT=S-0x1d8L;
    private static final long HEAP=0x72000000L,BEGIN=0x6f0000L;
    private record Transcript(List<CallStep> resize,TailStep third,Map<Long,Integer> carry) {
        private Transcript {resize=List.copyOf(resize);carry=Map.copyOf(carry);}
    }
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeGrowth200Fixtures().witnesses().get(0);
        return List.of(build(base,transcript(base)));
    }
    private static boolean allocation(CallStep c) {return c.expected().kind()==TargetKind.DIRECT_RVA
            &&c.expected().callSiteRva()==0x424dc3eL&&c.expected().targetBits()==0x425b804L;}
    private static boolean freeNull(CallStep c) {return c.expected().kind()==TargetKind.DIRECT_RVA
            &&c.expected().callSiteRva()==0x424dc48L&&c.expected().targetBits()==0x424e364L;}
    private static Transcript transcript(Witness base) {
        CallStep old=base.crtEvents().stream().filter(e->e instanceof CallStep c&&allocation(c)).map(e->(CallStep)e).findFirst().orElseThrow();
        TailStep third=base.crtEvents().stream().filter(e->e instanceof TailStep t&&t.expected().jumpSiteRva()==0x4248062L)
                .map(e->(TailStep)e).findFirst().orElseThrow();
        VolatileBits in=old.expected().volatileBits();NonvolatileBits n=old.expected().nonvolatileBits();
        Map<Long,Integer> saved=new LinkedHashMap<>();qword(saved,T+8,n.rbxBits());qword(saved,T+0x10,n.rbpBits());
        qword(saved,T+0x18,n.rsiBits());qword(saved,T-8,n.rdiBits());
        Map<Long,Integer> beforeSize=overlay(old.expectedMemoryBefore(),saved);qword(beforeSize,SLOT,I+0x425b84dL);
        VolatileBits sizePost=bits(0x5000L,16L,0xabcd777788889999L,0xbcde88889999aaaaL);
        VolatileBits sizePre=values(0x07ffffffffffffffL,BEGIN,0L,8L,in.r9Bits(),in.r10Bits(),in.r11Bits(),in);
        CallStep size=new CallStep(new Call(0x425b848L,TargetKind.DIRECT_RVA,0x4259250L,W,sizePre,
                work(n,0x20L,8L,BEGIN,n.rdiBits())),beforeSize,Map.of(),sizePost);

        Map<Long,Integer> beforeAlloc=new LinkedHashMap<>(beforeSize);qword(beforeAlloc,SLOT,I+0x425b863L);
        Map<Long,Integer> allocated=new LinkedHashMap<>();for(int i=0;i<256;i++)allocated.put(HEAP+i,0xa5);
        VolatileBits allocPost=bits(0x6000L,HEAP,0xcdef9999aaaabbbbL,0xdef0aaaabbbbccccL);
        VolatileBits allocPre=values(16L,BEGIN,0x100L,sizePost.r8Bits(),sizePost.r9Bits(),sizePost.r10Bits(),sizePost.r11Bits(),sizePost);
        CallStep alloc=new CallStep(new Call(0x425b85eL,TargetKind.DIRECT_RVA,0x4251f4cL,W,allocPre,
                work(n,0x100L,8L,BEGIN,16L)),beforeAlloc,allocated,allocPost);

        Map<Long,Integer> beforeFill=overlay(beforeAlloc,allocated);qword(beforeFill,SLOT,I+0x425b881L);
        Map<Long,Integer> cleared=new LinkedHashMap<>();for(int i=16;i<256;i++)cleared.put(HEAP+i,0);
        VolatileBits fillPost=bits(0x4000L,0xdead000055556666L,0xeeee555566667777L,0xffff666677778888L);
        VolatileBits fillPre=values(HEAP,HEAP+16,0L,0xf0L,allocPost.r9Bits(),allocPost.r10Bits(),allocPost.r11Bits(),allocPost);
        CallStep fill=new CallStep(new Call(0x425b87cL,TargetKind.DIRECT_RVA,0x4226f10L,W,fillPre,
                work(n,0xf0L,8L,HEAP,16L)),beforeFill,cleared,fillPost);

        Map<Long,Integer> carry=new LinkedHashMap<>(saved);qword(carry,SLOT,I+0x425b881L);
        Entry e=third.expected().entry();VolatileBits oldV=e.volatileBits();
        VolatileBits next=values(oldV.raxBits(),oldV.rcxBits(),0L,0x40L,HEAP,0L,fillPost.r11Bits(),fillPost);
        TailStep thirdNew=new TailStep(new Tail(third.expected().jumpSiteRva(),third.expected().kind(),third.expected().targetBits(),
                new Entry(e.imageBaseBits(),e.rspBits(),next,e.nonvolatileBits())),overlay(third.expectedMemoryBefore(),carry),
                third.mutation(),third.normalPost());
        return new Transcript(List.of(size,alloc,fill),thirdNew,carry);
    }
    private static NonvolatileBits work(NonvolatileBits n,long bx,long bp,long si,long di) {
        return new NonvolatileBits(bx,bp,si,di,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static VolatileBits bits(long s,long a,long c,long d) {
        return new VolatileBits(a,c,d,s+8,s+9,s+10,s+11,vector(s+0x10),vector(s+0x20),vector(s+0x30),
                vector(s+0x40),vector(s+0x50),vector(s+0x60));
    }
    private static Bits128 vector(long v) {return new Bits128(v,~v);}
    private static VolatileBits values(long a,long c,long d,long r8,long r9,long r10,long r11,VolatileBits x) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,x.xmm0(),x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());
    }
    private static Map<Long,Integer> overlay(Map<Long,Integer> old,Map<Long,Integer> state) {
        Map<Long,Integer> m=new LinkedHashMap<>(old);m.putAll(state);return m;
    }
    private static OrdinaryStep ordinary(OrdinaryStep p,Map<Long,Integer> state) {
        return new OrdinaryStep(p.expected(),overlay(p.expectedMemoryBytes(),state),p.mutation(),p.normalPost(),p.unsupported());
    }
    private static Event crt(Event p,Map<Long,Integer> state) {
        if(p instanceof CallStep c)return new CallStep(c.expected(),overlay(c.expectedMemoryBefore(),state),c.mutation(),c.normalPost());
        if(p instanceof TailStep t)return new TailStep(t.expected(),overlay(t.expectedMemoryBefore(),state),t.mutation(),t.normalPost());
        return p;
    }
    private static void qword(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}

    private static Witness build(Witness base, Transcript t) {
        List<Event> newCrt = new ArrayList<>();
        boolean after = false;
        for (Event e : base.crtEvents()) {
            if (e instanceof CallStep cs && allocation(cs)) {
                newCrt.addAll(t.resize());
                after = true;
            } else if (e instanceof CallStep cs && freeNull(cs)) {
                // Removed entirely
            } else if (e instanceof TailStep ts && ts.expected().jumpSiteRva() == 0x4248062L) {
                newCrt.add(t.third());
            } else {
                newCrt.add(after ? crt(e, t.carry()) : e);
            }
        }
        var oldWhole = base.legacy().whole();
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole202-resize-free",
            oldWhole.entry(),
            oldWhole.memorySeed(),
            oldWhole.gs58Bits(),
            oldWhole.initialCalls(),
            oldWhole.ordinaryCalls().stream().map(p -> ordinary(p, t.carry())).toList(),
            oldWhole.lookupCalls(),
            oldWhole.cpuCalls(),
            oldWhole.budgets(),
            oldWhole.afterInitial(),
            oldWhole.afterFinal(),
            oldWhole.post153(),
            overlay(oldWhole.expectedFinalBytes(), t.carry()),
            oldWhole.expectedResult(),
            oldWhole.failure()
        );
        var oldLegacy = base.legacy();
        var newLegacy = new GovernmentWholeConcrete173WitnessApi.Witness(
            newWhole,
            oldLegacy.m0HashMxcsrAt4FE(),
            oldLegacy.m1HashMxcsrAt85E(),
            oldLegacy.deepSteps(),
            oldLegacy.atomicSteps(),
            oldLegacy.gsSteps()
        );
        return new Witness(newLegacy, newCrt);
    }
}
