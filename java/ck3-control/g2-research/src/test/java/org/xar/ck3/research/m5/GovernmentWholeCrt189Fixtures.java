package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsPort;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** ONE independent whole189 literal. Old Books supply immutable data only, never
 * subject outputs. Two model rounds were rejected; target Java was not read/run.
 * Opaque V/mutations and source-constrained tail return frames are explicit input. */
public final class GovernmentWholeCrt189Fixtures implements GovernmentWholeCrt189WitnessApi.Book {
    private static final long I=0x140000000L,S=0xbfecd0L,G=0x600000L;
    private static final long TOKEN_ROOT=0x145dc1128L,TOKEN_GUARD=0x145dc1124L;
    private static final long CRIT=0x145c5cb18L,INDEX=0x145c5cbc4L,EPOCH=0x14542f090L;
    private static final long REG_G=0x145c5cb68L,REG_H=0x145c5d698L,CALLBACK=0x1443d7570L;
    private static final long ENTER=0x7777000011112222L,RELEASE=0x8888000033334444L;
    private record CrtData(List<Event> events,Map<Long,Integer> carry) { }

    @Override public List<Witness> witnesses() {
        var base=new GovernmentWholeToken184Fixtures().witnesses().get(0);var old=base.whole();
        var stages=new GovernmentWholeRoot181Fixtures().witnesses().get(0).whole().ordinaryCalls();
        Map<Long,Integer> owned=ownedInput(),seed=map(old.memorySeed());seed.putAll(owned);
        for(long a=S-0x140L;a<S-0x80L;a++) seed.put(a,0xa5);
        CrtData crt=crt(stages.get(0),owned);

        Map<Long,Integer> before1=stage(stages.get(1).expectedMemoryBytes(),owned,crt.carry());
        Map<Long,Integer> before2=stage(stages.get(3).expectedMemoryBytes(),owned,crt.carry());
        qword(before1,S-0x28L,TOKEN_ROOT);qword(before2,S-0x28L,TOKEN_ROOT);
        List<OrdinaryStep> calls=List.of(diag(base.whole().ordinaryCalls().get(0),before1,postH()),
                diag(base.whole().ordinaryCalls().get(1),before2,stages.get(2).expected().volatileBits()));
        Map<Long,Integer> end=stage(old.expectedFinalBytes(),owned,crt.carry());qword(end,S-0x28L,TOKEN_ROOT);
        var whole=new GovernmentWhole4798WitnessApi.Witness("whole189-first-CRT-init-second-epoch-hot",
                old.entry(),memory(seed),old.gs58Bits(),old.initialCalls(),calls,old.lookupCalls(),old.cpuCalls(),
                old.budgets(),old.afterInitial(),old.afterFinal(),old.post153(),end,old.expectedResult(),old.failure());
        List<GsStep> gs=new ArrayList<>(base.gsSteps().subList(0,4));
        gs.add(new GsStep(GsPort.ORDINARY,0x700000L));gs.add(base.gsSteps().get(4));gs.add(base.gsSteps().get(5));
        gs.add(new GsStep(GsPort.ORDINARY,0x700000L));gs.add(base.gsSteps().get(6));gs.add(base.gsSteps().get(7));
        var legacy=new GovernmentWholeConcrete173WitnessApi.Witness(whole,base.m0HashMxcsrAt4FE(),base.m1HashMxcsrAt85E(),
                base.deepSteps(),base.atomicSteps(),gs);
        return List.of(new Witness(legacy,crt.events()));
    }

    private static CrtData crt(OrdinaryStep lookup,Map<Long,Integer> owned) {
        NonvolatileBits n=lookup.expected().nonvolatileBits();VolatileBits entry=lookup.expected().volatileBits();
        Map<Long,Integer> current=stage(lookup.expectedMemoryBytes(),owned,Map.of());
        List<Event> events=new ArrayList<>();
        qword(current,S-0x88L,I+0x3f4f987L);qword(current,S-0x90L,n.rbxBits());qword(current,S-0xb8L,I+0x4223a9aL);
        VolatileBits headerPre=fields(0xffffffffL,CRIT,0x10L,2L,0L,entry.r10Bits(),entry.r11Bits(),entry);
        events.add(call(0x4223a94L,TargetKind.INDIRECT_ABSOLUTE,ENTER,S-0xb0L,headerPre,
                frameN(n,TOKEN_GUARD,n.rbpBits()),current,Map.of(),postC()));
        events.add(new LoopStep(0x4223a9aL,TOKEN_GUARD));dword(current,TOKEN_GUARD,0xffffffff);
        VolatileBits headerTail=fields(0xc000L,CRIT,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,postC());
        events.add(tail(0x4223ae4L,TargetKind.INDIRECT_ABSOLUTE,RELEASE,headerTail,n,current,postD(),I+0x3f4f987L));

        rootInit(current);
        qword(current,S-0x88L,I+0x3f4f9ebL);qword(current,S-0xb8L,I+0x4223f2dL);
        // Actual M4 and tail-forwarded M1 table own these literal writes.
        db38Before(current,n);
        Map<Long,Integer> mutation=new LinkedHashMap<>();qword(mutation,REG_H,0x33445566778899aaL);
        VolatileBits dbPre=fields(2L,S-0xd0L,S-0x110L,S-0x108L,S-0xc8L,0xd555L,0xd666L,postD());
        events.add(call(0x424df29L,TargetKind.DIRECT_RVA,0x424db38L,S-0x130L,dbPre,
                frameN(n,CALLBACK,S-0xf0L),current,mutation,db38Post()));
        current.putAll(mutation);

        qword(current,S-0x88L,I+0x3f4f9f8L);qword(current,S-0x90L,n.rbxBits());qword(current,S-0xb8L,I+0x4223a3aL);
        VolatileBits db=db38Post();
        VolatileBits footerPre=fields(0L,CRIT,CALLBACK,db.r8Bits(),db.r9Bits(),db.r10Bits(),db.r11Bits(),db);
        events.add(call(0x4223a34L,TargetKind.INDIRECT_ABSOLUTE,ENTER,S-0xb0L,footerPre,
                frameN(n,TOKEN_GUARD,n.rbpBits()),current,Map.of(),postF()));
        dword(current,EPOCH,0x42);dword(current,TOKEN_GUARD,0x42);
        events.add(new GovernmentCrtBoundary185WitnessApi.GsStep(0x700000L));dword(current,0x710010L,0x42);
        qword(current,S-0xb8L,I+0x4223a7aL);
        VolatileBits releasePre=fields(0x42L,CRIT,0L,0x710000L,0x10L,0xf555L,0xf666L,postF());
        events.add(call(0x4223a74L,TargetKind.INDIRECT_ABSOLUTE,RELEASE,S-0xb0L,releasePre,
                frameN(n,TOKEN_GUARD,n.rbpBits()),current,Map.of(),postG()));
        events.add(tail(0x4223a7fL,TargetKind.DIRECT_RVA,0x4223aecL,postG(),n,current,postH(),I+0x3f4f9f8L));

        Map<Long,Integer> carry=new LinkedHashMap<>();
        rootInit(carry);dword(carry,EPOCH,0x42);dword(carry,TOKEN_GUARD,0x42);dword(carry,0x710010L,0x42);
        qword(carry,REG_H,0x33445566778899aaL);qword(carry,S-0x90L,n.rbxBits());
        qword(carry,S-0xb8L,I+0x4223a7aL);db38Before(carry,n);
        // S-88 is later overwritten by helper C090; retain each independent stage's bytes.
        return new CrtData(List.copyOf(events),Map.copyOf(carry));
    }

    private static void db38Before(Map<Long,Integer> bytes,NonvolatileBits n) {
        qword(bytes,S-0xc0L,n.rbxBits());qword(bytes,S-0xe8L,I+0x4223f00L);
        qword(bytes,S-0xd8L,CALLBACK);qword(bytes,S-0xe0L,REG_H);qword(bytes,S-0xf0L,n.rbpBits());
        qword(bytes,S-0x108L,S-0xe0L);qword(bytes,S-0x100L,S-0xd8L);
        dword(bytes,S-0xc8L,2);dword(bytes,S-0x110L,2);qword(bytes,S-0x138L,I+0x424df2eL);
    }
    private static Map<Long,Integer> stage(Map<Long,Integer> prior,Map<Long,Integer> owned,Map<Long,Integer> carry) {
        Map<Long,Integer> out=new LinkedHashMap<>(prior);
        for(long a=S-0x140L;a<S-0x80L;a++) out.putIfAbsent(a,0xa5);
        out.putAll(owned);out.putAll(carry);return out;
    }
    private static Map<Long,Integer> ownedInput() {
        Map<Long,Integer> m=new LinkedHashMap<>();
        qword(m,I+0x5cbede8L,0xe00000L);dword(m,0xe00000L,0);qword(m,0xe00048L,0xe10000L);
        dword(m,0xe00054L,0x165);qword(m,0xe10000L+0x165L*8L,0);
        dword(m,0x710010L,0xffffffff);dword(m,TOKEN_GUARD,0);
        for(long a=TOKEN_ROOT;a<TOKEN_ROOT+32;a++) m.put(a,0x7b);
        dword(m,I+0x472c488L,0xf4338211);word(m,I+0x472c48cL,0xe655);m.put(I+0x472c48eL,0xf7);
        qword(m,I+0x43da500L,ENTER);qword(m,I+0x43da4f0L,RELEASE);dword(m,INDEX,0);dword(m,EPOCH,0x41);
        qword(m,REG_G,-1L);qword(m,REG_H,0x1122334455667788L);return m;
    }
    private static void rootInit(Map<Long,Integer> m) {
        qword(m,TOKEN_ROOT,0);qword(m,TOKEN_ROOT+0x18L,15);qword(m,TOKEN_ROOT+0x10L,7);
        dword(m,TOKEN_ROOT,0xf4338211);word(m,TOKEN_ROOT+4L,0xe655);m.put(TOKEN_ROOT+6L,0xf7);m.put(TOKEN_ROOT+7L,0);
    }
    private static OrdinaryStep diag(OrdinaryStep prior,Map<Long,Integer> before,VolatileBits source) {
        OpaqueCall p=prior.expected();VolatileBits v=p.volatileBits();NonvolatileBits n=p.nonvolatileBits();
        VolatileBits pre=fields(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),source.r11Bits(),source);
        NonvolatileBits nv=new NonvolatileBits(n.rbxBits(),n.rbpBits(),n.rsiBits(),TOKEN_ROOT,
                n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        return new OrdinaryStep(new OpaqueCall(p.callSiteRva(),p.targetRva(),p.rspBits(),pre,nv),before,
                prior.mutation(),prior.normalPost(),prior.unsupported());
    }
    private static CallStep call(long site,TargetKind kind,long target,long rsp,VolatileBits pre,NonvolatileBits nv,
            Map<Long,Integer> before,Map<Long,Integer> mutation,VolatileBits post) {
        return new CallStep(new Call(site,kind,target,rsp,pre,nv),before,mutation,post);
    }
    private static TailStep tail(long site,TargetKind kind,long target,VolatileBits pre,NonvolatileBits n,
            Map<Long,Integer> before,VolatileBits post,long returnRip) {
        return new TailStep(new Tail(site,kind,target,new Entry(I,S-0x88L,pre,n)),before,Map.of(),
                new NormalReturn(post,returnRip,S-0x80L,n));
    }
    private static NonvolatileBits frameN(NonvolatileBits n,long bx,long bp) {
        return new NonvolatileBits(bx,bp,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static VolatileBits db38Post() {
        return new VolatileBits(0xabcdef0000000000L,0xe002L,0xf002L,0xe208L,0xe209L,0xe20aL,0xe20bL,
                vector(0xe210L),vector(0xe220L),vector(0xe230L),vector(0xe240L),vector(0xe250L),vector(0xe260L));
    }
    private static Bits128 vector(long seed) {return new Bits128(seed,~seed);}
    private static VolatileBits postC() {return seq(0xc000L,0xd000L);}
    private static VolatileBits postD() {return seq(0xd000L,0xe000L);}
    private static VolatileBits postF() {return seq(0xf000L,0x10000L);}
    private static VolatileBits postG() {return seq(0x10000L,0x11000L);}
    private static VolatileBits postH() {return seq(0x11000L,0x12000L);}
    private static VolatileBits seq(long a,long x) {
        return new VolatileBits(a,a+0x111,a+0x222,a+0x333,a+0x444,a+0x555,a+0x666,
                new Bits128(x,x+1),new Bits128(x+2,x+3),new Bits128(x+4,x+5),
                new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static VolatileBits fields(long a,long c,long d,long r8,long r9,long r10,long r11,VolatileBits x) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,x.xmm0(),x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());
    }
    private static Map<Long,Integer> map(MemorySeed seed) {
        Map<Long,Integer> out=new LinkedHashMap<>();for(SeedByte b:seed.bytes()) out.put(b.addressBits(),b.byteBits());return out;
    }
    private static MemorySeed memory(Map<Long,Integer> m) {
        return new MemorySeed(m.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static void qword(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++) m.put(a+j,(int)(v>>>(j*8))&255);}
    private static void dword(Map<Long,Integer> m,long a,int v) {for(int j=0;j<4;j++) m.put(a+j,(v>>>(j*8))&255);}
    private static void word(Map<Long,Integer> m,long a,int v) {m.put(a,v&255);m.put(a+1,(v>>>8)&255);}
}
