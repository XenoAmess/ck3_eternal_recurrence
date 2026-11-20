package org.xar.ck3.markets.redemption;

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

/** Actual production-script subset, using shared SCRIPT parser. This is NOT CK3 or actual SAVE qualification.
 * Explicit ports: political controller refresh, deterministic random, story factory/failure,
 * event-context capture, unrelated coin/spot/futures AI consumers, and config capacities.
 * Cash/coin delivery, finance positions, public authority predicates, quote checks and receipts execute real scripts.
 */
final class RedemptionScriptContractTest {
    private static final Path SOURCE = Path.of(System.getProperty("xfm.source", ".."));
    private static final Path REFERENCE = Path.of(System.getProperty("xfm.reference.source", SOURCE.toString()));
    private static final List<String> INPUTS = List.of(
        "script_values/xfm_redemption_values.txt", "scripted_triggers/xfm_redemption_triggers.txt",
        "scripted_effects/xfm_redemption_windows.txt", "scripted_effects/xfm_redemption_exchange.txt",
        "scripted_effects/xfm_redemption_reclaim_receipts.txt",
        "scripted_effects/xfm_redemption_ai.txt", "scripted_effects/xfm_market_ui_redemption.txt",
        "scripted_guis/xfm_market_redemption.txt", "scripted_guis/xfm_market_otc_panel.txt",
        "scripted_effects/xfm_finance_attention.txt",
        "scripted_effects/xfm_finance_otc.txt", "scripted_effects/xfm_finance_assets.txt",
        "scripted_effects/xfm_finance_cash.txt", "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_policy.txt", "scripted_triggers/xfm_finance_triggers.txt",
        "scripted_triggers/xfm_issuer_triggers.txt", "scripted_effects/xfm_listing_otc.txt",
        "scripted_effects/xfm_listing_daily.txt", "script_values/xfm_finance_values.txt",
        "script_values/xfm_finance_asset_values.txt", "script_values/xfm_issuer_values.txt",
        "scripted_effects/xfm_issuer_ai_maintenance.txt",
        "scripted_triggers/xfm_issuer_ai_maintenance_triggers.txt",
        "script_values/xfm_issuer_ai_maintenance_values.txt",
        "scripted_effects/xfm_issuer_maintenance.txt",
        "scripted_effects/xfm_finance_maintenance.txt",
        "scripted_triggers/xfm_finance_maintenance_triggers.txt",
        "script_values/xfm_finance_maintenance_values.txt",
        "scripted_effects/xfm_finance_reserve.txt",
        "script_values/xfm_issuer_ai_values.txt",
        "scripted_effects/xfm_listing_transitions.txt");
    public static void main(String[] args) throws Exception {
        int passed = 0, failed = 0;
        for (var method : java.util.Arrays.stream(RedemptionScriptContractTest.class.getDeclaredMethods())
                .filter(m -> m.isAnnotationPresent(Test.class)).filter(m -> args.length == 0 || java.util.Arrays.asList(args).contains(m.getName())).sorted(java.util.Comparator.comparing(java.lang.reflect.Method::getName)).toList()) {
            try { method.invoke(new RedemptionScriptContractTest()); passed++; System.out.println("PASS " + method.getName()); }
            catch (java.lang.reflect.InvocationTargetException e) { failed++; System.out.println("FAIL " + method.getName()); e.getCause().printStackTrace(System.out); }
        }
        System.out.println("REDEMPTION_PRODUCTION_SUBSET groups=" + (passed + failed) + " passed=" + passed + " failed=" + failed + " CK3_NOT_RUN");
        if (failed != 0) throw new IllegalStateException("production subset failures " + failed);
    }


    @Test void controlSuccessionPreservesEscrowIdentityTermsAndIndependentUse() throws IOException {
        Scene s = scene(); publish(s); Node successor = addHolder(s, "successor", 100);
        Node escrow = s.coin.ref("xfm_redemption_account"), window = s.coin.ref("xfm_redemption_window");
        long accountId = escrow.integer("xfm_account_id"), windowId = window.integer("xfm_window_id");
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        Map<String, Datum> oldQuote = prepare(s, s.user, 1);
        s.controller.alive = false; s.coin.put("xfm_authoritative_controller", successor);
        s.v.run("xfm_redemption_refresh_effect", s.coin);
        assertSame(escrow, s.coin.ref("xfm_redemption_account")); assertEquals(accountId, escrow.integer("xfm_account_id"));
        assertSame(successor, escrow.ref("xfm_holder")); assertSame(successor, escrow.ref("xfm_beneficial_owner"));
        assertSame(successor, s.issuer.ref("xfm_holder")); assertSame(successor, s.maker.ref("xfm_beneficial_owner"));
        assertSame(window, s.coin.ref("xfm_redemption_window")); assertEquals(windowId, window.integer("xfm_window_id"));
        assertEquals(20, window.integer("xfm_price_cents")); assertEquals(10, window.integer("xfm_expiry_day"));
        assertEquals(100, window.integer("xfm_remaining_cents")); assertEquals(100, escrow.integer("xfm_free_cents"));
        s.v.restore(oldQuote); s.v.run("xfm_redemption_execute_quote_effect", s.user);
        assertEquals(0, s.user.integer("xfm_redemption_result")); assertEquals(cash, s.v.cashStock());
        successor.put("xfm_redemption_lots", 1); s.v.run("xfm_redemption_prepare_quote_effect", successor);
        assertEquals(0, successor.integer("xfm_redemption_result")); assertEquals(0, s.coin.integer("xfm_actual_utility_cents"));
        redeem(s, s.user, 1);
        Node receipt = s.user.ref("xfm_redemption_last_receipt");
        assertSame(successor, receipt.ref("xfm_controller")); assertSame(s.controller, window.ref("xfm_publisher"));
        assertEquals(accountId, receipt.integer("xfm_payer_account_id")); assertEquals(20, s.coin.integer("xfm_actual_utility_cents"));
        s.v.exchange.put("xfm_day", 10); s.v.run("xfm_redemption_reclaim_effect", successor);
        assertEquals(1, successor.integer("xfm_redemption_result")); assertEquals(1980, s.issuer.integer("xfm_free_cents"));
        assertEquals(0, escrow.integer("xfm_free_cents")); assertEquals(80, window.integer("xfm_reclaimed_cents"));
        assertEquals(accountId, escrow.integer("xfm_account_id")); assertEquals(20, window.integer("xfm_paid_cents"));
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
    }

    @Test void publicationMovesOnlyIssuerFreeAndFreezesTheFiniteTerms() throws IOException {
        Scene s = scene(); BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        publish(s);
        Node w = s.coin.ref("xfm_redemption_window"), escrow = s.coin.ref("xfm_redemption_account");
        assertEquals(1900, s.issuer.integer("xfm_free_cents"));
        assertEquals(500, s.issuer.integer("xfm_reserved_cents"));
        assertEquals(9999, s.maker.integer("xfm_free_cents"));
        assertEquals(100, escrow.integer("xfm_free_cents")); assertEquals(0, escrow.integer("xfm_reserved_cents"));
        assertEquals(1, escrow.integer("xfm_system_account")); assertSame(s.coin, escrow.ref("xfm_legal_entity"));
        assertEquals(20, w.integer("xfm_price_cents")); assertEquals(100, w.integer("xfm_initial_cents")); assertEquals(10, w.integer("xfm_expiry_day"));
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
        s.controller.put("xfm_redemption_price_cents", 200); s.controller.put("xfm_redemption_budget_cents", 500);
        s.v.run("xfm_redemption_publish_effect", s.controller);
        assertEquals(0, s.controller.integer("xfm_redemption_result")); assertSame(w, s.coin.ref("xfm_redemption_window"));
        assertEquals(20, w.integer("xfm_price_cents")); assertEquals(100, escrow.integer("xfm_free_cents"));
        s.v.run("xfm_redemption_reclaim_effect", s.controller);
        assertEquals(0, s.controller.integer("xfm_redemption_result")); assertEquals(100, escrow.integer("xfm_free_cents"));
    }

    @Test void insufficientFrozenWrongAuthorityAndInvalidTermsNeverCreateMoneyOrWindow() throws IOException {
        for (String failure : List.of("insufficient", "negative", "frozen", "wrong-authority", "price-zero", "fractional-price", "fractional-budget", "fractional-expiry", "expired", "too-long", "maker-source")) {
            Scene s = scene();
            switch (failure) {
                case "insufficient" -> s.issuer.put("xfm_free_cents", 99);
                case "negative" -> s.issuer.put("xfm_free_cents", -1);
                case "frozen" -> s.issuer.put("xfm_account_frozen", 1);
                case "wrong-authority" -> s.coin.put("xfm_authoritative_controller", s.user);
                case "price-zero" -> s.controller.put("xfm_redemption_price_cents", 0);
                case "fractional-price" -> s.controller.vars.put("xfm_redemption_price_cents", new NumberDatum(new BigDecimal("20.1")));
                case "fractional-budget" -> s.controller.vars.put("xfm_redemption_budget_cents", new NumberDatum(new BigDecimal("100.1")));
                case "fractional-expiry" -> s.controller.vars.put("xfm_redemption_expiry_day", new NumberDatum(new BigDecimal("10.1")));
                case "expired" -> s.controller.put("xfm_redemption_expiry_day", 1);
                case "too-long" -> s.controller.put("xfm_redemption_expiry_day", 92);
                case "maker-source" -> s.coin.put("xfm_issuer_account", s.maker);
                default -> throw new AssertionError(failure);
            }
            BigDecimal before = s.v.cashStock(), gold = s.controller.gold;
            s.v.run("xfm_redemption_publish_effect", s.controller);
            assertEquals(0, s.controller.integer("xfm_redemption_result"), failure);
            assertFalse(s.coin.vars.containsKey("xfm_redemption_window"), failure);
            assertEquals(before, s.v.cashStock(), failure); assertEquals(gold, s.controller.gold, failure);
        }
    }

    @Test void successfulDeliveryPreservesSupplyAndRecordsOnlyActualPaidUtility() throws IOException {
        Scene s = scene(); publish(s); BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        redeem(s, s.user, 1);
        Node escrow = s.coin.ref("xfm_redemption_account"), window = s.coin.ref("xfm_redemption_window"), receipt = s.user.ref("xfm_redemption_last_receipt");
        assertEquals(70, s.wallet.integer("xfm_free_cents")); assertEquals(80, escrow.integer("xfm_free_cents"));
        assertEquals(300, s.position.integer("xfm_quantity_units"));
        assertEquals(100, escrow.list("xfm_positions").getFirst().integer("xfm_quantity_units"));
        assertEquals(1000, s.coin.integer("xfm_supply_units"));
        assertEquals(20, s.coin.integer("xfm_actual_utility_cents")); assertEquals(20, s.coin.integer("xfm_redemption_lifetime_paid_cents"));
        assertEquals(100, s.coin.integer("xfm_redemption_lifetime_units")); assertEquals(20, s.coin.integer("xfm_project_spent_cents"));
        assertEquals(20, window.integer("xfm_paid_cents")); assertEquals(80, window.integer("xfm_remaining_cents"));
        assertEquals(1, receipt.integer("xfm_receipt_id")); assertEquals(44, receipt.integer("xfm_coin_id"));
        assertEquals(window.integer("xfm_window_id"), receipt.integer("xfm_window_id"));
        assertEquals(escrow.integer("xfm_account_id"), receipt.integer("xfm_payer_account_id"));
        assertEquals(s.wallet.integer("xfm_account_id"), receipt.integer("xfm_payee_account_id"));
        assertEquals(1, receipt.integer("xfm_day")); assertSame(s.coin, receipt.ref("xfm_coin"));
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
        assertEquals(17, s.coin.integer("xfm_price_version")); assertEquals(77, s.coin.integer("xfm_last_price_cents"));
        assertEquals(76, s.coin.integer("xfm_mark_cents")); assertEquals(10000, s.coin.integer("xfm_qualified_volume_cents"));
        assertEquals(0, s.v.exchange.integer("xfm_fee_cents"));
    }

    @Test void reservedCoinsAndOldOtcConsumingAvailableUnitsCauseAtomicRefusal() throws IOException {
        Scene s = scene(); publish(s);
        s.position.put("xfm_reserved_units", 350); s.user.put("xfm_redemption_lots", 1);
        s.v.run("xfm_redemption_prepare_quote_effect", s.user); assertEquals(0, s.user.integer("xfm_redemption_result"));
        s.position.put("xfm_reserved_units", 0);
        Map<String, Datum> quote = prepare(s, s.user, 1);
        Node oldBuyer = s.v.account("old-buyer", s.v.node("old-actor", ""), 1);
        oldBuyer.put("xfm_request_coin", s.coin); oldBuyer.put("xfm_request_target", s.wallet); oldBuyer.put("xfm_request_units", 400); oldBuyer.put("xfm_request_cents", 1);
        s.v.run("xfm_finance_otc_effect", oldBuyer); assertEquals(1, oldBuyer.integer("xfm_result"));
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        s.v.restore(quote); s.v.run("xfm_redemption_execute_quote_effect", s.user);
        assertEquals(0, s.user.integer("xfm_redemption_result")); assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
        assertEquals(0, s.coin.integer("xfm_actual_utility_cents")); assertEquals(100, s.coin.ref("xfm_redemption_window").integer("xfm_remaining_cents"));
        assertTrue(s.v.nodes.values().stream().filter(n -> n.type.equals("xfm_finance_redemption_receipt")).allMatch(n -> n.ended));
    }

    @Test void simultaneousBudgetQuotesCannotOverpayAndOldConfirmationsCannotReplay() throws IOException {
        Scene s = scene(); publish(s); Node other = addHolder(s, "other", 100);
        Map<String, Datum> first = prepare(s, s.user, 1), second = prepare(s, other, 1);
        s.v.restore(first); s.v.run("xfm_redemption_execute_quote_effect", s.user); assertEquals(1, s.user.integer("xfm_redemption_result"));
        BigDecimal cash = s.v.cashStock(); long otherFree = other.ref("xfm_account").integer("xfm_free_cents");
        s.v.restore(second); s.v.run("xfm_redemption_execute_quote_effect", other); assertEquals(0, other.integer("xfm_redemption_result"));
        assertEquals(otherFree, other.ref("xfm_account").integer("xfm_free_cents")); assertEquals(cash, s.v.cashStock());
        redeem(s, other, 1);
        assertEquals(2, other.ref("xfm_redemption_last_receipt").integer("xfm_receipt_id"));
        s.v.restore(first); s.v.run("xfm_redemption_execute_quote_effect", s.user); assertEquals(0, s.user.integer("xfm_redemption_result"));
        assertEquals(40, s.coin.integer("xfm_redemption_lifetime_paid_cents"));
        assertEquals(0, s.user.integer("xfm_redemption_last_action_result"));
        assertEquals(60, s.coin.ref("xfm_redemption_account").integer("xfm_free_cents"));
    }

    @Test void changedAccountCoinTermsControllerDayAndForgedUnitsInvalidateAQuote() throws IOException {
        for (String failure : List.of("active", "holder", "frozen", "coin", "coin-id", "account-id", "price", "controller", "day", "fractional-lot", "wrong-payment")) {
            Scene s = scene(); publish(s); Map<String, Datum> quote = new HashMap<>(prepare(s, s.user, 1));
            switch (failure) {
                case "active" -> s.user.put("xfm_active_account", s.v.account("secondary", s.user, 0));
                case "holder" -> s.wallet.put("xfm_holder", s.controller);
                case "frozen" -> s.wallet.put("xfm_account_frozen", 1);
                case "coin" -> s.user.put("xfm_selected_coin", s.v.node("foreign", "xfm_finance_coin"));
                case "coin-id" -> s.coin.put("xfm_coin_id", 45);
                case "account-id" -> s.wallet.put("xfm_account_id", 777);
                case "price" -> s.coin.ref("xfm_redemption_window").put("xfm_price_cents", 21);
                case "controller" -> s.coin.put("xfm_authoritative_controller", s.v.node("successor", ""));
                case "day" -> s.v.exchange.put("xfm_day", 2);
                case "fractional-lot" -> quote.put("xfm_red_quote_units", new NumberDatum(BigDecimal.valueOf(101)));
                case "wrong-payment" -> quote.put("xfm_red_quote_payment", new NumberDatum(BigDecimal.valueOf(21)));
                default -> throw new AssertionError(failure);
            }
            BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
            s.v.restore(quote); s.v.run("xfm_redemption_execute_quote_effect", s.user);
            assertEquals(0, s.user.integer("xfm_redemption_result"), failure); assertEquals(cash, s.v.cashStock(), failure); assertEquals(coins, s.v.coinStock(s.coin), failure);
            assertEquals(0, s.coin.integer("xfm_actual_utility_cents"), failure);
        }
    }

    @Test void relatedPartiesAndProjectOrFrozenAccountsCannotManufactureUtility() throws IOException {
        for (String failure : List.of("controller", "project", "frozen", "original-publisher")) {
            Scene s = scene(); publish(s); Node actor = s.user;
            switch (failure) {
                case "controller" -> { actor = s.controller; position(s.v, "controller-position", s.coin, actor.ref("xfm_account"), 100); }
                case "project" -> s.wallet.put("xfm_legal_entity", s.coin);
                case "frozen" -> s.wallet.put("xfm_account_frozen", 1);
                case "original-publisher" -> { s.coin.put("xfm_authoritative_controller", s.v.node("successor", "")); actor = s.controller; position(s.v, "old-controller-position", s.coin, actor.ref("xfm_account"), 100); }
                default -> throw new AssertionError(failure);
            }
            actor.put("xfm_redemption_lots", 1); actor.put("xfm_selected_coin", s.coin);
            BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
            s.v.run("xfm_redemption_prepare_quote_effect", actor);
            assertEquals(0, actor.integer("xfm_redemption_result"), failure);
            assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin)); assertEquals(0, s.coin.integer("xfm_actual_utility_cents"));
        }
    }

    @Test void allocationFailuresCannotMakeUnreceiptedPayments() throws IOException {
        for (String failure : List.of("xfm_finance_redemption_receipt", "xfm_finance_position")) {
            Scene s = scene(); publish(s); Map<String, Datum> quote = prepare(s, s.user, 1); s.v.failType = failure;
            BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
            s.v.restore(quote); s.v.run("xfm_redemption_execute_quote_effect", s.user);
            assertEquals(0, s.user.integer("xfm_redemption_result")); assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
            assertEquals(0, s.coin.integer("xfm_actual_utility_cents")); assertEquals(0, s.v.exchange.integer("xfm_next_redemption_receipt_id"));
            assertTrue(s.v.nodes.values().stream().filter(n -> n.type.equals("xfm_finance_redemption_receipt")).allMatch(n -> n.ended));
        }
        for (String failure : List.of("xfm_finance_account", "xfm_finance_redemption_window")) {
            Scene s = scene(); s.v.failType = failure; BigDecimal cash = s.v.cashStock();
            s.v.run("xfm_redemption_publish_effect", s.controller);
            assertEquals(0, s.controller.integer("xfm_redemption_result")); assertEquals(cash, s.v.cashStock()); assertEquals(2000, s.issuer.integer("xfm_free_cents"));
            assertFalse(s.coin.vars.containsKey("xfm_redemption_window"));
        }
    }

    @Test void soldOutDustIsExplicitAndExpiryReturnsOnlyRealUnusedCash() throws IOException {
        Scene s = scene(); s.controller.put("xfm_redemption_budget_cents", 50); publish(s); Node other = addHolder(s, "other", 100);
        redeem(s, s.user, 1); redeem(s, other, 1);
        Node w = s.coin.ref("xfm_redemption_window"), escrow = s.coin.ref("xfm_redemption_account");
        assertEquals(2, w.integer("xfm_status")); assertEquals(10, w.integer("xfm_remaining_cents"));
        Node third = addHolder(s, "third", 100); third.put("xfm_redemption_lots", 1); s.v.run("xfm_redemption_prepare_quote_effect", third); assertEquals(0, third.integer("xfm_redemption_result"));
        s.v.run("xfm_redemption_reclaim_effect", s.controller); assertEquals(0, s.controller.integer("xfm_redemption_result"));
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin); s.v.exchange.put("xfm_day", 10);
        s.v.run("xfm_redemption_reclaim_effect", s.controller);
        assertEquals(1, s.controller.integer("xfm_redemption_result")); assertEquals(0, escrow.integer("xfm_free_cents"));
        assertEquals(1960, s.issuer.integer("xfm_free_cents")); assertEquals(10, w.integer("xfm_reclaimed_cents"));
        assertEquals(w.integer("xfm_initial_cents"), w.integer("xfm_paid_cents") + w.integer("xfm_remaining_cents") + w.integer("xfm_reclaimed_cents"));
        assertEquals(200, escrow.list("xfm_positions").getFirst().integer("xfm_quantity_units"));
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin)); assertEquals(new BigDecimal("100.00"), s.controller.gold);
        s.controller.put("xfm_redemption_expiry_day", 30);
        s.v.run("xfm_redemption_publish_effect", s.controller); assertEquals(0, s.controller.integer("xfm_redemption_result"));
        s.v.exchange.put("xfm_day", 17); s.v.run("xfm_redemption_publish_effect", s.controller);
        assertEquals(1, s.controller.integer("xfm_redemption_result")); assertEquals(2, s.coin.ref("xfm_redemption_window").integer("xfm_window_id"));
        assertEquals(1, w.integer("xfm_window_id")); assertEquals(50, w.integer("xfm_initial_cents"));
        Scene archived = scene(); publish(archived); archived.coin.put("xfm_listing_state", 7);
        archived.v.exchange.put("xfm_day", 10);
        archived.v.run("xfm_redemption_reclaim_effect", archived.controller);
        assertEquals(1, archived.controller.integer("xfm_redemption_result"));
        assertEquals(2000, archived.issuer.integer("xfm_free_cents"));
        assertEquals(0, archived.coin.ref("xfm_redemption_account").integer("xfm_free_cents"));
        archived.v.exchange.put("xfm_day", 17); archived.controller.put("xfm_redemption_expiry_day", 30);
        archived.v.run("xfm_redemption_publish_effect", archived.controller);
        assertEquals(0, archived.controller.integer("xfm_redemption_result"));
    }

    @Test void corruptEscrowReconciliationRefusesToTurnBookBudgetIntoCash() throws IOException {
        for (long free : List.of(-1L, 0L, 99L, 101L)) {
            Scene s = scene(); publish(s); s.coin.ref("xfm_redemption_account").put("xfm_free_cents", free);
            BigDecimal before = s.v.cashStock(); s.user.put("xfm_redemption_lots", 1);
            s.v.run("xfm_redemption_prepare_quote_effect", s.user);
            assertEquals(0, s.user.integer("xfm_redemption_result")); assertEquals(before, s.v.cashStock()); assertEquals(0, s.coin.integer("xfm_actual_utility_cents"));
        }
    }

    @Test void monthlyUtilityWindowResetsWithoutLosingLifetimeOrReceiptEvidence() throws IOException {
        Scene s = scene(); publish(s); redeem(s, s.user, 1); Node receipt = s.user.ref("xfm_redemption_last_receipt");
        s.v.run("xfm_listing_review_demand_effect", s.coin);
        assertEquals(0, s.coin.integer("xfm_actual_utility_cents")); assertEquals(20, s.coin.integer("xfm_redemption_lifetime_paid_cents"));
        assertEquals(20, receipt.integer("xfm_paid_cents")); assertEquals(100, receipt.integer("xfm_paid_units"));
    }

    @Test void aiUsesExistingPaidDecisionOnceAndOnlyItsPrimaryInventory() throws IOException {
        Scene s = scene(); publish(s); s.user.ai = true;
        Node secondary = s.v.account("inherited", s.user, 500000); position(s.v, "secondary-position", s.coin, secondary, 100);
        s.user.put("xfm_active_account", secondary); s.user.list("xfm_finance_watchlist").add(s.coin);
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        s.v.run("xfm_finance_ai_decision_effect", s.user);
        assertEquals(1, s.v.exchange.integer("xfm_ai_decisions_today")); assertEquals(20, s.coin.integer("xfm_actual_utility_cents"));
        assertSame(secondary, s.user.ref("xfm_active_account")); assertEquals(500000, secondary.integer("xfm_free_cents"));
        assertEquals(300, s.position.integer("xfm_quantity_units")); assertEquals(100, secondary.list("xfm_positions").getFirst().integer("xfm_quantity_units"));
        s.v.run("xfm_finance_ai_decision_effect", s.user); s.v.run("xfm_redemption_ai_effect", s.user);
        assertEquals(1, s.v.exchange.integer("xfm_ai_decisions_today")); assertEquals(20, s.coin.integer("xfm_actual_utility_cents"));
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
        assertEquals(1, s.v.businessPorts.get("xfm_spot_ai_effect")); assertEquals(1, s.v.businessPorts.get("xfm_futures_ai_effect"));
    }

    @Test void normalGuiCapturesTermsAndWalletRatherThanLaterMutableInputs() throws IOException {
        Scene s = scene();
        s.controller.put("xfm_redemption_duration_days", 30);
        s.v.runGui("xfm_redemption_publish_gui", s.controller); assertEquals("xfm_redemption.1", s.v.lastEvent);
        Map<String, Datum> publication = s.v.lastEventScopes;
        s.controller.put("xfm_redemption_price_cents", 999); s.controller.put("xfm_redemption_budget_cents", 999);
        s.v.restore(publication); s.v.run("xfm_redemption_confirm_publish_effect", s.controller);
        assertEquals(20, s.coin.ref("xfm_redemption_window").integer("xfm_price_cents")); assertEquals(100, s.coin.ref("xfm_redemption_window").integer("xfm_initial_cents"));
        s.user.put("xfm_redemption_lots", 1); s.v.runGui("xfm_redemption_redeem_gui", s.user); assertEquals("xfm_redemption.2", s.v.lastEvent);
        Map<String, Datum> quote = s.v.lastEventScopes; s.user.put("xfm_redemption_lots", 100);
        s.v.restore(quote); s.v.run("xfm_redemption_execute_quote_effect", s.user);
        assertEquals(100, s.user.ref("xfm_redemption_last_receipt").integer("xfm_paid_units"));
        assertEquals(20, s.user.ref("xfm_redemption_last_receipt").integer("xfm_paid_cents"));
        Scene inheritedControl = scene(); inheritedControl.coin.put("xfm_authoritative_controller", inheritedControl.user);
        BigDecimal before = inheritedControl.v.cashStock();
        inheritedControl.v.runGui("xfm_redemption_initialize_gui", inheritedControl.user);
        assertTrue(inheritedControl.v.validGui("xfm_redemption_controller_gui", inheritedControl.user));
        assertFalse(inheritedControl.v.validGui("xfm_redemption_controller_gui", inheritedControl.controller));
        assertEquals(before, inheritedControl.v.cashStock());
    }

    @Test void ordinaryAcceptedOtcCannotSelectTheDedicatedSystemCash() throws IOException {
        Scene s = scene(); publish(s); Node buyer = s.v.node("otc-buyer", ""); buyer.gold = BigDecimal.ZERO;
        Node escrow = s.coin.ref("xfm_redemption_account"); buyer.put("xfm_account", escrow);
        buyer.put("xfm_otc_seller", s.user);
        s.user.put("xfm_otc_buyer", buyer); s.user.put("xfm_otc_consent", 1); s.user.put("xfm_otc_offer_expires_day", 8);
        s.user.put("xfm_otc_offer_lots", 1); s.user.put("xfm_otc_offer_price_cents", 10); s.user.put("xfm_otc_offer_coin", s.coin);
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        s.v.run("xfm_listing_accept_otc_effect", buyer);
        assertEquals(0, buyer.integer("xfm_issuer_result")); assertNotSame(escrow, buyer.ref("xfm_account"));
        assertEquals(0, buyer.ref("xfm_account").integer("xfm_free_cents")); assertEquals(100, escrow.integer("xfm_free_cents"));
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin)); assertEquals(0, s.coin.integer("xfm_actual_utility_cents"));
    }


    @Test void lifetimeCashAndUnitsRemainWithinExactBoundedCounters() throws IOException {
        for (boolean units : List.of(false, true)) {
            Scene s = scene(); publish(s);
            s.coin.put(units ? "xfm_redemption_lifetime_units" : "xfm_redemption_lifetime_paid_cents", units ? 999999999901L : 999999999981L);
            BigDecimal before = s.v.cashStock(); s.user.put("xfm_redemption_lots", 1);
            s.v.run("xfm_redemption_prepare_quote_effect", s.user);
            assertEquals(0, s.user.integer("xfm_redemption_result")); assertEquals(before, s.v.cashStock());
        }
        Scene exact = scene(); publish(exact);
        exact.coin.put("xfm_redemption_lifetime_paid_cents", 999999999980L); exact.coin.put("xfm_redemption_lifetime_units", 999999999900L);
        redeem(exact, exact.user, 1);
        assertEquals(1000000000000L, exact.coin.integer("xfm_redemption_lifetime_paid_cents"));
        assertEquals(1000000000000L, exact.coin.integer("xfm_redemption_lifetime_units"));
    }

    // These predicates are parsed from the selected production GUI files. The three
    // historical predicates are immutable regression data, not a second GUI implementation.
    @Test void hiddenGuiOriginalPredicatesDiagnoseMissingNumericInputsInStrictMode() throws IOException {
        for (String name : List.of("xfm_market_otc_next_gui", "xfm_market_otc_previous_gui")) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = v.node("fresh-hidden-actor", ""); actor.ai = false;
            MissingTriggerInput error = assertThrows(MissingTriggerInput.class, () -> historicalHiddenGui(v, name, actor));
            assertTrue(error.getMessage().contains(name.contains("next") ? "var:xfm_ui_otc_has_next" : "var:xfm_ui_otc_offset"));
        }
        Scene s = strictHiddenScene();
        s.controller.vars.remove("xfm_redemption_price_cents"); s.controller.vars.remove("xfm_redemption_budget_cents");
        MissingTriggerInput error = assertThrows(MissingTriggerInput.class,
            () -> historicalHiddenGui(s.v, "xfm_redemption_publish_gui", s.controller));
        assertTrue(error.getMessage().contains("var:xfm_redemption_price_cents"));
    }

    @Test void hiddenGuiFreshInputsAreFalseWithoutAnyStrictMissingRead() throws IOException {
        Vm v = vm(); v.strictTriggerInputs = true;
        Node actor = v.node("fresh-hidden-actor", ""); actor.ai = false;
        for (String name : List.of("xfm_market_otc_next_gui", "xfm_market_otc_previous_gui", "xfm_redemption_publish_gui")) {
            assertFalse(v.validGui(name, actor), name);
            assertTrue(actor.vars.isEmpty(), "is_valid must not initialize the inputs");
        }
    }

    @Test void hiddenGuiPartiallyInitializedInputsRemainQuietAndFalse() throws IOException {
        for (String name : List.of("xfm_market_otc_next_gui", "xfm_market_otc_previous_gui")) {
            String numeric = name.contains("next") ? "xfm_ui_otc_has_next" : "xfm_ui_otc_offset";
            for (String missing : List.of(numeric, "xfm_ui_otc_source_coin", "xfm_selected_coin")) {
                Vm v = vm(); v.strictTriggerInputs = true;
                Node actor = hiddenGuiOtcActor(v, true); actor.vars.remove(missing);
                assertFalse(v.validGui(name, actor), name + " missing " + missing);
            }
        }
        for (String missing : List.of("xfm_redemption_price_cents", "xfm_redemption_budget_cents", "xfm_selected_coin")) {
            Scene s = strictHiddenScene(); s.controller.vars.remove(missing);
            assertFalse(s.v.validGui("xfm_redemption_publish_gui", s.controller), missing);
        }
    }

    @Test void hiddenGuiStrictModeIsOptInAndOrdinaryAndDoesNotMaskLaterReads() throws IOException {
        Vm v = vm(); Node actor = v.node("hidden-ai-actor", ""); // is_ai=no is already false
        assertFalse(v.strictTriggerInputs);
        assertFalse(historicalHiddenGui(v, "xfm_market_otc_next_gui", actor));
        v.strictTriggerInputs = true;
        assertThrows(MissingTriggerInput.class, () -> historicalHiddenGui(v, "xfm_market_otc_next_gui", actor));
        // The real trigger_if does not enter its body when the existence limit is false.
        assertFalse(v.validGui("xfm_market_otc_next_gui", actor));
        assertFalse(v.validGui("xfm_redemption_publish_gui", actor));
    }

    @Test void hiddenGuiOriginalReferenceComparisonAlsoDiagnosesMissingCoin() throws IOException {
        for (String name : List.of("xfm_market_otc_next_gui", "xfm_market_otc_previous_gui")) {
            for (String missing : List.of("xfm_ui_otc_source_coin", "xfm_selected_coin")) {
                Vm v = vm(); v.strictTriggerInputs = true;
                Node actor = hiddenGuiOtcActor(v, true); actor.vars.remove(missing);
                MissingTriggerInput error = assertThrows(MissingTriggerInput.class, () -> historicalHiddenGui(v, name, actor));
                assertTrue(error.getMessage().contains("var:" + missing), error.getMessage());
                assertFalse(v.validGui(name, actor));
            }
        }
    }

    @Test void hiddenGuiNextRetainsHasNextAndExactCoinBoundaries() throws IOException {
        for (int hasNext : List.of(0, 1)) for (boolean sameCoin : List.of(false, true)) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = hiddenGuiOtcActor(v, sameCoin); actor.put("xfm_ui_otc_has_next", hasNext);
            assertHiddenGuiEquivalent(v, "xfm_market_otc_next_gui", actor, hasNext == 1 && sameCoin);
        }
    }

    @Test void hiddenGuiPreviousRetainsZeroAndSixteenOffsetBoundaries() throws IOException {
        for (int offset : List.of(0, 15, 16, 32)) for (boolean sameCoin : List.of(false, true)) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = hiddenGuiOtcActor(v, sameCoin); actor.put("xfm_ui_otc_offset", offset);
            assertHiddenGuiEquivalent(v, "xfm_market_otc_previous_gui", actor, offset >= 16 && sameCoin);
        }
    }

    @Test void hiddenGuiInitializedOtcButtonsStillRequireThePlayer() throws IOException {
        for (boolean ai : List.of(false, true)) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = hiddenGuiOtcActor(v, true); actor.ai = ai;
            assertHiddenGuiEquivalent(v, "xfm_market_otc_next_gui", actor, !ai);
            assertHiddenGuiEquivalent(v, "xfm_market_otc_previous_gui", actor, !ai);
        }
    }

    @Test void hiddenGuiPublishRetainsPriceFloorAndBudgetCoverage() throws IOException {
        for (long[] terms : List.of(new long[] {0, 100, 0}, new long[] {1, 1, 1},
                new long[] {20, 19, 0}, new long[] {20, 20, 1})) {
            Scene s = strictHiddenScene(); s.controller.put("xfm_redemption_price_cents", terms[0]);
            s.controller.put("xfm_redemption_budget_cents", terms[1]);
            assertHiddenGuiEquivalent(s.v, "xfm_redemption_publish_gui", s.controller, terms[2] == 1);
        }
    }

    @Test void hiddenGuiPublishRetainsRealIssuerFreeAndListingLimits() throws IOException {
        for (int free : List.of(99, 100)) for (int listing : List.of(6, 7)) {
            Scene s = strictHiddenScene(); s.issuer.put("xfm_free_cents", free); s.coin.put("xfm_listing_state", listing);
            assertHiddenGuiEquivalent(s.v, "xfm_redemption_publish_gui", s.controller, free >= 100 && listing <= 6);
        }
    }

    @Test void hiddenGuiPublishAbsentCooldownAndExactCurrentDayAreQuiet() throws IOException {
        for (int nextDay : List.of(-1, 0, 1, 2)) {
            Scene s = strictHiddenScene();
            if (nextDay >= 0) s.coin.put("xfm_redemption_next_publish_day", nextDay);
            assertHiddenGuiEquivalent(s.v, "xfm_redemption_publish_gui", s.controller, nextDay <= 1);
            assertEquals(nextDay >= 0, s.coin.vars.containsKey("xfm_redemption_next_publish_day"));
        }
    }

    @Test void hiddenGuiPublishAbsentOrExpiredEmptyWindowRetainsExactTerms() throws IOException {
        Scene absent = strictHiddenScene();
        assertHiddenGuiEquivalent(absent.v, "xfm_redemption_publish_gui", absent.controller, true);
        assertFalse(absent.coin.vars.containsKey("xfm_redemption_window"));
        for (int expiry : List.of(0, 1, 2)) for (int remaining : List.of(0, 1)) {
            Scene s = strictHiddenScene(); Node window = s.v.node("old-window", "xfm_finance_redemption_window");
            window.put("xfm_expiry_day", expiry); window.put("xfm_remaining_cents", remaining);
            s.coin.put("xfm_redemption_window", window);
            assertHiddenGuiEquivalent(s.v, "xfm_redemption_publish_gui", s.controller, expiry <= 1 && remaining == 0);
            assertEquals(expiry, window.integer("xfm_expiry_day")); assertEquals(remaining, window.integer("xfm_remaining_cents"));
        }
    }

    @Test void hiddenGuiPublishStillRequiresActualControllerAndPlayer() throws IOException {
        Scene other = strictHiddenScene(); other.user.put("xfm_redemption_price_cents", 20); other.user.put("xfm_redemption_budget_cents", 100);
        assertHiddenGuiEquivalent(other.v, "xfm_redemption_publish_gui", other.user, false);
        Scene ai = strictHiddenScene(); ai.controller.ai = true;
        assertHiddenGuiEquivalent(ai.v, "xfm_redemption_publish_gui", ai.controller, false);
    }

    @Test void hiddenGuiRepeatedReadonlyPollingDoesNotInitializeTermsOrInvokeBusiness() throws IOException {
        Scene s = strictHiddenScene();
        Map<Node, Map<String, Datum>> before = new LinkedHashMap<>();
        s.v.nodes.values().forEach(n -> before.put(n, Map.copyOf(n.vars)));
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        for (int poll = 0; poll < 20; poll++) {
            assertFalse(s.v.validGui("xfm_market_otc_next_gui", s.controller));
            assertFalse(s.v.validGui("xfm_market_otc_previous_gui", s.controller));
            assertTrue(s.v.validGui("xfm_redemption_publish_gui", s.controller));
        }
        before.forEach((node, vars) -> assertEquals(vars, node.vars, node.id));
        assertEquals(before.size(), s.v.nodes.size()); assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
        assertEquals("", s.v.lastEvent); assertTrue(s.v.businessPorts.isEmpty());
    }

    @Test void hiddenGuiOmittedSixOriginalScalarButtonsExposeTheActualMissingReads() throws IOException {
        for (HiddenScalarBoundary b : hiddenScalarBoundaries()) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = v.node("fresh-scalar", ""); actor.ai = false;
            MissingTriggerInput error = assertThrows(MissingTriggerInput.class,
                () -> remainingHistoricalHiddenGui(v, b.gui(), actor));
            assertTrue(error.getMessage().contains("var:" + b.variable()), b.gui());
            assertFalse(v.validGui(b.gui(), actor));
            assertTrue(actor.vars.isEmpty());
        }
    }

    @Test void hiddenGuiEveryControlFromBothActualFilesIsQuietForFreshHumanAndAi() throws IOException {
        List<String> names = allSelectedHiddenGuiNames();
        assertEquals(26, names.size(), "Review every authored GUI when this two-file surface changes");
        for (boolean ai : List.of(false, true)) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = v.node("fresh-complete", ""); actor.ai = ai;
            Map<Node, Map<String, Datum>> before = snapshotHiddenNodes(v);
            for (String name : names) assertFalse(v.validGui(name, actor), name);
            assertHiddenReadonly(v, before, Map.of(), "");
        }
    }

    @Test void hiddenGuiEveryControlRemainsQuietUnderIndependentPartialInitialization() throws IOException {
        List<String> partials = List.of("xfm_redemption_price_cents", "xfm_redemption_budget_cents",
            "xfm_redemption_lots", "xfm_redemption_duration_days", "xfm_ui_otc_has_next", "xfm_ui_otc_offset",
            "xfm_ui_otc_page_offset", "selected-only", "partial-window", "all-inputs-partial-window", "row-id-only");
        for (String partial : partials) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = v.node("partial-actor", ""); actor.ai = false;
            if (partial.startsWith("xfm_")) actor.put(partial, 1);
            else if (partial.equals("row-id-only")) v.scopes.put("xfm_ui_row_id", new NumberDatum(BigDecimal.ONE));
            else {
                Node coin = v.node("partial-coin", "xfm_finance_coin"); actor.put("xfm_selected_coin", coin);
                if (!partial.equals("selected-only")) coin.put("xfm_redemption_window", v.node("partial-window", "xfm_finance_redemption_window"));
                if (partial.equals("all-inputs-partial-window")) {
                    actor.put("xfm_redemption_price_cents", 20); actor.put("xfm_redemption_budget_cents", 100);
                    actor.put("xfm_redemption_lots", 1); actor.put("xfm_order_lots", 1); actor.put("xfm_order_limit_cents", 20);
                }
            }
            Map<Node, Map<String, Datum>> before = snapshotHiddenNodes(v); Map<String, Datum> scopes = v.capture();
            for (String name : allSelectedHiddenGuiNames())
                assertDoesNotThrow(() -> v.validGui(name, actor), partial + " / " + name);
            assertHiddenReadonly(v, before, scopes, "");
        }
    }

    @Test void hiddenGuiSixScalarButtonsKeepExactInitializedThresholdsAndRealUiChanges() throws IOException {
        for (HiddenScalarBoundary b : hiddenScalarBoundaries()) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = v.node("initialized-scalar", ""); actor.ai = false;
            actor.put(b.variable(), b.blocked());
            assertFalse(remainingHistoricalHiddenGui(v, b.gui(), actor), b.gui());
            assertFalse(v.validGui(b.gui(), actor), b.gui());
            actor.put(b.variable(), b.allowed());
            assertTrue(remainingHistoricalHiddenGui(v, b.gui(), actor), b.gui());
            assertTrue(v.validGui(b.gui(), actor), b.gui());
            v.runGui(b.gui(), actor); // The selected production effect, not a hand-written update.
            assertEquals(b.allowed() + b.delta(), actor.integer(b.variable()), b.gui());
            assertEquals(1, actor.vars.size()); assertEquals("", v.lastEvent); assertTrue(v.businessPorts.isEmpty());
            actor.ai = true;
            assertFalse(v.validGui(b.gui(), actor));
        }
    }

    @Test void hiddenGuiWindowStatusAndExpiryReadsRemainSafeAndKeepTheirBoundaries() throws IOException {
        for (int expiry : List.of(0, 1, 2)) for (int status : List.of(1, 2)) {
            Scene s = strictHiddenScene(); Node window = s.v.node("display-window", "xfm_finance_redemption_window");
            window.put("xfm_expiry_day", expiry); window.put("xfm_status", status); s.coin.put("xfm_redemption_window", window);
            assertEquals(expiry <= 1, s.v.validGui("xfm_redemption_expired_gui", s.controller));
            assertEquals(status == 2, s.v.validGui("xfm_redemption_sold_out_gui", s.controller));
            window.vars.remove("xfm_expiry_day"); assertFalse(s.v.validGui("xfm_redemption_expired_gui", s.controller));
            window.vars.remove("xfm_status"); assertFalse(s.v.validGui("xfm_redemption_sold_out_gui", s.controller));
            s.v.exchange.vars.remove("xfm_day");
            assertFalse(s.v.validGui("xfm_redemption_expired_gui", s.controller));
        }
    }

    @Test void hiddenGuiRedemptionAndReclaimUseRealPublishedWindowAndRejectSparseDependencies() throws IOException {
        for (String missing : List.of("none", "xfm_status", "xfm_price_cents", "xfm_expiry_day", "xfm_remaining_cents", "xfm_coin", "xfm_redemption_account")) {
            Scene s = scene(); publish(s); s.v.strictTriggerInputs = true; s.user.put("xfm_redemption_lots", 1);
            Node window = s.coin.ref("xfm_redemption_window");
            if (!missing.equals("none")) window.vars.remove(missing);
            assertEquals(missing.equals("none"), s.v.validGui("xfm_redemption_redeem_gui", s.user), missing);
        }
        for (int last : List.of(-1, 0, 1, 2)) {
            Scene s = scene(); publish(s); s.v.strictTriggerInputs = true; s.user.put("xfm_redemption_lots", 1);
            if (last >= 0) s.user.put("xfm_redemption_last_success_day", last);
            assertEquals(last < 1, s.v.validGui("xfm_redemption_redeem_gui", s.user));
        }
        for (String missing : List.of("none", "issuer-free", "escrow-free", "window-expiry", "clock-day")) {
            Scene s = scene(); publish(s); s.v.exchange.put("xfm_day", 10); s.v.strictTriggerInputs = true;
            switch (missing) {
                case "issuer-free" -> s.issuer.vars.remove("xfm_free_cents");
                case "escrow-free" -> s.coin.ref("xfm_redemption_account").vars.remove("xfm_free_cents");
                case "window-expiry" -> s.coin.ref("xfm_redemption_window").vars.remove("xfm_expiry_day");
                case "clock-day" -> s.v.exchange.vars.remove("xfm_day");
                case "none" -> { }
                default -> throw new AssertionError(missing);
            }
            assertEquals(missing.equals("none"), s.v.validGui("xfm_redemption_reclaim_gui", s.controller), missing);
        }
    }

    @Test void hiddenGuiCompleteSurfaceRepeatedPollingNeverInitializesTermsOrInvokesBusiness() throws IOException {
        Scene s = strictHiddenScene();
        s.controller.put("xfm_redemption_lots", 1); s.controller.put("xfm_redemption_duration_days", 7);
        Map<Node, Map<String, Datum>> before = snapshotHiddenNodes(s.v); Map<String, Datum> scopes = s.v.capture();
        BigDecimal cash = s.v.cashStock(), coins = s.v.coinStock(s.coin);
        for (int poll = 0; poll < 20; poll++) for (String name : allSelectedHiddenGuiNames())
            assertDoesNotThrow(() -> s.v.validGui(name, s.controller), name);
        assertHiddenReadonly(s.v, before, scopes, "");
        assertEquals(cash, s.v.cashStock()); assertEquals(coins, s.v.coinStock(s.coin));
    }

    private record HiddenScalarBoundary(String gui, String variable, long blocked, long allowed, long delta) { }
    private static List<HiddenScalarBoundary> hiddenScalarBoundaries() {
        return List.of(
            new HiddenScalarBoundary("xfm_redemption_price_up_gui", "xfm_redemption_price_cents", 1000000, 999999, 1),
            new HiddenScalarBoundary("xfm_redemption_price_down_gui", "xfm_redemption_price_cents", 1, 2, -1),
            new HiddenScalarBoundary("xfm_redemption_budget_up_gui", "xfm_redemption_budget_cents", 99999901, 99999900, 100),
            new HiddenScalarBoundary("xfm_redemption_budget_down_gui", "xfm_redemption_budget_cents", 100, 101, -100),
            new HiddenScalarBoundary("xfm_redemption_lots_up_gui", "xfm_redemption_lots", 100, 99, 1),
            new HiddenScalarBoundary("xfm_redemption_lots_down_gui", "xfm_redemption_lots", 1, 2, -1));
    }
    private static List<String> allSelectedHiddenGuiNames() throws IOException {
        List<String> names = new ArrayList<>();
        for (String relative : List.of("common/scripted_guis/xfm_market_redemption.txt", "common/scripted_guis/xfm_market_otc_panel.txt")) {
            Path source = SOURCE.resolve(relative); if (!Files.exists(source)) source = REFERENCE.resolve(relative);
            for (Entry e : Clausewitz.parse(Files.readString(source)).entries()) {
                if (!(e.value() instanceof Block b) || b.entries().stream().noneMatch(entry -> entry.key().equals("is_valid")))
                    throw new IllegalArgumentException("selected scripted GUI missing is_valid: " + e.key());
                names.add(e.key());
            }
        }
        return List.copyOf(names);
    }
    private static Map<Node, Map<String, Datum>> snapshotHiddenNodes(Vm v) {
        Map<Node, Map<String, Datum>> result = new LinkedHashMap<>();
        v.nodes.values().forEach(node -> result.put(node, Map.copyOf(node.vars))); return result;
    }
    private static void assertHiddenReadonly(Vm v, Map<Node, Map<String, Datum>> before, Map<String, Datum> scopes, String event) {
        before.forEach((node, vars) -> assertEquals(vars, node.vars, node.id));
        assertEquals(before.size(), v.nodes.size()); assertEquals(scopes, v.capture());
        assertEquals(event, v.lastEvent); assertTrue(v.businessPorts.isEmpty());
    }
    private static boolean remainingHistoricalHiddenGui(Vm v, String name, Node actor) throws IOException {
        try (var input = RedemptionScriptContractTest.class.getResourceAsStream("/fixtures/hidden_gui_r0033_remaining_before.txt")) {
            if (input == null) throw new IOException("missing actual complete pre-candidate two-file source fixture");
            Block actualBefore = Clausewitz.parse(new String(input.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            return v.test(((Block)field(actualBefore, name)).block("is_valid"), new Frame(actor, null, actor));
        }
    }

    @Test void hiddenGuiOptionalMakerAbsenceRemainsLegalAndForbiddenAliasesStillFail() throws IOException {
        Scene empty = strictHiddenScene(); empty.v.eagerOptionalBranches = true;
        empty.coin.vars.remove("xfm_market_maker_account");
        assertThrows(MissingTriggerInput.class,
            () -> remainingHistoricalHiddenPredicate(empty.v, "xfm_redemption_controller_trigger", empty.controller));
        assertTrue(empty.v.validGui("xfm_redemption_controller_gui", empty.controller));
        assertTrue(empty.v.validGui("xfm_redemption_publish_gui", empty.controller));

        Scene live = scene(); publish(live); live.v.strictTriggerInputs = true; live.v.eagerOptionalBranches = true;
        live.coin.vars.remove("xfm_market_maker_account"); live.user.put("xfm_redemption_lots", 1);
        assertThrows(MissingTriggerInput.class,
            () -> remainingHistoricalHiddenPredicate(live.v, "xfm_redemption_account_trigger", live.coin));
        assertTrue(live.v.validGui("xfm_redemption_redeem_gui", live.user));
        live.v.exchange.put("xfm_day", 10);
        assertTrue(live.v.validGui("xfm_redemption_reclaim_gui", live.controller));

        Scene issuerAlias = strictHiddenScene(); issuerAlias.v.eagerOptionalBranches = true;
        issuerAlias.coin.put("xfm_market_maker_account", issuerAlias.issuer);
        assertFalse(issuerAlias.v.validGui("xfm_redemption_controller_gui", issuerAlias.controller));
        assertFalse(issuerAlias.v.validGui("xfm_redemption_publish_gui", issuerAlias.controller));

        Scene escrowAlias = scene(); publish(escrowAlias); escrowAlias.v.strictTriggerInputs = true; escrowAlias.v.eagerOptionalBranches = true;
        escrowAlias.user.put("xfm_redemption_lots", 1);
        escrowAlias.coin.put("xfm_market_maker_account", escrowAlias.coin.ref("xfm_redemption_account"));
        assertFalse(escrowAlias.v.validGui("xfm_redemption_redeem_gui", escrowAlias.user));
        escrowAlias.v.exchange.put("xfm_day", 10);
        assertFalse(escrowAlias.v.validGui("xfm_redemption_reclaim_gui", escrowAlias.controller));
    }

    @Test void hiddenGuiOtcRowReadinessRejectsIncompleteCachedEntriesBeforeOriginalLookup() throws IOException {
        for (String missing : List.of("quantity", "coin", "account", "account-id", "holder", "holder-primary", "free", "frozen")) {
            Vm v = vm(); v.strictTriggerInputs = true;
            Node actor = v.node("row-actor", ""), buyer = v.node("row-buyer", ""), coin = v.node("row-coin", "xfm_finance_coin"); actor.ai = false;
            Node account = v.account("row-account", buyer, 100); buyer.put("xfm_account", account);
            Node position = v.node("row-position", "xfm_finance_position"); position.put("xfm_quantity_units", 100);
            position.put("xfm_coin", coin); position.put("xfm_account", account);
            actor.put("xfm_selected_coin", coin); actor.put("xfm_ui_otc_source_coin", coin);
            actor.put("xfm_ui_otc_page_offset", 0); actor.put("xfm_ui_otc_offset", 0);
            actor.list("xfm_ui_otc_buyers").add(position); v.scopes.put("xfm_ui_row_id", new NumberDatum(BigDecimal.ONE));
            switch (missing) {
                case "quantity" -> position.vars.remove("xfm_quantity_units");
                case "coin" -> position.vars.remove("xfm_coin");
                case "account" -> position.vars.remove("xfm_account");
                case "account-id" -> account.vars.remove("xfm_account_id");
                case "holder" -> account.vars.remove("xfm_holder");
                case "holder-primary" -> buyer.vars.remove("xfm_account");
                case "free" -> account.vars.remove("xfm_free_cents");
                case "frozen" -> account.vars.remove("xfm_account_frozen");
                default -> throw new AssertionError(missing);
            }
            Map<Node, Map<String, Datum>> before = snapshotHiddenNodes(v); Map<String, Datum> scopes = v.capture();
            assertFalse(v.validGui("xfm_market_otc_select_buyer_gui", actor), missing);
            assertFalse(v.trace.stream().anyMatch(row -> row.contains("xfm_market_otc_select_buyer_gui_row_valid_trigger")),
                "Incomplete cache must stop before the original row lookup, rather than testing an unknown predicate port");
            assertHiddenReadonly(v, before, scopes, "");
        }
    }

    private static boolean remainingHistoricalHiddenPredicate(Vm v, String name, Node actor) throws IOException {
        try (var input = RedemptionScriptContractTest.class.getResourceAsStream("/fixtures/hidden_gui_r0033_remaining_before.txt")) {
            if (input == null) throw new IOException("missing actual pre-candidate trigger source fixture");
            Block actualBefore = Clausewitz.parse(new String(input.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            return v.test((Block)field(actualBefore, name), new Frame(actor, null, actor));
        }
    }

    private static Scene strictHiddenScene() throws IOException { Scene s = scene(); s.v.strictTriggerInputs = true; return s; }
    private static Node hiddenGuiOtcActor(Vm v, boolean sameCoin) {
        Node actor = v.node("hidden-actor", ""), source = v.node("source-coin", "xfm_finance_coin"); actor.ai = false;
        actor.put("xfm_ui_otc_has_next", 1); actor.put("xfm_ui_otc_offset", 16); actor.put("xfm_ui_otc_source_coin", source);
        actor.put("xfm_selected_coin", sameCoin ? source : v.node("other-coin", "xfm_finance_coin")); return actor;
    }
    private static void assertHiddenGuiEquivalent(Vm v, String name, Node actor, boolean expected) throws IOException {
        assertEquals(expected, historicalHiddenGui(v, name, actor), "initialized historical " + name);
        assertEquals(expected, v.validGui(name, actor), "selected production " + name);
    }
    private static boolean historicalHiddenGui(Vm v, String name, Node actor) throws IOException {
        try (var input = RedemptionScriptContractTest.class.getResourceAsStream("/fixtures/hidden_gui_r0033_before.txt")) {
            if (input == null) throw new IOException("missing actual historical hidden-GUI regression input");
            Block source = Clausewitz.parse(new String(input.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
            Block gui = (Block)field(source, name);
            return v.test(gui.block("is_valid"), new Frame(actor, null, actor));
        }
    }


    @Test void newAiReceiptSnapshotsEngineIdentityAndActualPrimaryAfterRealAtomicPayment() throws IOException {
        Scene s=scene();publish(s);s.user.ai=true;s.user.list("xfm_finance_watchlist").add(s.coin);
        BigDecimal cash=s.v.cashStock(),coins=s.v.coinStock(s.coin);
        s.v.run("xfm_redemption_ai_effect",s.user);
        Node r=s.user.ref("xfm_redemption_last_receipt");assertNotNull(r);
        assertEquals(1,r.integer("xfm_redeemer_identity_version"));assertEquals(1,r.integer("xfm_redeemer_is_ai"));
        assertEquals(1,r.integer("xfm_redeemer_primary_known"));assertEquals(1,r.integer("xfm_redeemer_used_primary"));
        assertSame(s.user,r.ref("xfm_holder"));assertSame(s.wallet,r.ref("xfm_redeemer_primary_account"));
        assertSame(s.wallet,r.ref("xfm_payee_account"));assertEquals(s.wallet.integer("xfm_account_id"),r.integer("xfm_redeemer_primary_account_id"));
        assertEquals(100,r.integer("xfm_paid_units"));assertEquals(20,r.integer("xfm_paid_cents"));
        assertEquals(cash,s.v.cashStock());assertEquals(coins,s.v.coinStock(s.coin));
        Map<String,Datum> original=Map.copyOf(r.vars);s.v.run("xfm_redemption_ai_effect",s.user);
        assertEquals(original,r.vars);assertEquals(1,s.v.exchange.integer("xfm_next_redemption_receipt_id"));
    }

    @Test void humanOneLotWithMatchingAiDayDoesNotBecomeAiAndSecondaryDoesNotBecomePrimary() throws IOException {
        Scene primary=scene();publish(primary);primary.user.put("xfm_last_redemption_ai_day",1);
        redeem(primary,primary.user,1);Node first=primary.user.ref("xfm_redemption_last_receipt");
        assertEquals(1,first.integer("xfm_day"));assertEquals(100,first.integer("xfm_paid_units"));
        assertEquals(0,first.integer("xfm_redeemer_is_ai"));assertEquals(1,first.integer("xfm_redeemer_used_primary"));
        Scene secondary=scene();publish(secondary);
        Node extra=secondary.v.account("human-secondary",secondary.user,0);
        secondary.user.put("xfm_active_account",extra);
        position(secondary.v,"secondary-position",secondary.coin,extra,100);
        secondary.position.put("xfm_quantity_units",300);
        BigDecimal cash=secondary.v.cashStock(),coins=secondary.v.coinStock(secondary.coin);
        redeem(secondary,secondary.user,1);Node second=secondary.user.ref("xfm_redemption_last_receipt");
        assertEquals(0,second.integer("xfm_redeemer_is_ai"));assertEquals(1,second.integer("xfm_redeemer_primary_known"));
        assertEquals(0,second.integer("xfm_redeemer_used_primary"));
        assertSame(secondary.wallet,second.ref("xfm_redeemer_primary_account"));assertSame(extra,second.ref("xfm_payee_account"));
        assertEquals(20,extra.integer("xfm_free_cents"));assertEquals(cash,secondary.v.cashStock());assertEquals(coins,secondary.v.coinStock(secondary.coin));
    }

    @Test void realAiVisitStampWithoutCandidateOrAvailableUnitsIsNotAReceipt() throws IOException {
        for(boolean hasCandidate:List.of(false,true)) {
            Scene s=scene();publish(s);s.user.ai=true;
            if(hasCandidate){s.user.list("xfm_finance_watchlist").add(s.coin);s.position.put("xfm_reserved_units",400);}
            BigDecimal cash=s.v.cashStock(),coins=s.v.coinStock(s.coin);
            s.v.run("xfm_redemption_ai_effect",s.user);
            assertEquals(1,s.user.integer("xfm_last_redemption_ai_day"));assertFalse(s.user.vars.containsKey("xfm_redemption_last_receipt"));
            assertEquals(0,s.v.exchange.integer("xfm_next_redemption_receipt_id"));
            assertEquals(cash,s.v.cashStock());assertEquals(coins,s.v.coinStock(s.coin));
        }
    }

    @Test void malformedOrMissingPrimaryIsUnknownAndQuietWithoutBlockingLegitimateSecondaryDelivery() throws IOException {
        for(String missing:List.of("id","fractional-id","holder","beneficiary","system","primary")) {
            Scene s=scene();publish(s);Node extra=s.v.account("secondary-"+missing,s.user,0);
            s.user.put("xfm_active_account",extra);position(s.v,"secondary-units-"+missing,s.coin,extra,100);s.position.put("xfm_quantity_units",300);
            switch(missing){
                case "id"->s.wallet.vars.remove("xfm_account_id");
                case "fractional-id"->s.wallet.vars.put("xfm_account_id",new NumberDatum(new BigDecimal("10.5")));
                case "holder"->s.wallet.put("xfm_holder",s.controller);
                case "beneficiary"->s.wallet.put("xfm_beneficial_owner",s.controller);
                case "system"->s.wallet.put("xfm_system_account",1);
                case "primary"->s.user.vars.remove("xfm_account");
                default->throw new AssertionError(missing);
            }
            // Prepare first: the real finance selector can legitimately repair an invalid PRIMARY.
            Map<String,Datum> quote=prepare(s,s.user,1);
            if(missing.equals("primary"))s.user.vars.remove("xfm_account");
            if(missing.equals("holder")||missing.equals("system"))s.user.put("xfm_account",s.wallet);
            BigDecimal cash=s.v.cashStock(),coins=s.v.coinStock(s.coin);
            s.v.restore(quote);s.v.run("xfm_redemption_execute_quote_effect",s.user);
            assertEquals(1,s.user.integer("xfm_redemption_result"));Node r=s.user.ref("xfm_redemption_last_receipt");
            assertEquals(1,r.integer("xfm_redeemer_identity_version"));assertEquals(0,r.integer("xfm_redeemer_is_ai"));
            assertEquals(0,r.integer("xfm_redeemer_primary_known"));
            for(String field:List.of("xfm_redeemer_primary_account","xfm_redeemer_primary_account_id","xfm_redeemer_used_primary"))assertFalse(r.vars.containsKey(field),missing+" "+field);
            assertEquals(cash,s.v.cashStock());assertEquals(coins,s.v.coinStock(s.coin));
            Node fresh=s.v.node("strict-identity-"+missing,"xfm_finance_redemption_receipt");
            s.v.strictTriggerInputs=true;s.v.eagerOptionalBranches=true;
            s.v.execute(redeemerIdentityBlock(s.v),new Frame(fresh,s.user,s.user));
            assertEquals(0,fresh.integer("xfm_redeemer_primary_known"));
        }
    }

    @Test void identitySnapshotNeverOverwritesHistoryOrBackfillsLegacyAndFailedPaymentsRemainUnmarked() throws IOException {
        Scene s=scene();publish(s);s.user.ai=true;redeem(s,s.user,1);Node receipt=s.user.ref("xfm_redemption_last_receipt");
        Map<String,Datum> original=Map.copyOf(receipt.vars);s.user.ai=false;s.user.put("xfm_account",s.v.account("later-primary",s.user,0));
        s.v.execute(redeemerIdentityBlock(s.v),new Frame(receipt,s.user,s.user));assertEquals(original,receipt.vars);
        Node legacy=s.v.node("legacy-receipt","xfm_finance_redemption_receipt");legacy.put("xfm_receipt_id",77);legacy.put("xfm_holder",s.user);legacy.put("xfm_status",1);
        Map<String,Datum> before=Map.copyOf(legacy.vars);s.v.execute(redeemerIdentityBlock(s.v),new Frame(legacy,s.user,s.user));assertEquals(before,legacy.vars);
        Scene failed=scene();publish(failed);Map<String,Datum> quote=prepare(failed,failed.user,1);
        failed.coin.ref("xfm_redemption_account").put("xfm_free_cents",0);failed.v.restore(quote);failed.v.run("xfm_redemption_execute_quote_effect",failed.user);
        assertEquals(0,failed.user.integer("xfm_redemption_result"));
        assertTrue(failed.v.nodes.values().stream().filter(n->n.type.equals("xfm_finance_redemption_receipt")).noneMatch(n->n.vars.containsKey("xfm_redeemer_identity_version")));
    }

    @Test void primaryIdentityIntegerGuardLoadsProductionNamedFloorHelperAndExecutesIt() throws IOException {
        Scene s=scene();publish(s);prepare(s,s.user,1);
        String helper="xfm_redemption_primary_account_id_floor_value";
        Block actual=s.v.definition(helper);
        assertEquals(List.of(new Entry("value","=",new Atom("var:xfm_account_id")),
            new Entry("floor","=",new Atom("yes"))),actual.entries(),"pure helper loaded from production values file");
        Block metadata=redeemerIdentityBlock(s.v);
        assertTrue(metadata.render().contains("var:xfm_account_id >= "+helper));
        assertTrue(metadata.render().contains("var:xfm_account_id <= "+helper));
        BigDecimal cash=s.v.cashStock(),coins=s.v.coinStock(s.coin);
        int sequence=0;
        for(String id:List.of("1","10","10.00001","10.5","0","-1","-0.00001")) {
            BigDecimal value=new BigDecimal(id);s.wallet.vars.put("xfm_account_id",new NumberDatum(value));
            assertEquals(value.setScale(0,RoundingMode.FLOOR).longValueExact(),s.v.integerValue(helper,s.wallet));
            Node probe=s.v.node("helper-id-probe-"+ ++sequence,"xfm_finance_redemption_receipt");
            s.v.execute(metadata,new Frame(probe,s.user,s.user));
            boolean known=id.equals("1")||id.equals("10");
            assertEquals(known?1:0,probe.integer("xfm_redeemer_primary_known"),id);
            if(known){assertSame(s.wallet,probe.ref("xfm_redeemer_primary_account"));assertEquals(value.longValueExact(),probe.integer("xfm_redeemer_primary_account_id"));}
            else for(String field:List.of("xfm_redeemer_primary_account","xfm_redeemer_primary_account_id","xfm_redeemer_used_primary"))assertFalse(probe.vars.containsKey(field),id+" "+field);
        }
        // Prove the actual receipt predicate consumes the loaded helper, rather than a VM name-specific substitute.
        s.wallet.put("xfm_account_id",1007);
        try {
            s.v.program.put(helper,Clausewitz.parse("value = var:xfm_account_id subtract = 1 floor = yes"));
            Node changed=s.v.node("changed-helper-probe","xfm_finance_redemption_receipt");
            s.v.execute(metadata,new Frame(changed,s.user,s.user));
            assertEquals(0,changed.integer("xfm_redeemer_primary_known"));
        } finally {s.v.program.put(helper,actual);}
        Node restored=s.v.node("restored-helper-probe","xfm_finance_redemption_receipt");
        s.v.execute(metadata,new Frame(restored,s.user,s.user));assertEquals(1,restored.integer("xfm_redeemer_primary_known"));
        assertEquals(cash,s.v.cashStock());assertEquals(coins,s.v.coinStock(s.coin));
    }

    private static Block redeemerIdentityBlock(Vm v) {
        Block receipt=(Block)field(v.definition("xfm_redemption_record_receipt_effect"),"scope:xfm_red_new_receipt");
        Entry first=receipt.entries().getFirst();assertEquals("if",first.key());
        assertTrue(first.value().render().contains("xfm_redeemer_identity_version"));
        return new Block(List.of(first));
    }

    @Test void firstRealPositiveReclaimRecordsActualBeforeAndAfterAndPreservesRequest() throws IOException {
        Scene s=scene();publish(s);redeem(s,s.user,1);
        Node w=s.coin.ref("xfm_redemption_window"),escrow=s.coin.ref("xfm_redemption_account");
        assertFalse(w.vars.containsKey("xfm_reclaim_receipt_version"));
        escrow.put("xfm_request_cents",999);s.v.exchange.put("xfm_day",10);
        BigDecimal cash=s.v.cashStock(),coins=s.v.coinStock(s.coin);
        s.v.run("xfm_redemption_reclaim_effect",s.controller);
        assertEquals(1,s.controller.integer("xfm_redemption_result"));assertEquals(1,w.integer("xfm_reclaim_receipt_version"));
        assertSame(w,w.ref("xfm_reclaim_receipt_window"));assertSame(s.coin,w.ref("xfm_reclaim_receipt_coin"));
        assertSame(s.controller,w.ref("xfm_reclaim_receipt_actor"));assertSame(s.issuer,w.ref("xfm_reclaim_receipt_issuer"));assertSame(escrow,w.ref("xfm_reclaim_receipt_escrow"));
        assertEquals(w.integer("xfm_window_id"),w.integer("xfm_reclaim_receipt_window_id"));assertEquals(44,w.integer("xfm_reclaim_receipt_coin_id"));
        assertEquals(s.issuer.integer("xfm_account_id"),w.integer("xfm_reclaim_receipt_issuer_id"));assertEquals(escrow.integer("xfm_account_id"),w.integer("xfm_reclaim_receipt_escrow_id"));
        assertEquals(10,w.integer("xfm_reclaim_receipt_day"));assertEquals(80,w.integer("xfm_reclaim_receipt_amount_cents"));
        assertEquals(100,w.integer("xfm_reclaim_receipt_initial_cents"));
        assertEquals(20,w.integer("xfm_reclaim_receipt_paid_before_cents"));assertEquals(20,w.integer("xfm_reclaim_receipt_paid_after_cents"));
        assertEquals(80,w.integer("xfm_reclaim_receipt_remaining_before_cents"));assertEquals(0,w.integer("xfm_reclaim_receipt_remaining_after_cents"));
        assertEquals(0,w.integer("xfm_reclaim_receipt_reclaimed_before_cents"));assertEquals(80,w.integer("xfm_reclaim_receipt_reclaimed_after_cents"));
        assertEquals(1900,w.integer("xfm_reclaim_receipt_issuer_free_before_cents"));assertEquals(1980,w.integer("xfm_reclaim_receipt_issuer_free_after_cents"));
        assertEquals(500,w.integer("xfm_reclaim_receipt_issuer_reserved_before_cents"));assertEquals(500,w.integer("xfm_reclaim_receipt_issuer_reserved_after_cents"));
        assertEquals(80,w.integer("xfm_reclaim_receipt_escrow_free_before_cents"));assertEquals(0,w.integer("xfm_reclaim_receipt_escrow_free_after_cents"));
        assertEquals(0,w.integer("xfm_reclaim_receipt_escrow_reserved_before_cents"));assertEquals(0,w.integer("xfm_reclaim_receipt_escrow_reserved_after_cents"));
        assertEquals(1,w.integer("xfm_reclaim_receipt_status_before"));assertEquals(4,w.integer("xfm_reclaim_receipt_status_after"));
        assertEquals(80,escrow.integer("xfm_request_cents"),"capture reads the fresh original request, never overwrites it");
        assertEquals(cash,s.v.cashStock());assertEquals(coins,s.v.coinStock(s.coin));assertReclaimPrivateStateCleared(s.v);
    }

    @Test void failedReclaimsNeverCertifyAndMissingEvidenceDoesNotBlockOriginalRealTransfer() throws IOException {
        for(String failure:List.of("early","cash-mismatch","frozen","too-large")) {
            Scene s=scene();publish(s);redeem(s,s.user,1);Node w=s.coin.ref("xfm_redemption_window"),escrow=s.coin.ref("xfm_redemption_account");s.v.exchange.put("xfm_day",10);
            switch(failure){
                case "early"->s.v.exchange.put("xfm_day",9);
                case "cash-mismatch"->escrow.put("xfm_free_cents",79);
                case "frozen"->s.issuer.put("xfm_account_frozen",1);
                case "too-large"->{escrow.put("xfm_free_cents",100000001);w.put("xfm_remaining_cents",100000001);w.put("xfm_initial_cents",100000021);}
                default->throw new AssertionError(failure);
            }
            BigDecimal cash=s.v.cashStock();s.v.run("xfm_redemption_reclaim_effect",s.controller);
            assertEquals(0,s.controller.integer("xfm_redemption_result"),failure);assertTrue(reclaimFacts(w).isEmpty(),failure);
            assertEquals(cash,s.v.cashStock());assertReclaimPrivateStateCleared(s.v);
        }
        for(String missing:List.of("window-id","issuer-id","coin-id-fractional","initial-mismatch")) {
            Scene s=scene();publish(s);redeem(s,s.user,1);Node w=s.coin.ref("xfm_redemption_window");s.v.exchange.put("xfm_day",10);
            switch(missing){
                case "window-id"->w.vars.remove("xfm_window_id");
                case "issuer-id"->s.issuer.vars.remove("xfm_account_id");
                case "coin-id-fractional"->s.coin.vars.put("xfm_coin_id",new NumberDatum(new BigDecimal("44.5")));
                case "initial-mismatch"->w.put("xfm_initial_cents",101);
                default->throw new AssertionError(missing);
            }
            BigDecimal cash=s.v.cashStock();s.v.run("xfm_redemption_reclaim_effect",s.controller);
            assertEquals(1,s.controller.integer("xfm_redemption_result"),"evidence must not gate original payment "+missing);
            assertEquals(1980,s.issuer.integer("xfm_free_cents"));assertTrue(reclaimFacts(w).isEmpty(),missing);
            assertEquals(cash,s.v.cashStock());assertReclaimPrivateStateCleared(s.v);
        }
    }

    @Test void reclaimFactsNeverOverwriteAndHistoricalCompletedWindowsAreNotBackfilled() throws IOException {
        Scene s=scene();publish(s);redeem(s,s.user,1);s.v.exchange.put("xfm_day",10);s.v.run("xfm_redemption_reclaim_effect",s.controller);
        Node w=s.coin.ref("xfm_redemption_window");Map<String,Datum> facts=reclaimFacts(w);assertEquals(29,facts.size());
        s.v.exchange.put("xfm_day",11);s.issuer.put("xfm_free_cents",1990);BigDecimal cash=s.v.cashStock();
        s.v.run("xfm_redemption_reclaim_effect",s.controller);assertEquals(facts,reclaimFacts(w));assertEquals(cash,s.v.cashStock());assertReclaimPrivateStateCleared(s.v);
        Scene legacy=scene();publish(legacy);redeem(legacy,legacy.user,1);legacy.v.exchange.put("xfm_day",10);
        Block complete=legacy.v.definition("xfm_redemption_reclaim_effect");
        legacy.v.program.put("xfm_redemption_reclaim_effect",withoutReclaimEvidenceHooks(complete));
        legacy.v.run("xfm_redemption_reclaim_effect",legacy.controller);
        Node old=legacy.coin.ref("xfm_redemption_window");assertEquals(80,old.integer("xfm_reclaimed_cents"));assertEquals(4,old.integer("xfm_status"));assertTrue(reclaimFacts(old).isEmpty());
        legacy.v.program.put("xfm_redemption_reclaim_effect",complete);legacy.v.run("xfm_redemption_reclaim_effect",legacy.controller);
        assertEquals(1,legacy.controller.integer("xfm_redemption_result"));assertTrue(reclaimFacts(old).isEmpty());assertReclaimPrivateStateCleared(legacy.v);
    }

    @Test void reclaimReceiptRefusesWrongActualCreditReserveRequestIdentityOrWindowAfterRealTransfer() throws IOException {
        Map<String,String> corruptions=Map.of(
            "credit","var:xfm_request_target = { change_variable = { name = xfm_free_cents add = 1 } }",
            "reserve","var:xfm_request_target = { change_variable = { name = xfm_reserved_cents add = 1 } }",
            "request","change_variable = { name = xfm_request_cents add = 1 }",
            "identity","var:xfm_request_target = { change_variable = { name = xfm_account_id add = 1 } }",
            "window","scope:xfm_red_reclaim_coin.var:xfm_redemption_window = { change_variable = { name = xfm_paid_cents add = 1 } }");
        for(var fault:corruptions.entrySet()) {
            Scene s=scene();publish(s);redeem(s,s.user,1);s.v.exchange.put("xfm_day",10);
            Block real=s.v.definition("xfm_finance_transfer_effect");List<Entry> body=new ArrayList<>(real.entries());body.addAll(Clausewitz.parse(fault.getValue()).entries());
            s.v.program.put("xfm_finance_transfer_effect",new Block(body));
            s.v.run("xfm_redemption_reclaim_effect",s.controller);
            assertEquals(1,s.controller.integer("xfm_redemption_result"),"the unchanged business success is not revoked by evidence "+fault.getKey());
            assertTrue(reclaimFacts(s.coin.ref("xfm_redemption_window")).isEmpty(),fault.getKey());assertReclaimPrivateStateCleared(s.v);
        }
    }

    private static Map<String,Datum> reclaimFacts(Node window) {
        Map<String,Datum> facts=new LinkedHashMap<>();window.vars.forEach((key,value)->{if(key.startsWith("xfm_reclaim_receipt_"))facts.put(key,value);});return Map.copyOf(facts);
    }
    private static void assertReclaimPrivateStateCleared(Vm v) {
        for(Node n:v.nodes.values())assertFalse(n.vars.keySet().stream().anyMatch(key->key.startsWith("xfm_rr_")),n.id);
        assertFalse(v.scopes.keySet().stream().anyMatch(key->key.startsWith("xfm_rr_")));
    }
    private static Block withoutReclaimEvidenceHooks(Block original) {
        List<Entry> entries=new ArrayList<>();
        for(Entry e:original.entries())if(!e.key().startsWith("xfm_redemption_reclaim_receipt_"))entries.add(new Entry(e.key(),e.operator(),e.value() instanceof Block b?withoutReclaimEvidenceHooks(b):e.value()));
        return new Block(entries);
    }

    private record Scene(Vm v, Node controller, Node user, Node coin, Node issuer, Node maker, Node wallet, Node position) { }
    private static Scene scene() throws IOException {
        Vm v = vm(); Node c = v.node("controller", ""), u = v.node("user", ""), coin = v.node("coin", "xfm_finance_coin"); c.ai = false; u.ai = false;
        c.gold = new BigDecimal("100.00"); u.gold = new BigDecimal("7.00");
        coin.put("xfm_controller", c); coin.put("xfm_authoritative_controller", c); coin.put("xfm_entity_type", 1);
        coin.put("xfm_listing_state", 1); coin.put("xfm_coin_id", 44); coin.put("xfm_supply_units", 1000);
        coin.put("xfm_actual_utility_cents", 0); coin.put("xfm_project_spent_cents", 0); coin.put("xfm_asset_age", 10);
        coin.put("xfm_price_version", 17); coin.put("xfm_last_price_cents", 77); coin.put("xfm_mark_cents", 76);
        coin.put("xfm_qualified_volume_cents", 10000); coin.put("xfm_best_bid_cents", 15);
        Node issuer = v.account("issuer", c, 2000); issuer.put("xfm_system_account", 1); issuer.put("xfm_legal_entity", coin); issuer.put("xfm_reserved_cents", 500);
        Node maker = v.account("maker", c, 9999); maker.put("xfm_system_account", 1); maker.put("xfm_legal_entity", coin);
        coin.put("xfm_issuer_account", issuer); coin.put("xfm_market_maker_account", maker);
        c.put("xfm_account", v.account("controller-private", c, 10)); c.put("xfm_selected_coin", coin);
        c.put("xfm_redemption_price_cents", 20); c.put("xfm_redemption_budget_cents", 100); c.put("xfm_redemption_expiry_day", 10);
        Node wallet = v.account("wallet", u, 50); u.put("xfm_account", wallet); u.put("xfm_active_account", wallet); u.put("xfm_selected_coin", coin);
        Node position = position(v, "user-position", coin, wallet, 400); position(v, "issuer-position", coin, issuer, 600);
        return new Scene(v, c, u, coin, issuer, maker, wallet, position);
    }
    private static Node position(Vm v, String id, Node coin, Node account, long units) {
        Node p = v.node(id, "xfm_finance_position"); p.owner = v.custodian; p.put("xfm_coin", coin); p.put("xfm_account", account); p.put("xfm_quantity_units", units); p.put("xfm_reserved_units", 0); p.put("xfm_counted", 1);
        account.list("xfm_positions").add(p); account.put("xfm_holdings_count", account.integer("xfm_holdings_count") + 1); coin.list("xfm_holders").add(p); return p;
    }
    private static Node addHolder(Scene s, String id, int units) {
        Node a = s.v.node(id, ""); a.ai = false; Node wallet = s.v.account(id + "-wallet", a, 0);
        a.put("xfm_account", wallet); a.put("xfm_active_account", wallet); a.put("xfm_selected_coin", s.coin);
        position(s.v, id + "-position", s.coin, wallet, units);
        Node issuerPosition = s.issuer.list("xfm_positions").getFirst(); issuerPosition.put("xfm_quantity_units", issuerPosition.integer("xfm_quantity_units") - units); return a;
    }
    private static void publish(Scene s) { s.v.run("xfm_redemption_publish_effect", s.controller); assertEquals(1, s.controller.integer("xfm_redemption_result"), "publication must succeed"); }
    private static Map<String, Datum> prepare(Scene s, Node actor, int lots) { actor.put("xfm_redemption_lots", lots); s.v.run("xfm_redemption_prepare_quote_effect", actor); assertEquals(1, actor.integer("xfm_redemption_result"), "prepare must succeed"); return s.v.capture(); }
    private static void redeem(Scene s, Node actor, int lots) { s.v.restore(prepare(s, actor, lots)); s.v.run("xfm_redemption_execute_quote_effect", actor); assertEquals(1, actor.integer("xfm_redemption_result"), "redemption must succeed"); }
    private static Vm vm() throws IOException {
        Map<String, Block> definitions = new LinkedHashMap<>();
        for (String input : INPUTS) {
            Path p = SOURCE.resolve("common").resolve(input); if (!Files.exists(p)) p = REFERENCE.resolve("common").resolve(input);
            for (Entry e : Clausewitz.parse(Files.readString(p)).entries()) {
                Block b = e.value() instanceof Block block ? block : new Block(List.of(new Entry("value", "=", e.value())));
                if (definitions.put(e.key(), b) != null) throw new IllegalArgumentException("duplicate " + e.key());
            }
        }
        return new Vm(definitions);
    }
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
    private static final class MissingTriggerInput extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        MissingTriggerInput(String expression, Frame frame) {
            super("Missing trigger input at " + frame.here().id + ": " + expression);
        }
    }
    private static final class Vm {
        final Map<String, Block> program; final Map<String, Node> nodes = new LinkedHashMap<>();
        final Map<String, Datum> scopes = new HashMap<>();
        final Map<String, List<Node>> globalLists = new HashMap<>();
        final Node exchange, custodian;
        // Opt-in adversarial hidden-GUI diagnostic: ordinary AND visits all siblings.
        // Missing comparison operands are observable; exists/has_variable remain safe.
        // This models the observed log hazard, not every CK3 evaluation rule.
        boolean strictTriggerInputs;
        boolean eagerOptionalBranches;
        final List<String> trace = new ArrayList<>(); String failType = ""; boolean open = true, randomEnabled = true; int sequence, matchCalls, historyVisits, maxDiscoveryEntries, accountSequence = 1000; String lastEvent = ""; Map<String, Datum> lastEventScopes = Map.of(); final Map<String, Integer> businessPorts = new HashMap<>();
        Vm(Map<String, Block> program) {
            this.program = program; custodian = node("technical-owner", ""); exchange = node("exchange", "xfm_finance_exchange"); exchange.owner = custodian;
            exchange.put("xfm_day", 1); exchange.put("xfm_ai_seeded", 1); exchange.put("xfm_next_account_id", 0); exchange.put("xfm_next_reservation_id", 0);
            exchange.put("xfm_next_futures_contract_id", 0); exchange.put("xfm_next_futures_position_id", 0);
            exchange.put("xfm_active_orders_count", 0); exchange.put("xfm_futures_open_positions_count", 0);
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
            a.put("xfm_system_account", 0); accountSequence = (int)Math.max(accountSequence, exchange.integer("xfm_next_account_id")) + 1; a.put("xfm_account_id", accountSequence); exchange.put("xfm_next_account_id", accountSequence); a.put("xfm_inheritance_state", 0); a.put("xfm_open_orders_count", 0); a.put("xfm_open_positions_count", 0); return a;
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
            return sum.stripTrailingZeros();
        }
        long integerValue(String value, Node node) { return value(program.get(value), new Frame(node, null, node), BigDecimal.ZERO).longValueExact(); }
        Map<String, Datum> capture() { return Map.copyOf(scopes); }
        void restore(Map<String, Datum> context) { scopes.clear(); scopes.putAll(context); }
        BigDecimal coinStock(Node coin) { return nodes.values().stream().filter(n -> n.type.equals("xfm_finance_position") && n.ref("xfm_coin") == coin).map(n -> number(n.vars.get("xfm_quantity_units"))).reduce(BigDecimal.ZERO, BigDecimal::add).stripTrailingZeros(); }
        boolean validGui(String name, Node node) { return test(definition(name).block("is_valid"), new Frame(node, null, node)); }
        void runGui(String name, Node node) { if (!validGui(name, node)) throw new IllegalArgumentException("invalid GUI action"); execute(definition(name).block("effect"), new Frame(node, null, node)); }
        void run(String name, Node node) { trace.clear(); execute(definition(name), new Frame(node, null, node)); if (Boolean.getBoolean("xfm.subset.trace") && name.equals("xfm_futures_submit_effect") && node.integer("xfm_futures_result") == 0) System.out.println("REJECT reason=" + node.integer("xfm_futures_reason") + " " + trace); }
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
        boolean test(Block b, Frame f) {
            boolean all = true;
            Boolean conditional = null;
            for (Entry e : b.entries()) {
                boolean passed;
                if (e.key().equals("trigger_if")) {
                    Block branch = (Block)e.value(); conditional = test(branch.block("limit"), f);
                    passed = !conditional || test(without(branch, "limit"), f);
                } else if (e.key().equals("trigger_else")) {
                    if (conditional == null) throw new IllegalArgumentException("trigger_else without trigger_if");
                    passed = conditional || test((Block)e.value(), f); conditional = null;
                } else passed = check(e, f);
                if (!passed) {
                    if (trace.size() > 40) trace.removeFirst();
                    trace.add(f.here().id + ":" + e.key() + e.operator() + (e.value() instanceof Atom a ? a.token() : "{...}"));
                    if (!strictTriggerInputs) return false;
                    all = false;
                }
            }
            return all;
        }
        boolean check(Entry e, Frame f) {
            String k = e.key();
            if (k.equals("always")) return atom(e.value()).equals("yes");
            if (k.equals("OR")) {
                if (!strictTriggerInputs || !eagerOptionalBranches)
                    return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, f));
                boolean any = false;
                for (Entry branch : ((Block)e.value()).entries()) any |= check(branch, f);
                return any;
            }
            if (k.equals("AND")) return test((Block)e.value(), f);
            if (k.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, f));
            if (k.equals("exists")) return resolve(atom(e.value()), f) != null;
            if (k.equals("has_variable")) return f.here().vars.containsKey(atom(e.value()));
            if (k.equals("is_ai")) return f.here().ai == atom(e.value()).equals("yes");
            if (k.equals("is_alive")) return f.here().alive == atom(e.value()).equals("yes");
            if (k.equals("is_adult")) return f.here().adult == atom(e.value()).equals("yes");
            if (k.equals("story_type")) return f.here().type.equals(atom(e.value()));
            if (k.equals("has_trait")) return f.here().traits.contains(atom(e.value()));
            if (k.equals("trigger_if")) { Block child = (Block)e.value(); return !test(child.block("limit"), f) || test(without(child, "limit"), f); }
            if (k.equals("is_target_in_variable_list")) { Block child = (Block)e.value(); return f.here().list(atom(field(child, "name"))).contains((Node)evaluate(field(child, "target"), f)); }
            if (k.equals("xfm_config_futures_open_trigger")) return open;
            if (k.equals("any_in_list")) {
                Block b = (Block)e.value(); for (Node n : list(f.here(), atom(field(b, "variable")))) if (test(without(b, "variable"), f.enter(n))) return true; return false;
            }
            if (k.endsWith("_trigger") && program.containsKey(k)) return test(definition(k), f);
            if (e.value() instanceof Block child && !(resolve(k, f) instanceof NumberDatum)) {
                Datum scope = resolve(k, f);
                if (strictTriggerInputs && scope == null) throw new MissingTriggerInput(k + " scope predicate", f);
                return scope instanceof Node n && test(child, f.enter(n));
            }
            Datum left = resolve(k, f), right = evaluate(e.value(), f);
            if (strictTriggerInputs && (left == null || right == null))
                throw new MissingTriggerInput(k + " " + e.operator() + " " + (e.value() instanceof Atom a ? a.token() : "{...}"), f);
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
                if (k.equals("save_scope_as")) { scopes.put(atom(e.value()), f.here()); continue; }
                if (k.equals("clear_saved_scope")) { scopes.remove(atom(e.value())); continue; }
                if (k.equals("remove_variable")) { f.here().vars.remove(atom(e.value())); continue; }
                if (k.equals("clear_variable_list")) { f.here().list(atom(e.value())).clear(); continue; }
                if (k.equals("trigger_event")) { lastEvent = atom(e.value()); lastEventScopes = capture(); continue; }
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
                if (k.equals("every_in_list") || k.equals("random_in_list") || k.equals("random_in_global_list")) {
                    Block a = (Block)e.value(); String name = atom(field(a, "variable"));
                    List<Node> list = k.equals("random_in_global_list") ? List.copyOf(globalLists.getOrDefault(name, List.of())) : list(f.here(), name);
                    for (Node n : list) if (test(a.block("limit"), f.enter(n))) {
                        execute(without(without(a, "variable"), "limit"), f.enter(n)); if (!k.equals("every_in_list")) break;
                    }
                    continue;
                }
                if (k.equals("random")) { Block a = (Block)e.value(); if (randomEnabled && number(evaluate(field(a, "chance"), f)).signum() > 0) execute(without(a, "chance"), f); continue; }
                if (k.equals("xfm_issuer_refresh_controller_effect")) { Node authority = f.here().ref("xfm_authoritative_controller"); if (authority != null) f.here().put("xfm_controller", authority); continue; } // explicit existing political authority port
                if (Set.of("xfm_coin_ai_effect", "xfm_spot_ai_effect", "xfm_futures_ai_effect").contains(k)) { businessPorts.merge(k, 1, Integer::sum); continue; } // unrelated business modules, no cash/coin effects in this subset
                if (k.equals("xfm_futures_match_effect")) { matchCalls++; continue; } // no fictitious fill; reservation remains held
                if (e.value() instanceof Block child) { Datum scope = resolve(k, f); if (!(scope instanceof Node n)) throw new IllegalArgumentException("missing effect scope " + k); execute(child, f.enter(n)); continue; }
                execute(definition(k), f);
            }
        }
    }
    private static String atom(Value value) { if (!(value instanceof Atom a)) throw new IllegalArgumentException("atom required"); return a.token(); }
    private static Value field(Block block, String name) { List<Entry> found = block.named(name); if (found.size() != 1) throw new IllegalArgumentException("one field required " + name); return found.getFirst().value(); }
    private static Block without(Block block, String name) { return new Block(block.entries().stream().filter(e -> !e.key().equals(name)).toList()); }
}
