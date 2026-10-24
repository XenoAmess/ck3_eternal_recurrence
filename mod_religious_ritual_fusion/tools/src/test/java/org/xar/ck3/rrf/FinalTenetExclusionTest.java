package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Definition;

final class FinalTenetExclusionTest {
    @Test void fourActualSourceClausesRejectEveryPairAndPermitSingleReplacement() throws IOException {
        Catalog catalog = Json.read(Files.readAllBytes(Path.of(System.getProperty("rrf.source")).resolve("catalog/generated-catalog.json")), Catalog.class);
        List<String> ids = List.of("tenet_hesychasm", "tenet_anachoresis", "tenet_mortification_of_the_flesh", "tenet_asceticism");
        for (String candidate : ids) {
            Definition definition = catalog.definitions().stream().filter(d -> d.id().equals(candidate)).findFirst().orElseThrow();
            Clausewitz.Block original = Clausewitz.parse(definition.canPick()).block("custom_description").block("NOR");
            Clausewitz.Block projected = Clausewitz.parse(RuleProjection.project(definition.canPick())).block("custom_description").block("NOR");
            assertEquals(3, original.entries().size());
            assertTrue(original.entries().stream().allMatch(e -> e.key().equals("has_tenet")));
            List<String> excluded = projected.entries().stream().map(Clausewitz.Entry::key).map(k -> k.substring("tenet:".length())).toList();
            assertEquals(new LinkedHashSet<>(ids.stream().filter(id -> !id.equals(candidate)).toList()), new LinkedHashSet<>(excluded));
            for (Clausewitz.Entry e : projected.entries()) assertEquals("selected_tenets", ((Clausewitz.Block) e.value()).atom("is_in_list", ""));
            assertTrue(permits(excluded, Set.of(candidate), candidate));
            for (String peer : ids) if (!peer.equals(candidate)) assertFalse(permits(excluded, Set.of(candidate, peer), candidate));
        }
    }
    @Test void otherNativeFaithTenetChecksRetainGrandfatherSemantics() {
        String original = "OR = { has_tenet = tenet_rite religion = religion:christianity_religion }";
        assertEquals(Clausewitz.parse(original), Clausewitz.parse(RuleProjection.project(original)));
    }
    private static boolean permits(List<String> exclusions, Set<String> selected, String candidate) { Set<String> peers = new LinkedHashSet<>(selected); peers.remove(candidate); return exclusions.stream().noneMatch(peers::contains); }
}
