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

/** Five finite source-derived direct-callee cases, independent of all subjects. */
public final class GovernmentCrtCallee186WitnessBook implements GovernmentCrtCallee186WitnessApi.Book {
    @Override public List<Witness> witnesses() {
        return List.of(sentinelLowZero(), sentinelLowOneZeroArgument(),
                nonsentinelLowZero(), nonsentinelLowHighBit(), freshSavedWords());
    }

    private static Witness sentinelLowZero() {
        long sp = 0x10_0008L;
        long argument = 0x8000_0001_0000_0000L;
        long rootReturn = 0x1234_5678_1111_2222L;
        VolatileBits entryV = v(0x1101_0000_0000_0000L, 0x1101_AAAA_BBBB_CCCCL,
                argument, 0x1101_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5101_0000_0000_0000L, 0x5101_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, -1L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(sp - 8, entryN.rbxBits(),
                sp - 0x30, IMAGE + 0x4223F00L));
        VolatileBits post = v(0xB101_0000_0000_0000L, 0xFACE_CAFE_0000_0000L,
                0xB101_C1C2_C3C4_C5C6L, 0xB101_D1D2_D3D4_D5D6L);
        Call call = new Call(0x4223EFBL, TargetKind.DIRECT_RVA, 0x424DE78L,
                sp - 0x28, entryV, rbx(entryN, argument));
        NormalReturn expected = new NormalReturn(
                registers(post, argument, post.rcxBits(), argument), rootReturn, sp + 8, entryN);
        return new Witness("callee-sentinel-low32zero-high32nonzero", Subject.CALLEE,
                entry, seed, List.of(new CallStep(call, before, Map.of(), post)), before, expected);
    }

    private static Witness sentinelLowOneZeroArgument() {
        long sp = 0x11_0008L;
        long rootReturn = 0x1234_5678_3333_4444L;
        VolatileBits entryV = v(0x1102_0000_0000_0000L, 0x1102_AAAA_BBBB_CCCCL,
                0L, 0x1102_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5102_0000_0000_0000L, 0x5102_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, -1L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(sp - 8, entryN.rbxBits(),
                sp - 0x30, IMAGE + 0x4223F00L));
        VolatileBits post = v(0xB102_0000_0000_0000L, 0xFACE_CAFE_0000_0001L,
                0xB102_C1C2_C3C4_C5C6L, 0xB102_D1D2_D3D4_D5D6L);
        Call call = new Call(0x4223EFBL, TargetKind.DIRECT_RVA, 0x424DE78L,
                sp - 0x28, entryV, rbx(entryN, 0L));
        NormalReturn expected = new NormalReturn(
                registers(post, 0L, post.rcxBits(), 0L), rootReturn, sp + 8, entryN);
        return new Witness("callee-sentinel-low32one-zero-entryRCX", Subject.CALLEE,
                entry, seed, List.of(new CallStep(call, before, Map.of(), post)), before, expected);
    }

    private static Witness nonsentinelLowZero() {
        long sp = 0x12_0008L;
        long argument = 0x89AB_CDEF_0123_4567L;
        long rootReturn = 0x1234_5678_5555_6666L;
        VolatileBits entryV = v(0x1103_0000_0000_0000L, 0x1103_AAAA_BBBB_CCCCL,
                argument, 0x1103_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5103_0000_0000_0000L, 0x5103_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, 0x71A2_B3C4_D5E6_F708L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(sp - 8, entryN.rbxBits(),
                sp - 0x30, IMAGE + 0x4223F11L));
        VolatileBits post = v(0xB103_0000_0000_0000L, 0x1357_2468_0000_0000L,
                0xB103_C1C2_C3C4_C5C6L, 0xB103_D1D2_D3D4_D5D6L);
        Call call = new Call(0x4223F0CL, TargetKind.DIRECT_RVA, 0x424DEECL,
                sp - 0x28, registers(entryV, entryV.raxBits(), GLOBAL, argument), rbx(entryN, argument));
        NormalReturn expected = new NormalReturn(
                registers(post, argument, post.rcxBits(), argument), rootReturn, sp + 8, entryN);
        return new Witness("callee-nonsentinel-literal-address-low32zero", Subject.CALLEE,
                entry, seed, List.of(new CallStep(call, before, Map.of(), post)), before, expected);
    }

    private static Witness nonsentinelLowHighBit() {
        long sp = 0x13_0008L;
        long argument = 0xF123_4567_89AB_CDEFL;
        long rootReturn = 0x1234_5678_7777_8888L;
        VolatileBits entryV = v(0x1104_0000_0000_0000L, 0x1104_AAAA_BBBB_CCCCL,
                argument, 0x1104_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5104_0000_0000_0000L, 0x5104_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, 0x1234_9876_ABCD_EF01L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(sp - 8, entryN.rbxBits(),
                sp - 0x30, IMAGE + 0x4223F11L));
        VolatileBits post = v(0xB104_0000_0000_0000L, 0x8000_0000_8000_0000L,
                0xB104_C1C2_C3C4_C5C6L, 0xB104_D1D2_D3D4_D5D6L);
        Call call = new Call(0x4223F0CL, TargetKind.DIRECT_RVA, 0x424DEECL,
                sp - 0x28, registers(entryV, entryV.raxBits(), GLOBAL, argument), rbx(entryN, argument));
        NormalReturn expected = new NormalReturn(
                registers(post, 0L, post.rcxBits(), 0L), rootReturn, sp + 8, entryN);
        return new Witness("callee-nonsentinel-low32highbit-nonzero", Subject.CALLEE,
                entry, seed, List.of(new CallStep(call, before, Map.of(), post)), before, expected);
    }

    private static Witness freshSavedWords() {
        long sp = 0x14_0008L;
        long argument = 0x8122_3344_5566_7788L;
        long rootReturn = 0x2345_6789_1111_2222L;
        long freshRbx = 0xF0E1_D2C3_B4A5_9687L;
        long freshReturn = 0x1234_5678_ABCD_EF01L;
        VolatileBits entryV = v(0x1105_0000_0000_0000L, 0x1105_AAAA_BBBB_CCCCL,
                argument, 0x1105_DDDD_EEEE_FFFFL);
        NonvolatileBits entryN = n(0x5105_0000_0000_0000L, 0x5105_A1A2_A3A4_A5A6L);
        Entry entry = new Entry(IMAGE, sp, entryV, entryN);
        Map<Long, Integer> seed = words(GLOBAL, -1L, sp, rootReturn);
        Map<Long, Integer> before = overlay(seed, words(sp - 8, entryN.rbxBits(),
                sp - 0x30, IMAGE + 0x4223F00L));
        Map<Long, Integer> mutation = words(sp - 8, freshRbx, sp, freshReturn);
        VolatileBits post = v(0xB105_0000_0000_0000L, 0xABCD_EF01_0000_0000L,
                0xB105_C1C2_C3C4_C5C6L, 0xB105_D1D2_D3D4_D5D6L);
        Call call = new Call(0x4223EFBL, TargetKind.DIRECT_RVA, 0x424DE78L,
                sp - 0x28, entryV, rbx(entryN, argument));
        NormalReturn expected = new NormalReturn(
                registers(post, argument, post.rcxBits(), argument), freshReturn, sp + 8, rbx(entryN, freshRbx));
        return new Witness("callee-fresh-savedRBX-and-entryRET", Subject.CALLEE,
                entry, seed, List.of(new CallStep(call, before, mutation, post)),
                overlay(before, mutation), expected);
    }
}
