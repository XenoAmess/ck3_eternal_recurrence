package org.xar.ck3.markets.ui;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.build.ContentValidator;

/** Source/reference contracts only; normal GUI business outcomes require physical SAVE evidence. */
final class MarketSocialRowIdContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static String source(String name) throws IOException { return Files.readString(SOURCE.resolve(name)); }
    private static int count(String text, String needle) { return (text.length() - text.replace(needle, "").length()) / needle.length(); }
    @Test void allSixProductGuiFilesUseNumericRowsAndClaimsAidHaveTheirOwnConcreteButtons() throws IOException {
        int callbacks = 0;
        for (String file : List.of("window", "rows", "futures_book", "debts", "news", "otc")) {
            String gui = source("gui/xfm_market_" + file + ".gui");
            assertFalse(gui.contains("Scope.Self")); assertFalse(gui.contains(".AddScope( 'xfm_ui_item', Scope )"));
            callbacks += count(gui, ".AddScope( 'xfm_ui_row_id', MakeScopeValue(");
        }
        assertEquals(47, callbacks, "original43 callbacks plus two explicit claim/aid instance pairs");
        String debts = source("gui/xfm_market_debts.gui"), news = source("gui/xfm_market_news.gui");
        assertEquals(2, count(debts, "GetScriptedGui( 'xfm_market_select_claim_gui' )"));
        assertEquals(2, count(news, "GetScriptedGui( 'xfm_market_select_aid_debt_gui' )"));
        assertEquals(2, count(debts, "name = \"xfm_market_debt_row\"")); // Original debt type plus concrete claim item.
        assertEquals(1, count(news, "name = \"xfm_market_debt_row\"")); // Concrete aid item, with no inherited business callback.
        assertFalse(news.contains("xfm_market_debt_row = {"));
        assertTrue(debts.contains("GetList( 'xfm_ui_debts_page' )")); assertTrue(debts.contains("GetList( 'xfm_ui_claims_page' )"));
        assertTrue(news.contains("name = \"xfm_market_aid_previous\"")); assertTrue(news.contains("name = \"xfm_market_aid_next\""));
    }
    @Test void privateValidityAndCountsArePureBoundedPageLookupsAndNeverEnumerateTheWorldJournalOrCoinHolders() throws IOException {
        for (String path : List.of("scripted_triggers/xfm_market_social_row_ids.txt", "script_values/xfm_market_social_row_ids.txt")) {
            String text = source("common/" + path);
            for (String forbidden : List.of("set_variable", "change_variable", "remove_variable", "save_scope_as", "create_story",
                    "trigger_event", "add_gold", "every_living_character", "every_in_global_list", "ordered_in_global_list", "is_target_in_global_variable_list"))
                assertFalse(text.contains(forbidden), path + ": " + forbidden);
            assertFalse(text.contains("variable = xfm_news_entries")); assertFalse(text.contains("variable = xfm_holders"));
        }
        String ids = source("common/scripted_triggers/xfm_market_social_row_ids.txt");
        for (String required : List.of("xfm_market_row_input_trigger = yes", "xfm_market_row_owned_account_trigger = yes",
                "xfm_ui_news_bound_before_id", "xfm_ui_aid_news = var:xfm_selected_news", "xfm_ui_otc_page_offset = var:xfm_ui_otc_offset",
                "var:xfm_account.var:xfm_account_id = scope:xfm_ui_row_id", "xfm_market_otc_holder_position_trigger = yes"))
            assertTrue(ids.contains(required), required);
        for (String domain : List.of("debt", "claim", "aid", "news", "otc"))
            assertTrue(ids.contains("xfm_market_social_" + domain + "_count_value = 1"));
    }
    @Test void cacheRefreshIsExplicitAndAidPaginationUsesSixteenActualOutstandingDebtsWithoutPaying() throws IOException {
        String debt = source("common/scripted_effects/xfm_market_ui_debt_pages.txt");
        String aid = source("common/scripted_effects/xfm_market_ui_aid_page.txt");
        String values = source("common/script_values/xfm_market_ui_debt_pages.txt");
        assertEquals(3, count(values, "add = 16"));
        assertTrue(debt.contains("var:xfm_active_account = {")); assertTrue(aid.contains("variable = xfm_debts"));
        assertTrue(aid.contains("var:xfm_outstanding_cents > 0")); assertTrue(aid.contains("name = xfm_ui_aid_has_next value = 1"));
        for (String text : List.of(debt, aid)) for (String forbidden : List.of("create_story", "add_gold", "reserve_effect", "xfm_debt_pay", "xfm_finance_ensure"))
            assertFalse(text.contains(forbidden), forbidden);
        assertTrue(source("common/scripted_effects/xfm_market_ui_pages.txt").contains("xfm_market_ui_debt_pages_effect = yes"));
        assertEquals(4, count(source("common/scripted_guis/xfm_market_portfolio_pages.txt"), "xfm_market_ui_debt_pages_effect = yes"));
        for (String day : List.of("xfm_finance_schedule.txt", "xfm_futures_daily_index.txt")) {
            Path path = SOURCE.resolve("common/scripted_effects").resolve(day);
            if (Files.isRegularFile(path)) assertFalse(Files.readString(path).contains("xfm_market_ui_debt_pages_effect"));
        }
    }
    @Test void inventoryAndRealOriginalOtcProposalConsumerRemainConnected() throws IOException {
        var report = ContentValidator.validate(SOURCE);
        for (String leaf : List.of("scripted_triggers/xfm_market_social_row_ids.txt", "script_values/xfm_market_social_row_ids.txt",
                "scripted_effects/xfm_market_social_row_ids.txt", "scripted_effects/xfm_market_ui_debt_pages.txt",
                "script_values/xfm_market_ui_debt_pages.txt", "scripted_effects/xfm_market_ui_aid_page.txt",
                "scripted_guis/xfm_market_social_rows.txt"))
            assertTrue(report.runtimeFiles().contains("common/" + leaf));
        String otc = source("common/scripted_guis/xfm_market_otc_panel.txt");
        assertTrue(otc.contains("xfm_market_social_resolve_otc_effect = yes"));
        assertTrue(otc.contains("name = xfm_ui_otc_target_position value = scope:xfm_ui_item"));
        assertTrue(otc.contains("xfm_market_ui_otc_propose_effect = yes"));
        assertTrue(otc.contains("xfm_listing_cancel_otc_effect = yes"));
        assertFalse(otc.contains("trigger_event"));
    }
}
