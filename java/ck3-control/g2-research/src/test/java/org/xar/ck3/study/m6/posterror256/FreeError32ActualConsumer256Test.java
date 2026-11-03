package org.xar.ck3.study.m6.posterror256;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.function.Supplier;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.postfree251.FreePostState251;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/**
 * Two finite new same-RAM composition witnesses from the frozen5/17/61/32 ASM literal.
 * Invokes the actual251 -> actual known consumer -> actual256 producers once.
 * Explicit opaque full Outcomes do not establish lower algorithms or hardware FP.
 * Source-only at delivery: this file has not been compiled or executed by its owner.
 */
public final class FreeError32ActualConsumer256Test {
    private static final long IMAGE = 0x0000000140000000L;
    private static final long ROOT_SP = 0x0000000000120008L;
    private static final long FREE_PRE = 0x000000000011FFE0L;
    private static final long ERROR_ENTRY = 0x000000000011FFD8L;
    private static final long INNER_PRE = 0x000000000011FFB0L;
    private static final long INNER_ENTRY = 0x000000000011FFA8L;
    private static final long SAVED_RBX = 0x0000000000120000L;
    private static final long OLD_ROOT_RET = 0x0000000140333310L;
    private static final long FRESH_ROOT_RET = 0x0000000140444420L;
    private static final long FRESH_RBX = 0x1122AA55CC778899L;

    private static final VolatileBits V0 = new VolatileBits(
            0xA000000000000001L, 0x0000000000200000L, 0xA000000000000003L, 0xA000000000000004L, 0xA000000000000005L, 0xA000000000000006L, 0xA000000000000007L,
            new Bits128(0xA000000000000010L, 0xA000000000000020L),
            new Bits128(0xA000000000000011L, 0xA000000000000021L),
            new Bits128(0xA000000000000012L, 0xA000000000000022L),
            new Bits128(0xA000000000000013L, 0xA000000000000023L),
            new Bits128(0xA000000000000014L, 0xA000000000000024L),
            new Bits128(0xA000000000000015L, 0xA000000000000025L));
    private static final VolatileBits V1 = new VolatileBits(
            0xABCD000000000000L, 0xB100000000000002L, 0xB100000000000003L, 0xB100000000000004L, 0xB100000000000005L, 0xB100000000000006L, 0xB100000000000007L,
            new Bits128(0xB100000000000010L, 0xB100000000000020L),
            new Bits128(0xB100000000000011L, 0xB100000000000021L),
            new Bits128(0xB100000000000012L, 0xB100000000000022L),
            new Bits128(0xB100000000000013L, 0xB100000000000023L),
            new Bits128(0xB100000000000014L, 0xB100000000000024L),
            new Bits128(0xB100000000000015L, 0xB100000000000025L));
    private static final VolatileBits V2 = new VolatileBits(
            0x0000000000700000L, 0xC200000000000002L, 0xC200000000000003L, 0xC200000000000004L, 0xC200000000000005L, 0xC200000000000006L, 0xC200000000000007L,
            new Bits128(0xC200000000000010L, 0xC200000000000020L),
            new Bits128(0xC200000000000011L, 0xC200000000000021L),
            new Bits128(0xC200000000000012L, 0xC200000000000022L),
            new Bits128(0xC200000000000013L, 0xC200000000000023L),
            new Bits128(0xC200000000000014L, 0xC200000000000024L),
            new Bits128(0xC200000000000015L, 0xC200000000000025L));
    private static final VolatileBits V3 = new VolatileBits(
            0x9988776680000005L, 0xD300000000000002L, 0xD300000000000003L, 0xD300000000000004L, 0xD300000000000005L, 0xD300000000000006L, 0xD300000000000007L,
            new Bits128(0xD300000000000010L, 0xD300000000000020L),
            new Bits128(0xD300000000000011L, 0xD300000000000021L),
            new Bits128(0xD300000000000012L, 0xD300000000000022L),
            new Bits128(0xD300000000000013L, 0xD300000000000023L),
            new Bits128(0xD300000000000014L, 0xD300000000000024L),
            new Bits128(0xD300000000000015L, 0xD300000000000025L));
    private static final VolatileBits V4 = new VolatileBits(
            0xCCDD0011F0E1D2C3L, 0xE400000000000002L, 0xE400000000000003L, 0xE400000000000004L, 0xE400000000000005L, 0xE400000000000006L, 0xE400000000000007L,
            new Bits128(0xE400000000000010L, 0xE400000000000020L),
            new Bits128(0xE400000000000011L, 0xE400000000000021L),
            new Bits128(0xE400000000000012L, 0xE400000000000022L),
            new Bits128(0xE400000000000013L, 0xE400000000000023L),
            new Bits128(0xE400000000000014L, 0xE400000000000024L),
            new Bits128(0xE400000000000015L, 0xE400000000000025L));
    private static final NonvolatileBits N0 = new NonvolatileBits(
            0x0B0B0B0B0B0B0B0BL, 0x1212121212121212L, 0x2323232323232323L, 0x3434343434343434L, 0xFEDCBA9800000012L, 0x5656565656565656L, 0x6767676767676767L, 0x7878787878787878L,
            new Bits128(0x6A6A000011112222L, 0x6B6B333344445555L));
    private static final NonvolatileBits NLIVECELL = new NonvolatileBits(
            0x0000000000700020L, 0x1212121212121212L, 0x2323232323232323L, 0x3434343434343434L, 0xFEDCBA9800000012L, 0x5656565656565656L, 0x6767676767676767L, 0x7878787878787878L,
            new Bits128(0x6A6A000011112222L, 0x6B6B333344445555L));
    private static final NonvolatileBits NFINALFRESH = new NonvolatileBits(
            0x1122AA55CC778899L, 0x1212121212121212L, 0x2323232323232323L, 0x3434343434343434L, 0xFEDCBA9800000012L, 0x5656565656565656L, 0x6767676767676767L, 0x7878787878787878L,
            new Bits128(0x6A6A000011112222L, 0x6B6B333344445555L));
    private static final QueueFp604Api.Mxcsr M0 = new QueueFp604Api.Mxcsr(0x1F80, 0xFFC0);
    private static final QueueFp604Api.Mxcsr M1 = new QueueFp604Api.Mxcsr(0x3F81, 0xFFC1);
    private static final QueueFp604Api.Mxcsr M2 = new QueueFp604Api.Mxcsr(0x5F84, 0xFFC4);
    private static final QueueFp604Api.Mxcsr M3 = new QueueFp604Api.Mxcsr(0x1F88, 0xFFFF);
    private static final QueueFp604Api.Mxcsr M4 = new QueueFp604Api.Mxcsr(0x1F80, 0xFFC1);
    private static final VolatileBits C1_INPUT = new VolatileBits(
            0x0000000000000000L, 0x0000000000300000L, 0x0000000000000000L, 0x0000000000200000L, 0xA000000000000005L, 0xA000000000000006L, 0xA000000000000007L,
            new Bits128(0xA000000000000010L, 0xA000000000000020L),
            new Bits128(0xA000000000000011L, 0xA000000000000021L),
            new Bits128(0xA000000000000012L, 0xA000000000000022L),
            new Bits128(0xA000000000000013L, 0xA000000000000023L),
            new Bits128(0xA000000000000014L, 0xA000000000000024L),
            new Bits128(0xA000000000000015L, 0xA000000000000025L));
    private static final VolatileBits C3_INPUT = new VolatileBits(
            0x0000000000700020L, 0xC200000000000002L, 0xC200000000000003L, 0xC200000000000004L, 0xC200000000000005L, 0xC200000000000006L, 0xC200000000000007L,
            new Bits128(0xC200000000000010L, 0xC200000000000020L),
            new Bits128(0xC200000000000011L, 0xC200000000000021L),
            new Bits128(0xC200000000000012L, 0xC200000000000022L),
            new Bits128(0xC200000000000013L, 0xC200000000000023L),
            new Bits128(0xC200000000000014L, 0xC200000000000024L),
            new Bits128(0xC200000000000015L, 0xC200000000000025L));
    private static final VolatileBits C4_INPUT = new VolatileBits(
            0x9988776680000005L, 0x0000000080000005L, 0xD300000000000003L, 0xD300000000000004L, 0xD300000000000005L, 0xD300000000000006L, 0xD300000000000007L,
            new Bits128(0xD300000000000010L, 0xD300000000000020L),
            new Bits128(0xD300000000000011L, 0xD300000000000021L),
            new Bits128(0xD300000000000012L, 0xD300000000000022L),
            new Bits128(0xD300000000000013L, 0xD300000000000023L),
            new Bits128(0xD300000000000014L, 0xD300000000000024L),
            new Bits128(0xD300000000000015L, 0xD300000000000025L));

    private FreeError32ActualConsumer256Test() { }

    public static void main(String[] args) {
        if (args.length == 0) {
            run(false);
            run(true);
        } else if (args.length == 1 && args[0].equals("normal")) {
            run(false);
        } else if (args.length == 1 && args[0].equals("inner-stop")) {
            run(true);
        } else {
            throw new IllegalArgumentException("Expected no args, normal, or inner-stop");
        }
        System.out.println("Selected actual-free/error32 composition cases passed");
    }

    private static void run(boolean stopMode) {
        Ram ram = seededRam();
        List<Long> callOrder = new ArrayList<>();
        List<Long> freeOrder = new ArrayList<>();
        List<Long> fallbackOrder = new ArrayList<>();
        int[] actual32Entries = {0};
        int[] innerCalls = {0};
        Entry stopEntry = new Entry(IMAGE, INNER_ENTRY, V1, N0);
        QueueFp604Api.Stopped suppliedStop = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(stopEntry, 0x424FC74L, true, M1),
                0, 0x423B190L);

        KnownAllocateErrorFp625.ErrorCalls inner = frame -> {
            innerCalls[0]++;
            callOrder.add(0x423B190L);
            checkError(frame);
            if (stopMode) return suppliedStop;
            return ram.asActor("supplierFC74", () -> {
                ram.writeQword(SAVED_RBX, FRESH_RBX);
                ram.writeQword(ROOT_SP, FRESH_ROOT_RET);
                long freshRip = ram.readQword(INNER_ENTRY);
                equalLong(0x000000014423B195L, freshRip, "FC74 owned RET");
                return normal(V2, freshRip, INNER_PRE, N0, false, M2);
            });
        };
        Error32PostState256 actual32 = new Error32PostState256(inner);
        PostState240Api.EntryExecutor countedActual32 = (input, sameMemory) -> {
            actual32Entries[0]++;
            same(ram, sameMemory, "same RAM at actual32 entry");
            equal(new PostState240Api.Input(
                    new Entry(IMAGE, ERROR_ENTRY, V1, N0), true, M1, 0x424E384L),
                    input, "actual32 full input and actual E384 origin");
            QueueFp604Api.Outcome result = actual32.execute(input, sameMemory);
            if (stopMode) {
                same(suppliedStop, result, "actual32 original Stop");
            } else {
                equal(normal(C3_INPUT, 0x000000014424E389L, FREE_PRE, N0, false, M2),
                        result, "actual32 complete normal poststate");
            }
            return result;
        };

        FreePostState251Api.Children remaining = (frame, sameMemory) -> {
            same(ram, sameMemory, "same RAM at opaque free child");
            long site = frame.call().callSiteRva();
            fallbackOrder.add(site);
            if (site == 0x424E37AL) {
                return ram.asActor("supplierC1", () -> {
                    long freshRip = ram.readQword(ERROR_ENTRY);
                    equalLong(0x000000014424E380L, freshRip, "C1 owned RET");
                    return normal(V1, freshRip, FREE_PRE, N0, true, M1);
                });
            }
            if (site == 0x424E38CL && !stopMode) {
                return ram.asActor("supplierC3", () -> {
                    long freshRip = ram.readQword(ERROR_ENTRY);
                    equalLong(0x000000014424E392L, freshRip, "C3 owned RET");
                    return normal(V3, freshRip, FREE_PRE, NLIVECELL, false, M3);
                });
            }
            if (site == 0x424E394L && !stopMode) {
                return ram.asActor("supplierC4", () -> {
                    long freshRip = ram.readQword(ERROR_ENTRY);
                    equalLong(0x000000014424E399L, freshRip, "C4 owned RET");
                    return normal(V4, freshRip, FREE_PRE, NLIVECELL, true, M4);
                });
            }
            throw new AssertionError("Unexpected opaque free child " + Long.toHexString(site));
        };
        FreePostState251Api.Children actualBinding = FreeKnownError256.bind(
                countedActual32, remaining);
        FreePostState251Api.Children observer = (frame, sameMemory) -> {
            same(ram, sameMemory, "same RAM at actual251 child frame");
            int index = freeOrder.size();
            freeOrder.add(frame.call().callSiteRva());
            callOrder.add(frame.call().callSiteRva());
            checkFreeAtIndex(frame, index);
            return actualBinding.invoke(frame, sameMemory);
        };

        FreePostState251 actualWhole251 = new FreePostState251(observer);
        PostState240Api.Input rootInput = new PostState240Api.Input(
                new Entry(IMAGE, ROOT_SP, V0, N0), false, M0, 0xC0FFEEL);
        QueueFp604Api.Outcome result = actualWhole251.execute(rootInput, ram);

        equalLong(1, actual32Entries[0], "exactly one actual32 entry");
        equalLong(1, innerCalls[0], "exactly one inner FC74 call");
        if (stopMode) {
            same(suppliedStop, result, "original inner Stop through whole251");
            same(stopEntry, suppliedStop.snapshot().currentState(), "original Stop entry");
            same(M1, suppliedStop.snapshot().mxcsr(), "SAME partial MXCSR");
            equal(List.of(0x424E37AL, 0x424E384L, 0x423B190L), callOrder,
                    "Stop separate CALL markers");
            equal(List.of(0x424E37AL, 0x424E384L), freeOrder, "Stop actual251 frame order");
            equal(List.of(0x424E37AL), fallbackOrder, "Stop opaque free calls");
            equal(expectedNormalEvents().subList(0, 9), ram.events,
                    "Stop exact9 RAM events; no unwind RET/restore/store");
        } else {
            equal(normal(V4, FRESH_ROOT_RET, 0x0000000000120010L, NFINALFRESH, true, M4),
                    result, "whole251 full returned state and final post environment");
            equal(List.of(0x424E37AL, 0x424E384L, 0x423B190L, 0x424E38CL, 0x424E394L),
                    callOrder, "Normal separate CALL markers");
            equal(List.of(0x424E37AL, 0x424E384L, 0x424E38CL, 0x424E394L),
                    freeOrder, "Normal actual251 frame order");
            equal(List.of(0x424E37AL, 0x424E38CL, 0x424E394L),
                    fallbackOrder, "E384 must use actual known binding");
            equal(expectedNormalEvents(), ram.events, "Normal exact21 RAM events");
        }
        Ram expected = seededRam();
        if (stopMode) {
            expected.seed(0x0000000000120018L, 4, 0x00000000L);
            expected.seed(0x0000000000120000L, 8, 0x0B0B0B0B0B0B0B0BL);
            expected.seed(0x0000000000120008L, 8, 0x0000000140333310L);
            expected.seed(0x000000000011FFD8L, 8, 0x000000014424E389L);
            expected.seed(0x000000000011FFA8L, 8, 0x000000014423B195L);
            expected.seed(0x0000000000700020L, 4, 0x2468ACE0L);
        } else {
            expected.seed(0x0000000000120018L, 4, 0x00000000L);
            expected.seed(0x0000000000120000L, 8, 0x1122AA55CC778899L);
            expected.seed(0x0000000000120008L, 8, 0x0000000140444420L);
            expected.seed(0x000000000011FFD8L, 8, 0x000000014424E399L);
            expected.seed(0x000000000011FFA8L, 8, 0x000000014423B195L);
            expected.seed(0x0000000000700020L, 4, 0xF0E1D2C3L);
        }
        equal(expected.bytes, ram.bytes, "complete owned RAM after scene");
        equalLong(OLD_ROOT_RET, seededRam().peek(ROOT_SP, 8), "fixed initial root RET");
    }

    private static void checkFreeAtIndex(
            FreePostState251Api.AlreadyPushedCallFrame frame, int index) {
        switch (index) {
            case 0 -> checkFree(frame, 0x000000000424E37AL, TargetKind.INDIRECT_ABSOLUTE, 0x0000000140A10010L, 6, 0x000000014424E380L, C1_INPUT, N0, false, M0);
            case 1 -> checkFree(frame, 0x000000000424E384L, TargetKind.DIRECT_RVA, 0x000000000423B18CL, 5, 0x000000014424E389L, V1, N0, true, M1);
            case 2 -> checkFree(frame, 0x000000000424E38CL, TargetKind.INDIRECT_ABSOLUTE, 0x0000000140A30030L, 6, 0x000000014424E392L, C3_INPUT, NLIVECELL, false, M2);
            case 3 -> checkFree(frame, 0x000000000424E394L, TargetKind.DIRECT_RVA, 0x000000000423B0D4L, 5, 0x000000014424E399L, C4_INPUT, NLIVECELL, false, M3);
            default -> throw new AssertionError("Unexpected fifth Free61 frame");
        }
    }

    private static void checkFree(FreePostState251Api.AlreadyPushedCallFrame frame,
            long site, TargetKind kind, long target, int length, long returnRip,
            VolatileBits inputV, NonvolatileBits inputN, boolean preDf,
            QueueFp604Api.Mxcsr preMxcsr) {
        equalLong(0x424E364L, frame.ownerEntryRva(), "actual61 frame owner");
        equalLong(IMAGE, frame.imageBaseBits(), "actual61 image");
        equal(new Call(site, kind, target, FREE_PRE, inputV, inputN),
                frame.call(), "actual61 complete Call");
        equalLong(length, frame.instructionLength(), "actual61 instruction length");
        equalLong(returnRip, frame.returnRipBits(), "actual61 actual return RIP");
        equal(new PostState240Api.Input(new Entry(IMAGE, ERROR_ENTRY, inputV, inputN),
                preDf, preMxcsr, site), frame.childInput(),
                "actual61 full child input / latest environment / actual origin");
    }

    private static void checkError(KnownAllocateErrorFp625.ErrorCall frame) {
        equal(new Call(0x423B190L, TargetKind.DIRECT_RVA, 0x424FC74L,
                INNER_PRE, V1, N0), frame.original(), "actual B190 full Call");
        equal(new Entry(IMAGE, INNER_ENTRY, V1, N0), frame.childEntry(),
                "actual FC74 full entry");
        require(frame.directionFlagSet(), "actual FC74 consumes C1 DFtrue");
        equal(M1, frame.preMxcsr(), "actual FC74 consumes C1 partial MXCSR");
        equalLong(0x000000014423B195L, frame.returnRipBits(), "actual B190+5 return RIP");
    }

    private static QueueFp604Api.Normal normal(VolatileBits v, long rip, long callerSp,
            NonvolatileBits n, boolean df, QueueFp604Api.Mxcsr mxcsr) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new NormalReturn(v, rip, callerSp, n), df), mxcsr);
    }

    private static Ram seededRam() {
        Ram ram = new Ram();
        ram.seed(0x0000000000120018L, 4, 0xDEADBEEFL);
        ram.seed(0x0000000000120000L, 8, 0xAAAAAAAA55555555L);
        ram.seed(0x0000000000120008L, 8, 0x0000000140333310L);
        ram.seed(0x000000000011FFD8L, 8, 0x1111111122222222L);
        ram.seed(0x000000000011FFA8L, 8, 0x3333333344444444L);
        ram.seed(0x0000000145C5DE30L, 8, 0x0000000000300000L);
        ram.seed(0x00000001443DA748L, 8, 0x0000000140A10010L);
        ram.seed(0x00000001443DA738L, 8, 0x0000000140A30030L);
        ram.seed(0x0000000000700020L, 4, 0x2468ACE0L);
        return ram;
    }

    private static List<RamEvent> expectedNormalEvents() {
        return List.of(
            new RamEvent("source", "W4", 0x0000000000120018L, 0x00000000L),
            new RamEvent("source", "R4", 0x0000000000120018L, 0x00000000L),
            new RamEvent("source", "W8", 0x0000000000120000L, 0x0B0B0B0B0B0B0B0BL),
            new RamEvent("source", "R8", 0x0000000145C5DE30L, 0x0000000000300000L),
            new RamEvent("source", "R8", 0x00000001443DA748L, 0x0000000140A10010L),
            new RamEvent("source", "W8", 0x000000000011FFD8L, 0x000000014424E380L),
            new RamEvent("supplierC1", "R8", 0x000000000011FFD8L, 0x000000014424E380L),
            new RamEvent("source", "W8", 0x000000000011FFD8L, 0x000000014424E389L),
            new RamEvent("source", "W8", 0x000000000011FFA8L, 0x000000014423B195L),
            new RamEvent("supplierFC74", "W8", 0x0000000000120000L, 0x1122AA55CC778899L),
            new RamEvent("supplierFC74", "W8", 0x0000000000120008L, 0x0000000140444420L),
            new RamEvent("supplierFC74", "R8", 0x000000000011FFA8L, 0x000000014423B195L),
            new RamEvent("source", "R8", 0x000000000011FFD8L, 0x000000014424E389L),
            new RamEvent("source", "R8", 0x00000001443DA738L, 0x0000000140A30030L),
            new RamEvent("source", "W8", 0x000000000011FFD8L, 0x000000014424E392L),
            new RamEvent("supplierC3", "R8", 0x000000000011FFD8L, 0x000000014424E392L),
            new RamEvent("source", "W8", 0x000000000011FFD8L, 0x000000014424E399L),
            new RamEvent("supplierC4", "R8", 0x000000000011FFD8L, 0x000000014424E399L),
            new RamEvent("source", "W4", 0x0000000000700020L, 0xF0E1D2C3L),
            new RamEvent("source", "R8", 0x0000000000120000L, 0x1122AA55CC778899L),
            new RamEvent("source", "R8", 0x0000000000120008L, 0x0000000140444420L));
    }

    private record RamEvent(String actor, String operation, long addressBits, long valueBits) { }

    /** Plain byte RAM. Reads are pure; actor tags only distinguish explicit supplier effects. */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Integer> bytes = new TreeMap<>();
        private final List<RamEvent> events = new ArrayList<>();
        private String actor = "source";

        void seed(long address, int width, long value) {
            for (int i = 0; i < width; i++) {
                bytes.put(address + i, (int) ((value >>> (8 * i)) & 0xFFL));
            }
        }

        long peek(long address, int width) {
            long result = 0;
            for (int i = 0; i < width; i++) {
                Integer value = bytes.get(address + i);
                if (value == null) throw new AssertionError(
                        "Unseeded owned byte " + Long.toHexString(address + i));
                result |= ((long) value) << (8 * i);
            }
            return result;
        }

        <T> T asActor(String name, Supplier<T> action) {
            String previous = actor;
            actor = name;
            try {
                return action.get();
            } finally {
                actor = previous;
            }
        }

        @Override public int readDword(long address) {
            long value = peek(address, 4);
            events.add(new RamEvent(actor, "R4", address, value));
            return (int) value;
        }

        @Override public long readQword(long address) {
            long value = peek(address, 8);
            events.add(new RamEvent(actor, "R8", address, value));
            return value;
        }

        @Override public void writeDword(long address, int value) {
            events.add(new RamEvent(actor, "W4", address, Integer.toUnsignedLong(value)));
            seed(address, 4, Integer.toUnsignedLong(value));
        }

        @Override public void writeQword(long address, long value) {
            events.add(new RamEvent(actor, "W8", address, value));
            seed(address, 8, value);
        }

        @Override public int readUnsignedByte(long address) {
            throw new AssertionError("Unexpected byte read");
        }

        @Override public void writeByte(long address, int value) {
            throw new AssertionError("Unexpected byte write");
        }

        @Override public int lockedXaddDword(long address, int addend) {
            throw new AssertionError("Unexpected locked XADD");
        }

        @Override public Bits128 read128(long address) {
            throw new AssertionError("Unexpected 128-bit read");
        }

        @Override public void write128(long address, Bits128 value) {
            throw new AssertionError("Unexpected 128-bit write");
        }
    }

    private static void equal(Object expected, Object actual, String label) {
        if (!Objects.equals(expected, actual)) throw new AssertionError(
                label + "\nexpected=" + expected + "\nactual=" + actual);
    }

    private static void equalLong(long expected, long actual, String label) {
        if (expected != actual) throw new AssertionError(label + ": expected="
                + Long.toHexString(expected) + " actual=" + Long.toHexString(actual));
    }

    private static void same(Object expected, Object actual, String label) {
        if (expected != actual) throw new AssertionError(label + ": object identity changed");
    }

    private static void require(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }
}
