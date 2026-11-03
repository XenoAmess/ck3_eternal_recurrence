package org.xar.ck3.research.m3.fa90deep273;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90Fp267Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.callee68fcfp268.Callee68fcFp268Api;
import org.xar.ck3.research.m3.tail6670fp271.Tail6670Fp271Api;
import org.xar.ck3.research.m3.callee68fcfp268.Callee68fcFromFa90268;
import org.xar.ck3.research.m3.callee68d4fp269.Callee68d4From68fc269;
import org.xar.ck3.research.m3.b374fp270.B374Fp270Api;
import org.xar.ck3.research.m3.b374fp270.B374FromFa90270;
import org.xar.ck3.research.m3.tail6670fp271.Tail6670FromFa90271;
import org.xar.ck3.research.m3.tail6874fp272.Tail6874From6670272;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.research.m3.fa90fp267.Fa90FullState267;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Two finite direct267 deep public-DATA witnesses using existing268/269,270,271/272.
 * Oracle 5dfacbab374a46a6f2592068866c9c335814f540bf0db70dacbeb01ba7739826
 * was sealed before this author read selected bindKnown. The model method had already
 * been generated; the seal is not claimed to predate generation. Existing production
 * sources were visible: this witness is candidate-visible/source-derived, not wholeblind.
 * The selected1538byte method below is unchanged, including comments/format/LF.
 * All RAM/global contents and remaining lower Outcomes are explicit artificial DATA.
 * 270's E364/425689C remain opaque. No higher263/264/265/F82D acceptance or future274 use.
 * All original PC paths are source facts only; the public ports do not trace instruction PCs.
 * Internal oracle frames are source-derived; runtime frame assertions cover the two
 * public remaining270 callbacks, plus exact whole memory trace and complete root result.
 * No Native/loaded/RF/UW/hardware/RFLAGS/upperYMM/Game or performance proof.
 */
public final class Fa90DeepKnown273Manual {
    private Fa90DeepKnown273Manual() { }
    private static Fa90Fp267Api.Calls bindKnown(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget, B374Fp270Api.Calls remaining) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(remaining);

        // 1. Bind 269 (Callee68d4) to 268 (Callee68fc) context
        Callee68fcFp268Api.Calls calls268 = Callee68d4From68fc269.bind(memory, budget);

        // 2. Bind 272 (Tail6874) to 271 (Tail6670) context
        Tail6670Fp271Api.Calls calls271 = Tail6874From6670272.bind(memory, budget);

        // 3. Define the bottom foreign267 that throws on any escaped frame
        Fa90Fp267Api.Calls foreign267 = new Fa90Fp267Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(Fa90Fp267Api.CallFrame frame) {
                throw new AssertionError("Unexpected escaped Fa90 call frame");
            }
        };

        // 4. Bind 271 (Tail6670) to 267 (Fa90) context, routing 424FAE7 to 271
        Fa90Fp267Api.Calls calls267_step1 = Tail6670FromFa90271.bind(memory, budget, calls271, foreign267);

        // 5. Bind 270 (B374) to 267 (Fa90) context, routing 424FAD3 to 270
        Fa90Fp267Api.Calls calls267_step2 = B374FromFa90270.bind(memory, budget, remaining, calls267_step1);

        // 6. Bind 268 (Callee68fc) to 267 (Fa90) context, routing 424FAAC to 268
        Fa90Fp267Api.Calls calls267_final = Callee68fcFromFa90268.bind(memory, budget, calls268, calls267_step2);

        return calls267_final;
    }
    private static final long IMAGE = 0x0000000180000000L;
    private static final long ENTRY_SP = 0x0000000000058808L;
    private static final String INITIAL_RAM_SHA256 = "243fb26e99459f8c6c4e1f324ff2eb310c37890a5623185ef13e16831a8289a2";
    private static final String PREFIX_RAM_SHA256 = "b4c040531dbc217606046bd3234ec09b51a022c65abd9031e217de75ca4bd564";
    private static final String NORMAL_RAM_SHA256 = "6446411d3907eb67a392ce4208e1390900fdaf5f7b5ec7204f54ef7824dabac7";
    private static final VolatileBits INPUT_V = new VolatileBits(
        0x1122334455667788L, 0x0000000000053000L, 0x0000000000056000L, 0x91A2B3C4D5E6F708L, 0xA2B3C4D5E6F70819L, 0xB3C4D5E6F708192AL, 0xC4D5E6F708192A3BL,
        new Bits128(0x1425000000000000L, 0x2536000000000000L),
        new Bits128(0x1426020304050607L, 0x253906090C0F1215L),
        new Bits128(0x14270406080A0C0EL, 0x253C0C12181E242AL),
        new Bits128(0x142806090C0F1215L, 0x253F121B242D363FL),
        new Bits128(0x1429080C1014181CL, 0x25421824303C4854L),
        new Bits128(0x142A0A0F14191E23L, 0x25451E2D3C4B5A69L));
    private static final VolatileBits CALL_V = new VolatileBits(
        0x0000000000000000L, 0x0000000000057000L, 0x000000018542F498L, 0x0000000000000000L, 0x00000000FFFFFFFFL, 0xB3C4D5E6F708192AL, 0xC4D5E6F708192A3BL,
        new Bits128(0x1425000000000000L, 0x2536000000000000L),
        new Bits128(0x1426020304050607L, 0x253906090C0F1215L),
        new Bits128(0x14270406080A0C0EL, 0x253C0C12181E242AL),
        new Bits128(0x142806090C0F1215L, 0x253F121B242D363FL),
        new Bits128(0x1429080C1014181CL, 0x25421824303C4854L),
        new Bits128(0x142A0A0F14191E23L, 0x25451E2D3C4B5A69L));
    private static final VolatileBits TAIL_V = new VolatileBits(
        0x000000018542F498L, 0x0000000000055000L, 0xC328292A2B2C2D2EL, 0xD4393A3B3C3D3E3FL, 0xE54A4B4C5D5E6F70L, 0xF65B5C5D6E6F7081L, 0x776C6D6E7F809192L,
        new Bits128(0x3647000000000000L, 0x4758000000000000L),
        new Bits128(0x3648020304050607L, 0x475B06090C0F1215L),
        new Bits128(0x36490406080A0C0EL, 0x475E0C12181E242AL),
        new Bits128(0x364A06090C0F1215L, 0x4761121B242D363FL),
        new Bits128(0x364B080C1014181CL, 0x47641824303C4854L),
        new Bits128(0x364C0A0F14191E23L, 0x47671E2D3C4B5A69L));
    private static final VolatileBits POST_CALL_V = new VolatileBits(
        0xA1060708090A0B0CL, 0xB21718191A1B1C1DL, 0xC328292A2B2C2D2EL, 0xD4393A3B3C3D3E3FL, 0xE54A4B4C5D5E6F70L, 0xF65B5C5D6E6F7081L, 0x776C6D6E7F809192L,
        new Bits128(0x3647000000000000L, 0x4758000000000000L),
        new Bits128(0x3648020304050607L, 0x475B06090C0F1215L),
        new Bits128(0x36490406080A0C0EL, 0x475E0C12181E242AL),
        new Bits128(0x364A06090C0F1215L, 0x4761121B242D363FL),
        new Bits128(0x364B080C1014181CL, 0x47641824303C4854L),
        new Bits128(0x364C0A0F14191E23L, 0x47671E2D3C4B5A69L));
    private static final VolatileBits POST_TAIL_V = new VolatileBits(
        0x18293A4B5C6D7E8FL, 0x293A4B5C6D7E8F90L, 0x3A4B5C6D7E8F90A1L, 0x4B5C6D7E8F90A1B2L, 0xD1E2F30415263748L, 0x6D7E8F90A1B2C3D4L, 0x7E8F90A1B2C3D4E5L,
        new Bits128(0x5869000000000000L, 0x697A000000000000L),
        new Bits128(0x586A020304050607L, 0x697D06090C0F1215L),
        new Bits128(0x586B0406080A0C0EL, 0x69800C12181E242AL),
        new Bits128(0x586C06090C0F1215L, 0x6983121B242D363FL),
        new Bits128(0x586D080C1014181CL, 0x69861824303C4854L),
        new Bits128(0x586E0A0F14191E23L, 0x69891E2D3C4B5A69L));
    private static final VolatileBits ROOT_V = new VolatileBits(
        0x0000000000000000L, 0x0000000000058000L, 0x000000018542F498L, 0x0000000000000000L, 0xD1E2F30415263748L, 0x6D7E8F90A1B2C3D4L, 0x7E8F90A1B2C3D4E5L,
        new Bits128(0x5869000000000000L, 0x697A000000000000L),
        new Bits128(0x586A020304050607L, 0x697D06090C0F1215L),
        new Bits128(0x586B0406080A0C0EL, 0x69800C12181E242AL),
        new Bits128(0x586C06090C0F1215L, 0x6983121B242D363FL),
        new Bits128(0x586D080C1014181CL, 0x69861824303C4854L),
        new Bits128(0x586E0A0F14191E23L, 0x69891E2D3C4B5A69L));
    private static final VolatileBits STOP_V = new VolatileBits(
        0x8192A3B4C5D6E7F8L, 0x92A3B4C5D6E7F809L, 0xA3B4C5D6E7F8091AL, 0xB4C5D6E7F8091A2BL, 0xC5D6E7F8091A2B3CL, 0xD6E7F8091A2B3C4DL, 0xE7F8091A2B3C4D5EL,
        new Bits128(0x7A8B000000000000L, 0x8B9C000000000000L),
        new Bits128(0x7A8C020304050607L, 0x8B9F06090C0F1215L),
        new Bits128(0x7A8D0406080A0C0EL, 0x8BA20C12181E242AL),
        new Bits128(0x7A8E06090C0F1215L, 0x8BA5121B242D363FL),
        new Bits128(0x7A8F080C1014181CL, 0x8BA81824303C4854L),
        new Bits128(0x7A900A0F14191E23L, 0x8BAB1E2D3C4B5A69L));
    private static final NonvolatileBits INPUT_N = new NonvolatileBits(
        0xD011223344556677L, 0xD122334455667788L, 0xD233445566778899L, 0xD3445566778899AAL, 0xD45566778899AABBL, 0xD566778899AABBCCL, 0xD6778899AABBCCDDL, 0xD78899AABBCCDDEEL,
        new Bits128(0x9CABBDCEDFE00112L, 0xADBECDDCEBFA0918L));
    private static final NonvolatileBits CALL_N = new NonvolatileBits(
        0x0000000000055000L, 0xD122334455667788L, 0xD233445566778899L, 0x0000000000053000L, 0xD45566778899AABBL, 0xD566778899AABBCCL, 0xD6778899AABBCCDDL, 0xD78899AABBCCDDEEL,
        new Bits128(0x9CABBDCEDFE00112L, 0xADBECDDCEBFA0918L));
    private static final NonvolatileBits TAIL_N = new NonvolatileBits(
        0x0000000000056000L, 0xD122334455667788L, 0xD233445566778899L, 0x0000000000053000L, 0xD45566778899AABBL, 0xD566778899AABBCCL, 0xD6778899AABBCCDDL, 0xD78899AABBCCDDEEL,
        new Bits128(0x9CABBDCEDFE00112L, 0xADBECDDCEBFA0918L));
    private static final NonvolatileBits STOP_N = new NonvolatileBits(
        0x0A1B2C3D4E5F6071L, 0x1B2C3D4E5F607182L, 0xD233445566778899L, 0xD3445566778899AAL, 0xD45566778899AABBL, 0xD566778899AABBCCL, 0xD6778899AABBCCDDL, 0xD78899AABBCCDDEEL,
        new Bits128(0x9CABBDCEDFE00112L, 0xADBECDDCEBFA0918L));
    private static final QueueFp604Api.Mxcsr P0 = new QueueFp604Api.Mxcsr(0x0401, 0xC4C5);
    private static final QueueFp604Api.Mxcsr P1 = new QueueFp604Api.Mxcsr(0x8004, 0xA8C5);
    private static final QueueFp604Api.Mxcsr P2 = new QueueFp604Api.Mxcsr(0x0140, 0x6345);
    private static final QueueFp604Api.Mxcsr PS = new QueueFp604Api.Mxcsr(0x0201, 0xA205);

    // Literal79-event oracle; sublists end at frozen38/54-event boundaries, not SUT results.
    private static final List<String> EXPECTED_NORMAL_TRACE = List.of(
        "W64 0000000000058810 D011223344556677",
        "W64 0000000000058800 D3445566778899AA",
        "R64 0000000000053090 0000000000055000",
        "W64 00000000000587D8 000000018424FAB1",
        "X32 0000000000055010 FFFFFFFF 00000001 00000000",
        "R64 00000000000550E0 0000000000000000",
        "R64 00000000000550F0 0000000000000000",
        "R64 00000000000550E8 0000000000000000",
        "R64 0000000000055100 0000000000000000",
        "R64 0000000000055028 000000018542F498",
        "R64 0000000000055020 0000000000000000",
        "R64 0000000000055048 000000018542F498",
        "R64 0000000000055040 0000000000000000",
        "R64 0000000000055068 000000018542F498",
        "R64 0000000000055060 0000000000000000",
        "R64 0000000000055088 000000018542F498",
        "R64 0000000000055080 0000000000000000",
        "R64 00000000000550A8 000000018542F498",
        "R64 00000000000550A0 0000000000000000",
        "R64 00000000000550C8 000000018542F498",
        "R64 00000000000550C0 0000000000000000",
        "R64 0000000000055120 0000000000057000",
        "W64 00000000000587A8 000000018425699F",
        "X32 000000000005715C FFFFFFFF 00000000 FFFFFFFF",
        "R64 00000000000587A8 000000018425699F",
        "R64 00000000000587D8 000000018424FAB1",
        "R64 0000000000053090 0000000000055000",
        "R64 0000000185C5DCD8 0000000000056000",
        "R32 0000000000055010 00000000",
        "W64 00000000000587D8 000000018424FAD8",
        "W64 00000000000587E0 0000000000056000",
        "W64 00000000000587E8 D122334455667788",
        "W64 00000000000587F0 D233445566778899",
        "W64 00000000000587D0 0000000000053000",
        "R64 00000000000550F8 0000000000000000",
        "R64 0000000000055100 0000000000000000",
        "R64 0000000000055120 0000000000057000",
        "W64 00000000000587A8 00000001842567F7",
        "R64 0000000000055028 000000018542F498",
        "R64 0000000000055020 0000000000000000",
        "R64 0000000000055048 000000018542F498",
        "R64 0000000000055040 0000000000000000",
        "R64 0000000000055068 000000018542F498",
        "R64 0000000000055060 0000000000000000",
        "R64 0000000000055088 000000018542F498",
        "R64 0000000000055080 0000000000000000",
        "R64 00000000000550A8 000000018542F498",
        "R64 00000000000550A0 0000000000000000",
        "R64 00000000000550C8 000000018542F498",
        "R64 00000000000550C0 0000000000000000",
        "R64 00000000000587E0 0000000000056000",
        "R64 00000000000587E8 D122334455667788",
        "R64 00000000000587F0 D233445566778899",
        "R64 00000000000587D0 0000000000053000",
        "W64 0000000000053090 0000000000056000",
        "W64 00000000000587D8 000000018424FAEC",
        "X32 0000000000056010 00000001 FFFFFFFE FFFFFFFF",
        "R64 00000000000560E0 0000000000000000",
        "R64 00000000000560F0 0000000000000000",
        "R64 00000000000560E8 0000000000000000",
        "R64 0000000000056100 0000000000000000",
        "R64 0000000000056028 000000018542F498",
        "R64 0000000000056020 0000000000000000",
        "R64 0000000000056048 000000018542F498",
        "R64 0000000000056040 0000000000000000",
        "R64 0000000000056068 000000018542F498",
        "R64 0000000000056060 0000000000000000",
        "R64 0000000000056088 000000018542F498",
        "R64 0000000000056080 0000000000000000",
        "R64 00000000000560A8 000000018542F498",
        "R64 00000000000560A0 0000000000000000",
        "R64 00000000000560C8 000000018542F498",
        "R64 00000000000560C0 0000000000000000",
        "R64 0000000000056120 0000000000058000",
        "X32 000000000005815C 00000001 FFFFFFFF 00000000",
        "R64 00000000000587D8 000000018424FAEC",
        "R64 0000000000058810 D011223344556677",
        "R64 0000000000058800 D3445566778899AA",
        "R64 0000000000058808 1020304050607080"
    );
    private static final List<String> EXPECTED_STOP_TRACE = EXPECTED_NORMAL_TRACE.subList(0, 38);
    private static final List<String> EXPECTED_TAIL_TRACE = EXPECTED_NORMAL_TRACE.subList(0, 54);

    public static void main(String[] args) {
        runCase(false);
        runCase(true);
        System.out.print("Fa90DeepKnown273Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean stoppedMode) {
        Fixture fixture = new Fixture(stoppedMode);
        Checks.equal(INITIAL_RAM_SHA256, fixture.ram.serializedSha256(), "initial whole RAM");
        Checks.equal(List.of(), fixture.ram.traceSnapshot(), "unlogged DATA setup");
        GovernmentCrtBoundary185Api.LoopBudget budget = (site, address) -> {
            fixture.budgetCalls++;
            throw new AssertionError("Unexpected public budget callback");
        };
        Fa90Fp267Api.Calls known = bindKnown(fixture.ram, budget, fixture);
        Checks.equal(List.of(), fixture.ram.traceSnapshot(), "composition must not touch RAM");
        Checks.equal(INITIAL_RAM_SHA256, fixture.ram.serializedSha256(), "composition retains bytes");
        Checks.equal(0, fixture.ram.atomicCallCount(), "composition must not perform atomics");
        Checks.equal(0, fixture.budgetCalls, "composition must not invoke budget");
        QueueFp604Api.Input input = new QueueFp604Api.Input(new FullCopy437Api.Input(
            new GovernmentCrtBoundary185Api.Entry(IMAGE, ENTRY_SP, INPUT_V, INPUT_N), true, budget), P0);

        QueueFp604Api.Outcome actual = Fa90FullState267.execute(input, fixture.ram, known);
        Checks.equal(1, fixture.callCount, "one reached opaque270 CALL");
        Checks.equal(0, fixture.budgetCalls, "no public budget steps");
        if (stoppedMode) {
            Checks.same(fixture.firstOffer, actual, "opaque Stopped exact root identity");
            Checks.equal(0, fixture.tailCount, "Stopped has no later opaque tail");
            Checks.equal(2, fixture.ram.atomicCallCount(), "Stopped original prefix atomics");
            Checks.equal(EXPECTED_STOP_TRACE, fixture.ram.traceSnapshot(), "Stopped exact memory prefix");
            Checks.equal(PREFIX_RAM_SHA256, fixture.ram.serializedSha256(), "Stopped whole RAM");
            if (!(actual instanceof QueueFp604Api.Stopped stopped)) {
                throw new AssertionError("Expected exact explicit opaque Stopped");
            }
            Checks.equal(QueueFp604Api.StopReason.MISSING_POST_STATE, stopped.reason(), "stop reason");
            Checks.equal(new GovernmentCrtBoundary185Api.Entry(
                IMAGE, 0x00000000000587A8L, STOP_V, STOP_N),
                stopped.snapshot().currentState(), "complete supplied opaque stop state");
            Checks.bits(0x000000000425689CL, stopped.snapshot().instructionRva(), "stop instruction DATA");
            Checks.equal(false, stopped.snapshot().directionFlagSet(), "supplied stop DF");
            Checks.same(PS, stopped.snapshot().mxcsr(), "supplied stop partialFP identity");
            Checks.equal(0, stopped.raisedConditionBits(), "supplied stop condition DATA");
            Checks.bits(0x00000000042567F2L, stopped.originCallSiteRva(), "supplied stop origin DATA");
        } else {
            Checks.equal(1, fixture.tailCount, "one reached opaque270 tail");
            Checks.equal(4, fixture.ram.atomicCallCount(), "four actual known-child atomics");
            Checks.equal(EXPECTED_NORMAL_TRACE, fixture.ram.traceSnapshot(), "Normal exact memory transcript");
            Checks.equal(NORMAL_RAM_SHA256, fixture.ram.serializedSha256(), "Normal whole RAM");
            if (!(actual instanceof QueueFp604Api.Normal normal)) {
                throw new AssertionError("Expected root Normal after actual known272");
            }
            Checks.equal(new GovernmentCrtBoundary185Api.NormalReturn(
                ROOT_V, 0x1020304050607080L, 0x0000000000058810L, INPUT_N),
                normal.base().normalReturn(), "complete actual root V/N/RIP/SP");
            Checks.equal(true, normal.base().postDirectionFlagSet(), "actual final DF");
            Checks.same(P2, normal.postMxcsr(), "same opaque-tail P2 through known271/272");
        }
    }

    private static final class Fixture implements B374Fp270Api.Calls {
        private final boolean stoppedMode;
        private final Ram ram = new Ram();
        private final QueueFp604Api.Outcome firstOffer;
        private final QueueFp604Api.Normal tailOffer;
        private int callCount;
        private int tailCount;
        private int budgetCalls;

        private Fixture(boolean stoppedMode) {
            this.stoppedMode = stoppedMode;
            if (stoppedMode) {
                firstOffer = new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                    new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                        IMAGE, 0x00000000000587A8L, STOP_V, STOP_N),
                        0x000000000425689CL, false, PS),
                    0, 0x00000000042567F2L);
            } else {
                firstOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                    new GovernmentCrtBoundary185Api.NormalReturn(
                        POST_CALL_V, 0x00000001842567F7L,
                        0x00000000000587B0L, CALL_N), false), P1);
            }
            tailOffer = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                    POST_TAIL_V, 0x000000018424FAD8L,
                    0x00000000000587E0L, TAIL_N), true), P2);
        }

        @Override public QueueFp604Api.Outcome invoke(B374Fp270Api.CallFrame frame) {
            callCount++;
            Checks.equal(1, callCount, "one actual mandatory B374 CALL");
            Checks.equal(new GovernmentCrtBoundary185Api.Call(
                0x00000000042567F2L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x000000000425689CL, 0x00000000000587B0L, CALL_V, CALL_N),
                frame.original(), "complete actual mandatory CALL frame");
            Checks.equal(new GovernmentCrtBoundary185Api.Entry(
                IMAGE, 0x00000000000587A8L, CALL_V, CALL_N),
                frame.childEntry(), "complete actual mandatory child entry");
            Checks.bits(0x00000001842567F7L, frame.returnRipBits(), "mandatory owned RIP");
            Checks.equal(true, frame.directionFlagSet(), "actual pre-call DF");
            Checks.same(P0, frame.preMxcsr(), "actual pre-call partialFP identity");
            Checks.equal(EXPECTED_STOP_TRACE, ram.traceSnapshot(), "exact prefix before opaque CALL");
            Checks.equal(2, ram.atomicCallCount(), "known268/269 atomics before opaque CALL");
            Checks.equal(PREFIX_RAM_SHA256, ram.serializedSha256(), "whole RAM at opaque CALL");
            return firstOffer; // Complete immutable public DATA, no lower algorithm or RAM edits.
        }

        @Override public QueueFp604Api.Outcome tail(B374Fp270Api.TailFrame frame) {
            if (stoppedMode) throw new AssertionError("Stopped prefix reached later opaque tail");
            tailCount++;
            Checks.equal(1, callCount, "mandatory CALL precedes tail");
            Checks.equal(1, tailCount, "one actual opaque tail");
            Checks.equal(new GovernmentCrtBoundary185Api.Tail(
                0x000000000425686DL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                0x000000000424E364L, new GovernmentCrtBoundary185Api.Entry(
                    IMAGE, 0x00000000000587D8L, TAIL_V, TAIL_N)),
                frame.original(), "complete fresh restored B374 tail frame");
            Checks.equal(false, frame.directionFlagSet(), "accepted first-offer DF at tail");
            Checks.same(P1, frame.preMxcsr(), "same accepted first-offer partialFP at tail");
            Checks.equal(EXPECTED_TAIL_TRACE, ram.traceSnapshot(), "exact54-event pre-tail transcript");
            Checks.equal(2, ram.atomicCallCount(), "no opaque or row atomics");
            Checks.equal(PREFIX_RAM_SHA256, ram.serializedSha256(), "whole RAM at opaque tail");
            return tailOffer; // Explicit parent-owned RIP DATA; E364 remains foreign.
        }
    }

    /**
     * Mechanical widths/log/hash reuse this author's268 host6005B only.
     * All273 regions, fills,66patches,79events, tuples and offers are new frozen DATA.
     * Artificial low32768 plus global8 serialize without headers; no Native content read.
     */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long LOW_BASE = 0x0000000000051000L;
        private static final int LOW_SIZE = 32768;
        private static final long HIGH_BASE = 0x0000000185C5DCD8L;
        private static final int HIGH_SIZE = 8;
        private final byte[] bytes = new byte[LOW_SIZE + HIGH_SIZE];
        private final List<String> events = new ArrayList<>();
        private int atomicCalls;

        private Ram() {
            for (int i = 0; i < LOW_SIZE; i++) bytes[i] = (byte) (i * 13 + 0x47);
            for (int i = 0; i < HIGH_SIZE; i++) bytes[LOW_SIZE + i] = (byte) (i * 19 + 0x3D);
            put64(0x0000000000058808L, 0x1020304050607080L);
            put64(0x0000000000053090L, 0x0000000000055000L);
            put64(0x0000000185C5DCD8L, 0x0000000000056000L);
            put32(0x0000000000055010L, 0x00000001);
            put32(0x0000000000056010L, 0xFFFFFFFE);
            put64(0x00000000000550E0L, 0x0000000000000000L);
            put64(0x00000000000550F0L, 0x0000000000000000L);
            put64(0x00000000000550E8L, 0x0000000000000000L);
            put64(0x0000000000055100L, 0x0000000000000000L);
            put64(0x0000000000055020L, 0x0000000000000000L);
            put64(0x0000000000055028L, 0x000000018542F498L);
            put64(0x0000000000055030L, 0xDEAD00000005A000L);
            put64(0x0000000000055038L, 0xBEEF00000005B000L);
            put64(0x0000000000055040L, 0x0000000000000000L);
            put64(0x0000000000055048L, 0x000000018542F498L);
            put64(0x0000000000055050L, 0xDEAD00000005A040L);
            put64(0x0000000000055058L, 0xBEEF00000005B040L);
            put64(0x0000000000055060L, 0x0000000000000000L);
            put64(0x0000000000055068L, 0x000000018542F498L);
            put64(0x0000000000055070L, 0xDEAD00000005A080L);
            put64(0x0000000000055078L, 0xBEEF00000005B080L);
            put64(0x0000000000055080L, 0x0000000000000000L);
            put64(0x0000000000055088L, 0x000000018542F498L);
            put64(0x0000000000055090L, 0xDEAD00000005A0C0L);
            put64(0x0000000000055098L, 0xBEEF00000005B0C0L);
            put64(0x00000000000550A0L, 0x0000000000000000L);
            put64(0x00000000000550A8L, 0x000000018542F498L);
            put64(0x00000000000550B0L, 0xDEAD00000005A100L);
            put64(0x00000000000550B8L, 0xBEEF00000005B100L);
            put64(0x00000000000550C0L, 0x0000000000000000L);
            put64(0x00000000000550C8L, 0x000000018542F498L);
            put64(0x00000000000550D0L, 0xDEAD00000005A140L);
            put64(0x00000000000550D8L, 0xBEEF00000005B140L);
            put64(0x00000000000560E0L, 0x0000000000000000L);
            put64(0x00000000000560F0L, 0x0000000000000000L);
            put64(0x00000000000560E8L, 0x0000000000000000L);
            put64(0x0000000000056100L, 0x0000000000000000L);
            put64(0x0000000000056020L, 0x0000000000000000L);
            put64(0x0000000000056028L, 0x000000018542F498L);
            put64(0x0000000000056030L, 0xDEAD00000005B000L);
            put64(0x0000000000056038L, 0xBEEF00000005C000L);
            put64(0x0000000000056040L, 0x0000000000000000L);
            put64(0x0000000000056048L, 0x000000018542F498L);
            put64(0x0000000000056050L, 0xDEAD00000005B040L);
            put64(0x0000000000056058L, 0xBEEF00000005C040L);
            put64(0x0000000000056060L, 0x0000000000000000L);
            put64(0x0000000000056068L, 0x000000018542F498L);
            put64(0x0000000000056070L, 0xDEAD00000005B080L);
            put64(0x0000000000056078L, 0xBEEF00000005C080L);
            put64(0x0000000000056080L, 0x0000000000000000L);
            put64(0x0000000000056088L, 0x000000018542F498L);
            put64(0x0000000000056090L, 0xDEAD00000005B0C0L);
            put64(0x0000000000056098L, 0xBEEF00000005C0C0L);
            put64(0x00000000000560A0L, 0x0000000000000000L);
            put64(0x00000000000560A8L, 0x000000018542F498L);
            put64(0x00000000000560B0L, 0xDEAD00000005B100L);
            put64(0x00000000000560B8L, 0xBEEF00000005C100L);
            put64(0x00000000000560C0L, 0x0000000000000000L);
            put64(0x00000000000560C8L, 0x000000018542F498L);
            put64(0x00000000000560D0L, 0xDEAD00000005B140L);
            put64(0x00000000000560D8L, 0xBEEF00000005C140L);
            put64(0x00000000000550F8L, 0x0000000000000000L);
            put64(0x0000000000055120L, 0x0000000000057000L);
            put64(0x0000000000056120L, 0x0000000000058000L);
            put32(0x000000000005715CL, 0x00000000);
            put32(0x000000000005815CL, 0xFFFFFFFF);
        }

        private int index(long address, int width) {
            if (width <= 0) throw new AssertionError("Invalid RAM width");
            if (address >= LOW_BASE && address - LOW_BASE <= LOW_SIZE - width) {
                return (int) (address - LOW_BASE);
            }
            if (address >= HIGH_BASE && address - HIGH_BASE <= HIGH_SIZE - width) {
                return LOW_SIZE + (int) (address - HIGH_BASE);
            }
            throw new AssertionError("Unmapped artificial RAM address " + hex64(address) + " width " + width);
        }

        private long rawRead(long address, int width) {
            int start = index(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) value |= (long) (bytes[start + i] & 0xFF) << (i * 8);
            return value;
        }

        private void rawWrite(long address, long value, int width) {
            int start = index(address, width);
            for (int i = 0; i < width; i++) bytes[start + i] = (byte) (value >>> (i * 8));
        }

        private void put32(long address, int value) { rawWrite(address, value, 4); }
        private void put64(long address, long value) { rawWrite(address, value, 8); }

        @Override public long readQword(long address) {
            long value = rawRead(address, 8);
            events.add("R64 " + hex64(address) + " " + hex64(value));
            return value;
        }

        @Override public int readDword(long address) {
            int value = (int) rawRead(address, 4);
            events.add("R32 " + hex64(address) + " " + hex32(value));
            return value;
        }

        @Override public int readUnsignedByte(long address) {
            int value = (int) rawRead(address, 1);
            events.add("R8 " + hex64(address) + " " + hex32(value));
            return value;
        }

        @Override public int readUnsignedWord(long address) {
            int value = (int) rawRead(address, 2);
            events.add("R16 " + hex64(address) + " " + hex32(value));
            return value;
        }

        @Override public void writeQword(long address, long value) {
            rawWrite(address, value, 8);
            events.add("W64 " + hex64(address) + " " + hex64(value));
        }

        @Override public void writeDword(long address, int value) {
            rawWrite(address, value, 4);
            events.add("W32 " + hex64(address) + " " + hex32(value));
        }

        @Override public void writeByte(long address, int value) {
            rawWrite(address, value, 1);
            events.add("W8 " + hex64(address) + " " + hex32(value & 0xFF));
        }

        @Override public void writeWord(long address, int value) {
            rawWrite(address, value, 2);
            events.add("W16 " + hex64(address) + " " + hex32(value & 0xFFFF));
        }

        @Override public synchronized int lockedXaddDword(long address, int delta) {
            int old = (int) rawRead(address, 4);
            int updated = old + delta;
            rawWrite(address, updated, 4);
            atomicCalls++;
            events.add("X32 " + hex64(address) + " " + hex32(delta)
                + " " + hex32(old) + " " + hex32(updated));
            return old;
        }

        private Bits128 raw128(long address) {
            index(address, 16);
            return new Bits128(rawRead(address, 8), rawRead(address + 8, 8));
        }

        private void put128(long address, Bits128 value) {
            index(address, 16);
            rawWrite(address, value.lowBits(), 8);
            rawWrite(address + 8, value.highBits(), 8);
        }

        private static String bits128(Bits128 value) {
            return hex64(value.lowBits()) + " " + hex64(value.highBits());
        }

        @Override public Bits128 read128(long address) {
            Bits128 value = raw128(address);
            events.add("R128 " + hex64(address) + " " + bits128(value));
            return value;
        }

        @Override public void write128(long address, Bits128 value) {
            put128(address, value);
            events.add("W128 " + hex64(address) + " " + bits128(value));
        }

        @Override public void write128NonTemporal(long address, Bits128 value) {
            put128(address, value);
            events.add("W128NT " + hex64(address) + " " + bits128(value));
        }

        @Override public FullCopy437Api.Bits256 read256(long address) {
            index(address, 32);
            FullCopy437Api.Bits256 value =
                new FullCopy437Api.Bits256(raw128(address), raw128(address + 16));
            events.add("R256 " + hex64(address) + " " + bits128(value.low()) + " " + bits128(value.high()));
            return value;
        }

        private void put256(long address, FullCopy437Api.Bits256 value) {
            index(address, 32);
            put128(address, value.low());
            put128(address + 16, value.high());
        }

        @Override public void write256(long address, FullCopy437Api.Bits256 value) {
            put256(address, value);
            events.add("W256 " + hex64(address) + " " + bits128(value.low()) + " " + bits128(value.high()));
        }

        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) {
            put256(address, value);
            events.add("W256NT " + hex64(address) + " " + bits128(value.low()) + " " + bits128(value.high()));
        }

        @Override public void sfence() {
            events.add("SFENCE"); // Separate host token; no hardware fence proof.
        }

        private int atomicCallCount() { return atomicCalls; }
        private List<String> traceSnapshot() { return List.copyOf(events); }
        private byte[] serializedSnapshot() { return bytes.clone(); }

        private String serializedSha256() {
            try {
                byte[] digest = MessageDigest.getInstance("SHA-256").digest(serializedSnapshot());
                StringBuilder result = new StringBuilder(64);
                for (byte value : digest) result.append(String.format(Locale.ROOT, "%02x", value & 0xFF));
                return result.toString();
            } catch (NoSuchAlgorithmException impossible) {
                throw new AssertionError(impossible);
            }
        }

        private static String hex64(long value) {
            return String.format(Locale.ROOT, "%016X", value);
        }

        private static String hex32(int value) {
            return String.format(Locale.ROOT, "%08X", value);
        }
    }

    private static final class Checks {
        private Checks() { }
        private static void equal(Object expected, Object actual, String label) {
            if (!Objects.equals(expected, actual)) {
                throw new AssertionError(label + ": expected " + expected + ", actual " + actual);
            }
        }
        private static void same(Object expected, Object actual, String label) {
            if (expected != actual) throw new AssertionError(label + ": identity differs");
        }
        private static void bits(long expected, long actual, String label) {
            if (expected != actual) {
                throw new AssertionError(label + ": expected " + Long.toUnsignedString(expected, 16)
                    + ", actual " + Long.toUnsignedString(actual, 16));
            }
        }
    }
}
