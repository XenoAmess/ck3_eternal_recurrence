package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsPort;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.Witness;

/**
 * ONE new whole->174->176->178 literal. Owner takeover after two rejected model
 * rounds. No target Java algorithm was read or run. Existing175/173 Books supply
 * independent front-phase input/oracles and explicit opaque vectors only.
 */
public final class GovernmentWholeRoot181Fixtures implements GovernmentWholeConcrete173WitnessApi.Book {
    private static final long I=0x140000000L,G=0x600000L,S=0xbfecd0L,B=0xbfedd0L;
    private static final long COUNTER=0x145c6a9dcL,NORMAL_SP=S-0x50L;

    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeNormalized175Fixtures().witnesses().get(0);
        var old=base.whole();
        var oldPorts=new GovernmentWholeConcrete173Fixtures().witnesses().get(0).whole().ordinaryCalls();
        OrdinaryStep oldFirst=oldPorts.get(0),oldSecond=oldPorts.get(1);
        Map<Long,Integer> seed=map(old.memorySeed());inputChanges(seed);

        // The old final oracle differs from the first normalization stage only at
        // the futureD2 regions, input/output fields, and explicitly replaced CALL slot.
        // Source838..1012 takes signed guard/zero-count paths with no later memory writes.
        Map<Long,Integer> stage=new LinkedHashMap<>(seed);
        stage.putAll(old.expectedFinalBytes());inputChanges(stage);
        copy(stage,seed,B+0x60L,16);copy(stage,seed,B+0x1b0L,16);
        normalEntry(stage,I+0x30a3e6cL);
        qword(stage,S-0x58L,I+0x30a2e29L);

        List<OrdinaryStep> calls=new ArrayList<>();
        VolatileBits lookup1Pre=lookupPre(oldFirst.expected().volatileBits(),0x2dL);
        NonvolatileBits lookup1Nv=lookupNv(oldFirst);
        VolatileBits lookup1Post=withRax(oldFirst.normalPost(),0x330000L);
        calls.add(call(0x30a2e24L,0x3f4f8e0L,lookup1Pre,lookup1Nv,stage,lookup1Post));

        diagWrites(stage,oldFirst.expected().volatileBits().rdxBits());
        VolatileBits diag1Pre=diagPre(lookup1Post);
        calls.add(call(0x30a2e8eL,0x2850890L,diag1Pre,withRdi(lookup1Nv,0x330000L),
                stage,oldFirst.normalPost()));

        // Actual first XADD wraps FFFFFFFF to0; the normalizer then MOV EAX,7.
        dword(stage,COUNTER,0);dword(stage,G+0x4ccL,7);
        copy(stage,old.expectedFinalBytes(),B+0x60L,16);
        copy(stage,old.expectedFinalBytes(),B+0x1b0L,16);
        normalEntry(stage,I+0x30a3eaaL);
        qword(stage,S-0x58L,I+0x30a2e29L);

        VolatileBits lookup2Pre=lookupPre(oldSecond.expected().volatileBits(),0x2eL);
        NonvolatileBits lookup2Nv=lookupNv(oldSecond);
        VolatileBits lookup2Post=withRax(oldSecond.normalPost(),0x330000L);
        calls.add(call(0x30a2e24L,0x3f4f8e0L,lookup2Pre,lookup2Nv,stage,lookup2Post));
        diagWrites(stage,oldSecond.expected().volatileBits().rdxBits());
        calls.add(call(0x30a2e8eL,0x2850890L,diagPre(lookup2Post),withRdi(lookup2Nv,0x330000L),
                stage,oldSecond.normalPost()));
        dword(stage,COUNTER,1);dword(stage,G+0x4c8L,7);

        var oldResult=old.expectedResult();var oldMiddle=oldResult.middleResult();
        var oldJoined=oldMiddle.joinedResult();var oldJoin=oldJoined.actualJoin();
        VolatileBits finalJoinedV=withRax(oldSecond.normalPost(),7L);
        var join=new GovernmentPreprefix159Api.Join(oldJoin.nextRva(),oldJoin.imageBaseBits(),
                oldJoin.frameRspBits(),finalJoinedV,oldJoin.nonvolatileBits());
        var joined=new GovernmentJoined159Api.Result(join,oldJoined.suffixResult());
        var middle=new GovernmentMiddle166Api.Result(oldMiddle.compactionJoin(),oldMiddle.preludeEntry(),joined);
        var result=new GovernmentWhole4798Api.Result(oldResult.initialJoin(),oldResult.afterInitialMxcsr(),
                oldResult.lookupJoin(),oldResult.earlierJoin(),oldResult.rowsJoin(),middle,oldResult.finalMxcsr());
        var afterFinal=new GovernmentWhole4798WitnessApi.FinalMxcsrStep(middle,old.afterFinal().observation());
        var whole=new GovernmentWhole4798WitnessApi.Witness("whole181-two-real-normalizer-root-diags",
                old.entry(),memory(seed),old.gs58Bits(),old.initialCalls(),calls,old.lookupCalls(),old.cpuCalls(),
                old.budgets(),old.afterInitial(),afterFinal,old.post153(),stage,result,old.failure());
        List<AtomicStep> atomics=new ArrayList<>(base.atomicSteps());
        atomics.add(new AtomicStep(32,COUNTER,1,0xffffffff,0));
        atomics.add(new AtomicStep(32,COUNTER,1,0,1));
        List<GsStep> gs=new ArrayList<>(base.gsSteps());
        gs.add(new GsStep(GsPort.ORDINARY,0x700000L));gs.add(new GsStep(GsPort.ORDINARY,0xd00000L));
        gs.add(new GsStep(GsPort.ORDINARY,0x700000L));gs.add(new GsStep(GsPort.ORDINARY,0xd00000L));
        return List.of(new Witness(whole,base.m0HashMxcsrAt4FE(),base.m1HashMxcsrAt85E(),
                base.deepSteps(),atomics,gs));
    }

    private static void inputChanges(Map<Long,Integer> image) {
        image.put(G+0x4d6L,4);dword(image,G+0x4ccL,0x2d);dword(image,G+0x4c8L,0x2e);
        dword(image,COUNTER,0xffffffff);image.put(0x710158L,0);
        dword(image,0x145dc11c0L,0xffffffff);
        qword(image,0x145dc11d8L,0xb00000L);qword(image,0x145dc11e8L,0xa00000L);
        qword(image,0x145dc1200L,3L);qword(image,0xd00000L,0xd10000L);dword(image,0xd10010L,0x7fffffff);
        for(int n=0;n<4;n++) {
            qword(image,0xa00000L+n*16L,0xb30000L);qword(image,0xa00008L+n*16L,0x43ffe8L);
        }
        dword(image,0x43fff8L,0x10000);
    }
    private static void normalEntry(Map<Long,Integer> image,long returnRip) {
        qword(image,S-8L,returnRip);qword(image,S,0L);qword(image,S+8L,G+0x18L);qword(image,S-0x10L,G);
    }
    private static void diagWrites(Map<Long,Integer> image,long descriptor) {
        // Only this owned CALL introduces bytes below the old initial S-80 seed.
        qword(image,S-0x88L,I+0x3f5f980L);
        qword(image,S-0x60L,G+0x18L);dword(image,S-0x50L,0x10000);
        qword(image,S-0x18L,G+0x18L);qword(image,S-0x20L,descriptor);
        qword(image,S-0x28L,0x330000L);qword(image,S-0x30L,I+0x48b7bd0L);
        qword(image,S-0x58L,I+0x30a2e93L);
    }
    private static VolatileBits lookupPre(VolatileBits outer,long key) {
        return new VolatileBits(outer.raxBits(),0x165L,outer.rdxBits(),key,
                outer.r9Bits(),outer.r10Bits(),outer.r11Bits(),outer.xmm0(),outer.xmm1(),outer.xmm2(),
                outer.xmm3(),outer.xmm4(),outer.xmm5());
    }
    private static NonvolatileBits lookupNv(OrdinaryStep outer) {
        NonvolatileBits nv=outer.expected().nonvolatileBits();
        return new NonvolatileBits(G+0x18L,nv.rbpBits(),outer.expected().volatileBits().rdxBits(),G,
                nv.r12Bits(),nv.r13Bits(),nv.r14Bits(),nv.r15Bits(),nv.xmm6());
    }
    private static NonvolatileBits withRdi(NonvolatileBits nv,long rdi) {
        return new NonvolatileBits(nv.rbxBits(),nv.rbpBits(),nv.rsiBits(),rdi,
                nv.r12Bits(),nv.r13Bits(),nv.r14Bits(),nv.r15Bits(),nv.xmm6());
    }
    private static VolatileBits diagPre(VolatileBits lookupPost) {
        return new VolatileBits(0x440000L,0x440000L,I+0x48b7a48L,0x12cL,
                I+0x5dc11d0L,0x100000001b3L,lookupPost.r11Bits(),lookupPost.xmm0(),lookupPost.xmm1(),
                lookupPost.xmm2(),lookupPost.xmm3(),lookupPost.xmm4(),lookupPost.xmm5());
    }
    private static VolatileBits withRax(VolatileBits v,long rax) {
        return new VolatileBits(rax,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static OrdinaryStep call(long site,long target,VolatileBits pre,NonvolatileBits nv,
            Map<Long,Integer> before,VolatileBits post) {
        return new OrdinaryStep(new OpaqueCall(site,target,NORMAL_SP,pre,nv),before,List.of(),post,false);
    }
    private static Map<Long,Integer> map(MemorySeed seed) {
        Map<Long,Integer> out=new LinkedHashMap<>();
        for(SeedByte value:seed.bytes()) out.put(value.addressBits(),value.byteBits());return out;
    }
    private static MemorySeed memory(Map<Long,Integer> image) {
        return new MemorySeed(image.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static void copy(Map<Long,Integer> out,Map<Long,Integer> source,long start,int count) {
        for(int i=0;i<count;i++) {
            Integer value=source.get(start+i);
            if(value==null) throw new IllegalArgumentException("missing independent literal byte "+Long.toHexString(start+i));
            out.put(start+i,value);
        }
    }
    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
}
