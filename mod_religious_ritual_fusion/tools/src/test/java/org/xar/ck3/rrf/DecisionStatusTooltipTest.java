package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

/** Executes the actual tooltip/eligibility AST subset; this is not native UI acceptance. */
final class DecisionStatusTooltipTest {
    private record Rite(int id, int faith, int religion, boolean adoptable) { }
    private record Actor(List<Rite> rites, boolean cooldown, String state, BigDecimal piety) {
        Actor { rites = List.copyOf(rites); }
    }
    private record Scope(int religion, int faith, int rite) { }
    private static final Scope PLAYER = new Scope(8, 106, 155);
    private static final Rite OWN = new Rite(155, 106, 8, true);
    private static final String EMPTY = "RRF_ENTRY_STATUS_EMPTY";

    @Test void sourceStatusUsesActualSharedFiltersInBothModes() throws IOException {
        Clausewitz.Block definitions = read("common/scripted_triggers/rrf_eligibility_triggers.txt");
        for (List<Rite> rites : List.of(List.of(OWN), List.of(OWN, new Rite(156, 106, 8, false)),
                List.of(OWN, new Rite(156, 106, 8, true)), List.of(OWN, new Rite(157, 107, 8, true)),
                List.of(OWN, new Rite(158, 108, 9, true)))) {
            Actor actor = actor(rites, false, "succeeded", "-0.4");
            boolean same = rites.stream().anyMatch(r -> r.id() != 155 && r.faith() == 106 && r.adoptable());
            boolean other = rites.stream().anyMatch(r -> r.faith() != 106 && r.adoptable());
            assertEquals(same ? "RRF_RITE_SOURCE_SELECT" : "RRF_RITE_SOURCE_MISSING", status("RrfRiteSourceStatus", actor));
            assertEquals(other ? "RRF_FAITH_SOURCE_SELECT" : "RRF_FAITH_SOURCE_MISSING", status("RrfFaithSourceStatus", actor));
            Clausewitz.Block decisions = read("common/decisions/rrf_decisions.txt");
            assertEquals(same, check(decisions.block("rrf_begin_rite_fusion_decision").block("is_valid"), actor, PLAYER, definitions));
            assertEquals(other, check(decisions.block("rrf_begin_faith_fusion_decision").block("is_valid"), actor, PLAYER, definitions));
        }
    }

    @Test void independentCooldownAndPendingReasonsDoNotTurnWalletIntoEntryGate() throws IOException {
        List<Rite> sources = List.of(OWN, new Rite(156, 106, 8, true));
        Clausewitz.Block definitions = read("common/scripted_triggers/rrf_eligibility_triggers.txt");
        Actor persisted = actor(List.of(OWN), true, "succeeded", "-0.4");
        assertEquals("RRF_RITE_SOURCE_MISSING", status("RrfRiteSourceStatus", persisted));
        assertEquals("RRF_ENTRY_COOLDOWN", status("RrfCooldownStatus", persisted));
        assertEquals(EMPTY, status("RrfPendingStatus", persisted));
        assertFalse(check(definitions.block("rrf_actor_eligible_trigger"), persisted, PLAYER, definitions));
        for (String state : List.of("", "editing", "succeeded", "unrecognized")) {
            for (String wallet : List.of("-0.4", "0", "6000")) {
                Actor actor = actor(sources, false, state, wallet);
                assertEquals(EMPTY, status("RrfPendingStatus", actor));
                assertEquals(EMPTY, status("RrfCooldownStatus", actor));
                assertTrue(check(definitions.block("rrf_actor_eligible_trigger"), actor, PLAYER, definitions));
            }
        }
        for (String state : List.of("committing", "unresolved")) {
            Actor actor = actor(List.of(OWN), true, state, "-0.4");
            assertEquals("RRF_RITE_SOURCE_MISSING", status("RrfRiteSourceStatus", actor));
            assertEquals("RRF_ENTRY_COOLDOWN", status("RrfCooldownStatus", actor));
            assertEquals(state.equals("committing") ? "RRF_COMMITTING" : "RRF_UNRESOLVED", status("RrfPendingStatus", actor));
            assertFalse(check(definitions.block("rrf_actor_eligible_trigger"), actor, PLAYER, definitions));
        }
    }

    @Test void allRealLocalesWireSourceOnlyAndIndependentRowStatus() throws IOException {
        Path source = source();
        ContentValidator.validate(source);
        Contracts.Product product = Json.read(Files.readAllBytes(source.resolve("tools/product.json")), Contracts.Product.class);
        int languages = 0;
        for (String file : product.runtimeFiles()) {
            if (!file.startsWith("localization/") || !file.endsWith(".yml")) continue;
            Map<String, String> values = new LinkedHashMap<>();
            for (String line : Files.readAllLines(source.resolve(file))) {
                int split = line.indexOf(":0 \"");
                if (line.startsWith(" ") && split > 1 && line.endsWith("\""))
                    values.put(line.substring(1, split), line.substring(split + 4, line.length() - 1));
            }
            assertEquals("", values.get(EMPTY));
            for (String mode : List.of("rite", "faith")) {
                String prefix = "rrf_begin_" + mode + "_fusion_decision";
                assertEquals("[GetPlayer.Custom('Rrf" + (mode.equals("rite") ? "Rite" : "Faith") + "SourceStatus')]", values.get(prefix + "_no_item_selected"));
                String tooltip = values.get(prefix + "_tooltip");
                assertTrue(tooltip.contains("[GetPlayer.Custom('RrfCooldownStatus')]"));
                assertTrue(tooltip.contains("[GetPlayer.Custom('RrfPendingStatus')]"));
                assertFalse(tooltip.contains("SourceStatus"));
            }
            languages++;
        }
        assertEquals(9, languages);
    }

    private static String status(String name, Actor actor) throws IOException {
        Clausewitz.Block definition = read("common/customizable_localization/rrf_decision_status_loc.txt").block(name);
        assertEquals("character", definition.atom("type", ""));
        String fallback = null;
        Clausewitz.Block triggers = read("common/scripted_triggers/rrf_eligibility_triggers.txt");
        for (Clausewitz.Entry entry : definition.named("text")) {
            Clausewitz.Block row = (Clausewitz.Block) entry.value();
            if (row.atom("fallback", "no").equals("yes")) fallback = row.atom("localization_key", "");
            else if (check(row.block("trigger"), actor, PLAYER, triggers)) return row.atom("localization_key", "");
        }
        if (fallback == null || fallback.isEmpty()) throw new IllegalArgumentException("Missing real fallback: " + name);
        return fallback;
    }

    private static boolean check(Clausewitz.Block block, Actor actor, Scope scope, Clausewitz.Block definitions) {
        return block.entries().stream().allMatch(e -> condition(e, actor, scope, definitions));
    }
    private static boolean condition(Clausewitz.Entry e, Actor a, Scope s, Clausewitz.Block defs) {
        if (e.value() instanceof Clausewitz.Atom atom) {
            return switch (e.key()) {
                case "text" -> true;
                case "this" -> e.operator().equals("!=") && switch (atom.token()) {
                    case "root.rite" -> s.rite() != PLAYER.rite();
                    case "root.faith" -> s.faith() != PLAYER.faith();
                    default -> throw new IllegalArgumentException("Unexpected comparison: " + e.render());
                };
                case "can_convert_to_rite" -> atom.token().equals("yes") && a.rites().stream().anyMatch(r -> r.id() == s.rite() && r.adoptable());
                case "has_character_flag" -> atom.token().equals("rrf_fusion_cooldown") && a.cooldown();
                case "var:rrf_state" -> e.operator().equals("?=") && atom.token().equals("flag:" + a.state());
                case "is_adult", "is_landed" -> atom.token().equals("yes");
                case "is_at_war", "is_imprisoned" -> atom.token().equals("no");
                case "exists" -> atom.token().equals("rite") && PLAYER.rite() > 0;
                default -> {
                    if (defs.named(e.key()).isEmpty() || !atom.token().equals("yes")) throw new IllegalArgumentException("Unexpected trigger: " + e.render());
                    yield check(defs.block(e.key()), a, s, defs);
                }
            };
        }
        Clausewitz.Block child = (Clausewitz.Block) e.value();
        return switch (e.key()) {
            case "NOT" -> !check(child, a, s, defs);
            case "custom_description" -> check(child, a, s, defs);
            case "faith" -> check(child, a, new Scope(8, PLAYER.faith(), 0), defs);
            case "any_religion_global" -> a.rites().stream().map(Rite::religion).distinct().anyMatch(r -> check(child, a, new Scope(r, 0, 0), defs));
            case "any_faith" -> a.rites().stream().filter(r -> r.religion() == s.religion()).map(Rite::faith).distinct().anyMatch(f -> check(child, a, new Scope(s.religion(), f, 0), defs));
            case "any_faith_rite" -> a.rites().stream().filter(r -> r.faith() == s.faith()).anyMatch(r -> check(child, a, new Scope(r.religion(), r.faith(), r.id()), defs));
            default -> throw new IllegalArgumentException("Unexpected scope: " + e.key());
        };
    }
    private static Actor actor(List<Rite> rites, boolean cooldown, String state, String piety) {
        return new Actor(rites, cooldown, state, new BigDecimal(piety));
    }
    private static Path source() { return Path.of(System.getProperty("rrf.source")); }
    private static Clausewitz.Block read(String relative) throws IOException { return Clausewitz.parse(Files.readString(source().resolve(relative))); }
}
