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
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** Independent owner GROW32 CPU/byte transcript; model only supplies build overlay. */
public final class GovernmentWholeGrowth200Fixtures implements Book {
    private static final long I=0x140000000L,S=0xbfecd0L,Q=S-0x168L,W=S-0x1a0L,SLOT=S-0x1a8L;
    private static final long CELL=0x6b000000L,DESC=0x6b001000L,HOLDER=0x6b002000L;
    private static final long BEGIN=0x6f0000L,HEAP=0x72000000L,CALLBACK=0x1122334455667788L;
    private record Transcript(TailStep first,List<Event> growth,TailStep third,Map<Long,Integer> carry) {
        private Transcript {growth=List.copyOf(growth);carry=Map.copyOf(carry);}
    }
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeIndexed197Fixtures().witnesses().get(0);
        return List.of(build(base,transcript(base)));
    }
    private static boolean middle(CallStep c) {return c.expected().kind()==TargetKind.DIRECT_RVA
            &&c.expected().callSiteRva()==0x424db58L&&c.expected().targetBits()==0x424dbb0L;}
    private static boolean tail(TailStep t,long site) {return t.expected().jumpSiteRva()==site;}
    private static TailStep findTail(Witness base,long site) {
        return base.crtEvents().stream().filter(e->e instanceof TailStep t&&tail(t,site)).map(e->(TailStep)e).findFirst().orElseThrow();
    }
    private static Transcript transcript(Witness base) {
        TailStep first=findTail(base,0x424800eL),third=findTail(base,0x4248062L);
        CallStep old=base.crtEvents().stream().filter(e->e instanceof CallStep c&&middle(c)).map(e->(CallStep)e).findFirst().orElseThrow();
        Call entry=old.expected();VolatileBits in=entry.volatileBits();NonvolatileBits n=entry.nonvolatileBits();long p=in.rcxBits();
        Map<Long,Integer> inject=new LinkedHashMap<>(first.mutation());inject.putAll(old.mutation());
        qword(inject,p,CELL);qword(inject,p+8,HOLDER);qword(inject,CELL,DESC);qword(inject,HOLDER,CALLBACK);
        qword(inject,DESC,BEGIN);qword(inject,DESC+8,BEGIN);qword(inject,DESC+0x10,BEGIN);qword(inject,I+0x542f0b8L,0L);
        TailStep firstNew=new TailStep(first.expected(),first.expectedMemoryBefore(),inject,first.normalPost());

        Map<Long,Integer> saved=new LinkedHashMap<>();qword(saved,Q+0x10,n.rbxBits());qword(saved,Q+0x18,n.rbpBits());
        qword(saved,Q+0x20,n.rsiBits());qword(saved,Q-8,n.rdiBits());qword(saved,Q-0x10,n.r14Bits());qword(saved,Q-0x18,n.r15Bits());
        Map<Long,Integer> before1=overlay(old.expectedMemoryBefore(),inject);before1.putAll(saved);qword(before1,SLOT,I+0x424dc43L);
        VolatileBits p1=bits(0x2000L,HEAP,0xaaaa111122223333L,0xbbbb222233334444L);
        VolatileBits p2=bits(0x3000L,0xdead000055556666L,0xcccc333344445555L,0xdddd444455556666L);
        List<Event> growth=new ArrayList<>();
        VolatileBits pre1=values(0x20L,BEGIN,0x20L,8L,BEGIN,0L,in.r11Bits(),in);
        NonvolatileBits n1=work(n,0L,0L,BEGIN,0x20L,n.r14Bits(),p);
        growth.add(new CallStep(new Call(0x424dc3eL,TargetKind.DIRECT_RVA,0x425b804L,W,pre1,n1),before1,Map.of(),p1));
        Map<Long,Integer> before2=new LinkedHashMap<>(before1);qword(before2,SLOT,I+0x424dc4dL);
        VolatileBits pre2=values(HEAP,0L,p1.rdxBits(),p1.r8Bits(),p1.r9Bits(),p1.r10Bits(),p1.r11Bits(),p1);
        NonvolatileBits n2=work(n,0L,0L,BEGIN,0x20L,HEAP,p);
        growth.add(new CallStep(new Call(0x424dc48L,TargetKind.DIRECT_RVA,0x424e364L,W,pre2,n2),before2,Map.of(),p2));
        for(int i=0;i<32;i++)growth.add(new LoopStep(0x424dcacL,HEAP+i*8L));

        Map<Long,Integer> carry=new LinkedHashMap<>(inject);carry.putAll(saved);qword(carry,SLOT,I+0x424dc4dL);
        for(int i=0;i<32;i++)qword(carry,HEAP+i*8L,0L);qword(carry,HEAP,CALLBACK);
        qword(carry,DESC,HEAP);qword(carry,DESC+8,HEAP+8);qword(carry,DESC+0x10,HEAP+0x100);
        Entry oldThird=third.expected().entry();VolatileBits tv=oldThird.volatileBits();
        VolatileBits tailPre=values(tv.raxBits(),tv.rcxBits(),0L,0x40L,HEAP,0L,p2.r11Bits(),p2);
        TailStep thirdNew=new TailStep(new Tail(third.expected().jumpSiteRva(),third.expected().kind(),third.expected().targetBits(),
                new Entry(oldThird.imageBaseBits(),oldThird.rspBits(),tailPre,oldThird.nonvolatileBits())),
                overlay(third.expectedMemoryBefore(),carry),third.mutation(),third.normalPost());
        return new Transcript(firstNew,growth,thirdNew,carry);
    }
    private static NonvolatileBits work(NonvolatileBits n,long bx,long bp,long si,long di,long r14,long r15) {
        return new NonvolatileBits(bx,bp,si,di,n.r12Bits(),n.r13Bits(),r14,r15,n.xmm6());
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
            if (e instanceof TailStep ts && ts.expected().jumpSiteRva() == 0x424800eL) {
                newCrt.add(t.first());
            } else if (e instanceof CallStep cs && middle(cs)) {
                newCrt.addAll(t.growth());
                after = true;
            } else if (e instanceof TailStep ts && ts.expected().jumpSiteRva() == 0x4248062L) {
                newCrt.add(t.third());
            } else {
                newCrt.add(after ? crt(e, t.carry()) : e);
            }
        }
        var oldWhole = base.legacy().whole();
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole200-grow32",
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
