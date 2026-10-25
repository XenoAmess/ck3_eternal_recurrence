package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Runs the production AST. Native interaction replies are explicit boundary inputs, not engine evidence. */
final class OptionalReformAndConversionTest {
    private static final String DEFAULTS = "xar_rite_creation_optional_default_doctrines";

    @Test void optionalDefaultsRegisterOnceWithoutAConsumerAndPreserveOtherExtensions() throws IOException {
        Model model = model();
        Entity other = entity(Kind.DOCTRINE, "other_extension_default");
        model.global(DEFAULTS).add(other);
        for (int i = 0; i < 3; i++) model.effect("des_register_optional_rite_creation_defaults_effect", model.actor);
        assertEquals(List.of(other, entity(Kind.DOCTRINE, "des_doctrine_none")), model.global(DEFAULTS));
        assertTrue(model.dispatches.isEmpty());
    }

    @Test void initializedOldSaveCanCollectDefaultsWhilePausedWithoutRerunningWorldInitialization() throws IOException {
        Model model = model();
        model.globalMarkers.addAll(Set.of("des_initialized", "des_maintenance_queued"));
        model.effect("des_initialize_world_effect", model.actor);
        assertEquals(List.of(entity(Kind.DOCTRINE, "des_doctrine_none")), model.global(DEFAULTS));
        model.global(DEFAULTS).clear();
        // Execute the actual neutral parent -> DES child -> registration path.
        // There is deliberately no on_load assumption and no time advance.
        model.onAction("xar_rite_creation_collect_optional_default_doctrines", model.actor);
        assertEquals(List.of(entity(Kind.DOCTRINE, "des_doctrine_none")), model.global(DEFAULTS));
        assertTrue(model.dispatches.isEmpty());
    }

    @Test void disablingDynasticDoctrineClearsOnlyActivePenaltiesAndKeepsHistoricalBinding() throws IOException {
        Model model = model();
        Entity dynasty = entity(Kind.DYNASTY, "bound"), house = entity(Kind.HOUSE, "bound");
        Entity target = model.person("departed", model.oldRite, true);
        Entity unrelatedDynasty = entity(Kind.DYNASTY, "unrelated");
        model.state(model.rite).doctrines.add(entity(Kind.DOCTRINE, "des_doctrine_none"));
        model.state(model.rite).links.putAll(Map.of("des_bound_dynasty", dynasty, "des_join_house", house));
        model.state(dynasty).links.put("des_bound_rite", model.rite);
        model.state(house).links.put("house_dynasty", dynasty);
        model.state(model.actor).links.putAll(Map.of("dynasty", dynasty, "house", house));
        model.state(target).links.put("dynasty", unrelatedDynasty);
        model.state(target).links.put("des_apostate_rite", model.rite);
        model.state(target).traits.add("des_apostate");
        model.list(model.rite, "des_apostates").add(target);
        model.list(model.actor, "des_penalty_targets").add(target);
        model.list(target, "des_observers").add(model.actor);
        model.global("des_bound_rites").add(model.rite);
        model.global("des_apostates").add(target);
        Opinion own = new Opinion(model.actor, target, "des_apostasy_opinion");
        Opinion unrelated = new Opinion(model.actor, target, "unrelated_crime_opinion");
        model.opinions.addAll(Set.of(own, unrelated));

        assertTrue(model.check(model.scripts.get("des_has_binding_trigger"), model.rite));
        assertFalse(model.check(model.scripts.get("des_has_active_binding_trigger"), model.rite));
        model.effect("des_sync_rite_effect", model.rite);
        assertFalse(model.opinions.contains(own));
        assertTrue(model.opinions.contains(unrelated));
        assertFalse(model.state(target).traits.contains("des_apostate"));
        assertFalse(model.state(target).links.containsKey("des_apostate_rite"));
        assertTrue(model.global("des_apostates").isEmpty());
        assertEquals(dynasty, model.state(model.rite).links.get("des_bound_dynasty"));
        assertEquals(house, model.state(model.rite).links.get("des_join_house"));
        assertEquals(model.rite, model.state(dynasty).links.get("des_bound_rite"));
        assertEquals(dynasty, model.state(model.actor).links.get("dynasty"));
        model.state(model.rite).doctrines.clear();
        model.state(model.rite).doctrines.add(entity(Kind.DOCTRINE, "des_doctrine_dynastic"));
        assertTrue(model.check(model.scripts.get("des_has_active_binding_trigger"), model.rite));
    }

    @Test void previewUsesNativeAcceptanceAndSeparatesHumanDecliningAndUnavailableVassals() throws IOException {
        Model model = model();
        Entity yes = model.vassal("yes", true, true, true);
        Entity no = model.vassal("no", true, true, false);
        Entity unavailable = model.vassal("unavailable", true, false, true);
        Entity human = model.vassal("human", false, true, false);
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        assertEquals(List.of(yes), model.list(model.actor, "rrf_vassal_converts"));
        assertEquals(List.of(no), model.list(model.actor, "rrf_vassal_declines"));
        assertEquals(List.of(unavailable), model.list(model.actor, "rrf_vassal_ineligible"));
        assertEquals(List.of(human), model.list(model.actor, "rrf_vassal_players"));
        assertTrue(model.dispatches.isEmpty());
        model.state(model.rite).atoms.remove("rrf_native_configuration_complete");
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        assertTrue(model.list(model.actor, "rrf_vassal_converts").isEmpty());
        assertTrue(model.list(model.actor, "rrf_vassal_players").isEmpty());
    }

    @Test void invitationConsumesDisplayedSnapshotAndRechecksNativeAvailabilityAfterEachDispatch() throws IOException {
        Model model = model();
        Entity first = model.vassal("first", true, true, true);
        Entity second = model.vassal("second", true, true, true);
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        Entity appearedLater = model.vassal("new_since_preview", true, true, true);
        // Boundary simulates a change in the next target's native affordability/availability.
        model.unavailableAfterFirst = second;
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        assertEquals(List.of(first), model.dispatches.stream().map(Dispatch::recipient).toList());
        assertEquals(List.of(first), model.list(model.actor, "rrf_vassal_converted"));
        assertFalse(model.list(model.actor, "rrf_vassal_invited").contains(second));
        assertFalse(model.list(model.actor, "rrf_vassal_invited").contains(appearedLater));
    }

    @Test void humanAndUnknownNativeDispatchesNeverBecomeSuccessOrAutomaticRetries() throws IOException {
        Model model = model();
        Entity unknown = model.vassal("unknown", true, true, true);
        Entity human = model.vassal("human", false, true, true);
        model.nativeStates.put(unknown, new NativeState(true, true, false));
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        assertEquals(2, model.dispatches.size());
        Dispatch humanDispatch = model.dispatches.stream().filter(d -> d.recipient().equals(human)).findFirst().orElseThrow();
        assertEquals("decline", humanDispatch.sendThreshold());
        assertEquals("", humanDispatch.executeThreshold());
        assertTrue(model.list(model.actor, "rrf_vassal_converted").isEmpty());
        assertEquals(Set.of(unknown, human), Set.copyOf(model.list(model.actor, "rrf_vassal_pending")));
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        assertEquals(2, model.dispatches.size());
        model.state(human).links.put("rite", model.rite);
        model.effect("rrf_check_vassal_conversion_results_effect", model.actor);
        assertEquals(List.of(human), model.list(model.actor, "rrf_vassal_converted"));
        assertEquals(List.of(unknown), model.list(model.actor, "rrf_vassal_pending"));
    }

    @Test void actualFaithChoosesStockInteractionAndNoSourceRiteIsMutated() throws IOException {
        Model model = model();
        Entity same = model.vassal("same_faith", true, true, true);
        Entity different = model.vassal("other_faith", true, true, true);
        model.state(different).links.put("faith", entity(Kind.FAITH, "other"));
        Set<Entity> before = Set.copyOf(model.state(model.oldRite).doctrines);
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        assertEquals("sway_vassal_to_my_rite_interaction", model.dispatches.stream().filter(d -> d.recipient().equals(same)).findFirst().orElseThrow().interaction());
        assertEquals("ask_for_conversion_interaction", model.dispatches.stream().filter(d -> d.recipient().equals(different)).findFirst().orElseThrow().interaction());
        assertEquals(before, model.state(model.oldRite).doctrines);
        assertEquals(model.oldRite, model.state(model.oldRite).links.get("self_identity"));
    }

    @Test void attemptedDispatchesRemainGuardedForOneRiteAndResetOnlyForAnotherResult() throws IOException {
        Model model = model();
        Entity target = model.vassal("target", true, true, true);
        model.nativeStates.put(target, new NativeState(true, true, false));
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        assertEquals(1, model.dispatches.size());
        Entity next = entity(Kind.RITE, "next_result");
        model.state(next).links.putAll(Map.of("faith", model.faith, "rrf_origin_founder", model.actor));
        model.state(next).atoms.put("rrf_native_configuration_complete", "yes");
        model.state(model.actor).links.putAll(Map.of("rite", next, "rrf_last_result_rite", next));
        model.effect("rrf_refresh_vassal_conversion_preview_effect", model.actor);
        assertTrue(model.list(model.actor, "rrf_vassal_invited").isEmpty());
        model.effect("rrf_invite_previewed_vassals_effect", model.actor);
        assertEquals(2, model.dispatches.size());
        assertEquals(next, model.state(model.actor).links.get("rrf_vassal_preview_result"));
    }

    private static Model model() throws IOException {
        Model model = new Model();
        Path rrf = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize();
        Path des = rrf.getParent().resolve("mod_dynastic_esotericism");
        for (String relative : List.of("common/scripted_effects/des_initialization_effects.txt", "common/scripted_effects/des_maintenance_effects.txt", "common/scripted_effects/des_binding_effects.txt", "common/scripted_effects/des_character_effects.txt", "common/scripted_effects/des_crime_effects.txt", "common/scripted_triggers/des_dynastic_triggers.txt", "common/on_action/des_on_actions.txt")) model.add(Files.readString(des.resolve(relative)));
        for (String relative : List.of("common/scripted_effects/rrf_conversion_effects.txt", "common/scripted_triggers/rrf_conversion_triggers.txt")) model.add(Files.readString(rrf.resolve(relative)));
        return model;
    }

    private enum Kind { CHARACTER, RITE, FAITH, DYNASTY, HOUSE, DOCTRINE }
    private record Entity(Kind kind, String id) { }
    private record Opinion(Entity observer, Entity target, String modifier) { }
    private record NativeState(boolean available, boolean accepted, boolean actuallyConverts) { }
    private record Dispatch(Entity actor, Entity recipient, String interaction, String sendThreshold, String executeThreshold) { }
    private static Entity entity(Kind kind, String id) { return new Entity(kind, id); }
    private static final class State {
        final Map<String, Entity> links = new LinkedHashMap<>();
        final Map<String, String> atoms = new LinkedHashMap<>();
        final Map<String, List<Entity>> lists = new LinkedHashMap<>();
        final Set<Entity> doctrines = new LinkedHashSet<>(), known = new LinkedHashSet<>();
        final Set<String> traits = new LinkedHashSet<>();
        boolean alive = true, ai = true;
    }

    /** Only interprets commands reached in these contracts; unknown operations fail closed. */
    private static final class Model {
        final Entity actor = entity(Kind.CHARACTER, "actor"), rite = entity(Kind.RITE, "result"), oldRite = entity(Kind.RITE, "source"), faith = entity(Kind.FAITH, "base");
        final Map<Entity, State> states = new LinkedHashMap<>();
        final Map<String, Clausewitz.Block> scripts = new LinkedHashMap<>();
        final Map<String, Entity> saved = new LinkedHashMap<>();
        final Map<String, List<Entity>> globals = new LinkedHashMap<>(), locals = new LinkedHashMap<>();
        final Set<String> globalMarkers = new LinkedHashSet<>();
        final Set<Opinion> opinions = new LinkedHashSet<>();
        final Map<Entity, NativeState> nativeStates = new LinkedHashMap<>();
        final List<Dispatch> dispatches = new ArrayList<>();
        Entity unavailableAfterFirst;
        Model() {
            state(actor).links.putAll(Map.of("rite", rite, "faith", faith, "rrf_last_result_rite", rite));
            state(actor).atoms.put("rrf_state", "flag:succeeded");
            state(rite).links.putAll(Map.of("faith", faith, "rrf_origin_founder", actor));
            state(rite).atoms.put("rrf_native_configuration_complete", "yes");
            state(oldRite).links.putAll(Map.of("faith", faith, "self_identity", oldRite));
            saved.put("rrf_conversion_actor", actor);
        }
        State state(Entity owner) { return states.computeIfAbsent(Objects.requireNonNull(owner), unused -> new State()); }
        List<Entity> list(Entity owner, String key) { return state(owner).lists.computeIfAbsent(key, unused -> new ArrayList<>()); }
        List<Entity> global(String key) { return globals.computeIfAbsent(key, unused -> new ArrayList<>()); }
        Entity person(String id, Entity currentRite, boolean ai) { Entity person = entity(Kind.CHARACTER, id); state(person).links.putAll(Map.of("rite", currentRite, "faith", faith)); state(person).ai = ai; return person; }
        Entity vassal(String id, boolean ai, boolean available, boolean accepted) { Entity vassal = person(id, oldRite, ai); state(vassal).links.put("liege", actor); nativeStates.put(vassal, new NativeState(available, accepted, ai)); return vassal; }
        void add(String source) { for (Clausewitz.Entry entry : Clausewitz.parse(source).entries()) if (entry.value() instanceof Clausewitz.Block body) scripts.put(entry.key(), body); }
        void effect(String name, Entity current) { run(Objects.requireNonNull(scripts.get(name), name), current); }
        void onAction(String name, Entity current) { Clausewitz.Block action = Objects.requireNonNull(scripts.get(name), name); run(action.block("effect"), current); for (Clausewitz.Entry child : action.block("on_actions").entries()) onAction(((Clausewitz.Atom) child.value()).token(), current); }
        Entity resolve(String token, Entity current) {
            String[] path = token.split("\\.");
            Entity value;
            String first = path[0];
            if (first.equals("this")) value = current;
            else if (first.startsWith("scope:")) value = saved.get(first.substring(6));
            else if (first.startsWith("var:")) value = state(current).links.get(first.substring(4));
            else if (first.startsWith("doctrine:")) value = entity(Kind.DOCTRINE, first.substring(9));
            else value = state(current).links.get(first);
            for (int i = 1; i < path.length && value != null; i++) value = state(value).links.get(path[i].startsWith("var:") ? path[i].substring(4) : path[i]);
            return value;
        }
        boolean check(Clausewitz.Block body, Entity current) {
            boolean matched = false;
            for (Clausewitz.Entry e : body.entries()) {
                if (e.key().equals("limit") || e.key().equals("text")) continue;
                if (Set.of("trigger_if", "trigger_else_if", "trigger_else").contains(e.key())) {
                    Clausewitz.Block branch = (Clausewitz.Block) e.value();
                    if (e.key().equals("trigger_if")) matched = false;
                    boolean take = !matched && (e.key().equals("trigger_else") || check(branch.block("limit"), current));
                    if (take) { matched = true; if (!check(branch, current)) return false; }
                } else if (!condition(e, current)) return false;
            }
            return true;
        }
        boolean condition(Clausewitz.Entry e, Entity current) {
            if (e.value() instanceof Clausewitz.Block child) {
                if (scripts.containsKey(e.key())) return check(bind(scripts.get(e.key()), child), current);
                return switch (e.key()) {
                case "OR" -> child.entries().stream().anyMatch(x -> condition(x, current));
                case "NOR" -> child.entries().stream().noneMatch(x -> condition(x, current));
                case "NOT" -> !check(child, current);
                case "AND", "custom_description", "custom_tooltip" -> check(child, current);
                case "is_target_in_variable_list" -> list(current, child.atom("name", "")).contains(resolve(child.atom("target", ""), current));
                case "is_target_in_global_variable_list" -> global(child.atom("name", "")).contains(resolve(child.atom("target", ""), current));
                case "is_character_interaction_valid" -> nativeState(child, current).available();
                case "is_character_interaction_potentially_accepted" -> nativeState(child, current).available() && nativeState(child, current).accepted();
                case "pam_sway_to_rite_variant_can_send_trigger" -> nativeStates.get(saved.get("rrf_conversion_target")).accepted();
                default -> check(child, Objects.requireNonNull(resolve(e.key(), current), e.key()));
                };
            }
            String token = ((Clausewitz.Atom) e.value()).token();
            if (scripts.containsKey(e.key())) return token.equals("yes") == check(scripts.get(e.key()), current);
            return switch (e.key()) {
                case "always" -> token.equals("yes");
                case "exists" -> resolve(token, current) != null;
                case "has_global_variable" -> globalMarkers.contains(token);
                case "has_variable" -> state(current).links.containsKey(token) || state(current).atoms.containsKey(token);
                case "has_variable_list" -> !list(current, token).isEmpty();
                case "is_alive" -> state(current).alive == token.equals("yes");
                case "is_ai" -> state(current).ai == token.equals("yes");
                case "is_playable_character" -> current.kind() == Kind.CHARACTER;
                case "knows_doctrine" -> state(current).known.contains(resolve(token, current));
                case "rite_has_doctrine" -> state(current).doctrines.contains(entity(Kind.DOCTRINE, token));
                case "has_trait" -> state(current).traits.contains(token);
                default -> {
                    if (e.key().startsWith("var:") && state(current).atoms.containsKey(e.key().substring(4))) yield Objects.equals(state(current).atoms.get(e.key().substring(4)), token);
                    boolean same = Objects.equals(resolve(e.key(), current), resolve(token, current));
                    yield e.operator().equals("!=") ? !same : same;
                }
            };
        }
        NativeState nativeState(Clausewitz.Block arguments, Entity current) { return nativeStates.getOrDefault(resolve(arguments.atom("recipient", ""), current), new NativeState(false, false, false)); }
        void run(Clausewitz.Block body, Entity current) {
            boolean matched = false;
            for (Clausewitz.Entry e : body.entries()) {
                if (e.key().equals("limit")) continue;
                if (Set.of("if", "else_if", "else").contains(e.key())) {
                    Clausewitz.Block branch = (Clausewitz.Block) e.value();
                    if (e.key().equals("if")) matched = false;
                    if (!matched && (e.key().equals("else") || check(branch.block("limit"), current))) { matched = true; run(branch, current); }
                } else command(e, current);
            }
        }
        void command(Clausewitz.Entry e, Entity current) {
            if (scripts.containsKey(e.key())) {
                Clausewitz.Block script = scripts.get(e.key());
                if (e.value() instanceof Clausewitz.Block args) script = bind(script, args);
                run(script, current); return;
            }
            if (e.value() instanceof Clausewitz.Atom value) {
                switch (e.key()) {
                    case "save_scope_as" -> saved.put(value.token(), current);
                    case "remove_variable" -> { state(current).links.remove(value.token()); state(current).atoms.remove(value.token()); }
                    case "clear_variable_list" -> list(current, value.token()).clear();
                    case "clear_global_variable_list" -> global(value.token()).clear();
                    case "add_to_list" -> locals.computeIfAbsent(value.token(), unused -> new ArrayList<>()).add(current);
                    case "remove_from_list" -> locals.computeIfAbsent(value.token(), unused -> new ArrayList<>()).remove(current);
                    case "add_known_doctrine" -> state(current).known.add(entity(Kind.DOCTRINE, value.token()));
                    case "add_trait" -> state(current).traits.add(value.token());
                    case "remove_trait" -> state(current).traits.remove(value.token());
                    default -> throw new IllegalArgumentException("unsupported effect: " + e.key());
                }
                return;
            }
            Clausewitz.Block child = (Clausewitz.Block) e.value();
            switch (e.key()) {
                case "set_variable" -> { String name = child.atom("name", ""); String token = child.atom("value", ""); Entity target = resolve(token, current); if (target == null) state(current).atoms.put(name, token); else state(current).links.put(name, target); }
                case "set_global_variable" -> globalMarkers.add(child.atom("name", ""));
                case "add_to_variable_list" -> list(current, child.atom("name", "")).add(resolve(child.atom("target", ""), current));
                case "add_to_global_variable_list" -> global(child.atom("name", "")).add(resolve(child.atom("target", ""), current));
                case "remove_list_variable" -> list(current, child.atom("name", "")).remove(resolve(child.atom("target", ""), current));
                case "remove_list_global_variable" -> global(child.atom("name", "")).remove(resolve(child.atom("target", ""), current));
                case "remove_opinion" -> opinions.remove(new Opinion(current, resolve(child.atom("target", ""), current), child.atom("modifier", "")));
                case "every_in_list" -> iterate(child, current, child.named("variable").isEmpty() ? locals.getOrDefault(child.atom("list", ""), List.of()) : list(current, child.atom("variable", "")));
                case "every_in_global_list" -> iterate(child, current, global(child.atom("variable", "")));
                case "every_vassal" -> iterate(child, current, states.keySet().stream().filter(x -> x.kind() == Kind.CHARACTER && current.equals(state(x).links.get("liege"))).toList());
                case "every_dynasty_member" -> iterate(child, current, states.keySet().stream().filter(x -> x.kind() == Kind.CHARACTER && current.equals(state(x).links.get("dynasty"))).toList());
                case "run_interaction" -> dispatch(child, current);
                default -> run(child, Objects.requireNonNull(resolve(e.key(), current), "unsupported scope effect: " + e.key()));
            }
        }
        Clausewitz.Block bind(Clausewitz.Block script, Clausewitz.Block arguments) {
            Map<String, String> parameters = new LinkedHashMap<>();
            for (Clausewitz.Entry argument : arguments.entries()) parameters.put("$" + argument.key() + "$", ((Clausewitz.Atom) argument.value()).token());
            return Clausewitz.mapAtoms(script, atom -> { String result = atom; for (Map.Entry<String, String> parameter : parameters.entrySet()) result = result.replace(parameter.getKey(), parameter.getValue()); return result; });
        }
        void iterate(Clausewitz.Block body, Entity owner, List<Entity> values) {
            Clausewitz.Block operations = new Clausewitz.Block(body.entries().stream().filter(e -> !Set.of("list", "variable").contains(e.key())).toList());
            for (Entity item : List.copyOf(values)) if (check(operations.block("limit"), item)) run(operations, item);
        }
        void dispatch(Clausewitz.Block body, Entity current) {
            Entity sender = resolve(body.atom("actor", ""), current), recipient = resolve(body.atom("recipient", ""), current);
            if (!current.equals(sender)) throw new IllegalArgumentException("dispatch must run in sender scope");
            dispatches.add(new Dispatch(sender, recipient, body.atom("interaction", ""), body.atom("send_threshold", ""), body.atom("execute_threshold", "")));
            NativeState nativeState = nativeStates.get(recipient);
            if (nativeState.actuallyConverts()) state(recipient).links.put("rite", rite);
            if (dispatches.size() == 1 && unavailableAfterFirst != null) { NativeState previous = nativeStates.get(unavailableAfterFirst); nativeStates.put(unavailableAfterFirst, new NativeState(false, previous.accepted(), previous.actuallyConverts())); }
        }
    }
}
