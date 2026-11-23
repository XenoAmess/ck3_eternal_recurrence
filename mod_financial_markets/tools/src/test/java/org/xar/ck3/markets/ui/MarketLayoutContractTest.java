package org.xar.ck3.markets.ui;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;

/** Finite source geometry, not an engine hit-test or rendered-screen acceptance. */
final class MarketLayoutContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private record Rect(int x, int y, int width, int height) {
        boolean contains(Rect child) {
            return child.x >= 0 && child.y >= 0 && child.width > 0 && child.height > 0
                && child.x + child.width <= width && child.y + child.height <= height;
        }
        boolean overlaps(Rect other) {
            return x < other.x + other.width && other.x < x + width
                && y < other.y + other.height && other.y < y + height;
        }
    }

    @Test void browserAndTallTradingViewportStayInsideTheirHitRectangles() throws IOException {
        Block gui = gui();
        inside(gui, "xfm_market_window", "xfm_market_tabs", "xfm_market_body");
        inside(gui, "xfm_market_body", "xfm_market_browser", "xfm_market_trading");
        assertFalse(rect(named(gui, "xfm_market_browser")).overlaps(rect(named(gui, "xfm_market_trading"))));
        inside(gui, "xfm_market_browser", "xfm_market_wallet", "xfm_market_indexes", "xfm_market_pages");
        inside(gui, "xfm_market_trading", "xfm_market_detail_scroll");
        Rect detail = rect(named(gui, "xfm_market_detail_scroll"));
        assertTrue(detail.height >= 650, "Details must offer a tall viewport instead of the default 100px");
        assertTrue(detail.width >= 440, "The 400px order form and scroll margins must fit");
    }

    @Test void filtersRowsAndPaginationAreSeparateContainedClickRegions() throws IOException {
        Block gui = gui();
        inside(gui, "xfm_market_pages", "xfm_market_page_market");
        String[] areas = {"xfm_market_filters", "xfm_market_search", "xfm_market_coin_scroll", "xfm_market_pagination"};
        inside(gui, "xfm_market_page_market", areas);
        for (int a = 0; a < areas.length; a++) for (int b = a + 1; b < areas.length; b++)
            assertFalse(rect(named(gui, areas[a])).overlaps(rect(named(gui, areas[b]))), areas[a] + " / " + areas[b]);
        assertTrue(rect(named(gui, "xfm_market_coin_scroll")).height >= 350);
        for (String suffix : List.of("positions", "orders", "debts", "issuer", "news")) {
            inside(gui, "xfm_market_pages", "xfm_market_page_" + suffix);
            assertNotEquals("", named(gui, "xfm_market_page_" + suffix).atom("visible", ""));
        }
    }

    @Test void immediateTradingControlsPrecedeTheBookAndFullRulesRemainAvailable() throws IOException {
        String spot = Files.readString(SOURCE.resolve("gui/xfm_market_spot_ticket.gui"));
        assertTrue(spot.indexOf("name = \"xfm_market_buy\"") < spot.indexOf("text = \"xfm_market_book_title\""));
        assertTrue(spot.contains("tooltip = \"xfm_market_spot_terms\""));
        String futures = Files.readString(SOURCE.resolve("gui/xfm_market_futures.gui"));
        assertTrue(futures.indexOf("name = \"xfm_market_futures_long\"") < futures.indexOf("xfm_market_futures_book_panel = {}"));
    }

    private static Block gui() throws IOException {
        return Clausewitz.parse(Files.readString(SOURCE.resolve("gui/xfm_market_window.gui")));
    }
    private static void inside(Block gui, String parent, String... children) {
        Rect bounds = rect(named(gui, parent));
        for (String child : children) assertTrue(bounds.contains(rect(named(gui, child))), parent + " clips " + child);
    }
    private static Rect rect(Block block) {
        List<Integer> size = vector(block.block("size"));
        List<Integer> position = vector(block.block("position"));
        assertEquals(2, size.size(), "Each frame needs a finite explicit size");
        return new Rect(position.isEmpty() ? 0 : position.get(0), position.isEmpty() ? 0 : position.get(1), size.get(0), size.get(1));
    }
    private static List<Integer> vector(Block block) {
        return block.entries().stream().map(entry -> Integer.valueOf(((Atom) entry.value()).token())).toList();
    }
    private static Block named(Block block, String name) {
        List<Block> found = new ArrayList<>();
        collect(block, '"' + name + '"', found);
        assertEquals(1, found.size(), "Expected exactly one frame: " + name);
        return found.getFirst();
    }
    private static void collect(Block block, String name, List<Block> found) {
        if (block.atom("name", "").equals(name)) found.add(block);
        for (var entry : block.entries()) if (entry.value() instanceof Block child) collect(child, name, found);
    }
}
