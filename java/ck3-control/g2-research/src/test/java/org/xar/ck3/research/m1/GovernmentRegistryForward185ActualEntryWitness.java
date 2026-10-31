package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

public final class GovernmentRegistryForward185ActualEntryWitness {
    public static void main(String[] args) {
        long B = 0x100000000L;
        long parentS = 0x70000038L;
        long childS = 0x70000008L;
        long parentRET = 0x1234567887654321L;
        long subject = 0x4455667788990011L;
        long oldRBX = 0xAABBCCDDEEFF0011L;
        long oldRBP = 0x8877665544332211L;
        long oldRSI = 0x501L;
        long oldRDI = 0x502L;
        long oldR12 = 0xABCDEF0000000503L;
        long oldR13 = 0x504L;
        long oldR14 = 0x505L;
        long oldR15 = 0x506L;
        Bits128 oldXMM6 = vector(0x507L);

        MemoryImage memory = new MemoryImage();
        memory.writeQword(B + 0x5C5CB68L, -1L);
        memory.writeQword(parentS, parentRET);

        VolatileBits inputV = bits(0x3100L, 0x301L, subject, 0x303L);
        NonvolatileBits inputN = new NonvolatileBits(oldRBX, oldRBP, oldRSI, oldRDI, oldR12, oldR13, oldR14, oldR15, oldXMM6);

        GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(B, parentS, inputV, inputN);

        VolatileBits expectedV = new VolatileBits(2L, 0x70000020L, 0x6FFFFFE0L, 0x6FFFFFE8L, 0x70000028L, inputV.r10Bits(), inputV.r11Bits(), inputV.xmm0(), inputV.xmm1(), inputV.xmm2(), inputV.xmm3(), inputV.xmm4(), inputV.xmm5());
        NonvolatileBits expectedN = new NonvolatileBits(subject, 0x70000000L, oldRSI, oldRDI, oldR12, oldR13, oldR14, oldR15, oldXMM6);

        OpaqueCall expectedCall = new OpaqueCall(0x424DF29L, 0x424DB38L, 0x6FFFFFC0L, expectedV, expectedN);
        VolatileBits postV = bits(0x9100L, 0x1234567800000000L, 0x902L, 0x903L);

        Runnable sideEffect = () -> {
            equal(memory.readQword(0x70000030L), oldRBX, "saved callerRBX");
            equal(memory.readQword(childS), B + 0x4223F00L, "childreturn");
            equal(memory.readQword(0x6FFFFFB8L), B + 0x424DF2EL, "physicalDB38ret");
            equal(memory.readQword(0x70000010L), B + 0x5C5D698L, "staticRCXhome");
            equal(memory.readQword(0x70000018L), subject, "oldRCXhome");
            memory.writeQword(0x72000000L, 0x1020304050607080L);
        };

        CallScript script = new CallScript(0L);
        script.expect(expectedCall, postV, sideEffect);

        GovernmentPrimaryTail155Api.Calls calls = GovernmentRegistryForward185Calls.bind(B, memory, script);

        GovernmentCallee164Api.NormalReturn actual = GovernmentRegistryEntry183.execute(entry, memory, calls);

        VolatileBits finalV = new VolatileBits(subject, postV.rcxBits(), subject, postV.r8Bits(), postV.r9Bits(), postV.r10Bits(), postV.r11Bits(), postV.xmm0(), postV.xmm1(), postV.xmm2(), postV.xmm3(), postV.xmm4(), postV.xmm5());
        GovernmentCallee164Api.NormalReturn expectedReturn = new GovernmentCallee164Api.NormalReturn(finalV, inputN, parentRET, 0x70000040L);

        equal(expectedReturn, actual, "NormalReturn");
        equal(memory.readQword(B + 0x5C5CB68L), -1L, "global still -1");
        equal(memory.readQword(0x72000000L), 0x1020304050607080L, "effect retained");
        script.done(0);
    }
}
