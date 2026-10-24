package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Definition;
import org.xar.ck3.rrf.Contracts.Kind;
import org.xar.ck3.rrf.Contracts.SourceFile;

final class NativeSelectionProjectionTest {
    @Test void actualNativeNorAllowsOneAndRejectsTwoAfterExcludingCandidate() throws IOException {
        Clausewitz.Block excerpt = Clausewitz.parse(excerpt());
        for (String helper : List.of("unique_syncretism_trigger", "unique_christology_trigger")) {
            Clausewitz.Block definition = excerpt.block(helper);
            Clausewitz.Block description = definition.block(helper.equals("unique_syncretism_trigger") ? "custom_description" : "custom_tooltip");
            Clausewitz.Block nor = description.block("NOR");
            List<String> choices = nor.entries().stream().map(Clausewitz.Entry::key).toList();
            for (Clausewitz.Entry e : nor.entries()) assertEquals("selected_doctrines", ((Clausewitz.Block) e.value()).atom("is_in_list", ""));
            String first = choices.getFirst(); String second = choices.get(1);
            assertTrue(nativeNorWithoutSelf(choices, Set.of(first), first));
            assertFalse(nativeNorWithoutSelf(choices, Set.of(first, second), first));
            assertFalse(nativeNorWithoutSelf(choices, Set.of(first, second), second));
            List<Definition> definitions = List.of(new Definition(Kind.TENET, first.substring(6), "", "native/excerpt.txt", "", helper + " = yes", "", true, List.of()));
            Catalog catalog = new Catalog(1, "source-excerpt-fixture", "2026-10-24T00:00:00Z", List.of(new SourceFile("native/excerpt.txt", ReleaseBuilder.sha256(excerpt().getBytes(StandardCharsets.UTF_8)))), List.of(), definitions);
            String emitted = new CatalogGenerator().render(catalog).get("common/scripted_effects/rrf_catalog_validate_00.txt");
            int remove = emitted.indexOf("remove_from_list = selected_doctrines");
            int evaluate = emitted.indexOf(helper + " = yes");
            int restore = emitted.indexOf("add_to_list = selected_doctrines");
            assertTrue(remove >= 0 && remove < evaluate && evaluate < restore);
            assertTrue(emitted.contains("remove_from_list = selected_tenets"));
            assertTrue(emitted.contains("add_to_list = selected_tenets"));
        }
    }
    private static boolean nativeNorWithoutSelf(List<String> norMembers, Set<String> finalSelection, String candidate) {
        Set<String> peers = new LinkedHashSet<>(finalSelection); peers.remove(candidate);
        return norMembers.stream().noneMatch(peers::contains);
    }
    private static String excerpt() throws IOException {
        try (InputStream input = NativeSelectionProjectionTest.class.getResourceAsStream("/native-unique-selection.txt")) {
            if (input == null) throw new IOException("missing native selection fixture");
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
