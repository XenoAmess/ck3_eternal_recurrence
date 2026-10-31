package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtCallee186WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtCallee186WitnessApi.Subject;
import org.xar.ck3.research.m5.GovernmentCrtCallee186WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m5.GovernmentCrtCallee186WitnessData.*;

/** Two finite source-derived actual185-caller to actual186-callee cases. */
public final class GovernmentCrtCaller186WitnessBook implements GovernmentCrtCallee186WitnessApi.Book {
    @Override public List<Witness> witnesses() {
        return List.of(nonzeroCalleeToCallerZero(), zeroCalleeToCallerUnsignedMinusOne());
    }

    private static Witness nonzeroCalleeToCallerZero() {
        long sp = 0x20_0008L;
        long argument = 0x8000_0001_0000_0000L;
        long rootReturn = 0x3456_789A_1111_2222L;
        VolatileBits entryV = v(0x1201_0000_0000_0000L, 0x1201_AAAA_BBBB_CCCCL,
                argument, 0x1201_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5201_0000_0000_0000L, 0x5201_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, -1L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(
                sp - 0x30, IMAGE + 0x4223F2DL,
                sp - 0x38, entryN.rbxBits(),
                sp - 0x60, IMAGE + 0x4223F00L));
        VolatileBits post = v(0xB201_0000_0000_0000L, 0xBADD_CAFE_0000_0000L,
                0xB201_C1C2_C3C4_C5C6L, 0xB201_D1D2_D3D4_D5D6L);
        Call inner = new Call(0x4223EFBL, TargetKind.DIRECT_RVA, 0x424DE78L,
                sp - 0x58, entryV, rbx(entryN, argument));
        NormalReturn expected = new NormalReturn(
                registers(post, 0L, post.rcxBits(), argument), rootReturn, sp + 8, entryN);
        return new Witness("caller-actualcallee-nonzeroHigh32-low32zero-to-zero", Subject.CALLER_3F24,
                entry, seed, List.of(new CallStep(inner, before, Map.of(), post)), before, expected);
    }

    private static Witness zeroCalleeToCallerUnsignedMinusOne() {
        long sp = 0x21_0008L;
        long argument = 0x9FED_CBA9_8765_4321L;
        long rootReturn = 0x3456_789A_3333_4444L;
        VolatileBits entryV = v(0x1202_0000_0000_0000L, 0x1202_AAAA_BBBB_CCCCL,
                argument, 0x1202_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5202_0000_0000_0000L, 0x5202_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, 0x6342_10FE_DCBA_9876L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(
                sp - 0x30, IMAGE + 0x4223F2DL,
                sp - 0x38, entryN.rbxBits(),
                sp - 0x60, IMAGE + 0x4223F11L));
        VolatileBits post = v(0xB202_0000_0000_0000L, 0xDEAD_BEEF_8000_0001L,
                0xB202_C1C2_C3C4_C5C6L, 0xB202_D1D2_D3D4_D5D6L);
        Call inner = new Call(0x4223F0CL, TargetKind.DIRECT_RVA, 0x424DEECL,
                sp - 0x58, registers(entryV, entryV.raxBits(), GLOBAL, argument), rbx(entryN, argument));
        NormalReturn expected = new NormalReturn(
                registers(post, 0xFFFF_FFFFL, post.rcxBits(), 0L), rootReturn, sp + 8, entryN);
        return new Witness("caller-actualcallee-zero-to-zeroExtendedFFFFFFFF", Subject.CALLER_3F24,
                entry, seed, List.of(new CallStep(inner, before, Map.of(), post)), before, expected);
    }
}
