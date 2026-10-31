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
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Subject;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent five-case literal data from the three held raw bodies. All four
 * bounded model candidates were rejected; target185 Java was neither read nor run.
 * Opaque target bits, post-vectors and full tail returns are artificial owned input. */
public final class GovernmentCrtBoundary185Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L,BODY=0x7fffe0L,SLOT=0x7fffd8L,SAVED=0x800000L;
    private static final long RIP=0x123456789abcdef0L,G=0x900000L,GS=0xa00000L,TLS=0xa10000L;
    private static final long CRIT=0x145c5cb18L,INDEX=0x145c5cbc4L,EPOCH=0x14542f090L;
    private static final long CALL_TARGET=0x7777000011112222L,RELEASE_TARGET=0x8888000033334444L;
    private static final long CHANGED_RBX=0xabcdef0123456789L;

    @Override public List<Witness> witnesses() {
        return List.of(headerClaim(),headerWait(),footer(),
                wrapper("wrapper-fullRAX-zero",0L,0xffffffffL),
                wrapper("wrapper-fullRAX-highnonzero-lowzero",0x100000000L,0L));
    }

    private static Witness headerClaim() {
        Map<Long,Integer> seed=seed(0,0x2468ace1),current=new LinkedHashMap<>(seed);
        qword(current,SAVED,0xb000L);qword(current,SLOT,0x144223a9aL);
        List<Event> events=new ArrayList<>();
        events.add(call(0x4223a94L,TargetKind.INDIRECT_ABSOLUTE,CALL_TARGET,
                firstPre(),nv(G),current,Map.of(),postC()));
        events.add(new LoopStep(0x4223a9aL,G));
        dword(current,G,0xffffffff);
        VolatileBits tailV=v(0xc000L,CRIT,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        events.add(tail(0x4223ae4L,TargetKind.INDIRECT_ABSOLUTE,RELEASE_TARGET,tailV,nv(0xb000L),current));
        return witness("header-zero-claims-minusone-then-indirect-tail",Subject.RVA_4223A84,
                seed,events,current,tailReturn());
    }

    private static Witness headerWait() {
        Map<Long,Integer> seed=seed(0xffffffff,0x2468ace1),current=new LinkedHashMap<>(seed);
        qword(current,SAVED,0xb000L);qword(current,SLOT,0x144223a9aL);
        List<Event> events=new ArrayList<>();
        events.add(call(0x4223a94L,TargetKind.INDIRECT_ABSOLUTE,CALL_TARGET,
                firstPre(),nv(G),current,Map.of(),postC()));
        events.add(new LoopStep(0x4223a9aL,G));
        qword(current,SLOT,0x144223aaeL);
        Map<Long,Integer> mutation=new LinkedHashMap<>();dword(mutation,G,7);qword(mutation,SAVED,CHANGED_RBX);
        VolatileBits waitPre=v(0xc000L,0x64L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        events.add(call(0x4223aa9L,TargetKind.DIRECT_RVA,0x4223b30L,
                waitPre,nv(G),current,mutation,postD()));
        current.putAll(mutation);
        events.add(new LoopStep(0x4223a9aL,G));events.add(new GsStep(GS));
        dword(current,TLS+0x10L,0x2468ace1);
        VolatileBits tailV=v(0x2468ace1L,CRIT,TLS,0x10L,0xd444L,0xd555L,0xd666L,0xe000L);
        events.add(tail(0x4223ae4L,TargetKind.INDIRECT_ABSOLUTE,RELEASE_TARGET,tailV,nv(CHANGED_RBX),current));
        return witness("header-wait-freshguard-epoch-TLS-freshsavedRBX",Subject.RVA_4223A84,
                seed,events,current,tailReturn());
    }

    private static Witness footer() {
        Map<Long,Integer> seed=seed(5,0xffffffff),current=new LinkedHashMap<>(seed);
        qword(current,SAVED,0xb000L);qword(current,SLOT,0x144223a3aL);
        List<Event> events=new ArrayList<>();
        events.add(call(0x4223a34L,TargetKind.INDIRECT_ABSOLUTE,CALL_TARGET,
                firstPre(),nv(G),current,Map.of(),postC()));
        dword(current,EPOCH,0);dword(current,G,0);events.add(new GsStep(GS));
        dword(current,TLS+0x10L,0);qword(current,SLOT,0x144223a7aL);
        VolatileBits secondPre=v(0L,CRIT,3L,TLS,0x10L,0xc555L,0xc666L,0xd000L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();qword(mutation,SAVED,CHANGED_RBX);
        events.add(call(0x4223a74L,TargetKind.INDIRECT_ABSOLUTE,RELEASE_TARGET,
                secondPre,nv(G),current,mutation,postD()));
        current.putAll(mutation);
        events.add(tail(0x4223a7fL,TargetKind.DIRECT_RVA,0x4223aecL,postD(),nv(CHANGED_RBX),current));
        return witness("footer-epoch-wrap-secondcall-fullV-freshsavedRBX-directtail",Subject.RVA_4223A24,
                seed,events,current,tailReturn());
    }

    private static Witness wrapper(String name,long opaqueRax,long expectedRax) {
        Map<Long,Integer> seed=seed(5,0x2468ace1),current=new LinkedHashMap<>(seed);
        qword(current,SLOT,0x144223f2dL);
        VolatileBits post=v(opaqueRax,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        CallStep call=call(0x4223f28L,TargetKind.DIRECT_RVA,0x4223ee8L,
                entryV(),nv(0xb000L),current,Map.of(),post);
        VolatileBits end=v(expectedRax,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        return witness(name,Subject.RVA_4223F24,seed,List.of(call),current,
                new NormalReturn(end,RIP,0x800010L,nv(0xb000L)));
    }

    private static Witness witness(String name,Subject subject,Map<Long,Integer> seed,List<Event> events,
            Map<Long,Integer> end,NormalReturn expected) {
        return new Witness(name,subject,new Entry(I,S,entryV(),nv(0xb000L)),seed,events,end,expected);
    }
    private static CallStep call(long site,TargetKind kind,long target,VolatileBits pre,NonvolatileBits nv,
            Map<Long,Integer> before,Map<Long,Integer> mutation,VolatileBits post) {
        return new CallStep(new Call(site,kind,target,BODY,pre,nv),before,mutation,post);
    }
    private static TailStep tail(long site,TargetKind kind,long target,VolatileBits pre,NonvolatileBits nv,
            Map<Long,Integer> before) {
        return new TailStep(new Tail(site,kind,target,new Entry(I,S,pre,nv)),before,Map.of(),tailReturn());
    }
    private static Map<Long,Integer> seed(int guard,int epoch) {
        Map<Long,Integer> out=new LinkedHashMap<>();
        for(long a=0x7fff80L;a<0x800040L;a++) out.put(a,0xa5);
        qword(out,S,RIP);dword(out,G,guard);dword(out,INDEX,3);dword(out,EPOCH,epoch);
        qword(out,GS+3L*8L,TLS);dword(out,TLS+0x10L,0x11223344);
        qword(out,I+0x43da500L,CALL_TARGET);qword(out,I+0x43da4f0L,RELEASE_TARGET);
        return out;
    }
    private static VolatileBits entryV() {
        return v(0xa000L,G,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
    }
    private static VolatileBits firstPre() {
        return v(0xa000L,CRIT,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
    }
    private static VolatileBits postC() {
        return v(0xc000L,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
    }
    private static VolatileBits postD() {
        return v(0xd000L,0xd111L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);
    }
    private static NonvolatileBits nv(long rbx) {
        return new NonvolatileBits(rbx,0xb111L,0xb222L,0xb333L,0xb444L,0xb555L,0xb666L,0xb777L,
                new Bits128(0xb100L,0xb101L));
    }
    private static NormalReturn tailReturn() {
        NonvolatileBits nv=new NonvolatileBits(0x11000L,0x11111L,0x11222L,0x11333L,0x11444L,
                0x11555L,0x11666L,0x11777L,new Bits128(0x11800L,0x11801L));
        return new NormalReturn(v(0xf000L,0xf111L,0xf222L,0xf333L,0xf444L,0xf555L,0xf666L,0x10000L),
                0x1111222233334444L,0x880010L,nv);
    }
    private static VolatileBits v(long rax,long rcx,long rdx,long r8,long r9,long r10,long r11,long x) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,
                new Bits128(x,x+1),new Bits128(x+2,x+3),new Bits128(x+4,x+5),
                new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
}
