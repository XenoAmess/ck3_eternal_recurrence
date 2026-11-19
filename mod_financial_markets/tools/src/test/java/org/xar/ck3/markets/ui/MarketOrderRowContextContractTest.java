package org.xar.ck3.markets.ui;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

/** R18 Scope.Self parsing regression contracts. Direct Scope is the existing model value; no live-success claim. */
final class MarketOrderRowContextContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static String quoted(String text) { return Character.toString(34) + text + Character.toString(34); }
    private static String source(String relative) throws IOException { return Files.readString(SOURCE.resolve(relative)); }
    private static String body(String text, String header) {
        int start = text.indexOf(header);
        assertTrue(start >= 0, "expected concrete GUI block: " + header);
        int opening = text.indexOf('{', start), depth = 1;
        assertTrue(opening >= 0, "expected opening brace");
        boolean quoted = false, escaped = false, comment = false;
        for (int i = opening + 1; i < text.length(); i++) {
            char c = text.charAt(i);
            if (comment) { if (c == 10) comment = false; continue; }
            if (escaped) { escaped = false; continue; }
            if (quoted && c == 92) { escaped = true; continue; }
            if (c == 34) { quoted = !quoted; continue; }
            if (quoted) continue;
            if (c == '#') { comment = true; continue; }
            if (c == '{') depth++;
            else if (c == '}' && --depth == 0) return text.substring(opening + 1, i);
        }
        throw new IllegalArgumentException("unterminated GUI block");
    }
    private static String compact(String text) {
        StringBuilder result = new StringBuilder(); boolean quoted = false, escaped = false;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (quoted || !Character.isWhitespace(c)) result.append(c);
            if (escaped) { escaped = false; continue; }
            if (quoted && c == 92) { escaped = true; continue; }
            if (c == 34) quoted = !quoted;
        }
        return result.toString();
    }
    private static String list(String window, String name) {
        return body(window, "scrollbox = { name = " + quoted(name));
    }
    private static String row(String list) {
        String item = body(list, "item = {");
        assertFalse(item.contains("xfm_market_order_row ="), "the concrete item must own its context");
        return body(item, "vbox = {");
    }
    @Test void bothConcreteOrderItemsPreserveTheSharedTemplateWithNativeModelContext() throws IOException {
        String window = source("gui/xfm_market_window.gui");
        String original = body(source("gui/xfm_market_rows.gui"), "type xfm_market_order_row = vbox {");
        for (String name : List.of("xfm_market_orders_scroll", "xfm_market_history_scroll")) {
            String row = row(list(window, name));
            assertFalse(row.contains("datacontext ="), "the model item already supplies its Scope value");
            assertEquals(compact(original), compact(row), name);
        }
    }
    @Test void bothListsKeepTheSameAccountDataAndSixteenRowPagination() throws IOException {
        String window = source("gui/xfm_market_window.gui");
        for (String suffix : List.of("orders", "history")) {
            String selected = list(window, "xfm_market_" + suffix + "_scroll");
            assertTrue(selected.contains("DataModelSubSpan( GetPlayer.MakeScope.Var( 'xfm_active_account' ).GetList( 'xfm_" + (suffix.equals("orders") ? "orders" : "order_history") + "' )"));
            assertTrue(selected.contains("'(int32)16'"));
            assertTrue(selected.contains("xfm_ui_" + suffix + "_offset"));
        }
    }
    @Test void cancelCallbacksKeepPlayerRootAndTheExactModelItemNamedScope() throws IOException {
        String window = source("gui/xfm_market_window.gui");
        for (String name : List.of("xfm_market_orders_scroll", "xfm_market_history_scroll")) {
            String row = row(list(window, name));
            for (String button : List.of("xfm_market_cancel", "xfm_market_cancel_futures_order")) {
                String selected = body(row, "button_standard = { name = " + quoted(button));
                String gui = button.equals("xfm_market_cancel") ? "xfm_market_cancel_gui" : "xfm_market_cancel_futures_order_gui";
                for (String operation : List.of("IsValid", "IsValidTooltip", "Execute"))
                    assertTrue(selected.contains("GetScriptedGui( '" + gui + "' )." + operation + "( GuiScope.SetRoot( GetPlayer.MakeScope ).AddScope( 'xfm_ui_item', Scope ).End )"));
            }
        }
    }
    @Test void everyAffectedModelRowRejectsUnsupportedSelfAndPassesTheDirectScopeValue() throws IOException {
        for (String file : List.of("xfm_market_window", "xfm_market_rows", "xfm_market_debts",
                "xfm_market_news", "xfm_market_otc", "xfm_market_futures_book")) {
            String gui = source("gui/" + file + ".gui");
            assertFalse(gui.contains("Scope.Self"), file);
            assertFalse(gui.contains("datacontext = " + quoted("[Scope]")), "no new Scope self-binding is introduced");
            int expected = switch (file) {
                case "xfm_market_window" -> 16;
                case "xfm_market_rows" -> 20;
                case "xfm_market_futures_book" -> 1;
                default -> 2;
            };
            String argument = ".AddScope( 'xfm_ui_item', Scope )";
            int found = 0, offset = 0;
            while ((offset = gui.indexOf(argument, offset)) >= 0) { found++; offset += argument.length(); }
            assertEquals(expected, found, file);
        }
    }
    @Test void sourceTypeAndLegalAccountGuardsRemainWithTheOriginalCancellationHandlers() throws IOException {
        String predicates = source("common/scripted_guis/xfm_market_predicates.txt");
        for (String type : List.of("spot", "futures")) {
            String guard = body(predicates, "xfm_market_is_" + type + "_order_gui = {");
            assertTrue(guard.contains("saved_scopes = { xfm_ui_item }"));
            assertTrue(guard.contains("story_type = xfm_" + type + "_order"));
        }
        String cancel = body(source("common/scripted_guis/xfm_market_ticket.txt"), "xfm_market_cancel_gui = {");
        assertTrue(cancel.contains("var:xfm_account = root.var:xfm_active_account")); assertTrue(cancel.contains("var:xfm_status = 1"));
        assertTrue(cancel.contains("set_variable = { name = xfm_selected_order value = scope:xfm_ui_item }"));
        assertTrue(cancel.contains("xfm_spot_cancel_effect = yes"));
    }
}
