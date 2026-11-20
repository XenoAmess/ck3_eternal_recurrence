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

/** Executes the actual bounded production funding/discovery scripts through the shared SCRIPT parser.
 * Test-only semantic subset, not CK3 qualification. Unknown operations fail.
 * Explicit engine ports: deterministic random, story creation/failure, beneficiary refresh,
 * config capacities/open switch, and the matching callback (matching itself is outside this subset).
 */
final class FuturesAiScriptContractTest {
    /** External bounded source-subset execution; Maven later discovers the same @Test methods. */
    public static void main(String[] args) throws Exception {
        int passed = 0, failed = 0;
        for (var method : java.util.Arrays.stream(FuturesAiScriptContractTest.class.getDeclaredMethods())
                .filter(m -> m.isAnnotationPresent(Test.class)).sorted(java.util.Comparator.comparing(java.lang.reflect.Method::getName)).toList()) {
            try { method.invoke(new FuturesAiScriptContractTest()); passed++; System.out.println("PASS " + method.getName()); }
            catch (java.lang.reflect.InvocationTargetException error) { failed++; System.out.println("FAIL " + method.getName()); error.getCause().printStackTrace(System.out); }
        }
        System.out.println("PRODUCTION_SUBSET groups=" + (passed + failed) + " passed=" + passed + " failed=" + failed + " CK3_NOT_RUN");
        if (failed != 0) throw new IllegalStateException("production subset failures: " + failed);
    }
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final Path REFERENCE = Path.of(System.getProperty("xfm.reference.source", SOURCE.toString()));
    private static final List<String> INPUTS = List.of(
        "scripted_guis/xfm_market_futures_open.txt", "scripted_effects/xfm_futures_ai.txt", "scripted_effects/xfm_futures_ai_funding.txt",
        "scripted_effects/xfm_futures_discovery.txt", "scripted_effects/xfm_futures_orders.txt",
        "scripted_effects/xfm_futures_daily_index.txt",
        "scripted_effects/xfm_oracle_indexes.txt", "script_values/xfm_oracle_index_values.txt",
        "scripted_effects/xfm_finance_cash.txt", "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_reserve.txt", "scripted_effects/xfm_finance_schedule.txt", "scripted_triggers/xfm_finance_triggers.txt",
        "scripted_triggers/xfm_futures_triggers.txt", "scripted_triggers/xfm_futures_ai_triggers.txt",
        "script_values/xfm_finance_values.txt", "script_values/xfm_futures_values.txt",
        "script_values/xfm_futures_ai_values.txt", "script_values/xfm_numeric_comparison_values.txt");

    @Test void goldFundsANewZeroPrivateWalletAndAnActualReservation() throws IOException {
        Vm v = vm(); Node a = ticket(v, "30.00");
        BigDecimal before = v.cashStock();
        v.run("xfm_futures_submit_effect", a);
        Node account = a.ref("xfm_account");
        assertEquals(1, a.integer("xfm_futures_result"));
        assertEquals(121, account.integer("xfm_reserved_cents"));
        assertEquals(0, account.integer("xfm_free_cents"));
        assertEquals(new BigDecimal("28.79"), a.gold);
        assertEquals(before, v.cashStock());
        assertEquals(1, v.matchCalls);
        assertEquals(1, account.list("xfm_reservations").size());
    }

    @Test void exactFivePercentBoundaryIncludesRoundedFeeAndFiveGoldReserve() throws IOException {
        Vm v = vm(); Node a = ticket(v, "29.20");
        assertEquals(121, v.integerValue("xfm_futures_ai_budget_cents_value", a));
        v.run("xfm_futures_submit_effect", a);
        assertEquals(1, a.integer("xfm_futures_result"));
        Vm below = vm(); Node b = ticket(below, "29.19");
        BigDecimal before = below.cashStock();
        below.run("xfm_futures_submit_effect", b);
        assertEquals(0, b.integer("xfm_futures_result"));
        assertEquals(new BigDecimal("29.19"), b.gold);
        assertEquals(before, below.cashStock());
        assertEquals(0, below.created("xfm_futures_order"));
        // At mark 101, upper band is ceil(121.2)=122; fee ceil(.366)=1: reserve=123.
        Vm rounded = vm(); Node c = ticket(rounded, "29.60"); c.ref("xfm_selected_coin").put("xfm_mark_cents", 101);
        rounded.run("xfm_futures_submit_effect", c);
        assertEquals(123, c.ref("xfm_account").integer("xfm_reserved_cents"));
    }

    @Test void onlyTheRealGapIsDepositedAndReservedMoneyIsExcluded() throws IOException {
        Vm v = vm(); Node a = ticket(v, "30.00"), account = primary(v, a, 100);
        account.put("xfm_reserved_cents", 900000);
        BigDecimal before = v.cashStock();
        v.run("xfm_futures_submit_effect", a);
        assertEquals(new BigDecimal("29.79"), a.gold);
        assertEquals(0, account.integer("xfm_free_cents"));
        assertEquals(900121, account.integer("xfm_reserved_cents"));
        assertEquals(before, v.cashStock());
        assertEquals(21, a.integer("xfm_futures_ai_funded_cents"));
    }

    @Test void inheritedActiveAndProjectFundsCannotFinanceAiRisk() throws IOException {
        for (boolean project : List.of(false, true)) {
            Vm v = vm(); Node a = ticket(v, "0.00"), own = primary(v, a, 0);
            Node side = v.account("side", a, 1000000);
            if (project) side.put("xfm_legal_entity", v.node("project", "xfm_finance_coin"));
            a.put("xfm_active_account", side);
            v.run("xfm_futures_submit_effect", a);
            assertEquals(0, a.integer("xfm_futures_result"));
            assertEquals(0, own.integer("xfm_reserved_cents"));
            assertEquals(1000000, side.integer("xfm_free_cents"));
        }
        Vm v = vm(); Node a = ticket(v, "20.00"), own = primary(v, a, 1000), inherited = v.account("inherited", a, 500000);
        a.put("xfm_active_account", inherited);
        v.run("xfm_futures_submit_effect", a);
        assertEquals(1, a.integer("xfm_futures_result"));
        assertEquals(879, own.integer("xfm_free_cents"));
        assertEquals(121, own.integer("xfm_reserved_cents"));
        assertEquals(500000, inherited.integer("xfm_free_cents"));
        assertEquals(new BigDecimal("20.00"), a.gold);
    }

    @Test void invalidPrimaryAssetsNeverCountAsPersonalLiquidity() throws IOException {
        for (String defect : List.of("frozen", "project", "system", "other-holder")) {
            Vm v = vm(); Node a = ticket(v, "0.00"), p = primary(v, a, 1000000);
            switch (defect) {
                case "frozen" -> p.put("xfm_account_frozen", 1);
                case "project" -> p.put("xfm_legal_entity", v.node("entity", "xfm_finance_coin"));
                case "system" -> p.put("xfm_system_account", 1);
                case "other-holder" -> p.put("xfm_holder", v.node("other", ""));
                default -> throw new AssertionError(defect);
            }
            assertEquals(0, v.integerValue("xfm_futures_ai_budget_cents_value", a), defect);
            BigDecimal before = v.cashStock();
            v.run("xfm_futures_submit_effect", a);
            assertEquals(0, a.integer("xfm_futures_result"), defect);
            assertEquals(1000000, p.integer("xfm_free_cents"));
            assertEquals(before, v.cashStock());
        }
    }

    @Test void orderOrReservationCreationFailureDoesNotDepositOrLeaveAnOpenOrder() throws IOException {
        for (String failedType : List.of("xfm_futures_order", "xfm_finance_reservation")) {
            Vm v = vm(); Node a = ticket(v, "30.00"); primary(v, a, 100);
            BigDecimal before = v.cashStock(); v.failType = failedType;
            v.run("xfm_futures_submit_effect", a);
            assertEquals(0, a.integer("xfm_futures_result"));
            assertEquals(new BigDecimal("30.00"), a.gold);
            assertEquals(100, a.ref("xfm_account").integer("xfm_free_cents"));
            assertEquals(0, a.ref("xfm_account").integer("xfm_reserved_cents"));
            assertEquals(before, v.cashStock());
            assertTrue(v.nodes.values().stream().filter(n -> n.type.equals("xfm_futures_order")).allMatch(n -> n.ended));
            assertEquals(0, v.matchCalls);
        }
    }

    @Test void disabledDebtPendingAndRelatedCrossesRejectBeforeFunding() throws IOException {
        for (String rejection : List.of("disabled", "debt", "pending", "related", "expired", "stale")) {
            Vm v = vm(); Node a = ticket(v, "30.00"), own = primary(v, a, 0), contract = a.ref("xfm_futures_contract");
            switch (rejection) {
                case "disabled" -> v.open = false;
                case "debt" -> own.put("xfm_total_debt_cents", 1);
                case "pending" -> own.put("xfm_futures_pending_count", 1);
                case "related" -> v.order("related", contract, v.account("related-account", a, 0), 2, 100);
                case "expired" -> { contract.put("xfm_perpetual", 0); contract.put("xfm_expiry_day", 1); }
                case "stale" -> contract.ref("xfm_coin").put("xfm_oracle_day", 0);
                default -> throw new AssertionError(rejection);
            }
            BigDecimal before = v.cashStock();
            v.run("xfm_futures_submit_effect", a);
            assertEquals(0, a.integer("xfm_futures_result"), rejection);
            assertEquals(new BigDecimal("30.00"), a.gold, rejection);
            assertEquals(before, v.cashStock(), rejection);
            assertEquals(0, v.created("xfm_futures_order"), rejection);
        }
    }

    @Test void playersKeepTheirExplicitActiveWalletAndDoNotAutoDeposit() throws IOException {
        Vm v = vm(); Node a = ticket(v, "1000.00"); a.ai = false;
        primary(v, a, 10000); Node active = v.account("inherited", a, 121); a.put("xfm_active_account", active);
        v.run("xfm_futures_submit_effect", a);
        assertEquals(121, active.integer("xfm_reserved_cents"));
        assertEquals(10000, a.ref("xfm_account").integer("xfm_free_cents"));
        assertEquals(new BigDecimal("1000.00"), a.gold);
        Vm noCash = vm(); Node b = ticket(noCash, "1000.00"); b.ai = false; primary(noCash, b, 0);
        noCash.run("xfm_futures_submit_effect", b);
        assertEquals(0, b.integer("xfm_futures_result"));
        assertEquals(new BigDecimal("1000.00"), b.gold);
    }

    @Test void fixedExpirySharesAcrossDaysAndRollsWithoutRewritingOldIdentity() throws IOException {
        Vm v = vm(); Node a = v.node("actor", ""); Node asset = v.asset("asset"); a.put("xfm_selected_coin", asset);
        for (int day : List.of(0, 1, 22, 23)) {
            v.exchange.put("xfm_day", day);
            assertEquals(30, v.integerValue("xfm_futures_standard_expiry_day_value", a));
            a.put("xfm_futures_perpetual", 0); a.put("xfm_futures_expiry_day", 30);
            v.run("xfm_futures_ensure_market_effect", a);
            assertEquals(1, a.ref("xfm_futures_contract").integer("xfm_contract_id"));
        }
        Node first = a.ref("xfm_futures_contract");
        v.exchange.put("xfm_day", 24);
        assertEquals(60, v.integerValue("xfm_futures_standard_expiry_day_value", a));
        a.put("xfm_futures_expiry_day", 60); v.run("xfm_futures_ensure_market_effect", a);
        assertEquals(2, a.ref("xfm_futures_contract").integer("xfm_contract_id"));
        assertEquals(30, first.integer("xfm_expiry_day"));
        assertEquals(1, first.integer("xfm_contract_id"));
        assertEquals(0, v.historyVisits);
    }

    @Test void discoveryCyclesOnlyValidSameAssetContractsWithFixedEightEntryBound() throws IOException {
        Vm v = vm(); Node a = v.node("actor", ""), asset = v.asset("asset"), other = v.asset("other");
        a.put("xfm_selected_coin", asset);
        for (int i = 0; i < 1000; i++) asset.list("xfm_futures_contracts").add(v.contract("history" + i, asset, 0, 0));
        Node first = v.contract("first", asset, 0, 30), second = v.contract("second", asset, 0, 60);
        Node closed = v.contract("closed", asset, 0, 90); closed.put("xfm_status", 2);
        Node expired = v.contract("expired", asset, 0, 1), wrong = v.contract("wrong", other, 0, 40);
        asset.list("xfm_futures_discovery_contracts").addAll(List.of(second, closed, wrong, first, expired));
        asset.put("xfm_futures_discovery_count", 5);
        v.run("xfm_futures_select_next_dated_effect", a);
        assertSame(first, a.ref("xfm_futures_contract"));
        v.run("xfm_futures_select_next_dated_effect", a); assertSame(second, a.ref("xfm_futures_contract"));
        v.run("xfm_futures_select_next_dated_effect", a); assertSame(first, a.ref("xfm_futures_contract"));
        assertEquals(2, asset.integer("xfm_futures_discovery_count"));
        assertEquals(0, v.historyVisits);
        assertTrue(v.maxDiscoveryEntries <= 8);
        for (int i = 0; i < 20; i++) v.run("xfm_futures_register_discovery_effect", v.contract("extra" + i, asset, 0, 100 + i));
        assertEquals(8, asset.integer("xfm_futures_discovery_count"));
        assertEquals(8, asset.list("xfm_futures_discovery_contracts").size());
    }

    @Test void aiFindsFundedDatedCounterpartyAndSameDayRetryCannotSpendAgain() throws IOException {
        Vm v = vm(); Node a = ticket(v, "30.00"); a.vars.remove("xfm_futures_contract");
        Node asset = a.ref("xfm_selected_coin"), dated = v.contract("dated", asset, 0, 30);
        v.run("xfm_futures_register_discovery_effect", dated);
        Node b = v.node("independent", ""), counterparty = v.account("counterparty", b, 0);
        v.order("real-dated-order", dated, counterparty, 1, 100);
        a.list("xfm_finance_watchlist").add(asset);
        v.run("xfm_futures_ai_effect", a);
        assertSame(dated, a.ref("xfm_futures_contract"));
        assertEquals(0, a.integer("xfm_futures_perpetual"));
        assertEquals(30, a.integer("xfm_futures_expiry_day"));
        assertEquals(2, a.integer("xfm_futures_side"));
        assertEquals(1, a.integer("xfm_futures_result"));
        BigDecimal after = v.cashStock(), gold = a.gold;
        v.run("xfm_futures_ai_effect", a);
        assertEquals(gold, a.gold); assertEquals(after, v.cashStock()); assertEquals(1, v.matchCalls);
        assertEquals(0, v.historyVisits);
    }


    @Test void normalGuiAndAiShareTheSameSeriesAndGuiRejectsClosedOrForeignEntries() throws IOException {
        Vm v = vm(); v.exchange.put("xfm_day", 0);
        Node player = v.node("player", ""), asset = v.asset("asset"); player.ai = false; player.put("xfm_selected_coin", asset);
        assertTrue(v.validGui("xfm_market_contract_dated_gui", player));
        v.runGui("xfm_market_contract_dated_gui", player);
        Node contract = player.ref("xfm_futures_contract");
        assertEquals(30, contract.integer("xfm_expiry_day"));
        v.exchange.put("xfm_day", 1);
        v.runGui("xfm_market_contract_dated_gui", player);
        assertSame(contract, player.ref("xfm_futures_contract"));
        Node ai = v.node("ai", ""); ai.put("xfm_selected_coin", asset);
        v.scopes.put("xfm_fut_ai_actor", ai); v.randomEnabled = false; // deterministic dated fallback, not a claim about engine probabilities
        v.run("xfm_futures_ai_choose_market_effect", ai);
        assertSame(contract, ai.ref("xfm_futures_contract"));
        assertEquals(1, v.created("xfm_futures_contract"));
        assertTrue(v.validGui("xfm_market_contract_next_dated_gui", player));
        contract.put("xfm_status", 2);
        assertFalse(v.validGui("xfm_market_contract_next_dated_gui", player));
        contract.put("xfm_status", 0); player.put("xfm_selected_coin", v.asset("foreign"));
        assertFalse(v.validGui("xfm_market_contract_next_dated_gui", player));
        assertEquals(0, v.historyVisits);
    }

    @Test void explicitExistingContractRegistersWithoutChangingIdentityAndFailedSelectionClearsStaleTicket() throws IOException {
        Vm v = vm(); Node a = v.node("actor", ""), asset = v.asset("asset");
        Node existing = v.contract("existing", asset, 0, 30); existing.put("xfm_contract_id", 77);
        a.put("xfm_selected_coin", asset); a.put("xfm_futures_contract", existing);
        a.put("xfm_futures_perpetual", 0); a.put("xfm_futures_expiry_day", 30);
        asset.list("xfm_futures_contracts").add(existing); // permanent historical index is deliberately not searched
        v.run("xfm_futures_ensure_market_effect", a);
        assertSame(existing, a.ref("xfm_futures_contract"));
        assertEquals(77, existing.integer("xfm_contract_id"));
        assertEquals(0, v.created("xfm_futures_contract"));
        a.put("xfm_futures_expiry_day", 60); v.failType = "xfm_futures_contract";
        v.run("xfm_futures_ensure_market_effect", a);
        assertFalse(a.vars.containsKey("xfm_futures_contract"));
        assertEquals(77, existing.integer("xfm_contract_id"));
        assertEquals(0, v.historyVisits);
    }

    @Test void legacyEmptyLiveSeriesMigrationPreservesIdentityWithoutDailyObligation() throws IOException {
        Vm v = vm(); Node actor = v.node("legacy-player", ""); actor.ai = false;
        Node asset = v.asset("legacy-asset");
        Node original = v.contract("legacy-id-77", asset, 0, 30); original.put("xfm_contract_id", 77);
        Node expired = v.contract("expired-history", asset, 0, 1);
        Node closed = v.contract("closed-history", asset, 0, 60); closed.put("xfm_status", 2);
        Node foreignType = v.node("foreign-history", "xfm_finance_coin");
        v.exchange.list("xfm_futures_contracts").addAll(List.of(original, expired, closed, foreignType));
        actor.put("xfm_selected_coin", asset); actor.put("xfm_futures_perpetual", 0); actor.put("xfm_futures_expiry_day", 30);
        v.run("xfm_futures_daily_index_ensure_effect", v.exchange);
        assertEquals(List.of(original), asset.list("xfm_futures_discovery_contracts"));
        assertEquals(0, v.exchange.integer("xfm_futures_daily_count"));
        assertFalse(v.exchange.vars.containsKey("xfm_futures_daily_head"));
        assertEquals(4, v.historyVisits);
        v.run("xfm_futures_ensure_market_effect", actor);
        assertSame(original, actor.ref("xfm_futures_contract")); assertEquals(77, original.integer("xfm_contract_id"));
        assertEquals(0, v.created("xfm_futures_contract"));
        v.run("xfm_futures_daily_index_ensure_effect", v.exchange);
        assertEquals(4, v.historyVisits); assertEquals(1, asset.integer("xfm_futures_discovery_count"));
        assertEquals(4, v.exchange.list("xfm_futures_contracts").size());
    }

    @Test void newModelFirstAndRepeatedDailyQuotesUseSmallFaceAndPendingRetainsLastMark() throws IOException {
        Vm v = vm();
        Node grain = v.newIndex(1, "xfm_grain_index"), military = v.newIndex(2, "xfm_military_index"), trade = v.newIndex(3, "xfm_trade_index");
        for (Node index : List.of(grain, military, trade)) {
            assertEquals(100, index.integer("xfm_model_quote_divisor"));
            assertEquals(0, index.integer("xfm_index_cents"));
            assertEquals(0, index.integer("xfm_mark_cents"));
            assertEquals(0, index.integer("xfm_max_leverage"));
        }
        v.counties(8, 0, 100, false);
        for (int day : List.of(1, 2)) {
            v.exchange.put("xfm_day", day); v.run("xfm_oracle_index_daily_effect", v.exchange);
            for (Node index : List.of(grain, military, trade)) {
                assertEquals(100, index.integer("xfm_index_cents"));
                assertEquals(100, index.integer("xfm_mark_cents"));
                assertEquals(5, index.integer("xfm_max_leverage"));
                assertEquals(day, index.integer("xfm_oracle_last_valid_day"));
            }
        }
        v.exchange.list("xfm_oracle_counties").removeLast(); v.exchange.put("xfm_day", 3);
        v.run("xfm_oracle_index_daily_effect", v.exchange);
        assertEquals(100, grain.integer("xfm_mark_cents")); assertEquals(0, grain.integer("xfm_max_leverage"));
        assertEquals(0, grain.integer("xfm_oracle_quality")); assertEquals(2, grain.integer("xfm_oracle_last_valid_day"));
        assertEquals(3, grain.integer("xfm_oracle_day"));
    }

    @Test void mixedLegacyAndNewModelUnitsDoNotRewriteOldPortfolioOrCash() throws IOException {
        Vm v = vm(); Node grain = v.newIndex(1, "xfm_grain_index"), military = v.newIndex(2, "xfm_military_index"), trade = v.newIndex(3, "xfm_trade_index");
        grain.vars.remove("xfm_model_quote_divisor"); // Existing SAVE index: no migration or backfill.
        Node holder = v.node("legacy-holder", ""), account = v.account("legacy-wallet", holder, 4096);
        account.put("xfm_reserved_cents", 9000);
        Node contract = v.contract("legacy-series", grain, 0, 30); contract.put("xfm_contract_id", 77);
        Node position = v.node("legacy-position", "xfm_futures_position"); position.put("xfm_coin", grain);
        position.put("xfm_contract", contract); position.put("xfm_mark_cents", 10000); position.put("xfm_lots", 2);
        position.put("xfm_pending_payment", 1); position.put("xfm_pending_amount", 1234);
        Node debt = v.node("legacy-debt", "xfm_debt_claim"); debt.put("xfm_outstanding_cents", 1234); debt.put("xfm_source", position);
        Map<String, Datum> oldAccount = Map.copyOf(account.vars), oldContract = Map.copyOf(contract.vars);
        Map<String, Datum> oldPosition = Map.copyOf(position.vars), oldDebt = Map.copyOf(debt.vars);
        BigDecimal cash = v.cashStock(); v.counties(8, 100, 100, false);
        for (int day : List.of(1, 2)) { v.exchange.put("xfm_day", day); v.run("xfm_oracle_index_daily_effect", v.exchange); }
        assertEquals(5000, grain.integer("xfm_index_cents")); assertEquals(5000, grain.integer("xfm_mark_cents"));
        assertFalse(grain.vars.containsKey("xfm_model_quote_divisor"));
        assertEquals(120, military.integer("xfm_index_cents")); assertEquals(180, trade.integer("xfm_index_cents"));
        assertEquals(oldAccount, account.vars); assertEquals(oldContract, contract.vars);
        assertEquals(oldPosition, position.vars); assertEquals(oldDebt, debt.vars); assertEquals(cash, v.cashStock());
    }

    @Test void publishedSmallFaceFeedsActualAiReservationAndUnchangedMarginVariationValues() throws IOException {
        for (int leverage : List.of(1, 3)) {
            Vm v = vm(); Node grain = v.newIndex(1, "xfm_grain_index");
            v.newIndex(2, "xfm_military_index"); v.newIndex(3, "xfm_trade_index"); v.counties(8, 0, 100, false);
            v.run("xfm_oracle_index_daily_effect", v.exchange);
            Node actor = v.node("actor", ""); actor.gold = new BigDecimal(leverage == 1 ? "29.20" : "13.20");
            actor.put("xfm_selected_coin", grain); actor.put("xfm_futures_perpetual", 1); actor.put("xfm_futures_expiry_day", 0);
            actor.put("xfm_futures_contract", v.contract("new-series", grain, 1, 0)); actor.put("xfm_futures_side", 1);
            actor.put("xfm_futures_lots", 1); actor.put("xfm_futures_leverage", leverage); actor.put("xfm_futures_limit_cents", grain.integer("xfm_mark_cents"));
            BigDecimal cash = v.cashStock(); v.run("xfm_futures_submit_effect", actor);
            assertEquals(1, actor.integer("xfm_futures_result"));
            assertEquals(leverage == 1 ? 121 : 41, actor.ref("xfm_account").integer("xfm_reserved_cents"));
            assertEquals(cash, v.cashStock()); assertEquals(1, v.matchCalls); // Explicit matching port: no fill claimed.
            Node position = v.node("unit-values", "xfm_futures_position"); position.put("xfm_coin", grain);
            position.put("xfm_mark_cents", 100); position.put("xfm_new_mark_cents", 110); position.put("xfm_lots", 1);
            position.put("xfm_long_leverage", 5); position.put("xfm_short_leverage", 5);
            assertEquals(80, v.integerValue("xfm_futures_band_low_value", position));
            assertEquals(120, v.integerValue("xfm_futures_band_high_value", position));
            assertEquals(20, v.integerValue("xfm_futures_initial_long_value", position));
            assertEquals(12, v.integerValue("xfm_futures_maintenance_long_value", position));
            assertEquals(10, v.integerValue("xfm_futures_variation_value", position));
            position.put("xfm_mark_cents", 10000); position.put("xfm_new_mark_cents", 11000);
            assertEquals(1000, v.integerValue("xfm_futures_variation_value", position)); // Legacy positions keep full cents.
        }
    }

    @Test void boundedSizingKeepsOneLotAndReturnsZeroBelowItsRealRoundedCost() throws IOException {
        Vm v = vm(); Node a = ticket(v, "29.20"); primary(v, a, 0); BigDecimal cash = v.cashStock();
        v.run("xfm_futures_ai_size_order_effect", a);
        assertEquals(1, a.integer("xfm_futures_lots")); assertEquals(121, a.integer("xfm_futures_reserve_cents"));
        assertEquals(1, a.integer("xfm_futures_ai_size_result")); assertEquals(cash, v.cashStock());
        v.run("xfm_futures_submit_effect", a); assertEquals(121, a.ref("xfm_account").integer("xfm_reserved_cents"));
        Vm below = vm(); Node b = ticket(below, "29.19"); primary(below, b, 0); BigDecimal before = below.cashStock();
        below.run("xfm_futures_ai_size_order_effect", b);
        assertEquals(0, b.integer("xfm_futures_lots")); assertEquals(0, b.integer("xfm_futures_ai_size_result"));
        assertEquals(before, below.cashStock()); assertEquals(0, below.created("xfm_futures_order"));
        assertTrue(v.maxSizingIterations <= 16); assertEquals(16, below.maxSizingIterations);
    }
    @Test void exactMultiLotBudgetBoundaryIncludesBothRoundingsAtOneThreeAndFiveTimes() throws IOException {
        // At mark 107, H=129. Eleven-lot total costs are 1424 / 478 / 289, respectively.
        // A budget one cent below each must choose ten lots costing 1294 / 434 / 262.
        long[][] cases = {{1, 1424, 1294}, {3, 478, 434}, {5, 289, 262}};
        for (long[] c : cases) for (boolean below : List.of(false, true)) {
            long budget = c[1] - (below ? 1 : 0); Vm v = vm();
            Node a = ticket(v, BigDecimal.valueOf(budget * 20 + 500, 2).toPlainString()); primary(v, a, 0);
            a.ref("xfm_selected_coin").put("xfm_mark_cents", 107); a.put("xfm_futures_leverage", c[0]);
            BigDecimal stock = v.cashStock(); v.run("xfm_futures_ai_size_order_effect", a);
            assertEquals(below ? 10 : 11, a.integer("xfm_futures_lots"));
            assertEquals(below ? c[2] : c[1], a.integer("xfm_futures_reserve_cents"));
            assertTrue(a.integer("xfm_futures_reserve_cents") <= budget); assertEquals(stock, v.cashStock());
            v.run("xfm_futures_submit_effect", a); assertEquals(1, a.integer("xfm_futures_result"));
            assertEquals(below ? c[2] : c[1], a.ref("xfm_account").integer("xfm_reserved_cents"));
            Node order = a.ref("xfm_account").list("xfm_orders").getLast();
            assertEquals(below ? 10 : 11, order.integer("xfm_remaining_lots")); assertEquals(c[0], order.integer("xfm_leverage"));
            assertTrue(a.gold.compareTo(new BigDecimal("5.00")) >= 0); assertEquals(stock, v.cashStock());
        }
    }
    @Test void richAiQuantityIsCappedAtSixteenWithNoNewActionOrPopulationVisit() throws IOException {
        for (long leverage : List.of(1L, 3L, 5L)) {
            Vm v = vm(); Node a = ticket(v, "2005.00"); primary(v, a, 0); a.put("xfm_futures_leverage", leverage);
            a.ref("xfm_selected_coin").put("xfm_mark_cents", 107); BigDecimal stock = v.cashStock();
            v.run("xfm_futures_ai_size_order_effect", a); assertEquals(16, a.integer("xfm_futures_lots"));
            assertEquals(leverage == 1 ? 2071 : leverage == 3 ? 695 : 420, a.integer("xfm_futures_reserve_cents"));
            assertEquals(0, v.maxSizingIterations); assertEquals(stock, v.cashStock());
        }
        Vm v = vm(); Node a = ticket(v, "500.00"); a.vars.remove("xfm_futures_contract");
        Node asset = a.ref("xfm_selected_coin"), dated = v.contract("multi-dated", asset, 0, 30);
        v.run("xfm_futures_register_discovery_effect", dated);
        v.order("independent-offer", dated, v.account("external", v.node("external-holder", ""), 0), 1, 100);
        a.list("xfm_finance_watchlist").add(asset); BigDecimal stock = v.cashStock();
        v.run("xfm_futures_ai_effect", a); assertEquals(16, a.integer("xfm_futures_lots"));
        assertEquals(1, a.integer("xfm_futures_result")); assertEquals(1926, a.ref("xfm_account").integer("xfm_reserved_cents"));
        assertEquals(1, v.matchCalls); BigDecimal gold = a.gold;
        v.run("xfm_futures_ai_effect", a); assertEquals(1, v.matchCalls); assertEquals(gold, a.gold);
        assertEquals(stock, v.cashStock()); assertEquals(0, v.historyVisits);
    }
    @Test void sizingNeverBorrowsFrozenProjectReservedOrInheritedMoney() throws IOException {
        for (String defect : List.of("frozen", "project", "system", "other-holder", "reserved", "inherited")) {
            Vm v = vm(); Node a = ticket(v, "5.00"), own = primary(v, a, 0);
            switch (defect) {
                case "frozen" -> { own.put("xfm_free_cents", 1000000); own.put("xfm_account_frozen", 1); }
                case "project" -> { own.put("xfm_free_cents", 1000000); own.put("xfm_legal_entity", v.node("project", "xfm_finance_coin")); }
                case "system" -> { own.put("xfm_free_cents", 1000000); own.put("xfm_system_account", 1); }
                case "other-holder" -> { own.put("xfm_free_cents", 1000000); own.put("xfm_holder", v.node("foreign", "")); }
                case "reserved" -> own.put("xfm_reserved_cents", 1000000);
                case "inherited" -> a.put("xfm_active_account", v.account("inherited", a, 1000000));
                default -> throw new AssertionError(defect);
            }
            BigDecimal stock = v.cashStock(); v.run("xfm_futures_ai_size_order_effect", a);
            assertEquals(0, a.integer("xfm_futures_lots"), defect); assertEquals(0, a.integer("xfm_futures_ai_size_result"), defect);
            assertEquals(stock, v.cashStock()); assertEquals(0, v.created("xfm_futures_order"));
        }
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
        final Set<String> traits = new HashSet<>();
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
        final Map<String, Datum> globals = new HashMap<>();
        final Map<String, List<Node>> globalLists = new HashMap<>();
        final Node exchange, custodian;
        final List<String> trace = new ArrayList<>(); String failType = ""; boolean open = true, randomEnabled = true; int sequence, matchCalls, historyVisits, maxDiscoveryEntries, maxSizingIterations;
        Vm(Map<String, Block> program) {
            this.program = program; custodian = node("technical-owner", ""); exchange = node("exchange", "xfm_finance_exchange"); exchange.owner = custodian;
            globals.put("xfm_exchange", exchange);
            exchange.put("xfm_day", 1); exchange.put("xfm_ai_seeded", 1); exchange.put("xfm_next_account_id", 0); exchange.put("xfm_next_reservation_id", 0);
            exchange.put("xfm_next_futures_contract_id", 0); exchange.put("xfm_next_futures_position_id", 0);
            exchange.put("xfm_active_orders_count", 0); exchange.put("xfm_futures_open_positions_count", 0);
            exchange.put("xfm_futures_archive_count", 0); exchange.put("xfm_futures_opening_budget_v1", 1);
            exchange.put("xfm_futures_opening_budget_day", 1); exchange.put("xfm_futures_opening_allocated_today", 0); // Fresh bootstrap, advanced to fixture day1.
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
        Node newIndex(int id, String key) {
            execute(substitute(definition("xfm_oracle_create_index_effect"), Map.of("$ID$", Integer.toString(id), "$KEY$", key)), new Frame(exchange, null, exchange));
            return (Node) globals.get(key);
        }
        void counties(int count, int prosperity, int control, boolean war) {
            for (int i = 0; i < count; i++) {
                Node holder = node("county-holder-" + i, ""), county = node("county-" + i, "");
                holder.put("at_war", war ? 1 : 0); county.put("holder", holder);
                county.put("prosperity_level", prosperity); county.put("county_control", control);
                exchange.list("xfm_oracle_counties").add(county);
            }
        }
        BigDecimal cashStock() {
            BigDecimal sum = BigDecimal.ZERO;
            for (Node n : nodes.values()) {
                sum = sum.add(n.gold.multiply(BigDecimal.valueOf(100)));
                if (n.type.equals("xfm_finance_account")) sum = sum.add(number(n.vars.get("xfm_free_cents"))).add(number(n.vars.get("xfm_reserved_cents")));
            }
            return sum.stripTrailingZeros();
        }
        long integerValue(String value, Node node) { return value(program.get(value), new Frame(node, null, node), BigDecimal.ZERO).longValueExact(); }
        boolean validGui(String name, Node node) { return test(definition(name).block("is_valid"), new Frame(node, null, node)); }
        void runGui(String name, Node node) { if (!validGui(name, node)) throw new IllegalArgumentException("invalid GUI action"); execute(definition(name).block("effect"), new Frame(node, null, node)); }
        void run(String name, Node node) { trace.clear(); execute(definition(name), new Frame(node, null, node)); if (Boolean.getBoolean("xfm.subset.trace") && name.equals("xfm_futures_submit_effect") && node.integer("xfm_futures_result") == 0) System.out.println("REJECT reason=" + node.integer("xfm_futures_reason") + " " + trace); }
        Block definition(String name) { Block b = program.get(name); if (b == null) throw new IllegalArgumentException("unknown definition " + name); return b; }
        Datum resolve(String text, Frame f) {
            try { return new NumberDatum(new BigDecimal(text)); } catch (NumberFormatException ignored) { /* scope/value token */ }
            int dot = text.indexOf('.');
            if (dot > 0) { Datum base = resolve(text.substring(0, dot), f); return base instanceof Node n ? resolve(text.substring(dot + 1), f.enter(n)) : null; }
            if (text.equals("this")) return f.here(); if (text.equals("prev")) return f.previous(); if (text.equals("root")) return f.root();
            if (text.startsWith("global_var:")) return globals.get(text.substring(11));
            if (text.equals("story_owner")) return f.here().owner;
            if (text.startsWith("scope:")) return scopes.get(text.substring(6));
            if (text.startsWith("var:")) return f.here().vars.get(text.substring(4));
            if (text.equals("gold")) return new NumberDatum(f.here().gold);
            if (Set.of("holder", "prosperity_level", "county_control").contains(text)) return f.here().vars.get(text);
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
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if (k.equals("is_at_war")) return (f.here().integer("at_war") == 1) == atom(e.value()).equals("yes");
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("has_trait")) return f.here().traits.contains(atom(e.value()));
            if (k.equals("xfm_config_futures_open_trigger")) return open;
            if (k.equals("any_in_list")) {
                Block b = (Block)e.value(); for (Node n : list(f.here(), atom(field(b, "variable")))) if (test(without(b, "variable"), f.enter(n))) return true; return false;
            }
            if (k.endsWith("_trigger") && program.containsKey(k)) return test(definition(k), f);
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
                if (k.equals("while")) {
                    Block child = (Block)e.value(); int iterations = 0;
                    while (test(child.block("limit"), f)) {
                        if (++iterations > 16) throw new IllegalArgumentException("AI size probe exceeded its sixteen-lot bound");
                        execute(without(child, "limit"), f);
                    }
                    maxSizingIterations = Math.max(maxSizingIterations, iterations); continue;
                }
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("remove_variable")) { f.here().vars.remove(atom(e.value())); continue; }
                if (k.equals("set_global_variable")) { Block a = (Block)e.value(); globals.put(atom(field(a, "name")), evaluate(field(a, "value"), f)); continue; }
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
                if (k.equals("add_to_variable_list") || k.equals("remove_list_variable") || k.equals("add_to_global_variable_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "name")); Node target = (Node)evaluate(field(a, "target"), f);
                    List<Node> list = k.equals("add_to_global_variable_list") ? globalLists.computeIfAbsent(name, ignored -> new ArrayList<>()) : f.here().list(name);
                    if (k.equals("remove_list_variable")) list.remove(target); else list.add(target); continue;
                }
                if (k.equals("every_in_list") || k.equals("every_in_global_list") || k.equals("random_in_list") || k.equals("random_in_global_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> list = k.endsWith("in_global_list") ? List.copyOf(globalLists.getOrDefault(name, List.of())) : list(f.here(), name);
                    for (Node n : list) if (test(a.block("limit"), f.enter(n))) {
                        execute(without(without(a, "variable"), "limit"), f.enter(n)); if (!k.startsWith("every_")) break;
                    }
                    continue;
                }
                if (k.equals("random")) { Block a = (Block)e.value(); if (randomEnabled && number(evaluate(field(a, "chance"), f)).signum() > 0) execute(without(a, "chance"), f); continue; }
                if (k.equals("xfm_finance_refresh_beneficiary_effect")) continue; // explicit engine/controller port; fixtures supply authoritative holders
                if (k.equals("xfm_market_ui_futures_book_effect")) continue; // UI-only refresh port; the independent book contract executes its production scripts
                if (k.equals("xfm_futures_match_effect")) { matchCalls++; execute(definition("xfm_futures_finish_incoming_effect"), f); continue; } // no fabricated fill; actual post-match remainder admission/enrolment still runs
                if (e.value() instanceof Block child) { Datum scope = resolve(k, f); if (!(scope instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(child, f.enter(n)); continue; }
                execute(definition(k), f);
            }
        }
    }
    private static Block substitute(Block block, Map<String, String> arguments) {
        return new Block(block.entries().stream().map(entry -> new Entry(entry.key(), entry.operator(),
                entry.value() instanceof Block child ? substitute(child, arguments)
                : new Atom(arguments.getOrDefault(atom(entry.value()), atom(entry.value()))))).toList());
    }
    private static String atom(Value value) { if (!(value instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Value field(Block block, String name) { List<Entry> found = block.named(name); if (found.size() != 1) throw new IllegalArgumentException("one field required " + name); return found.getFirst().value(); }
    private static Block without(Block block, String name) { return new Block(block.entries().stream().filter(e -> !e.key().equals(name)).toList()); }
}
