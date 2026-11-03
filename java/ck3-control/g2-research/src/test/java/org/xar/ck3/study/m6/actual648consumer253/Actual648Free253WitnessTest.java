package org.xar.ck3.study.m6.actual648consumer253;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.DefaultReleaseWithFp648;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.postfree253.DefaultFreePost253;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;
import org.xar.ck3.study.m6.postvtable247.PostVtableForward247;

/**
 * Two new actual247 -> actual648 release ->253 -> actual251 composed witnesses.
 * Authored source-only; later software validation is recorded separately. No native/FP claim.
 * Synthetic getter/lower full outcomes and all RAM effects are explicit in the frozen contract.
 */
public final class Actual648Free253WitnessTest {
    private Actual648Free253WitnessTest() { }

    private static final long I = 0x140000000L;
    private static final long O = 0xD008L, P247 = 0xCFE0L, S251 = 0xCFD8L;
    private static final long P251 = 0xCFB0L, C251 = 0xCFA8L;
    private static final long ROOT = 0xB253000L, ROOT_VTABLE = 0xB253080L;
    private static final long BLOCK = 0xB253100L, OBJECT = 0xB253200L, RESULT_VTABLE = 0xB253280L;
    private static final long HEAP = 0xB253300L, CELL = 0xB253400L, PAYLOAD = 0xB253900L;
    private static final long GETTER_TARGET = 0xBAD25300L;
    private static final long LOWER0_TARGET = 0xBAD25301L, LOWER2_TARGET = 0xBAD25302L;
    private static final long SCRIPT_RBX = 0xA253B0L, SCRIPT_RDI = 0xA253D1L, SCRIPT_RET = 0xA253CA11L;

    private record Env(boolean df, QueueFp604Api.Mxcsr mx) { }
    private static final Env INPUT_ENV = new Env(true, new QueueFp604Api.Mxcsr(0, 0));
    private static final Env E0 = new Env(true, new QueueFp604Api.Mxcsr(0x4000, 0xFFC0));
    private static final Env E1 = new Env(false, new QueueFp604Api.Mxcsr(0x4001, 0xFFFF));
    private static final Env E2 = new Env(true, new QueueFp604Api.Mxcsr(0x4004, 0xFFFF));
    private static final Env E3 = new Env(false, new QueueFp604Api.Mxcsr(0x4010, 0xFFFF));
    private static final Env E4 = new Env(false, new QueueFp604Api.Mxcsr(0x4020, 0xFFFF));

    private static final NonvolatileBits ENTRY_N = n(0x253000B0L, 0x253000B3L);
    private static final NonvolatileBits WORK_N = n(BLOCK, PAYLOAD);
    private static final NonvolatileBits CELL_N = n(CELL, PAYLOAD);
    private static final NonvolatileBits FINAL_N = n(SCRIPT_RBX, SCRIPT_RDI);
    private static final VolatileBits ENTRY_V = v(0x1234253000000001L, ROOT, BLOCK, PAYLOAD,
            0x25300009L, 0x25300010L, 0x25300011L, 0x1000L);
    private static final VolatileBits GETTER_INPUT_V = v(ROOT_VTABLE, ROOT, BLOCK, PAYLOAD,
            0x25300009L, 0x25300010L, 0x25300011L, 0x1000L);
    private static final VolatileBits GETTER_NORMAL_V = v(OBJECT, 0x25310001L, 0x25310002L,
            0x25310008L, 0x25310009L, 0x25310010L, 0x25310011L, 0x2000L);
    private static final VolatileBits RELEASE_INPUT_V = v(OBJECT, OBJECT, BLOCK, PAYLOAD,
            RESULT_VTABLE, 0x25310010L, 0x25310011L, 0x2000L);
    private static final VolatileBits TAIL_V = v(OBJECT, BLOCK, BLOCK, PAYLOAD,
            RESULT_VTABLE, 0x25310010L, 0x25310011L, 0x2000L);
    private static final VolatileBits LOWER0_V = v(0L, HEAP, 0L, BLOCK,
            RESULT_VTABLE, 0x25310010L, 0x25310011L, 0x2000L);
    private static final VolatileBits V1 = v(0xCAFE253000000000L, 0x25320001L, 0x25320002L,
            0x25320008L, 0x25320009L, 0x25320010L, 0x25320011L, 0x3000L);
    private static final VolatileBits V2 = v(CELL, 0x25330001L, 0x25330002L,
            0x25330008L, 0x25330009L, 0x25330010L, 0x25330011L, 0x4000L);
    private static final VolatileBits V3 = v(0x77889900F2345678L, 0x25340001L, 0x25340002L,
            0x25340008L, 0x25340009L, 0x25340010L, 0x25340011L, 0x5000L);
    private static final VolatileBits LOWER3_V = v(0x77889900F2345678L, 0x00000000F2345678L,
            0x25340002L, 0x25340008L, 0x25340009L, 0x25340010L, 0x25340011L, 0x5000L);
    private static final VolatileBits V4 = v(0xF00D2530A1B2C3D4L, 0x25350001L, 0x25350002L,
            0x25350008L, 0x25350009L, 0x25350010L, 0x25350011L, 0x6000L);

    private static final List<Long> LOWER_SITES = List.of(0x424E37AL, 0x424E384L, 0x424E38CL, 0x424E394L);
    private static final List<Long> LOWER_TARGETS = List.of(LOWER0_TARGET, 0x423B18CL, LOWER2_TARGET, 0x423B0D4L);
    private static final List<Integer> LOWER_LENGTHS = List.of(6, 5, 6, 5);
    private static final List<Long> LOWER_RETURNS = List.of(0x424E380L, 0x424E389L, 0x424E392L, 0x424E399L);
    private static final List<VolatileBits> LOWER_INPUTS = List.of(LOWER0_V, V1, V2, LOWER3_V);
    private static final List<NonvolatileBits> LOWER_NS = List.of(WORK_N, WORK_N, CELL_N, CELL_N);
    private static final List<Env> LOWER_ENVS = List.of(E0, E1, E2, E3);
    private static final List<QueueFp604Api.Normal> LOWER_NORMALS = List.of(
            normal(V1, WORK_N, I + 0x424E380L, P251, E1),
            normal(V2, WORK_N, I + 0x424E389L, P251, E2),
            normal(V3, CELL_N, I + 0x424E392L, P251, E3),
            normal(V4, CELL_N, I + 0x424E399L, P251, E4));
    private static final QueueFp604Api.Normal EXPECTED_INNER_NORMAL =
            normal(V4, WORK_N, I + 0x85585FL, P247, E4);
    private static final QueueFp604Api.Normal EXPECTED_OUTER_NORMAL =
            normal(V4, FINAL_N, SCRIPT_RET, 0xD010L, E4);

    // Synthetic unknown-callee PC/current state: no held native instruction or trap claim.
    private static final QueueFp604Api.Stopped FOURTH_STOP = new QueueFp604Api.Stopped(
            QueueFp604Api.StopReason.MISSING_POST_STATE,
            new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I, 0xCF70L,
                    v(0x25370000L, 0x25370001L, 0x25370002L, 0x25370008L,
                            0x25370009L, 0x25370010L, 0x25370011L, 0x7000L),
                    new NonvolatileBits(0x253700B0L, 0x253700B1L, 0x253700B2L, 0x253700B3L,
                            0xDEAD253025370012L, 0x25370013L, 0x25370014L, 0x25370015L,
                            new Bits128(0x2537006000000001L, 0x2537006000000002L))),
                    0xD253394L, true, new QueueFp604Api.Mxcsr(0x4008, 0xFFFF)),
            0, 0x424E394L);

    private static final Map<Long, Long> INITIAL_RAM = Map.ofEntries(
            Map.entry(ROOT, ROOT_VTABLE), Map.entry(ROOT_VTABLE + 0x38L, GETTER_TARGET),
            Map.entry(OBJECT, RESULT_VTABLE), Map.entry(RESULT_VTABLE + 0x10L, I + 0x8571C0L),
            Map.entry(I + 0x5C5DE30L, HEAP), Map.entry(I + 0x43DA748L, LOWER0_TARGET),
            Map.entry(I + 0x43DA738L, LOWER2_TARGET), Map.entry(O, 0xBEEF2530L),
            Map.entry(O + 8L, 0xA5A5253000000001L), Map.entry(O - 8L, 0xA5A5253000000002L),
            Map.entry(S251, 0xA5A5253000000003L), Map.entry(S251 - 8L, 0xA5A5253000000004L),
            Map.entry(C251, 0xA5A5253000000005L), Map.entry(S251 + 0x10L, 0x1122334455667788L),
            Map.entry(CELL, 0xFFEEDDCC13579BDFL));

    private static final List<String> COMPLETED_PREFIX = List.of(
            e("W64", O + 8L, ENTRY_N.rbxBits()), e("W64", O - 8L, ENTRY_N.rdiBits()),
            e("R64", ROOT), e("R64", ROOT_VTABLE + 0x38L),
            e("W64", S251, I + 0x85584FL), e("GETTER", 0x85584CL),
            e("R64", OBJECT), e("R64", RESULT_VTABLE + 0x10L),
            e("W64", S251, I + 0x85585FL), e("RELEASE", 0x85585BL), e("TAIL", 0x8571C8L),
            e("W32", S251 + 0x10L, 0L), e("R32", S251 + 0x10L),
            e("W64", S251 - 8L, BLOCK), e("R64", I + 0x5C5DE30L), e("R64", I + 0x43DA748L),
            e("W64", C251, I + 0x424E380L), e("LOWER", 0x424E37AL),
            e("SUP64", O + 8L, SCRIPT_RBX), e("SUP64", O - 8L, SCRIPT_RDI), e("SUP64", O, SCRIPT_RET),
            e("W64", C251, I + 0x424E389L), e("LOWER", 0x424E384L),
            e("R64", I + 0x43DA738L), e("W64", C251, I + 0x424E392L), e("LOWER", 0x424E38CL),
            e("W64", C251, I + 0x424E399L), e("LOWER", 0x424E394L));
    private static final List<String> NORMAL_SUFFIX = List.of(
            e("W32", CELL, 0xA1B2C3D4L), e("R64", S251 - 8L), e("R64", S251),
            e("R64", O + 8L), e("R64", O - 8L), e("R64", O));

    public static void main(String[] args) {
        if (args.length == 0) {
            fourLowerNormalsThroughActual648();
            fourthLowerStopThroughActual648();
            return;
        }
        if (args.length != 1) throw new IllegalArgumentException("One selector: normal or fourth-stop");
        switch (args[0]) {
            case "normal" -> fourLowerNormalsThroughActual648();
            case "fourth-stop" -> fourthLowerStopThroughActual648();
            default -> throw new IllegalArgumentException("Unknown selector");
        }
    }

    public static void fourLowerNormalsThroughActual648() { run(false); }
    public static void fourthLowerStopThroughActual648() { run(true); }

    private static void run(boolean stopFourth) {
        Ram ram = new Ram(INITIAL_RAM);
        ActualCaller caller = new ActualCaller(ram, stopFourth);
        PostVtable247Api.Input input = new PostVtable247Api.Input(
                new GovernmentCrtBoundary185Api.Entry(I, O, ENTRY_V, ENTRY_N),
                INPUT_ENV.df(), INPUT_ENV.mx(), 0xD253001L); // explicit artificial upstream context
        QueueFp604Api.Outcome result = PostVtableForward247.fromSlot10(input, ram, caller);
        eq(2, caller.outerCalls, "two actual247 CALL callbacks");
        eq(1, caller.releaseTails, "actual648 tail reached once");
        eq(4, caller.lowerCalls, "each of four lower effects once");
        eq(0, caller.delegatedCalls, "selected free did not use fallback");
        if (stopFourth) {
            if (result != FOURTH_STOP || caller.releaseResult != FOURTH_STOP
                    || caller.selectedTailResult != FOURTH_STOP) {
                throw new AssertionError("Inner Stopped identity/current snapshot lost across whole chain");
            }
            eq(COMPLETED_PREFIX, ram.events, "stop exact completed prefix, no store/cleanup/RET");
        } else {
            eq(EXPECTED_INNER_NORMAL, caller.releaseResult, "actual648 complete tail-owned post-state");
            eq(EXPECTED_OUTER_NORMAL, result, "actual247 full fresh N/RET and inner post environment");
            List<String> complete = new ArrayList<>(COMPLETED_PREFIX);
            complete.addAll(NORMAL_SUFFIX);
            eq(complete, ram.events, "normal exact pushes and true RET reads, no wrapper replay");
        }
        ram.expectChanges(Map.ofEntries(Map.entry(O + 8L, SCRIPT_RBX), Map.entry(O - 8L, SCRIPT_RDI),
                Map.entry(O, SCRIPT_RET), Map.entry(S251, I + 0x85585FL),
                Map.entry(S251 - 8L, BLOCK), Map.entry(C251, I + 0x424E399L),
                Map.entry(S251 + 0x10L, 0x1122334400000000L),
                Map.entry(CELL, stopFourth ? 0xFFEEDDCC13579BDFL : 0xFFEEDDCCA1B2C3D4L)));
    }

    /** Test-only callback consumer for the actual emitted247 frame, not a future252 source leaf. */
    private static final class ActualCaller implements PostVtable247Api.Children, FreePostState251Api.Children {
        private final Ram ram;
        private final boolean stopFourth;
        private int outerCalls, releaseTails, lowerCalls, delegatedCalls;
        private QueueFp604Api.Outcome selectedTailResult, releaseResult;
        private ActualCaller(Ram ram, boolean stopFourth) { this.ram = ram; this.stopFourth = stopFourth; }

        @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,
                GovernmentCrtBoundary185Api.Memory sameMemory) {
            if (sameMemory != ram) throw new AssertionError("Actual247 RAM object changed");
            int ordinal = outerCalls++;
            if (ordinal == 0) {
                check247(frame, 0x85584CL, GETTER_TARGET, 3, 0x85584FL, GETTER_INPUT_V, INPUT_ENV);
                ram.events.add(e("GETTER", 0x85584CL));
                return normal(GETTER_NORMAL_V, WORK_N, I + 0x85584FL, P247, E0);
            }
            if (ordinal != 1) throw new AssertionError("Repeated actual247 callback");
            check247(frame, 0x85585BL, I + 0x8571C0L, 4, 0x85585FL, RELEASE_INPUT_V, E0);
            ram.events.add(e("RELEASE", frame.call().callSiteRva()));
            long actualIncomingOrigin = frame.childInput().originCallSiteRva();
            eq(0x85585BL, actualIncomingOrigin, "origin from actual emitted second247 CALL");
            DefaultStaticFp648Api.Calls bound = DefaultFreePost253.bind(
                    ram, this, actualIncomingOrigin, new DefaultStaticFp648Api.Calls() {
                        @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame other) {
                            delegatedCalls++; throw new AssertionError("Unexpected delegate CALL");
                        }
                        @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame other) {
                            delegatedCalls++; throw new AssertionError("Selected free fell through");
                        }
                    });
            DefaultStaticFp648Api.Calls observeActualTail = new DefaultStaticFp648Api.Calls() {
                @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame unexpected) {
                    throw new AssertionError("No CALL belongs to actual64814B release");
                }
                @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame actual) {
                    releaseTails++;
                    eq(new GovernmentCrtBoundary185Api.Tail(0x8571C8L,
                            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x40EC530L,
                            new GovernmentCrtBoundary185Api.Entry(I, S251, TAIL_V, WORK_N)),
                            actual.transfer(), "actual648 nonzero RDX -> true current tail");
                    eq(E0.df(), actual.directionFlagSet(), "648 tail explicit DF");
                    if (actual.preMxcsr() != E0.mx()) throw new AssertionError("648 partial MXCSR object replaced");
                    ram.events.add(e("TAIL", actual.transfer().jumpSiteRva()));
                    selectedTailResult = bound.tail(actual);
                    return selectedTailResult;
                }
            };
            DefaultStaticFp648Api.Input actual648Input = new DefaultStaticFp648Api.Input(
                    frame.childInput().entry(), frame.childInput().directionFlagSet(), frame.childInput().mxcsr());
            releaseResult = DefaultReleaseWithFp648.fromSlot10(actual648Input, ram, observeActualTail);
            if (releaseResult != selectedTailResult) throw new AssertionError("648 rebuilt tail-owned Outcome");
            return releaseResult;
        }

        @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame unexpected,
                GovernmentCrtBoundary185Api.Memory sameMemory) {
            throw new AssertionError("Selected actual24758B path has CALL, not tail");
        }

        @Override public QueueFp604Api.Outcome invoke(FreePostState251Api.AlreadyPushedCallFrame frame,
                GovernmentCrtBoundary185Api.Memory sameMemory) {
            int ordinal = lowerCalls++;
            if (sameMemory != ram || ordinal >= 4) throw new AssertionError("Lower RAM changed or callback replayed");
            GovernmentCrtBoundary185Api.TargetKind kind = (ordinal == 0 || ordinal == 2)
                    ? GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                    : GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
            GovernmentCrtBoundary185Api.Call expected = new GovernmentCrtBoundary185Api.Call(
                    LOWER_SITES.get(ordinal), kind, LOWER_TARGETS.get(ordinal), P251,
                    LOWER_INPUTS.get(ordinal), LOWER_NS.get(ordinal));
            eq(0x424E364L, frame.ownerEntryRva(), "lower owner");
            eq(I, frame.imageBaseBits(), "lower image");
            eq(expected, frame.call(), "complete lower Call");
            eq(new GovernmentCrtBoundary185Api.Entry(I, C251, expected.volatileBits(), expected.nonvolatileBits()),
                    frame.childInput().entry(), "complete post-push child Entry");
            eq(LOWER_ENVS.get(ordinal).df(), frame.childInput().directionFlagSet(), "actual preceding post DF");
            if (frame.childInput().mxcsr() != LOWER_ENVS.get(ordinal).mx()) {
                throw new AssertionError("Explicit post MXCSR/status knowledge replaced or prefilled");
            }
            eq(LOWER_SITES.get(ordinal), frame.childInput().originCallSiteRva(), "each new lower CALL origin");
            eq(LOWER_LENGTHS.get(ordinal), frame.instructionLength(), "actual lower length");
            eq(I + LOWER_RETURNS.get(ordinal), frame.returnRipBits(), "actual lower continuation");
            eq(frame.returnRipBits(), ram.peek(C251), "201 already owned one continuation");
            ram.events.add(e("LOWER", expected.callSiteRva()));
            if (stopFourth && ordinal == 3) return FOURTH_STOP;
            if (ordinal == 0) {
                // Declared artificial supplier data effects, unrelated to201's own saved RBX/RET.
                ram.supplier(O + 8L, SCRIPT_RBX); ram.supplier(O - 8L, SCRIPT_RDI); ram.supplier(O, SCRIPT_RET);
            }
            return LOWER_NORMALS.get(ordinal);
        }

        private void check247(PostVtable247Api.CallFrame frame, long site, long target,
                int length, long returnRva, VolatileBits bits, Env env) {
            eq(0x855830L, frame.ownerEntryRva(), "actual247 owner");
            eq(I, frame.imageBaseBits(), "actual247 image");
            eq(new GovernmentCrtBoundary185Api.Call(site,
                    GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target, P247, bits, WORK_N),
                    frame.call(), "actual247 complete Call");
            eq(new GovernmentCrtBoundary185Api.Entry(I, S251, bits, WORK_N), frame.childInput().entry(),
                    "actual247 complete child Entry");
            eq(site, frame.childInput().originCallSiteRva(), "source CALL origin");
            eq(env.df(), frame.childInput().directionFlagSet(), "actual247 child DF");
            if (frame.childInput().mxcsr() != env.mx()) throw new AssertionError("Actual247 child MXCSR replaced");
            eq(length, frame.instructionLength(), "actual247 source length");
            eq(I + returnRva, frame.returnRipBits(), "actual247 source continuation");
            eq(I + returnRva, ram.peek(S251), "actual247 already-pushed continuation");
        }
    }

    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<String> events = new ArrayList<>();
        private final Map<Long, Long> initial;
        private Ram(Map<Long, Long> initial) { this.initial = initial; initial.forEach(this::put); }
        private int b(long address) {
            Byte value = bytes.get(address);
            if (value == null) throw new AssertionError("Unheld supplied byte " + Long.toUnsignedString(address, 16));
            return value & 255;
        }
        private void put(long address, long value) {
            for (int lane = 0; lane < 8; lane++) bytes.put(address + lane, (byte) (value >>> (lane * 8)));
        }
        private long peek(long address) {
            long value = 0;
            for (int lane = 0; lane < 8; lane++) value |= (long) b(address + lane) << (lane * 8);
            return value;
        }
        @Override public long readQword(long address) { events.add(e("R64", address)); return peek(address); }
        @Override public int readDword(long address) {
            events.add(e("R32", address)); int value = 0;
            for (int lane = 0; lane < 4; lane++) value |= b(address + lane) << (lane * 8);
            return value;
        }
        @Override public void writeQword(long address, long value) {
            if (address != O + 8L && address != O - 8L && address != S251
                    && address != S251 - 8L && address != C251) throw new AssertionError("Extra source push/save");
            events.add(e("W64", address, value)); put(address, value);
        }
        @Override public void writeDword(long address, int value) {
            if (address != S251 + 0x10L && address != CELL) throw new AssertionError("Undeclared DWORD write");
            events.add(e("W32", address, Integer.toUnsignedLong(value)));
            for (int lane = 0; lane < 4; lane++) bytes.put(address + lane, (byte) (value >>> (lane * 8)));
        }
        private void supplier(long address, long value) {
            if (address != O + 8L && address != O - 8L && address != O) throw new AssertionError("Undeclared supplier effect");
            events.add(e("SUP64", address, value)); put(address, value);
        }
        private void expectChanges(Map<Long, Long> changes) {
            Ram expected = new Ram(initial); changes.forEach(expected::put);
            eq(expected.bytes, bytes, "entire supplied RAM, including adjacent DWORDs");
        }
        @Override public int readUnsignedByte(long address) { throw unused(); }
        @Override public int lockedXaddDword(long address, int addend) { throw unused(); }
        @Override public void writeByte(long address, int value) { throw unused(); }
        @Override public Bits128 read128(long address) { throw unused(); }
        @Override public void write128(long address, Bits128 value) { throw unused(); }
        private AssertionError unused() { return new AssertionError("No selected source operation"); }
    }

    private static NonvolatileBits n(long rbx, long rdi) {
        return new NonvolatileBits(rbx, 0x253000B1L, 0x253000B2L, rdi, 0xFEDCBA9825300012L,
                0x25300013L, 0x25300014L, 0x25300015L,
                new Bits128(0x2530006000000001L, 0x2530006000000002L));
    }
    private static VolatileBits v(long ax, long cx, long dx, long r8, long r9, long r10, long r11, long x) {
        return new VolatileBits(ax, cx, dx, r8, r9, r10, r11,
                new Bits128(x, x + 1L), new Bits128(x + 0x10L, x + 0x11L),
                new Bits128(x + 0x20L, x + 0x21L), new Bits128(x + 0x30L, x + 0x31L),
                new Bits128(x + 0x40L, x + 0x41L), new Bits128(x + 0x50L, x + 0x51L));
    }
    private static QueueFp604Api.Normal normal(VolatileBits v, NonvolatileBits n, long rip, long sp, Env env) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v, rip, sp, n), env.df()), env.mx());
    }
    private static String e(String name, long address) { return name + ":" + Long.toUnsignedString(address, 16); }
    private static String e(String name, long address, long value) { return e(name, address) + ":" + Long.toUnsignedString(value, 16); }
    private static void eq(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
    }
}
