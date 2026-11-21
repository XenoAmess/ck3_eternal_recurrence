package org.xar.ck3.markets.ui;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Source wiring only. R20 numeric transport PASS is separate from this backend's game acceptance. */
final class MarketOrderRowContextContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static String quoted(String text) { return Character.toString(34) + text + Character.toString(34); }
    private static String source(String relative) throws IOException { return Files.readString(SOURCE.resolve(relative)); }
    private static String body(String text, String header) {
        int start = text.indexOf(header);
        assertTrue(start >= 0, "expected GUI/script block: " + header);
        int opening = text.indexOf('{', start), depth = 1;
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
        throw new IllegalArgumentException("unterminated block");
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
    private static int occurrences(String text, String needle) {
        return (text.length() - text.replace(needle, "").length()) / needle.length();
    }
    @Test void onlyTheThirtySevenIncludedCallbacksUseNumericValuesWithoutBareOrSelfScopes() throws IOException {
        int total = 0;
        for (String file : List.of("xfm_market_window", "xfm_market_rows", "xfm_market_futures_book")) {
            String gui = source("gui/" + file + ".gui");
            assertFalse(gui.contains("Scope.Self"));
            assertFalse(gui.contains(".AddScope( 'xfm_ui_item', Scope )"));
            assertFalse(gui.contains("datacontext = " + quoted("[Scope]")));
            int count = occurrences(gui, ".AddScope( 'xfm_ui_row_id', MakeScopeValue(");
            assertEquals(file.equals("xfm_market_window") ? 16 : file.equals("xfm_market_rows") ? 20 : 1, count);
            total += count;
        }
        assertEquals(37, total, "debt/news/OTC are a separate unfinished closure");
    }
    @Test void activeAndHistoryInlineRowsKeepIdenticalControlsButHaveDifferentSourceDomains() throws IOException {
        String window = source("gui/xfm_market_window.gui");
        String template = body(source("gui/xfm_market_rows.gui"), "type xfm_market_order_row = vbox {");
        String receiptText = body(template, "vbox = { spacing = 2");
        assertEquals(2, occurrences(receiptText, "text_multi = {"));
        assertEquals(1, occurrences(receiptText, "text = " + quoted("xfm_market_futures_order_text")));
        assertEquals(1, occurrences(receiptText, "text = " + quoted("xfm_market_futures_cancel_text")));
        for (String forbidden : List.of(".AddScope(", ".Execute(", ".IsValid(", "Scope.Var(", "GetPlayer"))
            assertFalse(receiptText.contains(forbidden), "read-only text container must add no backend scopes/actions");
        for (String suffix : List.of("orders", "history")) {
            String list = body(window, "scrollbox = { name = " + quoted("xfm_market_" + suffix + "_scroll"));
            String row = body(body(list, "item = {"), "vbox = {");
            assertFalse(row.contains("datacontext"));
            assertEquals(1, occurrences(row, "text = " + quoted("xfm_market_futures_cancel_text")), suffix);
            assertEquals(compact(receiptText), compact(body(row, "vbox = { spacing = 2")), suffix);
            String table = ".AddScope( 'xfm_ui_row_table', MakeScopeValue( '(CFixedPoint)";
            assertEquals(compact(template), compact(row.replace(table + "2' ) )", table + "1' ) )")));
            assertEquals(8, occurrences(row, table + (suffix.equals("history") ? "2" : "1") + "' ) )"));
            assertTrue(list.contains("GetList( 'xfm_ui_" + suffix + "_page' )"));
        }
    }
    @Test void portfolioCachesAreExplicitSixteenRowSnapshotsAndAllSixPageControlsRebuildThem() throws IOException {
        String effect = source("common/scripted_effects/xfm_market_ui_portfolio_pages.txt");
        for (String page : List.of("positions", "orders", "history")) {
            assertTrue(effect.contains("clear_variable_list = xfm_ui_" + page + "_page"));
            assertTrue(effect.contains("name = xfm_ui_" + page + "_page_offset value = var:xfm_ui_" + page + "_offset"));
            assertTrue(effect.contains("name = xfm_ui_" + page + "_page target = scope:xfm_ui_page_item"));
        }
        assertFalse(effect.contains("every_living_character"));
        assertFalse(effect.contains("every_in_global_list"));
        assertTrue(effect.contains("var:xfm_active_account = {"));
        String pages = source("common/scripted_guis/xfm_market_portfolio_pages.txt");
        for (String page : List.of("positions", "orders", "history"))
            for (String direction : List.of("next", "previous"))
                assertTrue(body(pages, "xfm_market_" + page + "_" + direction + "_gui = {")
                        .contains("xfm_market_ui_portfolio_pages_effect = yes"));
        assertTrue(body(source("common/scripted_effects/xfm_market_ui_pages.txt"), "xfm_market_ui_refresh_effect = {")
                .contains("xfm_market_ui_portfolio_pages_effect = yes"));
    }
    @Test void mixedRowsCarryKindAndOrderTableWhileSpotPositionsUseTheRealAccountCoinIdentity() throws IOException {
        String rows = source("gui/xfm_market_rows.gui");
        assertTrue(body(rows, "type xfm_market_position_row = vbox {")
                .contains("Scope.Var( 'xfm_coin' ).Var( 'xfm_coin_id' ).GetValue"));
        assertTrue(body(rows, "type xfm_market_position_row = vbox {")
                .contains("Scope.Var( 'xfm_position_id' ).GetValue"));
        assertTrue(rows.contains(".AddScope( 'xfm_ui_row_kind', MakeScopeValue( Scope.Var( 'xfm_kind' ).GetValue ) )"));
        String identities = source("common/scripted_triggers/xfm_market_row_id_identity_1.txt");
        assertTrue(identities.contains("story_type = xfm_spot_order"));
        assertTrue(identities.contains("story_type = xfm_futures_order"));
        assertTrue(identities.contains("var:xfm_coin.var:xfm_coin_id = scope:xfm_ui_row_id"));
        assertTrue(identities.contains("var:xfm_holder = root"));
    }
    @Test void validityNeverWritesAndEffectRebindsARealStoryBeforeTheOriginalCancellation() throws IOException {
        for (String file : List.of("scripted_triggers/xfm_market_row_id_identity_1.txt",
                "scripted_triggers/xfm_market_row_id_actions_1.txt", "scripted_triggers/xfm_market_row_id_actions_2.txt",
                "script_values/xfm_market_row_id_counts_1.txt")) {
            String text = source("common/" + file);
            for (String forbidden : List.of("set_variable", "change_variable", "remove_variable", "save_scope_as",
                    "create_story", "end_story", "add_gold", "every_in_global_list", "every_living_character", "is_target_in_global_variable_list"))
                assertFalse(text.contains(forbidden), file + ": " + forbidden);
        }
        String ticket = source("common/scripted_guis/xfm_market_ticket.txt");
        String cancel = body(ticket, "xfm_market_cancel_gui = {");
        assertTrue(cancel.contains("saved_scopes = { xfm_ui_row_id xfm_ui_row_kind xfm_ui_row_table }"));
        assertTrue(cancel.contains("xfm_market_row_resolve_spot_order_effect = yes"));
        assertTrue(cancel.contains("var:xfm_account = root.var:xfm_active_account"));
        assertTrue(cancel.contains("var:xfm_status = 1"));
        assertTrue(cancel.contains("name = xfm_selected_order value = scope:xfm_ui_item"));
        assertTrue(cancel.contains("xfm_spot_cancel_effect = yes"));
        assertTrue(cancel.indexOf("xfm_market_row_resolve_spot_order_effect") < cancel.indexOf("xfm_spot_cancel_effect"));
        assertEquals(2, occurrences(body(cancel, "effect = {"), "clear_saved_scope = xfm_ui_item"));
    }
}
