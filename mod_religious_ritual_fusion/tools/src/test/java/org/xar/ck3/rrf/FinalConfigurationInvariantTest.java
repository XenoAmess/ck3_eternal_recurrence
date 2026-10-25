package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.rrf.NativeSetupLifecycleTest.Kind;
import org.xar.ck3.rrf.NativeSetupLifecycleTest.Model;
import org.xar.ck3.rrf.NativeSetupLifecycleTest.Node;
import org.xar.ck3.rrf.NativeSetupLifecycleTest.State;
import org.xar.ck3.rrf.NativeSetupLifecycleTest.Stored;

/** Executes the production snapshot, final guard, GUI finish and native-update hook without catalog IDs. */
final class FinalConfigurationInvariantTest {
    private static final List<String> CONTRACT_LISTS = List.of("rrf_exclusive_a_tenets", "rrf_exclusive_b_tenets", "rrf_exclusive_a_doctrines", "rrf_exclusive_b_doctrines");

    @Test void oneHundredActualThirdPartyCoresPassOnlyAsTheCompleteRecordedSet() throws IOException {
        Model model = NativeSetupLifecycleTest.model(false);
        List<Node> a = tenets(0, 100), b = tenets(1, 101);
        List<Node> selected = new ArrayList<>(tenets(0, 99)); selected.add(tenet(100));
        configure(model, a, b, selected, List.of());
        SourceImage aBefore = image(model.state(model.sourceA)), bBefore = image(model.state(model.sourceB));
        record(model);
        assertEquals(List.of(tenet(0)), model.list(model.result, "rrf_exclusive_a_tenets"));
        assertEquals(List.of(tenet(100)), model.list(model.result, "rrf_exclusive_b_tenets"));
        Map<String, List<Node>> contract = contract(model);
        model.effect("rrf_validate_final_configuration_effect", model.actor);
        assertValid(model);
        assertEquals(100, model.state(model.result).cores.size());
        assertEquals(contract, contract(model));
        assertEquals(aBefore, image(model.state(model.sourceA))); assertEquals(bBefore, image(model.state(model.sourceB)));
    }

    @Test void removingTheOnlyDoctrineContributionCannotFinishThroughTheRealNativeHook() throws IOException {
        Model model = NativeSetupLifecycleTest.model(false);
        Node bDoctrine = doctrine("third_party_b_unique");
        configure(model, tenets(0, 3), tenets(1, 4), tenets(0, 3), List.of(bDoctrine));
        model.state(model.sourceB).doctrines.add(bDoctrine); model.state(model.result).doctrines.add(bDoctrine);
        SourceImage aBefore = image(model.state(model.sourceA)), bBefore = image(model.state(model.sourceB));
        record(model);
        assertEquals(List.of(), model.list(model.result, "rrf_exclusive_b_tenets"));
        assertEquals(List.of(bDoctrine), model.list(model.result, "rrf_exclusive_b_doctrines"));
        model.effect("rrf_validate_final_configuration_effect", model.actor); assertValid(model);
        Map<String, List<Node>> contract = contract(model);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.guiExecute("rrf_mark_native_apply_gui", model.actor);
        model.state(model.result).doctrines.remove(bDoctrine);
        model.state(model.result).doctrines.add(doctrine("third_party_replacement"));
        model.saved.put("consume_rite_edit_token", model.token);
        model.onAction("on_rite_updated", model.result);
        assertTrue(model.state(model.actor).flags.containsKey("rrf_final_configuration_invalid"));
        assertTrue(model.state(model.actor).flags.containsKey("rrf_final_contribution_a"));
        assertFalse(model.state(model.actor).flags.containsKey("rrf_final_contribution_b"));
        assertPending(model);
        assertTrue(model.toasts.contains("RRF_FINAL_CONFIGURATION_INVALID"));
        assertEquals(contract, contract(model));
        assertEquals(aBefore, image(model.state(model.sourceA))); assertEquals(bBefore, image(model.state(model.sourceB)));
        // Restore actual content and consume the real update hook again; no stale invalid flag may survive.
        model.state(model.result).doctrines.remove(doctrine("third_party_replacement"));
        model.state(model.result).doctrines.add(bDoctrine);
        model.onAction("on_rite_updated", model.result);
        assertValid(model); assertFinished(model);
    }

    @Test void anotherRecordedContributionCanKeepTheSideValidAfterDoctrineReplacement() throws IOException {
        Model model = NativeSetupLifecycleTest.model(false);
        Node bDoctrine = doctrine("third_party_b_unique");
        configure(model, tenets(0, 3), tenets(1, 4), List.of(tenet(0), tenet(1), tenet(3)), List.of(bDoctrine));
        model.state(model.sourceB).doctrines.add(bDoctrine); model.state(model.result).doctrines.add(bDoctrine);
        record(model);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        model.guiExecute("rrf_mark_native_apply_gui", model.actor);
        model.state(model.result).doctrines.remove(bDoctrine);
        model.saved.put("consume_rite_edit_token", model.token);
        model.onAction("on_rite_updated", model.result);
        assertValid(model); assertFinished(model);
    }

    @Test void anEqualCountWithDifferentCoresCannotFinishUsingKeepDefaults() throws IOException {
        Model model = NativeSetupLifecycleTest.model(false);
        configure(model, tenets(0, 3), tenets(1, 4), List.of(tenet(0), tenet(1), tenet(3)), List.of());
        record(model);
        model.effect("rrf_begin_native_setup_effect", model.actor);
        int count = model.state(model.result).cores.size();
        model.state(model.result).cores.remove(tenet(1)); model.state(model.result).cores.add(tenet(99));
        model.guiExecute("rrf_keep_defaults_gui", model.actor);
        assertEquals(count, model.state(model.result).cores.size());
        assertTrue(model.state(model.actor).flags.containsKey("rrf_final_configuration_invalid"));
        // Both exclusive sides still contribute; the rejection is independently due to the wrong core set.
        assertTrue(model.state(model.actor).flags.containsKey("rrf_final_contribution_a"));
        assertTrue(model.state(model.actor).flags.containsKey("rrf_final_contribution_b"));
        assertPending(model);
    }

    @Test void snapshotsCannotBeRewrittenByLaterSourceOrDraftChanges() throws IOException {
        Model model = NativeSetupLifecycleTest.model(false);
        configure(model, tenets(0, 3), tenets(1, 4), List.of(tenet(0), tenet(1), tenet(3)), List.of());
        record(model); Map<String, List<Node>> contract = contract(model);
        model.state(model.sourceB).cores.add(tenet(0));
        model.list(model.actor, "rrf_selected_tenets").clear();
        model.list(model.actor, "rrf_selected_doctrines").add(doctrine("later_draft_content"));
        SourceImage aBefore = image(model.state(model.sourceA)), bBefore = image(model.state(model.sourceB));
        record(model);
        model.effect("rrf_validate_final_configuration_effect", model.actor);
        assertValid(model);
        assertEquals(contract, contract(model));
        assertEquals(aBefore, image(model.state(model.sourceA))); assertEquals(bBefore, image(model.state(model.sourceB)));
    }

    @Test void missingContractOrMissingOriginalCoreSelectionFailsClosed() throws IOException {
        for (String missing : List.of("version", "origin", "result")) {
            Model model = NativeSetupLifecycleTest.model(false);
            if (missing.equals("version")) model.state(model.result).variables.remove("rrf_final_configuration_contract_version");
            if (missing.equals("origin")) model.list(model.result, "rrf_origin_core_tenets").clear();
            if (missing.equals("result")) model.state(model.actor).variables.remove("rrf_last_result_rite");
            model.effect("rrf_validate_final_configuration_effect", model.actor);
            assertTrue(model.state(model.actor).flags.containsKey("rrf_final_configuration_invalid"), missing);
            assertFalse(model.state(model.actor).flags.containsKey("rrf_final_contribution_a"), missing);
            assertFalse(model.state(model.actor).flags.containsKey("rrf_final_contribution_b"), missing);
        }
    }

    private static void configure(Model model, List<Node> a, List<Node> b, List<Node> selected, List<Node> selectedDoctrines) {
        model.state(model.sourceA).cores.clear(); model.state(model.sourceA).cores.addAll(a);
        model.state(model.sourceB).cores.clear(); model.state(model.sourceB).cores.addAll(b);
        model.state(model.result).cores.clear(); model.state(model.result).cores.addAll(selected);
        model.list(model.actor, "rrf_selected_tenets").clear(); model.list(model.actor, "rrf_selected_tenets").addAll(selected);
        model.list(model.actor, "rrf_selected_doctrines").clear(); model.list(model.actor, "rrf_selected_doctrines").addAll(selectedDoctrines);
        model.list(model.result, "rrf_origin_core_tenets").clear(); model.list(model.result, "rrf_origin_core_tenets").addAll(selected);
        model.state(model.result).variables.remove("rrf_final_configuration_contract_version");
        for (String name : CONTRACT_LISTS) model.list(model.result, name).clear();
    }
    private static void record(Model model) { model.effect("rrf_record_final_configuration_contract_effect", model.actor); }
    private static void assertValid(Model model) { assertFalse(model.state(model.actor).flags.containsKey("rrf_final_configuration_invalid")); assertTrue(model.state(model.actor).flags.containsKey("rrf_final_contribution_a")); assertTrue(model.state(model.actor).flags.containsKey("rrf_final_contribution_b")); }
    private static void assertPending(Model model) { assertFalse(model.state(model.result).variables.containsKey("rrf_native_configuration_complete")); assertTrue(model.state(model.actor).flags.containsKey("rrf_native_setup_active")); assertTrue(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver")); assertTrue(model.state(model.actor).flags.containsKey("rrf_result_dialog")); }
    private static void assertFinished(Model model) { assertTrue(model.state(model.result).variables.containsKey("rrf_native_configuration_complete")); assertFalse(model.state(model.actor).flags.containsKey("rrf_native_setup_active")); assertFalse(model.state(model.actor).modifiers.containsKey("rrf_native_setup_cost_waiver")); }
    private static Node tenet(int id) { return new Node(Kind.TENET, "third_party_tenet_" + id); }
    private static Node doctrine(String id) { return new Node(Kind.DOCTRINE, id); }
    private static List<Node> tenets(int first, int end) { List<Node> result = new ArrayList<>(); for (int id = first; id < end; id++) result.add(tenet(id)); return List.copyOf(result); }
    private static Map<String, List<Node>> contract(Model model) { Map<String, List<Node>> result = new LinkedHashMap<>(); for (String name : CONTRACT_LISTS) result.put(name, List.copyOf(model.list(model.result, name))); result.put("rrf_origin_core_tenets", List.copyOf(model.list(model.result, "rrf_origin_core_tenets"))); return Map.copyOf(result); }
    private record SourceImage(Map<String, Node> links, Map<String, Stored> variables, Map<String, List<Node>> lists, Set<Node> cores, Set<Node> doctrines, BigDecimal piety) { }
    private static SourceImage image(State state) { Map<String, List<Node>> lists = new LinkedHashMap<>(); state.lists.forEach((name, values) -> lists.put(name, List.copyOf(values))); return new SourceImage(Map.copyOf(state.links), Map.copyOf(state.variables), Map.copyOf(lists), Set.copyOf(state.cores), Set.copyOf(state.doctrines), state.piety); }
}
