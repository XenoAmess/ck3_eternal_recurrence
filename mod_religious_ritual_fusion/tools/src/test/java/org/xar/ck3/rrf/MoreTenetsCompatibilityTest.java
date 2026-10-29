package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Contracts.Catalog;

/** Executes the real reader/generator and the bounded production-script subset. No native-game credit. */
final class MoreTenetsCompatibilityTest {
    @TempDir Path directory;

    private static final List<String> DRAFT_STATUSES = List.of("Actor", "Source", "Revalidation", "Content", "CoreRange", "Contribution", "Cost");

    @Test void disabledDraftListsEveryActualFailureAndPreservesTheCommitAndCancelGuards() throws IOException {
        Model model = model(3);
        model.numbers.put("rrf_core_count", 3);
        model.flags.addAll(List.of("rrf_selection_checked", "rrf_contribution_a"));
        model.piety = new BigDecimal("499");
        assertFalse(model.guiValid("rrf_commit_gui"));
        assertTrue(model.guiValid("rrf_cancel_gui"));
        assertEquals(List.of("RRF_BLOCKER_BOTH_SOURCES", "RRF_BLOCKER_COST"), model.blockers());
        model.numbers.put("rrf_core_count", 2);
        assertEquals(List.of("RRF_BLOCKER_CORE_RANGE", "RRF_BLOCKER_BOTH_SOURCES", "RRF_BLOCKER_COST"), model.blockers());
        assertFalse(model.guiValid("rrf_commit_gui"));
        model.numbers.put("rrf_core_count", 3);
        model.flags.add("rrf_contribution_b");
        assertEquals(List.of("RRF_BLOCKER_COST"), model.blockers());
        model.piety = new BigDecimal("499.999");
        assertFalse(model.guiValid("rrf_commit_gui"));
        model.piety = new BigDecimal("500");
        assertTrue(model.guiValid("rrf_commit_gui"));
        assertEquals(List.of(), model.blockers());
        model.flags.remove("rrf_contribution_b");
        assertEquals(List.of("RRF_BLOCKER_BOTH_SOURCES"), model.blockers());
        assertFalse(model.guiValid("rrf_commit_gui"));
    }

    @Test void remainingDraftFailuresAreVisibleAndPricesAndCoreLimitsUseProductionScriptValues() throws IOException {
        Model model = model(3);
        model.numbers.put("rrf_core_count", 3);
        model.flags.addAll(List.of("rrf_contribution_a", "rrf_contribution_b", "rrf_invalid_selection"));
        model.actorBooleans.put("is_at_war", true);
        model.references.remove("rrf_source_b");
        assertEquals(List.of("RRF_BLOCKER_ACTOR", "RRF_BLOCKER_SOURCE_CURRENT", "RRF_BLOCKER_REVALIDATED", "RRF_BLOCKER_CONTENT_VALID"), model.blockers());
        assertFalse(model.guiValid("rrf_commit_gui"));
        model.textVariables.put("rrf_mode", "flag:faith");
        assertEquals(1000, model.number("rrf_current_cost_value"));
        model.piety = new BigDecimal("999");
        assertEquals("RRF_BLOCKER_COST", model.status("Cost"));
        assertFalse(model.check(model.scripts.get("rrf_draft_cost_affordable_trigger"), model.actor));
        model.piety = new BigDecimal("1000");
        assertEquals("RRF_ENTRY_STATUS_EMPTY", model.status("Cost"));
        assertTrue(model.check(model.scripts.get("rrf_draft_cost_affordable_trigger"), model.actor));
        Model mts = model(100);
        for (int count : List.of(2, 3, 100, 101)) {
            mts.numbers.put("rrf_core_count", count);
            assertEquals(count >= 3 && count <= 100 ? "RRF_ENTRY_STATUS_EMPTY" : "RRF_BLOCKER_CORE_RANGE", mts.status("CoreRange"));
        }
    }

    @Test void panelAndHoverShareLocalizedFailureLinesWithoutDependingOnAnEmptyAutomaticTooltip() throws IOException {
        Path source = Path.of(System.getProperty("rrf.source"));
        Clausewitz.Block window = Clausewitz.parse(Files.readString(source.resolve("gui/rrf_fusion_window.gui"))).block("window");
        Clausewitz.Block text = widgets(window, "rrf_commit_blockers_text").getFirst();
        Clausewitz.Block commit = widgets(window, "rrf_commit").getFirst();
        assertEquals("\"RRF_COMMIT_BLOCKERS\"", text.atom("text", ""));
        assertEquals("\"RRF_COMMIT_HOVER\"", commit.atom("tooltip", ""));
        assertFalse(commit.atom("tooltip", "").contains("\\n"));
        assertEquals("\"[GetScriptedGui( 'rrf_commit_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\"", commit.atom("enabled", ""));
        assertEquals("\"[GetScriptedGui( 'rrf_commit_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\"", commit.atom("onclick", ""));
        assertTrue(widgets(window, "rrf_commit_blockers_scroll").getFirst().atom("visible", "").contains("Not( GetScriptedGui( 'rrf_commit_gui' ).IsValid"));
        Clausewitz.Block guis = Clausewitz.parse(Files.readString(source.resolve("common/scripted_guis/rrf_scripted_guis.txt")));
        assertEquals(Clausewitz.parse("rrf_ready_trigger = yes").render(), guis.block("rrf_commit_gui").block("is_valid").render());
        assertEquals(Clausewitz.parse("rrf_commit_effect = yes").render(), guis.block("rrf_commit_gui").block("effect").render());
        String expected = DRAFT_STATUSES.stream().map(name -> "[GetPlayer.Custom('RrfDraft" + name + "Status')]").collect(java.util.stream.Collectors.joining());
        int languages = 0;
        try (var files = Files.walk(source.resolve("localization"))) {
            for (Path path : files.filter(p -> p.getFileName().toString().startsWith("rrf_l_")).toList()) {
                byte[] raw = Files.readAllBytes(path);
                assertTrue(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf, path.toString());
                Map<String, String> loc = localizations(path);
                assertEquals(expected, loc.get("RRF_COMMIT_BLOCKERS"));
                assertEquals("$RRF_COMMIT_TT$\\n$RRF_COMMIT_BLOCKERS$", loc.get("RRF_COMMIT_HOVER"));
                assertEquals("", loc.get("RRF_ENTRY_STATUS_EMPTY"));
                for (String key : List.of("ACTOR", "SOURCE_CURRENT", "REVALIDATED", "CONTENT_VALID", "CORE_RANGE", "BOTH_SOURCES", "COST")) {
                    String required = key.equals("ACTOR") ? "ACTOR_ELIGIBLE" : key;
                    String line = loc.get("RRF_BLOCKER_" + key);
                    assertTrue(line.startsWith("#X $RRF_REQUIRE_" + required + "$"));
                    assertTrue(line.endsWith("#!\\n"));
                    assertTrue(loc.containsKey("RRF_REQUIRE_" + required));
                }
                assertTrue(loc.get("RRF_BLOCKER_COST").contains("ScriptValue( 'rrf_current_cost_value' )"));
                languages++;
            }
        }
        assertEquals(9, languages);
    }

    private static List<Clausewitz.Block> widgets(Clausewitz.Block parent, String name) {
        List<Clausewitz.Block> matches = new ArrayList<>();
        if (parent.atom("name", "").equals("\"" + name + "\"")) matches.add(parent);
        for (Clausewitz.Entry entry : parent.entries())
            if (entry.value() instanceof Clausewitz.Block child) matches.addAll(widgets(child, name));
        return List.copyOf(matches);
    }

    private static Map<String, String> localizations(Path path) throws IOException {
        Map<String, String> result = new LinkedHashMap<>();
        for (String line : Files.readAllLines(path)) {
            int split = line.indexOf(":0 \"");
            if (line.startsWith(" ") && split > 1 && line.endsWith("\""))
                result.put(line.substring(1, split), line.substring(split + 4, line.length() - 1));
        }
        return Map.copyOf(result);
    }

    @Test void sourceBoundMembershipRejectsMetadataHiddenAndLegacyBlankContent() throws IOException {
        Model model = model(100);
        for (String id : List.of("tenet_zz_empty_001", "tenet_empty", "tenet_hidden", "tenet_unknown")) {
            assertFalse(model.check(model.scripts.get("rrf_real_tenet_trigger"), scope("tenet:" + id)));
        }
        assertFalse(model.check(model.scripts.get("rrf_real_tenet_trigger"), scope("doctrine:mts_selector_doctrine_001")));
        assertFalse(model.check(model.scripts.get("rrf_real_doctrine_trigger"), scope("doctrine:mts_selector_doctrine_001")));
        assertTrue(model.check(model.scripts.get("rrf_real_tenet_trigger"), scope("tenet:tenet_real_099")));
        assertTrue(model.check(model.scripts.get("rrf_real_doctrine_trigger"), scope("doctrine:ordinary_a")));
        model.saved.put("rrf_item", scope("doctrine:mts_selector_doctrine_001"));
        model.doctrines.get(model.a).add(model.saved.get("rrf_item"));
        model.run(model.scripts.get("rrf_validate_doctrine_member_effect"), model.actor);
        assertTrue(model.flags.contains("rrf_invalid_selection"));
        assertFalse(model.flags.contains("rrf_contribution_a"));
        assertFalse(model.flags.contains("rrf_contribution_b"));
    }

    @Test void realCapacityAndRangeGuardsKeepOrdinaryThreeAndMtsThreeThroughOneHundred() throws IOException {
        Model ordinary = model(3); Model mts = model(100);
        Clausewitz.Block range = mts.scripts.get("rrf_ready_trigger").named("custom_description").stream()
                .map(e -> (Clausewitz.Block) e.value()).filter(b -> b.atom("text", "").equals("RRF_REQUIRE_CORE_RANGE")).findFirst().orElseThrow();
        for (int count : List.of(0, 2, 3, 4, 99, 100, 101)) {
            ordinary.numbers.put("rrf_core_count", count); mts.numbers.put("rrf_core_count", count);
            assertEquals(count == 3, ordinary.check(range, ordinary.actor), "ordinary count=" + count);
            assertEquals(count >= 3 && count <= 100, mts.check(range, mts.actor), "MTS count=" + count);
        }
        assertEquals(3, model(75).number("rrf_core_limit_value"));
    }

    @Test void actualDraftInitializerPreservesEveryRealSourceCoreAndNoEmptySlots() throws IOException {
        Model model = model(100);
        List<Scope> expected = realTenets(0, 100);
        model.cores.get(model.a).addAll(expected);
        model.cores.get(model.a).add(scope("tenet:tenet_zz_empty_001"));
        model.cores.get(model.b).addAll(realTenets(99, 110));
        model.run(model.scripts.get("rrf_prepare_draft_effect"), model.actor);
        assertEquals(expected, model.variables.get("rrf_selected_tenets"));
        assertEquals(new LinkedHashSet<>(realTenets(0, 110)), new LinkedHashSet<>(model.variables.get("rrf_candidate_tenets")));
        assertEquals(100, model.numbers.get("rrf_core_count"));
        assertEquals(100, model.numbers.get("rrf_core_limit"));
        assertTrue(model.creationHooks.contains("rrf_initialize_creation_options_effect"));
    }

    @Test void capacityDisablesOnlyNewPicksAndCommonOrMetadataContentNeverContributes() throws IOException {
        for (int cap : List.of(3, 100)) {
            Model model = model(cap);
            model.numbers.put("rrf_core_count", cap);
            model.variables.put("rrf_selected_tenets", new ArrayList<>(realTenets(0, cap)));
            model.variables.put("rrf_candidate_tenets", new ArrayList<>(realTenets(0, cap + 1)));
            model.saved.put("rrf_item", realTenets(cap, cap + 1).getFirst());
            assertFalse(model.check(model.scripts.get("rrf_tenet_selectable_trigger"), model.actor));
            model.saved.put("rrf_item", realTenets(0, 1).getFirst());
            assertTrue(model.check(model.scripts.get("rrf_tenet_selectable_trigger"), model.actor));
        }
        Model model = model(100);
        model.cores.get(model.a).addAll(realTenets(0, 2)); model.cores.get(model.b).addAll(realTenets(1, 3));
        model.saved.put("rrf_item", realTenets(1, 2).getFirst());
        model.run(model.scripts.get("rrf_validate_core_member_effect"), model.actor);
        assertFalse(model.flags.contains("rrf_contribution_a")); assertFalse(model.flags.contains("rrf_contribution_b"));
        model.saved.put("rrf_item", realTenets(0, 1).getFirst());
        model.run(model.scripts.get("rrf_validate_core_member_effect"), model.actor);
        assertTrue(model.flags.contains("rrf_contribution_a"));
        model.saved.put("rrf_item", realTenets(2, 3).getFirst());
        model.run(model.scripts.get("rrf_validate_core_member_effect"), model.actor);
        assertTrue(model.flags.contains("rrf_contribution_b"));
    }

    @Test void actualAlignmentAndPosteriorKeepFullSetAndBothSourcesUntouched() throws IOException {
        Model model = model(100);
        model.cores.get(model.a).addAll(realTenets(0, 100));
        model.cores.get(model.b).addAll(realTenets(10, 110));
        model.cores.get(model.created).addAll(model.cores.get(model.a));
        List<Scope> selected = realTenets(10, 110);
        model.variables.put("rrf_selected_tenets", new ArrayList<>(selected));
        model.numbers.put("rrf_core_count", 100);
        Set<Scope> aBefore = Set.copyOf(model.cores.get(model.a)); Set<Scope> bBefore = Set.copyOf(model.cores.get(model.b));
        model.run(model.scripts.get("rrf_align_created_core_set_effect"), model.actor);
        assertEquals(Set.copyOf(selected), model.cores.get(model.created));
        assertEquals(aBefore, model.cores.get(model.a)); assertEquals(bBefore, model.cores.get(model.b));
        model.run(model.scripts.get("rrf_check_created_result_effect"), model.actor);
        assertEquals(100, model.numbers.get("rrf_result_core_count"));
        assertFalse(model.flags.contains("rrf_result_invalid"));
        // Equal counts cannot hide a missing selected item replaced by an unselected extra item.
        model.cores.get(model.created).remove(selected.getFirst());
        model.cores.get(model.created).add(scope("tenet:tenet_real_000"));
        model.run(model.scripts.get("rrf_check_created_result_effect"), model.actor);
        assertTrue(model.flags.contains("rrf_result_invalid"));
    }

    @Test void ordinaryDoctrineReplacementRemainsUniqueAndMetadataCannotBeSelected() throws IOException {
        Model model = model(100);
        model.variables.put("rrf_selected_doctrines", new ArrayList<>(List.of(scope("doctrine:ordinary_a"))));
        model.saved.put("rrf_item", scope("doctrine:ordinary_b"));
        model.run(model.scripts.get("rrf_catalog_select_doctrine_effect"), model.actor);
        assertEquals(List.of(scope("doctrine:ordinary_b")), model.variables.get("rrf_selected_doctrines"));
        model.saved.put("rrf_item", scope("doctrine:mts_selector_doctrine_001"));
        model.run(model.scripts.get("rrf_catalog_select_doctrine_effect"), model.actor);
        assertEquals(List.of(scope("doctrine:ordinary_b")), model.variables.get("rrf_selected_doctrines"));
    }

    @Test void realCommitGuardRejectsAnySourceAliasBeforeNewRiteMutation() throws IOException {
        Model model = model(100);
        Clausewitz.Block identity = model.scripts.get("rrf_commit_effect").block("if").block("if").block("if").block("limit");
        assertTrue(model.check(identity, model.actor));
        for (Scope source : List.of(model.a, model.b)) { model.saved.put("rrf_new_rite", source); assertFalse(model.check(identity, model.actor)); }
    }

    @Test void nativeDoctrineArgumentAcceptsOnlyActualSourceBoundDoctrineIds() throws IOException {
        Model model = model(100);
        model.doctrines.get(model.a).add(scope("doctrine:ordinary_a"));
        assertTrue(model.check(Clausewitz.parse("rite_has_doctrine = ordinary_a"), model.a));
        assertTrue(model.check(Clausewitz.parse("rite_has_doctrine = doctrine:ordinary_a"), model.a));
        assertThrows(IllegalArgumentException.class, () -> model.check(Clausewitz.parse("rite_has_doctrine = arbitrary_unknown"), model.a));
        assertThrows(IllegalArgumentException.class, () -> model.check(Clausewitz.parse("rite_has_doctrine = scope:rrf_actor"), model.a));
        assertThrows(IllegalArgumentException.class, () -> model.entity("ordinary_a", model.a));
    }

    @Test void typedEffectScopesRequireRegisteredDefinitionsOfTheCorrectKind() throws IOException {
        Model model = model(100);
        model.run(Clausewitz.parse("tenet:tenet_real_000 = { add_to_list = probe } doctrine:ordinary_a = { add_to_list = probe }"), model.actor);
        assertEquals(List.of(scope("tenet:tenet_real_000"), scope("doctrine:ordinary_a")), model.locals.get("probe"));
        for (String invalid : List.of("tenet:tenet_unknown", "doctrine:arbitrary_unknown", "tenet:ordinary_a", "doctrine:tenet_real_000")) {
            assertThrows(IllegalArgumentException.class, () -> model.run(Clausewitz.parse(invalid + " = { add_to_list = probe }"), model.actor));
        }
        assertEquals(2, model.locals.get("probe").size());
    }

    private Model model(int mirror) throws IOException {
        Path game = Files.createTempDirectory(directory, "native-source-");
        write(game, "common/scripted_triggers/sample.txt", "");
        write(game, "common/religion/doctrine_group_types/sample.txt", "ordinary={category=main_group} mts_selector_group_001={category=not_creatable}");
        write(game, "common/religion/doctrine_types/sample.txt", "ordinary_a={doctrine_group_type=ordinary} ordinary_b={doctrine_group_type=ordinary} mts_selector_doctrine_001={doctrine_group_type=mts_selector_group_001 visible=no}");
        StringBuilder tenets = new StringBuilder();
        for (Scope tenet : realTenets(0, 110)) tenets.append(tenet.id()).append("={}\n");
        tenets.append("tenet_zz_empty_001={} tenet_empty={} tenet_hidden={visible=no}");
        write(game, "common/religion/tenet_types/sample.txt", tenets.toString());
        Catalog catalog = new CatalogReader().read(game, "synthetic-mts-contract");
        Model model = new Model(mirror);
        catalog.definitions().stream().filter(d -> d.kind() == Contracts.Kind.DOCTRINE).map(Contracts.Definition::id).forEach(model.doctrineDefinitions::add);
        catalog.definitions().stream().filter(d -> d.kind() == Contracts.Kind.TENET).map(Contracts.Definition::id).forEach(model.tenetDefinitions::add);
        for (String generated : new CatalogGenerator().render(catalog).values()) model.add(generated);
        Path source = Path.of(System.getProperty("rrf.source"));
        for (String relative : List.of("common/script_values/rrf_values.txt", "common/scripted_triggers/rrf_eligibility_triggers.txt", "common/scripted_triggers/rrf_draft_triggers.txt", "common/scripted_guis/rrf_scripted_guis.txt", "common/scripted_effects/rrf_draft_effects.txt", "common/scripted_effects/rrf_selection_effects.txt", "common/scripted_effects/rrf_commit_effects.txt")) model.add(Files.readString(source.resolve(relative)));
        for (Clausewitz.Entry entry : Clausewitz.parse(Files.readString(source.resolve("common/customizable_localization/rrf_decision_status_loc.txt"))).entries())
            model.statuses.put(entry.key(), (Clausewitz.Block) entry.value());
        return model;
    }
    private static void write(Path root, String relative, String content) throws IOException { Path target = root.resolve(relative); Files.createDirectories(target.getParent()); Files.writeString(target, content); }
    private static List<Scope> realTenets(int first, int end) { List<Scope> result = new ArrayList<>(); for (int i = first; i < end; i++) result.add(scope("tenet:tenet_real_" + String.format(java.util.Locale.ROOT, "%03d", i))); return List.copyOf(result); }
    private record Scope(String type, String id) { }
    private static Scope scope(String token) { String[] parts = token.split(":", 2); return new Scope(parts[0], parts[1]); }

    /** Narrow AST executor; unknown commands fail closed instead of simulating CK3 generally. */
    private static final class Model {
        final Scope actor = scope("character:actor"), a = scope("rite:a"), b = scope("rite:b"), created = scope("rite:new"), faith = scope("faith:original");
        final Map<String, Clausewitz.Block> scripts = new LinkedHashMap<>();
        final Map<String, Clausewitz.Block> statuses = new LinkedHashMap<>();
        final Map<String, Boolean> actorBooleans = new LinkedHashMap<>(Map.of("is_adult", true, "is_landed", true, "is_at_war", false, "is_imprisoned", false));
        BigDecimal piety = new BigDecimal("2000");
        final Map<String, Integer> constants = new LinkedHashMap<>(), numbers = new LinkedHashMap<>();
        final Map<String, Scope> saved = new LinkedHashMap<>(), references = new LinkedHashMap<>();
        final Map<String, String> textVariables = new LinkedHashMap<>();
        final Map<String, List<Scope>> variables = new LinkedHashMap<>(), locals = new LinkedHashMap<>();
        final Map<Scope, Set<Scope>> cores = new LinkedHashMap<>(), doctrines = new LinkedHashMap<>();
        final Set<String> flags = new LinkedHashSet<>(), creationHooks = new LinkedHashSet<>();
        final Set<String> doctrineDefinitions = new LinkedHashSet<>();
        final Set<String> tenetDefinitions = new LinkedHashSet<>();
        Model(int mirror) {
            constants.put("pam_faith_core_tenets_cap_value", mirror);
            saved.put("rrf_actor", actor); saved.put("actor", actor); saved.put("rrf_new_rite", created); saved.put("selected_item", b);
            references.put("rrf_source_a", a); references.put("rrf_source_b", b); references.put("rrf_source_a_faith", faith); references.put("rrf_source_b_faith", faith);
            textVariables.put("rrf_mode", "flag:rite"); textVariables.put("rrf_state", "flag:editing");
            for (Scope rite : List.of(a, b, created)) { cores.put(rite, new LinkedHashSet<>()); doctrines.put(rite, new LinkedHashSet<>()); }
        }
        void add(String source) { for (Clausewitz.Entry e : Clausewitz.parse(source).entries()) { if (e.value() instanceof Clausewitz.Block body) scripts.put(e.key(), body); else constants.put(e.key(), Integer.valueOf(((Clausewitz.Atom) e.value()).token())); } }
        boolean guiValid(String name) { return check(scripts.get(name).block("is_valid"), actor); }
        String status(String name) {
            Clausewitz.Block definition = statuses.get("RrfDraft" + name + "Status");
            if (!definition.atom("type", "").equals("character")) throw new IllegalArgumentException("unexpected status scope: " + name);
            String fallback = null;
            for (Clausewitz.Entry entry : definition.named("text")) {
                Clausewitz.Block row = (Clausewitz.Block) entry.value();
                if (row.atom("fallback", "no").equals("yes")) fallback = row.atom("localization_key", "");
                else if (check(row.block("trigger"), actor)) return row.atom("localization_key", "");
            }
            if (fallback == null || fallback.isEmpty()) throw new IllegalArgumentException("missing status fallback: " + name);
            return fallback;
        }
        List<String> blockers() { return DRAFT_STATUSES.stream().map(this::status).filter(key -> !key.equals("RRF_ENTRY_STATUS_EMPTY")).toList(); }
        int number(String token) {
            if (token.startsWith("var:")) return numbers.getOrDefault(token.substring(4), 0);
            if (constants.containsKey(token)) return constants.get(token);
            if (!scripts.containsKey(token)) return new BigDecimal(token).intValueExact();
            int result = 0;
            for (Clausewitz.Entry e : scripts.get(token).entries()) {
                if (e.key().equals("value")) result = number(((Clausewitz.Atom) e.value()).token());
                else if (e.key().equals("if")) { Clausewitz.Block child = (Clausewitz.Block) e.value(); if (check(child.block("limit"), actor)) for (Clausewitz.Entry operation : child.entries()) { if (operation.key().equals("value")) result = number(((Clausewitz.Atom) operation.value()).token()); else if (operation.key().equals("max")) result = Math.min(result, number(((Clausewitz.Atom) operation.value()).token())); else if (!operation.key().equals("limit")) throw new IllegalArgumentException(operation.key()); } }
                else throw new IllegalArgumentException("unexpected numeric operation: " + e.key());
            }
            return result;
        }
        Scope entity(String token, Scope current) {
            if (token.equals("this")) return current;
            if (token.equals("rite")) return a;
            if (token.equals("faith") || token.endsWith(".faith")) return faith;
            if (token.startsWith("scope:")) return saved.get(token.substring(6));
            if (token.startsWith("var:")) return references.get(token.substring(4));
            if (token.startsWith("tenet:") || token.startsWith("doctrine:")) {
                Scope definition = scope(token);
                Set<String> registered = definition.type().equals("tenet") ? tenetDefinitions : doctrineDefinitions;
                if (!registered.contains(definition.id())) throw new IllegalArgumentException("unknown typed definition scope: " + token);
                return definition;
            }
            throw new IllegalArgumentException("unexpected scope: " + token);
        }
        Scope doctrineArgument(String token, Scope current) {
            // Native rite_has_doctrine accepts either a literal definition ID or a typed doctrine scope.
            if (token.matches("[A-Za-z_][A-Za-z_0-9]*")) {
                if (!doctrineDefinitions.contains(token)) throw new IllegalArgumentException("unknown doctrine definition: " + token);
                return scope("doctrine:" + token);
            }
            Scope resolved = entity(token, current);
            if (resolved == null || !resolved.type().equals("doctrine") || !doctrineDefinitions.contains(resolved.id())) throw new IllegalArgumentException("expected source-bound doctrine: " + token);
            return resolved;
        }
        boolean check(Clausewitz.Block body, Scope current) { return body.entries().stream().filter(e -> !e.key().equals("text")).allMatch(e -> condition(e, current)); }
        boolean condition(Clausewitz.Entry e, Scope current) {
            if (e.value() instanceof Clausewitz.Block child) return switch (e.key()) {
                case "OR" -> child.entries().stream().anyMatch(x -> condition(x, current));
                case "NOR" -> child.entries().stream().noneMatch(x -> condition(x, current));
                case "NOT" -> !check(child, current);
                case "AND", "custom_description", "custom_tooltip" -> check(child, current);
                case "is_target_in_variable_list" -> variables.getOrDefault(child.atom("name", ""), List.of()).contains(entity(child.atom("target", ""), current));
                case "any_rite_tenet" -> cores.getOrDefault(current, Set.of()).stream().anyMatch(x -> check(child, x));
                case "any_in_list" -> list(child).stream().anyMatch(x -> check(new Clausewitz.Block(child.entries().stream().filter(xe -> !Set.of("list", "variable").contains(xe.key())).toList()), x));
                case "calc_true_if" -> { Clausewitz.Entry amount = child.named("amount").getFirst(); long count = child.entries().stream().filter(x -> !x.key().equals("amount")).filter(x -> condition(x, current)).count(); yield compare(count, number(((Clausewitz.Atom) amount.value()).token()), amount.operator()); }
                default -> check(child, entity(e.key(), current));
            };
            String token = ((Clausewitz.Atom) e.value()).token();
            if (scripts.containsKey(e.key())) return token.equals("yes") == check(scripts.get(e.key()), current);
            if (e.key().equals("always")) return token.equals("yes");
            if (actorBooleans.containsKey(e.key())) return token.equals("yes") == actorBooleans.get(e.key());
            if (e.key().equals("piety")) return compare(piety.compareTo(BigDecimal.valueOf(number(token))), 0, e.operator());
            if (e.key().equals("exists")) return entity(token, current) != null;
            if (e.key().equals("has_variable")) return references.containsKey(token) || numbers.containsKey(token) || textVariables.containsKey(token);
            if (e.key().equals("has_variable_list")) return !variables.getOrDefault(token, List.of()).isEmpty();
            if (e.key().equals("has_character_flag")) return flags.contains(token);
            if (e.key().equals("can_convert_to_rite") || e.key().equals("knows_tenet") || e.key().equals("knows_doctrine")) return true;
            if (e.key().equals("has_perk")) return false;
            if (e.key().equals("rite_has_doctrine")) return doctrines.getOrDefault(current, Set.of()).contains(doctrineArgument(token, current));
            if (e.key().equals("is_in_list")) return locals.getOrDefault(token, List.of()).contains(current);
            if (e.key().startsWith("var:") && token.startsWith("flag:")) return token.equals(textVariables.get(e.key().substring(4)));
            if (e.key().startsWith("var:") && numbers.containsKey(e.key().substring(4)) || constants.containsKey(e.key())) return compare(number(e.key()), number(token), e.operator());
            boolean same = java.util.Objects.equals(entity(e.key(), current), entity(token, current));
            return e.operator().equals("!=") ? !same : same;
        }
        private static boolean compare(long a, long b, String operator) { return switch (operator) { case "=" -> a == b; case "!=" -> a != b; case "<" -> a < b; case "<=" -> a <= b; case ">" -> a > b; case ">=" -> a >= b; default -> throw new IllegalArgumentException(operator); }; }
        List<Scope> list(Clausewitz.Block body) { return body.named("variable").isEmpty() ? locals.getOrDefault(body.atom("list", ""), List.of()) : variables.getOrDefault(body.atom("variable", ""), List.of()); }
        void run(Clausewitz.Block body, Scope current) {
            boolean branch = false;
            for (Clausewitz.Entry e : body.entries()) {
                if (Set.of("if", "else_if", "else").contains(e.key())) {
                    Clausewitz.Block child = (Clausewitz.Block) e.value();
                    if (e.key().equals("if")) branch = false;
                    if (!branch && (e.key().equals("else") || check(child.block("limit"), current))) { run(child, current); branch = true; }
                    continue;
                }
                if (e.key().equals("limit")) continue;
                if (e.key().startsWith("scope:") || e.key().startsWith("var:")) { run((Clausewitz.Block) e.value(), entity(e.key(), current)); continue; }
                if (e.key().startsWith("tenet:") || e.key().startsWith("doctrine:")) { run((Clausewitz.Block) e.value(), entity(e.key(), current)); continue; }
                if (e.key().equals("every_in_list") || e.key().equals("every_rite_tenet")) {
                    Clausewitz.Block child = (Clausewitz.Block) e.value();
                    List<Scope> items = new ArrayList<>(e.key().equals("every_rite_tenet") ? cores.getOrDefault(current, Set.of()) : list(child));
                    Clausewitz.Block effects = new Clausewitz.Block(child.entries().stream().filter(x -> !Set.of("list", "variable").contains(x.key())).toList());
                    for (Scope item : items) if (check(child.block("limit"), item)) run(effects, item);
                    continue;
                }
                if (scripts.containsKey(e.key())) { run(scripts.get(e.key()), current); continue; }
                if (Set.of("rrf_initialize_creation_options_effect", "rrf_clear_creation_options_effect", "rrf_apply_creation_options_effect").contains(e.key())) { creationHooks.add(e.key()); continue; }
                if (e.value() instanceof Clausewitz.Block child) {
                    String name = child.atom("name", "");
                    switch (e.key()) {
                        case "set_variable" -> { String token = child.atom("value", ""); if (token.startsWith("flag:")) textVariables.put(name, token); else if (token.equals("rite") || token.equals("faith") || token.startsWith("scope:")) references.put(name, entity(token, current)); else numbers.put(name, number(token)); }
                        case "change_variable" -> numbers.merge(name, number(child.atom("add", "")), Integer::sum);
                        case "add_to_variable_list" -> variables.computeIfAbsent(name, ignored -> new ArrayList<>()).add(entity(child.atom("target", ""), current));
                        case "remove_list_variable" -> variables.computeIfAbsent(name, ignored -> new ArrayList<>()).remove(entity(child.atom("target", ""), current));
                        default -> throw new IllegalArgumentException("unexpected block effect: " + e.key());
                    }
                    continue;
                }
                String token = ((Clausewitz.Atom) e.value()).token();
                switch (e.key()) {
                    case "save_scope_as" -> saved.put(token, current);
                    case "clear_variable_list" -> variables.put(token, new ArrayList<>());
                    case "remove_variable" -> { references.remove(token); numbers.remove(token); textVariables.remove(token); }
                    case "add_character_flag" -> flags.add(token);
                    case "remove_character_flag" -> flags.remove(token);
                    case "add_to_list" -> locals.computeIfAbsent(token, ignored -> new ArrayList<>()).add(current);
                    case "remove_from_list" -> locals.computeIfAbsent(token, ignored -> new ArrayList<>()).remove(current);
                    case "remove_rite_tenet" -> cores.get(current).remove(entity(token, current));
                    case "add_rite_tenet" -> { if (cores.get(current).size() >= number("rrf_core_limit_value")) throw new IllegalArgumentException("native capacity overflow"); cores.get(current).add(entity(token, current)); }
                    default -> throw new IllegalArgumentException("unexpected atom effect: " + e.key());
                }
            }
        }
    }
}
