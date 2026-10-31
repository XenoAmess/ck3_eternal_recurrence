package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Entry;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Owner literal oracle after two rejected model derivations. The target implementation
 * was neither supplied to this task nor executed to produce these values. Opaque post
 * vectors and mutations are explicit fixture scripts, not recovered helper semantics.
 */
public final class GovernmentNormalizeFull174Fixtures implements Book {
    private static final long IMAGE=0x140000000L;
    private static final long ENTRY_RSP=0x700008L;
    private static final long BODY_RSP=0x6fffc0L;
    private static final long CALL_SLOT=0x6fffb8L;
    private static final long RIP=0x123456789abcdef0L;
    private static final long COUNTER=0x145c6a9dcL;

    @Override public List<Witness> witnesses() {
        return List.of(earlyPass(),lookupTlsBlock(),lookupHelperDiagAtomic());
    }

    private static Witness earlyPass() {
        VolatileBits entryV=v(0xa000L,0x100000L,0x200000L,0xffffffff00000002L,
                0xa444L,0xa555L,0xa666L,0xb000L);
        Map<Long,Integer> seed=seed(5,false,false);
        Map<Long,Integer> end=saved(seed);
        VolatileBits finalV=v(2L,0x100000L,0x200000L,0xffffffff00000002L,
                0xa444L,0xa555L,0xa666L,0xb000L);
        return witness("early-pass",entryV,seed,List.of(),List.of(),List.of(),end,finalV);
    }

    private static Witness lookupTlsBlock() {
        VolatileBits entryV=v(0xa000L,0x100000L,0x200000L,0xffffffff00000001L,
                0xa444L,0xa555L,0xa666L,0xb000L);
        Map<Long,Integer> seed=seed(5,true,false);
        Map<Long,Integer> before=saved(seed);
        qword(before,CALL_SLOT,0x1430a2d43L);
        VolatileBits pre=v(0x1430a2d0fL,0x2807L,0x200000L,0xffffffff00000001L,
                0xa444L,0xa555L,0xa666L,0xb000L);
        CallStep lookup=new CallStep(new OpaqueCall(0x30a2d3eL,0x3f4f8e0L,BODY_RSP,
                pre,nv(0x100018L,0x200000L,0xb333L)),before,List.of(),lookupPost());
        VolatileBits finalV=v(3L,0x500000L,0x600000L,0x158L,
                0xc444L,0xc555L,0xc666L,0xd000L);
        return witness("lookup-tls-block",entryV,seed,List.of(lookup),
                List.of(0x500000L),List.of(),before,finalV);
    }

    private static Witness lookupHelperDiagAtomic() {
        VolatileBits entryV=v(0xa000L,0x100000L,0x200000L,0x1234567800000002L,
                0xa444L,0xa555L,0xa666L,0xb000L);
        Map<Long,Integer> seed=seed(4,false,true);
        Map<Long,Integer> beforeLookup=saved(seed);
        qword(beforeLookup,CALL_SLOT,0x1430a2e29L);
        VolatileBits lookupPre=v(0x1430a2dfcL,0x27e2L,0x200000L,0x1234567800000002L,
                0xa444L,0xa555L,0xa666L,0xb000L);
        CallStep lookup=new CallStep(new OpaqueCall(0x30a2e24L,0x3f4f8e0L,BODY_RSP,
                lookupPre,nv(0x100018L,0x200000L,0xb333L)),beforeLookup,List.of(),lookupPost());

        Map<Long,Integer> beforeHelper=new LinkedHashMap<>(beforeLookup);
        qword(beforeHelper,CALL_SLOT,0x1430a2e5eL);
        VolatileBits helperPre=v(0x330000L,0x10000L,0x600000L,0x158L,
                0xc444L,0xc555L,0xc666L,0xd000L);
        CallStep helper=new CallStep(new OpaqueCall(0x30a2e59L,0x3f5f970L,BODY_RSP,
                helperPre,nv(0x100018L,0x200000L,0x330000L)),beforeHelper,List.of(),helperPost());

        Map<Long,Integer> beforeDiag=new LinkedHashMap<>(beforeHelper);
        qword(beforeDiag,0x6ffff8L,0x100018L);
        qword(beforeDiag,0x6ffff0L,0x200000L);
        qword(beforeDiag,0x6fffe8L,0x330000L);
        qword(beforeDiag,0x6fffe0L,0x1448b7bd0L);
        qword(beforeDiag,CALL_SLOT,0x1430a2e93L);
        VolatileBits diagPre=v(0x440000L,0x440000L,0x1448b7a48L,0x12cL,
                0xd444L,0xd555L,0xd666L,0xe000L);
        Map<Long,Integer> mutation=new LinkedHashMap<>();
        dword(mutation,COUNTER,0xfffffffe);
        CallStep diag=new CallStep(new OpaqueCall(0x30a2e8eL,0x2850890L,BODY_RSP,
                diagPre,nv(0x100018L,0x200000L,0x330000L)),beforeDiag,bytes(mutation),diagPost());
        Map<Long,Integer> end=new LinkedHashMap<>(beforeDiag);
        dword(end,COUNTER,0xffffffff);
        VolatileBits finalV=v(7L,0xe111L,0xe222L,0xe333L,
                0xe444L,0xe555L,0xe666L,0xf000L);
        return witness("lookup-helper-diag-atomic",entryV,seed,List.of(lookup,helper,diag),
                List.of(0x500000L),List.of(new AtomicStep(COUNTER,1,0xfffffffe,0xffffffff)),end,finalV);
    }

    private static Witness witness(String name,VolatileBits entryV,Map<Long,Integer> seed,
            List<CallStep> calls,List<Long> gs,List<AtomicStep> atomics,
            Map<Long,Integer> end,VolatileBits finalV) {
        return new Witness(name,new Entry(IMAGE,ENTRY_RSP,entryV,initialNv()),bytes(seed),
                calls,gs,atomics,end,new NormalReturn(finalV,RIP,0x700010L,initialNv()));
    }

    private static Map<Long,Integer> seed(int tag,boolean tlsBlocked,boolean counter) {
        Map<Long,Integer> bytes=new LinkedHashMap<>();
        for(long address=0x6fff80L;address<0x700040L;address++) bytes.put(address,0xa5);
        qword(bytes,ENTRY_RSP,RIP);
        bytes.put(0x1004d6L,tag);
        if(tlsBlocked||counter) {
            qword(bytes,0x500000L,0x600000L);
            bytes.put(0x600158L,tlsBlocked?1:0);
        }
        if(counter) dword(bytes,COUNTER,0xffffffff);
        return bytes;
    }

    private static Map<Long,Integer> saved(Map<Long,Integer> seed) {
        Map<Long,Integer> out=new LinkedHashMap<>(seed);
        qword(out,0x700010L,0xb000L);
        qword(out,0x700018L,0xb222L);
        qword(out,0x700000L,0xb333L);
        return out;
    }

    private static NonvolatileBits initialNv() { return nv(0xb000L,0xb222L,0xb333L); }
    private static NonvolatileBits nv(long rbx,long rsi,long rdi) {
        return new NonvolatileBits(rbx,0xb111L,rsi,rdi,0xb444L,0xb555L,0xb666L,0xb777L,
                new Bits128(0xb100L,0xb101L));
    }
    private static VolatileBits lookupPost() {
        return v(0x330000L,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);
    }
    private static VolatileBits helperPost() {
        return v(0x440000L,0xd111L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);
    }
    private static VolatileBits diagPost() {
        return v(0xe000L,0xe111L,0xe222L,0xe333L,0xe444L,0xe555L,0xe666L,0xf000L);
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
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(i*8))&0xff);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(i*8))&0xff);
    }
}
