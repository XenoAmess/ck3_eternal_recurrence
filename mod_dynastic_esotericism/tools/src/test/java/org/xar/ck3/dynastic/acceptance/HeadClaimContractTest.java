package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;

/** Source contract regression for R0017; these checks do not execute or qualify the CK3 engine. */
final class HeadClaimContractTest {
    private static final String BINDING = "common/scripted_effects/des_binding_effects.txt";
    private static final String ACTIONS = "common/on_action/des_on_actions.txt";
    private static final String CREATOR = "des_claim_native_created_rite_head_effect";
    private static final String EDITOR = "des_record_native_rite_edit_head_claim_effect";
    private static final String COMPLETE = "des_finalize_native_rite_head_claim_effect";
    private static final String TRANSFER = "des_finalize_new_rite_head_effect";
    private static final String ACTOR = "des_native_head_claim_actor";
    private static final String PENDING = "des_native_head_claim_pending";
    private static final String ATTEMPTED = "des_native_head_claim_attempted";

    @Test
    void actualProductionSourcesResolveTheNativeCreatorBeforeAnyProductMigration() throws IOException {
        verify(Sources.load());
    }

    @Test
    void immediateEditCaptureAcceptsEitherDoctrineTimingButRejectsAnExistingBinding() throws IOException {
        Block guard = block(one(block(one(Sources.load().definition(EDITOR), "if")), "limit"));
        assertTrue(eligibleCapture(guard, Set.of(), false), "edit callback may precede doctrine application");
        assertTrue(eligibleCapture(guard, Set.of(), true), "edit callback may follow doctrine application");
        for (String occupied : List.of("des_bound_dynasty", "des_join_house", "des_binding_in_progress", PENDING, ATTEMPTED)) {
            assertFalse(eligibleCapture(guard, Set.of(occupied), true), occupied);
        }
    }

    @Test
    void regressionsRejectTheObservedMemberOnlyRaceAndUnsafeReplayOrMaintenanceRoutes() throws IOException {
        Sources actual = Sources.load();
        reject(actual, ACTIONS, "\t\t\tdes_claim_native_created_rite_head_effect = yes\n", "");
        reject(actual, BINDING, "set_variable = { name = " + ATTEMPTED + " value = yes }", "");
        reject(actual, BINDING, "var:" + ACTOR + " = { des_create_rite_dynasty_effect = yes }",
                "scope:des_selected_dynasty_founder = { des_create_rite_dynasty_effect = yes }");
        reject(actual, ACTIONS, "exists = scope:consume_rite_edit_token", "exists = scope:changed_tenets_or_doctrines");
        String maintenance = "common/scripted_effects/des_maintenance_effects.txt";
        reject(actual, maintenance, "des_maintenance_effect = {", "des_maintenance_effect = {\n\t" + COMPLETE + " = yes");
        reject(actual, BINDING, "limit = { rite = { is_target_in_global_variable_list = { name = des_ordinary_binding_rites target = this } } }",
                "limit = { always = yes }");
        reject(actual, BINDING, "add_rite_doctrine = des_doctrine_none", "");
        reject(actual, BINDING, "\t\t\t\t\t\t\thas_variable = des_native_head_claim_pending\n", "");
        reject(actual, BINDING, "\t\t\t\t\t\t\thas_variable = des_native_initial_binding_fault\n", "");
        reject(actual, BINDING, "des_reuse_native_dynast_binding_effect = {",
                "des_reuse_native_dynast_binding_effect = {\n\tcreate_dynasty = { spread_to_descendants = no }");
        reject(actual, "common/scripted_effects/des_identity_effects.txt",
                "NOT = { var:des_binding_mode = flag:native_dynast_reuse }", "always = yes");
        reject(actual, "common/scripted_triggers/des_dynastic_triggers.txt",
                "var:des_adopted_bound_rite = dynasty.var:des_bound_rite", "always = yes");
    }

    @Test
    void doctrineOrderRegressionCannotRestoreThePrematureImmediatePredicate() throws IOException {
        Sources actual = Sources.load();
        String prefix = EDITOR + " = {\n\tif = {\n\t\tlimit = {\n";
        reject(actual, BINDING, prefix, prefix + "\t\t\trite_has_doctrine = des_doctrine_dynastic\n");
    }

    @Test
    void reusedDynastyDoesNotMakeANeverAdoptingOrFormerOtherRiteMemberAnApostate() throws IOException {
        Block prior = block(one(Sources.load().definition("des_is_apostate_trigger"), "OR"));
        assertFalse(priorAdoption(prior, Map.of(), "new-rite"));
        assertFalse(priorAdoption(prior, Map.of("var:des_adopted_bound_rite", "old-rite"), "new-rite"));
        assertTrue(priorAdoption(prior, Map.of("var:des_adopted_bound_rite", "new-rite"), "new-rite"));
        assertTrue(priorAdoption(prior, Map.of("var:des_apostate_rite", "new-rite"), "new-rite"));
    }

    /** Evaluate the literal persisted prior-adoption predicate, not engine crime effects. */
    private static boolean priorAdoption(Block prior, Map<String, String> references, String boundRite) {
        for (Entry entry : prior.entries()) {
            assertEquals("=", entry.operator());
            assertEquals("dynasty.var:des_bound_rite", atom(entry));
            if (boundRite.equals(references.get(entry.key()))) return true;
        }
        return false;
    }

    @Test
    void acceptanceInputsCannotManufactureANativeHeadClaim() throws IOException {
        Path fixture = source().resolve("tools/src/main/resources/acceptance-fixture");
        try (Stream<Path> paths = Files.walk(fixture)) {
            for (Path path : paths.filter(p -> p.toString().endsWith(".txt")).toList()) {
                Block script = Parser.read(Files.readString(path, StandardCharsets.UTF_8));
                for (String helper : List.of(CREATOR, EDITOR, COMPLETE)) {
                    assertFalse(calls(script, helper), path + " must use real native callback provenance");
                }
            }
        }
        String input = Files.readString(fixture.resolve("common/scripted_effects/des_acceptance_effects.txt"));
        Block relation = block(one(Parser.read(input), "des_acceptance_read_original_edit_input_effect"));
        assertTrue(has(relation, "can_edit_rite_trigger", "yes"));
        assertTrue(has(relation, "rite.head_of_rite", "this"));
    }

    private static void verify(Sources sources) {
        Block created = sources.definition(CREATOR);
        assertTrue(calls(created, "des_capture_native_rite_source_effect"));
        Block capture = sources.definition("des_capture_native_rite_source_effect");
        assertTrue(sets(capture, ACTOR, "scope:des_native_source_actor"));
        assertTrue(sets(capture, PENDING, "yes"));
        assertTrue(has(capture, "is_dynast", "yes"));
        assertTrue(sets(capture, "des_native_source_dynasty", "scope:des_native_original_dynasty"));
        assertTrue(sets(capture, "des_native_source_house", "scope:des_native_original_house"));

        Block nativeCreated = block(one(block(one(sources.definition("des_on_rite_created"), "effect")), "if"));
        assertTrue(index(nativeCreated, CREATOR) < index(nativeCreated, "des_sync_character_effect"), "capture and policy must precede product migration");
        assertTrue(index(nativeCreated, CREATOR) < index(nativeCreated, "rite"));
        assertTrue(calls(block(one(nativeCreated, "rite")), "des_sync_rite_effect"));

        Block editGuard = block(one(block(one(sources.definition(EDITOR), "if")), "limit"));
        assertTrue(eligibleCapture(editGuard, Set.of(), false), "doctrine writes must not be assumed complete in immediate callback");
        assertFalse(eligibleCapture(editGuard, Set.of("des_bound_dynasty"), true));
        assertFalse(has(editGuard, "rite_has_doctrine", "des_doctrine_dynastic"));
        Block immediate = sources.definition("des_on_native_rite_edited");
        assertTrue(calls(immediate, EDITOR));
        for (String forbidden : List.of("des_sync_rite_effect", "des_ensure_own_rite_binding_effect", COMPLETE, TRANSFER)) {
            assertFalse(calls(immediate, forbidden), "immediate edit records provenance only");
        }

        Block updated = sources.definition("des_on_rite_updated");
        List<Block> tokenRoutes = walk(updated).stream().filter(e -> e.key().equals("if") && e.value() instanceof Block)
                .map(HeadClaimContractTest::block)
                .filter(b -> calls(b, COMPLETE) && has(block(one(b, "limit")), "exists", "scope:consume_rite_edit_token"))
                .toList();
        assertEquals(1, tokenRoutes.size(), "completion requires the actual native interface-update token");
        Block token = tokenRoutes.getFirst();
        assertTrue(has(block(one(token, "limit")), "rite_has_doctrine", "des_doctrine_dynastic"));
        Block updateBody = block(one(block(one(updated, "effect")), "if"));
        assertTrue(index(updateBody, "if") < index(updateBody, "head_of_rite"), "native policy must precede generic ensure");
        Block declined = walk(updated).stream().filter(e -> e.key().equals("if") && e.value() instanceof Block)
                .map(HeadClaimContractTest::block).filter(b -> has(b, "remove_variable", PENDING)).findFirst().orElseThrow();
        assertTrue(has(declined, "remove_variable", PENDING));
        assertTrue(has(declined, "remove_variable", ACTOR));
        assertFalse(sets(declined, ATTEMPTED, "yes"), "an unrelated non-dynastic edit is not a failed claim");
        assertFalse(sets(declined, "des_creator_head_fault", "yes"));

        Block complete = sources.definition(COMPLETE);
        Block body = block(one(complete, "if"));
        assertTrue(has(block(one(body, "limit")), "has_variable", PENDING));
        assertTrue(has(block(one(block(one(body, "limit")), "NOT")), "has_variable", ATTEMPTED));
        assertTrue(sets(body, ATTEMPTED, "yes"));
        assertTrue(index(body, "set_variable") < index(body, "if"), "consume claim before any native policy mutation");
        assertTrue(index(body, "remove_variable") < index(body, "if"));
        assertTrue(sets(complete, "des_native_head_claim_dynasty", "var:des_bound_dynasty"));
        assertTrue(sets(complete, "des_native_head_claim_house", "var:des_join_house"));
        List<Block> actorRoutes = walk(complete).stream().filter(e -> e.key().equals("var:" + ACTOR) && e.value() instanceof Block)
                .map(HeadClaimContractTest::block).filter(b -> calls(b, "des_create_rite_dynasty_effect")).toList();
        assertEquals(1, actorRoutes.size());
        assertTrue(has(complete, "var:des_join_house.house_head", "var:" + ACTOR));
        assertTrue(has(complete, "var:des_bound_dynasty.dynast", "var:" + ACTOR));
        for (String primitive : List.of("create_dynasty", "set_house", "set_house_head", "set_coa")) {
            assertFalse(calls(complete, primitive), "completion must use the guarded production policy branches");
        }
        assertTrue(has(sources.definition(TRANSFER), "any_dynasty_member", null), "do not weaken the single-House guard");
        assertEquals(Set.of("des_on_rite_created"), sources.callers(CREATOR));
        assertEquals(Set.of("des_on_native_rite_edited"), sources.callers(EDITOR));
        assertEquals(Set.of(CREATOR, "des_on_rite_updated"), sources.callers(COMPLETE));
        assertEquals(Set.of("des_create_rite_dynasty_effect"), sources.callers(TRANSFER));
        verifyPolicy(sources);
    }

    private static void verifyPolicy(Sources sources) {
        String reuseName = "des_reuse_native_dynast_binding_effect";
        Block reuse = sources.definition(reuseName);
        assertEquals(Set.of(COMPLETE), sources.callers(reuseName));
        assertEquals(Set.of(CREATOR, EDITOR), sources.callers("des_capture_native_rite_source_effect"));
        for (String forbidden : List.of("create_dynasty", "create_character", "create_cadet_branch", "set_house", "set_house_head", "set_coa", "generate_coa")) {
            assertFalse(calls(reuse, forbidden), "reuse must preserve actual members, heads, Houses and both original CoAs");
        }
        assertTrue(has(reuse, "var:des_native_source_dynasty.dynast", "var:des_native_source_actor"));
        assertTrue(has(reuse, "var:des_native_source_house.house_dynasty", "var:des_native_source_dynasty"));
        assertTrue(sets(reuse, "des_binding_mode", "flag:native_dynast_reuse"));
        assertTrue(has(reuse, "remove_rite_doctrine", "des_doctrine_dynastic"));
        assertTrue(has(reuse, "add_rite_doctrine", "des_doctrine_none"));
        assertTrue(calls(reuse, "des_clear_apostasy_effect"));
        for (String key : List.of("des_bound_dynasty", "des_join_house", "des_binding_mode")) {
            assertTrue(has(reuse, "remove_variable", key), "old binding state must be invalidated");
        }
        Block ensure = sources.definition("des_ensure_own_rite_binding_effect");
        List<Block> ordinary = walk(ensure).stream().filter(e -> e.key().equals("if") && e.value() instanceof Block)
                .map(HeadClaimContractTest::block).filter(b -> b.entries().stream().anyMatch(e -> e.key().equals("des_create_rite_dynasty_effect"))).toList();
        assertEquals(1, ordinary.size());
        assertTrue(has(block(one(ordinary.getFirst(), "limit")), "is_target_in_global_variable_list", null));
        assertTrue(has(block(one(ordinary.getFirst(), "limit")), "name", "des_ordinary_binding_rites"));
        assertFalse(calls(ensure, reuseName), "ordinary Dynast adoption cannot reuse");
        assertTrue(has(ensure, "has_variable", PENDING), "generic creation must wait for the native edit token");
        assertTrue(has(ensure, "has_variable", "des_native_initial_binding_fault"), "failed provenance cannot fall through to generic creation");
        Block queued = sources.definition("des_queue_unknown_rite_binding_effect");
        assertTrue(sets(queued, "des_deferred_binding_requester", "scope:des_first_ordinary_requester"));
        assertTrue(has(queued, "days", "1"));
        assertEquals(Set.of("des_ensure_own_rite_binding_effect", COMPLETE), sources.callers("des_create_rite_dynasty_effect"));
        assertEquals(Set.of("des_initialize_world_effect", COMPLETE, "des_deferred_rite_binding"),
                sources.callers("des_allow_ordinary_rite_binding_effect"));
        assertTrue(has(sources.definition("des_deferred_rite_binding"), "has_variable", PENDING));
        Block identity = sources.definition("des_apply_rite_identity_effect");
        List<Block> coaGuard = walk(identity).stream().filter(e -> e.key().equals("if") && e.value() instanceof Block)
                .map(HeadClaimContractTest::block).filter(b -> has(block(one(b, "limit")), "var:des_binding_mode", "flag:native_dynast_reuse")).toList();
        assertEquals(1, coaGuard.size());
        assertTrue(has(block(one(block(one(coaGuard.getFirst(), "limit")), "NOT")), "var:des_binding_mode", "flag:native_dynast_reuse"));
        assertEquals(walk(identity).stream().filter(e -> e.key().equals("set_coa") || e.key().equals("generate_coa")).count(),
                walk(coaGuard.getFirst()).stream().filter(e -> e.key().equals("set_coa") || e.key().equals("generate_coa")).count());
        Block apostasy = sources.definition("des_is_apostate_trigger");
        assertTrue(has(apostasy, "var:des_adopted_bound_rite", "dynasty.var:des_bound_rite"));
        assertTrue(sets(sources.definition("des_join_rite_dynasty_effect"), "des_adopted_bound_rite", "rite"));
    }

    /** Evaluate only the recorded unbound-state predicate, not any engine effect. */
    private static boolean eligibleCapture(Block guard, Set<String> variables, boolean dynastic) {
        return guard.entries().stream().allMatch(e -> predicate(e, variables, dynastic));
    }

    private static boolean predicate(Entry entry, Set<String> variables, boolean dynastic) {
        return switch (entry.key()) {
            case "has_variable" -> variables.contains(atom(entry));
            case "exists" -> { assertEquals("head_of_rite", atom(entry)); yield true; }
            case "rite_has_doctrine" -> { assertEquals("des_doctrine_dynastic", atom(entry)); yield dynastic; }
            case "NOR", "NOT" -> !block(entry).entries().stream().anyMatch(e -> predicate(e, variables, dynastic));
            default -> throw new AssertionError("unsupported capture predicate: " + entry.key());
        };
    }

    private static void reject(Sources sources, String path, String old, String replacement) {
        assertTrue(sources.text().get(path).contains(old), "mutation must hit actual production source");
        assertThrows(AssertionError.class, () -> verify(sources.replace(path, old, replacement)));
    }

    private static Path source() { return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize(); }
    private static Block block(Entry entry) { return assertInstanceOf(Block.class, entry.value()); }
    private static String atom(Entry entry) { return assertInstanceOf(Atom.class, entry.value()).token(); }
    private static Entry one(Block block, String key) {
        List<Entry> entries = block.entries().stream().filter(e -> e.key().equals(key)).toList();
        assertEquals(1, entries.size(), "one field required: " + key);
        return entries.getFirst();
    }
    private static int index(Block block, String key) {
        for (int i = 0; i < block.entries().size(); i++) if (block.entries().get(i).key().equals(key)) return i;
        throw new AssertionError("missing direct statement: " + key);
    }
    private static List<Entry> walk(Block block) {
        List<Entry> result = new ArrayList<>();
        for (Entry entry : block.entries()) {
            result.add(entry);
            if (entry.value() instanceof Block nested) result.addAll(walk(nested));
        }
        return List.copyOf(result);
    }
    private static boolean has(Block block, String key, String value) {
        return walk(block).stream().anyMatch(e -> e.key().equals(key)
                && (value == null || e.value() instanceof Atom atom && atom.token().equals(value)));
    }
    private static boolean calls(Block block, String key) { return has(block, key, null); }
    private static boolean sets(Block block, String name, String value) {
        return walk(block).stream().filter(e -> e.key().equals("set_variable") && e.value() instanceof Block)
                .map(HeadClaimContractTest::block).anyMatch(b -> has(b, "name", name) && has(b, "value", value));
    }

    private record Sources(Map<String, String> text) {
        Sources { text = Map.copyOf(text); }
        static Sources load() throws IOException {
            Map<String, String> files = new HashMap<>();
            for (String directory : List.of("common/scripted_effects", "common/on_action", "common/scripted_triggers")) {
                try (Stream<Path> paths = Files.walk(source().resolve(directory))) {
                    for (Path path : paths.filter(p -> p.toString().endsWith(".txt")).toList()) {
                        files.put(source().relativize(path).toString().replace('\\', '/'), Files.readString(path));
                    }
                }
            }
            return new Sources(files);
        }
        Sources replace(String path, String old, String replacement) {
            Map<String, String> changed = new HashMap<>(text);
            changed.put(path, changed.get(path).replace(old, replacement));
            return new Sources(changed);
        }
        Block definition(String name) {
            List<Entry> found = new ArrayList<>();
            for (String script : text.values()) found.addAll(Parser.read(script).entries().stream().filter(e -> e.key().equals(name)).toList());
            assertEquals(1, found.size(), "one production definition required: " + name);
            return block(found.getFirst());
        }
        Set<String> callers(String helper) {
            Set<String> result = new HashSet<>();
            for (String script : text.values()) {
                for (Entry entry : Parser.read(script).entries()) {
                    if (entry.value() instanceof Block body && calls(body, helper)) result.add(entry.key());
                }
            }
            return Set.copyOf(result);
        }
    }

    private sealed interface Value permits Atom, Block { }
    private record Atom(String token) implements Value { }
    private record Block(List<Entry> entries) implements Value { Block { entries = List.copyOf(entries); } }
    private record Entry(String key, String operator, Value value) { }

    /** Literal source structure only; operators and list atoms are preserved, never executed. */
    private static final class Parser {
        private static final Pattern TOKEN = Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|#[^\\r\\n]*|\\s+|\\?=|!=|<=|>=|[{}=<>]|[^\\s{}=<>!?#\"]+");
        private static final Set<String> OPERATORS = Set.of("=", "?=", "!=", "<", ">", "<=", ">=");
        private final List<String> tokens = new ArrayList<>();
        private int cursor;
        private Parser(String source) {
            String text = source.startsWith("\ufeff") ? source.substring(1) : source;
            Matcher matcher = TOKEN.matcher(text);
            int offset = 0;
            while (matcher.find()) {
                assertEquals(offset, matcher.start(), "unparsed source byte interval");
                String token = matcher.group();
                if (!Character.isWhitespace(token.charAt(0)) && !token.startsWith("#")) tokens.add(token);
                offset = matcher.end();
            }
            assertEquals(text.length(), offset);
        }
        static Block read(String source) { return new Parser(source).body(false); }
        private Block body(boolean nested) {
            List<Entry> entries = new ArrayList<>();
            while (cursor < tokens.size()) {
                String key = tokens.get(cursor++);
                if (key.equals("}")) { assertTrue(nested); return new Block(entries); }
                assertFalse(key.equals("{") || OPERATORS.contains(key), "field or list atom required");
                if (cursor < tokens.size() && OPERATORS.contains(tokens.get(cursor))) {
                    String operator = tokens.get(cursor++);
                    assertTrue(cursor < tokens.size());
                    String value = tokens.get(cursor++);
                    assertFalse(value.equals("}") || OPERATORS.contains(value));
                    entries.add(new Entry(key, operator, value.equals("{") ? body(true) : new Atom(value)));
                } else entries.add(new Entry("", "", new Atom(key)));
            }
            assertFalse(nested, "unclosed source block");
            return new Block(entries);
        }
    }
}
