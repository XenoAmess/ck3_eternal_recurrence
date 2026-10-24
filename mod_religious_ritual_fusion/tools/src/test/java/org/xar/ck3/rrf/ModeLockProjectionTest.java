package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Contracts.Catalog;

/** L0 interpreter for the emitted initialization subset only; it does not claim native CK3 acceptance. */
final class ModeLockProjectionTest {
    @TempDir Path directory;
    @Test void realReaderAndGeneratorApplyRiteFaithReligionLocksByMode() throws IOException {
        Path game = directory.resolve("game");
        Files.createDirectories(game.resolve("common/scripted_triggers"));
        write(game, "common/religion/doctrine_group_types/sample.txt", "open_group={category=main_group} rite_group={category=special doctrine_lock=rite} faith_group={category=special doctrine_lock=faith} religion_group={category=special doctrine_lock=religion}");
        write(game, "common/religion/doctrine_types/sample.txt", "open_a={doctrine_group_type=open_group} open_b={doctrine_group_type=open_group} rite_a={doctrine_group_type=rite_group} faith_a={doctrine_group_type=faith_group} faith_b={doctrine_group_type=faith_group} religion_a={doctrine_group_type=religion_group} religion_b={doctrine_group_type=religion_group}");
        write(game, "common/religion/tenet_types/sample.txt", "tenet_sample={}");
        Catalog catalog = new CatalogReader().read(game, "lock-fixture");
        String emitted = new CatalogGenerator().render(catalog).get("common/scripted_effects/rrf_catalog_initialize_00.txt");
        Clausewitz.Block initialization = (Clausewitz.Block) Clausewitz.parse(emitted).entries().getFirst().value();
        State rite = new State("rite"); run(initialization, rite);
        assertEquals(Set.of("doctrine:open_a", "doctrine:open_b", "doctrine:faith_a", "doctrine:faith_b", "doctrine:religion_a"), rite.candidates);
        assertEquals(Set.of("doctrine:open_a", "doctrine:faith_a", "doctrine:religion_a"), rite.selected);
        State faith = new State("faith"); run(initialization, faith);
        assertEquals(Set.of("doctrine:open_a", "doctrine:open_b", "doctrine:religion_a"), faith.candidates);
        assertEquals(Set.of("doctrine:open_a", "doctrine:religion_a"), faith.selected);
        assertTrue(catalog.definitions().stream().filter(d -> d.id().equals("rite_a")).findFirst().orElseThrow().blockedReasons().contains("rite_lock_cleared_on_creation"));
        String validation = new CatalogGenerator().render(catalog).get("common/scripted_effects/rrf_catalog_validate_00.txt");
        assertTrue(validation.contains("scope:actor = { var:rrf_mode = flag:rite }"));
        assertTrue(validation.contains("scope:actor = { var:rrf_source_a = { rite_has_doctrine = religion_b } }"));
    }
    private static final class State {
        final String mode;
        final Set<String> candidates = new LinkedHashSet<>(); final Set<String> selected = new LinkedHashSet<>();
        State(String mode) { this.mode = mode; }
    }
    private static void run(Clausewitz.Block body, State state) {
        for (Clausewitz.Entry entry : body.entries()) {
            Clausewitz.Block child = (Clausewitz.Block) entry.value();
            if (entry.key().equals("if")) { if (check(child.block("limit"), state, "actor")) run(new Clausewitz.Block(child.entries().stream().filter(e -> !e.key().equals("limit")).toList()), state); }
            else if (entry.key().equals("add_to_variable_list")) {
                Set<String> list = child.atom("name", "").equals("rrf_candidate_doctrines") ? state.candidates : state.selected;
                list.add(child.atom("target", ""));
            } else throw new IllegalArgumentException("unexpected effect in fixture interpreter: " + entry.key());
        }
    }
    private static boolean check(Clausewitz.Block body, State state, String scope) { return body.entries().stream().allMatch(e -> condition(e, state, scope)); }
    private static boolean condition(Clausewitz.Entry entry, State state, String scope) {
        if (entry.value() instanceof Clausewitz.Atom atom) {
            return switch (entry.key()) {
                case "var:rrf_mode" -> atom.token().equals("flag:" + state.mode);
                case "rite_has_doctrine" -> (scope.equals("a") ? Set.of("open_a", "rite_a", "faith_a", "religion_a") : Set.of("open_b", "rite_a", "faith_b", "religion_b")).contains(atom.token());
                default -> throw new IllegalArgumentException("unexpected condition: " + entry.key());
            };
        }
        Clausewitz.Block child = (Clausewitz.Block) entry.value();
        return switch (entry.key()) {
            case "OR" -> child.entries().stream().anyMatch(e -> condition(e, state, scope));
            case "var:rrf_source_a" -> check(child, state, "a");
            case "var:rrf_source_b" -> check(child, state, "b");
            default -> throw new IllegalArgumentException("unexpected scope: " + entry.key());
        };
    }
    private static void write(Path root, String relative, String content) throws IOException { Path target = root.resolve(relative); Files.createDirectories(target.getParent()); Files.writeString(target, content); }
}
