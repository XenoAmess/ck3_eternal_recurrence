package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.time.format.DateTimeParseException;
import org.junit.jupiter.api.Test;

final class StrictJsonUtcNormalizationBoundaryTest {
    @Test
    void chainedUtcFormsReturnTheOriginalString() {
        String[] values = {
                "20240229 123456+00:00",
                "2024-02-29T123456+00:00",
                "2020-W53-7 235959Z"
        };
        for (String value : values) {
            String original = new String(value);
            assertSame(original, StrictJson.utc(original));
        }
    }

    @Test
    void parseFailuresRetainTheTextFromTheirOriginalFailureStage() {
        String[][] cases = {
                {"20241301T000000Z", "20241301"},
                {"2020-W99-1T000000Z", "2020-W99-1"},
                {"20240229 250000Z", "2024-02-29T25:00:00Z"},
                {"20241301T000000Z\n", "20241301T000000Z\n"},
                {"20241301T000000Z" + String.valueOf((char) 0x0000), "20241301"},
                {"20241301T000000Z" + String.valueOf((char) 0x2028), "20241301T000000Z" + String.valueOf((char) 0x2028)},
                {"20240229\n000000Z", "2024-02-29\n00:00:00Z"},
                {"20240229" + String.valueOf((char) 0x0000) + "000000Z", "2024-02-29" + String.valueOf((char) 0x0000) + "00:00:00Z"},
                {"2020-w53-7T000000Z", "2020-w53-7T00:00:00Z"},
                {"2024-02-29T12" + String.valueOf((char) 0x0663) + "456Z", "2024-02-29T12" + String.valueOf((char) 0x0663) + "456Z"},
                {"2024-02-29T12345Z", "2024-02-29T12345Z"},
                {"2020-W99-1T000000Z\n", "2020-W99-1T00:00:00Z\n"}
        };
        for (String[] example : cases) {
            ContractViolationException failure = assertThrows(
                    ContractViolationException.class, () -> StrictJson.utc(example[0]));
            assertEquals("ISO UTC observation time required", failure.getMessage());
            DateTimeParseException cause = assertInstanceOf(
                    DateTimeParseException.class, failure.getCause());
            assertEquals(example[1], cause.getParsedString());
        }
    }

    @Test
    void textAndNonZeroOffsetErrorsKeepTheirFirstPublicFailure() {
        String[][] textCases = {
                {null, "nonempty bounded text required"},
                {"", "nonempty bounded text required"},
                {String.valueOf((char) 0xd800), "unpaired Unicode surrogate"},
                {String.valueOf((char) 0xdc00), "unpaired Unicode surrogate"},
                {"x".repeat(32767) + String.valueOf((char) 0xd800), "unpaired Unicode surrogate"},
                {"x".repeat(32768) + String.valueOf((char) 0xd800), "nonempty bounded text required"}
        };
        for (String[] example : textCases) {
            ContractViolationException failure = assertThrows(
                    ContractViolationException.class, () -> StrictJson.utc(example[0]));
            assertEquals(example[1], failure.getMessage());
            assertNull(failure.getCause());
        }
        String[] nonZeroOffsets = {
                "20240229 123456+01:00",
                "2024-02-29T123456+00:00:01"
        };
        for (String value : nonZeroOffsets) {
            ContractViolationException failure = assertThrows(
                    ContractViolationException.class, () -> StrictJson.utc(value));
            assertEquals("UTC offset zero required", failure.getMessage());
            assertNull(failure.getCause());
        }
    }
}
