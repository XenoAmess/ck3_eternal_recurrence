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
        "scripted_effects/xfm_redemption_ai.txt", "scripted_effects/xfm_market_ui_redemption.txt",
        "scripted_guis/xfm_market_redemption.txt", "scripted_effects/xfm_finance_attention.txt",
        "scripted_effects/xfm_finance_otc.txt", "scripted_effects/xfm_finance_assets.txt",
        "scripted_effects/xfm_finance_cash.txt", "scripted_effects/xfm_finance_init.txt",
        "scripted_effects/xfm_finance_policy.txt", "scripted_triggers/xfm_finance_triggers.txt",
        "scripted_triggers/xfm_issuer_triggers.txt", "scripted_effects/xfm_listing_otc.txt",
        "scripted_effects/xfm_listing_daily.txt", "script_values/xfm_finance_values.txt",
        "script_values/xfm_finance_asset_values.txt", "script_values/xfm_issuer_values.txt");
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
    private static final class Vm {
        final Map<String, Block> program; final Map<String, Node> nodes = new LinkedHashMap<>();
        final Map<String, Datum> scopes = new HashMap<>();
        final Map<String, List<Node>> globalLists = new HashMap<>();
        final Node exchange, custodian;
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
