package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.Entry;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Three frozen independent original-code witnesses. Owner takeover after two rejected
 * model rounds. Hash literals come from separate fixed-four-byte scalar arithmetic;
 * the helper implementation was not read or run. Opaque postV/mutation is owned input.
 */
public final class GovernmentLookupHelper176Fixtures implements Book {
    private static final long IMAGE=0x140000000L,S=0x800008L,BODY=0x7fffe0L;
    private static final long RIP=0x123456789abcdef0L,ROOT=0x900000L,BUCKETS=0xa00000L;
    private static final long SENTINEL=0xb00000L,NODE1=0xb10000L,NODE2=0xb20000L,END=0xb30000L;
    private static final long PRIME=0x100000001b3L;

    @Override public List<Witness> witnesses() {
        return List.of(
                make("sentinel-miss",0x8765432111223344L,0,
                        0x3c1b247411d7b2b5L,0xa00010L,0L,List.of()),
                make("first-key-hit",0x12345678a1b2c3d4L,1,
                        0x8381a92307066c15L,END,0xb10018L,List.of()),
                make("chain-hit-fresh-home-high-bytes",0x12345678a1b2c3d4L,2,
                        0xcceee924e3f552acL,END,0xb20018L,
                        List.of(new LoopStep(0x3f5f9f0L,NODE1,END))));
    }

    private static Witness make(String name,long keyRcx,int inputKind,long literalHash,
            long finalRcx,long finalRax,List<LoopStep> loops) {
        VolatileBits entryV=v(0xa000L,keyRcx,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
        Map<Long,Integer> seed=seed(inputKind,(int)keyRcx);
        Map<Long,Integer> before=new LinkedHashMap<>(seed);
        dword(before,0x800010L,(int)keyRcx);
        qword(before,0x800000L,0xb000L);
        qword(before,0x7fffd8L,0x143f5f980L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();
        if(inputKind==2) dword(mutation,0x800010L,0x44332211);
        CallStep getter=new CallStep(new OpaqueCall(0x3f5f97bL,0x3f5c090L,BODY,
                entryV,nv(Integer.toUnsignedLong((int)keyRcx))),before,bytes(mutation),post());
        Map<Long,Integer> end=new LinkedHashMap<>(before);
        end.putAll(mutation);
        VolatileBits finalV=v(finalRax,finalRcx,SENTINEL,literalHash,ROOT,PRIME,0xc666L,0xd000L);
        return new Witness(name,new Entry(IMAGE,S,entryV,nv(0xb000L)),bytes(seed),
                List.of(getter),List.of(),List.of(),loops,end,
                new NormalReturn(finalV,RIP,0x800010L,nv(0xb000L)));
    }

    private static Map<Long,Integer> seed(int kind,int keyDword) {
        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(long address=0x7fff80L;address<0x800040L;address++) seed.put(address,0xa5);
        qword(seed,S,RIP);
        qword(seed,ROOT+8L,SENTINEL);
        qword(seed,ROOT+0x18L,BUCKETS);
        qword(seed,ROOT+0x30L,3L);
        for(int bucket=0;bucket<4;bucket++) {
            qword(seed,BUCKETS+bucket*16L,END);
            qword(seed,BUCKETS+bucket*16L+8L,kind==0?SENTINEL:NODE1);
        }
        if(kind!=0) {
            dword(seed,NODE1+0x10L,kind==1?keyDword:0x01010101);
            qword(seed,NODE1+8L,NODE2);
            dword(seed,NODE2+0x10L,keyDword);
        }
        return seed;
    }

    private static NonvolatileBits nv(long rbx) {
        return new NonvolatileBits(rbx,0xb111L,0xb222L,0xb333L,0xb444L,0xb555L,0xb666L,0xb777L,
                new Bits128(0xb100L,0xb101L));
    }
    private static VolatileBits post() {
        return v(ROOT,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
    }
    private static VolatileBits v(long rax,long rcx,long rdx,long r8,long r9,long r10,long r11,long x) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,
                new Bits128(x,x+1),new Bits128(x+2,x+3),new Bits128(x+4,x+5),
                new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static List<SeedByte> bytes(Map<Long,Integer> image) {
        List<SeedByte> out=new ArrayList<>();
        for(Map.Entry<Long,Integer> value:image.entrySet()) out.add(new SeedByte(value.getKey(),value.getValue()));
        return List.copyOf(out);
    }
    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
}
