package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Actual AST and localization closure. Native tooltip rendering remains an engine boundary. */
final class NegatedTooltipTest {
    private static Path source() { return Path.of(System.getProperty("rrf.source")); }
    private static Clausewitz.Block drafts() throws IOException {
        return Clausewitz.parse(Files.readString(source().resolve("common/scripted_triggers/rrf_draft_triggers.txt")));
    }
    private static Map<String, String> english() throws IOException {
        Map<String, String> result = new LinkedHashMap<>();
        for (String line : Files.readAllLines(source().resolve("localization/english/rrf_l_english.yml"))) {
            int split = line.indexOf(":0 \"");
            if (line.startsWith(" ") && split > 1 && line.endsWith("\""))
                result.put(line.substring(1, split), line.substring(split + 4, line.length() - 1));
        }
        return result;
    }
    @Test void allProductionLocalesHaveTheActualCustomDescriptionFallbackClosure() throws IOException {
        ContentValidator.validate(source());
    }
    @Test void actualR0003MissingCanonicalCapacityFallbackIsRejectedByTheProductionConsumer() throws IOException {
        Map<String, String> values = english();
        values.remove("NOT_RRF_REQUIRE_CORE_CAPACITY");
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                () -> ContentValidator.validateNegatedDescriptions(drafts(), values, "actual-draft-triggers"));
        assertTrue(failure.getMessage().contains("NOT_RRF_REQUIRE_CORE_CAPACITY"));
        values.put("NOT_RRF_REQUIRE_CORE_CAPACITY", "   ");
        assertThrows(IllegalArgumentException.class,
                () -> ContentValidator.validateNegatedDescriptions(drafts(), values, "actual-draft-triggers"));
    }
    @Test void commentsAndQuotedExamplesDoNotInventCustomDescriptionRequirements() {
        Clausewitz.Block ast = Clausewitz.parse("# custom_description = { text = RRF_NOT_A_REAL_PREDICATE }\n"
                + "example = { desc = \"custom_description text RRF_NOT_A_REAL_PREDICATE\" }\n");
        ContentValidator.validateNegatedDescriptions(ast, Map.of(), "authored-quoted-comment-boundary");
    }
    @Test void fullCapacityBlocksOnlyAddingAnUnselectedTenetWhileRangeCostAndContributionsStayIndependent() throws IOException {
        Clausewitz.Block definitions = drafts();
        Clausewitz.Block capacity = definitions.block("rrf_tenet_selectable_trigger").named("custom_description").stream()
                .map(e -> (Clausewitz.Block) e.value()).filter(b -> b.atom("text", "").equals("RRF_REQUIRE_CORE_CAPACITY")).findFirst().orElseThrow();
        Draft full = new Draft(Set.of("a", "b", "c"), "new-source-b", 3, 3, new BigDecimal("499"), false);
        assertFalse(check(capacity, full));
        assertTrue(check(capacity, new Draft(full.selected(), "a", 3, 3, full.piety(), false)));
        assertTrue(check(capacity, new Draft(Set.of("a", "b"), "new-source-b", 2, 3, full.piety(), false)));
        assertTrue(check(definitions.block("rrf_draft_core_range_trigger"), full));
        assertFalse(check(definitions.block("rrf_draft_cost_affordable_trigger"), full));
        assertFalse(check(Clausewitz.parse(Files.readString(source().resolve("common/scripted_triggers/rrf_eligibility_triggers.txt"))).block("rrf_sources_contributed_trigger"), full));
        Draft affordableBoth = new Draft(full.selected(), full.candidate(), 3, 3, new BigDecimal("500"), true);
        assertTrue(check(definitions.block("rrf_draft_cost_affordable_trigger"), affordableBoth));
        assertTrue(check(Clausewitz.parse(Files.readString(source().resolve("common/scripted_triggers/rrf_eligibility_triggers.txt"))).block("rrf_sources_contributed_trigger"), affordableBoth));
    }
    private record Draft(Set<String> selected, String candidate, int count, int limit, BigDecimal piety, boolean both) { }
    private static boolean check(Clausewitz.Block block, Draft draft) {
        return block.entries().stream().allMatch(e -> condition(e, draft));
    }
    private static boolean condition(Clausewitz.Entry entry, Draft d) {
        if (entry.value() instanceof Clausewitz.Block body) return switch (entry.key()) {
            case "OR" -> body.entries().stream().anyMatch(e -> condition(e, d));
            case "is_target_in_variable_list" -> {
                if (!body.atom("name", "").equals("rrf_selected_tenets") || !body.atom("target", "").equals("scope:rrf_item"))
                    throw new IllegalArgumentException("unsupported actual list predicate: " + entry.render());
                yield d.selected().contains(d.candidate());
            }
            default -> throw new IllegalArgumentException("unsupported actual tooltip scope: " + entry.render());
        };
        String token = ((Clausewitz.Atom) entry.value()).token();
        return switch (entry.key()) {
            case "text" -> true;
            case "var:rrf_core_count" -> {
                int right = token.equals("rrf_core_limit_value") ? d.limit() : Integer.parseInt(token);
                yield switch (entry.operator()) { case "<" -> d.count() < right; case "<=" -> d.count() <= right; case ">=" -> d.count() >= right; default -> throw new IllegalArgumentException(entry.render()); };
            }
            case "piety" -> {
                if (!token.equals("rrf_current_cost_value") || !entry.operator().equals(">=")) throw new IllegalArgumentException(entry.render());
                yield d.piety().compareTo(new BigDecimal("500")) >= 0;
            }
            case "has_character_flag" -> switch (token) { case "rrf_contribution_a" -> true; case "rrf_contribution_b" -> d.both(); default -> throw new IllegalArgumentException(entry.render()); };
            default -> throw new IllegalArgumentException("unsupported actual tooltip predicate: " + entry.render());
        };
    }
}
