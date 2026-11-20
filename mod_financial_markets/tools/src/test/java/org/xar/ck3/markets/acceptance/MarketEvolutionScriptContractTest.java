package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.markets.acceptance.FollowupFixtureTest.parse;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.acceptance.FollowupContracts.*;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Atom;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Block;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Entry;
import org.xar.ck3.markets.acceptance.FollowupFixtureTest.Expr;

/** Executes the actual emitted read-only effects. Explicit synthetic inputs grant no CK3/business credit. */
final class MarketEvolutionScriptContractTest {
    private static Vm capacityVm() {
        Request input = new Request(2, Profile.AI_CAPACITY, 1, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", null, null, null, null), null, ScaleTier.CONSERVATIVE);
        Vm v = new Vm(input);
        // Explicit software observations of fields written by the actual bootstrap/daily sources, not generated assets.
        v.exchange.put("xfm_active_coin_count", 2048).put("xfm_registered_coin_count", 2200).put("xfm_resident_coin_count", 2100)
                .put("xfm_active_orders_count", 20).put("xfm_futures_open_positions_count", 1024).put("xfm_attention_work_today", 64);
        return v;
    }

    @Test void capacityActualFinanceTailRetainsThirtyWarmAndThreeHundredSixtyFiveImmutableSamples() throws IOException {
        Vm v = capacityVm(); v.arm(); Node o = v.observer(); long start = v.exchange.n("xfm_day");
        assertEquals(1, o.n("xfma_capacity_protocol")); assertTrue(o.nodes("xfma_capacity_days").isEmpty());
        for (int offset = 1; offset <= 395; offset++) {
            v.nativeDate += 24; long previous = o.n("xfma_daily_samples");
            String product = v.productState(); v.observe(); // Real pre-finance ordering must be inert.
            assertEquals(previous, o.n("xfma_daily_samples")); assertEquals(product, v.productState());
            v.exchange.put("xfm_day", start + offset).put("xfm_last_date", v.nativeDate).put("xfm_ai_work_today", 512).put("xfm_ai_decisions_today", 500);
            product = v.productState(); v.afterFinanceTail();
            assertEquals(product, v.productState()); assertEquals(offset, o.nodes("xfma_capacity_days").size());
            Node day = o.nodes("xfma_capacity_days").getLast(); Map<String, Value> immutable = Map.copyOf(day.vars);
            assertEquals(offset, day.n("xfma_record_id")); assertEquals(offset, day.n("xfma_window_day"));
            assertEquals(start + offset, day.n("xfma_financial_day")); assertEquals(v.nativeDate, day.n("xfma_source_script_date"));
            assertEquals(offset > 30 ? 1 : 0, day.n("xfma_measured_sample")); assertEquals(0, day.n("xfma_skipped_financial_days_before"));
            assertEquals(12, day.n("xfma_work_without_decision")); assertEquals(1, day.n("xfma_required_sources_complete"));
            v.exchange.put("xfm_ai_work_today", 100); product = v.productState(); v.observe(); v.afterFinanceTail();
            assertEquals(immutable, day.vars, "same-day refresh cannot rewrite a completed daily sample"); assertEquals(product, v.productState());
        }
        assertEquals(395, o.n("xfma_daily_samples")); assertEquals(365, o.n("xfma_measured_samples"));
        assertEquals(395, o.n("xfma_capacity_day_records")); assertEquals(30, o.n("xfma_capacity_warmup_records")); assertEquals(365, o.n("xfma_capacity_measured_records"));
        assertEquals(0, o.n("xfma_capacity_skipped_financial_days")); assertEquals(0, o.n("xfma_capacity_missing_source_days"));
        assertFalse(o.vars.containsKey("xfma_sample_gap"));
        assertEquals(1, v.logs.stream().filter(log -> log.endsWith("365_daily_samples_after_warmup")).count());
        v.day(start + 396); v.afterFinanceTail(); assertEquals(395, o.nodes("xfma_capacity_days").size());
        assertFalse(v.aliases.containsKey("xfma_capacity_day_record"));
    }

    @Test void capacityMissingCallbackRecordsTheActualGapWithoutBackfillOrWindowCredit() throws IOException {
        Vm v = capacityVm(); v.arm(); Node o = v.observer(); long start = v.exchange.n("xfm_day");
        for (int offset = 1; offset <= 395; offset++) {
            v.day(start + offset); if (offset != 14) v.afterFinanceTail();
        }
        assertEquals(394, o.nodes("xfma_capacity_days").size()); assertEquals(394, o.n("xfma_daily_samples"));
        assertEquals(1, o.n("xfma_capacity_skipped_financial_days")); assertEquals(1, o.n("xfma_sample_gap"));
        Node afterGap = o.nodes("xfma_capacity_days").get(13);
        assertEquals(15, afterGap.n("xfma_window_day")); assertEquals(1, afterGap.n("xfma_skipped_financial_days_before"));
        assertTrue(o.nodes("xfma_capacity_days").stream().noneMatch(day -> day.n("xfma_window_day") == 14));
        assertTrue(v.logs.stream().noneMatch(log -> log.endsWith("365_daily_samples_after_warmup")));
    }

    @Test void capacityZeroMissingAndWorkWithoutDecisionRemainDifferentFacts() throws IOException {
        Vm v = capacityVm(); v.arm(); Node o = v.observer();
        v.exchange.vars.remove("xfm_resident_coin_count"); v.exchange.put("xfm_pending_coin_count", 0).put("xfm_ai_work_today", 0).put("xfm_ai_decisions_today", 0);
        v.day(7); String product = v.productState(); v.afterFinanceTail(); assertEquals(product, v.productState());
        Node first = o.nodes("xfma_capacity_days").getFirst();
        assertEquals(1, first.n("xfma_pending_coin_count_available")); assertEquals(0, first.n("xfma_pending_coin_count"));
        assertEquals(0, first.n("xfma_resident_coin_count_available")); assertFalse(first.vars.containsKey("xfma_resident_coin_count"));
        assertEquals(1, first.n("xfma_work_without_decision_available")); assertEquals(0, first.n("xfma_work_without_decision"));
        assertEquals(1, o.n("xfma_capacity_missing_source_days"));
        v.exchange.put("xfm_resident_coin_count", 2100).put("xfm_ai_work_today", 3).put("xfm_ai_decisions_today", 5);
        v.day(8); v.afterFinanceTail(); Node second = o.nodes("xfma_capacity_days").getLast();
        assertEquals(0, second.n("xfma_work_without_decision_available")); assertFalse(second.vars.containsKey("xfma_work_without_decision"));
        assertEquals(1, o.n("xfma_capacity_invalid_work_days"));
    }

    @Test void capacityOneMissingSourceDayCannotBeErasedByLaterCompleteSamplesOrGrantWindowCredit() throws IOException {
        Vm v = capacityVm(); v.arm(); Node o = v.observer(); long start = v.exchange.n("xfm_day");
        for (int offset = 1; offset <= 395; offset++) {
            if (offset == 14) v.exchange.vars.remove("xfm_resident_coin_count");
            else v.exchange.put("xfm_resident_coin_count", 2100);
            v.day(start + offset); v.afterFinanceTail();
        }
        assertEquals(395, o.n("xfma_capacity_day_records")); assertEquals(365, o.n("xfma_capacity_measured_records"));
        assertFalse(o.vars.containsKey("xfma_sample_gap")); assertEquals(1, o.n("xfma_capacity_missing_source_days"));
        Node missing = o.nodes("xfma_capacity_days").get(13);
        assertEquals(0, missing.n("xfma_resident_coin_count_available")); assertFalse(missing.vars.containsKey("xfma_resident_coin_count"));
        assertTrue(v.logs.stream().noneMatch(log -> log.endsWith("365_daily_samples_after_warmup")));
    }

    @Test void capacityFailedRecordAllocationIsRetainedAndNeverRetriedBySameDayRefresh() throws IOException {
        Vm v = capacityVm(); v.arm(); Node o = v.observer(); v.failRecordCreation = true;
        v.day(7); v.afterFinanceTail(); assertEquals(0, o.n("xfma_capacity_day_records"));
        assertEquals(1, o.n("xfma_capacity_record_allocation_failed")); assertEquals(7, o.n("xfma_capacity_last_attempt_day"));
        v.failRecordCreation = false; int allocated = v.nodes.size(); v.observe(); v.afterFinanceTail();
        assertEquals(allocated, v.nodes.size()); assertEquals(0, o.n("xfma_capacity_day_records"));
        v.day(8); v.afterFinanceTail(); assertEquals(1, o.n("xfma_capacity_day_records"));
        assertEquals(1, o.nodes("xfma_capacity_days").getFirst().n("xfma_skipped_financial_days_before"));
    }

    @Test void capacityStaleArmAndRetainedLegacyObserverNeverCreateOrUpgradeSamples() throws IOException {
        Vm stale = capacityVm(); stale.nativeDate += 24; String product = stale.productState(); stale.arm();
        assertFalse(stale.player.vars.containsKey(stale.input.prefix() + "_story")); assertEquals(product, stale.productState());
        Vm v = capacityVm(); v.arm(); Node old = v.observer(); old.vars.remove("xfma_capacity_protocol");
        Map<String, Value> before = Map.copyOf(old.vars); v.day(7); int allocations = v.nodes.size(); product = v.productState();
        v.afterFinanceTail(); v.observe(); v.arm(); assertEquals(before, old.vars); assertEquals(allocations, v.nodes.size()); assertEquals(product, v.productState());
        assertSame(old, v.observer());
    }

    @Test void capacityTechnicalOwnerHandoffStillSamplesOnlyTheActuallyArmedPlayer() throws IOException {
        Vm v = capacityVm(); v.arm(); Node o = v.observer();
        Node custodian = v.character("capacity-technical-custodian", true); v.exchange.owner = custodian;
        Node other = v.character("capacity-other-player", false); v.players.add(other);
        Node retired = v.node("capacity-retired-e2", "xfma_ai_capacity_e2_observer", false).put("xfma_daily_samples", 12);
        retired.owner = v.player; v.player.ref("xfma_ai_capacity_e2_story", retired).put("xfma_ai_capacity_e2_armed", 1);
        Map<String, Value> retained = Map.copyOf(retired.vars); v.day(7); String product = v.productState(); v.afterFinanceTail();
        assertEquals(1, o.n("xfma_capacity_day_records")); assertEquals(retained, retired.vars); assertEquals(product, v.productState());
        assertFalse(other.vars.containsKey(v.input.prefix() + "_story"));
    }

    private static Request request(String contract, String position) {
        return new Request(2, Profile.MARKET_EVOLUTION, 1, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", contract, position, null, null), null, null);
    }

    @Test void newObservationProfileNeedsNoDebtAndNeverRelaxesLifecycleOrCapacity() {
        assertDoesNotThrow(() -> request(null, null));
        var actor = new ActorBinding(ActorMode.CURRENT_PLAYER, null);
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.LIFECYCLE, 1, actor,
                new Targets("2", "1", null, null, null, null), null, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.MARKET_EVOLUTION, 1, actor,
                new Targets("2", "1", null, null, "9", null), null, null));
        assertThrows(IllegalArgumentException.class, () -> new Request(2, Profile.MARKET_EVOLUTION, 1, actor,
                new Targets("2", "1", null, null, null, null), null, ScaleTier.SMOKE));
        assertEquals(128, ScaleTier.SMOKE.coins());
        assertFalse(request(null, null).markers().stream().anyMatch(m -> m.contains("issuance_readback") || m.contains("claim_accounting")));
    }

    @Test void epochThreeStartsAtTheCurrentDurableDayAndCannotRearmOrMutateOlderEpochs() {
        Request input = new Request(2, Profile.MARKET_EVOLUTION, 3,
                new ActorBinding(ActorMode.CURRENT_PLAYER, null), new Targets("2", "1", null, null, null, null), null, null);
        Vm v = new Vm(input);
        Node e1 = v.node("retained-e1", "xfma_market_evolution_e1_observer", false)
                .put("xfma_start_day", 2).put("xfma_daily_samples", 4);
        Node e2 = v.node("retained-e2", "xfma_market_evolution_e2_observer", false)
                .put("xfma_start_day", 6).put("xfma_daily_samples", 0);
        v.player.put("xfma_market_evolution_e1_armed", 1).ref("xfma_market_evolution_e1_story", e1)
                .put("xfma_market_evolution_e2_armed", 1).ref("xfma_market_evolution_e2_story", e2);
        Map<String, Value> e1Before = Map.copyOf(e1.vars), e2Before = Map.copyOf(e2.vars);
        String product = v.productState();
        v.arm(); Node e3 = v.observer();
        assertEquals("xfma_market_evolution_e3_observer", e3.kind);
        assertEquals(6, e3.n("xfma_start_day"));
        assertEquals(0, e3.n("xfma_daily_samples"));
        assertEquals(1, e3.n("xfma_evolution_day_records"));
        assertSame(e1, v.player.node("xfma_market_evolution_e1_story"));
        assertSame(e2, v.player.node("xfma_market_evolution_e2_story"));
        assertEquals(product, v.productState());
        v.day(7); product = v.productState(); v.observe();
        int allocations = v.nodes.size(), logs = v.logs.size();
        long firstDate = e3.nodes("xfma_evolution_days").getFirst().n("xfma_first_native_date");
        v.arm();
        assertSame(e3, v.observer());
        assertEquals(allocations, v.nodes.size()); assertEquals(logs, v.logs.size());
        assertEquals(6, e3.n("xfma_start_day"));
        assertEquals(1, e3.n("xfma_daily_samples"));
        assertEquals(2, e3.n("xfma_evolution_day_records"));
        assertEquals(firstDate, e3.nodes("xfma_evolution_days").getFirst().n("xfma_first_native_date"));
        v.player.vars.remove("xfma_market_evolution_e3_armed");
        v.arm();
        assertSame(e3, v.observer(), "a retained current story also prevents a second Arm without its flag");
        assertEquals(allocations, v.nodes.size()); assertEquals(logs, v.logs.size());
        assertEquals(1, v.player.n("xfma_market_evolution_e1_armed"));
        assertEquals(1, v.player.n("xfma_market_evolution_e2_armed"));
        assertEquals(e1Before, e1.vars); assertEquals(e2Before, e2.vars);
        assertEquals(product, v.productState(), "observation must not invoke or mutate the financial product");
    }

    @Test void baselineAndRepeatedSameDayReadsDoNotInventCoinsFeesOrDailySamples() {
        Vm v = new Vm(request(null, null)); v.arm(); Node o = v.observer();
        String product = v.productState();
        v.observe(); v.observe();
        assertEquals(1, o.n("xfma_evolution_day_records"));
        assertEquals(0, o.n("xfma_daily_samples"));
        assertEquals(1, o.n("xfma_evolution_coin_records"));
        assertEquals(0, o.n("xfma_new_ai_issues_observed"));
        assertEquals(0, o.n("xfma_new_listings_observed"));
        assertEquals(0, o.n("xfma_expiry_available"));
        assertEquals(product, v.productState());
        assertEquals(1, v.logs.stream().filter(s -> s.endsWith("baseline_inventory_captured")).count());
        Node first = o.nodes("xfma_evolution_days").getFirst();
        v.exchange.put("xfm_fee_cents", 17); v.observe();
        assertEquals(0, first.n("xfma_first_fee_cents"));
        assertEquals(17, first.n("xfma_fee_cents"));
        assertEquals(1, o.n("xfma_evolution_day_records"));
    }

    @Test void staleCalendarReadCannotArmOrRewriteThePreviousFinancialDay() {
        Vm beforeArm = new Vm(request(null, null)); beforeArm.nativeDate += 24;
        String untouched = beforeArm.productState(); beforeArm.arm();
        assertFalse(beforeArm.player.vars.containsKey(beforeArm.input.prefix() + "_story"));
        assertEquals(untouched, beforeArm.productState());

        Vm v = new Vm(request(null, null)); v.arm(); Node o = v.observer();
        Node baseline = o.nodes("xfma_evolution_days").getFirst();
        Map<String, Value> originalDay = Map.copyOf(baseline.vars);
        long refreshes = o.n("xfma_refreshes"); v.nativeDate += 24;
        String product = v.productState(); v.observe();
        assertEquals(originalDay, baseline.vars, "a pre-clock refresh must not relabel yesterday with today's date");
        assertEquals(refreshes, o.n("xfma_refreshes"));
        assertEquals(0, o.n("xfma_daily_samples")); assertEquals(1, o.n("xfma_evolution_day_records"));
        assertEquals(product, v.productState());
    }

    @Test void realAfterFinanceTailSamplesFourteenDaysBeforeAnyGuiRefreshOrSave() throws IOException {
        Vm v = new Vm(request(null, null)); v.arm(); Node o = v.observer();
        long baselineDate = v.nativeDate;
        for (int financialDay = 7; financialDay <= 20; financialDay++) {
            v.nativeDate += 24;
            // The original failure order: an observation callback arrives before the exchange clock.
            long previousSamples = o.n("xfma_daily_samples"); v.observe();
            assertEquals(previousSamples, o.n("xfma_daily_samples"));
            v.exchange.put("xfm_day", financialDay).put("xfm_last_date", v.nativeDate)
                    .put("xfm_fee_cents", financialDay);
            String product = v.productState(); v.afterFinanceTail();
            assertEquals(product, v.productState(), "the genuine tail subscription has no financial writer");
            assertEquals(financialDay - 6, o.n("xfma_daily_samples"));
            assertEquals(financialDay - 5, o.n("xfma_evolution_day_records"));
            Node latest = o.nodes("xfma_evolution_days").getLast();
            assertEquals(financialDay, latest.n("xfma_financial_day"));
            assertEquals(v.nativeDate, latest.n("xfma_first_native_date"));
            assertEquals(v.nativeDate, latest.n("xfma_latest_native_date"));
            assertEquals(financialDay, latest.n("xfma_fee_cents"));
            v.observe(); v.afterFinanceTail();
            assertEquals(financialDay - 6, o.n("xfma_daily_samples"), "same-day GUI and duplicate dispatch stay idempotent");
        }
        assertEquals(14, o.n("xfma_daily_samples")); assertEquals(15, o.n("xfma_evolution_day_records"));
        assertEquals(20, o.n("xfma_last_sample_day")); assertFalse(o.vars.containsKey("xfma_sample_gap"));
        for (int offset = 0; offset <= 14; offset++) {
            Node day = o.nodes("xfma_evolution_days").get(offset);
            assertEquals(6 + offset, day.n("xfma_financial_day"));
            assertEquals(baselineDate + offset * 24L, day.n("xfma_first_native_date"));
            assertEquals(baselineDate + offset * 24L, day.n("xfma_latest_native_date"));
        }
    }

    @Test void technicalCustodianHandoffUsesTheArmedPlayerReferenceAndLeavesRetiredEpochsUntouched() throws IOException {
        Request input = new Request(2, Profile.MARKET_EVOLUTION, 5,
                new ActorBinding(ActorMode.CURRENT_PLAYER, null), new Targets("2", "1", null, null, null, null), null, null);
        Vm v = new Vm(input); v.arm(); Node armed = v.observer();
        Node old = v.node("retired-e4", "xfma_market_evolution_e4_observer", false).put("xfma_daily_samples", 13);
        v.player.ref("xfma_market_evolution_e4_story", old);
        Map<String, Value> retiredBefore = Map.copyOf(old.vars);
        Node otherPlayer = v.character("unarmed-other-player", false); v.players.add(otherPlayer);
        Node custodian = v.character("technical-custodian", true); v.exchange.owner = custodian;
        v.day(7); v.afterFinanceTail();
        assertSame(v.player, armed.owner); assertSame(armed, v.observer());
        assertFalse(custodian.vars.containsKey(input.prefix() + "_story"));
        assertFalse(otherPlayer.vars.containsKey(input.prefix() + "_story"));
        assertEquals(1, armed.n("xfma_daily_samples")); assertEquals(retiredBefore, old.vars);
        // A stale/foreign pointer is not an authorization to read someone else's observer.
        otherPlayer.ref(input.prefix() + "_story", armed);
        v.exchange.owner = v.character("successor-custodian", true); v.day(8); v.afterFinanceTail();
        assertEquals(2, armed.n("xfma_daily_samples")); assertSame(v.player, armed.owner);
        assertEquals(retiredBefore, old.vars);
    }

    @Test void unrelatedOrSystemAccountAndPerpetualTargetCannotBeArmedAsADatedPrivateBaseline() {
        Vm system = new Vm(request(null, null)); system.privateAccount.put("xfm_system_account", 1); system.arm();
        assertFalse(system.observer().vars.containsKey("xfma_ready"));
        assertTrue(system.logs.stream().anyMatch(s -> s.contains("followup_target_missing")));
        Vm foreign = new Vm(request(null, null)); foreign.privateAccount.ref("xfm_holder", foreign.character("other-holder", true)); foreign.arm();
        assertFalse(foreign.observer().vars.containsKey("xfma_ready"));
        Vm perpetual = new Vm(request("3", null));
        perpetual.exchange.nodes("xfm_futures_contracts").add(perpetual.node("perpetual", "xfm_futures_contract", true)
                .put("xfm_contract_id", 3).put("xfm_perpetual", 1).put("xfm_expiry_day", 0));
        perpetual.arm(); assertFalse(perpetual.observer().vars.containsKey("xfma_ready"));
    }

    @Test void newLandlessAiIssueAndRealListedStateUsePermanentIdentityAndFirstObservedRank() {
        Vm v = new Vm(request(null, null)); v.arm();
        Node ai = v.character("landless-ai", true); ai.gold = 5;
        Node privateAccount = v.account("private-ai", 33, ai, 0); privateAccount.put("xfm_system_account", 0); ai.ref("xfm_account", privateAccount);
        Node coin = v.coin("new-ai-coin", 2, ai, 0); coin.put("xfm_actual_raised_cents", 1600).put("xfm_external_raised_cents", 200);
        v.global("xfm_coin_registry").add(coin);
        v.exchange.put("xfm_next_coin_id", 2).put("xfm_registered_coin_count", 2).put("xfm_pending_coin_count", 1);
        v.day(7); String before = v.productState(); v.observe();
        Node sample = v.coinRecord(2);
        assertEquals(1, v.observer().n("xfma_new_ai_issues_observed"));
        assertEquals(1, v.observer().n("xfma_new_landless_ai_issues_observed"));
        assertEquals(0, sample.n("xfma_first_issuer_rank"));
        assertSame(ai, sample.node("xfma_first_original_issuer"));
        assertSame(privateAccount, sample.node("xfma_first_issuer_private_account"));
        assertEquals(100, sample.n("xfma_first_registration_paid_cents"));
        assertEquals(0, sample.n("xfma_actual_registration_transfer_verified"));
        assertEquals(before, v.productState());
        coin.put("xfm_listing_state", 1).put("xfm_listed_day", 8).put("xfm_trading_open", 1)
                .put("xfm_actual_raised_cents", 2000).put("xfm_external_raised_cents", 400);
        v.exchange.put("xfm_active_coin_count", 2).put("xfm_pending_coin_count", 0);
        ai.landed = true; ai.tier = 4;
        v.day(8); v.observe();
        assertEquals(1, v.observer().n("xfma_new_listings_observed"));
        assertEquals(0, sample.n("xfma_first_issuer_rank"), "first observation cannot become an invented issuance-time rank");
        assertEquals(1, sample.n("xfma_latest_listing_state"));
        assertEquals(2, sample.n("xfma_latest_coin_id"));
    }

    @Test void refundWitnessNeedsActualOriginalReservationStateAndMissingAmountsStayUnavailable() {
        Vm v = new Vm(request(null, null)); v.arm();
        Node ai = v.character("issuer", true), buyer = v.character("external", true);
        Node wallet = v.account("external-private", 40, buyer, 0);
        Node coin = v.coin("pending", 2, ai, 0);
        Node subscription = v.node("reservation", "xfm_finance_reservation", true)
                .put("xfm_reservation_id", 90).put("xfm_subscription_state", 0)
                .put("xfm_subscription_paid_cents", 400).put("xfm_remaining_cents", 400).ref("xfm_account", wallet);
        coin.nodes("xfm_subscriptions").add(subscription); v.global("xfm_coin_registry").add(coin);
        v.exchange.put("xfm_next_coin_id", 2).put("xfm_registered_coin_count", 2); v.day(7); v.observe();
        Node record = v.coinRecord(2);
        assertSame(subscription, record.nodes("xfma_subscription_sources").getFirst());
        coin.put("xfm_listing_state", 6).put("xfm_refund_news_recorded", 1);
        subscription.put("xfm_subscription_state", 3); subscription.vars.remove("xfm_remaining_cents");
        v.day(8); v.observe();
        assertEquals(0, record.n("xfma_subscriptions_available"));
        assertEquals(0, record.n("xfma_refund_readback_occurred"));
        assertEquals(1, record.n("xfma_fundraise_failed_occurred"), "failed fundraising does not invent a successful money refund");
        coin.vars.remove("xfm_registration_paid_cents"); v.observe();
        assertEquals(0, record.n("xfma_latest_registration_paid_cents_available"));
        assertFalse(record.vars.containsKey("xfma_latest_registration_paid_cents"), "missing financial value must not become zero");
        subscription.put("xfm_remaining_cents", 0); wallet.put("xfm_free_cents", 400);
        v.observe();
        assertEquals(1, record.n("xfma_subscriptions_available"));
        assertEquals(1, record.n("xfma_refund_readback_occurred"));
        assertEquals(1, v.observer().n("xfma_offer_refunds_observed"));
        assertEquals(0, record.n("xfma_actual_registration_transfer_verified"));
    }

    @Test void exactlyThirtyFiveConsecutiveDaysCompleteObservationWithoutRequiringRandomFeatures() {
        Vm v = new Vm(request(null, null)); v.arm();
        for (int day = 7; day <= 41; day++) { v.day(day); v.observe(); v.observe(); }
        Node o = v.observer();
        assertEquals(36, o.n("xfma_evolution_day_records"));
        assertEquals(35, o.n("xfma_daily_samples"));
        assertEquals(0, o.n("xfma_new_ai_issues_observed"));
        assertEquals(0, o.n("xfma_offer_refunds_observed"));
        assertEquals(0, o.n("xfma_expiry_available"));
        assertEquals(1, v.logs.stream().filter(s -> s.endsWith("35_daily_samples_observed")).count());
        assertFalse(v.logs.stream().anyMatch(s -> s.contains("ai_paid_issuance") || s.contains("surviving_claim")));
        v.day(42); v.observe();
        assertEquals(36, o.n("xfma_evolution_day_records"), "never append beyond the declared observation bound");
    }

    @Test void skippedFinancialDayOrAllocationFailureNeverCompletesAnObservationWindow() {
        Vm gap = new Vm(request(null, null)); gap.arm(); gap.day(8); gap.observe();
        for (int day = 9; day <= 41; day++) { gap.day(day); gap.observe(); }
        assertEquals(1, gap.observer().n("xfma_sample_gap"));
        assertFalse(gap.logs.stream().anyMatch(s -> s.endsWith("35_daily_samples_observed")));
        Vm failed = new Vm(request(null, null)); failed.failRecordCreation = true; failed.arm();
        assertEquals(1, failed.observer().n("xfma_record_allocation_failed"));
        assertTrue(failed.logs.stream().anyMatch(s -> s.contains("TEST FAIL evolution_day_record")));
        assertFalse(failed.logs.stream().anyMatch(s -> s.endsWith("baseline_inventory_captured")));
    }

    @Test void expiryDateReachedIsDistinctFromPendingOrActualTerminalReadback() {
        Vm v = new Vm(request("3", null));
        Node index = v.node("index", "xfm_oracle_index", true).put("xfm_index_id", 3);
        Node contract = v.node("dated", "xfm_futures_contract", true).put("xfm_contract_id", 3)
                .put("xfm_perpetual", 0).put("xfm_expiry_day", 30).put("xfm_status", 0).ref("xfm_coin", index);
        v.exchange.nodes("xfm_futures_contracts").add(contract);
        Node shortAccount = v.account("short-private", 44, v.character("short", true), 5);
        Node longReserve = v.node("long-reserve", "xfm_finance_reservation", true).put("xfm_remaining_cents", 20);
        Node shortReserve = v.node("short-reserve", "xfm_finance_reservation", true).put("xfm_remaining_cents", 20);
        Node position = v.node("paired-position", "xfm_futures_position", true).put("xfm_position_id", 12)
                .put("xfm_status", 0).put("xfm_last_settled_day", 6).ref("xfm_contract", contract)
                .ref("xfm_long_account", v.privateAccount).ref("xfm_short_account", shortAccount)
                .ref("xfm_long_reservation", longReserve).ref("xfm_short_reservation", shortReserve);
        contract.nodes("xfm_positions").add(position); v.arm();
        assertEquals(1, v.observer().n("xfma_expiry_available"));
        assertEquals(1, v.observer().n("xfma_expiry_contract_available"));
        assertEquals(1, v.observer().n("xfma_expiry_positions_available"));
        assertEquals(0, v.observer().n("xfma_expiry_due_occurred"));
        v.day(30); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_due_occurred"));
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
        position.put("xfm_pending_payment", 1).put("xfm_pending_kind", 4); v.observe();
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
        position.vars.remove("xfm_pending_payment"); position.put("xfm_status", 2).put("xfm_last_settled_day", 30);
        contract.nodes("xfm_positions").clear(); longReserve.put("xfm_remaining_cents", 0); shortReserve.put("xfm_remaining_cents", 0);
        String product = v.productState(); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_closed_readback_occurred"));
        assertEquals(12, v.observer().n("xfma_expiry_closed_position_id"));
        assertSame(position, v.observer().node("xfma_expiry_closed_position"));
        assertEquals(product, v.productState());
        assertEquals(30, contract.n("xfm_expiry_day"));
    }

    @Test void readableContractDatesDoNotInventReadablePositionsOrMissingContractStatus() {
        Vm v = new Vm(request("3", null));
        Node contract = v.node("empty-dated", "xfm_futures_contract", true).put("xfm_contract_id", 3)
                .put("xfm_perpetual", 0).put("xfm_expiry_day", 30).put("xfm_status", 0);
        v.exchange.nodes("xfm_futures_contracts").add(contract); v.arm();
        assertEquals(1, v.observer().n("xfma_expiry_contract_available"));
        assertEquals(0, v.observer().n("xfma_expiry_positions_available"));
        assertEquals(0, v.observer().n("xfma_expiry_available"));
        v.day(30); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_due_occurred"));
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
        Node position = v.node("date-only-position", "xfm_futures_position", true).put("xfm_position_id", 22)
                .put("xfm_status", 0).put("xfm_last_settled_day", 30).ref("xfm_contract", contract);
        contract.nodes("xfm_positions").add(position); contract.vars.remove("xfm_status"); v.observe();
        assertEquals(1, v.observer().n("xfma_expiry_contract_available"));
        assertEquals(1, v.observer().n("xfma_expiry_positions_sampled"));
        assertEquals(0, v.observer().n("xfma_watched_status_available"));
        assertEquals(0, v.observer().n("xfma_expiry_positions_available"));
        assertEquals(0, v.observer().n("xfma_expiry_available"));
        assertEquals(0, v.observer().n("xfma_expiry_closed_readback_occurred"));
    }

    @Test void finiteCoinCapacityIsRecheckedInsideTheIteratorAndTruncationIsExplicit() {
        Vm v = new Vm(request(null, null));
        for (int id = 2; id <= 63; id++) v.global("xfm_coin_registry").add(v.coin("old-" + id, id, v.player, 1));
        v.exchange.put("xfm_next_coin_id", 63).put("xfm_registered_coin_count", 63).put("xfm_active_coin_count", 63);
        v.arm(); assertEquals(63, v.observer().n("xfma_evolution_coin_records"));
        for (int id = 64; id <= 127; id++) v.global("xfm_coin_registry").add(v.coin("new-" + id, id, v.player, 0));
        v.exchange.put("xfm_next_coin_id", 127).put("xfm_registered_coin_count", 127); v.day(7); v.observe();
        assertEquals(64, v.observer().n("xfma_evolution_coin_records"));
        assertEquals(64, v.observer().n("xfma_evolution_coin_cursor"));
        assertEquals(0, v.observer().n("xfma_coin_coverage_complete"));
        assertEquals(0, v.observer().n("xfma_new_ai_issues_observed"));
        v.observe(); assertEquals(64, v.observer().n("xfma_evolution_coin_records"));
    }

    @Test void publicRegistryAddsOnlyTheNewCaseAndKeepsExistingFiniteWindowsAndStrictClaims() throws IOException {
        String shared = System.getProperty("xfm.shared.source");
        Path root = shared == null ? Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent()
                : Path.of(shared).toAbsolutePath().normalize();
        var products = FixtureEmitter.JSON.readTree(Files.readAllBytes(root.resolve("tools/ck3_mod_acceptance_products.json")));
        var cases = products.path("products").path("financial-markets").path("cases");
        Map<String, com.fasterxml.jackson.databind.JsonNode> indexed = new HashMap<>();
        cases.forEach(c -> assertNull(indexed.put(c.path("id").asText(), c)));
        assertEquals(10800, indexed.get("market-evolution").path("budgets").path("timeout").intValue());
        assertFalse(indexed.get("market-evolution").path("whole_product_acceptance_credit").booleanValue());
        var newCase = FixtureEmitter.JSON.readTree(Files.readAllBytes(root.resolve("tools/ck3_mod_acceptance_cases/financial_markets_market_evolution.json")));
        assertEquals(35, newCase.path("maximum_natural_days").intValue());
        assertFalse(newCase.path("whole_product_release_pass").booleanValue());
        assertEquals(3, readCase(root, "spot").path("maximum_natural_days").intValue());
        assertEquals(14, readCase(root, "derivatives").path("maximum_natural_days").intValue());
        assertEquals(35, readCase(root, "lifecycle").path("maximum_natural_days").intValue());
        assertEquals(395, readCase(root, "ai_capacity").path("maximum_natural_days").intValue());
    }

    @Test void subscriptionInspectionHasAHardHundredRecordBodyBoundAndReportsTruncation() {
        Vm v = new Vm(request(null, null));
        Node coin = v.global("xfm_coin_registry").getFirst();
        for (int id = 1; id <= 101; id++) coin.nodes("xfm_subscriptions").add(
                v.node("subscription-" + id, "xfm_finance_reservation", true)
                        .put("xfm_reservation_id", id).put("xfm_subscription_state", 3)
                        .put("xfm_subscription_paid_cents", 20).put("xfm_remaining_cents", 0)
                        .ref("xfm_account", v.privateAccount));
        String product = v.productState(); v.arm(); Node record = v.coinRecord(1);
        assertEquals(100, record.n("xfma_subscriptions_sampled"));
        assertEquals(100, record.nodes("xfma_subscription_sources").size());
        assertEquals(0, record.n("xfma_subscriptions_available"));
        assertEquals(0, v.observer().n("xfma_refund_available"));
        assertEquals(product, v.productState());
    }
    @Test void dailyAttemptDiagnosticsInitializeLazilyAndCaptureActualGuardInputsOnNewDates() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadDailyAttemptDiagnostics();
        assertFalse(v.exchange.vars.containsKey("xfm_daily_attempt_count"), "loading definitions does not initialize a cold save");
        v.exchange.put("xfm_last_date", v.nativeDate - 24);
        String financial = v.nonDiagnosticProductState();
        v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(financial, v.nonDiagnosticProductState());
        assertEquals(1, v.exchange.n("xfm_daily_attempt_count"));
        assertEquals(1, v.exchange.n("xfm_daily_attempts_on_date"));
        assertEquals(0, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(v.nativeDate, v.exchange.n("xfm_daily_attempt_script_date"));
        assertEquals(v.nativeDate - 24, v.exchange.n("xfm_daily_attempt_prev_date"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_prev_date_present"));
        assertEquals(0, v.exchange.n("xfm_daily_attempt_count_saturated"));
        assertEquals(0, v.exchange.n("xfm_daily_rejected_count_saturated"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_last_rejected_date"));
        assertEquals(6, v.exchange.n("xfm_day"), "these diagnostic helpers do not execute the business clock");
        // Explicit fixture input for the next invocation; no business outcome is fabricated by this VM.
        v.exchange.put("xfm_last_date", v.nativeDate); v.nativeDate += 24;
        financial = v.nonDiagnosticProductState(); v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(financial, v.nonDiagnosticProductState());
        assertEquals(2, v.exchange.n("xfm_daily_attempt_count"));
        assertEquals(1, v.exchange.n("xfm_daily_attempts_on_date"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(v.nativeDate - 24, v.exchange.n("xfm_daily_attempt_prev_date"));
        assertEquals(0, v.exchange.n("xfm_daily_rejected_count"));
    }

    @Test void dailyAttemptDiagnosticsCountSameDateRejectionsAndRetainTheLastRejectedInputs() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadDailyAttemptDiagnostics();
        long previous = v.nativeDate; String financial = v.nonDiagnosticProductState();
        v.dailyAttemptDiagnostics(v.exchange); v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(financial, v.nonDiagnosticProductState());
        assertEquals(2, v.exchange.n("xfm_daily_attempt_count"));
        assertEquals(2, v.exchange.n("xfm_daily_attempts_on_date"));
        assertEquals(2, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(0, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(previous, v.exchange.n("xfm_daily_last_rejected_date"));
        assertEquals(previous, v.exchange.n("xfm_daily_last_rejected_prev_date"));
        v.nativeDate += 24; financial = v.nonDiagnosticProductState(); v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(financial, v.nonDiagnosticProductState());
        assertEquals(3, v.exchange.n("xfm_daily_attempt_count"));
        assertEquals(1, v.exchange.n("xfm_daily_attempts_on_date"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(2, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(previous, v.exchange.n("xfm_daily_last_rejected_date"));
        assertEquals(previous, v.exchange.n("xfm_daily_last_rejected_prev_date"));
    }

    @Test void dailyAttemptDiagnosticsPreserveMissingPreviousDateInsteadOfInventingZero() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadDailyAttemptDiagnostics();
        v.dailyAttemptDiagnostics(v.exchange);
        assertTrue(v.exchange.vars.containsKey("xfm_daily_last_rejected_prev_date"));
        v.exchange.vars.remove("xfm_last_date"); v.nativeDate += 24;
        String financial = v.nonDiagnosticProductState(); v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(financial, v.nonDiagnosticProductState());
        assertEquals(2, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(0, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(0, v.exchange.n("xfm_daily_attempt_prev_date_present"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_attempt_prev_date"));
        assertEquals(0, v.exchange.n("xfm_daily_last_rejected_prev_date_present"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_last_rejected_prev_date"));
        assertFalse(v.exchange.vars.containsKey("xfm_last_date"));
    }

    @Test void dailyAttemptDiagnosticsSaturateOnlyAfterTheExactCounterBoundsAndResetTheDateCounter() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadDailyAttemptDiagnostics(); v.dailyAttemptDiagnostics(v.exchange);
        v.exchange.put("xfm_daily_attempt_count", 999999999).put("xfm_daily_rejected_count", 999999999)
                .put("xfm_daily_attempts_on_date", 1023);
        String financial = v.nonDiagnosticProductState(); v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(1000000000, v.exchange.n("xfm_daily_attempt_count"));
        assertEquals(1000000000, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(1024, v.exchange.n("xfm_daily_attempts_on_date"));
        for (String flag : List.of("xfm_daily_attempt_count_saturated", "xfm_daily_rejected_count_saturated", "xfm_daily_attempts_on_date_saturated"))
            assertEquals(0, v.exchange.n(flag), "the exact bound is still an exact count");
        v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(1000000000, v.exchange.n("xfm_daily_attempt_count"));
        assertEquals(1000000000, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(1024, v.exchange.n("xfm_daily_attempts_on_date"));
        for (String flag : List.of("xfm_daily_attempt_count_saturated", "xfm_daily_rejected_count_saturated", "xfm_daily_attempts_on_date_saturated"))
            assertEquals(1, v.exchange.n(flag), "a further call changes the count to a lower bound");
        assertEquals(financial, v.nonDiagnosticProductState());
        v.nativeDate += 24; v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(1, v.exchange.n("xfm_daily_attempts_on_date"));
        assertEquals(0, v.exchange.n("xfm_daily_attempts_on_date_saturated"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_count_saturated"));
        assertEquals(1, v.exchange.n("xfm_daily_rejected_count_saturated"));
        assertEquals(1000000000, v.exchange.n("xfm_daily_rejected_count"));
    }

    @Test void dailyAttemptDiagnosticsWriteNothingForCharactersForeignStoriesOrAnAbsentGlobalExchange() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadDailyAttemptDiagnostics();
        Node foreign = v.node("foreign-exchange", "xfm_finance_exchange", true)
                .put("xfm_last_date", v.nativeDate - 24).put("xfm_day", 6);
        v.player.put("xfm_last_date", v.nativeDate - 24);
        String original = v.productState();
        v.dailyAttemptDiagnostics(v.player); v.dailyAttemptDiagnostics(foreign);
        assertEquals(original, v.productState());
        v.exchangeAvailable = false; v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(original, v.productState());
        assertTrue(v.nodes.stream().noneMatch(n -> n.vars.keySet().stream().anyMatch(key -> key.startsWith("xfm_daily_"))));
    }

    @Test void dailyAttemptInstrumentationKeepsTheRealTimerGuardBusinessOrderAndObserverTail() throws IOException {
        Path source = Path.of(System.getProperty("xfm.source"));
        Block schedule = parse(Files.readString(source.resolve("common/scripted_effects/xfm_finance_schedule.txt")));
        Block daily = schedule.block("xfm_finance_daily_effect");
        assertEquals(List.of("xfm_finance_daily_attempt_begin_effect", "if", "xfm_finance_daily_attempt_finish_effect"),
                daily.entries().stream().map(Entry::key).toList());
        Block body = daily.block("if");
        assertEquals(parse("guard = { exists = global_var:xfm_exchange this = global_var:xfm_exchange has_variable = xfm_last_date var:xfm_last_date < current_date }").block("guard"), body.block("limit"));
        List<Entry> business = body.entries().stream().filter(e -> !e.key().equals("limit") && !Vm.diagnosticVariableWrite(e)).toList();
        assertEquals(List.of("set_variable", "change_variable", "set_variable", "if", "xfm_spot_daily_effect", "xfm_oracle_daily_effect",
                "xfm_finance_capitalize_default_fund_effect", "xfm_futures_daily_effect", "xfm_coin_daily_effect", "xfm_listing_daily_effect",
                "xfm_debt_daily_effect", "xfm_news_daily_effect", "xfm_finance_run_ai_budget_effect", "if"), business.stream().map(Entry::key).toList());
        assertEquals(parse("x = { set_variable = { name = xfm_last_date value = current_date } change_variable = { name = xfm_day add = 1 } set_variable = { name = xfm_new_listings_today value = 0 } }").block("x").entries(), business.subList(0, 3));
        assertEquals(parse("x = { if = { limit = { NOT = { var:xfm_a0_migration_scanned = 1 } } xfm_finance_migrate_a0_effect = yes } }").block("x").entries().getFirst(), business.get(3));
        assertEquals(parse("x = { if = { limit = { exists = story_owner } story_owner = { trigger_event = { on_action = xfm_finance_daily_observation_on_action } } } }").block("x").entries().getFirst(), business.getLast());
        Block timer = parse(Files.readString(source.resolve("common/story_cycles/xfm_finance_runtime.txt"))).block("xfm_finance_exchange").block("effect_group");
        assertEquals("1", Vm.atom(timer.blockOrAtom("days")));
        assertEquals(parse("x = { xfm_finance_daily_raw_entry_effect = yes xfm_finance_daily_effect = yes }").block("x"), timer.block("triggered_effect").block("effect"));
    }

    @Test void rawDailyProbeCapturesTheActualCallerAndStoryAndCleansOnlyItsPrivateAliases() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadRawDailyProbe();
        v.aliases.put("xfm_finance_ai_actor", v.player);
        v.aliases.put("xfm_daily_raw_entry_caller", v.player);
        v.aliases.put("xfm_daily_raw_entry_story", v.player);
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_attempt_count"));
        String financial = v.nonDiagnosticProductState();
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(financial, v.nonDiagnosticProductState());
        assertEquals(1, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_attempt_count_saturated"));
        assertEquals(v.nativeDate, v.exchange.n("xfm_daily_raw_script_date"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_caller_present"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_caller_matches_exchange"));
        assertSame(v.exchange, v.exchange.node("xfm_daily_raw_caller"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_story_present"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_story_matches_exchange"));
        assertSame(v.exchange, v.exchange.node("xfm_daily_raw_story"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_last_mismatch_date"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_attempt_count"), "the probe does not call the authorized helper or business clock");
        assertSame(v.player, v.aliases.get("xfm_finance_ai_actor"));
        assertSame(v.exchange, v.aliases.get("story"), "the engine-supplied story scope is not cleared");
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(2, v.exchange.n("xfm_daily_raw_attempt_count"), "every actual same-date entry is counted, not deduplicated");
        assertEquals(0, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(financial, v.nonDiagnosticProductState());
    }

    @Test void rawDailyProbePreservesTypedMismatchEvidenceAcrossMissingScopesAndLaterCorrectCalls() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadRawDailyProbe();
        Node caller = v.character("unexpected-caller", true);
        Node otherStory = v.node("other-story", "xfm_finance_exchange", true);
        String financial = v.nonDiagnosticProductState();
        v.rawDailyProbe(caller, v.exchange);
        assertEquals(1, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_caller_present"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_caller_matches_exchange"));
        assertSame(caller, v.exchange.node("xfm_daily_raw_caller"));
        assertSame(caller, v.exchange.node("xfm_daily_raw_last_caller"));
        assertEquals("character", v.exchange.node("xfm_daily_raw_last_caller").kind);
        assertSame(v.exchange, v.exchange.node("xfm_daily_raw_last_story"));
        v.nativeDate += 24; v.rawDailyProbe(v.exchange, otherStory);
        assertEquals(2, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_story_present"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_story_matches_exchange"));
        assertSame(otherStory, v.exchange.node("xfm_daily_raw_story"));
        assertSame(otherStory, v.exchange.node("xfm_daily_raw_last_story"));
        // A stale private alias must not manufacture a scope when the actual built-in scope is absent.
        v.aliases.put("xfm_daily_raw_entry_story", otherStory);
        v.nativeDate += 24; long badDate = v.nativeDate; v.rawDailyProbe(v.exchange, null);
        assertEquals(3, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_story_present"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_story"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_last_story_present"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_last_story"));
        assertEquals(badDate, v.exchange.n("xfm_daily_raw_last_mismatch_date"));
        assertSame(v.exchange, v.exchange.node("xfm_daily_raw_last_caller"));
        v.nativeDate += 24; v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(4, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(3, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_story_present"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_story_matches_exchange"));
        assertEquals(badDate, v.exchange.n("xfm_daily_raw_last_mismatch_date"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_last_story_present"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_last_story"));
        assertEquals(financial, v.nonDiagnosticProductState());
    }

    @Test void rawDailyProbeDoesNotZeroMissingGlobalDataAndSaturatesCountsWithoutFinancialWrites() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadRawDailyProbe();
        Node caller = v.character("wrong-caller", true);
        v.exchangeAvailable = false; String all = v.productState();
        v.rawDailyProbe(caller, null);
        assertEquals(all, v.productState());
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_attempt_count"));
        v.exchangeAvailable = true; v.rawDailyProbe(v.exchange, v.exchange);
        all = v.productState(); v.exchangeAvailable = false; v.rawDailyProbe(caller, null);
        assertEquals(all, v.productState(), "no canonical destination means no persisted observation and no zero reset");
        v.exchangeAvailable = true;
        v.exchange.put("xfm_daily_raw_attempt_count", 999999999).put("xfm_daily_raw_mismatch_count", 999999999);
        String financial = v.nonDiagnosticProductState(); v.rawDailyProbe(caller, null);
        assertEquals(1000000000, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(1000000000, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_attempt_count_saturated"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_mismatch_count_saturated"));
        v.rawDailyProbe(caller, null);
        assertEquals(1000000000, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(1000000000, v.exchange.n("xfm_daily_raw_mismatch_count"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_attempt_count_saturated"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_mismatch_count_saturated"));
        assertEquals(financial, v.nonDiagnosticProductState());
        assertFalse(v.exchange.vars.containsKey("xfm_daily_attempt_count"));
    }

    @Test void rawDateGapFirstCallbackKeepsMissingHistoryAndChangesNoBusinessFields() throws IOException {
        Vm v = rawDateGapVm(); String financial = v.nonDiagnosticProductState();
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_script_date"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_prev_script_date_present"));
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(389430, v.exchange.n("xfm_daily_raw_script_date"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_prev_script_date_present"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_prev_script_date"));
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_script_date_delta"));
        assertNoFirstRawGap(v);
        assertEquals(1, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(financial, v.nonDiagnosticProductState());
        assertFalse(v.exchange.vars.containsKey("xfm_daily_attempt_count"));
    }

    @Test void rawDateGapUsesOneScriptDayAndCountsSameDayReentryWithoutInventingAGap() throws IOException {
        Vm v = rawDateGapVm(); long nativeTicks = v.nativeDate;
        v.rawDailyProbe(v.exchange, v.exchange);
        v.scriptDateOverride = 389431L; String financial = v.nonDiagnosticProductState();
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(1, v.exchange.n("xfm_daily_raw_prev_script_date_present"));
        assertEquals(389430, v.exchange.n("xfm_daily_raw_prev_script_date"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_script_date_delta"));
        assertNoFirstRawGap(v);
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(389431, v.exchange.n("xfm_daily_raw_prev_script_date"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_script_date_delta"));
        assertEquals(3, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertNoFirstRawGap(v);
        assertEquals(nativeTicks, v.nativeDate, "one script day is not a synthetic Native +24 input");
        assertEquals(financial, v.nonDiagnosticProductState());
    }

    @Test void rawDateGapRecordsTheFirstMissingIntervalAndNeverOverwritesIt() throws IOException {
        Vm v = rawDateGapVm(); v.rawDailyProbe(v.exchange, v.exchange);
        v.scriptDateOverride = 389431L; v.rawDailyProbe(v.exchange, v.exchange);
        v.scriptDateOverride = 389434L; String financial = v.nonDiagnosticProductState();
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(389431, v.exchange.n("xfm_daily_raw_first_gap_prev_date"));
        assertEquals(389434, v.exchange.n("xfm_daily_raw_first_gap_date"));
        assertEquals(2, v.exchange.n("xfm_daily_raw_first_gap_missing_dates"));
        assertEquals(3, v.exchange.n("xfm_daily_raw_first_gap_attempt_count"));
        Map<String, Value> first = firstRawGap(v);
        v.scriptDateOverride = 389435L; v.rawDailyProbe(v.exchange, v.exchange);
        v.scriptDateOverride = 389440L; v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(389435, v.exchange.n("xfm_daily_raw_prev_script_date"));
        assertEquals(5, v.exchange.n("xfm_daily_raw_script_date_delta"));
        assertEquals(first, firstRawGap(v));
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(0, v.exchange.n("xfm_daily_raw_script_date_delta"));
        assertEquals(6, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(first, firstRawGap(v));
        assertEquals(financial, v.nonDiagnosticProductState());
    }

    @Test void rawDateGapOldSavesUseExistingRawDateButNeverBackfillAnAbsentDate() throws IOException {
        for (boolean previousPresent : List.of(false, true)) {
            Vm v = rawDateGapVm(); seedRawCounter(v, 17);
            if (previousPresent) v.exchange.put("xfm_daily_raw_script_date", 389428);
            String financial = v.nonDiagnosticProductState();
            assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_prev_script_date_present"));
            v.rawDailyProbe(v.exchange, v.exchange);
            assertEquals(18, v.exchange.n("xfm_daily_raw_attempt_count"));
            assertEquals(previousPresent ? 1 : 0, v.exchange.n("xfm_daily_raw_prev_script_date_present"));
            if (previousPresent) {
                assertEquals(389428, v.exchange.n("xfm_daily_raw_prev_script_date"));
                assertEquals(2, v.exchange.n("xfm_daily_raw_script_date_delta"));
                assertEquals(389428, v.exchange.n("xfm_daily_raw_first_gap_prev_date"));
                assertEquals(389430, v.exchange.n("xfm_daily_raw_first_gap_date"));
                assertEquals(1, v.exchange.n("xfm_daily_raw_first_gap_missing_dates"));
                assertEquals(18, v.exchange.n("xfm_daily_raw_first_gap_attempt_count"));
            } else {
                assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_prev_script_date"));
                assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_script_date_delta"));
                assertNoFirstRawGap(v);
            }
            assertEquals(financial, v.nonDiagnosticProductState());
        }
    }

    @Test void rawDateGapBackwardAndZeroDifferencesAreSignedDiagnosticsOnly() throws IOException {
        Vm v = rawDateGapVm(); v.rawDailyProbe(v.exchange, v.exchange);
        String financial = v.nonDiagnosticProductState();
        v.scriptDateOverride = 389429L; v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(-1, v.exchange.n("xfm_daily_raw_script_date_delta")); assertNoFirstRawGap(v);
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(0, v.exchange.n("xfm_daily_raw_script_date_delta")); assertNoFirstRawGap(v);
        v.scriptDateOverride = 389430L; v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(1, v.exchange.n("xfm_daily_raw_script_date_delta")); assertNoFirstRawGap(v);
        assertEquals(financial, v.nonDiagnosticProductState());
    }

    @Test void rawDateGapPreservesSavedFirstGapAndUsesTheExistingSaturatedCounter() throws IOException {
        Vm v = rawDateGapVm(); seedRawCounter(v, 999999999);
        v.exchange.put("xfm_daily_raw_script_date", 389426)
                .put("xfm_daily_raw_first_gap_prev_date", 389400).put("xfm_daily_raw_first_gap_date", 389404)
                .put("xfm_daily_raw_first_gap_missing_dates", 3).put("xfm_daily_raw_first_gap_attempt_count", 10);
        Map<String, Value> first = firstRawGap(v); String financial = v.nonDiagnosticProductState();
        v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(1000000000, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(0, v.exchange.n("xfm_daily_raw_attempt_count_saturated"));
        assertEquals(4, v.exchange.n("xfm_daily_raw_script_date_delta")); assertEquals(first, firstRawGap(v));
        v.scriptDateOverride = 389432L; v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(1000000000, v.exchange.n("xfm_daily_raw_attempt_count"));
        assertEquals(1, v.exchange.n("xfm_daily_raw_attempt_count_saturated"));
        assertEquals(2, v.exchange.n("xfm_daily_raw_script_date_delta")); assertEquals(first, firstRawGap(v));
        assertEquals(financial, v.nonDiagnosticProductState());
        Vm alreadyCapped = rawDateGapVm(); seedRawCounter(alreadyCapped, 1000000000);
        alreadyCapped.exchange.put("xfm_daily_raw_script_date", 389428);
        alreadyCapped.rawDailyProbe(alreadyCapped.exchange, alreadyCapped.exchange);
        assertEquals(1000000000, alreadyCapped.exchange.n("xfm_daily_raw_first_gap_attempt_count"));
        assertEquals(1, alreadyCapped.exchange.n("xfm_daily_raw_attempt_count_saturated"));
        assertEquals(1, alreadyCapped.exchange.n("xfm_daily_raw_first_gap_missing_dates"));
    }

    @Test void rawDateGapDoesNotWriteWithoutTheGlobalOrChangeTheRealSameDayGuard() throws IOException {
        Vm v = rawDateGapVm(); v.loadDailyAttemptDiagnostics();
        v.exchange.put("xfm_last_date", 389430); v.exchangeAvailable = false;
        String all = v.productState(); v.rawDailyProbe(v.exchange, v.exchange);
        assertEquals(all, v.productState()); assertNoFirstRawGap(v);
        v.exchangeAvailable = true; String financial = v.nonDiagnosticProductState();
        v.rawDailyProbe(v.exchange, v.exchange);
        assertFalse(v.exchange.vars.containsKey("xfm_daily_attempt_count"), "raw diagnostics never call daily business");
        v.dailyAttemptDiagnostics(v.exchange); // existing real guard/marker subset, never business effects
        assertEquals(0, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(1, v.exchange.n("xfm_daily_rejected_count"));
        v.scriptDateOverride = 389431L; v.rawDailyProbe(v.exchange, v.exchange);
        v.dailyAttemptDiagnostics(v.exchange);
        assertEquals(1, v.exchange.n("xfm_daily_attempt_entered_dispatch"));
        assertEquals(1, v.exchange.n("xfm_daily_rejected_count"));
        assertEquals(389430, v.exchange.n("xfm_last_date")); assertEquals(6, v.exchange.n("xfm_day"));
        assertEquals(financial, v.nonDiagnosticProductState());
    }

    private static Vm rawDateGapVm() throws IOException {
        Vm v = new Vm(request(null, null)); v.loadRawDailyProbe();
        v.scriptDateOverride = 389430L; // explicit script-calendar ordinal; Native raw date remains independent
        return v;
    }
    private static void seedRawCounter(Vm v, long count) {
        v.exchange.put("xfm_daily_raw_attempt_count", count).put("xfm_daily_raw_attempt_count_saturated", 0)
                .put("xfm_daily_raw_mismatch_count", 0).put("xfm_daily_raw_mismatch_count_saturated", 0);
    }
    private static Map<String, Value> firstRawGap(Vm v) {
        Map<String, Value> first = new LinkedHashMap<>();
        v.exchange.vars.forEach((key, value) -> { if (key.startsWith("xfm_daily_raw_first_gap_")) first.put(key, value); });
        return first;
    }
    private static void assertNoFirstRawGap(Vm v) { assertTrue(firstRawGap(v).isEmpty(), "missing history is not a gap at zero"); }

    private static com.fasterxml.jackson.databind.JsonNode readCase(Path root, String key) throws IOException {
        return FixtureEmitter.JSON.readTree(Files.readAllBytes(root.resolve("tools/ck3_mod_acceptance_cases/financial_markets_" + key + ".json")));
    }

    private sealed interface Value permits NumberValue, Reference { }
    private record NumberValue(long value) implements Value { }
    private record Reference(Node node) implements Value { }
    private static final class Node {
        final String key, kind; final boolean product;
        final Map<String, Value> vars = new LinkedHashMap<>();
        final Map<String, List<Node>> lists = new LinkedHashMap<>();
        Node owner, title; boolean ai, adult = true, alive = true, landed; int tier; long gold;
        Node(String key, String kind, boolean product) { this.key = key; this.kind = kind; this.product = product; }
        Node put(String key, long value) { vars.put(key, new NumberValue(value)); return this; }
        Node ref(String key, Node value) { vars.put(key, new Reference(value)); return this; }
        long n(String key) { return ((NumberValue) java.util.Objects.requireNonNull(vars.get(key), key)).value(); }
        Node node(String key) { return ((Reference) java.util.Objects.requireNonNull(vars.get(key), key)).node(); }
        List<Node> nodes(String key) { return lists.computeIfAbsent(key, ignored -> new ArrayList<>()); }
    }
    /** No product effects, implicit missing=zero, random business decisions or financial ports exist. */
    private static final class Vm {
        final Request input; final Map<String, Block> program = new HashMap<>(), onActions = new HashMap<>();
        final Map<String, Node> aliases = new HashMap<>(); final Map<String, List<Node>> globals = new HashMap<>();
        final List<Node> nodes = new ArrayList<>(), players = new ArrayList<>(); final List<String> logs = new ArrayList<>();
        final Node exchange, player, privateAccount; long nativeDate = 53144448; boolean failRecordCreation;
        boolean exchangeAvailable = true, diagnosticWrites; Block diagnosticCallbackSubset, rawTimerProbe;
        Long scriptDateOverride; // opt-in script-day input; legacy tests keep their original default
        Vm(Request input) {
            this.input = input;
            FollowupObservationScripts.render(input).forEach((name, bytes) -> {
                if (name.startsWith("common/scripted_effects/") || name.startsWith("common/scripted_triggers/") || name.startsWith("common/script_values/"))
                    for (Entry e : parse(new String(bytes, StandardCharsets.UTF_8)).entries())
                        assertNull(program.put(e.key(), (Block)e.value()), e.key());
                if (name.startsWith("common/on_action/"))
                    for (Entry e : parse(new String(bytes, StandardCharsets.UTF_8)).entries())
                        assertNull(onActions.put(e.key(), (Block)e.value()), e.key());
            });
            player = character("player", false); players.add(player);
            exchange = node("exchange", "xfm_finance_exchange", true); exchange.owner = player;
            exchange.put("xfm_day", 6).put("xfm_next_coin_id", 1).put("xfm_registered_coin_count", 1)
                    .put("xfm_pending_coin_count", 0).put("xfm_active_coin_count", 1).put("xfm_new_listings_today", 0)
                    .put("xfm_fee_cents", 0).put("xfm_ai_work_today", 512).put("xfm_ai_decisions_today", 500)
                    .put("xfm_ai_count", 35000).put("xfm_futures_open_positions_count", 0).put("xfm_last_date", nativeDate);
            privateAccount = account("private", 2, player, 6000); privateAccount.put("xfm_system_account", 0); player.ref("xfm_account", privateAccount);
            global("xfm_account_registry").add(privateAccount);
            global("xfm_coin_registry").add(coin("baseline-coin", 1, player, 1));
            Node fund = account("fund", 1, player, 0); exchange.ref("xfm_default_fund_account", fund);
        }
        Node node(String key, String kind, boolean product) { Node n = new Node(key, kind, product); nodes.add(n); return n; }
        Node character(String key, boolean ai) { Node n = node(key, "character", true); n.ai = ai; n.gold = 5; return n; }
        Node account(String key, long id, Node holder, long free) { return node(key, "xfm_finance_account", true).put("xfm_account_id", id).put("xfm_free_cents", free).put("xfm_reserved_cents", 0).ref("xfm_holder", holder); }
        Node coin(String key, long id, Node issuer, long state) {
            Node project = account(key + "-project", 1000 + id, issuer, 0);
            Node coin = node(key, "xfm_finance_coin", true).put("xfm_coin_id", id).put("xfm_listing_state", state)
                    .put("xfm_supply_units", 15000).put("xfm_trading_open", state == 0 ? 0 : 1)
                    .put("xfm_asset_age", 0).put("xfm_offer_age", 0).put("xfm_service_tier", 1)
                    .put("xfm_registration_paid_cents", 100).put("xfm_minimum_raised_cents", 2000)
                    .put("xfm_actual_raised_cents", state == 0 ? 0 : 2000).put("xfm_external_raised_cents", state == 0 ? 0 : 400)
                    .put("xfm_unresolved_claim_count", 0)
                    .ref("xfm_original_issuer", issuer).ref("xfm_controller", issuer).ref("xfm_issuer_account", project);
            if (state != 0) coin.put("xfm_listed_day", 0);
            return coin;
        }
        List<Node> global(String name) { return globals.computeIfAbsent(name, ignored -> new ArrayList<>()); }
        void arm() { run(input.prefix() + "_arm_effect", player, null); }
        void observe() { run(input.prefix() + "_observe_effect", observer(), null); }
        Node observer() { return player.node(input.prefix() + "_story"); }
        Node coinRecord(long id) { return observer().nodes("xfma_evolution_coins").stream().filter(n -> n.n("xfma_first_coin_id") == id).findFirst().orElseThrow(); }
        void day(long day) { nativeDate += Math.multiplyExact(day - exchange.n("xfm_day"), 24); exchange.put("xfm_day", day).put("xfm_last_date", nativeDate); }
        void afterFinanceTail() throws IOException {
            Path source = Path.of(System.getProperty("xfm.source"));
            Block daily = parse(Files.readString(source.resolve("common/scripted_effects/xfm_finance_schedule.txt")))
                    .block("xfm_finance_daily_effect").block("if");
            List<Entry> steps = daily.entries();
            assertEquals("xfm_finance_run_ai_budget_effect", steps.get(steps.size() - 2).key(),
                    "the observation hook follows the real last AI step, not a competing daily timer");
            Entry tail = steps.getLast(); assertEquals("if", tail.key());
            Block base = parse(Files.readString(source.resolve("common/on_action/xfm_finance_on_actions.txt")))
                    .block("xfm_finance_daily_observation_on_action");
            assertTrue(base.entries().isEmpty(), "the ordinary product has no observer or extra business action");
            // Execute the actual production tail and actual emitted on_action, not a stand-in observation call.
            execute(new Block(List.of(tail)), exchange, null);
        }
        void fireOnAction(String name, Node here, Node prev) {
            Block action = java.util.Objects.requireNonNull(onActions.get(name), name);
            for (Entry entry : action.entries()) {
                if (entry.key().equals("effect")) execute((Block)entry.value(), here, prev);
                else if (entry.key().equals("on_actions")) {
                    for (Entry child : ((Block)entry.value()).entries()) {
                        assertEquals("$literal", child.key()); fireOnAction(atom(child.value()), here, prev);
                    }
                } else throw new AssertionError("unsupported observation on_action " + entry.key());
            }
        }
        /** Execute only actual diagnostic helpers + the actual guard/entry marker, never business hooks. */
        void loadDailyAttemptDiagnostics() throws IOException {
            Block schedule = parse(Files.readString(Path.of(System.getProperty("xfm.source"))
                    .resolve("common/scripted_effects/xfm_finance_schedule.txt")));
            List<Entry> helpers = schedule.entries().stream().filter(e -> e.key().startsWith("xfm_finance_daily_attempt_")).toList();
            assertEquals(List.of("xfm_finance_daily_attempt_begin_effect", "xfm_finance_daily_attempt_total_effect",
                    "xfm_finance_daily_attempt_date_effect", "xfm_finance_daily_attempt_finish_effect"), helpers.stream().map(Entry::key).toList());
            for (Entry helper : helpers) assertNull(program.put(helper.key(), (Block)helper.value()), helper.key());
            Block actual = schedule.block("xfm_finance_daily_effect");
            assertEquals(3, actual.entries().size());
            Entry dispatch = actual.entries().get(1); assertEquals("if", dispatch.key());
            Block originalBody = (Block)dispatch.value();
            List<Entry> retained = originalBody.entries().stream()
                    .filter(e -> e.key().equals("limit") || diagnosticVariableWrite(e)).toList();
            assertEquals(2, retained.size(), "the isolated production subset retains only the real guard and entry marker");
            assertEquals("xfm_daily_attempt_entered_dispatch", atom(((Block)retained.getLast().value()).blockOrAtom("name")));
            diagnosticCallbackSubset = new Block(List.of(actual.entries().getFirst(),
                    new Entry(dispatch.key(), dispatch.operator(), new Block(retained)), actual.entries().getLast()));
        }
        static boolean diagnosticVariableWrite(Entry entry) {
            if (!List.of("set_variable", "change_variable").contains(entry.key()) || !(entry.value() instanceof Block child)) return false;
            return atom(child.blockOrAtom("name")).startsWith("xfm_daily_");
        }
        void dailyAttemptDiagnostics(Node here) {
            assertFalse(diagnosticWrites); assertNotNull(diagnosticCallbackSubset);
            diagnosticWrites = true;
            try { execute(diagnosticCallbackSubset, here, null); }
            finally { diagnosticWrites = false; }
        }
        /** Execute the real first timer effect only; the original daily/business call is never executed here. */
        void loadRawDailyProbe() throws IOException {
            Path source = Path.of(System.getProperty("xfm.source"));
            Block schedule = parse(Files.readString(source.resolve("common/scripted_effects/xfm_finance_schedule.txt")));
            List<Entry> helpers = schedule.entries().stream().filter(e -> e.key().startsWith("xfm_finance_daily_raw_")).toList();
            assertEquals(List.of("xfm_finance_daily_raw_entry_effect", "xfm_finance_daily_raw_record_effect",
                    "xfm_finance_daily_raw_capture_effect", "xfm_finance_daily_raw_mismatch_effect",
                    "xfm_finance_daily_raw_dates_effect"), helpers.stream().map(Entry::key).toList());
            for (Entry helper : helpers) assertNull(program.put(helper.key(), (Block)helper.value()), helper.key());
            Block timer = parse(Files.readString(source.resolve("common/story_cycles/xfm_finance_runtime.txt")))
                    .block("xfm_finance_exchange").block("effect_group").block("triggered_effect").block("effect");
            assertEquals(List.of("xfm_finance_daily_raw_entry_effect", "xfm_finance_daily_effect"), timer.entries().stream().map(Entry::key).toList());
            rawTimerProbe = new Block(List.of(timer.entries().getFirst()));
        }
        void rawDailyProbe(Node caller, Node actualStoryScope) {
            assertFalse(diagnosticWrites); assertNotNull(rawTimerProbe);
            // Explicit fixture binding of the installed documented scope:story, never a fallback to the caller/global.
            if (actualStoryScope == null) aliases.remove("story"); else aliases.put("story", actualStoryScope);
            diagnosticWrites = true;
            try { execute(rawTimerProbe, caller, null); }
            finally { diagnosticWrites = false; }
            assertFalse(aliases.containsKey("xfm_daily_raw_entry_caller"));
            assertFalse(aliases.containsKey("xfm_daily_raw_entry_story"));
            if (actualStoryScope == null) assertFalse(aliases.containsKey("story"));
            else assertSame(actualStoryScope, aliases.get("story"));
        }

        void assertVariableWrite(String name, Node here) {
            if (diagnosticWrites) {
                assertSame(exchange, here, "diagnostics cannot mutate another scope");
                assertTrue(name.startsWith("xfm_daily_"), "diagnostics cannot write financial/observer variable " + name);
            } else assertTrue(name.startsWith("xfma_"), "product mutation " + name);
        }

        String productState() { return productState(false); }
        String nonDiagnosticProductState() { return productState(true); }
        private String productState(boolean omitDiagnostics) {
            StringBuilder s = new StringBuilder();
            for (Node n : nodes) if (n.product) {
                s.append(n.key).append(':').append(n.gold).append(':').append(n.ai).append(':').append(n.alive).append(':').append(n.adult).append(':').append(n.landed).append(':').append(n.tier);
                n.vars.forEach((k,v) -> { if (!k.startsWith("xfma_") && (!omitDiagnostics || !k.startsWith("xfm_daily_"))) s.append('|').append(k).append('=').append(v instanceof NumberValue x ? x.value() : ((Reference)v).node().key); });
                n.lists.forEach((k,v) -> { if (!k.startsWith("xfma_")) s.append('|').append(k).append('=').append(v.stream().map(x -> x.key).toList()); });
                s.append('\n');
            }
            return s.toString();
        }
        void run(String name, Node here, Node prev) { execute(java.util.Objects.requireNonNull(program.get(name), name), here, prev); }
        void execute(Block b, Node here, Node prev) {
            boolean chain = false, taken = false;
            for (Entry e : b.entries()) {
                if (e.key().equals("limit")) continue;
                if (e.key().equals("if") || e.key().equals("else_if")) {
                    boolean first = e.key().equals("if"); assertTrue(first || chain, "orphan else_if");
                    if (first) { chain = true; taken = false; }
                    Block child = (Block)e.value();
                    if (!taken && matches(child.block("limit"), here, prev)) { execute(child, here, prev); taken = true; }
                    continue;
                }
                if (e.key().equals("else")) { assertTrue(chain, "orphan else"); if (!taken) execute((Block)e.value(), here, prev); chain = false; continue; }
                chain = false;
                String key = e.key();
                if (key.equals("save_scope_as")) { aliases.put(atom(e.value()), here); continue; }
                if (key.equals("clear_saved_scope")) { aliases.remove(atom(e.value())); continue; }
                if (key.equals("set_variable") || key.equals("change_variable")) {
                    Block child = (Block)e.value(); String name = atom(child.blockOrAtom("name"));
                    assertVariableWrite(name, here);
                    if (key.equals("set_variable")) here.vars.put(name, requiredValue(child.blockOrAtom("value"), here, prev));
                    else {
                        Entry operation = child.entries().stream().filter(x -> !x.key().equals("name")).findFirst().orElseThrow();
                        long old = here.n(name), amount = number(operation.value(), here, prev);
                        here.put(name, operation.key().equals("add") ? Math.addExact(old, amount) : Math.subtractExact(old, amount));
                    }
                    continue;
                }
                if (key.equals("remove_variable")) { String name = atom(e.value()); assertVariableWrite(name, here); here.vars.remove(name); continue; }
                if (key.equals("clear_variable_list")) { String name = atom(e.value()); assertTrue(name.startsWith("xfma_")); here.nodes(name).clear(); continue; }
                if (key.equals("add_to_variable_list")) {
                    Block child = (Block)e.value(); String name = atom(child.blockOrAtom("name")); assertTrue(name.startsWith("xfma_"));
                    Node target = ref(requiredValue(child.blockOrAtom("target"), here, prev));
                    if (!here.nodes(name).contains(target)) here.nodes(name).add(target); continue;
                }
                if (key.equals("create_story")) {
                    Block child = (Block)e.value(); String type = atom(child.blockOrAtom("type"));
                    assertTrue(type.startsWith("xfma_"));
                    if (failRecordCreation && (FollowupObservationScripts.marketEvolutionRecordTypes().contains(type)
                            || FollowupObservationScripts.capacityRecordTypes().contains(type))) continue;
                    Node created = node("observation-" + nodes.size(), type, false); created.owner = here;
                    aliases.put(atom(child.blockOrAtom("save_scope_as")), created); continue;
                }
                if (key.equals("debug_log")) { logs.add(unquote(atom(e.value()))); continue; }
                if (key.equals("trigger_event")) {
                    Block child = (Block)e.value(); assertEquals(1, child.entries().size());
                    fireOnAction(atom(child.blockOrAtom("on_action")), here, prev); continue;
                }
                if (key.equals("every_player")) {
                    Block child = (Block)e.value(), predicate = optionalBlock(child, "limit");
                    for (Node actualPlayer : List.copyOf(players))
                        if (predicate == null || matches(predicate, actualPlayer, here))
                            execute(without(child, "limit"), actualPlayer, here);
                    continue;
                }
                if (key.equals("every_in_list") || key.equals("every_in_global_list") || key.equals("ordered_in_list") || key.equals("ordered_in_global_list")) {
                    Block child = (Block)e.value(); String list = atom(child.blockOrAtom("variable"));
                    List<Node> selected = new ArrayList<>(key.contains("global") ? global(list) : here.lists.getOrDefault(list, List.of()));
                    Block predicate = optionalBlock(child, "limit");
                    if (predicate != null) selected.removeIf(n -> !matches(predicate, n, here));
                    if (key.startsWith("ordered")) {
                        Expr order = child.blockOrAtom("order_by"); selected.sort(Comparator.comparingLong((Node n) -> number(order, n, here)).reversed());
                        int maximum = Math.toIntExact(number(child.blockOrAtom("max"), here, prev));
                        if (selected.size() > maximum) selected = new ArrayList<>(selected.subList(0, maximum));
                    }
                    Block body = without(child, "variable", "limit", "order_by", "max", "check_range_bounds");
                    for (Node n : selected) execute(body, n, here); continue;
                }
                if (program.containsKey(key)) { run(key, here, prev); continue; }
                Value target = resolve(key, here, prev);
                if (e.value() instanceof Block child && target instanceof Reference n) { execute(child, n.node(), here); continue; }
                throw new AssertionError("unsupported emitted effect " + key);
            }
        }
        boolean matches(Block b, Node here, Node prev) { return b.entries().stream().allMatch(e -> check(e, here, prev)); }
        boolean check(Entry e, Node here, Node prev) {
            String key = e.key();
            if (key.equals("AND")) return matches((Block)e.value(), here, prev);
            if (key.equals("OR")) return ((Block)e.value()).entries().stream().anyMatch(x -> check(x, here, prev));
            if (key.equals("NOT")) return ((Block)e.value()).entries().stream().noneMatch(x -> check(x, here, prev));
            if (key.equals("has_variable")) return here.vars.containsKey(atom(e.value()));
            if (key.equals("exists")) return resolve(atom(e.value()), here, prev) != null;
            if (key.equals("story_type")) return here.kind.equals(atom(e.value()));
            if (key.equals("is_target_in_variable_list")) {
                Block child = (Block)e.value(); Value target = value(child.blockOrAtom("target"), here, prev);
                return target instanceof Reference n && here.lists.getOrDefault(atom(child.blockOrAtom("name")), List.of()).contains(n.node());
            }
            if (key.equals("any_in_list") || key.equals("any_in_global_list")) {
                Block child = (Block)e.value(); String name = atom(child.blockOrAtom("variable"));
                return (key.contains("global") ? global(name) : here.lists.getOrDefault(name, List.of())).stream().anyMatch(n -> matches(without(child, "variable"), n, here));
            }
            if (program.containsKey(key)) return matches(program.get(key), here, prev);
            Value left = resolve(key, here, prev);
            if (left == null) return false;
            if (e.value() instanceof Block child && left instanceof Reference n) return matches(child, n.node(), here);
            Value right = value(e.value(), here, prev);
            if (left == null || right == null) return false;
            if (left instanceof Reference a && right instanceof Reference c) return e.operator().equals("=") ? a.node() == c.node() : e.operator().equals("!=") && a.node() != c.node();
            if (!(left instanceof NumberValue a) || !(right instanceof NumberValue c)) return false;
            return switch (e.operator()) {
                case "=" -> a.value() == c.value(); case "!=" -> a.value() != c.value();
                case ">" -> a.value() > c.value(); case "<" -> a.value() < c.value();
                case ">=" -> a.value() >= c.value(); case "<=" -> a.value() <= c.value();
                default -> throw new AssertionError("unknown comparison " + e.operator());
            };
        }
        Value requiredValue(Expr e, Node here, Node prev) { return java.util.Objects.requireNonNull(value(e, here, prev), "missing emitted operand " + e); }
        long number(Expr e, Node here, Node prev) { return ((NumberValue)requiredValue(e, here, prev)).value(); }
        Value value(Expr e, Node here, Node prev) {
            if (e instanceof Atom a) return resolve(a.word(), here, prev);
            long sum = 0;
            for (Entry operation : ((Block)e).entries()) {
                long operand = number(operation.value(), here, prev);
                sum = switch (operation.key()) {
                    case "value" -> operand; case "add" -> Math.addExact(sum, operand); case "subtract" -> Math.subtractExact(sum, operand);
                    default -> throw new AssertionError("unsupported observation arithmetic " + operation.key());
                };
            }
            return new NumberValue(sum);
        }
        Value resolve(String text, Node here, Node prev) {
            if (text.matches("-?[0-9]+")) return new NumberValue(Long.parseLong(text));
            if (text.equals("yes")) return new NumberValue(1); if (text.equals("no")) return new NumberValue(0);
            if (text.equals("current_date")) return new NumberValue(scriptDateOverride == null ? nativeDate : scriptDateOverride);
            List<String> tiers = List.of("tier_barony", "tier_county", "tier_duchy", "tier_kingdom", "tier_empire");
            if (tiers.contains(text)) return new NumberValue(tiers.indexOf(text) + 1L);
            if (program.containsKey(text)) return value(program.get(text), here, prev);
            String[] parts = text.split("\\.");
            assertTrue(parts[0].startsWith("var:") || parts[0].startsWith("scope:") || parts[0].startsWith("global_var:")
                    || List.of("this", "prev", "story_owner", "primary_title", "gold", "is_ai", "is_adult", "is_alive", "is_landed", "highest_held_title_tier").contains(parts[0]),
                    "unsupported emitted reference " + text);
            Value current = new Reference(here);
            for (int i = 0; i < parts.length; i++) {
                String part = parts[i];
                if (i == 0 && part.equals("global_var:xfm_exchange")) { current = exchangeAvailable ? new Reference(exchange) : null; continue; }
                if (i == 0 && part.startsWith("scope:")) { Node n = aliases.get(part.substring(6)); current = n == null ? null : new Reference(n); continue; }
                if (i == 0 && part.equals("prev")) { current = prev == null ? null : new Reference(prev); continue; }
                if (i == 0 && part.equals("this")) continue;
                if (!(current instanceof Reference reference)) return null;
                Node n = reference.node();
                if (part.startsWith("var:")) current = n.vars.get(part.substring(4));
                else current = switch (part) {
                    case "story_owner" -> n.owner == null ? null : new Reference(n.owner);
                    case "primary_title" -> n.title == null ? null : new Reference(n.title);
                    case "gold" -> new NumberValue(n.gold);
                    case "is_ai" -> new NumberValue(n.ai ? 1 : 0); case "is_adult" -> new NumberValue(n.adult ? 1 : 0);
                    case "is_alive" -> new NumberValue(n.alive ? 1 : 0); case "is_landed" -> new NumberValue(n.landed ? 1 : 0);
                    case "highest_held_title_tier" -> new NumberValue(n.tier);
                    default -> null;
                };
            }
            return current;
        }
        private static Node ref(Value value) { return ((Reference)value).node(); }
        private static String atom(Expr e) { return ((Atom)e).word(); }
        private static String unquote(String text) { return text.startsWith("\"") && text.endsWith("\"") ? text.substring(1, text.length() - 1) : text; }
        private static Block optionalBlock(Block b, String key) { return b.entries().stream().filter(e -> e.key().equals(key)).map(e -> (Block)e.value()).findFirst().orElse(null); }
        private static Block without(Block b, String... keys) { return new Block(b.entries().stream().filter(e -> !List.of(keys).contains(e.key())).toList()); }
    }
}
