package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Source regression for the reported 100x100 viewport; does not simulate CK3 rendering. */
final class FusionPageLayoutTest {
    private static final List<String> PAGES = List.of("tenets", "doctrines", "identity");

    @Test void allThreePagesFillTheirPlainWidgetParent() throws IOException {
        validateAllocation(pages());
    }

    @Test void eachPageRejectsMissingWidthAndHeightAllocation() throws IOException {
        Clausewitz.Block actual = pages();
        validateAllocation(actual);
        for (String page : PAGES) {
            for (String replacement : List.of("", "size = { 100 100% }", "size = { 100% 100 }")) {
                Clausewitz.Block mutated = replaceSize(actual, page, replacement);
                AssertionError failure = assertThrows(AssertionError.class, () -> validateAllocation(mutated));
                assertTrue(failure.getMessage().contains(page), failure.getMessage());
            }
        }
    }

    @Test void scrollingBodiesKeepNaturalHeightInsideOneBoundedViewportPerPage() throws IOException {
        Clausewitz.Block actual = pages();
        for (String page : PAGES) {
            Clausewitz.Entry surface = surface(actual, page);
            Clausewitz.Block body = (Clausewitz.Block) surface.value();
            Clausewitz.Block viewport;
            if (surface.key().equals("scrollbox")) {
                viewport = body;
            } else {
                assertEquals("vbox", surface.key(), page);
                assertEquals(1, body.named("scrollbox").size(), page);
                viewport = body.block("scrollbox");
                assertEquals("expanding", viewport.atom("layoutpolicy_vertical", ""), page);
            }
            Clausewitz.Block wrapper = contentOverride(viewport);
            assertEquals(1, wrapper.entries().size(), page);
            Clausewitz.Entry content = wrapper.entries().getFirst();
            assertTrue(List.of("vbox", "fixedgridbox").contains(content.key()), page);
            Clausewitz.Block natural = assertInstanceOf(Clausewitz.Block.class, content.value(), page);
            for (Clausewitz.Block node : List.of(body, viewport, wrapper, natural)) {
                assertFalse(node.atom("restrictparent_min", "no").equals("yes"), page);
                assertFalse(node.atom("set_parent_size_to_minimum", "no").equals("yes"), page);
            }
            List<Clausewitz.Entry> size = natural.block("size").entries();
            if (!size.isEmpty()) {
                assertEquals(2, size.size(), page);
                assertFalse(assertInstanceOf(Clausewitz.Atom.class, size.get(1).value()).token().endsWith("%"), page);
            }
        }
    }

    private static Clausewitz.Block pages() throws IOException {
        Path source = Path.of(System.getProperty("rrf.source"));
        Clausewitz.Block window = Clausewitz.parse(Files.readString(source.resolve("gui/rrf_fusion_window.gui")));
        List<Clausewitz.Entry> found = new ArrayList<>();
        findNamed(window, "rrf_editor_pages", found);
        assertEquals(1, found.size());
        assertEquals("widget", found.getFirst().key());
        return (Clausewitz.Block) found.getFirst().value();
    }

    private static void findNamed(Clausewitz.Block parent, String name, List<Clausewitz.Entry> found) {
        for (Clausewitz.Entry entry : parent.entries()) {
            if (entry.value() instanceof Clausewitz.Block child) {
                if (child.atom("name", "").equals("\"" + name + "\"")) found.add(entry);
                findNamed(child, name, found);
            }
        }
    }

    private static Clausewitz.Entry surface(Clausewitz.Block parent, String page) {
        String visible = "\"[GetVariableSystem.HasValue( 'rrf_editor_page', '" + page + "' )]\"";
        List<Clausewitz.Entry> found = parent.entries().stream()
                .filter(e -> e.value() instanceof Clausewitz.Block child && child.atom("visible", "").equals(visible)).toList();
        assertEquals(1, found.size(), page);
        return found.getFirst();
    }

    private static void validateAllocation(Clausewitz.Block parent) {
        for (String page : PAGES) {
            Clausewitz.Block body = (Clausewitz.Block) surface(parent, page).value();
            assertEquals(Clausewitz.parse("size = { 100% 100% }").block("size"), body.block("size"), page);
        }
    }

    private static Clausewitz.Block replaceSize(Clausewitz.Block parent, String page, String replacement) {
        Clausewitz.Entry original = surface(parent, page);
        Clausewitz.Block body = (Clausewitz.Block) original.value();
        List<Clausewitz.Entry> changed = new ArrayList<>(body.entries().stream().filter(e -> !e.key().equals("size")).toList());
        changed.addAll(Clausewitz.parse(replacement).entries());
        Clausewitz.Entry modified = new Clausewitz.Entry(original.key(), original.operator(), new Clausewitz.Block(changed));
        return new Clausewitz.Block(parent.entries().stream().map(e -> e == original ? modified : e).toList());
    }

    private static Clausewitz.Block contentOverride(Clausewitz.Block viewport) {
        List<Clausewitz.Block> found = new ArrayList<>();
        List<Clausewitz.Entry> entries = viewport.entries();
        // The production parser preserves GUI blockoverride syntax as three list entries.
        for (int i = 0; i + 2 < entries.size(); i++) {
            Clausewitz.Entry first = entries.get(i), second = entries.get(i + 1), third = entries.get(i + 2);
            if (first.operator().isEmpty() && first.value().equals(new Clausewitz.Atom("blockoverride"))
                    && second.operator().isEmpty() && second.value().equals(new Clausewitz.Atom("\"scrollbox_content\""))
                    && third.operator().isEmpty() && third.value() instanceof Clausewitz.Block block) found.add(block);
        }
        assertEquals(1, found.size(), "one real scrollbox_content override required");
        return found.getFirst();
    }
}
