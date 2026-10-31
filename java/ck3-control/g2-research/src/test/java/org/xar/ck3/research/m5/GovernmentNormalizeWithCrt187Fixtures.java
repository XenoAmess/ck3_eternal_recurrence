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
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.CrtCallStep;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.CrtLoopStep;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.CrtTailStep;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.Port;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent ONE174->182->185 raw-source literal after two rejected model rounds.
 * Old174 supplies frozen input data only; no subject Java was read or executed.
 * All remaining opaque posts/targets/tail normal-return frames are explicit input. */
public final class GovernmentNormalizeWithCrt187Fixtures implements Book {
    private static final long I=0x140000000L,LOCK=0xe00000L,TABLE=0xe10000L;
    private static final long GUARD=0x145dc1124L,ROOT=0x145dc1128L,CONST=0x14472c488L;
    private static final long CRIT=0x145c5cb18L,INDEX=0x145c5cbc4L,EPOCH=0x14542f090L;
    private static final long CRT_BODY=0x6fff60L,CRT_ENTRY=0x6fff88L,CRT_SLOT=0x6fff58L,SAVED=0x6fff80L;
    private static final long ENTER=0x7777000011112222L,RELEASE=0x8888000033334444L;

    @Override public List<Witness> witnesses() {
        var base=new GovernmentNormalizeFull174Fixtures().witnesses().get(1);
        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(var b:base.memorySeed()) seed.put(b.addressBits(),b.byteBits());
        input(seed);
        Map<Long,Integer> current=new LinkedHashMap<>(seed);
        qword(current,0x700010L,0xb000L);qword(current,0x700018L,0xb222L);qword(current,0x700000L,0xb333L);
        qword(current,0x6fffb8L,0x1430a2d43L);
        List<Event> events=new ArrayList<>();
        events.add(new AtomicStep(LOCK,2,0,2));events.add(new AtomicStep(LOCK,-2,2,0));
        events.add(new GsStep(Port.ORDINARY,0xb00000L));

        // The real182 caller and real185 prologue own these slots before the IAT port.
        qword(current,CRT_ENTRY,0x143f4f987L);qword(current,SAVED,0x100018L);
        qword(current,CRT_SLOT,0x144223a9aL);
        VolatileBits headerPre=v(0xffffffffL,CRIT,0x10L,2L,0L,0xa555L,0xa666L,0xb000L);
        events.add(call(0x4223a94L,TargetKind.INDIRECT_ABSOLUTE,ENTER,headerPre,workingNv(GUARD),current,postC()));
        events.add(new CrtLoopStep(0x4223a9aL,GUARD));dword(current,GUARD,0xffffffff);
        VolatileBits headerTailPre=v(0xc000L,CRIT,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        events.add(tail(0x4223ae4L,TargetKind.INDIRECT_ABSOLUTE,RELEASE,headerTailPre,current,
                new NormalReturn(postD(),0x143f4f987L,0x6fff90L,workingNv(0x100018L))));

        // Real182 init leaves ROOT+8 padding intact and consumes the seven owned bytes.
        qword(current,ROOT,0);qword(current,ROOT+0x18L,15);qword(current,ROOT+0x10L,7);
        dword(current,ROOT,0xf4338211);word(current,ROOT+4L,0xe655);
        current.put(ROOT+6L,0xf7);current.put(ROOT+7L,0);
        qword(current,CRT_ENTRY,0x143f4f9ebL);qword(current,CRT_SLOT,0x144223f2dL);
        VolatileBits wrapperPre=v(0xf7L,0x1443d7570L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);
        events.add(call(0x4223f28L,TargetKind.DIRECT_RVA,0x4223ee8L,wrapperPre,workingNv(0x100018L),current,postE()));

        // Wrapper's rawRAX1 becomes0; the following caller LEA and footer LEA set RCX.
        qword(current,CRT_ENTRY,0x143f4f9f8L);qword(current,SAVED,0x100018L);
        qword(current,CRT_SLOT,0x144223a3aL);
        VolatileBits footerPre=v(0L,CRIT,0xe222L,0xe333L,0xe444L,0xe555L,0xe666L,0xf000L);
        events.add(call(0x4223a34L,TargetKind.INDIRECT_ABSOLUTE,ENTER,footerPre,workingNv(GUARD),current,postF()));
        dword(current,EPOCH,0x42);dword(current,GUARD,0x42);
        events.add(new GsStep(Port.CRT,0xa00000L));dword(current,0xa10010L,0x42);
        qword(current,CRT_SLOT,0x144223a7aL);
        VolatileBits releasePre=v(0x42L,CRIT,3L,0xa10000L,0x10L,0xf555L,0xf666L,0x10000L);
        events.add(call(0x4223a74L,TargetKind.INDIRECT_ABSOLUTE,RELEASE,releasePre,workingNv(GUARD),current,postG()));
        events.add(tail(0x4223a7fL,TargetKind.DIRECT_RVA,0x4223aecL,postG(),current,
                new NormalReturn(postH(),0x143f4f9f8L,0x6fff90L,workingNv(0x100018L))));
        events.add(new GsStep(Port.ORDINARY,0x500000L));

        VolatileBits end=v(3L,0x500000L,0x600000L,0x158L,0x11444L,0x11555L,0x11666L,0x12000L);
        var expected=new GovernmentNormalizeFull174Api.NormalReturn(end,base.expected().returnRipBits(),
                base.expected().callerRspBits(),base.entry().nonvolatileBits());
        return List.of(new Witness("actual-normalizer-token-CRT-init-TLS-block",base.entry(),seed,events,current,expected));
    }

    private static CrtCallStep call(long site,TargetKind kind,long target,VolatileBits pre,NonvolatileBits nv,
            Map<Long,Integer> before,VolatileBits post) {
        return new CrtCallStep(new Call(site,kind,target,CRT_BODY,pre,nv),before,Map.of(),post);
    }
    private static CrtTailStep tail(long site,TargetKind kind,long target,VolatileBits pre,
            Map<Long,Integer> before,NormalReturn post) {
        return new CrtTailStep(new Tail(site,kind,target,new Entry(I,CRT_ENTRY,pre,workingNv(0x100018L))),before,Map.of(),post);
    }
    private static void input(Map<Long,Integer> seed) {
        qword(seed,I+0x5cbede8L,LOCK);dword(seed,LOCK,0);qword(seed,LOCK+0x48L,TABLE);
        dword(seed,LOCK+0x54L,0x2807);qword(seed,TABLE+0x2807L*8L,0);
        qword(seed,0xb00000L,0xb10000L);dword(seed,0xb10010L,0xffffffff);dword(seed,GUARD,0);
        for(long a=ROOT;a<ROOT+32;a++) seed.put(a,0x7b);
        for(long a=0x6fff20L;a<0x6fff80L;a++) seed.put(a,0xa5);
        dword(seed,CONST,0xf4338211);word(seed,CONST+4L,0xe655);seed.put(CONST+6L,0xf7);
        qword(seed,I+0x43da500L,ENTER);qword(seed,I+0x43da4f0L,RELEASE);
        dword(seed,INDEX,3);dword(seed,EPOCH,0x41);qword(seed,0xa00018L,0xa10000L);dword(seed,0xa10010L,0x11223344);
    }
    private static NonvolatileBits workingNv(long rbx) {
        return new NonvolatileBits(rbx,0xb111L,0x200000L,0xb333L,0xb444L,0xb555L,0xb666L,0xb777L,
                new Bits128(0xb100L,0xb101L));
    }
    private static VolatileBits postC() {return v(0xc000L,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);}
    private static VolatileBits postD() {return v(0xd000L,0xd111L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);}
    private static VolatileBits postE() {return v(1L,0xe111L,0xe222L,0xe333L,0xe444L,0xe555L,0xe666L,0xf000L);}
    private static VolatileBits postF() {return v(0xf000L,0xf111L,0xf222L,0xf333L,0xf444L,0xf555L,0xf666L,0x10000L);}
    private static VolatileBits postG() {return v(0x10000L,0x10111L,0x10222L,0x10333L,0x10444L,0x10555L,0x10666L,0x11000L);}
    private static VolatileBits postH() {return v(0x11000L,0x11111L,0x11222L,0x11333L,0x11444L,0x11555L,0x11666L,0x12000L);}
    private static VolatileBits v(long rax,long rcx,long rdx,long r8,long r9,long r10,long r11,long x) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,new Bits128(x,x+1),new Bits128(x+2,x+3),
                new Bits128(x+4,x+5),new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
    private static void word(Map<Long,Integer> image,long address,int value) {
        image.put(address,value&255);image.put(address+1L,(value>>>8)&255);
    }
}
