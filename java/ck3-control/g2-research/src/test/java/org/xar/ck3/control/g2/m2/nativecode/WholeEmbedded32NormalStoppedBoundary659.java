package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Two fresh generic whole394 scenes from the independently frozen659 oracle.
 * Growth reaches five source sites; shrink reaches BA and27B twice, then stops.
 * All child outcomes are explicit typed foreign offers, including37272F0.
 * No known637 binding, selfthrow case, target replay or producer loop is copied.
 * Final Test source is owner-written after the selected R1 source was read.
 */
public final class WholeEmbedded32NormalStoppedBoundary659 {
    private WholeEmbedded32NormalStoppedBoundary659() { }

    private static final class Ram extends Embedded32ByteFixture659
            implements Embedded32Fp659.Memory {
        private Ram() { }
    }

    private record Region(long base, String hex) { }
    private record Spec(Call call, Entry child, boolean df, QueueFp604Api.Mxcsr fp,
            int length, long rip) { }
    private record BudgetArgs(long pc, long cursor) { }
    private record ObservationExpected(String name, String mode, Object value) { }
    private record RamExpected(int ordinal, Map<Long,Byte> bytes) { }
    private record Effect(String primitive, long address, long value) { }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static Map<Long,Byte> literalMap(Region... regions) {
        Map<Long,Byte> result=new HashMap<>();
        for (Region region:regions) {
            byte[] raw=HexFormat.of().parseHex(region.hex());
            for (int i=0;i<raw.length;i++)
                check(result.put(region.base()+i,raw[i])==null, "overlapping literal ownership");
        }
        return Map.copyOf(result);
    }

    private static final class Expected {
        final Map<String,QueueFp604Api.Mxcsr> fp=new LinkedHashMap<>();
        final List<Spec> frames=new ArrayList<>();
        final List<QueueFp604Api.Outcome> offers=new ArrayList<>();
        final List<List<Effect>> effects=new ArrayList<>();
        final Map<Integer,RamExpected> ram=new LinkedHashMap<>();
        final List<Object> trace=new ArrayList<>();
        final RuntimeException unconfigured=new UnsupportedOperationException("Unexpected659 opaque call; use one preconstructed same exception per case. No fabricated normal/FP fallback.");
        Entry root;
        boolean rootDf;
        QueueFp604Api.Mxcsr rootFp;
        Map<Long,Byte> initial;
        int ownedBytes;
        int expectedMemory;
        int expectedBudget;
        NormalReturn finalReturn;
        boolean finalDf;
        QueueFp604Api.Mxcsr finalFp;
        QueueFp604Api.Snapshot sameSnapshot;
        Entry sameStopEntry;
        QueueFp604Api.Stopped sameStop;
    }

    private static final class Harness {
        final Ram host;
        final Expected e;
        final List<Embedded32Fp659.CallFrame> captured=new ArrayList<>();
        final List<Integer> checkedRam=new ArrayList<>();
        int calls;
        int budgets;
        Harness(Ram host, Expected e) { this.host=host; this.e=e; }

        void ram() {
            int ordinal=host.events.size();
            RamExpected r=e.ram.get(ordinal);
            check(r!=null && !checkedRam.contains(ordinal), "one observable RAM checkpoint "+ordinal);
            check(host.bytes.keySet().equals(r.bytes().keySet()), "whole RAM keyset "+ordinal);
            check(host.bytes.equals(r.bytes()), "whole RAM byte values "+ordinal);
            checkedRam.add(ordinal);
        }

        void frame(Embedded32Fp659.CallFrame actual, Spec expected) {
            Embedded32Copy581Api.CallFrame original=actual.original();
            Call call=original.call();
            Entry child=original.childEntry();
            Call literal=expected.call();
            check(call.callSiteRva()==literal.callSiteRva() && call.kind()==literal.kind()
                    && call.targetBits()==literal.targetBits(), "source site/kind/target");
            check(call.rspBits()==literal.rspBits(), "CALL prepush SP");
            check(call.volatileBits().equals(literal.volatileBits()), "CALL all V/XMM0..5");
            check(call.nonvolatileBits().equals(literal.nonvolatileBits()), "CALL all N/XMM6");
            Entry literalChild=expected.child();
            check(child.imageBaseBits()==literalChild.imageBaseBits()
                    && child.rspBits()==literalChild.rspBits(), "child image and postpush SP");
            check(child.volatileBits().equals(literalChild.volatileBits()), "child all V");
            check(child.nonvolatileBits().equals(literalChild.nonvolatileBits()), "child all N");
            check(original.directionFlagSet()==expected.df(), "current preDF");
            check(actual.preMxcsr().equals(expected.fp()), "full partialFP value/mask");
            check(actual.preMxcsr()==expected.fp(), "SAME current preFP object");
            check(original.instructionLength()==expected.length()
                    && original.returnRipBits()==expected.rip(), "actual length and continuation");
            check(child.rspBits()==call.rspBits()-8L, "source single push");
            check(child.volatileBits().equals(call.volatileBits())
                    && child.nonvolatileBits().equals(call.nonvolatileBits()), "source child whole banks");
            check(original.returnRipBits()==child.imageBaseBits()+call.callSiteRva()
                    +original.instructionLength(), "relocation-aware actual continuation");
        }

        QueueFp604Api.Outcome invoke(Embedded32Fp659.CallFrame actual) {
            if (calls>=e.frames.size()) throw e.unconfigured;
            if (actual.original().call().callSiteRva()!=e.frames.get(calls).call().callSiteRva())
                throw e.unconfigured;
            int index=calls++;
            frame(actual,e.frames.get(index));
            captured.add(actual);
            ram();
            host.observe("CALL_ENTER",actual);
            for (Effect effect:e.effects.get(index)) {
                switch(effect.primitive()) {
                    case "writeQword" -> host.writeQword(effect.address(),effect.value());
                    case "writeDword" -> host.writeDword(effect.address(),(int)effect.value());
                    default -> throw e.unconfigured;
                }
            }
            QueueFp604Api.Outcome offered=e.offers.get(index);
            host.observe("CALL_OFFER",offered);
            ram();
            return offered;
        }

        void budget(long pc,long cursor) {
            budgets++;
            host.observe("BUDGET2",new BudgetArgs(pc,cursor));
            ram();
        }

        void finish() {
            check(calls==e.frames.size() && budgets==e.expectedBudget, "exact actual CALL/budget count");
            check(checkedRam.equals(new ArrayList<>(e.ram.keySet())), "all existing observable full RAM maps");
            check(host.bytes.size()==e.ownedBytes, "complete owned byte count");
            check(host.events.size()==e.trace.size()
                    && host.memoryEvents.size()==e.expectedMemory, "exact full mixed and Memory counts");
            int memory=0;
            for (int i=0;i<e.trace.size();i++) {
                Object expected=e.trace.get(i),actual=host.events.get(i);
                if (expected instanceof Embedded32ByteFixture659.Event event) {
                    check(actual instanceof Embedded32ByteFixture659.Event && event.equals(actual),
                            "literal Memory row "+(i+1));
                    check(actual==host.memoryEvents.get(memory++), "same recorded Memory event");
                } else {
                    ObservationExpected literal=(ObservationExpected)expected;
                    check(actual instanceof Embedded32ByteFixture659.Observation, "actual observation type");
                    Embedded32ByteFixture659.Observation observed=(Embedded32ByteFixture659.Observation)actual;
                    check(observed.name().equals(literal.name()), "literal observation kind "+(i+1));
                    switch(literal.mode()) {
                        case "FRAME" -> check(observed.actual()==captured.get((Integer)literal.value()),
                                "SAME actual exposed frame "+(i+1));
                        case "SAME" -> check(observed.actual()==literal.value(), "SAME complete caller Outcome");
                        case "VALUE" -> check(literal.value().equals(observed.actual()), "both actual budget arguments");
                        default -> throw new AssertionError("literal observation mode");
                    }
                }
            }
            check(memory==e.expectedMemory, "all literal Memory rows");
        }
    }

    private static void run(Expected e) {
        // A fresh nominal adapter and complete literal expectations/offers exist
        // before this scene's only execute. No default banks/DF/FP/RAM are used.
        Ram host=new Ram();
        for (Map.Entry<Long,Byte> seed:e.initial.entrySet())
            host.seedHex(seed.getKey(),HexFormat.of().toHexDigits(seed.getValue()));
        check(host.bytes.keySet().equals(e.initial.keySet()) && host.bytes.equals(e.initial),
                "complete explicitly seeded initial map");
        check(host.events.isEmpty() && host.memoryEvents.isEmpty(), "no target events from seed");
        Harness h=new Harness(host,e);
        GovernmentCrtBoundary185Api.LoopBudget budget=h::budget;
        QueueFp604Api.Input input=new QueueFp604Api.Input(
                new FullCopy437Api.Input(e.root,e.rootDf,budget),e.rootFp);
        check(input.base().entry()==e.root && input.base().budget()==budget
                && input.mxcsr()==e.rootFp, "SAME explicit input Entry/budget/FP");

        QueueFp604Api.Outcome actual=Embedded32Fp659.execute(input,host,h::invoke);

        if (e.sameStop==null) {
            check(actual instanceof QueueFp604Api.Normal, "actual whole Normal");
            QueueFp604Api.Normal normal=(QueueFp604Api.Normal)actual;
            NormalReturn returned=normal.base().normalReturn();
            check(returned.volatileBits().equals(e.finalReturn.volatileBits()), "whole final V/XMM0..5");
            check(returned.nonvolatileBits().equals(e.finalReturn.nonvolatileBits()), "fresh final all N/XMM6");
            check(returned.returnRipBits()==e.finalReturn.returnRipBits()
                    && returned.callerRspBits()==e.finalReturn.callerRspBits(), "fresh root RET/callerSP");
            check(normal.base().postDirectionFlagSet()==e.finalDf, "whole final DF");
            check(normal.postMxcsr().equals(e.finalFp) && normal.postMxcsr()==e.finalFp,
                    "whole final FP value/mask and SAMElastpostFP");
            h.ram();
        } else {
            check(actual==e.sameStop, "SAME middle Stopped Outcome");
            QueueFp604Api.Stopped stopped=(QueueFp604Api.Stopped)actual;
            check(stopped.snapshot()==e.sameSnapshot, "SAME explicit Snapshot");
            check(stopped.snapshot().currentState()==e.sameStopEntry, "SAME explicit stopped Entry");
            check(stopped.snapshot().currentState().equals(e.sameSnapshot.currentState()), "complete stopped V/N/image/SP");
            check(stopped.reason()==e.sameStop.reason()
                    && stopped.raisedConditionBits()==e.sameStop.raisedConditionBits()
                    && stopped.originCallSiteRva()==e.sameStop.originCallSiteRva(), "complete Stop metadata");
            check(stopped.snapshot().instructionRva()==e.sameSnapshot.instructionRva()
                    && stopped.snapshot().directionFlagSet()==e.sameSnapshot.directionFlagSet(),
                    "explicit stop instruction/DF");
            check(stopped.snapshot().mxcsr().equals(e.sameSnapshot.mxcsr())
                    && stopped.snapshot().mxcsr()==e.sameSnapshot.mxcsr(), "SAME complete stopped FP");
            RamExpected finalMap=e.ram.get(e.trace.size());
            check(finalMap!=null && host.bytes.keySet().equals(finalMap.bytes().keySet())
                    && host.bytes.equals(finalMap.bytes()), "complete final stopped map, no suffix");
        }
        h.finish();
    }

    public static void growthFiveCallsCarryExplicitFpToWholeNormal() {
        run(normalLiteral());
    }

    public static void secondDestructorReturnsSameStoppedAfterFirstNormal() {
        run(stoppedLiteral());
    }

    public static int verify() {
        growthFiveCallsCarryExplicitFpToWholeNormal();
        secondDestructorReturnsSameStoppedAfterFirstNormal();
        return 2;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static Expected normalLiteral() {
        Expected e=new Expected();
        e.fp.put("N_ROOT_FP659",new QueueFp604Api.Mxcsr(0x0001,0x0003));
        e.fp.put("N_AFTER_BA_FP659",new QueueFp604Api.Mxcsr(0x0200,0x0201));
        e.fp.put("N_AFTER_ALLOC_FP659",new QueueFp604Api.Mxcsr(0x0040,0x0041));
        e.fp.put("N_AFTER_COMMIT_FP659",new QueueFp604Api.Mxcsr(0x2000,0x2003));
        e.fp.put("N_AFTER_SELECTED_UNKNOWN659",new QueueFp604Api.Mxcsr(0x0000,0x0000));
        e.fp.put("N_AFTER_FINAL_FP659",new QueueFp604Api.Mxcsr(0x0041,0x00c3));
        e.root=new Entry(0x0000000140000000L, 0x0000000074024008L, new VolatileBits(0xa659000000000001L, 0x0000000000350000L, 0x0000000000360000L, 0xa659000000000008L, 0xa659000000000009L, 0xa65900000000000aL, 0xa65900000000000bL, new Bits128(0xa659000000000100L, 0xa659000000000200L), new Bits128(0xa659000000000101L, 0xa659000000000201L), new Bits128(0xa659000000000102L, 0xa659000000000202L), new Bits128(0xa659000000000103L, 0xa659000000000203L), new Bits128(0xa659000000000104L, 0xa659000000000204L), new Bits128(0xa659000000000105L, 0xa659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0xb659000000000003L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0xb659000000000007L, 0xb659000000000008L, new Bits128(0x6659665966596659L, 0x9659965996599659L)));
        e.rootDf=true;
        e.rootFp=e.fp.get("N_ROOT_FP659");
        e.ownedBytes=640;
        e.expectedMemory=59;
        e.expectedBudget=3;
        e.initial=normalInitial();
        e.frames.add(new Spec(new Call(0x00000000037271baL, TargetKind.DIRECT_RVA, 0x0000000000889660L, 0x0000000074023fc0L, new VolatileBits(0x0000000000360010L, 0x0000000000350010L, 0x0000000000360000L, 0xa659000000000008L, 0xa659000000000009L, 0xa65900000000000aL, 0xa65900000000000bL, new Bits128(0xa659000000000100L, 0xa659000000000200L), new Bits128(0xa659000000000101L, 0xa659000000000201L), new Bits128(0xa659000000000102L, 0xa659000000000202L), new Bits128(0xa659000000000103L, 0xa659000000000203L), new Bits128(0xa659000000000104L, 0xa659000000000204L), new Bits128(0xa659000000000105L, 0xa659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0xb659000000000005L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), new Entry(0x0000000140000000L, 0x0000000074023fb8L, new VolatileBits(0x0000000000360010L, 0x0000000000350010L, 0x0000000000360000L, 0xa659000000000008L, 0xa659000000000009L, 0xa65900000000000aL, 0xa65900000000000bL, new Bits128(0xa659000000000100L, 0xa659000000000200L), new Bits128(0xa659000000000101L, 0xa659000000000201L), new Bits128(0xa659000000000102L, 0xa659000000000202L), new Bits128(0xa659000000000103L, 0xa659000000000203L), new Bits128(0xa659000000000104L, 0xa659000000000204L), new Bits128(0xa659000000000105L, 0xa659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0xb659000000000005L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), true, e.fp.get("N_ROOT_FP659"), 5, 0x00000001437271bfL));
        e.frames.add(new Spec(new Call(0x00000000037271eeL, TargetKind.INDIRECT_ABSOLUTE, 0x00000001a6592008L, 0x0000000074023fc0L, new VolatileBits(0x00000000003b0000L, 0x00000000003a0000L, 0x0000000000000040L, 0x0000000000000008L, 0xc659000000000009L, 0xc65900000000000aL, 0xc65900000000000bL, new Bits128(0xc659000000000100L, 0xc659000000000200L), new Bits128(0xc659000000000101L, 0xc659000000000201L), new Bits128(0xc659000000000102L, 0xc659000000000202L), new Bits128(0xc659000000000103L, 0xc659000000000203L), new Bits128(0xc659000000000104L, 0xc659000000000204L), new Bits128(0xc659000000000105L, 0xc659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0x000000014448d230L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), new Entry(0x0000000140000000L, 0x0000000074023fb8L, new VolatileBits(0x00000000003b0000L, 0x00000000003a0000L, 0x0000000000000040L, 0x0000000000000008L, 0xc659000000000009L, 0xc65900000000000aL, 0xc65900000000000bL, new Bits128(0xc659000000000100L, 0xc659000000000200L), new Bits128(0xc659000000000101L, 0xc659000000000201L), new Bits128(0xc659000000000102L, 0xc659000000000202L), new Bits128(0xc659000000000103L, 0xc659000000000203L), new Bits128(0xc659000000000104L, 0xc659000000000204L), new Bits128(0xc659000000000105L, 0xc659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0x000000014448d230L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), false, e.fp.get("N_AFTER_BA_FP659"), 3, 0x00000001437271f1L));
        e.frames.add(new Spec(new Call(0x0000000003727249L, TargetKind.DIRECT_RVA, 0x00000000008874d0L, 0x0000000074023fc0L, new VolatileBits(0x0000000089abcdefL, 0x0000000000350010L, 0x0000000000380000L, 0x0000000000000001L, 0x0000000000000002L, 0x0000000000380000L, 0xd65900000000000bL, new Bits128(0x1111222233334444L, 0xaaaabbbbccccddddL), new Bits128(0xd659000000000101L, 0xd659000000000201L), new Bits128(0xd659000000000102L, 0xd659000000000202L), new Bits128(0xd659000000000103L, 0xd659000000000203L), new Bits128(0xd659000000000104L, 0xd659000000000204L), new Bits128(0xd659000000000105L, 0xd659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0x000000014448d230L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), new Entry(0x0000000140000000L, 0x0000000074023fb8L, new VolatileBits(0x0000000089abcdefL, 0x0000000000350010L, 0x0000000000380000L, 0x0000000000000001L, 0x0000000000000002L, 0x0000000000380000L, 0xd65900000000000bL, new Bits128(0x1111222233334444L, 0xaaaabbbbccccddddL), new Bits128(0xd659000000000101L, 0xd659000000000201L), new Bits128(0xd659000000000102L, 0xd659000000000202L), new Bits128(0xd659000000000103L, 0xd659000000000203L), new Bits128(0xd659000000000104L, 0xd659000000000204L), new Bits128(0xd659000000000105L, 0xd659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0x000000014448d230L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), true, e.fp.get("N_AFTER_ALLOC_FP659"), 5, 0x000000014372724eL));
        e.frames.add(new Spec(new Call(0x00000000037272f0L, TargetKind.DIRECT_RVA, 0x00000000037282b0L, 0x0000000074023fc0L, new VolatileBits(0x00000000deadbeefL, 0x0000000000350030L, 0x0000000000360030L, 0xe659000000000008L, 0xe659000000000009L, 0xe65900000000000aL, 0xe65900000000000bL, new Bits128(0x1122334455667788L, 0x8877665544332211L), new Bits128(0xe659000000000101L, 0xe659000000000201L), new Bits128(0xe659000000000102L, 0xe659000000000202L), new Bits128(0xe659000000000103L, 0xe659000000000203L), new Bits128(0xe659000000000104L, 0xe659000000000204L), new Bits128(0xe659000000000105L, 0xe659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), new Entry(0x0000000140000000L, 0x0000000074023fb8L, new VolatileBits(0x00000000deadbeefL, 0x0000000000350030L, 0x0000000000360030L, 0xe659000000000008L, 0xe659000000000009L, 0xe65900000000000aL, 0xe65900000000000bL, new Bits128(0x1122334455667788L, 0x8877665544332211L), new Bits128(0xe659000000000101L, 0xe659000000000201L), new Bits128(0xe659000000000102L, 0xe659000000000202L), new Bits128(0xe659000000000103L, 0xe659000000000203L), new Bits128(0xe659000000000104L, 0xe659000000000204L), new Bits128(0xe659000000000105L, 0xe659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), false, e.fp.get("N_AFTER_COMMIT_FP659"), 5, 0x00000001437272f5L));
        e.frames.add(new Spec(new Call(0x00000000037272f8L, TargetKind.DIRECT_RVA, 0x0000000003727ec0L, 0x0000000074023fc0L, new VolatileBits(0xf659000000000001L, 0x0000000000350000L, 0xf659000000000003L, 0xf659000000000008L, 0xf659000000000009L, 0xf65900000000000aL, 0xf65900000000000bL, new Bits128(0xf659000000000100L, 0xf659000000000200L), new Bits128(0xf659000000000101L, 0xf659000000000201L), new Bits128(0xf659000000000102L, 0xf659000000000202L), new Bits128(0xf659000000000103L, 0xf659000000000203L), new Bits128(0xf659000000000104L, 0xf659000000000204L), new Bits128(0xf659000000000105L, 0xf659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), new Entry(0x0000000140000000L, 0x0000000074023fb8L, new VolatileBits(0xf659000000000001L, 0x0000000000350000L, 0xf659000000000003L, 0xf659000000000008L, 0xf659000000000009L, 0xf65900000000000aL, 0xf65900000000000bL, new Bits128(0xf659000000000100L, 0xf659000000000200L), new Bits128(0xf659000000000101L, 0xf659000000000201L), new Bits128(0xf659000000000102L, 0xf659000000000202L), new Bits128(0xf659000000000103L, 0xf659000000000203L), new Bits128(0xf659000000000104L, 0xf659000000000204L), new Bits128(0xf659000000000105L, 0xf659000000000205L)), new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))), true, e.fp.get("N_AFTER_SELECTED_UNKNOWN659"), 5, 0x00000001437272fdL));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0xc659000000000001L, 0xc659000000000002L, 0xc659000000000003L, 0xc659000000000008L, 0xc659000000000009L, 0xc65900000000000aL, 0xc65900000000000bL, new Bits128(0xc659000000000100L, 0xc659000000000200L), new Bits128(0xc659000000000101L, 0xc659000000000201L), new Bits128(0xc659000000000102L, 0xc659000000000202L), new Bits128(0xc659000000000103L, 0xc659000000000203L), new Bits128(0xc659000000000104L, 0xc659000000000204L), new Bits128(0xc659000000000105L, 0xc659000000000205L)), 0x00000001437271bfL, 0x0000000074023fc0L, new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0xb659000000000005L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))),false),e.fp.get("N_AFTER_BA_FP659")));
        e.effects.add(List.of(new Effect("writeQword",0x00000000003b0008L,0x00000001a6592008L)));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0x0000000000380000L, 0xd659000000000002L, 0xd659000000000003L, 0xd659000000000008L, 0xd659000000000009L, 0xd65900000000000aL, 0xd65900000000000bL, new Bits128(0xd659000000000100L, 0xd659000000000200L), new Bits128(0xd659000000000101L, 0xd659000000000201L), new Bits128(0xd659000000000102L, 0xd659000000000202L), new Bits128(0xd659000000000103L, 0xd659000000000203L), new Bits128(0xd659000000000104L, 0xd659000000000204L), new Bits128(0xd659000000000105L, 0xd659000000000205L)), 0x00000001437271f1L, 0x0000000074023fc0L, new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0x000000014448d230L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))),true),e.fp.get("N_AFTER_ALLOC_FP659")));
        e.effects.add(List.of(new Effect("writeQword",0x00000000003c0000L,0xcc65900000000002L)));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0xe659000000000001L, 0xe659000000000002L, 0xe659000000000003L, 0xe659000000000008L, 0xe659000000000009L, 0xe65900000000000aL, 0xe65900000000000bL, new Bits128(0xe659000000000100L, 0xe659000000000200L), new Bits128(0xe659000000000101L, 0xe659000000000201L), new Bits128(0xe659000000000102L, 0xe659000000000202L), new Bits128(0xe659000000000103L, 0xe659000000000203L), new Bits128(0xe659000000000104L, 0xe659000000000204L), new Bits128(0xe659000000000105L, 0xe659000000000205L)), 0x000000014372724eL, 0x0000000074023fc0L, new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0x0000000000000002L, 0x000000014448d230L, 0x0000000000390000L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))),false),e.fp.get("N_AFTER_COMMIT_FP659")));
        e.effects.add(List.of(new Effect("writeQword",0x0000000000350010L,0x0000000000380000L), new Effect("writeDword",0x0000000000350018L,0x0000000000000002L)));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0xf659000000000001L, 0xf659000000000002L, 0xf659000000000003L, 0xf659000000000008L, 0xf659000000000009L, 0xf65900000000000aL, 0xf65900000000000bL, new Bits128(0xf659000000000100L, 0xf659000000000200L), new Bits128(0xf659000000000101L, 0xf659000000000201L), new Bits128(0xf659000000000102L, 0xf659000000000202L), new Bits128(0xf659000000000103L, 0xf659000000000203L), new Bits128(0xf659000000000104L, 0xf659000000000204L), new Bits128(0xf659000000000105L, 0xf659000000000205L)), 0x00000001437272f5L, 0x0000000074023fc0L, new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))),true),e.fp.get("N_AFTER_SELECTED_UNKNOWN659")));
        e.effects.add(List.of(new Effect("writeQword",0x00000000003c0000L,0xcc65900000000004L)));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0x8659000000000001L, 0x8659000000000002L, 0x8659000000000003L, 0x8659000000000008L, 0x8659000000000009L, 0x865900000000000aL, 0x865900000000000bL, new Bits128(0x8659000000000100L, 0x8659000000000200L), new Bits128(0x8659000000000101L, 0x8659000000000201L), new Bits128(0x8659000000000102L, 0x8659000000000202L), new Bits128(0x8659000000000103L, 0x8659000000000203L), new Bits128(0x8659000000000104L, 0x8659000000000204L), new Bits128(0x8659000000000105L, 0x8659000000000205L)), 0x00000001437272fdL, 0x0000000074023fc0L, new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0x0000000000350010L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0x0000000000350000L, 0x0000000000360000L, new Bits128(0x6659665966596659L, 0x9659965996599659L))),false),e.fp.get("N_AFTER_FINAL_FP659")));
        e.effects.add(List.of(new Effect("writeQword",0x00000000003c0000L,0xcc65900000000005L)));
        e.ram.put(9,new RamExpected(9,normalRam9()));
        e.ram.put(12,new RamExpected(12,normalRam12()));
        e.ram.put(18,new RamExpected(18,normalRam18()));
        e.ram.put(21,new RamExpected(21,normalRam21()));
        e.ram.put(24,new RamExpected(24,normalRam24()));
        e.ram.put(33,new RamExpected(33,normalRam33()));
        e.ram.put(37,new RamExpected(37,normalRam37()));
        e.ram.put(40,new RamExpected(40,normalRam40()));
        e.ram.put(48,new RamExpected(48,normalRam48()));
        e.ram.put(61,new RamExpected(61,normalRam61()));
        e.ram.put(64,new RamExpected(64,normalRam64()));
        e.ram.put(65,new RamExpected(65,normalRam65()));
        e.ram.put(68,new RamExpected(68,normalRam68()));
        e.ram.put(72,new RamExpected(72,normalRam72()));
        e.finalReturn=new NormalReturn(new VolatileBits(0x0000000000350000L, 0x8659000000000002L, 0x8659000000000003L, 0x8659000000000008L, 0x8659000000000009L, 0x865900000000000aL, 0x865900000000000bL, new Bits128(0x8659000000000100L, 0x8659000000000200L), new Bits128(0x8659000000000101L, 0x8659000000000201L), new Bits128(0x8659000000000102L, 0x8659000000000202L), new Bits128(0x8659000000000103L, 0x8659000000000203L), new Bits128(0x8659000000000104L, 0x8659000000000204L), new Bits128(0x8659000000000105L, 0x8659000000000205L)), 0x00000001a6590123L, 0x0000000074024010L, new NonvolatileBits(0xb659000000000001L, 0xb659000000000002L, 0xb659000000000003L, 0xb659000000000004L, 0xb659000000000005L, 0xb659000000000006L, 0xb659000000000007L, 0xb659000000000008L, new Bits128(0x6659665966596659L, 0x9659965996599659L)));
        e.finalDf=false;
        e.finalFp=e.fp.get("N_AFTER_FINAL_FP659");
        normalTrace(e);
        return e;
    }

    private static Map<Long,Byte> normalInitial() {
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000081059a601000000"),
                new Region(0x00000000003c0000L,
                "0000000000596655"));
    }

    private static Map<Long,Byte> normalRam9() {
        // N_BA-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5dbf717243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000081059a601000000"),
                new Region(0x00000000003c0000L,
                "0000000000596655"));
    }

    private static Map<Long,Byte> normalRam12() {
        // N_BA_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5dbf717243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "0000000000596655"));
    }

    private static Map<Long,Byte> normalRam18() {
        // N_ALLOC-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5df1717243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "0000000000596655"));
    }

    private static Map<Long,Byte> normalRam21() {
        // N_ALLOC_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5df1717243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam24() {
        // budget-24
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5df1717243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam33() {
        // N_COMMIT-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d4e727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000370000000000010000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d2484401000000674523f1efcdab894444333322221111ddddccccbbbbaaaaa5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam37() {
        // N_COMMIT_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d4e727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000100000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d2484401000000674523f1efcdab894444333322221111ddddccccbbbbaaaaa5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam40() {
        // budget-40
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d4e727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d2484401000000674523f1efcdab894444333322221111ddddccccbbbbaaaaa5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam48() {
        // budget-48
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d4e727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000222211110000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d24844010000007856341298badcfeefcdab89674523011032547698badcfea5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam61() {
        // N_SELECTED-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5df5727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d24844010000007856341298badcfeefcdab89674523011032547698badcfe30d2484401000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "02000000009065cc"));
    }

    private static Map<Long,Byte> normalRam64() {
        // N_SELECTED_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5df5727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d24844010000007856341298badcfeefcdab89674523011032547698badcfe30d2484401000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "04000000009065cc"));
    }

    private static Map<Long,Byte> normalRam65() {
        // N_FINAL-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5dfd727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d24844010000007856341298badcfeefcdab89674523011032547698badcfe30d2484401000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "04000000009065cc"));
    }

    private static Map<Long,Byte> normalRam68() {
        // N_FINAL_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5dfd727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d24844010000007856341298badcfeefcdab89674523011032547698badcfe30d2484401000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "05000000009065cc"));
    }

    private static Map<Long,Byte> normalRam72() {
        // whole-Normal-after-fresh-three-POPs-and-RET
        return literalMap(
                new Region(0x0000000074023f88L,
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5dfd727243010000005d5d5d5d5d5d5d5d" +
                "5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d06000000000059b605000000000059b608000000000059b607000000000059b603000000000059b6" +
                "230159a6010000005d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d04000000000059b65d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d"),
                new Region(0x0000000000350000L,
                "000000000000000000000000000000000000380000000000020000000200000000003a0000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000360000L,
                "00000000000000000000000000000000000039000000000002000000020000000000000000000000efbeadde0000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000370000L,
                "005059a601000000674523f1efcdab894444333322221111ddddccccbbbbaaaa"),
                new Region(0x0000000000380000L,
                "30d24844010000007856341298badcfeefcdab89674523011032547698badcfe30d2484401000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x0000000000390000L,
                "006059a6010000007856341298badcfeefcdab89674523011032547698badcfe206059a601000000214365870df0ad0b88776655443322111122334455667788"),
                new Region(0x00000000003a0000L,
                "00003b0000000000"),
                new Region(0x00000000003b0000L,
                "001059a601000000082059a601000000"),
                new Region(0x00000000003c0000L,
                "05000000009065cc"));
    }

    private static void normalTrace(Expected e) {
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074024000L, 0xb659000000000003L, 0L, 0L, 0L)); // 1
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023ff8L, 0xb659000000000007L, 0L, 0L, 0L)); // 2
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023ff0L, 0xb659000000000008L, 0L, 0L, 0L)); // 3
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074024020L, 0xb659000000000004L, 0L, 0L, 0L)); // 4
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000036001cL, 2L, 0L, 0L, 0L)); // 5
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fe8L, 0xb659000000000005L, 0L, 0L, 0L)); // 6
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fe0L, 0xb659000000000006L, 0L, 0L, 0L)); // 7
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000360010L, 0x0000000000390000L, 0L, 0L, 0L)); // 8
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fb8L, 0x00000001437271bfL, 0L, 0L, 0L)); // 9
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",0)); // 10
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000003b0008L, 0x00000001a6592008L, 0L, 0L, 0L)); // 11
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(0))); // 12
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000035001cL, 1L, 0L, 0L, 0L)); // 13
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x0000000000350018L, 1L, 0L, 0L, 0L)); // 14
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000350020L, 0x00000000003a0000L, 0L, 0L, 0L)); // 15
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x00000000003a0000L, 0x00000000003b0000L, 0L, 0L, 0L)); // 16
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x00000000003b0008L, 0x00000001a6592008L, 0L, 0L, 0L)); // 17
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fb8L, 0x00000001437271f1L, 0L, 0L, 0L)); // 18
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",1)); // 19
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000003c0000L, 0xcc65900000000002L, 0L, 0L, 0L)); // 20
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(1))); // 21
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000035001cL, 1L, 0L, 0L, 0L)); // 22
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000350010L, 0x0000000000370000L, 0L, 0L, 0L)); // 23
        e.trace.add(new ObservationExpected("BUDGET2","VALUE",new BudgetArgs(0x0000000003727210L,0x000000000037000cL))); // 24
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000000380000L, 0x000000014448d230L, 0L, 0L, 0L)); // 25
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x0000000000370008L, -249346713L, 0L, 0L, 0L)); // 26
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x0000000000380008L, -249346713L, 0L, 0L, 0L)); // 27
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000037000cL, -1985229329L, 0L, 0L, 0L)); // 28
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x000000000038000cL, -1985229329L, 0L, 0L, 0L)); // 29
        e.trace.add(new Embedded32ByteFixture659.Event("R128", 0x0000000000370010L, 0x1111222233334444L, 0xaaaabbbbccccddddL, 0L, 0L)); // 30
        e.trace.add(new Embedded32ByteFixture659.Event("W128", 0x0000000000380010L, 0x1111222233334444L, 0xaaaabbbbccccddddL, 0L, 0L)); // 31
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000035001cL, 1L, 0L, 0L, 0L)); // 32
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fb8L, 0x000000014372724eL, 0L, 0L, 0L)); // 33
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",2)); // 34
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000000350010L, 0x0000000000380000L, 0L, 0L, 0L)); // 35
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x0000000000350018L, 2L, 0L, 0L, 0L)); // 36
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(2))); // 37
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x000000000035001cL, 2L, 0L, 0L, 0L)); // 38
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000350010L, 0x0000000000380000L, 0L, 0L, 0L)); // 39
        e.trace.add(new ObservationExpected("BUDGET2","VALUE",new BudgetArgs(0x00000000037272a0L,0x000000000039000cL))); // 40
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000000380000L, 0x000000014448d230L, 0L, 0L, 0L)); // 41
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x0000000000390008L, 305419896L, 0L, 0L, 0L)); // 42
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x0000000000380008L, 305419896L, 0L, 0L, 0L)); // 43
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000039000cL, -19088744L, 0L, 0L, 0L)); // 44
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x000000000038000cL, -19088744L, 0L, 0L, 0L)); // 45
        e.trace.add(new Embedded32ByteFixture659.Event("R128", 0x0000000000390010L, 0x0123456789abcdefL, 0xfedcba9876543210L, 0L, 0L)); // 46
        e.trace.add(new Embedded32ByteFixture659.Event("W128", 0x0000000000380010L, 0x0123456789abcdefL, 0xfedcba9876543210L, 0L, 0L)); // 47
        e.trace.add(new ObservationExpected("BUDGET2","VALUE",new BudgetArgs(0x00000000037272a0L,0x000000000039002cL))); // 48
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000000380020L, 0x000000014448d230L, 0L, 0L, 0L)); // 49
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x0000000000390028L, -2023406815L, 0L, 0L, 0L)); // 50
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x0000000000380028L, -2023406815L, 0L, 0L, 0L)); // 51
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000039002cL, 195948557L, 0L, 0L, 0L)); // 52
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x000000000038002cL, 195948557L, 0L, 0L, 0L)); // 53
        e.trace.add(new Embedded32ByteFixture659.Event("R128", 0x0000000000390030L, 0x1122334455667788L, 0x8877665544332211L, 0L, 0L)); // 54
        e.trace.add(new Embedded32ByteFixture659.Event("W128", 0x0000000000380030L, 0x1122334455667788L, 0x8877665544332211L, 0L, 0L)); // 55
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074024020L, 0xb659000000000004L, 0L, 0L, 0L)); // 56
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074023fe8L, 0xb659000000000005L, 0L, 0L, 0L)); // 57
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074023fe0L, 0xb659000000000006L, 0L, 0L, 0L)); // 58
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x0000000000360028L, -559038737L, 0L, 0L, 0L)); // 59
        e.trace.add(new Embedded32ByteFixture659.Event("W32", 0x0000000000350028L, -559038737L, 0L, 0L, 0L)); // 60
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fb8L, 0x00000001437272f5L, 0L, 0L, 0L)); // 61
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",3)); // 62
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000003c0000L, 0xcc65900000000004L, 0L, 0L, 0L)); // 63
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(3))); // 64
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074023fb8L, 0x00000001437272fdL, 0L, 0L, 0L)); // 65
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",4)); // 66
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000003c0000L, 0xcc65900000000005L, 0L, 0L, 0L)); // 67
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(4))); // 68
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074023ff0L, 0xb659000000000008L, 0L, 0L, 0L)); // 69
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074023ff8L, 0xb659000000000007L, 0L, 0L, 0L)); // 70
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074024000L, 0xb659000000000003L, 0L, 0L, 0L)); // 71
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000074024008L, 0x00000001a6590123L, 0L, 0L, 0L)); // 72
    }

    private static Expected stoppedLiteral() {
        Expected e=new Expected();
        e.fp.put("S_ROOT_FP659",new QueueFp604Api.Mxcsr(0x0100,0x0101));
        e.fp.put("S_AFTER_BA_FP659",new QueueFp604Api.Mxcsr(0x0400,0x0401));
        e.fp.put("S_AFTER_DTOR1_FP659",new QueueFp604Api.Mxcsr(0x0800,0x0841));
        e.fp.put("S_EXPLICIT_STOP_UNKNOWN659",new QueueFp604Api.Mxcsr(0x0000,0x0000));
        e.root=new Entry(0x0000000140000000L, 0x0000000074034008L, new VolatileBits(0xa659100000000001L, 0x0000000000450000L, 0x0000000000460000L, 0xa659100000000008L, 0xa659100000000009L, 0xa65910000000000aL, 0xa65910000000000bL, new Bits128(0xa659100000000100L, 0xa659100000000200L), new Bits128(0xa659100000000101L, 0xa659100000000201L), new Bits128(0xa659100000000102L, 0xa659100000000202L), new Bits128(0xa659100000000103L, 0xa659100000000203L), new Bits128(0xa659100000000104L, 0xa659100000000204L), new Bits128(0xa659100000000105L, 0xa659100000000205L)), new NonvolatileBits(0xb659100000000001L, 0xb659100000000002L, 0xb659100000000003L, 0xb659100000000004L, 0xb659100000000005L, 0xb659100000000006L, 0xb659100000000007L, 0xb659100000000008L, new Bits128(0x6659665911111111L, 0x9659965922222222L)));
        e.rootDf=false;
        e.rootFp=e.fp.get("S_ROOT_FP659");
        e.ownedBytes=608;
        e.expectedMemory=24;
        e.expectedBudget=2;
        e.initial=stoppedInitial();
        e.frames.add(new Spec(new Call(0x00000000037271baL, TargetKind.DIRECT_RVA, 0x0000000000889660L, 0x0000000074033fc0L, new VolatileBits(0x0000000000460010L, 0x0000000000450010L, 0x0000000000460000L, 0xa659100000000008L, 0xa659100000000009L, 0xa65910000000000aL, 0xa65910000000000bL, new Bits128(0xa659100000000100L, 0xa659100000000200L), new Bits128(0xa659100000000101L, 0xa659100000000201L), new Bits128(0xa659100000000102L, 0xa659100000000202L), new Bits128(0xa659100000000103L, 0xa659100000000203L), new Bits128(0xa659100000000104L, 0xa659100000000204L), new Bits128(0xa659100000000105L, 0xa659100000000205L)), new NonvolatileBits(0xb659100000000001L, 0xb659100000000002L, 0x0000000000450010L, 0x0000000000000001L, 0xb659100000000005L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))), new Entry(0x0000000140000000L, 0x0000000074033fb8L, new VolatileBits(0x0000000000460010L, 0x0000000000450010L, 0x0000000000460000L, 0xa659100000000008L, 0xa659100000000009L, 0xa65910000000000aL, 0xa65910000000000bL, new Bits128(0xa659100000000100L, 0xa659100000000200L), new Bits128(0xa659100000000101L, 0xa659100000000201L), new Bits128(0xa659100000000102L, 0xa659100000000202L), new Bits128(0xa659100000000103L, 0xa659100000000203L), new Bits128(0xa659100000000104L, 0xa659100000000204L), new Bits128(0xa659100000000105L, 0xa659100000000205L)), new NonvolatileBits(0xb659100000000001L, 0xb659100000000002L, 0x0000000000450010L, 0x0000000000000001L, 0xb659100000000005L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))), false, e.fp.get("S_ROOT_FP659"), 5, 0x00000001437271bfL));
        e.frames.add(new Spec(new Call(0x000000000372727bL, TargetKind.INDIRECT_ABSOLUTE, 0x00000001a6593100L, 0x0000000074033fc0L, new VolatileBits(0x00000000004a0000L, 0x0000000000470020L, 0x0000000000000000L, 0xc659100000000008L, 0xc659100000000009L, 0xc65910000000000aL, 0xc65910000000000bL, new Bits128(0xc659100000000100L, 0xc659100000000200L), new Bits128(0xc659100000000101L, 0xc659100000000201L), new Bits128(0xc659100000000102L, 0xc659100000000202L), new Bits128(0xc659100000000103L, 0xc659100000000203L), new Bits128(0xc659100000000104L, 0xc659100000000204L), new Bits128(0xc659100000000105L, 0xc659100000000205L)), new NonvolatileBits(0x0000000000470020L, 0x0000000000470060L, 0x0000000000450010L, 0x0000000000000001L, 0x000000014448d230L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))), new Entry(0x0000000140000000L, 0x0000000074033fb8L, new VolatileBits(0x00000000004a0000L, 0x0000000000470020L, 0x0000000000000000L, 0xc659100000000008L, 0xc659100000000009L, 0xc65910000000000aL, 0xc65910000000000bL, new Bits128(0xc659100000000100L, 0xc659100000000200L), new Bits128(0xc659100000000101L, 0xc659100000000201L), new Bits128(0xc659100000000102L, 0xc659100000000202L), new Bits128(0xc659100000000103L, 0xc659100000000203L), new Bits128(0xc659100000000104L, 0xc659100000000204L), new Bits128(0xc659100000000105L, 0xc659100000000205L)), new NonvolatileBits(0x0000000000470020L, 0x0000000000470060L, 0x0000000000450010L, 0x0000000000000001L, 0x000000014448d230L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))), false, e.fp.get("S_AFTER_BA_FP659"), 2, 0x000000014372727dL));
        e.frames.add(new Spec(new Call(0x000000000372727bL, TargetKind.INDIRECT_ABSOLUTE, 0x00000001a6594100L, 0x0000000074033fc0L, new VolatileBits(0x00000000004b0000L, 0x0000000000470040L, 0x0000000000000000L, 0xd659100000000008L, 0xd659100000000009L, 0xd65910000000000aL, 0xd65910000000000bL, new Bits128(0xd659100000000100L, 0xd659100000000200L), new Bits128(0xd659100000000101L, 0xd659100000000201L), new Bits128(0xd659100000000102L, 0xd659100000000202L), new Bits128(0xd659100000000103L, 0xd659100000000203L), new Bits128(0xd659100000000104L, 0xd659100000000204L), new Bits128(0xd659100000000105L, 0xd659100000000205L)), new NonvolatileBits(0x0000000000470040L, 0x0000000000470060L, 0x0000000000450010L, 0x0000000000000001L, 0x000000014448d230L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))), new Entry(0x0000000140000000L, 0x0000000074033fb8L, new VolatileBits(0x00000000004b0000L, 0x0000000000470040L, 0x0000000000000000L, 0xd659100000000008L, 0xd659100000000009L, 0xd65910000000000aL, 0xd65910000000000bL, new Bits128(0xd659100000000100L, 0xd659100000000200L), new Bits128(0xd659100000000101L, 0xd659100000000201L), new Bits128(0xd659100000000102L, 0xd659100000000202L), new Bits128(0xd659100000000103L, 0xd659100000000203L), new Bits128(0xd659100000000104L, 0xd659100000000204L), new Bits128(0xd659100000000105L, 0xd659100000000205L)), new NonvolatileBits(0x0000000000470040L, 0x0000000000470060L, 0x0000000000450010L, 0x0000000000000001L, 0x000000014448d230L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))), true, e.fp.get("S_AFTER_DTOR1_FP659"), 2, 0x000000014372727dL));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0xc659100000000001L, 0xc659100000000002L, 0xc659100000000003L, 0xc659100000000008L, 0xc659100000000009L, 0xc65910000000000aL, 0xc65910000000000bL, new Bits128(0xc659100000000100L, 0xc659100000000200L), new Bits128(0xc659100000000101L, 0xc659100000000201L), new Bits128(0xc659100000000102L, 0xc659100000000202L), new Bits128(0xc659100000000103L, 0xc659100000000203L), new Bits128(0xc659100000000104L, 0xc659100000000204L), new Bits128(0xc659100000000105L, 0xc659100000000205L)), 0x00000001437271bfL, 0x0000000074033fc0L, new NonvolatileBits(0xb659100000000001L, 0xb659100000000002L, 0x0000000000450010L, 0x0000000000000001L, 0xb659100000000005L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))),false),e.fp.get("S_AFTER_BA_FP659")));
        e.effects.add(List.of(new Effect("writeQword",0x00000000004c0000L,0xcc65910000000001L)));
        e.offers.add(new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new NormalReturn(new VolatileBits(0xd659100000000001L, 0xd659100000000002L, 0xd659100000000003L, 0xd659100000000008L, 0xd659100000000009L, 0xd65910000000000aL, 0xd65910000000000bL, new Bits128(0xd659100000000100L, 0xd659100000000200L), new Bits128(0xd659100000000101L, 0xd659100000000201L), new Bits128(0xd659100000000102L, 0xd659100000000202L), new Bits128(0xd659100000000103L, 0xd659100000000203L), new Bits128(0xd659100000000104L, 0xd659100000000204L), new Bits128(0xd659100000000105L, 0xd659100000000205L)), 0x000000014372727dL, 0x0000000074033fc0L, new NonvolatileBits(0x0000000000470020L, 0x0000000000470060L, 0x0000000000450010L, 0x0000000000000001L, 0x000000014448d230L, 0x0000000000490000L, 0x0000000000450000L, 0x0000000000460000L, new Bits128(0x6659665911111111L, 0x9659965922222222L))),true),e.fp.get("S_AFTER_DTOR1_FP659")));
        e.effects.add(List.of(new Effect("writeQword",0x0000000000470040L,0x00000000004b0000L), new Effect("writeQword",0x00000000004b0000L,0x00000001a6594100L)));
        e.sameStopEntry=new Entry(0x0000000140000000L, 0x0000000074033fb8L, new VolatileBits(0x9659100000000001L, 0x9659100000000002L, 0x9659100000000003L, 0x9659100000000008L, 0x9659100000000009L, 0x965910000000000aL, 0x965910000000000bL, new Bits128(0x9659100000000100L, 0x9659100000000200L), new Bits128(0x9659100000000101L, 0x9659100000000201L), new Bits128(0x9659100000000102L, 0x9659100000000202L), new Bits128(0x9659100000000103L, 0x9659100000000203L), new Bits128(0x9659100000000104L, 0x9659100000000204L), new Bits128(0x9659100000000105L, 0x9659100000000205L)), new NonvolatileBits(0xe659100000000001L, 0xe659100000000002L, 0xe659100000000003L, 0xe659100000000004L, 0xe659100000000005L, 0xe659100000000006L, 0xe659100000000007L, 0xe659100000000008L, new Bits128(0x6659665933333333L, 0x9659965944444444L)));
        e.sameSnapshot=new QueueFp604Api.Snapshot(e.sameStopEntry,0x000000000659beefL,false,e.fp.get("S_EXPLICIT_STOP_UNKNOWN659"));
        e.sameStop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,e.sameSnapshot,0,0x000000000372727bL);
        e.offers.add(e.sameStop);
        e.effects.add(List.of(new Effect("writeQword",0x00000000004c0008L,0xcc65910000000003L)));
        e.ram.put(9,new RamExpected(9,stoppedRam9()));
        e.ram.put(12,new RamExpected(12,stoppedRam12()));
        e.ram.put(18,new RamExpected(18,stoppedRam18()));
        e.ram.put(21,new RamExpected(21,stoppedRam21()));
        e.ram.put(25,new RamExpected(25,stoppedRam25()));
        e.ram.put(26,new RamExpected(26,stoppedRam26()));
        e.ram.put(29,new RamExpected(29,stoppedRam29()));
        e.ram.put(32,new RamExpected(32,stoppedRam32()));
        stoppedTrace(e);
        return e;
    }

    private static Map<Long,Byte> stoppedInitial() {
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d" +
                "231159a6010000006d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004059a601000000"),
                new Region(0x00000000004c0000L,
                "00000000105966550100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam9() {
        // S_BA-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6dbf717243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a6010000006d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d04000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004059a601000000"),
                new Region(0x00000000004c0000L,
                "00000000105966550100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam12() {
        // S_BA_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6dbf717243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a6010000006d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d04000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004059a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc0100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam18() {
        // budget-18
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6dbf717243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a60100000001000000001059b602000000001059b604000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004059a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc0100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam21() {
        // S_FIRST_DESTRUCTOR-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d7d727243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a60100000001000000001059b602000000001059b604000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004059a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc0100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam25() {
        // S_FIRST_DTOR_NORMAL659-offer
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d7d727243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a60100000001000000001059b602000000001059b604000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004b00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004159a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc0100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam26() {
        // budget-26
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d7d727243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a60100000001000000001059b602000000001059b604000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004b00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004159a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc0100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam29() {
        // S_SECOND_DESTRUCTOR_STOP-entry-after-owned-CALL-push
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d7d727243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a60100000001000000001059b602000000001059b604000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004b00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004159a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc0100000010596655"));
    }

    private static Map<Long,Byte> stoppedRam32() {
        // S_SECOND_DTOR_SAME_STOPPED659-offer
        return literalMap(
                new Region(0x0000000074033f88L,
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d7d727243010000006d6d6d6d6d6d6d6d" +
                "6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d06000000001059b605000000001059b608000000001059b607000000001059b603000000001059b6" +
                "231159a60100000001000000001059b602000000001059b604000000001059b66d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d6d"),
                new Region(0x0000000000450000L,
                "00000000000000000000000000000000000047000000000003000000030000000000000000000000554433220000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000460000L,
                "00000000000000000000000000000000000049000000000001000000010000000000000000000000998877660000000000000000000000000000000000000000" +
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                new Region(0x0000000000470000L,
                "00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d00004a00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d" +
                "00004b00000000004d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d"),
                new Region(0x0000000000490000L,
                "007059a6010000007d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d7d"),
                new Region(0x00000000004a0000L,
                "003159a601000000"),
                new Region(0x00000000004b0000L,
                "004159a601000000"),
                new Region(0x00000000004c0000L,
                "01000000009165cc03000000009165cc"));
    }

    private static void stoppedTrace(Expected e) {
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074034000L, 0xb659100000000003L, 0L, 0L, 0L)); // 1
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033ff8L, 0xb659100000000007L, 0L, 0L, 0L)); // 2
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033ff0L, 0xb659100000000008L, 0L, 0L, 0L)); // 3
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074034020L, 0xb659100000000004L, 0L, 0L, 0L)); // 4
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000046001cL, 1L, 0L, 0L, 0L)); // 5
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033fe8L, 0xb659100000000005L, 0L, 0L, 0L)); // 6
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033fe0L, 0xb659100000000006L, 0L, 0L, 0L)); // 7
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000460010L, 0x0000000000490000L, 0L, 0L, 0L)); // 8
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033fb8L, 0x00000001437271bfL, 0L, 0L, 0L)); // 9
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",0)); // 10
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000004c0000L, 0xcc65910000000001L, 0L, 0L, 0L)); // 11
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(0))); // 12
        e.trace.add(new Embedded32ByteFixture659.Event("R32", 0x000000000045001cL, 3L, 0L, 0L, 0L)); // 13
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074034010L, 0xb659100000000001L, 0L, 0L, 0L)); // 14
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074034018L, 0xb659100000000002L, 0L, 0L, 0L)); // 15
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000450010L, 0x0000000000470000L, 0L, 0L, 0L)); // 16
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000450010L, 0x0000000000470000L, 0L, 0L, 0L)); // 17
        e.trace.add(new ObservationExpected("BUDGET2","VALUE",new BudgetArgs(0x0000000003727273L,0x0000000000470020L))); // 18
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000470020L, 0x00000000004a0000L, 0L, 0L, 0L)); // 19
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x00000000004a0000L, 0x00000001a6593100L, 0L, 0L, 0L)); // 20
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033fb8L, 0x000000014372727dL, 0L, 0L, 0L)); // 21
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",1)); // 22
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000000470040L, 0x00000000004b0000L, 0L, 0L, 0L)); // 23
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000004b0000L, 0x00000001a6594100L, 0L, 0L, 0L)); // 24
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(1))); // 25
        e.trace.add(new ObservationExpected("BUDGET2","VALUE",new BudgetArgs(0x0000000003727273L,0x0000000000470040L))); // 26
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x0000000000470040L, 0x00000000004b0000L, 0L, 0L, 0L)); // 27
        e.trace.add(new Embedded32ByteFixture659.Event("R64", 0x00000000004b0000L, 0x00000001a6594100L, 0L, 0L, 0L)); // 28
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x0000000074033fb8L, 0x000000014372727dL, 0L, 0L, 0L)); // 29
        e.trace.add(new ObservationExpected("CALL_ENTER","FRAME",2)); // 30
        e.trace.add(new Embedded32ByteFixture659.Event("W64", 0x00000000004c0008L, 0xcc65910000000003L, 0L, 0L, 0L)); // 31
        e.trace.add(new ObservationExpected("CALL_OFFER","SAME",e.offers.get(2))); // 32
    }

}
