package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
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
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Executes the actual setup producers and consumers. Native setters/frames are explicit boundary inputs. */
final class NativeSetupLifecycleTest {
    @Test void editorControlsAreConsumedInsideTheOriginalNativeWindowInsteadOfAStandaloneContext() throws IOException {
        Path source = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize();
        Clausewitz.Block window = Clausewitz.parse(Files.readString(source.resolve("gui/window_rite_creation.gui"))).block("window");
        assertEquals("\"rite_creation_window\"", window.atom("name", ""));
        assertFalse(Files.exists(source.resolve("gui/rrf_native_setup_window.gui")));
        assertFalse(Files.exists(source.resolve("gui/scripted_widgets/rrf_native_setup_widgets.txt")));
        assertFalse(Files.readString(source.resolve("gui/rrf_result_window.gui")).contains("RiteCreationWindow."));
        String manifest = Files.readString(source.resolve("tools/product.json"));
        assertTrue(manifest.contains("\"gui/window_rite_creation.gui\""));
        assertFalse(manifest.contains("rrf_native_setup_window.gui"));

        Map<String, String> originalCallbacks = Map.of("faith_name_edit", "OnEditName", "faith_adjective_edit", "OnEditAdjective", "faith_adherent_edit", "OnEditAdherent", "faith_adherent_plural_edit", "OnEditAdherentPlural");
        for (Map.Entry<String, String> expected : originalCallbacks.entrySet())
            assertEquals("\"[RiteCreationWindow." + expected.getValue() + "]\"", widget(window, expected.getKey()).orElseThrow().atom("ontextedited", ""));
        Clausewitz.Block apply = widget(window, "rrf_native_apply").orElseThrow();
        List<String> actions = apply.named("onclick").stream().map(e -> ((Clausewitz.Atom) e.value()).token()).toList();
        assertEquals(2, actions.size());
        assertTrue(actions.getFirst().contains("rrf_mark_native_apply_gui"));
        assertTrue(actions.getFirst().contains("AddScope( 'rrf_native_target', RiteCreationWindow.GetRite.MakeScope )"));
        assertEquals("\"[RiteCreationWindow.EditRite]\"", actions.getLast());
        assertTrue(apply.atom("enabled", "").contains("RiteCreationWindow.CanEditRite"));
        assertTrue(apply.atom("enabled", "").contains("EqualTo_CFixedPoint( RiteCreationWindow.CalcPietyCost, '(CFixedPoint)0' )"));
        assertTrue(widget(window, "rrf_native_setup_details").orElseThrow().render().contains("RiteCreationWindow.GetEditBlockers"));
        for (String original : List.of("edit_faith", "create_faith", "reform_faith"))
            assertTrue(widget(window, original).orElseThrow().atom("visible", "").contains("Not( GetScriptedGui( 'rrf_native_setup_window_gui' )"));

        assertTrue(widget(window, "mts_tenets_grid_scroll").isPresent());
        Clausewitz.Block cores = widget(window, "tenets_grid").orElseThrow().block("item").block("button_group");
        assertTrue(cores.atom("enabled", "").contains("Not( GetScriptedGui( 'rrf_native_setup_window_gui' )"));
        assertTrue(cores.atom("visible", "").contains("TenetType.IsValid"));
        String nativeBody = window.render();
        for (String category : List.of("main_group", "marriage", "crimes", "clergy"))
            assertTrue(nativeBody.contains("RiteCreationWindow.GetCategoryHelper( '" + category + "' ).GetCategory"));
        for (String nativeInput : List.of("RiteCreationWindow.SelectFaithIcon", "RiteCreationWindow.SetColor", "RiteCreationWindow.GetSins", "RiteCreationWindow.GetVirtues"))
            assertTrue(nativeBody.contains(nativeInput));
    }

    @Test void nativeWindowGateRequiresTheActualTargetWhileRecoveryDoesNotInventAnEditorContext() throws IOException {
        Model model = model(true);
        assertFalse(model.guiShown("rrf_native_setup_window_gui", model.actor));
        assertFalse(model.guiShown("rrf_native_recovery_gui", model.actor));
        model.effect("rrf_begin_native_setup_effect", model.actor);
        assertTrue(model.guiShown("rrf_native_recovery_gui", model.actor));
        for (Node wrong : List.of(model.sourceA, model.sourceB, model.other)) {
            model.saved.put("rrf_native_target", wrong);
            assertFalse(model.guiShown("rrf_native_setup_window_gui", model.actor));
        }
        model.saved.put("rrf_native_target", model.result);
        assertTrue(model.guiShown("rrf_native_setup_window_gui", model.actor));
        model.guiExecute("rrf_cancel_native_setup_gui", model.actor);
        assertFalse(model.guiShown("rrf_native_recovery_gui", model.actor));
        assertTrue(model.guiShown("rrf_result_window_gui", model.actor));
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
        assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
    }

    private static Optional<Clausewitz.Block> widget(Clausewitz.Block parent, String name) {
        if (parent.atom("name", "").equals("\"" + name + "\"")) return Optional.of(parent);
        for (Clausewitz.Entry entry : parent.entries()) if (entry.value() instanceof Clausewitz.Block child) {
            Optional<Clausewitz.Block> found = widget(child, name);
            if (found.isPresent()) return found;
        }
        return Optional.empty();
    }

    @Test void permissionBelongsOnlyToTheCurrentResultAndItsActualFounder() throws IOException {
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        assertTrue(model.trigger("rrf_native_setup_permission_trigger", model.actor));
        for (Node wrong : List.of(model.sourceA, model.sourceB)) {
            model.state(model.actor).links.put("rite", wrong);
            assertFalse(model.trigger("rrf_native_setup_permission_trigger", model.actor));
        }
        model.state(model.actor).links.put("rite", model.result);
        model.state(model.result).variables.put("rrf_origin_founder", new Reference(model.other));
        assertFalse(model.trigger("rrf_native_setup_permission_trigger", model.actor));
        model.state(model.result).variables.put("rrf_origin_founder", new Reference(model.actor));
        assertTrue(model.trigger("rrf_native_setup_permission_trigger", model.actor));
    }

    @Test void setupBlocksAnotherCreationAndKeepsTheStockRulesOutsideTheSession() throws IOException {
        Model model = model(true);
        assertTrue(model.trigger("can_create_rite", model.actor));
        assertFalse(model.trigger("can_edit_rite", model.actor));
        model.effect("rrf_begin_native_setup_effect", model.actor);
        assertFalse(model.trigger("can_create_rite", model.actor));
        assertTrue(model.trigger("can_edit_rite", model.actor));
        model.state(model.actor).flags.remove("rrf_native_setup_active");
        assertTrue(model.trigger("can_create_rite", model.actor));
        assertFalse(model.trigger("can_edit_rite", model.actor));
    }

    @Test void sessionRequiresBothFinitePermissionAndWaiverAndPreservesTheStockBlockers() throws IOException {
        for (String blocker : List.of("is_adult", "is_at_war", "is_imprisoned", "council")) {
            Model model = model(true);
            model.effect("rrf_begin_native_setup_effect", model.actor);
            if (blocker.equals("council")) model.state(model.faith).variables.put("ecumenical_council_ongoing", new Token("yes"));
            else model.state(model.actor).booleans.put(blocker, !blocker.equals("is_adult"));
            assertFalse(model.trigger("rrf_native_setup_permission_trigger", model.actor), blocker);
        }
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.state(model.actor).modifiers.remove("rrf_native_setup_cost_waiver");
        assertFalse(model.trigger("rrf_native_setup_permission_trigger", model.actor));
        model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        assertTrue(model.trigger("rrf_native_setup_permission_trigger", model.actor));
        model.advanceYears(1);
        assertFalse(model.trigger("rrf_native_setup_permission_trigger", model.actor));
        assertFalse(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
    }

    @Test void nativeApplyRequestAloneDoesNotFinishOrRemoveTheWaiver() throws IOException {
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.effect("rrf_mark_native_apply_effect", model.actor);
        assertTrue(model.state(model.actor).flags.containsKey("rrf_native_apply_requested"));
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
        assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
        assertFalse(model.state(model.actor).flags.containsKey("rrf_result_dialog"));
    }

    @Test void applyEntryIndependentlyChecksTheActualEditorTarget() throws IOException {
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        for (Node wrong : List.of(model.sourceA, model.sourceB, model.other)) {
            model.saved.put("rrf_native_target", wrong);
            assertFalse(model.guiValid("rrf_mark_native_apply_gui", model.actor));
            model.effect("rrf_mark_native_apply_effect", model.actor);
            assertFalse(model.state(model.actor).flags.containsKey("rrf_native_apply_requested"));
        }
        model.saved.put("rrf_native_target", model.result);
        assertTrue(model.guiValid("rrf_mark_native_apply_gui", model.actor));
    }

    @Test void closingAfterRequestOrDeclineKeepsPermissionUntilAnActualNativeUpdate() throws IOException {
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.guiExecute("rrf_mark_native_apply_gui", model.actor);
        model.guiExecute("rrf_cancel_native_setup_gui", model.actor);
        assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
        assertTrue(model.state(model.actor).flags.containsKey("rrf_native_setup_active"));
        assertTrue(model.state(model.actor).flags.containsKey("rrf_result_dialog"));
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
        assertFalse(model.guiValid("rrf_keep_defaults_gui", model.actor));
        model.guiExecute("rrf_resume_native_setup_gui", model.actor);
        assertTrue(model.guiValid("rrf_mark_native_apply_gui", model.actor));
        model.saved.put("consume_rite_edit_token", model.token);
        model.onAction("on_rite_updated", model.result);
        assertTrue(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
        assertFalse(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
    }

    @Test void launchConsumerAcknowledgesOneRequestAndOnlyExplicitResumeRequestsAnother() throws IOException {
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        assertTrue(model.guiShown("rrf_native_launch_gui", model.actor));
        model.guiExecute("rrf_native_open_ack_gui", model.actor);
        assertFalse(model.guiShown("rrf_native_launch_gui", model.actor));
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
        assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
        assertFalse(model.state(model.actor).flags.containsKey("rrf_native_apply_requested"));
        model.guiExecute("rrf_resume_native_setup_gui", model.actor);
        assertTrue(model.guiShown("rrf_native_launch_gui", model.actor));
        model.guiExecute("rrf_native_open_ack_gui", model.actor);
        assertFalse(model.guiShown("rrf_native_launch_gui", model.actor));
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
    }

    @Test void onlyActualUpdatedResultWithTheNativeTokenAndApplyRequestFinishes() throws IOException {
        for (String missing : List.of("consume", "apply", "active", "actual_rite", "last_result", "founder", "none")) {
            Model model = model(true);
            model.effect("rrf_begin_native_setup_effect", model.actor);
            model.effect("rrf_mark_native_apply_effect", model.actor);
            if (!missing.equals("consume")) model.saved.put("consume_rite_edit_token", model.token);
            if (missing.equals("apply")) model.state(model.actor).flags.remove("rrf_native_apply_requested");
            if (missing.equals("active")) model.state(model.actor).flags.remove("rrf_native_setup_active");
            if (missing.equals("actual_rite")) model.state(model.actor).links.put("rite", model.sourceA);
            if (missing.equals("last_result")) model.state(model.actor).variables.put("rrf_last_result_rite", new Reference(model.sourceA));
            if (missing.equals("founder")) model.state(model.result).variables.put("rrf_origin_founder", new Reference(model.other));
            model.onAction("on_rite_updated", model.result);
            assertEquals(missing.equals("none"), model.state(model.result).variables.containsKey("rrf_native_configuration_complete"), missing);
            if (missing.equals("none")) {
                assertFalse(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
                assertFalse(model.state(model.actor).flags.containsKey("rrf_native_setup_active"));
                assertTrue(model.state(model.actor).flags.containsKey("rrf_result_dialog"));
            } else assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"), missing);
        }
    }

    @Test void unrelatedRiteUpdateCannotConsumeAnOwnedSetupSession() throws IOException {
        Model model = model(true);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.effect("rrf_mark_native_apply_effect", model.actor);
        model.saved.put("consume_rite_edit_token", model.token);
        model.state(model.sourceA).variables.put("rrf_origin_founder", new Reference(model.actor));
        model.onAction("on_rite_updated", model.sourceA);
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
        assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
    }

    @Test void explicitFinishKeepsDefaultContentAndCannotReopenACompletedResult() throws IOException {
        Model model = model(true);
        Set<Node> before = Set.copyOf(model.state(model.result).doctrines);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.guiExecute("rrf_keep_defaults_gui", model.actor);
        assertEquals(before, model.state(model.result).doctrines);
        assertEquals(new Token("yes"), model.state(model.result).variables.get("rrf_native_configuration_complete"));
        assertFalse(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
        model.effect("rrf_begin_native_setup_effect", model.actor);
        assertFalse(model.state(model.actor).flags.containsKey("rrf_native_open_requested"));
        assertFalse(model.state(model.actor).flags.containsKey("rrf_native_setup_active"));
        assertTrue(model.guiValid("rrf_configured_result_gui", model.actor));
    }

    @Test void optionalProviderIsCollectedByTheActualConsumerDespiteTheLaterEmptyParent() throws IOException {
        Model model = model(true);
        Node none = node(Kind.DOCTRINE, "des_doctrine_none"), dynastic = node(Kind.DOCTRINE, "des_doctrine_dynastic");
        model.state(model.sourceA).doctrines.add(dynastic);
        model.state(model.result).doctrines.add(dynastic);
        model.effect("rrf_apply_creation_options_effect", model.actor);
        assertEquals(List.of(none), model.globals.get("xar_rite_creation_optional_default_doctrines"));
        assertEquals(Set.of(none), model.state(model.result).doctrines);
        assertEquals(Set.of(dynastic), model.state(model.sourceA).doctrines);
        assertTrue(model.state(model.sourceB).doctrines.isEmpty());
        model.effect("rrf_apply_creation_options_effect", model.actor);
        assertEquals(List.of(none), model.globals.get("xar_rite_creation_optional_default_doctrines"));
    }

    @Test void noProviderRequiresNoOptionalDatabaseObjectOrPrivateFunction() throws IOException {
        Model model = model(false);
        model.effect("rrf_apply_creation_options_effect", model.actor);
        assertTrue(model.state(model.result).doctrines.isEmpty());
        assertTrue(model.globals.getOrDefault("xar_rite_creation_optional_default_doctrines", List.of()).isEmpty());
    }

    @Test void realCompletionRecordsTheResultChargesOnceAndThenBeginsSetupAfterAdoption() throws IOException {
        Model model = model(true);
        model.state(model.actor).links.put("rite", model.sourceA);
        model.effect("rrf_complete_success_effect", model.actor);
        assertEquals(new Reference(model.actor), model.state(model.result).variables.get("rrf_origin_founder"));
        assertEquals(new Reference(model.sourceA), model.state(model.result).variables.get("rrf_origin_a"));
        assertEquals(new Reference(model.sourceB), model.state(model.result).variables.get("rrf_origin_b"));
        assertEquals(new NumberValue(new BigDecimal("500")), model.state(model.actor).variables.get("rrf_charged_cost"));
        assertEquals(new BigDecimal("1500"), model.state(model.actor).piety);
        assertEquals(model.result, model.state(model.actor).links.get("rite"));
        assertTrue(model.state(model.actor).flags.containsKey("rrf_native_open_requested"));
        assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
        assertFalse(model.state(model.actor).variables.containsKey("rrf_source_a"));
        assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete"));
    }

    @Test void rejectedNativeAdoptionCannotEnterASetupOrClaimSuccess() throws IOException {
        Model model = model(true);
        model.state(model.actor).links.put("rite", model.sourceA);
        model.nativeAdoptionSucceeds = false;
        model.effect("rrf_complete_success_effect", model.actor);
        assertEquals(new Token("flag:unresolved"), model.state(model.actor).variables.get("rrf_state"));
        assertEquals(model.sourceA, model.state(model.actor).links.get("rite"));
        assertFalse(model.state(model.actor).flags.containsKey("rrf_native_setup_active"));
        assertFalse(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver"));
    }

    static Model model(boolean provider) throws IOException {
        Model model = new Model();
        Path rrf = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize();
        if (provider) {
            Path des = rrf.getParent().resolve("mod_dynastic_esotericism");
            model.load(des.resolve("common/scripted_effects/des_initialization_effects.txt"), SourceKind.SCRIPTS);
            model.load(des.resolve("common/on_action/des_on_actions.txt"), SourceKind.ON_ACTIONS);
            for (Clausewitz.Entry definition : Clausewitz.parse(Files.readString(des.resolve("common/religion/doctrine_types/des_doctrines.txt"))).entries()) model.doctrineGroups.put(node(Kind.DOCTRINE, definition.key()), ((Clausewitz.Block) definition.value()).atom("doctrine_group_type", ""));
        }
        for (String path : List.of("common/scripted_effects/rrf_native_setup_effects.txt", "common/scripted_triggers/rrf_native_setup_triggers.txt", "common/scripted_rules/zz_rrf_native_setup_rules.txt", "common/scripted_effects/rrf_creation_options_effects.txt", "common/scripted_effects/rrf_completion_effects.txt", "common/scripted_effects/rrf_draft_effects.txt", "common/script_values/rrf_values.txt", "common/scripted_effects/rrf_conversion_effects.txt", "common/scripted_triggers/rrf_conversion_triggers.txt", "common/scripted_guis/rrf_scripted_guis.txt", "common/scripted_effects/rrf_final_configuration_effects.txt")) model.load(rrf.resolve(path), SourceKind.SCRIPTS);
        // Providers are deliberately read first, matching the requested mod order.
        model.load(rrf.resolve("common/on_action/rrf_native_setup_on_actions.txt"), SourceKind.ON_ACTIONS);
        model.effect("rrf_record_final_configuration_contract_effect", model.actor);
        return model;
    }

    private enum SourceKind { SCRIPTS, ON_ACTIONS }
    enum Kind { CHARACTER, RITE, FAITH, TENET, DOCTRINE, MARKER }
    record Node(Kind kind, String id) { }
    private record Frame(Node current, Node previous, Node root) { Frame enter(Node target) { return new Frame(target, current, root); } }
    sealed interface Stored permits Reference, Token, NumberValue { }
    record Reference(Node node) implements Stored { }
    record Token(String token) implements Stored { }
    record NumberValue(BigDecimal value) implements Stored { }
    private record Expiry(int year) { }
    static Node node(Kind kind, String id) { return new Node(kind, id); }
    static final class State {
        final Map<String, Node> links = new LinkedHashMap<>();
        final Map<String, Stored> variables = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new LinkedHashMap<>();
        final Map<String, Expiry> flags = new LinkedHashMap<>(), modifiers = new LinkedHashMap<>();
        final Map<String, Boolean> booleans = new LinkedHashMap<>();
        final Set<Node> doctrines = new LinkedHashSet<>();
        final Set<Node> cores = new LinkedHashSet<>();
        BigDecimal piety = new BigDecimal("2000");
    }

    /** The supported subset is explicit. An unimplemented command or native query fails this test. */
    static final class Model {
        final Node actor = node(Kind.CHARACTER, "creator"), other = node(Kind.CHARACTER, "other"), result = node(Kind.RITE, "result"), sourceA = node(Kind.RITE, "a"), sourceB = node(Kind.RITE, "b"), faith = node(Kind.FAITH, "base"), token = node(Kind.MARKER, "native_edit_token");
        final Map<Node, State> states = new LinkedHashMap<>();
        final Map<String, Clausewitz.Block> scripts = new LinkedHashMap<>(), actions = new LinkedHashMap<>();
        final Map<String, BigDecimal> constants = new LinkedHashMap<>();
        final Map<String, Node> saved = new LinkedHashMap<>();
        final Map<String, List<Node>> globals = new LinkedHashMap<>(), locals = new LinkedHashMap<>();
        final Map<Node, String> doctrineGroups = new LinkedHashMap<>();
        final Map<String, Boolean> nativeRules = Map.of("can_create_rite_trigger", true, "can_edit_rite_trigger", false);
        final Set<String> globalMarkers = new LinkedHashSet<>();
        final List<String> toasts = new ArrayList<>();
        boolean nativeAdoptionSucceeds = true;
        int year;
        Model() {
            state(actor).links.putAll(Map.of("rite", result, "faith", faith));
            state(actor).variables.putAll(Map.of("rrf_last_result_rite", new Reference(result), "rrf_source_a", new Reference(sourceA), "rrf_source_b", new Reference(sourceB), "rrf_source_a_faith", new Reference(faith), "rrf_source_b_faith", new Reference(faith), "rrf_mode", new Token("flag:rite"), "rrf_state", new Token("flag:succeeded")));
            state(actor).booleans.putAll(Map.of("is_ai", false, "is_alive", true, "is_adult", true, "is_at_war", false, "is_imprisoned", false));
            state(result).variables.put("rrf_origin_founder", new Reference(actor));
            for (Node rite : List.of(result, sourceA, sourceB)) state(rite).links.put("faith", faith);
            Node aCore = node(Kind.TENET, "a_core"), bCore = node(Kind.TENET, "b_core"), shared = node(Kind.TENET, "shared_core"), otherShared = node(Kind.TENET, "other_shared_core");
            state(sourceA).cores.addAll(List.of(aCore, shared, otherShared));
            state(sourceB).cores.addAll(List.of(bCore, shared, otherShared));
            state(result).cores.addAll(List.of(aCore, bCore, shared));
            list(actor, "rrf_selected_tenets").addAll(state(result).cores);
            list(result, "rrf_origin_core_tenets").addAll(state(result).cores);
            saved.putAll(Map.of("rrf_actor", actor, "rrf_new_rite", result, "rrf_native_target", result));
        }
        State state(Node owner) { return states.computeIfAbsent(Objects.requireNonNull(owner), unused -> new State()); }
        List<Node> list(Node owner, String name) { return state(owner).lists.computeIfAbsent(name, unused -> new ArrayList<>()); }
        void load(Path path, SourceKind kind) throws IOException {
            for (Clausewitz.Entry e : Clausewitz.parse(Files.readString(path)).entries()) {
                if (e.value() instanceof Clausewitz.Atom atom) { constants.put(e.key(), new BigDecimal(atom.token())); continue; }
                Clausewitz.Block body = (Clausewitz.Block) e.value();
                if (kind == SourceKind.SCRIPTS) scripts.put(e.key(), body);
                else actions.merge(e.key(), body, (first, second) -> { List<Clausewitz.Entry> entries = new ArrayList<>(first.entries()); entries.addAll(second.entries()); return new Clausewitz.Block(entries); });
            }
        }
        void advanceYears(int amount) { year += amount; for (State s : states.values()) { s.flags.values().removeIf(x -> x.year() <= year); s.modifiers.values().removeIf(x -> x.year() <= year); } }
        void effect(String name, Node current) { run(Objects.requireNonNull(scripts.get(name), name), new Frame(current, null, current)); }
        boolean trigger(String name, Node current) { return check(Objects.requireNonNull(scripts.get(name), name), new Frame(current, null, current)); }
        boolean guiShown(String name, Node current) { return check(Objects.requireNonNull(scripts.get(name), name).block("is_shown"), new Frame(current, null, current)); }
        boolean guiValid(String name, Node current) { return check(Objects.requireNonNull(scripts.get(name), name).block("is_valid"), new Frame(current, null, current)); }
        void guiExecute(String name, Node current) { if (!guiValid(name, current)) throw new IllegalArgumentException("invalid GUI action: " + name); run(scripts.get(name).block("effect"), new Frame(current, null, current)); }
        void onAction(String name, Node current) { onAction(name, new Frame(current, null, current)); }
        void onAction(String name, Frame frame) {
            Clausewitz.Block body = Objects.requireNonNull(actions.get(name), name);
            if (body.named("effect").size() > 1 || body.named("trigger").size() > 1) throw new IllegalArgumentException("conflicting on_action blocks: " + name);
            if (!check(body.block("trigger"), frame)) return;
            run(body.block("effect"), frame);
            for (Clausewitz.Entry children : body.named("on_actions")) for (Clausewitz.Entry child : ((Clausewitz.Block) children.value()).entries()) onAction(((Clausewitz.Atom) child.value()).token(), frame);
        }
        Stored value(String expression, Frame frame) {
            String[] path = expression.split("\\.");
            Stored current;
            String first = path[0];
            if (first.equals("this")) current = new Reference(frame.current());
            else if (first.equals("prev")) current = frame.previous() == null ? null : new Reference(frame.previous());
            else if (first.equals("root")) current = new Reference(frame.root());
            else if (first.startsWith("scope:")) current = saved.containsKey(first.substring(6)) ? new Reference(saved.get(first.substring(6))) : null;
            else if (first.startsWith("var:")) current = state(frame.current()).variables.get(first.substring(4));
            else if (first.startsWith("doctrine:")) current = new Reference(node(Kind.DOCTRINE, first.substring(9)));
            else if (first.startsWith("tenet:")) current = new Reference(node(Kind.TENET, first.substring(6)));
            else current = state(frame.current()).links.containsKey(first) ? new Reference(state(frame.current()).links.get(first)) : literal(first, frame);
            for (int i = 1; i < path.length && current != null; i++) { Node owner = reference(current); String part = path[i]; current = part.startsWith("var:") ? state(owner).variables.get(part.substring(4)) : state(owner).links.containsKey(part) ? new Reference(state(owner).links.get(part)) : null; }
            return current;
        }
        Stored literal(String text, Frame frame) { if (constants.containsKey(text) || scripts.containsKey(text) && text.endsWith("_value")) return new NumberValue(number(text, frame)); try { return new NumberValue(new BigDecimal(text)); } catch (NumberFormatException ex) { return new Token(text); } }
        Node reference(Stored stored) { if (stored instanceof Reference ref) return ref.node(); throw new IllegalArgumentException("not a scope: " + stored); }
        Node target(String expression, Frame frame) { Stored found = value(expression, frame); return found instanceof Reference ref ? ref.node() : null; }
        BigDecimal number(String expression, Frame frame) {
            if (constants.containsKey(expression)) return constants.get(expression);
            Clausewitz.Block script = scripts.get(expression);
            if (script == null) return new BigDecimal(expression);
            BigDecimal resultValue = BigDecimal.ZERO;
            for (Clausewitz.Entry e : script.entries()) {
                if (e.key().equals("value")) resultValue = number(((Clausewitz.Atom) e.value()).token(), frame);
                else if (e.key().equals("if")) { Clausewitz.Block branch = (Clausewitz.Block) e.value(); if (check(branch.block("limit"), frame)) resultValue = number(branch.atom("value", resultValue.toPlainString()), frame); }
                else throw new IllegalArgumentException("unsupported numeric operation: " + e.key());
            }
            return resultValue;
        }
        boolean check(Clausewitz.Block body, Frame frame) {
            boolean matched = false;
            for (Clausewitz.Entry e : body.entries()) {
                if (Set.of("text", "limit").contains(e.key())) continue;
                if (Set.of("trigger_if", "trigger_else_if", "trigger_else").contains(e.key())) {
                    Clausewitz.Block branch = (Clausewitz.Block) e.value();
                    if (e.key().equals("trigger_if")) matched = false;
                    if (!matched && (e.key().equals("trigger_else") || check(branch.block("limit"), frame))) { matched = true; if (!check(branch, frame)) return false; }
                } else if (!condition(e, frame)) return false;
            }
            return true;
        }
        boolean condition(Clausewitz.Entry e, Frame frame) {
            if (e.value() instanceof Clausewitz.Block child) return switch (e.key()) {
                case "custom_description", "custom_tooltip", "AND" -> check(child, frame);
                case "NOT" -> !check(child, frame);
                case "NOR" -> child.entries().stream().noneMatch(x -> condition(x, frame));
                case "OR" -> child.entries().stream().anyMatch(x -> condition(x, frame));
                case "is_target_in_global_variable_list" -> globals.getOrDefault(child.atom("name", ""), List.of()).contains(target(child.atom("target", ""), frame));
                case "is_target_in_variable_list" -> list(frame.current(), child.atom("name", "")).contains(target(child.atom("target", ""), frame));
                case "any_rite_tenet" -> state(frame.current()).cores.stream().anyMatch(item -> check(child, frame.enter(item)));
                default -> check(child, frame.enter(Objects.requireNonNull(target(e.key(), frame), e.key())));
            };
            String tokenValue = ((Clausewitz.Atom) e.value()).token();
            if (scripts.containsKey(e.key())) return check(scripts.get(e.key()), frame) == tokenValue.equals("yes");
            if (nativeRules.containsKey(e.key())) return nativeRules.get(e.key()) == tokenValue.equals("yes");
            return switch (e.key()) {
                case "always" -> tokenValue.equals("yes");
                case "exists" -> target(tokenValue, frame) != null;
                case "has_variable" -> state(frame.current()).variables.containsKey(tokenValue);
                case "has_global_variable" -> globalMarkers.contains(tokenValue);
                case "has_character_flag" -> state(frame.current()).flags.containsKey(tokenValue);
                case "has_character_modifier" -> state(frame.current()).modifiers.containsKey(tokenValue);
                case "has_variable_list" -> !list(frame.current(), tokenValue).isEmpty();
                case "rite_has_doctrine" -> state(frame.current()).doctrines.contains(target(tokenValue, frame));
                case "is_ai", "is_alive", "is_adult", "is_at_war", "is_imprisoned" -> Objects.requireNonNull(state(frame.current()).booleans.get(e.key()), e.key()) == tokenValue.equals("yes");
                default -> {
                    if (!e.key().startsWith("var:") && !e.key().startsWith("scope:") && !Set.of("this", "prev", "root").contains(e.key()) && !state(frame.current()).links.containsKey(e.key())) throw new IllegalArgumentException("unsupported predicate: " + e.key());
                    Stored left = value(e.key(), frame), right = value(tokenValue, frame); boolean same = left != null && right != null && left.equals(right); yield e.operator().equals("!=") ? !same : same;
                }
            };
        }
        void run(Clausewitz.Block body, Frame frame) {
            boolean matched = false;
            for (Clausewitz.Entry e : body.entries()) {
                if (e.key().equals("limit")) continue;
                if (Set.of("if", "else_if", "else").contains(e.key())) { Clausewitz.Block branch = (Clausewitz.Block) e.value(); if (e.key().equals("if")) matched = false; if (!matched && (e.key().equals("else") || check(branch.block("limit"), frame))) { matched = true; run(branch, frame); } }
                else command(e, frame);
            }
        }
        void command(Clausewitz.Entry e, Frame frame) {
            if (scripts.containsKey(e.key())) { run(scripts.get(e.key()), frame); return; }
            if (e.value() instanceof Clausewitz.Atom atom) {
                String text = atom.token();
                switch (e.key()) {
                    case "save_scope_as" -> saved.put(text, frame.current());
                    case "remove_variable" -> state(frame.current()).variables.remove(text);
                    case "clear_variable_list" -> list(frame.current(), text).clear();
                    case "remove_character_flag" -> state(frame.current()).flags.remove(text);
                    case "remove_character_modifier" -> state(frame.current()).modifiers.remove(text);
                    case "add_character_flag" -> state(frame.current()).flags.put(text, new Expiry(Integer.MAX_VALUE));
                    case "add_to_list" -> locals.computeIfAbsent(text, unused -> new ArrayList<>()).add(frame.current());
                    case "remove_from_list" -> locals.computeIfAbsent(text, unused -> new ArrayList<>()).remove(frame.current());
                    case "set_character_rite" -> { if (nativeAdoptionSucceeds) state(frame.current()).links.put("rite", Objects.requireNonNull(target(text, frame))); }
                    case "change_rite_doctrine" -> {
                        Node doctrine = Objects.requireNonNull(target(text, frame));
                        String group = Objects.requireNonNull(doctrineGroups.get(doctrine), "unbound native doctrine group: " + doctrine);
                        state(frame.current()).doctrines.removeIf(existing -> group.equals(doctrineGroups.get(existing)));
                        state(frame.current()).doctrines.add(doctrine);
                    }
                    default -> throw new IllegalArgumentException("unsupported effect: " + e.key());
                }
                return;
            }
            Clausewitz.Block child = (Clausewitz.Block) e.value();
            switch (e.key()) {
                case "set_variable" -> state(frame.current()).variables.put(child.atom("name", ""), Objects.requireNonNull(value(child.atom("value", ""), frame)));
                case "add_character_flag" -> state(frame.current()).flags.put(child.atom("flag", ""), expiry(child));
                case "add_character_modifier" -> state(frame.current()).modifiers.put(child.atom("modifier", ""), expiry(child));
                case "add_piety" -> state(frame.current()).piety = state(frame.current()).piety.add(number(child.atom("value", "0"), frame).multiply(number(child.atom("multiply", "1"), frame)));
                case "send_interface_toast" -> toasts.add(child.atom("title", ""));
                case "trigger_event" -> onAction(child.atom("on_action", ""), frame);
                case "add_to_global_variable_list" -> globals.computeIfAbsent(child.atom("name", ""), unused -> new ArrayList<>()).add(Objects.requireNonNull(target(child.atom("target", ""), frame)));
                case "add_to_variable_list" -> list(frame.current(), child.atom("name", "")).add(Objects.requireNonNull(target(child.atom("target", ""), frame)));
                case "change_rite_doctrine" -> throw new IllegalArgumentException("unexpected block-valued doctrine setter");
                case "every_in_global_list" -> iterate(child, frame, globals.getOrDefault(child.atom("variable", ""), List.of()));
                case "every_in_list" -> iterate(child, frame, child.named("variable").isEmpty() ? locals.getOrDefault(child.atom("list", ""), List.of()) : list(frame.current(), child.atom("variable", "")));
                case "every_spouse" -> iterate(child, frame, list(frame.current(), "native_spouses"));
                case "every_close_family_member" -> iterate(child, frame, list(frame.current(), "native_close_family"));
                case "every_vassal" -> iterate(child, frame, list(frame.current(), "native_vassals"));
                case "every_rite_tenet" -> iterate(child, frame, List.copyOf(state(frame.current()).cores));
                default -> run(child, frame.enter(Objects.requireNonNull(target(e.key(), frame), "unsupported scope/effect: " + e.key())));
            }
        }
        Expiry expiry(Clausewitz.Block child) { return new Expiry(year + Integer.parseInt(child.atom("years", "0"))); }
        void iterate(Clausewitz.Block child, Frame frame, List<Node> values) {
            Clausewitz.Block operations = new Clausewitz.Block(child.entries().stream().filter(e -> !Set.of("variable", "list").contains(e.key())).toList());
            for (Node item : List.copyOf(values)) { Frame itemFrame = frame.enter(item); if (check(child.block("limit"), itemFrame)) run(operations, itemFrame); }
        }
    }
}
