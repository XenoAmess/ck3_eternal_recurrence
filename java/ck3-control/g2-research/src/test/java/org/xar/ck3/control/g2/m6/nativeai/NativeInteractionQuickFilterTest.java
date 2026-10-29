package org.xar.ck3.control.g2.m6.nativeai;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.nativeai.NativeInteractionQuickFilter.*;

final class NativeInteractionQuickFilterTest {
    private static final AdultThresholds ADULT = new AdultThresholds(16, 18);
    private static CharacterFacts person(int sex, int preference, int age) {
        return new CharacterFacts(age, new AttractionRaw(sex, preference), new MissingComponent());
    }
    private static PreparedFlags flags(QuickFlags quick, int sex, int preference) {
        return derive(quick, new AttractionRaw(sex, preference));
    }

    @Test void currentSixWayOwnerPreferenceTableUsesRawSexComparisons() {
        boolean[][] expectedForOwnerZero = {{false, true}, {true, false}, {true, true},
                {false, false}, {false, false}, {false, false}};
        QuickFlags quick = new QuickFlags(false, false, true, false);
        for (int preference = 0; preference < 6; preference++) {
            PreparedFlags prepared = flags(quick, 0, preference);
            assertEquals(expectedForOwnerZero[preference][0], passes(prepared, person(0, 2, 20), ADULT));
            assertEquals(expectedForOwnerZero[preference][1], passes(prepared, person(1, 2, 20), ADULT));
        }
        assertTrue(passes(flags(quick, 1, 0), person(0, 2, 20), ADULT));
        assertFalse(passes(flags(quick, 1, 0), person(1, 2, 20), ADULT));
        // Native CMP ownerSex,1 and TEST ownerSex differ for noncanonical bytes.
        assertTrue(passes(flags(quick, 2, 0), person(0, 2, 20), ADULT));
        assertTrue(passes(flags(quick, 2, 0), person(1, 2, 20), ADULT));
        assertFalse(passes(flags(quick, 2, 1), person(0, 2, 20), ADULT));
        assertFalse(passes(flags(quick, 0, 255), person(1, 2, 20), ADULT));
    }

    @Test void targetAttractionIsIndependentlyEvaluatedInTheOtherDirection() {
        PreparedFlags prepared = flags(new QuickFlags(false, true, false, false), 0, 5);
        boolean[][] expected = {{false, true}, {true, false}, {true, true},
                {false, false}, {false, false}, {false, false}};
        for (int preference = 0; preference < 6; preference++) {
            assertEquals(expected[preference][0], passes(prepared, person(0, preference, 20), ADULT));
            assertEquals(expected[preference][1], passes(prepared, person(1, preference, 20), ADULT));
        }
        assertTrue(passes(flags(new QuickFlags(false, false, false, false), 0, 5),
                person(1, 255, 20), ADULT));
    }

    @Test void adultGateUsesIndependentCurrentSettingsAndSignedWordInclusiveBoundary() {
        PreparedFlags prepared = flags(new QuickFlags(true, false, false, false), 0, 0);
        assertFalse(passes(prepared, person(0, 2, 15), ADULT));
        assertTrue(passes(prepared, person(0, 2, 16), ADULT));
        assertFalse(passes(prepared, person(1, 2, 17), ADULT));
        assertTrue(passes(prepared, person(1, 2, 18), ADULT));
        assertFalse(passes(prepared, person(0, 2, -1), ADULT));
        assertTrue(passes(prepared, person(0, 2, -1), new AdultThresholds(-1, 99)));
    }

    @Test void prisonGateRequiresBothComponentAndItsNativePointer() {
        PreparedFlags prepared = flags(new QuickFlags(false, false, false, true), 0, 0);
        assertFalse(passes(prepared, person(1, 2, 20), ADULT));
        assertFalse(passes(prepared, new CharacterFacts(20, new AttractionRaw(1, 2),
                new PresentComponent(false)), ADULT));
        assertTrue(passes(prepared, new CharacterFacts(20, new AttractionRaw(1, 2),
                new PresentComponent(true)), ADULT));
    }

    @Test void reverseSwapRemovalKeepsActualSurvivorOrderAndExplicitFallback() {
        var a = new ResolvedCandidate(10, Resolution.EXACT_NATIVE_LOOKUP, person(0, 2, 20));
        var b = new ResolvedCandidate(20, Resolution.EXACT_NATIVE_LOOKUP, person(0, 2, 15));
        var c = new ResolvedCandidate(30, Resolution.EXACT_NATIVE_LOOKUP, person(0, 2, 20));
        var d = new ResolvedCandidate(40, Resolution.EXACT_NATIVE_LOOKUP, person(0, 2, 20));
        List<ResolvedCandidate> original = List.of(a, b, c, d);
        assertEquals(List.of(a, d, c), filter(original,
                flags(new QuickFlags(true, false, false, false), 0, 0), ADULT));
        assertEquals(4, original.size());
        var fallback = new ResolvedCandidate(0xFFFF_FFFFL, Resolution.NATIVE_FALLBACK, person(0, 0, 0));
        assertEquals(List.of(fallback), filter(List.of(fallback),
                flags(new QuickFlags(false, false, false, false), 0, 0), ADULT));
        // Retention by this quick gate is not native preparation or CanSend.
    }

    @Test void rawBoundaryRejectsValuesWhichCannotComeFromActualFieldWidths() {
        assertThrows(IllegalArgumentException.class, () -> new AttractionRaw(-1, 0));
        assertThrows(IllegalArgumentException.class, () -> new AttractionRaw(0, 256));
        assertThrows(IllegalArgumentException.class, () -> person(0, 0, 32768));
        assertThrows(IllegalArgumentException.class, () -> new ResolvedCandidate(
                0x1_0000_0000L, Resolution.NATIVE_FALLBACK, person(0, 0, 0)));
    }

    @Test void pinnedNativeJumpTablesAndFamilyIndexComeFromRequiredCurrentSourceFixture() throws IOException {
        try (var stream = getClass().getResourceAsStream("/m6native/source07.json")) {
            assertNotNull(stream, "required actual source fixture");
            var source = StrictJson.parse(stream.readAllBytes(), 100000);
            assertEquals(NativeActivityAi.EXE_SHA256, source.get("exe_sha256").textValue());
            List<String> owner = List.of("292E920", "292E937", "292E96B", "292E94E", "292E94E", "292E954");
            List<String> target = List.of("292EA1E", "292EA26", "292EA30", "292E9EA", "292E9EA", "292E9EA");
            for (String name : List.of("owner_first", "target")) {
                byte[] raw = HexFormat.of().parseHex(source.get("quick_tables").get(name).get("bytes_hex").textValue());
                assertEquals(24, raw.length);
                var little = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
                for (String expected : name.equals("owner_first") ? owner : target) {
                    assertEquals(Long.parseLong(expected, 16), Integer.toUnsignedLong(little.getInt()));
                }
            }
            assertEquals(57, source.get("family_runtime_tokens").size());
            assertEquals(58, source.get("family_dispatch_rvas").size());
            assertEquals("2930399", source.get("family_dispatch_rvas").get(57).textValue());
        }
    }
}
