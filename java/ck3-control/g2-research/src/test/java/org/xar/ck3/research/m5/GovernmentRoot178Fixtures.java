package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Entry;
import org.xar.ck3.research.m5.GovernmentRoot178Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentRoot178WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentRoot178WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentRoot178WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentRoot178WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Independent literal240B root witnesses after two rejected model rounds. Target178
 * Java was not read or executed. Callback vectors/mutations and constantDWORD are
 * artificial owned inputs; no actual CRT, allocator, floating environment or Game claim.
 */
public final class GovernmentRoot178Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L,BODY=0x7fffe0L,SLOT=0x7fffd8L;
    private static final long RIP=0x123456789abcdef0L,CHANGED_RIP=0xfedcba9876543210L;
    private static final long GUARD=0x145dc11c0L,ROOT=0x145dc11d0L,CONST=0x1449f6464L;
    private static final long HEAP=0x700000L,GS=0x500000L;
    private static final int RAW_FLOAT=0x7fa12345;

    @Override public List<Witness> witnesses() { return List.of(hot(),freshFast(),fullInit()); }

    private static Witness hot() {
        Map<Long,Integer> seed=seed(0x7fffffff,0xffffffff);
        VolatileBits end=v(ROOT,0x600000L,0x10L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
        return witness("signed-hot-no-call",seed,List.of(),seed,end,RIP);
    }

    private static Witness freshFast() {
        Map<Long,Integer> seed=seed(0xffffffff,5);
        Map<Long,Integer> before=new LinkedHashMap<>(seed);
        qword(before,SLOT,0x143f5c0c8L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();dword(mutation,GUARD,0);
        CallStep call=step(0x3f5c0c3L,0x4223a84L,firstPre(),before,mutation,post1());
        Map<Long,Integer> end=new LinkedHashMap<>(before);end.putAll(mutation);
        VolatileBits finalV=v(ROOT,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
        return witness("fresh-guard-nonminusone-fast",seed,List.of(call),end,finalV,RIP);
    }

    private static Witness fullInit() {
        Map<Long,Integer> seed=seed(0xffffffff,5);
        Map<Long,Integer> current=new LinkedHashMap<>(seed);
        List<CallStep> calls=new ArrayList<>();
        Map<Long,Integer> guardMutation=new LinkedHashMap<>();dword(guardMutation,GUARD,0xffffffff);
        qword(current,SLOT,0x143f5c0c8L);
        calls.add(step(0x3f5c0c3L,0x4223a84L,firstPre(),current,guardMutation,post1()));
        current.putAll(guardMutation);

        // Source zeroes only lowDWORD at ROOT; its nextDWORD retains seed7B padding.
        dword(current,ROOT,0);qword(current,ROOT+8L,0);qword(current,ROOT+0x10L,0);
        qword(current,SLOT,0x143f5c0fcL);
        VolatileBits allocPre=withX0(v(0xc000L,0x40L,0xc222L,0xc333L,
                0xc444L,0xc555L,0xc666L,0xd000L),new Bits128(0,0));
        VolatileBits allocPost=v(HEAP,0xd111L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);
        calls.add(step(0x3f5c0f7L,0x4223b94L,allocPre,current,Map.of(),allocPost));

        qword(current,HEAP,HEAP);qword(current,HEAP+8L,HEAP);qword(current,ROOT+8L,HEAP);
        qword(current,ROOT+0x18L,0);qword(current,ROOT+0x20L,0);qword(current,ROOT+0x28L,0);
        qword(current,ROOT+0x30L,7L);qword(current,ROOT+0x38L,8L);dword(current,ROOT,RAW_FLOAT);
        qword(current,SLOT,0x143f5c15aL);
        VolatileBits thirdPre=withX0(v(HEAP,ROOT+0x18L,0x10L,HEAP,
                0xd444L,0xd555L,0xd666L,0xe000L),new Bits128(0x7fa12345L,0L));
        VolatileBits thirdPost=v(0xe000L,0xe111L,0xe222L,0xe333L,0xe444L,0xe555L,0xe666L,0xf000L);
        calls.add(step(0x3f5c155L,0x3714560L,thirdPre,current,Map.of(),thirdPost));

        qword(current,SLOT,0x143f5c167L);
        VolatileBits fourthPre=v(0xe000L,0x1443d7820L,0xe222L,0xe333L,
                0xe444L,0xe555L,0xe666L,0xf000L);
        VolatileBits fourthPost=v(0xf000L,0xf111L,0xf222L,0xf333L,0xf444L,0xf555L,0xf666L,0x10000L);
        calls.add(step(0x3f5c162L,0x4223f24L,fourthPre,current,Map.of(),fourthPost));

        qword(current,SLOT,0x143f5c174L);
        VolatileBits fifthPre=v(0xf000L,GUARD,0xf222L,0xf333L,0xf444L,0xf555L,0xf666L,0x10000L);
        VolatileBits fifthPost=v(0x10000L,0x10111L,0x10222L,0x10333L,0x10444L,0x10555L,0x10666L,0x11000L);
        Map<Long,Integer> retMutation=new LinkedHashMap<>();qword(retMutation,S,CHANGED_RIP);
        calls.add(step(0x3f5c16fL,0x4223a24L,fifthPre,current,retMutation,fifthPost));
        current.putAll(retMutation);
        VolatileBits end=v(ROOT,0x10111L,0x10222L,0x10333L,0x10444L,0x10555L,0x10666L,0x11000L);
        return witness("full-five-call-init-fresh-ret",seed,calls,current,end,CHANGED_RIP);
    }

    private static Witness witness(String name,Map<Long,Integer> seed,List<CallStep> calls,
            Map<Long,Integer> end,VolatileBits finalV,long returnRip) {
        return new Witness(name,new Entry(I,S,entryV(),nv()),bytes(seed),calls,List.of(GS),List.of(),
                end,new NormalReturn(finalV,returnRip,0x800010L,nv()));
    }
    private static CallStep step(long site,long target,VolatileBits pre,Map<Long,Integer> before,
            Map<Long,Integer> mutation,VolatileBits post) {
        return new CallStep(new OpaqueCall(site,target,BODY,pre,nv()),before,bytes(mutation),post);
    }
    private static Map<Long,Integer> seed(int tls,int guard) {
        Map<Long,Integer> out=new LinkedHashMap<>();
        for(long a=0x7fff80L;a<0x800040L;a++) out.put(a,0xa5);
        qword(out,S,RIP);qword(out,GS,0x600000L);dword(out,0x600010L,tls);dword(out,GUARD,guard);
        for(long a=ROOT;a<ROOT+0x40L;a++) out.put(a,0x7b);
        for(long a=HEAP;a<HEAP+0x40L;a++) out.put(a,0x6c);
        dword(out,CONST,RAW_FLOAT);return out;
    }
    private static VolatileBits entryV() {
        return v(0xa000L,0xa111L,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
    }
    private static VolatileBits firstPre() {
        return v(0xffffffffL,GUARD,0x10L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
    }
    private static VolatileBits post1() {
        return v(0xc000L,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
    }
    private static NonvolatileBits nv() {
        return new NonvolatileBits(0xb000L,0xb111L,0xb222L,0xb333L,0xb444L,0xb555L,0xb666L,0xb777L,
                new Bits128(0xb100L,0xb101L));
    }
    private static VolatileBits withX0(VolatileBits v,Bits128 x0) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                x0,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
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
}
