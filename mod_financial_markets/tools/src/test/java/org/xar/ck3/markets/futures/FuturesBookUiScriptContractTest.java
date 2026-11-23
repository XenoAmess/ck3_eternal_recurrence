package org.xar.ck3.markets.futures;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.Clausewitz.Value;

/** Executes actual selected-series projection, funding guards, legal-owner refresh and normal
 * GUI -> reduce -> real order/reservation producers. Engine random/story allocation/config are explicit
 * ports; futures matching only records invocation. Spot regressions execute the actual admission,
 * matching, cash/coin reservation, transfer and finalization scripts. This is not CK3 or a saved game. */
final class FuturesBookUiScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final Path REFERENCE = SOURCE;
    private static final List<String> INPUTS = List.of(
        "scripted_effects/xfm_market_ui_futures_book.txt",
        "scripted_triggers/xfm_market_futures_book_triggers.txt",
        "script_values/xfm_market_futures_book_values.txt",
        "scripted_guis/xfm_market_futures_book.txt",
        "scripted_guis/xfm_market_futures_open.txt",
        "scripted_guis/xfm_market_futures_positions.txt",
        "scripted_guis/xfm_market_futures_stops.txt",
        "scripted_effects/xfm_futures_margin.txt",
        "scripted_effects/xfm_futures_reduce.txt",
        "scripted_effects/xfm_futures_orders.txt",
        "scripted_effects/xfm_futures_cancel_receipts.txt",
        "scripted_triggers/xfm_futures_cancel_triggers.txt", "script_values/xfm_futures_cancel_values.txt", "scripted_effects/xfm_futures_daily_index.txt",
        "scripted_effects/xfm_finance_policy.txt",
        "scripted_effects/xfm_issuer_governance.txt",
        "scripted_effects/xfm_finance_cash.txt",
        "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_reserve.txt",
        "scripted_effects/xfm_finance_assets.txt",
        "scripted_effects/xfm_spot_submit.txt", "scripted_effects/xfm_spot_match.txt",
        "scripted_effects/xfm_spot_orders.txt", "scripted_effects/xfm_spot_trades.txt",
        "scripted_effects/xfm_spot_archive.txt", "scripted_triggers/xfm_spot_triggers.txt",
        "script_values/xfm_spot_values.txt", "script_values/xfm_finance_asset_values.txt",
        "scripted_guis/xfm_market_ticket.txt",
        "scripted_triggers/xfm_finance_triggers.txt",
        "scripted_triggers/xfm_futures_triggers.txt",
        "script_values/xfm_finance_values.txt",
        "script_values/xfm_futures_values.txt",
        "script_values/xfm_numeric_comparison_values.txt",
        "script_values/xfm_config_values.txt",
        "scripted_guis/xfm_market_navigation.txt",
        "scripted_guis/xfm_market_predicates.txt",
        "scripted_guis/xfm_market_portfolio_pages.txt",
        "scripted_effects/xfm_market_ui_book.txt",
        "scripted_effects/xfm_futures_archive.txt",
        "scripted_effects/xfm_futures_ai_funding.txt",
        "scripted_triggers/xfm_futures_ai_triggers.txt",
        "scripted_triggers/xfm_market_row_id_identity_1.txt",
        "scripted_triggers/xfm_market_row_id_actions_1.txt",
        "scripted_triggers/xfm_market_row_id_actions_2.txt",
        "script_values/xfm_market_row_id_counts_1.txt",
        "scripted_effects/xfm_market_row_id_resolve_1.txt",
        "scripted_effects/xfm_market_ui_portfolio_pages.txt",
        "script_values/xfm_market_ui_portfolio_pages.txt",
        "scripted_triggers/xfm_market_social_row_ids.txt",
        "script_values/xfm_market_social_row_ids.txt",
        "scripted_effects/xfm_market_social_row_ids.txt",
        "scripted_effects/xfm_market_ui_debt_pages.txt",
        "script_values/xfm_market_ui_debt_pages.txt",
        "scripted_effects/xfm_market_ui_aid_page.txt",
        "scripted_guis/xfm_market_social_rows.txt",
        "scripted_guis/xfm_market_debts.txt",
        "scripted_guis/xfm_market_otc_panel.txt",
        "scripted_triggers/xfm_market_otc_triggers.txt",
        "script_values/xfm_market_ui_otc_values.txt",
        "scripted_effects/xfm_market_ui_otc_targets.txt",
        "scripted_effects/xfm_market_ui_news.txt",
        "scripted_effects/xfm_finance_legacy.txt",
        "scripted_effects/xfm_spot_maker.txt",
        "scripted_effects/xfm_spot_history.txt");
    public static void main(String[] ignored) throws Exception {
        int passed = 0;
        for (var method : FuturesBookUiScriptContractTest.class.getDeclaredMethods()) {
            if (!method.isAnnotationPresent(Test.class)) continue;
            try { method.invoke(new FuturesBookUiScriptContractTest()); passed++; System.out.println("PASS " + method.getName()); }
            catch (java.lang.reflect.InvocationTargetException error) { throw new AssertionError("FAIL " + method.getName(), error.getCause()); }
        }
        System.out.println("PRODUCTION_SUBSET groups=" + passed + " passed=" + passed + " CK3_NOT_RUN");
    }
    private record Market(Vm vm, Node actor, Node asset, Node contract) { }
    private static Market market() throws IOException {
        Vm v = vm(); Node a = v.node("viewer", ""); a.ai = false;
        Node own = primary(v, a, 10000); a.put("xfm_active_account", own); a.put("xfm_ui_step", 1);
        Node asset = v.asset("asset"), contract = v.contract("series-77", asset, 0, 30);
        contract.put("xfm_contract_id", 77); a.put("xfm_selected_coin", asset); a.put("xfm_futures_contract", contract);
        a.put("xfm_order_limit_cents", 88); return new Market(v, a, asset, contract);
    }
    private static Node quote(Market m, String name, Node contract, int side, int price, int lots, int id) {
        Vm v = m.vm; Node holder = v.node(name + "-holder", ""), account = v.account(name + "-wallet", holder, 0);
        v.order(name, contract, account, side, price); Node order = v.nodes.get(name), reserve = order.ref("xfm_reservation");
        order.put("xfm_order_id", id); order.put("xfm_leverage", 1); order.put("xfm_reserve_price_cents", 120);
        order.put("xfm_filled_gross_cents", 0); order.put("xfm_fee_paid_cents", 0); order.put("xfm_remaining_lots", lots);
        long required = lots * 120L + (long)Math.ceil(lots * 120 * 0.003);
        reserve.put("xfm_remaining_cents", required); account.put("xfm_reserved_cents", required); return order;
    }
    private static void refresh(Market m) { m.vm.runGui("xfm_market_futures_book_refresh_gui", m.actor); }
    private static List<Node> bids(Market m) { return m.actor.list("xfm_ui_futures_bids"); }
    private static List<Node> asks(Market m) { return m.actor.list("xfm_ui_futures_asks"); }

    @Test void twoSameAssetSeriesHaveDifferentRealBooksAndExecutionSnapshots() throws IOException {
        Market m = market(); Node b = m.vm.contract("series-88", m.asset, 0, 60); b.put("xfm_contract_id", 88);
        Node aBid = quote(m, "a-bid", m.contract, 1, 94, 2, 1), bAsk = quote(m, "b-ask", b, 2, 114, 3, 2);
        m.contract.put("xfm_last_execution_cents", 97); m.contract.put("xfm_execution_day", 0); m.contract.put("xfm_execution_lots", 8);
        refresh(m); assertEquals(List.of(aBid), bids(m)); assertTrue(asks(m).isEmpty());
        assertSame(m.contract, m.actor.ref("xfm_ui_futures_book_contract")); assertEquals(97, m.actor.integer("xfm_ui_futures_execution_cents"));
        m.actor.put("xfm_futures_contract", b); refresh(m);
        assertTrue(bids(m).isEmpty()); assertEquals(List.of(bAsk), asks(m)); assertSame(b, m.actor.ref("xfm_ui_futures_book_contract"));
        assertEquals(0, m.actor.integer("xfm_ui_futures_execution_present")); assertEquals(88, m.actor.integer("xfm_order_limit_cents"));
        assertEquals(77, m.contract.integer("xfm_contract_id")); assertEquals(88, b.integer("xfm_contract_id")); assertEquals(0, m.vm.created("xfm_futures_contract"));
    }
    @Test void onlyFundedRemainingPartialOrdersSurviveBlockedCancelledWrongSeriesAndSelf() throws IOException {
        Market m = market(); Node valid = quote(m, "partial", m.contract, 1, 99, 1, 1); valid.put("xfm_status", 1);
        valid.put("xfm_filled_gross_cents", 200); valid.put("xfm_fee_paid_cents", 1);
        Node noMoney = quote(m, "underfunded", m.contract, 1, 100, 2, 2); noMoney.ref("xfm_reservation").put("xfm_remaining_cents", 1);
        Node frozen = quote(m, "frozen", m.contract, 2, 101, 1, 3); frozen.ref("xfm_account").put("xfm_account_frozen", 1);
        Node cancelled = quote(m, "cancelled", m.contract, 1, 102, 1, 4); cancelled.put("xfm_status", 3);
        Node other = m.vm.contract("other-series", m.asset, 0, 60); Node foreign = quote(m, "wrong-series", other, 1, 103, 1, 5); m.contract.list("xfm_orders").add(foreign);
        Node self = quote(m, "self", m.contract, 1, 104, 1, 6); self.ref("xfm_account").put("xfm_holder", m.actor);
        Node reduced = quote(m, "reduce", m.contract, 2, 105, 1, 7); reduced.put("xfm_reduce_order", 1);
        Node mismatch = quote(m, "reserve-mismatch", m.contract, 1, 106, 1, 8); mismatch.ref("xfm_reservation").put("xfm_account", m.actor.ref("xfm_active_account"));
        refresh(m); assertEquals(List.of(valid), bids(m)); assertTrue(asks(m).isEmpty());
        assertEquals(1, m.actor.integer("xfm_ui_futures_bid_lots")); assertEquals(0, m.actor.integer("xfm_ui_futures_ask_lots"));
        assertEquals(0, valid.ref("xfm_account").integer("xfm_free_cents")); // Real frozen funds, not free cash, make this order eligible.
        valid.put("xfm_status", 3); row(m.vm, valid.integer("xfm_order_id"), 2, 1);
        assertFalse(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor));
        refresh(m); assertTrue(bids(m).isEmpty()); assertEquals(0, m.actor.integer("xfm_ui_futures_bid_lots"));
    }
    @Test void actualControllerRefreshExcludesNewlyOwnedProjectAndRestoresExternalOwner() throws IOException {
        Market m = market(); Node order = quote(m, "political", m.contract, 1, 100, 1, 1), account = order.ref("xfm_account");
        Node issuer = m.vm.node("bound-coin", "xfm_finance_coin"), title = m.vm.node("title", "landed_title");
        issuer.put("xfm_entity_type", 4); issuer.put("xfm_bound_entity", title); issuer.put("xfm_controller", account.ref("xfm_holder"));
        issuer.put("xfm_issuer_account", account); title.links.put("holder", account.ref("xfm_holder")); account.put("xfm_legal_entity", issuer);
        refresh(m); assertEquals(List.of(order), bids(m));
        title.links.put("holder", m.actor); refresh(m); assertTrue(bids(m).isEmpty()); assertSame(m.actor, account.ref("xfm_beneficial_owner"));
        Node outsider = m.vm.node("new-controller", ""); title.links.put("holder", outsider); refresh(m); assertEquals(List.of(order), bids(m));
        assertSame(outsider, account.ref("xfm_holder"));
    }
    @Test void exactPriceFifoTopFiveHasBoundedRowsAndFullEligibleDepth() throws IOException {
        Market m = market(); List<Node> all = new ArrayList<>();
        for (int i = 0; i < 6; i++) all.add(quote(m, "bid-" + i, m.contract, 1, i == 0 ? 99 : 100, 1, 20 - i));
        quote(m, "ask-1", m.contract, 2, 110, 2, 21); Node firstAsk = quote(m, "ask-2", m.contract, 2, 109, 1, 22);
        refresh(m); assertEquals(List.of(all.get(5), all.get(4), all.get(3), all.get(2), all.get(1)), bids(m));
        assertSame(firstAsk, asks(m).getFirst()); assertEquals(6, m.actor.integer("xfm_ui_futures_bid_lots"));
        assertEquals(3, m.actor.integer("xfm_ui_futures_ask_lots")); assertTrue(m.actor.list("xfm_ui_futures_candidates").isEmpty());
        assertEquals(0, m.vm.historyVisits); assertEquals(64, m.vm.integerValue("xfm_config_coin_order_capacity_value", m.actor));
    }
    @Test void staleOracleClosedMarketAndExpiredSeriesNeverSubstituteSpotOrMarkForExecution() throws IOException {
        Market m = market(); quote(m, "bid", m.contract, 1, 100, 1, 1); refresh(m);
        assertEquals(0, m.actor.integer("xfm_ui_futures_execution_present")); assertFalse(m.actor.vars.containsKey("xfm_ui_futures_execution_cents"));
        m.asset.put("xfm_oracle_day", 0); refresh(m); assertTrue(bids(m).isEmpty());
        m.asset.put("xfm_oracle_day", 1); m.asset.put("xfm_derivatives_reduce_only", 1); refresh(m); assertTrue(bids(m).isEmpty());
        m.asset.put("xfm_derivatives_reduce_only", 0); m.vm.open = false; refresh(m); assertTrue(bids(m).isEmpty());
        m.vm.open = true; m.contract.put("xfm_expiry_day", 1); refresh(m); assertTrue(bids(m).isEmpty());
        m.contract.put("xfm_expiry_day", 30); m.contract.put("xfm_last_execution_cents", 105); m.contract.put("xfm_execution_day", 0); m.contract.put("xfm_execution_lots", 7);
        refresh(m); assertEquals(105, m.actor.integer("xfm_ui_futures_execution_cents")); assertEquals(0, m.actor.integer("xfm_ui_futures_execution_day")); assertEquals(7, m.actor.integer("xfm_ui_futures_execution_lots"));
        m.actor.put("xfm_selected_coin", m.vm.asset("different-index")); m.vm.run("xfm_market_ui_futures_book_effect", m.actor);
        assertEquals(0, m.actor.integer("xfm_ui_futures_book_ready")); assertTrue(bids(m).isEmpty()); assertFalse(m.actor.vars.containsKey("xfm_ui_futures_book_contract"));
    }
    @Test void inheritedHolderCanSelectThenReduceAtThisGuiLimitWithoutAnyOpeningOrSpotCopy() throws IOException {
        Market m = market(); Node inherited = m.vm.account("inherited-stable-99", m.actor, 10000); inherited.put("xfm_account_id", 99); m.actor.put("xfm_active_account", inherited);
        Node other = m.vm.node("old-counterparty", ""), otherAccount = m.vm.account("old-counterparty-account", other, 1000);
        Node position = m.vm.node("old-position", "xfm_futures_position"); position.put("xfm_contract", m.contract); position.put("xfm_long_account", inherited); position.put("xfm_short_account", otherAccount);
        position.put("xfm_status", 0); position.put("xfm_lots", 3); position.put("xfm_mark_cents", 96); position.put("xfm_long_stop_cents", 80); position.put("xfm_long_take_profit_cents", 115);
        Node longReserve = m.vm.node("old-long-reserve", "xfm_finance_reservation"), shortReserve = m.vm.node("old-short-reserve", "xfm_finance_reservation");
        position.put("xfm_long_reservation", longReserve); position.put("xfm_short_reservation", shortReserve);
        position.put("xfm_position_id", 11); position.put("xfm_kind", 2); inherited.list("xfm_positions").add(position);
        m.vm.run("xfm_market_ui_portfolio_pages_effect", m.actor);
        m.actor.put("xfm_futures_limit_cents", 42); row(m.vm, 11, 2, 1);
        m.vm.runGui("xfm_market_select_futures_position_gui", m.actor); m.actor.put("xfm_ui_step", 7);
        m.vm.runGui("xfm_market_futures_limit_up_gui", m.actor); assertEquals(107, m.actor.integer("xfm_futures_limit_cents"));
        m.vm.runGui("xfm_market_futures_reduce_gui", m.actor); assertEquals(1, m.actor.integer("xfm_futures_result"));
        Node close = m.contract.list("xfm_orders").getLast(); assertEquals(107, close.integer("xfm_limit_cents")); assertSame(inherited, close.ref("xfm_account"));
        assertEquals(88, m.actor.integer("xfm_order_limit_cents")); assertEquals(1, close.ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(0, m.vm.created("xfm_futures_position")); assertEquals(1, m.vm.matchCalls); // Order exists; no synthetic fill.
        m.actor.put("xfm_ui_step", 1); m.vm.runGui("xfm_market_futures_stop_up_gui", m.actor); m.vm.runGui("xfm_market_futures_take_profit_up_gui", m.actor); m.vm.runGui("xfm_market_futures_set_stops_gui", m.actor);
        assertEquals(81, position.integer("xfm_long_stop_cents")); assertEquals(116, position.integer("xfm_long_take_profit_cents")); assertEquals(107, m.actor.integer("xfm_futures_limit_cents"));
    }
    @Test void normalUiReferencesRefreshHooksAndInventoryCloseWithoutAnyDailyHistoryHook() throws IOException {
        var report = org.xar.ck3.markets.build.ContentValidator.validate(SOURCE);
        assertTrue(report.runtimeFiles().containsAll(List.of(
            "common/script_values/xfm_market_futures_book_values.txt", "common/scripted_triggers/xfm_market_futures_book_triggers.txt",
            "common/scripted_effects/xfm_market_ui_futures_book.txt", "common/scripted_guis/xfm_market_futures_book.txt",
            "gui/xfm_market_futures_book.gui", "localization/english/xfm_market_futures_book_l_english.yml",
            "localization/simp_chinese/xfm_market_futures_book_l_simp_chinese.yml")));
        String opening = Files.readString(SOURCE.resolve("common/scripted_guis/xfm_market_futures_open.txt"));
        assertFalse(opening.contains("xfm_order_limit_cents")); assertEquals(3, opening.split("xfm_market_ui_futures_book_effect = yes", -1).length - 1);
        String gui = Files.readString(SOURCE.resolve("gui/xfm_market_futures.gui")); assertTrue(gui.contains("xfm_market_futures_book_panel = {}")); assertFalse(gui.contains("xfm_market_price_up"));
        String book = Files.readString(SOURCE.resolve("common/scripted_effects/xfm_market_ui_futures_book.txt"));
        for (String forbidden : List.of("every_living_character", "xfm_futures_contracts", "xfm_finance_reserve_effect", "add_gold", "trigger_event")) assertFalse(book.contains(forbidden), forbidden);
        String loc = Files.readString(SOURCE.resolve("localization/english/xfm_market_futures_book_l_english.yml")); assertTrue(loc.contains("daily VWAP")); assertTrue(loc.contains("Closing and own/related orders are excluded"));
        for (String dayFile : List.of("xfm_futures_daily_index.txt", "xfm_futures_settlement.txt")) assertFalse(Files.readString(SOURCE.resolve("common/scripted_effects/" + dayFile)).contains("xfm_market_ui_futures_book_effect"));
    }
    @Test void modelLeverageCyclesOnlyThroughItsActualMaximum() throws IOException {
        Market m = market(); m.actor.put("xfm_futures_leverage", 1);
        List<Long> observed = new ArrayList<>(); observed.add(m.actor.integer("xfm_futures_leverage"));
        for (int i = 0; i < 4; i++) { m.vm.runGui("xfm_market_futures_leverage_gui", m.actor); observed.add(m.actor.integer("xfm_futures_leverage")); }
        assertEquals(List.of(1L, 2L, 3L, 5L, 1L), observed);
        assertEquals(0, m.vm.created("xfm_futures_order")); assertEquals(0, m.vm.created("xfm_futures_position"));
        assertEquals(10000, m.actor.ref("xfm_active_account").integer("xfm_free_cents"));
    }
    @Test void leverageCycleUsesSelectedAssetCapsOneThreeTenAndFutureTwenty() throws IOException {
        for (List<Long> expected : List.of(List.of(1L, 1L), List.of(1L, 2L, 3L, 1L),
                List.of(1L, 2L, 3L, 5L, 10L, 1L), List.of(1L, 2L, 3L, 5L, 10L, 20L, 1L))) {
            Market m = market(); long cap = expected.subList(0, expected.size() - 1).stream().mapToLong(Long::longValue).max().orElseThrow();
            m.asset.put("xfm_max_leverage", cap); m.actor.put("xfm_futures_leverage", 1);
            List<Long> observed = new ArrayList<>(); observed.add(1L);
            for (int i = 1; i < expected.size(); i++) { m.vm.runGui("xfm_market_futures_leverage_gui", m.actor); observed.add(m.actor.integer("xfm_futures_leverage")); }
            assertEquals(expected, observed, "software cap=" + cap); // Cap 20 is hypothetical input, not current oracle authority.
        }
    }
    @Test void changedAssetCapImmediatelyDisablesBothSidesAndCycleRepairsOldTicket() throws IOException {
        Market m = market(); m.actor.put("xfm_futures_lots", 1); m.actor.put("xfm_futures_limit_cents", 100); m.actor.put("xfm_futures_leverage", 10);
        BigDecimal cash = m.vm.cashStock();
        for (String side : List.of("long", "short")) {
            String gui = "xfm_market_futures_" + side + "_gui"; assertFalse(m.vm.validGui(gui, m.actor));
            assertThrows(IllegalArgumentException.class, () -> m.vm.runGui(gui, m.actor));
        }
        m.vm.runGui("xfm_market_futures_leverage_gui", m.actor); assertEquals(1, m.actor.integer("xfm_futures_leverage"));
        for (long leverage : List.of(1L, 3L, 5L)) {
            m.actor.put("xfm_futures_leverage", leverage);
            assertTrue(m.vm.validGui("xfm_market_futures_long_gui", m.actor)); assertTrue(m.vm.validGui("xfm_market_futures_short_gui", m.actor));
        }
        Node other = m.vm.asset("single-venue-cap-three"); other.put("xfm_max_leverage", 3); m.actor.put("xfm_selected_coin", other);
        assertFalse(m.vm.validGui("xfm_market_futures_long_gui", m.actor)); assertFalse(m.vm.validGui("xfm_market_futures_short_gui", m.actor));
        m.vm.runGui("xfm_market_futures_leverage_gui", m.actor); assertEquals(1, m.actor.integer("xfm_futures_leverage"));
        assertEquals(cash, m.vm.cashStock()); assertEquals(0, m.vm.created("xfm_futures_order"));
    }
    @Test void absentOrUnqualifiedAssetNeverEnablesLeverageOrOpeningSides() throws IOException {
        Market m = market(); m.actor.put("xfm_futures_lots", 1); m.actor.put("xfm_futures_limit_cents", 100); m.actor.put("xfm_futures_leverage", 1);
        for (String mode : List.of("zero", "missing-cap", "missing-asset")) {
            m.actor.put("xfm_selected_coin", m.asset); m.asset.put("xfm_max_leverage", 0);
            if (mode.equals("missing-cap")) m.asset.vars.remove("xfm_max_leverage");
            if (mode.equals("missing-asset")) m.actor.vars.remove("xfm_selected_coin");
            for (String gui : List.of("xfm_market_futures_leverage_gui", "xfm_market_futures_long_gui", "xfm_market_futures_short_gui")) {
                assertFalse(m.vm.validGui(gui, m.actor), mode + ":" + gui);
                assertThrows(IllegalArgumentException.class, () -> m.vm.runGui(gui, m.actor));
            }
        }
        assertEquals(1, m.actor.integer("xfm_futures_leverage")); assertEquals(0, m.vm.created("xfm_futures_order"));
    }
    private static Vm vm() throws IOException {
        Map<String, Block> definitions = new LinkedHashMap<>();
        for (String input : INPUTS) {
            Path p = SOURCE.resolve("common").resolve(input);
            if (!Files.exists(p)) p = REFERENCE.resolve("common").resolve(input);
            for (Entry e : Clausewitz.parse(Files.readString(p)).entries()) {
                Block b = e.value() instanceof Block block ? block : new Block(List.of(new Entry("value", "=", e.value())));
                if (definitions.put(e.key(), b) != null) throw new IllegalArgumentException("duplicate " + e.key());
            }
        }
        return new Vm(definitions);
    }
    @Test void fullSpotBookAcceptsRealOppositeGtcAndRestsOnlyAfterSixtyFourFifoFills() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"), seller = v.account("seller", v.node("seller-holder", ""), 0);
        Node position = spotPosition(v, "seller-position", seller, coin, 8000);
        List<Node> bids = fillSpotBook(v, coin, 1, 87);
        BigDecimal cash = v.cashStock(); long units = spotSupply(v, coin);
        Node sell = spotSubmit(v, seller, coin, 2, 71, 20, false);
        assertEquals(1, seller.integer("xfm_result")); assertEquals(64, sell.integer("xfm_filled_lots"));
        assertEquals(7, sell.integer("xfm_remaining_lots")); assertEquals(1, sell.integer("xfm_indexed"));
        assertEquals(List.of(sell), coin.list("xfm_spot_orders")); assertEquals(1, coin.integer("xfm_open_orders_count"));
        assertEquals(1, v.exchange.integer("xfm_active_orders_count"));
        assertEquals(bids.stream().map(o -> o.integer("xfm_order_id")).toList(), v.spotExecutionOrderIds);
        assertEquals(64, v.maxSpotMatchIterations); assertEquals(64, v.maxSpotBookEntries);
        assertEquals(1600, position.integer("xfm_quantity_units")); assertEquals(700, position.integer("xfm_reserved_units"));
        assertEquals(5551, seller.integer("xfm_free_cents")); assertEquals(81, v.exchange.integer("xfm_fee_cents"));
        assertEquals(cash, v.cashStock()); assertEquals(units, spotSupply(v, coin));
        for (Node bid : bids) { assertEquals(2, bid.integer("xfm_status")); assertEquals(0, bid.ref("xfm_reservation").integer("xfm_remaining_cents")); }
    }
    @Test void fullAskBookPriceImprovementKeepsExactCumulativeFeeAndOnlyRemainingCashFrozen() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"); fillSpotBook(v, coin, 2, 87);
        Node buyer = v.account("buyer", v.node("buyer-holder", ""), 7122);
        BigDecimal cash = v.cashStock(); long units = spotSupply(v, coin);
        Node buy = spotSubmit(v, buyer, coin, 1, 71, 100, false);
        assertEquals(64, buy.integer("xfm_filled_lots")); assertEquals(17, buy.integer("xfm_fee_paid_cents"));
        assertEquals(7, buy.integer("xfm_remaining_lots")); assertEquals(702, buyer.integer("xfm_reserved_cents"));
        assertEquals(835, buyer.integer("xfm_free_cents")); assertEquals(702, buy.ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(1, coin.list("xfm_spot_orders").size()); assertEquals(81, v.exchange.integer("xfm_fee_cents"));
        assertEquals(cash, v.cashStock()); assertEquals(units, spotSupply(v, coin));
    }
    @Test void fullSubmitterCapacityStillPermitsFillsButReturnsOnlyUnplaceableRemainder() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"), other = spotCoin(v, "other");
        Node seller = v.account("seller", v.node("seller-holder", ""), 64);
        Node position = spotPosition(v, "seller-position", seller, coin, 8000);
        for (int i = 0; i < 32; i++) assertNotNull(spotSubmit(v, seller, other, 1, 1, 1, false));
        fillSpotBook(v, coin, 1, 87); BigDecimal cash = v.cashStock();
        Node sell = spotSubmit(v, seller, coin, 2, 71, 20, false);
        assertEquals(1, seller.integer("xfm_result")); assertEquals(64, sell.integer("xfm_filled_lots"));
        assertEquals(3, sell.integer("xfm_status")); assertEquals(7, sell.integer("xfm_cancelled_lots"));
        assertEquals(7, sell.integer("xfm_capacity_cancelled_lots")); assertEquals(0, sell.integer("xfm_indexed"));
        assertEquals(32, seller.integer("xfm_open_orders_count")); assertEquals(32, other.list("xfm_spot_orders").size());
        assertTrue(coin.list("xfm_spot_orders").isEmpty()); assertEquals(0, position.integer("xfm_reserved_units"));
        assertEquals(1600, position.integer("xfm_quantity_units")); assertEquals(64, seller.integer("xfm_reserved_cents"));
        assertEquals(cash, v.cashStock());
    }
    @Test void fullBookWithoutIndependentCrossingCannotAlterFundsOrEvictAMaker() throws IOException {
        for (String mode : List.of("non-crossing", "same-beneficiary", "underfunded")) {
            Vm v = vm(); Node coin = spotCoin(v, "coin"), holder = v.node("seller-holder", "");
            Node seller = v.account("seller", holder, 0), position = spotPosition(v, "position", seller, coin, 8000);
            List<Node> bids = fillSpotBook(v, coin, 1, 87); bids.getFirst().put("xfm_is_maker_quote", 1);
            if (mode.equals("same-beneficiary")) for (Node bid : bids) bid.ref("xfm_account").put("xfm_holder", holder);
            if (mode.equals("underfunded")) for (Node bid : bids) bid.ref("xfm_reservation").put("xfm_remaining_cents", 1);
            BigDecimal cash = v.cashStock(); long stories = v.exchange.integer("xfm_order_stories_count");
            Node refused = spotSubmit(v, seller, coin, 2, 71, mode.equals("non-crossing") ? 88 : 20, false);
            assertNull(refused, mode); assertEquals(0, seller.integer("xfm_result"), mode);
            assertEquals(bids, coin.list("xfm_spot_orders")); assertEquals(64, coin.integer("xfm_open_orders_count"));
            assertEquals(0, v.spotExecutionOrderIds.size()); assertEquals(0, position.integer("xfm_reserved_units"));
            assertEquals(stories, v.exchange.integer("xfm_order_stories_count")); assertEquals(cash, v.cashStock());
            for (Node bid : bids) assertEquals(1, bid.integer("xfm_status"));
        }
    }
    @Test void crossingAtFullCapacityStillRequiresWholeCashFeeOrUnreservedCoinsBeforeZeroFills() throws IOException {
        for (boolean buy : List.of(false, true)) {
            Vm v = vm(); Node coin = spotCoin(v, "coin"); List<Node> resting = fillSpotBook(v, coin, buy ? 2 : 1, 87);
            Node incoming = v.account("incoming", v.node("holder", ""), buy ? 87 : 0);
            if (!buy) spotPosition(v, "position", incoming, coin, 99);
            BigDecimal cash = v.cashStock(); long stories = v.exchange.integer("xfm_order_stories_count");
            assertNull(spotSubmit(v, incoming, coin, buy ? 1 : 2, 1, 87, false));
            assertEquals(0, incoming.integer("xfm_result")); assertEquals(0, incoming.integer("xfm_reserved_cents"));
            assertEquals(0, v.spotExecutionOrderIds.size()); assertEquals(resting, coin.list("xfm_spot_orders"));
            assertEquals(stories, v.exchange.integer("xfm_order_stories_count")); assertEquals(cash, v.cashStock());
        }
    }
    @Test void partialMakerFreesNoSlotButFullyFilledTakerNeverNeedsAnotherRestingSlot() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"); List<Node> bids = fillSpotBook(v, coin, 1, 87, 2);
        // The original two-lot bid was funded by the production submission/reservation path.
        Node first = bids.getFirst(), account = first.ref("xfm_account"), reserve = first.ref("xfm_reservation");
        Node seller = v.account("seller", v.node("seller-holder", ""), 0); spotPosition(v, "position", seller, coin, 100);
        BigDecimal cash = v.cashStock(); Node sell = spotSubmit(v, seller, coin, 2, 1, 20, false);
        assertEquals(2, sell.integer("xfm_status")); assertEquals(0, sell.integer("xfm_indexed"));
        assertEquals(64, coin.list("xfm_spot_orders").size()); assertEquals(1, first.integer("xfm_remaining_lots"));
        assertEquals(87, reserve.integer("xfm_remaining_cents")); assertEquals(64, v.maxSpotBookEntries);
        assertEquals(List.of(first.integer("xfm_order_id")), v.spotExecutionOrderIds); assertEquals(cash, v.cashStock());
    }
    @Test void fullMixedBookSkipsOwnBetterBidAndKeepsRealPriceThenFifoPriority() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"); List<Node> bids = fillSpotBook(v, coin, 1, 87);
        Node former = bids.getLast(); v.run("xfm_spot_cancel_order_effect", former);
        Node better = v.account("better-bid", v.node("better-holder", ""), 100);
        Node laterBetter = spotSubmit(v, better, coin, 1, 1, 99, false);
        Node holder = bids.getFirst().ref("xfm_account").ref("xfm_holder");
        Node seller = v.account("same-owner-secondary", holder, 0); spotPosition(v, "seller-position", seller, coin, 200);
        BigDecimal cash = v.cashStock(); Node sell = spotSubmit(v, seller, coin, 2, 2, 20, false);
        assertEquals(2, sell.integer("xfm_filled_lots"));
        assertEquals(List.of(laterBetter.integer("xfm_order_id"), bids.get(1).integer("xfm_order_id")), v.spotExecutionOrderIds);
        assertEquals(1, bids.getFirst().integer("xfm_remaining_lots"));
        assertEquals(88, bids.getFirst().ref("xfm_reservation").integer("xfm_remaining_cents"));
        assertEquals(0, sell.integer("xfm_indexed")); assertEquals(cash, v.cashStock());
    }
    @Test void iocStillCancelsOnlyItsRemainderAndHardStoryLimitCannotBeBypassedByCrossing() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"); fillSpotBook(v, coin, 1, 87);
        Node seller = v.account("seller", v.node("holder", ""), 0); Node p = spotPosition(v, "position", seller, coin, 8000);
        BigDecimal cash = v.cashStock(); Node sell = spotSubmit(v, seller, coin, 2, 71, 20, true);
        assertEquals(64, sell.integer("xfm_filled_lots")); assertEquals(7, sell.integer("xfm_cancelled_lots"));
        assertEquals(0, sell.integer("xfm_capacity_cancelled_lots")); assertTrue(coin.list("xfm_spot_orders").isEmpty());
        assertEquals(0, p.integer("xfm_reserved_units")); assertEquals(cash, v.cashStock());
        Vm capped = vm(); Node c = spotCoin(capped, "coin"); fillSpotBook(capped, c, 1, 87);
        Node a = capped.account("seller", capped.node("holder", ""), 0); spotPosition(capped, "position", a, c, 100);
        capped.exchange.put("xfm_order_stories_count", 24576);
        assertNull(spotSubmit(capped, a, c, 2, 1, 20, true)); assertEquals(0, capped.spotExecutionOrderIds.size());
    }
    @Test void normalSpotButtonsReadTheSameCapacityCrossingAndLegalActiveAccountWithoutMutating() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "coin"); fillSpotBook(v, coin, 1, 87);
        Node actor = v.node("actor", ""); actor.ai = false; Node wallet = v.account("wallet", actor, 0);
        actor.put("xfm_account", wallet); actor.put("xfm_active_account", wallet); actor.put("xfm_selected_coin", coin);
        actor.put("xfm_order_lots", 71); actor.put("xfm_order_limit_cents", 100); actor.put("xfm_order_ioc", 0);
        actor.put("xfm_order_side", 1); // The sell button must not accidentally inspect the previous buy-side ticket.
        BigDecimal cash = v.cashStock(); long stories = v.exchange.integer("xfm_order_stories_count");
        assertFalse(v.validGui("xfm_market_sell_gui", actor)); assertFalse(v.validGui("xfm_market_buy_gui", actor));
        actor.put("xfm_order_limit_cents", 20); assertTrue(v.validGui("xfm_market_sell_gui", actor));
        assertFalse(v.validGui("xfm_market_buy_gui", actor));
        wallet.put("xfm_account_frozen", 1); assertFalse(v.validGui("xfm_market_sell_gui", actor)); wallet.put("xfm_account_frozen", 0);
        Node foreign = v.account("foreign", v.node("foreign-holder", ""), 0); actor.put("xfm_active_account", foreign);
        assertTrue(v.validGui("xfm_market_sell_gui", actor)); // Same legal primary fallback as select_account.
        for (Node order : coin.list("xfm_spot_orders")) order.ref("xfm_account").put("xfm_holder", actor);
        v.run("xfm_spot_refresh_book_effect", coin);
        assertFalse(v.validGui("xfm_market_sell_gui", actor));
        assertEquals(stories, v.exchange.integer("xfm_order_stories_count")); assertEquals(cash, v.cashStock());
        assertEquals(64, coin.list("xfm_spot_orders").size());
    }
    private static void row(Vm v, long id, long kind, long table) {
        v.scopes.put("xfm_ui_row_id", new NumberDatum(BigDecimal.valueOf(id)));
        v.scopes.put("xfm_ui_row_kind", new NumberDatum(BigDecimal.valueOf(kind)));
        v.scopes.put("xfm_ui_row_table", new NumberDatum(BigDecimal.valueOf(table)));
    }
    @Test void numericSpotCancelRebindsTheRealPartialOrderAndReleasesOnlyItsSevenLots() throws IOException {
        Vm v = vm(); Node coin = spotCoin(v, "numeric-coin"); coin.put("xfm_coin_id", 55);
        Node actor = v.node("numeric-seller", ""); actor.ai = false;
        Node account = v.account("numeric-wallet", actor, 0); account.put("xfm_account_id", 54);
        actor.put("xfm_account", account); actor.put("xfm_active_account", account); actor.put("xfm_selected_coin", coin);
        Node position = spotPosition(v, "numeric-holding", account, coin, 8000);
        List<Node> bids = fillSpotBook(v, coin, 1, 87);
        BigDecimal cash = v.cashStock(); long supply = spotSupply(v, coin);
        Node sell = spotSubmit(v, account, coin, 2, 71, 20, false);
        assertEquals(64, sell.integer("xfm_filled_lots")); assertEquals(7, sell.integer("xfm_remaining_lots"));
        assertEquals(700, position.integer("xfm_reserved_units"));
        v.run("xfm_market_ui_portfolio_pages_effect", actor);
        row(v, sell.integer("xfm_order_id"), 0, 1);
        Map<String, Datum> beforeValid = Map.copyOf(actor.vars);
        assertTrue(v.validGui("xfm_market_cancel_gui", actor)); assertEquals(beforeValid, actor.vars);
        v.runGui("xfm_market_cancel_gui", actor);
        assertSame(sell, actor.ref("xfm_selected_order")); assertEquals(1, actor.integer("xfm_result"));
        assertEquals(3, sell.integer("xfm_status")); assertEquals(7, sell.integer("xfm_cancelled_lots"));
        assertEquals(0, sell.integer("xfm_remaining_lots")); assertEquals(64, sell.integer("xfm_filled_lots"));
        assertEquals(0, position.integer("xfm_reserved_units")); assertEquals(1600, position.integer("xfm_quantity_units"));
        assertTrue(account.list("xfm_orders").isEmpty()); assertEquals(List.of(sell), account.list("xfm_order_history"));
        assertTrue(actor.list("xfm_ui_orders_page").isEmpty()); assertEquals(List.of(sell), actor.list("xfm_ui_history_page"));
        assertFalse(v.scopes.containsKey("xfm_ui_item")); assertEquals(cash, v.cashStock()); assertEquals(supply, spotSupply(v, coin));
        for (Node bid : bids) { assertEquals(2, bid.integer("xfm_status")); assertEquals(0, bid.integer("xfm_remaining_lots")); }
        row(v, sell.integer("xfm_order_id"), 0, 1); assertFalse(v.validGui("xfm_market_cancel_gui", actor));
        row(v, sell.integer("xfm_order_id"), 0, 2); assertTrue(v.validGui("xfm_market_is_spot_order_gui", actor));
        assertFalse(v.validGui("xfm_market_cancel_gui", actor)); // History is readable, never a route to cancel a terminal order.
    }
    @Test void naturalSpotAndFuturesOrderIdCollisionHasSeparateKindsAndRealCancellationEffects() throws IOException {
        Vm v = vm(); Node actor = ticket(v, "0"); actor.ai = false; Node account = primary(v, actor, 10000);
        actor.put("xfm_active_account", account);
        Node coin = spotCoin(v, "collision-coin"); coin.put("xfm_coin_id", 55);
        Node selectedAsset = actor.ref("xfm_selected_coin"), selectedContract = actor.ref("xfm_futures_contract");
        Node spot = spotSubmit(v, account, coin, 1, 1, 20, false);
        assertSame(selectedAsset, actor.ref("xfm_selected_coin")); // Account-scope spot input does not select an asset on its holder.
        assertSame(selectedAsset, selectedContract.ref("xfm_coin")); assertSame(selectedContract, actor.ref("xfm_futures_contract"));
        assertTrue(v.program.containsKey("xfm_futures_discoverable_trigger")); // Load the actual contract guard, never port it to true.
        assertTrue(v.test(v.definition("xfm_futures_discoverable_trigger"), new Frame(selectedContract, null, actor)));
        v.runGui("xfm_market_futures_long_gui", actor);
        assertEquals(1, actor.integer("xfm_futures_result"));
        Node future = actor.ref("xfm_futures_contract").list("xfm_orders").getLast();
        assertEquals(1, spot.integer("xfm_order_id")); assertEquals(1, future.integer("xfm_order_id"));
        v.run("xfm_market_ui_portfolio_pages_effect", actor); row(v, 1, 0, 1);
        assertTrue(v.validGui("xfm_market_cancel_gui", actor)); assertFalse(v.validGui("xfm_market_cancel_futures_order_gui", actor));
        long futureReserve = future.ref("xfm_reservation").integer("xfm_remaining_cents"); BigDecimal cash = v.cashStock();
        v.runGui("xfm_market_cancel_gui", actor);
        assertSame(spot, actor.ref("xfm_selected_order")); assertEquals(3, spot.integer("xfm_status"));
        assertEquals(0, future.integer("xfm_status")); assertEquals(futureReserve, future.ref("xfm_reservation").integer("xfm_remaining_cents"));
        row(v, 1, 2, 1); assertFalse(v.validGui("xfm_market_cancel_gui", actor)); assertTrue(v.validGui("xfm_market_cancel_futures_order_gui", actor));
        v.runGui("xfm_market_cancel_futures_order_gui", actor);
        assertSame(future, actor.ref("xfm_futures_selected_order")); assertEquals(3, future.integer("xfm_status"));
        assertEquals(0, future.ref("xfm_reservation").integer("xfm_remaining_cents")); assertEquals(cash, v.cashStock());
        assertEquals(1, future.integer("xfm_cancel_receipt_version")); assertEquals(2, future.integer("xfm_cancel_reason"));
        assertEquals(1, future.integer("xfm_cancel_release_api_called")); assertEquals(1, future.integer("xfm_cancel_release_result"));
        assertEquals(1, future.integer("xfm_cancel_release_verified")); assertEquals(futureReserve, future.integer("xfm_cancel_released_cents"));
        assertEquals(futureReserve, future.integer("xfm_cancel_before_remaining_cents")); assertEquals(0, future.integer("xfm_cancel_after_remaining_cents"));
        Map<String, Datum> firstCancellation = Map.copyOf(future.vars);
        v.execute(Clausewitz.parse("xfm_futures_cancel_with_reason_effect = { REASON = 15 }"), new Frame(future, null, future));
        assertEquals(firstCancellation, future.vars); assertEquals(cash, v.cashStock());
        assertThrows(IllegalArgumentException.class, () -> v.execute(Clausewitz.parse("invented_parameter_effect = { REASON = 2 }"), new Frame(future, null, future)));
        assertFalse(v.scopes.containsKey("xfm_ui_item"));
    }
    @Test void missingZeroForeignStaleDuplicateAndWrongPageIdsCannotWriteSelectionOrCancel() throws IOException {
        Vm v = vm(); Node actor = v.node("guard-actor", ""); actor.ai = false;
        Node account = primary(v, actor, 1000); actor.put("xfm_active_account", account);
        Node coin = spotCoin(v, "guard-coin"); coin.put("xfm_coin_id", 55);
        Node order = spotSubmit(v, account, coin, 1, 1, 20, false);
        v.run("xfm_market_ui_portfolio_pages_effect", actor); BigDecimal cash = v.cashStock();
        long id = order.integer("xfm_order_id"); row(v, id, 0, 1);
        Map<String, Datum> actorBefore = Map.copyOf(actor.vars);
        v.scopes.remove("xfm_ui_row_id"); assertFalse(v.validGui("xfm_market_cancel_gui", actor));
        for (long bad : List.of(0L, -1L, id + 100L)) { row(v, bad, 0, 1); assertFalse(v.validGui("xfm_market_cancel_gui", actor)); }
        row(v, id, 0, 2); assertFalse(v.validGui("xfm_market_cancel_gui", actor));
        row(v, id, 0, 1); actor.put("xfm_ui_orders_offset", 16); assertFalse(v.validGui("xfm_market_cancel_gui", actor)); actor.put("xfm_ui_orders_offset", 0);
        Node stranger = v.node("guard-stranger", ""); account.put("xfm_holder", stranger);
        assertFalse(v.validGui("xfm_market_cancel_gui", actor)); account.put("xfm_holder", actor);
        Node duplicate = v.node("corrupt-same-domain-id", "xfm_spot_order");
        duplicate.put("xfm_order_id", id); duplicate.put("xfm_account", account); duplicate.put("xfm_status", 1);
        actor.list("xfm_ui_orders_page").add(duplicate); assertFalse(v.validGui("xfm_market_cancel_gui", actor));
        // Execute the real effect body directly as a stale-render race. It must check its own typed resolver gate.
        v.execute(v.definition("xfm_market_cancel_gui").block("effect"), new Frame(actor, null, actor));
        assertEquals(actorBefore, actor.vars); assertEquals(1, order.integer("xfm_status")); assertEquals(cash, v.cashStock());
        assertFalse(v.scopes.containsKey("xfm_ui_item"));
        actor.list("xfm_ui_orders_page").remove(duplicate); assertTrue(v.validGui("xfm_market_cancel_gui", actor));
        Node alien = v.account("guard-foreign-wallet", stranger, 1000); order.put("xfm_account", alien);
        v.execute(v.definition("xfm_market_cancel_gui").block("effect"), new Frame(actor, null, actor));
        assertEquals(actorBefore, actor.vars); assertEquals(1, order.integer("xfm_status"));
        order.put("xfm_account", account); account.list("xfm_orders").remove(order);
        assertTrue(v.validGui("xfm_market_cancel_gui", actor)); // A render snapshot can precede the maintained-list removal.
        v.execute(v.definition("xfm_market_cancel_gui").block("effect"), new Frame(actor, null, actor));
        assertEquals(actorBefore, actor.vars); assertEquals(1, order.integer("xfm_status")); // Execution must recheck current source membership.
    }
    @Test void normalPortfolioPagingCachesOnlySixteenRealReferencesAndSpotRowsUseCoinIds() throws IOException {
        Vm v = vm(); Node actor = v.node("page-actor", ""); actor.ai = false;
        Node account = primary(v, actor, 0); actor.put("xfm_active_account", account);
        List<Node> positions = new ArrayList<>();
        for (int i = 1; i <= 17; i++) {
            Node coin = spotCoin(v, "page-coin-" + i); coin.put("xfm_coin_id", i); coin.put("xfm_last_price_cents", 10 + i);
            positions.add(spotPosition(v, "page-position-" + i, account, coin, 100));
        }
        v.run("xfm_market_ui_portfolio_pages_effect", actor);
        assertEquals(positions.subList(0, 16), actor.list("xfm_ui_positions_page"));
        row(v, 17, 0, 1); assertFalse(v.validGui("xfm_market_select_position_gui", actor)); assertEquals(16, v.maxUiPageEntries);
        v.runGui("xfm_market_positions_next_gui", actor);
        assertEquals(List.of(positions.get(16)), actor.list("xfm_ui_positions_page"));
        row(v, 1, 0, 1); assertFalse(v.validGui("xfm_market_select_position_gui", actor));
        row(v, 17, 0, 1); assertTrue(v.validGui("xfm_market_select_position_gui", actor));
        v.runGui("xfm_market_select_position_gui", actor);
        assertSame(positions.get(16).ref("xfm_coin"), actor.ref("xfm_selected_coin")); assertEquals(27, actor.integer("xfm_order_limit_cents"));
        assertFalse(positions.get(16).vars.containsKey("xfm_position_id")); // No invented position ID on spot holdings.
        assertFalse(v.scopes.containsKey("xfm_ui_item")); assertEquals(0, v.created("xfm_futures_order"));
        v.runGui("xfm_market_positions_previous_gui", actor); row(v, 1, 0, 1);
        assertTrue(v.validGui("xfm_market_select_position_gui", actor)); assertEquals(0, actor.integer("xfm_ui_positions_offset"));
    }
    @Test void fourLotShortPositionElevenCanBeSelectedThenSubmitTwoLotCloseAtThisGuiPrice() throws IOException {
        Market m = market(); Node account = m.actor.ref("xfm_active_account"), other = m.vm.account("p11-other-account", m.vm.node("p11-other-holder", ""), 1000);
        Node position = m.vm.node("legacy-position-eleven", "xfm_futures_position");
        position.put("xfm_position_id", 11); position.put("xfm_kind", 2); position.put("xfm_contract", m.contract);
        position.put("xfm_long_account", other); position.put("xfm_short_account", account);
        position.put("xfm_status", 0); position.put("xfm_lots", 4); position.put("xfm_mark_cents", 96);
        position.put("xfm_short_stop_cents", 120); position.put("xfm_short_take_profit_cents", 70);
        Node longReserve = m.vm.node("p11-long-reserve", "xfm_finance_reservation"), shortReserve = m.vm.node("p11-short-reserve", "xfm_finance_reservation");
        position.put("xfm_long_reservation", longReserve); position.put("xfm_short_reservation", shortReserve);
        account.list("xfm_positions").add(position); m.contract.list("xfm_positions").add(position);
        m.actor.put("xfm_futures_limit_cents", 42);
        refresh(m); // Normal explicit series-book refresh initializes a new series ticket from the current asset mark.
        assertEquals(100, m.actor.integer("xfm_futures_limit_cents")); assertSame(m.contract, m.actor.ref("xfm_ui_futures_book_contract"));
        m.vm.run("xfm_market_ui_portfolio_pages_effect", m.actor);
        row(m.vm, 11, 2, 1); assertFalse(m.vm.validGui("xfm_market_select_position_gui", m.actor));
        m.vm.runGui("xfm_market_select_futures_position_gui", m.actor);
        assertSame(position, m.actor.ref("xfm_futures_selected_position")); assertSame(m.contract, m.actor.ref("xfm_futures_contract"));
        assertEquals(2, m.actor.integer("xfm_futures_holding_side")); assertEquals(96, m.actor.integer("xfm_futures_limit_cents"));
        m.vm.runGui("xfm_market_futures_reduce_up_gui", m.actor); assertEquals(2, m.actor.integer("xfm_futures_reduce_lots"));
        m.actor.put("xfm_ui_step", 11); m.vm.runGui("xfm_market_futures_limit_up_gui", m.actor);
        m.vm.runGui("xfm_market_futures_reduce_gui", m.actor);
        Node close = m.contract.list("xfm_orders").getLast();
        assertEquals(1, m.actor.integer("xfm_futures_result")); assertSame(position, close.ref("xfm_close_position"));
        assertSame(account, close.ref("xfm_account")); assertEquals(2, close.integer("xfm_remaining_lots")); assertEquals(107, close.integer("xfm_limit_cents"));
        assertEquals(1, close.integer("xfm_side")); assertEquals(88, m.actor.integer("xfm_order_limit_cents"));
        assertEquals(4, position.integer("xfm_lots")); assertEquals(0, m.vm.created("xfm_futures_position")); // No fabricated replacement or fill.
        position.put("xfm_status", 1); assertFalse(m.vm.validGui("xfm_market_select_futures_position_gui", m.actor));
    }
    @Test void readOnlyBookUsesOtherPeoplesCurrentContractIdsAndRejectsStaleOrDuplicateIds() throws IOException {
        Market m = market(); Node order = quote(m, "id-book-external", m.contract, 1, 99, 2, 18); refresh(m);
        row(m.vm, 18, 2, 1); assertTrue(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor));
        assertNotSame(m.actor, order.ref("xfm_account").ref("xfm_holder"));
        Node other = m.vm.contract("id-book-other-series", m.asset, 0, 60); m.actor.put("xfm_futures_contract", other);
        assertFalse(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor)); m.actor.put("xfm_futures_contract", m.contract);
        Node duplicate = quote(m, "id-book-duplicate", m.contract, 2, 110, 1, 18); refresh(m);
        assertFalse(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor));
        duplicate.put("xfm_order_id", 19); refresh(m); assertTrue(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor));
        order.put("xfm_status", 3); assertFalse(m.vm.validGui("xfm_market_futures_book_row_gui", m.actor));
        assertFalse(m.vm.scopes.containsKey("xfm_ui_item")); assertEquals(0, m.vm.created("xfm_futures_order"));
    }

    private static Node debt(Vm v, String name, long id, Node debtor, Node creditor, long outstanding) {
        Node d = v.node(name, "xfm_debt_claim"); d.put("xfm_debt_id", id); d.put("xfm_debtor_account", debtor);
        d.put("xfm_creditor_account", creditor); d.put("xfm_outstanding_cents", outstanding); d.put("xfm_state", 1);
        debtor.list("xfm_debts").add(d); creditor.list("xfm_claims").add(d); return d;
    }
    @Test void debtsTabCallbackRefreshesTheCurrentPagesBeforeShowingTheTab() throws IOException {
        String line = Files.readAllLines(SOURCE.resolve("gui/xfm_market_window.gui")).stream()
            .filter(text -> text.contains("name = \"xfm_tab_debts\"")).findFirst().orElseThrow();
        String valid = "[GetScriptedGui( 'xfm_market_debts_tab_gui' ).IsValid( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]";
        String refresh = "[GetScriptedGui( 'xfm_market_debts_tab_gui' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]";
        String show = "[GetVariableSystem.Set( 'xfm_market_tab', 'debts' )]";
        assertTrue(line.contains("enabled = \"" + valid + "\""));
        assertTrue(line.contains("onclick = \"" + refresh + "\""));
        assertTrue(line.indexOf(refresh) < line.indexOf(show));
        assertFalse(line.contains("xfm_market_refresh_gui"));
    }
    @Test void enteringDebtsTabMakesANewClaimSelectableWithoutMarketRefreshOrBusinessWrites() throws IOException {
        Market m = market(); Node own = m.actor.ref("xfm_active_account"); m.actor.flags.add("xfm_market_open");
        m.vm.runGui("xfm_market_debts_tab_gui", m.actor); // Empty pages when the normal window was first opened.
        Node other = m.vm.account("tab-counterparty", m.vm.node("tab-counterparty-holder", ""), 900);
        Node owed = debt(m.vm, "tab-owed", 11, own, other, 200);
        Node claim = debt(m.vm, "tab-new-claim", 12, other, own, 300);
        m.actor.put("xfm_selected_debt", owed); row(m.vm, 12, 0, 1);
        assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor), "The new claim is not in the stale page");
        Map<Node, Map<String, Datum>> before = new HashMap<>();
        for (Node node : m.vm.nodes.values()) before.put(node, Map.copyOf(node.vars));
        BigDecimal cash = m.vm.cashStock(); int nodes = m.vm.nodes.size(); m.vm.effectCalls.clear();
        m.vm.runGui("xfm_market_debts_tab_gui", m.actor);
        assertEquals(List.of(owed), m.actor.list("xfm_ui_debts_page"));
        assertEquals(List.of(claim), m.actor.list("xfm_ui_claims_page"));
        assertSame(own, m.actor.ref("xfm_ui_debt_page_account"));
        assertSame(owed, m.actor.ref("xfm_selected_debt"), "Entering the tab does not select or consent to a claim");
        assertEquals(Map.of("xfm_market_ui_debt_pages_effect", 1), m.vm.effectCalls);
        for (Node node : m.vm.nodes.values()) if (node != m.actor) assertEquals(before.get(node), node.vars, node.id);
        for (var entry : before.get(m.actor).entrySet()) assertEquals(entry.getValue(), m.actor.vars.get(entry.getKey()), entry.getKey());
        assertEquals(nodes, m.vm.nodes.size()); assertEquals(cash, m.vm.cashStock());
        assertFalse(m.vm.scopes.containsKey("xfm_ui_debt_page_actor")); assertFalse(m.vm.scopes.containsKey("xfm_ui_debt_page_item"));
        assertTrue(m.vm.validGui("xfm_market_select_claim_gui", m.actor));
        m.vm.runGui("xfm_market_select_claim_gui", m.actor); assertSame(claim, m.actor.ref("xfm_selected_debt"));
        assertEquals(300, claim.integer("xfm_outstanding_cents")); assertEquals(cash, m.vm.cashStock());
    }
    @Test void debtsTabKeepsTheExistingSixteenRowOffsetsAndRebindsAnotherOwnedAccount() throws IOException {
        Market m = market(); Node own = m.actor.ref("xfm_active_account"); m.actor.flags.add("xfm_market_open");
        Node other = m.vm.account("tab-page-debtor", m.vm.node("tab-page-debtor-holder", ""), 500);
        List<Node> all = new ArrayList<>();
        for (int i = 1; i <= 17; i++) all.add(debt(m.vm, "tab-page-claim-" + i, i, other, own, 100));
        m.actor.put("xfm_ui_claims_offset", 16); BigDecimal cash = m.vm.cashStock();
        m.vm.runGui("xfm_market_debts_tab_gui", m.actor);
        assertEquals(List.of(all.get(16)), m.actor.list("xfm_ui_claims_page")); assertEquals(16, m.actor.integer("xfm_ui_claims_page_offset"));
        row(m.vm, 17, 0, 1); assertTrue(m.vm.validGui("xfm_market_select_claim_gui", m.actor));
        row(m.vm, 1, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor));
        m.vm.runGui("xfm_market_claims_previous_gui", m.actor); assertEquals(all.subList(0, 16), m.actor.list("xfm_ui_claims_page"));
        Node second = m.vm.account("tab-second-owned", m.actor, 700);
        Node secondClaim = debt(m.vm, "tab-second-claim", 18, other, second, 250);
        m.actor.put("xfm_active_account", second);
        assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor), "Old-account page is not a valid new-account row");
        m.vm.runGui("xfm_market_debts_tab_gui", m.actor);
        assertEquals(List.of(secondClaim), m.actor.list("xfm_ui_claims_page")); assertSame(second, m.actor.ref("xfm_ui_debt_page_account"));
        row(m.vm, 18, 0, 1); assertTrue(m.vm.validGui("xfm_market_select_claim_gui", m.actor));
        row(m.vm, 1, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor));
        assertEquals(cash.add(BigDecimal.valueOf(700)).stripTrailingZeros(), m.vm.cashStock());
        for (Node claim : all) assertEquals(100, claim.integer("xfm_outstanding_cents"));
        assertEquals(250, secondClaim.integer("xfm_outstanding_cents"));
    }
    @Test void debtsTabRejectsAIClosedMissingWrongTypeAndForeignAccountsBeforeAnyPageWrite() throws IOException {
        for (String mode : List.of("AI", "closed", "missing", "wrong-type", "foreign")) {
            Market m = market(); Node own = m.actor.ref("xfm_active_account"); m.actor.flags.add("xfm_market_open");
            Node other = m.vm.account("tab-invalid-other", m.vm.node("tab-invalid-holder", ""), 500);
            Node claim = debt(m.vm, "tab-invalid-claim", 21, other, own, 300);
            m.vm.runGui("xfm_market_debts_tab_gui", m.actor);
            switch (mode) {
                case "AI" -> m.actor.ai = true;
                case "closed" -> m.actor.flags.remove("xfm_market_open");
                case "missing" -> m.actor.vars.remove("xfm_active_account");
                case "wrong-type" -> m.actor.put("xfm_active_account", m.asset);
                case "foreign" -> m.actor.put("xfm_active_account", other);
                default -> throw new AssertionError(mode);
            }
            Map<String, Datum> before = Map.copyOf(m.actor.vars);
            List<Node> debtsBefore = List.copyOf(m.actor.list("xfm_ui_debts_page")), claimsBefore = List.copyOf(m.actor.list("xfm_ui_claims_page"));
            BigDecimal cash = m.vm.cashStock(); m.vm.effectCalls.clear();
            assertFalse(m.vm.validGui("xfm_market_debts_tab_gui", m.actor), mode);
            assertThrows(IllegalArgumentException.class, () -> m.vm.runGui("xfm_market_debts_tab_gui", m.actor), mode);
            // Revalidate even a direct scripted-GUI effect call; it must not clear a previously populated page.
            m.vm.execute(m.vm.definition("xfm_market_debts_tab_gui").block("effect"), new Frame(m.actor, null, m.actor));
            assertEquals(before, m.actor.vars, mode); assertEquals(debtsBefore, m.actor.list("xfm_ui_debts_page"), mode);
            assertEquals(claimsBefore, m.actor.list("xfm_ui_claims_page"), mode); assertEquals(Map.of(), m.vm.effectCalls, mode);
            assertEquals(300, claim.integer("xfm_outstanding_cents"), mode); assertEquals(cash, m.vm.cashStock(), mode);
            assertFalse(m.vm.scopes.containsKey("xfm_ui_debt_page_actor"), mode);
        }
    }
    @Test void typedDebtAndClaimIdsSelectOnlyTheCurrentLegalAccountPageAndNeverPay() throws IOException {
        Market m = market(); Node own = m.actor.ref("xfm_active_account"), other = m.vm.account("social-other", m.vm.node("social-other-holder", ""), 0);
        Node owed = debt(m.vm, "social-owed", 1, own, other, 200);
        Node claim = debt(m.vm, "social-claim", 2, other, own, 300);
        m.vm.run("xfm_market_ui_debt_pages_effect", m.actor); BigDecimal cash = m.vm.cashStock();
        row(m.vm, 1, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor));
        m.vm.runGui("xfm_market_select_debt_gui", m.actor); assertSame(owed, m.actor.ref("xfm_selected_debt"));
        assertEquals(1000, m.actor.integer("xfm_ui_debt_pay_cents"));
        row(m.vm, 2, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        m.vm.runGui("xfm_market_select_claim_gui", m.actor); assertSame(claim, m.actor.ref("xfm_selected_debt"));
        assertEquals(cash, m.vm.cashStock()); assertEquals(200, owed.integer("xfm_outstanding_cents")); assertEquals(300, claim.integer("xfm_outstanding_cents"));
        Map<String, Datum> before = Map.copyOf(m.actor.vars);
        m.actor.put("xfm_ui_claims_offset", 16); assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor)); m.actor.put("xfm_ui_claims_offset", 0);
        claim.put("xfm_creditor_account", other); assertFalse(m.vm.validGui("xfm_market_select_claim_gui", m.actor)); claim.put("xfm_creditor_account", own);
        own.list("xfm_claims").remove(claim);
        m.vm.execute(m.vm.definition("xfm_market_select_claim_gui").block("effect"), new Frame(m.actor, null, m.actor));
        assertEquals(before, m.actor.vars); assertFalse(m.vm.scopes.containsKey("xfm_ui_item"));
    }
    @Test void debtPagesAreSixteenAndMissingDuplicateOrForeignAccountIdsNeverMutateSelection() throws IOException {
        Market m = market(); Node own = m.actor.ref("xfm_active_account"), other = m.vm.account("debt-pages-other", m.vm.node("debt-pages-holder", ""), 0);
        List<Node> all = new ArrayList<>();
        for (int i = 1; i <= 17; i++) all.add(debt(m.vm, "debt-pages-" + i, i, own, other, 100));
        m.vm.run("xfm_market_ui_debt_pages_effect", m.actor);
        assertEquals(all.subList(0, 16), m.actor.list("xfm_ui_debts_page")); row(m.vm, 17, 0, 1);
        assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        m.vm.runGui("xfm_market_debts_next_gui", m.actor); assertEquals(List.of(all.get(16)), m.actor.list("xfm_ui_debts_page"));
        assertTrue(m.vm.validGui("xfm_market_select_debt_gui", m.actor)); row(m.vm, 1, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        row(m.vm, 17, 0, 1); m.vm.scopes.remove("xfm_ui_row_id"); assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        row(m.vm, 0, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        row(m.vm, 17, 0, 1); Node duplicate = m.vm.node("duplicate-social-debt", "xfm_debt_claim");
        duplicate.put("xfm_debt_id", 17); duplicate.put("xfm_debtor_account", own); m.actor.list("xfm_ui_debts_page").add(duplicate);
        Map<String, Datum> before = Map.copyOf(m.actor.vars); assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        m.vm.execute(m.vm.definition("xfm_market_select_debt_gui").block("effect"), new Frame(m.actor, null, m.actor));
        assertEquals(before, m.actor.vars); m.actor.list("xfm_ui_debts_page").remove(duplicate);
        own.put("xfm_holder", other.ref("xfm_holder")); assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor));
        assertFalse(m.actor.vars.containsKey("xfm_selected_debt"));
    }
    @Test void normalAidButtonAndPagingSelectOnlyThisNewsActorsOutstandingDebts() throws IOException {
        Market m = market(); Node victim = m.vm.node("aid-victim", ""), wallet = m.vm.account("aid-victim-wallet", victim, 0);
        victim.put("xfm_account", wallet); Node creditor = m.actor.ref("xfm_active_account");
        Node news = m.vm.node("aid-news", "xfm_news_entry"); news.put("xfm_news_id", 20); news.put("xfm_news_actor", victim);
        m.actor.put("xfm_selected_news", news); List<Node> all = new ArrayList<>();
        for (int i = 1; i <= 17; i++) all.add(debt(m.vm, "aid-debt-" + i, i, wallet, creditor, 100));
        Node settled = debt(m.vm, "aid-settled", 18, wallet, creditor, 0);
        BigDecimal cash = m.vm.cashStock(); m.vm.runGui("xfm_market_news_aid_gui", m.actor);
        assertEquals(all.subList(0, 16), m.actor.list("xfm_ui_aid_debts")); assertEquals(1, m.actor.integer("xfm_ui_aid_has_next"));
        row(m.vm, 1, 0, 1); m.vm.runGui("xfm_market_select_aid_debt_gui", m.actor); assertSame(all.getFirst(), m.actor.ref("xfm_selected_debt"));
        assertFalse(m.vm.validGui("xfm_market_select_debt_gui", m.actor)); // These are another person's debts, never the player's debt page.
        m.vm.runGui("xfm_market_aid_next_gui", m.actor); assertEquals(List.of(all.get(16)), m.actor.list("xfm_ui_aid_debts"));
        row(m.vm, 1, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_aid_debt_gui", m.actor));
        row(m.vm, 17, 0, 1); m.vm.runGui("xfm_market_select_aid_debt_gui", m.actor); assertSame(all.get(16), m.actor.ref("xfm_selected_debt"));
        row(m.vm, 18, 0, 1); assertFalse(m.vm.validGui("xfm_market_select_aid_debt_gui", m.actor)); assertEquals(0, settled.integer("xfm_outstanding_cents"));
        Node different = m.vm.node("aid-different-news", "xfm_news_entry"); different.put("xfm_news_id", 21); different.put("xfm_news_actor", m.actor);
        m.actor.put("xfm_selected_news", different); row(m.vm, 17, 0, 1);
        assertFalse(m.vm.validGui("xfm_market_select_aid_debt_gui", m.actor)); assertEquals(cash, m.vm.cashStock());
        for (Node d : all) assertEquals(100, d.integer("xfm_outstanding_cents")); assertFalse(m.vm.scopes.containsKey("xfm_ui_item"));
    }
    @Test void publicNewsRowIdsAreBoundToThisCursorAndRejectDuplicateMissingAndWrongTypes() throws IOException {
        Market m = market(); Node news = m.vm.node("journal-row", "xfm_news_entry"); news.put("xfm_news_id", 21);
        m.actor.list("xfm_ui_news").add(news); m.actor.put("xfm_ui_news_before_id", 22); m.actor.put("xfm_ui_news_bound_before_id", 22);
        row(m.vm, 21, 0, 1); m.vm.runGui("xfm_market_select_news_gui", m.actor); assertSame(news, m.actor.ref("xfm_selected_news"));
        Map<String, Datum> before = Map.copyOf(m.actor.vars); assertTrue(m.vm.validGui("xfm_market_select_news_gui", m.actor)); assertEquals(before, m.actor.vars);
        m.actor.put("xfm_ui_news_before_id", 20); assertFalse(m.vm.validGui("xfm_market_select_news_gui", m.actor)); m.actor.put("xfm_ui_news_before_id", 22);
        Node duplicate = m.vm.node("journal-duplicate", "xfm_news_entry"); duplicate.put("xfm_news_id", 21); m.actor.list("xfm_ui_news").add(duplicate);
        assertFalse(m.vm.validGui("xfm_market_select_news_gui", m.actor)); m.actor.list("xfm_ui_news").remove(duplicate);
        Node wrong = m.vm.node("journal-wrong-type", "xfm_debt_claim"); wrong.put("xfm_news_id", 21);
        m.actor.list("xfm_ui_news").clear(); m.actor.list("xfm_ui_news").add(wrong);
        m.vm.execute(m.vm.definition("xfm_market_select_news_gui").block("effect"), new Frame(m.actor, null, m.actor));
        assertEquals(before, m.actor.vars); assertFalse(m.vm.scopes.containsKey("xfm_ui_item"));
    }
    @Test void otcBuyerAccountIdRebindsOnlyThisCoinsCurrentLegalPrimaryHolderPage() throws IOException {
        Market m = market(); Node coin = spotCoin(m.vm, "otc-numeric-coin"); coin.put("xfm_coin_id", 55);
        Node buyer = m.vm.node("otc-actual-buyer", ""), account = m.vm.account("otc-buyer-primary", buyer, 0); account.put("xfm_account_id", 99); buyer.put("xfm_account", account);
        Node holding = spotPosition(m.vm, "otc-holder-position", account, coin, 100);
        m.actor.put("xfm_selected_coin", coin); m.vm.runGui("xfm_market_otc_refresh_gui", m.actor);
        assertEquals(List.of(holding), m.actor.list("xfm_ui_otc_buyers")); assertEquals(0, m.actor.integer("xfm_ui_otc_page_offset"));
        BigDecimal cash = m.vm.cashStock();
        row(m.vm, 99, 0, 1); m.vm.runGui("xfm_market_otc_select_buyer_gui", m.actor);
        assertSame(holding, m.actor.ref("xfm_ui_otc_target_position")); assertSame(account, m.actor.ref("xfm_ui_otc_target_account")); assertSame(buyer, m.actor.ref("xfm_ui_otc_target_buyer"));
        assertEquals(cash, m.vm.cashStock()); assertEquals(100, holding.integer("xfm_quantity_units")); // Selection neither pays nor reserves.
        Map<String, Datum> before = Map.copyOf(m.actor.vars);
        m.actor.put("xfm_ui_otc_offset", 16); assertFalse(m.vm.validGui("xfm_market_otc_select_buyer_gui", m.actor)); m.actor.put("xfm_ui_otc_offset", 0);
        m.actor.put("xfm_selected_coin", m.asset); assertFalse(m.vm.validGui("xfm_market_otc_select_buyer_gui", m.actor)); m.actor.put("xfm_selected_coin", coin);
        account.put("xfm_holder", m.actor); assertFalse(m.vm.validGui("xfm_market_otc_select_buyer_gui", m.actor)); account.put("xfm_holder", buyer);
        buyer.adult = false; assertFalse(m.vm.validGui("xfm_market_otc_select_buyer_gui", m.actor)); buyer.adult = true;
        account.put("xfm_account_frozen", 1); assertFalse(m.vm.validGui("xfm_market_otc_select_buyer_gui", m.actor)); account.put("xfm_account_frozen", 0);
        coin.list("xfm_holders").remove(holding);
        m.vm.execute(m.vm.definition("xfm_market_otc_select_buyer_gui").block("effect"), new Frame(m.actor, null, m.actor));
        assertEquals(before, m.actor.vars); assertFalse(m.vm.scopes.containsKey("xfm_ui_item"));
    }

    @Test void otcRefreshConditionalGuardKeepsMissingAndTerminalCoinsUnavailableWithoutWrites() throws IOException {
        Market m = market(); Node coin = spotCoin(m.vm, "otc-guard-coin"); coin.put("xfm_coin_id", 55);
        Node buyer = m.vm.node("otc-guard-buyer", ""), account = m.vm.account("otc-guard-primary", buyer, 0);
        account.put("xfm_account_id", 99); buyer.put("xfm_account", account);
        Node holding = spotPosition(m.vm, "otc-guard-holding", account, coin, 100);
        BigDecimal cash = m.vm.cashStock();
        m.actor.vars.remove("xfm_selected_coin"); Map<String, Datum> actorBefore = Map.copyOf(m.actor.vars);
        assertFalse(m.vm.validGui("xfm_market_otc_refresh_gui", m.actor)); assertEquals(actorBefore, m.actor.vars);
        m.actor.put("xfm_selected_coin", coin); coin.vars.remove("xfm_listing_state");
        actorBefore = Map.copyOf(m.actor.vars); Map<String, Datum> coinBefore = Map.copyOf(coin.vars);
        assertFalse(m.vm.validGui("xfm_market_otc_refresh_gui", m.actor));
        assertEquals(actorBefore, m.actor.vars); assertEquals(coinBefore, coin.vars);
        coin.put("xfm_listing_state", 7); assertFalse(m.vm.validGui("xfm_market_otc_refresh_gui", m.actor));
        coin.put("xfm_listing_state", 1); assertTrue(m.vm.validGui("xfm_market_otc_refresh_gui", m.actor));
        m.vm.runGui("xfm_market_otc_refresh_gui", m.actor);
        assertEquals(List.of(holding), m.actor.list("xfm_ui_otc_buyers"));
        assertSame(coin, m.actor.ref("xfm_ui_otc_source_coin")); assertEquals(0, m.actor.integer("xfm_ui_otc_page_offset"));
        assertEquals(cash, m.vm.cashStock()); assertEquals(100, holding.integer("xfm_quantity_units"));
        m.actor.ai = true; actorBefore = Map.copyOf(m.actor.vars); coinBefore = Map.copyOf(coin.vars);
        assertFalse(m.vm.validGui("xfm_market_otc_refresh_gui", m.actor));
        assertEquals(actorBefore, m.actor.vars); assertEquals(coinBefore, coin.vars); assertEquals(cash, m.vm.cashStock());
    }

    @Test void failedAccountFactoryCannotFreezeOrImportAnotherBeneficiarysLegacyAssetsAndRetryIsIdempotent() throws IOException {
        Vm v = vm(); Node a = v.node("legacy-owner-a", ""), b = v.node("legacy-owner-b", "");
        Node accountA = v.account("legacy-account-a", a, 777); a.put("xfm_account", accountA);
        Node debtA = v.node("legacy-unrelated-debt-a", "xfm_debt_claim"); debtA.put("xfm_debtor_account", accountA); debtA.put("xfm_outstanding_cents", 345); accountA.list("xfm_debts").add(debtA);
        Node migratedCoin = spotCoin(v, "legacy-migrated-coin"); migratedCoin.put("xfm_coin_id", 55); migratedCoin.put("xfm_supply_units", 200); migratedCoin.put("xfm_legacy_accounted_units", 0);
        Node legacyCoin = v.node("legacy-original-coin", "xfm_a0_coin"); legacyCoin.put("xfm_finance_migrated_coin", migratedCoin);
        Node legacyPosition = v.node("legacy-original-position", "xfm_a0_position"); legacyPosition.put("xfm_coin", legacyCoin);
        legacyPosition.put("xfm_frozen_beneficiary", b); legacyPosition.put("xfm_quantity", 200);
        v.scopes.put("xfm_account", accountA); v.failType = "xfm_finance_account"; BigDecimal cash = v.cashStock();
        v.run("xfm_finance_ensure_account_effect", b);
        assertFalse(v.scopes.containsKey("xfm_account")); assertFalse(b.vars.containsKey("xfm_account"));
        v.scopes.put("xfm_account", accountA); v.run("xfm_finance_import_a0_position_effect", legacyPosition);
        assertFalse(v.scopes.containsKey("xfm_account")); assertEquals(0, v.created("xfm_finance_position"));
        assertEquals(0, accountA.integer("xfm_account_frozen")); assertEquals(0, accountA.integer("xfm_inheritance_state"));
        assertTrue(accountA.list("xfm_positions").isEmpty()); assertEquals(777, accountA.integer("xfm_free_cents"));
        assertEquals(List.of(debtA), accountA.list("xfm_debts")); assertSame(accountA, debtA.ref("xfm_debtor_account")); assertEquals(345, debtA.integer("xfm_outstanding_cents"));
        assertFalse(legacyPosition.vars.containsKey("xfm_finance_imported")); assertEquals(0, migratedCoin.integer("xfm_legacy_accounted_units")); assertEquals(1, v.exchange.integer("xfm_a0_import_errors")); assertEquals(cash, v.cashStock());
        v.failType = ""; v.run("xfm_finance_import_a0_position_effect", legacyPosition);
        Node accountB = b.ref("xfm_account"), imported = legacyPosition.ref("xfm_finance_migrated_position");
        assertNotNull(accountB); assertNotSame(accountA, accountB); assertSame(b, accountB.ref("xfm_holder")); assertSame(accountB, imported.ref("xfm_account"));
        assertEquals(1, accountB.integer("xfm_account_frozen")); assertEquals(2, accountB.integer("xfm_inheritance_state"));
        assertEquals(200, imported.integer("xfm_quantity_units")); assertEquals(200, migratedCoin.integer("xfm_legacy_accounted_units"));
        assertEquals(1, legacyPosition.integer("xfm_finance_imported")); assertEquals(1, v.created("xfm_finance_position"));
        v.run("xfm_finance_import_a0_position_effect", legacyPosition);
        assertEquals(200, imported.integer("xfm_quantity_units")); assertEquals(200, migratedCoin.integer("xfm_legacy_accounted_units"));
        assertEquals(1, v.created("xfm_finance_position")); assertEquals(cash, v.cashStock()); assertSame(a, accountA.ref("xfm_holder"));
    }
    @Test void actualMakerFollowsPoliticalControllerAndCannotFillItsNewControllersOwnOrder() throws IOException {
        Vm v = vm(); Node a = v.node("maker-controller-a", ""), b = v.node("maker-controller-b", ""), external = v.node("maker-independent-buyer", "");
        Node coin = spotCoin(v, "political-maker-coin"); coin.put("xfm_coin_id", 55); coin.put("xfm_last_price_cents", 100); coin.put("xfm_entity_type", 4); coin.put("xfm_controller", a);
        Node title = v.node("maker-bound-title", "landed_title"); title.links.put("holder", a); coin.put("xfm_bound_entity", title);
        Node issuer = v.account("maker-project", a, 0), maker = v.account("maker-dedicated", a, 1000);
        issuer.put("xfm_system_account", 1); maker.put("xfm_system_account", 1); issuer.put("xfm_legal_entity", coin); maker.put("xfm_legal_entity", coin);
        coin.put("xfm_issuer_account", issuer); coin.put("xfm_market_maker_account", maker);
        Node inventory = spotPosition(v, "maker-inventory", maker, coin, 300);
        v.run("xfm_spot_maker_effect", coin);
        assertEquals(2, maker.list("xfm_orders").size());
        Node ask = maker.list("xfm_orders").stream().filter(o -> o.integer("xfm_side") == 2).findFirst().orElseThrow();
        assertEquals(1, ask.integer("xfm_is_maker_quote")); assertEquals(105, ask.integer("xfm_limit_cents")); assertEquals(100, inventory.integer("xfm_reserved_units"));
        title.links.put("holder", b); v.run("xfm_issuer_refresh_controller_effect", coin);
        assertSame(b, coin.ref("xfm_controller")); assertSame(b, maker.ref("xfm_holder")); assertSame(b, maker.ref("xfm_beneficial_owner")); assertSame(b, issuer.ref("xfm_beneficial_owner"));
        Node own = v.account("maker-controller-b-private", b, 1000); b.put("xfm_account", own);
        BigDecimal cash = v.cashStock(); Node ownBuy = spotSubmit(v, own, coin, 1, 1, 105, false);
        assertNotNull(ownBuy); assertEquals(0, ownBuy.integer("xfm_filled_lots")); assertEquals(1, ownBuy.integer("xfm_remaining_lots"));
        assertEquals(1, ask.integer("xfm_status")); assertEquals(1, ask.integer("xfm_remaining_lots")); assertTrue(v.spotExecutionOrderIds.isEmpty());
        assertEquals(300, inventory.integer("xfm_quantity_units")); assertEquals(0, v.exchange.integer("xfm_fee_cents")); assertEquals(cash, v.cashStock());
        Node outsider = v.account("maker-independent-wallet", external, 1000); external.put("xfm_account", outsider);
        cash = v.cashStock(); Node externalBuy = spotSubmit(v, outsider, coin, 1, 1, 105, false);
        assertNotNull(externalBuy); assertEquals(1, externalBuy.integer("xfm_filled_lots")); assertEquals(2, ask.integer("xfm_status"));
        assertEquals(List.of(ask.integer("xfm_order_id")), v.spotExecutionOrderIds); assertEquals(200, inventory.integer("xfm_quantity_units"));
        assertEquals(0, ownBuy.integer("xfm_filled_lots")); assertEquals(1, ownBuy.integer("xfm_remaining_lots")); assertEquals(cash, v.cashStock());
    }
    @Test void makerCashWithdrawalUsesThirtyTwoRealBoundedTransfersThenTheActualDailyPendingBranchExactlyOnce() throws IOException {
        Vm v = vm(); Node owner = v.node("large-maker-controller", ""), coin = spotCoin(v, "large-maker-coin"); coin.put("xfm_controller", owner);
        Node maker = v.account("large-maker-wallet", owner, 3_200_000_123L), issuer = v.account("large-maker-project", owner, 7);
        maker.put("xfm_system_account", 1); issuer.put("xfm_system_account", 1);
        maker.put("xfm_legal_entity", coin); issuer.put("xfm_legal_entity", coin);
        coin.put("xfm_market_maker_account", maker); coin.put("xfm_issuer_account", issuer);
        BigDecimal cash = v.cashStock(); v.run("xfm_spot_withdraw_maker_effect", coin);
        assertEquals(123, maker.integer("xfm_free_cents")); assertEquals(3_200_000_007L, issuer.integer("xfm_free_cents"));
        assertEquals(1, coin.integer("xfm_maker_withdrawn")); assertEquals(1, coin.integer("xfm_maker_withdrawal_pending"));
        assertEquals(32, v.effectCalls.getOrDefault("xfm_finance_transfer_effect", 0));
        assertEquals(32, v.cashTransferRequests.size()); assertTrue(v.cashTransferRequests.stream().allMatch(n -> n == 100_000_000L));
        assertEquals(cash, v.cashStock());
        // Use the unchanged actual if Entry inside the registry loop, not an authored replacement predicate/body.
        List<Block> loops = v.definition("xfm_spot_daily_effect").named("every_in_global_list").stream().map(e -> (Block)e.value())
                .filter(b -> atom(field(b, "variable")).equals("xfm_coin_registry")).toList();
        assertEquals(1, loops.size());
        List<Entry> originalBranches = loops.getFirst().named("if").stream()
                .filter(e -> ((Block)e.value()).named("xfm_spot_withdraw_maker_effect").size() == 1).toList();
        assertEquals(1, originalBranches.size());
        Block actualPendingBranch = new Block(originalBranches); int withdrawalsBefore = v.effectCalls.getOrDefault("xfm_spot_withdraw_maker_effect", 0);
        v.execute(actualPendingBranch, new Frame(coin, v.exchange, v.exchange));
        assertEquals(withdrawalsBefore + 1, v.effectCalls.getOrDefault("xfm_spot_withdraw_maker_effect", 0));
        assertEquals(0, maker.integer("xfm_free_cents")); assertEquals(3_200_000_130L, issuer.integer("xfm_free_cents")); assertEquals(0, coin.integer("xfm_maker_withdrawal_pending"));
        assertEquals(33, v.effectCalls.getOrDefault("xfm_finance_transfer_effect", 0)); assertEquals(123L, v.cashTransferRequests.getLast().longValue()); assertEquals(cash, v.cashStock());
        v.execute(actualPendingBranch, new Frame(coin, v.exchange, v.exchange));
        assertEquals(withdrawalsBefore + 1, v.effectCalls.getOrDefault("xfm_spot_withdraw_maker_effect", 0));
        assertEquals(33, v.effectCalls.getOrDefault("xfm_finance_transfer_effect", 0)); assertEquals(0, maker.integer("xfm_free_cents")); assertEquals(3_200_000_130L, issuer.integer("xfm_free_cents")); assertEquals(cash, v.cashStock());
    }


    @Test void capacityRulesReachActualSpotAdmissionAndCancelledSlotsRecover() throws IOException {
        for (String rule : List.of("xfm_capacity_conservative", "xfm_capacity_standard", "xfm_capacity_extended")) {
            Vm v = vm(); v.rules.add(rule); Node coin = spotCoin(v, "depth-coin");
            int depth = rule.equals("xfm_capacity_conservative") ? 32 : rule.equals("xfm_capacity_extended") ? 128 : 64;
            assertEquals(depth, v.integerValue("xfm_config_detailed_book_capacity_value", coin));
            assertEquals(depth, v.integerValue("xfm_config_coin_order_capacity_value", coin));
            assertEquals(64, v.integerValue("xfm_config_spot_match_fill_budget_value", coin));
            assertEquals(128, v.integerValue("xfm_config_book_service_capacity_value", coin));
            List<Node> orders = fillSpotDepth(v, coin, depth, 87);
            Node extra = v.account("extra", v.node("extra-holder", ""), 88); BigDecimal cash = v.cashStock();
            int created = v.created("xfm_spot_order");
            assertNull(spotSubmit(v, extra, coin, 1, 1, 87, false));
            assertEquals(0, extra.integer("xfm_result")); assertEquals(88, extra.integer("xfm_free_cents"));
            assertEquals(0, extra.integer("xfm_reserved_cents")); assertEquals(created, v.created("xfm_spot_order"));
            assertEquals(orders, coin.list("xfm_spot_orders")); assertEquals(cash, v.cashStock());
            Node removed = orders.getLast(); v.run("xfm_spot_cancel_order_effect", removed);
            assertEquals(3, removed.integer("xfm_status")); assertEquals(0, removed.ref("xfm_reservation").integer("xfm_remaining_cents"));
            assertNotNull(spotSubmit(v, extra, coin, 1, 1, 87, false));
            assertEquals(depth, coin.integer("xfm_open_orders_count")); assertEquals(depth, coin.list("xfm_spot_orders").size());
            assertEquals(cash, v.cashStock());
        }
    }
    @Test void loweringSpotDepthPreservesOldBookAndOriginalFillWorkReturningOnlyNewRemainder() throws IOException {
        for (boolean ioc : List.of(false, true)) {
            Vm v = vm(); v.rules.add("xfm_capacity_extended"); Node coin = spotCoin(v, "depth-coin");
            List<Node> old = fillSpotDepth(v, coin, 128, 87);
            Node seller = v.account("seller", v.node("seller-holder", ""), 0);
            Node position = spotPosition(v, "position", seller, coin, 8000);
            BigDecimal cash = v.cashStock(); long supply = spotSupply(v, coin);
            v.rules.clear(); v.rules.add("xfm_capacity_conservative");
            assertEquals(old, coin.list("xfm_spot_orders"));
            Node sell = spotSubmit(v, seller, coin, 2, 71, 20, ioc);
            assertNotNull(sell); assertEquals(1, seller.integer("xfm_result"));
            assertEquals(64, sell.integer("xfm_filled_lots")); assertEquals(7, sell.integer("xfm_cancelled_lots"));
            assertEquals(ioc ? 0 : 7, sell.integer("xfm_capacity_cancelled_lots"));
            assertEquals(3, sell.integer("xfm_status")); assertEquals(0, sell.integer("xfm_indexed"));
            assertEquals(old.subList(64, 128), coin.list("xfm_spot_orders"));
            assertEquals(old.subList(0, 64).stream().map(o -> o.integer("xfm_order_id")).toList(), v.spotExecutionOrderIds);
            assertEquals(64, v.maxSpotMatchIterations); assertEquals(128, v.maxSpotBookEntries);
            assertEquals(1600, position.integer("xfm_quantity_units")); assertEquals(0, position.integer("xfm_reserved_units"));
            assertEquals(cash, v.cashStock()); assertEquals(supply, spotSupply(v, coin));
            Node tail = old.getLast(); v.run("xfm_spot_cancel_order_effect", tail);
            assertEquals(3, tail.integer("xfm_status")); assertEquals(0, tail.ref("xfm_reservation").integer("xfm_remaining_cents"));
            assertEquals(63, coin.list("xfm_spot_orders").size()); assertEquals(cash, v.cashStock());
        }
    }
    @Test void lowerRuleStillProjectsBestOldFuturesOrderBeyondFirstThirtyTwoEntries() throws IOException {
        Market m = market(); m.vm.rules.add("xfm_capacity_extended"); Node best = null;
        for (int i = 0; i < 128; i++) best = quote(m, "old-" + i, m.contract, 1, i == 127 ? 109 : 100, 1, i + 1);
        m.vm.rules.clear(); m.vm.rules.add("xfm_capacity_conservative");
        refresh(m); assertSame(best, bids(m).getFirst()); assertEquals(5, bids(m).size());
        assertEquals(128, m.actor.integer("xfm_ui_futures_bid_lots")); assertEquals(128, m.contract.list("xfm_orders").size());
        assertTrue(m.actor.list("xfm_ui_futures_candidates").isEmpty()); assertEquals(0, m.vm.historyVisits);
    }
    @Test void extendedBookSettingKeepsActualAccountAndGlobalAdmissionLimits() throws IOException {
        Vm v = vm(); v.rules.add("xfm_capacity_extended"); Node coin = spotCoin(v, "depth-coin");
        Node account = v.account("account", v.node("holder", ""), 66);
        for (int i = 0; i < 32; i++) assertNotNull(spotSubmit(v, account, coin, 1, 1, 1, false));
        int created = v.created("xfm_spot_order"); assertNull(spotSubmit(v, account, coin, 1, 1, 1, false));
        assertEquals(created, v.created("xfm_spot_order")); assertEquals(32, account.integer("xfm_open_orders_count"));
        assertEquals(2, account.integer("xfm_free_cents")); assertEquals(64, account.integer("xfm_reserved_cents"));
        Node other = v.account("other", v.node("other-holder", ""), 2);
        v.exchange.put("xfm_active_orders_count", 8192);
        assertNull(spotSubmit(v, other, coin, 1, 1, 1, false)); assertEquals(0, other.integer("xfm_reserved_cents"));
        assertEquals(32, v.integerValue("xfm_config_player_order_capacity_value", account));
        assertEquals(8192, v.integerValue("xfm_config_global_order_capacity_value", account));
        assertEquals(created, v.created("xfm_spot_order")); assertEquals(32, coin.list("xfm_spot_orders").size());
    }
    private static List<Node> fillSpotDepth(Vm v, Node coin, int depth, int price) {
        List<Node> result = new ArrayList<>();
        for (int i = 0; i < depth; i++) {
            Node a = v.account("depth-account-" + i, v.node("depth-holder-" + i, ""), price + 1L);
            Node order = spotSubmit(v, a, coin, 1, 1, price, false); assertNotNull(order); result.add(order);
        }
        assertEquals(depth, coin.list("xfm_spot_orders").size()); return result;
    }

    @Test void openingCreateCancelLoopStopsAtActualDailyAllocationCostAndKeepsEveryRefund() throws IOException {
        Vm v = vm(); Node actor = openingTicket(v); BigDecimal cash = v.cashStock();
        for (int i = 0; i < 512; i++) {
            v.run("xfm_futures_submit_effect", actor); assertEquals(1, actor.integer("xfm_futures_result"), "allocation " + i);
            Node order = (Node)v.scopes.get("xfm_fut_incoming"); assertNotNull(order);
            v.run("xfm_futures_cancel_order_effect", order);
            assertEquals(3, order.integer("xfm_status")); assertEquals(0, order.ref("xfm_reservation").integer("xfm_remaining_cents"));
        }
        assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(512, v.created("xfm_futures_order"));
        assertEquals(512, v.created("xfm_finance_reservation")); assertEquals(512, v.exchange.integer("xfm_futures_archive_count"));
        assertEquals(0, actor.ref("xfm_account").integer("xfm_reserved_cents")); assertEquals(cash, v.cashStock());
        int nodes = v.nodes.size(); v.run("xfm_futures_submit_effect", actor);
        assertEquals(0, actor.integer("xfm_futures_result")); assertEquals(8, actor.integer("xfm_futures_reason")); assertEquals(nodes, v.nodes.size());
        Node other = v.node("other-player", ""); other.ai = false; other.vars.putAll(actor.vars);
        Node otherWallet = v.account("other-private", other, 10000); other.put("xfm_account", otherWallet); other.put("xfm_active_account", otherWallet);
        v.run("xfm_futures_submit_effect", other); assertEquals(0, other.integer("xfm_futures_result")); assertEquals(nodes + 2, v.nodes.size(), "changing actor cannot bypass the exchange-wide budget");
    }

    @Test void oldExchangeUnknownEarlierWorkSealsActivationDayThenRealFinancialDayRestoresAllowance() throws IOException {
        Vm v = vm(); Node actor = openingTicket(v);
        for (String key : List.of("xfm_futures_opening_budget_v1", "xfm_futures_opening_budget_day", "xfm_futures_opening_allocated_today")) v.exchange.vars.remove(key);
        v.exchange.vars.remove("xfm_futures_archive_count"); // Actual absent queue header; no claim that unrelated old stories are absent.
        v.run("xfm_futures_submit_effect", actor); assertEquals(0, actor.integer("xfm_futures_result")); assertEquals(0, v.created("xfm_futures_order"));
        assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(1, v.exchange.integer("xfm_futures_opening_budget_day"));
        assertEquals(0, v.exchange.integer("xfm_futures_archive_count"));
        v.run("xfm_futures_submit_effect", actor); assertEquals(0, v.created("xfm_futures_order"), "same-day retry has no fresh allowance");
        v.exchange.put("xfm_day", 2); actor.ref("xfm_selected_coin").put("xfm_oracle_day", 2);
        v.run("xfm_futures_submit_effect", actor); assertEquals(1, actor.integer("xfm_futures_result")); assertEquals(1, v.exchange.integer("xfm_futures_opening_allocated_today"));
        assertEquals(2, v.exchange.integer("xfm_futures_opening_budget_day"));
    }

    @Test void missingPartialMalformedAndRollbackBudgetOrQueueSourcesFailBeforeAllocation() throws IOException {
        for (String mode : List.of("partial", "missing-archive", "negative-used", "fractional-used", "future-day", "unknown-version", "negative-archive", "fractional-archive", "orphan-head", "missing-head")) {
            Vm v = vm(); Node actor = openingTicket(v); BigDecimal cash = v.cashStock();
            switch (mode) {
                case "partial" -> v.exchange.vars.remove("xfm_futures_opening_allocated_today");
                case "missing-archive" -> { v.exchange.vars.remove("xfm_futures_archive_count"); Node head = v.node("unknown-head", "xfm_futures_order"); v.exchange.put("xfm_futures_archive_head", head); v.exchange.put("xfm_futures_archive_tail", head); }
                case "negative-used" -> v.exchange.put("xfm_futures_opening_allocated_today", -1);
                case "fractional-used" -> v.exchange.vars.put("xfm_futures_opening_allocated_today", new NumberDatum(new BigDecimal("0.5")));
                case "future-day" -> v.exchange.put("xfm_futures_opening_budget_day", 2);
                case "unknown-version" -> v.exchange.put("xfm_futures_opening_budget_v1", 2);
                case "negative-archive" -> v.exchange.put("xfm_futures_archive_count", -1);
                case "fractional-archive" -> v.exchange.vars.put("xfm_futures_archive_count", new NumberDatum(new BigDecimal("0.5")));
                case "orphan-head" -> v.exchange.put("xfm_futures_archive_head", v.node("orphan", "xfm_futures_order"));
                case "missing-head" -> v.exchange.put("xfm_futures_archive_count", 1);
                default -> throw new AssertionError(mode);
            }
            v.run("xfm_futures_submit_effect", actor); assertEquals(0, actor.integer("xfm_futures_result"), mode);
            assertEquals(0, v.created("xfm_futures_order"), mode); assertEquals(0, v.created("xfm_finance_reservation"), mode); assertEquals(cash, v.cashStock(), mode);
        }
    }

    @Test void actualFailedOrderAllocationCostsNothingButFailedReservationDoesNotRefundAllocatedWork() throws IOException {
        Vm v = vm(); Node actor = openingTicket(v); BigDecimal cash = v.cashStock(); v.failType = "xfm_futures_order";
        v.run("xfm_futures_submit_effect", actor); assertEquals(0, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(0, v.created("xfm_futures_order"));
        v.failType = "xfm_finance_reservation"; v.run("xfm_futures_submit_effect", actor);
        assertEquals(1, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(1, v.created("xfm_futures_order"));
        assertTrue(v.nodes.values().stream().filter(n -> n.type.equals("xfm_futures_order")).allMatch(n -> n.ended));
        assertEquals(0, actor.ref("xfm_account").integer("xfm_reserved_cents")); assertEquals(cash, v.cashStock());
        assertEquals(0, v.exchange.integer("xfm_next_futures_order_id"), "physical allocation cost is independent of the permanent accepted-order id");
    }

    @Test void sameDayArchiveBackpressurePreservesNodesAndNextDayUsesOnlySixtyFourRealPruneSteps() throws IOException {
        Vm v = vm(); Node actor = openingTicket(v); List<Node> archive = archiveChain(v, actor.ref("xfm_account"), 4096, false); BigDecimal cash = v.cashStock();
        v.run("xfm_futures_submit_effect", actor); assertEquals(0, actor.integer("xfm_futures_result")); assertEquals(8, actor.integer("xfm_futures_reason"));
        assertEquals(0, v.created("xfm_futures_order")); assertEquals(4096, v.exchange.integer("xfm_futures_archive_count"));
        assertTrue(archive.stream().noneMatch(n -> n.ended)); assertEquals(64, v.maxArchivePruneIterations);
        v.exchange.put("xfm_day", 2); actor.ref("xfm_selected_coin").put("xfm_oracle_day", 2);
        v.run("xfm_futures_submit_effect", actor); assertEquals(1, actor.integer("xfm_futures_result"));
        assertEquals(4032, v.exchange.integer("xfm_futures_archive_count")); assertEquals(64, archive.stream().filter(n -> n.ended).count());
        assertEquals(64, v.maxArchivePruneIterations); assertEquals(cash, v.cashStock());
    }

    @Test void pruneKeepsProtectedClaimSourcesResidentAndQueueCountIsNotMisreportedAsTotalStories() throws IOException {
        Vm v = vm(); Node actor = openingTicket(v); List<Node> archive = archiveChain(v, actor.ref("xfm_account"), 4096, true);
        v.run("xfm_futures_submit_effect", actor); assertEquals(1, actor.integer("xfm_futures_result")); assertEquals(4032, v.exchange.integer("xfm_futures_archive_count"));
        assertEquals(64, archive.stream().filter(n -> n.integer("xfm_futures_archive_retained") == 1).count());
        assertTrue(archive.stream().noneMatch(n -> n.ended), "dequeueing a protected source never frees or rewrites that source");
    }

    @Test void exhaustedOpeningAllowanceStillAllowsActualReduceReservationAndCancelRefund() throws IOException {
        Market m = market(); Vm v = m.vm; Node own = m.actor.ref("xfm_account"), other = v.account("counterparty", v.node("counterparty-holder", ""), 1000);
        Node p = v.node("existing-position", "xfm_futures_position"); p.put("xfm_contract", m.contract); p.put("xfm_long_account", own); p.put("xfm_short_account", other);
        p.put("xfm_long_reservation", v.node("existing-long-margin", "xfm_finance_reservation")); p.put("xfm_short_reservation", v.node("existing-short-margin", "xfm_finance_reservation"));
        p.put("xfm_status", 0); p.put("xfm_lots", 3); m.actor.put("xfm_futures_selected_position", p); m.actor.put("xfm_futures_reduce_lots", 1); m.actor.put("xfm_futures_limit_cents", 100);
        v.exchange.put("xfm_futures_opening_allocated_today", 512); BigDecimal cash = v.cashStock();
        v.run("xfm_futures_reduce_effect", m.actor); assertEquals(1, m.actor.integer("xfm_futures_result")); Node close = (Node)v.scopes.get("xfm_fut_incoming");
        assertNotNull(close); assertSame(p, close.ref("xfm_close_position")); assertEquals(1, close.integer("xfm_reduce_order"));
        assertEquals(512, v.exchange.integer("xfm_futures_opening_allocated_today")); assertEquals(0, v.effectCalls.getOrDefault("xfm_futures_prepare_opening_admission_effect", 0));
        v.run("xfm_futures_cancel_order_effect", close); assertEquals(0, close.ref("xfm_reservation").integer("xfm_remaining_cents")); assertEquals(cash, v.cashStock());
    }

    @Test void permanentIdDoesNotActAsCapacityAndFreshDefaultsComeFromActualBootstrapFragment() throws IOException {
        Vm v = vm(); Node actor = openingTicket(v);
        Block first = (Block)field(v.definition("xfm_finance_bootstrap_effect"), "if"), created = (Block)field(first, "if");
        Block initialization = (Block)field(created, "scope:xfm_fin_new_exchange");
        Set<String> names = Set.of("xfm_futures_archive_count", "xfm_futures_opening_budget_v1", "xfm_futures_opening_budget_day", "xfm_futures_opening_allocated_today");
        List<Entry> actual = initialization.entries().stream().filter(e -> e.key().equals("set_variable") && names.contains(atom(field((Block)e.value(), "name")))).toList();
        assertEquals(4, actual.size()); v.execute(new Block(actual), new Frame(v.exchange, null, v.exchange));
        assertEquals(1, v.exchange.integer("xfm_futures_opening_budget_v1")); assertEquals(0, v.exchange.integer("xfm_futures_opening_budget_day"));
        v.exchange.put("xfm_next_futures_order_id", 1_000_000); v.run("xfm_futures_submit_effect", actor);
        assertEquals(1, actor.integer("xfm_futures_result")); assertEquals(1_000_001, v.exchange.integer("xfm_next_futures_order_id")); assertEquals(1, v.exchange.integer("xfm_futures_opening_allocated_today"));
        v.run("xfm_finance_bootstrap_effect", actor); assertEquals(1, v.exchange.integer("xfm_futures_opening_allocated_today"), "loading an existing exchange must not reset its allowance");
    }

    private static Node openingTicket(Vm v) {
        Node actor = ticket(v, "0.00"); actor.ai = false; Node wallet = primary(v, actor, 10000); actor.put("xfm_active_account", wallet); return actor;
    }
    private static List<Node> archiveChain(Vm v, Node account, int count, boolean protectedClaim) {
        List<Node> result = new ArrayList<>(); Node claim = protectedClaim ? v.node("retained-debt-receipt", "xfm_debt_claim") : null;
        for (int i = 0; i < count; i++) {
            Node n = v.node("old-archive-" + i, "xfm_futures_order"); n.put("xfm_order_id", i + 1); n.put("xfm_archived_day", protectedClaim ? 0 : 1); n.put("xfm_futures_archive_queued", 1); n.put("xfm_account", account);
            if (claim != null) n.put("xfm_debt_receipt_1", claim); if (!result.isEmpty()) result.getLast().put("xfm_futures_archive_next", n); result.add(n); account.list("xfm_futures_order_history").add(n);
        }
        v.exchange.put("xfm_futures_archive_count", count); v.exchange.put("xfm_futures_archive_head", result.getFirst()); v.exchange.put("xfm_futures_archive_tail", result.getLast()); return result;
    }

    private static Node spotCoin(Vm v, String id) {
        Node c = v.node(id, "xfm_finance_coin"); c.put("xfm_listing_state", 1); c.put("xfm_trading_open", 1);
        c.put("xfm_controller", v.node(id + "-controller", "")); c.put("xfm_open_orders_count", 0); c.put("xfm_supply_units", 0); return c;
    }
    private static Node spotPosition(Vm v, String id, Node account, Node coin, long units) {
        Node p = v.node(id, "xfm_finance_position"); p.put("xfm_account", account); p.put("xfm_coin", coin);
        p.put("xfm_quantity_units", units); p.put("xfm_reserved_units", 0); p.put("xfm_counted", 1);
        account.list("xfm_positions").add(p); coin.list("xfm_holders").add(p);
        if (units > 0) account.put("xfm_holdings_count", account.integer("xfm_holdings_count") + 1);
        coin.put("xfm_supply_units", coin.integer("xfm_supply_units") + units); return p;
    }
    private static Node spotSubmit(Vm v, Node account, Node coin, int side, int lots, int price, boolean ioc) {
        account.put("xfm_selected_coin", coin); account.put("xfm_order_side", side); account.put("xfm_order_lots", lots);
        account.put("xfm_order_limit_cents", price); account.put("xfm_order_ioc", ioc ? 1 : 0);
        v.run("xfm_spot_submit_account_effect", account); return account.ref("xfm_result_order");
    }
    private static List<Node> fillSpotBook(Vm v, Node coin, int side, int price) {
        return fillSpotBook(v, coin, side, price, 1);
    }
    private static List<Node> fillSpotBook(Vm v, Node coin, int side, int price, int firstLots) {
        List<Node> orders = new ArrayList<>();
        for (int i = 0; i < 64; i++) {
            int lots = i == 0 ? firstLots : 1; long gross = (long)lots * price, required = gross + (gross * 3 + 999) / 1000;
            Node a = v.account("spot-" + side + "-" + i + "-account", v.node("spot-" + side + "-" + i + "-holder", ""), side == 1 ? required : 0);
            if (side == 2) spotPosition(v, "spot-sell-position-" + i, a, coin, 100L * lots);
            Node o = spotSubmit(v, a, coin, side, lots, price, false); assertNotNull(o); orders.add(o);
        }
        assertEquals(64, coin.list("xfm_spot_orders").size()); return orders;
    }
    private static long spotSupply(Vm v, Node coin) {
        return v.nodes.values().stream().filter(n -> n.type.equals("xfm_finance_position") && n.ref("xfm_coin") == coin)
                .mapToLong(n -> n.integer("xfm_quantity_units")).sum();
    }
    private static Node ticket(Vm v, String gold) {
        Node a = v.node("actor", ""); a.gold = new BigDecimal(gold);
        Node asset = v.asset("asset"), contract = v.contract("ticket-contract", asset, 1, 0);
        a.put("xfm_selected_coin", asset); a.put("xfm_futures_contract", contract);
        a.put("xfm_futures_perpetual", 1); a.put("xfm_futures_expiry_day", 0);
        a.put("xfm_futures_side", 1); a.put("xfm_futures_leverage", 1);
        a.put("xfm_futures_limit_cents", 100); a.put("xfm_futures_lots", 1);
        return a;
    }
    private static Node primary(Vm v, Node actor, int free) { Node p = v.account("private", actor, free); actor.put("xfm_account", p); return p; }
    private sealed interface Datum permits NumberDatum, TextDatum, Node { }
    private record NumberDatum(BigDecimal value) implements Datum { }
    private record TextDatum(String text) implements Datum { }
    private static final class Node implements Datum {
        final String id, type;
        final Map<String, Datum> vars = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new HashMap<>();
        final Set<String> flags = new HashSet<>(); // Explicit engine-owned window flag input, not a finance/business effect.
        final Set<String> traits = new HashSet<>(); final Map<String, Node> links = new HashMap<>();
        BigDecimal gold = BigDecimal.ZERO; Node owner; boolean ai = true, alive = true, adult = true, ended;
        Node(String id, String type) { this.id = id; this.type = type; }
        void put(String name, long value) { vars.put(name, new NumberDatum(BigDecimal.valueOf(value))); }
        void put(String name, Node value) { vars.put(name, value); }
        long integer(String name) { Datum d = vars.get(name); return d == null ? 0 : ((NumberDatum) d).value().longValueExact(); }
        Node ref(String name) { return (Node) vars.get(name); }
        List<Node> list(String name) { return lists.computeIfAbsent(name, ignored -> new ArrayList<>()); }
    }
    private record Frame(Node here, Node previous, Node root) { Frame enter(Node node) { return new Frame(node, here, root); } }
    private static final class Vm {
        final Map<String, Block> program; final Map<String, Node> nodes = new LinkedHashMap<>();
        final Map<String, Datum> scopes = new HashMap<>();
        final Set<String> rules = new HashSet<>(); // Explicit engine rule selection; numeric values execute production AST.
        final Map<String, List<Node>> globalLists = new HashMap<>();
        final Map<String, List<Node>> temporaryLists = new HashMap<>();
        final Map<String, Integer> effectCalls = new HashMap<>();
        final List<Long> cashTransferRequests = new ArrayList<>();
        final Node exchange, custodian;
        final List<String> trace = new ArrayList<>(); String failType = ""; boolean open = true, randomEnabled = true; int sequence, matchCalls, historyVisits, maxDiscoveryEntries;
        final List<Long> spotExecutionOrderIds = new ArrayList<>(); int maxSpotBookEntries, maxSpotMatchIterations;
        int maxUiPageEntries;
        int maxArchivePruneIterations;
        Vm(Map<String, Block> program) {
            this.program = program; custodian = node("technical-owner", ""); exchange = node("exchange", "xfm_finance_exchange"); exchange.owner = custodian;
            exchange.put("xfm_day", 1); exchange.put("xfm_ai_seeded", 1); exchange.put("xfm_next_account_id", 0); exchange.put("xfm_next_reservation_id", 0);
            exchange.put("xfm_next_futures_contract_id", 0); exchange.put("xfm_next_futures_position_id", 0);
            exchange.put("xfm_active_orders_count", 0); exchange.put("xfm_futures_open_positions_count", 0);
            exchange.put("xfm_futures_archive_count", 0); exchange.put("xfm_futures_opening_budget_v1", 1);
            exchange.put("xfm_futures_opening_budget_day", 1); exchange.put("xfm_futures_opening_allocated_today", 0); // Fresh bootstrap, advanced to fixture day1.
            exchange.put("xfm_order_stories_count", 0); // Actual finance bootstrap initializes the physical spot-story admission counter.
        }
        Node node(String id, String type) {
            Node n = new Node(id, type); if (nodes.putIfAbsent(id, n) != null) throw new IllegalArgumentException("duplicate node " + id); return n;
        }
        Node asset(String id) {
            Node a = node(id, "xfm_oracle_index"); a.put("xfm_mark_cents", 100); a.put("xfm_index_cents", 100);
            a.put("xfm_oracle_quality", 3); a.put("xfm_oracle_day", exchange.integer("xfm_day")); a.put("xfm_max_leverage", 5);
            a.put("xfm_derivatives_reduce_only", 0); return a;
        }
        Node account(String id, Node holder, long free) {
            Node a = node(id, "xfm_finance_account"); a.owner = custodian; a.put("xfm_holder", holder); a.put("xfm_beneficial_owner", holder);
            a.put("xfm_free_cents", free); a.put("xfm_reserved_cents", 0); a.put("xfm_account_frozen", 0);
            a.put("xfm_system_account", 0); a.put("xfm_inheritance_state", 0); a.put("xfm_open_orders_count", 0); a.put("xfm_open_positions_count", 0); return a;
        }
        Node contract(String id, Node asset, long perpetual, long expiry) {
            Node c = node(id, "xfm_futures_contract"); c.owner = custodian; c.put("xfm_coin", asset); c.put("xfm_status", 0);
            c.put("xfm_perpetual", perpetual); c.put("xfm_expiry_day", expiry); c.put("xfm_open_orders_count", 0); return c;
        }
        void order(String id, Node contract, Node account, int side, int price) {
            Node r = node(id + "-reservation", "xfm_finance_reservation"); r.put("xfm_account", account); r.put("xfm_status", 1); r.put("xfm_remaining_cents", 121);
            account.put("xfm_reserved_cents", account.integer("xfm_reserved_cents") + 121);
            Node o = node(id, "xfm_futures_order"); o.put("xfm_contract", contract); o.put("xfm_account", account); o.put("xfm_reservation", r);
            o.put("xfm_status", 0); o.put("xfm_remaining_lots", 1); o.put("xfm_side", side); o.put("xfm_limit_cents", price);
            contract.list("xfm_orders").add(o); contract.put("xfm_open_orders_count", contract.integer("xfm_open_orders_count") + 1);
        }
        int created(String type) { return (int) nodes.values().stream().filter(n -> n.id.startsWith("created-") && n.type.equals(type)).count(); }
        BigDecimal cashStock() {
            BigDecimal sum = BigDecimal.ZERO;
            for (Node n : nodes.values()) {
                sum = sum.add(n.gold.multiply(BigDecimal.valueOf(100)));
                if (n.type.equals("xfm_finance_account")) sum = sum.add(number(n.vars.get("xfm_free_cents"))).add(number(n.vars.get("xfm_reserved_cents")));
            }
            return sum.add(BigDecimal.valueOf(exchange.integer("xfm_fee_cents"))).stripTrailingZeros();
        }
        long integerValue(String value, Node node) { return value(program.get(value), new Frame(node, null, node), BigDecimal.ZERO).longValueExact(); }
        boolean validGui(String name, Node node) { return test(definition(name).block("is_valid"), new Frame(node, null, node)); }
        void runGui(String name, Node node) { if (!validGui(name, node)) throw new IllegalArgumentException("invalid GUI action"); execute(definition(name).block("effect"), new Frame(node, null, node)); }
        void run(String name, Node node) { trace.clear(); temporaryLists.clear(); execute(definition(name), new Frame(node, null, node)); if (Boolean.getBoolean("xfm.subset.trace") && name.equals("xfm_futures_submit_effect") && node.integer("xfm_futures_result") == 0) System.out.println("REJECT reason=" + node.integer("xfm_futures_reason") + " " + trace); }
        Block definition(String name) { Block b = program.get(name); if (b == null) throw new IllegalArgumentException("unknown definition " + name); return b; }
        Datum resolve(String text, Frame f) {
            try { return new NumberDatum(new BigDecimal(text)); } catch (NumberFormatException ignored) { /* scope/value token */ }
            int dot = text.indexOf('.');
            if (dot > 0) { Datum base = resolve(text.substring(0, dot), f); return base instanceof Node n ? resolve(text.substring(dot + 1), f.enter(n)) : null; }
            if (text.equals("this")) return f.here(); if (text.equals("prev")) return f.previous(); if (text.equals("root")) return f.root();
            if (text.equals("global_var:xfm_exchange")) return exchange;
            if (text.equals("story_owner")) return f.here().owner;
            if (text.startsWith("scope:")) return scopes.get(text.substring(6));
            if (text.startsWith("var:")) return f.here().vars.get(text.substring(4));
            if (text.equals("gold")) return new NumberDatum(f.here().gold);
            if (f.here().links.containsKey(text)) return f.here().links.get(text);
            if (program.containsKey(text)) return new NumberDatum(value(definition(text), f, BigDecimal.ZERO));
            if (Set.of("xfm_config_player_order_capacity_value", "xfm_config_coin_order_capacity_value", "xfm_config_global_order_capacity_value", "xfm_config_futures_position_capacity_value").contains(text)) return new NumberDatum(BigDecimal.valueOf(4096));
            try { return new NumberDatum(new BigDecimal(text)); } catch (NumberFormatException ignored) { return new TextDatum(text); }
        }
        Datum evaluate(Value v, Frame f) { return v instanceof Block b ? new NumberDatum(value(b, f, BigDecimal.ZERO)) : resolve(atom(v), f); }
        BigDecimal number(Datum d) { if (d == null) return BigDecimal.ZERO; if (d instanceof NumberDatum n) return n.value(); throw new IllegalArgumentException("number required " + d); }
        BigDecimal value(Block b, Frame f, BigDecimal initial) {
            BigDecimal n = initial; boolean chain = false;
            for (Entry e : b.entries()) {
                if (e.key().equals("if") || e.key().equals("else_if")) {
                    Block child = (Block)e.value(); boolean yes = (!e.key().equals("else_if") || !chain) && test(child.block("limit"), f);
                    if (e.key().equals("if")) chain = false;
                    if (yes) { n = value(without(child, "limit"), f, n); chain = true; } continue;
                }
                if (e.key().equals("else")) { if (!chain) n = value((Block)e.value(), f, n); chain = false; continue; }
                if (e.key().equals("every_in_list")) {
                    Block child = (Block)e.value();
                    for (Node item : list(f.here(), atom(field(child, "variable"))))
                        if (test(child.block("limit"), f.enter(item))) n = value(without(without(child, "variable"), "limit"), f.enter(item), n);
                    continue;
                }
                if (e.key().equals("floor")) { n = n.setScale(0, RoundingMode.FLOOR); continue; }
                if (e.key().equals("ceiling")) { n = n.setScale(0, RoundingMode.CEILING); continue; }
                BigDecimal x = number(evaluate(e.value(), f));
                n = switch (e.key()) {
                    case "value" -> x; case "add" -> n.add(x); case "subtract" -> n.subtract(x); case "multiply" -> n.multiply(x);
                    case "divide" -> n.divide(x, 18, RoundingMode.HALF_EVEN); case "max" -> n.min(x); case "min" -> n.max(x);
                    default -> throw new IllegalArgumentException("unknown value operation " + e.key());
                };
            }
            return n;
        }
        boolean test(Block b, Frame f) { for (Entry e : b.entries()) if (!check(e, f)) { if (trace.size() > 40) trace.removeFirst(); trace.add(f.here().id + ":" + e.key() + e.operator() + (e.value() instanceof Atom a ? a.token() : "{...}")); return false; } return true; }
        boolean check(Entry e, Frame f) {
            String k = e.key();
            if (k.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, f));
            if (k.equals("AND")) return test((Block)e.value(), f);
            if (k.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, f));
            if (k.equals("exists")) return resolve(atom(e.value()), f) != null;
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("trigger_if")) { Block child = (Block)e.value(); return !test(child.block("limit"), f) || test(without(child, "limit"), f); }
            if (k.equals("has_character_flag")) return f.here().flags.contains(atom(e.value()));
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("has_trait")) return f.here().traits.contains(atom(e.value()));
            if (k.equals("has_game_rule")) return rules.contains(atom(e.value())); // Engine rule selection only.
            if (k.equals("xfm_config_futures_open_trigger")) return open;
            if (k.equals("xfm_config_spot_open_trigger")) return open;
            if (k.equals("is_target_in_variable_list") || k.equals("is_target_in_global_variable_list")) {
                Block b = (Block)e.value(); String name = atom(field(b, "name")); Datum target = evaluate(field(b, "target"), f);
                return target instanceof Node && (k.equals("is_target_in_global_variable_list")
                        ? globalLists.getOrDefault(name, List.of()) : list(f.here(), name)).contains(target);
            }
            if (k.equals("any_in_list")) {
                Block b = (Block)e.value(); for (Node n : list(f.here(), atom(field(b, "variable")))) if (test(without(b, "variable"), f.enter(n))) return true; return false;
            }
            if (k.endsWith("_trigger") && program.containsKey(k)) return test(e.value() instanceof Block args ? substitute(definition(k), args) : definition(k), f);
            if (e.value() instanceof Block child && !(resolve(k, f) instanceof NumberDatum)) {
                Datum scope = resolve(k, f); return scope instanceof Node n && test(child, f.enter(n));
            }
            Datum left = resolve(k, f), right = evaluate(e.value(), f);
            if (left instanceof NumberDatum x && right instanceof NumberDatum y) {
                int cmp = x.value().compareTo(y.value()); return switch (e.operator()) { case "=" -> cmp == 0; case "!=" -> cmp != 0; case ">" -> cmp > 0; case "<" -> cmp < 0; case ">=" -> cmp >= 0; case "<=" -> cmp <= 0; default -> throw new IllegalArgumentException(e.operator()); };
            }
            if (e.operator().equals("=")) return java.util.Objects.equals(left, right);
            if (e.operator().equals("!=")) return !java.util.Objects.equals(left, right);
            return false;
        }
        List<Node> list(Node owner, String name) {
            List<Node> result = List.copyOf(owner.list(name));
            if (Set.of("xfm_ui_positions_page", "xfm_ui_orders_page", "xfm_ui_history_page", "xfm_ui_debts_page", "xfm_ui_claims_page", "xfm_ui_aid_debts", "xfm_ui_news", "xfm_ui_otc_buyers").contains(name)) {
                maxUiPageEntries = Math.max(maxUiPageEntries, result.size());
                if (result.size() > 16) throw new IllegalArgumentException("portfolio UI page exceeds sixteen real references");
            }
            if (name.equals("xfm_futures_discovery_contracts")) { maxDiscoveryEntries = Math.max(maxDiscoveryEntries, result.size()); if (result.size() > 8) throw new IllegalArgumentException("discovery capacity exceeded"); }
            if (name.equals("xfm_futures_contracts")) historyVisits += result.size();
            return result;
        }
        void execute(Block b, Frame f) {
            boolean chain = false;
            for (Entry e : b.entries()) {
                String k = e.key();
                if (k.equals("if") || k.equals("else_if")) {
                    Block child = (Block)e.value(); boolean yes = (!k.equals("else_if") || !chain) && test(child.block("limit"), f);
                    if (k.equals("if")) chain = false; if (yes) { execute(without(child, "limit"), f); chain = true; } continue;
                }
                if (k.equals("else")) { if (!chain) execute((Block)e.value(), f); chain = false; continue; }
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("remove_variable")) { f.here().vars.remove(atom(e.value())); continue; }
                if (k.equals("clear_variable_list")) { f.here().list(atom(e.value())).clear(); continue; }
                if (k.equals("add_to_temporary_list")) { temporaryLists.computeIfAbsent(atom(e.value()), ignored -> new ArrayList<>()).add(f.here()); continue; }
                if (k.equals("while")) {
                    Block a = (Block)e.value(); int bound = 0;
                    if (!a.named("count").isEmpty()) {
                        int count = number(evaluate(field(a, "count"), f)).intValueExact();
                        if (f.here().type.equals("xfm_spot_order")) { if (count > 64) throw new IllegalArgumentException("spot work cap exceeded"); maxSpotMatchIterations = Math.max(maxSpotMatchIterations, count); }
                        for (int i = 0; i < count; i++) execute(without(a, "count"), f);
                        continue;
                    }
                    boolean archiveLoop = f.here() == exchange && a.block("limit").entries().stream().anyMatch(x -> x.key().equals("var:xfm_futures_prune_budget"));
                    while (test(a.block("limit"), f)) {
                        if (++bound > (archiveLoop ? 64 : 10)) throw new IllegalArgumentException("bounded production loop exceeded limit");
                        if (archiveLoop) maxArchivePruneIterations = Math.max(maxArchivePruneIterations, bound);
                        execute(without(a, "limit"), f);
                    }
                    continue;
                }
                if (k.equals("ordered_in_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> ordered = new ArrayList<>();
                    for (Node n : list(f.here(), name)) if (test(a.block("limit"), f.enter(n))) ordered.add(n);
                    ordered.sort((left, right) -> number(evaluate(field(a, "order_by"), f.enter(right))).compareTo(number(evaluate(field(a, "order_by"), f.enter(left)))));
                    int start = a.named("position").isEmpty() ? 0 : number(evaluate(field(a, "position"), f)).intValueExact();
                    int count = a.named("max").isEmpty() ? 1 : number(evaluate(field(a, "max"), f)).intValueExact();
                    Block effect = without(without(without(without(without(without(a, "variable"), "limit"), "order_by"), "max"), "position"), "check_range_bounds");
                    for (int i = start; i < Math.min(ordered.size(), start + count); i++) execute(effect, f.enter(ordered.get(i)));
                    continue;
                }
                if (k.equals("set_variable") || k.equals("change_variable")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name"));
                    if (k.equals("set_variable")) f.here().vars.put(name, evaluate(field(a, "value"), f));
                    else {
                        boolean add = !a.named("add").isEmpty(); BigDecimal amount = number(evaluate(field(a, add ? "add" : "subtract"), f));
                        BigDecimal old = number(f.here().vars.get(name)); f.here().vars.put(name, new NumberDatum(add ? old.add(amount) : old.subtract(amount)));
                    }
                    continue;
                }
                if (k.equals("save_scope_value_as")) { Block a = (Block)e.value(); scopes.put(atom(field(a, "name")), evaluate(field(a, "value"), f)); continue; }
                if (k.equals("remove_short_term_gold")) { f.here().gold = f.here().gold.subtract(number(evaluate(e.value(), f))).setScale(2); continue; }
                if (k.equals("add_gold")) { f.here().gold = f.here().gold.add(number(evaluate(e.value(), f))).setScale(2); continue; }
                if (k.equals("create_story")) {
                    Block a = (Block)e.value(); String type = atom(field(a, "type"));
                    if (!type.equals(failType)) { Node created = node("created-" + ++sequence, type); created.owner = f.here(); scopes.put(atom(field(a, "save_scope_as")), created); }
                    continue;
                }
                if (k.equals("end_story")) { f.here().ended = true; continue; }
                if (k.equals("add_to_variable_list") || k.equals("remove_list_variable") || k.equals("add_to_global_variable_list") || k.equals("remove_list_global_variable")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name")); Node target = (Node)evaluate(field(a, "target"), f);
                    List<Node> list = k.equals("add_to_global_variable_list") || k.equals("remove_list_global_variable") ? globalLists.computeIfAbsent(name, ignored -> new ArrayList<>()) : f.here().list(name);
                    if (k.equals("remove_list_variable") || k.equals("remove_list_global_variable")) list.remove(target); else list.add(target);
                    if (name.equals("xfm_spot_orders")) { maxSpotBookEntries = Math.max(maxSpotBookEntries, list.size()); if (list.size() > 128) throw new IllegalArgumentException("resting book exceeds every supported preset"); }
                    continue;
                }
                if (k.equals("every_in_list") || k.equals("random_in_list") || k.equals("random_in_global_list")) {
                    Block a = (Block)e.value(); String selector = a.named("variable").isEmpty() ? "list" : "variable";
                    String name = atom(field(a, selector));
                    List<Node> list = k.equals("random_in_global_list") ? List.copyOf(globalLists.getOrDefault(name, List.of()))
                            : selector.equals("list") ? List.copyOf(temporaryLists.getOrDefault(name, List.of())) : list(f.here(), name);
                    for (Node n : list) if (test(a.block("limit"), f.enter(n))) {
                        execute(without(without(a, selector), "limit"), f.enter(n)); if (!k.equals("every_in_list")) break;
                    }
                    continue;
                }
                if (k.equals("random")) { Block a = (Block)e.value(); if (randomEnabled && number(evaluate(field(a, "chance"), f)).signum() > 0) execute(without(a, "chance"), f); continue; }
                if (k.equals("xfm_futures_match_effect")) { matchCalls++; execute(definition("xfm_futures_finish_incoming_effect"), f); continue; } // no fabricated fill; actual post-match remainder admission/enrolment still runs
                if (k.equals("xfm_oracle_record_trade_effect")) continue; // independent oracle sampler, outside cash/coin settlement subset
                if (k.equals("xfm_spot_record_trade_effect")) spotExecutionOrderIds.add(((Node)scopes.get("xfm_spot_resting")).integer("xfm_order_id"));
                // A known parameterized scripted effect is not an object scope or a script value.
                // Reuse the existing recursive token substitution, then execute its real AST body.
                if (k.endsWith("_effect") && program.containsKey(k) && e.value() instanceof Block arguments) {
                    effectCalls.merge(k, 1, Integer::sum);
                    execute(substitute(definition(k), arguments), f); continue;
                }
                if (e.value() instanceof Block child) { Datum scope = resolve(k, f); if (!(scope instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(child, f.enter(n)); continue; }
                effectCalls.merge(k, 1, Integer::sum);
                if (k.equals("xfm_finance_transfer_effect")) cashTransferRequests.add(f.here().integer("xfm_request_cents"));
                execute(definition(k), f); // Observe calls only; execute the unchanged actual production body.
            }
        }
    }
    private static String atom(Value value) { if (!(value instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Block substitute(Block block, Block arguments) {
        Map<String, String> replacements = new LinkedHashMap<>();
        for (Entry arg : arguments.entries()) replacements.put("$" + arg.key() + "$", atom(arg.value()));
        return substitute(block, replacements);
    }
    private static Block substitute(Block block, Map<String, String> replacements) {
        return new Block(block.entries().stream().map(entry -> new Entry(replace(entry.key(), replacements), entry.operator(),
                entry.value() instanceof Block child ? substitute(child, replacements)
                        : new Atom(replace(atom(entry.value()), replacements)))).toList());
    }
    private static String replace(String text, Map<String, String> replacements) {
        String result = text; for (var e : replacements.entrySet()) result = result.replace(e.getKey(), e.getValue()); return result;
    }
    private static Value field(Block block, String name) { List<Entry> found = block.named(name); if (found.size() != 1) throw new IllegalArgumentException("one field required " + name); return found.getFirst().value(); }
    private static Block without(Block block, String name) { return new Block(block.entries().stream().filter(e -> !e.key().equals(name)).toList()); }
}
