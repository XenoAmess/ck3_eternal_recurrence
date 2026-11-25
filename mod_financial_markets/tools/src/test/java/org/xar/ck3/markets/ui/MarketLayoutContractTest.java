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

/** Source structure only; engine-assigned rectangles, rendered pixels and mouse hits require real game acceptance. */
final class MarketLayoutContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));

    @Test void boundedRootFlowAndExpandingContentAreDeclaredInSource() throws IOException {
        Block window = named(gui(), "xfm_market_window");
        finiteSize(window);
        Block content = child(window, "vbox", "xfm_market_content");
        assertEquals(List.of("100%", "100%"), vector(content.block("size")));
        expanding(content, "horizontal", "vertical");
        Block header = content.block("header_pattern");
        finiteSize(header);
        expanding(header, "horizontal");
        ordered(content, "xfm_market_tabs", "xfm_market_body");

        Block tabs = child(content, "hbox", "xfm_market_tabs");
        fixedRow(tabs);
        assertEquals(6, tabs.named("button_tab").size());
        for (String suffix : List.of("market", "positions", "orders", "debts", "issuer", "news")) {
            Block tab = child(tabs, "button_tab", "xfm_tab_" + suffix);
            assertEquals(List.of("212", "42"), vector(tab.block("size")), "Explicit source tab width: " + suffix);
        }

        Block body = child(content, "hbox", "xfm_market_body");
        finiteSize(body);
        expanding(body, "horizontal", "vertical");
        assertTrue(body.block("position").entries().isEmpty(), "Body participates in its parent VBox flow");
        Block browser = child(body, "vbox", "xfm_market_browser");
        expanding(browser, "vertical");
        assertTrue(Integer.parseInt(vector(browser.block("size")).getFirst()) > 0);
        Block pages = child(browser, "widget", "xfm_market_pages");
        finiteSize(pages);
        expanding(pages, "horizontal", "vertical");
        Block trading = child(body, "vbox", "xfm_market_trading");
        expanding(trading, "vertical");
        assertTrue(Integer.parseInt(vector(trading.block("size")).getFirst()) > 0);
        Block detail = child(trading, "scrollbox", "xfm_market_detail_scroll");
        finiteSize(detail);
        expanding(detail, "horizontal", "vertical");
        // Expanding is a source declaration, not proof of any runtime viewport height.
    }

    @Test void toolbarOrderAndTransparentCoinCellsAreDeclaredInSource() throws IOException {
        Block gui = gui();
        Block browser = named(gui, "xfm_market_browser");
        ordered(browser, "xfm_market_wallet", "xfm_market_indexes", "xfm_market_pages");
        fixedRow(child(browser, "vbox", "xfm_market_wallet"));
        fixedRow(child(browser, "hbox", "xfm_market_indexes"));
        Block pages = child(browser, "widget", "xfm_market_pages");
        Block market = child(pages, "vbox", "xfm_market_page_market");
        expanding(market, "horizontal", "vertical");
        assertEquals(List.of("100%", "100%"), vector(market.block("size")));
        ordered(market, "xfm_market_filters", "xfm_market_search", "xfm_market_coin_columns",
                "xfm_market_coin_scroll", "xfm_market_pagination");
        for (String name : List.of("xfm_market_filters", "xfm_market_search", "xfm_market_pagination")) {
            Block row = child(market, "hbox", name);
            fixedRow(row);
            assertTrue(row.block("position").entries().isEmpty(), name + " participates in VBox flow");
        }
        Block scroll = child(market, "scrollbox", "xfm_market_coin_scroll");
        finiteSize(scroll);
        expanding(scroll, "horizontal", "vertical");
        for (String suffix : List.of("positions", "orders", "debts", "issuer", "news")) {
            String kind = List.of("positions", "orders").contains(suffix) ? "vbox" : "scrollbox";
            Block page = child(pages, kind, "xfm_market_page_" + suffix);
            assertEquals(List.of("100%", "100%"), vector(page.block("size")));
            expanding(page, "horizontal", "vertical");
            assertNotEquals("", page.atom("visible", ""));
        }

        Block rows = Clausewitz.parse(Files.readString(SOURCE.resolve("gui/xfm_market_rows.gui")));
        Block coin = named(rows, "xfm_market_coin_row");
        finiteSize(coin);
        expanding(coin, "horizontal");
        assertTrue(coin.atom("enabled", "").contains("xfm_market_select_coin_gui"));
        assertTrue(coin.atom("onclick", "").contains("xfm_market_select_coin_gui"));
        assertTrue(coin.atom("onclick", "").contains("'xfm_ui_row_id', MakeScopeValue( Scope.Var( 'xfm_coin_id' ).GetValue )"));
        Block builtInLabel = coin.block("buttonText").block("text_single");
        assertEquals("no", builtInLabel.atom("visible", ""));
        assertEquals("yes", builtInLabel.atom("alwaystransparent", ""));
        assertEquals(5, coin.named("text_single").size());
        Block heading = child(market, "widget", "xfm_market_coin_columns");
        fixedRow(heading);
        assertEquals("yes", heading.atom("alwaystransparent", ""));
        for (String suffix : List.of("identity", "last", "bid", "ask", "volume")) {
            Block cell = child(coin, "text_single", "xfm_market_coin_cell_" + suffix);
            Block label = child(heading, "text_single", "xfm_market_column_" + suffix);
            finiteSize(cell);
            finiteSize(label);
            assertEquals(vector(cell.block("size")).getFirst(), vector(label.block("size")).getFirst());
            for (Block text : List.of(cell, label)) {
                assertEquals("yes", text.atom("alwaystransparent", ""));
                assertEquals("no", text.atom("autoresize", ""));
                assertTrue(text.named("onclick").isEmpty(), "Only the original parent button selects a coin");
            }
        }
        // Transparent declarations still require actual mouse hits over the rendered cells.
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
    private static void expanding(Block block, String... axes) {
        for (String axis : axes) assertEquals("expanding", block.atom("layoutpolicy_" + axis, ""));
    }
    private static void fixedRow(Block block) {
        finiteSize(block);
        assertEquals("fixed", block.atom("layoutpolicy_vertical", ""));
    }
    private static void finiteSize(Block block) {
        List<String> size = vector(block.block("size"));
        assertEquals(2, size.size(), "A finite source size needs two values");
        for (String value : size) assertTrue(value.matches("[1-9][0-9]*"), "Expected a positive finite source size: " + value);
    }
    private static List<String> vector(Block block) {
        return block.entries().stream().map(entry -> ((Atom) entry.value()).token()).toList();
    }
    private static Block child(Block parent, String type, String name) {
        List<Block> found = parent.named(type).stream().filter(entry -> entry.value() instanceof Block)
                .map(entry -> (Block) entry.value()).filter(block -> block.atom("name", "").equals('"' + name + '"')).toList();
        assertEquals(1, found.size(), "Expected one direct " + type + " child: " + name);
        return found.getFirst();
    }
    private static void ordered(Block parent, String... names) {
        List<String> directNames = parent.entries().stream().filter(entry -> entry.value() instanceof Block)
                .map(entry -> ((Block) entry.value()).atom("name", "")).toList();
        int previous = -1;
        for (String name : names) {
            int index = directNames.indexOf('"' + name + '"');
            assertTrue(index > previous, "Expected direct source flow order: " + name);
            previous = index;
        }
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
