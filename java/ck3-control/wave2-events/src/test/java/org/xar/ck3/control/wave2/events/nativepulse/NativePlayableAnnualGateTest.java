package org.xar.ck3.control.wave2.events.nativepulse;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.nativepulse.NativePlayableAnnualGate.*;

/** Arithmetic/source-bound regressions, not a claim that a runtime character belongs to the native scheduler bucket. */
final class NativePlayableAnnualGateTest {
    @Test void independentIntegerDivisionMatchesTheExactUnsignedNativeHashGateAcrossOverflowAndDateBounds() {
        BigInteger modulus = BigInteger.ONE.shiftLeft(32);
        for (long actor : new long[]{0, 1, 73, 29829, 0x7fffffffL, 0x80000000L, 0xffffffffL})
            for (int year : new int[]{-32768, -1, 0, 1066, 32767, Integer.MIN_VALUE, Integer.MAX_VALUE})
                for (int day = 0; day < 365; day++) {
                    var input = new Input(Executable.CURRENT_12004, actor, year, day);
                    BigInteger value = BigInteger.valueOf(year).add(BigInteger.valueOf(actor));
                    BigInteger seed = value.multiply(BigInteger.valueOf(0x2b3d)).add(BigInteger.valueOf(0x6d4f)).multiply(value).mod(modulus);
                    BigInteger candidate = seed.add(BigInteger.valueOf(day)).mod(modulus);
                    var actual = NativePlayableAnnualGate.evaluate(input);
                    assertEquals(seed.longValueExact(), actual.seedU32()); assertEquals(candidate.longValueExact(), actual.candidateU32());
                    assertEquals(candidate.mod(BigInteger.valueOf(365)).signum() == 0, actual.hashGateOpen());
                    assertFalse(actual.candidateBucketMembershipProven()); assertFalse(actual.eventSelected()); assertFalse(actual.materialCreditGranted());
                }
    }
    @Test void nativeInstructionDerivedReferenceValuesRemainExact() {
        assertEquals(1507016898L, NativePlayableAnnualGate.evaluate(new Input(Executable.CURRENT_12004, 73, 1066, 0)).seedU32());
        assertEquals(616832350L, NativePlayableAnnualGate.evaluate(new Input(Executable.CURRENT_12004, 29829, 1066, 0)).seedU32());
        assertEquals(3994603828L, NativePlayableAnnualGate.evaluate(new Input(Executable.CURRENT_12004, 0xffffffffL, 1066, 0)).seedU32());
    }
    @Test void strictJsonRoundTripRejectsWrongSourcesBooleansFloatsAndRangeDrift() {
        var input = new Input(Executable.CURRENT_12004, 0xffffffffL, 1066, 364);
        byte[] raw = NativePlayableAnnualGate.encode(input); assertEquals(input, NativePlayableAnnualGate.decode(raw));
        for (String field : new String[]{"character_id_u32", "year", "day_of_year"}) {
            var wrong = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "executable_sha256", "character_id_u32", "year", "day_of_year")).deepCopy(); wrong.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> NativePlayableAnnualGate.decode(StrictJson.canonical(wrong)));
            var floating = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "executable_sha256", "character_id_u32", "year", "day_of_year")).deepCopy(); floating.put(field, 1.0);
            assertThrows(IllegalArgumentException.class, () -> NativePlayableAnnualGate.decode(StrictJson.canonical(floating)));
        }
        String text = new String(raw, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> NativePlayableAnnualGate.decode(text.replace(NativePlayableAnnualGate.EXECUTABLE_SHA256, "a".repeat(64)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new Input(Executable.CURRENT_12004, 0x100000000L, 1066, 0));
        assertThrows(IllegalArgumentException.class, () -> new Input(Executable.CURRENT_12004, 1, 1066, 365));
    }
}
