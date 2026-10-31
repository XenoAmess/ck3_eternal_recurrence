package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Entry;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.PauseStep;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.Witness;

/** Independent literal292B witnesses. Both model rounds were rejected; owner data
 * comes from the original ASM and frozen inputs, without reading/running target182.
 * Callback vectors, shared-memory actors and seven constant bytes are owned input,
 * not assertions about actual CRT, loaded constants, floating environment or Game. */
public final class GovernmentTokenLookup182Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L,BODY=0x7fffe0L,SLOT=0x7fffd8L;
    private static final long RIP=0x123456789abcdef0L,CHANGED_RIP=0xfedcba9876543210L;
    private static final long LOCK=0x900000L,TABLE=0xa00000L,GS=0xb00000L,TLS=0xb10000L;
    private static final long POINTER=0x145cbede8L,GUARD=0x145dc1124L,ROOT=0x145dc1128L;
    private static final long CONST=0x14472c488L,KEY2=0x1234567800000002L;

    @Override public List<Witness> witnesses() { return List.of(hit(),pauseHot(),fullInit()); }

    private static Witness hit() {
        Map<Long,Integer> seed=seed(0x80000000,0xa10000L,0x7fffffff,0xffffffff);
        List<Event> events=List.of(
                new AtomicStep(LOCK,2,0x80000000,0x80000002),
                new AtomicStep(LOCK,-2,0x80000002,0x80000000));
        VolatileBits end=v(0xa10000L,TABLE,0x80000000L,0x80000002L,
                0xa10000L,0xa555L,0xa666L,0xb000L);
        return witness("inclusive-index-hit-highbit-atomic",KEY2,seed,events,seed,end,RIP);
    }

    private static Witness pauseHot() {
        long key=0x12345678ffffffffL;
        Map<Long,Integer> seed=seed(1,0xa10000L,0x7fffffff,0xffffffff);
        Map<Long,Integer> pauseMutation=new LinkedHashMap<>();dword(pauseMutation,LOCK,0);
        List<Event> events=List.of(
                new AtomicStep(LOCK,2,1,3),
                new AtomicStep(LOCK,-2,3,1),
                new LoopStep(0x3f4f910L,LOCK),
                new PauseStep(0x3f4f917L,bytes(pauseMutation)),
                new LoopStep(0x3f4f910L,LOCK),
                new AtomicStep(LOCK,2,0,2),
                new AtomicStep(LOCK,-2,2,0),
                new GsStep(GS));
        Map<Long,Integer> endMemory=new LinkedHashMap<>(seed);dword(endMemory,LOCK,0);
        VolatileBits end=v(ROOT,TLS,0x10L,2L,-1L,0xa555L,0xa666L,0xb000L);
        return witness("odd-lock-pause-negative-key-hot-fallback",key,seed,events,endMemory,end,RIP);
    }

    private static Witness fullInit() {
        Map<Long,Integer> seed=seed(0,0L,0xffffffff,5);
        Map<Long,Integer> current=new LinkedHashMap<>(seed);
        List<Event> events=new ArrayList<>();
        events.add(new AtomicStep(LOCK,2,0,2));
        events.add(new AtomicStep(LOCK,-2,2,0));
        events.add(new GsStep(GS));

        // Both atomics leave the seeded lock at0 before the first actual CALL.
        qword(current,SLOT,0x143f4f987L);
        Map<Long,Integer> guardMutation=new LinkedHashMap<>();dword(guardMutation,GUARD,0xffffffff);
        VolatileBits firstPre=v(0xffffffffL,GUARD,0x10L,2L,0L,0xa555L,0xa666L,0xb000L);
        VolatileBits firstPost=v(0xc000L,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        events.add(step(0x3f4f982L,0x4223a84L,firstPre,current,guardMutation,firstPost));
        current.putAll(guardMutation);

        // Init owns ROOT[0..7], ROOT+10QWORD and ROOT+18QWORD; +8 padding stays7B.
        qword(current,ROOT,0L);qword(current,ROOT+0x18L,15L);qword(current,ROOT+0x10L,7L);
        dword(current,ROOT,0xf4338211);word(current,ROOT+4L,0xe655);
        current.put(ROOT+6L,0xf7);current.put(ROOT+7L,0);
        qword(current,SLOT,0x143f4f9ebL);
        VolatileBits secondPre=v(0xf7L,0x1443d7570L,0xc222L,0xc333L,
                0xc444L,0xc555L,0xc666L,0xd000L);
        VolatileBits secondPost=v(0xd000L,0xd111L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);
        events.add(step(0x3f4f9e6L,0x4223f24L,secondPre,current,Map.of(),secondPost));

        qword(current,SLOT,0x143f4f9f8L);
        VolatileBits thirdPre=v(0xd000L,GUARD,0xd222L,0xd333L,
                0xd444L,0xd555L,0xd666L,0xe000L);
        VolatileBits thirdPost=v(0xe000L,0xe111L,0xe222L,0xe333L,0xe444L,0xe555L,0xe666L,0xf000L);
        Map<Long,Integer> retMutation=new LinkedHashMap<>();qword(retMutation,S,CHANGED_RIP);
        events.add(step(0x3f4f9f3L,0x4223a24L,thirdPre,current,retMutation,thirdPost));
        current.putAll(retMutation);
        VolatileBits end=v(ROOT,0xe111L,0xe222L,0xe333L,0xe444L,0xe555L,0xe666L,0xf000L);
        return witness("null-entry-full-threecall-init-fresh-ret",KEY2,seed,events,current,end,CHANGED_RIP);
    }

    private static Witness witness(String name,long key,Map<Long,Integer> seed,List<Event> events,
            Map<Long,Integer> end,VolatileBits finalV,long returnRip) {
        return new Witness(name,new Entry(I,S,entryV(key),nv()),bytes(seed),events,end,
                new NormalReturn(finalV,returnRip,0x800010L,nv()));
    }
    private static CallStep step(long site,long target,VolatileBits pre,Map<Long,Integer> before,
            Map<Long,Integer> mutation,VolatileBits post) {
        return new CallStep(new OpaqueCall(site,target,BODY,pre,nv()),before,bytes(mutation),post);
    }
    private static Map<Long,Integer> seed(int lock,long tableIndex2,int tls,int guard) {
        Map<Long,Integer> out=new LinkedHashMap<>();
        for(long a=0x7fff80L;a<0x800040L;a++) out.put(a,0xa5);
        qword(out,S,RIP);qword(out,POINTER,LOCK);dword(out,LOCK,lock);
        qword(out,LOCK+0x48L,TABLE);dword(out,LOCK+0x54L,2);qword(out,TABLE+16L,tableIndex2);
        qword(out,GS,TLS);dword(out,TLS+0x10L,tls);dword(out,GUARD,guard);
        for(long a=ROOT;a<ROOT+0x20L;a++) out.put(a,0x7b);
        dword(out,CONST,0xf4338211);word(out,CONST+4L,0xe655);out.put(CONST+6L,0xf7);
        return out;
    }
    private static VolatileBits entryV(long key) {
        return v(0xa000L,key,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
    }
    private static NonvolatileBits nv() {
        return new NonvolatileBits(0xb000L,0xb111L,0xb222L,0xb333L,0xb444L,0xb555L,0xb666L,0xb777L,
                new Bits128(0xb100L,0xb101L));
    }
    private static VolatileBits v(long rax,long rcx,long rdx,long r8,long r9,long r10,long r11,long x) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,
                new Bits128(x,x+1),new Bits128(x+2,x+3),new Bits128(x+4,x+5),
                new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static List<SeedByte> bytes(Map<Long,Integer> image) {
        return image.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList();
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
