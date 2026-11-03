package org.xar.ck3.research.m3.fa90fp267;

import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Two finite direct103 public-DATA witnesses. Original ASM oracle and sparse
 * DATA images were sealed before any new267 API/body read. Existing old245 and
 * current265 caller were known source. Global contents are artificial DATA.
 * No binder/negative/native/hardware or opaque-child algorithm qualification.
 */
public final class Fa90Protocol267Manual {
    private Fa90Protocol267Manual() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 0) throw new IllegalArgumentException("No arguments accepted");
        runCase(false);
        runCase(true);
        System.out.print("Fa90Protocol267Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean replacementZeroCountNonzero) throws Exception {
        Fixture f = new Fixture();
        int[] callCount = {0};
        Fa90Fp267Api.Calls offered = actual -> {
            int ordinal = ++callCount[0];
            if (ordinal == 1) {
                GovernmentCrtBoundary185Api.Call expectedCall = replacementZeroCountNonzero
                        ? f.zeroFirstCall : f.firstCall;
                GovernmentCrtBoundary185Api.Entry expectedChild = replacementZeroCountNonzero
                        ? f.zeroFirstChild : f.firstChild;
                if (!actual.original().equals(expectedCall)
                        || !actual.childEntry().equals(expectedChild)
                        || actual.directionFlagSet() != false
                        || actual.preMxcsr() != f.fpEntry
                        || actual.returnRipBits() != 0x00000001E424FAB1L) {
                    throw new AssertionError("First complete frame differs from sealed267 DATA");
                }
                if (replacementZeroCountNonzero) {
                    f.ram.writeQword(0x000000000000B090L, 0x000000000000BC00L);
                    f.ram.writeQword(0x00000001E5C5DCD8L, 0x0A0B0C0D0E0F1011L);
                    f.ram.writeDword(0x000000000000BC10L, 0xF0000001);
                    f.ram.writeQword(0x000000000000A010L, 0xD0C0B0A090807060L);
                    f.ram.writeQword(0x000000000000A000L, 0xE1D1C1B1A1918171L);
                    f.ram.writeQword(0x000000000000A008L, 0x00000001E0607080L);
                    return f.zeroFirstNormal;
                }
                f.ram.writeQword(0x000000000000B090L, 0x000000000000BC00L);
                f.ram.writeQword(0x00000001E5C5DCD8L, 0x0A0B0C0D0E0F1011L);
                f.ram.writeDword(0x000000000000BC10L, 0x00000000);
                return f.firstNormal;
            }
            if (ordinal == 2 && !replacementZeroCountNonzero) {
                if (!actual.original().equals(f.secondCall)
                        || !actual.childEntry().equals(f.secondChild)
                        || actual.directionFlagSet() != true
                        || actual.preMxcsr() != f.fpAfterFirst
                        || actual.returnRipBits() != 0x00000001E424FAD8L) {
                    throw new AssertionError("Second complete frame differs from sealed267 DATA");
                }
                f.ram.writeQword(0x000000000000B090L, 0xD00D998877665544L);
                return f.secondNormal;
            }
            if (ordinal == 3 && !replacementZeroCountNonzero) {
                if (!actual.original().equals(f.thirdCall)
                        || !actual.childEntry().equals(f.thirdChild)
                        || actual.directionFlagSet() != false
                        || actual.preMxcsr() != f.fpAfterSecond
                        || actual.returnRipBits() != 0x00000001E424FAECL) {
                    throw new AssertionError("Third complete frame differs from sealed267 DATA");
                }
                f.ram.writeQword(0x000000000000A010L, 0xBEEFFACE12345678L);
                f.ram.writeQword(0x000000000000A000L, 0xCEF0112233445566L);
                f.ram.writeQword(0x000000000000A008L, 0x00000001E0708090L);
                return f.thirdNormal;
            }
            throw new AssertionError("Unexpected opaque call ordinal " + ordinal);
        };
        GovernmentCrtBoundary185Api.LoopBudget budget = (header, guard) -> {
            throw new AssertionError("Straight-line original103 used loop budget");
        };
        QueueFp604Api.Input input = new QueueFp604Api.Input(
                new FullCopy437Api.Input(replacementZeroCountNonzero ? f.zeroEntry : f.entry,
                        false, budget), f.fpEntry);
        QueueFp604Api.Outcome actual = Fa90FullState267.execute(input, f.ram, offered);
        List<String> expectedTrace = replacementZeroCountNonzero
                ? f.expectedZeroTrace : f.expectedNormalTrace;
        if (!f.ram.trace.equals(expectedTrace)) {
            throw new AssertionError("Exact memory trace differs: " + f.ram.trace
                    + " expected " + expectedTrace);
        }
        if (callCount[0] != (replacementZeroCountNonzero ? 1 : 3)) {
            throw new AssertionError("Opaque call count differs");
        }
        QueueFp604Api.Normal expected = replacementZeroCountNonzero
                ? f.expectedZeroNormal : f.expectedNormal;
        QueueFp604Api.Mxcsr expectedFp = replacementZeroCountNonzero
                ? f.fpAfterFirst : f.fpAfterThird;
        if (!(actual instanceof QueueFp604Api.Normal normal)
                || !normal.base().equals(expected.base())
                || normal.postMxcsr() != expectedFp) {
            throw new AssertionError("Final complete V/N/SP/RIP/DF/partialFP differs");
        }
        String actualRamHash = HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(f.ram.bytes));
        String expectedRamHash = replacementZeroCountNonzero
                ? "a03554725097a7d1a168cb75cc183ed5a3f036335af49ca192d66cbc981d10f4"
                : "ea19ded38a55b1cee7bd8ec4ea9e6d83fbf5b7bc6707cc16d621a19f6036f449";
        if (!actualRamHash.equals(expectedRamHash)) {
            throw new AssertionError("Whole sparse RAM differs from sealed DATA: " + actualRamHash);
        }
    }

    private static final class Fixture {
        final QueueFp604Api.Mxcsr fpEntry = new QueueFp604Api.Mxcsr(0x0010, 0x0011);
        final QueueFp604Api.Mxcsr fpAfterFirst = new QueueFp604Api.Mxcsr(0x0042, 0x0043);
        final QueueFp604Api.Mxcsr fpAfterSecond = new QueueFp604Api.Mxcsr(0x0101, 0x0103);
        final QueueFp604Api.Mxcsr fpAfterThird = new QueueFp604Api.Mxcsr(0x0202, 0x0203);
        final GovernmentPrimaryTail155Api.VolatileBits entryV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x7201415263748596L, 0x000000000000B000L, 0x000000000000C000L, 0x7204415263748596L, 0x7205415263748596L, 0x7206415263748596L, 0x7207415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x7240415263748596L, 0x7241415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7242415263748596L, 0x7243415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7244415263748596L, 0x7245415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7246415263748596L, 0x7247415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7248415263748596L, 0x7249415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x724A415263748596L, 0x724B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits zeroEntryV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x7201415263748596L, 0x000000000000B000L, 0x0000000000000000L, 0x7204415263748596L, 0x7205415263748596L, 0x7206415263748596L, 0x7207415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x7240415263748596L, 0x7241415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7242415263748596L, 0x7243415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7244415263748596L, 0x7245415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7246415263748596L, 0x7247415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7248415263748596L, 0x7249415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x724A415263748596L, 0x724B415263748596L));
        final GovernmentPrimaryTail155Api.NonvolatileBits entryN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x123456789ABCDEF0L, 0x23456789ABCDEF01L, 0x3456789ABCDEF012L, 0x456789ABCDEF0123L, 0x56789ABCDEF01234L, 0x6789ABCDEF012345L, 0x789ABCDEF0123456L, 0x89ABCDEF01234567L,
                new GovernmentPrimaryTail155Api.Bits128(0x9ABCDEF012345678L, 0xABCDEF0123456789L));
        final GovernmentPrimaryTail155Api.NonvolatileBits callN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x000000000000C000L, 0x23456789ABCDEF01L, 0x3456789ABCDEF012L, 0x000000000000B000L, 0x56789ABCDEF01234L, 0x6789ABCDEF012345L, 0x789ABCDEF0123456L, 0x89ABCDEF01234567L,
                new GovernmentPrimaryTail155Api.Bits128(0x9ABCDEF012345678L, 0xABCDEF0123456789L));
        final GovernmentPrimaryTail155Api.NonvolatileBits zeroCallN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0x0000000000000000L, 0x23456789ABCDEF01L, 0x3456789ABCDEF012L, 0x000000000000B000L, 0x56789ABCDEF01234L, 0x6789ABCDEF012345L, 0x789ABCDEF0123456L, 0x89ABCDEF01234567L,
                new GovernmentPrimaryTail155Api.Bits128(0x9ABCDEF012345678L, 0xABCDEF0123456789L));
        final GovernmentPrimaryTail155Api.NonvolatileBits finalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0xBEEFFACE12345678L, 0x23456789ABCDEF01L, 0x3456789ABCDEF012L, 0xCEF0112233445566L, 0x56789ABCDEF01234L, 0x6789ABCDEF012345L, 0x789ABCDEF0123456L, 0x89ABCDEF01234567L,
                new GovernmentPrimaryTail155Api.Bits128(0x9ABCDEF012345678L, 0xABCDEF0123456789L));
        final GovernmentPrimaryTail155Api.NonvolatileBits zeroFinalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
                0xD0C0B0A090807060L, 0x23456789ABCDEF01L, 0x3456789ABCDEF012L, 0xE1D1C1B1A1918171L, 0x56789ABCDEF01234L, 0x6789ABCDEF012345L, 0x789ABCDEF0123456L, 0x89ABCDEF01234567L,
                new GovernmentPrimaryTail155Api.Bits128(0x9ABCDEF012345678L, 0xABCDEF0123456789L));
        final GovernmentPrimaryTail155Api.VolatileBits firstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x7201415263748596L, 0x000000000000B800L, 0x000000000000C000L, 0x7204415263748596L, 0x7205415263748596L, 0x7206415263748596L, 0x7207415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x7240415263748596L, 0x7241415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7242415263748596L, 0x7243415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7244415263748596L, 0x7245415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7246415263748596L, 0x7247415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7248415263748596L, 0x7249415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x724A415263748596L, 0x724B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits zeroFirstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x7201415263748596L, 0x000000000000B800L, 0x0000000000000000L, 0x7204415263748596L, 0x7205415263748596L, 0x7206415263748596L, 0x7207415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x7240415263748596L, 0x7241415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7242415263748596L, 0x7243415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7244415263748596L, 0x7245415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7246415263748596L, 0x7247415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x7248415263748596L, 0x7249415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x724A415263748596L, 0x724B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits secondV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x00000001E542F330L, 0x000000000000BC00L, 0x9303415263748596L, 0x9304415263748596L, 0x9305415263748596L, 0x9306415263748596L, 0x9307415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x9340415263748596L, 0x9341415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9342415263748596L, 0x9343415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9344415263748596L, 0x9345415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9346415263748596L, 0x9347415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9348415263748596L, 0x9349415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x934A415263748596L, 0x934B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits thirdV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xB501415263748596L, 0x000000000000C000L, 0xB503415263748596L, 0xB504415263748596L, 0xB505415263748596L, 0xB506415263748596L, 0xB507415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0xB540415263748596L, 0xB541415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB542415263748596L, 0xB543415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB544415263748596L, 0xB545415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB546415263748596L, 0xB547415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB548415263748596L, 0xB549415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB54A415263748596L, 0xB54B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits postFirstV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x9301415263748596L, 0x9302415263748596L, 0x9303415263748596L, 0x9304415263748596L, 0x9305415263748596L, 0x9306415263748596L, 0x9307415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x9340415263748596L, 0x9341415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9342415263748596L, 0x9343415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9344415263748596L, 0x9345415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9346415263748596L, 0x9347415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9348415263748596L, 0x9349415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x934A415263748596L, 0x934B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits postSecondV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xB501415263748596L, 0xB502415263748596L, 0xB503415263748596L, 0xB504415263748596L, 0xB505415263748596L, 0xB506415263748596L, 0xB507415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0xB540415263748596L, 0xB541415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB542415263748596L, 0xB543415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB544415263748596L, 0xB545415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB546415263748596L, 0xB547415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB548415263748596L, 0xB549415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xB54A415263748596L, 0xB54B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits postThirdV = new GovernmentPrimaryTail155Api.VolatileBits(
                0xD701415263748596L, 0xD702415263748596L, 0xD703415263748596L, 0xD704415263748596L, 0xD705415263748596L, 0xD706415263748596L, 0xD707415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0xD740415263748596L, 0xD741415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xD742415263748596L, 0xD743415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xD744415263748596L, 0xD745415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xD746415263748596L, 0xD747415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xD748415263748596L, 0xD749415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0xD74A415263748596L, 0xD74B415263748596L));
        final GovernmentPrimaryTail155Api.VolatileBits zeroFinalV = new GovernmentPrimaryTail155Api.VolatileBits(
                0x00000001E542F330L, 0x000000000000BC00L, 0x9303415263748596L, 0x9304415263748596L, 0x9305415263748596L, 0x9306415263748596L, 0x9307415263748596L,
                new GovernmentPrimaryTail155Api.Bits128(0x9340415263748596L, 0x9341415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9342415263748596L, 0x9343415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9344415263748596L, 0x9345415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9346415263748596L, 0x9347415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x9348415263748596L, 0x9349415263748596L),
                new GovernmentPrimaryTail155Api.Bits128(0x934A415263748596L, 0x934B415263748596L));
        final GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(0x00000001E0000000L, 0x000000000000A008L, entryV, entryN);
        final GovernmentCrtBoundary185Api.Entry zeroEntry = new GovernmentCrtBoundary185Api.Entry(0x00000001E0000000L, 0x000000000000A008L, zeroEntryV, entryN);
        final GovernmentCrtBoundary185Api.Call firstCall = new GovernmentCrtBoundary185Api.Call(0x000000000424FAACL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x00000000042568FCL, 0x0000000000009FE0L, firstV, callN);
        final GovernmentCrtBoundary185Api.Entry firstChild = new GovernmentCrtBoundary185Api.Entry(0x00000001E0000000L, 0x0000000000009FD8L, firstV, callN);
        final GovernmentCrtBoundary185Api.Call zeroFirstCall = new GovernmentCrtBoundary185Api.Call(0x000000000424FAACL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x00000000042568FCL, 0x0000000000009FE0L, zeroFirstV, zeroCallN);
        final GovernmentCrtBoundary185Api.Entry zeroFirstChild = new GovernmentCrtBoundary185Api.Entry(0x00000001E0000000L, 0x0000000000009FD8L, zeroFirstV, zeroCallN);
        final GovernmentCrtBoundary185Api.Call secondCall = new GovernmentCrtBoundary185Api.Call(0x000000000424FAD3L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x00000000042566FCL, 0x0000000000009FE0L, secondV, callN);
        final GovernmentCrtBoundary185Api.Entry secondChild = new GovernmentCrtBoundary185Api.Entry(0x00000001E0000000L, 0x0000000000009FD8L, secondV, callN);
        final GovernmentCrtBoundary185Api.Call thirdCall = new GovernmentCrtBoundary185Api.Call(0x000000000424FAE7L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x0000000004256670L, 0x0000000000009FE0L, thirdV, callN);
        final GovernmentCrtBoundary185Api.Entry thirdChild = new GovernmentCrtBoundary185Api.Entry(0x00000001E0000000L, 0x0000000000009FD8L, thirdV, callN);
        final QueueFp604Api.Normal firstNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postFirstV, 0x00000001E424FAB1L, 0x0000000000009FE0L, callN),
                true), fpAfterFirst);
        final QueueFp604Api.Normal zeroFirstNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postFirstV, 0x00000001E424FAB1L, 0x0000000000009FE0L, zeroCallN),
                true), fpAfterFirst);
        final QueueFp604Api.Normal secondNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postSecondV, 0x00000001E424FAD8L, 0x0000000000009FE0L, callN),
                false), fpAfterSecond);
        final QueueFp604Api.Normal thirdNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postThirdV, 0x00000001E424FAECL, 0x0000000000009FE0L, callN),
                true), fpAfterThird);
        final QueueFp604Api.Normal expectedNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(postThirdV, 0x00000001E0708090L, 0x000000000000A010L, finalN),
                true), fpAfterThird);
        final QueueFp604Api.Normal expectedZeroNormal = new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(zeroFinalV, 0x00000001E0607080L, 0x000000000000A010L, zeroFinalN),
                true), fpAfterFirst);
        final List<String> expectedNormalTrace = List.of(
                "W64@a010=123456789abcdef0",
                "W64@a000=456789abcdef0123",
                "R64@b090=b800",
                "W64@9fd8=1e424fab1",
                "W64@b090=bc00",
                "W64@1e5c5dcd8=a0b0c0d0e0f1011",
                "W32@bc10=0",
                "R64@b090=bc00",
                "R64@1e5c5dcd8=a0b0c0d0e0f1011",
                "R32@bc10=0",
                "W64@9fd8=1e424fad8",
                "W64@b090=d00d998877665544",
                "W64@b090=c000",
                "W64@9fd8=1e424faec",
                "W64@a010=beefface12345678",
                "W64@a000=cef0112233445566",
                "W64@a008=1e0708090",
                "R64@a010=beefface12345678",
                "R64@a000=cef0112233445566",
                "R64@a008=1e0708090");
        final List<String> expectedZeroTrace = List.of(
                "W64@a010=123456789abcdef0",
                "W64@a000=456789abcdef0123",
                "R64@b090=b800",
                "W64@9fd8=1e424fab1",
                "W64@b090=bc00",
                "W64@1e5c5dcd8=a0b0c0d0e0f1011",
                "W32@bc10=f0000001",
                "W64@a010=d0c0b0a090807060",
                "W64@a000=e1d1c1b1a1918171",
                "W64@a008=1e0607080",
                "R64@b090=bc00",
                "R64@1e5c5dcd8=a0b0c0d0e0f1011",
                "R32@bc10=f0000001",
                "W64@b090=0",
                "R64@a010=d0c0b0a090807060",
                "R64@a000=e1d1c1b1a1918171",
                "R64@a008=1e0607080");
        final Ram ram = new Ram();

        Fixture() {
            ram.seed(0x000000000000A008L, 8, 0x00000001E0102030L);
            ram.seed(0x000000000000B090L, 8, 0x000000000000B800L);
            ram.seed(0x000000000000B810L, 4, 0x12345678L);
            ram.seed(0x000000000000BC10L, 4, 0x00000002L);
        }
    }

    /** Finite storage only: low stack/heap plus explicit artificial global8B. */
    private static final class Ram implements FullCopy437Api.Memory {
        private static final long LOW_BASE = 0x8000L;
        private static final int LOW_LENGTH = 0x7000;
        private static final long GLOBAL = 0x00000001E5C5DCD8L;
        private final byte[] bytes = new byte[0x7008];
        private final List<String> trace = new ArrayList<>();

        Ram() {
            for (int i = 0; i < LOW_LENGTH; i++) bytes[i] = (byte) (i * 31 + 0x27);
            seed(GLOBAL, 8, 0x5555666677778888L); // Artificial DATA, Native contents NOT_HELD.
        }

        private int index(long address, int width) {
            if (width < 1) throw new UnsupportedOperationException("Invalid exact width");
            if (address >= LOW_BASE && address - LOW_BASE <= LOW_LENGTH - width) {
                return (int) (address - LOW_BASE);
            }
            if (address >= GLOBAL && address - GLOBAL <= 8L - width) {
                return LOW_LENGTH + (int) (address - GLOBAL);
            }
            throw new UnsupportedOperationException("Unmapped sparse address; LEA has no dataread");
        }

        private long loadRaw(long address, int width) {
            int start = index(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) value |= (bytes[start + i] & 0xFFL) << (8 * i);
            return value;
        }

        private void storeRaw(long address, int width, long value) {
            int start = index(address, width);
            for (int i = 0; i < width; i++) bytes[start + i] = (byte) (value >>> (8 * i));
        }

        void seed(long address, int width, long value) { storeRaw(address, width, value); }

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
        @Override public int lockedXaddDword(long address, int addend) { throw new UnsupportedOperationException("No atomic operation in original103"); }
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
