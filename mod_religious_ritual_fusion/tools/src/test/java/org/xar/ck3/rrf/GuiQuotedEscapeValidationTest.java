package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Replays the actual R0011 producer fault through the release byte consumer. */
final class GuiQuotedEscapeValidationTest {
    private record ObservedFailure(String relative, String quotedPrefix, int observedLine) { }

    @Test void actualProductionTooltipsRejectTheObservedEscapeAtTheActualFilenameAndLine() throws IOException {
        Path source = Path.of(System.getProperty("rrf.source"));
        for (ObservedFailure observed : List.of(
                new ObservedFailure("gui/rrf_fusion_window.gui", "RRF_COMMIT_HOVER", 352),
                new ObservedFailure("gui/window_rite_creation.gui", "[Localize( 'RRF_NATIVE_SETUP_APPLY_TT' )] ", 483),
                new ObservedFailure("gui/rrf_result_window.gui", "[Localize( 'RRF_INVITE_VASSALS_TT' )] ", 151))) {
            byte[] actual = Files.readAllBytes(source.resolve(observed.relative()));
            assertDoesNotThrow(() -> ContentValidator.validateBytes(observed.relative(), actual));
            String text = new String(actual, StandardCharsets.UTF_8);
            String marker = observed.quotedPrefix();
            int offset = text.indexOf(marker);
            assertTrue(offset >= 0, observed.toString());
            assertEquals(offset, text.lastIndexOf(marker), observed.toString());
            String malformed = text.substring(0, offset) + marker
                    + "\\n\\n" + text.substring(offset + marker.length());
            int escape = malformed.indexOf("\\n\\n", offset);
            long line = malformed.substring(0, escape).chars().filter(c -> c == '\n').count() + 1;
            int column = escape - malformed.lastIndexOf('\n', escape - 1);
            IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                    () -> ContentValidator.validateBytes(observed.relative(), malformed.getBytes(StandardCharsets.UTF_8)));
            assertEquals("invalid GUI quoted escape at " + observed.relative() + ":" + line + ":" + column
                    + ": backslash must be followed by quote or backslash", failure.getMessage());
        }
    }

    @Test void escapedQuoteBackslashAndCommentTextRemainValid() {
        String slash = Character.toString('\\');
        String text = "\ufeffwindow = { tooltip = \"escaped " + slash + "\" quote and "
                + slash + slash + " path # inside string\" }\n# ignored " + slash + "n and \"quote\n";
        assertDoesNotThrow(() -> Clausewitz.parse(text));
        assertDoesNotThrow(() -> ContentValidator.validateBytes("gui/valid.gui", text.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void hashInsideQuotedTextDoesNotTurnTheRestOfTheStringIntoAComment() {
        String text = "\ufeff# ignored \\q\nwindow = { tooltip = \"inside # \\q\" }\n";
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                () -> ContentValidator.validateBytes("gui/quoted-hash.gui", text.getBytes(StandardCharsets.UTF_8)));
        assertTrue(failure.getMessage().startsWith("invalid GUI quoted escape at gui/quoted-hash.gui:2:"));
    }

    @Test void localizationNewlineSyntaxIsOutsideThisGuiOnlyRule() {
        String text = "\ufeffl_english:\n fixture:0 \"First\\nSecond\"\n";
        assertDoesNotThrow(() -> ContentValidator.validateBytes(
                "localization/english/rrf_l_english.yml", text.getBytes(StandardCharsets.UTF_8)));
    }
}
