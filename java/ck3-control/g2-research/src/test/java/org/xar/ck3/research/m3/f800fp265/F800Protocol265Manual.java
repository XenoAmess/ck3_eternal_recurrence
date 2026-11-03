package org.xar.ck3.research.m3.f800fp265;

import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Two finite public-DATA protocol witnesses from original69 ASM.
 * Oracle265 and finite images were sealed before any new265 body read.
 * Opaque FA90 and indexed tails only offer the explicit full states and RAM DATA.
 * No Native, hardware, ABI, EH or opaque-child algorithm qualification.
 */
public final class F800Protocol265Manual {
    private F800Protocol265Manual() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 0) throw new IllegalArgumentException("No arguments accepted");
        runCase(false);
        runCase(true);
        System.out.print("F800Protocol265Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean middleStopped) throws Exception {
        Fixture f = new Fixture();
        int[] callCount = {0};
        F800Fp265Api.Calls offered = actual -> {
            int ordinal = ++callCount[0];
            if (ordinal == 1) {
                if (!actual.original().equals(f.firstCall)
                        || !actual.childEntry().equals(f.firstChild)
                        || actual.directionFlagSet() != false
                        || actual.preMxcsr() != f.fpEntry
                        || actual.returnRipBits() != 0x00000001A424F81CL) {
                    throw new AssertionError("First complete frame differs from sealed265 DATA");
                }
                f.ram.writeQword(0x0000000000006108L, 0x0000000000006400L);
                f.ram.writeQword(0x0000000000006400L, 0x0000000000006600L);
                f.ram.writeQword(0x0000000000006100L, 0x0000000000006700L);
                f.ram.writeQword(0x0000000000006600L, 0x8899AABBCCDDEEFFL);
                f.ram.writeQword(0x0000000000006700L, 0xFEDCBA9876543210L);
                return f.firstNormal;
            }
            if (ordinal == 2) {
                if (!actual.original().equals(f.middleCall)
                        || !actual.childEntry().equals(f.middleChild)
                        || actual.directionFlagSet() != true
                        || actual.preMxcsr() != f.fpAfterFirst
                        || actual.returnRipBits() != 0x00000001A424F832L) {
                    throw new AssertionError("Middle FA90 full frame differs from sealed265 DATA");
                }
                if (middleStopped) return f.middleStopped;
                f.ram.writeDword(0x0000000000006180L, 0x87654321);
                return f.middleNormal;
            }
            if (ordinal == 3 && !middleStopped) {
                if (!actual.original().equals(f.finalCall)
                        || !actual.childEntry().equals(f.finalChild)
                        || actual.directionFlagSet() != false
                        || actual.preMxcsr() != f.fpAfterMiddle
                        || actual.returnRipBits() != 0x00000001A424F83AL) {
                    throw new AssertionError("Final complete frame differs from sealed265 DATA");
                }
                f.ram.writeQword(0x0000000000005010L, 0xCEAD0123456789ABL);
                f.ram.writeQword(0x0000000000005000L, 0xDEBC123456789ABCL);
                f.ram.writeQword(0x0000000000005008L, 0x00000001A0776655L);
                return f.finalNormal;
            }
            throw new AssertionError("Unexpected opaque call ordinal " + ordinal);
        };
        QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(f.entry, false, (header, guard) -> {
                    throw new AssertionError("Straight-line original69 used loop budget");
                }), f.fpEntry);
        QueueFp604Api.Outcome actual = F800FullState265.execute(input, f.ram, offered);
        List<String> expectedTrace = middleStopped ? f.stoppedTrace : f.normalTrace;
        if (!f.ram.trace.equals(expectedTrace)) {
            throw new AssertionError("Memory effect trace differs: " + f.ram.trace
                    + " expected " + expectedTrace);
        }
        if (callCount[0] != (middleStopped ? 2 : 3) || f.ram.atomicCalls != 0) {
            throw new AssertionError("Opaque call count differs or unexpected atomic effect");
        }
        if (middleStopped) {
            if (actual != f.middleStopped) {
                throw new AssertionError("Middle FA90 Stopped identity was reconstructed or lost");
            }
        } else {
            if (!(actual instanceof QueueFp604Api.Normal normal)
                    || !normal.base().equals(f.expectedNormal.base())
                    || normal.postMxcsr() != f.fpAfterFinal) {
                throw new AssertionError("Final complete V/N/SP/RIP/DF/partialFP differs");
            }
        }
        String ramHash = HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(f.ram.bytes));
        String expectedHash = middleStopped
                ? "c62dd1b6f3c511993f8699b43cdb513a54d5f04f50cbce504bf82d8be9a163fe"
                : "26cb35e46367781a52ae6bbe36041489dea7fbaee592070f161bfcf67a43fe4a";
        if (!ramHash.equals(expectedHash)) {
            throw new AssertionError("Finite RAM differs from sealed265 byte image: " + ramHash);
        }
    }

    private static final class Fixture {
        final QueueFp604Api.Mxcsr fpEntry = new QueueFp604Api.Mxcsr(0x0041, 0x0043);
        final QueueFp604Api.Mxcsr fpAfterFirst = new QueueFp604Api.Mxcsr(0x0082, 0x00C3);
        final QueueFp604Api.Mxcsr fpAfterMiddle = new QueueFp604Api.Mxcsr(0x0204, 0x0205);
        final QueueFp604Api.Mxcsr fpAfterFinal = new QueueFp604Api.Mxcsr(0x0401, 0x0403);
        final QueueFp604Api.Mxcsr fpStopped = new QueueFp604Api.Mxcsr(0x0008, 0x000C);
        final GovernmentPrimaryTail155Api.VolatileBits entryV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xF201A1B2C3D4E5F6L, 0xF202A1B2C3D4E5F6L, 0x0000000000006000L, 0x0000000000006100L, 0x0000000000006180L, 0xF206A1B2C3D4E5F6L, 0xF207A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0xF220A1B2C3D4E5F6L, 0xF221A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF222A1B2C3D4E5F6L, 0xF223A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF224A1B2C3D4E5F6L, 0xF225A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF226A1B2C3D4E5F6L, 0xF227A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF228A1B2C3D4E5F6L, 0xF229A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF22AA1B2C3D4E5F6L, 0xF22BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.NonvolatileBits entryN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x194A5B6C7D8E9FA0L, 0x2A5B6C7D8E9FA0B1L, 0x3B6C7D8E9FA0B1C2L, 0x4C7D8E9FA0B1C2D3L, 0x5D8E9FA0B1C2D3E4L, 0x6E9FA0B1C2D3E4F5L, 0x7FA0B1C2D3E4F506L, 0x80B1C2D3E4F50617L,
                new GovernmentPrimaryTail155Api.Bits128(0x91C2D3E4F5061728L, 0xA2D3E4F506172839L));
        final GovernmentPrimaryTail155Api.VolatileBits firstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xF201A1B2C3D4E5F6L, 0x00000000D234ABCDL, 0x0000000000006000L, 0x0000000000006100L, 0x0000000000006180L, 0xF206A1B2C3D4E5F6L, 0xF207A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0xF220A1B2C3D4E5F6L, 0xF221A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF222A1B2C3D4E5F6L, 0xF223A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF224A1B2C3D4E5F6L, 0xF225A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF226A1B2C3D4E5F6L, 0xF227A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF228A1B2C3D4E5F6L, 0xF229A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xF22AA1B2C3D4E5F6L, 0xF22BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.VolatileBits middleV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x0000000000006400L, 0xFEDCBA9876543210L, 0x8899AABBCCDDEEFFL, 0x9104A1B2C3D4E5F6L, 0x9105A1B2C3D4E5F6L, 0x9106A1B2C3D4E5F6L, 0x9107A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0x9120A1B2C3D4E5F6L, 0x9121A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9122A1B2C3D4E5F6L, 0x9123A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9124A1B2C3D4E5F6L, 0x9125A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9126A1B2C3D4E5F6L, 0x9127A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9128A1B2C3D4E5F6L, 0x9129A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x912AA1B2C3D4E5F6L, 0x912BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.VolatileBits finalV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xA501A1B2C3D4E5F6L, 0x0000000087654321L, 0xA503A1B2C3D4E5F6L, 0xA504A1B2C3D4E5F6L, 0xA505A1B2C3D4E5F6L, 0xA506A1B2C3D4E5F6L, 0xA507A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0xA520A1B2C3D4E5F6L, 0xA521A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA522A1B2C3D4E5F6L, 0xA523A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA524A1B2C3D4E5F6L, 0xA525A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA526A1B2C3D4E5F6L, 0xA527A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA528A1B2C3D4E5F6L, 0xA529A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA52AA1B2C3D4E5F6L, 0xA52BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.NonvolatileBits callN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x0000000000006180L, 0x2A5B6C7D8E9FA0B1L, 0x3B6C7D8E9FA0B1C2L, 0x0000000000006100L, 0x5D8E9FA0B1C2D3E4L, 0x6E9FA0B1C2D3E4F5L, 0x7FA0B1C2D3E4F506L, 0x80B1C2D3E4F50617L,
                new GovernmentPrimaryTail155Api.Bits128(0x91C2D3E4F5061728L, 0xA2D3E4F506172839L));
        final GovernmentPrimaryTail155Api.VolatileBits postFirstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x9101A1B2C3D4E5F6L, 0x9102A1B2C3D4E5F6L, 0x9103A1B2C3D4E5F6L, 0x9104A1B2C3D4E5F6L, 0x9105A1B2C3D4E5F6L, 0x9106A1B2C3D4E5F6L, 0x9107A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0x9120A1B2C3D4E5F6L, 0x9121A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9122A1B2C3D4E5F6L, 0x9123A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9124A1B2C3D4E5F6L, 0x9125A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9126A1B2C3D4E5F6L, 0x9127A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x9128A1B2C3D4E5F6L, 0x9129A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0x912AA1B2C3D4E5F6L, 0x912BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.VolatileBits postMiddleV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xA501A1B2C3D4E5F6L, 0xA502A1B2C3D4E5F6L, 0xA503A1B2C3D4E5F6L, 0xA504A1B2C3D4E5F6L, 0xA505A1B2C3D4E5F6L, 0xA506A1B2C3D4E5F6L, 0xA507A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0xA520A1B2C3D4E5F6L, 0xA521A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA522A1B2C3D4E5F6L, 0xA523A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA524A1B2C3D4E5F6L, 0xA525A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA526A1B2C3D4E5F6L, 0xA527A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA528A1B2C3D4E5F6L, 0xA529A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xA52AA1B2C3D4E5F6L, 0xA52BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.VolatileBits postFinalV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xC901A1B2C3D4E5F6L, 0xC902A1B2C3D4E5F6L, 0xC903A1B2C3D4E5F6L, 0xC904A1B2C3D4E5F6L, 0xC905A1B2C3D4E5F6L, 0xC906A1B2C3D4E5F6L, 0xC907A1B2C3D4E5F6L,
                new GovernmentPrimaryTail155Api.Bits128(0xC920A1B2C3D4E5F6L, 0xC921A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xC922A1B2C3D4E5F6L, 0xC923A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xC924A1B2C3D4E5F6L, 0xC925A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xC926A1B2C3D4E5F6L, 0xC927A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xC928A1B2C3D4E5F6L, 0xC929A1B2C3D4E5F6L),
                new GovernmentPrimaryTail155Api.Bits128(0xC92AA1B2C3D4E5F6L, 0xC92BA1B2C3D4E5F6L));
        final GovernmentPrimaryTail155Api.NonvolatileBits finalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0xCEAD0123456789ABL, 0x2A5B6C7D8E9FA0B1L, 0x3B6C7D8E9FA0B1C2L, 0xDEBC123456789ABCL, 0x5D8E9FA0B1C2D3E4L, 0x6E9FA0B1C2D3E4F5L, 0x7FA0B1C2D3E4F506L, 0x80B1C2D3E4F50617L,
                new GovernmentPrimaryTail155Api.Bits128(0x91C2D3E4F5061728L, 0xA2D3E4F506172839L));
        final GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(0x00000001A0000000L, 0x0000000000005008L, entryV, entryN);
        final GovernmentCrtBoundary185Api.Call firstCall = new GovernmentCrtBoundary185Api.Call(
                0x000000000424F817L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x0000000004247FFCL, 0x0000000000004FE0L, firstV, callN);
        final GovernmentCrtBoundary185Api.Entry firstChild = new GovernmentCrtBoundary185Api.Entry(0x00000001A0000000L, 0x0000000000004FD8L, firstV, callN);
        final GovernmentCrtBoundary185Api.Call middleCall = new GovernmentCrtBoundary185Api.Call(
                0x000000000424F82DL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x000000000424FA90L, 0x0000000000004FE0L, middleV, callN);
        final GovernmentCrtBoundary185Api.Entry middleChild = new GovernmentCrtBoundary185Api.Entry(0x00000001A0000000L, 0x0000000000004FD8L, middleV, callN);
        final GovernmentCrtBoundary185Api.Call finalCall = new GovernmentCrtBoundary185Api.Call(
                0x000000000424F835L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x0000000004248050L, 0x0000000000004FE0L, finalV, callN);
        final GovernmentCrtBoundary185Api.Entry finalChild = new GovernmentCrtBoundary185Api.Entry(0x00000001A0000000L, 0x0000000000004FD8L, finalV, callN);
        final QueueFp604Api.Normal firstNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postFirstV, 0x00000001A424F81CL, 0x0000000000004FE0L, callN),
                true), fpAfterFirst);
        final QueueFp604Api.Normal middleNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postMiddleV, 0x00000001A424F832L, 0x0000000000004FE0L, callN),
                false), fpAfterMiddle);
        final QueueFp604Api.Normal finalNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postFinalV, 0x00000001A424F83AL, 0x0000000000004FE0L, callN),
                true), fpAfterFinal);
        final QueueFp604Api.Normal expectedNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postFinalV, 0x00000001A0776655L, 0x0000000000005010L, finalN),
                true), fpAfterFinal);
        final QueueFp604Api.Stopped middleStopped = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(middleChild, 0x000000000424FA90L, false, fpStopped),
                0, 0x000000000424F82DL);
        final List<String> normalTrace = List.of(
                "W64@5010=194a5b6c7d8e9fa0",
                "W64@5028=6180",
                "W64@5000=4c7d8e9fa0b1c2d3",
                "R32@6000=d234abcd",
                "W64@4fd8=1a424f81c",
                "W64@6108=6400",
                "W64@6400=6600",
                "W64@6100=6700",
                "W64@6600=8899aabbccddeeff",
                "W64@6700=fedcba9876543210",
                "R64@6108=6400",
                "R64@6400=6600",
                "R64@6100=6700",
                "R64@6600=8899aabbccddeeff",
                "R64@6700=fedcba9876543210",
                "W64@4fd8=1a424f832",
                "W32@6180=87654321",
                "R32@6180=87654321",
                "W64@4fd8=1a424f83a",
                "W64@5010=cead0123456789ab",
                "W64@5000=debc123456789abc",
                "W64@5008=1a0776655",
                "R64@5010=cead0123456789ab",
                "R64@5000=debc123456789abc",
                "R64@5008=1a0776655");
        final List<String> stoppedTrace = List.of(
                "W64@5010=194a5b6c7d8e9fa0",
                "W64@5028=6180",
                "W64@5000=4c7d8e9fa0b1c2d3",
                "R32@6000=d234abcd",
                "W64@4fd8=1a424f81c",
                "W64@6108=6400",
                "W64@6400=6600",
                "W64@6100=6700",
                "W64@6600=8899aabbccddeeff",
                "W64@6700=fedcba9876543210",
                "R64@6108=6400",
                "R64@6400=6600",
                "R64@6100=6700",
                "R64@6600=8899aabbccddeeff",
                "R64@6700=fedcba9876543210",
                "W64@4fd8=1a424f832");
        final Ram ram = new Ram();

        Fixture() {
            ram.seed(0x0000000000005008L, 8, 0x00000001A0112233L);
            ram.seed(0x0000000000006000L, 4, 0xD234ABCDL);
            ram.seed(0x0000000000006180L, 4, 0xF1234567L);
            ram.seed(0x0000000000006108L, 8, 0x0000000000006200L);
            ram.seed(0x0000000000006200L, 8, 0x0000000000006300L);
            ram.seed(0x0000000000006300L, 8, 0xBADC0FFEE0DDF00DL);
            ram.seed(0x0000000000006100L, 8, 0x0000000000006500L);
            ram.seed(0x0000000000006500L, 8, 0x1020304050607080L);
        }
    }

    /** Exact-width finite host storage; unused protocol methods fail explicitly. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long BASE = 0x4000L;
        private final byte[] bytes = new byte[0x4000];
        private final List<String> trace = new ArrayList<>();
        private int atomicCalls;

        Ram() {
            for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (i * 29 + 0x63);
        }

        private int index(long address, int width) {
            if (width < 1 || address < BASE || address - BASE > bytes.length - width) {
                throw new UnsupportedOperationException("Access outside finite RAM");
            }
            return (int) (address - BASE);
        }

        private long loadRaw(long address, int width) {
            int start = index(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) {
                value |= (bytes[start + i] & 0xFFL) << (8 * i);
            }
            return value;
        }

        private void storeRaw(long address, int width, long value) {
            int start = index(address, width);
            for (int i = 0; i < width; i++) {
                bytes[start + i] = (byte) (value >>> (8 * i));
            }
        }

        void seed(long address, int width, long value) {
            storeRaw(address, width, value);
        }

        private void effect(String op, long address, long value) {
            trace.add(op + "@" + Long.toUnsignedString(address, 16)
                    + "=" + Long.toUnsignedString(value, 16));
        }

        @Override public int readDword(long address) {
            int value = (int) loadRaw(address, 4);
            effect("R32", address, Integer.toUnsignedLong(value));
            return value;
        }

        @Override public long readQword(long address) {
            long value = loadRaw(address, 8);
            effect("R64", address, value);
            return value;
        }

        @Override public void writeDword(long address, int value) {
            storeRaw(address, 4, Integer.toUnsignedLong(value));
            effect("W32", address, Integer.toUnsignedLong(value));
        }

        @Override public void writeQword(long address, long value) {
            storeRaw(address, 8, value);
            effect("W64", address, value);
        }

        @Override public synchronized int lockedXaddDword(long address, int addend) {
            int before = (int) loadRaw(address, 4);
            int after = before + addend;
            storeRaw(address, 4, Integer.toUnsignedLong(after));
            atomicCalls++;
            trace.add("A32@" + Long.toUnsignedString(address, 16) + "="
                    + Integer.toUnsignedString(addend, 16) + "/"
                    + Integer.toUnsignedString(before, 16) + "/"
                    + Integer.toUnsignedString(after, 16));
            return before;
        }

        @Override public int readUnsignedByte(long address) { throw new UnsupportedOperationException("Unused readUnsignedByte"); }
        @Override public int readUnsignedWord(long address) { throw new UnsupportedOperationException("Unused readUnsignedWord"); }
        @Override public void writeByte(long address, int value) { throw new UnsupportedOperationException("Unused writeByte"); }
        @Override public void writeWord(long address, int value) { throw new UnsupportedOperationException("Unused writeWord"); }
        @Override public GovernmentPrimaryTail155Api.Bits128 read128(long address) { throw new UnsupportedOperationException("Unused read128"); }
        @Override public void write128(long address, GovernmentPrimaryTail155Api.Bits128 value) { throw new UnsupportedOperationException("Unused write128"); }
        @Override public void write128NonTemporal(long address, GovernmentPrimaryTail155Api.Bits128 value) { throw new UnsupportedOperationException("Unused write128NonTemporal"); }
        @Override public FullCopy437Api.Bits256 read256(long address) { throw new UnsupportedOperationException("Unused read256"); }
        @Override public void write256(long address, FullCopy437Api.Bits256 value) { throw new UnsupportedOperationException("Unused write256"); }
        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) { throw new UnsupportedOperationException("Unused write256NonTemporal"); }
        @Override public void sfence() { throw new UnsupportedOperationException("Unused sfence"); }
    }
}
