package org.xar.ck3.markets.otc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.build.ContentValidator;
import org.xar.ck3.save.Clausewitz;

/** Source composition and real generated-reference regressions; never CK3/business acceptance. */
final class OtcGuiContractTest {
    private static final Path CANDIDATE = Path.of(System.getProperty("xfm.candidate", System.getProperty("xfm.source", "..")));
    private static final Path BASELINE = Path.of(System.getProperty("xfm.baseline", CANDIDATE.toString()));
    private static final List<String> ADDITIONS = List.of(
            "common/scripted_triggers/xfm_market_otc_triggers.txt",
            "common/script_values/xfm_market_ui_otc_values.txt",
            "common/scripted_effects/xfm_market_ui_otc_targets.txt",
            "common/scripted_guis/xfm_market_otc_panel.txt", "gui/xfm_market_otc.gui",
            "localization/english/xfm_market_otc_l_english.yml",
            "localization/simp_chinese/xfm_market_otc_l_simp_chinese.yml");

    @Test void originalInteractionEligibilityAndBusinessReceiversArePreserved() throws IOException {
        String original = baseline("xfm_market_otc_interactions.txt");
        String changed = read(CANDIDATE, "common/character_interactions/xfm_market_otc_interactions.txt");
        String extracted = block(read(CANDIDATE, "common/scripted_triggers/xfm_market_otc_triggers.txt"),
                "xfm_market_otc_can_send_trigger");
        String previousEligibility = block(block(block(original, "xfm_market_otc_offer_interaction"),
                "is_valid_showing_failures_only"), "scope:actor");
        assertEquals(normalize(previousEligibility), normalize(extracted));
        String oldBlock = block(original, "is_valid_showing_failures_only");
        String newBlock = block(changed, "is_valid_showing_failures_only");
        assertEquals(normalize(original.replace(oldBlock, newBlock)), normalize(changed));
    }

    @Test void normalButtonsUseTheSameProposalAndCancellationPaths() throws IOException {
        String interaction = baseline("xfm_market_otc_interactions.txt");
        String guis = read(CANDIDATE, "common/scripted_guis/xfm_market_otc_panel.txt");
        String previousSend = block(block(block(interaction, "xfm_market_otc_offer_interaction"), "on_accept"), "scope:actor");
        String currentSend = block(block(guis, "xfm_market_otc_send_gui"), "effect");
        assertEquals(normalize(previousSend.replace("scope:recipient", "var:xfm_ui_otc_target_buyer")), normalize(currentSend));
        String previousCancel = block(block(block(interaction, "xfm_market_otc_cancel_interaction"), "on_accept"), "scope:actor");
        String currentCancel = block(block(guis, "xfm_market_otc_cancel_offer_gui"), "effect");
        assertEquals(normalize(previousCancel), normalize(currentCancel));
        String previousTicket = baseline("xfm_market_spot_ticket.gui");
        String currentTicket = read(CANDIDATE, "gui/xfm_market_spot_ticket.gui");
        // The order form may move above the book; all original controls and callbacks stay identical.
        assertEquals(spotControls(previousTicket), spotControls(currentTicket));
        assertFalse(guis.contains("trigger_event"));
        assertFalse(read(CANDIDATE, "common/scripted_effects/xfm_market_ui_otc_targets.txt").contains("every_living_character"));
    }

    @Test void mergedRealRuntimeReferencesAndBilingualContentClose(@TempDir Path projection) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        ContentValidator.Manifest manifest = mapper.readValue(BASELINE.resolve("runtime-files.json").toFile(), ContentValidator.Manifest.class);
        List<String> paths = new ArrayList<>(manifest.files());
        for (String addition : ADDITIONS) if (!paths.contains(addition)) paths.add(addition);
        for (String name : paths) {
            Path source = Files.isRegularFile(CANDIDATE.resolve(name)) ? CANDIDATE.resolve(name) : BASELINE.resolve(name);
            Path target = projection.resolve(name);
            Files.createDirectories(target.getParent());
            Files.copy(source, target, StandardCopyOption.COPY_ATTRIBUTES);
        }
        mapper.writeValue(projection.resolve("runtime-files.json").toFile(),
                new ContentValidator.Manifest("xfm.runtime-files.v1", List.copyOf(paths)));
        ContentValidator.Report report = ContentValidator.validate(projection);
        assertEquals(paths.size(), report.files());
        assertEquals("STATIC_ONLY_NOT_ENGINE_OR_BUSINESS_PASS", report.boundary());
        assertTrue(report.runtimeFiles().containsAll(ADDITIONS));
    }

    private static Map<String, String> spotControls(String source) {
        Map<String, String> controls = new TreeMap<>();
        spotControls(Clausewitz.parse(source), controls);
        assertFalse(controls.isEmpty());
        return controls;
    }
    private static void spotControls(Clausewitz.Block block, Map<String, String> controls) {
        for (var entry : block.entries()) if (entry.value() instanceof Clausewitz.Block child) {
            if (entry.key().equals("button_standard")) {
                String name = child.atom("name", "");
                assertFalse(name.isEmpty());
                assertEquals(null, controls.put(name, normalize(child.render())), "duplicate spot control");
            }
            spotControls(child, controls);
        }
    }

    private static String read(Path root, String relative) throws IOException {
        return Files.readString(root.resolve(relative), StandardCharsets.UTF_8).replace("\ufeff", "").replace("\r\n", "\n");
    }

    private static String baseline(String name) throws IOException {
        try (var input = OtcGuiContractTest.class.getResourceAsStream("/otc-gui-baseline/" + name)) {
            if (input == null) throw new IOException("missing original production source fixture: " + name);
            return new String(input.readAllBytes(), StandardCharsets.UTF_8).replace("\ufeff", "").replace("\r\n", "\n");
        }
    }

    private static String normalize(String script) {
        return script.replaceAll("(?m)#[^\\r\\n]*", "").replaceAll("\\s+", "").replace("\ufeff", "");
    }

    private static String block(String script, String key) {
        var matcher = Pattern.compile("(?<![A-Za-z0-9_:])" + Pattern.quote(key) + "\\s*=\\s*\\{").matcher(script);
        if (!matcher.find()) throw new IllegalArgumentException("missing actual source block: " + key);
        int begin = matcher.end() - 1, depth = 0;
        boolean quoted = false, escaped = false, comment = false;
        for (int index = begin; index < script.length(); index++) {
            char value = script.charAt(index);
            if (comment) { if (value == '\n') comment = false; continue; }
            if (quoted) {
                if (escaped) escaped = false;
                else if (value == '\\') escaped = true;
                else if (value == '"') quoted = false;
                continue;
            }
            if (value == '#') comment = true;
            else if (value == '"') quoted = true;
            else if (value == '{') depth++;
            else if (value == '}' && --depth == 0) return script.substring(begin, index + 1);
        }
        throw new IllegalArgumentException("unclosed actual source block: " + key);
    }
}
