package org.xar.ck3.control.wave2.military.capture;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Base64;
import java.util.Set;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Builder contract only; actual Python imports require the later qualified capture regression. */
final class OriginalProducerOracleTest {
    private static final Set<String> MODULES = Set.of("xar_autoplayer.ordinary_war_results_window_v1");
    private static ExactRef reference(long bytes) {
        return new ExactRef(Path.of("historical-union-fixture.json.gz").toAbsolutePath().toString(), bytes, "0".repeat(64));
    }
    @Test void originalScriptAndExactReferenceSurviveLiteralEncoding() {
        String script = "from __future__ import annotations\nprint('quote\\\\ newline\\n unicode 战争')\n";
        ExactRef ref = reference(327680);
        String program = OriginalProducerOracle.program(script, ref, MODULES);
        var match = Pattern.compile("_historical_original_run\\('([A-Za-z0-9+/=]+)','([A-Za-z0-9+/=]+)'\\)\\n$").matcher(program);
        assertTrue(match.find());
        assertEquals(script, new String(Base64.getDecoder().decode(match.group(2)), StandardCharsets.UTF_8));
        var config = StrictJson.parse(Base64.getDecoder().decode(match.group(1)));
        assertEquals(ref, ExactRef.fromJson(config.get("archive")));
        assertEquals(MODULES.iterator().next(), config.get("allowed_modules").get(0).textValue());
    }
    @Test void absentRelativeOversizedAndUnqualifiedInputsCannotCreateOracleProgram() {
        assertThrows(NullPointerException.class, () -> OriginalProducerOracle.program("pass", null, MODULES));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("", reference(1), MODULES));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("pass", reference(0), MODULES));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("pass", reference(327681), MODULES));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("pass", new ExactRef("relative.gz", 1, "0".repeat(64)), MODULES));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("pass", reference(1), Set.of()));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("pass", reference(1), Set.of("arbitrary.module")));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("pass", reference(1), Set.of("xar_autoplayer...bad")));
        assertThrows(IllegalArgumentException.class, () -> OriginalProducerOracle.program("\ud800", reference(1), MODULES));
    }
}
