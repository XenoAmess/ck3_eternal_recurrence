package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;

final class RiteDeclineSourceKnowledgeTest {
    @Test void fixedSourceKnowledgeRetainsAiConditionAndCannotGrantLiveAuthority() {
        var knowledge = RiteDeclineSourceKnowledge.current();
        assertEquals(knowledge, RiteDeclineSourceKnowledge.decode(RetainedJson.encode(knowledge.json())));
        assertTrue(knowledge.helper().body().contains("limit = { is_ai = yes }"));
        assertTrue(knowledge.helper().body().contains("opinion = -10"));
        assertFalse(knowledge.helper().body().contains("set_character_rite"));
        assertFalse(knowledge.runtimeHelperSourceVerified()); assertFalse(knowledge.materialEffectsVerified());
        assertFalse(knowledge.semanticOptimal()); assertFalse(knowledge.nativeAiEquivalent());
    }

    @Test void runtimeInputRejectsAuthorityUpgradeMissingIdentityAndEqualWrongTypes() {
        ObjectValue good = RiteDeclineSourceKnowledge.current().json();
        for (String field : java.util.List.of("runtime_helper_source_verified", "material_effects_verified", "semantic_optimal", "native_ai_equivalent"))
            assertThrows(IllegalArgumentException.class, () -> RiteDeclineSourceKnowledge.decode(RetainedJson.encode(good.with(field, b(true)))));
        assertThrows(IllegalArgumentException.class, () -> RiteDeclineSourceKnowledge.decode(RetainedJson.encode(good.with("deterministic_key_hash", b(true)))));
        var missing = new LinkedHashMap<>(good.fields()); missing.remove("on_decline_sha256");
        assertThrows(IllegalArgumentException.class, () -> RiteDeclineSourceKnowledge.decode(RetainedJson.encode(new ObjectValue(missing))));
        ObjectValue helper = o(good, "helper_source");
        assertThrows(IllegalArgumentException.class, () -> RiteDeclineSourceKnowledge.decode(RetainedJson.encode(good.with("helper_source", helper.with("first_line", b(true))))));
        assertThrows(IllegalArgumentException.class, () -> RiteDeclineSourceKnowledge.decode(RetainedJson.encode(good.with("helper_source", helper.with("body", s("changed source"))))));
        assertThrows(IllegalArgumentException.class, () -> RiteDeclineSourceKnowledge.decode(RetainedJson.encode(good.with("recipient_opinion_clause", o(good, "recipient_opinion_clause").with("delta", b(false))))));
    }

    @Test void otherBuildDefinitionSourceOrDeclineBodyNeverReceivesThisKnowledge() {
        var known = RiteDeclineSourceKnowledge.current().json(); String original = "original analysis";
        var build = new InteractionRegistry.BuildIdentity("1.20.0.4", text(known, "exe_sha256"));
        var definition = new InteractionRegistry.Definition(text(known, "canonical_key"), number(known, "deterministic_key_hash").longValueExact());
        String gui = "a3c946a98346de2f57c5c3408a24bf298329df24a6ab25ec88d893befa1fe6e0";
        var binding = new InteractionRegistry.Binding(build, definition, text(known, "interaction_source_sha256"), gui);
        String decline = "\r\n\ton_decline = {\r\n\t\tpam_sway_to_rite_on_decline_effect = yes\r\n\t}";
        assertTrue(RiteDeclineSourceKnowledge.appendAnalysis(original, binding, decline).contains("runtime_helper_source_verified"));
        assertEquals(original, RiteDeclineSourceKnowledge.appendAnalysis(original, binding, null));
        assertEquals(original, RiteDeclineSourceKnowledge.appendAnalysis(original, binding, decline + "\n"));
        assertEquals(original, RiteDeclineSourceKnowledge.appendAnalysis(original,
                new InteractionRegistry.Binding(new InteractionRegistry.BuildIdentity("1.20.1", build.exeSha256()), definition, binding.sourceSha256(), gui), decline));
        assertEquals(original, RiteDeclineSourceKnowledge.appendAnalysis(original,
                new InteractionRegistry.Binding(build, new InteractionRegistry.Definition("another_interaction", definition.deterministicKeyHash()), binding.sourceSha256(), gui), decline));
        assertEquals(original, RiteDeclineSourceKnowledge.appendAnalysis(original,
                new InteractionRegistry.Binding(build, new InteractionRegistry.Definition(definition.canonicalKey(), 1), binding.sourceSha256(), gui), decline));
        assertEquals(original, RiteDeclineSourceKnowledge.appendAnalysis(original,
                new InteractionRegistry.Binding(build, definition, "0".repeat(64), gui), decline));
    }
}
